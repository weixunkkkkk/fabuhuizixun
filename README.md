# 发布会资讯日历 / Launch Event Calendar

这是一个自动整理「手机新品、科技数码、新能源汽车、开发者大会」相关发布会的公开日历源。仓库会生成可订阅的 `.ics` 文件，也保留 CSV、JSON 和网页清单，方便在 iPhone、Google Calendar、Mac 日历或其他日历 App 中查看。

## 订阅地址

推荐使用这个稳定地址：

```text
https://weixunkkkkk.github.io/fabuhuizixun/out/subscription_feed.ics
```

兼容地址：

```text
https://weixunkkkkk.github.io/fabuhuizixun/subscription_feed.ics
```

网页清单：

```text
https://weixunkkkkk.github.io/fabuhuizixun/out/events.html
```

## 数据策略

- 主源：IT之家科技日历，来源标记为 `@微醺kkkkk`
- 补充源：IT之家 RSS、36氪 RSS、Gemini Google Sheet
- 优先级：IT之家科技日历 > IT之家 RSS > 其他补充源
- 去重：同一天同产品/同会议只保留一条；与 IT之家重复时优先保留 IT之家
- 过滤：排除京东直播/首发、两轮车、小牛、九号、春风、电摩、跑分、IPO、融资、交付量、销量等非发布会信息
- 时间范围：默认关注最近和未来约 60 天内的明确日程

当前 Gemini 表格源支持中文表头：

```csv
日期,时间,发布会名称,状态
```

`状态=已结束` 的行会自动跳过。

## 输出文件

- `out/subscription_feed.ics`：推荐订阅源，供 GitHub Pages 使用
- `subscription_feed.ics`：根目录兼容订阅源，内容与推荐订阅源同步
- `out/events.html`：手机竖屏发布会清单页
- `out/events.json`：结构化事件数据
- `out/events.csv`：表格版本
- `out/google_calendar_import.csv`：Google Calendar CSV 导入格式
- `out/daily_summary.md`：每日汇总
- `out/undated_candidates.json`：像发布会但日期不明确的候选项

## 订阅方法

iPhone / iPad：

1. 打开「日历」App
2. 进入「日历」列表
3. 添加日历
4. 选择「添加订阅日历」
5. 粘贴推荐订阅地址并保存

Google Calendar：

1. 打开 Google Calendar 网页版
2. 在「其他日历」旁点击 `+`
3. 选择「通过网址」
4. 粘贴推荐订阅地址
5. 点击「添加日历」

## 本地运行

解析自测：

```bash
python3 launch_calendar.py --self-test
```

刷新本地输出：

```bash
python3 launch_calendar.py --config config.example.json
```

刷新并上传 GitHub Pages 订阅源：

```bash
python3 run_daily_upload_github.py
```

macOS 上也可以双击：

```text
一键刷新并上传到GitHub.command
```

## Gemini 补充

如果 Gemini 每天固定时间输出发布会候选，可以写入 Google Sheet 并发布为 CSV。脚本会自动拉取 `config.example.json` 中的 `manual_sources`。

本地临时补充可以写入：

```text
inbox/gemini_events.csv
```

推荐表头：

```csv
title,start,end,all_day,category,location,url,source,summary
```

`start` 推荐格式：`2026-06-08 19:00`。`category` 可填：`手机新品`、`新能源汽车`、`科技数码`、`电脑新品`。

## 自动更新

当前发布流程是本地自动化每天刷新数据，然后把生成的订阅源推送到 GitHub。GitHub Pages 只负责托管静态文件，不负责主动抓取。

如果要换自己的仓库，需要修改：

- `LAUNCH_FEED_GIT_REMOTE`
- `LAUNCH_FEED_GIT_BRANCH`
- `config.example.json`

## 说明

日程来自公开信息，发布会时间可能临时调整。重要活动建议在开始前再核对品牌官方公告。

维护者：`@微醺kkkkk`
