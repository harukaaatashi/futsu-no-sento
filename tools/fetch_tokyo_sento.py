#!/usr/bin/env python3
"""東京都浴場組合の「東京銭湯マップ」から、銭湯の名前と位置を読む。

使い方: python3 tools/fetch_tokyo_sento.py <元データを置くフォルダ>
出力: <フォルダ>/tokyo_sento.json（途中の分は tokyo_detail.jsonl）\n名前、位置、住所、電話、行き方、休み、営業時間、設備を読む。紹介文と写真は組合のものなので取らない。

相手のサイトに負担をかけないよう、1 秒おきに 1 ページずつ読む。
"""
import html
import json
import re
import subprocess
import sys
import time
from pathlib import Path

RAW = Path(sys.argv[1])
BASE = 'https://www.1010.or.jp/map/'


def get(url):
    # Python の urllib ではつながるまでに時間がかかったので、curl に任せる
    for wait in (0, 5, 20):
        time.sleep(1 + wait)
        r = subprocess.run(['curl', '-s', '-4', '-m', '30', '-A', 'Mozilla/5.0 (sento coverage research)', url],
                           capture_output=True)
        if r.returncode == 0:
            return r.stdout.decode('utf-8', 'replace')
    print('読めなかった', url, flush=True)
    return ''


def clean(t):
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', html.unescape(t)).strip()


def parse(url, h):
    """銭湯 1 軒のページから、事実だけを取り出す。紹介文と写真は取らない。"""
    m = re.search(r'destination=(-?\d+\.\d+),(-?\d+\.\d+)', h)
    a, b = h.find('<h2>'), h.find('TOKYO 銭湯検索')
    if not m or a < 0 or b < 0:
        return None
    body = h[a:b]
    t = re.search(r'<h2>(.*?)\s*\[([^\]]+)\]</h2>', body, re.S)
    if not t:
        return None
    d = {'name': clean(t[1]), 'area': clean(t[2]), 'lat': float(m[1]), 'lon': float(m[2]), 'url': url}
    k = re.search(r'class="furigana">([^<]*)<', body)
    d['kana'] = clean(k[1]) if k else ''
    rows = dict((clean(x), y) for x, y in re.findall(r'<th>(.*?)</th>\s*<td>(.*?)</td>', body, re.S))
    d['address'] = clean(rows.get('住所', ''))
    d['tel'] = clean(rows.get('電話番号', ''))
    d['access'] = clean(rows.get('アクセス', ''))
    d['closed'] = clean(rows.get('休日', ''))
    d['hours'] = clean(rows.get('営業時間', ''))
    d['links'] = [[clean(n), u] for u, n in re.findall(r'<a href="(https?://[^"]+)"[^>]*>(.*?)</a>', rows.get('公式ページ', ''), re.S)]
    d['services'] = [clean(x) for x in re.findall(r'archives/meta/[^"]+">([^<]+)<', body)]
    d['features'] = [clean(x) for x in re.findall(r'archives/item_tag/[^"]+">([^<]+)<', body)]
    return d


def main():
    log = RAW / 'tokyo_detail.jsonl'         # 途中で止まっても、続きから読めるように 1 軒ずつ書く
    done = {}
    if log.exists():
        for line in open(log, encoding='utf-8'):
            d = json.loads(line)
            done[d['url']] = d
    site = get(BASE + 'wp-sitemap-posts-item-1.xml')
    urls = sorted(set(re.findall(r'https://www\.1010\.or\.jp/map/item/[^<]+', site)))
    print(len(urls), 'ページ、うち', len(done), 'は読んである', flush=True)
    with open(log, 'a', encoding='utf-8') as f:
        for n, url in enumerate(urls):
            if url in done:
                continue
            d = parse(url, get(url))
            if not d:
                print('読めず', url, flush=True)
                continue
            done[url] = d
            f.write(json.dumps(d, ensure_ascii=False) + '\n')
            f.flush()
            if n % 25 == 0:
                print(n, '/', len(urls), flush=True)
    json.dump([done[u] for u in urls if u in done], open(RAW / 'tokyo_sento.json', 'w'), ensure_ascii=False, indent=0)
    print(len(done), '軒', flush=True)


if __name__ == '__main__':
    main()
