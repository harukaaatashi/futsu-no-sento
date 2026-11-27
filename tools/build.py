"""ページを作り直す。リポジトリのいちばん上で `python3 tools/build.py` を実行する。

読むもの: actions.md、data/ideas.json、data/cases.json
作るもの: index.html、idea-01.html から idea-10.html、players.md
"""
import html, json, re
from pathlib import Path

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
    f'<li><a href="idea-{i["id"]}.html"><div class="p-name"><strong>{e(i["name"])}</strong><p>{e(i["one"])}</p></div>'
    f'{meter("効果", i["effect"])}{meter("始めやすさ", i["ease"])}'
    f'<div class="who"><span>先にやっている人</span><b>{e(i["players"])}</b><span class="go">事例を{len(i["cases"])}件見る{ARROW}</span></div></a></li>'
    for i in ideas)
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
    <p>案ごとに、業界への効果、始めやすさ、先にやっている人の多さを並べました。案を押すと、調べた事例が写真つきで見られます。点数は、現場の話を聞く前の仮のものです。</p>
    <ol class="plist">{plist}</ol>
  </section>

  <section class="sec">
    <h2>最初の3か月</h2>
    <ol class="steps">{steps}</ol>
  </section>

  <section class="sec">
    <h2>何で測るか</h2>
    <p>アプリの利用者数やフォロワー数では測りません。</p>
    <ul class="measure"><li>減らせた労働時間</li><li>減らせた経費</li><li>続けられた銭湯の数</li><li>自転車10分圏内で銭湯に行ける人の割合</li></ul>
  </section>

  <footer>もとの文章は<a href="https://github.com/harukaaatashi/futsu-no-sento">GitHubのリポジトリ</a>にあります。</footer>
</main>
<script>
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
    page = head(f'{i["name"]}｜普通の銭湯研究所', i['one']) + f'''
  <a class="brand" href="index.html">普通の銭湯研究所</a>
  <nav class="crumb" aria-label="いまいる場所"><a href="index.html">全体</a>{ARROW}<a href="index.html#ideas">10個の案</a>{ARROW}<span>{e(i["name"])}</span></nav>
  <div class="idea-head">
    <h1>{e(i["name"])}</h1>
    <p class="lead">{e(i["what"])}</p>
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
