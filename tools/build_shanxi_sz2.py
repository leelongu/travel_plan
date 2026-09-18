#!/usr/bin/env python3
"""Build shanxi-sz2.html from data/trip_data.json + inlined engines.

Single-file HTML generator per travel-plan-viz SKILL.md:
- Inline 5 engine files (map/reminders/weather/nav-buttons/day-coloring)
- Inline complete trip-data as <script id="trip-data">
- 古建美学 (dark + brass) visual styling
- 7-day plan with day-tab coloring
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRIP_JSON = ROOT / "data" / "trip_data.json"
OUT = ROOT / "shanxi-sz2.html"

# Engine sources — read at module import
ENGINES = {
    "map.js":          ROOT / "travel-plan-viz" / "assets" / "map.js",
    "reminders.js":    ROOT / "travel-plan-viz" / "assets" / "reminders.js",
    "weather.js":      ROOT / "travel-plan-viz" / "assets" / "weather.js",
    "nav-buttons.js":  ROOT / "travel-plan-viz" / "assets" / "nav-buttons.js",
    "day-coloring.js": ROOT / "travel-plan-viz" / "assets" / "day-coloring.js",
    "day-coloring.css": ROOT / "travel-plan-viz" / "assets" / "day-coloring.css",
}

def load_engines():
    return {k: p.read_text() for k, p in ENGINES.items()}

def load_trip():
    return json.loads(TRIP_JSON.read_text())

def render_html(trip):
    engines = load_engines()
    trip_json = json.dumps(trip, ensure_ascii=False, indent=2)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{trip['title']}</title>
  <meta name="description" content="{trip['title']} · 单文件离线可读旅行 HTML">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=ZCOOL+XiaoWei&family=DM+Mono:wght@400;500&family=Ma+Shan+Zheng&display=swap" rel="stylesheet">

  <!-- Leaflet CSS (CDN) -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">

  <style>{CSS_MAIN}</style>
  <style>{engines['day-coloring.css']}</style>
</head>
<body>

<div class="page-wrap" id="page">

  <!-- ═══════════════ HERO ═══════════════ -->
  <section class="hero">
    <div class="hero-eyebrow">MIGO · 旅行领航</div>
    <h1 class="hero-title">{trip['title']}<span class="accent">朔州进</span></h1>
    <p class="hero-sub">黑神话悟空 · 朔州进 · 太原出 · 9/26 国庆前夕出发 · 7 天 6 晚</p>
    <div class="hero-meta">
      <span class="hero-badge">📅 出发 9/26（周六早班）</span>
      <span class="hero-badge">🛬 返程 10/2（周五·太原武宿T2）</span>
      <span class="hero-badge">⏱ 7 天 6 晚</span>
      <span class="hero-badge">🚗 自驾总里程约 1,220 km</span>
    </div>
  </section>

  <!-- ═══════════════ MAP (行程简图 · 顶部) ═══════════════ -->
  <section class="section section--map-top">
    <div class="section-header">
      <div class="section-icon jade">🗺️</div>
      <div>
        <div class="section-title">行程简图</div>
        <div class="section-subtitle">At a Glance · 朔州 → 临汾 · 7 天自驾</div>
      </div>
    </div>
    <div class="section-body">
      <div id="map" class="map"></div>
      <div class="route-chips" id="route-chips"></div>
    </div>
  </section>

  <!-- ═══════════════ PRE-TRIP CHECKLIST ═══════════════ -->
  <section class="section section--checklist">
    <div class="section-header">
      <div class="section-icon cinnabar">📋</div>
      <div>
        <div class="section-title">出发前待办清单</div>
        <div class="section-subtitle">按提前天数排序 · 出行前必查</div>
      </div>
    </div>
    <div class="section-body">
      <div id="checklist-container"><!-- JS 生成 --></div>
    </div>
  </section>

  <!-- ═══════════════ PRE-TRIP ESSENTIALS ═══════════════ -->
  <section class="section">
    <div class="section-header">
      <div class="section-icon gold">🌤️</div>
      <div>
        <div class="section-title">行前须知</div>
        <div class="section-subtitle">Pre-Trip · 9 月末山西定制</div>
      </div>
    </div>
    <div class="section-body" id="pretrip-container"></div>
  </section>

  <!-- ═══════════════ HOTELS ═══════════════ -->
  <section class="section">
    <div class="section-header">
      <div class="section-icon indigo">🏨</div>
      <div>
        <div class="section-title">住宿推荐 · 按片区价位</div>
        <div class="section-subtitle">Hotel Areas · 代县/浑源/大同/太原/临汾</div>
      </div>
    </div>
    <div class="section-body" id="hotels-container"></div>
  </section>

  <!-- ═══════════════ VIEW TOGGLE (fixed) ═══════════════ -->
  <div class="view-toggle" id="view-toggle">
    <button type="button" class="view-toggle__btn active" data-mode="tabs">▤ 标签页</button>
    <button type="button" class="view-toggle__btn" data-mode="timeline">≡ 时间轴</button>
  </div>

  <!-- ═══════════════ DAILY TIMELINE ═══════════════ -->
  <section class="section">
    <div class="section-header">
      <div class="section-icon purple">📅</div>
      <div>
        <div class="section-title">每日时间轴</div>
        <div class="section-subtitle">Day-by-Day Timeline · 7 天</div>
      </div>
    </div>
    <div class="section-body">
      <div id="day-tabs"></div>
      <div id="day-blocks"></div>
    </div>
  </section>

  <!-- ═══════════════ TIPS ═══════════════ -->
  <section class="section">
    <div class="section-header">
      <div class="section-icon gold">💡</div>
      <div>
        <div class="section-title">全程实用贴士</div>
        <div class="section-subtitle">Tips · 14 条实战经验</div>
      </div>
    </div>
    <div class="section-body" id="tips-container"></div>
  </section>

  <!-- ═══════════════ ADJUSTMENTS (folded) ═══════════════ -->
  <section class="adjustments-wrap">
    <details class="adjustments">
      <summary class="adjustments__summary">▸ 如果要加觉山寺（小西天/壶口已排入主行程），应该在哪些地方调整？</summary>
      <div class="adjustments__body" id="adjustments-body"></div>
    </details>
  </section>

  <!-- ═══════════════ CLOSURE AUDIT ═══════════════ -->
  <section class="adjustments-wrap">
    <details class="adjustments">
      <summary class="adjustments__summary">▸ 核心古建 2026-10 前后闭馆 / 调整公告</summary>
      <div class="adjustments__body" id="closure-body"></div>
    </details>
  </section>

  <!-- ═══════════════ FLIGHTS (folded) ═══════════════ -->
  <section class="adjustments-wrap">
    <details class="adjustments">
      <summary class="adjustments__summary">▸ 推荐航班 · 待选班次（参考 · 需自核）</summary>
      <div class="adjustments__body">
        <p class="adjustments__note">去程 9/26 周六早班（广州 → 朔州）、返程 10/2 周五下午班（太原 → 广州）。班期/票价均可能变动，**务必自行查询实时信息并核实**——本页遵循「不查实时票价」红线，仅给参考班次与时段。</p>
        <div class="flight-block-label">✈ 去程 · 广州 (CAN) → 朔州 (SZV) · 2026-09-26（周六）</div>
        <div id="outbound-flights"></div>
        <div class="flight-block-label">✈ 返程 · 太原 (TYN) → 广州 (CAN) · 2026-10-02（周五）</div>
        <div id="return-flights"></div>
      </div>
    </details>
  </section>

  <!-- ═══════════════ DISCLOSURE ═══════════════ -->
  <section class="disclosure">
    <strong>免责声明 · </strong><span>{trip['disclaimer']}</span>
  </section>

  <!-- ═══════════════ NAV JUMP ═══════════════ -->
  <div class="nav-jump">
    <span class="nav-jump__label">// 切换行程版本</span>
    <a href="shanxi-sz2.html" class="nav-jump__btn active" aria-disabled="true">7 天朔州进·太原出（当前）</a>
    <a href="shanxi-sz.html" class="nav-jump__btn">6 天反向/原版（保留）</a>
    <a href="index.html" class="nav-jump__btn">GitHub 首页</a>
  </div>

  <footer>
    <div class="footer-cta">山西古建 · 七日朝圣</div>
    <div class="footer-line">Generated by Migo · travel-plan-viz</div>
    <div class="footer-line">所有信息仅供参考 · 出行前请核实</div>
  </footer>

</div>

<!-- ═══════════════ TRIP DATA ═══════════════ -->
<script id="trip-data" type="application/json">{trip_json}</script>

<!-- ═══════════════ LEAFLET ═══════════════ -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<!-- ═══════════════ ENGINES (inlined) ═══════════════ -->
<script>{engines['map.js']}</script>
<script>{engines['reminders.js']}</script>
<script>{engines['weather.js']}</script>
<script>{engines['nav-buttons.js']}</script>
<script>{engines['day-coloring.js']}</script>

<!-- ═══════════════ INIT SCRIPT ═══════════════ -->
<script>
{INIT_SCRIPT}
</script>

</body>
</html>
"""


# ==================================================================
# CSS — 古建美学 · 深底 + 黄铜
# ==================================================================
CSS_MAIN = """
:root {
  --bg-deep: #1a1410;
  --bg-mid: #2a1f15;
  --bg-soft: #3a2e22;
  --bg-card: #2a1f15;
  --bg-card-soft: #3a2e22;
  --parchment: #f7f2e8;
  --parchment-dim: #d4c8b5;
  --gold: #b8862e;
  --gold-lt: #d4a04c;
  --cinnabar: #b8392e;
  --jade: #2a6f5f;
  --indigo: #1f3a6e;
  --purple: #8a4b8f;
  --border: rgba(184,134,46,0.25);
  --border-soft: rgba(184,134,46,0.12);
  --shadow: 0 2px 16px rgba(0,0,0,0.4);
  --shadow-hover: 0 8px 32px rgba(0,0,0,0.6);
  --radius: 14px;
  --radius-lg: 22px;

  /* day colors (overridden per day via [data-day-N] selectors) */
  --day1: #b8392e;
  --day1-light: rgba(184,57,46,0.10);
  --day2: #b8862e;
  --day2-light: rgba(184,134,46,0.10);
  --day3: #1f3a6e;
  --day3-light: rgba(31,58,110,0.10);
  --day4: #2a6f5f;
  --day4-light: rgba(42,111,95,0.10);
  --day5: #8a4b8f;
  --day5-light: rgba(138,75,143,0.10);
  --day6: #6b4a2b;
  --day6-light: rgba(107,74,43,0.10);
  --day7: #6b6b6b;
  --day7-light: rgba(107,107,107,0.10);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { min-height: 100vh; }
body {
  background: linear-gradient(160deg, #1a1410 0%, #2a1f15 60%, #3a2e22 100%);
  color: var(--parchment);
  font-family: 'Noto Serif SC', serif;
  font-size: 14px;
  line-height: 1.7;
  background-attachment: fixed;
}
a { color: var(--gold-lt); text-decoration: none; }
a:hover { color: var(--gold); text-decoration: underline; }

/* layout */
.page-wrap { max-width: 460px; margin: 0 auto; padding: 0 0 60px; }
@media (min-width: 768px) {
  .page-wrap { max-width: 920px; padding: 0 24px 80px; }
}

/* HERO */
.hero {
  background: linear-gradient(160deg, #1a1410 0%, #2a1f15 60%, #3a2e22 100%);
  padding: 56px 24px 36px;
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid var(--border);
}
.hero::before {
  content: '晋';
  position: absolute;
  top: -30px; right: -10px;
  font-family: 'Ma Shan Zheng', cursive;
  font-size: 280px;
  color: rgba(184,134,46,0.06);
  line-height: 1;
  pointer-events: none;
}
.hero-eyebrow {
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--gold-lt);
  margin-bottom: 12px;
  position: relative; z-index: 1;
}
.hero-title {
  font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
  font-size: 36px;
  line-height: 1.15;
  color: var(--parchment);
  margin-bottom: 14px;
  position: relative; z-index: 1;
  letter-spacing: 0.04em;
}
.hero-title .accent {
  color: var(--gold-lt);
  font-family: 'Ma Shan Zheng', cursive;
  font-size: 0.55em;
  vertical-align: middle;
  margin-left: 6px;
}
.hero-sub {
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.18em;
  color: rgba(247,242,232,0.55);
  text-transform: uppercase;
  position: relative; z-index: 1;
  margin-bottom: 16px;
}
.hero-meta { display: flex; flex-wrap: wrap; gap: 8px; position: relative; z-index: 1; }
.hero-badge {
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 100px;
  border: 1px solid var(--border);
  background: rgba(184,134,46,0.08);
  color: var(--parchment-dim);
}

/* SECTIONS */
.section { margin: 24px 16px; padding: 20px 22px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow); }
@media (min-width: 768px) {
  .section { padding: 28px 32px; }
}
.section-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.section-icon {
  width: 36px; height: 36px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
}
.section-icon.cinnabar { background: rgba(184,57,46,0.15); color: var(--cinnabar); }
.section-icon.gold { background: rgba(184,134,46,0.15); color: var(--gold-lt); }
.section-icon.jade { background: rgba(42,111,95,0.15); color: #6fbf97; }
.section-icon.indigo { background: rgba(31,58,110,0.15); color: #7090c8; }
.section-icon.purple { background: rgba(138,75,143,0.15); color: #c690cf; }
.section-title { font-family: 'Noto Serif SC', serif; font-weight: 700; font-size: 16px; color: var(--parchment); }
.section-subtitle { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--parchment-dim); margin-top: 2px; }
.section-body { color: var(--parchment); }
.section-body h3 { font-size: 15px; color: var(--gold-lt); margin: 16px 0 8px; font-weight: 700; }
.section-body p { margin-bottom: 8px; }
.section-body ul { padding-left: 20px; margin-bottom: 12px; }
.section-body ul li { margin-bottom: 4px; }

/* PRE-TRIP CHECKLIST */
.checklist-item { padding: 10px 0; border-bottom: 1px dashed var(--border-soft); display: flex; align-items: center; gap: 10px; }
.checklist-item:last-child { border-bottom: 0; }
.checklist-box { width: 18px; height: 18px; border-radius: 4px; border: 1.5px solid var(--gold); flex-shrink: 0; }
.checklist-text { flex: 1; font-size: 13px; }
.checklist-days { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--gold-lt); flex-shrink: 0; }

/* HOTEL AREA */
.hotel-area { padding: 14px 0; border-bottom: 1px dashed var(--border-soft); }
.hotel-area:last-child { border-bottom: 0; }
.hotel-area-name { font-family: 'Noto Serif SC', serif; font-weight: 700; color: var(--gold-lt); font-size: 15px; margin-bottom: 4px; }
.hotel-area-reason { font-size: 12px; color: var(--parchment-dim); margin-bottom: 10px; line-height: 1.6; }
.hotel-options { display: grid; gap: 8px; }
@media (min-width: 768px) {
  .hotel-options { grid-template-columns: 1fr 1fr 1fr; }
}
.hotel-opt { padding: 10px 12px; background: var(--bg-card-soft); border-radius: var(--radius); border-left: 2px solid var(--gold); }
.hotel-tier { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--gold-lt); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 2px; }
.hotel-opt-name { font-size: 13px; font-weight: 600; color: var(--parchment); margin-bottom: 2px; }
.hotel-opt-price { font-family: 'DM Mono', monospace; font-size: 11px; color: var(--gold); margin-bottom: 2px; }
.hotel-opt-note { font-size: 11px; color: var(--parchment-dim); }

/* MAP */
.map { height: 360px; border-radius: var(--radius); border: 1px solid var(--border); background: var(--bg-mid); }
@media (min-width: 768px) { .map { height: 480px; } }

/* DAY TABS */
.day-tabs { display: flex; gap: 6px; overflow-x: auto; margin-bottom: 16px; padding-bottom: 4px; }
.day-tab {
  flex-shrink: 0;
  padding: 8px 14px;
  border-radius: 100px;
  border: 1px solid var(--border);
  background: var(--bg-card-soft);
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--parchment-dim);
}
.day-tab.active { color: var(--parchment); }
.day-tab:hover { border-color: var(--gold); }

/* DAY BLOCK */
.day-block {
  padding: 16px 18px;
  margin-bottom: 16px;
  background: var(--bg-card-soft);
  border-radius: var(--radius);
  border-left: 3px solid;
}
.day-block h3 {
  font-family: 'Noto Serif SC', serif;
  font-weight: 700;
  font-size: 16px;
  margin-bottom: 4px;
  color: var(--parchment);
}
.day-block .day-meta { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--parchment-dim); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px; }
.day-tips { padding: 10px 12px; background: rgba(184,134,46,0.06); border-radius: 8px; margin-bottom: 12px; font-size: 12px; color: var(--parchment-dim); }
.day-tips li { margin-bottom: 4px; }

/* SLOT CARD */
.slot-card { padding: 12px 14px; margin-bottom: 10px; background: var(--bg-card); border-radius: 10px; border: 1px solid var(--border-soft); position: relative; }
.slot-period { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--gold-lt); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 4px; }
.slot-name { font-weight: 700; color: var(--parchment); font-size: 14px; margin-bottom: 4px; }
.slot-time { font-family: 'DM Mono', monospace; font-size: 11px; color: var(--gold); margin-bottom: 6px; }
.slot-photo {
  width: 100%; height: 160px; border-radius: 8px; overflow: hidden;
  background: var(--bg-mid);
  margin-bottom: 8px;
  position: relative;
}
.slot-photo img { width: 100%; height: 100%; object-fit: cover; display: block; }
.slot-rating { font-family: 'DM Mono', monospace; font-size: 11px; color: var(--gold-lt); margin-bottom: 4px; }
.slot-review { font-size: 12px; color: var(--parchment-dim); margin-bottom: 6px; line-height: 1.6; }
.slot-meta { font-size: 11px; color: var(--parchment-dim); display: flex; flex-wrap: wrap; gap: 6px 12px; }
.slot-meta span::before { content: '·'; margin-right: 6px; color: var(--gold); }
.slot-meta span:first-child::before { content: ''; margin: 0; }
.slot-transport { padding: 8px 10px; background: rgba(0,0,0,0.2); border-radius: 6px; font-size: 11px; color: var(--parchment-dim); margin-top: 6px; }
.slot-nav-row { display: flex; gap: 6px; margin-top: 8px; }
.slot-nav-btn {
  padding: 5px 12px;
  border-radius: 100px;
  border: 1px solid var(--gold);
  background: rgba(184,134,46,0.10);
  color: var(--gold-lt);
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  cursor: pointer;
  text-decoration: none;
}
.slot-nav-btn:hover { background: rgba(184,134,46,0.25); color: var(--parchment); text-decoration: none; }

/* DINING */
.dining { padding: 10px 12px; background: var(--bg-card); border-radius: 10px; margin-top: 10px; border: 1px dashed var(--border); }
.dining-meal { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--gold-lt); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 2px; }
.dining-place { font-size: 12px; color: var(--parchment); margin-bottom: 4px; }
.dining-dishes { font-size: 11px; color: var(--parchment-dim); }
.dining-dishes .dish { display: inline-block; margin-right: 12px; }
.dining-dishes .dish-price { color: var(--gold); }

/* ALTERNATIVES */
.alternatives-block { padding: 12px 14px; background: rgba(138,75,143,0.08); border-radius: 10px; margin-top: 12px; border-left: 2px solid var(--purple); }
.alternatives-title { font-size: 12px; color: var(--purple); font-weight: 700; margin-bottom: 8px; letter-spacing: 0.05em; }
.alt-card { padding: 8px 10px; background: rgba(0,0,0,0.2); border-radius: 8px; margin-bottom: 6px; }
.alt-card:last-child { margin-bottom: 0; }
.alt-label { font-size: 11px; color: var(--gold-lt); font-weight: 700; margin-bottom: 4px; }
.alt-summary { font-size: 11px; color: var(--parchment-dim); }

/* TIPS */
.tip-item { padding: 8px 12px; background: var(--bg-card-soft); border-radius: 8px; margin-bottom: 6px; border-left: 2px solid var(--gold); font-size: 12px; color: var(--parchment); line-height: 1.6; }

/* ADJUSTMENTS (folded) */
.adjustments-wrap { margin: 16px; }
@media (min-width: 768px) { .adjustments-wrap { margin: 0 0 24px; } }
.adjustments {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.adjustments__summary {
  padding: 14px 18px;
  cursor: pointer;
  font-size: 13px;
  color: var(--gold-lt);
  font-weight: 600;
  user-select: none;
  list-style: none;
}
.adjustments__summary::-webkit-details-marker { display: none; }
.adjustments__summary::before { content: '▸ '; color: var(--gold); }
.adjustments[open] .adjustments__summary::before { content: '▾ '; }
.adjustments__body { padding: 0 18px 16px; font-size: 12px; color: var(--parchment-dim); }
.adjustments__note { padding: 8px 12px; background: rgba(184,57,46,0.06); border-radius: 6px; margin-bottom: 10px; line-height: 1.6; }

/* CLOSURE AUDIT */
.closure-item { padding: 10px 12px; background: rgba(0,0,0,0.2); border-radius: 8px; margin-bottom: 6px; border-left: 2px solid var(--gold); }
.closure-name { font-weight: 700; color: var(--parchment); font-size: 13px; margin-bottom: 2px; }
.closure-status { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--gold-lt); letter-spacing: 0.05em; margin-bottom: 4px; }
.closure-detail { font-size: 11px; color: var(--parchment-dim); line-height: 1.5; }

/* FLIGHTS */
.flight-block-label { font-family: 'DM Mono', monospace; font-size: 11px; color: var(--gold-lt); margin: 12px 0 8px; letter-spacing: 0.05em; }
.flight-card { padding: 10px 12px; background: var(--bg-card-soft); border-radius: 8px; margin-bottom: 8px; border-left: 2px solid var(--gold); }
.flight-label { font-weight: 700; color: var(--parchment); font-size: 13px; margin-bottom: 2px; }
.flight-code { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--gold-lt); margin-bottom: 4px; letter-spacing: 0.05em; }
.flight-time { font-family: 'DM Mono', monospace; font-size: 11px; color: var(--gold); margin-bottom: 4px; }
.flight-note { font-size: 11px; color: var(--parchment-dim); line-height: 1.5; }

/* DISCLOSURE */
.disclosure {
  margin: 24px 16px;
  padding: 14px 18px;
  background: rgba(184,57,46,0.05);
  border: 1px solid rgba(184,57,46,0.18);
  border-left: 3px solid var(--cinnabar);
  border-radius: var(--radius);
  font-size: 11px;
  color: var(--parchment-dim);
  line-height: 1.7;
}
.disclosure strong { color: var(--cinnabar); font-weight: 700; }

/* NAV JUMP */
.nav-jump { display: flex; flex-wrap: wrap; gap: 8px; padding: 16px 16px 0; align-items: center; }
.nav-jump__label { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--parchment-dim); letter-spacing: 0.1em; margin-right: 8px; }
.nav-jump__btn {
  padding: 6px 14px;
  border-radius: 100px;
  border: 1px solid var(--border);
  background: transparent;
  font-size: 11px;
  color: var(--parchment-dim);
}
.nav-jump__btn.active { border-color: var(--gold); color: var(--gold-lt); }
.nav-jump__btn:hover { border-color: var(--gold); color: var(--gold-lt); text-decoration: none; }

/* FOOTER */
footer { margin-top: 24px; padding: 24px 16px; border-top: 1px solid var(--border); text-align: center; }
.footer-cta { font-family: 'ZCOOL XiaoWei', serif; font-size: 16px; color: var(--gold-lt); margin-bottom: 6px; }
.footer-line { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--parchment-dim); letter-spacing: 0.05em; }

/* ROUTE PIN (map markers) — 基础圆形样式（按天描边见 day-coloring.css） */
.route-pin {
  background: var(--bg-deep) !important;
  border: 2px solid var(--gold) !important;
  border-radius: 50%;
  display: flex !important;
  align-items: center; justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.5);
}
.route-pin__num {
  font-family: 'DM Mono', monospace;
  font-size: 10px; font-weight: 500;
  color: var(--gold-lt);
  line-height: 1;
}

/* ROUTE CHIPS（地图下方点击站点） */
.route-chips {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 12px 0 4px;
  scrollbar-width: thin;
  scrollbar-color: rgba(184,134,46,0.3) transparent;
}
.route-chips::-webkit-scrollbar { height: 4px; }
.route-chips::-webkit-scrollbar-thumb { background: rgba(184,134,46,0.3); border-radius: 2px; }
.route-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  background: var(--bg-card-soft);
  border: 1px solid var(--border);
  border-radius: 100px;
  font-size: 12px;
  color: var(--parchment-dim);
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: all 0.18s ease;
}
.route-chip:hover { border-color: var(--gold); color: var(--parchment); transform: translateY(-1px); }
.route-chip.active { background: var(--bg-soft); color: var(--gold-lt); border-color: var(--gold); font-weight: 600; }
.route-chip__num {
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  color: var(--gold);
  background: rgba(184,134,46,0.12);
  border-radius: 50%;
  width: 20px; height: 20px;
  display: inline-flex;
  align-items: center; justify-content: center;
  flex-shrink: 0;
}
.route-chip.active .route-chip__num { background: var(--gold); color: var(--bg-deep); }
.route-chip__emoji { font-size: 13px; flex-shrink: 0; }

/* MAP DAY HIGHLIGHT（点天标签时其余 pin 变暗） */
.map-point-dim .route-pin { opacity: 0.25; transition: opacity 0.3s; }

/* SLOT CARD NAV BUTTONS */
.slot-nav-row__label {
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  color: var(--parchment-dim);
  letter-spacing: 0.08em;
  align-self: center;
}
.popup-nav-link {
  padding: 5px 12px;
  border-radius: 100px;
  border: 1px solid var(--gold);
  background: rgba(184,134,46,0.10);
  color: var(--gold-lt);
  font-family: 'DM Mono', monospace;
  font-size: 11px;
  cursor: pointer;
}
.popup-nav-link:hover { background: rgba(184,134,46,0.25); color: var(--parchment); }

/* VIEW TOGGLE（标签页 / 时间轴 切换） */
.view-toggle {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 1100;
  display: flex;
  gap: 0;
  background: var(--bg-soft);
  border-radius: 100px;
  padding: 4px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.5);
  border: 1px solid var(--border);
}
.view-toggle__btn {
  border: none;
  background: transparent;
  color: rgba(247,242,232,0.55);
  padding: 7px 14px;
  font-family: 'DM Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.12em;
  cursor: pointer;
  border-radius: 100px;
  transition: all 0.18s;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.view-toggle__btn.active { background: var(--gold); color: var(--bg-deep); font-weight: 700; }
.view-toggle__btn:hover:not(.active) { color: var(--parchment); }
@media (max-width: 480px) {
  .view-toggle { top: auto; bottom: 16px; right: 16px; left: 16px; justify-content: center; }
  .view-toggle__btn { flex: 1; justify-content: center; padding: 10px 12px; }
}

/* TIMELINE BOOKMARKS（时间轴右侧竖排圆点） */
#timeline-bookmarks {
  position: fixed;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1099;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.bookmark {
  width: 32px; height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--parchment-dim);
  font-family: 'DM Mono', monospace;
  font-size: 12px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.4);
  transition: all 0.18s;
  padding: 0;
}
.bookmark:hover { border-color: var(--gold); transform: scale(1.08); }
.bookmark.is-current-day { background: var(--gold); color: var(--bg-deep); border-color: var(--gold); font-weight: 700; }
@media (max-width: 767px) { #timeline-bookmarks { display: none; } }

/* utility */
img { max-width: 100%; }
"""


# ==================================================================
# INIT SCRIPT — runs after engines load
# ==================================================================
INIT_SCRIPT = r"""
(function () {
  'use strict';
  var trip = JSON.parse(document.getElementById('trip-data').textContent);
  var DAYS = trip.days;

  // 共享状态：travelMap/mapPoints 在下方 map 段赋值，供视图切换/高亮懒引用。
  var travelMap = null;
  var mapPoints = [];
  var currentDayIdx = 0;
  var currentViewMode = 'tabs';  // 'tabs' 一天一页 | 'timeline' 全部展开

  // 给每个 slot 挂上一个可导航点（用于导航链接预填出发地 from）。
  (function attachPrevNav() {
    var last = null;
    DAYS.forEach(function (day) {
      (day.slots || []).forEach(function (slot) {
        slot._prevNav = last;
        if (typeof slot.lat === 'number' && typeof slot.lng === 'number'
            && isFinite(slot.lat) && isFinite(slot.lng)) {
          last = { lat: slot.lat, lng: slot.lng, name: String(slot.name || '') };
        }
      });
    });
  })();

  // ----- 1. checklist -----
  var checklistData = computeReminders(trip.startDate, trip.reminders);
  var checklistEl = document.getElementById('checklist-container');
  if (checklistEl && typeof renderChecklistHTML === 'function') {
    checklistEl.innerHTML = renderChecklistHTML(checklistData);
  }

  // ----- 2. pretrip -----
  var pt = trip.preTrip || {};
  var pretripEl = document.getElementById('pretrip-container');
  if (pretripEl) {
    pretripEl.innerHTML = ''
      + '<h3>🌤 天气</h3><p>' + escapeHTML(pt.weather && pt.weather.summary || '') + '</p>'
      + (pt.weather && pt.weather.typhoon ? '<p style="color:var(--cinnabar);font-size:11px;">⚠ ' + escapeHTML(pt.weather.typhoon) + '</p>' : '')
      + '<h3>🎒 穿搭</h3><p>' + escapeHTML(pt.packing || '') + '</p>'
      + '<h3>💳 支付</h3><p>' + escapeHTML(pt.payment || '') + '</p>'
      + '<h3>📱 必备 App</h3><ul>' + (pt.apps || []).map(function (a) { return '<li>' + escapeHTML(a) + '</li>'; }).join('') + '</ul>'
      + '<h3>🎫 购票时机</h3><p>' + escapeHTML(pt.ticketTip || '') + '</p>';
  }

  // ----- 3. hotels -----
  var hotelsEl = document.getElementById('hotels-container');
  if (hotelsEl) {
    hotelsEl.innerHTML = (trip.hotelAreas || []).map(function (area) {
      return '<div class="hotel-area">'
        + '<div class="hotel-area-name">' + escapeHTML(area.area) + '</div>'
        + '<div class="hotel-area-reason">' + escapeHTML(area.reason || '') + '</div>'
        + '<div class="hotel-options">' + (area.options || []).map(function (o) {
            return '<div class="hotel-opt">'
              + '<div class="hotel-tier">' + escapeHTML(o.tier || '') + '</div>'
              + '<div class="hotel-opt-name">' + escapeHTML(o.name || '') + '</div>'
              + '<div class="hotel-opt-price">' + escapeHTML(o.priceRange || '') + '</div>'
              + '<div class="hotel-opt-note">' + escapeHTML(o.note || '') + '</div>'
              + '</div>';
          }).join('') + '</div></div>';
    }).join('');
  }

  // ----- 4. day tabs + blocks -----
  var tabsEl = document.getElementById('day-tabs');
  var blocksEl = document.getElementById('day-blocks');

  function renderSlotsHTML(day, dayIdx) {
    var html = '';
    (day.slots || []).forEach(function (slot) {
      var photoHTML = '';
      if (slot.photo) {
        var credit = slot.photoCredit && slot.photoCredit.author
          ? '<div style="position:absolute;right:6px;background:rgba(0,0,0,0.6);color:#f0c890;font-size:9px;padding:2px 6px;border-radius:3px;font-family:DM Mono,monospace;">📷 ' + escapeHTML(slot.photoCredit.author.split(',')[0]) + '</div>'
          : '';
        photoHTML = '<div class="slot-photo day-' + (dayIdx + 1) + '-bg">'
          + '<img src="' + escapeHTML(slot.photo) + '" alt="' + escapeHTML(slot.name) + '" loading="lazy" onerror="this.style.display=\'none\'">'
          + credit + '</div>';
      }
      var reviewHTML = slot.review ? '<div class="slot-review">' + escapeHTML(slot.review) + '</div>' : '';
      var ratingHTML = slot.rating > 0 ? '<div class="slot-rating">★ ' + slot.rating.toFixed(1) + ' / 5</div>' : '';
      var timeHTML = slot.time ? '<div class="slot-time">' + escapeHTML(slot.time) + '</div>' : '';
      var metaParts = [];
      if (slot.openingHours && slot.openingHours !== '全天' && slot.openingHours !== '—' && slot.openingHours !== '依航班') metaParts.push(slot.openingHours);
      if (slot.ticketPrice && slot.ticketPrice !== '—' && slot.ticketPrice !== '') metaParts.push(slot.ticketPrice);
      var metaHTML = metaParts.length ? '<div class="slot-meta">' + metaParts.map(function (m) { return '<span>' + escapeHTML(m) + '</span>'; }).join('') + '</div>' : '';
      var t = slot.transport || {};
      var transportHTML = (t.mode && t.mode !== '—') ? '<div class="slot-transport">🛣 ' + escapeHTML(t.mode || '') + ' · ' + escapeHTML(t.distance || '') + ' · ' + escapeHTML(t.duration || '') + ' · ' + escapeHTML(t.fare || '') + '</div>' : '';

      var navRowHTML = '';
      if (typeof renderSlotNavRow === 'function' && typeof slot.lat === 'number') {
        try { navRowHTML = renderSlotNavRow(slot, slot._prevNav); } catch (e) { navRowHTML = ''; }
      }

      var periodMap = { morning: '上午', noon: '中午', afternoon: '下午', evening: '晚上' };
      var periodZH = periodMap[slot.period] || slot.period;

      html += '<div class="slot-card day-' + (dayIdx + 1) + '-border">'
        + '<div class="slot-period">' + periodZH + '</div>'
        + '<div class="slot-name">' + escapeHTML(slot.name) + '</div>'
        + timeHTML
        + photoHTML
        + ratingHTML
        + reviewHTML
        + metaHTML
        + transportHTML
        + navRowHTML
        + '</div>';
    });
    return html;
  }

  function renderDiningHTML(day) {
    return (day.dining || []).map(function (d) {
      var dishes = (d.dishes || []).map(function (di) {
        return '<span class="dish">' + escapeHTML(di.name) + ' <span class="dish-price">' + escapeHTML(di.price) + '</span></span>';
      }).join('');
      return '<div class="dining">'
        + '<div class="dining-meal">' + escapeHTML(d.meal) + '</div>'
        + '<div class="dining-place">' + escapeHTML(d.place) + (d.hours && d.hours !== '—' ? ' · ' + escapeHTML(d.hours) : '') + '</div>'
        + '<div class="dining-dishes">' + dishes + '</div>'
        + '</div>';
    }).join('');
  }

  function renderAlternativesHTML(day) {
    if (!day.alternatives || !day.alternatives.length) return '';
    return '<div class="alternatives-block">'
      + '<div class="alternatives-title">🔀 路径二选一 / 三选一</div>'
      + day.alternatives.map(function (a) {
        return '<div class="alt-card">'
          + '<div class="alt-label">' + escapeHTML(a.label) + '</div>'
          + '<div class="alt-summary">' + escapeHTML(a.summary) + '</div>'
          + '</div>';
      }).join('')
      + '</div>';
  }

  function renderDayBlockHTML(day, dayIdx) {
    var n = dayIdx + 1;
    return '<div class="day-block day-' + n + '" id="day-block-' + dayIdx + '">'
      + '<h3>Day ' + n + ' · ' + escapeHTML(day.theme) + '</h3>'
      + '<div class="day-meta">' + escapeHTML(day.date) + ' · ' + escapeHTML(day.weekday) + '</div>'
      + (day.tips && day.tips.length
          ? '<ul class="day-tips">' + day.tips.map(function (t) { return '<li>' + escapeHTML(t) + '</li>'; }).join('') + '</ul>'
          : '')
      + renderSlotsHTML(day, dayIdx)
      + renderAlternativesHTML(day)
      + renderDiningHTML(day)
      + '</div>';
  }

  function renderAllDays() {
    if (blocksEl) blocksEl.innerHTML = DAYS.map(renderDayBlockHTML).join('');
  }

  function renderDayTabsHTML() {
    if (!tabsEl) return;
    tabsEl.innerHTML = DAYS.map(function (day, dayIdx) {
      var n = dayIdx + 1;
      return '<button type="button" class="day-tab day-tab--day-' + n + ' day-' + n + '" data-day-idx="' + dayIdx + '">'
        + '<span class="day-tab__num">Day ' + n + '</span> · ' + escapeHTML(day.date.slice(5)) + '</button>';
    }).join('');
  }

  function updateActiveTab(idx) {
    if (!tabsEl) return;
    tabsEl.querySelectorAll('.day-tab').forEach(function (t) {
      var i = parseInt(t.getAttribute('data-day-idx'), 10);
      if (i === idx) t.classList.add('active');
      else t.classList.remove('active');
    });
  }

  function showDayTab(idx, skipHighlight) {
    currentDayIdx = idx;
    if (blocksEl) blocksEl.innerHTML = renderDayBlockHTML(DAYS[idx], idx);
    updateActiveTab(idx);
    if (!skipHighlight) highlightDayOnMap(idx);
  }

  // ---- 视图切换（标签页 / 时间轴）----
  function setViewMode(mode, skipHighlight) {
    currentViewMode = mode;
    document.querySelectorAll('.view-toggle__btn').forEach(function (b) {
      if (b.getAttribute('data-mode') === mode) b.classList.add('active');
      else b.classList.remove('active');
    });
    if (mode === 'timeline') {
      renderAllDays();
      clearDayHighlights();
      buildTimelineBookmarks();
    } else {
      teardownTimelineBookmarks();
      showDayTab(currentDayIdx, skipHighlight);
    }
  }

  function buildTimelineBookmarks() {
    if (document.getElementById('timeline-bookmarks')) return;
    var rail = document.createElement('aside');
    rail.id = 'timeline-bookmarks';
    rail.setAttribute('aria-label', '快速跳转到某一天');
    DAYS.forEach(function (day, di) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'bookmark';
      btn.setAttribute('data-day-idx', String(di));
      btn.textContent = String(di + 1);
      rail.appendChild(btn);
    });
    document.body.appendChild(rail);
    if ('IntersectionObserver' in window) {
      var obs = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          var idx = parseInt(e.target.id.replace('day-block-', ''), 10);
          if (isNaN(idx)) return;
          document.querySelectorAll('#timeline-bookmarks .bookmark').forEach(function (b) {
            b.classList.toggle('is-current-day', parseInt(b.getAttribute('data-day-idx'), 10) === idx);
          });
        });
      }, { rootMargin: '-10% 0px -70% 0px', threshold: 0 });
      document.querySelectorAll('.day-block').forEach(function (b) { obs.observe(b); });
    }
  }

  function teardownTimelineBookmarks() {
    var rail = document.getElementById('timeline-bookmarks');
    if (rail) rail.parentNode.removeChild(rail);
  }

  function initViewToggle() {
    var vt = document.getElementById('view-toggle');
    if (vt) {
      vt.addEventListener('click', function (e) {
        var btn = e.target.closest('button[data-mode]');
        if (!btn) return;
        var mode = btn.getAttribute('data-mode');
        if (mode !== currentViewMode) setViewMode(mode);
      });
    }
    if (tabsEl) {
      tabsEl.addEventListener('click', function (e) {
        var btn = e.target.closest('.day-tab');
        if (!btn) return;
        var idx = parseInt(btn.getAttribute('data-day-idx'), 10);
        if (isNaN(idx)) return;
        if (currentViewMode === 'tabs') {
          showDayTab(idx);
        } else {
          currentDayIdx = idx;
          updateActiveTab(idx);
          highlightDayOnMap(idx);
          var block = document.getElementById('day-block-' + idx);
          if (block) block.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    }
    document.body.addEventListener('click', function (e) {
      var btn = e.target.closest('.bookmark');
      if (!btn) return;
      var idx = parseInt(btn.getAttribute('data-day-idx'), 10);
      if (isNaN(idx)) return;
      var target = document.getElementById('day-block-' + idx);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  // ----- 5. tips -----
  var tipsEl = document.getElementById('tips-container');
  if (tipsEl) {
    tipsEl.innerHTML = (trip.tips || []).map(function (t) {
      return '<div class="tip-item">' + escapeHTML(t) + '</div>';
    }).join('');
  }

  // ----- 6. closure audit -----
  var closureEl = document.getElementById('closure-body');
  if (closureEl && trip.closureAudit && trip.closureAudit.items) {
    closureEl.innerHTML = (trip.closureAudit.items || []).map(function (it) {
      return '<div class="closure-item">'
        + '<div class="closure-name">' + escapeHTML(it.name) + '</div>'
        + '<div class="closure-status">' + escapeHTML(it.status || '') + (it.source ? ' · ' + escapeHTML(it.source) : '') + '</div>'
        + '<div class="closure-detail">' + escapeHTML(it.detail || '') + '</div>'
        + '</div>';
    }).join('')
      + '<div class="adjustments__note">⚠ ' + escapeHTML(trip.closureAudit.method || '出行前请再核实') + '</div>';
  }

  // ----- 7. flights -----
  function renderFlights(containerId, list, title) {
    var el = document.getElementById(containerId);
    if (!el) return;
    if (!list || !list.length) {
      el.innerHTML = '<div class="flight-card"><div class="flight-note">（暂无' + title + '班次）</div></div>';
      return;
    }
    el.innerHTML = list.map(function (f) {
      return '<div class="flight-card">'
        + '<div class="flight-label">' + escapeHTML(f.label || '') + '</div>'
        + (f.code ? '<div class="flight-code">' + escapeHTML(f.code) + '</div>' : '')
        + '<div class="flight-time">' + escapeHTML(f.time || '') + '</div>'
        + (f.note ? '<div class="flight-note">' + escapeHTML(f.note) + '</div>' : '')
        + '</div>';
    }).join('');
  }
  renderFlights('outbound-flights', (trip.flights && trip.flights.candidates && trip.flights.candidates.outbound) || [], '去程');
  var retList = (trip.flights && trip.flights.booked || []).concat(trip.flights && trip.flights.candidates && trip.flights.candidates.return || []);
  renderFlights('return-flights', retList, '返程');

  // ----- 8. map -----
  DAYS.forEach(function (day, dayIdx) {
    (day.slots || []).forEach(function (slot) {
      if (typeof slot.lat === 'number' && typeof slot.lng === 'number' && !slot.hideFromMap) {
        mapPoints.push({ lat: slot.lat, lng: slot.lng, name: slot.name, time: slot.time, day: day.date });
      }
    });
  });
  mapPoints = (typeof attachDayIdx === 'function') ? attachDayIdx(trip, mapPoints) : mapPoints;
  if (typeof initTravelMap === 'function') {
    try {
      travelMap = initTravelMap('map', mapPoints, {
        tileUrl: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
        attribution: '© OpenStreetMap contributors · © CARTO',
        dayColor: (typeof dayColor === 'function') ? dayColor : undefined
      });

      // 缩放与位移限制：maxBounds 硬墙 + 黏度 + maxZoom/minZoom
      if (travelMap && typeof L !== 'undefined' && mapPoints.length >= 2) {
        var lats = mapPoints.map(function (p) { return p.lat; });
        var lngs = mapPoints.map(function (p) { return p.lng; });
        var latLngs = lats.map(function (lat, i) { return [lat, lngs[i]]; });
        var pointBounds = L.latLngBounds(latLngs);
        var paddedBounds = pointBounds.pad(0.3);
        travelMap.setMaxBounds(paddedBounds);
        travelMap.options.maxBoundsViscosity = 1.0;
        travelMap.options.maxZoom = 19;
        travelMap.options.minZoom = travelMap.getZoom();
      } else if (travelMap) {
        travelMap.options.maxZoom = 19;
      }
    } catch (e) {
      document.getElementById('map').innerHTML = '<div style="padding:60px 20px;text-align:center;color:var(--parchment-dim);">地图加载失败（可能离线）</div>';
    }
  }

  // 地图按日高亮：dim 全部 pin + 画当天高亮折线 + 缩放到当天点位
  function highlightDayOnMap(idx) {
    if (!travelMap) return;
    var day = DAYS[idx];
    var dayCoords = (day.slots || []).filter(function (s) {
      return typeof s.lat === 'number' && typeof s.lng === 'number' && !s.hideFromMap;
    }).map(function (s) { return L.latLng(s.lat, s.lng); });
    if (window.__dayHighlightLine) {
      travelMap.removeLayer(window.__dayHighlightLine);
      window.__dayHighlightLine = null;
    }
    if (dayCoords.length === 0) { clearDayHighlights(); return; }
    var mapEl = document.getElementById('map');
    if (mapEl) mapEl.classList.add('map-point-dim');
    window.__dayHighlightLine = L.polyline(dayCoords, {
      color: (typeof dayColor === 'function') ? dayColor(idx) : '#b8392e',
      weight: 4,
      opacity: 0.9
    }).addTo(travelMap);
    if (dayCoords.length === 1) {
      travelMap.setView(dayCoords[0], Math.max(travelMap.getZoom(), 12));
    } else {
      travelMap.fitBounds(L.latLngBounds(dayCoords), { padding: [60, 60], maxZoom: 13 });
    }
  }

  function clearDayHighlights() {
    var mapEl = document.getElementById('map');
    if (mapEl) mapEl.classList.remove('map-point-dim');
    if (travelMap && window.__dayHighlightLine) {
      travelMap.removeLayer(window.__dayHighlightLine);
      window.__dayHighlightLine = null;
    }
  }

  // ----- 8b. route chips（地图下方点击站点） -----
  var activeChipIdx = 0;
  var routeCache = {};
  var animCancel = null;

  function chipEmoji(name) {
    if (!name) return '📍';
    if (name.includes('机场')) return '✈️';
    if (name.includes('长城') || name.includes('雁门关')) return '🏰';
    if (name.includes('木塔')) return '🗼';
    if (name.includes('云冈') || name.includes('石窟')) return '⛩️';
    if (name.includes('壶口')) return '🌊';
    if (name.includes('恒山')) return '⛰️';
    if (name.includes('寺')) return '🏯';
    if (name.includes('高铁') || name.includes('返程')) return '🚄';
    if (name.includes('夜宿')) return '🏨';
    return '📍';
  }

  function haversineKm(lat1, lng1, lat2, lng2) {
    var R = 6371;
    var toRad = function (d) { return d * Math.PI / 180; };
    var dLat = toRad(lat2 - lat1), dLng = toRad(lng2 - lng1);
    var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) * Math.sin(dLng / 2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  function durationForDistance(km) {
    if (km < 5) return 0.8;
    if (km > 200) return 3.0;
    if (km <= 50) return 0.8 + (km - 5) * (1.0 / 45);
    return 1.8 + (km - 50) * (1.2 / 150);
  }

  function fetchRoute(fromIdx, toIdx) {
    var a = mapPoints[fromIdx], b = mapPoints[toIdx];
    var key = a.lng + ',' + a.lat + ';' + b.lng + ',' + b.lat;
    if (routeCache[key]) return Promise.resolve(routeCache[key]);
    var url = 'https://router.project-osrm.org/route/v1/driving/' + a.lng + ',' + a.lat + ';' + b.lng + ',' + b.lat + '?overview=full&geometries=geojson';
    return fetch(url, { mode: 'cors' })
      .then(function (r) { if (!r.ok) throw new Error('OSRM HTTP ' + r.status); return r.json(); })
      .then(function (data) {
        if (data.code !== 'Ok' || !data.routes || !data.routes.length) throw new Error('OSRM no route');
        var coords = data.routes[0].geometry.coordinates;
        routeCache[key] = coords;
        return coords;
      })
      .catch(function (err) {
        console.warn('OSRM 失败，回退直线:', err.message);
        var mid = [(a.lng + b.lng) / 2, (a.lat + b.lat) / 2];
        var fallback = [[a.lng, a.lat], mid, [b.lng, b.lat]];
        routeCache[key] = fallback;
        return fallback;
      });
  }

  function setActiveChip(idx) {
    activeChipIdx = idx;
    document.querySelectorAll('.route-chip').forEach(function (el) {
      var i = parseInt(el.getAttribute('data-idx'), 10);
      if (i === idx) el.classList.add('active');
      else el.classList.remove('active');
    });
  }

  function flyAlongRoute(fromIdx, toIdx) {
    if (!travelMap) return;
    if (fromIdx === toIdx) {
      var p = mapPoints[toIdx];
      travelMap.flyTo([p.lat, p.lng], Math.max(travelMap.getZoom(), 11), { duration: 0.6 });
      setActiveChip(toIdx);
      return;
    }
    if (animCancel) animCancel.cancelled = true;
    var token = { cancelled: false };
    animCancel = token;
    setActiveChip(toIdx);
    fetchRoute(fromIdx, toIdx).then(function (coords) {
      if (token.cancelled) return;
      var km = haversineKm(mapPoints[fromIdx].lat, mapPoints[fromIdx].lng, mapPoints[toIdx].lat, mapPoints[toIdx].lng);
      var dur = durationForDistance(km) * 1000;
      var startTs = null;
      var targetZoom = Math.max(travelMap.getZoom(), km < 30 ? 12 : 9);
      function step(ts) {
        if (token.cancelled) return;
        if (startTs === null) startTs = ts;
        var t = (ts - startTs) / dur;
        if (t >= 1) {
          var last = coords[coords.length - 1];
          travelMap.setView([last[1], last[0]], targetZoom, { animate: false });
          return;
        }
        var idx = t * (coords.length - 1);
        var i0 = Math.floor(idx);
        var i1 = Math.min(coords.length - 1, i0 + 1);
        var frac = idx - i0;
        var c0 = coords[i0], c1 = coords[i1];
        var lng = c0[0] + (c1[0] - c0[0]) * frac;
        var lat = c0[1] + (c1[1] - c0[1]) * frac;
        travelMap.setView([lat, lng], targetZoom, { animate: false });
        requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  }

  function renderRouteChips() {
    var container = document.getElementById('route-chips');
    if (!container) return;
    var html = '';
    mapPoints.forEach(function (p, i) {
      html += '<button type="button" class="route-chip route-chip--day-' + ((p.dayIdx || 0) + 1) + (i === 0 ? ' active' : '')
        + '" data-idx="' + i + '">'
        + '<span class="route-chip__num">' + (i + 1) + '</span>'
        + '<span class="route-chip__emoji">' + chipEmoji(p.name) + '</span>'
        + '<span>' + escapeHTML(p.name) + '</span>'
        + '</button>';
    });
    container.innerHTML = html;
    container.addEventListener('click', function (e) {
      var btn = e.target.closest('.route-chip');
      if (!btn) return;
      var idx = parseInt(btn.getAttribute('data-idx'), 10);
      if (isNaN(idx)) return;
      flyAlongRoute(activeChipIdx, idx);
    });
  }
  renderRouteChips();

  // ----- 9. nav buttons -----
  if (typeof initNavButtons === 'function') {
    try { initNavButtons(); } catch (e) {}
  }

  // ----- 10. weather -----
  if (typeof fetchAllWeather === 'function') {
    try { fetchAllWeather(trip); } catch (e) {}
  }

  // ----- init: 渲染时间轴 + 视图切换（默认标签页一天一页，初始不高亮地图） -----
  renderDayTabsHTML();
  initViewToggle();
  setViewMode('tabs', true);
})();
"""


# ==================================================================
# Main
# ==================================================================
if __name__ == "__main__":
    trip = load_trip()
    html = render_html(trip)
    OUT.write_text(html)
    print(f"OK: {OUT} ({len(html)} bytes, {len(trip['days'])} days)")