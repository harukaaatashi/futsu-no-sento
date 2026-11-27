#!/usr/bin/env python3
"""東京都浴場組合の「東京銭湯マップ」から、銭湯の名前と位置を読む。

使い方: python3 tools/fetch_tokyo_sento.py <元データを置くフォルダ>
出力: <フォルダ>/tokyo_sento.json（途中の分は tokyo_sento.jsonl）

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


def main():
    log = RAW / 'tokyo_sento.jsonl'          # 途中で止まっても、続きから読めるように 1 軒ずつ書く
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
            h = get(url)
            m = re.search(r'destination=(-?\d+\.\d+),(-?\d+\.\d+)', h)
            t = re.search(r'<title>([^<]+?)\s{2,}([^：<\s]+)：', h)
            if not m or not t:
                print('読めず', url, flush=True)
                continue
            d = {'name': html.unescape(t[1]).strip(), 'area': t[2], 'lat': float(m[1]), 'lon': float(m[2]), 'url': url}
            done[url] = d
            f.write(json.dumps(d, ensure_ascii=False) + '\n')
            f.flush()
            if n % 25 == 0:
                print(n, '/', len(urls), flush=True)
    json.dump([done[u] for u in urls if u in done], open(RAW / 'tokyo_sento.json', 'w'), ensure_ascii=False, indent=0)
    print(len(done), '軒', flush=True)


if __name__ == '__main__':
    main()
