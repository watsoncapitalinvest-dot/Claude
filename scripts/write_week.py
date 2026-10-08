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
_t = importlib.util.spec_from_file_location('sd', os.path.join(ROOT, 'scripts', 'standings.py'))
sd = importlib.util.module_from_spec(_t); sys.modules['sd'] = sd; _t.loader.exec_module(sd)
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


ORD2 = {1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth', 6: 'sixth',
        7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth', 11: 'eleventh',
        12: 'twelfth', 13: 'thirteenth', 14: 'fourteenth', 15: 'fifteenth',
        16: 'sixteenth'}

USED = set()


def seeded(seq, seed, salt=0):
    """Deterministic choice, but never the same line twice in one issue.

    The same game rebuilt twice must read identically or a rebuild looks like
    an edit, so the starting point is seeded rather than random. From there it
    walks forward to the first line this issue has not already spent."""
    if not seq:
        return ''
    start = (seed * 31 + salt * 17) % len(seq)
    for i in range(len(seq)):
        pick = seq[(start + i) % len(seq)]
        if pick not in USED:
            USED.add(pick)
            return pick
    return seq[start]


def an(n):
    """'a' or 'an' in front of a number as it is SPOKEN -- eight, eleven and
    eighteen all take 'an', and so does anything starting with them."""
    d = str(n).lstrip('-')
    return 'an' if d.startswith('8') or d.startswith('11') or d.startswith('18') else 'a'


def tell(e, article=True):
    t = e['text'] or e['kind']
    if article and not t[:1].isalpha():
        t = an(t) + ' ' + t
    return t


def names(items):
    """A list of people as a sentence says them, not as a table prints them."""
    xs = list(items)
    if not xs:
        return ''
    if len(xs) == 1:
        return xs[0]
    return ', '.join(xs[:-1]) + ' and ' + xs[-1]


# ---------------------------------------------------------------------------
# The voice: dry, unimpressed, fond of a drink and of its own misfortune.
# Inspired by the man at the SportsCenter desk rather than copied from him.
#
# The structural rule, learned the hard way: an article is not a list of true
# statements. Each paragraph below takes two or three facts and RELATES them --
# this happened because that did, this mattered only because of that. Facts are
# never simply emitted one after another, and a number only appears when the
# sentence is doing something with it.
#
# The honesty rule is unchanged: jokes live in the connective tissue and never
# inside a factual clause. Every name, number, yardage and sequence comes out
# of the replay.
# ---------------------------------------------------------------------------
LEDE = {
    'rout': [
        'Some games are contests.',
        'There is no kind way to file this one.',
        'I have seen car accidents with more suspense.',
        'The scoreboard operator went home early and nobody blamed him.',
        'This was not a football game, it was a receipt.',
        'I have watched a lot of these. This was one of them, technically.',
        'Mercy rules exist in other sports for a reason.',
        'Somebody should have called this at halftime.',
        'I took notes for the first quarter and then stopped.',
        'There is a version of this where it stays interesting. This was not it.',
    ],
    'comfortable': [
        'This had the shape of a competitive game without ever being one.',
        'Close enough to watch, never close enough to worry about.',
        'A comfortable afternoon, assuming you were on the right side of it.',
        'Never in doubt, never quite dull. A rare combination, and not a thrilling one.',
        'The margin flattered the loser for about an hour.',
        'It stayed respectable, which is a low bar cleared with room to spare.',
        'One team was always going to win this. They did it politely.',
        'A tidy afternoon of work, if you like your afternoons tidy.',
        'This was handled rather than won.',
    ],
    'seesaw': [
        'Now this one I enjoyed, and I enjoy almost nothing.',
        'My scorekeeper asked to be relieved at halftime.',
        'If you like your football unresolved, this was yours.',
        'I lost track twice and I am paid to keep track.',
        'They could not stop trading punches and I could not stop watching.',
        'This one had everything except a moment of calm.',
        'Somebody please check on the men who had money on this.',
        'Every time I reached for the drink, the lead changed.',
        'A proper back-and-forth, and I say that having seen a great many improper ones.',
    ],
    'tight': [
        'Nobody could put this away, which is the polite version.',
        'Tight the whole way. Tight like a bad shoe.',
        'This went to the end, largely because neither of them had the decency to end it.',
        'Two teams spent the weekend refusing to settle anything.',
        'Close games are only fun when you are not in them.',
        'The margin here would fit in a hat.',
        'This one came down to the last thing that happened, which is rarer than it sounds.',
        'Neither of them deserved to lose. One of them did it anyway.',
        'I have seen wider gaps in a set of teeth.',
    ],
    'steady': [
        'Not a classic, not a disaster, one of the other ones.',
        'Workmanlike. Businesslike. Several other kinds of like.',
        'The sort of win you forget by Thursday and mention in December.',
        'A game happened here. I was present for it.',
        'Nothing in this one will be read back to anybody in twenty years.',
        'They got on with it, which I respect and cannot write about.',
        'This was a job of work and it got done.',
        'No drama, no collapse, no complaints. Faintly disappointing.',
        'Solid, unremarkable, and over on time.',
    ],
}

CLOSE = {
    'rout': [
        'They all count the same, as my second wife used to say, usually about something else.',
        'The good news is that it is over, and that is the whole of the good news.',
        'File it, forget it, and let us never speak of it again.',
        'Burn the tape. I will bring the matches.',
        'Somewhere a roster is being rebuilt out of spite.',
        'That one goes in the paper whether anybody likes it or not.',
        'I have said all I intend to say about this.',
        'Next week is also a football game. That is the encouraging part.',
        'A beating, administered and received. Nothing more to add.',
    ],
    'comfortable': [
        'Nothing flashy. Like a good haircut.',
        'Somewhere a waiver claim from August is feeling good about itself.',
        'History will be kind to the winners. It always is.',
        'Efficient. Unsentimental. The way my accountant does things.',
        'A win you can put in the bank and forget the account number.',
        'No notes, and no particular enthusiasm either.',
        'They did what they came to do and left at a reasonable hour.',
        'The kind of result that keeps a season quietly alive.',
        'Good teams win these without anybody noticing. That is the trick.',
    ],
    'seesaw': [
        'That is why you watch. That, and in my case a contract.',
        'I aged a year on that one, and I was already old.',
        'Games like that are why I switched to the second drink. No regrets.',
        'I would watch that again. I will not, but I would.',
        'Somebody put that one on the tape and keep it somewhere safe.',
        'My producer is still lying down.',
        'That is the game selling itself, and it does not need my help.',
        'I have nothing clever for that. It was simply good.',
        'Both of them earned the night off. One of them gets to enjoy it.',
    ],
    'tight': [
        'A win is a win. It does not always feel like one.',
        'Both of these teams should sit down for a minute.',
        'Somewhere a front office is staring at a bench score and hoping nobody noticed.',
        'That is not a loss, that is a paper cut that needs stitches.',
        'A few points the other way and we are writing a different piece.',
        'Neither one of them should frame this.',
        'Fine margins, as the men who lose them like to say.',
        'They will both tell themselves it was close. Only one of them gets to be pleased about it.',
        'That result will look very different in December.',
    ],
    'steady': [
        'On to the next one, which I am assured is also football.',
        'Not pretty. They all count the same.',
        'My producer says move on, and for once he is right.',
        'Filed without comment, mostly because I have none.',
        'A professional afternoon. I have had worse.',
        'Nobody will write a book about this. Somebody had to write a paragraph.',
        'That is the week. The next one starts immediately, as they do.',
        'Respectable, forgettable, and done.',
        'There it is. There it goes.',
    ],
}

# The loser's best man, on a day when it bought him nothing.
BURN = [
    '{n} managed {v} for {t}, which on an afternoon like this one is a lovely painting in '
    'a burning house.',
    '{n} put up {v} for {t} and may as well have stayed home, which is the cruelty of the '
    'format.',
    '{n} had {v} of it for {t}. The other nine spots have some explaining to do.',
    '{n} gave {t} {v} and no help whatsoever arrived.',
    '{n} was the only thing working for {t} at {v}, and one thing is not enough.',
    '{t} got {v} from {n} and almost nothing from anybody standing near him.',
    '{n} finished with {v}. It will look good in a season summary and it did nothing today.',
    '{n} did his part for {t} with {v}. His part was not the problem.',
    '{v} from {n}, and a long quiet afternoon from the rest of {t}.',
]

# The winner's supporting cast.
HELP = [
    'with {r} close enough behind to matter.',
    'and {r} kept him company.',
    'though {r} did enough that he did not have to do it alone.',
    'with {r} chipping in enough to keep it honest.',
    'and {r} covered the rest of the ground.',
    'backed by {r}, who were not merely present.',
    'with {r} doing the unglamorous half of it.',
    'and {r} saw to the remainder.',
    'with useful afternoons from {r} as well.',
]

# A bench mistake that did not end up costing anything. Five games a week can
# need one of these, so the bank runs deeper than the number of games.
NODIFF = [
    'It made no difference to the result, which is the only comfort on offer.',
    'It cost them nothing in the end, which is the best that can be said for it.',
    'The result survived it. Their dignity is a separate question.',
    'They won anyway, so it goes in the drawer marked never mind.',
    'No harm done, unless you count the man who had to watch it.',
    'It did not matter. It rarely does until the one week it does.',
    'Nobody will remember it, which is the kindest outcome available.',
    'The scoreboard forgave it. The group chat may not.',
    'Harmless this time. That is not the same as sensible.',
    'It went unpunished, which is how habits form.',
    'A free lesson, and those are the only ones anybody takes.',
    'The win covers it, the way a rug covers a stain.',
]

# The biggest single play of the week, when it is genuinely large.
BIG = [
    'That, friends, is a career highlight. I would know — mine was a walk.',
    'You do not coach that. You do not scout it either. You just sit there.',
    'Put that one on the tape and keep it.',
    'That is the play people will remember, which is unfortunate for everybody else.',
    'One play, and the rest of the afternoon had to work around it.',
    'That is the sort of thing that gets a man drafted too high next summer.',
    'I have seen entire games produce less than that did.',
    'Everything else in this match was a rounding error next to it.',
    'A single play worth more than some of these teams managed all day.',
]

# A starter who produced nothing.
DUD = [
    'He was out there. I can confirm he was out there.',
    'The box score says he played. The box score has been wrong before, but not this time.',
    'Somebody is going to have to answer for that at the next meeting.',
    'A full afternoon of football and nothing to show anyone.',
    'He took up a roster spot with great commitment.',
    'That is not a performance, that is an attendance record.',
    'I have checked twice. That is the number.',
    'He will be dropped by Wednesday and nobody will write about it.',
    'A quiet day at the office, if the office had been closed.',
]


# Which positions a lineup slot will actually accept. A bench player can only
# be said to have been "left out" for a starter he could legally have replaced:
# an RB does not go in a WR slot, so comparing their points implies a choice
# that was never on the table.
SLOT_OK = {
    'QB': {'QB'}, 'RB': {'RB'}, 'WR': {'WR'}, 'TE': {'TE'}, 'K': {'K'},
    'DEF': {'DEF'}, 'DST': {'DEF'},
    'FLEX': {'RB', 'WR', 'TE'},
    'WRRB_FLEX': {'RB', 'WR'},
    'REC_FLEX': {'WR', 'TE'},
    'SUPER_FLEX': {'QB', 'RB', 'WR', 'TE'},
}


def best_regret(team, slots):
    """The biggest points gain available from a swap that was legal.

    Returns (bench_player, starter_replaced, gain) or None. Every bench player
    is tested against every starter whose SLOT would have taken him, rather
    than the top bench score against the worst starter on the roster.
    """
    lineup = list(zip(slots, team['starters']))
    best = None
    for b in team['bench']:
        bp = (b.get('pos') or '').upper()
        if not bp or (b.get('points') or 0) <= 0:
            continue
        for slot, st in lineup:
            if bp not in SLOT_OK.get(slot, {slot}):
                continue
            gain = (b.get('points') or 0) - (st.get('points') or 0)
            if gain > 0 and (best is None or gain > best[2]):
                best = (b, st, gain)
    return best


def story(g, gw, windows, slots=None, st=None):
    """One game report, written as a piece rather than assembled from slots."""
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
    marg = f'{g["margin"]:.1f}'
    last = lambda n: n.split()[-1]
    P = []

    # ---- headline & dek ----------------------------------------------------
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
    dek = (f'{wn} {W["final"]}, {ln} {L["final"]}.'
           + (f' {g["lead_changes"]} lead changes, and the last one was the only one that kept.'
              if g['lead_changes'] >= 6 else
              ' It was over long before it was finished.' if arc == 'rout' else
              f' {marg} points in it.' if arc == 'tight' else ''))

    # ---- 1. the lede: the result AND what the game actually was ------------
    hook = seeded(LEDE[arc], seed)
    if arc == 'rout':
        P.append(f'{hook} {wn} beat {ln} {W["final"]} to {L["final"]}, '
                 f'and the {marg} points between them at the end flatter nobody — '
                 + (f'{ln} did not lead at any stage of this football game.'
                    if g['lead_changes'] == 0 else
                    f'{ln} led early, lost it, and never argued again.'))
    elif g['lead_changes'] >= 6:
        P.append(f'{hook} {wn} and {ln} swapped the lead {g["lead_changes"]} times before one of '
                 f'them finally kept it, and {wn} were the ones holding it when the weekend ran '
                 f'out: {W["final"]}–{L["final"]}.')
    elif go and late(go) and go['side'] == wi:
        P.append(f'{hook} {wn} were behind this football game until the fourth quarter and won it '
                 f'{W["final"]} to {L["final"]}, which tells you most of what you need and none of '
                 f'how it felt.')
    else:
        P.append(f'{hook} {wn} {W["final"]}, {ln} {L["final"]}, {an(marg)} {marg}-point margin that '
                 f'never seriously came under review.')

    # ---- 2. the middle: the swing, with its consequence attached -----------
    if go:
        q, w = when(go, windows)
        who, pl = go['player'], tell(go)
        if go['kind'] in ('int', 'fum'):
            P.append(f'It turned, as these things do, on somebody else’s mistake. {who} threw '
                     f'{pl} in the {q} — {w} — and the lead crossed the aisle at '
                     f'{scoreline(go, go["side"])}. '
                     + (f'{ln} spent the rest of the weekend chasing it and never got close enough '
                        f'to touch it.' if go['side'] != wi else
                        f'{wn} took it straight back and kept it.'))
        elif go['side'] == wi:
            early = go['fc']['qtr'] <= 2
            if early:
                P.append(f'They took it in the {q} — {who} with {pl}, {scoreline(go, go["side"])} '
                         f'— and then simply never gave it back. '
                         + (f'{len(tds)} touchdowns were scored after that and not one of them '
                            f'put {ln} in front again.' if len(tds) >= 6 else
                            f'{ln} never led again.'))
            else:
                P.append(f'The play that settled it came in the {q}, {w}: {who} with {pl}. '
                         f'That put {wn} in front at {scoreline(go, go["side"])}, and for all the '
                         f'traffic that had come before it, nobody took it back.'
                         + (f' There were {len(tds)} touchdowns in this game and the one that '
                            f'mattered went {wn}\u2019s way last.' if len(tds) >= 6 else ''))
        else:
            P.append(f'{ln} had their moment in the {q}, {w} — {who} with {pl}, good for the lead '
                     f'at {scoreline(go, go["side"])} — and it bought them exactly as long as it '
                     f'took {wn} to answer.')
    elif g['lead_changes'] == 0:
        P.append(f'There is no sequence to describe, because there was no sequence. {wn} scored '
                 f'first, kept scoring, and the remainder was arithmetic performed in public.')

    # ---- 2b. what it did to their seasons ---------------------------------
    # A game report that never says what the result cost anybody is a box score
    # with adjectives. This is the paragraph that gives the ninety minutes a
    # consequence, and it is written from the real table rather than asserted.
    if st:
        rw, rl = st['by_team'].get(wn), st['by_team'].get(ln)
        if rw and rl:
            bits = f'{wn} {sd.situation(st, wn)}'
            bits += f'. {ln} {sd.situation(st, ln)}'
            if rl['w'] == 0 and rl['games'] >= 3:
                bits += ', and are still looking for a first win'
            bits += '.'
            if rw['seed'] <= 3:
                bits += (f' {wn} sit {ORD2.get(rw["seed"], rw["seed"])} in the league on the '
                         f'full table, {rw["pf"]:.0f} points scored.')
            elif rl['seed'] >= st['teams'] - 2:
                bits += (f' {ln} are {ORD2.get(rl["seed"], rl["seed"])} of {st["teams"]}, and '
                         f'the {rl["pa"]:.0f} points conceded is most of the reason.')
            P.append(bits)

    # ---- 3. the people, related to each other rather than listed -----------
    if wtop:
        topn, topv = wtop[0]
        rest = [n for n, _ in wtop[1:3]]
        if big and big['side'] == wi and big['pts'] >= 8:
            q, w = when(big, windows)
            line = (f'{big["player"]} did the heaviest lifting — {tell(big)} in the {q}, {w}, '
                    f'worth {big["pts"]:.1f} on its own')
            if topn != big['player']:
                line += f', though it was {topn} who finished with the biggest number at {topv:.1f}'
            line += '.'
            if rest:
                line += f' {names(rest)} did the rest of the damage.'
        else:
            line = f'{topn} led the winners with {topv:.1f}'
            line += ((', ' + seeded(HELP, seed, 8).format(r=names(rest))) if rest else '.')
        if ltop:
            ln0, lv0 = ltop[0]
            if lv0 > topv:
                line += (f' {ln0} actually outscored every man on the field with {lv0:.1f} and '
                         f'still lost, which tells you plenty about the other nine spots.')
            elif arc in ('rout', 'comfortable'):
                line += ' ' + seeded(BURN, seed, 7).format(n=ln0, v=f'{lv0:.1f}', t=ln)
            else:
                line += f' {ln0} answered with {lv0:.1f} and it finished {marg} short.'
        P.append(line)

    # ---- 4. the cost: a dud or a bench, framed as the reason ---------------
    cost = None
    for t, side in ((gw['teams'][1 - wi], 1 - wi), (gw['teams'][wi], wi)):
        r = best_regret(t, slots) if slots else None
        if not r:
            continue
        bb, ws, gap = r
        if gap >= 12:
            nm = TEAM(t['team'])
            if side != wi and gap > g['margin']:
                cost = (f'{nm} will want to look away from this next bit. {bb["name"]} sat on '
                        f'their bench and scored {bb["points"]:.1f} while {ws["name"]} held the '
                        f'same slot and returned {ws["points"]:.1f} — {gap:.1f} points in a '
                        f'chair, in a game they lost by {marg}. That is not a defeat, that is a '
                        f'self-inflicted wound with a witness.')
            else:
                cost = (f'{nm} left {bb["name"]} and his {bb["points"]:.1f} on the bench and '
                        f'played {ws["name"]} in the spot instead, for {ws["points"]:.1f}. '
                        + seeded(NODIFF, seed, 9))
            break
    if not cost and arc in ('rout', 'comfortable', 'steady'):
        duds = [p for p in gw['teams'][1 - wi]['starters']
                if p['pos'] not in ('K', 'DEF') and (p.get('points') or 0) <= 2]
        if duds:
            d = min(duds, key=lambda p: p['points'])
            cost = (f'{ln} started {d["name"]} and were rewarded with {d["points"]:.1f} points. '
                    f'He was out there. I can confirm he was out there.')
    if cost:
        P.append(cost)

    # ---- 5. the sign-off ----------------------------------------------------
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
    slots = [x for x in (wd.get('roster_positions') or []) if x != 'BN']
    st = sd.build(str(season), int(week))
    if st and st['through'] != int(week):
        print(f'  note: standings only run through week {st["through"]} '
              f'(weeks on disk: {", ".join(map(str, st["weeks"]))})')
    stories = [story(g, gw, windows, slots, st) for g, gw in zip(rp['games'], wd['games'])]

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
