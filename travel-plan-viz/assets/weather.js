// 天气查询引擎：Open-Meteo forecast API + 静态 fallback。
// 浏览器与 Node 双用。浏览器侧内联到 index.html 使用。
//
// 设计要点：
// - 公开函数尽量纯（wmoIconCN / wmoToText / precipAdvice / roundCoord）便于单测
// - fetch / cache / DOM 部分不强求纯函数，做不到的依赖 try/catch 兜底
// - 不发起实时票价/机票价查询（CLAUDE.md 红线）—— 天气不是票价

// ───────── HTML 转义（与 map.js/reminders.js 重复属故意，CLAUDE.md 要求） ─────────
function escapeHTML(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ───────── WMO 天气码 → [emoji, 中文] ─────────
var wmoIconCN = {
  0:  ['☀', '晴'],
  1:  ['🌤', '晴间多云'],
  2:  ['⛅', '多云'],
  3:  ['☁', '阴'],
  45: ['🌫', '雾'],
  48: ['🌫', '雾凇'],
  51: ['🌦', '毛毛雨'],
  53: ['🌦', '毛毛雨'],
  55: ['🌦', '毛毛雨'],
  61: ['🌧', '小雨'],
  63: ['🌧', '中雨'],
  65: ['🌧', '大雨'],
  71: ['🌨', '小雪'],
  73: ['🌨', '中雪'],
  75: ['🌨', '大雪'],
  80: ['🌦', '阵雨'],
  81: ['🌦', '阵雨'],
  82: ['⛈', '强阵雨'],
  95: ['⛈', '雷暴']
};

// ───────── WMO + 降水概率 → { icon, conditions } ─────────
// prob: 0–100 整数百分比
function wmoToText(code, prob) {
  var entry = wmoIconCN[code] || ['🌤', '多云'];
  var cond = entry[1];
  if (prob >= 50) cond += '（有雨）';
  else if (prob >= 20) cond += '（可能有阵雨）';
  return { icon: entry[0], conditions: cond };
}

// ───────── 降水概率 → 建议文案 ─────────
// 阈值 < 20 / 20–50 / > 50
function precipAdvice(prob) {
  if (prob > 50) return '必带雨具';
  if (prob >= 20) return '建议备伞';
  return '无需备伞';
}

// ───────── 坐标 5km 网格去重（0.05° ≈ 5km）─────────
function roundCoord(v) {
  return Math.round(v * 20) / 20;
}

// ───────── 从 live 数据 + fallback 解析出渲染用的天气结果 ─────────
// liveResults: { key: { daily: {...} } }；unavailable: 该 cell 是否抓取失败（true 才显示 ⚠）
// 返回 { source: 'live'|'fallback', icon, conditions, high, low, precipAdvice, [unavailable] }
function resolveWeather(liveResults, slot, targetDate, unavailable) {
  if (!slot.weather) return null;
  var key = roundCoord(slot.weather.coords.lat) + ':' + roundCoord(slot.weather.coords.lng);
  var live = liveResults[key];
  if (live && live.daily) {
    var i = live.daily.time.indexOf(targetDate);
    if (i >= 0) {
      var cond = wmoToText(live.daily.weather_code[i], live.daily.precipitation_probability_max[i]);
      return {
        source: 'live',
        icon: cond.icon,
        conditions: cond.conditions,
        high: Math.round(live.daily.temperature_2m_max[i]),
        low: Math.round(live.daily.temperature_2m_min[i]),
        precipAdvice: precipAdvice(live.daily.precipitation_probability_max[i])
      };
    }
  }
  var fb = Object.assign({ source: 'fallback' }, slot.weather.fallback);
  if (unavailable) fb.unavailable = true;
  return fb;
}

// ═══════════ 浏览器侧 fetch + DOM ═══════════
// 以下函数依赖 fetch / sessionStorage —— Node 环境（单测）跳过；
// 由调用方在 init 阶段显式触发 fetchAllWeather(trip)，不要自动执行。
var WEATHER_CACHE_KEY = 't6d_weather_v1';
var WEATHER_CACHE_TTL = 6 * 60 * 60 * 1000;
var WEATHER_FETCH_TIMEOUT = 4000;
var liveWeatherResults = {};  // { key: { daily: {...} } }
var weatherCellStatus = {};   // { key: 'ok' | 'error' } —— 'error' 才显示 ⚠ 实时不可用

function buildDailyUrl(lat, lng, startDate, endDate) {
  return 'https://api.open-meteo.com/v1/forecast'
    + '?latitude=' + lat + '&longitude=' + lng
    + '&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max'
    + '&timezone=Asia/Shanghai'
    + '&start_date=' + startDate + '&end_date=' + endDate;
}

function loadWeatherCache() {
  try {
    var raw = sessionStorage.getItem(WEATHER_CACHE_KEY);
    if (!raw) return {};
    return JSON.parse(raw);
  } catch (e) { return {}; }
}

function saveWeatherCache(cache) {
  try { sessionStorage.setItem(WEATHER_CACHE_KEY, JSON.stringify(cache)); }
  catch (e) { /* 隐私模式/容量满静默 */ }
}

function fetchOneCell(lat, lng, startDate, endDate) {
  var url = buildDailyUrl(lat, lng, startDate, endDate);
  return Promise.race([
    fetch(url).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }),
    new Promise(function (resolve) { setTimeout(function () { resolve(null); }, WEATHER_FETCH_TIMEOUT); })
  ]);
}

// 给没有内嵌 weather 字段的 slot 自动派生 fallback。两条规则：
// 1. 若数据已带 slot.weather.fallback（如 shanxi-6d 的内嵌风格），不覆盖。
// 2. 否则按"南北 + 月份"启发式给出华南/江南/华北三类默认 fallback。
// fallbackMonth 默认从 trip.startDate 推导（也可由调用方显式传入）。
function ensureSlotWeather(slot, fallbackMonth) {
  if (typeof slot.lat !== 'number' || typeof slot.lng !== 'number'
      || !isFinite(slot.lat) || !isFinite(slot.lng)) return;
  if (slot.weather && slot.weather.fallback) return;
  slot.weather = slot.weather || {};
  slot.weather.coords = { lat: slot.lat, lng: slot.lng };
  if (!slot.weather.fallback) {
    var month = fallbackMonth || 10;
    var fb;
    if (slot.lat < 28) {
      // 华南
      fb = month >= 6 && month <= 9
        ? { icon: '⛅', conditions: '多云', high: 32, low: 25, precipAdvice: '建议备伞' }
        : { icon: '☀', conditions: '晴', high: 28, low: 22, precipAdvice: '无需备伞' };
    } else if (slot.lat < 35) {
      // 江南
      fb = month >= 6 && month <= 9
        ? { icon: '⛅', conditions: '多云', high: 32, low: 24, precipAdvice: '建议备伞' }
        : { icon: '⛅', conditions: '多云', high: 22, low: 16, precipAdvice: '无需备伞' };
    } else {
      // 华北/西北
      fb = month >= 6 && month <= 9
        ? { icon: '☀', conditions: '晴', high: 30, low: 18, precipAdvice: '无需备伞' }
        : { icon: '☀', conditions: '晴', high: 14, low: 4, precipAdvice: '无需备伞' };
    }
    fb.updatedAt = new Date().toISOString().slice(0, 10);
    slot.weather.fallback = fb;
  }
}

function getWeatherForRender(slot, targetDate) {
  if (!slot.weather) return null;
  var key = roundCoord(slot.weather.coords.lat) + ':' + roundCoord(slot.weather.coords.lng);
  return resolveWeather(liveWeatherResults, slot, targetDate, weatherCellStatus[key] === 'error');
}

// 收集所有 (date, cell) 不重复的请求；先做 ensureSlotWeather 派生。
function collectWeatherRequests(trip, fallbackMonth) {
  trip.days.forEach(function (day) {
    (day.slots || []).forEach(function (s) { ensureSlotWeather(s, fallbackMonth); });
  });
  var seen = {};
  var reqs = [];
  trip.days.forEach(function (day) {
    (day.slots || []).forEach(function (slot) {
      if (!slot.weather || !slot.weather.coords) return;
      var lat = slot.weather.coords.lat;
      var lng = slot.weather.coords.lng;
      var key = roundCoord(lat) + ':' + roundCoord(lng);
      var composite = key + ':' + day.date;
      if (seen[composite]) return;
      seen[composite] = true;
      reqs.push({ key: key, lat: lat, lng: lng, date: day.date });
    });
  });
  return reqs;
}

// 入口：fetch 所有 cell；返回 Promise；成功后从 liveWeatherResults 取数据。
// trip.startDate 用于决定 fallbackMonth。
function fetchAllWeather(trip) {
  if (typeof fetch === 'undefined') return Promise.resolve();  // Node 环境跳过
  var fallbackMonth = trip && trip.startDate
    ? parseInt(String(trip.startDate).slice(5, 7), 10) : 10;
  var reqs = collectWeatherRequests(trip, fallbackMonth);
  if (!reqs.length) return Promise.resolve();
  var cache = loadWeatherCache();
  var now = Date.now();
  var dateMin = reqs.reduce(function (a, r) { return r.date < a ? r.date : a; }, reqs[0].date);
  var dateMax = reqs.reduce(function (a, r) { return r.date > a ? r.date : a; }, reqs[0].date);

  var fetches = {};
  reqs.forEach(function (r) {
    var cached = cache[r.key];
    if (cached && (now - cached.fetchedAt) < WEATHER_CACHE_TTL) {
      liveWeatherResults[r.key] = { daily: cached.daily };
      weatherCellStatus[r.key] = 'ok';
      return;
    }
    if (fetches[r.key]) return;
    fetches[r.key] = fetchOneCell(r.lat, r.lng, dateMin, dateMax).then(function (data) {
      if (!data || !data.daily) {
        weatherCellStatus[r.key] = 'error';
        return;
      }
      liveWeatherResults[r.key] = { daily: data.daily };
      weatherCellStatus[r.key] = 'ok';
      cache[r.key] = { fetchedAt: now, daily: data.daily };
    });
  });

  return Promise.all(Object.values(fetches)).then(function () {
    saveWeatherCache(cache);
  });
}

// ───────── Node 导出守卫 ─────────
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    wmoIconCN, wmoToText, precipAdvice, roundCoord, escapeHTML, resolveWeather,
    // 浏览器侧 fetch 入口；Node 侧调用 fetchAllWeather 不会真发请求（守卫提前 return）
    fetchAllWeather, getWeatherForRender, ensureSlotWeather,
    liveWeatherResults, weatherCellStatus,
  };
}
