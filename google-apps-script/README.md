# Google Apps Script 版本

这是最简单的 Google 方案：代码直接跑在 Google 里，用 `CalendarApp` 写入你的 Google 日历，用 `SpreadsheetApp` 记录已同步和候选项。

如果你只想要 iPhone 可以订阅的公开地址，不想先同步到 Mac 或 Google 日历，用 `iphone-subscription-feed.gs`。它会把发布会清单直接输出成 `.ics` 订阅源。

## iPhone 订阅地址版

1. 打开 https://script.google.com/ 新建项目。
2. 把 `iphone-subscription-feed.gs` 全部复制进去，替换默认的 `Code.gs`。
3. 先运行 `previewFeed`，按提示授权，确认日志里能看到事件数量。
4. 运行 `setupSyncToken`，复制日志里生成的 token。
5. 运行 `installDailyTrigger`，安装每天 9 点刷新。
6. 点右上角 `部署` -> `新部署` -> 类型选 `Web 应用`。
7. `执行身份` 选你自己，`谁可以访问` 选 `任何人`，然后部署。
8. 复制生成的 `https://script.google.com/macros/s/.../exec` 地址；这就是 iPhone 的订阅地址。

iPhone 上添加：打开 `日历` -> `日历` -> `添加日历` -> `添加订阅日历`，粘贴上面的 `/exec` 地址。旧版 iOS 可以在 `设置` -> `日历` -> `账户` -> `添加账户` -> `其他` -> `添加已订阅的日历` 里添加。

## 本地新增后怎么同步到这个订阅地址

Apps Script 的 `/exec` 地址是 iPhone 订阅入口；真正的同步动作由本地 `publish_subscription_feed.py` 完成。

1. 复制 `publisher.example.json` 为 `publisher.json`。
2. 把 `web_app_url` 改成你的 Apps Script `/exec` 地址。
3. 把 `sync_token` 改成 `setupSyncToken` 日志里那串 token。
4. 以后运行 `python3 run_daily.py`，脚本会刷新本地 `out/subscription_feed.ics`，再自动上传到 Apps Script。

手动只上传一次也可以运行：

```bash
python3 publish_subscription_feed.py
```

上传成功后，iPhone 仍然订阅同一个 `/exec` 地址，不需要重新添加。iPhone 自己会按系统频率刷新；通常不是秒级，可能会有一段缓存延迟。

## 怎么用

1. 打开你的 Google 表格，进入 `扩展程序` -> `Apps Script`。
2. 用 `Code.gs` 里的内容替换原来的代码。
3. 先运行 `testCreateEvent`，按提示授权，确认日历里能看到测试事件。
4. 再运行 `previewCandidatesOnly`，看表格里的 `候选池` 是否有内容。
5. 最后运行 `syncLaunchEvents`，正式写入日历。
6. 需要每天自动同步，运行一次 `installDailyTrigger`。

## 为什么这版比原来更容易抓到

- 加了 Google News RSS 作为补充来源，不只靠单站 RSS。
- 36Kr 改用 `feed-newsflash`，原来的 `https://www.36kr.com/feed` 有时抓不到。
- 筛选从“必须完全命中”改成打分制，误杀少很多。
- 支持 `5月20日 19:00`、`5月20日晚7点`、`明晚8点`、`本周五 10:30`。
- 只识别到日期但没有具体时间时，也能先创建“具体时间待定”的全天事件。
- 所有候选都会写进 `候选池`，方便看是 RSS 没抓到、时间没识别，还是分数不够。

## 常用函数

- `previewCandidatesOnly`：只抓取并写候选，不创建日历事件。
- `syncLaunchEvents`：抓取并同步到 Google Calendar。
- `installDailyTrigger`：安装每天自动同步。
- `testCreateEvent`：测试日历授权。
- `testExtractDateTime`：测试中文时间识别。
