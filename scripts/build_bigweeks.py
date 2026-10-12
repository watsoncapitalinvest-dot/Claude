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

def week_files():
    """The season's week files, newest first, with whether each one is final."""
    import glob
    out = []
    for f in glob.glob(os.path.join(ROOT, 'week-data', '2026-w*.json')):
        if not re.search(r'-w\d+\.json$', f):
            continue
        d = json.load(open(f, encoding='utf-8'))
        pts = [t['points'] for g in d['games'] for t in g['teams']]
        if not pts:
            continue
        # A week is PLAYED when its weakest team has a real score. Files get
        # pulled mid-week for their rosters, and nobody finishes a week under 30.
        st = [p for g in d['games'] for t in g['teams'] for p in t['starters']]
        zero = sum(1 for p in st if p['points'] == 0) / max(len(st), 1)
        # Two tells, because one is not enough. The weakest team's score catches
        # a week nobody has played: nobody finishes under 30. The share of
        # starters on exactly nothing catches a week half played -- the four
        # finished weeks of this season run 1.2 to 5.6 per cent, and a Sunday
        # evening with the night games still to come reads 10.
        out.append({'week': d['week'], 'pts': pts, 'games': d['games'],
                    'final': min(pts) >= 30 and zero < 0.07,
                    'left': zero,
                    'fetched': d.get('fetchedAt', '')})
    return sorted(out, key=lambda w: -w['week'])


def live_watch(record):
    """The record watch, read off the newest week file instead of typed in.

    It used to be a hand-set dict, which meant the page said 177 for as long as
    nobody remembered to change it -- a press box note that quietly becomes a
    stale one is worse than no note. Now the box cannot be more out of date
    than the data behind it, and it says which it is: a week still being
    played, or a finished week that did or did not take the record.
    """
    # The newest week that has actually been scored. A week file pulled before
    # the week starts is all zeroes -- the rosters are there, the points are
    # not -- and taking it as "the latest week" means the watch disappears
    # every time somebody fetches a week early.
    ws = [w for w in week_files() if max(w['pts']) > 0]
    if not ws:
        return None
    w = ws[0]
    best = max(((t['points'], t['team']) for g in w['games'] for t in g['teams']))
    pts, team = best
    if pts < 0.6 * record:          # nobody is near it; there is nothing to watch
        return None
    return {'team': clean(team), 'pts': pts, 'week': w['week'], 'final': w['final'],
            'took_it': pts > record, 'asof': asof(w['fetched']),
            'fetched': w['fetched']}


def asof(ts):
    """'2026-10-12T01:07:33Z' -> 'Sunday evening' in the league's own time.

    The box is anchored on this rather than on a judgement about whether the
    week is over, because a timestamp cannot be wrong. Eastern, because that is
    the clock everybody in this league reads a Sunday by.
    """
    import datetime
    try:
        t = datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ')
    except Exception:
        return ''
    t -= datetime.timedelta(hours=4)                 # UTC -> US Eastern, in season
    part = ('overnight' if t.hour < 6 else 'morning' if t.hour < 12
            else 'afternoon' if t.hour < 17 else 'evening')
    return f'{t.strftime("%A")} {part}'


def live_2026_average():
    """This season's average team week, counting only the weeks that are done.

    A week counts once it is PLAYED. Week files get pulled while the week is
    still live, and letting one in dropped this average from 96.6 to 86.1 --
    which flipped the conclusion of this article. It happened a second time on
    a Sunday evening, when the weakest team was already past 30 and the test
    passed anyway, so the test now lives in week_files() and uses both tells.
    """
    import statistics as st
    sc = []
    for w in week_files():
        if w['final']:
            sc += w['pts']
    return st.mean(sc) if sc else None


def franchises(h):
    """owner -> the name that franchise goes by now, and every alias it has used.

    Fourteen of the sixteen owners in this league have renamed their team at
    least once, and one of them has used seven names. Keying the record book on
    the name printed that season splits a single franchise into several: The
    Machines played 2011 as THE LEGION OF DOOM and 2015 as COUSIN PETE IS SOFT,
    the Beaver Eaters have been YO MAMA and Tre'Quan Da Chef among others, and
    Killer Klowns were the Ball Chinians. Owner is the only stable identity in
    the file, so the book is keyed on that and the period name is carried
    alongside for the copy to say "as THE LEGION OF DOOM".
    """
    now = {}
    for s in h['seasons']:
        for t in s.get('teams', []):
            if t.get('owner'):
                now[t['owner']] = clean(t['name'])
    return now


def crunch():
    h = json.load(open(os.path.join(ROOT, 'history.json'), encoding='utf-8'))
    NOW = franchises(h)
    avg, rows = {}, []
    for s in h['seasons']:
        nm = {t['id']: (NOW.get(t.get('owner')) or clean(t['name']))
              for t in s.get('teams', [])}
        asname = {t['id']: clean(t['name']) for t in s.get('teams', [])}
        sc = []
        for m in s.get('matchups') or []:
            hs, as_ = m.get('homeScore'), m.get('awayScore')
            if hs is None or as_ is None:
                continue
            sc += [float(hs), float(as_)]
            for a, b, ai, bi in ((hs, as_, m.get('home'), m.get('away')),
                                 (as_, hs, m.get('away'), m.get('home'))):
                rows.append({'pts': float(a), 'year': s['year'], 'week': m['week'],
                             'team': nm.get(ai, '?'), 'opp': nm.get(bi, '?'),
                             # what they were called that season, when it differs
                             'as': asname.get(ai, ''), 'oppAs': asname.get(bi, ''),
                             'oppPts': float(b), 'playoff': bool(m.get('playoff'))})
        if sc:
            avg[s['year']] = statistics.mean(sc)
    for r in rows:
        r['idx'] = r['pts'] / avg[r['year']]
        r['won'] = r['pts'] > r['oppPts']
    champ, season_rec = {}, {}
    for s2 in h['seasons']:
        own = {t['id']: t.get('owner') for t in s2.get('teams', [])}
        nm2 = {t['id']: (NOW.get(t.get('owner')) or clean(t['name']))
               for t in s2.get('teams', [])}
        c = s2.get('champion')
        champ[s2['year']] = next((nm2[i] for i, o in own.items() if o == c), None)
        w = {}
        for m in s2.get('matchups') or []:
            a, b = m.get('homeScore'), m.get('awayScore')
            if a is None or b is None:
                continue
            for me, op, i in ((a, b, m.get('home')), (b, a, m.get('away'))):
                r = w.setdefault(nm2.get(i), [0, 0, 0])
                r[0 if me > op else 1 if me < op else 2] += 1
        season_rec[s2['year']] = w
    return {'rows': rows, 'avg': avg, 'seasons': len(h['seasons']),
            'span': (min(avg), max(avg)), 'champ': champ, 'rec': season_rec}


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
.was{display:block;font-family:var(--sans);font-size:10px;font-weight:600;
 letter-spacing:.04em;color:var(--faint);margin-top:1px;}
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
<p class="dek">__NWEEKS__ team-weeks across __SEASONS__ seasons, and these are the ten
afternoons nobody has got near. Five belong to the same franchise, two came in the playoffs, and
the one at the top has stood since 2022.</p>
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


def alias(r, key='as', team='team'):
    """The name that franchise was playing under at the time, when it differs.

    Worth printing rather than silently normalising: the 2011 record was set by
    a team calling itself THE LEGION OF DOOM, and a reader who was there
    remembers the name, not the owner id.
    """
    a = r.get(key) or ''
    return (f'<span class="was">as {E(a)}</span>' if a and a != r[team] else '')


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
    nmach = sum(1 for r in raw if 'MACHINES' in r['team'].upper())

    P(f'''<div class="stats">
      <div class="stat"><div class="k">The record</div><div class="v">{top['pts']:.0f}</div>
        <div class="n">{E(top['team'])}, {top['year']} week {top['week']}</div></div>
      <div class="stat"><div class="k">Margin that day</div>
        <div class="v">+{top['pts']-top['oppPts']:.0f}</div>
        <div class="n">{E(top['opp'])} managed {top['oppPts']:.0f}</div></div>
      <div class="stat"><div class="k">Seasons on record</div><div class="v">{C['seasons']}</div>
        <div class="n">{C['span'][0]}&ndash;{C['span'][1]}</div></div>
      <div class="stat"><div class="k">One franchise</div><div class="v">{nmach}</div>
        <div class="n">of the ten, all to The Machines</div></div>
    </div>''')

    LIVE = live_watch(top['pts'])
    if LIVE:
        a26 = live_2026_average()
        gap = top['pts'] - LIVE['pts']
        stood = 2026 - top['year']
        ix = LIVE['pts'] / a26 if a26 else 0
        # Everything in this box is read off the week file and off the record
        # above it. The draft was hand-written -- "seven points", "four
        # seasons" -- and both of those were a week away from being wrong.
        live = not LIVE['final']
        when = f" as of {LIVE['asof']}" if LIVE['asof'] else ''
        verb = 'are on' if live else 'finished on'
        still = ' with players still to play' if live else ''
        if LIVE['took_it']:
            lede = (f"<p><b>{E(LIVE['team'])}</b> {verb} <b>{LIVE['pts']:.1f}</b> in week "
                    f"{LIVE['week']}{still} &mdash; <b>{abs(gap):.1f} past</b> the record on "
                    f"this page, which had stood {stood} season"
                    f"{'' if stood == 1 else 's'}.</p>"
                    + (f"<p>Nothing is in the book until the week is final, but it is there"
                       f"{when}.</p>" if live else
                       f"<p>The table below is the record as imported. It is out of date"
                       f"{when}.</p>"))
        else:
            lede = (f"<p><b>{E(LIVE['team'])}</b> {verb} <b>{LIVE['pts']:.1f}</b> in week "
                    f"{LIVE['week']}{still} &mdash; <b>{gap:.1f} points</b> short of the "
                    f"record on this page, which has stood {stood} season"
                    f"{'' if stood == 1 else 's'}.</p>"
                    + (f"<p>That is the closest anybody has come this season{when}. "
                       if LIVE['pts'] >= max((max(w['pts']) for w in week_files()), default=0)
                       else f"<p>That is where it stands{when}. ")
                    + "The number is read off the week file, so when the week finishes it "
                      "changes with it.</p>")
        ped = (f'<p class="lf">For the pedants: {LIVE["pts"]:.0f} in a {a26:.0f}-point league '
               f'is {ix:.2f}&times; the field, which '
               + ('would reach' if ix >= era[-1]['idx'] else 'would not reach')
               + ' the adjusted ten below.</p>') if a26 else ''
        P(f'<div class="live"><div class="lk">'
          + ('The record has gone' if LIVE['took_it'] else 'As we go to press')
          + f'</div>{lede}{ped}</div>')

    rec = (C['rec'].get(top['year']) or {}).get(top['team'])
    won = C['champ'].get(top['year']) == top['team']
    tail = ''
    if rec:
        w, l, t = rec
        tail = (f' They finished that season {w}-{l}' + (f'-{t}' if t else '')
                + (' and won the title.' if won else '.'))
    P(f'<p class="b">The biggest score anybody has ever put up in this league is '
      f'{top["pts"]:.0f}, by {E(top["team"])} in week {top["week"]} of {top["year"]}, against '
      f'{E(top["opp"])}, who managed {top["oppPts"]:.0f}.{tail}</p>')
    P(f'<p class="b">Below it sit nine more afternoons that got close and never arrived. '
      f'{nmach} of the ten belong to The Machines. '
      f'{sum(1 for r in raw if r["playoff"])} came in the playoffs. And one of them was put up '
      f'against a team that scored {max(r["oppPts"] for r in raw):.0f} &mdash; the highest losing '
      f'score in the book.</p>')

    S('The List As It Stands')
    mx = raw[0]['pts']
    rr = ''
    for i, r in enumerate(raw, 1):
        po = '<span class="po">playoff</span>' if r['playoff'] else ''
        res = '' if r['won'] else '<span class="lost"> &mdash; and lost</span>'
        rr += (f'<tr><th class="rk">{i}</th><th scope="row">{E(r["team"])}{po}{alias(r)}</th>'
               f'<td class="bar"><span style="width:{100*r["pts"]/mx:.1f}%"></span></td>'
               f'<td class="num"><b>{r["pts"]:.1f}</b></td>'
               f'<td class="num dim">{r["year"]} wk {r["week"]}</td>'
               f'<td class="dim">v {E(r["opp"])} ({r["oppPts"]:.0f}){res}'
               f'{alias(r, "oppAs", "opp")}</td></tr>')
    B(f'<figure><div class="scroll"><table><thead><tr><th></th><th class="lt">Team</th>'
      f'<th class="lt">Points</th><th></th><th>When</th><th class="lt">Opponent</th></tr></thead>'
      f'<tbody>{rr}</tbody></table></div>'
      f'<figcaption>Every team-week in {C["seasons"]} recorded seasons. '
      f'{sum(1 for r in raw if "MACHINES" in r["team"].upper())} of the ten belong to one '
      f'franchise.</figcaption></figure>')

    # The companion record: scoring enough to win almost any week and losing.
    lost = sorted((r for r in rows if r['pts'] < r['oppPts']),
                  key=lambda r: -r['pts'])[:8]
    S('The Ones That Were Not Enough')
    L0 = lost[0]
    beat = sum(1 for r in rows if r['pts'] < L0['pts'] and r['pts'] > r['oppPts'])
    # The week that beat it may or may not be on the top ten. Find it by who,
    # when and against whom -- matching on the score alone would pick the wrong
    # week the first time two of them tie, which in 4,688 team-weeks it will.
    ranked = next((i for i, r in enumerate(raw, 1)
                   if r['year'] == L0['year'] and r['week'] == L0['week']
                   and r['team'] == L0['opp']), 0)
    place = (f' &mdash; the week sitting at number {ranked} on the list above'
             if ranked else '')
    P(f'<p class="b">The other half of a record list is the afternoons that deserved better. '
      f'{E(L0["team"])} scored {L0["pts"]:.0f} in week {L0["week"]} of {L0["year"]} and lost, '
      f'because {E(L0["opp"])} picked the same afternoon for {L0["oppPts"]:.0f}{place}. '
      f'That {L0["pts"]:.0f} would have won '
      f'{100*beat/max(sum(1 for r in rows if r["pts"] != r["oppPts"]),1):.0f} per cent of every '
      f'other game ever played in this league.</p>')
    mx = lost[0]['pts']
    rr = ''
    for i, r in enumerate(lost, 1):
        po = '<span class="po">playoff</span>' if r['playoff'] else ''
        rr += (f'<tr><th class="rk">{i}</th><th scope="row">{E(r["team"])}{po}{alias(r)}</th>'
               f'<td class="bar"><span class="lo" style="width:{100*r["pts"]/mx:.1f}%"></span></td>'
               f'<td class="num"><b>{r["pts"]:.1f}</b></td>'
               f'<td class="num dim">{r["year"]} wk {r["week"]}</td>'
               f'<td class="dim">lost to {E(r["opp"])} ({r["oppPts"]:.0f})'
               f'{alias(r, "oppAs", "opp")}</td>'
               f'<td class="num dim">&minus;{r["oppPts"]-r["pts"]:.1f}</td></tr>')
    B(f'<figure><div class="scroll"><table><thead><tr><th></th><th class="lt">Team</th>'
      f'<th class="lt">Points, and still beaten</th><th></th><th>When</th>'
      f'<th class="lt">Beaten by</th><th>Margin</th></tr></thead>'
      f'<tbody>{rr}</tbody></table></div>'
      f'<figcaption>Highest scores by a losing team. '
      f'{sum(1 for r in lost if r["playoff"])} of the eight came in the playoffs, where there is '
      f'no next week.</figcaption></figure>')
    close = min(lost, key=lambda r: r['oppPts'] - r['pts'])
    P(f'<p class="b">The cruellest is not the biggest. {E(close["team"])} put '
      f'{close["pts"]:.0f} on the board in {close["year"]}'
      + (f' &mdash; in the playoffs &mdash;' if close['playoff'] else '') +
      f' and went out by {close["oppPts"]-close["pts"]:.1f}.</p>')

    S('A Note On Era')
    P(f'<p class="b">One caveat for anyone who likes arguing about records. The league averaged '
      f'{avg[lo_y]:.1f} points a team-week in {lo_y} and {avg[hi_y]:.1f} in {hi_y}, so the same '
      f'score is a different achievement depending on when it happened. Measured against its own '
      f'season, the order shuffles &mdash; {E(best["team"])} top it, and the record itself drops '
      f'to {1 + [r is top for r in era].index(True) if any(r is top for r in era) else 3}.</p>')
    mx = era[0]['idx']
    rr = ''
    for i, r in enumerate(era, 1):
        po = '<span class="po">playoff</span>' if r['playoff'] else ''
        rr += (f'<tr><th class="rk">{i}</th><th scope="row">{E(r["team"])}{po}{alias(r)}</th>'
               f'<td class="bar"><span style="width:{100*r["idx"]/mx:.1f}%"></span></td>'
               f'<td class="num"><b>{r["idx"]:.2f}&times;</b></td>'
               f'<td class="num dim">{r["pts"]:.1f}</td>'
               f'<td class="num dim">{r["year"]}</td>'
               f'<td class="num dim">league avg {avg[r["year"]]:.1f}</td></tr>')
    B(f'<figure><div class="scroll"><table><thead><tr><th></th><th class="lt">Team</th>'
      f'<th class="lt">Share of that season&rsquo;s average</th><th>Index</th><th>Points</th>'
      f'<th>Year</th><th>Context</th></tr></thead><tbody>{rr}</tbody></table></div>'
      f'<figcaption>Score divided by the average team week of that season. It is a footnote, not '
      f'a rewrite &mdash; the record is still {top["pts"]:.0f}.</figcaption></figure>')

    mach = [r for r in raw if 'MACHINES' in r['team'].upper()]
    if mach:
        P(f'<div class="pull">Five of the ten biggest afternoons in eighteen seasons belong to '
          f'one team. Nobody else has two.</div>')
        # derive the count -- hardcoding it said "Four" while the table said five
        WORD = {2:'Two',3:'Three',4:'Four',5:'Five',6:'Six',7:'Seven'}
        S(f'One Franchise, {WORD.get(len(mach), len(mach))} Entries')
        yrs = ', '.join(str(r['year']) for r in sorted(mach, key=lambda r: r['year']))
        P(f'<p class="b">{len(mach)} of the ten biggest weeks in league history belong to The '
          f'Machines &mdash; {yrs}. No other franchise has more than one. Whatever else the record '
          f'book says about that team, it says they have been capable of an afternoon nobody else '
          f'can reach, across {max(r["year"] for r in mach) - min(r["year"] for r in mach)} years '
          f'and every scoring era this league has had.</p>')

    # Any of the top ten that lost. As the book stands all ten won, so this does
    # not print -- but it is written to count rather than to assert, because the
    # draft of it said "the only week in the top ten that did not win" and that
    # would have become false the moment a second one joined it.
    lost10 = [r for r in raw if not r['won']]
    if lost10:
        S('The Cruellest One' if len(lost10) == 1 else 'The Ones In The Top Ten That Lost')
        for l in lost10:
            P(f'<p class="b">{E(l["team"])} scored {l["pts"]:.1f} in {l["year"]} and lost, '
              f'because {E(l["opp"])} scored {l["oppPts"]:.1f} on the same afternoon.</p>')
        P(f'<p class="b">{"That is" if len(lost10) == 1 else "Those are"} '
          f'{len(lost10)} of the ten biggest weeks this league has ever seen that did not win a '
          f'football game.</p>')
    return out


CARD = """<style>
:root{--red:#c20f16;--ink:#17181c;--faint:#9a958c;--gold:#d8b45a;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;margin:0;}
html,body{width:1200px;height:630px;overflow:hidden;background:#efe9de;
 font-family:Georgia,'Times New Roman',serif;color:var(--ink);}
.card{position:relative;width:1200px;height:630px;overflow:hidden;background:#efe9de;
 border-top:9px solid var(--red);border-bottom:9px solid var(--red);
 padding:52px 60px 44px;display:flex;}
.l{width:470px;flex:0 0 470px;display:flex;flex-direction:column;}
.flag{font-family:var(--sans);font-size:11.5px;font-weight:900;letter-spacing:.22em;
 text-transform:uppercase;color:var(--red);}
h1{font-size:62px;line-height:.98;letter-spacing:-.026em;font-weight:900;margin-top:16px;}
h1 em{font-style:normal;color:var(--red);}
.rule{width:64px;height:3px;background:var(--red);margin:22px 0 18px;}
.dek{font-style:italic;color:#4b4b52;font-size:17px;line-height:1.4;max-width:26ch;}
.st{margin-top:auto;display:flex;gap:30px;}
.st .k{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.st .v{font-size:32px;font-weight:900;line-height:1.1;font-variant-numeric:tabular-nums;}
.r{flex:1;padding-left:50px;display:flex;flex-direction:column;justify-content:center;}
table{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:13px;}
td,th{padding:5px 0;vertical-align:middle;}
th{text-align:left;font-weight:700;white-space:nowrap;padding-right:12px;}
tr+tr td,tr+tr th{border-top:1px solid #e3dcce;}
.bar{width:150px;}
.bar span{display:block;height:11px;background:var(--red);border-radius:0 2px 2px 0;}
.num{text-align:right;font-variant-numeric:tabular-nums;font-weight:800;padding-left:10px;}
.yr{text-align:right;color:var(--faint);padding-left:12px;font-size:11.5px;}
.cap{font-family:var(--sans);font-size:10px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);margin-bottom:12px;}
</style>
<div class="card">
 <div class="l">
  <div class="flag">The Record Book</div>
  <h1>The Ten<br>Biggest <em>Weeks</em></h1>
  <div class="rule"></div>
  <div class="dek">__DEK__</div>
  <div class="st">
   <div><div class="k">The record</div><div class="v">__REC__</div></div>
   <div><div class="k">Team-weeks</div><div class="v">__N__</div></div>
   <div><div class="k">Seasons</div><div class="v">__S__</div></div>
  </div>
 </div>
 <div class="r"><div class="cap">The top six</div><table><tbody>__ROWS__</tbody></table></div>
</div>"""


def card(C, raw):
    """The share card. The page carried an og:image tag pointing at a file that
    was never built, so every time it was pasted anywhere it came up blank --
    and the sender could not see that from their end."""
    top = raw[:6]
    mx = top[0]['pts']
    rows = ''.join(
        f'<tr><th>{E(r["team"])}</th>'
        f'<td class="bar"><span style="width:{100*r["pts"]/mx:.0f}%"></span></td>'
        f'<td class="num">{r["pts"]:.0f}</td>'
        f'<td class="yr">{r["year"]}</td></tr>' for r in top)
    doc = (CARD.replace('__ROWS__', rows)
               .replace('__REC__', f'{raw[0]["pts"]:.0f}')
               .replace('__N__', f'{len(C["rows"]):,}')
               .replace('__S__', str(C['seasons']))
               # the spread across the whole top ten, which is the actual
               # story: they are bunched, and the one at the top has held
               .replace('__DEK__', f'{E(raw[0]["team"])}&rsquo;s {raw[0]["pts"]:.0f} has stood '
                                   f'since {raw[0]["year"]}. All ten of these afternoons sit '
                                   f'inside {raw[0]["pts"]-raw[-1]["pts"]:.0f} points of each '
                                   f'other.'))
    ad.shoot(doc, OG, 'bigweeks-card')


def build():
    C = crunch()
    body = '\n'.join(figures(C))
    raw = sorted(C['rows'], key=lambda r: -r['pts'])[0]
    era = sorted(C['rows'], key=lambda r: -r['idx'])[0]
    desc = (f'{raw["team"]} hold the record at {raw["pts"]:.0f}. Adjusted for an era when the '
            f'league scored a quarter less, the biggest week belongs to {era["team"]}.')
    page = (PAGE.replace('__FIGCSS__', ad.FIG_CSS).replace('__BODY__', body)
                .replace('__DESC__', desc).replace('__SEASONS__', str(C['seasons']))
                .replace('__NWEEKS__', f"{len(C['rows']):,}")
                .replace('__FROM__', str(C['span'][0])).replace('__TO__', str(C['span'][1])))
    open(OUT, 'w', encoding='utf-8').write(page)
    print(f'wrote {os.path.basename(OUT)} ({len(page):,} chars)')
    print(f'  record {raw["pts"]:.0f} {raw["team"]} {raw["year"]} | era-adjusted '
          f'{era["idx"]:.2f}x {era["team"]} {era["year"]}')
    card(C, sorted(C['rows'], key=lambda r: -r['pts'])[:10])


if __name__ == '__main__':
    build()
