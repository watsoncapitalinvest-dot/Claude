#!/usr/bin/env python3
"""The two twelve-month charts, as pages on the live site.

    python3 scripts/build_trade_charts.py

Writes two articles and their share cards:

    scfl-twelve-months-on.html   the lines chart, on its own, as large as a
                                 page allows -- one row a franchise, from what
                                 its trades were worth the day it made them to
                                 what the same deals were worth a year later.
    scfl-trade-ledger.html       the same chart, plus the scatter, plus every
                                 trade a franchise made listed asset by asset
                                 with both valuations against each one.

They began as private links. They are articles, so they belong on the site
with everything else -- findable from The Full Record, with a share card that
works when the link is pasted.

NOTHING HERE IS ANYBODY'S HAND. Every figure is a completed trade the whole
league watched happen, priced on a public consensus board. There is no
valuation of an unmade deal, no read on who is buying or selling now, and no
assessment of a roster's weak spot. That is the test a page has to pass to go
in this repository (see CLAUDE.md), and these pass it the same way the Trade
Audit does.

Both pages are deliberately single-theme: cream stock, the magazine's own
paper, so they look the same wherever they are opened rather than turning
black on a phone set to dark.

The card is drawn here rather than screenshotted, so rebuilding the pages
cannot leave a stale picture behind. Same red-ahead, blue-behind, same rows,
same order.
"""
import json, os, re, statistics, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://watsoncapitalinvest-dot.github.io/Claude'
SRC = 'trade-oneyear.json'
TC_DEFAULT = 12

PAGES = {
    'scfl-twelve-months-on.html': {
        'tpl': 'lines',
        'title': 'Twelve Months On',
        'kicker': 'The Trade Desk · Twelve Months On',
        'og': 'scfl-twelve-months-on-og.jpg',
        'desc': ("What every franchise's trades were worth the day it made them, and "
                 "what the same deals were worth a year later to the day. One fixed "
                 "clock for all of them."),
    },
    'scfl-who-wins-trades.html': {
        'tpl': 'fair',
        'title': 'Who Wins The Trades',
        'kicker': 'The Trade Desk · Who Wins The Trades',
        'og': 'scfl-who-wins-trades-og.jpg',
        'desc': ("Every priced deal in the dynasty ledger, split three ways for each "
                 "franchise: won, fair, lost. Then the same verdict asked again a year "
                 "later, to see who was still winning it."),
    },
    'scfl-trade-ledger.html': {
        'tpl': 'ledger',
        'title': 'The Twelve-Month Ledger',
        'kicker': 'The Trade Desk · The Twelve-Month Ledger',
        'og': 'scfl-trade-ledger-og.jpg',
        'desc': ("Every trade priced twice -- the day it was made and a year later -- "
                 "then listed franchise by franchise, asset by asset, with both "
                 "valuations against each one."),
    },
}

INK = (23, 24, 28)
PAPER = (255, 253, 251)
STOCK = (247, 243, 234)
UP = (194, 15, 22)
DOWN = (14, 138, 181)
FAINT = (139, 141, 149)
RULE = (226, 220, 207)


def head(name, cfg, stamp):
    """The house <head>: title, kicker, share blurb, card, publish date."""
    t, d = cfg['title'], cfg['desc']
    return (f'<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width,initial-scale=1,'
            f'viewport-fit=cover">\n'
            f'<title>{t} &mdash; Skirt Chasers</title>\n'
            f'<link rel="icon" href="newsroom-favicon.png">\n'
            f'<meta name="scfl:kicker" content="{cfg["kicker"]}">\n'
            f'<meta name="scfl:published" content="{stamp}">\n'
            f'<meta property="og:type" content="article">\n'
            f'<meta property="og:site_name" content="Skirt Chasers '
            f'&mdash; Dynasty League Magazine">\n'
            f'<meta property="og:title" content="{t}">\n'
            f'<meta property="og:description" content="{d}">\n'
            f'<meta property="og:url" content="{SITE}/{name}">\n'
            f'<meta property="og:image" content="{SITE}/{cfg["og"]}">\n'
            f'<meta property="og:image:alt" content="{t}">\n'
            f'<meta name="twitter:card" content="summary_large_image">\n')


def fairness():
    """Every franchise's priced deals split into won, fair and lost.

    The same board the Trade Audit grades on, read for all sixteen rather
    than for one: each deal is priced at the August of the season it was made
    in, a win is a net above the Trade Court's own threshold, a loss below
    minus it, and everything between is fair. A trade appears twice, once from
    each side, because it has two verdicts.

    Three-team deals are left out and counted out loud: their receipts do not
    say which side each asset came from, so no net can be formed without
    guessing.

    tradeValues.json is gitignored and rebuilt on demand, the same way
    build_trade_audit.py does it.
    """
    path = os.path.join(ROOT, 'tradeValues.json')
    if not os.path.exists(path):
        subprocess.run([sys.executable, os.path.join(ROOT, 'scripts',
                                                     'build_trade_values.py')],
                       cwd=ROOT, capture_output=True)
    if not os.path.exists(path):
        return None
    d = json.load(open(path, encoding='utf-8'))
    fr = {f['key']: f['club'] for f in
          json.load(open(os.path.join(ROOT, 'scfl-franchises.json'),
                         encoding='utf-8'))['franchises']}
    # whole seasons only -- the one in progress is a quarter of a season
    cnt = json.load(open(os.path.join(ROOT, 'trade-counts.json'), encoding='utf-8'))
    part = {int(s) for s in (cnt.get('partSeasons') or [])}
    seasons = sorted({t['season'] for t in d['trades']} - part)

    # The pick board is the softest part of the model, so every figure on
    # this page is recomputed under four different assumptions about it and
    # only the ones that survive all four are called firm:
    #
    #   as built      an unslotted future pick is weighted by the owner's last
    #                 finish, so a bad team's first is worth more
    #   flat          that weighting removed entirely -- every unslotted pick
    #                 priced at the flat average of its round
    #   picks +30%    every pick worth thirty per cent more
    #   picks -30%    every pick worth thirty per cent less
    #
    # A franchise whose net keeps its sign under all four is firm. The ends of
    # the table are: Wookie Leaks are last and Pork Chop Express first in every
    # one of them. The middle is not, which is why this page ranks but does not
    # claim the order between neighbours.
    import importlib.util as _u
    _s = _u.spec_from_file_location('tv', os.path.join(ROOT, 'scripts',
                                                       'build_trade_values.py'))
    TV = _u.module_from_spec(_s); sys.modules['tv'] = TV; _s.loader.exec_module(TV)
    R1 = sum(TV.PICK_CHART[x] for x in range(1, 17)) / 16
    R2 = sum(TV.PICK_CHART[x] for x in range(17, 33)) / 16

    def priced(a, season, mode):
        v = a.get('value') or 0
        if a['kind'] != 'pick':
            return v
        if mode == 'flat' and a.get('resolved') == 'expected-value':
            base = R1 if (a.get('round') or 1) == 1 else R2
            return base * (TV.PICK_DECAY ** max(0, (a.get('year') or season) - season))
        return v * (1.3 if mode == 'up' else 0.7 if mode == 'down' else 1)

    tc, per, skipped = 12, {}, 0
    # Where the money actually moves. `assets` on a side is what that side
    # GOT, not what it gave -- trade-ledger.json points the other way and the
    # two have caught this desk twice -- so a franchise's net on players is
    # the players it received less the players the other side received.
    split = {}
    for t in d['trades']:
        if t['season'] in part:
            continue
        if len(t['sides']) != 2:
            skipped += 1
            continue
        a, b = t['sides']
        for me, other in ((a, b), (b, a)):
            per.setdefault(me['franchiseKey'], []).append(me['total'] - other['total'])
            sp = split.setdefault(me['franchiseKey'], {'player': 0.0, 'pick': 0.0})
            for x in me['assets']:
                sp[x['kind']] = sp.get(x['kind'], 0) + (x.get('value') or 0)
            for x in other['assets']:
                sp[x['kind']] = sp.get(x['kind'], 0) - (x.get('value') or 0)
    rows = []
    for k, v in per.items():
        w = sum(1 for x in v if x > tc)
        l = sum(1 for x in v if x < -tc)
        sp = split.get(k, {})
        decided = w + l
        rows.append({'k': k, 'club': fr.get(k, k), 'n': len(v), 'w': w, 'l': l,
                     'level': round(100 * (len(v) - w - l) / len(v)),
                     'sharp': round(100 * w / decided) if decided else None,
                     'decided': decided,
                     'e': len(v) - w - l, 'net': round(sum(v)),
                     'players': round(sp.get('player', 0)),
                     'picks': round(sp.get('pick', 0)),
                     'med': round(statistics.median(v), 1),
                     # the single worst and best deal a side made, and how many
                     # of its deals went down at all. A total can be built out
                     # of one disaster or out of forty small leaks, and the two
                     # are different problems -- these three say which.
                     'worst': round(min(v), 1), 'best': round(max(v), 1),
                     'down': sum(1 for x in v if x < 0)})
    # the same table under each assumption, to see what survives
    alt = {}
    for mode in ('flat', 'up', 'down'):
        acc = {}
        for t in d['trades']:
            if t['season'] in part or len(t['sides']) != 2:
                continue
            x, y = t['sides']
            tx = sum(priced(z, t['season'], mode) for z in x['assets'])
            ty = sum(priced(z, t['season'], mode) for z in y['assets'])
            acc.setdefault(x['franchiseKey'], []).append(tx - ty)
            acc.setdefault(y['franchiseKey'], []).append(ty - tx)
        alt[mode] = {k: round(sum(v)) for k, v in acc.items()}
    for r in rows:
        nets = [r['net']] + [alt[m].get(r['k'], 0) for m in ('flat', 'up', 'down')]
        r['firm'] = all(n > 0 for n in nets) or all(n < 0 for n in nets)
        r['range'] = [min(nets), max(nets)]

    rows.sort(key=lambda r: (-(r['w'] - r['l']), -r['n']))
    MIN = 10
    rank = [r for r in rows if r['n'] >= MIN]
    # The four verdicts the board prints, all of them rates rather than counts
    # so a side with sixty-six deals is not flattered against one with fifteen:
    #
    #   best / worst record   of the deals that did NOT come out level, the
    #                         share that went that side's way. Level deals are
    #                         the draws; this is the win percentage.
    #   most fair             the most deals that came out level
    #   most unfair           the fewest. Its trades land one way or the other
    #                         more often than anybody's, in either direction.
    #
    # The record needs a floor of its own: three-and-one is not a rate.
    DECIDED_MIN = 8
    sharp_pool = [r for r in rank if r['decided'] >= DECIDED_MIN]

    # the single most lopsided deal in the window, named
    big = None
    for t in d['trades']:
        if t['season'] in part or len(t['sides']) != 2:
            continue
        a, b = t['sides']
        n = a['total'] - b['total']
        if big is None or abs(n) > big['margin']:
            wn, ls = (a, b) if n > 0 else (b, a)
            nm = lambda side: [x.get('name') or x.get('raw') for x in side['assets']]
            big = {'season': t['season'], 'margin': round(abs(n)),
                   'winner': wn['team'], 'loser': ls['team'],
                   'winnerGot': nm(wn), 'loserGot': nm(ls)}

    return {'rows': rows, 'tc': tc, 'minDeals': MIN, 'skipped': skipped,
            'decidedMin': DECIDED_MIN,
            'mostUnfair': min(rank, key=lambda r: r['level']),
            'bestRec': (max(sharp_pool, key=lambda r: r['sharp'])
                        if sharp_pool else None),
            'worstRec': (min(sharp_pool, key=lambda r: r['sharp'])
                         if sharp_pool else None),
            'biggest': big,
            'seasons': seasons,
            'totals': {'n': sum(r['n'] for r in rows), 'w': sum(r['w'] for r in rows),
                       'e': sum(r['e'] for r in rows), 'l': sum(r['l'] for r in rows)},
            'fairest': max(rank, key=lambda r: r['e'] / r['n'])}


def later(d):
    """The same verdict asked twice: on the day, and a year later to the day.

    A different window from the page's main chart, on purpose, and the page
    says so. A verdict twelve months on needs a consensus board at both ends
    and the board opens in October 2020, so this is 2020-2024 and the deals
    that can be priced twice, not the whole ledger. The two sets are never
    netted against each other.

    A trade appears twice here as well, once from each side.
    """
    tc = d.get('winThreshold', TC_DEFAULT)
    V = lambda n: 'W' if n > tc else 'L' if n < -tc else 'E'
    fr = {f['key']: f['club'] for f in
          json.load(open(os.path.join(ROOT, 'scfl-franchises.json'),
                         encoding='utf-8'))['franchises']}
    per = {}
    for t in d['trades']:
        for s in t['sides']:
            per.setdefault(s['franchiseKey'], []).append((s['netDay'], s['netYear']))
    rows = []
    for k, v in per.items():
        dv = [V(a) for a, _ in v]
        yv = [V(b) for _, b in v]
        r = {'k': k, 'club': fr.get(k, k), 'n': len(v),
             'dw': dv.count('W'), 'de': dv.count('E'), 'dl': dv.count('L'),
             'yw': yv.count('W'), 'ye': yv.count('E'), 'yl': yv.count('L'),
             'ch': sum(1 for a, b in zip(dv, yv) if a != b),
             'day': round(sum(a for a, _ in v)),
             'year': round(sum(b for _, b in v)),
             # which way the changed verdicts went, so a sentence about them
             # is counted rather than guessed from the totals
             'tr': {a + b: sum(1 for x, y in zip(dv, yv) if x == a and y == b)
                    for a in 'WEL' for b in 'WEL' if a != b}}
        # what the re-check did to the record, and to the money
        r['swing'] = (r['yw'] - r['yl']) - (r['dw'] - r['dl'])
        r['move'] = r['year'] - r['day']
        rows.append(r)
    rows.sort(key=lambda r: (-(r['yw'] - r['yl']), -r['n']))
    MIN = 10
    rank = [r for r in rows if r['n'] >= MIN]
    pool = [r for r in rank if r['yw'] + r['yl'] >= 6]
    rate = lambda r: r['yw'] / (r['yw'] + r['yl'])
    return {'rows': rows, 'tc': tc, 'minDeals': MIN, 'decidedMin': 6,
            'count': d['count'], 'held': d['verdictHeld'],
            'seasons': d['seasons'], 'ecr': d['ecrSpan'],
            'thin': sum(1 for r in rows if r['n'] < MIN),
            'best': max(pool, key=rate) if pool else None,
            'worst': min(pool, key=rate) if pool else None,
            'up': max(rank, key=lambda r: r['swing']) if rank else None,
            'down': min(rank, key=lambda r: r['swing']) if rank else None,
            'totals': {'n': sum(r['n'] for r in rows),
                       'dw': sum(r['dw'] for r in rows), 'de': sum(r['de'] for r in rows),
                       'dl': sum(r['dl'] for r in rows),
                       'yw': sum(r['yw'] for r in rows), 'ye': sum(r['ye'] for r in rows),
                       'yl': sum(r['yl'] for r in rows),
                       'ch': sum(r['ch'] for r in rows)}}


def rows_from(d):
    """One row a franchise: counts, both nets, both records, verdicts changed."""
    tc = d.get('winThreshold', TC_DEFAULT)
    V = lambda n: 'W' if n > tc else 'L' if n < -tc else 'E'
    out = []
    for k, v in d['byFranchise'].items():
        if v['n'] < 10:
            continue
        mine = [(s['netDay'], s['netYear']) for t in d['trades']
                for s in t['sides'] if s['franchiseKey'] == k]
        out.append({
            'k': k, 'club': v['club'], 'n': v['n'],
            'day': round(v['day'], 1), 'year': round(v['year'], 1),
            'tw': sum(1 for a, b in mine if V(a) == 'W'),
            'tl': sum(1 for a, b in mine if V(a) == 'L'),
            'nw': sum(1 for a, b in mine if V(b) == 'W'),
            'nl': sum(1 for a, b in mine if V(b) == 'L'),
            'ch': sum(1 for a, b in mine if V(a) != V(b)),
        })
    out.sort(key=lambda r: -(r['year'] - r['day']))
    return out, tc


def card(rows, cfg, path):
    """A 1200x630 share card: the chart's own shape, drawn not screenshotted."""
    W, H = 1200, 630
    im = Image.new('RGB', (W, H), PAPER)
    dr = ImageDraw.Draw(im)

    def font(sz, bold=False):
        for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSerif%s.ttf',
                  '/usr/share/fonts/truetype/liberation/LiberationSerif-%s.ttf'):
            try:
                return ImageFont.truetype(p % ('-Bold' if bold else ''), sz)
            except OSError:
                pass
        try:
            return ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
                % ('-Bold' if bold else ''), sz)
        except OSError:
            return ImageFont.load_default()

    dr.text((56, 44), 'SKIRT CHASERS  ·  THE TRADE DESK', font=font(17, True), fill=UP)
    dr.text((54, 74), cfg['title'], font=font(52, True), fill=INK)
    dr.line([(56, 150), (W - 56, 150)], fill=INK, width=3)

    vals = [v for r in rows for v in (r['day'], r['year'])]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.08
    x0, x1 = lo - pad, hi + pad
    L, R, T = 300, W - 150, 182
    rowh = (H - T - 56) / len(rows)
    X = lambda v: L + (v - x0) / (x1 - x0) * (R - L)

    dr.line([(X(0), T - 10), (X(0), H - 50)], fill=RULE, width=2)
    for i, r in enumerate(rows):
        y = T + rowh * i + rowh / 2
        c = UP if r['year'] >= r['day'] else DOWN
        if i % 2 == 0:
            dr.rectangle([0, y - rowh / 2, W, y + rowh / 2], fill=STOCK)
        dr.line([(X(r['day']), y), (X(r['year']), y)], fill=c, width=5)
        rr = 8
        dr.ellipse([X(r['day']) - rr, y - rr, X(r['day']) + rr, y + rr],
                   fill=PAPER, outline=FAINT, width=3)
        dr.ellipse([X(r['year']) - rr, y - rr, X(r['year']) + rr, y + rr],
                   fill=c, outline=PAPER, width=3)
        f = font(21, True)
        nm = r['club']
        w = dr.textlength(nm, font=f)
        dr.text((L - 24 - w, y - 13), nm, font=f, fill=INK)
        dv = r['year'] - r['day']
        lab = ('+$' if dv >= 0 else '−$') + f'{abs(round(dv)):,}'
        dr.text((R + 22, y - 12), lab, font=font(20, True), fill=c)
    im.save(os.path.join(ROOT, path), quality=92, optimize=True)
    return path


def card_fair(f, cfg, path):
    """A 1200x630 card: the same stacked bars, drawn rather than screenshotted."""
    W, H = 1200, 630
    im = Image.new('RGB', (W, H), PAPER)
    dr = ImageDraw.Draw(im)

    def font(sz, bold=False):
        for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSerif%s.ttf',
                  '/usr/share/fonts/truetype/liberation/LiberationSerif-%s.ttf'):
            try:
                return ImageFont.truetype(p % ('-Bold' if bold else ''), sz)
            except OSError:
                pass
        try:
            return ImageFont.truetype(
                '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
                % ('-Bold' if bold else ''), sz)
        except OSError:
            return ImageFont.load_default()

    FAIRC = (184, 138, 31)
    dr.text((56, 40), 'SKIRT CHASERS  ·  THE TRADE DESK', font=font(17, True), fill=UP)
    dr.text((54, 70), cfg['title'], font=font(50, True), fill=INK)
    dr.line([(56, 144), (W - 56, 144)], fill=INK, width=3)

    rows = [r for r in f['rows'] if r['n'] >= f['minDeals']]
    L, R, T = 290, W - 210, 176
    rowh = (H - T - 46) / len(rows)
    bh = min(20, rowh * 0.46)
    for i, r in enumerate(rows):
        y = T + rowh * i + rowh / 2
        if i % 2 == 0:
            dr.rectangle([0, y - rowh / 2, W, y + rowh / 2], fill=STOCK)
        x = L
        for v, c in ((r['w'], UP), (r['e'], FAIRC), (r['l'], DOWN)):
            if not v:
                continue
            w = (R - L) * v / r['n']
            dr.rectangle([x, y - bh / 2, x + max(w - 2, 1), y + bh / 2], fill=c)
            x += w
        f1 = font(20, True)
        nm = r['club']
        dr.text((L - 22 - dr.textlength(nm, font=f1), y - 12), nm, font=f1, fill=INK)
        rec = f"{r['w']}\u2013{r['l']}"
        dr.text((R + 20, y - 12), rec, font=font(20, True), fill=INK)
    im.save(os.path.join(ROOT, path), quality=92, optimize=True)
    return path


def build():
    d = json.load(open(os.path.join(ROOT, SRC), encoding='utf-8'))
    rows, tc = rows_from(d)
    stamp = (d.get('builtAt') or '')[:10] or __import__('datetime').date.today().isoformat()

    lines_data = json.dumps({'rows': rows, 'count': d['count'], 'held': d['verdictHeld'],
                             'tc': tc, 'seasons': d['seasons'], 'ecr': d['ecrSpan']},
                            separators=(',', ':'))
    full_data = json.dumps({
        'tc': tc, 'count': d['count'], 'held': d['verdictHeld'],
        'seasons': d['seasons'], 'ecr': d['ecrSpan'],
        'fr': [{'k': r['k'], 'club': r['club'], 'n': r['n'],
                'day': r['day'], 'year': r['year']} for r in rows],
        'tr': [{'s': t['season'], 'd': t['date'], 'o': t['asOf'],
                'S': [{'k': x['franchiseKey'], 't': x['team'],
                       'gd': round(x['gaveDay'], 1), 'gy': round(x['gaveYear'], 1),
                       'nd': round(x['netDay'], 1), 'ny': round(x['netYear'], 1),
                       'a': [{'n': a['asset'], 'd': a['day'], 'y': a['year'],
                              'b': a['became']} for a in x['assets']]}
                      for x in t['sides']]} for t in d['trades']],
    }, separators=(',', ':'))

    fair = fairness()
    if fair:
        # the same page's second question: not who won the deal, but who was
        # still winning it a year later
        fair['later'] = later(d)
    fair_data = json.dumps(fair, separators=(',', ':')) if fair else '{}'
    here = os.path.dirname(os.path.abspath(__file__))
    for name, cfg in PAGES.items():
        if cfg['tpl'] == 'fair' and not fair:
            print(f'  {name}: skipped, tradeValues.json could not be built')
            continue
        tpl = open(os.path.join(here, 'tpl', f'{cfg["tpl"]}.html'),
                   encoding='utf-8').read()
        body = tpl.replace('__DATA__',
                           fair_data if cfg['tpl'] == 'fair' else
                           lines_data if cfg['tpl'] == 'lines' else full_data)
        html = '<!doctype html>\n<html lang="en">\n<head>\n' + head(name, cfg, stamp) \
               + '</head>\n<body>\n' + body + '\n</body>\n</html>\n'
        open(os.path.join(ROOT, name), 'w', encoding='utf-8').write(html)
        c = (card_fair(fair, cfg, cfg['og']) if cfg['tpl'] == 'fair'
             else card(rows, cfg, cfg['og']))
        print(f'  {name}  ({len(html) // 1024}kb)  card {c}')


if __name__ == '__main__':
    build()
