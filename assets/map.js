// 空白地帯マップ。data/map の JSON を読んで、地図と横（スマホでは下）の欄を描く。
// 欄の中身は URL の # で決まる。#s=銭湯、#q=検索、#t=タイプ、なにもなければ全体。
(function () {
  "use strict";
  var RADIUS = 1500;
  // 10分で行ける銭湯が多いほど、青を濃くする。1軒、2軒、3軒、4軒、5軒、6軒以上
  // 10分で行ける銭湯の数を 3 段に分ける: 1軒だけ、2〜3軒、4軒以上（段に名前を付けて凡例を読まずにすむようにする）
  var IN_ALPHA = [0, 0.1, 0.22, 0.22, 0.38, 0.38, 0.38];
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
  // 外から取ったリンクは、http と https だけを通す。ほかは空にする
  function url(u) { return /^https?:\/\//i.test(String(u || "")) ? esc(u) : ""; }
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
    if (!map.getSize().x || !map.getSize().y) return;   // 地図に大きさがないときは動かさない
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
    var F = {}, FAREA = "";   // 絞りこみの条件。F は条件の id → true、FAREA は区や市

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
      if (factive() || filter) {
        var hit = (!filter || (s.types || []).indexOf(filter) >= 0) && fmatch(s);
        return hit
          ? { renderer: dots, radius: 7, weight: 2, color: C.paper, fillColor: s.paused ? C.paper : C.noren, fillOpacity: 1, opacity: 1 }
          : { renderer: dots, radius: 3, weight: 0, color: C.paper, fillColor: C.sub, fillOpacity: 0.35, opacity: 0 };
      }
      var on = (!filter || (s.types || []).indexOf(filter) >= 0) && fmatch(s), typed = s.types && s.types.length;
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

    // 絞りこみで当てはまる銭湯が少ないときは、印に値（候補なら創業から何年、空白なら人数）か名前を載せる（Airbnb の値つきの印にならう）
    var pillLayer = L.layerGroup().addTo(map);
    function pillText(s) {
      if (F.visit && s.hist && s.hist.founded) return esc(s.name) + " " + (YEAR - s.hist.founded + 1) + "年目";
      if ((F.only10k || F.only) && s.only) return esc(s.name) + " " + (s.only >= 10000 ? (s.only / 10000).toFixed(1) + "万人" : num(s.only) + "人");
      return esc(s.name);
    }
    function pills() {
      pillLayer.clearLayers();
      if (!factive()) return;
      var b = map.getBounds().pad(0.1);
      var hits = sento.filter(function (s) { return fmatch(s); });
      // 重なって読めなくならないよう、15 軒以下か、地図を大きくして映っている分が 25 軒以下のときだけ載せる
      var shown = hits.length <= 15 ? hits : map.getZoom() >= 13 ? hits.filter(function (s) { return b.contains([s.la, s.lo]); }) : [];
      if (shown.length > 25) return;
      shown.forEach(function (s) {
        L.marker([s.la, s.lo], { keyboard: false, icon: L.divIcon({ className: "vpill", html: "<span>" + pillText(s) + "</span>", iconSize: null, iconAnchor: [-10, 12] }) })
          .on("click", function () { go("s=" + s.id); }).addTo(pillLayer);
      });
    }
    // 大きくしたときだけ、名前を地図に書く
    var labels = L.layerGroup(sento.map(function (s) {
      return L.marker([s.la, s.lo], { interactive: false, keyboard: false,
        icon: L.divIcon({ className: "lbl", html: esc(s.name), iconSize: null, iconAnchor: [-10, 9] }) });
    }));
    function showLabels() { if (map.getZoom() >= 15 && !factive()) labels.addTo(map); else map.removeLayer(labels); }
    map.on("zoomend", showLabels);
    map.on("moveend", function () { if (factive()) pills(); });

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
      return '<div class="vh"><button class="icon-btn" type="button" data-back aria-label="戻る">' + icon("arrow-left") + '</button><span>' + title + '</span>' +
        '<button class="icon-btn close" type="button" data-home aria-label="閉じて最初の欄に戻る">' + icon("x") + '</button></div>';
    }
    function typeIcons(s) {
      return (s.types || []).map(function (id) { var t = typeById[id]; return t ? '<span class="ti" title="' + esc(t.name) + '"><span class="sr">' + esc(t.name) + '</span>' + icon(t.icon) + '</span>' : ""; }).join("");
    }
    function rowStatus(s) {
      var st = status(s);
      return st ? '<span class="row-open ' + (st.open ? "on" : "shut") + '">' + st.text + "</span>" : "";
    }
    // 銭湯の一覧の 1 行。右には見出しが指す数を 1 つ（v と単位 u）、補足は左の 2 行目（note）
    function row(s, v, u, note) {
      return '<li><button class="row" type="button" data-go="s=' + esc(s.id) + '"><span class="row-main"><strong>' + esc(s.name) + typeIcons(s) + '</strong>' +
        '<span class="row-sub">' + esc(note || ((s.area || "都の外") + (s.access ? "、" + s.access : ""))) + '</span>' + rowStatus(s) + '</span>' +
        (v != null ? '<span class="row-n"><b>' + v + '</b>' + u + '</span>' : "") + '</button></li>';
    }

    // ---------- いま開いているか ----------
    // 祝日。2026年と2027年の分だけ持つ。ほかの年は、祝日の扱いを「確かめて」と出す
    var HOL = ("2026-01-01 2026-01-12 2026-02-11 2026-02-23 2026-03-20 2026-04-29 2026-05-03 2026-05-04 2026-05-05 2026-05-06 " +
      "2026-07-20 2026-08-11 2026-09-21 2026-09-22 2026-09-23 2026-10-12 2026-11-03 2026-11-23 " +
      "2027-01-01 2027-01-11 2027-02-11 2027-02-23 2027-03-21 2027-03-22 2027-04-29 2027-05-03 2027-05-04 2027-05-05 " +
      "2027-07-19 2027-08-11 2027-09-20 2027-09-23 2027-10-11 2027-11-03 2027-11-23").split(" ");
    var WDN = "日月火水木金土";
    function jst() { return new Date(new Date().toLocaleString("en-US", { timeZone: "Asia/Tokyo" })); }
    function ymd(d) { return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); }
    function isHol(d) { return HOL.indexOf(ymd(d)) >= 0; }
    function hm(m) { m = m % 1440; return Math.floor(m / 60) + ":" + String(m % 60).padStart(2, "0"); }
    // 決まりの上で休みの日か（祝日の扱いは入れない）
    function ruleOff(o, d) {
      var wd = d.getDay(), date = d.getDate(), month = d.getMonth() + 1;
      var dim = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
      return o.wd.indexOf(wd) >= 0 || o.dates.indexOf(date) >= 0 ||
        ((!o.months.length || o.months.indexOf(month) >= 0) && o.nth.some(function (n) { return n[0] === Math.ceil(date / 7) && n[1] === wd; })) ||
        (o.last.indexOf(wd) >= 0 && date + 7 > dim);
    }
    function isOff(sc, d) {
      var r = ruleOff(sc.off, d);
      if (isHol(d)) {
        if (sc.hol === "off") return true;
        if (r && (sc.hol === "open" || sc.hol === "next")) return false;
      }
      if (sc.hol === "next") {
        var y = new Date(d); y.setDate(d.getDate() - 1);
        if (isHol(y) && ruleOff(sc.off, y)) return true;
      }
      return r;
    }
    function rangesOn(sc, d) { var h = sc.hours; return (isHol(d) && h.h) || h[String(d.getDay())] || h.d || []; }
    // { open: 開いているか, text: 出す言葉 }。読めない銭湯は null
    function status(s) {
      var sc = s.sched;
      if (s.hist && s.hist.closedUntil) return { open: false, text: "改装のため休み。" + s.hist.closedUntil + "まで" };
      if (!sc || s.paused) return null;
      var now = jst(), m = now.getHours() * 60 + now.getMinutes();
      var y = new Date(now); y.setDate(now.getDate() - 1);
      if (!isOff(sc, y)) {
        var late = rangesOn(sc, y).filter(function (r) { return r[1] > 1440 && m < r[1] - 1440; })[0];
        if (late) return { open: true, text: "営業中、" + hm(late[1]) + "まで" };
      }
      if (isOff(sc, now)) return { open: false, text: "きょうは休み" };
      var rs = rangesOn(sc, now);
      for (var i = 0; i < rs.length; i++) {
        if (m >= rs[i][0] && m < rs[i][1]) return { open: true, text: "営業中、" + (rs[i][1] > 1440 ? "夜中の" : "") + hm(rs[i][1]) + "まで" };
        if (m < rs[i][0]) return { open: false, text: hm(rs[i][0]) + "から営業" };
      }
      return { open: false, text: "きょうの営業は終わりました" };
    }
    function statusLine(s) {
      var st = status(s);
      if (!st) return s.paused ? "" : '<p class="now-st shut">いま開いているかは、組合のページで確かめてください</p>';
      return '<p class="now-st ' + (st.open ? "on" : "shut") + '">' + esc(st.text) + (s.sched && s.sched.odd ? '<span class="odd">不定休があります</span>' : "") + "</p>";
    }
    // 曜日ごとの営業時間の表。月曜から並べ、きょうの行を太くする
    function weekTable(s) {
      var sc = s.sched, today = jst().getDay();
      if (!sc) return "";
      var rows = [1, 2, 3, 4, 5, 6, 0].map(function (wd) {
        var off = sc.off.wd.indexOf(wd) >= 0;
        var rs = sc.hours[String(wd)] || sc.hours.d || [];
        var txt = off ? "休み" : rs.map(function (r) { return hm(r[0]) + "〜" + (r[1] > 1440 ? "夜中の" : "") + hm(r[1]); }).join("、");
        return '<tr' + (wd === today ? ' class="today"' : "") + '><th scope="row">' + WDN.charAt(wd) + '曜</th><td>' + txt + "</td></tr>";
      });
      if (sc.hours.h) rows.push('<tr><th scope="row">祝日</th><td>' + sc.hours.h.map(function (r) { return hm(r[0]) + "〜" + (r[1] > 1440 ? "夜中の" : "") + hm(r[1]); }).join("、") + "</td></tr>");
      return '<table class="week">' + rows.join("") + "</table>";
    }

    // ---------- 絞りこみ ----------
    var YEAR = jst().getFullYear();
    function has(s, label) { return (s.services || []).indexOf(label) >= 0 || (s.features || []).indexOf(label) >= 0; }
    function anyRange(s, test) { return !!(s.sched && Object.keys(s.sched.hours).some(function (k) { return s.sched.hours[k].some(test); })); }
    // 話を聞きに行く候補: 創業から60年以上たち、代替わりの話がまだ記事にない銭湯
    function isVisit(s) { return s.src === "tokyo" && !s.paused && !!(s.hist && s.hist.founded && YEAR - s.hist.founded >= 60 && !s.hist.gen); }
    function tag(label) { return function (s) { return has(s, label); }; }
    var FGROUPS = [
      ["営業", [
        ["open", "いま営業中", function (s) { var st = status(s); return !!(st && st.open); }],
        ["morning", "朝10時より前に開く日がある", function (s) { return anyRange(s, function (r) { return r[0] < 600; }); }],
        ["late", "夜中の1時を過ぎても開いている日がある", function (s) { return anyRange(s, function (r) { return r[1] > 1500; }); }]]],
      ["歩み", [
        ["old", "創業から60年以上", function (s) { return !!(s.hist && s.hist.founded && YEAR - s.hist.founded >= 60); }],
        ["handed", "代替わりしている", function (s) { return !!(s.hist && s.hist.gen >= 2); }],
        ["nogen", "代替わりがまだわからない", function (s) { return s.src === "tokyo" && !(s.hist && s.hist.gen); }],
        ["visit", "話を聞きに行く候補", isVisit]]],
      ["いい普通の銭湯のタイプ", types.map(function (t) { return ["type-" + t.id, t.name, function (s) { return (s.types || []).indexOf(t.id) >= 0; }]; })],
      ["支えるときの目安", [
        ["only10k", "なくなると10分で銭湯に行けなくなる人が1万人以上", function (s) { return s.only >= 10000; }],
        ["only", "なくなると10分で銭湯に行けなくなる人がいる", function (s) { return s.only > 0; }]]],
      ["建物と内装", [
        ["miya", "宮造り", tag("宮造り建築")], ["paint", "ペンキ絵", tag("ペンキ絵")],
        ["tile", "タイル絵", function (s) { return has(s, "モザイクタイル絵（浴室）") || has(s, "浴室のタイル絵"); }],
        ["geta", "木の下足札", tag("木の下足札")], ["bandai", "番台", tag("番台")], ["maki", "薪で沸かす", tag("薪")]]],
      ["お風呂", [
        ["sauna", "サウナ", tag("サウナ")], ["rotenburo", "露天風呂", tag("露天風呂")], ["mizu", "水風呂", tag("水風呂")],
        ["yaku", "薬湯", tag("薬湯")], ["onsen", "温泉", tag("温泉")]]],
      ["使いやすさ", [
        ["bf", "バリアフリー", tag("バリアフリー")], ["baby", "ベビーベッド", tag("ベビーベッド")], ["rest", "休憩室", tag("休憩室")],
        ["laundry", "コインランドリー", tag("ランドリー")], ["park", "無料の駐車場", tag("駐車場（無料）")]]],
      ["そのほか", [
        ["photo", "写真がある", function (s) { return !!(s.photos && s.photos.length); }],
        ["nopause", "休業中の銭湯を出さない", function (s) { return !s.paused; }]]]
    ];
    var FTEST = {}, FGROUP = {}, FLABEL = {};
    FGROUPS.forEach(function (g, gi) { g[1].forEach(function (o) { FTEST[o[0]] = o[2]; FGROUP[o[0]] = gi; FLABEL[o[0]] = o[1]; }); });
    // 同じ群の中はどれか 1 つに当てはまればよく、群どうしはすべてに当てはまる（英国労働年金省の絞りこみの調査にならう）
    function fmatch(s, extra) {
      var by = {};
      Object.keys(F).concat(extra && !F[extra] ? [extra] : []).forEach(function (id) { (by[FGROUP[id]] = by[FGROUP[id]] || []).push(id); });
      for (var gi in by) if (!by[gi].some(function (id) { return FTEST[id](s); })) return false;
      return !FAREA || s.area === FAREA;
    }
    // 選んでいる条件を文にする。群の中は「か」、群どうしは「、」でつなぐ
    function fsentence() {
      var by = {};
      Object.keys(F).forEach(function (id) { (by[FGROUP[id]] = by[FGROUP[id]] || []).push(FLABEL[id]); });
      var parts = Object.keys(by).sort().map(function (gi) { return by[gi].join("か"); });
      if (FAREA) parts.unshift(FAREA);
      return parts.join("、");
    }
    function factive() { return Object.keys(F).filter(function (k) { return F[k]; }).length + (FAREA ? 1 : 0); }
    var AREAS = sento.reduce(function (a, s) { if (s.area && a.indexOf(s.area) < 0) a.push(s.area); return a; }, [])
      .sort(function (a, b) { return (/区$/.test(b) - /区$/.test(a)) || a.localeCompare(b, "ja"); });

    function showFilters() {
      current = null; unmark();
      var html = head("絞りこむ") + '<p class="fsen" id="fsen" aria-live="polite"></p><p class="note">同じ見出しの中で 2 つ選ぶと、どちらかに当てはまる銭湯を出します。見出しが違う条件は、すべてに当てはまる銭湯を出します。</p>';
      FGROUPS.forEach(function (g) {
        html += '<fieldset class="fg"><legend>' + g[0] + '</legend>' +
          (g[0] === "いい普通の銭湯のタイプ" ? '<p class="fdesc">なるが持ち寄った例から置いた4つのタイプです。資料で裏が取れた銭湯にだけつけています。行って見つけたら書き足します。</p>' : "") + '<div class="fopts">' + g[1].map(function (o) {
          return '<label class="fopt"><input type="checkbox" data-f="' + o[0] + '"' + (F[o[0]] ? " checked" : "") + '><span>' + o[1] + '<b class="fn" data-fn="' + o[0] + '"></b></span></label>';
        }).join("") + "</div></fieldset>";
      });
      html += '<fieldset class="fg"><legend>区や市</legend><select class="fsel" data-farea aria-label="区や市を選ぶ"><option value="">すべての区と市</option>' +
        AREAS.map(function (a) { return '<option' + (a === FAREA ? " selected" : "") + ">" + esc(a) + "</option>"; }).join("") + "</select></fieldset>";
      html += '<div class="fbar"><button class="btn primary" type="button" data-fshow></button><button class="btn" type="button" data-fclear>条件を消す</button></div>';
      html += '<ol class="list" id="flist"></ol>';
      show(html, "絞りこみの条件を選べます");
      fupdate();
      lift();
    }
    // 条件が変わったら、地図、数、一覧、上のボタンをそろえる
    function applied() {
      // 上のボタンで選べる「いま営業中」「話を聞きに行く候補」は、押した状態のボタンで見えるので帯には出さない
      var ap = $("applied"), ids = Object.keys(F).filter(function (id) { return id !== "open" && id !== "visit"; });
      if (!ids.length && !FAREA) { ap.hidden = true; ap.innerHTML = ""; return; }
      ap.hidden = false;
      ap.innerHTML = (FAREA ? '<button class="ach" type="button" data-unarea>' + esc(FAREA) + icon("x") + '</button>' : "") +
        ids.map(function (id) { return '<button class="ach" type="button" data-unf="' + id + '" aria-label="' + esc(FLABEL[id]) + 'の条件を外す">' + esc(FLABEL[id]) + icon("x") + "</button>"; }).join("") +
        '<button class="ach clear" type="button" data-unall>すべて消す</button>';
      draw();
    }
    function fupdate() {
      restyle();
      applied();
      pills();
      var hits = sento.filter(function (s) { return fmatch(s); });
      var n = factive();
      var chip = document.querySelector("[data-filters]");
      if (chip) { chip.setAttribute("aria-pressed", n ? "true" : "false"); chip.querySelector(".badge").textContent = n ? n : ""; }
      var oc = document.querySelector("[data-open]");
      if (oc) oc.setAttribute("aria-pressed", F.open ? "true" : "false");
      var vc = document.querySelector("[data-visit]");
      if (vc) vc.setAttribute("aria-pressed", F.visit ? "true" : "false");
      var bar = body.querySelector("[data-fshow]");
      if (!bar) return;
      bar.textContent = hits.length + "軒を地図で見る";
      var sen = $("fsen");
      if (sen) sen.innerHTML = n ? esc(fsentence()) + "の銭湯は<b>" + hits.length + "</b>軒です" : "条件を選ぶと、当てはまる銭湯の数がここに出ます";
      bar.disabled = !hits.length;
      body.querySelectorAll("[data-fn]").forEach(function (el) {
        var id = el.dataset.fn;
        var c = F[id] ? "" : sento.filter(function (s) { return fmatch(s, id); }).length;
        el.textContent = c;
        el.closest(".fopt").classList.toggle("zero", c === 0);
      });
      $("flist").innerHTML = hits.length
        ? hits.slice(0, 60).map(function (s) { return row(s); }).join("") + (hits.length > 60 ? '<li class="more-n">ほかに' + (hits.length - 60) + "軒あります。地図で見てください。</li>" : "")
        : '<li class="empty">当てはまる銭湯はありません。条件を減らしてみてください。</li>';
      draw();
      showLabels();
      $("live").textContent = hits.length + "軒が当てはまります";
    }
    body.addEventListener("change", function (ev) {
      var t = ev.target;
      if (t.dataset.f) { if (t.checked) F[t.dataset.f] = true; else delete F[t.dataset.f]; fupdate(); }
      if (t.hasAttribute("data-farea")) { FAREA = t.value; fupdate(); }
    });

    // 一覧の中身。最初の欄では上位 5 件、「すべて見る」で全部
    function lossList() {
      return sento.filter(function (s) { return s.src === "tokyo" && !s.paused && s.only > 0; }).sort(function (a, b) { return b.only - a.only; });
    }
    function visitList() { return sento.filter(isVisit).sort(function (a, b) { return b.only - a.only; }); }
    function townRow(t) {
      var share = t.in / t.pop * 100;
      return '<li><button class="town" type="button" data-fly="' + t.lat + "," + t.lon + '"><strong>' + esc(t.name) + '</strong>' +
        '<span class="bar" role="img" aria-label="10分圏内に住む人は' + share.toFixed(0) + '%"><i style="width:' + share.toFixed(1) + '%"></i></span>' +
        '<span class="out"><b>' + num(t.pop - t.in) + '</b>人</span></button></li>';
    }
    function lossRow(s) { return row(s, num(s.only), "人"); }
    function visitRow(s) { return row(s, num(s.only), "人", (s.area || "") + "、創業から" + (YEAR - s.hist.founded + 1) + "年目"); }
    var LISTS = {
      towns: ["空白が大きい区と市", "10分圏の外に住む人が多い順です。押すと、地図がその場所に動きます。棒の青は圏内、黄色は圏外です。", function () { return S.towns; }, townRow, "towns"],
      loss: ["なくなると空白が広がる銭湯", "その銭湯がなくなると、10分で銭湯に行けなくなる人の数です。多い順に並べました。", lossList, lossRow, "list"],
      visit: ["話を聞きに行く候補", "創業から60年以上たっていて、代替わりの話がまだ記事に出てこない銭湯です。なくなると10分で銭湯に行けなくなる人が多い順に並べました。", visitList, visitRow, "list"]
    };
    function block(id) {
      var L_ = LISTS[id], items = L_[2]();
      return '<section class="blk"><h2>' + L_[0] + '</h2><p>' + L_[1] + '</p><ol class="' + L_[4] + '">' + items.slice(0, 5).map(L_[3]).join("") + '</ol>' +
        (items.length > 5 ? '<button class="seeall" type="button" data-go="l=' + id + '">すべて見る<span>' + items.length + (id === "towns" ? "の区市町村" : "軒") + '</span>' + icon("chevron-right") + '</button>' : "") + '</section>';
    }
    function showList(id) {
      current = null; unmark();
      var L_ = LISTS[id], items = L_[2]();
      var onMap = id === "visit" ? "visit" : id === "loss" ? "only" : "";
      show(head(L_[0]) + '<p class="lead-s">' + L_[1] + '</p>' +
        (onMap ? '<button class="btn primary wide" type="button" data-onmap="' + onMap + '">' + icon("map") + 'この' + items.length + '軒を地図に出す</button>' : "") +
        '<ol class="' + L_[4] + '">' + items.map(L_[3]).join("") + '</ol>' +
        (id === "visit" ? '<p class="note">創業の年がわかる銭湯は' + sento.filter(function (x) { return x.hist && x.hist.founded; }).length + '軒、何代目かがわかる銭湯は' + sento.filter(function (x) { return x.hist && x.hist.gen; }).length + '軒です。組合のサイトの、店主に話を聞いた記事から取り出しました。</p>' : ""), L_[0]);
      lift();
    }

    function showHome() {
      current = null; unmark();
      var pct = S.in / S.pop * 100;
      show(

        '<h1 class="h1"><span>東京で、</span><span>自転車10分以内に</span><span>銭湯がある人は</span></h1>' +
        '<p class="big"><b>' + pct.toFixed(0) + '<small>%</small></b><span>残りの' + man(S.out) + '人は、<br>10分では着きません。</span></p>' +
        '<div class="split" role="img" aria-label="圏内が' + pct.toFixed(0) + '%、圏外が' + (100 - pct).toFixed(0) + '%"><i style="width:' + pct.toFixed(1) + '%"></i><em></em></div>' +
        '<p class="split-key"><span>10分圏内 ' + man(S.in) + '人</span><span>10分圏の外 ' + man(S.out) + '人</span></p>' +
        block("towns") + block("loss") + block("visit") +
        '<details class="more blk"><summary>数え方と、まだ粗いところ</summary><ul class="caveats">' +
        '<li>自転車で10分を、直線で1.5kmと置きました。時速12kmで走ると道のりは2kmで、道は直線より3割ほど遠回りになる、という仮の計算です。坂や川、線路は見ていません。</li>' +
        '<li>人口は、2020年の国勢調査を250m四方に区切ったものです。島は入れていません。</li>' +
        '<li>都内の銭湯は、東京都浴場組合の東京銭湯マップに載っている' + S.sento_tokyo + '軒です。組合に入っていない銭湯は入っていません。2026年11月28日に読みました。</li>' +
        '<li>このうち、一覧で休業中になっている' + S.sento_paused + '軒は、10分圏の数に入れていません。</li>' +
        '<li>都の外の銭湯は、OpenStreetMapにある' + S.sento_around + '軒を使いました。都内の一覧より抜けが多く、県境の近くでは圏外が多めに出ているはずです。</li>' +
        '<li>いい銭湯かどうか、これからも続きそうかどうかは、まだ見ていません。</li></ul>' +
        '<p class="note">出どころは、<a href="https://www.e-stat.go.jp/gis">e-Statの地図で見る統計</a>、<a href="https://www.1010.or.jp/map/">東京銭湯マップ</a>、<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>、<a href="https://github.com/gsi-cyberjapan/optimal_bvmap">国土地理院最適化ベクトルタイル</a>、<a href="https://commons.wikimedia.org/">Wikimedia Commons</a>です。</p></details>' +
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
        if (map.getSize().x) map.flyToBounds(b, { paddingTopLeft: [h.x + 48, 120], paddingBottomRight: [48, h.y + 48], maxZoom: 13, duration: 0.6 });
      } else {
        html += '<p class="empty">このタイプの銭湯は、まだ書いていません。行って見つけたら書き足します。</p>';
      }
      html += '<p class="note">タイプは、資料で裏が取れた銭湯にだけつけています。クラブ銭湯で回った銭湯も、ここに書き足していきます。</p>';
      show(html, t.name + "の銭湯は" + list.length + "軒です");
      lift();
    }

    function photoStrip(s) {
      var ps = s.photos || [];
      var gq = "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(s.name + " " + (s.address || s.area || ""));
      if (!ps.length) return '<a class="nophoto" href="' + esc(gq) + '" target="_blank" rel="noopener">' + icon("images") + '<span>写真はまだありません。Googleマップで写真を見る</span></a>';
      return '<ul class="photos-s">' + ps.map(function (p) {
        if (!url(p.thumb)) return "";
        return '<li><a href="' + url(p.page) + '" target="_blank" rel="noopener"><img src="' + url(p.thumb) + '" alt="' + esc(s.name) + 'の写真" loading="lazy" referrerpolicy="no-referrer"></a>' +
          '<span class="credit">' + (p.date ? esc(p.date.replace(/^(\d{4})-0?(\d{1,2}).*$/, "$1年$2月")) + "に撮影。" : "") + '写真は' + esc(p.artist || "撮った人の名前なし") + '、' + (url(p.licenseUrl) ? '<a href="' + url(p.licenseUrl) + '" target="_blank" rel="noopener">' + esc(p.license) + "</a>" : esc(p.license)) + "</span></li>";
      }).join("") + '</ul>' + '<a class="morephoto" href="' + esc(gq) + '" target="_blank" rel="noopener">Googleマップでほかの写真を見る</a>';
    }

    // この銭湯について: なくなると困る人、10分圏の人、創業、代替わり。わからないものは「まだわからない」と出す
    function factsBlock(s) {
      var nx = sento[s.next[0]];
      var near = nx ? '<button class="row near" type="button" data-go="s=' + esc(nx.id) + '">' + icon("bath") + '<span class="row-main"><span class="row-sub">' + (s.paused ? "いちばん近い、開いている銭湯" : "いちばん近いほかの銭湯") + '</span><strong>' + esc(nx.name) + '</strong></span><span class="row-n">直線で' + km(s.next[1]) + '</span></button>' : "";
      if (s.paused) return '<section class="blk"><h3>この銭湯について</h3>' + near + '</section>';
      var h = s.hist || {}, tokyo = s.src === "tokyo";
      var cells = [
        ["なくなると10分で銭湯に行けなくなる人", '<b>' + num(s.only) + '</b>人'],
        ["10分圏に住む人", '<b>' + num(s.reach) + '</b>人']
      ];
      if (tokyo) {
        cells.push(["創業", h.founded ? '<b>' + (YEAR - h.founded + 1) + '</b>年目<small>' + esc(h.foundedText || "") + "、" + h.founded + "年</small>" : '<span class="unk">まだわからない</span>']);
        cells.push(["代替わり", h.gen ? (h.gen >= 2 ? '<b>' + h.gen + '</b>代目まで' : "創業した人が続けている") : '<span class="unk">まだわからない</span>']);
      }
      var note = [];
      if (h.renewal) note.push(h.renewal + "年に改装しています。");
      if (h.src && url(h.src)) note.push('創業と代替わりは<a href="' + url(h.src) + '" target="_blank" rel="noopener">組合のサイトの記事</a>によります。');
      else if (tokyo && !(h.founded || h.gen)) note.push("創業や代替わりは、行って聞いたら書き足します。");
      note.push("地図の円は、ここから直線で1.5kmです。");
      return '<section class="blk"><h3>この銭湯について</h3><dl class="facts4">' +
        cells.map(function (c) { return "<div><dt>" + c[0] + "</dt><dd>" + c[1] + "</dd></div>"; }).join("") + "</dl>" +
        '<p class="note">' + note.join("") + "</p>" + near + "</section>";
    }

    function showSento(s) {
      current = s; mark(s);
      var gmap = "https://www.google.com/maps/dir/?api=1&destination=" + s.la + "," + s.lo;
      var html = head("銭湯") + photoStrip(s) +
        '<h2 class="name">' + esc(s.name) + '</h2>' +
        (s.kana ? '<p class="kana">' + esc(s.kana) + '</p>' : "") +
        '<p class="area">' + esc(s.area || "都の外") + '</p>' +
        (s.paused ? '<p class="paused-note">組合の一覧で、休業中になっています。10分圏の数には入れていません。</p>' : "") +
        ((s.types || []).length ? '<ul class="tchips">' + s.types.map(function (id) { var t = typeById[id]; return '<li>' + icon(t.icon) + esc(t.name) + '</li>'; }).join("") + '</ul>' : "") +
        statusLine(s) +
        '<div class="acts">' +
        '<a class="act primary" href="' + gmap + '" target="_blank" rel="noopener"><span class="act-i">' + icon("navigation") + '</span>経路を見る</a>' +
        (s.src === "tokyo"
          ? '<a class="act" href="' + url(s.url) + '" target="_blank" rel="noopener"><span class="act-i">' + icon("external-link") + '</span>組合のページ</a>'
          : '<a class="act" href="' + url(s.url) + '" target="_blank" rel="noopener"><span class="act-i">' + icon("external-link") + '</span>地図の元</a>') +
        '<button class="act" type="button" data-share><span class="act-i">' + icon("share-2") + '</span>リンクを送る</button></div>';

      html += factsBlock(s);
      if (s.src === "tokyo") {
        var info = [
          ["map-pin", "住所", esc(s.address)],
          ["clock", "営業時間", s.sched
            ? '<details class="hours"><summary>' + esc(s.hours) + '</summary>' + weekTable(s) + '<p class="note">休み: ' + esc(s.closed) + "</p></details>"
            : esc(s.hours)],
          ["calendar-x", "休み", s.sched ? "" : esc(s.closed)],
          ["train-front", "行き方", esc(s.access)],
          ["phone", "電話", s.tel ? '<a href="tel:' + esc(s.tel.replace(/[^\d+]/g, "")) + '">' + esc(s.tel) + "</a>" : ""],
          ["globe", "公式ページ", (s.links || []).map(function (l) { return url(l[1]) ? '<a href="' + url(l[1]) + '" target="_blank" rel="noopener">' + esc(l[0]) + "</a>" : ""; }).join("、")]
        ].filter(function (r) { return r[2]; });
        html += '<section class="blk"><h3>行くとき</h3><ul class="info">' + info.map(function (r) { return '<li>' + icon(r[0]) + '<div><span class="sr">' + r[1] + '</span>' + r[2] + '</div></li>'; }).join("") + '</ul></section>';
      } else {
        html += '<p class="note">都の外の銭湯です。OpenStreetMapにある名前と位置だけで、くわしい中身はありません。</p>';
      }
      if ((s.notes || []).length) {
        html += '<section class="blk"><h3>いい普通の銭湯のタイプ</h3>' + s.notes.map(function (n) {
          return '<div class="tnote"><p>' + esc(n.what) + '</p><p class="note">' + (url(n.src) ? '<a href="' + url(n.src) + '" target="_blank" rel="noopener">' + esc(n.srcName) + '</a>' : esc(n.srcName)) + (n.date ? '、<span class="nw">' + esc(n.date.replace(/^(\d+)-0?(\d+)-0?(\d+)$/, "$1年$2月$3日")) + "の資料</span>" : "") + '</p></div>';
        }).join("") + '</section>';
      }

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
      document.querySelectorAll(".chip[data-type]").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.type === filter ? "true" : "false"); });
      if ((m = h.match(/^s=(.+)$/)) && byId[m[1]]) return showSento(byId[m[1]]);
      if ((m = h.match(/^q=(.+)$/))) { if (input.value !== m[1]) input.value = m[1]; $("clear").hidden = false; return showResults(m[1]); }
      if (f) return showType(f);
      if (h === "f") return showFilters();
      if (/^a=/.test(h)) return showArea();
      if ((m = h.match(/^l=(towns|loss|visit)$/))) return showList(m[1]);
      showHome();
    }
    window.addEventListener("hashchange", route);

    body.addEventListener("click", function (ev) {
      var b = ev.target.closest("[data-go],[data-fly],[data-back],[data-share],[data-fshow],[data-fclear],[data-onmap],[data-home]");
      if (!b) return;
      if (b.hasAttribute("data-home")) { input.value = ""; $("clear").hidden = true; navs = 0; history.replaceState(null, "", location.pathname); route(); return; }
      if (b.dataset.onmap) {
        F[b.dataset.onmap] = true; fupdate();
        var on = sento.filter(function (x) { return fmatch(x); });
        if (on.length && map.getSize().x) {
          var hb = hidden();
          if (!wide.matches) { setState("peek"); hb = { x: 0, y: 136 }; }
          map.flyToBounds(L.latLngBounds(on.map(function (x) { return [x.la, x.lo]; })), { paddingTopLeft: [hb.x + 48, 120], paddingBottomRight: [48, hb.y + 48], maxZoom: 15, duration: 0.6 });
        }
        toast(on.length + "軒を地図に出しました。上の「絞りこむ」で条件を消せます");
        return;
      }
      if (b.hasAttribute("data-fclear")) { F = {}; FAREA = ""; showFilters(); return; }
      if (b.hasAttribute("data-fshow")) {
        var hits = sento.filter(function (x) { return fmatch(x); });
        if (hits.length && map.getSize().x) {
          var hh = hidden();
          if (!wide.matches) { setState("peek"); hh = { x: 0, y: 136 }; }
          map.flyToBounds(L.latLngBounds(hits.map(function (x) { return [x.la, x.lo]; })), { paddingTopLeft: [hh.x + 48, 120], paddingBottomRight: [48, hh.y + 48], maxZoom: 15, duration: 0.6 });
        }
        return;
      }
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
    $("chips").innerHTML = '<button class="chip filter-chip" type="button" aria-pressed="false" data-filters>' + icon("sliders-horizontal") + '絞りこむ<span class="badge"></span></button>' +
      '<button class="chip open-chip" type="button" aria-pressed="false" data-open>' + icon("clock") + 'いま営業中</button>' +
      '<button class="chip" type="button" aria-pressed="false" data-visit>' + icon("message-circle") + '話を聞きに行く候補</button>';
    $("chips").addEventListener("click", function (ev) {
      var b = ev.target.closest(".chip");
      if (b && b.hasAttribute("data-filters")) { go("f"); return; }
      if (b && b.hasAttribute("data-visit")) {
        if (F.visit) delete F.visit; else F.visit = true;
        fupdate();
        var cv = body.querySelector('[data-f="visit"]');
        if (cv) cv.checked = !!F.visit;
        toast(F.visit ? "話を聞きに行く候補は" + sento.filter(function (x) { return fmatch(x); }).length + "軒です" : (factive() ? sento.filter(function (x) { return fmatch(x); }).length + "軒を出しています" : "すべての銭湯を出しています"));
        return;
      }
      if (b && b.hasAttribute("data-open")) {
        if (F.open) delete F.open; else F.open = true;
        fupdate();
        var cb = body.querySelector('[data-f="open"]');
        if (cb) cb.checked = !!F.open;
        var n = sento.filter(function (x) { return fmatch(x); }).length;
        toast(F.open ? "いま営業中の銭湯は" + n + "軒です" : (factive() ? n + "軒を出しています" : "すべての銭湯を出しています"));
        return;
      }
      if (b && b.dataset.type) go(b.dataset.type === filter ? "" : "t=" + b.dataset.type);
    });

    $("applied").addEventListener("click", function (ev) {
      var b = ev.target.closest(".ach");
      if (!b) return;
      if (b.dataset.unf) delete F[b.dataset.unf];
      if (b.hasAttribute("data-unarea")) FAREA = "";
      if (b.hasAttribute("data-unall")) { F = {}; FAREA = ""; }
      fupdate();
      if (location.hash === "#f") showFilters();
      else if (!location.hash || location.hash === "#") showHome();
      showLabels();
      toast(factive() ? sento.filter(function (x) { return fmatch(x); }).length + "軒を出しています" : "すべての銭湯を出しています");
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
    var userMoved = false;
    map.on("dragstart zoomstart", function (ev) { if (ev.originalEvent || ev.type === "dragstart") userMoved = true; });
    map.getContainer().addEventListener("wheel", function () { userMoved = true; }, { passive: true });
    map.on("moveend", function () { if (userMoved) { $("area").hidden = false; userMoved = false; } });
    $("area").addEventListener("click", function () { this.hidden = true; go("a=" + Date.now()); });
    function showArea() {
      current = null; unmark();
      // 横（スマホでは下）の欄に隠れていない範囲だけを数え、その真ん中から近い順に並べる
      var hh = hidden(), sz = map.getSize();
      var b = L.latLngBounds(map.containerPointToLatLng([hh.x, 0]), map.containerPointToLatLng([sz.x, sz.y - hh.y]));
      var c = map.containerPointToLatLng([hh.x + (sz.x - hh.x) / 2, (sz.y - hh.y) / 2]);
      var list = sento.filter(function (s) { return b.contains([s.la, s.lo]) && (!factive() || fmatch(s)); })
        .sort(function (a, z) { return c.distanceTo([a.la, a.lo]) - c.distanceTo([z.la, z.lo]); });
      show(head("このあたりの銭湯") + '<p class="fsen">地図に映っている銭湯は<b>' + list.length + '</b>軒です' + (factive() ? "。絞りこみの条件に合うものだけを数えています" : "") + '</p>' +
        (list.length ? '<ol class="list">' + list.slice(0, 60).map(function (s) { return row(s, km(Math.round(c.distanceTo([s.la, s.lo]))), "", null); }).join("") + "</ol>" + (list.length > 60 ? '<p class="note">地図の真ん中から近い順に60軒まで出しています。</p>' : "")
          : '<p class="empty">地図に映っている範囲に、銭湯はありません。地図を広げてみてください。</p>'), "このあたりの銭湯は" + list.length + "軒です");
      lift();
    }

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

    setInterval(function () { if (F.open) restyle(); }, 60000);
    var lg = $("legend");
    lg.innerHTML = '<div class="lg-head"><strong>地図の見方</strong><button class="icon-btn" type="button" data-lgclose aria-label="地図の見方を閉じる">' + icon("x") + '</button></div><ul>' +
      '<li><i class="k-dot"></i>都内の銭湯</li><li><i class="k-dot osm"></i>都の外の銭湯</li><li><i class="k-dot paused"></i>休業中の銭湯</li>' +
      '<li><i class="k-dot big"></i>タイプがわかっている銭湯</li><li><i class="k-dot dim"></i>絞りこみの条件に合わない銭湯</li>' +
      '</ul><p class="lg-sub">10分で行ける銭湯の数</p><ul class="lg-steps"><li><i class="st1"></i>1軒だけ</li><li><i class="st2"></i>2〜3軒</li><li><i class="st3"></i>4軒以上</li><li><i class="st0"></i>0軒。人が多いほど濃い</li></ul>';
    function setLegend(open) { lg.hidden = !open; $("lgbtn").setAttribute("aria-pressed", open ? "true" : "false"); }
    setLegend(wide.matches);
    $("lgbtn").addEventListener("click", function () { setLegend(lg.hidden); });
    lg.addEventListener("click", function (ev) { if (ev.target.closest("[data-lgclose]")) setLegend(false); });
    draw();
    placeCtrls();
    var h0 = hidden();
    if (map.getSize().x && map.getSize().y) map.fitBounds([[35.53, 139.28], [35.82, 139.9]], { paddingTopLeft: [h0.x, wide.matches ? 48 : 104], paddingBottomRight: [0, h0.y], animate: false });
    route();
    showLabels();
  }
})();
