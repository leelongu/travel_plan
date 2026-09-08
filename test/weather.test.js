// 天气引擎纯函数测试。
// 项目约定单测用 `node --test test/*.test.js`（详见 CLAUDE.md）。
const { test } = require('node:test');
const assert = require('node:assert');
const { wmoIconCN, wmoToText, precipAdvice, roundCoord } = require('../travel-plan-viz/assets/weather.js');

// ─────── wmoIconCN ───────
test('wmoIconCN 覆盖晴天/多云/阴/雨/雪/雷暴主类', () => {
  assert.ok(wmoIconCN[0]);   // 晴
  assert.ok(wmoIconCN[1]);   // 晴间多云
  assert.ok(wmoIconCN[3]);   // 阴
  assert.ok(wmoIconCN[61]);  // 小雨
  assert.ok(wmoIconCN[71]);  // 小雪
  assert.ok(wmoIconCN[95]);  // 雷暴
});

test('wmoIconCN 每项是 [emoji, 中文] 二元组', () => {
  Object.keys(wmoIconCN).forEach(function (k) {
    assert.strictEqual(wmoIconCN[k].length, 2, 'wmoIconCN[' + k + '] 应为二元组');
    assert.ok(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u.test(wmoIconCN[k][0]), '应含 emoji');
    assert.ok(wmoIconCN[k][1].length > 0, '中文描述非空');
  });
});

// ─────── wmoToText ───────
test('wmoToText 雨天高概率降水追加（有雨）', () => {
  var r = wmoToText(61, 70);  // 小雨 + 70%
  assert.strictEqual(r.conditions, '小雨（有雨）');
  assert.ok(r.icon);
});

test('wmoToText 雨天低概率降水追加（可能有阵雨）', () => {
  var r = wmoToText(80, 30);  // 阵雨 + 30%
  assert.strictEqual(r.conditions, '阵雨（可能有阵雨）');
});

test('wmoToText 晴天低概率降水无附加', () => {
  var r = wmoToText(0, 5);
  assert.strictEqual(r.conditions, '晴');
  assert.strictEqual(r.icon, '☀');
});

test('wmoToText 未知 WMO 码兜底多云', () => {
  var r = wmoToText(999, 0);
  assert.strictEqual(r.conditions, '多云');
});

// ─────── precipAdvice ───────
test('precipAdvice < 20% 提示无需备伞', () => {
  assert.strictEqual(precipAdvice(0), '无需备伞');
  assert.strictEqual(precipAdvice(19), '无需备伞');
});

test('precipAdvice 20–50% 提示建议备伞', () => {
  assert.strictEqual(precipAdvice(20), '建议备伞');
  assert.strictEqual(precipAdvice(50), '建议备伞');
});

test('precipAdvice ≥ 50% 提示必带雨具', () => {
  assert.strictEqual(precipAdvice(51), '必带雨具');
  assert.strictEqual(precipAdvice(100), '必带雨具');
});

// ─────── roundCoord ───────
test('roundCoord 5km 网格去重精度（0.05°）', () => {
  assert.strictEqual(roundCoord(40.001), 40.00);
  assert.strictEqual(roundCoord(40.02), 40.00);
  assert.strictEqual(roundCoord(40.03), 40.05);  // 边界四舍五入到 40.05
  assert.strictEqual(roundCoord(40.07), 40.05);
  assert.strictEqual(roundCoord(40.08), 40.10);
});

test('roundCoord 处理负坐标', () => {
  assert.strictEqual(roundCoord(-30.03), -30.05);
});
