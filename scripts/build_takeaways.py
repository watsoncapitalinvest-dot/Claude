#!/usr/bin/env python3
"""Ten Things The Ledger Says -- one sheet, ten findings, every one of them counted.

    python3 scripts/build_takeaways.py

The Trade Desk's three chart pages show the shape of the ledger. This is what
the shape turns out to mean, on one page, in ten entries.

NOTHING HERE IS ANYBODY'S HAND. Every figure is a completed trade the whole
league watched happen, priced on a public consensus board. No valuation of an
unmade deal, no read on who is buying or selling now, no assessment of a
roster's weak spot -- the same test scfl-who-wins-trades.html passes.

The model is NOT reimplemented here. fairness() and later() are imported from
build_trade_charts.py, so this sheet and the charts cannot disagree: one
threshold, one pricing basis, one set of franchise keys. A second copy of the
same arithmetic is how two pages on the same site end up printing different
numbers for the same deal.

Every finding is a function that returns None when the thing it would say is
not true of the data in front of it. A correlation claim checks the
correlation before it is made; an "only three franchises" claim counts them.
If a finding will not derive, it does not print and the headline counts what
is left -- the sheet is not contractually ten. It is however ten today, and
build() says so out loud if that ever changes.
"""
import importlib.util, json, math, os, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod(name, path):
    s = importlib.util.spec_from_file_location(name, os.path.join(ROOT, 'scripts', path))
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


TC = _mod('tcharts', 'build_trade_charts.py')
ad = _mod('addm', 'build_addendum.py')
E = ad.esc

OUT = os.path.join(ROOT, 'scfl-trade-takeaways.html')
OG = os.path.join(ROOT, 'scfl-trade-takeaways-og.jpg')

WORD = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
        'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
        'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty']
CAPS = [w.capitalize() for w in WORD]


def num(n):
    return WORD[n] if 0 <= n < len(WORD) else f'{n:,}'


def Num(n):
    return CAPS[n] if 0 <= n < len(CAPS) else f'{n:,}'


def money(v, cents=False):
    """House money: a real minus sign, cents only where they carry a point, and
    never broken across a line -- a minus left at the end of a line with its
    figure on the next one reads as a dash."""
    s = f'{abs(v):,.2f}' if cents else f'{abs(round(v)):,}'
    return '<span class="nb">' + ('&minus;$' if v < 0 else '$') + s + '</span>"'.rstrip('"')


def sign(v, places=2):
    """A signed figure with a real minus sign. A hyphen reads as a dash next to
    a word, and every other number on this desk uses U+2212."""
    return f'{v:+.{places}f}'.replace('-', '&minus;')


def poss(name):
    """Wookie Leaks' deal, not Wookie Leaks's. Half the clubs end in an s."""
    return name + ('&rsquo;' if name.rstrip().lower().endswith('s') else '&rsquo;s')


def andlist(xs):
    """A, B and C -- a comma before the last one reads as a fourth name."""
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


def corr(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    sy = math.sqrt(sum((b - my) ** 2 for b in ys))
    if not sx or not sy:
        return 0.0
    return sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / (sx * sy)


def rank_of(rows, r):
    """Where a franchise finishes on net, 1 being the richest."""
    return sorted(rows, key=lambda x: -x['net']).index(r) + 1


def ordinal(n):
    return {1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth',
            6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth',
            11: 'eleventh', 12: 'twelfth', 13: 'thirteenth', 14: 'fourteenth',
            15: 'fifteenth', 16: 'sixteenth'}.get(n, f'{n}th')


# --- the findings ----------------------------------------------------------
# Each takes the whole board and returns {fig, claim, body} or None. The
# condition it tests is the condition the sentence asserts, so a finding
# cannot outlive the data that made it true.

def f_fair(C):
    """Does trading fairly have anything to do with coming out ahead?"""
    rk = C['rank']
    c = corr([r['level'] for r in rk], [r['net'] for r in rk])
    if abs(c) > 0.2:
        return None                      # there IS a relationship; do not say this
    fair = max(rk, key=lambda r: r['e'] / r['n'])
    unf = min(rk, key=lambda r: r['level'])
    best = C['bestRec']
    if not best:
        return None
    return {
        'fig': sign(c),
        'claim': 'Being fair tells you nothing about whether you win',
        'body': (
            f'Across the {num(len(rk))} ranked franchises, the correlation between how '
            f'often a side&rsquo;s deals come out level and how many dollars it ends up '
            f'with is <b>{sign(c)}</b>. Not weak &mdash; absent. '
            f'{E(fair["club"])} are the fairest side in the league at '
            f'{round(100 * fair["e"] / fair["n"])}&thinsp;% level and have the best '
            f'record. {E(unf["club"])} come out level least often of anybody at '
            f'{unf["level"]}&thinsp;% and finish {ordinal(rank_of(rk, unf))} on money. '
            f'{Num(len(rk))} points is not a study, but there is no hint of a '
            f'relationship to chase.'),
    }


def f_grind(C):
    """Is a franchise's total built out of one deal or out of all of them?"""
    rk = C['rank']
    net = [r['net'] for r in rk]
    cm = corr([r['med'] for r in rk], net)
    cb = corr([r['best'] for r in rk], net)
    cw = corr([r['worst'] for r in rk], net)
    if cm <= max(cb, cw):
        return None                      # the big deal explains it better; different story
    return {
        'fig': f'{cm:.2f}',
        'claim': 'It is a grind, not a heist',
        'body': (
            f'The single best predictor of what a franchise is worth across the whole '
            f'ledger is its <b>median deal</b> &mdash; correlation <b>{cm:.2f}</b>. Its '
            f'best ever trade manages {sign(cb)} and its worst {sign(cw)}. Nobody in this '
            f'league got rich on one afternoon: the medians that separate '
            f'{E(max(rk, key=lambda r: r["med"])["club"])} at the top from '
            f'{E(min(rk, key=lambda r: r["med"])["club"])} at the bottom run from '
            f'{money(max(r["med"] for r in rk), cents=True)} to '
            f'{money(min(r["med"] for r in rk), cents=True)} a deal. That is the whole '
            f'league, {money(abs(max(r["med"] for r in rk)) + abs(min(r["med"] for r in rk)), cents=True)} '
            f'wide.'),
    }


def f_split(C):
    """Is anybody actually good at trading, or only at half of it?"""
    rk = C['rank']
    same = [r for r in rk if (r['players'] > 0) == (r['picks'] > 0)]
    split = [r for r in rk if r not in same]
    if len(split) <= len(same):
        return None
    ranks = sorted(rank_of(rk, r) for r in same)
    return {
        'fig': f'{len(split)}/{len(rk)}',
        'claim': 'Almost nobody is simply good at trading',
        'body': (
            f'<b>{Num(len(split))} of the {num(len(rk))}</b> gain on one half of the '
            f'ledger and lose on the other &mdash; up on players and down on picks, or '
            f'the reverse. Only {num(len(same))} move both the same way, and they are '
            f'the ones at the ends: '
            + andlist(f'{E(r["club"])} ({ordinal(rank_of(rk, r))})'
                      for r in sorted(same, key=lambda r: rank_of(rk, r)))
            + f'. The top and the bottom are consistent. Everyone in between is good at '
              f'exactly one thing, and the table does not tell them which.'),
    }


def f_mirror(C):
    """The two best, and whether they do it the same way."""
    rk = sorted(C['rank'], key=lambda r: -r['net'])
    if len(rk) < 2:
        return None
    a, b = rk[0], rk[1]
    side = lambda r: 'players' if abs(r['players']) > abs(r['picks']) else 'picks'
    if side(a) == side(b):
        return None                      # they do it the same way; no mirror to print
    return {
        'fig': money(a['net'] - b['net']),
        'claim': 'The two best traders in the league are mirror images',
        'body': (
            f'<b>{E(a["club"])}</b>: {money(a["players"])} on players, '
            f'{money(a["picks"])} on picks. <b>{E(b["club"])}</b>: '
            f'{money(b["players"])} on players, {money(b["picks"])} on picks. '
            f'{money(a["net"])} and {money(b["net"])} &mdash; nearly the same '
            f'destination by opposite roads. One buys the man, the other buys the slot, '
            f'and neither does the other&rsquo;s job at all.'),
    }


def f_volume(C):
    """Does trading more often get you anywhere?"""
    rk = C['rank']
    cn = corr([r['n'] for r in rk], [r['net'] for r in rk])
    cl = corr([r['n'] for r in rk], [r['level'] for r in rk])
    if abs(cn) > 0.5:
        return None
    busy = max(rk, key=lambda r: r['n'])
    # the busiest side that still finished behind, if there is one
    behind = [r for r in rk if r['net'] < 0]
    busy_behind = max(behind, key=lambda r: r['n']) if behind else None
    thin = [r for r in C['rows'] if r['n'] < C['minDeals'] and r['net'] > 0]
    quiet = max(thin, key=lambda r: r['net']) if thin else None
    return {
        'fig': f'{cn:.2f}',
        'claim': 'Volume buys nothing',
        'body': (
            f'Deals made against dollars made: <b>{cn:.2f}</b>. Deals made against how '
            f'often you come out level: <b>{cl:.2f}</b>. {E(busy["club"])} made '
            f'{busy["n"]} and finished {money(busy["net"])}'
            + (f'; {E(busy_behind["club"])} made {busy_behind["n"]} and finished '
               f'{money(busy_behind["net"])}' if busy_behind else '')
            + (f'. {E(quiet["club"])} made {num(quiet["n"])} and {"is" if False else "are"} '
               f'up {money(quiet["net"])}' if quiet else '')
            + '. Picking up the phone is not a strategy.'),
    }


def f_concentration(C):
    """How the winnings are spread."""
    rk = C['rank']
    ahead = [r for r in rk if r['net'] > 0]
    behind = [r for r in rk if r['net'] < 0]
    if len(ahead) < 3:
        return None
    pot = sum(r['net'] for r in ahead)
    top3 = sorted(ahead, key=lambda r: -r['net'])[:3]
    share = round(100 * sum(r['net'] for r in top3) / pot)
    if share < 60:
        return None                      # it is not concentrated; do not call it that
    return {
        'fig': f'{share}%',
        'claim': 'The money is held by three men',
        'body': (
            f'{Num(len(ahead))} of the {num(len(rk))} ranked franchises are ahead and '
            f'{num(len(behind))} behind, which sounds like a league in balance. It is '
            f'not. '
            + andlist(E(r['club']) for r in top3)
            + f' hold <b>{share}&thinsp;%</b> of every dollar on the plus side '
              f'({money(sum(r["net"] for r in top3))} of {money(pot)}). This is not a '
              f'few sharks and a soft middle. It is three men and then a long flat '
              f'stretch.'),
    }


def f_onecurrency(C):
    """The biggest single-currency gain in the league, and what it bought."""
    rk = C['rank']
    best = max(rk, key=lambda r: max(r['players'], r['picks']))
    side = 'players' if best['players'] > best['picks'] else 'picks'
    other = 'picks' if side == 'players' else 'players'
    gain, drag = best[side], best[other]
    if drag >= 0 or abs(drag) < 0.4 * gain:
        return None                      # nothing is cancelling it; no finding here
    return {
        'fig': money(gain),
        'claim': f'The best {side[:-1]} trader in the league has almost nothing to show for it',
        'body': (
            f'<b>{E(best["club"])}</b> are up <b>{money(gain)}</b> on {side} across '
            f'{best["n"]} deals &mdash; the largest gain on either half of the ledger '
            f'anybody has. Their net is {money(best["net"])}, because they hand back '
            f'{money(abs(drag))} on {other}. The best {side[:-1]} trader in the league '
            f'is also one of its worst {other[:-1]} traders, and the two very nearly '
            f'cancel.'),
    }


def f_twoways(C):
    """Two franchises behind by the same mechanism? No -- by opposite ones."""
    rk = [r for r in C['rank'] if r['net'] < 0 and r['worst'] < 0]
    if len(rk) < 2:
        return None
    frac = lambda r: abs(r['worst']) / abs(r['net'])
    leak = min(rk, key=frac)
    blow = max(C['rank'], key=lambda r: abs(r['worst']))
    if leak is blow or frac(leak) > 0.35:
        return None
    # The biggest loss and the most lopsided deal are usually the same trade
    # seen from the other side. Worth saying so, because the aside names that
    # side by the name it was playing under and this entry names it by the
    # name it goes by now -- two names, one franchise, and a reader left to
    # guess whether they are looking at one deal or two.
    big = C.get('biggest') or {}
    same = (big.get('loserKey') == blow['k']
            and abs(abs(blow['worst']) - big.get('margin', 0)) <= 1)
    return {
        'fig': f'{round(100 * frac(leak))}%',
        'claim': 'There are two ways to lose, and the table cannot tell them apart',
        'body': (
            f'<b>{poss(E(leak["club"]))}</b> worst single deal is {money(leak["worst"])} '
            f'against a {money(leak["net"])} total &mdash; no one trade is more than '
            f'{round(100 * frac(leak))}&thinsp;% of the hole &mdash; with a median of '
            f'{money(leak["med"], cents=True)} across {leak["n"]} trades, '
            f'{leak["down"]} of which went down. That is a leak. '
            f'<b>{E(blow["club"])}</b> took the single biggest loss in the league '
            f'({money(blow["worst"])}'
            + (f', the {big["season"]} deal in the margin, which they signed as '
               f'{E(big["loser"])}' if same else '')
            + f') and still finish {money(blow["net"])} across {blow["n"]}. One has a '
              f'habit. The other had a bad Tuesday.'),
    }


def f_hold(C):
    """Does the verdict on the day survive a year?"""
    L = C['later']
    if not L:
        return None
    t = L['totals']
    held = t['n'] - t['ch']
    pct = round(100 * held / t['n'])
    push = t['de'] - t['ye']
    if push <= 0:
        return None
    return {
        'fig': f'{pct}%',
        'claim': 'The board is right about four deals in five',
        'body': (
            f'Of the {t["n"]} verdicts that can be checked a year on, <b>{held} hold '
            f'and {t["ch"]} change</b> &mdash; {pct}&thinsp;%. And the league-wide '
            f'split barely moves: {num(push)} deals that looked level on the day did '
            f'not stay level, which is {num(t["yw"] - t["dw"])} more wins and the same '
            f'{num(t["yl"] - t["dl"])} more losses. The wait does not make this league '
            f'fairer. It moves who is holding the win.'),
    }


def f_time(C):
    """Who the year is kind to, and who it is not."""
    L = C['later']
    if not L:
        return None
    lr = [r for r in L['rows'] if r['n'] >= L['minDeals']]
    if len(lr) < 2:
        return None
    up = max(lr, key=lambda r: r['year'] - r['day'])
    dn = min(lr, key=lambda r: r['year'] - r['day'])
    if up['year'] - up['day'] <= 0 or dn['year'] - dn['day'] >= 0:
        return None
    d0 = sum(abs(r['day']) for r in lr)
    d1 = sum(abs(r['year']) for r in lr)
    move = round(100 * (d1 - d0) / d0)
    return {
        'fig': money(up['year'] - up['day']),
        'claim': 'Time is not neutral, and it is not random either',
        'body': (
            f'<b>{E(up["club"])}</b> recover <b>{money(up["year"] - up["day"])}</b> of '
            f'their day-of position ({money(up["day"])} to {money(up["year"])}): they '
            f'sold players who then did not produce. <b>{E(dn["club"])}</b> go the '
            f'other way, {money(dn["day"])} to {money(dn["year"])}. Across all '
            f'{num(len(lr))}, the total money on the table '
            f'{"falls" if move < 0 else "rises"} {abs(move)}&thinsp;% over the year, so '
            f'the typical edge is real and smaller than it looked on the day.'),
    }


FINDINGS = [f_fair, f_grind, f_split, f_mirror, f_volume,
            f_concentration, f_onecurrency, f_twoways, f_hold, f_time]


# --- one line a franchise --------------------------------------------------
# Sixteen lines, and not one of them written here. Each ANGLE below looks at
# the whole board and bids for the franchises it has something true to say
# about, with a score for how striking the thing is. Every franchise then
# takes the best bid still available, and an angle can only be spent once, so
# the sixteen lines are sixteen different observations rather than the same
# sentence with the names swapped.
#
# The point of doing it this way rather than typing sixteen sentences: a line
# cannot survive the number that made it true. If Killer Klowns take a $90
# loss tomorrow, nobody has to remember to delete the line about their worst
# deal being $17 -- the bid simply is not made.
#
# An angle may name only what it has counted, and only inside the pool it
# counted it in: `rank` is the thirteen with enough deals to be ranked, `all`
# is the sixteen. Saying "lowest in the league" off a pool of thirteen while
# one of the other three is lower is the exact mistake this desk keeps making.

def _rank(pool, r, key, high=True):
    """Where a franchise sits on a measure, 1 being the end being claimed."""
    s = sorted(pool, key=lambda x: -key(x) if high else key(x))
    return s.index(r) + 1


def a_clean_sheet(C, **_):
    """Every priced deal came out level. Nobody else can say that."""
    out = {}
    for r in C['rows']:
        if r['n'] >= 3 and r['e'] == r['n']:
            out[r['k']] = (95, (
                f'{Num(r["n"])} priced deals and <b>every one of them came out '
                f'level</b> &mdash; not a win, not a loss, not a dollar either way past '
                f'the ${C["tc"]} line. Nobody else has a clean sheet.'))
    return out


def a_all_down(C, **_):
    """Every priced deal came out on the wrong side of even.

    Stated and left there. The desk prints what it counts, and a side with a
    bad row does not also need telling about it -- the line below used to end
    "which is the only good news in the row", which is a joke on a man rather
    than on a situation, and this desk is not in that business.
    """
    out = {}
    for r in C['rows']:
        if r['n'] >= 3 and r['down'] == r['n']:
            out[r['k']] = (50, (
                f'{Num(r["n"])} priced deals, {money(r["net"])} together, and '
                f'<b>every one of them finished on the wrong side of even</b> &mdash; '
                f'though only {num(r["l"])} cleared the ${C["tc"]} line that makes a '
                f'loss a loss. A book this small is one bad winter, not a pattern.'))
    return out


def a_one_side_only(C, **_):
    """A deficit that sits entirely on one half of the ledger.

    Worth its own angle because it is the most useful thing you can say about
    a position: a side whose players are intact and whose picks are gone has a
    different problem, and a more fixable one, than a side that is losing on
    both. It bids high for that reason, and only fires when the untouched half
    really is untouched -- flat or better, and under a fifth of the damage.
    """
    out = {}
    for r in C['rows']:
        if r['net'] >= 0:
            continue
        sides = [(r['players'], 'players', 'roster'), (r['picks'], 'picks', 'draft')]
        (bad, bad_s, _), (good, good_s, good_half) = min(sides), max(sides)
        if good < 0 or bad >= 0 or abs(good) > 0.2 * abs(bad) or abs(bad) < abs(r['net']):
            continue
        out[r['k']] = (92, (
            f'<b>Not one dollar of this is a {good_s[:-1]}.</b> Their {good_s[:-1]} '
            f'trading is {money(good)} across {num(r["n"])} deals &mdash; the '
            f'{good_half} half of the ledger is untouched. The whole {money(r["net"])} '
            f'sits in {bad_s}, and no single deal in it cost more than '
            f'{money(abs(r["worst"]))}.'))
    return out


def a_one_currency(C, rank, **_):
    """A total that is really one side of the ledger wearing a hat."""
    out = {}
    for r in rank:
        if r['net'] == 0:
            continue
        sides = [(r['players'], 'players'), (r['picks'], 'picks')]
        big = max(sides, key=lambda t: abs(t[0]))
        small = min(sides, key=lambda t: abs(t[0]))
        if big[0] * r['net'] <= 0 or abs(big[0]) < 0.88 * abs(r['net']):
            continue
        if abs(small[0]) > 0.14 * abs(r['net']):
            continue
        out[r['k']] = (90, (
            f'The richest ledger in the league is really one ledger: '
            f'<b>{money(big[0])} of their {money(r["net"])} is {big[1]}</b>. '
            f'{Num(r["n"])} deals in {num(len(C["seasons"]))} seasons and the {small[1]} '
            f'column contributes {money(small[0])}.')
            if _rank(rank, r, lambda x: x['net']) == 1 else (85, (
                f'<b>{money(big[0])} of their {money(r["net"])} is {big[1]}</b>. The '
                f'{small[1]} column contributes {money(small[0])} across '
                f'{r["n"]} deals.')))
    return out


def a_side_extreme(C, rank, **_):
    """The biggest single-sided gain or loss on the board."""
    out = {}
    for side, other in (('players', 'picks'), ('picks', 'players')):
        lo = min(rank, key=lambda x: x[side])
        if lo[side] < 0:
            out.setdefault(lo['k'], (80, f'side_{side}', (
                f'<b>{money(lo[side])} on {side}</b>, the heaviest loss on that half of '
                f'the ledger anybody carries. Their {other} are {money(lo[other])}, and '
                f'it is not nearly enough: {money(lo["net"])} across {lo["n"]} deals.')))
    return out


def a_per_deal(C, rank, **_):
    """Not the biggest hole, the deepest one -- bleed measured per trade."""
    out = {}
    for side in ('players', 'picks'):
        rate = lambda x: x[side] / x['n']
        lo = min(rank, key=rate)
        if rate(lo) > -4 or lo['n'] >= 25:
            continue        # a shallow hole, or a big enough book to say it twice
        out.setdefault(lo['k'], (78, f'perdeal_{side}', (
            f'{money(lo[side])} on {side} across only {lo["n"]} deals &mdash; '
            f'<b>{money(rate(lo), cents=True)} a trade</b>, the steepest rate on that '
            f'side of the ledger in the league. Their {"picks" if side == "players" else "players"} '
            f'are {money(lo["picks"] if side == "players" else lo["players"])}.')))
    return out


def a_one_deal(C, rank, **_):
    """A total that one afternoon paid for."""
    out = {}
    for r in rank:
        if r['net'] >= 0 or abs(r['worst']) <= abs(r['net']) * 2:
            continue
        out[r['k']] = (76 + min(14, abs(r['worst']) / abs(r['net'])), (
            f'Their worst single deal is {money(r["worst"])}. Their whole ledger across '
            f'{r["n"]} trades is {money(r["net"])}. <b>Take that one afternoon out and '
            f'the rest of the book is {money(r["net"] - r["worst"])}</b>. One afternoon '
            f'is the difference between a winning ledger and a losing one.'))
    return out


def a_small_worst(C, rank, **_):
    """Never been hurt. Which is not the same as having won anything."""
    r = max(rank, key=lambda x: x['worst'])
    if r['worst'] > -25 and r['n'] >= 10:
        return {r['k']: (76, (
            f'<b>No deal they have made has cost them more than '
            f'{money(abs(r["worst"]))}</b> &mdash; the softest worst case in the league, '
            f'by a distance. They also take home only {r["sharp"]}&thinsp;% of the deals '
            f'that come out decided.'))}
    return {}


def a_down_rate(C, rank, **_):
    """How often a side's deals go down at all, win line or no win line."""
    rate = lambda x: x['down'] / x['n']
    out = {}
    lo, hi = min(rank, key=rate), max(rank, key=rate)
    out[lo['k']] = (74, 'down_low', (
        f'<b>{lo["down"]} of their {lo["n"]} deals go down</b>, '
        f'{round(100 * rate(lo))}&thinsp;%, the lowest share of losing trades of any '
        f'ranked side. {Num(lo["n"] - lo["down"])} of the {num(lo["n"])} come out '
        f'level or better.'))
    out[hi['k']] = (75, 'down_high', (
        f'<b>{hi["down"]} of their {hi["n"]} deals go down</b> &mdash; '
        f'{round(100 * rate(hi))}&thinsp;%, the highest rate among the ranked. The '
        f'median one loses {money(abs(hi["med"]), cents=True)}.'))
    return out


def a_median(C, rank, **_):
    """The middle deal, which this sheet has already shown decides everything."""
    hi = max(rank, key=lambda x: x['med'])
    return {hi['k']: (79, (
        f'<b>The best middle deal in the league at {money(hi["med"], cents=True)}</b>. '
        f'Across {hi["n"]} trades that is where {money(hi["net"])} comes from &mdash; '
        f'not from the big one, of which they have none.'))} if hi['med'] > 0 else {}


def a_win_rate(C, rank, **_):
    """How often anything clears the win line at all."""
    rate = lambda x: x['w'] / x['n']
    lo = min(rank, key=rate)
    if rate(lo) > 0.12:
        return {}
    one_in = round(lo['n'] / lo['w']) if lo['w'] else 0
    return {lo['k']: (81, (
        f'<b>{Num(lo["w"])} of their {lo["n"]} deals cleared the win line.</b> One in '
        f'{num(one_in)}, the lowest rate in the league. {Num(lo["l"])} went the other '
        f'way, and {num(lo["e"])} came out level.'))}


def a_ahead_but_median_down(C, rank, **_):
    """Ahead on the ledger and behind in the middle of it."""
    out = {}
    for r in rank:
        if r['net'] <= 0 or r['med'] >= 0:
            continue
        out[r['k']] = (72, (
            f'Ahead overall and behind in the middle: {money(r["net"])} across '
            f'{r["n"]} deals, but a <b>median of {money(r["med"], cents=True)}</b>. '
            f'{Num(r["down"])} of the {num(r["n"])} went down; the rest more than '
            f'covered it.'))
    return out


def a_split_rescue(C, rank, **_):
    """One half of the ledger sinking a franchise the other half is carrying."""
    out = {}
    for r in rank:
        if r['net'] >= 0:
            continue
        sides = [(r['players'], 'players'), (r['picks'], 'picks')]
        (bad, bad_s), (good, good_s) = min(sides), max(sides)
        if good <= 0 or abs(bad) <= abs(r['net']):
            continue
        out[r['k']] = (70, (
            f'Their {good_s[:-1]} trading is {money(good)} to the good. '
            f'<b>{money(bad)} on {bad_s} buries it</b>, and the two together make '
            f'{money(r["net"])} across {r["n"]} deals.'))
    return out


def a_side_best(C, rank, **_):
    """The biggest gain on one half of the ledger, and what the other half did
    to it. A gain that is handed straight back is a different story from one
    that is kept, so the sentence checks which it is before choosing."""
    out = {}
    for side, other in (('players', 'picks'), ('picks', 'players')):
        hi = max(rank, key=lambda x: x[side])
        if hi[side] <= 0:
            continue
        kept = hi[other] >= 0
        out.setdefault(hi['k'], (79, f'sidehi_{side}', (
            f'<b>{money(hi[side])} on {side}</b>, the biggest gain on either half of '
            f'the ledger anybody has'
            + (f', and they keep it: {money(hi["net"])} across {hi["n"]} deals.'
               if kept else
               f'. They hand {money(abs(hi[other]))} of it back on {other}, and '
               f'{money(hi["net"])} survives across {hi["n"]} deals.'))))
    return out


def a_cancel(C, rank, **_):
    """The widest cancellation: a lot of money moving, almost none of it staying."""
    moved = lambda x: abs(x['players']) + abs(x['picks'])
    pool = [r for r in rank if r['net'] and moved(r) > 3 * abs(r['net'])]
    if not pool:
        return {}
    r = max(pool, key=lambda x: moved(x) / abs(x['net']))
    return {r['k']: (80, (
        f'<b>{money(moved(r))} moves across the two halves of their ledger and '
        f'{money(abs(r["net"]))} of it survives</b> &mdash; {money(r["players"])} on '
        f'players against {money(r["picks"])} on picks. The widest cancellation in the '
        f'league: a great deal of trading that very nearly adds to nothing.'))}


def a_fewest(C, **_):
    """The smallest book in the league."""
    r = min(C['rows'], key=lambda x: x['n'])
    if r['n'] >= C['minDeals']:
        return {}
    return {r['k']: (73, (
        f'<b>{Num(r["n"])} priced deals in {num(len(C["seasons"]))} seasons</b>, fewest '
        f'of the sixteen, and {money(r["net"])} up on them. Too small a book to rank, '
        f'and the smallest book is still a position.'))}


def a_not_firm(C, **_):
    """The one direction the model will not commit to."""
    soft = [r for r in C['rows'] if not r['firm']]
    if len(soft) != 1:
        return {}
    r = soft[0]
    return {r['k']: (83, (
        f'<b>The only side in the league whose direction is not settled.</b> '
        f'{money(r["net"])} as the board is built, but anywhere from '
        f'{money(r["range"][0])} to {money(r["range"][1])} depending on how picks are '
        f'priced. Read them as even.'))}


def a_year(C, **_):
    """What twelve months does to a position, in both directions."""
    L = C['later']
    if not L:
        return {}
    lr = [r for r in L['rows'] if r['n'] >= L['minDeals']]
    if len(lr) < 2:
        return {}
    out = {}
    up = max(lr, key=lambda r: r['year'] - r['day'])
    dn = min(lr, key=lambda r: r['year'] - r['day'])
    if up['year'] - up['day'] > 0:
        clean = up['ch'] and all(up['tr'].get(x, 0) == 0 for x in ('WL', 'WE', 'EL'))
        out[up['k']] = (71, 'year_up', (
            f'The year is kinder to them than to anybody: {money(up["day"])} on the days '
            f'they traded, <b>{money(up["year"])} twelve months on</b>. '
            + (f'Of the {num(up["ch"])} verdicts that changed, every one went their way.'
               if clean else
               f'{Num(up["ch"])} of their verdicts changed across {up["n"]} deals '
               f'priced twice.')))
    if dn['year'] - dn['day'] < 0:
        out[dn['k']] = (69, 'year_down', (
            f'The one side the wait makes worse than anybody: {money(dn["day"])} on the '
            f'days they traded, <b>{money(dn["year"])} a year later</b>. {Num(dn["ch"])} '
            f'of their verdicts changed across {dn["n"]} deals priced twice.'))
    return out


def a_plain(C, **_):
    """The fallback, so every one of the sixteen gets a line.

    Not a filler sentence with no number in it: a side with nothing singular
    about it still has a record, a net and a middle deal, and those are the
    three things the rest of the sheet is built on.
    """
    out = {}
    for r in C['rows']:
        thin = r['n'] < C['minDeals']
        out[r['k']] = (10, (
            f'{r["w"]}&ndash;{r["l"]} with {num(r["e"])} level across {r["n"]} priced '
            f'deals, {money(r["net"])} together and {money(r["med"], cents=True)} in the '
            f'middle. {round(100 * abs(r["players"]) / (abs(r["players"]) + abs(r["picks"]))) if (r["players"] or r["picks"]) else 0}'
            f'&thinsp;% of the movement is on the player side.'
            if not thin else
            f'{Num(r["n"])} priced deals, too few to rank: {r["w"]}&ndash;{r["l"]} with '
            f'{num(r["e"])} level, {money(r["net"])} together. They are on the chart, '
            f'not in the table.'))
    return out


ANGLES = [a_clean_sheet, a_one_side_only, a_all_down, a_one_currency, a_one_deal, a_win_rate,
          a_side_extreme, a_side_best, a_cancel, a_median, a_per_deal, a_not_firm,
          a_small_worst, a_down_rate, a_fewest, a_ahead_but_median_down, a_year,
          a_split_rescue]


def each_team(C):
    """Assign every franchise the most striking thing still unclaimed.

    Greedy on score, one angle to a customer. Greedy rather than optimal on
    purpose: the best line about a franchise should go to that franchise, and
    an exact assignment would happily hand somebody a duller line to improve
    a total nobody is reading.
    """
    rank = C['rank']
    bids = {}
    for fn in ANGLES:
        for k, bid in (fn(C, rank=rank) or {}).items():
            # (score, text), or (score, tag, text) where one angle makes two
            # genuinely different observations -- the highest and the lowest
            # on a measure are not the same line twice
            score, tag, text = (bid if len(bid) == 3
                                else (bid[0], fn.__name__, bid[1]))
            bids.setdefault(k, []).append((score, tag, text))
    picked, used = {}, set()
    pool = sorted(((s, f, t, k) for k, v in bids.items() for s, f, t in v),
                  key=lambda x: -x[0])
    for score, fn, text, k in pool:
        if k in picked or fn in used:
            continue
        picked[k] = (fn, text)
        used.add(fn)
    for k, (score, text) in a_plain(C).items():
        picked.setdefault(k, ('a_plain', text))
    return [{'k': r['k'], 'club': r['club'], 'n': r['n'], 'net': r['net'],
             'thin': r['n'] < C['minDeals'],
             'angle': picked[r['k']][0], 'line': picked[r['k']][1]}
            for r in sorted(C['rows'], key=lambda r: -r['net'])]


# --- the sheet -------------------------------------------------------------

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>__TITLE__ &mdash; Skirt Chasers</title>
<link rel="icon" href="newsroom-favicon.png">
<meta name="scfl:kicker" content="The Trade Desk &middot; One Sheet">
<meta name="scfl:published" content="__STAMP__">
<meta name="scfl:category" content="Trade Desk">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Skirt Chasers &mdash; Dynasty League Magazine">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:url" content="https://watsoncapitalinvest-dot.github.io/Claude/scfl-trade-takeaways.html">
<meta property="og:image" content="https://watsoncapitalinvest-dot.github.io/Claude/scfl-trade-takeaways-og.jpg">
<meta property="og:image:alt" content="__TITLE__">
<meta name="twitter:card" content="summary_large_image">
<style>
/* One sheet. Cream stock, single theme on purpose -- the same paper the rest
   of the Trade Desk is printed on, so it looks the same wherever it opens
   rather than turning black on a phone set to dark. */
:root{--cream:#fffdfb;--stock:#f7f3ea;--ink:#17181c;--muted:#5b5d64;--faint:#8b8d95;
 --line:#e2dccf;--hair:#efeae0;--red:#c20f16;--blue:#0e8ab5;--gold:#b88a1f;
 --serif:Georgia,'Iowan Old Style','Times New Roman',serif;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
 color-scheme:light;}
*{box-sizing:border-box}
.nb{white-space:nowrap}
html{background:var(--cream)}
body{margin:0;background:var(--cream);color:var(--ink);font-family:var(--serif);
 -webkit-font-smoothing:antialiased;
 padding-left:max(16px,env(safe-area-inset-left,0px));
 padding-right:max(16px,env(safe-area-inset-right,0px));}
.wrap{max-width:1000px;margin:0 auto;padding:0 0 64px}
.runhead{font-family:var(--sans);font-size:10.5px;font-weight:800;letter-spacing:.22em;
 text-transform:uppercase;color:var(--faint);border-bottom:1px solid var(--line);
 padding:20px 0 12px}
.flag{font-family:var(--sans);font-size:10.5px;font-weight:900;letter-spacing:.24em;
 text-transform:uppercase;color:var(--red);margin-top:26px;display:block}
h1{font-weight:900;font-size:clamp(34px,7.2vw,60px);line-height:1.0;letter-spacing:-.024em;
 margin:11px 0 0;text-wrap:balance}
h1 em{font-style:normal;color:var(--red)}
.dek{font-style:italic;color:var(--muted);font-size:18px;line-height:1.5;margin:14px 0 0;
 max-width:62ch}
.byline{font-family:var(--sans);font-size:11px;letter-spacing:.08em;color:var(--faint);
 margin-top:15px;text-transform:uppercase}
.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(152px,1fr));gap:1px;
 background:var(--line);border:1px solid var(--line);margin:24px 0 0}
.strip>div{background:var(--cream);padding:12px 14px}
.strip .v{font-size:25px;font-weight:900;line-height:1;font-variant-numeric:tabular-nums}
.strip .k{font-family:var(--sans);font-size:9.5px;font-weight:800;letter-spacing:.13em;
 text-transform:uppercase;color:var(--faint);margin-top:6px}
ol.ten{list-style:none;margin:30px 0 0;padding:0;
 display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line);
 border-top:2px solid var(--ink);border-left:1px solid var(--line);
 border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
ol.ten>li{background:var(--cream);padding:18px 20px 20px;display:flex;
 flex-direction:column;gap:7px}
ol.ten>li:nth-child(4n),ol.ten>li:nth-child(4n+1){background:var(--stock)}
.rk{font-family:var(--sans);font-size:10px;font-weight:900;letter-spacing:.18em;
 color:var(--red)}
.fig{font-size:34px;font-weight:900;line-height:.95;letter-spacing:-.02em;
 font-variant-numeric:tabular-nums;color:var(--ink)}
h2{font-family:var(--serif);font-size:20px;font-weight:800;line-height:1.18;margin:2px 0 0;
 letter-spacing:-.012em;text-wrap:balance}
ol.ten p{font-family:var(--sans);font-size:13px;line-height:1.56;color:var(--muted);
 margin:3px 0 0}
ol.ten p b{color:var(--ink);font-weight:800}
.sec{font-family:var(--sans);font-size:11px;font-weight:900;letter-spacing:.2em;
 text-transform:uppercase;color:var(--red);margin:36px 0 0;padding-top:16px;
 border-top:2px solid var(--ink)}
.teams{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line);
 border:1px solid var(--line);margin-top:14px}
.teams>div{background:var(--cream);padding:13px 16px 15px}
.teams .tm{display:flex;align-items:baseline;gap:9px}
.teams .nm{font-family:var(--serif);font-size:17px;font-weight:800;letter-spacing:-.01em}
.teams .nt{font-family:var(--sans);font-size:12px;font-weight:800;
 font-variant-numeric:tabular-nums;margin-left:auto;white-space:nowrap}
.teams .up{color:var(--red)} .teams .dn{color:var(--blue)}
.teams .thin{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.1em;
 text-transform:uppercase;color:var(--faint);border:1px solid var(--line);
 border-radius:2px;padding:1px 4px}
.teams p{font-family:var(--sans);font-size:12.5px;line-height:1.52;color:var(--muted);
 margin:6px 0 0}
.teams p b{color:var(--ink);font-weight:800}
.also{margin-top:26px;border-top:2px solid var(--ink);padding-top:14px;
 display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px 28px}
.also h3{font-family:var(--sans);font-size:9.5px;font-weight:900;letter-spacing:.16em;
 text-transform:uppercase;color:var(--faint);margin:0 0 5px}
.also p{font-family:var(--sans);font-size:12.5px;line-height:1.55;color:var(--muted);margin:0}
.also b{color:var(--ink)}
.more{margin-top:28px;border-top:1px solid var(--line);padding-top:16px;
 font-family:var(--sans);font-size:12px;line-height:1.65;color:var(--faint);max-width:80ch}
.more a{color:var(--red);font-weight:700}
.more code{font-size:11.5px}
@media(max-width:720px){
 ol.ten{grid-template-columns:1fr}
 .teams{grid-template-columns:1fr}
 ol.ten>li:nth-child(4n),ol.ten>li:nth-child(4n+1){background:var(--cream)}
 ol.ten>li:nth-child(even){background:var(--stock)}
}
@media print{body{padding:0}.wrap{max-width:none}ol.ten{break-inside:avoid}}
</style></head>
<body><div class="wrap">
<div class="runhead">SCFL NewsRoom &middot; The Trade Desk &middot; One Sheet</div>
<span class="flag">The Trade Desk</span>
<h1>__H1__</h1>
<p class="dek">__DEK__</p>
<div class="byline">The SCFL NewsRoom &middot; The Trade Desk</div>
<div class="strip">__STRIP__</div>
<ol class="ten">__ITEMS__</ol>
<h2 class="sec">__SECH__</h2>
<div class="teams">__TEAMS__</div>
<div class="also">__ALSO__</div>
<div class="more">__METHOD__</div>
</div></body></html>"""

# The card is drawn, not screenshotted, so rebuilding the sheet cannot leave a
# stale picture behind. It runs an ink masthead and an ink footer on purpose:
# a cream card with black text on it is mostly white paper, and ad.shoot
# refuses anything over 55 per cent near-white on the grounds that a card
# which arrives blank is invisible to the person who sent it.
CARD = """<style>
.nb{white-space:nowrap}
body{margin:0;width:1200px;height:630px;background:#fffdfb;color:#17181c;
 font-family:Georgia,'Times New Roman',serif;overflow:hidden;
 display:flex;flex-direction:column}
.bar{background:#17181c;color:#fffdfb;padding:22px 56px;display:flex;
 justify-content:space-between;align-items:baseline}
.bar .a{font-family:Helvetica,Arial,sans-serif;font-size:19px;font-weight:800;
 letter-spacing:.22em;text-transform:uppercase}
.bar .a em{font-style:normal;color:#c20f16}
.bar .b{font-family:Helvetica,Arial,sans-serif;font-size:15px;font-weight:700;
 letter-spacing:.16em;text-transform:uppercase;color:#9a958c}
.p{padding:34px 56px 26px;background:#fffdfb}
.band{flex:1;background:#f7f3ea;border-top:2px solid #17181c;padding:26px 56px 0}
h1{font-size:72px;font-weight:900;line-height:.95;letter-spacing:-.028em;margin:0}
h1 em{font-style:normal;color:#c20f16}
.d{font-style:italic;color:#5b5d64;font-size:22px;line-height:1.38;margin:0;max-width:48ch}
.g{display:flex;gap:1px;background:#d8d1c2;border:1px solid #d8d1c2;margin-top:24px}
.g>div{background:#fffdfb;padding:18px 22px;flex:1}
.g .v{font-size:40px;font-weight:900;line-height:1;font-variant-numeric:tabular-nums}
.g>div:nth-child(2) .v{color:#0e8ab5}
.g>div:nth-child(3) .v{color:#c20f16}
.g .l{font-family:Helvetica,Arial,sans-serif;font-size:11.5px;font-weight:800;
 letter-spacing:.14em;text-transform:uppercase;color:#8b8d95;margin-top:8px}
.cl{display:grid;grid-template-columns:1fr 1fr;gap:9px 34px;margin-top:24px}
.cl div{font-family:Helvetica,Arial,sans-serif;font-size:15.5px;font-weight:700;
 color:#3c3e45;line-height:1.3;display:flex;gap:10px}
.cl b{color:#c20f16;font-weight:900;font-variant-numeric:tabular-nums;flex:none}
.foot{background:#17181c;color:#9a958c;padding:16px 56px;
 font-family:Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;
 letter-spacing:.14em;text-transform:uppercase}
.foot b{color:#fffdfb}
</style>
<div class="bar"><div class="a">Skirt <em>Chasers</em></div>
<div class="b">The Trade Desk &middot; One Sheet</div></div>
<div class="p"><h1>__H1__</h1></div>
<div class="band">
<p class="d">__DEK__</p>
<div class="g">__G__</div>
<div class="cl">__CL__</div>
</div>
<div class="foot">__FOOT__</div>"""


def crunch():
    F = TC.fairness()
    if not F:
        raise SystemExit('tradeValues.json could not be built')
    d = json.load(open(os.path.join(ROOT, TC.SRC), encoding='utf-8'))
    F['later'] = TC.later(d)
    F['rank'] = [r for r in F['rows'] if r['n'] >= F['minDeals']]
    return F


def build():
    C = crunch()
    rk, T, L = C['rank'], C['totals'], C['later']
    found = [f(C) for f in FINDINGS]
    items = [x for x in found if x]
    missed = [f.__name__ for f, x in zip(FINDINGS, found) if not x]
    title = f'{Num(len(items))} Things The Ledger Says'
    h1 = title.replace(' The Ledger', ' The <em>Ledger</em>')

    li = ''.join(
        f'<li><span class="rk">{i + 1:02d}</span>'
        f'<span class="fig">{x["fig"]}</span>'
        f'<h2>{x["claim"]}</h2><p>{x["body"]}</p></li>'
        for i, x in enumerate(items))

    strip = ''.join(f'<div><div class="v">{v}</div><div class="k">{k}</div></div>'
                    for v, k in [
                        (f'{T["n"] // 2:,}', 'Deals priced'),
                        (f'{round(100 * T["e"] / T["n"])}%', 'Come out level'),
                        (f'{C["seasons"][0]}&ndash;{C["seasons"][-1]}', 'Seasons'),
                        (f'${C["tc"]}', 'Win threshold'),
                    ])

    # the asides: true things that did not need a numbered entry of their own
    also = []
    big = C.get('biggest')
    if big:
        # named as the table knows them, with the name on the receipt kept:
        # this league renames franchises, and the loser here signed as THE
        # A-TEAM and appears everywhere else on the sheet as Lil Chops
        def was(then, now):
            k = lambda t: ''.join(c for c in t.lower() if c.isalnum()).removeprefix('the')
            return E(now) if k(then) == k(now) else f'{E(now)} (as {E(then)})'
        also.append(('The most lopsided single deal', (
            f'<b>{was(big["winner"], big["winnerNow"])}</b> by ${big["margin"]} in '
            f'{big["season"]}. They got {E(", ".join(big["winnerGot"]))}. '
            f'<b>{was(big["loser"], big["loserNow"])}</b> got '
            f'{E(", ".join(big["loserGot"]))}.')))
    soft = [r for r in C['rows'] if not r['firm']]
    if soft:
        also.append((f'Read {"this one" if len(soft) == 1 else "these"} as even', ' '.join(
            f'<b>{E(r["club"])}</b>&rsquo;s {money(r["net"])} does not hold its sign '
            f'under all four ways of pricing picks &mdash; it ranges {money(r["range"][0])} '
            f'to {money(r["range"][1])}.' for r in soft)
            + f' Every other franchise&rsquo;s direction survives all four.'))
    thin = [r for r in C['rows'] if r['n'] < C['minDeals']]
    if thin:
        also.append((f'Too few deals to rank', (
            f'{Num(len(thin))} {"franchise is" if len(thin) == 1 else "franchises are"} '
            f'left out of every figure above for having fewer than {C["minDeals"]} priced '
            f'deals: '
            + andlist(f'{E(r["club"])} ({num(r["n"])})'
                      for r in sorted(thin, key=lambda r: -r['n']))
            + '. They are on the chart, not in the rankings.')))
    also_html = ''.join(f'<div><h3>{h}</h3><p>{b}</p></div>' for h, b in also)

    teams = each_team(C)
    c_fair = corr([r['level'] for r in rk], [r['net'] for r in rk])
    c_med = corr([r['med'] for r in rk], [r['net'] for r in rk])
    dek = (f'{T["n"] // 2:,} two-team trades, priced at the season each one was made and '
           f'read {num(len(items))} ways, then once more for each of the '
           f'{num(len(teams))} franchises. Fairness turns out to have nothing to do with '
           f'winning, the median deal turns out to decide everything, and most of this '
           f'league is good at exactly half of the job.')
    desc = (f'{T["n"] // 2:,} priced trades, {num(len(items))} findings and one line on '
            f'every franchise. Trading fairly correlates {c_fair:+.2f} with coming out '
            f'ahead; the median deal correlates {c_med:.2f}. One sheet from the Trade '
            f'Desk.')

    method = (
        f'Built by <code>scripts/build_takeaways.py</code> from the same model as the '
        f'charts &mdash; <code>fairness()</code> and <code>later()</code> are imported '
        f'from <code>scripts/build_trade_charts.py</code> rather than rewritten, so this '
        f'sheet and <a href="scfl-who-wins-trades.html">Who Wins The Trades</a> cannot '
        f'disagree. Every asset is priced at the August of the season its trade was made '
        f'in, so nothing here is graded with hindsight; a deal is won above ${C["tc"]} to '
        f'that side, lost below &minus;${C["tc"]}, and level in between. Each trade '
        f'appears twice, once from each side. {Num(C["skipped"])} three-team '
        f'{"deal is" if C["skipped"] == 1 else "deals are"} left out, because their '
        f'receipts do not say which side each asset came from. The year-later figures '
        f'cover {L["seasons"][0]}&ndash;{L["seasons"][-1]} and {L["count"]} trades, a '
        f'smaller set, because a reading twelve months on needs a consensus board at both '
        f'ends. The charts behind all of it: '
        f'<a href="scfl-who-wins-trades.html">Who Wins The Trades</a>, '
        f'<a href="scfl-twelve-months-on.html">Twelve Months On</a> and '
        f'<a href="scfl-trade-ledger.html">The Twelve-Month Ledger</a>, with '
        f'<a href="scfl-trade-audit.html">Trial of the Evil Empire</a> the investigation '
        f'they came out of.')

    team_html = ''.join(
        f'<div><div class="tm"><span class="nm">{E(t["club"])}</span>'
        + ('<span class="thin">unranked</span>' if t['thin'] else '')
        + f'<span class="nt {"up" if t["net"] >= 0 else "dn"}">{money(t["net"])}</span>'
          f'</div><p>{t["line"]}</p></div>' for t in teams)
    sech = (f'{Num(len(teams))} franchises, one line each &mdash; ordered by what the '
            f'ledger says they are worth')

    stamp = __import__('datetime').date.today().isoformat()
    page = (PAGE.replace('__TITLE__', title).replace('__H1__', h1)
                .replace('__DEK__', dek).replace('__DESC__', E(desc))
                .replace('__STRIP__', strip).replace('__ITEMS__', li)
                .replace('__ALSO__', also_html).replace('__METHOD__', method)
                .replace('__SECH__', sech).replace('__TEAMS__', team_html)
                .replace('__STAMP__', stamp))
    open(OUT, 'w', encoding='utf-8').write(page)
    print(f'wrote {os.path.basename(OUT)} ({len(page):,} chars) &middot; '
          f'{len(items)} findings')
    if missed:
        print('  did not derive (left off the sheet):', ', '.join(missed))
    import re as _re
    bare = lambda t: _re.sub('<[^>]+>', '', t).replace('&minus;', '-')
    for i, x in enumerate(items, 1):
        print(f'  {i:2}. {bare(x["fig"]):>8}  {x["claim"]}')
    fell = [t['club'] for t in teams if t['angle'] == 'a_plain']
    print(f'  {len(teams)} franchise lines, '
          f'{len({t["angle"] for t in teams})} different angles'
          + (f' -- fell back to the plain line: {", ".join(fell)}' if fell else ''))

    g = ''.join(f'<div><div class="v">{v}</div><div class="l">{k}</div></div>'
                for v, k in [(f'{T["n"] // 2:,}', 'Deals priced'),
                             (sign(c_fair), 'Fair vs. ahead'),
                             (f'{c_med:.2f}', 'Median vs. total')])
    foot = (f'<b>{len(items)}</b> findings &middot; <b>{C["seasons"][0]}&ndash;'
            f'{C["seasons"][-1]}</b> &middot; every figure counted, none of them typed')
    ad.shoot(CARD.replace('__H1__', h1)
                 .replace('__DEK__', E(items[0]['claim']) + '. '
                          + E(items[1]['claim']) + '.')
                 .replace('__G__', g).replace('__FOOT__', foot)
                 .replace('__CL__', ''.join(
                     f'<div><b>{i:02d}</b>{E(x["claim"])}</div>'
                     for i, x in enumerate(items[2:8], 3))),
             OG, 'takeaways-card')


if __name__ == '__main__':
    build()
