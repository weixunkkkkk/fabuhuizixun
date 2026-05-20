#!/usr/bin/env python3
"""
Fetch upcoming launch-event news and export a Google Calendar friendly ICS file.

The script intentionally uses only Python's standard library so it can run in a
fresh macOS/Python environment without installing packages.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import email.utils
import hashlib
import html
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


CN_TZ = dt.timezone(dt.timedelta(hours=8), name="Asia/Shanghai")
UTC = dt.timezone.utc

DEFAULT_CONFIG = {
    "calendar_name": "新品/科技发布会追踪",
    "lookback_days": 60,
    "event_lookback_hours": 48,
    "calendar_past_days": 1,
    "lookahead_days": 60,
    "default_start_time": "19:00",
    "default_duration_minutes": 60,
    "min_score": 3,
    "request_sleep_seconds": 1.0,
    "page_auto_refresh_seconds": 300,
    "output_dir": "out",
    "calendar_sources": [
        {
            "name": "IT之家科技日历",
            "source": "@微醺kkkkk",
            "url_template": "https://napi.ithome.com/api/newsevent/{year}/{month:02d}",
            "detail_url_template": "https://img.ithome.com/app/calendar/event_detail.html?id={id}&noapp=1",
        },
    ],
    "rss_sources": [],
    "queries": [],
}

CATEGORY_LABELS = {
    "mobile": "手机新品",
    "computer": "电脑新品",
    "ev": "新能源汽车",
    "auto": "合资/日系车",
    "tech": "科技数码",
}

CATEGORY_KEYWORDS = {
    "mobile": [
        "手机",
        "新机",
        "旗舰",
        "折叠屏",
        "iphone",
        "galaxy",
        "小米",
        "华为",
        "nova",
        "mate",
        "pura",
        "荣耀",
        "oppo",
        "vivo",
        "一加",
        "realme",
        "红米",
        "魅族",
    ],
    "ev": [
        "新能源汽车",
        "汽车",
        "新车",
        "电动车",
        "智能汽车",
        "特斯拉",
        "比亚迪",
        "蔚来",
        "小鹏",
        "理想",
        "极氪",
        "问界",
        "智界",
        "享界",
        "尊界",
        "尚界",
        "鸿蒙智行",
        "华为乾崑",
        "乾崑",
        "乾崑ads",
        "乾崑智驾",
        "引望",
        "启境",
        "奕境",
        "华境",
        "hima",
        "aito",
        "luxeed",
        "stelato",
        "maextro",
        "华为车bu",
        "华为智能汽车解决方案bu",
        "华为智驾",
        "华为智选车",
        "鸿蒙座舱",
        "赛力斯",
        "奇瑞",
        "北汽蓝谷",
        "江淮",
        "上汽",
        "小米汽车",
        "红旗",
        "北汽",
        "极狐",
        "arcfox",
        "北京越野",
        "bj40",
        "吉利银河",
        "岚图",
        "一汽悦意",
        "吉利",
        "广汽",
        "传祺",
        "奥迪",
        "丰田",
        "博越",
        "领汇",
        "铂智",
        "方程豹",
        "华境",
        "五菱",
        "理想",
        "乐道",
        "哈弗",
        "长城汽车",
        "昊铂",
        "魏牌",
        "腾势",
        "极狐",
        "东风",
        "奕派",
        "悦意",
        "瑞虎",
        "奇瑞",
    ],
    "auto": [
        "合资车",
        "日系车",
        "燃油车",
        "新车",
        "上市",
        "丰田",
        "toyota",
        "本田",
        "honda",
        "日产",
        "nissan",
        "马自达",
        "mazda",
        "斯巴鲁",
        "subaru",
        "三菱",
        "大众",
        "volkswagen",
        "别克",
        "buick",
        "现代",
        "hyundai",
        "起亚",
        "kia",
    ],
    "tech": [
        "科技",
        "数码",
        "ai",
        "芯片",
        "开发者日",
        "平板",
        "笔记本",
        "耳机",
        "音频芯片",
        "nas",
        "私有云",
        "显卡",
        "gpu",
        "机器人",
        "仿真机器人",
        "spacex",
        "starship",
        "星舰",
        "amd",
        "高通",
        "瑞莎",
        "radxa",
        "safe",
        "三星",
        "索尼",
        "绿联",
        "安克",
        "砺算",
        "可穿戴",
        "智能",
        "机器人",
        "大疆",
        "影像",
        "家电",
    ],
    "computer": [
        "电脑",
        "pc",
        "笔记本",
        "游戏本",
        "轻薄本",
        "台式机",
        "一体机",
        "工作站",
        "平板电脑",
        "thinkpad",
        "联想",
        "lenovo",
        "惠普",
        "hp",
        "戴尔",
        "dell",
        "华硕",
        "asus",
        "宏碁",
        "acer",
        "机械革命",
    ],
}

EVENT_KEYWORDS = [
    "发布会",
    "新品发布",
    "新机发布",
    "新车发布",
    "首发",
    "亮相",
    "预售",
    "开启预订",
    "开启小订",
    "开启交付",
    "直播",
    "定档",
    "官宣",
    "邀请函",
    "全球发布",
    "上市发布",
]

NEGATIVE_KEYWORDS = [
    "回顾",
    "汇总",
    "一图看懂",
    "发布会后",
    "发布会结束",
    "看点汇总",
    "早报",
    "do早报",
    "一文汇总",
    "主讲人",
    "京东直播",
    "京东首发",
    "京东首发开售",
    "京东全球首场",
    "京东举办",
    "京东直播",
    "京东 618",
    "京东618",
    "618 正式启动",
    "618 大促",
    "618大促",
    "大促正式启动",
    "机器人拍卖",
    "两轮电动车",
    "电动自行车",
    "电动摩托",
    "电摩",
    "摩托车",
    "摩托",
    "新国标电动车",
    "九号",
    "九号电动",
    "小牛",
    "小牛电动",
    "爱玛",
    "雅迪",
    "春风动力",
    "张雪机车",
    "WSBK",
    "SSP",
]

CHINESE_WEEKDAY = {
    "一": 0,
    "二": 1,
    "三": 2,
    "四": 3,
    "五": 4,
    "六": 5,
    "日": 6,
    "天": 6,
}


@dataclasses.dataclass
class NewsItem:
    title: str
    link: str
    summary: str
    source: str
    published_at: Optional[dt.datetime]
    query_name: str
    category: str


@dataclasses.dataclass
class LaunchEvent:
    title: str
    category: str
    start: dt.datetime
    end: dt.datetime
    all_day: bool
    location: str
    url: str
    source: str
    summary: str
    published_at: Optional[dt.datetime]
    score: int
    matched_date: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch launch events and export ICS/JSON/CSV.")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config JSON. Defaults to built-in config or config.json if present.",
    )
    parser.add_argument("--output-dir", default=None, help="Override output directory.")
    parser.add_argument("--max-items", type=int, default=80, help="Max RSS items to read per query.")
    parser.add_argument("--self-test", action="store_true", help="Run parser self-tests and exit.")
    return parser.parse_args()


def load_config(path: Optional[str]) -> Dict:
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    candidate = Path(path) if path else Path("config.json")
    if candidate.exists():
        with candidate.open("r", encoding="utf-8") as handle:
            user_config = json.load(handle)
        deep_update(config, user_config)
    return config


def deep_update(base: Dict, override: Dict) -> Dict:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_update(base[key], value)
        else:
            base[key] = value
    return base


def google_news_rss_url(query: str, lookback_days: int) -> str:
    q = f"({query}) when:{max(1, lookback_days)}d"
    params = {
        "q": q,
        "hl": "zh-CN",
        "gl": "CN",
        "ceid": "CN:zh-Hans",
    }
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)


def fetch_url(url: str, timeout: int = 20) -> bytes:
    headers = {
        "User-Agent": "launch-calendar-bot/1.0 (+https://news.google.com/rss)",
        "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    }
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        # The Codex sandbox can block Python DNS while allowing curl. The daily
        # macOS LaunchAgent usually uses urllib directly, but this fallback keeps
        # manual refreshes reliable from the same script.
        completed = subprocess.run(
            [
                "curl",
                "-L",
                "--max-time",
                str(timeout),
                "-A",
                headers["User-Agent"],
                url,
            ],
            text=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            message = completed.stderr.decode("utf-8", errors="replace").strip()
            raise urllib.error.URLError(message or f"curl exited {completed.returncode}")
        return completed.stdout


def parse_rss(data: bytes, query_name: str, category: str, max_items: int) -> List[NewsItem]:
    root = ET.fromstring(data)
    items: List[NewsItem] = []
    for node in root.findall(".//item")[:max_items]:
        title = clean_text(node.findtext("title") or "")
        link = clean_text(node.findtext("link") or "")
        summary = clean_html(node.findtext("description") or "")
        source = clean_text(node.findtext("source") or "")
        published_at = parse_rfc822(node.findtext("pubDate") or "")
        if published_at:
            published_at = published_at.astimezone(CN_TZ)
        items.append(
            NewsItem(
                title=title,
                link=link,
                summary=summary,
                source=source,
                published_at=published_at,
                query_name=query_name,
                category=category,
            )
        )
    return items


def parse_rfc822(value: str) -> Optional[dt.datetime]:
    if not value:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def clean_html(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    return clean_text(text)


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def score_item(item: NewsItem) -> int:
    text = f"{item.title} {item.summary}".lower()
    if any(word.lower() in text for word in NEGATIVE_KEYWORDS):
        return 0
    score = 0
    if any(word in text for word in EVENT_KEYWORDS):
        score += 2
    if "发布会" in text:
        score += 2
    if any(word in text for word in ["时间", "定档", "直播", "官宣", "邀请函"]):
        score += 1
    if item.category == "auto_detect":
        category_keywords = [word for words in CATEGORY_KEYWORDS.values() for word in words]
    else:
        category_keywords = CATEGORY_KEYWORDS.get(item.category, [])
    if any(word.lower() in text for word in category_keywords):
        score += 2
    return score


def find_event_datetime(
    text: str,
    now: dt.datetime,
    published_at: Optional[dt.datetime],
    default_start_time: str,
) -> Optional[Tuple[dt.datetime, bool, str]]:
    text = normalize_date_text(text)
    anchor = published_at or now
    default_hour, default_minute = parse_hhmm(default_start_time)

    explicit = find_explicit_date(text, now, anchor, default_hour, default_minute)
    if explicit:
        return explicit

    relative = find_relative_date(text, anchor, default_hour, default_minute)
    if relative:
        return relative

    return None


def normalize_date_text(text: str) -> str:
    text = text.replace("：", ":")
    text = text.replace("号", "日")
    text = re.sub(r"\s+", "", text)
    return text


def parse_hhmm(value: str) -> Tuple[int, int]:
    match = re.match(r"^(\d{1,2}):(\d{2})$", value)
    if not match:
        return 19, 0
    hour, minute = int(match.group(1)), int(match.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return 19, 0
    return hour, minute


def find_explicit_date(
    text: str,
    now: dt.datetime,
    anchor: dt.datetime,
    default_hour: int,
    default_minute: int,
) -> Optional[Tuple[dt.datetime, bool, str]]:
    patterns = [
        re.compile(r"(?P<year>20\d{2})年(?P<month>\d{1,2})月(?P<day>\d{1,2})日?"),
        re.compile(r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日"),
        re.compile(r"(?<!\d)(?P<month>\d{1,2})/(?P<day>\d{1,2})(?!\d)"),
    ]
    for pattern in patterns:
        for match in pattern.finditer(text):
            year = int(match.groupdict().get("year") or infer_year(int(match.group("month")), int(match.group("day")), now, anchor))
            month = int(match.group("month"))
            day = int(match.group("day"))
            try:
                event_date = dt.date(year, month, day)
            except ValueError:
                continue

            after_date = text[match.end() : match.end() + 6]
            before_date = text[max(0, match.start() - 6) : match.start()]
            if after_date.startswith(("消息", "讯", "前", "之前", "内")):
                continue
            if before_date.endswith(("截至", "截止", "有效期至")):
                continue

            nearby = text[match.end() : match.end() + 36]
            before = text[max(0, match.start() - 12) : match.start()]
            time_result = find_time(nearby) or find_time(before)
            if time_result:
                hour, minute, raw_time = time_result
                all_day = False
            else:
                hour, minute, raw_time = default_hour, default_minute, ""
                all_day = True

            start = dt.datetime(year, month, day, hour, minute, tzinfo=CN_TZ)
            raw = match.group(0) + raw_time
            return start, all_day, raw
    return None


def infer_year(month: int, day: int, now: dt.datetime, anchor: dt.datetime) -> int:
    year = anchor.year
    try:
        candidate = dt.datetime(year, month, day, tzinfo=CN_TZ)
    except ValueError:
        return year

    # If an article is old but the date is clearly near its publication date, keep
    # the publication year. Otherwise prefer the next upcoming occurrence.
    if abs((candidate.date() - anchor.date()).days) <= 45:
        return year
    if candidate.date() < now.date() - dt.timedelta(days=3):
        return year + 1
    return year


def find_relative_date(
    text: str,
    anchor: dt.datetime,
    default_hour: int,
    default_minute: int,
) -> Optional[Tuple[dt.datetime, bool, str]]:
    mapping = [
        (r"(今日|今天|今晚)", 0),
        (r"(明日|明天|明晚)", 1),
        (r"(后日|后天)", 2),
    ]
    for pattern, offset in mapping:
        match = re.search(pattern, text)
        if not match:
            continue
        target = anchor.date() + dt.timedelta(days=offset)
        window = text[match.start() : match.end() + 24]
        nearby = text[match.end() : match.end() + 24]
        time_result = find_time(window) or find_time(nearby)
        if time_result:
            hour, minute, raw_time = time_result
            all_day = False
        else:
            hour, minute, raw_time = default_hour, default_minute, ""
            all_day = True
        return dt.datetime(target.year, target.month, target.day, hour, minute, tzinfo=CN_TZ), all_day, match.group(0) + raw_time

    week_match = re.search(r"(本周|下周)([一二三四五六日天])", text)
    if week_match:
        base = anchor.date()
        target_weekday = CHINESE_WEEKDAY[week_match.group(2)]
        week_offset = 7 if week_match.group(1) == "下周" else 0
        days = target_weekday - base.weekday() + week_offset
        if days < 0 and week_match.group(1) == "本周":
            days += 7
        target = base + dt.timedelta(days=days)
        nearby = text[week_match.end() : week_match.end() + 24]
        time_result = find_time(nearby)
        if time_result:
            hour, minute, raw_time = time_result
            all_day = False
        else:
            hour, minute, raw_time = default_hour, default_minute, ""
            all_day = True
        return dt.datetime(target.year, target.month, target.day, hour, minute, tzinfo=CN_TZ), all_day, week_match.group(0) + raw_time

    return None


def find_time(text: str) -> Optional[Tuple[int, int, str]]:
    time_pattern = re.compile(
        r"(?P<period>凌晨|早上|上午|中午|下午|晚上|晚间|今晚|明晚|晚)?"
        r"(?P<hour>\d{1,2})(?:(?:点|时)(?P<minute_cn>\d{1,2})?分?|:(?P<minute>\d{2}))"
    )
    for match in time_pattern.finditer(text):
        hour = int(match.group("hour"))
        minute = int(match.group("minute") or match.group("minute_cn") or 0)
        if not (0 <= hour <= 24 and 0 <= minute <= 59):
            continue
        period = match.group("period") or ""
        if period in {"下午", "晚上", "晚间", "今晚", "明晚", "晚"} and hour < 12:
            hour += 12
        elif period == "中午" and hour < 11:
            hour += 12
        elif hour == 24:
            hour = 0
        return hour, minute, match.group(0)
    return None


def item_to_event(item: NewsItem, config: Dict, now: dt.datetime) -> Optional[LaunchEvent]:
    score = score_item(item)
    if score < int(config["min_score"]):
        return None
    combined = f"{item.title} {item.summary}"
    parsed = find_event_datetime(
        combined,
        now=now,
        published_at=item.published_at,
        default_start_time=str(config["default_start_time"]),
    )
    if not parsed:
        return None
    start, all_day, matched_date = parsed
    event_lookback = dt.timedelta(hours=int(config.get("event_lookback_hours", 24)))
    lookahead = dt.timedelta(days=int(config["lookahead_days"]))
    if start < now - event_lookback or start > now + lookahead:
        return None
    duration = dt.timedelta(minutes=int(config["default_duration_minutes"]))
    end = start + (dt.timedelta(days=1) if all_day else duration)
    category = detect_category(combined, item.category)
    return LaunchEvent(
        title=strip_news_source_suffix(item.title),
        category=category,
        start=start,
        end=end,
        all_day=all_day,
        location=extract_location(combined),
        url=item.link,
        source=item.source or item.query_name,
        summary=item.summary,
        published_at=item.published_at,
        score=score,
        matched_date=matched_date,
    )


def detect_category(text: str, fallback: str) -> str:
    if fallback != "auto_detect":
        return fallback
    lowered = text.lower()
    scores: Dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for keyword in keywords if keyword.lower() in lowered)
    if not scores:
        return "tech"
    best_category, best_score = max(scores.items(), key=lambda item: item[1])
    return best_category if best_score > 0 else "tech"


def strip_news_source_suffix(title: str) -> str:
    return re.sub(r"\s+-\s+[^-]{1,20}$", "", title).strip()


def extract_location(text: str) -> str:
    normalized = clean_text(text)
    if any(word in normalized for word in ["线上", "直播", "在线", "云发布", "官网"]):
        return "线上"
    city_match = re.search(
        r"(北京|上海|广州|深圳|成都|杭州|武汉|南京|重庆|西安|苏州|合肥|"
        r"长沙|厦门|青岛|郑州|珠海|宁波|天津|香港|澳门|台北|东京|首尔|"
        r"新加坡|纽约|洛杉矶|伦敦|巴黎|柏林)",
        normalized,
    )
    if city_match:
        return city_match.group(1)
    return "线上"


def dedupe_events(events: Iterable[LaunchEvent]) -> List[LaunchEvent]:
    best_by_key: Dict[str, LaunchEvent] = {}
    for event in events:
        key = stable_event_key(event)
        key = find_existing_fuzzy_key(best_by_key, key, event)
        existing = best_by_key.get(key)
        if existing is None or event_quality(event) > event_quality(existing):
            best_by_key[key] = event
    return sorted(best_by_key.values(), key=lambda event: (event.start, event.category, event.title))


def stable_event_key(event: LaunchEvent) -> str:
    normalized_title = compact_title_for_dedupe(event.title)[:48]
    return f"{event.category}:{event.start.date().isoformat()}:{normalized_title}"


def find_existing_fuzzy_key(existing: Dict[str, LaunchEvent], default_key: str, event: LaunchEvent) -> str:
    event_title = compact_title_for_dedupe(event.title)
    if len(event_title) < 4:
        return default_key
    for key, other in existing.items():
        if other.category != event.category:
            continue
        if abs((other.start - event.start).total_seconds()) > 90:
            continue
        other_title = compact_title_for_dedupe(other.title)
        if len(other_title) < 4:
            continue
        if event_title in other_title or other_title in event_title:
            return key
    return default_key


def compact_title_for_dedupe(title: str) -> str:
    normalized = title.lower()
    normalized = re.sub(r"[（(].*?具体时间待定.*?[）)]", "", normalized)
    for word in [
        "发布会",
        "新品发布",
        "上市发布",
        "正式上市",
        "开启预售",
        "开启预约",
        "发布上市",
        "全球首秀",
        "国行版",
        "系列",
        "手机",
        "车型",
        "汽车",
        "全新",
        "正式",
        "2026款",
        "2026年",
        "东风",
    ]:
        normalized = normalized.replace(word, "")
    normalized = re.sub(r"[\W_]+", "", normalized)
    return normalized or re.sub(r"[\W_]+", "", title.lower())


def event_quality(event: LaunchEvent) -> Tuple[int, int, int]:
    has_news_url = 1 if re.search(r"https://www\.ithome\.com/0/\d+/\d+\.htm", event.url) else 0
    return event.score, has_news_url, len(event.title)


def write_outputs(events: List[LaunchEvent], candidates: List[NewsItem], output_dir: Path, config: Dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(events, output_dir / "events.json")
    write_csv(events, output_dir / "events.csv")
    write_google_calendar_csv(events, output_dir / "google_calendar_import.csv")
    write_ics(events, output_dir / "launch_events.ics", config)
    write_ics(events, output_dir / "subscription_feed.ics", config)
    write_html(events, output_dir / "events.html", config)
    write_candidates(candidates, output_dir / "undated_candidates.json")


def write_json(events: List[LaunchEvent], path: Path) -> None:
    payload = [event_to_dict(event) for event in events]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(events: List[LaunchEvent], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "start",
                "end",
                "all_day",
                "category",
                "title",
                "location",
                "source",
                "url",
                "score",
                "matched_date",
            ],
        )
        writer.writeheader()
        for event in events:
            writer.writerow(
                {
                    "start": event.start.isoformat(),
                    "end": event.end.isoformat(),
                    "all_day": event.all_day,
                    "category": CATEGORY_LABELS.get(event.category, event.category),
                    "title": event.title,
                    "location": event.location,
                    "source": event.source,
                    "url": event.url,
                    "score": event.score,
                    "matched_date": event.matched_date,
                }
            )


def write_google_calendar_csv(events: List[LaunchEvent], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "Subject",
                "Start Date",
                "Start Time",
                "End Date",
                "End Time",
                "All Day Event",
                "Description",
                "Location",
                "Private",
            ],
        )
        writer.writeheader()
        for event in events:
            writer.writerow(
                {
                    "Subject": f"[{CATEGORY_LABELS.get(event.category, event.category)}] {event.title}",
                    "Start Date": event.start.strftime("%m/%d/%Y"),
                    "Start Time": "" if event.all_day else event.start.strftime("%I:%M %p"),
                    "End Date": event.end.strftime("%m/%d/%Y"),
                    "End Time": "" if event.all_day else event.end.strftime("%I:%M %p"),
                    "All Day Event": "True" if event.all_day else "False",
                    "Description": google_csv_description(event),
                    "Location": event.location,
                    "Private": "False",
                }
            )


def google_csv_description(event: LaunchEvent) -> str:
    return "\n".join(
        part
        for part in [
            f"来源：{event.source}" if event.source else None,
            f"链接：{event.url}" if event.url else None,
            f"识别到的时间：{event.matched_date}",
            f"可信度分数：{event.score}",
            event.url if event.url else None,
        ]
        if part
    )


def write_candidates(candidates: List[NewsItem], path: Path) -> None:
    payload = [
        {
            "title": item.title,
            "category": CATEGORY_LABELS.get(item.category, item.category),
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "score": score_item(item),
        }
        for item in candidates
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def event_to_dict(event: LaunchEvent) -> Dict:
    return {
        "title": event.title,
        "category": CATEGORY_LABELS.get(event.category, event.category),
        "start": event.start.isoformat(),
        "end": event.end.isoformat(),
        "all_day": event.all_day,
        "location": event.location,
        "source": event.source,
        "url": event.url,
        "summary": event.summary,
        "published_at": event.published_at.isoformat() if event.published_at else None,
        "score": event.score,
        "matched_date": event.matched_date,
    }


def write_html(events: List[LaunchEvent], path: Path, config: Dict) -> None:
    now = dt.datetime.now(tz=CN_TZ)
    updated_at = now.strftime("%Y-%m-%d %H:%M")
    rows = "\n".join(render_event_row(event, now) for event in events)
    if not rows:
        rows = (
            '<section class="empty">'
            "<strong>暂时没有识别到明确时间的发布会。</strong>"
            "<span>抓取器会继续每天更新；日期不明确的候选项在 undated_candidates.json 里。</span>"
            "</section>"
        )

    title = html.escape(str(config["calendar_name"]))
    count_text = f"{len(events)} 场"
    refresh_seconds = int(config.get("page_auto_refresh_seconds", 300))
    refresh_meta = ""
    if refresh_seconds > 0:
        refresh_meta = f'  <meta http-equiv="refresh" content="{refresh_seconds}">\n'
    path.write_text(
        f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
{refresh_meta}  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f5f3;
      --surface: #ffffff;
      --surface-muted: #eeeeec;
      --text: #232323;
      --muted: #969696;
      --accent: #f05b57;
      --fresh: #52c79a;
      --hairline: #efefef;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue",
        Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      letter-spacing: 0;
    }}

    .screen {{
      width: min(100%, 560px);
      min-height: 100vh;
      margin: 0 auto;
      background: var(--surface);
    }}

    header {{
      position: sticky;
      top: 0;
      z-index: 2;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 18px 12px;
      background: rgba(255, 255, 255, 0.95);
      border-bottom: 1px solid var(--hairline);
      backdrop-filter: blur(12px);
    }}

    .headline {{
      min-width: 0;
    }}

    h1 {{
      margin: 0;
      font-size: 17px;
      line-height: 1.3;
      font-weight: 700;
    }}

    .updated {{
      margin-top: 3px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }}

    .count {{
      flex: none;
      color: var(--fresh);
      font-size: 13px;
      font-weight: 600;
      white-space: nowrap;
    }}

    .list {{
      padding: 0 0 20px;
    }}

    .event-link {{
      display: block;
      color: inherit;
      text-decoration: none;
    }}

    .event {{
      display: grid;
      grid-template-columns: 4px minmax(0, 1fr) auto;
      column-gap: 12px;
      align-items: start;
      min-height: 58px;
      padding: 13px 18px 12px;
      border-bottom: 1px solid #f4f4f4;
    }}

    .event.ended {{
      background: var(--surface-muted);
      border-bottom-color: #e4e4e2;
    }}

    .rail {{
      width: 4px;
      height: 34px;
      margin-top: 2px;
      border-radius: 1px;
      background: var(--accent);
    }}

    h2 {{
      margin: 0;
      color: #242424;
      font-size: 14px;
      line-height: 1.35;
      font-weight: 700;
      word-break: break-word;
    }}

    .meta {{
      margin-top: 3px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
      word-break: break-word;
    }}

    .status {{
      margin-top: 2px;
      color: var(--fresh);
      font-size: 12px;
      line-height: 1.4;
      font-weight: 600;
      white-space: nowrap;
    }}

    .status.ended {{
      color: #a0a0a0;
      font-weight: 500;
    }}

    .empty {{
      display: grid;
      gap: 8px;
      padding: 28px 20px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }}

    .empty strong {{
      color: var(--text);
      font-size: 14px;
    }}

    @media (max-width: 430px) {{
      header {{
        padding-inline: 14px;
      }}

      .event {{
        grid-template-columns: 4px minmax(0, 1fr) 54px;
        padding-inline: 14px;
        column-gap: 10px;
      }}
    }}
  </style>
</head>
<body>
  <main class="screen">
    <header>
      <div class="headline">
        <h1>{title}</h1>
        <div class="updated">更新于 {html.escape(updated_at)} · 最近两个月</div>
      </div>
      <div class="count">{html.escape(count_text)}</div>
    </header>
    <section class="list" aria-label="发布会清单">
      {rows}
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


def render_event_row(event: LaunchEvent, now: dt.datetime) -> str:
    status_label, status_class = relative_status(event, now)
    classes = "event ended" if status_class == "ended" else "event"
    title = html.escape(event.title)
    meta = html.escape(f"{format_display_time(event)}　{event.location}")
    status = html.escape(status_label)
    return f"""<div class="event-link">
        <article class="{classes}">
          <span class="rail" aria-hidden="true"></span>
          <div>
            <h2>{title}</h2>
            <div class="meta">{meta}</div>
          </div>
          <div class="status {status_class}">{status}</div>
        </article>
      </div>"""


def format_display_time(event: LaunchEvent) -> str:
    date_part = event.start.strftime("%m月%d日")
    if event.all_day:
        return f"{date_part} 00:00"
    return f"{date_part} {event.start.strftime('%H:%M')}"


def relative_status(event: LaunchEvent, now: dt.datetime) -> Tuple[str, str]:
    if now >= event.end:
        return "已结束", "ended"
    if event.start <= now < event.end:
        return "进行中", "live"

    seconds = int((event.start - now).total_seconds())
    if seconds < 3600:
        minutes = max(1, (seconds + 59) // 60)
        return f"{minutes}分钟后", "soon"
    if seconds < 86400:
        hours = max(1, (seconds + 3599) // 3600)
        return f"{hours}小时后", "soon"

    days = max(1, (seconds + 86399) // 86400)
    if days < 7:
        return f"{days}天后", "soon"

    weeks = max(1, (days + 6) // 7)
    return f"{weeks}周后", "soon"


def write_ics(events: List[LaunchEvent], path: Path, config: Dict) -> None:
    now_utc = dt.datetime.now(tz=UTC)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Codex//Launch Calendar Bot//ZH-CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{ics_escape(str(config['calendar_name']))}",
        "X-WR-TIMEZONE:Asia/Shanghai",
    ]
    for event in events:
        lines.extend(event_to_ics_lines(event, now_utc))
    lines.append("END:VCALENDAR")
    path.write_text("\r\n".join(fold_ics_line(line) for line in lines) + "\r\n", encoding="utf-8")


def event_to_ics_lines(event: LaunchEvent, now_utc: dt.datetime) -> List[str]:
    uid_basis = f"{event.category}|{event.start.isoformat()}|{event.title}"
    uid = hashlib.sha1(uid_basis.encode("utf-8")).hexdigest() + "@launch-calendar-bot"
    label = CATEGORY_LABELS.get(event.category, event.category)
    description = "\n".join(
        part
        for part in [
            f"来源：{event.source}" if event.source else None,
            f"链接：{event.url}" if event.url else None,
            f"识别到的时间：{event.matched_date}",
            f"可信度分数：{event.score}",
            event.url if event.url else None,
        ]
        if part
    )
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{format_utc(now_utc)}",
        f"SUMMARY:{ics_escape('[' + label + '] ' + event.title)}",
        f"DESCRIPTION:{ics_escape(description)}",
        f"CATEGORIES:{ics_escape(label)}",
    ]
    if event.location:
        lines.append(f"LOCATION:{ics_escape(event.location)}")
    if event.all_day:
        lines.append(f"DTSTART;VALUE=DATE:{event.start.strftime('%Y%m%d')}")
        lines.append(f"DTEND;VALUE=DATE:{event.end.strftime('%Y%m%d')}")
    else:
        lines.append(f"DTSTART:{format_utc(event.start.astimezone(UTC))}")
        lines.append(f"DTEND:{format_utc(event.end.astimezone(UTC))}")
    lines.append("END:VEVENT")
    return lines


def ics_escape(value: str) -> str:
    value = value.replace("\\", "\\\\")
    value = value.replace(";", "\\;")
    value = value.replace(",", "\\,")
    value = value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
    return value


def fold_ics_line(line: str) -> str:
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line
    chunks = []
    current = ""
    current_len = 0
    for char in line:
        char_len = len(char.encode("utf-8"))
        if current_len + char_len > 73:
            chunks.append(current)
            current = " " + char
            current_len = 1 + char_len
        else:
            current += char
            current_len += char_len
    if current:
        chunks.append(current)
    return "\r\n".join(chunks)


def format_utc(value: dt.datetime) -> str:
    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def iter_calendar_months(now: dt.datetime, config: Dict) -> Iterable[Tuple[int, int]]:
    start = (now - dt.timedelta(hours=int(config.get("event_lookback_hours", 48)))).date().replace(day=1)
    end = (now + dt.timedelta(days=int(config["lookahead_days"]))).date().replace(day=1)
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        yield year, month
        month += 1
        if month > 12:
            year += 1
            month = 1


def parse_ithome_calendar(data: bytes) -> List[Dict]:
    payload = json.loads(data.decode("utf-8-sig"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        nested = payload.get("data") or payload.get("Data") or payload.get("result")
        if isinstance(nested, list):
            return [item for item in nested if isinstance(item, dict)]
    return []


def ithome_calendar_item_to_event(
    raw: Dict,
    config: Dict,
    source_config: Dict,
    now: dt.datetime,
) -> Optional[LaunchEvent]:
    if bool(raw.get("Internal")):
        return None
    if is_blocked_ithome_calendar_item(raw):
        return None

    start = parse_ithome_datetime(raw)
    if not start:
        return None

    lookahead = dt.timedelta(days=int(config["lookahead_days"]))
    min_calendar_date = now.date() - dt.timedelta(days=int(config.get("calendar_past_days", 1)))
    if start.date() < min_calendar_date or start > now + lookahead:
        return None

    title = clean_text(str(raw.get("Title") or ""))
    if not title:
        return None

    all_day = bool(raw.get("TimeNotdecided")) or (
        str(raw.get("EventTime") or "").strip() in {"0:00", "00:00"} and "具体时间待定" in title
    )
    end = parse_dotnet_datetime(str(raw.get("EndTime") or ""))
    if all_day:
        if end and end.date() > start.date():
            end = dt.datetime.combine(end.date() + dt.timedelta(days=1), dt.time.min, tzinfo=CN_TZ)
        else:
            end = dt.datetime.combine(start.date() + dt.timedelta(days=1), dt.time.min, tzinfo=CN_TZ)
        start = dt.datetime.combine(start.date(), dt.time.min, tzinfo=CN_TZ)
    else:
        default_end = start + dt.timedelta(minutes=int(config["default_duration_minutes"]))
        end = end if end and end > start else default_end

    tags = clean_text(str(raw.get("Tags") or ""))
    memo = clean_html(str(raw.get("MemoHtml") or raw.get("Memo") or ""))
    combined = " ".join(part for part in [title, tags, memo] if part)
    event_id = raw.get("ID")
    detail_url = ithome_calendar_detail_url(source_config, event_id)
    url = ithome_news_url(raw.get("NewsId")) or detail_url
    summary = "\n".join(part for part in [memo, f"IT之家日历：{detail_url}", f"标签：{tags}" if tags else ""] if part)

    return LaunchEvent(
        title=title,
        category=detect_ithome_calendar_category(combined),
        start=start,
        end=end,
        all_day=all_day,
        location=clean_text(str(raw.get("EventPlace") or "")) or "线上",
        url=url,
        source=str(source_config.get("source") or "@微醺kkkkk"),
        summary=summary,
        published_at=parse_iso_datetime(str(raw.get("UpdateTime") or "")),
        score=10 if not all_day else 9,
        matched_date=start.strftime("%m月%d日 %H:%M"),
    )


def is_blocked_ithome_calendar_item(raw: Dict) -> bool:
    title = clean_text(str(raw.get("Title") or ""))
    tags = clean_text(str(raw.get("Tags") or ""))
    memo = clean_html(str(raw.get("MemoHtml") or raw.get("Memo") or ""))
    place = clean_text(str(raw.get("EventPlace") or ""))
    searchable = f"{title} {tags} {memo}"
    lowered = searchable.lower()
    if any(keyword.lower() in lowered for keyword in NEGATIVE_KEYWORDS):
        return True
    if "京东" in place and any(word in title for word in ["开售", "首发", "直播", "大促"]):
        return True
    return False


def detect_ithome_calendar_category(text: str) -> str:
    lowered = text.lower()
    ev_words = [
        "汽车",
        "新车",
        "车型",
        "华为乾崑",
        "乾崑智驾",
        "鸿蒙智行",
        "问界",
        "智界",
        "享界",
        "尊界",
        "尚界",
        "华境",
        "启境",
        "奕境",
        "小米汽车",
        "比亚迪",
        "蔚来",
        "小鹏",
        "理想",
        "极氪",
        "红旗",
        "北汽",
        "极狐",
        "arcfox",
        "北京越野",
        "吉利",
        "岚图",
        "五菱",
        "乐道",
        "哈弗",
        "长城汽车",
        "腾势",
        "东风",
        "奕派",
        "悦意",
        "瑞虎",
        "奇瑞",
    ]
    if any(word.lower() in lowered for word in ev_words):
        return "ev"

    computer_words = [
        "电脑",
        "笔记本",
        "游戏本",
        "台式机",
        "pc",
        "computex",
        "华硕",
        "rog",
        "七彩虹",
        "英特尔酷睿",
    ]
    if any(word.lower() in lowered for word in computer_words):
        return "computer"

    mobile_words = [
        "手机",
        "新机",
        "iqoo",
        "oppo",
        "reno",
        "vivo",
        "xperia",
        "红魔",
        "小米 17t",
        "荣耀 600",
        "win turbo",
        "nova",
        "pura",
    ]
    if any(word.lower() in lowered for word in mobile_words):
        return "mobile"

    return "tech"


def parse_ithome_datetime(raw: Dict) -> Optional[dt.datetime]:
    parsed = parse_dotnet_datetime(str(raw.get("RealTime") or ""))
    if parsed:
        return parsed
    return parse_iso_datetime(str(raw.get("RealTimeNew") or ""))


def parse_dotnet_datetime(value: str) -> Optional[dt.datetime]:
    match = re.search(r"/Date\((-?\d+)", value)
    if not match:
        return None
    try:
        timestamp = int(match.group(1)) / 1000
    except ValueError:
        return None
    return dt.datetime.fromtimestamp(timestamp, tz=UTC).astimezone(CN_TZ)


def parse_iso_datetime(value: str) -> Optional[dt.datetime]:
    if not value:
        return None
    normalized = re.sub(r"\.(\d{6})\d+", r".\1", value)
    try:
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=CN_TZ)
    return parsed.astimezone(CN_TZ)


def ithome_news_url(news_id: object) -> str:
    try:
        value = int(news_id or 0)
    except (TypeError, ValueError):
        return ""
    if value <= 0:
        return ""
    return f"https://www.ithome.com/0/{value // 1000:03d}/{value % 1000:03d}.htm"


def ithome_calendar_detail_url(source_config: Dict, event_id: object) -> str:
    template = str(
        source_config.get("detail_url_template")
        or "https://img.ithome.com/app/calendar/event_detail.html?id={id}&noapp=1"
    )
    try:
        return template.format(id=int(event_id or 0))
    except (TypeError, ValueError):
        return template.format(id=0)


def collect_events(config: Dict, max_items: int) -> Tuple[List[LaunchEvent], List[NewsItem], List[str]]:
    now = dt.datetime.now(tz=CN_TZ)
    events: List[LaunchEvent] = []
    candidates: List[NewsItem] = []
    errors: List[str] = []
    for source_config in config.get("calendar_sources", []):
        template = source_config.get("url_template")
        if not template:
            continue
        for year, month in iter_calendar_months(now, config):
            try:
                url = str(template).format(year=year, month=month)
                data = fetch_url(url)
                items = parse_ithome_calendar(data)
            except (KeyError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                errors.append(f"{source_config.get('name', 'Calendar')} {year}-{month:02d}: {exc}")
                continue
            for item in items:
                event = ithome_calendar_item_to_event(item, config, source_config, now)
                if event:
                    events.append(event)
            time.sleep(float(config.get("request_sleep_seconds", 1.0)))

    for source_config in config.get("rss_sources", []):
        try:
            data = fetch_url(source_config["url"])
            items = parse_rss(data, source_config["name"], source_config.get("category", "auto_detect"), max_items)
        except (KeyError, urllib.error.URLError, TimeoutError, ET.ParseError, OSError) as exc:
            errors.append(f"{source_config.get('name', 'RSS')}: {exc}")
            continue

        for item in items:
            event = item_to_event(item, config, now)
            if event:
                events.append(event)
            elif score_item(item) >= int(config["min_score"]):
                candidates.append(item)
        time.sleep(float(config.get("request_sleep_seconds", 1.0)))

    for query_config in config.get("queries", []):
        url = google_news_rss_url(query_config["query"], int(config["lookback_days"]))
        try:
            data = fetch_url(url)
            items = parse_rss(data, query_config["name"], query_config["category"], max_items)
        except (urllib.error.URLError, TimeoutError, ET.ParseError, OSError) as exc:
            errors.append(f"{query_config['name']}: {exc}")
            continue

        for item in items:
            event = item_to_event(item, config, now)
            if event:
                events.append(event)
            elif score_item(item) >= int(config["min_score"]):
                candidates.append(item)
        time.sleep(float(config.get("request_sleep_seconds", 1.0)))
    return dedupe_events(events), candidates, errors


def run_self_tests() -> int:
    now = dt.datetime(2026, 5, 19, 17, 0, tzinfo=CN_TZ)
    cases = [
        ("某品牌新品发布会定档 5月20日 19:00", dt.datetime(2026, 5, 20, 19, 0, tzinfo=CN_TZ), False),
        ("新车发布会将于2026年6月1日晚上8点举行", dt.datetime(2026, 6, 1, 20, 0, tzinfo=CN_TZ), False),
        ("旗舰新机发布会 5月21日晚8点直播", dt.datetime(2026, 5, 21, 20, 0, tzinfo=CN_TZ), False),
        ("手机发布会明晚8点直播", dt.datetime(2026, 5, 20, 20, 0, tzinfo=CN_TZ), False),
        ("科技新品发布会本周五举行", dt.datetime(2026, 5, 22, 19, 0, tzinfo=CN_TZ), True),
        ("5月20日消息，vivo S60 系列手机新品发布会定档 5月29日 19:30", dt.datetime(2026, 5, 29, 19, 30, tzinfo=CN_TZ), False),
    ]
    for text, expected_start, expected_all_day in cases:
        parsed = find_event_datetime(text, now, now, "19:00")
        if not parsed:
            print(f"FAIL: no parse for {text}", file=sys.stderr)
            return 1
        start, all_day, _ = parsed
        if start != expected_start or all_day != expected_all_day:
            print(f"FAIL: {text}: got {start} all_day={all_day}", file=sys.stderr)
            return 1
    print("self-test ok")
    return 0


def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_tests()

    config = load_config(args.config)
    if args.output_dir:
        config["output_dir"] = args.output_dir
    output_dir = Path(config["output_dir"])
    events, candidates, errors = collect_events(config, args.max_items)
    source_count = len(config.get("calendar_sources", [])) + len(config.get("rss_sources", [])) + len(config.get("queries", []))
    all_sources_failed = bool(errors) and len(errors) >= source_count and not events and not candidates
    if all_sources_failed:
        print("refresh failed before finding any items; existing outputs were kept", file=sys.stderr)
    else:
        write_outputs(events, candidates, output_dir, config)

    print(f"events: {len(events)}")
    print(f"undated candidates: {len(candidates)}")
    print(f"html: {output_dir / 'events.html'}")
    print(f"ics: {output_dir / 'launch_events.ics'}")
    print(f"subscription feed: {output_dir / 'subscription_feed.ics'}")
    print(f"google calendar csv: {output_dir / 'google_calendar_import.csv'}")
    print(f"json: {output_dir / 'events.json'}")
    if errors:
        print("errors:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
    return 0 if events or candidates or not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
