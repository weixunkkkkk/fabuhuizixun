#!/usr/bin/env python3
"""Create a concise daily launch-event summary table."""

from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List, Tuple


CN_TZ = dt.timezone(dt.timedelta(hours=8), name="Asia/Shanghai")
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"


def read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def parse_dt(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=CN_TZ)
    return parsed.astimezone(CN_TZ)


def status_for(event: Dict, now: dt.datetime) -> Tuple[str, int]:
    start = parse_dt(event["start"])
    end = parse_dt(event["end"])
    if now >= end:
        return "已结束", -1
    if start <= now < end:
        return "进行中", 0

    seconds = int((start - now).total_seconds())
    if seconds < 3600:
        minutes = max(1, (seconds + 59) // 60)
        return f"{minutes}分钟后", 1
    if seconds < 86400:
        hours = max(1, (seconds + 3599) // 3600)
        return f"{hours}小时后", 2
    days = max(1, (seconds + 86399) // 86400)
    if days < 7:
        return f"{days}天后", 3
    weeks = max(1, (days + 6) // 7)
    return f"{weeks}周后", 4


def display_time(event: Dict) -> str:
    start = parse_dt(event["start"])
    if event.get("all_day"):
        return start.strftime("%m月%d日 全天/待定")
    return start.strftime("%m月%d日 %H:%M")


def build_rows(events: List[Dict], now: dt.datetime) -> List[Dict]:
    rows = []
    for event in events:
        status, rank = status_for(event, now)
        rows.append(
            {
                "状态": status,
                "时间": display_time(event),
                "标题": event.get("title", ""),
                "分类": event.get("category", ""),
                "地点": event.get("location", "线上"),
                "_sort": (rank, parse_dt(event["start"])),
            }
        )
    return sorted(rows, key=lambda row: row["_sort"])


def write_csv(rows: List[Dict], path: Path) -> None:
    fields = ["状态", "时间", "标题", "分类", "地点"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def markdown_table(rows: List[Dict], limit: int = 30) -> str:
    fields = ["状态", "时间", "标题", "分类", "地点"]
    if not rows:
        return "暂无明确时间的发布会。"

    lines = [
        "| 状态 | 时间 | 标题 | 分类 | 地点 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows[:limit]:
        lines.append(
            "| "
            + " | ".join(escape_md(str(row.get(field, ""))) for field in fields)
            + " |"
        )
    return "\n".join(lines)


def candidate_table(candidates: List[Dict], limit: int = 12) -> str:
    if not candidates:
        return "暂无候选项。"
    ranked = sorted(candidates, key=lambda item: int(item.get("score", 0)), reverse=True)[:limit]
    lines = [
        "| 分数 | 标题 | 分类 |",
        "| ---: | --- | --- |",
    ]
    for item in ranked:
        lines.append(
            "| "
            + " | ".join(
                [
                    escape_md(str(item.get("score", ""))),
                    escape_md(str(item.get("title", ""))),
                    escape_md(str(item.get("category", ""))),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_markdown(rows: List[Dict], candidates: List[Dict], path: Path, now: dt.datetime) -> None:
    active = [row for row in rows if row["状态"] not in {"已结束"}]
    ended = len(rows) - len(active)
    today = sum(1 for row in active if "小时后" in row["状态"] or "分钟后" in row["状态"] or row["状态"] == "进行中")
    content = f"""# 发布会每日汇总

更新时间：{now.strftime("%Y-%m-%d %H:%M")}（Asia/Shanghai）

| 指标 | 数量 |
| --- | ---: |
| 明确时间发布会 | {len(rows)} |
| 未结束发布会 | {len(active)} |
| 24小时内/进行中 | {today} |
| 已结束 | {ended} |
| 候选项 | {len(candidates)} |

## 近期发布会

{markdown_table(active)}

## 已结束

{markdown_table([row for row in rows if row["状态"] == "已结束"], limit=10)}

## 候选池

{candidate_table(candidates)}
"""
    path.write_text(content, encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(tz=CN_TZ)
    events = read_json(OUT / "events.json", [])
    candidates = read_json(OUT / "undated_candidates.json", [])
    rows = build_rows(events, now)
    write_csv(rows, OUT / "daily_summary.csv")
    write_markdown(rows, candidates, OUT / "daily_summary.md", now)

    print(f"summary csv: {OUT / 'daily_summary.csv'}")
    print(f"summary markdown: {OUT / 'daily_summary.md'}")
    print("")
    print((OUT / "daily_summary.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
