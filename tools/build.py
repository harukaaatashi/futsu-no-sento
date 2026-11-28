"""ページを作り直す。リポジトリのいちばん上で `python3 tools/build.py` を実行する。

読むもの: actions.md、data/ideas.json、data/cases.json
作るもの: index.html、idea-01.html から idea-10.html、map.html、players.md
空白地帯マップの data/map/sento.json に、タイプ（types.json）、写真（photos.json）、営業時間の決まり（tools/hours.py）を入れる
"""
import html, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hours import schedule  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
e = html.escape


def tidy(s):
    """画面では和文と英数字のあいだの空白を打たない。"""
    return re.sub(r'(?<=[^\x00-\x7f]) (?=[A-Za-z0-9])|(?<=[A-Za-z0-9%]) (?=[^\x00-\x7f])', '', s)


branches = []
for line in (ROOT / 'actions.md').read_text(encoding='utf-8').splitlines():
    if m := re.match(r'## (\d)\. (.+)', line):
        branches.append({'n': m[1], 't': m[2], 'g': []})
    elif m := re.match(r'### (.+)', line):
        branches[-1]['g'].append({'t': m[1], 'i': []})
    elif m := re.match(r'- (.+)', line):
        branches[-1]['g'][-1]['i'].append(m[1])
branch_name = {b['n']: tidy(b['t']) for b in branches}
icons = {'1': 'i-sento', '2': 'i-oke', '3': 'i-yu', '4': 'i-new', '5': 'i-net'}

ideas = json.loads((ROOT / 'data/ideas.json').read_text(encoding='utf-8'))
cases = json.loads((ROOT / 'data/cases.json').read_text(encoding='utf-8'))
for i in ideas:
    i['cases'] = [c for c in cases if i['id'] in c['ideas']]

months = [
    ('1', '銭湯の仕事を知る', '営業前から閉店後までの仕事を見せてもらい、一日の流れを書き出す。'),
    ('2', '一つの困りごとを解決する', '手段を決めずに、試作品を一つつくる。'),
    ('3', 'ほかの銭湯でも使えるようにする', '減らせた時間を測り、つくり方と結果を公開する。'),
]
C = 'https://upload.wikimedia.org/wikipedia/commons/thumb/'
photos = [
    ('d/d8/Tatsuno-yu_Sento_Tokyo_1.jpg', '外から見た銭湯。東京都練馬区にあります。', '瓦屋根の入口がある、昔ながらの銭湯の建物', 'Kurihaya', 'CC0', 'https://creativecommons.org/publicdomain/zero/1.0/deed.ja'),
    ('4/49/Interior_of_Bathroom_of_Kodakara-Yu.jpg', '浴室の壁に描かれた富士山。江戸東京たてもの園に残されている子宝湯です。', '白いタイルの浴室と、壁いっぱいの富士山の絵', 'kanegen', 'CC BY 2.0', 'https://creativecommons.org/licenses/by/2.0/deed.ja'),
    ('9/9b/Shoes_boxes_at_a_Sento_-_Tokyo_area_-_Dec_22_2021.jpeg', '入口の下足箱。東京近郊の銭湯です。', '番号のついた小さな扉が並ぶ、木の下足箱', 'Nesnad', 'CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/deed.ja'),
]

DEFS = '''<svg class="defs" aria-hidden="true">
  <symbol id="i-sento" viewBox="0 0 48 48"><path class="f-paper" d="M32 24V6h6v18"/><path class="f-noren" d="M6 24 24 12l18 12z"/><path class="f-paper" d="M9 24h30v18H9z"/><path class="f-blue" d="M17 28h14v7H17z"/></symbol>
  <symbol id="i-oke" viewBox="0 0 48 48"><path class="f-paper" d="M22 8h18v10H22z"/><path class="f-oke" d="M8 18h32l-4 22H12z"/><path d="M10 28h28"/></symbol>
  <symbol id="i-yu" viewBox="0 0 48 48"><path class="f-water" d="M6 26h36v6a8 8 0 0 1-8 8H14a8 8 0 0 1-8-8z"/><path d="M16 20c-3-4 3-6 0-10M24 20c-3-4 3-6 0-10M32 20c-3-4 3-6 0-10"/></symbol>
  <symbol id="i-new" viewBox="0 0 48 48"><path stroke-dasharray="3 4" d="M6 26 22 15l16 11zM9 26h26v16H9z"/><circle class="f-oke" cx="37" cy="12" r="8"/><path d="M37 8v8M33 12h8"/></symbol>
  <symbol id="i-net" viewBox="0 0 48 48"><path d="M24 12 10 36h28z"/><circle class="f-blue" cx="24" cy="12" r="6"/><circle class="f-paper" cx="10" cy="36" r="6"/><circle class="f-paper" cx="38" cy="36" r="6"/></symbol>
  <symbol id="bike" viewBox="-12 -24 52 36" overflow="visible"><circle cx="0" cy="0" r="9"/><circle cx="27" cy="0" r="9"/><path d="M0 0 9-13h12l6 13M9-13l5 13H0M21-13l-7 13M6-17h7M19-18h6"/></symbol>
  <symbol id="c-tag" viewBox="0 0 48 48"><path d="M8 8h32"/><path class="f-paper" d="M11 8h8v26h-8z"/><path class="f-blue" d="M21 8h8v26h-8z"/><path class="f-paper" d="M31 8h8v26h-8z"/></symbol>
  <symbol id="c-mix" viewBox="0 0 48 48"><circle class="f-paper" cx="17" cy="14" r="7"/><path class="f-paper" d="M5 42v-8a12 12 0 0 1 24 0v8"/><circle class="f-oke" cx="35" cy="24" r="5"/><path class="f-oke" d="M27 42v-4a8 8 0 0 1 16 0v4"/></symbol>
  <symbol id="c-town" viewBox="0 0 48 48"><path class="f-paper" d="M4 40V22l10-8 10 8v18z"/><path class="f-blue" d="M10 26h8v6h-8z"/><path class="f-paper" d="M24 40V28h10v12zM34 40V24h10v16z"/><path d="M38 30v4"/></symbol>
  <symbol id="c-sun" viewBox="0 0 48 48"><circle class="f-oke" cx="24" cy="26" r="9"/><path d="M24 6v6M8 26h4M36 26h4M11 13l4 4M37 13l-4 4M6 42h36"/></symbol>
  <symbol id="i-arrow" viewBox="0 0 16 16"><path d="M3 8h10M9 4l4 4-4 4"/></symbol>
</svg>'''
ARROW = '<svg class="arrow" aria-hidden="true"><use href="#i-arrow"/></svg>'


def head(title, desc):
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
{DEFS}
<main>
'''


def meter(label, v):
    cells = ''.join(f'<i class="{"on" if k < v else ""}"></i>' for k in range(5))
    return f'<div class="meter"><span>{label}</span><span class="cells" role="img" aria-label="5点のうち{v}点">{cells}</span><b>{v}</b></div>'


def mk(x, y, n):
    return f'<circle class="mk" cx="{x}" cy="{y}" r="11"/><text class="mk-n" x="{x}" y="{y}">{n}</text>'


def house(x, y, cls='house'):
    return f'<g class="{cls}" transform="translate({x} {y})"><path d="M0 14 14 0l14 14v18H0z"/><path d="M11 32V22h6v10"/></g>'


def date_ja(d):
    if not d:
        return '公開日は不明'
    p = d.split('-')
    return ''.join([p[0] + '年'] + ([str(int(p[1])) + '月'] if len(p) > 1 else []) + ([str(int(p[2])) + '日'] if len(p) > 2 else [])) + 'の資料'


def thumb(c, icon):
    img = f'<img src="{e(c["img"])}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">' if c.get('img') else ''
    return f'<span class="thumb">{img}<svg class="icon" aria-hidden="true"><use href="#{icon}"/></svg></span>'


# ---------- 全体のページ ----------
wall = ''
for b in branches:
    tiles = panels = ''
    for k, g in enumerate(b['g']):
        pid = f'b{b["n"]}g{k}'
        tiles += (f'<button class="tile" type="button" aria-expanded="false" aria-controls="{pid}">'
                  f'<span class="tile-t">{e(tidy(g["t"]))}</span>'
                  f'<span class="tile-n">{len(g["i"])}つ<svg class="pm" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h10"/><path class="v" d="M8 3v10"/></svg></span></button>')
        items = ''.join(f'<li>{e(tidy(i))}</li>' for i in g['i'])
        panels += f'<div class="panel" id="{pid}" hidden><h4>{e(tidy(g["t"]))}ためにできそうなこと</h4><ul>{items}</ul></div>'
    rel = ''.join(f'<a href="idea-{i["id"]}.html">{e(i["name"])}</a>' for i in ideas if i['branch'] == b['n'])
    wall += (f'<section class="branch" id="b{b["n"]}"><h3><svg class="icon" aria-hidden="true"><use href="#{icons[b["n"]]}"/></svg>'
             f'<span class="mark">{b["n"]}</span><span>{e(tidy(b["t"]))}</span></h3>'
             f'<p class="related"><span>この枝の案</span>{rel}</p><div class="tiles">{tiles}</div>{panels}</section>')

plist = ''.join(
    f'<li><a href="idea-{i["id"]}.html"><div class="p-name"><strong><span class="no">{int(i["id"])}</span>{e(i["name"])}</strong><p>{e(i["one"])}</p></div>'
    f'{meter("効果", i["effect"])}{meter("始めやすさ", i["ease"])}'
    f'<div class="who"><span>先にやっている人</span><b>{e(i["players"])}</b><span class="go">事例を{len(i["cases"])}件見る{ARROW}</span></div></a></li>'
    for i in ideas)
# 2つの軸の上に10個の案を置く。印の形で、先にやっている人の多さも見せる
PCLASS = {'見つからず': 'p-none', '一部にいる': 'p-some', '多い': 'p-many'}
NUM = [1, 2, 3, 4, 5]
AXES = {
    # 値を小さいほうから並べる。good は「よいところ」に入る値
    'effect': dict(key='effect', values=NUM, ticks=NUM, low='効果が小さい', high='効果が大きい', good=(4, 5), word='効果が大きい'),
    'ease': dict(key='ease', values=NUM, ticks=NUM, low='始めにくい', high='始めやすい', good=(4, 5), word='始めやすい'),
    'players': dict(key='players', values=['多い', '一部にいる', '見つからず'], ticks=['多い', '一部にいる', '見つからず'], low='先にやっている人が多い', high='見つからない', good=('見つからず',), word='先にやっている人が見つからない'),
}
# 切り替えの名前, 横の軸, 縦の軸, よいところの説明
VIEWS = [
    ('効果と始めやすさ', 'effect', 'ease', '始めやすくて、効果も大きいところ'),
    ('効果と先にやっている人', 'players', 'effect', '効果が大きくて、先にやっている人が見つからないところ'),
    ('始めやすさと先にやっている人', 'players', 'ease', '始めやすくて、先にやっている人が見つからないところ'),
]


def make_map(n, title, xk, yk, good_text):
    x, y = AXES[xk], AXES[yk]
    rows = ''
    for yv, yt in reversed(list(zip(y['values'], y['ticks']))):
        cells = ''
        for xv in x['values']:
            here = ''.join(f'<a class="pin {PCLASS[i["players"]]}" href="idea-{i["id"]}.html"><b>{int(i["id"])}</b><span>{e(i["name"])}</span></a>' for i in ideas if i[x['key']] == xv and i[y['key']] == yv)
            cells += f'<td class="{"good" if xv in x["good"] and yv in y["good"] else ""}">{here}</td>'
        rows += f'<tr><th scope="row">{yt}</th>{cells}</tr>'
    foot = ''.join(f'<th scope="col">{t}</th>' for t in x['ticks'])
    return f'''<div class="map-view" id="map-{n}"{"" if n == 0 else " hidden"}>
      <p class="axis-y"><span>{y["high"]}</span><span>{y["low"]}</span></p>
      <table aria-label="10個の案を、{title}で並べた図">
        <colgroup><col class="c-head"><col span="{len(x["values"])}"></colgroup>
        <tbody>{rows}</tbody>
        <tfoot><tr><td></td>{foot}</tr></tfoot>
      </table>
      <p class="axis-x"><span>{x["low"]}</span><span>{x["high"]}</span></p>
      <p class="zone"><span class="swatch"></span>{good_text}</p>
    </div>'''


switch = ''.join(f'<button class="seg" type="button" aria-pressed="{"true" if n == 0 else "false"}" data-map="map-{n}">{v[0]}</button>' for n, v in enumerate(VIEWS))
idea_map = f'''<figure class="map">
      <div class="switch" role="group" aria-label="図の軸を選ぶ">{switch}</div>
      {''.join(make_map(n, *v) for n, v in enumerate(VIEWS))}
      <ul class="legend" aria-label="印の見方">
        <li><span class="pin p-none"><b>1</b></span>先にやっている人が見つからない</li>
        <li><span class="pin p-some"><b>1</b></span>一部にいる</li>
        <li><span class="pin p-many"><b>1</b></span>多い</li>
      </ul>
    </figure>'''
clues = [
    ('c-tag', '常連さんの名前札', '来たら自分の札をひっくり返す。だれが来ているかが、ひと目でわかります。'),
    ('c-mix', '子どもとお年寄りが交わる', '学童の子どもとお年寄りが同じ場所にいて、教わったり遊んだりしています。'),
    ('c-town', '街との接点を持つ', '長屋や休憩の場所、本屋が隣にくっついていて、風呂のほかの用でも立ち寄れます。'),
    ('c-sun', '朝のラジオ体操', '夏の朝6時に集まって体操をし、風呂に入って帰ります。毎週行けば顔見知りができます。'),
]
clue_html = ''.join(f'<li><svg class="icon" aria-hidden="true"><use href="#{ic}"/></svg><strong>{t}</strong><p>{d}</p></li>' for ic, t, d in clues)
now = [
    ('はるか', '銭湯のマップを作ってみる', 'まず東京の分を作りました。なくなりそうな、いい銭湯を探すためでもあります。', 'map.html'),
    ('なる', 'クラブ銭湯をつくる', '会社の部活として、共通の入浴券でいろいろな銭湯を回り、風呂上がりに話します。', 'idea-10.html'),
    ('なる', '支える相手を深掘りする', 'どういう銭湯を、どういう人たちを支えるのかを、もう少し具体的にします。', ''),
]
now_html = ''.join(f'<li><span class="by">{w}</span><strong>{t}</strong><p>{d}</p>' + (f'<a class="go" href="{h}">{"地図を見る" if h == "map.html" else "関わる案を見る"}{ARROW}</a>' if h else '') + '</li>' for w, t, d, h in now)
steps = ''.join(f'<li><span class="when"><b>{m[0]}</b>か月目</span><strong>{m[1]}</strong><p>{m[2]}</p></li>' for m in months)
gallery = ''.join(
    f'<figure><img src="{C}{f}/960px-{f.split("/")[-1]}" alt="{e(alt)}" loading="lazy" width="960" height="720">'
    f'<figcaption>{e(cap)}<span class="credit">写真は<a href="https://commons.wikimedia.org/wiki/File:{f.split("/")[-1]}">{e(by)}</a>さん、<a href="{lic_url}">{lic}</a></span></figcaption></figure>'
    for f, cap, alt, by, lic, lic_url in photos)

index = head('普通の銭湯研究所', '日本中の誰もが、自転車で10分以内に、いい普通の銭湯に行ける世界をつくる。そのために要ることを、絵と図で整理しました。') + f'''
  <span class="brand">普通の銭湯研究所</span>
  <div class="hero">
    <div>
      <h1><span>日本中の誰もが、</span><span>自転車で10分以内に、</span><span>いい普通の銭湯に</span><span>行ける世界をつくる。</span></h1>
      <p class="lead">特別な日のレジャーではなく、ふだんの日に通える銭湯の話です。まだ現場の話を聞く前の仮説を、絵と図にまとめました。</p>
    </div>
    <figure>
      <svg class="pic" viewBox="0 0 480 400" role="img" aria-label="銭湯を中心にした円の中に家が並び、一軒の家から銭湯へ自転車で向かう道がある。円の外にも家が2軒ある。">
        <circle class="ring" cx="240" cy="206" r="172"/>
        {house(22, 318, 'house far')}{house(432, 30, 'house far')}
        {house(96, 96)}{house(338, 104)}{house(352, 268)}{house(226, 322)}{house(120, 300)}
        <path class="route" d="M112 134c-4 60 30 100 82 104"/>
        <g class="f-paper"><circle cx="126" cy="214" r="26" stroke="none"/><use href="#bike" x="101" y="202" width="52" height="36"/></g>
        <path class="f-paper" d="M270 184v-78h14v78"/>
        <g class="f-paper s-sub"><circle cx="277" cy="92" r="7"/><circle cx="287" cy="76" r="9"/><circle cx="301" cy="58" r="11"/></g>
        <path class="f-paper" d="M194 188h92v58h-92z"/>
        <path class="f-noren" d="M184 190 240 156l56 34z"/>
        <path class="f-blue" d="M214 204h52v24h-52z"/><path class="s-paper" stroke-width="2" d="M231 212v16M249 212v16"/>
        <text class="on-dark" x="240" y="217" font-size="13" text-anchor="middle" dominant-baseline="central">ゆ</text>
        <text class="halo" x="30" y="262" font-size="19">自転車で10分</text>
      </svg>
      <figcaption>円の中の家は、自転車で10分あれば銭湯に着きます。円の外の家にも、この円を届けたい。</figcaption>
    </figure>
  </div>

  <section class="sec">
    <h2>普通の銭湯の風景</h2>
    <div class="photos">{gallery}</div>
    <p class="note">写真は、見やすいように一部を切り抜いて表示しています。</p>
  </section>

  <section class="sec">
    <h2>いい普通の銭湯の手がかり</h2>
    <p>いいなと思った銭湯の例を持ち寄りました。どれも、ただ入浴する場所ではなく、人がつながる場所として働いています。地域の見守りにもなっています。</p>
    <ul class="clues">{clue_html}</ul>
    <p class="note">「いい普通の銭湯」は、まだ仮の言葉です。こうした例を集めて現地を回りながら、言葉にしていきます。</p>
  </section>

  <section class="sec">
    <h2>蛇口を開けて、栓から逃がさない</h2>
    <p>湯船のお湯を、日本にある銭湯の数だと考えます。新しくできる数より、なくなる数のほうが多ければ、お湯は減っていきます。2024年3月の時点で、銭湯は全国に2,847施設です。やることは5つに分かれます。</p>
    <div class="tub">
      <figure class="tub-fig">
        <svg class="pic" viewBox="0 0 360 352" role="img" aria-label="湯船の図。蛇口から注ぐお湯が4番の新しくつくる、栓から出ていくお湯が1番のなくさない、湯船の中が2番の通う人を増やすと3番の体験をよくする、湯船を支える床が5番の仕組みで支える。">
          <path stroke-width="9" stroke-linecap="butt" d="M20 46h58a14 14 0 0 1 14 14v14"/><path stroke-width="5" d="M52 44V28M40 28h24"/>
          <path class="s-blue" stroke-width="6" stroke-dasharray="10 8" d="M92 86v48"/>
          {mk(130, 38, 4)}<text x="148" y="38" font-size="17" dominant-baseline="central">新しくつくる</text>
          <text class="cap" x="119" y="66" font-size="13">つくれる速さを上げる</text>
          <path class="f-paper" d="M40 112v102a40 40 0 0 0 40 40h200a40 40 0 0 0 40-40V112"/>
          <path class="f-water" stroke="none" d="M42 142h276v72a38 38 0 0 1-38 38H80a38 38 0 0 1-38-38z"/>
          <path class="s-blue" stroke-width="2.5" d="M44 142c12-6 24 6 36 0s24 6 36 0 24 6 36 0 24 6 36 0 24 6 36 0 24 6 36 0 24 6 36 0 12 3 20 0"/>
          <path stroke-width="5" d="M26 112h308"/>
          {mk(100, 178, 2)}<text x="118" y="178" font-size="17" dominant-baseline="central">通う人を増やす</text>
          {mk(100, 214, 3)}<text x="118" y="214" font-size="17" dominant-baseline="central">体験をよくする</text>
          <path stroke-width="9" stroke-linecap="butt" d="M266 256v26"/>
          <path class="s-blue" stroke-width="6" stroke-dasharray="8 8" d="M266 292v22"/>
          {mk(120, 278, 1)}<text x="138" y="278" font-size="17" dominant-baseline="central">なくさない</text>
          <text class="cap" x="109" y="306" font-size="13">なくなる速さを下げる</text>
          <path class="f-noren" stroke="none" d="M0 322h360v30H0z"/>
          {mk(100, 337, 5)}<text class="on-dark" x="118" y="337" font-size="17" dominant-baseline="central">仕組みで支える</text>
        </svg>
        <figcaption>銭湯の数は<a href="https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/kenkou/seikatsu-eisei/seikatsu-eisei03/04.html">厚生労働省の公衆浴場業概要</a>によります。</figcaption>
      </figure>
      <nav class="tub-links" aria-label="5つのやること">
        {''.join(f'<a href="#b{b["n"]}"><span class="mark">{b["n"]}</span><span>{e(tidy(b["t"]))}</span></a>' for b in branches)}
      </nav>
    </div>
  </section>

  <section class="sec">
    <h2>5つのやることの中身</h2>
    <p>タイルを押すと、具体的にできそうなことが開きます。</p>
    {wall}
  </section>

  <section class="sec" id="ideas">
    <h2>10個の案と、先にやっている人</h2>
    <p>どの図も、右上にあるほどよい案です。上のボタンで、図の軸を切り替えられます。印が青く塗ってあるものは、先にやっている人が見つからなかった案です。番号は、下の一覧の番号と同じです。案を押すと、調べた事例が写真つきで見られます。点数は、現場の話を聞く前の仮のものです。</p>
    {idea_map}
    <ol class="plist">{plist}</ol>
  </section>

  <section class="sec">
    <h2>だれを支えるか</h2>
    <p>すべての銭湯を支えようとはしません。いまの考えは次のとおりで、これから深掘りします。</p>
    <ul class="targets">
      <li class="yes"><span class="tag">ここを支える</span><strong>とてもいいのに、忙しくて手が回らない銭湯</strong><p>やりたいけれど面倒でやれていないことを、代わりにやります。</p></li>
      <li><span class="tag">参考にする</span><strong>個性がとても強い銭湯</strong><p>学ぶところは多いけれど、自分たちが何かをする相手ではなさそうです。</p></li>
    </ul>
  </section>

  <section class="sec">
    <h2>いまやっていること</h2>
    <p>2026年11月27日に2人で話して決めました。毎週金曜日に、進み具合を話します。</p>
    <ul class="now">{now_html}</ul>
    <p class="note">話した中身は<a href="https://github.com/harukaaatashi/futsu-no-sento/blob/main/notes/2026-11-27.md">11月27日のメモ</a>にあります。</p>
  </section>

  <section class="sec">
    <h2>最初の3か月</h2>
    <ol class="steps">{steps}</ol>
  </section>

  <section class="sec">
    <h2>何で測るか</h2>
    <p>アプリの利用者数やフォロワー数では測りません。</p>
    <ul class="measure"><li>減らせた労働時間</li><li>減らせた経費</li><li>続けられた銭湯の数</li><li>自転車10分圏内で銭湯に行ける人の割合</li></ul>
    <p class="note">4つ目は、東京の分を<a href="map.html">空白地帯マップ</a>で数えはじめました。</p>
  </section>

  <footer>もとの文章は<a href="https://github.com/harukaaatashi/futsu-no-sento">GitHubのリポジトリ</a>にあります。</footer>
</main>
<script>
// 図の軸を切り替える
var segs = document.querySelectorAll(".seg");
segs.forEach(function (seg) {{
  seg.addEventListener("click", function () {{
    segs.forEach(function (s) {{
      s.setAttribute("aria-pressed", s === seg ? "true" : "false");
      document.getElementById(s.dataset.map).hidden = s !== seg;
    }});
  }});
}});
// タイルを押すと、その枝の下に中身を開く。同じ枝で開くのは1つだけ
document.querySelectorAll(".branch").forEach(function (branch) {{
  var tiles = branch.querySelectorAll(".tile");
  tiles.forEach(function (tile) {{
    tile.addEventListener("click", function () {{
      var open = tile.getAttribute("aria-expanded") === "true";
      tiles.forEach(function (t) {{
        t.setAttribute("aria-expanded", "false");
        document.getElementById(t.getAttribute("aria-controls")).hidden = true;
      }});
      if (!open) {{
        tile.setAttribute("aria-expanded", "true");
        document.getElementById(tile.getAttribute("aria-controls")).hidden = false;
      }}
    }});
  }});
}});
</script>
</body>
</html>
'''
(ROOT / 'index.html').write_text(index, encoding='utf-8')

# ---------- 案のページ ----------
DIALOG_JS = '''<script>
// カードを押すと、その事例のくわしい中身を重ねて開く
var dlg = document.getElementById("case");
document.querySelectorAll(".card").forEach(function (card) {
  card.addEventListener("click", function (ev) {
    ev.preventDefault();
    dlg.querySelector(".dlg-in").innerHTML = document.getElementById(card.dataset.detail).innerHTML;
    dlg.showModal();
    dlg.scrollTop = 0;
  });
});
dlg.addEventListener("click", function (ev) {
  if (ev.target === dlg || ev.target.closest("[data-close]")) dlg.close();
});
</script>'''

for n, i in enumerate(ideas):
    icon = icons[i['branch']]
    cards = details = ''
    for c in i['cases']:
        did = f'd-{c["id"]}'
        cards += (f'<li><a class="card" href="{e(c["src"])}" data-detail="{did}">{thumb(c, icon)}'
                  f'<span class="card-t">{e(c["name"])}</span><span class="card-by">{e(c["by"])}</span>'
                  f'<span class="card-w">{e(c["what"])}</span></a></li>')
        credit = f'<p class="dlg-credit">{e(c["credit"])}</p>' if c.get('credit') else (f'<p class="dlg-credit">画像は{e(c["srcName"])}のページのものです。</p>' if c.get('img') else '')
        details += (f'<template id="{did}">{thumb(c, icon)}{credit}<div class="dlg-body"><h2>{e(c["name"])}</h2><p class="dlg-by">{e(c["by"])}</p><dl>'
                    f'<div><dt>していること</dt><dd>{e(c["what"])}</dd></div>'
                    f'<div><dt>いつから</dt><dd>{e(c["since"])}</dd></div>'
                    f'<div><dt>規模</dt><dd>{e(c["scale"])}</dd></div>'
                    f'<div><dt>お金を出す人</dt><dd>{e(c["pay"])}</dd></div>'
                    f'<div><dt>出どころ</dt><dd>{e(c["srcName"])}、{date_ja(c["date"])}</dd></div></dl>'
                    f'<div class="dlg-actions"><a class="btn primary" href="{e(c["src"])}" target="_blank" rel="noopener">出どころを開く{ARROW}</a>'
                    f'<button class="btn" type="button" data-close>閉じる</button></div></div></template>')
    prev_i, next_i = ideas[n - 1], ideas[(n + 1) % len(ideas)]
    gap = ''.join(f'<li>{e(g)}</li>' for g in i['gap'])
    talk = f'''
  <section class="sec">
    <h2>2人で話したこと</h2>
    <p class="talk">{e(i["talk"])}</p>
    <p class="note">2026年11月27日に話した中身です。</p>
  </section>''' if i.get('talk') else ''
    extra = f'<p class="cta"><a class="btn primary" href="map.html">東京の地図を見る{ARROW}</a></p>' if i['id'] == '04' else ''
    page = head(f'{i["name"]}｜普通の銭湯研究所', i['one']) + f'''
  <a class="brand" href="index.html">普通の銭湯研究所</a>
  <nav class="crumb" aria-label="いまいる場所"><a href="index.html">全体</a>{ARROW}<a href="index.html#ideas">10個の案</a>{ARROW}<span>{e(i["name"])}</span></nav>
  <div class="idea-head">
    <h1>{e(i["name"])}</h1>
    <p class="lead">{e(i["what"])}</p>
    {extra}
    <a class="of-branch" href="index.html#b{i["branch"]}"><span class="mark">{i["branch"]}</span><span>{e(branch_name[i["branch"]])}ための案</span></a>
  </div>
  <div class="facts">
    <div>{meter("業界への効果", i["effect"])}</div>
    <div>{meter("始めやすさ", i["ease"])}</div>
    <div class="who-big">先にやっている人<b>{e(i["players"])}</b></div>
  </div>

  <section class="sec">
    <h2>調べてわかったこと</h2>
    <div class="two">
      <div><h3>すでにあるもの</h3><p>{e(i["found"])}</p></div>
      <div class="open"><h3>見つからなかったもの</h3><ul class="dots">{gap}</ul></div>
    </div>
    <p class="note">2026年11月に、公開されている資料を検索して調べました。見つからなかったことは、だれもやっていないことの証明ではありません。</p>
  </section>

{talk}
  <section class="sec">
    <h2>先にやっている人の事例</h2>
    <p>{len(i["cases"])}件あります。カードを押すと、いつから、どの規模で、だれのお金でやっているかが見られます。</p>
    <ul class="cards">{cards}</ul>
    {details}
  </section>

  <nav class="pager" aria-label="ほかの案">
    <a href="idea-{prev_i["id"]}.html"><small>前の案</small>{e(prev_i["name"])}</a>
    <a class="next" href="idea-{next_i["id"]}.html"><small>次の案</small>{e(next_i["name"])}</a>
  </nav>
  <footer><a href="index.html">全体のページに戻る</a></footer>
</main>
<dialog id="case" aria-label="事例のくわしい中身"><div class="dlg-in"></div></dialog>
{DIALOG_JS}
</body>
</html>
'''
    (ROOT / f'idea-{i["id"]}.html').write_text(page, encoding='utf-8')

# ---------- 空白地帯マップ ----------
# data/map/types.json に人が書いた銭湯のタイプを、名前と区市で一覧の銭湯に結びつける。
# 元データがなくても、タイプだけ書き足して作り直せるように、ここで行う
if (ROOT / 'data/map/sento.json').exists():
    sento = json.loads((ROOT / 'data/map/sento.json').read_text(encoding='utf-8'))
    tdata = json.loads((ROOT / 'data/map/types.json').read_text(encoding='utf-8'))
    tids = {t['id'] for t in tdata['types']}
    hist_path = ROOT / 'data/map/history.json'
    hist = json.loads(hist_path.read_text(encoding='utf-8')) if hist_path.exists() else {}
    photos_path = ROOT / 'data/map/photos.json'
    photos = json.loads(photos_path.read_text(encoding='utf-8')) if photos_path.exists() else {}
    for x in sento:
        x.pop('types', None)
        x.pop('notes', None)
        x.pop('photos', None)
        x.pop('sched', None)
        x.pop('hist', None)
        if hist.get(x['id']):
            x['hist'] = hist[x['id']]                  # 創業の年、何代目か、改装の年と、その出どころ
        if x['src'] == 'tokyo':
            sc = schedule(x.get('hours', ''), x.get('closed', ''))
            if sc:
                x['sched'] = sc                        # 曜日ごとの営業時間と休みの決まり。読めない銭湯は持たない
        if photos.get(x['id']):
            x['photos'] = photos[x['id']][:3]
    for m in tdata['sento']:
        hit = [x for x in sento if x['src'] == 'tokyo' and x['area'] == m['area'] and m['name'] in x['name']]
        if len(hit) != 1:
            raise SystemExit(f'types.json の「{m["name"]}、{m["area"]}」が、一覧の銭湯 1 軒に決まりません: {[h["name"] for h in hit]}')
        if set(m['types']) - tids:
            raise SystemExit(f'types.json の「{m["name"]}」に、ないタイプがあります: {set(m["types"]) - tids}')
        x = hit[0]
        x['types'] = x.get('types', []) + [t for t in m['types'] if t not in x.get('types', [])]
        x.setdefault('notes', []).append({k: m.get(k, '') for k in ('types', 'what', 'src', 'srcName', 'date')})
    (ROOT / 'data/map/sento.json').write_text(json.dumps(sento, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    sm = json.loads((ROOT / 'data/map/summary.json').read_text(encoding='utf-8'))
    sm['types'] = [dict(t, count=sum(1 for x in sento if t['id'] in x.get('types', []))) for t in tdata['types']]
    (ROOT / 'data/map/summary.json').write_text(json.dumps(sm, ensure_ascii=False, indent=1), encoding='utf-8')

# 中身は assets/map.js が data/map の JSON から描く。ここでは枠だけを作る
if (ROOT / 'data/map/summary.json').exists():
    page = '''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>空白地帯マップ｜普通の銭湯研究所</title>
<meta name="description" content="東京で、自転車10分以内に銭湯がある人の割合と、銭湯ごとのくわしい中身を地図で見られます。">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/4.7.1/maplibre-gl.min.css">
<link rel="stylesheet" href="assets/style.css">
</head>
<body class="mapapp">
<div id="gapmap" role="application" aria-label="東京の銭湯と、10分圏の内と外に住む人の地図"></div>
<form class="searchbar" id="search" role="search">
  <a class="icon-btn" href="index.html" aria-label="全体のページに戻る"><i data-lucide="house"></i></a>
  <label class="sr" for="q">銭湯をさがす</label>
  <input id="q" type="search" placeholder="銭湯、駅、区や市でさがす" autocomplete="off" enterkeyhint="search">
  <button class="icon-btn" type="button" id="clear" aria-label="入力を消す" hidden><i data-lucide="x"></i></button>
  <button class="icon-btn" type="submit" aria-label="さがす"><i data-lucide="search"></i></button>
</form>
<div class="chips" id="chips" role="group" aria-label="地図の銭湯を絞りこむ"></div>
<aside class="sheet" id="sheet" data-state="half" aria-label="銭湯のくわしい中身">
  <div class="grab" id="grab"><span class="handle"></span><span class="sr">上下に動かすと、欄の高さが変わります</span></div>
  <div class="sheet-body" id="body" tabindex="-1"><p class="loading">地図のデータを読みこんでいます。</p></div>
  <button class="collapse" id="collapse" type="button" aria-label="左の欄をしまう" aria-expanded="true"><i data-lucide="chevron-left"></i></button>
</aside>
<div class="ctrls" id="ctrls">
  <button class="ctrl" type="button" id="locate" aria-label="いまいる場所を見る"><i data-lucide="locate-fixed"></i></button>
  <button class="ctrl" type="button" id="layer" aria-pressed="true" aria-label="10分圏の塗り分けを出す"><i data-lucide="layers"></i></button>
  <div class="zoom"><button class="ctrl" type="button" id="zin" aria-label="地図を大きくする"><i data-lucide="plus"></i></button><button class="ctrl" type="button" id="zout" aria-label="地図を小さくする"><i data-lucide="minus"></i></button></div>
</div>
<p class="toast" id="toast" role="status" hidden></p>
<p class="sr" id="live" aria-live="polite"></p>
<noscript><p class="noscript">この地図は JavaScript を使います。ブラウザの設定で JavaScript を使えるようにしてください。</p></noscript>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/4.7.1/maplibre-gl.min.js"></script>
<script src="https://unpkg.com/@maplibre/maplibre-gl-leaflet@0.0.22/leaflet-maplibre-gl.js"></script>
<script src="https://unpkg.com/lucide@0.460.0/dist/umd/lucide.min.js"></script>
<script src="assets/map.js"></script>
</body>
</html>
'''
    (ROOT / 'map.html').write_text(page, encoding='utf-8')

# ---------- 文章で読む版 ----------
md = ['# 先にやっている人', '', '10 個の案ごとに、すでに取り組んでいる人や会社を調べました。2026 年 11 月に、公開されている資料を検索して集めたものです。見つからなかったことは、だれもやっていないことの証明ではありません。', '',
      'このファイルは `data/ideas.json` と `data/cases.json` から作っています。直すときは、そちらを直して `python3 tools/build.py` を実行してください。', '']
for i in ideas:
    md += [f'## {i["id"]}. {i["name"]}', '', f'先にやっている人: {i["players"]}', '', f'すでにあるもの: {i["found"]}', '', '見つからなかったもの:', ''] + [f'- {g}' for g in i['gap']] + ['', '事例:', '']
    for c in i['cases']:
        md.append(f'- [{c["name"]}]({c["src"]})、{c["by"]}。{c["what"]} いつから: {c["since"]}。規模: {c["scale"]}。お金を出す人: {c["pay"]}。出どころは{c["srcName"]}、{date_ja(c["date"])}。')
    md.append('')
(ROOT / 'players.md').write_text('\n'.join(md), encoding='utf-8')
print(len(ideas), 'ideas,', len(cases), 'cases')
