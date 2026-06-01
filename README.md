# 新品发布会日历抓取器

这个小工具会自动搜索三类发布会信息：

- 手机新品/新机发布会
- 新能源汽车/智能汽车/新车发布会
- 科技数码/AI 硬件/消费电子发布会

抓到的信息会输出成：

- `out/events.html`：像截图那样的手机竖屏发布会清单页，默认每 5 分钟自动刷新一次
- `out/launch_events.ics`：可以导入 Google Calendar 的日历文件
- `out/google_calendar_import.csv`：Google Calendar 官方 CSV 导入格式
- `out/daily_summary.csv`：每日汇总表格
- `out/daily_summary.md`：每天自动任务会贴给你的 Markdown 汇总
- `out/events.json`：结构化事件数据，方便后续接 API
- `out/events.csv`：表格版本
- `out/undated_candidates.json`：像发布会但日期不够明确的候选新闻

## 运行

在这个目录下执行：

```bash
python3 launch_calendar.py --config config.example.json
```

也可以先跑解析自测：

```bash
python3 launch_calendar.py --self-test
```

## 导入 Google Calendar

最简单方式，不做 Google 授权：

双击 `一键导入到日历.command`，它会自动刷新并打开 `out/launch_events.ics`。

如果你的 Mac 日历已经登录 Google 账号，弹窗里选你的 Google 日历，然后点导入。

推荐优先用 `out/launch_events.ics`，它对中文和链接更稳；如果你更习惯表格导入，就用 `out/google_calendar_import.csv`。

## 同步 Google Calendar

当前用本地 Google Calendar API 同步，不依赖第三方 Python 包。

一次性授权：

1. 在 Google Cloud 里创建 OAuth 客户端，类型选 `Desktop app`。
2. 下载客户端 JSON，放到本目录并命名为 `google_client_secret.json`。
3. 执行：

```bash
python3 sync_google_calendar.py --authorize
```

以后同步：

```bash
python3 run_daily.py
```

`run_daily.py` 会先刷新抓取结果，再生成 `out/daily_summary.csv` 和 `out/daily_summary.md`。如果授权文件存在，它还会把 `out/events.json` 里的发布会创建/更新到 Google Calendar 的 `新品/科技发布会追踪` 日历里。

授权文件说明：

- `google_client_secret.json`：Google OAuth 客户端配置。
- `google_token.json`：第一次授权后自动生成。
- 这两个文件已经写进 `.gitignore`，不会被误提交。

## 同步 Mac 日历

现在每日自动任务也会尝试把明确时间的发布会同步到 Mac 日历，目标日历名是 `科技新品发布会日程`。

如果你已经把这个 Mac/iCloud 日历设成公开订阅日历，脚本会写入这个同名日历；你的公开订阅链接会随着日历内容更新。

同时会持续刷新一个稳定的订阅源文件：

```text
out/subscription_feed.ics
```

如果你的订阅地址是由某个公开文件服务托管的，就让那个公开 URL 指向这个文件或它的同步副本。

第一次使用前，双击：

```text
一键授权Mac日历同步.command
```

如果系统弹出日历权限，点允许。授权后每天自动任务会自动创建或更新事件，并用 `out/mac_calendar_state.json` 防止重复创建。

## iPhone 订阅地址

如果你不想经过 Mac，可以用 Google Apps Script 直接生成一个 iPhone 可订阅的公网地址。代码在：

```text
google-apps-script/iphone-subscription-feed.gs
```

部署成 Web 应用后，生成的 `https://script.google.com/macros/s/.../exec` 就是 iPhone 订阅地址。

本地新增内容后，复制 `publisher.example.json` 为 `publisher.json`，填入 Apps Script 的 `/exec` 地址和 `setupSyncToken` 生成的 token。之后每天 `run_daily.py` 会自动把本地 `out/subscription_feed.ics` 上传到这个订阅地址背后；手动上传可运行：

```bash
python3 publish_subscription_feed.py
```

## 调整抓取范围

复制一份配置：

```bash
cp config.example.json config.json
```

默认每次覆盖最近 60 天抓到的消息，并只把今天前后 60 天窗口内的发布会写进日历。你可以改 `config.json` 里的 `queries`、`lookback_days`、`lookahead_days` 或 `min_score`。

`min_score` 越高，误报越少，但可能漏掉一些小品牌发布会。默认值 `3` 比较适合先用起来。

## Gemini 补充数据

如果你用 Gemini 每天额外跑一遍，把结果整理成 CSV 后放到：

```text
inbox/gemini_events.csv
```

表头固定为：

```csv
title,start,end,all_day,category,location,url,source,summary
```

`start` 推荐格式：`2026-06-08 19:00`。`category` 可填：`手机新品`、`新能源汽车`、`科技数码`、`电脑新品`。

这些补充数据会自动进入同一套过滤和去重逻辑；如果和 IT之家科技日历重复，会优先保留 IT之家那条。

## 定时任务建议

现在按每天抓一次配置。新品发布会信息一般提前几天到几周公布，这个频率比较稳。

我已经在 Codex 里创建了一个名为 `每日发布会汇总并同步Mac日历` 的自动任务，按北京时间每天早上尝试刷新一次这个目录里的日历输出。每次都会生成 `out/daily_summary.csv` 和 `out/daily_summary.md`，在自动任务结果里贴出当天汇总表格，并把明确时间的发布会同步到 Mac 日历。
