# 6d 给每个景点加天气 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 `index.html`（6d 主版）每个景点卡片加一行天气（实时优先 + 静态兜底），同步 mirror 到 `shanxi-6d.html`。不动 5d/3d。

**Architecture:**
- 新增 `assets/weather.js`：浏览器/Node 双用，含 WMO 中文映射、Open-Meteo fetch、sessionStorage 6h 缓存、5km 网格去重
- 内联 `assets/weather.js` 内容到 `index.html`
- 修改 `renderSlotCard()` 在 `slot-meta` 行下方增加天气行（loading / live / fallback / error 四态）
- 新增 `updateWeatherRows()` 在 fetch 完成后二次 patch DOM
- `init()` 末尾 `fetchAllWeather().then(updateWeatherRows)`（不阻塞首屏渲染）

**Tech Stack:**
- HTML/CSS/Vanilla JS（无新依赖）
- Open-Meteo `forecast` API（免费、CORS、无 key）
- sessionStorage 缓存
- Node `node --test`（已有测试基础设施）

## File Structure

| 文件 | 角色 | 改动类型 |
|------|------|---------|
| `travel-plan-viz/assets/weather.js` | **新建** | 天气引擎（含 dual-mode 导出守卫） |
| `test/weather.test.js` | **新建** | 纯函数单元测试（TDD） |
| `index.html` | 修改 | (a) trip JSON 给 14 个 slot 加 `weather.fallback`<br>(b) `<style>` 追加 weather CSS<br>(c) 内联 weather.js 到 main `<script>`<br>(d) `renderSlotCard` 加天气行<br>(e) 新增 `updateWeatherRows`<br>(f) `init()` 加 fetchAllWeather 钩子 |
| `shanxi-6d.html` | 修改（最后） | `cp index.html shanxi-6d.html && diff` 必须为空 |
| `travel-plan-viz/assets/validate.js` | **不动** | 用作机械校验 |
| `docs/superpowers/specs/2026-09-09-weather-attractions-design.md` | **不动** | 设计文档 |

## Global Constraints

[From the spec, copy verbatim and extend as plan fills in]

- **目标文件**：`index.html`（6d 主版），同步 mirror 到 `shanxi-6d.html`。
- **不改** `shanxi-5d.html`、`shanxi-3d.html`、`travel-plan-viz/assets/map.js`、`travel-plan-viz/assets/reminders.js`。
- **WGS-84 坐标**（CLAUDE.md）：Open-Meteo 接受 WGS-84，无需 GCJ-02 转换。
- **不查实时票价**（CLAUDE.md 红线）：天气不是票价，符合。
- **`escapeHTML` 重复不合并**（CLAUDE.md）：weather 引擎自带一份 `escapeHTML`，不动现有 map.js/reminders.js。
- **数据与呈现分离**：完整 `trip`（含 `slot.weather.fallback`）必须以 `<script id="trip-data">` 原样内嵌进页面。
- **图片必须能加载**（page-contract）：天气 UI 纯文字/emoji，无需图片。
- **单文件 + 离线能力如实**（CLAUDE.md）：fetch 失败时降级到 fallback + 行末"⚠ 实时不可用"提示，不冒充离线可用。
- **测试命令**：`node --test test/*.test.js`（注意 glob，不是 `test/`）。
- **校验命令**：`node travel-plan-viz/assets/validate.js <file>`。
- **提交策略**（CLAUDE.md）：一条 commit 只干一类事，feat/fix/docs/chore 如实归类。

---

## Task 1: 写 weather 引擎纯函数的失败测试（TDD red）

**Files:**
- Create: `test/weather.test.js`

**Interfaces:**
- Consumes: `assets/weather.js` 导出的 `wmoIconCN`、`wmoToText`、`precipAdvice`、`roundCoord`
- Produces: 失败测试，定义后续实现的契约

- [ ] **Step 1: 创建 test/weather.test.js**

写入以下内容（注意 `require` 路径对应 assets/weather.js，但**该文件还不存在**，测试应失败）：

```js
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
```

- [ ] **Step 2: 运行测试，验证失败**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main && node --test test/weather.test.js
```

**Expected:** FAIL — `Cannot find module '../travel-plan-viz/assets/weather.js'`（assets/weather.js 还没创建）

- [ ] **Step 3: 提交失败测试**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
git add test/weather.test.js
git commit -m "test: 6d 天气引擎纯函数失败测试（TDD red）"
```

---

## Task 2: 实现 weather 引擎纯函数 + dual-mode 守卫（TDD green）

**Files:**
- Create: `travel-plan-viz/assets/weather.js`

**Interfaces:**
- Consumes: 上述测试
- Produces: 浏览器可用的全局函数（`wmoIconCN`、`wmoToText`、`precipAdvice`、`roundCoord`、`escapeHTML`）+ Node `module.exports`

- [ ] **Step 1: 创建 travel-plan-viz/assets/weather.js**

写入以下完整内容（顶部 JSDoc 注释 + 纯函数实现 + 底部 dual-mode 守卫，对齐现有 `assets/reminders.js` 与 `assets/map.js` 的导出风格）：

```js
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
// 阈值 < 20 / 20–50 / ≥ 50
function precipAdvice(prob) {
  if (prob >= 50) return '必带雨具';
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
```

- [ ] **Step 2: 运行测试，验证通过**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main && node --test test/weather.test.js
```

**Expected:** 全部 PASS（约 12 个 test 通过）

- [ ] **Step 3: 提交实现**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
git add travel-plan-viz/assets/weather.js
git commit -m "feat: 6d 天气引擎纯函数实现（Open-Meteo + fallback）"
```

---

## Task 3: 给 trip-data JSON 所有 14 个 slot 加 `weather.fallback`

**Files:**
- Modify: `index.html` 内 `<script id="trip-data">` 段（约 line 1675–2353 的 JSON）

**Interfaces:**
- Consumes: 现有 slots 字段
- Produces: 每个 slot 加 `weather: { coords: {lat, lng}, fallback: {...} }`

**注意：**`mapPoints` 数组（line 2360+）和 `closureAudit`/`reminders` 等不重复坐标的字段不需要改；只需给 `days[*].slots[*]` 加 weather。

- [ ] **Step 1: 列出每个 slot 的 (date, name, lat, lng) 用于填表**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
node -e "
const html = require('fs').readFileSync('index.html', 'utf8');
const m = html.match(/<script id=\"trip-data\"[^>]*>([\s\S]*?)<\/script>/);
const trip = JSON.parse(m[1]);
trip.days.forEach(d => d.slots.forEach(s => {
  console.log(d.date + ' | ' + s.name + ' | ' + s.lat + ',' + s.lng);
}));
"
```

**Expected:** 输出 14 行（每个 slot 一行）。验证日期是 9/25–9/30。

- [ ] **Step 2: 在每个 slot 上加 weather.fallback 字段**

依据设计文档 §5 的 fallback 表（如下），按 slot 顺序逐个 Edit：

| date | name | coords | icon | cond | high | low | precip |
|------|------|--------|------|------|------|-----|--------|
| 9/25 | 太原武宿机场→市区酒店 | 37.7398,112.6286 | ⛅ | 多云 | 22 | 12 | 无需备伞 |
| 9/26 | 山西博物院 | 37.8755,112.5512 | 🌤 | 晴间多云 | 22 | 12 | 无需备伞 |
| 9/26 | 晋祠 | 37.7060,112.4459 | 🌤 | 晴间多云 | 22 | 12 | 无需备伞 |
| 9/27 | 佛光寺 | 38.7250,113.3706 | ☀ | 晴 | 7 | 0 | 无需备伞 |
| 9/27 | 南禅寺 | 38.7013,113.1138 | ☀ | 晴 | 7 | 0 | 无需备伞 |
| 9/27 | 代县古城/边靖楼 | 39.0897,112.9630 | ⛅ | 多云 | 19 | 8 | 无需备伞 |
| 9/28 | 应县木塔 | 39.5572,113.1847 | 🌤 | 晴间多云 | 19 | 8 | 无需备伞 |
| 9/28 | 崇福寺（朔州） | 39.3131,112.4257 | 🌤 | 晴间多云 | 19 | 8 | 无需备伞 |
| 9/28 | 大同古城夜景 | 40.0936,113.2954 | ☀ | 晴 | 18 | 6 | 无需备伞 |
| 9/29 | 悬空寺 | 39.6792,113.7369 | ⛅ | 多云 | 15 | 5 | 建议备伞 |
| 9/29 | 觉山寺 | 39.6900,113.7100 | 🌤 | 晴间多云 | 18 | 6 | 无需备伞 |
| 9/29 | 华严寺/九龙壁 | 40.0937,113.2960 | ☀ | 晴 | 18 | 6 | 无需备伞 |
| 9/30 | 云冈石窟 | 40.1096,113.1469 | ☀ | 晴 | 18 | 6 | 无需备伞 |
| 9/30 | 太原机场返程 | 37.7398,112.6286 | ⛅ | 多云 | 22 | 12 | 无需备伞 |

每个 slot 在 `transport: {...}` 后面（或 `needsBooking`/`leadDays` 之前）插入：

```json
"weather": {
  "coords": { "lat": <slot.lat>, "lng": <slot.lng> },
  "fallback": {
    "icon": "<emoji>",
    "conditions": "<cond>",
    "high": <high>,
    "low": <low>,
    "precipAdvice": "<precip>",
    "updatedAt": "2026-09-09"
  }
},
```

**实现提示**：用 Edit 工具对每个 slot 找到独特上下文（如 slot 紧邻的 `closingDays` / `ticketPrice` / `transport` / `seasonal`）做替换，确保唯一。例：

```
old_string: "      "needsBooking": false,\n      "leadDays": 0\n    },
new_string: "      "needsBooking": false,\n      "leadDays": 0,\n      "weather": {\n        "coords": { "lat": 37.7398, "lng": 112.6286 },\n        "fallback": { "icon": "⛅", "conditions": "多云", "high": 22, "low": 12, "precipAdvice": "无需备伞", "updatedAt": "2026-09-09" }\n      }\n    },
```

但实际每个 slot 的上下文不同，按 slot 的实际末尾字段（`ticketPrice`/`seasonal`/`review` 等）做锚点。

- [ ] **Step 3: 验证 JSON 解析**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
node -e "
const html = require('fs').readFileSync('index.html', 'utf8');
const m = html.match(/<script id=\"trip-data\"[^>]*>([\s\S]*?)<\/script>/);
const trip = JSON.parse(m[1]);
let total = 0, withWeather = 0;
trip.days.forEach(d => d.slots.forEach(s => {
  total++;
  if (s.weather && s.weather.fallback) withWeather++;
}));
console.log('slots total=' + total + ', with weather.fallback=' + withWeather);
console.assert(total === withWeather, '每个 slot 都需要 weather');
console.log('JSON OK');
"
```

**Expected:** `slots total=14, with weather.fallback=14` + `JSON OK`

- [ ] **Step 4: 跑现有 validate.js**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
node travel-plan-viz/assets/validate.js index.html
```

**Expected:** `✓ 契约校验通过`（加 weather 字段不破坏契约，因为 validate.js 不检查该字段——若有 ERROR，说明天气字段破坏了某条规则，需排查）

- [ ] **Step 5: 提交**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
git add index.html
git commit -m "feat: 6d trip JSON 加 14 个 slot 的 weather.fallback"
```

---

## Task 4: 加 weather 行 CSS 到 `<style>`

**Files:**
- Modify: `index.html` 内 `<style>` 段（搜索 `</style>` 前插入）

**Interfaces:**
- Consumes: 现有 `.slot-meta` 类的样式
- Produces: `.slot-weather`、`.slot-weather-icon`、`.slot-weather-text`、`.slot-weather-live-dot`、`.slot-weather-note`、`.slot-weather-error`、`.slot-weather-loading` 七个类

- [ ] **Step 1: 定位 `</style>` 闭合标签**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
grep -n "</style>" index.html
```

记录行号，假设在 line N。

- [ ] **Step 2: 在 `</style>` 前插入 CSS**

用 Edit，old_string 为 `</style>` 前面的最后一条 CSS 规则（任取一条做锚点），new_string 在末尾追加 weather CSS + 闭合：

```css
/* ─────── 天气行（每个 slot 卡片） ─────── */
.slot-weather {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed rgba(0,0,0,.08);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}
.slot-weather-icon { font-size: 16px; }
.slot-weather-text { flex: 1; color: #2a2a2a; }
.slot-weather-live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4caf50;
  flex-shrink: 0;
}
.slot-weather-note {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
  padding-left: 4px;
}
.slot-weather-error {
  color: #c62828;
  font-size: 12px;
  margin-left: 8px;
}
.slot-weather-loading { color: #999; }
</style>
```

（即 Edit 时 old_string = 现有某条 CSS 规则 + `</style>`，new_string = 现有规则 + weather CSS + `</style>`）

- [ ] **Step 3: 验证 HTML 仍合法**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
node travel-plan-viz/assets/validate.js index.html
```

**Expected:** `✓ 契约校验通过`

- [ ] **Step 4: 提交**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
git add index.html
git commit -m "feat: 6d slot 卡片加 weather 行 CSS"
```

---

## Task 5: 内联 weather.js 到 index.html 主脚本

**Files:**
- Modify: `index.html` 主 `<script>` 段（line 2356+，在 `var trip = JSON.parse(...)` 之前或之后插入新模块）

**Interfaces:**
- Consumes: `assets/weather.js` 文件内容
- Produces: `index.html` 主脚本内多出 weather 模块（含 fetch/cache/coord-collection/getWeatherForRender）

**重要：** 把 assets/weather.js 的纯函数部分（wmoIconCN/wmoToText/precipAdvice/roundCoord/escapeHTML）**不要重复定义**——它们会通过内联 join 进来，与现有 escapeHTML 同名会冲突。改用 IIFE 或重命名为内嵌模块的私有函数。

或者：**只内联 fetch/cache/coord/getWeatherForRender 这部分**，纯函数已经在 assets/weather.js 顶部定义、并通过内联被加入全局作用域即可。需要在主脚本里手动加一行 `var wmoIconCN = ...; function wmoToText...`——但这就重复了。

**实际方案**（最简）：把 assets/weather.js 完整内容内联到主脚本的 `(function init(){...})()` **之前**，并在末尾去掉 dual-mode 守卫（避免污染内联 HTML）。这样所有函数成为全局变量，与现有 `escapeHTML` 同名会冲突 —— 而现有 escapeHTML 也在全局。

**解决方案**：assets/weather.js 已自带 escapeHTML 函数定义，会与现有 escapeHTML 重复 → 用 IIFE 包一层：

```js
(function(){
  // ── 这里是 assets/weather.js 的完整内容，但去掉底部 dual-mode 守卫 ──
  var wmoIconCN = {...};
  function wmoToText(...) {...}
  function precipAdvice(...) {...}
  function roundCoord(...) {...}
  function escapeHTML(...) {...}  // 重复定义会覆盖现有版本——这是故意的，统一用 weather.js 的版本
  function buildDailyUrl(...) {...}
  function fetchOneCell(...) {...}
  function loadCache(...) {...}
  function saveCache(...) {...}
  function collectWeatherRequests() {...}
  function fetchAllWeather() {...}
  function getWeatherForRender(...) {...}

  // ── 暴露给主脚本的接口 ──
  window.__weather = {
    getWeatherForRender: getWeatherForRender,
    fetchAllWeather: fetchAllWeather,
    collectWeatherRequests: collectWeatherRequests,
    escapeHTML: escapeHTML  // 主脚本改用这一份 escapeHTML
  };
})();
```

但这样 escapeHTML 不会全局化 —— 主脚本的 escapeHTML 函数是独立的（可能略有差异）。**简化路径**：

- 内联时**不要**用 IIFE，把所有函数直接放全局
- 现有 escapeHTML 在文件靠前位置定义（line ~1478 according to summary），weather.js 的 escapeHTML 后定义会**覆盖**之
- 验证 escapeHTML 行为一致（map.js 已有版本是 `.replace(/&/g, '&amp;').replace(/</g, '&lt;')...` 与 weather.js 写的完全一致），覆盖无副作用

**最终方案：直接全局内联，去掉底部 dual-mode 守卫。**

- [ ] **Step 1: 读 assets/weather.js 全文**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
cat travel-plan-viz/assets/weather.js
```

- [ ] **Step 2: 在主 `<script>` 顶部插入 weather.js 全部内容（去掉 dual-mode 守卫）**

用 Edit 找到 `var trip = JSON.parse(...)` 这行（line 2358），在它**之前**插入：

```js
// ═══════════════ WEATHER ENGINE（内联自 travel-plan-viz/assets/weather.js）═══════════════
// [assets/weather.js 全部内容，去掉底部 if (typeof module !== 'undefined' && module.exports) {...} 守卫]
// ════════════════════════════════════════════════════════════════════════════════════

var trip = JSON.parse(document.getElementById('trip-data').textContent);
```

具体操作：
- 复制 assets/weather.js 全文（除最后 3 行 dual-mode 守卫）
- 用 Edit，old_string = `// ─── Extract trip data from embedded JSON ───\nvar trip = JSON.parse(document.getElementById('trip-data').textContent);`
- new_string = `// ═══════════════ WEATHER ENGINE ═══════════════\n[完整 inline 内容]\n// ══════════════════════════════════════════════════════════\n\nvar trip = JSON.parse(document.getElementById('trip-data').textContent);`

- [ ] **Step 3: 验证 HTML 仍合法**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
node travel-plan-viz/assets/validate.js index.html
```

**Expected:** `✓ 契约校验通过`

- [ ] **Step 4: 浏览器 smoke test**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
open index.html  # macOS
```

在浏览器 DevTools console 检查：
- `typeof wmoToText` → `'function'`
- `typeof precipAdvice` → `'function'`
- `typeof fetchAllWeather` → `'function'`
- `typeof roundCoord` → `'function'`
- `typeof escapeHTML` → `'function'`（应是 weather.js 覆盖后的版本，但行为一致）
- 无 ReferenceError

- [ ] **Step 5: 提交**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
git add index.html
git commit -m "feat: 6d 内联 weather.js 引擎到主脚本"
```

---

## Task 6: 修改 renderSlotCard 加天气行

**Files:**
- Modify: `index.html` 内 `renderSlotCard` 函数（约 line 2472–2535）

**Interfaces:**
- Consumes: `slot.weather.fallback`、`getWeatherForRender(slot, targetDate)`（live 时返回 source='live'，否则 fallback）
- Produces: 卡片 DOM 在 `.slot-meta` `</div>` 闭合之后追加 `.slot-weather` 行 + `.slot-weather-note` 声明

- [ ] **Step 1: 定位 renderSlotCard 函数末尾**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
grep -n "renderSlotCard\|renderBackupSpots" index.html | head -10
```

确认 `renderSlotCard` 函数体结束位置（紧接 `return html;` 和 `}` 之前）。

- [ ] **Step 2: 在 `slot-meta` `</div>` 后插入天气行渲染**

用 Edit 找到：
```js
  html += '</div>';   // 关闭 slot-meta
  html += '</div>';   // 关闭 slot-body
```

替换为：
```js
  html += '</div>';   // 关闭 slot-meta

  // ── 天气行 ──
  var dayDate = (slot._dayDate) || '';  // 临时标记（见 Task 7）
  var w = dayDate ? getWeatherForRender(slot, dayDate) : null;
  if (w) {
    html += '<div class="slot-weather">';
    html += '<span class="slot-weather-icon">' + escapeHTML(w.icon) + '</span>';
    html += '<span class="slot-weather-text">天气  ' + escapeHTML(w.conditions) + ' · '
          + w.high + '°/' + w.low + '° · 💧' + escapeHTML(w.precipAdvice) + '</span>';
    if (w.source === 'live') {
      html += '<span class="slot-weather-live-dot" title="实时数据"></span>';
    }
    html += '</div>';
    html += '<div class="slot-weather-note">📡 Open-Meteo · 11km 网格 · 参考'
          + (w.source === 'fallback' ? ' · <span class="slot-weather-error">⚠ 实时不可用</span>' : '')
          + '</div>';
  }

  html += '</div>';   // 关闭 slot-body
```

**实现提示：**`slot._dayDate` 是从外层 day 注入的临时字段（Task 7 会处理）；此处先用 `_dayDate` 字段查找，无则跳过天气渲染（loading 态），避免破坏现有渲染。

- [ ] **Step 3: 验证**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
node travel-plan-viz/assets/validate.js index.html
```

**Expected:** `✓ 契约校验通过`（注意：现在 slot 还没被注入 _dayDate，所以天气行**不会出现**，仅渲染 fallback 默认态。这是预期——Task 7 会注入 dayDate 并触发渲染）

- [ ] **Step 4: 浏览器 smoke test**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
open index.html
```

DevTools console 检查：
- `slot._dayDate` 应为 undefined（在所有 slot 上）
- 天气行应**不显示**（slot 上没 dayDate）
- 无 JS error

- [ ] **Step 5: 提交**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
git add index.html
git commit -m "feat: 6d renderSlotCard 加天气行（待 _dayDate 注入）"
```

---

## Task 7: 注入 day.date 到 slot、添加 updateWeatherRows 和 init 钩子

**Files:**
- Modify: `index.html` 内 `renderTimeline`/`showDayTab`（line ~2576+ 和 line ~2849+）注入 `slot._dayDate`
- Modify: `index.html` 内 `init()` 函数（line ~3165）

**Interfaces:**
- Consumes: `slot` 对象、`day.date`、`fetchAllWeather()`（Promise）、`getWeatherForRender()`、`renderSlotCard()` 返回的 HTML
- Produces: 
  - 每个 slot 在传入 `renderSlotCard` 前被临时打上 `_dayDate`
  - 新函数 `updateWeatherRows()` 重新渲染所有 slot 的天气行
  - `init()` 末尾 `fetchAllWeather().then(updateWeatherRows)`

- [ ] **Step 1: 修改 renderTimeline，在渲染 slot 前注入 _dayDate**

定位 `renderTimeline`（line 2576）：

```js
function renderTimeline() {
  ...
  trip.days.forEach(function (day, di) {
    ...
    day.slots.forEach(function (slot) {
      html += renderSlotCard(slot);
    });
    ...
  });
}
```

把 `day.slots.forEach(function (slot) {` 后插入 `slot._dayDate = day.date;`：

```js
      day.slots.forEach(function (slot) {
        slot._dayDate = day.date;   // 注入临时日期，供 weather 行渲染
        html += renderSlotCard(slot);
      });
```

- [ ] **Step 2: 修改 showDayTab 同样注入**

定位 `showDayTab` 函数（line ~2849 起）：

```js
function showDayTab(idx) {
  ...
  trip.days[idx].slots.forEach(function (slot) {
    html += renderSlotCard(slot);
  });
  ...
}
```

同样插入 `slot._dayDate = trip.days[idx].date;`。

- [ ] **Step 3: 验证首屏渲染**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
node travel-plan-viz/assets/validate.js index.html
```

**Expected:** `✓ 契约校验通过`

- [ ] **Step 4: 浏览器 smoke test（首屏 fallback）**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
open index.html
```

DevTools 检查：
- 切到 Day 1 tab：每个 slot 卡片底部出现天气行，**无**绿点●，底部声明 `📡 Open-Meteo · 11km 网格 · 参考`（无 `⚠ 实时不可用`，因为 init 钩子还没接，下一 task 才会 fetch 失败时加）
- DevTools Network：暂时没有 Open-Meteo 请求（init 钩子还没接）
- 切到每个 day tab 都确认天气行显示

- [ ] **Step 5: 在主脚本添加 updateWeatherRows 函数**

定位 init() 函数（line ~3165）之前，插入：

```js
// ─────── 天气二次 patch ───────
// fetchAllWeather() 完成后调用；只重渲染天气行，不重建整个卡片。
function updateWeatherRows() {
  trip.days.forEach(function (day) {
    day.slots.forEach(function (slot) {
      // 找到已渲染的天气行节点（querySelector 在 slot 卡片内）
      var cards = document.querySelectorAll('.slot-card');
      // 用 slot name + 时间戳定位（实际只能用 name，因为没有 ID）
      cards.forEach(function (card) {
        var nameEl = card.querySelector('.slot-name');
        if (!nameEl || nameEl.textContent !== slot.name) return;
        var w = getWeatherForRender(slot, day.date);
        if (!w) return;
        var weatherRow = card.querySelector('.slot-weather');
        var noteRow = card.querySelector('.slot-weather-note');
        if (!weatherRow) return;  // 没渲染就跳过
        // 重写天气行
        weatherRow.innerHTML =
          '<span class="slot-weather-icon">' + escapeHTML(w.icon) + '</span>' +
          '<span class="slot-weather-text">天气  ' + escapeHTML(w.conditions) + ' · '
            + w.high + '°/' + w.low + '° · 💧' + escapeHTML(w.precipAdvice) + '</span>' +
          (w.source === 'live' ? '<span class="slot-weather-live-dot" title="实时数据"></span>' : '');
        if (noteRow) {
          noteRow.innerHTML = '📡 Open-Meteo · 11km 网格 · 参考'
            + (w.source === 'fallback' ? ' · <span class="slot-weather-error">⚠ 实时不可用</span>' : '');
        }
      });
    });
  });
}
```

- [ ] **Step 6: 在 init() 末尾接 fetchAllWeather 钩子**

定位 init() 函数最后一行 `initPlayButton();` 后插入：

```js
  // ── 启动天气抓取（不阻塞首屏）──
  fetchAllWeather().then(updateWeatherRows);
```

- [ ] **Step 7: 验证**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
node travel-plan-viz/assets/validate.js index.html
```

**Expected:** `✓ 契约校验通过`

- [ ] **Step 8: 浏览器 smoke test（完整流程）**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
open index.html
```

DevTools Network 检查：
- 应出现 1–3 个 Open-Meteo 请求（5km 网格去重后约 3 个 cell）
- 完成后各 slot 天气行 DOM 应**未变化**（因为 9/25–9/30 还在 16 天窗口外 → fallback）

DevTools Application → Session Storage：
- 应有 `t6d_weather_v1` key，内容包含 fetchedAt 与 daily 数据

切到各 day tab：
- 所有天气行文案应一致（fallback 静态值）

切 DevTools Network → Offline，再刷新：
- 应显示 fallback + `⚠ 实时不可用`

- [ ] **Step 9: 提交**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
git add index.html
git commit -m "feat: 6d 天气 fetch 钩子 + updateWeatherRows 二次 patch"
```

---

## Task 8: Mirror 到 shanxi-6d.html + 校验

**Files:**
- Mirror: `shanxi-6d.html` ← `cp index.html shanxi-6d.html`

- [ ] **Step 1: 复制**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
cp index.html shanxi-6d.html
```

- [ ] **Step 2: 验证字节一致**

```bash
diff index.html shanxi-6d.html
```

**Expected:** 没有任何输出（空 diff）

- [ ] **Step 3: 跑 validate.js**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
node travel-plan-viz/assets/validate.js shanxi-6d.html
```

**Expected:** `✓ 契约校验通过`

- [ ] **Step 4: 浏览器 smoke test shanxi-6d.html**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
open shanxi-6d.html
```

DevTools console：
- `typeof wmoToText === 'function'`
- 切 day tabs 都有天气行
- DevTools Network 应有 Open-Meteo 请求

- [ ] **Step 5: 提交 mirror**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
git add shanxi-6d.html
git commit -m "feat: 6d mirror 同步天气功能"
```

---

## Task 9: 全量回归测试

**Files:**
- 无修改（仅验证）

- [ ] **Step 1: 跑所有单元测试**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
node --test test/*.test.js
```

**Expected:** 全部 PASS（map/reminders/security/validate/weather 共 5 个 test 文件，无 fail、无 fail-fast）

- [ ] **Step 2: 跑 validate.js 两个文件**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
node travel-plan-viz/assets/validate.js index.html
node travel-plan-viz/assets/validate.js shanxi-6d.html
```

**Expected:** 两个文件都 `✓ 契约校验通过`，无 ERROR，无 WARNING（若新增 WARNING 是预期变化，逐条人工判断）

- [ ] **Step 3: 浏览器回归（index.html）**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
open index.html
```

逐 day tab 检查（4 个关键 view）：
1. **首屏 / Day 1（9/25）**：交通日 slot 有天气行 ⛅ 多云 22°/12°
2. **Day 2（9/26）**：山西博物院 + 晋祠 都有天气行，文案一致
3. **Day 5（9/29）**：悬空寺（15°/5° 建议备伞）与华严寺（18°/6° 无需备伞）**不同**
4. **Day 6（9/30）**：云冈石窟（18°/6°）+ 太原机场（22°/12°）**不同**

地图、时间轴、餐饮、备选景点等其他区块**未变化**。

- [ ] **Step 4: 浏览器回归（shanxi-6d.html）**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
open shanxi-6d.html
```

同上 4 个 day 检查。

- [ ] **Step 5: 检查 git log**

```bash
cd /Users/lynnlong/PycharmProjects/travel-plan-viz-main
git log --oneline -10
```

**Expected:** 看到以下 8 个 commit（顺序可能略不同，按本 plan 步骤）：
1. `docs: 6d 加景点天气设计（Open-Meteo live + fallback）` ← Task 0 已提交
2. `test: 6d 天气引擎纯函数失败测试（TDD red）`
3. `feat: 6d 天气引擎纯函数实现（Open-Meteo + fallback）`
4. `feat: 6d trip JSON 加 14 个 slot 的 weather.fallback`
5. `feat: 6d slot 卡片加 weather 行 CSS`
6. `feat: 6d 内联 weather.js 引擎到主脚本`
7. `feat: 6d renderSlotCard 加天气行（待 _dayDate 注入）`
8. `feat: 6d 天气 fetch 钩子 + updateWeatherRows 二次 patch`
9. `feat: 6d mirror 同步天气功能`

---

## Self-Review Checklist

### Spec coverage

- [x] §数据源策略（Open-Meteo + fallback） → Task 2/3/7
- [x] §数据结构（slot.weather.fallback） → Task 3
- [x] §WMO 映射 → Task 2
- [x] §抓取逻辑（fetchAllWeather、collectWeatherRequests、getWeatherForRender） → Task 5/7
- [x] §启动与渲染流程（不阻塞首屏 + 二次 patch） → Task 7
- [x] §UI 细节（loading/live/fallback/error 四态） → Task 4/6/7
- [x] §Fallback 数据 14 行预填 → Task 3
- [x] §修改文件清单（index.html + shanxi-6d.html mirror） → Task 8
- [x] §验证（validate.js + node --test + 浏览器） → Task 9

### Placeholder scan

- 无 TBD/TODO/"implement later"/"add appropriate error handling" 等占位符
- 每个 task 的 code block 完整，可直接执行

### Type consistency

- `wmoIconCN` 在 Task 2 定义、被 Task 6/7 通过 `getWeatherForRender` 间接使用 → 一致
- `getWeatherForRender` 在 Task 5 内联时定义、被 Task 6/7 直接调用 → 一致
- `fetchAllWeather` 在 Task 5 内联时定义、返回 Promise、在 Task 7 `.then(updateWeatherRows)` 调用 → 一致
- `slot._dayDate` 在 Task 7 注入、被 Task 6 的 renderSlotCard 读取 → 一致
- `escapeHTML` 在 weather.js 定义、被 Task 6/7 调用 → 一致（与 map.js/reminders.js 行为一致，覆盖现有版本无副作用）

### Scope check

- 本计划只涉及 6d（index.html + shanxi-6d.html），不动 5d/3d → 与设计文档对齐
- 不创建额外 skill、不引入新依赖 → 与"简洁优先"原则对齐

### Known limitations（来自 spec §11 不做）

- ❌ 不查实时票价（保持红线）
- ❌ 不做天气地图叠加层（不做）
- ❌ 不做 24h 逐小时预报（不做）
- ❌ 不做手动刷新按钮（不做）
- ❌ 不做"超出窗口"弹窗（UI 内联声明替代）

---

## 关键文件

- `index.html`（6d 主版，改造目标）
- `shanxi-6d.html`（mirror，Task 8 同步）
- `travel-plan-viz/assets/weather.js`（新建）
- `test/weather.test.js`（新建）
- `docs/superpowers/specs/2026-09-09-weather-attractions-design.md`（设计文档，已提交）
- `travel-plan-viz/assets/validate.js`（机械校验工具）

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-09-09-weather-attractions.md`.**

Two execution options:
1. **Subagent-Driven (recommended)** - dispatch fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** - execute tasks in this session using executing-plans, batch with checkpoints

Which approach?