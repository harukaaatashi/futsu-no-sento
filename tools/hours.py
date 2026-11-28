"""組合の一覧にある「営業時間」と「休日」の文を、曜日ごとの時間と休みの決まりに読みかえる。

返すもの:
  hours: {"d": 毎日の時間, "0".."6": 曜日ごとの時間（0 が日曜）, "h": 祝日の時間}
         時間は [[開く分, 閉じる分], ...]。夜中をまたぐときは 1440 を超える（25:00 は 1500）
  off:   {"wd": 休む曜日, "nth": [[第何, 曜日]], "last": 月の最後に休む曜日, "dates": 休む日付, "months": 休みのある月}
  hol:   祝日の扱い。"open" は休みの曜日でも祝日なら営業、"next" は営業して翌日休み、"off" は祝日も休み、"" は決まりなし
  odd:   不定休や臨時の休みなど、決まりの外の休みがありうる
  ok:    読みきれたか。読みきれないときは、いま開いているかを出さない
"""
import re

WD = '日月火水木金土'
WEEKDAYS = ['1', '2', '3', '4', '5']
SKIP = re.compile('最終|受付|入店|入場|サウナ|喫茶|清掃|退出|休憩|告知|変更|掲示|朝湯を実施|別料金|ミスト|待合室')
NUM = str.maketrans('０１２３４５６７８９一二三四五', '012345678912345')


def _time_text(t):
    t = t.replace('〜', '-').replace('~', '-').replace('－', '-').replace('−', '-')
    t = re.sub(r'(\d{1,2})-(\d{1,2})時半', r'\1:00-\2:30', t)
    t = re.sub(r'(\d{1,2})-(\d{1,2})時', r'\1:00-\2:00', t)
    t = re.sub(r'(\d{1,2})時半', r'\1:30', t)
    t = re.sub(r'(\d{1,2})時', r'\1:00', t)
    t = re.sub(r'翌日?朝?(\d{1,2}):(\d{2})', lambda m: f'{int(m[1]) + 24}:{m[2]}', t)
    return t


def _days(spec):
    """「土・日・祝日」「月~金曜」「平日」などを、曜日の番号と h（祝日）の並びにする。"""
    spec = spec.replace('祝日', '祝').replace('祭日', '祝')
    out = []
    if '平日' in spec:
        out += WEEKDAYS
    m = re.search(r'([月火水木金土日])曜?日?-([月火水木金土日])', spec)
    if m:
        a, b = WD.index(m[1]), WD.index(m[2])
        out += [str(i % 7) for i in range(a, (b if b >= a else b + 7) + 1)]
        spec = spec.replace(m[0], '')
    for c in re.findall(r'[月火水木金土日祝]', spec):
        k = 'h' if c == '祝' else str(WD.index(c))
        if k not in out:
            out.append(k)
    return out


DAYSPEC = r'(?:平日(?:[・、]\s*)?)?(?:[月火水木金土日祝](?:曜日|曜|日)?(?:\s*[・、,-]\s*|(?=[月火水木金土日祝])))*[月火水木金土日祝](?:曜日|曜|日)?|平日'
TOKEN = re.compile(
    r'(?P<range>(?:\d{1,2}:\d{2}-\d{1,2}:\d{2}(?:\s*[／/、,]\s*(?=\d{1,2}:\d{2}-))?)+)(?P<also>も営業)?'
    r'|(?P<from>\d{1,2}):(?P<fm>\d{2})(?:から|より|-(?!\d))'
    r'|(?P<until>\d{1,2}):(?P<um>\d{2})まで'
    r'|(?P<days>' + DAYSPEC + r')')


def _mins(hm):
    h, m = hm.split(':')
    return int(h) * 60 + int(m)


def parse_hours(text):
    t = text.translate(NUM)
    t = re.sub(r'\d+月\d+日[^ 、]*', ' ', t)                  # 1月2日だけの話は読まない
    if re.search(r'\d+月', t) or '第' in t:
        return None
    t = re.sub(r'（[^）)]*[）)]|\([^)）]*[)）]', ' ', t)
    t = re.sub(r'\d{1,2}:\d{2}-\d{1,2}:\d{2}\s*清掃', ' ', t)
    t = t.replace('※', ' ※')
    t = re.sub(r'、?女湯[^、 ]*', '', t)
    t = t.replace('男湯', '').replace('祝日月曜', '祝')
    t = ' '.join(c for c in re.split(r'[ 　]+', t) if c and not SKIP.search(c))
    t = _time_text(t)
    hours, cur, last_was_range = {}, None, False
    for m in TOKEN.finditer(t):
        if m['days']:
            ds = _days(m['days'])
            if ds:
                cur, last_was_range = ds, False
            continue
        keys = cur or ['d']
        if m['range']:
            rs = [[_mins(a), _mins(b)] for a, b in re.findall(r'(\d{1,2}:\d{2})-(\d{1,2}:\d{2})', m['range'])]
            for k in keys:
                if m['also']:
                    hours[k] = sorted(hours.get(k, [list(r) for r in hours.get('d', [])]) + rs)
                elif last_was_range and k in hours:
                    hours[k] = hours[k] + rs
                else:
                    hours[k] = [list(r) for r in rs]
            last_was_range = True
            continue
        base = hours.get('d')
        if not base:
            return None
        for k in keys:
            rs = [list(r) for r in hours.get(k, base)]
            if m['from']:
                rs[0][0] = _mins(m['from'] + ':' + m['fm'])
            else:
                rs[-1][1] = _mins(m['until'] + ':' + m['um'])
                if rs[-1][1] < rs[-1][0]:
                    rs[-1][1] += 1440
            hours[k] = rs
        last_was_range = False
    if not hours:
        return None
    for rs in hours.values():
        for r in rs:
            if r[1] <= r[0]:
                r[1] += 1440
    return hours


def parse_closed(text):
    t = text.translate(NUM).replace('曜日', '曜')
    odd = bool(re.search('1月\\d+日|隔週|月末の.曜は営業|不定|要確認|確認|告知|連休|振替|営業の場合あり|隔週|正月|三が日|銭湯の日|ゆず湯|しょうぶ湯|前日休|ただし|および|月末に|SNS|掲示|当面|その他', t))
    if '当面' in t:
        return None
    hol = ''
    if re.search(r'祝日?(?:の場合|時)?は?翌(?:日|火曜)', t) or re.search(r'祝日の場合は翌', t) \
            or re.search(r'翌[月火水木金土日]曜休', t) or re.search(r'祝日の場合は[月火水木金土日]曜', t):
        hol = 'next'
    elif re.search(r'(?:祝日?|祭日)(?:月曜)?(?:の場合)?は?営業|祝日でも営業', t) and '祝日でも月曜休' not in t:
        hol = 'open'
    off = {'wd': [], 'nth': [], 'last': [], 'dates': [], 'months': []}
    if re.fullmatch(r'\s*(無休|年中無休|なし)(\s.*)?', t) or t.startswith('無休'):
        return {'off': off, 'hol': hol, 'odd': odd, 'ok': True}
    base = re.split(r'[ 　（(／]', t)[0] if not t.startswith('不定休') else ''
    base = re.sub(r'\d+月\d+日(?:[・、]\d+日)*|隔週[月火水木金土日]曜?', '', base)   # 正月だけの休みと、隔週の休みは決まりに入れない
    if '祝' in base:
        hol = 'off'                                    # 「日曜、祝日」のように、祝日も休み
        base = re.sub(r'[、・]?祝日?', '', base)
    m = re.match(r'([\d・、,]+)月の(.*)', base)
    if m:
        off['months'] = [int(x) for x in re.findall(r'\d+', m[1])]
        base = m[2]
    for n_text, d in re.findall(r'第(\d(?:\s*[・、,]\s*第?\d)*)\s*([月火水木金土日])曜?', base):
        for n in re.findall(r'\d', n_text):
            off['nth'].append([int(n), WD.index(d)])
    base = re.sub(r'第\d(?:\s*[・、,]\s*第?\d)*\s*[月火水木金土日]曜?日?', '', base)
    for d in re.findall(r'(?:最終|月末の|毎月最後の)([月火水木金土日])曜?', base):
        off['last'].append(WD.index(d))
    base = re.sub(r'(?:最終|月末の|毎月最後の)[月火水木金土日]曜?', '', base)
    if re.search(r'\d+日', base) and not re.search('曜', base):
        off['dates'] = [int(x) for x in re.findall(r'(\d{1,2})(?=日|[、・,])', base)]
        base = ''
    m = re.search(r'([月火水木金土日])曜?日?[~-]([月火水木金土日])曜', base)
    if m:
        a, b = WD.index(m[1]), WD.index(m[2])
        off['wd'] += [i % 7 for i in range(a, (b if b >= a else b + 7) + 1)]
        base = base.replace(m[0], '')
    for spec in re.findall(r'((?:[月火水木金土日](?:曜日?)?\s*[・、,]?\s*)+)', base):
        if '曜' not in spec and not re.fullmatch(r'[月火水木金土日](\s*[・、,]\s*[月火水木金土日])+', spec.strip(' 、・,')):
            continue
        for c in re.findall(r'[月火水木金土日]', spec):
            if WD.index(c) not in off['wd']:
                off['wd'].append(WD.index(c))
    if '不定休' in t:
        odd = True
    if not any(off.values()) and not odd:
        return None
    return {'off': off, 'hol': hol, 'odd': odd, 'ok': True}


def schedule(hours_text, closed_text):
    h = parse_hours(hours_text or '')
    c = parse_closed(closed_text or '')
    if not h or not c:
        return None
    # 休みでない曜日には、どれも時間が書いてあること
    if 'd' not in h and any(str(i) not in h for i in range(7) if i not in c['off']['wd']):
        return None
    return {'hours': h, 'off': c['off'], 'hol': c['hol'], 'odd': c['odd']}
