# 给景点加天气（山西 6 天行程）

> 状态：用户已批准设计，进入实现计划阶段。
> 适用于 `index.html`（= `shanxi-6d.html`，6 天主版）。
> **不**改 `shanxi-5d.html`、`shanxi-3d.html`。

## Context

用户需求：「能否给每个景点加上当天天气」。

当前 `index.html` 已有：
- `trip.preTrip.weather` —— 行程级总述（太原 22/12、大同 18/6、昼夜温差大、五台山/恒山 5–10℃ 偏低）
- `days[i].slots[j]` —— 每个景点卡片，含 period/name/time/review/openingHours/ticketPrice/transport/seasonal 等

**缺口**：每个具体景点的天气不可见；用户在出行前不知道当天下午云冈石窟的天气如何。

**目标**：每个 slot 卡片在 `slot-meta` 下方显示一行天气（含温度、天气状况、降水建议），数据**实时优先 + 静态兜底**。

## 数据源策略

| 来源 | 何时用 | 说明 |
|------|--------|------|
| **Open-Meteo `forecast`** | 在线 & 目标日期在 16 天窗口内 | 实时联网，免费、CORS 开放、无需 API key |
| **静态 fallback** | 离线 / 抓取失败 / 目标日期 >16 天 | 当前文档 §5 中预填的"参考预报" |
| 缓存 | sessionStorage 6h TTL | 避免同一会话重复打 API |

**Open-Meteo 边界诚实声明**：
- 模型分辨率 ~9–11km 网格（ECMWF IFS）
- 两个景点< 11km 距离会拿到**几乎相同**的数据
- 这意味着大同古城 / 九龙壁 / 华严寺 共享一份预报，但**悬空寺**（恒山，海拔高、独立网格）会拿到独立预报
- UI 上明确标注 `📡 Open-Meteo · 11km 网格 · 参考`，让用户知道精度上限

**时间窗口警告**：今天是 2026-09-09，行程 9/25–9/30 距今 16–21 天。**Open-Meteo 当前还拿不到 9/25 的预报**（窗口最远到 9/25 零点）。预计 2026-09-18 之后能完整取到所有日期。提前打开会显示 fallback。

## 数据结构

### `slot.weather` 字段

```js
{
  coords: { lat: 40.0611, lng: 113.4822 },   // = slot.lat/lng（同一坐标请求更精确）
  fallback: {
    icon: "☀",                              // emoji
    conditions: "晴间多云",                  // 简短中文
    high: 18,                               // 整数 °C
    low: 6,
    precipAdvice: "无需备伞",                // 短文本
    updatedAt: "2026-09-09"                  // 数据生成日期（≠ 当天）
  }
}
```

**`live` 字段不存 JSON** —— live 数据每次刷新都变，存 JSON 反而误导。运行时由渲染函数决定显示 live 还是 fallback。

### WMO 码 → 中文映射（引擎内）

```js
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
```

### 降水建议阈值

| `precipitation_probability_max` | 建议文案 |
|--------------------------------|----------|
| < 20% | 无需备伞 |
| 20–50% | 建议备伞 |
| ≥ 50% | 必带雨具 |

## 抓取逻辑（新增内联引擎片段）

```js
var WEATHER_CACHE_KEY = 't6d_weather_v1';
var WEATHER_CACHE_TTL = 6 * 60 * 60 * 1000;
var WEATHER_FETCH_TIMEOUT = 4000;

function roundCoord(v) { return Math.round(v * 20) / 20; }  // 0.05° (~5km)

function buildDailyUrl(lat, lng, startDate, endDate) {
  return 'https://api.open-meteo.com/v1/forecast'
    + '?latitude=' + lat + '&longitude=' + lng
    + '&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max'
    + '&timezone=Asia/Shanghai'
    + '&start_date=' + startDate + '&end_date=' + endDate;
}

function wmoToText(code, prob) {
  var entry = wmoIconCN[code] || ['🌤', '多云'];
  var cond = entry[1];
  if (prob >= 50) cond += '（有雨）';
  else if (prob >= 20) cond += '（可能有阵雨）';
  return { icon: entry[0], conditions: cond };
}

function precipAdvice(prob) {
  if (prob >= 50) return '必带雨具';
  if (prob >= 20) return '建议备伞';
  return '无需备伞';
}

function fetchOneCell(lat, lng, startDate, endDate) {
  // Promise.race(fetch + setTimeout(4000))
  // 失败/超时/4xx/5xx → 返回 null（不抛异常）
}

function loadCache() {
  // sessionStorage 反序列化；损坏时返回 {}
}

function saveCache(cache) {
  // sessionStorage 序列化（try/catch，隐私模式/容量满时静默）
}

function collectWeatherRequests() {
  // 遍历 trip.days+slots
  // 按 roundCoord() 去重（5km 网格），返回 [{ key, lat, lng, date }]
}

function fetchAllWeather() {
  // 1) 读缓存
  // 2) 未命中且日期在 16 天窗口内 → 并发 fetch
  // 3) 全部结果写回缓存
  // 4) 返回 Map<key, dailyResult>
}

function getWeatherForRender(slot, targetDate) {
  var key = roundCoord(slot.lat) + ':' + roundCoord(slot.lng);
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
  return Object.assign({ source: 'fallback' }, slot.weather.fallback);
}
```

## 启动与渲染流程

```
DOMContentLoaded
  ├─ renderTimeline() / showDayTab()  第一次渲染
  │     └─ renderSlotCard(slot) 包含 weather 行
  │           ├─ live 数据未到达 → 显示 fallback + 无 ●
  │           └─ live 数据已就绪 → 显示 live + 绿点 ●
  │
  └─ fetchAllWeather() 并发
        └─ 完成后 updateWeatherRows() 二次 patch
              ├─ 命中目标日期的 slot 行替换为 live 数据 + ●
              └─ 抓取超时/失败的 slot 行追加 ⚠ 实时不可用 提示
```

**关键设计**：
- **不阻塞首屏渲染**：先静态渲染（fallback），抓取完成再二次 patch（live）
- **不闪烁**：二次 patch 用 DOM 节点替换，只改 innerHTML，不重建整个卡片
- **不重复 fetch**：sessionStorage 6h 缓存跨标签页共享（同一会话）

## UI 细节

### slot 卡片新增的天气行

```
┌──────────────────────────────────────────┐
│ 营业 09:00–17:00                         │
│ 门票 免费（公众号预约）                    │
│ 自驾 包车 · 60km · 二广高速 · 约1h        │
│ ──────────────────────────────────────   │
│ 🌤 天气  ☀ 晴间多云 · 18°/6° · 💧无需备伞 ●│ ← 新增
│ 📡 Open-Meteo · 11km 网格 · 参考         │ ← 新增（小字声明）
└──────────────────────────────────────────┘
```

### 三种状态

| 状态 | 展示 |
|------|------|
| **加载中** | `🌤 天气 ⏳ 加载中…` （layout 保留，无 ●，无声明） |
| **live** | `🌤 天气 ☀ 晴间多云 · 18°/6° · 💧无需备伞 ●` + 底部声明 |
| **fallback（成功）** | 同上但**无** `●`，仍显示底部声明 |
| **fallback（失败）** | 同上 + 末尾 `⚠ 实时不可用`（红色） |

### CSS 追加

```css
.slot-weather {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed rgba(0,0,0,.08);
  display: flex; align-items: center; gap: 8px;
  font-size: 14px;
}
.slot-weather-icon { font-size: 16px; }
.slot-weather-text { flex: 1; color: #2a2a2a; }
.slot-weather-live-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #4caf50; flex-shrink: 0;
}
.slot-weather-note {
  font-size: 11px; color: #999;
  margin-top: 4px; padding-left: 4px;
}
.slot-weather-error { color: #c62828; font-size: 12px; margin-left: 8px; }
.slot-weather-loading { color: #999; }
```

## Fallback 数据（基于气候平均 + 联网调研）

调研来源：[五台山 9 月下旬气候](https://weather.zuziche.com/c3157_m9_3.html)、[恒山历史天气](https://waptianqi.2345.com/wea_history/71510.htm)

按城市-海拔分组的气候基线：

| 城市/景点 | 海拔 | 9 月下旬白天 | 9 月下旬夜间 | 降水 |
|-----------|------|-------------|-------------|------|
| 太原（市区） | ~800m | 22°C | 12°C | 偶有阵雨 |
| 大同（市区） | ~1000m | 18°C | 6°C | 旱季，少 |
| 应县/代县 | ~1000m | 19°C | 8°C | 偶有阵雨 |
| 恒山/悬空寺 | ~1500m | 15°C | 5°C | 山区多变 |
| 五台山区 | ~2200m | 7°C | 0°C | 旱季，极少 |

按日期填入每个 slot：

| Date | 景点 | 城市/海拔 | 高 | 低 | 状况 | 降水建议 |
|------|------|----------|---|---|------|---------|
| 9/25 | 太原武宿机场 | 太原 | 22 | 12 | 多云 | 无需备伞 |
| 9/26 | 山西博物院 | 太原 | 22 | 12 | 多云转晴 | 无需备伞 |
| 9/26 | 晋祠 | 太原 | 22 | 12 | 晴间多云 | 无需备伞 |
| 9/27 | 佛光寺 | 五台山 | 7 | 0 | 晴 | 无需备伞 |
| 9/27 | 南禅寺 | 五台山 | 7 | 0 | 晴 | 无需备伞 |
| 9/27 | 代县古城/边靖楼 | 代县 | 19 | 8 | 多云 | 无需备伞 |
| 9/28 | 应县木塔 | 应县 | 19 | 8 | 晴间多云 | 无需备伞 |
| 9/28 | 崇福寺 | 应县 | 19 | 8 | 晴间多云 | 无需备伞 |
| 9/28 | 大同古城夜景 | 大同 | 18 | 6 | 晴 | 无需备伞 |
| 9/29 | 悬空寺 | 恒山 | 15 | 5 | 多云 | 建议备伞 |
| 9/29 | 觉山寺 | 大同北郊 | 18 | 6 | 晴间多云 | 无需备伞 |
| 9/29 | 华严寺/九龙壁 | 大同 | 18 | 6 | 晴 | 无需备伞 |
| 9/30 | 云冈石窟 | 大同 | 18 | 6 | 晴 | 无需备伞 |
| 9/30 | 太原机场返程 | 太原 | 22 | 12 | 多云 | 无需备伞 |

（Day 1 交通日 23:30 已无景点天气意义，按惯例也填太原当日）

## 修改文件清单

| 文件 | 改动 |
|------|------|
| `index.html` | +1) trip JSON 给所有 slot 加 `weather.fallback`（18 处）<br>+2) 内联 weather 引擎片段（wmoIconCN + fetch 函数 + cache）<br>+3) `renderSlotCard()` 增加 weather 行（live/fallback/loading/error 四态）<br>+4) `updateWeatherRows()` 新函数（抓取完成后二次 patch）<br>+5) `DOMContentLoaded` 钩子调用 `fetchAllWeather().then(updateWeatherRows)`<br>+6) CSS 追加（~50 行）<br>+7) `escapeHTML` 已内联，无需新增 |
| `shanxi-6d.html` | `cp index.html shanxi-6d.html && diff` 空 |
| `shanxi-5d.html` / `shanxi-3d.html` | **不动** |

## 验证

```bash
node /Users/lynnlong/PycharmProjects/travel-plan-viz-main/travel-plan-viz/assets/validate.js /Users/lynnlong/PycharmProjects/travel-plan-viz-main/index.html
node /Users/lynnlong/PycharmProjects/travel-plan-viz-main/travel-plan-viz/assets/validate.js /Users/lynnlong/PycharmProjects/travel-plan-viz-main/shanxi-6d.html
diff /Users/lynnlong/PycharmProjects/travel-plan-viz-main/index.html /Users/lynnlong/PycharmProjects/travel-plan-viz-main/shanxi-6d.html  # 必须空
```

**手动浏览器测试（index.html）**：

1. **正常在线**：所有 slot 显示天气行；今天 9/25–9/30 还在 16 天窗口外，应显示 fallback（**无绿点**）+ 底部 `📡 Open-Meteo` 声明
2. **离线模式**（DevTools → Network → Offline）：所有 slot 显示 fallback + 末尾 `⚠ 实时不可用`
3. **9/18 后**（用户实际出发前 7 天）：再次打开应能看到 live 数据 + 绿点 ●
4. **slot 滚动对比**：大同古城/九龙壁/华严寺 应显示**完全相同**的天气；悬空寺/应县木塔/五台山 应**各自独立**
5. **重复打开**：sessionStorage 缓存命中，DevTools 看 Network 应只看到**第一次**的 3 个 Open-Meteo 请求

## 关键边界

- **不查实时票价**（CLAUDE.md 红线）—— 天气不是票价，符合
- **图片必须能加载**（page-contract）—— 天气 UI 纯文字/emoji，无需图片
- **`escapeHTML` 重复不合并**（CLAUDE.md）—— weather 引擎自带一份，不动现有 map.js/reminders.js
- **WGS-84 坐标**（CLAUDE.md）—— Open-Meteo 接受 WGS-84，无需转换
- **离线能力如实**（CLAUDE.md）—— 天气行明确标注"实时不可用"提示，不冒充离线可用

## 不做

- ❌ 不存历史/历史天气（archive API）—— 本次只看未来 16 天预报
- ❌ 不做天气地图叠加层 —— 复杂度爆炸，行程不需要
- ❌ 不做 24 小时逐小时预报 —— 每天一行足够；用户可去"高德/天文台"App 看精细化
- ❌ 不做用户手动刷新按钮 —— 6h 缓存 + 重打开即可
- ❌ 不做"今天已过/未来超过 16 天"等智能边界提示弹窗 —— UI 行内足够说明

## 提交策略

按 CLAUDE.md「一条 commit 只干一类事」：

1. `feat: 6d 给每个景点加天气（Open-Meteo live + 静态 fallback）`
   - 含 `index.html` + `shanxi-6d.html` mirror
   - 含 fallback 数据（§5 表格）
   - 含新设计文档（本文件）

---

## 关键文件

- `/Users/lynnlong/PycharmProjects/travel-plan-viz-main/index.html`（6d 主版 + 改造目标）
- `/Users/lynnlong/PycharmProjects/travel-plan-viz-main/shanxi-6d.html`（mirror）
- `/Users/lynnlong/PycharmProjects/travel-plan-viz-main/docs/superpowers/specs/2026-09-09-weather-attractions-design.md`（本设计）
- `/Users/lynnlong/PycharmProjects/travel-plan-viz-main/travel-plan-viz/assets/validate.js`（机械校验）