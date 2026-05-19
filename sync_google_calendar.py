#!/usr/bin/env python3
"""
Sync launch events into Google Calendar using only Python's standard library.

One-time setup:
1. Create a Google OAuth Desktop client and save it as google_client_secret.json.
2. Run: python3 sync_google_calendar.py --authorize
3. Future runs can use: python3 sync_google_calendar.py
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import http.server
import json
import secrets
import socketserver
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Tuple


TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
CALENDAR_API = "https://www.googleapis.com/calendar/v3"
SCOPE = "https://www.googleapis.com/auth/calendar"
TIME_ZONE = "Asia/Shanghai"


class CalendarSyncError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync launch events to Google Calendar.")
    parser.add_argument("--events", default="out/events.json", help="Path to generated events JSON.")
    parser.add_argument("--credentials", default="google_client_secret.json", help="Google OAuth client JSON.")
    parser.add_argument("--token", default="google_token.json", help="Saved OAuth token JSON.")
    parser.add_argument("--calendar-name", default="新品/科技发布会追踪", help="Google Calendar name.")
    parser.add_argument("--authorize", action="store_true", help="Run one-time OAuth authorization.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would sync without calling Google APIs.")
    parser.add_argument("--no-browser", action="store_true", help="Print auth URL without opening a browser.")
    return parser.parse_args()


def read_credentials(path: Path) -> Dict:
    if not path.exists():
        raise CalendarSyncError(
            f"Missing {path}. Put your Google OAuth Desktop client JSON here first."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    client = payload.get("installed") or payload.get("web")
    if not client or not client.get("client_id") or not client.get("client_secret"):
        raise CalendarSyncError(f"{path} is not a valid Google OAuth client JSON.")
    return client


def read_events(path: Path) -> List[Dict]:
    if not path.exists():
        raise CalendarSyncError(f"Missing {path}. Run launch_calendar.py first.")
    events = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(events, list):
        raise CalendarSyncError(f"{path} must contain a JSON list.")
    return events


def load_token(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_token(path: Path, token: Dict) -> None:
    path.write_text(json.dumps(token, ensure_ascii=False, indent=2), encoding="utf-8")


def request_json(
    url: str,
    method: str = "GET",
    token: Optional[str] = None,
    body: Optional[Dict] = None,
    form: Optional[Dict] = None,
) -> Dict:
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json; charset=utf-8"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    elif form is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = urllib.parse.urlencode(form).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise CalendarSyncError(f"Google API {method} {url} failed: {exc.code} {raw}") from exc
    except urllib.error.URLError as exc:
        raise CalendarSyncError(f"Network error calling Google API: {exc}") from exc


def exchange_code_for_token(client: Dict, code: str, redirect_uri: str) -> Dict:
    payload = request_json(
        TOKEN_URL,
        method="POST",
        form={
            "code": code,
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
    )
    return normalize_token(payload)


def refresh_access_token(client: Dict, token: Dict) -> Dict:
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise CalendarSyncError("Token has no refresh_token. Run --authorize again.")
    payload = request_json(
        TOKEN_URL,
        method="POST",
        form={
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )
    payload["refresh_token"] = refresh_token
    return normalize_token(payload)


def normalize_token(token: Dict) -> Dict:
    expires_in = int(token.get("expires_in", 3600))
    token["expires_at"] = int(time.time()) + max(60, expires_in) - 60
    return token


def get_access_token(client: Dict, token_path: Path) -> str:
    token = load_token(token_path)
    if not token:
        raise CalendarSyncError("No saved Google token. Run sync_google_calendar.py --authorize first.")
    if token.get("access_token") and int(token.get("expires_at", 0)) > int(time.time()) + 60:
        return token["access_token"]
    token = refresh_access_token(client, token)
    save_token(token_path, token)
    return token["access_token"]


class OAuthHandler(http.server.BaseHTTPRequestHandler):
    code: Optional[str] = None
    error: Optional[str] = None
    expected_state: str = ""

    def do_GET(self) -> None:  # noqa: N802 - stdlib callback name
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        if parsed.path != "/oauth2callback":
            self.send_response(404)
            self.end_headers()
            return
        state = query.get("state", [""])[0]
        if state != self.expected_state:
            self.error = "OAuth state mismatch."
        elif "error" in query:
            self.error = query["error"][0]
        else:
            self.code = query.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            "授权完成，可以回到 Codex/终端了。".encode("utf-8")
            if self.code
            else f"授权失败：{self.error}".encode("utf-8")
        )

    def log_message(self, *_args) -> None:
        return


def run_authorization(client: Dict, token_path: Path, open_browser: bool) -> None:
    state = secrets.token_urlsafe(24)
    handler = type("Handler", (OAuthHandler,), {"expected_state": state, "code": None, "error": None})
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as server:
        port = server.server_address[1]
        redirect_uri = f"http://127.0.0.1:{port}/oauth2callback"
        params = {
            "client_id": client["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        auth_url = AUTH_URL + "?" + urllib.parse.urlencode(params)
        print("Open this URL to authorize Google Calendar access:")
        print(auth_url)
        if open_browser:
            webbrowser.open(auth_url)
        while handler.code is None and handler.error is None:
            server.handle_request()

        if handler.error or not handler.code:
            raise CalendarSyncError(f"Authorization failed: {handler.error}")
        token = exchange_code_for_token(client, handler.code, redirect_uri)
        save_token(token_path, token)
        print(f"Saved token to {token_path}")


def find_or_create_calendar(access_token: str, calendar_name: str) -> str:
    page_token = None
    while True:
        params = {"maxResults": "250"}
        if page_token:
            params["pageToken"] = page_token
        url = f"{CALENDAR_API}/users/me/calendarList?{urllib.parse.urlencode(params)}"
        payload = request_json(url, token=access_token)
        for item in payload.get("items", []):
            if item.get("summary") == calendar_name:
                return item["id"]
        page_token = payload.get("nextPageToken")
        if not page_token:
            break

    created = request_json(
        f"{CALENDAR_API}/calendars",
        method="POST",
        token=access_token,
        body={"summary": calendar_name, "timeZone": TIME_ZONE},
    )
    return created["id"]


def google_event_id(event: Dict) -> str:
    title = "".join(ch for ch in str(event.get("title", "")).lower() if ch.isalnum())
    basis = f"{event.get('category', '')}|{title[:80]}|{event.get('url', '')}"
    digest = hashlib.sha256(basis.encode("utf-8")).digest()[:16]
    encoded = base64.b32hexencode(digest).decode("ascii").lower().rstrip("=")
    return "lc" + encoded


def to_google_event(event: Dict) -> Dict:
    summary = f"[{event.get('category', '发布会')}] {event.get('title', '新品发布会')}"
    description_parts = [
        "由 launch-calendar-bot 自动同步。",
        f"来源：{event.get('source')}" if event.get("source") else "",
        f"链接：{event.get('url')}" if event.get("url") else "",
        f"识别到的时间：{event.get('matched_date')}" if event.get("matched_date") else "",
        f"可信度分数：{event.get('score')}" if event.get("score") is not None else "",
        event.get("summary") or "",
    ]
    payload = {
        "id": google_event_id(event),
        "summary": summary,
        "location": event.get("location") or "线上",
        "description": "\n".join(part for part in description_parts if part),
        "extendedProperties": {
            "private": {
                "launchCalendarBot": "1",
                "launchCalendarBotId": google_event_id(event),
            }
        },
    }
    if event.get("url"):
        payload["source"] = {"title": event.get("source") or "launch-calendar-bot", "url": event["url"]}
    start = parse_event_datetime(event["start"])
    end = parse_event_datetime(event["end"])
    if event.get("all_day"):
        payload["start"] = {"date": start.date().isoformat()}
        payload["end"] = {"date": end.date().isoformat()}
    else:
        payload["start"] = {"dateTime": start.isoformat(), "timeZone": TIME_ZONE}
        payload["end"] = {"dateTime": end.isoformat(), "timeZone": TIME_ZONE}
    return payload


def parse_event_datetime(value: str) -> dt.datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone(dt.timedelta(hours=8)))
    return parsed


def upsert_event(access_token: str, calendar_id: str, event: Dict) -> str:
    google_event = to_google_event(event)
    event_id = google_event["id"]
    encoded_calendar_id = urllib.parse.quote(calendar_id, safe="")
    encoded_event_id = urllib.parse.quote(event_id, safe="")
    event_url = f"{CALENDAR_API}/calendars/{encoded_calendar_id}/events/{encoded_event_id}"
    try:
        request_json(event_url, token=access_token)
        request_json(event_url + "?sendUpdates=none", method="PUT", token=access_token, body=google_event)
        return "updated"
    except CalendarSyncError as exc:
        if "failed: 404" not in str(exc):
            raise
    insert_url = f"{CALENDAR_API}/calendars/{encoded_calendar_id}/events?sendUpdates=none"
    request_json(insert_url, method="POST", token=access_token, body=google_event)
    return "created"


def sync_events(access_token: str, calendar_name: str, events: List[Dict], dry_run: bool) -> Tuple[int, int]:
    if dry_run:
        for event in events:
            google_event = to_google_event(event)
            print(f"[dry-run] {google_event['id']} {google_event['summary']}")
        return len(events), 0

    calendar_id = find_or_create_calendar(access_token, calendar_name)
    created = 0
    updated = 0
    for event in events:
        result = upsert_event(access_token, calendar_id, event)
        if result == "created":
            created += 1
        else:
            updated += 1
        print(f"{result}: {event.get('title')}")
    return created, updated


def main() -> int:
    args = parse_args()
    credential_path = Path(args.credentials)
    token_path = Path(args.token)
    event_path = Path(args.events)

    try:
        client = None if args.dry_run else read_credentials(credential_path)
        if args.authorize:
            client = read_credentials(credential_path)
            run_authorization(client, token_path, open_browser=not args.no_browser)
            return 0

        events = read_events(event_path)
        if not events:
            print(f"No events in {event_path}; nothing to sync.")
            return 0
        access_token = "dry-run-token" if args.dry_run else get_access_token(client, token_path)
        created, updated = sync_events(access_token, args.calendar_name, events, args.dry_run)
        print(f"created: {created}")
        print(f"updated: {updated}")
        return 0
    except CalendarSyncError as exc:
        print(f"Google Calendar sync failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
