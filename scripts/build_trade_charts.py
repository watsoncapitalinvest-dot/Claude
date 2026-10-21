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
import json, os, re
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

    here = os.path.dirname(os.path.abspath(__file__))
    for name, cfg in PAGES.items():
        tpl = open(os.path.join(here, 'tpl', f'{cfg["tpl"]}.html'),
                   encoding='utf-8').read()
        body = tpl.replace('__DATA__', lines_data if cfg['tpl'] == 'lines' else full_data)
        html = '<!doctype html>\n<html lang="en">\n<head>\n' + head(name, cfg, stamp) \
               + '</head>\n<body>\n' + body + '\n</body>\n</html>\n'
        open(os.path.join(ROOT, name), 'w', encoding='utf-8').write(html)
        c = card(rows, cfg, cfg['og'])
        print(f'  {name}  ({len(html) // 1024}kb)  card {c}')


if __name__ == '__main__':
    build()
