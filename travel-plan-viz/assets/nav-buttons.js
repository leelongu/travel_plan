// 导航按钮组件：高德/百度路径规划按钮 + 平台分流 + document 级委托。
// 浏览器与 Node 双用（Node 下 render 返回 HTML 字符串、委托不绑定）。
// 内联到 HTML 后任何 button.popup-nav-link[data-nav-lat] 都会被自动接管。

// HTML 转义（与 map.js/reminders.js/weather.js 重复属故意，CLAUDE.md 要求）
function navEscapeHTML(s) {
  return String(s)
    .replace(/&/g, '&')
    .replace(/</g, '<')
    .replace(/>/g, '>')
    .replace(/"/g, '"')
    .replace(/'/g, '&#39;');
}

// ── WGS-84 → GCJ-02（百度 direction / baidumap:// scheme 要求 GCJ-02） ──
// 复刻自 map.js；保留独立副本避免依赖顺序（CLAUDE.md 红线）。
var NAV_GCJ_A = 6378245.0;
var NAV_GCJ_EE = 0.00669342162296594323;
function navIsInChinaBBox(lat, lng) {
  return lng >= 72.004 && lng <= 137.8347 && lat >= 0.8293 && lat <= 55.8271;
}
function navGcjTransformLat(x, y) {
  var ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x));
  ret += (20.0 * Math.sin(6.0 * x * Math.PI) + 20.0 * Math.sin(2.0 * x * Math.PI)) * 2.0 / 3.0;
  ret += (20.0 * Math.sin(y * Math.PI) + 40.0 * Math.sin(y / 3.0 * Math.PI)) * 2.0 / 3.0;
  ret += (160.0 * Math.sin(y / 12.0 * Math.PI) + 320.0 * Math.sin(y * Math.PI / 30.0)) * 2.0 / 3.0;
  return ret;
}
function navGcjTransformLng(x, y) {
  var ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x));
  ret += (20.0 * Math.sin(6.0 * x * Math.PI) + 20.0 * Math.sin(2.0 * x * Math.PI)) * 2.0 / 3.0;
  ret += (20.0 * Math.sin(x * Math.PI) + 40.0 * Math.sin(x / 3.0 * Math.PI)) * 2.0 / 3.0;
  ret += (150.0 * Math.sin(x / 12.0 * Math.PI) + 300.0 * Math.sin(x / 30.0 * Math.PI)) * 2.0 / 3.0;
  return ret;
}
function navWgs84ToGcj02(lat, lng) {
  if (!navIsInChinaBBox(lat, lng)) return { lat: lat, lng: lng };
  var dLat = navGcjTransformLat(lng - 105.0, lat - 35.0);
  var dLng = navGcjTransformLng(lng - 105.0, lat - 35.0);
  var radLat = lat / 180.0 * Math.PI;
  var magic = Math.sin(radLat);
  magic = 1 - NAV_GCJ_EE * magic * magic;
  var sqrtMagic = Math.sqrt(magic);
  dLat = (dLat * 180.0) / ((NAV_GCJ_A * (1 - NAV_GCJ_EE)) / (magic * sqrtMagic) * Math.PI);
  dLng = (dLng * 180.0) / (NAV_GCJ_A / sqrtMagic * Math.cos(radLat) * Math.PI);
  return { lat: lat + dLat, lng: lng + dLng };
}

// 生成 slot 卡片底部"导航到此处"行的 HTML。
// slot 需含 lat/lng/name；返回字符串可直接拼到 render 输出。
function renderSlotNavRow(slot, from) {
  if (!slot || typeof slot.lat !== 'number' || typeof slot.lng !== 'number'
      || !isFinite(slot.lat) || !isFinite(slot.lng)) return '';
  var lat = slot.lat, lng = slot.lng, name = navEscapeHTML(String(slot.name || ''));
  var fromAttrs = (from && typeof from.lat === 'number' && typeof from.lng === 'number'
      && isFinite(from.lat) && isFinite(from.lng))
    ? ' data-nav-from-lat="' + from.lat + '" data-nav-from-lng="' + from.lng
      + '" data-nav-from-name="' + navEscapeHTML(String(from.name || '')) + '"'
    : '';
  return '<div class="slot-nav-row">'
    + '<span class="slot-nav-row__label">导航到此处</span>'
    + '<button type="button" class="popup-nav-link popup-nav-link--amap"'
      + ' data-nav-lat="' + lat + '" data-nav-lng="' + lng + '" data-nav-name="' + name + '"' + fromAttrs + '>高德地图</button>'
    + '<button type="button" class="popup-nav-link popup-nav-link--baidu"'
      + ' data-nav-lat="' + lat + '" data-nav-lng="' + lng + '" data-nav-name="' + name + '"' + fromAttrs + '>百度地图</button>'
    + '</div>';
}

// 生成 popup 里"导航/高德/百度"行的 HTML。依赖 buildNavLink（在 map.js 内联）。
// ua 可选；iOS 时第一个按钮也走 iosamap:// 唤起。
function renderPopupNavRow(lat, lng, name, ua, buildNavLink) {
  if (typeof lat !== 'number' || typeof lng !== 'number'
      || !isFinite(lat) || !isFinite(lng)) return '';
  var safeName = navEscapeHTML(String(name || ''));
  var navHref = buildNavLink ? buildNavLink(lat, lng, name, ua) : '#';
  return '<div class="popup-nav-row">'
    + '<a href="' + navEscapeHTML(navHref) + '" target="_blank" class="popup-nav-link popup-nav-link--default">导航</a>'
    + '<button type="button" class="popup-nav-link popup-nav-link--amap"'
      + ' data-nav-lat="' + lat + '" data-nav-lng="' + lng + '" data-nav-name="' + safeName + '">高德地图</button>'
    + '<button type="button" class="popup-nav-link popup-nav-link--baidu"'
      + ' data-nav-lat="' + lat + '" data-nav-lng="' + lng + '" data-nav-name="' + safeName + '">百度地图</button>'
    + '</div>';
}

// 平台分流：返回 { amapWeb, baiduWeb, iosAmap, iosBaidu }，调用方按 UA 选。
// ua 缺省时按 PC 处理。
function getNavLinks(lat, lng, label, ua, from) {
  var encLabel = encodeURIComponent(String(label || ''));
  var platform = (ua && /iPhone|iPad|iPod/.test(ua)) ? 'ios'
    : (ua && /Android/.test(ua)) ? 'android' : 'pc';
  var hasFrom = !!from && isFinite(Number(from.lat)) && isFinite(Number(from.lng));
  var amapWeb = 'https://uri.amap.com/navigation?to=' + lng + ',' + lat + ',' + encLabel
    + '&mode=car&policy=1&coordinate=wgs84&src=travel-plan-viz';
  if (hasFrom) {
    amapWeb = 'https://uri.amap.com/navigation?from=' + from.lng + ',' + from.lat
      + ',' + encodeURIComponent(String(from.name || ''))
      + '&to=' + lng + ',' + lat + ',' + encLabel
      + '&mode=car&policy=1&coordinate=wgs84&src=travel-plan-viz';
  }
  var gcj = navWgs84ToGcj02(lat, lng);
  var baiduWeb = 'https://api.map.baidu.com/direction?destination=' + gcj.lat + ',' + gcj.lng
    + '&destination_name=' + encLabel
    + '&mode=driving&region=cn&output=html&src=travel-plan-viz';
  if (hasFrom) {
    var fg = navWgs84ToGcj02(from.lat, from.lng);
    baiduWeb = 'https://api.map.baidu.com/direction?origin=' + fg.lat + ',' + fg.lng
      + '&origin_name=' + encodeURIComponent(String(from.name || ''))
      + '&destination=' + gcj.lat + ',' + gcj.lng
      + '&destination_name=' + encLabel
      + '&mode=driving&region=cn&output=html&src=travel-plan-viz';
  }
  var iosAmap = 'iosamap://navi?sourceApplication=travel-plan-viz&lat=' + lat
    + '&lon=' + lng + '&dev=0&style=2&name=' + encLabel;
  var iosBaidu = 'baidumap://map/navi?coord_type=gcj02&location=' + gcj.lat + ',' + gcj.lng
    + '&type=BLK&src=travel-plan-viz';
  return { platform: platform, amapWeb: amapWeb, baiduWeb: baiduWeb,
           iosAmap: iosAmap, iosBaidu: iosBaidu };
}

// document 级点击委托：捕获所有 button.popup-nav-link 点击。
// 调用方在 init 阶段执行一次即可。Node 环境跳过（无 document）。
function initNavButtons() {
  if (typeof document === 'undefined') return;
  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('button.popup-nav-link');
    if (!btn) return;
    e.preventDefault();
    var lat = parseFloat(btn.getAttribute('data-nav-lat'));
    var lng = parseFloat(btn.getAttribute('data-nav-lng'));
    var name = btn.getAttribute('data-nav-name') || '';
    if (!isFinite(lat) || !isFinite(lng)) return;
    var ua = navigator.userAgent || '';
    var flat = parseFloat(btn.getAttribute('data-nav-from-lat'));
    var flng = parseFloat(btn.getAttribute('data-nav-from-lng'));
    var from = null;
    if (isFinite(flat) && isFinite(flng)) {
      from = { lat: flat, lng: flng, name: btn.getAttribute('data-nav-from-name') || '' };
    }
    var nav = getNavLinks(lat, lng, name, ua, from);
    var isAmap = btn.classList.contains('popup-nav-link--amap');
    if (nav.platform === 'ios') {
      var ok = window.confirm('用 ' + (isAmap ? '高德地图' : '百度地图') + ' 开始路径规划？');
      if (!ok) return;
      var uri = isAmap ? nav.iosAmap : nav.iosBaidu;
      var web = isAmap ? nav.amapWeb : nav.baiduWeb;
      window.location.href = uri;
      setTimeout(function () { window.open(web, '_blank'); }, 1500);
    } else {
      window.open(isAmap ? nav.amapWeb : nav.baiduWeb, '_blank');
    }
  });
}

// ───────── Node 导出守卫 ─────────
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    renderSlotNavRow: renderSlotNavRow,
    renderPopupNavRow: renderPopupNavRow,
    getNavLinks: getNavLinks,
    initNavButtons: initNavButtons,
    navEscapeHTML: navEscapeHTML,
  };
}
