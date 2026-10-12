#!/usr/bin/env python3
"""The Ten Biggest Weeks -- the scoring record, and the record behind it.

    python3 scripts/build_bigweeks.py

Every figure comes out of history.json, the ESPN import covering eighteen
seasons, so the page cannot disagree with the record book.

The piece exists because the raw list is misleading. Scoring in this league has
moved a long way -- the average team week was 78.5 points in 2011 and 101.2 in
2018 -- so a number put up in a low-scoring year is worth more than the same
number put up in a high-scoring one. Ranked against its own season, the record
changes hands.
"""
import importlib.util, json, os, re, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts', 'build_addendum.py'))
ad = importlib.util.module_from_spec(_s); sys.modules['ad'] = ad; _s.loader.exec_module(ad)
E = ad.esc
OUT = os.path.join(ROOT, 'scfl-big-weeks.html')
OG = os.path.join(ROOT, 'scfl-big-weeks-og.jpg')

# the import carries display noise -- asterisks a manager put round his own
# name, and doubled spaces -- which is not part of the franchise's name
clean = lambda s: re.sub(r'\s+', ' ', (s or '').replace('*', '')).strip()

# A live run at the record, reported from the app while the week is still being
# played. Set to None once the week is final and the real figure is in the
# week data -- it is a press box note, not a record, and it says so.
LIVE = {
    'team': 'Beaver Eaters',
    'pts': 177.0,
    'week': 6,
    'season': 2026,
    'note': 'with players still to play',
}


def live_2026_average():
    """This season's average team week, from the weeks already fetched."""
    import glob, statistics as st
    sc = []
    for f in glob.glob(os.path.join(ROOT, 'week-data', '2026-w*.json')):
        if not re.search(r'-w\d+\.json$', f):
            continue
        d = json.load(open(f, encoding='utf-8'))
        pts = [t['points'] for g in d['games'] for t in g['teams']]
        # A week only counts once it is PLAYED. Week files are fetched for their
        # rosters while the week is still live, so the scores in them can be
        # near zero -- and letting one in dropped the season average from 96.6
        # to 86.1, which flipped this article's conclusion. The test is the
        # weakest team in the week: nobody finishes a real week under 30.
        if pts and min(pts) >= 30:
            sc += pts
    return st.mean(sc) if sc else None


def crunch():
    h = json.load(open(os.path.join(ROOT, 'history.json'), encoding='utf-8'))
    avg, rows = {}, []
    for s in h['seasons']:
        nm = {t['id']: t['name'] for t in s.get('teams', [])}
        sc = []
        for m in s.get('matchups') or []:
            hs, as_ = m.get('homeScore'), m.get('awayScore')
            if hs is None or as_ is None:
                continue
            sc += [float(hs), float(as_)]
            for a, b, ai, bi in ((hs, as_, m.get('home'), m.get('away')),
                                 (as_, hs, m.get('away'), m.get('home'))):
                rows.append({'pts': float(a), 'year': s['year'], 'week': m['week'],
                             'team': clean(nm.get(ai, '?')), 'opp': clean(nm.get(bi, '?')),
                             'oppPts': float(b), 'playoff': bool(m.get('playoff'))})
        if sc:
            avg[s['year']] = statistics.mean(sc)
    for r in rows:
        r['idx'] = r['pts'] / avg[r['year']]
        r['won'] = r['pts'] > r['oppPts']
    return {'rows': rows, 'avg': avg, 'seasons': len(h['seasons']),
            'span': (min(avg), max(avg))}


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>The Ten Biggest Weeks &mdash; SCFL NewsRoom</title>
<meta name="scfl:kicker" content="The Record Book &middot; October 2026">
<meta name="scfl:published" content="2026-10-12">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SCFL NewsRoom">
<meta property="og:title" content="The Ten Biggest Weeks">
<meta property="og:description" content="__DESC__">
<meta property="og:image" content="https://watsoncapitalinvest-dot.github.io/Claude/scfl-big-weeks-og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="newsroom-favicon.png">
<style>
:root{--cream:#fffdfb;--paper:#faf7f2;--ink:#17181c;--muted:#65656b;--faint:#9a958c;
 --line:#e6e0d6;--red:#c20f16;--blue:#0e8ab5;--gold:#d8b45a;
 --serif:Georgia,'Times New Roman',serif;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;}
body{margin:0;background:var(--cream);color:var(--ink);font-family:var(--serif);font-size:17px;
 line-height:1.62;-webkit-font-smoothing:antialiased;}
.wrap{max-width:860px;margin:0 auto;padding:0 20px 80px;}
.runhead{font-family:var(--sans);font-size:10.5px;font-weight:800;letter-spacing:.22em;
 text-transform:uppercase;color:var(--faint);border-bottom:1px solid var(--line);padding:20px 0 12px;}
.flag{font-family:var(--sans);font-size:10.5px;font-weight:900;letter-spacing:.24em;
 text-transform:uppercase;color:var(--red);margin-top:26px;display:block;}
h1{font-weight:900;font-size:clamp(34px,7vw,54px);line-height:1.02;letter-spacing:-.022em;
 margin:12px 0 0;text-wrap:balance;}
h1 em{font-style:normal;color:var(--red);}
.dek{font-style:italic;color:var(--muted);font-size:18px;margin:14px 0 0;max-width:60ch;}
.byline{font-family:var(--sans);font-size:11.5px;letter-spacing:.06em;color:var(--faint);
 margin-top:16px;text-transform:uppercase;}
.rule{height:3px;background:var(--red);width:70px;margin:22px 0 26px;}
.sect{font-family:var(--sans);font-size:11px;font-weight:900;letter-spacing:.2em;
 text-transform:uppercase;color:var(--red);margin:44px 0 12px;padding-top:14px;
 border-top:1px solid var(--line);}
p.b{margin:0 0 16px;max-width:62ch;}
.stats{display:flex;flex-wrap:wrap;gap:24px 38px;margin:0 0 28px;padding-bottom:22px;
 border-bottom:1px solid var(--line);}
.stat .k{font-family:var(--sans);font-size:9.5px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.stat .v{font-size:30px;font-weight:900;line-height:1.15;font-variant-numeric:tabular-nums;}
.stat .n{font-family:var(--sans);font-size:11px;color:var(--muted);}
.pull{margin:30px 0;padding:0 0 0 20px;border-left:3px solid var(--red);font-size:21px;
 line-height:1.42;font-weight:700;max-width:46ch;letter-spacing:-.01em;}
.more{margin-top:46px;border-top:1px solid var(--line);padding-top:18px;font-family:var(--sans);
 font-size:12.5px;line-height:1.6;color:var(--muted);max-width:74ch;}
.more a{color:var(--red);font-weight:700;}
__FIGCSS__
.ad .rk{font-family:var(--sans);font-weight:900;color:var(--red);width:26px;}
.ad .po{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.1em;
 text-transform:uppercase;color:#fff;background:var(--gold);padding:1px 5px;border-radius:2px;
 margin-left:6px;vertical-align:1px;}
.ad .lost{color:var(--blue);font-weight:800;}
.live{border:2px solid var(--red);border-radius:3px;padding:16px 18px;margin:0 0 28px;
 background:#fdf4f2;}
.live .lk{font-family:var(--sans);font-size:9.5px;font-weight:900;letter-spacing:.2em;
 text-transform:uppercase;color:var(--red);margin-bottom:8px;}
.live p{margin:0 0 10px;font-size:16px;line-height:1.55;max-width:62ch;}
.live p:last-child{margin-bottom:0;}
.live .lf{font-style:italic;color:var(--muted);font-size:15px;}
</style></head>
<body><div class="wrap">
<div class="runhead">SCFL NewsRoom &middot; The Record Book &middot; October 2026</div>
<span class="flag">The Record Book</span>
<h1>The Ten Biggest <em>Weeks</em></h1>
<p class="dek">One hundred and eighty-four points is the number in the book. It is not the
best week anybody has had &mdash; this league scored a quarter less in 2011 than it did in 2018,
and nobody has ever adjusted for it. Here is the list, and then the list that counts.</p>
<div class="byline">The SCFL NewsRoom &middot; The Record Book</div>
<div class="rule"></div>
__BODY__
<div class="more">Built from <code>history.json</code> &mdash; the ESPN import covering
__SEASONS__ seasons, __FROM__ to __TO__ &mdash; by <code>scripts/build_bigweeks.py</code>.
Season average means every team-week played that year, so the index is a score measured against
the league that produced it. Franchise names are shown as the record book has them; this league
renames its worst team every year by rule, so the same franchise appears under more than one name.
</div>
</div></body></html>"""


def figures(C):
    out = []
    S = lambda t: out.append(f'<div class="sect">{t}</div>')
    B = lambda h: out.append(f'<div class="ad">{h}</div>')
    P = lambda h: out.append(h)
    rows, avg = C['rows'], C['avg']
    raw = sorted(rows, key=lambda r: -r['pts'])[:10]
    era = sorted(rows, key=lambda r: -r['idx'])[:10]
    top, best = raw[0], era[0]
    lo_y = min(avg, key=lambda y: avg[y]); hi_y = max(avg, key=lambda y: avg[y])

    P(f'''<div class="stats">
      <div class="stat"><div class="k">The record</div><div class="v">{top['pts']:.0f}</div>
        <div class="n">{E(top['team'])}, {top['year']} week {top['week']}</div></div>
      <div class="stat"><div class="k">Biggest for its era</div>
        <div class="v">{best['idx']:.2f}&times;</div>
        <div class="n">{E(best['team'])}, {best['year']} &mdash; {best['pts']:.0f} in a {avg[best['year']]:.0f}-point league</div></div>
      <div class="stat"><div class="k">Seasons on record</div><div class="v">{C['seasons']}</div>
        <div class="n">{C['span'][0]}&ndash;{C['span'][1]}</div></div>
      <div class="stat"><div class="k">Scoring swing</div>
        <div class="v">{avg[hi_y]/avg[lo_y]:.2f}&times;</div>
        <div class="n">{avg[lo_y]:.1f} a week in {lo_y}, {avg[hi_y]:.1f} in {hi_y}</div></div>
    </div>''')

    if LIVE:
        a26 = live_2026_average()
        gap = top['pts'] - LIVE['pts']
        ix = LIVE['pts'] / a26 if a26 else 0
        tenth = era[-1]['idx']
        need10 = tenth * a26 if a26 else 0
        need1 = best['idx'] * a26 if a26 else 0
        P(f'''<div class="live"><div class="lk">As we go to press</div>
          <p><b>{E(LIVE['team'])}</b> are on <b>{LIVE['pts']:.0f}</b> in week {LIVE['week']}
          {E(LIVE['note'])} &mdash; <b>{gap:.0f} points</b> short of the record on this page.
          They may well take it tonight.</p>
          <p>They will not take the other one. The league is averaging
          <b>{a26:.1f}</b> a week this season, so {LIVE['pts']:.0f} is <b>{ix:.2f}&times;</b> the
          field. Tenth place on the adjusted board is {tenth:.2f}&times;, which in this scoring
          environment is <b>{need10:.0f} points</b>. First place is {best['idx']:.2f}&times; &mdash;
          <b>{need1:.0f}</b>.</p>
          <p class="lf">That is the argument of this piece, happening live: a number can be the
          biggest ever recorded and not be among the ten best weeks anybody has had.</p></div>''')

    P(f'<p class="b">The biggest score anybody has ever put up in this league is '
      f'{top["pts"]:.0f}, by {E(top["team"])} in week {top["week"]} of {top["year"]}, against '
      f'{E(top["opp"])}, who managed {top["oppPts"]:.0f}. That is the record and it is not in '
      f'dispute.</p>')
    P(f'<p class="b">What is in dispute is whether it was the best week anybody has had. The '
      f'average team week in this league was {avg[lo_y]:.1f} points in {lo_y} and {avg[hi_y]:.1f} '
      f'in {hi_y}. Those are different sports. A number put up against the first one is worth '
      f'considerably more than the same number put up against the second, and the record book has '
      f'never said so.</p>')

    S('The List As It Stands')
    mx = raw[0]['pts']
    rr = ''
    for i, r in enumerate(raw, 1):
        po = '<span class="po">playoff</span>' if r['playoff'] else ''
        res = '' if r['won'] else '<span class="lost"> &mdash; and lost</span>'
        rr += (f'<tr><th class="rk">{i}</th><th scope="row">{E(r["team"])}{po}</th>'
               f'<td class="bar"><span style="width:{100*r["pts"]/mx:.1f}%"></span></td>'
               f'<td class="num"><b>{r["pts"]:.1f}</b></td>'
               f'<td class="num dim">{r["year"]} wk {r["week"]}</td>'
               f'<td class="dim">v {E(r["opp"])} ({r["oppPts"]:.0f}){res}</td></tr>')
    B(f'<figure><div class="scroll"><table><thead><tr><th></th><th class="lt">Team</th>'
      f'<th class="lt">Points</th><th></th><th>When</th><th class="lt">Opponent</th></tr></thead>'
      f'<tbody>{rr}</tbody></table></div>'
      f'<figcaption>Every team-week in {C["seasons"]} recorded seasons. '
      f'{sum(1 for r in raw if "MACHINES" in r["team"].upper())} of the ten belong to one '
      f'franchise.</figcaption></figure>')

    S('The List That Counts')
    P('<p class="b">Now the same weeks measured against the league that produced them &mdash; the '
      'score divided by the average team week of that season. The order changes, and so does the '
      'record.</p>')
    mx = era[0]['idx']
    rr = ''
    for i, r in enumerate(era, 1):
        po = '<span class="po">playoff</span>' if r['playoff'] else ''
        rr += (f'<tr><th class="rk">{i}</th><th scope="row">{E(r["team"])}{po}</th>'
               f'<td class="bar"><span style="width:{100*r["idx"]/mx:.1f}%"></span></td>'
               f'<td class="num"><b>{r["idx"]:.2f}&times;</b></td>'
               f'<td class="num dim">{r["pts"]:.1f}</td>'
               f'<td class="num dim">{r["year"]}</td>'
               f'<td class="num dim">league avg {avg[r["year"]]:.1f}</td></tr>')
    B(f'<figure><div class="scroll"><table><thead><tr><th></th><th class="lt">Team</th>'
      f'<th class="lt">Share of that season&rsquo;s average</th><th>Index</th><th>Points</th>'
      f'<th>Year</th><th>Context</th></tr></thead><tbody>{rr}</tbody></table></div>'
      f'<figcaption>{E(best["team"])} scored {best["pts"]:.0f} in a season where the average team '
      f'week was {avg[best["year"]]:.1f}. Nobody has beaten the league by that much before or '
      f'since.</figcaption></figure>')

    P(f'<div class="pull">{E(best["team"])} did not score the most points. They beat their '
      f'league by more than anybody ever has.</div>')

    mach = [r for r in raw if 'MACHINES' in r['team'].upper()]
    if mach:
        # derive the count -- hardcoding it said "Four" while the table said five
        WORD = {2:'Two',3:'Three',4:'Four',5:'Five',6:'Six',7:'Seven'}
        S(f'One Franchise, {WORD.get(len(mach), len(mach))} Entries')
        yrs = ', '.join(str(r['year']) for r in sorted(mach, key=lambda r: r['year']))
        P(f'<p class="b">{len(mach)} of the ten biggest weeks in league history belong to The '
          f'Machines &mdash; {yrs}. No other franchise has more than one. Whatever else the record '
          f'book says about that team, it says they have been capable of an afternoon nobody else '
          f'can reach, across {max(r["year"] for r in mach) - min(r["year"] for r in mach)} years '
          f'and every scoring era this league has had.</p>')

    lost = [r for r in raw if not r['won']]
    if lost:
        l = lost[0]
        S('The Cruellest One')
        P(f'<p class="b">{E(l["team"])} scored {l["pts"]:.1f} in {l["year"]} and lost, because '
          f'{E(l["opp"])} scored {l["oppPts"]:.1f} on the same afternoon. It remains the only week '
          f'in the top ten that did not win a football game.</p>')
    return out


def build():
    C = crunch()
    body = '\n'.join(figures(C))
    raw = sorted(C['rows'], key=lambda r: -r['pts'])[0]
    era = sorted(C['rows'], key=lambda r: -r['idx'])[0]
    desc = (f'{raw["team"]} hold the record at {raw["pts"]:.0f}. Adjusted for an era when the '
            f'league scored a quarter less, the biggest week belongs to {era["team"]}.')
    page = (PAGE.replace('__FIGCSS__', ad.FIG_CSS).replace('__BODY__', body)
                .replace('__DESC__', desc).replace('__SEASONS__', str(C['seasons']))
                .replace('__FROM__', str(C['span'][0])).replace('__TO__', str(C['span'][1])))
    open(OUT, 'w', encoding='utf-8').write(page)
    print(f'wrote {os.path.basename(OUT)} ({len(page):,} chars)')
    print(f'  record {raw["pts"]:.0f} {raw["team"]} {raw["year"]} | era-adjusted '
          f'{era["idx"]:.2f}x {era["team"]} {era["year"]}')


if __name__ == '__main__':
    build()
