# 发布会资讯日历

一个面向手机新品、科技数码、新能源汽车和智能汽车发布会的公开日程订阅源。适合每天快速扫一眼近期发布会，也适合直接订阅到 iPhone、Mac 日历或 Google Calendar。

维护者：`@微醺kkkkk`

## 快速入口

网页清单：

```text
https://weixunkkkkk.github.io/fabuhuizixun/out/events.html
```

推荐订阅源：

```text
https://weixunkkkkk.github.io/fabuhuizixun/out/subscription_feed.ics
```

备用订阅源：

```text
https://weixunkkkkk.github.io/fabuhuizixun/subscription_feed.ics
```

## 网页可以看什么

网页清单是一个轻量发布会看板，支持：

- 点击顶部统计卡查看「未结束」「24 小时内」「手机新品」「科技数码」「新能源汽车」等二级视图
- 搜索品牌、车型、会议名称或地点
- 通过 URL hash 直接分享筛选结果
- 手机端滚动时自动收起顶部统计区，减少占屏
- 每 5 分钟自动刷新页面

常用链接：

- 未结束发布会：`https://weixunkkkkk.github.io/fabuhuizixun/out/events.html#view=active`
- 24 小时内：`https://weixunkkkkk.github.io/fabuhuizixun/out/events.html#view=soon24`
- 科技数码：`https://weixunkkkkk.github.io/fabuhuizixun/out/events.html#category=%E7%A7%91%E6%8A%80%E6%95%B0%E7%A0%81`
- 新能源汽车：`https://weixunkkkkk.github.io/fabuhuizixun/out/events.html#category=%E6%96%B0%E8%83%BD%E6%BA%90%E6%B1%BD%E8%BD%A6`

## 怎么订阅日历

iPhone / iPad：

1. 打开「日历」App
2. 进入「日历」列表
3. 添加日历
4. 选择「添加订阅日历」
5. 粘贴推荐订阅源地址并保存

Mac：

1. 打开「日历」App
2. 选择「文件」-「新建日历订阅」
3. 粘贴推荐订阅源地址
4. 设置自动刷新频率

Google Calendar：

1. 打开 Google Calendar 网页版
2. 在「其他日历」旁点击 `+`
3. 选择「通过网址」
4. 粘贴推荐订阅源地址
5. 点击「添加日历」

## 收录范围

会优先收录：

- 手机、新机、旗舰机、折叠屏、影像新品发布会
- 耳机、平板、手表、充电设备、相机、游戏硬件等消费科技新品发布会
- 新能源汽车、智能汽车、新车上市、智驾技术沟通会
- WWDC、HDC、Build、Google I/O、GTC 等明确科技或开发者主题活动
- 品牌官方发布会、主题演讲、上市发布、开启预售等强日程信号

会主动排除：

- 直播带货、京东直播、618 促销
- 两轮车、电摩、小牛、九号、春风等不需要关注的品类
- 跑分、评测、开箱、曝光、爆料、销量、财报
- IPO、融资、排名、注册登记、普通行业新闻
- 泛行业展会、峰会、论坛、博览会

## 数据来源和更新

当前主源是 IT之家科技日历，来源标记为 `@微醺kkkkk`。补充来源包括 IT之家 RSS、36氪 RSS、极客公园 RSS、Google News RSS、品牌官方页面和 Gemini 表格。

处理规则：

- 用户已整理的 GitHub ICS 优先
- IT之家科技日历优先于普通 RSS
- 官方来源只用于高置信补充或修正待定时间
- 同一天同产品或同一场活动会去重，只保留一条
- 没有明确活动日期的新闻不会直接进入日历

数据由本地自动化定期刷新并推送到 GitHub Pages。GitHub Pages 只负责托管静态文件，不负责主动抓取。

## 仓库文件

- `out/events.html`：网页发布会看板
- `out/subscription_feed.ics`：推荐日历订阅源
- `subscription_feed.ics`：兼容订阅源
- `out/events.json`：结构化事件数据
- `out/events.csv`：表格版本
- `out/google_calendar_import.csv`：Google Calendar CSV 导入格式
- `out/undated_candidates.json`：像发布会但时间不明确的候选项
- `out/rejected_events.json`：被过滤掉的项目及原因

## 说明

日程来自公开信息，发布会时间可能临时调整。重要活动建议在开始前再核对品牌官方公告。
