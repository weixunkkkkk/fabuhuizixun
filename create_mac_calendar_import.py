#!/usr/bin/env python3
"""Create a one-off ICS file for Mac Calendar import from curated launch events."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from launch_calendar import CN_TZ, LaunchEvent, write_ics, write_outputs


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
CURATOR_SOURCE = "@微醺kkkkk"


def event(title, category, month, day, hour, minute, location, url):
    start = dt.datetime(2026, month, day, hour, minute, tzinfo=CN_TZ)
    return LaunchEvent(
        title=title,
        category=category,
        start=start,
        end=start + dt.timedelta(minutes=90),
        all_day=False,
        location=location,
        url=url,
        source=CURATOR_SOURCE,
        summary=url,
        published_at=None,
        score=10,
        matched_date=start.strftime("%m月%d日 %H:%M"),
    )


def all_day_event(title, category, month, day, location, url):
    start = dt.datetime(2026, month, day, 0, 0, tzinfo=CN_TZ)
    return LaunchEvent(
        title=title,
        category=category,
        start=start,
        end=start + dt.timedelta(days=1),
        all_day=True,
        location=location,
        url=url,
        source=CURATOR_SOURCE,
        summary=url,
        published_at=None,
        score=8,
        matched_date=start.strftime("%m月%d日"),
    )


def all_day_range(title, category, start_month, start_day, end_month, end_day, location, url):
    start = dt.datetime(2026, start_month, start_day, 0, 0, tzinfo=CN_TZ)
    inclusive_end = dt.datetime(2026, end_month, end_day, 0, 0, tzinfo=CN_TZ)
    end = inclusive_end + dt.timedelta(days=1)
    return LaunchEvent(
        title=title,
        category=category,
        start=start,
        end=end,
        all_day=True,
        location=location,
        url=url,
        source=CURATOR_SOURCE,
        summary=url,
        published_at=None,
        score=8,
        matched_date=f"{start.strftime('%m月%d日')} - {inclusive_end.strftime('%m月%d日')}",
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    events = [
        event("联想天禧 AI 一体多端全场景新品超能之夜", "tech", 5, 19, 19, 0, "线上", "https://www.sohu.com/a/1024261683_121839622"),
        event("影石 Insta360 新品发布", "tech", 5, 19, 21, 0, "线上", "https://www.sina.cn/news/detail/5298218549382274.html"),
        event("Google I/O 2026", "tech", 5, 20, 1, 0, "线上", "https://io.google/2026/"),
        event("iQOO 15T 新品发布", "mobile", 5, 20, 19, 0, "线上", "https://www.ithome.com/0/949/624.htm"),
        event("小鹏 GX 上市发布会", "ev", 5, 20, 19, 30, "线上", "https://www.ithome.com/0/950/843.htm"),
        event("网易游戏 520 线上发布会", "tech", 5, 20, 19, 30, "线上", "https://www.ithome.com/0/948/671.htm"),
        all_day_event("2026 阿里云峰会", "tech", 5, 20, "线上/杭州", "https://summit.aliyun.com/2026"),
        event("小米人车家全生态新品发布会", "mobile", 5, 21, 19, 0, "线上", "https://finance.sina.com.cn/tech/roll/2026-05-18/doc-inhyhyqn0717717.shtml"),
        all_day_event("BOOX 文石 Poke7/Pro 墨水屏阅读器发布", "tech", 5, 21, "线上", "https://www.ithome.com/0/948/192.htm"),
        all_day_event("北汽极狐 S3 上市", "ev", 5, 22, "线上", "https://www.ithome.com/0/949/896.htm"),
        all_day_event("五菱缤果 Pro 上市发布会", "ev", 5, 22, "威海", "https://www.bitauto.com/article/1003109938743/"),
        all_day_event("神舟二十三号计划近日择机发射", "tech", 5, 24, "酒泉卫星发射中心", "https://www.ithome.com/0/951/187.htm"),
        event("OPPO Reno16 系列发布会", "mobile", 5, 25, 18, 0, "线上", "https://www.ithome.com/0/951/680.htm"),
        event("荣耀 600 系列暨全场景新品发布会", "mobile", 5, 25, 19, 0, "厦门/线上", "https://club.honor.com/cn/thread-30202295-1-1.html"),
        all_day_event("蔚来 ES9 上市并开启交付", "ev", 5, 27, "线上", "https://cbgc.scol.com.cn/news/7568996"),
        event("SPARK 2026 腾讯游戏发布会", "tech", 5, 27, 20, 0, "线上", "https://finance.sina.com.cn/tech/digi/2026-05-18/doc-inhyimei2851668.shtml"),
        event("vivo S60 系列发布会", "mobile", 5, 29, 19, 30, "线上", "https://www.ithome.com/0/952/238.htm"),
        event("京东 618 正式启动", "tech", 5, 30, 20, 0, "线上", "https://finance.sina.com.cn/tob/2026-05-18/doc-inhyhyqp2925192.shtml"),
        all_day_event("华为 nova 16 系列全场景发布会（待确认）", "mobile", 6, 1, "线上", "https://mobile.zol.com.cn/1181/11818097.html"),
        event("NVIDIA COMPUTEX 2026 Keynote（黄仁勋）", "tech", 6, 1, 11, 0, "台北", "https://www.taiwannews.com.tw/news/6341753"),
        all_day_range("NVIDIA GTC Taipei 2026", "tech", 6, 2, 6, 4, "台北", "https://www.nvidia.com/en-us/events/computex/"),
        all_day_range("COMPUTEX Taipei 2026", "tech", 6, 2, 6, 5, "台北", "https://www.computextaipei.com.tw/en/news/8F914C77B6AF77A5/info.html?cid=news&cr=5&lt=data"),
        all_day_range("Microsoft Build 2026", "tech", 6, 2, 6, 3, "线上/旧金山", "https://build.microsoft.com/"),
        all_day_range("SNEC PV+ 2026 华为光储新品展示", "tech", 6, 3, 6, 5, "上海", "https://solar.huawei.com/cn/events/snec2026/"),
        all_day_range("Apple WWDC 2026", "tech", 6, 9, 6, 13, "线上/Apple Park", "https://www.apple.com.cn/newsroom/2026/05/apple-kicks-off-worldwide-developers-conference-on-june-8/"),
        all_day_range("华为开发者大会 HDC 2026", "tech", 6, 12, 6, 14, "东莞松山湖", "https://www.ithome.com/0/944/689.htm"),
        all_day_range("MWC Shanghai 2026", "tech", 6, 24, 6, 26, "上海新国际博览中心", "https://www.mwcshanghai.com/location-venues"),
    ]
    path = OUT / "mac_calendar_import.ics"
    write_ics(events, path, {"calendar_name": "科技新品发布会日程"})
    write_outputs(events, [], OUT, {"calendar_name": "科技新品发布会日程", "page_auto_refresh_seconds": 300})
    print(path)
    print(OUT / "subscription_feed.ics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
