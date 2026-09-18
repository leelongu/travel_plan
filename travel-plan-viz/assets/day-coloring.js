// 按日配色：把"第 N 天"映射成同套色彩体系，覆盖地图 pin/polyline、
// 时间轴 day-tab / day-block / day-theme、地图下方 chip。
// 单一色源是 :root 的 --day1..--day7（CSS 文件 day-coloring.css 定义）。
// JS 在初始化时通过 getComputedStyle 读这些变量，避免 CSS 与 JS 各写一份 hex 漂移。
// trip.days 长度 > 7 时回退到 --day7。

var dayColors = [];
(function _initDayColors() {
  if (typeof getComputedStyle === 'undefined' || typeof document === 'undefined') return;
  var cs = getComputedStyle(document.documentElement);
  for (var i = 1; i <= 7; i++) {
    var v = cs.getPropertyValue('--day' + i).trim();
    if (v) dayColors.push(v);
  }
})();
function dayColor(dayIdx) {
  if (!dayColors.length) return '#4a8a8a';  // 兜底色（变量未读到时）
  return dayColors[Math.min(Math.max(dayIdx || 0, 0), dayColors.length - 1)];
}

// 给 mapPoints 数组的每个元素加 dayIdx（不带则保持 0）。返回新数组（不修改原数组）。
// trip 必须为含 days 数组的对象，slot 按出现顺序连续归属同一 day。
function attachDayIdx(trip, mapPoints) {
  var idx = 0;
  var out = [];
  trip.days.forEach(function (day, dayIdx) {
    (day.slots || []).forEach(function (slot) {
      if (typeof slot.lat === 'number' && typeof slot.lng === 'number'
          && isFinite(slot.lat) && isFinite(slot.lng)
          && !slot.hideFromMap) {
        // 在 mapPoints 里找到对应元素（按引用匹配）
        var src = mapPoints[idx];
        if (src) {
          out.push(Object.assign({}, src, { dayIdx: dayIdx }));
          idx++;
        }
      }
    });
  });
  return out;
}

// ───────── Node 导出守卫 ─────────
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    dayColor: dayColor,
    attachDayIdx: attachDayIdx,
    dayColors: dayColors,
  };
}
