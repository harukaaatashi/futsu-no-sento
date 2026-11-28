#!/usr/bin/env python3
"""Wikimedia Commons の「Sento in Tokyo」の分類から、都内の銭湯の写真を集める。

使い方: python3 tools/fetch_commons_photos.py
読むもの: data/map/sento.json
出力: data/map/photos.json（銭湯の id → 写真）

分類の下にある銭湯ごとの分類（Kosugiyu、Inari-yu (1930) など）を、銭湯の名前の
ローマ字と区の名前で一覧の銭湯に結びつける。名前が合っても、写真の撮影地が
銭湯から 300m より遠いものは使わない。使ってよい条件が CC0、パブリックドメイン、
CC BY、CC BY-SA のものに限る。問い合わせは 1 秒おきにする。
"""
import html
import json
import math
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = 'https://commons.wikimedia.org/w/api.php'
TOP = 'Category:Sento in Tokyo'
OK_LICENSE = re.compile(r'^(CC0|Public domain|PD|CC BY(-SA)? [0-9.]+)', re.I)
PLACES = {
    'adachi': '足立区', 'arakawa': '荒川区', 'bunkyo': '文京区', 'chiyoda': '千代田区', 'chuo': '中央区', 'edogawa': '江戸川区',
    'itabashi': '板橋区', 'katsushika': '葛飾区', 'kita': '北区', 'koto': '江東区', 'meguro': '目黒区', 'minato': '港区',
    'nakano': '中野区', 'nerima': '練馬区', 'ota': '大田区', 'setagaya': '世田谷区', 'shibuya': '渋谷区', 'shinagawa': '品川区',
    'shinjuku': '新宿区', 'suginami': '杉並区', 'sumida': '墨田区', 'taito': '台東区', 'toshima': '豊島区',
    'hachioji': '八王子市', 'machida': '町田市', 'mitaka': '三鷹市', 'musashino': '武蔵野市', 'chofu': '調布市', 'fuchu': '府中市',
    'kokubunji': '国分寺市', 'tachikawa': '立川市', 'koganei': '小金井市', 'nishitokyo': '西東京市', 'kodaira': '小平市',
}
ROMA2 = {'きゃ': 'kya', 'きゅ': 'kyu', 'きょ': 'kyo', 'しゃ': 'sha', 'しゅ': 'shu', 'しょ': 'sho', 'ちゃ': 'cha', 'ちゅ': 'chu', 'ちょ': 'cho',
         'にゃ': 'nya', 'にゅ': 'nyu', 'にょ': 'nyo', 'ひゃ': 'hya', 'ひゅ': 'hyu', 'ひょ': 'hyo', 'みゃ': 'mya', 'みゅ': 'myu', 'みょ': 'myo',
         'りゃ': 'rya', 'りゅ': 'ryu', 'りょ': 'ryo', 'ぎゃ': 'gya', 'ぎゅ': 'gyu', 'ぎょ': 'gyo', 'じゃ': 'ja', 'じゅ': 'ju', 'じょ': 'jo',
         'びゃ': 'bya', 'びゅ': 'byu', 'びょ': 'byo', 'ぴゃ': 'pya', 'ぴゅ': 'pyu', 'ぴょ': 'pyo'}
ROMA1 = dict(zip(
    'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ',
    'a i u e o ka ki ku ke ko sa shi su se so ta chi tsu te to na ni nu ne no ha hi fu he ho ma mi mu me mo ya yu yo ra ri ru re ro wa o n '
    'ga gi gu ge go za ji zu ze zo da ji zu de do ba bi bu be bo pa pi pu pe po'.split()))


def romaji(kana):
    out, i = '', 0
    while i < len(kana):
        if kana[i:i + 2] in ROMA2:
            out += ROMA2[kana[i:i + 2]]; i += 2; continue
        c = kana[i]
        if c == 'っ' and i + 1 < len(kana):
            out += romaji(kana[i + 1:i + 3])[:1]
        else:
            out += ROMA1.get(c, '')
        i += 1
    return out


def flat(t):
    """長音を落とし、ou と uu をそろえ、英数字だけにする。Hōrai-yu と ほうらいゆ を同じ形にするため。"""
    t = unicodedata.normalize('NFKD', html.unescape(t or ''))
    t = ''.join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r'[^0-9a-z]', '', t)
    return t.replace('ou', 'o').replace('uu', 'u').replace('oo', 'o')


def get(params):
    q = urllib.parse.urlencode(dict(params, format='json', formatversion=2))
    req = urllib.request.Request(API + '?' + q, headers={'User-Agent': 'sento-map-research/1.0'})
    for wait in (0, 10, 30, 60):
        time.sleep(1 + wait)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            print('やり直す', e, flush=True)
    return {}


def members(cat):
    out, cont = [], {}
    while True:
        d = get(dict({'action': 'query', 'list': 'categorymembers', 'cmtitle': cat, 'cmlimit': 500, 'cmtype': 'subcat|file'}, **cont))
        out += d.get('query', {}).get('categorymembers', [])
        if 'continue' not in d:
            return out
        cont = d['continue']


def near(a, b):
    return math.hypot((a[0] - b['la']) * 111320, (a[1] - b['lo']) * 111320 * math.cos(math.radians(b['la'])))


def main():
    sento = [s for s in json.loads((ROOT / 'data/map/sento.json').read_text(encoding='utf-8')) if s['src'] == 'tokyo']
    for s in sento:
        s['flat'] = flat(romaji(s.get('kana', '').replace(' ', '')))
        s['core'] = re.sub(r'（.*?）|\(.*?\)|\s', '', s['name'])

    # 入口は「Sento in Tokyo」と、区や市ごとの「Public bath in ○○, Tokyo」
    d = get({'action': 'query', 'list': 'search', 'srnamespace': 14, 'srsearch': 'intitle:"Public bath in" Tokyo', 'srlimit': 100})
    seeds = [TOP] + [x['title'] for x in d.get('query', {}).get('search', []) if x['title'].endswith(', Tokyo')]
    print('入口', len(seeds), flush=True)

    file_cat, cat_place, seen, queue = {}, {}, set(), [(c, 0) for c in seeds]
    for c in seeds:
        m = re.search(r'Public bath in (.+), Tokyo', c)
        if m:
            cat_place[c] = next((v for k, v in PLACES.items() if k == flat(m[1])), None)
    while queue:
        cat, depth = queue.pop(0)
        if cat in seen or depth > 2:
            continue
        seen.add(cat)
        for m in members(cat):
            if m['ns'] == 14:
                cat_place.setdefault(m['title'], cat_place.get(cat))
                queue.append((m['title'], depth + 1))
            elif m['ns'] == 6:
                file_cat.setdefault(m['title'], cat)
    print('分類', len(seen), '写真', len(file_cat), flush=True)

    # 写真の条件、撮影地、説明を読む
    info = {}
    titles = list(file_cat)
    for i in range(0, len(titles), 40):
        d = get({'action': 'query', 'titles': '|'.join(titles[i:i + 40]), 'prop': 'imageinfo|coordinates',
                 'iiprop': 'url|extmetadata', 'iiurlwidth': 800, 'colimit': 'max'})
        for p in d.get('query', {}).get('pages', []):
            info[p['title']] = p
    print('読んだ写真', len(info), flush=True)

    def kanji_hit(core, t):
        """名前が、ほかの漢字の続きとして当たっていないか（子宝湯の中の宝湯を外す）"""
        i = t.find(core)
        while i >= 0:
            if i == 0 or not re.match(r'[\u4e00-\u9fff\u3040-\u30ff]', t[i - 1]):
                return True
            i = t.find(core, i + 1)
        return False

    def roma_hit(sf, text):
        """ローマ字の名前が、言葉の切れ目から始まって切れ目で終わるか（Kodakara-yu の中の takarayu を外す）"""
        toks = re.findall(r'[0-9a-z]+', unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower())
        for i in range(len(toks)):
            acc = ''
            for j in range(i, min(i + 4, len(toks))):
                acc += toks[j]
                if flat(acc) == sf:
                    return True
        return False

    def by_name(text, place):
        """題名や分類の名前に、銭湯の名前が入っている銭湯。区や市がわかれば、その中から"""
        t, f = text, flat(text)
        out = [s for s in sento if (len(s['core']) >= 2 and kanji_hit(s['core'], t)) or (len(s['flat']) >= 5 and roma_hit(s['flat'], t))]
        if place:
            out = [s for s in out if s['area'] == place]
        if len(out) > 1:                     # 長い名前で当たったほうを残す（大黒湯より押上温泉 大黒湯）
            best = max(max(len(s['core']) if s['core'] in t else 0, len(s['flat']) if s['flat'] in f else 0) for s in out)
            out = [s for s in out if max(len(s['core']) if s['core'] in t else 0, len(s['flat']) if s['flat'] in f else 0) == best]
        return out

    photos = {}
    for title, cat in file_cat.items():
        p = info.get(title)
        if not p:
            continue
        ii = (p.get('imageinfo') or [{}])[0]
        meta = ii.get('extmetadata', {})
        lic = re.sub(r'<[^>]+>', '', meta.get('LicenseShortName', {}).get('value', ''))
        if not OK_LICENSE.match(lic) or not ii.get('thumburl'):
            continue
        co = (p.get('coordinates') or [None])[0]
        co = (co['lat'], co['lon']) if co else None
        catname = cat.split(':', 1)[1]
        place = cat_place.get(cat) or next((v for k, v in PLACES.items() if re.search(r'\(.*' + k, flat(catname)) or ('(' in catname and k in flat(catname.split('(')[-1]))), None)
        desc = re.sub(r'<[^>]+>', ' ', html.unescape(meta.get('ImageDescription', {}).get('value', '') + ' ' + meta.get('ObjectName', {}).get('value', '')))
        cands = []
        if cat != TOP and not cat.startswith('Category:Public bath in'):
            cands = by_name(re.sub(r'\s*\(.*\)$', '', catname), place)      # 銭湯ごとの分類
        if not cands:
            cands = by_name(title + ' ' + desc, place)
        if co:
            cands = [s for s in cands if near(co, s) <= 300]
            if len(cands) > 1:
                cands = [min(cands, key=lambda s: near(co, s))]
        if len(cands) != 1:
            continue
        s = cands[0]
        # 撮影地も区もわからない写真は、説明に区や市の名前があるときだけ使う（同じ名前の別の銭湯を外す）
        if not co and not place:
            roma = next((k for k, v in PLACES.items() if v == s['area']), None)
            text = title + ' ' + desc
            if s['area'] not in text and not (roma and roma in flat(text)):
                continue
        photos.setdefault(s['id'], []).append({
            'thumb': ii['thumburl'], 'page': ii.get('descriptionshorturl') or ii.get('descriptionurl'),
            'license': lic, 'licenseUrl': meta.get('LicenseUrl', {}).get('value', ''),
            'artist': re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html.unescape(meta.get('Artist', {}).get('value', '')))).strip()[:80],
            'date': re.sub(r'<[^>]+>', '', meta.get('DateTimeOriginal', {}).get('value', ''))[:10],
            'file': title, 'located': bool(co),
        })
    for k in photos:            # 撮影地がわかる写真を先に、その中では新しい写真を先にする
        photos[k].sort(key=lambda x: x['date'] or '', reverse=True)
        photos[k].sort(key=lambda x: not x['located'])
    out = ROOT / 'data/map/photos.json'
    out.write_text(json.dumps(photos, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    names = {s['id']: s['name'] + '（' + s['area'] + '）' for s in sento}
    print('写真がある銭湯', len(photos), flush=True)
    for k, v in photos.items():
        print(' ', names[k], len(v), '|', v[0]['file'][:70], '|', '撮影地あり' if v[0]['located'] else '撮影地なし', flush=True)


if __name__ == '__main__':
    main()
