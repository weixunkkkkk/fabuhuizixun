#!/usr/bin/env python3
"""Commit and push only the generated subscription feed to GitHub."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FEED = Path("out/subscription_feed.ics")


def git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_DIR"] = str(ROOT / ".git-local")
    env["GIT_WORK_TREE"] = str(ROOT)
    return env


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        env=git_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout.rstrip())
    if check and completed.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed with exit code {completed.returncode}")
    return completed


def ensure_repo() -> None:
    if not (ROOT / ".git-local").exists():
        raise RuntimeError("missing .git-local repository")
    if not (ROOT / FEED).exists():
        raise RuntimeError(f"missing {FEED}")
    run_git(["config", "user.name", "Codex"], check=False)
    run_git(["config", "user.email", "codex@local"], check=False)


def feed_changed() -> bool:
    completed = run_git(["status", "--porcelain", "--", str(FEED)], check=False)
    return bool(completed.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload out/subscription_feed.ics to GitHub.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without committing or pushing.")
    args = parser.parse_args()

    try:
        ensure_repo()
        if not feed_changed():
            print("subscription feed unchanged; GitHub upload skipped.")
            return 0

        if args.dry_run:
            print(f"dry-run: would commit and push {FEED}")
            return 0

        run_git(["add", str(FEED)])
        message = "Update subscription feed " + dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        run_git(["commit", "--only", str(FEED), "-m", message])
        run_git(["push", "-u", "origin", "main"])
        print("GitHub upload complete.")
        return 0
    except RuntimeError as exc:
        print(f"GitHub upload failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
