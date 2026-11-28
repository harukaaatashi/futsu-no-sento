#!/usr/bin/env python3
"""組合のサイトの、店主に話を聞いた記事から、創業の年と何代目かを取り出す候補を作る。

使い方: python3 tools/fetch_sento_history.py <元データを置くフォルダ>
読むもの: <フォルダ>/sento_text.json（tools/fetch_sento_text.py の出力）
出力: <フォルダ>/history_candidates.json

記事の本文は手元にだけ置く。ここで作るのは、人が確かめるための候補と、
その前後の短い抜き出しまで。地図に出す data/map/history.json は、候補を
確かめてから人が書く（または確かめたものだけを写す）。
"""
import html
import json
import re
import subprocess
import sys
import time
from pathlib import Path

RAW = Path(sys.argv[1])
ERA = {'明治': 1867, '大正': 1911, '昭和': 1925, '平成': 1988, '令和': 2018}
KANJI = str.maketrans('〇一二三四五六七八九', '0123456789')


def get(url):
    for wait in (0, 5, 20):
        time.sleep(1 + wait)
        r = subprocess.run(['curl', '-sL', '-4', '-m', '30', '-A', 'Mozilla/5.0 (sento coverage research)', url], capture_output=True)
        if r.returncode == 0:
            return r.stdout.decode('utf-8', 'replace')
    return ''


def body_text(h):
    h = re.sub(r'<script.*?</script>|<style.*?</style>', '', h, flags=re.S)
    a = h.find('<article')
    if a >= 0:
        h = h[a:]
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h)))


def year_of(era, n, west):
    if west:
        return int(west)
    if era in ERA:
        return ERA[era] + (1 if n == '元' else int(n))
    return None


YEAR = r'(?:(明治|大正|昭和|平成|令和)\s*(\d{1,2}|元)\s*年?\s*[（(]?\s*(\d{4})?\s*年?[）)]?|(\d{4})\s*[（(][^）)]{0,6}[）)]?)\s*年?'
FOUND = [
    re.compile(r'(?:創業|開業|開店)(?:は|したのは|されたのは|が)?[^。]{0,12}?' + YEAR),
    re.compile(YEAR + r'[^。]{0,14}?(?:創業|開業|に開店|にオープン|から営|より営|から当地|に建て)'),
]
GEN = re.compile(r'([0-9０-９一二三四五六七八九十]{1,3})代目')
SUCC = re.compile(r'[^。]{0,40}(?:継い|継が|引き継|事業承継|承継|後継|跡を継|跡継|経営を任|運営を引|新しい経営|オーナーが変|譲り受)[^。]{0,40}')


def main():
    texts = json.loads((RAW / 'sento_text.json').read_text(encoding='utf-8'))
    cache_path = RAW / 'articles.json'
    cache = json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
    out = {}
    for sid, v in texts.items():
        urls = [u for label, u in v['links'] if '1010.or.jp' in u and 'preview' not in u]
        found, gens, succ, sources = [], [], [], []
        for u in urls:
            if u not in cache:
                h = get(u)
                pub = re.search(r'article:published_time" content="([^"]+)', h) or re.search(r'"datePublished":"([^"]+)', h)
                cache[u] = {'text': body_text(h), 'date': pub[1][:10] if pub else ''}
                cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding='utf-8')
            t = cache[u]['text']
            for pat in FOUND:
                for m in pat.finditer(t):
                    g = m.groups()
                    y = year_of(g[0], g[1], g[2] or g[3]) if g[0] or g[3] else None
                    if y and 1868 <= y <= 2026:
                        found.append({'year': y, 'clip': t[max(0, m.start() - 20):m.end() + 20], 'src': u})
            for m in GEN.finditer(t):
                n = m[1].translate(KANJI).translate(str.maketrans('０１２３４５６７８９', '0123456789'))
                n = {'十': 10}.get(n, n)
                try:
                    gens.append({'gen': int(n), 'clip': t[max(0, m.start() - 25):m.end() + 15], 'src': u})
                except ValueError:
                    pass
            for m in SUCC.finditer(t):
                succ.append({'clip': m[0][:90], 'src': u})
            sources.append({'url': u, 'date': cache[u]['date']})
        # 組合の紹介文にも、リニューアルや再開の年がある
        reno = [m[0] for m in re.finditer(r'(\d{4})年(?:\d{1,2}月)?(?:\d{1,2}日)?[^。]{0,6}(?:リニューアル|営業再開|再開|改装)', v['text'])]
        if found or gens or succ or reno:
            out[sid] = {'found': found, 'gen': gens, 'succ': succ[:4], 'renewal': reno, 'sources': sources}
    (RAW / 'history_candidates.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print('記事', len(cache), '候補がある銭湯', len(out),
          '創業', sum(1 for x in out.values() if x['found']), '代目', sum(1 for x in out.values() if x['gen']),
          '引き継ぎの話', sum(1 for x in out.values() if x['succ']), flush=True)


if __name__ == '__main__':
    main()
