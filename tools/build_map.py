#!/usr/bin/env python3
"""空白地帯マップのデータを作る。

使い方: python3 tools/build_map.py <元データを置いたフォルダ>

元データ（リポジトリには入れない）:
  tokyo_sento.json         都内の銭湯（tools/fetch_tokyo_sento.py の出力）
  osm_bath.json            OpenStreetMap の amenity=public_bath（Overpass API の出力）
  towns.json               都内の区市町村の境界（OpenStreetMap、Overpass API の out geom）
  tblT001142Q5339.txt      2020 年国勢調査 250m メッシュ（e-Stat、1 次メッシュ 5339）
  tblT001142Q5338.txt      同じく 5338
  13.csv                   市区町村別メッシュ・コード一覧の東京都（総務省統計局）

銭湯のタイプ（data/map/types.json）は、tools/build.py が結びつける。
出力: data/map/cells.json, data/map/sento.json, data/map/summary.json
"""
import csv
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent.parent / 'data' / 'map'
OUT.mkdir(parents=True, exist_ok=True)

RADIUS = 1500          # 自転車 10 分を、直線 1.5km と置く
DLAT = 1 / 480         # 250m メッシュの縦（7.5 秒）
DLON = 1 / 320         # 250m メッシュの横（11.25 秒）
LAT0, LON0 = 35.0, 138.0

# 銭湯ではなさそうなものを名前で外す。完全ではない
DROP_TYPE = {'foot_bath', 'hand_bath', 'finger_bath', 'super_sento', 'river'}
DROP_NAME = re.compile(
    'サウナ|スパ|SPA|Spa|センター|ランド|健康|温浴|ホテル|旅館|足湯|手湯|プール|クラブ|ジム|'
    '極楽湯|湯楽の里|おふろの王様|湯けむり|万葉|天然温泉|スーパー銭湯|岩盤|カプセル|'
    '老人|福祉|いこい|憩|会館|公園|の里|の郷|の森|庭の湯|湯処|湯どころ|お湯どころ|風呂の日')


def mesh_pos(code):
    """250m メッシュのコード（10 桁）から、行と列を返す。"""
    p, u = int(code[0:2]), int(code[2:4])
    q, v = int(code[4]), int(code[5])
    r, w = int(code[6]), int(code[7])
    m, n = int(code[8]) - 1, int(code[9]) - 1
    row = ((p * 8 + q) * 10 + r) * 4 + (m // 2) * 2 + (n // 2)
    col = (((u - 38) * 8 + v) * 10 + w) * 4 + (m % 2) * 2 + (n % 2)
    return row - int(LAT0 * 480), col


def load_towns():
    """区市町村の境界を、行ごとの線分の束にして持つ。島は外す。"""
    towns = []
    for e in json.load(open(RAW / 'towns.json'))['elements']:
        b = e['bounds']
        if b['minlat'] < 35.4:
            continue
        rows = defaultdict(list)
        for m in e['members']:
            g = m.get('geometry')
            if m['type'] != 'way' or not g:
                continue
            for a, c in zip(g, g[1:]):
                y1, y2 = sorted((a['lat'], c['lat']))
                for r in range(int((y1 - LAT0) / DLAT), int((y2 - LAT0) / DLAT) + 1):
                    rows[r].append((a['lat'], a['lon'], c['lat'], c['lon']))
        towns.append({'name': e['tags']['name'], 'b': b, 'rows': rows})
    return towns


def town_of(towns, la, lo):
    r = int((la - LAT0) / DLAT)
    for t in towns:
        b = t['b']
        if not (b['minlat'] <= la <= b['maxlat'] and b['minlon'] <= lo <= b['maxlon']):
            continue
        n = 0
        for y1, x1, y2, x2 in t['rows'].get(r, ()):
            if (y1 > la) != (y2 > la) and lo < x1 + (la - y1) * (x2 - x1) / (y2 - y1):
                n += 1
        if n % 2:
            return t['name']
    return None


Z2H = str.maketrans('０１２３４５６７８９：－−〜～', '0123456789:--~~')


def load_sento(towns):
    """都内は浴場組合の一覧、都の外は OpenStreetMap。1 軒を 1 つの辞書で返す。"""
    out = []
    for s in json.load(open(RAW / 'tokyo_sento.json')):
        if not (35.4 < s['lat'] < 36.0 and 138.9 < s['lon'] < 140.0):
            continue
        paused = '休業中' in s['name']          # 組合の一覧で名前に「（休業中）」とある銭湯
        out.append({
            'id': s['url'].rstrip('/').rsplit('/', 1)[1], 'name': re.sub(r'\s*（休業中）\s*', '', s['name']), 'kana': s.get('kana', ''),
            'paused': paused,
            'area': s['area'], 'la': round(s['lat'], 5), 'lo': round(s['lon'], 5), 'src': 'tokyo',
            'address': s.get('address', '').translate(Z2H), 'tel': s.get('tel', ''), 'access': s.get('access', '').translate(Z2H),
            'closed': s.get('closed', '').translate(Z2H), 'hours': s.get('hours', '').translate(Z2H),
            'links': s.get('links', []), 'services': s.get('services', []), 'features': s.get('features', []),
            'url': s['url'],
        })
    for e in json.load(open(RAW / 'osm_bath.json'))['elements']:
        t = e.get('tags', {})
        lat = e.get('lat') or e.get('center', {}).get('lat')
        lon = e.get('lon') or e.get('center', {}).get('lon')
        if lat is None or not (35.4 < lat < 36.0 and 138.85 < lon < 140.0):
            continue
        name = t.get('name', '')
        kind = t.get('bath:type', '')
        if not name or kind in DROP_TYPE:
            continue
        if kind != 'sento' and DROP_NAME.search(name):
            continue
        if town_of(towns, lat, lon):
            continue
        out.append({'id': f'osm-{e["type"][0]}{e["id"]}', 'name': name.split(';')[0], 'la': round(lat, 5), 'lo': round(lon, 5),
                    'src': 'osm', 'url': f'https://www.openstreetmap.org/{e["type"]}/{e["id"]}'})
    return out


def main():
    towns = load_towns()
    near = set()                      # 都にかかる 1km メッシュ。細かい判定の前のふるい
    with open(RAW / '13.csv', encoding='cp932') as f:
        for code, name, mesh in list(csv.reader(f))[1:]:
            near.add(mesh)

    sento = load_sento(towns)
    grid = defaultdict(list)          # 粗いマス目に銭湯を入れて、近いものだけを比べる。休業中の銭湯は数えない
    for i, s in enumerate(sento):
        if not s.get('paused'):
            grid[(int(s['la'] * 20), int(s['lo'] * 20))].append(i)

    def dist(i, la, lo):
        return math.hypot((sento[i]['la'] - la) * 111320.0, (sento[i]['lo'] - lo) * 111320.0 * math.cos(math.radians(la)))

    def around(la, lo, span):
        gy, gx = int(la * 20), int(lo * 20)
        for y in range(gy - span, gy + span + 1):
            for x in range(gx - span, gx + span + 1):
                yield from grid.get((y, x), ())

    def nearest(la, lo, skip=-1):
        best, bi = 1e9, -1
        for span in (1, 3, 8):
            for i in around(la, lo, span):
                d = dist(i, la, lo)
                if i != skip and d < best:
                    best, bi = d, i
            if best < span * 4000:
                break
        return best, bi

    cells = []
    by_town = defaultdict(lambda: [0, 0, 0.0, 0.0])    # [人口, 圏内の人口, 緯度×人口, 経度×人口]
    reach = defaultdict(int)          # 銭湯ごとの、10 分圏に住む人
    only = defaultdict(int)           # そのうち、10 分圏にほかの銭湯がない人
    for name in ('tblT001142Q5339.txt', 'tblT001142Q5338.txt'):
        with open(RAW / name, encoding='cp932') as f:
            rows = list(csv.reader(f))[2:]
        for r in rows:
            code = r[0]
            if code[:8] not in near or not r[4].isdigit() or int(r[4]) == 0:
                continue
            pop = int(r[4])
            row, col = mesh_pos(code)
            la = LAT0 + (row + 0.5) * DLAT
            lo = LON0 + (col + 0.5) * DLON
            tn = town_of(towns, la, lo)
            if not tn:
                continue
            d, si = nearest(la, lo)
            d = int(round(d))
            hits = [i for i in around(la, lo, 1) if dist(i, la, lo) <= RADIUS] if d <= RADIUS else []
            cells.append([row, col, pop, d, si, len(hits)])   # 最後は、10 分で行ける銭湯の数
            t = by_town[tn]
            t[0] += pop
            t[2] += la * pop
            t[3] += lo * pop
            if d <= RADIUS:
                t[1] += pop
                for i in hits:
                    reach[i] += pop
                if len(hits) == 1:
                    only[hits[0]] += pop

    for i, s in enumerate(sento):
        s['reach'] = reach[i]
        s['only'] = only[i]
        d, j = nearest(s['la'], s['lo'], skip=i)
        s['next'] = [j, int(round(d))]

    total = sum(c[2] for c in cells)
    inside = sum(c[2] for c in cells if c[3] <= RADIUS)
    town_out = [{'name': k, 'pop': v[0], 'in': v[1], 'lat': round(v[2] / v[0], 4), 'lon': round(v[3] / v[0], 4)}
                for k, v in by_town.items()]
    town_out.sort(key=lambda t: t['in'] - t['pop'])
    summary = {
        'radius': RADIUS, 'pop': total, 'in': inside, 'out': total - inside,
        'cells': len(cells), 'sento_tokyo': sum(1 for s in sento if s['src'] == 'tokyo'),
        'sento_paused': sum(1 for s in sento if s.get('paused')),
        'sento_around': sum(1 for s in sento if s['src'] == 'osm'), 'towns': town_out,
    }

    json.dump({'lat0': LAT0, 'lon0': LON0, 'dlat': DLAT, 'dlon': DLON, 'cells': cells},
              open(OUT / 'cells.json', 'w'), separators=(',', ':'))
    json.dump(sento, open(OUT / 'sento.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    json.dump(summary, open(OUT / 'summary.json', 'w'), ensure_ascii=False, indent=1)
    print(f'人口 {total:,} / 圏内 {inside:,} ({inside / total:.1%}) / 圏外 {total - inside:,}')
    print(f'メッシュ {len(cells):,} / 都内の銭湯 {summary["sento_tokyo"]} / まわり {summary["sento_around"]}')
    for s in sorted(sento, key=lambda s: -s['only'])[:8]:
        print(s['name'], s.get('area', ''), f"10分圏 {s['reach']:,}", f"ここだけ {s['only']:,}")


if __name__ == '__main__':
    main()
