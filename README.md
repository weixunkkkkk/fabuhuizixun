# 发布会资讯日历

这个仓库只用于托管公开订阅源。采集脚本和一键上传工具保留在本机，不再放到 GitHub 上，避免仓库变得杂乱。

## 订阅地址

推荐使用：

```text
https://weixunkkkkk.github.io/fabuhuizixun/out/subscription_feed.ics
```

备用地址：

```text
https://weixunkkkkk.github.io/fabuhuizixun/subscription_feed.ics
```

## 数据策略

- 主源：IT之家科技日历，来源标记为 `@微醺kkkkk`
- 补充源：IT之家 RSS、36氪 RSS、Gemini Google Sheet
- 优先级：IT之家科技日历 > IT之家 RSS > 其他补充源
- 去重：同一天同产品/同会议只保留一条；与 IT之家重复时优先保留 IT之家
- 过滤：排除直播带货、两轮车、跑分、IPO、融资、销量等非发布会信息

## 仓库文件

- `out/subscription_feed.ics`：推荐订阅源，供 GitHub Pages 使用
- `subscription_feed.ics`：兼容订阅源，内容与推荐订阅源同步
- `README.md`：说明文档

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

## 自动更新

当前发布流程是本地手动刷新数据，然后把生成的订阅源推送到 GitHub。GitHub Pages 只负责托管静态文件，不负责主动抓取。

## 说明

日程来自公开信息，发布会时间可能临时调整。重要活动建议在开始前再核对品牌官方公告。

维护者：`@微醺kkkkk`
