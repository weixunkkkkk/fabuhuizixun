#!/usr/bin/env python3
"""Commit and push generated subscription feeds to GitHub.

From the local project it uses a small separate clone, so the GitHub repo can
keep its own README or other files without being overwritten. When run inside
the GitHub repo itself, it updates that repo directly.
"""

from __future__ import annotations

import argparse
import shutil
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FEED = Path("out/subscription_feed.ics")
COMPAT_FEED = Path("subscription_feed.ics")
PUBLISHED_FEEDS = [FEED, COMPAT_FEED]
REMOTE = os.environ.get(
    "LAUNCH_FEED_GIT_REMOTE",
    "https://github.com/weixunkkkkk/fabuhuizixun.git",
)
BRANCH = os.environ.get("LAUNCH_FEED_GIT_BRANCH", "main")
PUBLISH_ROOT = ROOT if (ROOT / ".git").exists() else ROOT / ".github-feed-worktree"


def run(command: list[str], cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout.rstrip())
    if check and completed.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} failed with exit code {completed.returncode}")
    return completed


def run_git(args: list[str], cwd: Path = PUBLISH_ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=cwd, check=check)


def ensure_feed() -> None:
    if not (ROOT / FEED).exists():
        raise RuntimeError(f"missing {FEED}")


def ensure_publish_repo(dry_run: bool) -> None:
    direct_publish = PUBLISH_ROOT == ROOT
    if dry_run and not (PUBLISH_ROOT / ".git").exists():
        print(f"dry-run: would clone {REMOTE} into {PUBLISH_ROOT}")
        return

    if not (PUBLISH_ROOT / ".git").exists():
        PUBLISH_ROOT.parent.mkdir(parents=True, exist_ok=True)
        if PUBLISH_ROOT.exists():
            shutil.rmtree(PUBLISH_ROOT)
        run(["git", "clone", REMOTE, str(PUBLISH_ROOT)], cwd=ROOT)
    else:
        run_git(["remote", "set-url", "origin", REMOTE])

    run_git(["config", "user.name", "Codex"], check=False)
    run_git(["config", "user.email", "codex@local"], check=False)

    if (PUBLISH_ROOT / ".git" / "rebase-merge").exists() or (PUBLISH_ROOT / ".git" / "rebase-apply").exists():
        run_git(["rebase", "--abort"], check=False)
    run_git(["fetch", "origin", BRANCH], check=False)
    if not direct_publish:
        run_git(
            ["stash", "push", "--include-untracked", "--message", "launch-feed-upload-autostash", "--"]
            + [str(path) for path in PUBLISHED_FEEDS],
            check=False,
        )
        run_git(["checkout", "--detach", f"origin/{BRANCH}"])


def feed_changed() -> bool:
    completed = run_git(["status", "--porcelain", "--", *[str(path) for path in PUBLISHED_FEEDS]], check=False)
    return bool(completed.stdout.strip())


def has_unpushed_commits() -> bool:
    completed = subprocess.run(
        ["git", "rev-list", "--count", f"origin/{BRANCH}..HEAD"],
        cwd=str(PUBLISH_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    try:
        return int(completed.stdout.strip() or "0") > 0
    except ValueError:
        return False


def sync_with_remote_before_edit() -> None:
    run_git(["fetch", "origin", BRANCH])
    run_git(["rebase", "--autostash", f"origin/{BRANCH}"])


def copy_feed() -> None:
    source = ROOT / FEED
    for target_path in PUBLISHED_FEEDS:
        target = PUBLISH_ROOT / target_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload generated subscription feeds to GitHub.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without committing or pushing.")
    args = parser.parse_args()

    try:
        ensure_feed()
        ensure_publish_repo(args.dry_run)
        if args.dry_run and not (PUBLISH_ROOT / ".git").exists():
            print(f"dry-run: would copy {ROOT / FEED} to GitHub feed paths")
            return 0

        if not args.dry_run:
            sync_with_remote_before_edit()
        copy_feed()
        changed = feed_changed()
        ahead = has_unpushed_commits()
        if not changed and not ahead:
            print("subscription feed unchanged; GitHub upload skipped.")
            return 0

        if args.dry_run:
            print("dry-run: would commit and push generated feed files")
            return 0

        if changed:
            run_git(["add", *[str(path) for path in PUBLISHED_FEEDS]])
            message = "Update subscription feed " + dt.datetime.now().strftime("%Y-%m-%d %H:%M")
            run_git(["commit", "-m", message, "--", *[str(path) for path in PUBLISHED_FEEDS]])
        run_git(["push", "-u", "origin", f"HEAD:{BRANCH}"])
        print("GitHub upload complete.")
        return 0
    except RuntimeError as exc:
        print(f"GitHub upload failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
