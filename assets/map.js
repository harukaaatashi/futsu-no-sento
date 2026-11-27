// 空白地帯マップ。data/map の3つのファイルを読んで、地図と区市の一覧を描く
(function () {
  var RADIUS = 1500;
  var el = document.getElementById("gapmap");
  var map = L.map(el, { minZoom: 9, maxZoom: 16, scrollWheelZoom: false });
  map.fitBounds([[35.53, 139.28], [35.82, 139.9]]);
  map.attributionControl.setPrefix(false);
  L.tileLayer("https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png", {
    attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル</a>、銭湯の位置の一部は © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);
  // 地図の上で指を止めたときだけ、ホイールで拡大できるようにする
  map.on("click", function () { map.scrollWheelZoom.enable(); });
  el.addEventListener("mouseleave", function () { map.scrollWheelZoom.disable(); });

  function km(m) { return m < 1000 ? m + "m" : (m / 1000).toFixed(1) + "km"; }
  function num(n) { return n.toLocaleString("ja-JP"); }

  Promise.all([
    fetch("data/map/cells.json").then(function (r) { return r.json(); }),
    fetch("data/map/sento.json").then(function (r) { return r.json(); })
  ]).then(function (res) {
    var g = res[0], sento = res[1], W = 8192, look = new Map();
    g.cells.forEach(function (c) { look.set(c[0] * W + c[1], c); });

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
          var yTop = map.project([g.lat0 + (r + 1) * g.dlat, 0], co.z).y - oy;
          var yBot = map.project([g.lat0 + r * g.dlat, 0], co.z).y - oy;
          for (var c = c0; c <= c1; c++) {
            var v = look.get(r * W + c);
            if (!v) continue;
            if (v[3] <= RADIUS) ctx.fillStyle = "rgba(36,104,173,0.16)";
            else ctx.fillStyle = "rgba(244,170,20," + Math.min(0.92, 0.28 + v[2] / 900).toFixed(2) + ")";
            ctx.fillRect(x0 + (c - c0) * dx, yTop, dx + 0.5, yBot - yTop + 0.5);
          }
        }
        return t;
      }
    });
    new Grid({ opacity: 1 }).addTo(map);

    var dots = L.canvas({ padding: 0.3 });
    sento.forEach(function (s) {
      L.circleMarker([s[0], s[1]], { renderer: dots, radius: 4, color: "#fff", weight: 1.5, fillColor: "#1b3358", fillOpacity: 1 })
        .bindTooltip(s[2]).addTo(map)
        .on("click", function (ev) {
          L.DomEvent.stop(ev);
          ring.setLatLng([s[0], s[1]]).addTo(map);
          L.popup().setLatLng([s[0], s[1]]).setContent("<strong>" + s[2] + "</strong><br>円は、ここから直線で1.5kmです。").openOn(map);
        });
    });
    var ring = L.circle([0, 0], { radius: RADIUS, color: "#1b3358", weight: 2, dashArray: "6 6", fill: false, interactive: false });

    map.on("click", function (ev) {
      var r = Math.floor((ev.latlng.lat - g.lat0) / g.dlat), c = Math.floor((ev.latlng.lng - g.lon0) / g.dlon);
      var v = look.get(r * W + c);
      if (!v) return;
      var s = sento[v[4]];
      ring.setLatLng([s[0], s[1]]).addTo(map);
      L.popup().setLatLng(ev.latlng).setContent(
        "<strong>" + (v[3] <= RADIUS ? "10分圏内" : "10分圏の外") + "</strong><br>この250m四方に住む人は" + num(v[2]) +
        "人。<br>いちばん近いのは" + s[2] + "で、直線で" + km(v[3]) + "です。").openOn(map);
    });

    document.querySelectorAll("[data-fly]").forEach(function (b) {
      b.addEventListener("click", function () {
        var p = b.dataset.fly.split(",");
        map.flyTo([+p[0], +p[1]], 13, { duration: 0.8 });
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      });
    });
  }).catch(function () {
    el.insertAdjacentHTML("beforeend", '<p class="map-error">地図のデータを読みこめませんでした。ページを読みこみ直してください。</p>');
  });
})();
