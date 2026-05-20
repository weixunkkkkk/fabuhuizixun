/***************
 * 科技新品发布会自动抓取 + 同步 Google 日历
 * 适合：手机发布会 / 新能源汽车发布会 / 数码科技发布会
 *
 * 用法：
 * 1. 把本文件放进 Google Apps Script 的 Code.gs。
 * 2. 先运行 testCreateEvent，确认日历授权正常。
 * 3. 再运行 syncLaunchEvents。
 * 4. 想每天自动跑，运行 installDailyTrigger。
 ***************/

const CONFIG = {
  calendarName: '科技新品发布会日程',
  spreadsheetName: '科技新品发布会同步记录',
  timezone: 'Asia/Shanghai',
  defaultDurationMinutes: 90,
  futureDays: 60,
  includePastHours: 24,
  maxItemsPerSource: 50,
  minScoreToSync: 9,
  minScoreToLogCandidate: 4,
  createDateOnlyEvents: true,
  defaultDateOnlyTitleSuffix: '（具体时间待定）',
  dailyTriggerHour: 9,

  rssSources: [
    { name: 'IT之家', url: 'https://www.ithome.com/rss/' },
    { name: '36氪快讯', url: 'https://36kr.com/feed-newsflash' },
    { name: '36氪', url: 'https://36kr.com/feed' },
    { name: '极客公园', url: 'https://www.geekpark.net/rss' }
  ],

  // Google News RSS 是兜底增广，通常比单站 RSS 更容易抓到“定档/时间/直播”类新闻。
  googleNewsLookbackDays: 14,
  googleNewsQueries: [
    '手机 新品 发布会 时间 OR 新机 发布会 直播 OR 手机 发布会 定档',
    '新能源汽车 发布会 时间 OR 新车 发布会 直播 OR 智能汽车 发布会 定档',
    '科技 数码 发布会 时间 OR 新品 发布会 直播 OR AI 硬件 发布会',
    '华为 新品 发布会 OR 华为 nova Mate Pura 发布会 OR 华为开发者大会 HDC OR 鸿蒙 HarmonyOS 发布会',
    '鸿蒙智行 发布会 OR 华为车BU 发布会 OR 华为乾崑 发布会 OR 问界 智界 享界 尊界 尚界 启境 奕境 华境 发布会',
    '两轮电动车 发布会 OR 电动自行车 新国标 发布 OR 九号 爱玛 雅迪 春风动力 发布会 上市 预购',
    '耳机 NAS 私有云 显卡 机器人 拍卖 音频芯片 发布会 开售 OR 索尼 绿联 安克 砺算 西昇 发布'
  ],

  eventSignals: [
    '发布会', '新品发布', '新品发布会', '发布', '上市发布', '正式上市',
    '开发者大会', '技术沟通会', '影像沟通会', '全球发布',
    '定档', '官宣', '邀请函', '直播', '开启预售', '开启预约'
  ],

  productSignals: [
    '手机', '新机', '旗舰', '折叠屏', '小折叠', '影像', 'AI', '系统',
    '耳机', '平板', '手表', '智能穿戴', '充电器', '充电宝',
    '新能源汽车', '新车', '智驾', '智能驾驶', '预售',
    '小米', '华为', '荣耀', 'vivo', 'iQOO', 'OPPO', '一加',
    'realme', '魅族', '努比亚', '红魔', '三星', '苹果',
    '小鹏', '理想', '蔚来', '极氪', '零跑', '比亚迪', '鸿蒙智行',
    '华为乾崑', '乾崑智驾', '乾崑ADS', '引望',
    '问界', '智界', '享界', '尊界', '尚界',
    '启境', '奕境', '华境', '两轮电动车', '电动自行车',
    '新国标', '九号', '爱玛', '雅迪', '春风动力',
    '红旗', '北京越野', '吉利银河', '岚图', '一汽悦意',
    '阿维塔', '深蓝', '安克', '酷态科', '绿联', '大疆',
    '影石', '徕卡', '索尼', 'NAS', '私有云', '显卡',
    '音频芯片', '机器人', '仿真机器人', 'SpaceX', 'AMD',
    '高通', '瑞莎'
  ],

  negativeSignals: [
    '评测', '体验', '开箱', '降价', '补贴', '销量', '财报',
    '招聘', '教程', '维修', '二手', '拆解', '渲染图',
    '回顾', '汇总', '一图看懂', '发布会后', '发布会结束'
  ],

  hardNegativeSignals: [
    '爆料称', '疑似', '曝光', '渲染图曝光', '谍照'
  ]
};


function syncLaunchEvents() {
  const calendar = getOrCreateCalendar_();
  const syncedSheet = getOrCreateSheet_('已同步发布会', getSyncedHeaders_());
  const logSheet = getOrCreateSheet_('同步日志', getLogHeaders_());
  const candidateSheet = resetSheet_('候选池', getCandidateHeaders_());
  const existing = loadExistingEvents_(syncedSheet);

  let addedCount = 0;
  let skippedCount = 0;
  let candidateCount = 0;
  const sources = getAllSources_();

  sources.forEach(source => {
    try {
      const items = fetchRssItems_(source.url, source.name).slice(0, CONFIG.maxItemsPerSource);

      items.forEach(item => {
        const normalized = normalizeItem_(item, source);
        const scoreResult = scoreItem_(normalized.text);
        const dateResult = extractDateTime_(normalized.text, normalized.pubDate);
        const decision = decideItem_(normalized, scoreResult, dateResult, existing);

        if (scoreResult.score >= CONFIG.minScoreToLogCandidate || dateResult) {
          candidateSheet.appendRow([
            new Date(),
            source.name,
            scoreResult.score,
            decision.status,
            decision.reason,
            dateResult ? formatEventTime_(dateResult) : '',
            normalized.title,
            normalized.link
          ]);
          candidateCount++;
        }

        if (!decision.shouldSync) {
          skippedCount++;
          return;
        }

        const eventTitle = buildEventTitle_(normalized.title, dateResult);
        const endTime = new Date(dateResult.start.getTime() + CONFIG.defaultDurationMinutes * 60 * 1000);
        let calendarEvent;

        if (dateResult.allDay) {
          calendarEvent = calendar.createAllDayEvent(eventTitle, dateResult.start, {
            description: buildDescription_(normalized, source, scoreResult, dateResult),
            location: extractLocation_(normalized.text)
          });
        } else {
          calendarEvent = calendar.createEvent(eventTitle, dateResult.start, endTime, {
            description: buildDescription_(normalized, source, scoreResult, dateResult),
            location: extractLocation_(normalized.text)
          });
        }

        syncedSheet.appendRow([
          new Date(),
          decision.uniqueKey,
          eventTitle,
          dateResult.start,
          dateResult.allDay ? '是' : '否',
          normalized.link,
          source.name,
          scoreResult.score,
          calendarEvent.getId(),
          '已同步'
        ]);

        existing.keys[decision.uniqueKey] = true;
        existing.fingerprints[decision.fingerprint] = true;
        addedCount++;
      });

    } catch (e) {
      logSheet.appendRow([new Date(), source.name, source.url, '抓取失败', String(e)]);
    }
  });

  logSheet.appendRow([
    new Date(),
    '全部来源',
    '',
    `完成：新增 ${addedCount} 条，跳过 ${skippedCount} 条，候选 ${candidateCount} 条`,
    ''
  ]);
}


function previewCandidatesOnly() {
  const candidateSheet = resetSheet_('候选池', getCandidateHeaders_());
  getAllSources_().forEach(source => {
    try {
      fetchRssItems_(source.url, source.name).slice(0, CONFIG.maxItemsPerSource).forEach(item => {
        const normalized = normalizeItem_(item, source);
        const scoreResult = scoreItem_(normalized.text);
        const dateResult = extractDateTime_(normalized.text, normalized.pubDate);
        if (scoreResult.score >= CONFIG.minScoreToLogCandidate || dateResult) {
          candidateSheet.appendRow([
            new Date(),
            source.name,
            scoreResult.score,
            dateResult ? '可识别时间' : '仅候选',
            scoreResult.reasons.join(' / '),
            dateResult ? formatEventTime_(dateResult) : '',
            normalized.title,
            normalized.link
          ]);
        }
      });
    } catch (e) {
      candidateSheet.appendRow([new Date(), source.name, 0, '抓取失败', String(e), '', '', source.url]);
    }
  });
}


function installDailyTrigger() {
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === 'syncLaunchEvents') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  ScriptApp.newTrigger('syncLaunchEvents')
    .timeBased()
    .everyDays(1)
    .atHour(CONFIG.dailyTriggerHour)
    .inTimezone(CONFIG.timezone)
    .create();
}


function testCreateEvent() {
  const calendar = getOrCreateCalendar_();
  const start = new Date();
  start.setHours(start.getHours() + 1);
  const end = new Date(start.getTime() + 60 * 60 * 1000);

  calendar.createEvent('测试：科技新品发布会日程同步', start, end, {
    description: '如果你能在 Google 日历看到这个事件，说明授权和日历创建成功。',
    location: '线上'
  });
}


function testExtractDateTime() {
  [
    '小米新品发布会定档 5月20日 19:00 线上直播',
    '荣耀新机发布会 5月21日晚7点举行',
    '新能源汽车发布会明晚8点开启',
    '科技开发者大会本周五 10:30 开幕',
    '新品发布会 6月1日 具体时间待定'
  ].forEach(text => {
    const result = extractDateTime_(text, new Date());
    Logger.log(`${text} => ${result ? formatEventTime_(result) : '未识别'}`);
  });
}


function getAllSources_() {
  const sources = CONFIG.rssSources.slice();
  CONFIG.googleNewsQueries.forEach((query, index) => {
    sources.push({
      name: `Google News ${index + 1}`,
      url: buildGoogleNewsRssUrl_(query)
    });
  });
  return sources;
}


function buildGoogleNewsRssUrl_(query) {
  const q = `(${query}) when:${CONFIG.googleNewsLookbackDays}d`;
  return 'https://news.google.com/rss/search?' + toQueryString_({
    q,
    hl: 'zh-CN',
    gl: 'CN',
    ceid: 'CN:zh-Hans'
  });
}


function fetchRssItems_(url, sourceName) {
  const response = UrlFetchApp.fetch(url, {
    muteHttpExceptions: true,
    followRedirects: true,
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; LaunchCalendarBot/2.0)'
    }
  });

  const code = response.getResponseCode();
  if (code < 200 || code >= 300) {
    throw new Error(`HTTP ${code}`);
  }

  const xml = sanitizeXml_(response.getContentText('UTF-8'));
  const document = XmlService.parse(xml);
  const root = document.getRootElement();
  const items = [];

  const channel = root.getChild('channel');
  if (channel) {
    channel.getChildren('item').forEach(item => {
      items.push({
        title: getChildText_(item, 'title'),
        link: getChildText_(item, 'link'),
        description: getChildText_(item, 'description'),
        pubDate: getChildText_(item, 'pubDate'),
        sourceName
      });
    });
    return items;
  }

  const ns = root.getNamespace();
  root.getChildren('entry', ns).forEach(entry => {
    items.push({
      title: getChildTextNs_(entry, 'title', ns),
      link: getAtomLink_(entry, ns),
      description: getChildTextNs_(entry, 'summary', ns) || getChildTextNs_(entry, 'content', ns),
      pubDate: getChildTextNs_(entry, 'updated', ns) || getChildTextNs_(entry, 'published', ns),
      sourceName
    });
  });

  return items;
}


function normalizeItem_(item, source) {
  const title = cleanText_(item.title || '');
  const description = cleanText_(item.description || '');
  return {
    title,
    link: item.link || '',
    description,
    pubDate: parseDateSafe_(item.pubDate),
    sourceName: source.name,
    text: cleanText_(`${title} ${description}`)
  };
}


function scoreItem_(text) {
  let score = 0;
  const reasons = [];

  CONFIG.eventSignals.forEach(k => {
    if (text.includes(k)) {
      score += k === '发布会' ? 5 : 3;
      reasons.push(`事件:${k}`);
    }
  });

  CONFIG.productSignals.forEach(k => {
    if (text.includes(k)) {
      score += 1;
      reasons.push(`产品:${k}`);
    }
  });

  CONFIG.negativeSignals.forEach(k => {
    if (text.includes(k)) {
      score -= 3;
      reasons.push(`扣分:${k}`);
    }
  });

  CONFIG.hardNegativeSignals.forEach(k => {
    if (text.includes(k)) {
      score -= 8;
      reasons.push(`强扣:${k}`);
    }
  });

  if (/[0-9一二三四五六七八九十]+月/.test(text) || /(今天|今晚|明天|明晚|本周|下周)/.test(text)) {
    score += 2;
    reasons.push('含时间表达');
  }

  return { score, reasons };
}


function decideItem_(item, scoreResult, dateResult, existing) {
  if (scoreResult.score < CONFIG.minScoreToSync) {
    return reject_('分数不足', scoreResult);
  }

  if (!dateResult) {
    return reject_('未识别到日期时间', scoreResult);
  }

  if (!CONFIG.createDateOnlyEvents && dateResult.allDay) {
    return reject_('仅识别到日期，未识别具体时间', scoreResult);
  }

  if (!withinWindow_(dateResult.start)) {
    return reject_('不在同步时间窗口内', scoreResult);
  }

  const uniqueKey = makeUniqueKey_(item.title, item.link, dateResult.start);
  const fingerprint = makeFingerprint_(item.title, dateResult.start);

  if (existing.keys[uniqueKey] || existing.fingerprints[fingerprint]) {
    return {
      shouldSync: false,
      status: '跳过',
      reason: '已同步/疑似重复',
      uniqueKey,
      fingerprint
    };
  }

  return {
    shouldSync: true,
    status: '将同步',
    reason: scoreResult.reasons.join(' / '),
    uniqueKey,
    fingerprint
  };
}


function reject_(reason, scoreResult) {
  return {
    shouldSync: false,
    status: '跳过',
    reason: `${reason}；${scoreResult.reasons.join(' / ')}`
  };
}


function extractDateTime_(rawText, pubDate) {
  const text = normalizeDateText_(rawText);
  const now = new Date();
  const anchor = pubDate || now;
  const explicit = extractExplicitDate_(text, anchor);
  if (explicit) return explicit;

  const relative = extractRelativeDate_(text, anchor);
  if (relative) return relative;

  const weekday = extractWeekdayDate_(text, anchor);
  if (weekday) return weekday;

  return null;
}


function extractExplicitDate_(text, anchor) {
  const patterns = [
    { regex: /(20\d{2})年(\d{1,2})月(\d{1,2})日?/g, yearIndex: 1, monthIndex: 2, dayIndex: 3 },
    { regex: /(\d{1,2})月(\d{1,2})日/g, yearIndex: 0, monthIndex: 1, dayIndex: 2 },
    { regex: /(^|[^\d])(\d{1,2})[\/.-](\d{1,2})(?!\d)/g, yearIndex: 0, monthIndex: 2, dayIndex: 3 }
  ];

  for (let p = 0; p < patterns.length; p++) {
    const pattern = patterns[p].regex;
    let match;
    while ((match = pattern.exec(text)) !== null) {
      const month = Number(match[patterns[p].monthIndex]);
      const day = Number(match[patterns[p].dayIndex]);
      const year = patterns[p].yearIndex ? Number(match[patterns[p].yearIndex]) : inferYear_(month, day, anchor);
      if (!isValidDatePart_(year, month, day)) continue;

      const after = text.slice(match.index + match[0].length, match.index + match[0].length + 40);
      const before = text.slice(Math.max(0, match.index - 16), match.index);
      const time = extractTime_(after) || extractTime_(before);
      const date = new Date(year, month - 1, day);

      if (!time) {
        return {
          start: date,
          allDay: true,
          matchedText: match[0]
        };
      }

      date.setHours(time.hour, time.minute, 0, 0);
      return {
        start: date,
        allDay: false,
        matchedText: `${match[0]}${time.raw}`
      };
    }
  }

  return null;
}


function extractRelativeDate_(text, anchor) {
  const mappings = [
    { pattern: /(今天|今日|今晚)/, offset: 0 },
    { pattern: /(明天|明日|明晚)/, offset: 1 },
    { pattern: /(后天|后日)/, offset: 2 }
  ];

  for (let i = 0; i < mappings.length; i++) {
    const match = text.match(mappings[i].pattern);
    if (!match) continue;

    const date = new Date(anchor);
    date.setDate(date.getDate() + mappings[i].offset);
    date.setHours(0, 0, 0, 0);

    const windowText = text.slice(match.index, match.index + 40);
    const time = extractTime_(windowText);
    if (!time) {
      return { start: date, allDay: true, matchedText: match[0] };
    }

    date.setHours(time.hour, time.minute, 0, 0);
    return { start: date, allDay: false, matchedText: `${match[0]}${time.raw}` };
  }

  return null;
}


function extractWeekdayDate_(text, anchor) {
  const match = text.match(/(本周|下周)([一二三四五六日天])/);
  if (!match) return null;

  const weekdayMap = { 一: 1, 二: 2, 三: 3, 四: 4, 五: 5, 六: 6, 日: 0, 天: 0 };
  const target = weekdayMap[match[2]];
  const date = new Date(anchor);
  const current = date.getDay();
  let offset = target - current + (match[1] === '下周' ? 7 : 0);
  if (offset < 0 && match[1] === '本周') offset += 7;
  date.setDate(date.getDate() + offset);
  date.setHours(0, 0, 0, 0);

  const windowText = text.slice(match.index, match.index + 40);
  const time = extractTime_(windowText);
  if (!time) {
    return { start: date, allDay: true, matchedText: match[0] };
  }

  date.setHours(time.hour, time.minute, 0, 0);
  return { start: date, allDay: false, matchedText: `${match[0]}${time.raw}` };
}


function extractTime_(text) {
  const match = text.match(/(凌晨|早上|上午|中午|下午|晚上|晚间|今晚|明晚|晚)?\s*(\d{1,2})\s*(?:[:：点时])\s*(\d{1,2})?\s*分?/);
  if (!match) return null;

  let hour = Number(match[2]);
  const minute = match[3] ? Number(match[3]) : 0;
  if (hour > 24 || minute > 59) return null;

  const period = match[1] || '';
  if (['下午', '晚上', '晚间', '今晚', '明晚', '晚'].includes(period) && hour < 12) {
    hour += 12;
  }
  if (period === '中午' && hour < 11) {
    hour += 12;
  }
  if (hour === 24) hour = 0;

  return { hour, minute, raw: match[0] };
}


function withinWindow_(date) {
  const now = new Date();
  const min = new Date(now.getTime() - CONFIG.includePastHours * 60 * 60 * 1000);
  const max = new Date(now.getTime() + CONFIG.futureDays * 24 * 60 * 60 * 1000);
  return date >= min && date <= max;
}


function buildEventTitle_(title, dateResult) {
  if (dateResult.allDay && !title.includes('待定')) {
    return `${title}${CONFIG.defaultDateOnlyTitleSuffix}`;
  }
  return title;
}


function buildDescription_(item, source, scoreResult, dateResult) {
  return [
    `自动抓取来源：${source.name}`,
    `原文链接：${item.link}`,
    `识别时间：${formatEventTime_(dateResult)}`,
    `筛选分数：${scoreResult.score}`,
    `命中原因：${scoreResult.reasons.join(' / ')}`,
    '',
    `标题：${item.title}`,
    '',
    item.description
  ].filter(Boolean).join('\n');
}


function extractLocation_(text) {
  if (/(线上|直播|在线|云发布|官网)/.test(text)) return '线上';
  const match = text.match(/(北京|上海|广州|深圳|成都|杭州|武汉|南京|重庆|西安|苏州|合肥|长沙|厦门|青岛|郑州|珠海|宁波|天津|香港|澳门|台北|东京|首尔|新加坡|纽约|洛杉矶|伦敦|巴黎|柏林)/);
  return match ? match[1] : '线上 / 具体地点待定';
}


function getOrCreateCalendar_() {
  const calendars = CalendarApp.getCalendarsByName(CONFIG.calendarName);
  if (calendars.length > 0) return calendars[0];
  return CalendarApp.createCalendar(CONFIG.calendarName, { timeZone: CONFIG.timezone });
}


function getSpreadsheet_() {
  const active = SpreadsheetApp.getActiveSpreadsheet();
  if (active) return active;

  const props = PropertiesService.getScriptProperties();
  const savedId = props.getProperty('SPREADSHEET_ID');
  if (savedId) return SpreadsheetApp.openById(savedId);

  const ss = SpreadsheetApp.create(CONFIG.spreadsheetName);
  props.setProperty('SPREADSHEET_ID', ss.getId());
  return ss;
}


function getOrCreateSheet_(sheetName, headers) {
  const ss = getSpreadsheet_();
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) sheet = ss.insertSheet(sheetName);
  ensureHeaders_(sheet, headers);
  return sheet;
}


function resetSheet_(sheetName, headers) {
  const sheet = getOrCreateSheet_(sheetName, headers);
  sheet.clearContents();
  sheet.appendRow(headers);
  sheet.setFrozenRows(1);
  return sheet;
}


function ensureHeaders_(sheet, headers) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    sheet.setFrozenRows(1);
    return;
  }
  const firstRow = sheet.getRange(1, 1, 1, headers.length).getValues()[0];
  const same = headers.every((header, index) => firstRow[index] === header);
  if (!same) {
    sheet.insertRowBefore(1);
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.setFrozenRows(1);
  }
}


function loadExistingEvents_(sheet) {
  const keys = {};
  const fingerprints = {};
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return { keys, fingerprints };

  const rows = sheet.getRange(2, 2, lastRow - 1, 3).getValues();
  rows.forEach(row => {
    if (row[0]) keys[row[0]] = true;
    if (row[1] && row[2]) fingerprints[makeFingerprint_(row[1], new Date(row[2]))] = true;
  });
  return { keys, fingerprints };
}


function makeUniqueKey_(title, link, eventTime) {
  return sha256Hex_(`${normalizeTitle_(title)}|${link}|${dateKey_(eventTime)}`).slice(0, 40);
}


function makeFingerprint_(title, eventTime) {
  return sha256Hex_(`${normalizeTitle_(title).slice(0, 28)}|${dateKey_(eventTime)}`).slice(0, 32);
}


function normalizeTitle_(title) {
  return cleanText_(title)
    .replace(/(正式)?(官宣|定档|发布会|新品发布会|新品发布|全球发布|上市发布|开启预售|开启预约|具体时间待定)/g, '')
    .replace(/[^\w\u4e00-\u9fa5]/g, '')
    .toLowerCase();
}


function dateKey_(date) {
  return Utilities.formatDate(date, CONFIG.timezone, 'yyyy-MM-dd');
}


function sha256Hex_(value) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, value, Utilities.Charset.UTF_8)
    .map(byte => {
      const v = byte < 0 ? byte + 256 : byte;
      return ('0' + v.toString(16)).slice(-2);
    })
    .join('');
}


function getChildText_(element, name) {
  const child = element.getChild(name);
  return child ? child.getText() : '';
}


function getChildTextNs_(element, name, ns) {
  const child = element.getChild(name, ns);
  return child ? child.getText() : '';
}


function getAtomLink_(entry, ns) {
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
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}


function normalizeDateText_(text) {
  return cleanText_(text)
    .replace(/号/g, '日')
    .replace(/：/g, ':')
    .replace(/\s+/g, '');
}


function sanitizeXml_(xml) {
  return String(xml || '').replace(/[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]/g, '');
}


function parseDateSafe_(value) {
  if (!value) return null;
  const date = new Date(value);
  return isNaN(date.getTime()) ? null : date;
}


function inferYear_(month, day, anchor) {
  const year = anchor.getFullYear();
  const candidate = new Date(year, month - 1, day);
  const now = new Date();
  if (candidate.getTime() < now.getTime() - 30 * 24 * 60 * 60 * 1000) {
    return year + 1;
  }
  return year;
}


function isValidDatePart_(year, month, day) {
  if (year < 2020 || month < 1 || month > 12 || day < 1 || day > 31) return false;
  const date = new Date(year, month - 1, day);
  return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
}


function formatEventTime_(dateResult) {
  const dateText = Utilities.formatDate(dateResult.start, CONFIG.timezone, 'yyyy-MM-dd');
  if (dateResult.allDay) return `${dateText} 全天/时间待定`;
  return Utilities.formatDate(dateResult.start, CONFIG.timezone, 'yyyy-MM-dd HH:mm');
}


function toQueryString_(params) {
  return Object.keys(params)
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&');
}


function getSyncedHeaders_() {
  return ['抓取时间', '唯一ID', '标题', '发布时间', '全天/待定', '原文链接', '来源', '分数', 'Google事件ID', '状态'];
}


function getLogHeaders_() {
  return ['时间', '来源', 'URL', '状态', '备注'];
}


function getCandidateHeaders_() {
  return ['时间', '来源', '分数', '状态', '原因', '识别时间', '标题', '原文链接'];
}
