/***************
 * iPhone 订阅日历版：科技新品发布会 .ics 订阅源
 *
 * 用法：
 * 1. 打开 https://script.google.com/ 新建 Apps Script 项目。
 * 2. 把本文件全部复制到 Code.gs。
 * 3. 先运行 previewFeed 授权并检查日志。
 * 4. 运行 installDailyTrigger，安装每天 9 点刷新。
 * 5. 部署 -> 新部署 -> Web 应用，访问权限选“任何人”。
 * 6. 复制部署后的 /exec 地址，在 iPhone 日历里添加“订阅日历”。
 ***************/

const CONFIG = {
  calendarName: '科技新品发布会日程',
  timezone: 'Asia/Shanghai',
  defaultDurationMinutes: 90,
  lookAheadDays: 60,
  lookBackHours: 24,
  minScore: 6,
 dailyHour: 9,
  sourceLabel: '@微醺kkkkk',
  cacheSeconds: 6 * 60 * 60,
  uploadChunkSize: 7000,

  queries: [
    '手机 新品 发布会 时间 新机 直播 定档',
    '新能源汽车 新车 发布会 直播 定档 上市 预售',
    '科技 数码 新品 发布会 AI 硬件 开发者大会',
    '小米 华为 荣耀 vivo OPPO iQOO 发布会',
    '蔚来 小鹏 理想 极氪 比亚迪 问界 发布会 上市',
    '华为 新品 发布会 nova Mate Pura 鸿蒙 HarmonyOS HDC',
    '鸿蒙智行 华为车BU 华为乾崑 问界 智界 享界 尊界 尚界 启境 奕境 华境 发布会',
    '耳机 NAS 私有云 显卡 机器人 音频芯片 索尼 绿联 安克 砺算 发布会 开售'
  ],

  rssSources: [
    'https://www.ithome.com/rss/'
  ],

  strongWords: [
    '发布会', '新品发布', '上市发布', '正式上市', '开发者大会',
    '技术沟通会', '影像沟通会', '全球发布', '定档', '官宣',
    '邀请函', '直播', '开启预售', '开启预约', '上市'
  ],

  productWords: [
    '手机', '新机', '旗舰', '折叠屏', '影像', 'AI', '系统',
    '耳机', '平板', '手表', '智能穿戴', '新能源汽车', '新车',
    '智驾', '智能驾驶', '小米', '华为', '荣耀', 'vivo', 'iQOO',
    'OPPO', '一加', 'realme', '魅族', '三星', '苹果', '小鹏',
    '理想', '蔚来', '极氪', '比亚迪', '鸿蒙智行', '华为乾崑',
    '乾崑智驾', '乾崑ADS', '引望', '问界', '智界', '享界',
    '尊界', '尚界', '启境', '奕境', '华境',
    '红旗', '北京越野', '吉利银河', '岚图', '一汽悦意',
    '安克', '绿联', '索尼', 'NAS', '私有云', '显卡', '音频芯片',
    '机器人', '仿真机器人', 'SpaceX', 'AMD', '高通', '瑞莎',
    '大疆', '影石',
    'NVIDIA', '英伟达', '微软', 'Apple', 'WWDC', 'COMPUTEX', 'MWC'
  ],

  negativeWords: [
    '评测', '体验', '开箱', '降价', '销量', '财报', '招聘',
    '教程', '维修', '二手', '拆解', '渲染图', '爆料称',
    '疑似', '曝光', '回顾', '汇总', '一图看懂',
    '京东直播', '京东首发', '京东 618', '618 正式启动',
    '两轮电动车', '电动自行车', '新国标电动车',
    '九号电动', '小牛电动', '爱玛', '雅迪', '春风动力'
  ]
};


function doGet() {
  const ics = getCurrentFeed_();

  return ContentService
    .createTextOutput(ics)
    .setMimeType(ContentService.MimeType.ICAL);
}


function doPost(e) {
  const expectedToken = PropertiesService.getScriptProperties().getProperty('SYNC_TOKEN');
  const token = e && e.parameter ? String(e.parameter.token || '') : '';
  const ics = e && e.postData ? String(e.postData.contents || '') : '';

  if (!expectedToken) {
    return jsonOutput_({ ok: false, error: '请先在 Apps Script 里运行 setupSyncToken。' });
  }

  if (!token || token !== expectedToken) {
    return jsonOutput_({ ok: false, error: '同步 token 不正确。' });
  }

  if (ics.indexOf('BEGIN:VCALENDAR') === -1 || ics.indexOf('END:VCALENDAR') === -1) {
    return jsonOutput_({ ok: false, error: '上传内容不是有效的 iCalendar。' });
  }

  storeUploadedIcs_(ics);
  CacheService.getScriptCache().put('ICS_FEED', ics, CONFIG.cacheSeconds);

  return jsonOutput_({
    ok: true,
    updatedAt: new Date().toISOString(),
    eventCount: countEventsInIcs_(ics)
  });
}


function getCurrentFeed_() {
  const cache = CacheService.getScriptCache();
  let ics = cache.get('ICS_FEED');

  if (!ics) {
    ics = refreshSubscriptionFeed();
  }

  return ics;
}


function refreshSubscriptionFeed() {
  const uploaded = readUploadedIcs_();
  if (uploaded) {
    CacheService.getScriptCache().put('ICS_FEED', uploaded, CONFIG.cacheSeconds);
    PropertiesService.getScriptProperties().setProperties({
      UPDATED_AT: new Date().toISOString(),
      EVENT_COUNT: String(countEventsInIcs_(uploaded)),
      FEED_MODE: 'uploaded'
    });
    return uploaded;
  }

  const events = buildEvents_();
  const ics = buildIcs_(events);

  CacheService.getScriptCache().put('ICS_FEED', ics, CONFIG.cacheSeconds);
  PropertiesService.getScriptProperties().setProperties({
    UPDATED_AT: new Date().toISOString(),
    EVENT_COUNT: String(events.length),
    FEED_MODE: 'generated'
  });

  return ics;
}


function setupSyncToken() {
  const token = `${Utilities.getUuid()}-${Utilities.getUuid()}`.replace(/-/g, '');
  PropertiesService.getScriptProperties().setProperty('SYNC_TOKEN', token);
  Logger.log('本地上传 token：' + token);
  Logger.log('把这个 token 填到本地 publisher.json 的 sync_token。');
  return token;
}


function clearUploadedFeed() {
  deleteUploadedIcs_();
  CacheService.getScriptCache().remove('ICS_FEED');
  Logger.log('已清空本地上传的 ICS，之后会回到 Apps Script 自己生成。');
}


function previewFeed() {
  const events = buildEvents_();
  Logger.log('事件数量：' + events.length);
  events.slice(0, 40).forEach(event => {
    Logger.log(`${event.identifyTime} ${event.title} ${event.url}`);
  });
  Logger.log(buildIcs_(events).slice(0, 1200));
}


function installDailyTrigger() {
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === 'refreshSubscriptionFeed') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  ScriptApp.newTrigger('refreshSubscriptionFeed')
    .timeBased()
    .everyDays(1)
    .atHour(CONFIG.dailyHour)
    .inTimezone(CONFIG.timezone)
    .create();
}


function buildEvents_() {
  const events = manualEvents_().concat(fetchRssEvents_());
  return dedupeEvents_(events)
    .filter(isInWindow_)
    .sort((a, b) => a.start.getTime() - b.start.getTime());
}


function manualEvents_() {
  return [
    event_('联想天禧 AI 一体多端全场景新品超能之夜', '科技数码', '2026-05-19T19:00:00+08:00', '线上', 'https://www.sohu.com/a/1024261683_121839622', 10, '05月19日 19:00'),
    event_('影石 Insta360 新品发布', '科技数码', '2026-05-19T21:00:00+08:00', '线上', 'https://www.sina.cn/news/detail/5298218549382274.html', 10, '05月19日 21:00'),
    allDay_('2026 阿里云峰会', '科技数码', '2026-05-20', '线上/杭州', 'https://summit.aliyun.com/2026', 8, '05月20日'),
    event_('Google I/O 2026', '科技数码', '2026-05-20T01:00:00+08:00', '线上', 'https://io.google/2026/', 10, '05月20日 01:00'),
    event_('iQOO 15T 新品发布', '手机新品', '2026-05-20T19:00:00+08:00', '线上', 'https://www.ithome.com/0/949/624.htm', 10, '05月20日 19:00'),
    event_('小鹏 GX 上市发布会', '新能源汽车', '2026-05-20T19:30:00+08:00', '线上', 'https://www.ithome.com/0/950/843.htm', 10, '05月20日 19:30'),
    event_('网易游戏 520 线上发布会', '科技数码', '2026-05-20T19:30:00+08:00', '线上', 'https://www.ithome.com/0/948/671.htm', 10, '05月20日 19:30'),
    allDay_('BOOX 文石 Poke7/Pro 墨水屏阅读器发布', '科技数码', '2026-05-21', '线上', 'https://www.ithome.com/0/948/192.htm', 8, '05月21日'),
    event_('小米人车家全生态新品发布会', '手机新品', '2026-05-21T19:00:00+08:00', '线上', 'https://finance.sina.com.cn/tech/roll/2026-05-18/doc-inhyhyqn0717717.shtml', 10, '05月21日 19:00'),
    allDay_('北汽极狐 S3 上市', '新能源汽车', '2026-05-22', '线上', 'https://www.ithome.com/0/949/896.htm', 8, '05月22日'),
    allDay_('五菱缤果 Pro 上市发布会', '新能源汽车', '2026-05-22', '威海', 'https://www.bitauto.com/article/1003109938743/', 8, '05月22日'),
    allDay_('神舟二十三号计划近日择机发射', '科技数码', '2026-05-24', '酒泉卫星发射中心', 'https://www.ithome.com/0/951/187.htm', 8, '05月24日'),
    event_('OPPO Reno16 系列发布会', '手机新品', '2026-05-25T18:00:00+08:00', '线上', 'https://www.ithome.com/0/951/680.htm', 10, '05月25日 18:00'),
    event_('荣耀 600 系列暨全场景新品发布会', '手机新品', '2026-05-25T19:00:00+08:00', '厦门/线上', 'https://club.honor.com/cn/thread-30202295-1-1.html', 10, '05月25日 19:00'),
    allDay_('蔚来 ES9 上市并开启交付', '新能源汽车', '2026-05-27', '线上', 'https://cbgc.scol.com.cn/news/7568996', 8, '05月27日'),
    event_('SPARK 2026 腾讯游戏发布会', '科技数码', '2026-05-27T20:00:00+08:00', '线上', 'https://finance.sina.com.cn/tech/digi/2026-05-18/doc-inhyimei2851668.shtml', 10, '05月27日 20:00'),
    event_('vivo S60 系列发布会', '手机新品', '2026-05-29T19:30:00+08:00', '线上', 'https://www.ithome.com/0/952/238.htm', 10, '05月29日 19:30'),
    allDay_('华为 nova 16 系列全场景发布会（待确认）', '手机新品', '2026-06-01', '线上', 'https://mobile.zol.com.cn/1181/11818097.html', 6, '06月01日'),
    event_('NVIDIA COMPUTEX 2026 Keynote（黄仁勋）', '科技数码', '2026-06-01T11:00:00+08:00', '台北', 'https://www.taiwannews.com.tw/news/6341753', 10, '06月01日 11:00'),
    rangeDay_('NVIDIA GTC Taipei 2026', '科技数码', '2026-06-02', '2026-06-04', '台北', 'https://www.nvidia.com/en-us/events/computex/', 9, '06月02日-06月04日'),
    rangeDay_('COMPUTEX Taipei 2026', '科技数码', '2026-06-02', '2026-06-05', '台北', 'https://www.computextaipei.com.tw/en/news/8F914C77B6AF77A5/info.html?cid=news&cr=5&lt=data', 9, '06月02日-06月05日'),
    rangeDay_('Microsoft Build 2026', '科技数码', '2026-06-02', '2026-06-03', '线上/旧金山', 'https://developer.microsoft.com/en-us/red-shirt-tour/', 8, '06月02日-06月03日'),
    rangeDay_('SNEC PV+ 2026 华为光储新品展示', '科技数码', '2026-06-03', '2026-06-05', '上海', 'https://solar.huawei.com/cn/events/snec2026/', 8, '06月03日-06月05日'),
    rangeDay_('Apple WWDC 2026', '科技数码', '2026-06-09', '2026-06-13', '线上/Apple Park', 'https://www.apple.com.cn/newsroom/2026/05/apple-kicks-off-worldwide-developers-conference-on-june-8/', 9, '06月09日-06月13日'),
    rangeDay_('华为开发者大会 HDC 2026', '科技数码', '2026-06-12', '2026-06-14', '东莞松山湖', 'https://www.ithome.com/0/944/689.htm', 8, '06月12日-06月14日'),
    rangeDay_('MWC Shanghai 2026', '科技数码', '2026-06-24', '2026-06-26', '上海新国际博览中心', 'https://www.mwcshanghai.com/location-venues', 9, '06月24日-06月26日')
  ];
}


function fetchRssEvents_() {
  const events = [];

  getSourceUrls_().forEach(source => {
    try {
      fetchRssItems_(source.url).slice(0, 50).forEach(item => {
        const title = cleanText_(item.title);
        const link = item.link || '';
        const text = cleanText_(`${title} ${item.description || ''}`);
        const score = scoreText_(text);
        const time = parseDateTime_(text);

        if (!time || score.value < CONFIG.minScore) return;

        events.push({
          title,
          category: guessCategory_(text),
          start: time.start,
          end: time.end,
          allDay: time.allDay,
          location: guessLocation_(text),
          url: link,
          confidence: Math.min(10, score.value),
          identifyTime: time.label,
          source: CONFIG.sourceLabel
        });
      });
    } catch (e) {
      Logger.log(`抓取失败：${source.name} ${String(e)}`);
    }
  });

  return events;
}


function getSourceUrls_() {
  const sources = CONFIG.rssSources.map((url, index) => ({ name: `RSS ${index + 1}`, url }));
  CONFIG.queries.forEach((query, index) => {
    sources.push({
      name: `Google News ${index + 1}`,
      url: 'https://news.google.com/rss/search?' + queryString_({
        q: `(${query}) when:30d`,
        hl: 'zh-CN',
        gl: 'CN',
        ceid: 'CN:zh-Hans'
      })
    });
  });
  return sources;
}


function fetchRssItems_(url) {
  const response = UrlFetchApp.fetch(url, {
    muteHttpExceptions: true,
    followRedirects: true,
    headers: { 'User-Agent': 'Mozilla/5.0 LaunchCalendarFeed' }
  });

  const xml = response.getContentText('UTF-8');
  const document = XmlService.parse(xml);
  const root = document.getRootElement();
  const items = [];
  const channel = root.getChild('channel');

  if (channel) {
    channel.getChildren('item').forEach(item => {
      items.push({
        title: childText_(item, 'title'),
        link: childText_(item, 'link'),
        description: childText_(item, 'description')
      });
    });
    return items;
  }

  const ns = root.getNamespace();
  root.getChildren('entry', ns).forEach(entry => {
    items.push({
      title: childTextNs_(entry, 'title', ns),
      link: atomLink_(entry, ns),
      description: childTextNs_(entry, 'summary', ns) || childTextNs_(entry, 'content', ns)
    });
  });

  return items;
}


function scoreText_(text) {
  let value = 0;
  const reasons = [];

  CONFIG.strongWords.forEach(word => {
    if (text.indexOf(word) !== -1) {
      value += 3;
      reasons.push(word);
    }
  });

  CONFIG.productWords.forEach(word => {
    if (text.indexOf(word) !== -1) {
      value += 1;
      reasons.push(word);
    }
  });

  CONFIG.negativeWords.forEach(word => {
    if (text.indexOf(word) !== -1) {
      value -= 4;
      reasons.push(`排除:${word}`);
    }
  });

  return { value, reasons };
}


function parseDateTime_(text) {
  const now = new Date();
  let match;

  match = text.match(/(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日\s*(\d{1,2})[:：](\d{2})/);
  if (match) return timed_(Number(match[1]), Number(match[2]), Number(match[3]), Number(match[4]), Number(match[5]));

  match = text.match(/(\d{1,2})月\s*(\d{1,2})日\s*(\d{1,2})[:：](\d{2})/);
  if (match) return timed_(now.getFullYear(), Number(match[1]), Number(match[2]), Number(match[3]), Number(match[4]));

  match = text.match(/(\d{1,2})月\s*(\d{1,2})日\s*(晚|晚上|今晚|下午)?\s*(\d{1,2})点(?:半)?/);
  if (match) {
    let hour = Number(match[4]);
    const minute = text.indexOf('点半') !== -1 ? 30 : 0;
    if ((match[3] === '晚' || match[3] === '晚上' || match[3] === '今晚' || match[3] === '下午') && hour < 12) hour += 12;
    return timed_(now.getFullYear(), Number(match[1]), Number(match[2]), hour, minute);
  }

  match = text.match(/明天\s*(\d{1,2})[:：](\d{2})|明晚\s*(\d{1,2})[:：](\d{2})/);
  if (match) {
    const d = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    const hour = Number(match[1] || match[3]);
    const minute = Number(match[2] || match[4]);
    return timed_(d.getFullYear(), d.getMonth() + 1, d.getDate(), hour, minute);
  }

  match = text.match(/今晚\s*(\d{1,2})[:：](\d{2})/);
  if (match) return timed_(now.getFullYear(), now.getMonth() + 1, now.getDate(), Number(match[1]), Number(match[2]));

  match = text.match(/(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日/);
  if (match) return allDayTime_(Number(match[1]), Number(match[2]), Number(match[3]));

  match = text.match(/(\d{1,2})月\s*(\d{1,2})日/);
  if (match) return allDayTime_(now.getFullYear(), Number(match[1]), Number(match[2]));

  return null;
}


function timed_(year, month, day, hour, minute) {
  const start = new Date(`${year}-${pad_(month)}-${pad_(day)}T${pad_(hour)}:${pad_(minute)}:00+08:00`);
  const end = new Date(start.getTime() + CONFIG.defaultDurationMinutes * 60 * 1000);
  return {
    start,
    end,
    allDay: false,
    label: Utilities.formatDate(start, CONFIG.timezone, 'MM月dd日 HH:mm')
  };
}


function allDayTime_(year, month, day) {
  const start = new Date(`${year}-${pad_(month)}-${pad_(day)}T00:00:00+08:00`);
  const end = new Date(start.getTime() + 24 * 60 * 60 * 1000);
  return {
    start,
    end,
    allDay: true,
    label: Utilities.formatDate(start, CONFIG.timezone, 'MM月dd日')
  };
}


function event_(title, category, isoStart, location, url, confidence, identifyTime) {
  const start = new Date(isoStart);
  return {
    title,
    category,
    start,
    end: new Date(start.getTime() + CONFIG.defaultDurationMinutes * 60 * 1000),
    allDay: false,
    location,
    url,
    confidence,
    identifyTime,
    source: CONFIG.sourceLabel
  };
}


function allDay_(title, category, dateText, location, url, confidence, identifyTime) {
  const start = new Date(`${dateText}T00:00:00+08:00`);
  return {
    title,
    category,
    start,
    end: new Date(start.getTime() + 24 * 60 * 60 * 1000),
    allDay: true,
    location,
    url,
    confidence,
    identifyTime,
    source: CONFIG.sourceLabel
  };
}


function rangeDay_(title, category, startText, endInclusiveText, location, url, confidence, identifyTime) {
  const start = new Date(`${startText}T00:00:00+08:00`);
  const endInclusive = new Date(`${endInclusiveText}T00:00:00+08:00`);
  const end = new Date(endInclusive.getTime() + 24 * 60 * 60 * 1000);
  return {
    title,
    category,
    start,
    end,
    allDay: true,
    location,
    url,
    confidence,
    identifyTime,
    source: CONFIG.sourceLabel
  };
}


function dedupeEvents_(events) {
  const seen = {};
  return events.filter(event => {
    const key = normalize_(event.title) + '|' + Utilities.formatDate(event.start, CONFIG.timezone, 'yyyyMMddHHmm');
    if (seen[key]) return false;
    seen[key] = true;
    return true;
  });
}


function isInWindow_(event) {
  const now = new Date();
  const min = new Date(now.getTime() - CONFIG.lookBackHours * 60 * 60 * 1000);
  const max = new Date(now.getTime() + CONFIG.lookAheadDays * 24 * 60 * 60 * 1000);
  return event.end >= min && event.start <= max;
}


function buildIcs_(events) {
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Launch Calendar Feed//@weixun-kkkkk//ZH-CN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    `X-WR-CALNAME:${escapeIcs_(CONFIG.calendarName)}`,
    `X-WR-TIMEZONE:${CONFIG.timezone}`,
    'REFRESH-INTERVAL;VALUE=DURATION:PT6H',
    'X-PUBLISHED-TTL:PT6H'
  ];

  events.forEach(event => {
    lines.push('BEGIN:VEVENT');
    lines.push(`UID:${makeUid_(event)}`);
    lines.push(`DTSTAMP:${formatUtc_(new Date())}`);
    lines.push(`SUMMARY:${escapeIcs_(`[${event.category}] ${event.title}`)}`);

    if (event.allDay) {
      lines.push(`DTSTART;VALUE=DATE:${formatDate_(event.start)}`);
      lines.push(`DTEND;VALUE=DATE:${formatDate_(event.end)}`);
    } else {
      lines.push(`DTSTART:${formatUtc_(event.start)}`);
      lines.push(`DTEND:${formatUtc_(event.end)}`);
    }

    lines.push(`LOCATION:${escapeIcs_(event.location || '线上')}`);
    lines.push(`DESCRIPTION:${escapeIcs_(description_(event))}`);
    lines.push(`URL:${escapeIcs_(event.url || '')}`);
    lines.push(`CATEGORIES:${escapeIcs_(event.category)}`);
    lines.push('BEGIN:VALARM');
    lines.push('TRIGGER:-PT30M');
    lines.push('ACTION:DISPLAY');
    lines.push(`DESCRIPTION:${escapeIcs_(event.title)}`);
    lines.push('END:VALARM');
    lines.push('END:VEVENT');
  });

  lines.push('END:VCALENDAR');
  return lines.map(foldLine_).join('\r\n') + '\r\n';
}


function description_(event) {
  return [
    `来源：${CONFIG.sourceLabel}`,
    `链接：${event.url || ''}`,
    `识别时间：${event.identifyTime || ''}`,
    `可信度分数：${event.confidence || ''}`,
    '',
    event.url || ''
  ].join('\n');
}


function readUploadedIcs_() {
  const props = PropertiesService.getScriptProperties();
  const count = Number(props.getProperty('UPLOADED_ICS_CHUNK_COUNT') || 0);
  if (!count) return '';

  const chunks = [];
  for (let i = 0; i < count; i++) {
    const chunk = props.getProperty(`UPLOADED_ICS_CHUNK_${i}`);
    if (chunk === null) return '';
    chunks.push(chunk);
  }

  return chunks.join('');
}


function storeUploadedIcs_(ics) {
  deleteUploadedIcs_();

  const props = PropertiesService.getScriptProperties();
  const chunks = [];
  for (let i = 0; i < ics.length; i += CONFIG.uploadChunkSize) {
    chunks.push(ics.slice(i, i + CONFIG.uploadChunkSize));
  }

  const values = {
    UPLOADED_ICS_CHUNK_COUNT: String(chunks.length),
    UPLOADED_ICS_UPDATED_AT: new Date().toISOString(),
    UPDATED_AT: new Date().toISOString(),
    EVENT_COUNT: String(countEventsInIcs_(ics)),
    FEED_MODE: 'uploaded'
  };

  chunks.forEach((chunk, index) => {
    values[`UPLOADED_ICS_CHUNK_${index}`] = chunk;
  });

  props.setProperties(values);
}


function deleteUploadedIcs_() {
  const props = PropertiesService.getScriptProperties();
  const count = Number(props.getProperty('UPLOADED_ICS_CHUNK_COUNT') || 0);
  for (let i = 0; i < count; i++) {
    props.deleteProperty(`UPLOADED_ICS_CHUNK_${i}`);
  }
  props.deleteProperty('UPLOADED_ICS_CHUNK_COUNT');
  props.deleteProperty('UPLOADED_ICS_UPDATED_AT');
}


function countEventsInIcs_(ics) {
  const matches = String(ics || '').match(/BEGIN:VEVENT/g);
  return matches ? matches.length : 0;
}


function jsonOutput_(value) {
  return ContentService
    .createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}


function makeUid_(event) {
  const raw = `${event.title}|${event.url}|${event.start.toISOString()}`;
  return Utilities.base64EncodeWebSafe(raw).replace(/=+$/g, '').slice(0, 48) + '@launch-calendar-feed';
}


function formatUtc_(date) {
  return Utilities.formatDate(date, 'UTC', "yyyyMMdd'T'HHmmss'Z'");
}


function formatDate_(date) {
  return Utilities.formatDate(date, CONFIG.timezone, 'yyyyMMdd');
}


function escapeIcs_(value) {
  return String(value || '')
    .replace(/\\/g, '\\\\')
    .replace(/\n/g, '\\n')
    .replace(/,/g, '\\,')
    .replace(/;/g, '\\;');
}


function foldLine_(line) {
  const limit = 72;
  let output = '';
  let rest = String(line);
  while (rest.length > limit) {
    output += rest.slice(0, limit) + '\r\n ';
    rest = rest.slice(limit);
  }
  return output + rest;
}


function guessCategory_(text) {
  if (/新能源|新车|汽车|智驾|鸿蒙智行|华为车BU|华为乾崑|乾崑|引望|小鹏|理想|蔚来|极氪|比亚迪|问界|智界|享界|尊界|尚界|启境|奕境|华境|五菱|极狐|红旗|北京越野|吉利银河|岚图|一汽悦意/.test(text)) return '新能源汽车';
  if (/手机|新机|旗舰|折叠屏|小米|华为|荣耀|vivo|iQOO|OPPO|一加|realme|三星|苹果|nova|Reno/.test(text)) return '手机新品';
  return '科技数码';
}


function guessLocation_(text) {
  const cities = ['北京', '上海', '深圳', '广州', '杭州', '成都', '厦门', '武汉', '台北', '东莞', '威海', '线上'];
  for (let i = 0; i < cities.length; i++) {
    if (text.indexOf(cities[i]) !== -1) return cities[i];
  }
  return '线上';
}


function childText_(element, name) {
  const child = element.getChild(name);
  return child ? child.getText() : '';
}


function childTextNs_(element, name, ns) {
  const child = element.getChild(name, ns);
  return child ? child.getText() : '';
}


function atomLink_(entry, ns) {
  const links = entry.getChildren('link', ns);
  for (let i = 0; i < links.length; i++) {
    const href = links[i].getAttribute('href');
    if (href) return href.getValue();
  }
  return '';
}


function cleanText_(text) {
  return String(text || '')
    .replace(/<!\[CDATA\[/g, '')
    .replace(/\]\]>/g, '')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .trim();
}


function normalize_(text) {
  return String(text || '').toLowerCase().replace(/\s+/g, '').replace(/[^\w\u4e00-\u9fa5]/g, '');
}


function queryString_(params) {
  return Object.keys(params)
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&');
}


function pad_(number) {
  return String(number).padStart(2, '0');
}
