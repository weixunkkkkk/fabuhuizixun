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
        all_day_range("2026 年中国网络文明大会", "tech", 5, 19, 5, 20, "广西南宁", "https://www.wicinternet.org.cn/2026-05/07/c_1748329453354091.htm"),
        event("2026 AMD AI 开发者日", "tech", 5, 19, 10, 30, "上海", "https://www.ithome.com/0/951/099.htm"),
        event("焕新极氪 009 上市", "ev", 5, 19, 19, 0, "线上", "https://www.ithome.com/0/951/625.htm"),
        event("联想天禧 AI 一体多端全场景新品超能之夜", "tech", 5, 19, 19, 0, "线上", "https://www.sohu.com/a/1024261683_121839622"),
        event("影石 Insta360 新品发布", "tech", 5, 19, 21, 0, "线上", "https://www.sina.cn/news/detail/5298218549382274.html"),
        event("Google I/O 2026", "tech", 5, 20, 1, 0, "线上", "https://io.google/2026/"),
        all_day_event("爱玛冠军笛 Oi 全国上架", "ev", 5, 20, "线上", ""),
        all_day_event("索尼耳机新品发布（WH-1000X）", "tech", 5, 20, "线上", "https://www.ithome.com/0/952/299.htm"),
        event("九号 Mz1 新国标电动车发布", "ev", 5, 20, 9, 0, "线上", "https://finance.sina.com.cn/tech/digi/2026-05-20/doc-inhyksve4829722.shtml"),
        event("iQOO 15T 新品发布", "mobile", 5, 20, 19, 0, "线上", "https://www.ithome.com/0/949/624.htm"),
        event("2026 款红旗 H5 / 红旗 HQ9 PHEV 上市发布会", "ev", 5, 20, 19, 0, "线上", "https://www.ithome.com/0/949/428.htm"),
        event("小鹏 GX 上市发布会", "ev", 5, 20, 19, 30, "线上", "https://www.ithome.com/0/950/843.htm"),
        event("网易游戏 520 线上发布会", "tech", 5, 20, 19, 30, "线上", "https://www.ithome.com/0/948/671.htm"),
        event("西昇科技 7G100 显卡京东首发开售", "tech", 5, 20, 20, 0, "线上", "https://www.gamersky.com/hardware/202605/2035124.shtml"),
        event("九号电动全新 M3 系列预购", "ev", 5, 20, 20, 0, "线上", ""),
        event("春风动力 550CL-C 新品发布会", "ev", 5, 20, 20, 0, "线上", ""),
        all_day_event("2026 阿里云峰会", "tech", 5, 20, "线上/杭州", "https://summit.aliyun.com/2026"),
        all_day_event("北京越野 BJ40 增程长续航版上市发布会", "ev", 5, 21, "线上", "https://www.ithome.com/0/947/010.htm"),
        all_day_event("比亚迪第三代元 PLUS 正式上市", "ev", 5, 21, "线上", "https://www.sohu.com/a/1026035987_120043996"),
        event("绿联 NAS 私有云新品发布", "tech", 5, 21, 10, 0, "京东直播", "https://www.sohu.com/a/1022031590_122066678"),
        event("小米人车家全生态新品发布会", "mobile", 5, 21, 19, 0, "线上", "https://finance.sina.com.cn/tech/roll/2026-05-18/doc-inhyhyqn0717717.shtml"),
        all_day_event("BOOX 文石 Poke7/Pro 墨水屏阅读器发布", "tech", 5, 21, "线上", "https://www.ithome.com/0/948/192.htm"),
        all_day_event("京东全球首场仿真机器人拍卖", "tech", 5, 22, "线上", "https://www.ithome.com/0/951/935.htm"),
        all_day_event("北汽极狐 S3 上市", "ev", 5, 22, "线上", "https://www.ithome.com/0/949/896.htm"),
        all_day_event("吉利银河星耀 7 上市发布会", "ev", 5, 22, "线上", "https://www.ithome.com/0/952/052.htm"),
        all_day_event("五菱缤果 Pro 上市发布会", "ev", 5, 22, "威海", "https://www.bitauto.com/article/1003109938743/"),
        all_day_event("安克 ANKER Thus AI 音频芯片及旗舰耳机发布会", "tech", 5, 22, "线上", "https://www.ithome.com/0/952/106.htm"),
        all_day_event("岚图泰山 X8 上市发布会", "ev", 5, 22, "线上", "https://www.ithome.com/0/951/700.htm"),
        event("SpaceX 星际 V3 首飞", "tech", 5, 22, 6, 30, "博卡奇卡星际基地", "https://www.space.com/spaceflight/spacex-starship-flight-10-target-date"),
        event("2026 雅迪摩登之夜暨全球新品发布会", "ev", 5, 24, 19, 30, "江苏无锡", "https://finance.sina.cn/2026-05-19/detail-inhykfuk7660901.d.html"),
        event("神舟二十三号载人飞船发射（预测）", "tech", 5, 24, 22, 47, "酒泉卫星发射中心", "https://www.ithome.com/0/951/187.htm"),
        all_day_event("荣耀手表 6 Plus 发布", "tech", 5, 25, "线上", "https://www.ithome.com/0/951/697.htm"),
        event("OPPO Reno16 系列发布会", "mobile", 5, 25, 18, 0, "线上", "https://www.ithome.com/0/951/680.htm"),
        event("荣耀 600 系列暨全场景新品发布会", "mobile", 5, 25, 19, 0, "厦门/线上", "https://club.honor.com/cn/thread-30202295-1-1.html"),
        event("荣耀 Earbuds 耳夹式耳机 Pro 发布", "tech", 5, 25, 20, 0, "线上", "https://www.ithome.com/0/951/692.htm"),
        all_day_event("蔚来 ES9 上市并开启交付", "ev", 5, 27, "线上", "https://cbgc.scol.com.cn/news/7568996"),
        event("SPARK 2026 腾讯游戏发布会", "tech", 5, 27, 20, 0, "线上", "https://finance.sina.com.cn/tech/digi/2026-05-18/doc-inhyimei2851668.shtml"),
        all_day_event("小米 17T 系列手机海外发布会", "mobile", 5, 28, "海外", "https://www.ithome.com/0/951/343.htm"),
        event("三星 SAFE 论坛 2026 美国场", "tech", 5, 29, 1, 0, "美国圣何塞", "https://semiconductor.samsung.com/us/safe-forum/"),
        all_day_event("一汽悦意 08 拆车开启预售", "ev", 5, 29, "线上", "https://www.ithome.com/0/951/779.htm"),
        event("vivo S60 系列发布会", "mobile", 5, 29, 19, 30, "线上", "https://www.ithome.com/0/952/238.htm"),
        event("2026 高通 & 瑞莎 AI 开发者日", "tech", 5, 30, 9, 0, "深圳", "https://finance.sina.com.cn/tob/2026-05-19/doc-inhymisn7138683.shtml"),
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
