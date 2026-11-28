#!/usr/bin/env python3
"""tools/fetch_sento_history.py が作った候補から、創業の年と何代目かを決めて data/map/history.json に書く。

使い方: python3 tools/pick_history.py <元データを置くフォルダ>

決め方:
- 創業の年は、「創業」「開業」の言葉から 8 字以内にある年だけを使う。建て替えや移転の年を外すため
- 創業の年が 2 つ以上当たったときは、いちばん古い年を使う。あとの年は建て替え、移転、亡くなった年などだったため
- 何代目かは、店主、主人、女将、経営、継ぐ、「私で」などの話の中に出てきたものだけを使う
- 改装の年は、組合の紹介文の「○年リニューアル」「○年営業再開」から取る。2026 年 11 月より後の年は使わない
- 「2027年2月下旬まで改装」のように、いま改装で休んでいる銭湯は closedUntil に書く
"""
import json
import re
import sys
from pathlib import Path

RAW = Path(sys.argv[1])
ROOT = Path(__file__).resolve().parent.parent
ERA = {1867: '明治', 1911: '大正', 1925: '昭和', 1988: '平成', 2018: '令和'}
OWNER = re.compile('店主|主人|旦那|女将|おかみ|経営|継|私で|私が|僕で|僕が|当主|社長|オーナー|館主|息子|娘|跡|さん')
NOT_OWNER = re.compile('絵師|ペンキ|建物|釜|ボイラー|番台|看板|浴槽|タイル')


def era_text(y):
    for base in sorted(ERA, reverse=True):
        if y > base:
            n = y - base
            return f'{ERA[base]}{"元" if n == 1 else n}年'
    return ''


def main():
    cand = json.loads((RAW / 'history_candidates.json').read_text(encoding='utf-8'))
    cache = json.loads((RAW / 'articles.json').read_text(encoding='utf-8'))
    out = {}
    for sid, v in cand.items():
        years = set()
        for f in v['found']:
            c = f['clip']
            # 年の数字と「創業／開業」のあいだが 8 字以内か
            for m in re.finditer(r'(創業|開業)', c):
                for y in re.finditer(r'(明治|大正|昭和|平成|令和)\s*(\d{1,2}|元)|(\d{4})', c):
                    if abs(m.start() - y.start()) <= 12 and (y[3] is None or int(y[3]) == f['year']):
                        years.add(f['year'])
        gens = [g['gen'] for g in v['gen'] if OWNER.search(g['clip']) and not NOT_OWNER.search(g['clip']) and g['gen'] <= 6]
        reno = [int(re.match(r'\d{4}', r)[0]) for r in v['renewal'] if 'まで' not in r and r < '2026年12月']
        until = [re.match(r'(.*?)まで', r)[1].replace('、', '') for r in v['renewal'] if 'まで' in r]
        if not years and not gens and not reno and not until:
            continue
        src = next((s for s in v['sources'] if s['url'] in {f['src'] for f in v['found']} | {g['src'] for g in v['gen']}), v['sources'][0] if v['sources'] else None)
        h = {}
        ys = sorted(years)
        if ys:
            h['founded'] = ys[0]
            h['foundedText'] = era_text(ys[0])
        if gens:
            h['gen'] = max(gens)
        if reno:
            h['renewal'] = max(reno)
        if until:
            h['closedUntil'] = until[0]
        if src:
            h['src'] = src['url']
            h['srcName'] = '組合のサイトの記事'
            h['date'] = src['date']
        elif reno:
            h['srcName'] = '組合の銭湯のページ'
        out[sid] = h
    (ROOT / 'data/map/history.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('銭湯', len(out), '創業', sum(1 for h in out.values() if 'founded' in h), '改装で休み', sum(1 for h in out.values() if 'closedUntil' in h),
          '何代目', sum(1 for h in out.values() if 'gen' in h), '改装', sum(1 for h in out.values() if 'renewal' in h))


if __name__ == '__main__':
    main()
