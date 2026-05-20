#!/usr/bin/env python3
"""Daily entrypoint: refresh launch events and keep the local ICS feed current."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config.json"
CONFIG_FALLBACK = ROOT / "config.example.json"
MAC_SYNC = ROOT / "mac_calendar_sync.swift"
PUBLISH_FEED = ROOT / "publish_subscription_feed.py"


def run(command: list[str], env_extra: dict[str, str] | None = None) -> int:
    print("$ " + " ".join(command))
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    completed = subprocess.run(command, cwd=str(ROOT), check=False, env=env)
    return int(completed.returncode)


def main() -> int:
    config_path = CONFIG if CONFIG.exists() else CONFIG_FALLBACK
    refresh_code = run([sys.executable, "launch_calendar.py", "--config", str(config_path)])
    if refresh_code != 0:
        print("Refresh failed; using the latest existing local data for the summary.", file=sys.stderr)

    summary_code = run([sys.executable, "daily_summary.py"])
    if summary_code != 0:
        return summary_code

    if os.environ.get("SYNC_MAC_CALENDAR") == "1":
        mac_sync_code = run(
            [
                "swift",
                str(MAC_SYNC),
                "--events",
                str(ROOT / "out" / "events.json"),
                "--state",
                str(ROOT / "out" / "mac_calendar_state.json"),
                "--calendar-name",
                "科技新品发布会日程",
            ],
            env_extra={"CLANG_MODULE_CACHE_PATH": str(ROOT / ".swift-module-cache")},
        )
        if mac_sync_code != 0:
            print("Mac Calendar sync failed or needs first-time permission; summary still generated.", file=sys.stderr)
    else:
        print("Mac Calendar sync skipped. Set SYNC_MAC_CALENDAR=1 to enable it.")

    if os.environ.get("PUBLISH_SUBSCRIPTION_FEED") == "1":
        publish_code = run([sys.executable, str(PUBLISH_FEED)])
        if publish_code != 0:
            print("Subscription feed publish failed; local files are still generated.", file=sys.stderr)
    else:
        print("Subscription feed publish skipped. Upload out/subscription_feed.ics to GitHub yourself.")

    print(f"subscription feed: {ROOT / 'out' / 'subscription_feed.ics'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
