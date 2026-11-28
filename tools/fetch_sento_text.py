#!/usr/bin/env python3
"""組合の銭湯のページから、紹介文を手元に集める。

使い方: python3 tools/fetch_sento_text.py <元データを置くフォルダ>
読むもの: data/map/sento.json
出力: <フォルダ>/sento_text.json（銭湯の id → 紹介文と、店主に話を聞いた記事へのリンク）

紹介文は組合が書いた文章なので、リポジトリにも地図にも入れない。
創業の年や何代目かのような事実を取り出すためだけに、手元に置く。
1 秒おきに 1 ページずつ読む。
"""
import html
import json
import re
import subprocess
import sys
import time
from pathlib import Path

RAW = Path(sys.argv[1])
ROOT = Path(__file__).resolve().parent.parent


def get(url):
    for wait in (0, 5, 20):
        time.sleep(1 + wait)
        r = subprocess.run(['curl', '-s', '-4', '-m', '30', '-A', 'Mozilla/5.0 (sento coverage research)', url], capture_output=True)
        if r.returncode == 0:
            return r.stdout.decode('utf-8', 'replace')
    return ''


def main():
    out_path = RAW / 'sento_text.json'
    done = json.loads(out_path.read_text(encoding='utf-8')) if out_path.exists() else {}
    sento = [s for s in json.loads((ROOT / 'data/map/sento.json').read_text(encoding='utf-8')) if s['src'] == 'tokyo']
    for n, s in enumerate(sento):
        if s['id'] in done:
            continue
        h = get(s['url'])
        a, b = h.find('class="metas"'), h.find('最新の銭湯情報はこちら')
        text, links = '', []
        if a >= 0 and b > a:
            seg = h[a:b]
            seg = seg[seg.find('</ul>') + 5:] if '</ul>' in seg else seg
            # 「紹介記事は こちら」のような、店主に話を聞いた記事へのリンク
            for m in re.finditer(r'([^。<>]{0,30})<a[^>]+href="(https?://[^"]+)"[^>]*>\s*こちら\s*</a>', seg):
                links.append([re.sub(r'\s+', '', html.unescape(re.sub(r'<[^>]+>', '', m[1]))), m[2]])
            text = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', seg))).strip()
        done[s['id']] = {'text': text, 'links': links}
        out_path.write_text(json.dumps(done, ensure_ascii=False), encoding='utf-8')
        if n % 25 == 0:
            print(n, '/', len(sento), flush=True)
    print('おわり', len(done), '紹介文あり', sum(1 for v in done.values() if v['text']), '記事あり', sum(1 for v in done.values() if v['links']), flush=True)


if __name__ == '__main__':
    main()
