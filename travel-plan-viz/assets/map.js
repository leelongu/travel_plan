// Leaflet 地图引擎。纯函数（buildNavLink/buildMapAppLinks/routeCoordinates/gcj02ToWgs84）可单元测试；
// initTravelMap 需浏览器 + Leaflet (L)。浏览器与 Node 双用。

// HTML 转义，防止 XSS
function escapeHTML(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// 坐标兜底：恶意 lat/lng 可能含字符串、NaN/Infinity 等非数字，夹到合法范围。
// 来源若不可信（用户输入、AI 生成、第三方 skill），必须经此函数。
function _sanitizeLat(v) {
  var n = Number(v);
  if (!isFinite(n)) return 0;
  return Math.max(-90, Math.min(90, n));
}
function _sanitizeLng(v) {
  var n = Number(v);
  if (!isFinite(n)) return 0;
  return Math.max(-180, Math.min(180, n));
}

// 生成跳转手机地图导航的链接。
// iOS 不识别 geo: scheme，用 Apple Maps 的 https 通用链接；其余平台用 geo:。
// ua 可选（浏览器里传 navigator.userAgent），不传则回退 geo:。
// label 已 encodeURIComponent 编码；坐标经 _sanitizeLat/_sanitizeLng 夹到合法范围，
//   防恶意字符串/NaN 突破 URL 上下文注入。
function buildNavLink(lat, lng, label, ua) {
  var sLat = _sanitizeLat(lat);
  var sLng = _sanitizeLng(lng);
  var encLabel = encodeURIComponent(String(label));
  if (ua && /iPhone|iPad|iPod/.test(ua)) {
    return 'https://maps.apple.com/?ll=' + sLat + ',' + sLng + '&q=' + encLabel;
  }
  return 'geo:' + sLat + ',' + sLng + '?q=' + sLat + ',' + sLng + '(' + encLabel + ')';
}

// 常用地图 App 的导航/路径规划链接（免 key 的官方 URI 规范）。
// 这不是 page-contract 的 actionLink——不承载实时数据主张，只是"打开地图看这个点/开始路径规划"。
// 境内点给高德 + 百度（两者都要求 GCJ-02；用 coordinate=wgs84 / coord_type=wgs84 声明由其换算）；
// 境外点给 Google + 高德（高德全球可用，调用方按 UI 偏好展示）。
// 坐标经 _sanitizeLat/_sanitizeLng 兜底，防恶意字符串注入 URL 参数。
// mode: 'marker' = 只把这个点标在地图上；'navi' = 以这个点为目的地开始路径规划。
// isInChinaBBox 声明在下方 GCJ 区块（函数声明有提升，此处可用）。
function buildMapAppLinks(lat, lng, label, mode, from) {
  var sLat = _sanitizeLat(lat);
  var sLng = _sanitizeLng(lng);
  var encLabel = encodeURIComponent(String(label));
  mode = mode || 'marker';
  // 可选出发地 {lat, lng, name}：navi 模式预填 from，省去手动选出发地。
  var hasFrom = !!from && isFinite(Number(from.lat)) && isFinite(Number(from.lng));
  var amap;
  if (mode === 'navi') {
    var q = 'to=' + sLng + ',' + sLat + ',' + encLabel;
    if (hasFrom) {
      q = 'from=' + _sanitizeLng(from.lng) + ',' + _sanitizeLat(from.lat)
        + ',' + encodeURIComponent(String(from.name || '')) + '&' + q;
    }
    amap = {
      label: '高德地图',
      url: 'https://uri.amap.com/navigation?' + q
        + '&mode=car&policy=1&coordinate=wgs84&src=travel-plan-viz&callnative=1',
    };
  } else {
    amap = {
      label: '高德地图',
      url: 'https://uri.amap.com/marker?position=' + sLng + ',' + sLat
        + '&name=' + encLabel
        + '&coordinate=wgs84&callnative=1&src=travel-plan-viz',
    };
  }
  var baidu;
  if (mode === 'navi') {
    var gcj = wgs84ToGcj02(sLat, sLng);
    var bq = 'destination=' + gcj.lat + ',' + gcj.lng + '&destination_name=' + encLabel;
    if (hasFrom) {
      var fg = wgs84ToGcj02(_sanitizeLat(from.lat), _sanitizeLng(from.lng));
      bq = 'origin=' + fg.lat + ',' + fg.lng + '&origin_name='
        + encodeURIComponent(String(from.name || '')) + '&' + bq;
    }
    baidu = {
      label: '百度地图',
      url: 'https://api.map.baidu.com/direction?' + bq
        + '&mode=driving&region=cn&output=html&src=travel-plan-viz',
    };
  } else {
    baidu = {
      label: '百度地图',
      url: 'https://api.map.baidu.com/marker?location=' + sLat + ',' + sLng
        + '&title=' + encLabel + '&content=' + encLabel
        + '&output=html&coord_type=wgs84&src=travel-plan-viz',
    };
  }
  var google = {
    label: 'Google 地图',
    url: 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(sLat + ',' + sLng),
  };
  return isInChinaBBox(sLat, sLng) ? [amap, baidu] : [google, amap];
}

// 平台分流：PC / Android 直接打开网页端；iOS 先 confirm 询问用哪个地图 App，再调起 App 走"路径规划"模式。
// 返回 { platform, amapUrl, baiduUrl, iosAmapUri, iosBaiduUri } —— 调用方按 UA 选一组。
// iOS 走 Universal Link 不可行（高德/百度 Universal Link 国内不稳定），用官方 URI scheme；
// 若用户没装该 App，Safari 会弹"无法打开页面"，再走网页降级 URL 即可。
function getNavLinks(lat, lng, label, ua) {
  var sLat = _sanitizeLat(lat);
  var sLng = _sanitizeLng(lng);
  var encLabel = encodeURIComponent(String(label));
  var platform = (ua && /iPhone|iPad|iPod/.test(ua)) ? 'ios'
    : (ua && /Android/.test(ua)) ? 'android' : 'pc';
  // 高德网页导航（路径规划）—— coordinate=wgs84 声明由其自转 GCJ-02 显示
  var amapWeb = 'https://uri.amap.com/navigation?to=' + sLng + ',' + sLat + ',' + encLabel
    + '&mode=car&policy=1&coordinate=wgs84&src=travel-plan-viz';
  // 百度 scheme/direction 接口的 location/destination 解释为 GCJ-02；先转
  var gcj = wgs84ToGcj02(sLat, sLng);
  var baiduWeb = 'https://api.map.baidu.com/direction?destination=' + gcj.lat + ',' + gcj.lng
    + '&destination_name=' + encLabel
    + '&mode=driving&region=cn&output=html&src=travel-plan-viz';
  // iOS URI scheme（App 调起）
  var iosAmap = 'iosamap://navi?sourceApplication=travel-plan-viz&lat=' + sLat
    + '&lon=' + sLng + '&dev=0&style=2&name=' + encLabel;
  var iosBaidu = 'baidumap://map/navi?coord_type=gcj02&location=' + gcj.lat + ',' + gcj.lng
    + '&type=BLK&src=travel-plan-viz';
  return {
    platform: platform,
    amapWeb: amapWeb,
    baiduWeb: baiduWeb,
    iosAmap: iosAmap,
    iosBaidu: iosBaidu,
  };
}

// —— GCJ-02 → WGS-84 坐标转换 ——
// 高德/腾讯地图返回的坐标是 GCJ-02（国测局加密），直接画在 OSM（WGS-84）瓦片上
// 会偏移一百到几百米。凡坐标来自高德/腾讯类 skill，必须先经此函数转换。
// 中国境外坐标原样返回（GCJ-02 仅在境内加偏）。
var GCJ_A = 6378245.0;
var GCJ_EE = 0.00669342162296594323;

function isInChinaBBox(lat, lng) {
  return lng >= 72.004 && lng <= 137.8347 && lat >= 0.8293 && lat <= 55.8271;
}

function gcjTransformLat(x, y) {
  var ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x));
  ret += (20.0 * Math.sin(6.0 * x * Math.PI) + 20.0 * Math.sin(2.0 * x * Math.PI)) * 2.0 / 3.0;
  ret += (20.0 * Math.sin(y * Math.PI) + 40.0 * Math.sin(y / 3.0 * Math.PI)) * 2.0 / 3.0;
  ret += (160.0 * Math.sin(y / 12.0 * Math.PI) + 320.0 * Math.sin(y * Math.PI / 30.0)) * 2.0 / 3.0;
  return ret;
}

function gcjTransformLng(x, y) {
  var ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x));
  ret += (20.0 * Math.sin(6.0 * x * Math.PI) + 20.0 * Math.sin(2.0 * x * Math.PI)) * 2.0 / 3.0;
  ret += (20.0 * Math.sin(x * Math.PI) + 40.0 * Math.sin(x / 3.0 * Math.PI)) * 2.0 / 3.0;
  ret += (150.0 * Math.sin(x / 12.0 * Math.PI) + 300.0 * Math.sin(x / 30.0 * Math.PI)) * 2.0 / 3.0;
  return ret;
}

function gcj02ToWgs84(lat, lng) {
  if (!isInChinaBBox(lat, lng)) return { lat: lat, lng: lng };
  var dLat = gcjTransformLat(lng - 105.0, lat - 35.0);
  var dLng = gcjTransformLng(lng - 105.0, lat - 35.0);
  var radLat = lat / 180.0 * Math.PI;
  var magic = Math.sin(radLat);
  magic = 1 - GCJ_EE * magic * magic;
  var sqrtMagic = Math.sqrt(magic);
  dLat = (dLat * 180.0) / ((GCJ_A * (1 - GCJ_EE)) / (magic * sqrtMagic) * Math.PI);
  dLng = (dLng * 180.0) / (GCJ_A / sqrtMagic * Math.cos(radLat) * Math.PI);
  return { lat: lat - dLat, lng: lng - dLng };
}

// WGS-84 → GCJ-02（反向）。百度/腾讯地图使用 GCJ-02；先调用此函数再传百度 URI，
// 否则几百米偏移。境外点直接返回原值（GCJ-02 仅在境内加偏）。
function wgs84ToGcj02(lat, lng) {
  if (!isInChinaBBox(lat, lng)) return { lat: lat, lng: lng };
  var dLat = gcjTransformLat(lng - 105.0, lat - 35.0);
  var dLng = gcjTransformLng(lng - 105.0, lat - 35.0);
  var radLat = lat / 180.0 * Math.PI;
  var magic = Math.sin(radLat);
  magic = 1 - GCJ_EE * magic * magic;
  var sqrtMagic = Math.sqrt(magic);
  dLat = (dLat * 180.0) / ((GCJ_A * (1 - GCJ_EE)) / (magic * sqrtMagic) * Math.PI);
  dLng = (dLng * 180.0) / (GCJ_A / sqrtMagic * Math.cos(radLat) * Math.PI);
  return { lat: lat + dLat, lng: lng + dLng };
}

// 从有序点位提取 [lat,lng] 数组，用于连线
function routeCoordinates(points) {
  return points.map(function (p) { return [p.lat, p.lng]; });
}

// 初始化地图：编号 divIcon 标记、按序虚线路线、点击弹出 名称+时间+导航链接。
// elementId: 容器 id；points: [{lat, lng, name, time}]（按行程顺序，坐标须为 WGS-84）
// opts 可选：{ tileUrl, attribution } 替换默认瓦片源。
//
// 默认走 OpenTopoMap（OSM 衍生、免 key），不直连 tile.openstreetmap.org——
// 后者的 Tile Usage Policy 禁止第三方应用做"分发/批量加载"用途，
// 否则会触发 403。免 key 替代：
//   CyclOSM  'https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png'（骑行风格，maxZoom 20）
//   Stadia   'https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}.png'（公网部署需 key）
function initTravelMap(elementId, points, opts) {
  opts = opts || {};
  var map = L.map(elementId);
  L.tileLayer(opts.tileUrl || 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
    attribution: opts.attribution || '© OpenStreetMap contributors · Tiles by OpenTopoMap (CC-BY-SA)',
    maxZoom: 17,
  }).addTo(map);

  var ua = (typeof navigator !== 'undefined' && navigator.userAgent) || '';
  var prev = null;  // 上一个可导航点，作为下一段的出发地（预填 from）
  points.forEach(function (p, i) {
    // 来自 trip-data 的坐标/名称若不可信，先兜底再喂给 Leaflet / URL 拼接
    var sLat = _sanitizeLat(p.lat);
    var sLng = _sanitizeLng(p.lng);
    var dayCls = (typeof p.dayIdx === 'number') ? ' route-pin--day-' + p.dayIdx : '';
    var icon = L.divIcon({
      className: 'route-pin' + dayCls,
      html: '<span class="route-pin__num">' + (i + 1) + '</span>',
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });
    var navLinks = [{ label: '导航', url: buildNavLink(sLat, sLng, p.name, ua) }]
      .concat(buildMapAppLinks(sLat, sLng, p.name, 'navi', prev));
    L.marker([sLat, sLng], { icon: icon }).addTo(map).bindPopup(
      '<b>' + (i + 1) + '. ' + escapeHTML(String(p.name)) + '</b><br>'
      + (p.time ? escapeHTML(String(p.time)) + '<br>' : '')
      + navLinks.map(function (l) {
          return '<a href="' + l.url + '">' + escapeHTML(l.label) + '</a>';
        }).join(' · ')
    );
    prev = { lat: sLat, lng: sLng, name: String(p.name || '') };
  });

  var coords = routeCoordinates(points);
  // 折线：传了 dayColor 且点位带 dayIdx 时按天分色；否则单色虚线（原行为）。
  if (typeof opts.dayColor === 'function' && points.length && typeof points[0].dayIdx === 'number') {
    var byDay = {};
    points.forEach(function (p) {
      var d = p.dayIdx || 0;
      (byDay[d] = byDay[d] || []).push([_sanitizeLat(p.lat), _sanitizeLng(p.lng)]);
    });
    Object.keys(byDay).forEach(function (d) {
      var pts = byDay[d];
      if (pts.length > 1) {
        L.polyline(pts, { color: opts.dayColor(parseInt(d, 10)), weight: 2.5, opacity: 0.9 }).addTo(map);
      }
    });
  } else if (coords.length > 1) {
    L.polyline(coords, { dashArray: '6 8', weight: 2 }).addTo(map);
  }
  map.fitBounds(coords.length ? coords : [[0, 0]], { padding: [30, 30] });
  return map;
}

// 一键全天多点导航：构造高德 URI 导航链接（from=首 to=尾 via=中间多个）。
// points: [{lat, lng, name}]（按行程顺序，坐标须为 WGS-84）；不足 2 点返回 null。
// URL > 2000 字符降级为首点的 geo: 链接（避免部分 App/WebView 截断）。
function buildMultiPointNavLink(points) {
  if (!points || points.length < 2) return null;
  var first = points[0];
  var last = points[points.length - 1];
  var via = points.slice(1, -1);
  var url = 'https://uri.amap.com/navigation'
    + '?from=' + _sanitizeLng(first.lng) + ',' + _sanitizeLat(first.lat) + ',' + encodeURIComponent(String(first.name || ''))
    + '&to=' + _sanitizeLng(last.lng) + ',' + _sanitizeLat(last.lat) + ',' + encodeURIComponent(String(last.name || ''));
  if (via.length > 0) {
    var viaStr = via.map(function (p) { return _sanitizeLng(p.lng) + ',' + _sanitizeLat(p.lat); }).join(',');
    url += '&via=' + viaStr;
  }
  url += '&mode=car&src=travel-plan-viz';
  // 超长降级：直接给出首点的 geo: 链接，提示用户手动添加途经点
  if (url.length > 2000) {
    return buildNavLink(_sanitizeLat(first.lat), _sanitizeLng(first.lng), String(first.name || ''));
  }
  return url;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    buildNavLink: buildNavLink,
    buildMapAppLinks: buildMapAppLinks,
    routeCoordinates: routeCoordinates,
    gcj02ToWgs84: gcj02ToWgs84,
    wgs84ToGcj02: wgs84ToGcj02,
    initTravelMap: initTravelMap,
    buildMultiPointNavLink: buildMultiPointNavLink,
    getNavLinks: getNavLinks,
  };
}
