// 空白地帯マップ。data/map の JSON を読んで、地図と横（スマホでは下）の欄を描く。
// 欄の中身は URL の # で決まる。#s=銭湯、#q=検索、#t=タイプ、なにもなければ全体。
(function () {
  "use strict";
  var RADIUS = 1500;
  // 10分で行ける銭湯が多いほど、青を濃くする。1軒、2軒、3軒、4軒、5軒、6軒以上
  var IN_ALPHA = [0, 0.08, 0.16, 0.23, 0.3, 0.36, 0.42];
  var PANEL = 400;
  var $ = function (id) { return document.getElementById(id); };
  var wide = window.matchMedia("(min-width: 760px)");
  var body = $("body"), sheet = $("sheet"), input = $("q");
  var css = getComputedStyle(document.documentElement);
  var C = {};
  ["ink", "sub", "paper", "noren", "water", "land", "rail", "cover-in", "cover-out"].forEach(function (k) { C[k] = css.getPropertyValue("--" + k).trim(); });

  // ---------- 小さな道具 ----------
  // 銭湯の名前などは外から取ったデータなので、HTMLとして働かないようにしてから出す
  function esc(t) { return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function num(n) { return Number(n).toLocaleString("ja-JP"); }
  function km(m) { return m < 1000 ? m + "m" : (m / 1000).toFixed(1) + "km"; }
  function man(n) { return Math.round(n / 10000).toLocaleString("ja-JP") + "万"; }
  function norm(t) {
    return String(t || "").normalize("NFKC").toLowerCase().replace(/\s+/g, "")
      .replace(/[ァ-ヶ]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0x60); });
  }
  function icon(name) { return '<i data-lucide="' + name + '"></i>'; }
  function draw() { if (window.lucide) window.lucide.createIcons({ attrs: { "aria-hidden": "true" } }); }
  var toastTimer;
  function toast(text) {
    var t = $("toast");
    t.textContent = text;
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.hidden = true; }, 4000);
  }

  // ---------- 地図 ----------
  var map = L.map("gapmap", { zoomControl: false, zoomSnap: 0.5, minZoom: 9, maxZoom: 18 });
  map.setView([35.69, 139.6], 11);
  map.attributionControl.setPrefix(false);
  // 下に敷く地図。この地図で要るものだけを描く: 海と川、地上の線路、都県と区市の境目、区市の名前、駅の名前。
  // 道路、建物、お寺や学校などの記号、道路の番号、等高線、町の名前は描かない
  function baseStyle(part) {
    var font = ["NotoSansJP-Regular"];
    var surface = ["all", ["!", ["in", ["get", "vt_railstate"], ["literal", ["トンネル", "地下", "雪覆い"]]]], ["in", ["get", "vt_rtcode"], ["literal", ["JR", "JR以外", "路面"]]]];
    var style = {
      version: 8,
      glyphs: "https://gsi-cyberjapan.github.io/optimal_bvmap/glyphs/{fontstack}/{range}.pbf",
      sources: { v: { type: "vector", minzoom: 4, maxzoom: 16, tiles: ["https://cyberjapandata.gsi.go.jp/xyz/optimal_bvmap-v1/{z}/{x}/{y}.pbf"] } },
      layers: [
        { id: "bg", type: "background", paint: { "background-color": C.land } },
        { id: "water", type: "fill", source: "v", "source-layer": "WA", paint: { "fill-color": C.water } },
        { id: "river", type: "line", source: "v", "source-layer": "RvrCL", filter: ["!", ["in", ["get", "vt_code"], ["literal", [5302, 5322]]]],
          paint: { "line-color": C.water, "line-width": ["interpolate", ["linear"], ["zoom"], 9, 0.6, 15, 2] } },
        { id: "pref", type: "line", source: "v", "source-layer": "AdmBdry", filter: ["==", ["get", "vt_code"], 1211],
          paint: { "line-color": C.sub, "line-opacity": 0.6, "line-width": 1.5 } },
        { id: "town", type: "line", source: "v", "source-layer": "AdmBdry", filter: ["==", ["get", "vt_code"], 1212], minzoom: 8.5,
          paint: { "line-color": C.sub, "line-opacity": 0.45, "line-width": 1, "line-dasharray": [4, 3] } },
        { id: "rail", type: "line", source: "v", "source-layer": "RailCL", filter: surface,
          paint: { "line-color": C.rail, "line-width": ["interpolate", ["linear"], ["zoom"], 9, 0.8, 15, 2.2] } },
        { id: "station", type: "symbol", source: "v", "source-layer": "Anno", minzoom: 12, filter: ["==", ["get", "vt_code"], 422],
          layout: { "text-field": ["get", "vt_text"], "text-font": font, "text-size": 12, "text-padding": 4 },
          paint: { "text-color": C.sub, "text-halo-color": C.land, "text-halo-width": 2 } },
        { id: "townname", type: "symbol", source: "v", "source-layer": "Anno", maxzoom: 13, filter: ["==", ["get", "vt_code"], 110],
          layout: { "text-field": ["get", "vt_text"], "text-font": font, "text-size": ["interpolate", ["linear"], ["zoom"], 9, 11, 12, 14], "text-padding": 8 },
          paint: { "text-color": C.ink, "text-opacity": 0.7, "text-halo-color": C.land, "text-halo-width": 2 } }
      ]
    };
    // 名前は塗り分けの上に、それ以外は塗り分けの下に置くので、2枚に分ける
    style.layers = style.layers.filter(function (l) { return (l.type === "symbol") === (part === "labels"); });
    return style;
  }
  map.createPane("labels");
  map.getPane("labels").style.zIndex = 350;
  map.getPane("labels").style.pointerEvents = "none";
  L.maplibreGL({ style: baseStyle("labels"), interactive: false, pane: "labels" }).addTo(map);
  L.maplibreGL({
    style: baseStyle("base"), interactive: false,
    attribution: '<a href="https://github.com/gsi-cyberjapan/optimal_bvmap">国土地理院最適化ベクトルタイル</a>、銭湯の位置の一部は © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);

  // 欄に隠れていない部分の真ん中に、その場所が来るように動かす
  function hidden() {
    if (wide.matches) return { x: sheet.classList.contains("closed") ? 0 : PANEL, y: 0 };
    return { x: 0, y: Math.max(0, window.innerHeight - sheet.getBoundingClientRect().top) };
  }
  function focus(latlng, zoom) {
    var z = zoom || Math.max(map.getZoom(), 14), h = hidden();
    var p = map.project(latlng, z).subtract([h.x / 2, -h.y / 2]);
    map.flyTo(map.unproject(p, z), z, { duration: 0.6 });
  }

  $("zin").addEventListener("click", function () { map.zoomIn(); });
  $("zout").addEventListener("click", function () { map.zoomOut(); });

  // ---------- 欄の開け閉め ----------
  // 広い画面: 左の欄をしまう。スマホ: 下の欄を3つの高さで止める
  var STATES = ["peek", "half", "full"];
  function placeCtrls() {
    var c = $("ctrls");
    if (wide.matches) { c.style.bottom = ""; return; }
    c.style.bottom = (window.innerHeight - sheet.getBoundingClientRect().top + 12) + "px";
  }
  function setState(s) {
    sheet.dataset.state = s;
    setTimeout(placeCtrls, 260);
  }
  $("collapse").addEventListener("click", function () {
    var closed = sheet.classList.toggle("closed");
    this.setAttribute("aria-expanded", closed ? "false" : "true");
    this.setAttribute("aria-label", closed ? "左の欄を出す" : "左の欄をしまう");
    this.innerHTML = icon(closed ? "chevron-right" : "chevron-left");
    draw();
  });
  (function () {
    var grab = $("grab"), y0 = 0, t0 = 0, moved = false;
    function top() { return sheet.getBoundingClientRect().top; }
    grab.addEventListener("pointerdown", function (ev) {
      y0 = ev.clientY; t0 = top(); moved = false;
      grab.setPointerCapture(ev.pointerId);
      sheet.classList.add("dragging");
    });
    grab.addEventListener("pointermove", function (ev) {
      if (!sheet.classList.contains("dragging")) return;
      var dy = ev.clientY - y0;
      if (Math.abs(dy) > 4) moved = true;
      var h = sheet.offsetHeight, y = Math.min(Math.max(t0 + dy - (window.innerHeight - h), 0), h - 96);
      sheet.style.transform = "translateY(" + y + "px)";
      placeCtrls();
    });
    grab.addEventListener("pointerup", function () {
      sheet.classList.remove("dragging");
      sheet.style.transform = "";
      if (!moved) { setState(STATES[(STATES.indexOf(sheet.dataset.state) + 1) % 3]); return; }
      var shown = window.innerHeight - top(), h = window.innerHeight;
      setState(shown < h * 0.3 ? "peek" : shown < h * 0.7 ? "half" : "full");
    });
  })();
  function lift() { if (!wide.matches && sheet.dataset.state === "peek") setState("half"); }
  window.addEventListener("resize", placeCtrls);

  // ---------- データを読む ----------
  function get(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(u); return r.json(); }); }
  Promise.all([get("data/map/cells.json"), get("data/map/sento.json"), get("data/map/summary.json")]).then(function (res) {
    start(res[0], res[1], res[2]);
  }).catch(function () {
    body.innerHTML = '<p class="empty">地図のデータを読みこめませんでした。ページを読みこみ直してください。</p>';
  });

  function start(g, sento, S) {
    var W = 8192, look = new Map(), byId = {}, types = S.types || [], typeById = {};
    g.cells.forEach(function (c) { look.set(c[0] * W + c[1], c); });
    sento.forEach(function (s, i) { s.i = i; s.key = norm([s.name, s.kana, s.area, s.address, s.access].join(" ")); byId[s.id] = s; });
    types.forEach(function (t) { typeById[t.id] = t; });
    var filter = null, current = null, navs = 0;

    // 250m 四方ごとに、圏内は薄い青、圏外は黄色（人が多いほど濃く）で塗る
    var Grid = L.GridLayer.extend({
      createTile: function (co) {
        var s = this.getTileSize(), t = document.createElement("canvas");
        t.width = s.x; t.height = s.y;
        var ctx = t.getContext("2d"), ox = co.x * s.x, oy = co.y * s.y;
        var nw = map.unproject([ox, oy], co.z), se = map.unproject([ox + s.x, oy + s.y], co.z);
        var r0 = Math.floor((se.lat - g.lat0) / g.dlat), r1 = Math.floor((nw.lat - g.lat0) / g.dlat);
        var c0 = Math.floor((nw.lng - g.lon0) / g.dlon), c1 = Math.floor((se.lng - g.lon0) / g.dlon);
        var x0 = map.project([0, g.lon0 + c0 * g.dlon], co.z).x - ox;
        var dx = map.project([0, g.lon0 + (c0 + 1) * g.dlon], co.z).x - ox - x0;
        for (var r = r0; r <= r1; r++) {
          var ya = Math.round(map.project([g.lat0 + (r + 1) * g.dlat, 0], co.z).y - oy);
          var yb = Math.round(map.project([g.lat0 + r * g.dlat, 0], co.z).y - oy);
          for (var c = c0; c <= c1; c++) {
            var v = look.get(r * W + c);
            if (!v) continue;
            var xa = Math.round(x0 + (c - c0) * dx), xb = Math.round(x0 + (c - c0 + 1) * dx);
            ctx.fillStyle = v[3] <= RADIUS ? "rgba(" + C["cover-in"] + "," + IN_ALPHA[Math.min(v[5] || 1, 6)] + ")" : "rgba(" + C["cover-out"] + "," + Math.min(0.7, 0.22 + v[2] / 1100).toFixed(2) + ")";
            ctx.fillRect(xa, ya, Math.max(1, xb - xa), Math.max(1, yb - ya));
          }
        }
        return t;
      }
    });
    var cover = new Grid({ zIndex: 5 }).addTo(map);
    $("layer").addEventListener("click", function () {
      var on = this.getAttribute("aria-pressed") !== "true";
      this.setAttribute("aria-pressed", on ? "true" : "false");
      this.setAttribute("aria-label", on ? "10分圏の塗り分けを消す" : "10分圏の塗り分けを出す");
      if (on) cover.addTo(map); else map.removeLayer(cover);
    });

    // 銭湯の点。タイプがわかっている銭湯は大きく描く
    var dots = L.canvas({ padding: 0.3 });
    function look1(s) {
      var on = !filter || (s.types || []).indexOf(filter) >= 0, typed = s.types && s.types.length;
      return { renderer: dots, radius: typed ? 8 : 5, weight: typed ? 3 : 1.5,
        fillColor: s.paused ? C.paper : s.src === "osm" ? C.sub : C.noren, color: s.paused ? C.sub : C.paper,
        fillOpacity: on ? 1 : 0.2, opacity: on ? 1 : 0.3 };
    }
    var hover = window.matchMedia("(hover: hover)").matches;
    var marks = sento.map(function (s) {
      var m = L.circleMarker([s.la, s.lo], look1(s)).addTo(map);
      m.on("click", function (ev) { L.DomEvent.stop(ev); go("s=" + s.id); });
      if (hover) m.bindTooltip(esc(s.name), { direction: "top", offset: [0, -6] });
      return m;
    });
    function restyle() { marks.forEach(function (m, i) { m.setStyle(look1(sento[i])); }); }

    // 大きくしたときだけ、名前を地図に書く
    var labels = L.layerGroup(sento.map(function (s) {
      return L.marker([s.la, s.lo], { interactive: false, keyboard: false,
        icon: L.divIcon({ className: "lbl", html: esc(s.name), iconSize: null, iconAnchor: [-10, 9] }) });
    }));
    function showLabels() { if (map.getZoom() >= 15) labels.addTo(map); else map.removeLayer(labels); }
    map.on("zoomend", showLabels);

    // 選んだ銭湯の印と、そこから1.5kmの円
    var ring = L.circle([0, 0], { radius: RADIUS, color: C.noren, weight: 2, dashArray: "6 6", fill: false, interactive: false });
    var pin = L.marker([0, 0], { interactive: false, keyboard: false, zIndexOffset: 1000,
      icon: L.divIcon({ className: "selpin", html: icon("map-pin"), iconSize: [40, 40], iconAnchor: [20, 38] }) });
    var here = L.circleMarker([0, 0], { radius: 8, color: C.paper, weight: 3, fillColor: C.ink, fillOpacity: 1, interactive: false });
    function mark(s) {
      ring.setLatLng([s.la, s.lo]).addTo(map);
      pin.setLatLng([s.la, s.lo]).addTo(map);
      draw();
    }
    function unmark() { map.removeLayer(ring); map.removeLayer(pin); }

    // ---------- 欄の中身 ----------
    function show(html, label) {
      body.innerHTML = html;
      body.scrollTop = 0;
      draw();
      if (label) $("live").textContent = label;
    }
    function head(title) {
      return '<div class="vh"><button class="icon-btn" type="button" data-back aria-label="戻る">' + icon("arrow-left") + '</button><span>' + title + '</span></div>';
    }
    function typeIcons(s) {
      return (s.types || []).map(function (id) { var t = typeById[id]; return t ? '<span class="ti" title="' + esc(t.name) + '">' + icon(t.icon) + '</span>' : ""; }).join("");
    }
    function row(s, extra) {
      return '<li><button class="row" type="button" data-go="s=' + esc(s.id) + '"><span class="row-main"><strong>' + esc(s.name) + '</strong>' +
        '<span class="row-sub">' + esc(s.area || "都の外") + (s.access ? "、" + esc(s.access) : "") + '</span></span>' +
        (extra || '<span class="row-icons">' + typeIcons(s) + '</span>') + '</button></li>';
    }

    // 営業時間と休みが単純に書かれているときだけ、いま開いているかを出す
    function openNow(s) {
      if (s.paused) return "";
      var h = (s.hours || "").replace(/（[^）]*）|\([^)]*\)/g, "").replace(/\s/g, "").match(/^(\d{1,2}):(\d{2})[-~](\d{1,2}):(\d{2})$/);
      if (!h) return "";
      var now = new Date(new Date().toLocaleString("en-US", { timeZone: "Asia/Tokyo" }));
      var day = "日月火水木金土".charAt(now.getDay()), closed = (s.closed || "").replace(/\s/g, "");
      if (/^([日月火水木金土]曜(日)?、?)+$/.test(closed) && closed.indexOf(day + "曜") >= 0) return '<p class="open shut">きょうは休み</p>';
      if (!/^([日月火水木金土]曜(日)?、?)*$|^なし$|^無休$/.test(closed)) return "";
      var m = now.getHours() * 60 + now.getMinutes(), a = +h[1] * 60 + +h[2], b = +h[3] * 60 + +h[4];
      if (b > 1440 && m < b - 1440) m += 1440;   // 25:00のように、夜中をまたいで開いている
      if (m < a) return '<p class="open shut">' + h[1] + ":" + h[2] + "から営業</p>";
      if (m < b) return '<p class="open on">営業中、' + h[3] + ":" + h[4] + "まで</p>";
      return '<p class="open shut">きょうの営業は終わりました</p>';
    }

    function showHome() {
      current = null; unmark();
      var pct = S.in / S.pop * 100;
      var rank = sento.filter(function (s) { return s.src === "tokyo" && !s.paused; }).sort(function (a, b) { return b.only - a.only; }).slice(0, 10);
      var top = rank[0].only;
      var townRow = function (t) {
        var share = t.in / t.pop * 100;
        return '<li><button class="town" type="button" data-fly="' + t.lat + "," + t.lon + '"><strong>' + esc(t.name) + '</strong>' +
          '<span class="bar" role="img" aria-label="10分圏内に住む人は' + share.toFixed(0) + '%"><i style="width:' + share.toFixed(1) + '%"></i></span>' +
          '<span class="out">圏外に<b>' + num(t.pop - t.in) + '</b>人</span></button></li>';
      };
      show(
        '<h1 class="h1"><span>東京で、</span><span>自転車10分以内に</span><span>銭湯がある人は</span></h1>' +
        '<p class="big"><b>' + pct.toFixed(0) + '<small>%</small></b><span>残りの' + man(S.out) + '人は、<br>10分では着きません。</span></p>' +
        '<div class="split" role="img" aria-label="圏内が' + pct.toFixed(0) + '%、圏外が' + (100 - pct).toFixed(0) + '%"><i style="width:' + pct.toFixed(1) + '%"></i><em></em></div>' +
        '<ul class="map-key" aria-label="地図の見方"><li><i class="k-dot"></i>銭湯</li><li><i class="k-dot paused"></i>休業中の銭湯</li><li><i class="k-in"></i>10分圏内。行ける銭湯が多いほど濃い</li><li><i class="k-out"></i>10分圏の外。住む人が多いほど濃い</li></ul>' +

        '<section class="blk"><h2>いい普通の銭湯のタイプ</h2>' +
        '<p>なるが持ち寄った例から、4つのタイプを置きました。資料で裏が取れた銭湯にだけ、タイプをつけています。押すと、そのタイプの銭湯だけを地図に出します。</p>' +
        '<ul class="types">' + types.map(function (t) {
          return '<li><button class="type" type="button" data-go="t=' + t.id + '">' + icon(t.icon) + '<span><strong>' + esc(t.name) + '</strong><small>' + esc(t.desc) + '</small></span><b>' + t.count + '軒</b></button></li>';
        }).join("") + '</ul></section>' +

        '<section class="blk"><h2>なくなると、10分で行ける銭湯がなくなる人が多い銭湯</h2>' +
        '<p>その銭湯のほかに、10分で行ける銭湯がない人の数です。この銭湯がなくなると、その人たちは圏外になります。</p>' +
        '<ol class="list">' + rank.map(function (s) {
          return row(s, '<span class="row-n"><b>' + num(s.only) + '</b>人<span class="bar thin"><i style="width:' + (s.only / top * 100).toFixed(1) + '%"></i></span></span>');
        }).join("") + '</ol></section>' +

        '<section class="blk"><h2>圏外の人が多い区と市</h2><p>押すと、地図がその場所に動きます。青が圏内、黄色が圏外です。</p>' +
        '<ol class="towns">' + S.towns.slice(0, 10).map(townRow).join("") + '</ol>' +
        '<details class="more"><summary>残りの' + (S.towns.length - 10) + 'の区市町村も見る</summary><ol class="towns">' + S.towns.slice(10).map(townRow).join("") + '</ol></details></section>' +

        '<details class="more blk"><summary>数え方と、まだ粗いところ</summary><ul class="caveats">' +
        '<li>自転車で10分を、直線で1.5kmと置きました。時速12kmで走ると道のりは2kmで、道は直線より3割ほど遠回りになる、という仮の計算です。坂や川、線路は見ていません。</li>' +
        '<li>人口は、2020年の国勢調査を250m四方に区切ったものです。島は入れていません。</li>' +
        '<li>都内の銭湯は、東京都浴場組合の東京銭湯マップに載っている' + S.sento_tokyo + '軒です。組合に入っていない銭湯は入っていません。2026年11月28日に読みました。</li>' +
        '<li>このうち、一覧で休業中になっている' + S.sento_paused + '軒は、10分圏の数に入れていません。</li>' +
        '<li>都の外の銭湯は、OpenStreetMapにある' + S.sento_around + '軒を使いました。都内の一覧より抜けが多く、県境の近くでは圏外が多めに出ているはずです。</li>' +
        '<li>いい銭湯かどうか、これからも続きそうかどうかは、まだ見ていません。</li></ul>' +
        '<p class="note">出どころは、<a href="https://www.e-stat.go.jp/gis">e-Statの地図で見る統計</a>、<a href="https://www.1010.or.jp/map/">東京銭湯マップ</a>、<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>、<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル</a>です。</p></details>' +
        '<p class="foot"><a href="index.html">全体のページに戻る</a></p>'
      );
    }

    function find(q) {
      var k = norm(q);
      if (!k) return [];
      return sento.filter(function (s) { return s.key.indexOf(k) >= 0; })
        .sort(function (a, b) { return (norm(a.name).indexOf(k) < 0) - (norm(b.name).indexOf(k) < 0) || (a.src === "osm") - (b.src === "osm"); });
    }
    function showResults(q) {
      current = null; unmark();
      var hits = find(q), k = norm(q);
      var towns = S.towns.filter(function (t) { return norm(t.name).indexOf(k) >= 0; });
      var html = head("「" + esc(q) + "」でさがした結果");
      if (towns.length) html += '<ul class="hits">' + towns.map(function (t) {
        return '<li><button class="row" type="button" data-fly="' + t.lat + "," + t.lon + '">' + icon("map") + '<span class="row-main"><strong>' + esc(t.name) + '</strong><span class="row-sub">地図をこの区や市に動かす</span></span></button></li>';
      }).join("") + '</ul>';
      if (hits.length) html += '<p class="count">銭湯が' + hits.length + '軒あります。</p><ol class="list">' + hits.slice(0, 80).map(function (s) { return row(s); }).join("") + '</ol>';
      if (!hits.length && !towns.length) html += '<p class="empty">見つかりませんでした。銭湯の名前、駅の名前、区や市の名前で、さがしてみてください。</p>';
      show(html, hits.length ? "銭湯が" + hits.length + "軒見つかりました" : "見つかりませんでした");
      lift();
    }

    function showType(id) {
      current = null; unmark();
      var t = typeById[id], list = sento.filter(function (s) { return (s.types || []).indexOf(id) >= 0; });
      var html = head(esc(t.name)) + '<p class="lead-s">' + esc(t.desc) + '。</p>';
      if (list.length) {
        html += '<ol class="list">' + list.map(function (s) { return row(s); }).join("") + '</ol>';
        var b = L.latLngBounds(list.map(function (s) { return [s.la, s.lo]; }));
        var h = hidden();
        map.flyToBounds(b, { paddingTopLeft: [h.x + 48, 120], paddingBottomRight: [48, h.y + 48], maxZoom: 13, duration: 0.6 });
      } else {
        html += '<p class="empty">このタイプの銭湯は、まだ書いていません。行って見つけたら書き足します。</p>';
      }
      html += '<p class="note">タイプは、資料で裏が取れた銭湯にだけつけています。クラブ銭湯で回った銭湯も、ここに書き足していきます。</p>';
      show(html, t.name + "の銭湯は" + list.length + "軒です");
      lift();
    }

    function showSento(s) {
      current = s; mark(s);
      var nx = sento[s.next[0]];
      var gmap = "https://www.google.com/maps/dir/?api=1&destination=" + s.la + "," + s.lo;
      var html = head("銭湯") +
        '<h2 class="name">' + esc(s.name) + '</h2>' +
        (s.kana ? '<p class="kana">' + esc(s.kana) + '</p>' : "") +
        '<p class="area">' + esc(s.area || "都の外") + '</p>' +
        (s.paused ? '<p class="paused-note">組合の一覧で、休業中になっています。10分圏の数には入れていません。</p>' : "") +
        ((s.types || []).length ? '<ul class="tchips">' + s.types.map(function (id) { var t = typeById[id]; return '<li>' + icon(t.icon) + esc(t.name) + '</li>'; }).join("") + '</ul>' : "") +
        openNow(s) +
        '<div class="acts">' +
        '<a class="act primary" href="' + gmap + '" target="_blank" rel="noopener"><span class="act-i">' + icon("navigation") + '</span>経路を見る</a>' +
        (s.src === "tokyo"
          ? '<a class="act" href="' + esc(s.url) + '" target="_blank" rel="noopener"><span class="act-i">' + icon("external-link") + '</span>組合のページ</a>'
          : '<a class="act" href="' + esc(s.url) + '" target="_blank" rel="noopener"><span class="act-i">' + icon("external-link") + '</span>地図の元</a>') +
        '<button class="act" type="button" data-share><span class="act-i">' + icon("share-2") + '</span>リンクを送る</button></div>';

      if (s.src === "tokyo") {
        var info = [
          ["map-pin", "住所", esc(s.address)],
          ["clock", "営業時間", esc(s.hours)],
          ["calendar-x", "休み", esc(s.closed)],
          ["train-front", "行き方", esc(s.access)],
          ["phone", "電話", s.tel ? '<a href="tel:' + esc(s.tel.replace(/[^\d+]/g, "")) + '">' + esc(s.tel) + "</a>" : ""],
          ["globe", "公式ページ", (s.links || []).map(function (l) { return /^https?:\/\//.test(l[1]) ? '<a href="' + esc(l[1]) + '" target="_blank" rel="noopener">' + esc(l[0]) + "</a>" : ""; }).join("、")]
        ].filter(function (r) { return r[2]; });
        html += '<ul class="info">' + info.map(function (r) { return '<li>' + icon(r[0]) + '<div><span class="sr">' + r[1] + '</span>' + r[2] + '</div></li>'; }).join("") + '</ul>';
      } else {
        html += '<p class="note">都の外の銭湯です。OpenStreetMapにある名前と位置だけで、くわしい中身はありません。</p>';
      }

      if (s.paused) html += '<section class="blk"><h3>この銭湯のまわり</h3>' +
        (nx ? '<button class="row near" type="button" data-go="s=' + esc(nx.id) + '">' + icon("bath") + '<span class="row-main"><span class="row-sub">いちばん近い、開いている銭湯</span><strong>' + esc(nx.name) + '</strong></span><span class="row-n">直線で' + km(s.next[1]) + '</span></button>' : "") + '</section>';
      else html += '<section class="blk"><h3>この銭湯のまわり</h3><dl class="facts2">' +
        '<div><dt>10分圏に住む人</dt><dd><b>' + num(s.reach) + '</b>人</dd></div>' +
        '<div><dt>ほかに10分で行ける銭湯がない人</dt><dd><b>' + num(s.only) + '</b>人</dd></div></dl>' +
        '<p class="note">' + (s.only ? "この銭湯がなくなると、" + num(s.only) + "人が10分で銭湯に行けなくなります。" : "この銭湯がなくなっても、まわりの人は10分でほかの銭湯に行けます。") + '円は、ここから直線で1.5kmです。</p>' +
        (nx ? '<button class="row near" type="button" data-go="s=' + esc(nx.id) + '">' + icon("bath") + '<span class="row-main"><span class="row-sub">いちばん近いほかの銭湯</span><strong>' + esc(nx.name) + '</strong></span><span class="row-n">直線で' + km(s.next[1]) + '</span></button>' : "") +
        '</section>';

      html += '<section class="blk"><h3>いい普通の銭湯のタイプ</h3>';
      if ((s.notes || []).length) {
        html += s.notes.map(function (n) {
          return '<div class="tnote"><p>' + esc(n.what) + '</p><p class="note"><a href="' + esc(n.src) + '" target="_blank" rel="noopener">' + esc(n.srcName) + '</a>' + (n.date ? '、<span class="nw">' + esc(n.date.replace(/^(\d+)-0?(\d+)-0?(\d+)$/, "$1年$2月$3日")) + "の資料</span>" : "") + '</p></div>';
        }).join("");
      } else {
        html += '<p class="empty-s">まだわかりません。行って確かめたら書き足します。</p>';
      }
      html += '</section>';

      var eq = (s.services || []).concat(s.features || []).filter(function (x, i, a) { return x && a.indexOf(x) === i; });
      if (eq.length) html += '<section class="blk"><h3>設備</h3><ul class="eq">' + eq.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + '</ul></section>';
      if (s.src === "tokyo") html += '<p class="note">住所や営業時間は、2026年11月28日に東京銭湯マップで読んだものです。行く前に、組合のページで確かめてください。</p>';

      show(html, s.name);
      lift();
      focus([s.la, s.lo]);
    }

    // 地図の何もないところを押したとき。その250m四方の人数と、いちばん近い銭湯
    function showCell(latlng, mine) {
      var r = Math.floor((latlng.lat - g.lat0) / g.dlat), c = Math.floor((latlng.lng - g.lon0) / g.dlon);
      var v = look.get(r * W + c);
      unmark();
      var html = head(mine ? "いまいる場所" : "押した場所");
      if (!v) {
        html += '<p class="empty">ここには、数えた人が住んでいません。東京都の本土の、人が住んでいる場所を押すと、人数と近い銭湯がわかります。</p>';
      } else {
        var s = sento[v[4]], inside = v[3] <= RADIUS;
        html += '<p class="verdict ' + (inside ? "in" : "out") + '">' + (inside ? "10分圏内です" : "10分圏の外です") + '</p>' +
          '<dl class="facts2"><div><dt>この250m四方に住む人</dt><dd><b>' + num(v[2]) + '</b>人</dd></div>' +
          '<div><dt>10分で行ける銭湯</dt><dd><b>' + (v[5] || 0) + '</b>軒</dd></div></dl>' +
          '<button class="row near" type="button" data-go="s=' + esc(s.id) + '">' + icon("bath") + '<span class="row-main"><span class="row-sub">いちばん近い銭湯</span><strong>' + esc(s.name) + '</strong></span><span class="row-n">直線で' + km(v[3]) + '</span></button>';
      }
      show(html);
      lift();
    }

    // ---------- 行き来 ----------
    function go(h) { navs++; if (location.hash === "#" + h) route(); else location.hash = h; }
    function route() {
      var h = decodeURIComponent(location.hash.slice(1)), m;
      var f = (m = h.match(/^t=(.+)$/)) && typeById[m[1]] ? m[1] : null;
      if (f !== filter) { filter = f; restyle(); }
      document.querySelectorAll(".chip").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.type === filter ? "true" : "false"); });
      if ((m = h.match(/^s=(.+)$/)) && byId[m[1]]) return showSento(byId[m[1]]);
      if ((m = h.match(/^q=(.+)$/))) { if (input.value !== m[1]) input.value = m[1]; $("clear").hidden = false; return showResults(m[1]); }
      if (f) return showType(f);
      showHome();
    }
    window.addEventListener("hashchange", route);

    body.addEventListener("click", function (ev) {
      var b = ev.target.closest("[data-go],[data-fly],[data-back],[data-share]");
      if (!b) return;
      if (b.dataset.go) return go(b.dataset.go);
      if (b.dataset.fly) { var p = b.dataset.fly.split(","); focus([+p[0], +p[1]], 13); if (!wide.matches) setState("peek"); return; }
      if (b.hasAttribute("data-back")) {
        if (navs > 0) { navs--; history.back(); } else { input.value = ""; $("clear").hidden = true; history.replaceState(null, "", location.pathname); route(); }
        return;
      }
      if (b.hasAttribute("data-share")) {
        var url = location.href;
        if (navigator.share) navigator.share({ title: current ? current.name : document.title, url: url }).catch(function () {});
        else if (navigator.clipboard) navigator.clipboard.writeText(url).then(function () { toast("リンクをコピーしました"); }, function () { toast("コピーできませんでした。アドレス欄からコピーしてください"); });
      }
    });

    // 上のボタンで、タイプを絞る。もう一度押すと全部に戻る
    $("chips").innerHTML = types.map(function (t) {
      return '<button class="chip" type="button" aria-pressed="false" data-type="' + t.id + '">' + icon(t.icon) + esc(t.name) + '</button>';
    }).join("");
    $("chips").addEventListener("click", function (ev) {
      var b = ev.target.closest(".chip");
      if (b) go(b.dataset.type === filter ? "" : "t=" + b.dataset.type);
    });

    // 文字を打つたびにさがす。検索の途中は戻るの履歴を増やさない
    var timer;
    input.addEventListener("input", function () {
      clearTimeout(timer);
      var q = input.value.trim();
      $("clear").hidden = !input.value;
      timer = setTimeout(function () {
        history.replaceState(null, "", q ? "#q=" + encodeURIComponent(q) : location.pathname);
        route();
      }, 150);
    });
    $("search").addEventListener("submit", function (ev) {
      ev.preventDefault();
      var hits = find(input.value.trim());
      if (hits.length === 1) go("s=" + hits[0].id);
      input.blur();
    });
    $("clear").addEventListener("click", function () {
      input.value = ""; this.hidden = true; input.focus();
      history.replaceState(null, "", location.pathname);
      route();
    });

    map.on("click", function (ev) { showCell(ev.latlng, false); });

    $("locate").addEventListener("click", function () {
      if (!navigator.geolocation) return toast("このブラウザでは、いまいる場所を使えません");
      toast("いまいる場所をさがしています");
      navigator.geolocation.getCurrentPosition(function (p) {
        var ll = L.latLng(p.coords.latitude, p.coords.longitude);
        here.setLatLng(ll).addTo(map);
        $("toast").hidden = true;
        showCell(ll, true);
        focus(ll, 15);
      }, function () {
        toast("いまいる場所がわかりませんでした。ブラウザで位置情報を許可しているか、確かめてください");
      }, { enableHighAccuracy: true, timeout: 10000 });
    });

    draw();
    placeCtrls();
    var h0 = hidden();
    map.fitBounds([[35.53, 139.28], [35.82, 139.9]], { paddingTopLeft: [h0.x, wide.matches ? 48 : 104], paddingBottomRight: [0, h0.y], animate: false });
    route();
    showLabels();
  }
})();
