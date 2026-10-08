#!/usr/bin/env python3
"""Write the week's game stories from the replay, and lay them out as an issue.

    python3 scripts/write_week.py --week 4

Reads week-data/{season}-w{week}-replay.json and writes scfl-week-{n}.html:
eight game reports plus a scoreboard, in the house style.

The voice is a magazine game report -- the paper, or ESPN the Magazine. Not the
group chat. Every factual clause is pulled from the replay, so a sentence can
be argued with as writing but cannot be wrong about what happened: the yardage
is the real yardage, the order is the real order, and "to put them ahead" is
only ever written when the running score actually flipped on that play.

Residual events are invisible here by construction. They are real points that
no single play explains -- a team defence, mostly -- and the writer is never
handed one, so it cannot describe a thing that did not occur.
"""
import argparse, importlib.util, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')
_s = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts', 'build_addendum.py'))
ad = importlib.util.module_from_spec(_s); sys.modules['ad'] = ad; _s.loader.exec_module(ad)
E = ad.esc

TEAM = lambda s: (s or '').strip().strip('*').strip()
ORD = {1: 'first', 2: 'second', 3: 'third', 4: 'fourth'}


def late(e):
    """Is this play late in the game, in the way a reader means it?"""
    return e['fc']['qtr'] == 4 and int(e['fc']['clock'].split(':')[0]) <= 7


def when(e, windows):
    """A human phrase for when a play happened, in both clocks at once."""
    q = ORD[e['fc']['qtr']]
    w = windows.get(e['window'], '')
    return f"{q} quarter", w


def play(e):
    """The play as prose. replay.py stores bare yardage phrases, which need an
    article in front of them before they can sit inside a sentence."""
    t = e['text'] or e['kind']
    return t if t[:1].isalpha() else ('an ' if t[:1] == '8' else 'a ') + t


def scoreline(e, side):
    """The running score written from one side's point of view, leading side
    first. Printing the raw pair put the trailing team's number first and made
    'put them ahead at 34.62-37.26' read as a contradiction."""
    mine, theirs = e['score'][side], e['score'][1 - side]
    hi, lo = (mine, theirs) if mine >= theirs else (theirs, mine)
    return f'{hi}\u2013{lo}'


def tally(tl, side):
    t = {}
    for e in tl:
        if e['side'] == side and not e['residual']:
            t[e['player']] = t.get(e['player'], 0) + e['pts']
    return sorted(t.items(), key=lambda x: -x[1])


def arc_of(g, tl):
    m = g['margin']
    if m >= 40: return 'rout'
    if m >= 25: return 'comfortable'
    if g['lead_changes'] >= 6: return 'seesaw'
    if m <= 10: return 'tight'
    return 'steady'


def story(g, gw, windows):
    """One game report. Returns dict(headline, dek, paragraphs)."""
    tl = [e for e in g['timeline'] if not e['residual']]
    A, B = g['teams']
    an, bn = TEAM(A['team']), TEAM(B['team'])
    wi = 0 if A['final'] >= B['final'] else 1
    W, L = (A, B) if wi == 0 else (B, A)
    wn, ln = (an, bn) if wi == 0 else (bn, an)
    arc = arc_of(g, tl)
    go = g.get('go_ahead')
    if go and go['residual']:
        go = None
    big = max(tl, key=lambda e: e['pts']) if tl else None
    wtop, ltop = tally(tl, wi), tally(tl, 1 - wi)
    P = []

    # ---- headline -----------------------------------------------------------
    if arc == 'rout':
        hl = f'{wn} Leave No Doubt'
    elif arc == 'seesaw':
        hl = f'{wn} Win the Last Exchange'
    elif arc == 'tight':
        hl = f'{wn} Edge {ln}'
    elif go and late(go):
        hl = f'{wn} Finish Late'
    else:
        hl = f'{wn} Hold Off {ln}'
    if go and late(go) and go['td'] and arc in ('tight', 'seesaw'):
        hl = f"{go['player'].split()[-1]} Wins It Late for {wn}"

    # ---- dek ----------------------------------------------------------------
    if arc == 'rout':
        dek = f'{wn} {W["final"]}, {ln} {L["final"]} — and it was over long before it ended.'
    elif g['lead_changes'] >= 6:
        dek = (f'{g["lead_changes"]} lead changes, and {wn} had the ball last. '
               f'Final: {W["final"]}–{L["final"]}.')
    else:
        dek = f'Final: {wn} {W["final"]}, {ln} {L["final"]}.'

    # ---- P1: the result -----------------------------------------------------
    if arc == 'rout':
        P.append(f'{wn} beat {ln} {W["final"]} to {L["final"]}, a {g["margin"]:.1f}-point win that '
                 f'never really asked a question. '
                 + (f'{ln} did not lead at any point.' if g['lead_changes'] == 0
                    else (f'{ln} led, and lost it for good in the '
                          f'{ORD[go["fc"]["qtr"]]}.' if go else
                          f'{ln} led early and could not hold it.')))
    elif arc == 'seesaw':
        P.append(f'{wn} and {ln} traded the lead {g["lead_changes"]} times before {wn} '
                 f'settled it, {W["final"]} to {L["final"]}.')
    elif arc == 'tight':
        P.append(f'{wn} got past {ln} {W["final"]} to {L["final"]}, a margin of '
                 f'{g["margin"]:.1f} points in a game that was live to the end.')
    else:
        P.append(f'{wn} handled {ln} {W["final"]} to {L["final"]}.')

    # ---- P2: the play that decided it --------------------------------------
    if go:
        q, w = when(go, windows)
        who = go['player']
        took = (f'put {TEAM(g["teams"][go["side"]]["team"])} ahead'
                if go['side'] == wi else 'handed the lead back')
        if go['kind'] in ('int', 'fum'):
            P.append(f'The game turned on a mistake. {who} threw {go["text"]} in the {q} — '
                     f'{w} — and the lead changed hands at {go["score"][0]}–{go["score"][1]}. '
                     f'{ln} did not lead again.' if go['side'] != wi else
                     f'{who} threw {play(go)} in the {q}, {w}, and the lead changed hands.')
        else:
            P.append(f'The decisive play came in the {q}, {w}: {who} with {play(go)}, which '
                     f'{took} at {scoreline(go, go["side"])}.'
                     + (' Nobody took it back.' if go['side'] == wi else ''))
    elif g['lead_changes'] == 0:
        P.append(f'{wn} led from the first score and the margin only grew.')

    # ---- P3: the biggest single play ---------------------------------------
    if big and (not go or big is not go) and big['pts'] >= 7:
        q, w = when(big, windows)
        side = TEAM(g['teams'][big['side']]['team'])
        P.append(f'The biggest single play of the week belonged to {big["player"]}: '
                 f'{play(big)} in the {q}, {w}, worth {big["pts"]:.1f} to {side}.')

    # ---- P4: who carried it -------------------------------------------------
    if wtop:
        lead_line = ', '.join(f'{n} ({v:.1f})' for n, v in wtop[:3])
        P.append(f'{wn} got there on {lead_line}.'
                 + (f' {ltop[0][0]} led {ln} with {ltop[0][1]:.1f}, which was not close to enough.'
                    if ltop and arc in ('rout', 'comfortable') else
                    f' {ltop[0][0]} answered with {ltop[0][1]:.1f} for {ln}.' if ltop else ''))

    # ---- P5: the bench ------------------------------------------------------
    for t in gw['teams']:
        bench = [p for p in t['bench'] if (p.get('points') or 0) > 0]
        starters = [p for p in t['starters'] if p['pos'] not in ('K', 'DEF')]
        if not bench or not starters:
            continue
        bb = max(bench, key=lambda p: p['points'])
        ws = min(starters, key=lambda p: p['points'])
        gap = bb['points'] - ws['points']
        if gap >= 12:
            nm = TEAM(t['team'])
            verdict = ('would have changed the result' if gap > g['margin']
                       else 'would not have changed the result')
            P.append(f'{nm} left {bb["name"]} and his {bb["points"]:.1f} points on the bench while '
                     f'{ws["name"]} started and returned {ws["points"]:.1f}. The '
                     f'{gap:.1f}-point difference {verdict}.')
            break

    return {'headline': hl, 'dek': dek, 'paragraphs': P,
            'winner': wn, 'loser': ln, 'score': [W['final'], L['final']],
            'margin': g['margin'], 'arc': arc}


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Week __WK__ — SCFL NewsRoom</title>
<meta name="scfl:kicker" content="The Weekly Issue &middot; Week __WK__">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SCFL NewsRoom">
<meta property="og:title" content="SCFL Week __WK__">
<meta property="og:description" content="__DESC__">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="newsroom-favicon.png">
<style>
:root{--cream:#fffdfb;--paper:#faf7f2;--ink:#17181c;--muted:#65656b;--faint:#9a958c;
 --line:#e6e0d6;--red:#c20f16;--blue:#0e8ab5;
 --serif:Georgia,'Times New Roman',serif;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;}
body{margin:0;background:var(--cream);color:var(--ink);font-family:var(--serif);font-size:17px;
 line-height:1.62;-webkit-font-smoothing:antialiased;}
.wrap{max-width:860px;margin:0 auto;padding:0 20px 80px;}
.runhead{font-family:var(--sans);font-size:10.5px;font-weight:800;letter-spacing:.22em;
 text-transform:uppercase;color:var(--faint);border-bottom:1px solid var(--line);padding:20px 0 12px;}
.mast{font-weight:900;font-size:clamp(40px,9vw,76px);line-height:.94;letter-spacing:-.03em;
 margin:18px 0 0;}
.mast em{font-style:normal;color:var(--red);}
.tag{font-family:var(--sans);font-size:11.5px;font-weight:800;letter-spacing:.2em;
 text-transform:uppercase;color:var(--muted);margin-top:12px;}
.rule{height:3px;background:var(--red);width:84px;margin:20px 0 30px;}
.sect{font-family:var(--sans);font-size:11px;font-weight:900;letter-spacing:.2em;
 text-transform:uppercase;color:var(--red);margin:46px 0 14px;padding-top:14px;
 border-top:1px solid var(--line);}
article{margin:0 0 42px;padding-bottom:30px;border-bottom:1px solid var(--line);}
article:last-of-type{border-bottom:0;}
h2{font-weight:900;font-size:clamp(25px,4.4vw,34px);line-height:1.06;letter-spacing:-.018em;
 margin:0 0 8px;text-wrap:balance;}
.score{font-family:var(--sans);font-size:11.5px;font-weight:800;letter-spacing:.07em;
 text-transform:uppercase;color:var(--faint);margin-bottom:10px;}
.dek{font-style:italic;color:var(--muted);font-size:17.5px;margin:0 0 16px;max-width:58ch;}
p.b{margin:0 0 15px;max-width:63ch;}
.board{width:100%;border-collapse:collapse;font-family:var(--sans);font-size:13.5px;}
.board td,.board th{padding:7px 8px;border-bottom:1px solid var(--line);}
.board .w{font-weight:800;}
.board .n{text-align:right;font-variant-numeric:tabular-nums;}
.board .m{text-align:right;font-variant-numeric:tabular-nums;color:var(--faint);}
.more{margin-top:44px;border-top:1px solid var(--line);padding-top:18px;font-family:var(--sans);
 font-size:12.5px;line-height:1.6;color:var(--muted);max-width:74ch;}
.more a{color:var(--red);font-weight:700;}
</style></head>
<body><div class="wrap">
<div class="runhead">SCFL NewsRoom &middot; The Weekly Issue &middot; Week __WK__, __SEASON__</div>
<div class="mast">Week <em>__WK__</em></div>
<div class="tag">Eight games, replayed from the tape</div>
<div class="rule"></div>
__LEAD__
<div class="sect">The Scoreboard</div>
<table class="board"><tbody>__BOARD__</tbody></table>
<div class="sect">The Games</div>
__BODY__
<div class="more">Every game on this page was rebuilt from real plays. Each scoring play in a
manager&rsquo;s week &mdash; the yardage, the touchdown, the order it happened in &mdash; is laid
onto sixty minutes by the window its NFL game sat in, so Thursday night opens the first quarter
and Monday night closes the fourth. Nothing is invented; only the clock is. Points that no single
play explains, almost all of them team defences, are carried in the totals but never described.
Built by <code>scripts/replay.py</code> and <code>scripts/write_week.py</code> from
<code>nflverse</code> play-by-play and the league&rsquo;s own week data.</div>
</div></body></html>"""


def build(season, week):
    rp = json.load(open(os.path.join(WDIR, f'{season}-w{week}-replay.json'), encoding='utf-8'))
    wd = json.load(open(os.path.join(WDIR, f'{season}-w{week}.json'), encoding='utf-8'))
    windows = {w['code']: w['label'] for w in rp['windows']}
    stories = [story(g, gw, windows) for g, gw in zip(rp['games'], wd['games'])]

    # The game of the week is the one you would have wanted to watch, and what
    # makes that is mostly WHEN it was settled. A game that changed hands ten
    # times and then went quiet after the first quarter is not it; a game won
    # on Monday night is. So lateness carries the most weight, traded blows
    # next, and the margin only breaks ties.
    def watchability(i):
        g = rp['games'][i]
        go = g.get('go_ahead')
        bonus = 0
        if go and not go['residual']:
            bonus = 7 if late(go) else (3 if go['fc']['qtr'] == 4 else 0)
        return g['lead_changes'] + bonus - stories[i]['margin'] / 5
    lead_i = max(range(len(stories)), key=watchability)

    board = ''
    for s in sorted(stories, key=lambda s: -(s['score'][0] + s['score'][1])):
        board += (f'<tr><td class="w">{E(s["winner"])}</td><td class="n">{s["score"][0]}</td>'
                  f'<td style="color:var(--faint)">{E(s["loser"])}</td>'
                  f'<td class="n">{s["score"][1]}</td>'
                  f'<td class="m">+{s["margin"]:.1f}</td></tr>')

    def art(s):
        return (f'<article><h2>{E(s["headline"])}</h2>'
                f'<div class="score">{E(s["winner"])} {s["score"][0]} &middot; '
                f'{E(s["loser"])} {s["score"][1]}</div>'
                f'<div class="dek">{E(s["dek"])}</div>'
                + ''.join(f'<p class="b">{E(p)}</p>' for p in s['paragraphs'])
                + '</article>')

    ls = stories[lead_i]
    lead_html = (f'<div class="sect">The Game of the Week</div>{art(ls)}')
    body = ''.join(art(s) for i, s in enumerate(stories) if i != lead_i)
    desc = (f'{ls["headline"]} — and seven more. Week {week} of the SCFL, '
            f'rebuilt play by play.')
    page = (PAGE.replace('__WK__', str(week)).replace('__SEASON__', str(season))
                .replace('__LEAD__', lead_html).replace('__BOARD__', board)
                .replace('__BODY__', body).replace('__DESC__', desc))
    out = os.path.join(ROOT, f'scfl-week-{week}.html')
    open(out, 'w', encoding='utf-8').write(page)
    json.dump({'season': season, 'week': week, 'lead': lead_i, 'stories': stories},
              open(os.path.join(WDIR, f'{season}-w{week}-stories.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'wrote scfl-week-{week}.html ({len(page):,} chars)')
    for i, s in enumerate(stories):
        print(f'  {"*" if i == lead_i else " "} {s["headline"]}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, required=True)
    ap.add_argument('--season', default='2026')
    a = ap.parse_args()
    build(a.season, a.week)


if __name__ == '__main__':
    main()
