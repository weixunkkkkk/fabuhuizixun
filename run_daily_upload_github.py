#!/usr/bin/env python3
"""Refresh the feed, then upload the subscription ICS to GitHub."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run(command: list[str]) -> int:
    print("$ " + " ".join(command))
    completed = subprocess.run(command, cwd=str(ROOT), check=False)
    return int(completed.returncode)


def main() -> int:
    daily_code = run([sys.executable, "run_daily.py"])
    if daily_code != 0:
        return daily_code
    return run([sys.executable, "upload_subscription_feed_to_github.py"])


if __name__ == "__main__":
    raise SystemExit(main())
