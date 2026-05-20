/***************
 * 最简单版：Google 表格抓取发布会 + 同步 Google 日历
 *
 * 放到 Google 表格 -> 扩展程序 -> Apps Script -> Code.gs
 * 第一次先运行 testCreateEvent 授权，再运行 syncLaunchEvents。
 ***************/

const CONFIG = {
  calendarName: '科技新品发布会日程',
  timezone: 'Asia/Shanghai',
  defaultDurationMinutes: 90,
  lookAheadDays: 60,
  lookBackHours: 24,
  minScore: 6,
  dailyHour: 9,

  queries: [
    '手机 新品 发布会 时间 新机 直播 定档',
    '新能源汽车 新车 发布会 直播 定档 上市',
    '科技 数码 新品 发布会 AI 硬件 开发者大会',
    '华为 新品 发布会 nova Mate Pura 鸿蒙 HarmonyOS HDC',
    '鸿蒙智行 华为车BU 华为乾崑 问界 智界 享界 尊界 尚界 启境 奕境 华境 发布会',
    '两轮电动车 电动自行车 新国标 九号 爱玛 雅迪 春风动力 发布会 上市 预购',
    '耳机 NAS 私有云 显卡 机器人 拍卖 音频芯片 索尼 绿联 安克 砺算 西昇 发布会 开售'
  ],

  extraRss: [
    'https://www.ithome.com/rss/'
  ],

  strongWords: [
    '发布会', '新品发布', '上市发布', '正式上市', '开发者大会',
    '技术沟通会', '影像沟通会', '全球发布', '定档', '官宣',
    '邀请函', '直播', '开启预售', '开启预约'
  ],

  productWords: [
    '手机', '新机', '旗舰', '折叠屏', '影像', 'AI', '系统',
    '耳机', '平板', '手表', '智能穿戴', '新能源汽车', '新车',
    '智驾', '智能驾驶', '小米', '华为', '荣耀', 'vivo', 'iQOO',
    'OPPO', '一加', 'realme', '魅族', '三星', '苹果', '小鹏',
    '理想', '蔚来', '极氪', '比亚迪', '鸿蒙智行', '华为乾崑',
    '乾崑智驾', '乾崑ADS', '引望', '问界', '智界', '享界',
    '尊界', '尚界', '启境', '奕境', '华境', '两轮电动车',
    '电动自行车', '新国标', '九号', '爱玛', '雅迪', '春风动力',
    '红旗', '北京越野', '吉利银河', '岚图', '一汽悦意',
    '安克', '绿联', '索尼', 'NAS', '私有云', '显卡', '音频芯片',
    '机器人', '仿真机器人', 'SpaceX', 'AMD', '高通', '瑞莎',
    '大疆', '影石'
  ],

  negativeWords: [
    '评测', '体验', '开箱', '降价', '销量', '财报', '招聘',
    '教程', '维修', '二手', '拆解', '渲染图', '爆料称',
    '疑似', '曝光', '回顾', '汇总', '一图看懂'
  ]
};


function syncLaunchEvents() {
  const calendar = getOrCreateCalendar_();
  const syncedSheet = getSheet_('已同步', ['同步时间', '唯一ID', '标题', '时间', '地点', '来源', '链接', '日历事件ID']);
  const candidateSheet = resetSheet_('候选池', ['抓取时间', '分数', '状态', '识别时间', '标题', '来源', '链接', '命中原因']);
  const logSheet = getSheet_('运行日志', ['时间', '状态', '备注']);
  const existingIds = loadExistingIds_(syncedSheet);

  let added = 0;
  let skipped = 0;
  let candidates = 0;

  getSources_().forEach(source => {
    try {
      const items = fetchRss_(source.url).slice(0, 60);

      items.forEach(item => {
        const title = cleanText_(item.title);
        const link = item.link || '';
        const text = cleanText_(`${title} ${item.description || ''}`);
        const score = scoreText_(text);
        const time = parseDateTime_(text, item.pubDate);
        const status = decideStatus_(score, time);

        if (score.value >= 3 || time) {
          candidateSheet.appendRow([
            new Date(),
            score.value,
            status,
            time ? formatTime_(time.start, time.allDay) : '',
            title,
            source.name,
            link,
            score.reasons.join(' / ')
          ]);
          candidates++;
        }

        if (status !== '同步') {
          skipped++;
          return;
        }

        const uniqueId = makeId_(title, link, time.start);
        if (existingIds[uniqueId]) {
          skipped++;
          return;
        }

        const eventTitle = time.allDay ? `${title}（具体时间待定）` : title;
        const location = guessLocation_(text);
        const description = [
          `自动抓取来源：${source.name}`,
          `原文链接：${link}`,
          `筛选分数：${score.value}`,
          `命中原因：${score.reasons.join(' / ')}`,
          '',
          text
        ].join('\n');

        let event;
        if (time.allDay) {
          event = calendar.createAllDayEvent(eventTitle, time.start, { description, location });
        } else {
          const end = new Date(time.start.getTime() + CONFIG.defaultDurationMinutes * 60 * 1000);
          event = calendar.createEvent(eventTitle, time.start, end, { description, location });
        }

        syncedSheet.appendRow([
          new Date(),
          uniqueId,
          eventTitle,
          time.start,
          location,
          source.name,
          link,
          event.getId()
        ]);

        existingIds[uniqueId] = true;
        added++;
      });
    } catch (e) {
      logSheet.appendRow([new Date(), '抓取失败', `${source.name}: ${String(e)}`]);
    }
  });

  logSheet.appendRow([new Date(), '完成', `新增 ${added} 条，跳过 ${skipped} 条，候选 ${candidates} 条`]);
}


function previewOnly() {
  const candidateSheet = resetSheet_('候选池', ['抓取时间', '分数', '状态', '识别时间', '标题', '来源', '链接', '命中原因']);

  getSources_().forEach(source => {
    try {
      fetchRss_(source.url).slice(0, 60).forEach(item => {
        const title = cleanText_(item.title);
        const text = cleanText_(`${title} ${item.description || ''}`);
        const score = scoreText_(text);
        const time = parseDateTime_(text, item.pubDate);
        if (score.value >= 3 || time) {
          candidateSheet.appendRow([
            new Date(),
            score.value,
            decideStatus_(score, time),
            time ? formatTime_(time.start, time.allDay) : '',
            title,
            source.name,
            item.link || '',
            score.reasons.join(' / ')
          ]);
        }
      });
    } catch (e) {
      candidateSheet.appendRow([new Date(), 0, '抓取失败', '', '', source.name, source.url, String(e)]);
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
    .atHour(CONFIG.dailyHour)
    .inTimezone(CONFIG.timezone)
    .create();
}


function testCreateEvent() {
  const calendar = getOrCreateCalendar_();
  const start = new Date(Date.now() + 60 * 60 * 1000);
  const end = new Date(start.getTime() + 60 * 60 * 1000);
  calendar.createEvent('测试：科技新品发布会同步', start, end, {
    description: '能看到这个事件，就说明授权成功。',
    location: '线上'
  });
}


function getSources_() {
  const sources = CONFIG.extraRss.map((url, index) => ({ name: `RSS ${index + 1}`, url }));
  CONFIG.queries.forEach((query, index) => {
    const q = `(${query}) when:30d`;
    sources.push({
      name: `Google News ${index + 1}`,
      url: 'https://news.google.com/rss/search?' + queryString_({
        q,
        hl: 'zh-CN',
        gl: 'CN',
        ceid: 'CN:zh-Hans'
      })
    });
  });
  return sources;
}


function fetchRss_(url) {
  const response = UrlFetchApp.fetch(url, {
    muteHttpExceptions: true,
    followRedirects: true,
    headers: { 'User-Agent': 'Mozilla/5.0 LaunchCalendarBot' }
  });

  const code = response.getResponseCode();
  if (code < 200 || code >= 300) throw new Error(`HTTP ${code}`);

  const xml = response.getContentText('UTF-8').replace(/[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]/g, '');
  const root = XmlService.parse(xml).getRootElement();
  const items = [];

  const channel = root.getChild('channel');
  if (channel) {
    channel.getChildren('item').forEach(item => {
      items.push({
        title: childText_(item, 'title'),
        link: childText_(item, 'link'),
        description: childText_(item, 'description'),
        pubDate: childText_(item, 'pubDate')
      });
    });
    return items;
  }

  const ns = root.getNamespace();
  root.getChildren('entry', ns).forEach(entry => {
    items.push({
      title: childTextNs_(entry, 'title', ns),
      link: atomLink_(entry, ns),
      description: childTextNs_(entry, 'summary', ns) || childTextNs_(entry, 'content', ns),
      pubDate: childTextNs_(entry, 'updated', ns) || childTextNs_(entry, 'published', ns)
    });
  });
  return items;
}


function scoreText_(text) {
  let value = 0;
  const reasons = [];

  CONFIG.strongWords.forEach(word => {
    if (text.includes(word)) {
      value += word === '发布会' ? 5 : 3;
      reasons.push(word);
    }
  });

  CONFIG.productWords.forEach(word => {
    if (text.includes(word)) {
      value += 1;
      reasons.push(word);
    }
  });

  CONFIG.negativeWords.forEach(word => {
    if (text.includes(word)) {
      value -= 4;
      reasons.push(`排除:${word}`);
    }
  });

  if (/(\d{1,2}月\d{1,2}日|今天|今晚|明天|明晚|本周|下周)/.test(text)) {
    value += 2;
    reasons.push('时间');
  }

  return { value, reasons };
}


function decideStatus_(score, time) {
  if (score.value < CONFIG.minScore) return '分数不足';
  if (!time) return '没识别到时间';
  if (!inWindow_(time.start)) return '不在60天内';
  return '同步';
}


function parseDateTime_(text, pubDate) {
  const normalized = cleanText_(text).replace(/号/g, '日').replace(/：/g, ':').replace(/\s+/g, '');
  const anchor = parseDate_(pubDate) || new Date();

  const explicit = parseExplicitDate_(normalized, anchor);
  if (explicit) return explicit;

  const relative = parseRelativeDate_(normalized, anchor);
  if (relative) return relative;

  const weekday = parseWeekdayDate_(normalized, anchor);
  if (weekday) return weekday;

  return null;
}


function parseExplicitDate_(text, anchor) {
  const patterns = [
    { re: /(20\d{2})年(\d{1,2})月(\d{1,2})日?/g, y: 1, m: 2, d: 3 },
    { re: /(\d{1,2})月(\d{1,2})日/g, y: 0, m: 1, d: 2 }
  ];

  for (let i = 0; i < patterns.length; i++) {
    let match;
    const pattern = patterns[i];
    while ((match = pattern.re.exec(text)) !== null) {
      const month = Number(match[pattern.m]);
      const day = Number(match[pattern.d]);
      const year = pattern.y ? Number(match[pattern.y]) : inferYear_(month, day, anchor);
      if (!validDate_(year, month, day)) continue;

      const after = text.slice(match.index + match[0].length, match.index + match[0].length + 35);
      const before = text.slice(Math.max(0, match.index - 12), match.index);
      const time = parseTime_(after) || parseTime_(before);
      const date = new Date(year, month - 1, day);

      if (!time) return { start: date, allDay: true };
      date.setHours(time.hour, time.minute, 0, 0);
      return { start: date, allDay: false };
    }
  }

  return null;
}


function parseRelativeDate_(text, anchor) {
  const list = [
    { re: /(今天|今日|今晚)/, offset: 0 },
    { re: /(明天|明日|明晚)/, offset: 1 },
    { re: /(后天|后日)/, offset: 2 }
  ];

  for (let i = 0; i < list.length; i++) {
    const match = text.match(list[i].re);
    if (!match) continue;

    const date = new Date(anchor);
    date.setDate(date.getDate() + list[i].offset);
    date.setHours(0, 0, 0, 0);

    const time = parseTime_(text.slice(match.index, match.index + 30));
    if (!time) return { start: date, allDay: true };
    date.setHours(time.hour, time.minute, 0, 0);
    return { start: date, allDay: false };
  }

  return null;
}


function parseWeekdayDate_(text, anchor) {
  const match = text.match(/(本周|下周)([一二三四五六日天])/);
  if (!match) return null;

  const map = { 日: 0, 天: 0, 一: 1, 二: 2, 三: 3, 四: 4, 五: 5, 六: 6 };
  const date = new Date(anchor);
  let offset = map[match[2]] - date.getDay() + (match[1] === '下周' ? 7 : 0);
  if (offset < 0 && match[1] === '本周') offset += 7;
  date.setDate(date.getDate() + offset);
  date.setHours(0, 0, 0, 0);

  const time = parseTime_(text.slice(match.index, match.index + 30));
  if (!time) return { start: date, allDay: true };
  date.setHours(time.hour, time.minute, 0, 0);
  return { start: date, allDay: false };
}


function parseTime_(text) {
  const match = text.match(/(凌晨|早上|上午|中午|下午|晚上|晚间|今晚|明晚|晚)?(\d{1,2})(?:[:点时])(\d{1,2})?分?/);
  if (!match) return null;

  let hour = Number(match[2]);
  const minute = match[3] ? Number(match[3]) : 0;
  if (hour > 24 || minute > 59) return null;

  const period = match[1] || '';
  if (['下午', '晚上', '晚间', '今晚', '明晚', '晚'].includes(period) && hour < 12) hour += 12;
  if (period === '中午' && hour < 11) hour += 12;
  if (hour === 24) hour = 0;

  return { hour, minute };
}


function inWindow_(date) {
  const now = new Date();
  const min = new Date(now.getTime() - CONFIG.lookBackHours * 60 * 60 * 1000);
  const max = new Date(now.getTime() + CONFIG.lookAheadDays * 24 * 60 * 60 * 1000);
  return date >= min && date <= max;
}


function getOrCreateCalendar_() {
  const list = CalendarApp.getCalendarsByName(CONFIG.calendarName);
  if (list.length) return list[0];
  return CalendarApp.createCalendar(CONFIG.calendarName, { timeZone: CONFIG.timezone });
}


function getSheet_(name, headers) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(name);
  if (!sheet) sheet = ss.insertSheet(name);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    sheet.setFrozenRows(1);
  }
  return sheet;
}


function resetSheet_(name, headers) {
  const sheet = getSheet_(name, headers);
  sheet.clearContents();
  sheet.appendRow(headers);
  sheet.setFrozenRows(1);
  return sheet;
}


function loadExistingIds_(sheet) {
  const ids = {};
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return ids;

  sheet.getRange(2, 2, lastRow - 1, 1).getValues().forEach(row => {
    if (row[0]) ids[row[0]] = true;
  });
  return ids;
}


function makeId_(title, link, date) {
  const raw = `${normalizeTitle_(title)}|${link}|${Utilities.formatDate(date, CONFIG.timezone, 'yyyy-MM-dd')}`;
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, raw, Utilities.Charset.UTF_8)
    .map(b => ('0' + ((b < 0 ? b + 256 : b).toString(16))).slice(-2))
    .join('')
    .slice(0, 40);
}


function normalizeTitle_(title) {
  return cleanText_(title)
    .replace(/(发布会|新品发布会|新品发布|上市发布|正式上市|定档|官宣|直播|开启预售|开启预约|具体时间待定)/g, '')
    .replace(/[^\w\u4e00-\u9fa5]/g, '')
    .toLowerCase();
}


function guessLocation_(text) {
  if (/(线上|直播|在线|云发布|官网)/.test(text)) return '线上';
  const match = text.match(/(北京|上海|广州|深圳|成都|杭州|武汉|南京|重庆|西安|苏州|合肥|长沙|厦门|青岛|郑州|珠海|宁波|天津|香港|澳门|台北|东京|首尔|新加坡|纽约|洛杉矶|伦敦|巴黎|柏林)/);
  return match ? match[1] : '线上 / 具体地点待定';
}


function cleanText_(value) {
  return String(value || '')
    .replace(/<!\[CDATA\[/g, '')
    .replace(/\]\]>/g, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
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


function parseDate_(value) {
  if (!value) return null;
  const date = new Date(value);
  return isNaN(date.getTime()) ? null : date;
}


function inferYear_(month, day, anchor) {
  const year = anchor.getFullYear();
  const candidate = new Date(year, month - 1, day);
  const now = new Date();
  if (candidate < new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)) return year + 1;
  return year;
}


function validDate_(year, month, day) {
  const date = new Date(year, month - 1, day);
  return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
}


function formatTime_(date, allDay) {
  const dateText = Utilities.formatDate(date, CONFIG.timezone, 'yyyy-MM-dd');
  if (allDay) return `${dateText} 全天/时间待定`;
  return Utilities.formatDate(date, CONFIG.timezone, 'yyyy-MM-dd HH:mm');
}


function queryString_(params) {
  return Object.keys(params)
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&');
}
