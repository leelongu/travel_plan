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

// ───────── Node 导出守卫 ─────────
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { wmoIconCN, wmoToText, precipAdvice, roundCoord, escapeHTML };
}
