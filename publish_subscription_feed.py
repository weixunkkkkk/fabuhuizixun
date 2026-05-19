#!/usr/bin/env python3
"""Publish the local iCalendar feed to the Apps Script web app."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_FEED = ROOT / "out" / "subscription_feed.ics"
DEFAULT_CONFIG = ROOT / "publisher.json"


def load_config(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def with_token(url: str, token: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
    query["token"] = token
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query)))


def publish(url: str, token: str, feed_path: Path, timeout: int) -> int:
    ics = feed_path.read_text(encoding="utf-8")
    if "BEGIN:VCALENDAR" not in ics or "END:VCALENDAR" not in ics:
        print(f"{feed_path} does not look like an iCalendar file.", file=sys.stderr)
        return 2

    request = urllib.request.Request(
        with_token(url, token),
        data=ics.encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "text/calendar; charset=utf-8",
            "User-Agent": "LaunchCalendarPublisher/1.0",
        },
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")

    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        print(body)
        return 1

    if not result.get("ok"):
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        return 1

    print(f"Published {result.get('eventCount', '?')} events to subscription feed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--feed", default=str(DEFAULT_FEED))
    parser.add_argument("--url", default=os.environ.get("LAUNCH_FEED_PUBLISH_URL", ""))
    parser.add_argument("--token", default=os.environ.get("LAUNCH_FEED_PUBLISH_TOKEN", ""))
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    config = load_config(Path(args.config))
    url = args.url or config.get("web_app_url", "")
    token = args.token or config.get("sync_token", "")
    feed_path = Path(args.feed)

    if not url or not token:
        print(
            "No publisher configured. Create publisher.json or set "
            "LAUNCH_FEED_PUBLISH_URL and LAUNCH_FEED_PUBLISH_TOKEN."
        )
        return 0

    if not feed_path.exists():
        print(f"Feed file not found: {feed_path}", file=sys.stderr)
        return 2

    return publish(url, token, feed_path, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
