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


# Phrases already spent in this issue. Eight games out of a phrasebank this
# size will collide, and two stories opening with the same joke reads worse
# than either story would alone.
USED = set()


def seeded(seq, seed, salt=0):
    """Deterministic choice, but never the same line twice in one issue.

    The same game rebuilt twice must read identically or a rebuild looks like
    an edit, so the starting point is seeded rather than random. From there it
    walks forward to the first line this issue has not already used."""
    if not seq:
        return ''
    start = (seed * 31 + salt * 17) % len(seq)
    for i in range(len(seq)):
        pick = seq[(start + i) % len(seq)]
        if pick not in USED:
            USED.add(pick)
            return pick
    return seq[start]


# ---------------------------------------------------------------------------
# The voice. Inspired by the man at the SportsCenter desk, not a clone of him:
# dry, unimpressed, willing to say the quiet part, fond of a drink and of his
# own misfortune. The rule that keeps it honest is that the jokes live in the
# connective tissue and never in a factual clause. Every number, name, yardage
# and sequence below comes out of the replay. The colour is how it is said.
# ---------------------------------------------------------------------------
OPEN = {
    'rout': [
        'Some games are contests. This was a chore.',
        'There is no polite way to write this one up, so I will not try.',
        'I have seen car accidents with more suspense, and better outcomes for everybody involved.',
        'This one was decided early and then kept going anyway, which is the worst kind.',
    ],
    'comfortable': [
        'Never close enough to be interesting, never far enough apart to turn off.',
        'A comfortable afternoon, if you were on the right side of it.',
        'This had the shape of a competitive game without ever actually being one.',
    ],
    'seesaw': [
        'Now this one I enjoyed, and I say that about almost nothing.',
        'Back and forth all afternoon. My scorekeeper asked to be relieved.',
        'If you like your football unresolved until the very end, this was your game.',
    ],
    'tight': [
        'Close the whole way, which is a nice way of saying nobody could put it away.',
        'They played a tight one. Tight is the word for it. Tight like a bad shoe.',
        'This went down to the end, mostly because neither side had the decency to end it.',
    ],
    'steady': [
        'Not a classic. Not a disaster. One of the other ones.',
        'Workmanlike. Businesslike. Several other kinds of like.',
        'The kind of win you forget by Thursday and bring up in December.',
    ],
}

CLOSE = {
    'rout': [
        'They all count the same, as my second wife used to say, usually about something else.',
        'The good news is that it is over. That is the entire list of good news.',
        'File it, forget it, and let us never speak of it again.',
    ],
    'comfortable': [
        'Nothing flashy. Like a good haircut.',
        'Somewhere a waiver claim from August is feeling pretty good about itself.',
        'History will be kind to the winners. It always is.',
    ],
    'seesaw': [
        'That is why you watch. Well. That, and the fact that I am contractually obligated.',
        'I aged a year on that one and I was already old.',
        'A game like that is why I switched to the second drink. I regret nothing.',
    ],
    'tight': [
        'Both of these teams should probably sit down for a minute.',
        'A win is a win. It just does not always feel like one.',
        'Somewhere a front office is staring at a bench score and hoping nobody noticed.',
    ],
    'steady': [
        'On to the next one, which I am told is also a football game.',
        'Not pretty. They all count the same.',
        'My producer is telling me to move on, and for once he is right.',
    ],
}

BIG = ['That, friends, is a career highlight. I would know — mine was a walk.',
       'You do not coach that. You do not scout it either. You just sit there.',
       'Put that one on the tape and keep it.',
       'That is the play people will remember, which is unfortunate for everyone else.']

DUD = ['A lovely painting in a burning house.',
       'He was out there. I can confirm he was out there.',
       'The box score says he played. The box score has been wrong before, but not this time.',
       'Somebody is going to have to answer for that at the next meeting.']


def an(n):
    """'a' or 'an' in front of a number as it is SPOKEN -- eight, eleven and
    eighteen all take 'an', and so does anything starting with them."""
    d = str(n).lstrip('-')
    return 'an' if d.startswith('8') or d.startswith('11') or d.startswith('18') else 'a'


def tell(e, windows, article=True):
    """A play, told. Yardage phrases need an article before they can sit in a
    sentence, and the window is worth naming because it is the whole trick:
    Monday night and the late fourth are the same moment."""
    t = e['text'] or e['kind']
    if article and not t[:1].isalpha():
        t = an(t) + ' ' + t
    return t


def story(g, gw, windows):
    """One game report. Factually bound to the replay, delivered by the desk."""
    tl = [e for e in g['timeline'] if not e['residual']]
    A, B = g['teams']
    wi = 0 if A['final'] >= B['final'] else 1
    W, L = (A, B) if wi == 0 else (B, A)
    wn, ln = TEAM(W['team']), TEAM(L['team'])
    arc = arc_of(g, tl)
    seed = int(round(W['final'] * 10 + L['final'] + g['matchup_id']))
    go = g.get('go_ahead')
    if go and go['residual']:
        go = None
    big = max(tl, key=lambda e: e['pts']) if tl else None
    wtop, ltop = tally(tl, wi), tally(tl, 1 - wi)
    tds = [e for e in tl if e['td']]
    P = []

    # ---- headline -----------------------------------------------------------
    last = lambda n: n.split()[-1]
    if go and late(go) and go['side'] == wi and arc in ('tight', 'seesaw'):
        hl = f'{last(go["player"])} Wins It Late for {wn}'
    elif arc == 'rout':
        hl = seeded([f'{wn} Leave No Doubt', f'{wn} Make It Hurt',
                     f'{ln} Never Showed Up'], seed)
    elif arc == 'seesaw':
        hl = seeded([f'{wn} Win the Last Exchange', f'{wn} Survive the Back-and-Forth'], seed)
    elif arc == 'tight':
        hl = seeded([f'{wn} Edge {ln}', f'{wn} Hang On'], seed)
    else:
        hl = seeded([f'{wn} Handle {ln}', f'{wn} Hold Off {ln}'], seed)

    # ---- dek ----------------------------------------------------------------
    if arc == 'rout':
        dek = f'{wn} {W["final"]}, {ln} {L["final"]}. It was over long before it was finished.'
    elif g['lead_changes'] >= 6:
        dek = f'{g["lead_changes"]} lead changes. {wn} had it last, {W["final"]}–{L["final"]}.'
    elif go and late(go):
        dek = f'Settled in the fourth. {wn} {W["final"]}, {ln} {L["final"]}.'
    else:
        dek = f'{wn} {W["final"]}, {ln} {L["final"]}.'

    # ---- P1: the hook, then the result -------------------------------------
    marg = f'{g["margin"]:.1f}'
    P.append(seeded(OPEN[arc], seed) + ' ' +
             f'{wn} {W["final"]}, {ln} {L["final"]}' +
             (f', {an(marg)} {marg}-point margin.' if arc != 'tight'
              else f' — {marg} points in it.'))

    # ---- P2: how it got there ----------------------------------------------
    if g['lead_changes'] >= 6:
        # how far across the weekend the trading actually ran. Ten lead changes
        # that all happen before one o'clock is a different story from ten that
        # run to Monday night, and the sentence has to know which it was.
        flips = [e for e in tl if e.get('go_ahead')]
        wins_ = {e['window'] for e in flips}
        if len(wins_) <= 1:
            span = (f'All of it inside {windows.get(flips[0]["window"], "one window")}, '
                    f'which tells you how early this got settled and how long it took '
                    f'anybody to notice.')
        elif 'MON' in wins_ or 'SNF' in wins_:
            span = 'It ran right through to the night games.'
        else:
            span = 'It took most of Sunday to shake out.'
        P.append(f'They traded it {g["lead_changes"]} times. Every time one of them looked like '
                 f'getting clear the other one answered. {span} There were {len(tds)} touchdowns '
                 f'between them, and none of them settled a thing until the last one did.')
    elif g['lead_changes'] == 0:
        P.append(f'{ln} did not lead at any point in this football game. Not once. There is no '
                 f'sequence to describe because there was no sequence — {wn} scored first and '
                 f'then kept scoring, and the rest was arithmetic.')
    elif arc == 'rout':
        P.append(f'{ln} had the lead early and then watched it leave. By the time it mattered '
                 f'there were {g["margin"]:.1f} points in it, and the only question left was '
                 f'whether anybody was still watching.')

    # ---- P3: the play that did it -------------------------------------------
    if go:
        q, w = when(go, windows)
        who, pl = go['player'], tell(go, windows)
        if go['kind'] in ('int', 'fum'):
            P.append(f'It turned on a mistake, because of course it did. {who} threw {pl} in the '
                     f'{q} — {w} — and the lead went across the aisle at {scoreline(go, go["side"])}. '
                     f'{"He got it back." if go["side"] == wi else f"{ln} never got it back."}')
        else:
            took = (f'put {wn} in front' if go['side'] == wi else 'handed the lead over')
            P.append(f'The one that did it came in the {q}, {w}: {who}, {pl}, and that {took} at '
                     f'{scoreline(go, go["side"])}. '
                     + ('Nobody took it back.' if go['side'] == wi else ''))

    # ---- P4: the biggest swing ---------------------------------------------
    if big and big is not go and big['pts'] >= 7:
        q, w = when(big, windows)
        side = TEAM(g['teams'][big['side']]['team'])
        P.append(f'The biggest single play of the week belonged to {big["player"]} — '
                 f'{tell(big, windows)} in the {q}, {w}, worth {big["pts"]:.1f} to {side}. '
                 + (seeded(BIG, seed, 2) if big['pts'] >= 10 else ''))

    # ---- P5: who carried it, and who did not -------------------------------
    if wtop:
        names = ', '.join(f'{n} ({v:.1f})' for n, v in wtop[:3])
        line = f'{wn} got there on {names}.'
        if ltop:
            if arc in ('rout', 'comfortable'):
                line += (f' {ltop[0][0]} led {ln} with {ltop[0][1]:.1f}, which on an afternoon '
                         f'like this one is a lovely painting in a burning house.')
            else:
                line += f' {ltop[0][0]} answered with {ltop[0][1]:.1f} and it was not quite enough.'
        P.append(line)

    # ---- P6: the dud --------------------------------------------------------
    duds = [p for p in gw['teams'][1 - wi]['starters']
            if p['pos'] not in ('K', 'DEF') and (p.get('points') or 0) <= 2]
    if duds and arc in ('rout', 'comfortable', 'steady'):
        d = min(duds, key=lambda p: p['points'])
        P.append(f'{ln} started {d["name"]} and got {d["points"]:.1f} points for the trouble. '
                 + seeded(DUD, seed, 3))

    # ---- P7: the bench ------------------------------------------------------
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
            if gap > g['margin'] and nm == ln:
                verdict = ('and yes, before you ask, that would have won them the football game. '
                           'I would not bring it up at the next meeting.')
            else:
                verdict = 'It would not have changed the result, which is the only consolation available.'
            P.append(f'{nm} left {bb["name"]} and his {bb["points"]:.1f} on the bench and started '
                     f'{ws["name"]}, who returned {ws["points"]:.1f}. That is {gap:.1f} points '
                     f'sitting in a chair. {verdict}')
            break

    # ---- P8: the sign-off ---------------------------------------------------
    P.append(seeded(CLOSE[arc], seed, 5))

    P = [re.sub(r'\s+', ' ', x).strip() for x in P if x and x.strip()]
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
