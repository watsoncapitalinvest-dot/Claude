#!/usr/bin/env python3
"""Desk Notes -- the short pieces, saved as articles instead of as chat.

    python3 scripts/build_notes.py              # every note
    python3 scripts/build_notes.py pick-value    # just one

Most of what this desk works out never becomes an issue. Somebody asks what a
second-round pick is actually worth, or whether a waiver tight end is real, and
the answer gets written out once, read once, and then scrolls off the top of a
chat window. A week later nobody can find it, and the next time the question
comes round the work is done again from scratch.

So: desk-notes.json is the store, and every note in it is rendered here as a
real page in the house style -- kicker, headline, dek, byline, the same cream
and red as the magazine -- which puts it in the catalog
(scripts/build_site_index.py) and in the app's Desk Notes view alongside
everything else the desk has published.

Each note declares its own category in the JSON, and that category is written
into the page as a scfl:category meta tag. The catalog reads the tag off the
page rather than keeping a second list, so the catalog cannot disagree with the
note about which desk it came from -- the same rule the blurbs already follow.

Copy in desk-notes.json is trusted: it is hand-authored and committed, so
inline <b>, <em> and entities pass through to the page as written. Figures do
not. Anything numeric in a note is expected to have been checked against the
repo's own data before it was written down, and the note's "sources" list is
where it says against what.
"""
import importlib.util, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts', 'build_addendum.py'))
ad = importlib.util.module_from_spec(_s); sys.modules['ad'] = ad; _s.loader.exec_module(ad)
E = ad.esc
STORE = os.path.join(ROOT, 'desk-notes.json')
SITE = 'https://watsoncapitalinvest-dot.github.io/Claude/'

MONTH = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May',
         '06': 'June', '07': 'July', '08': 'August', '09': 'September', '10': 'October',
         '11': 'November', '12': 'December'}


def when(date):
    """2026-10-12 -> October 2026, for the kicker and the runhead."""
    try:
        y, m, _ = date.split('-')
        return f'{MONTH[m]} {y}'
    except Exception:
        return date or ''


# ---- blocks ---------------------------------------------------------------
# A note is a list of these. Nothing here is clever on purpose: the point of a
# note is that writing one costs a paragraph of JSON, not a new builder.

def blk(b):
    t = b.get('t', 'p')
    if t == 'p':
        return f'<p class="b">{b["x"]}</p>'
    if t == 'sect':
        return f'<div class="sect">{b["x"]}</div>'
    if t == 'pull':
        return f'<div class="pull">{b["x"]}</div>'
    if t == 'ul':
        return '<ul class="bul">' + ''.join(f'<li>{x}</li>' for x in b['x']) + '</ul>'
    if t == 'stats':
        return ('<div class="stats">' + ''.join(
            f'<div class="stat"><div class="k">{s["k"]}</div><div class="v">{s["v"]}</div>'
            + (f'<div class="n">{s["n"]}</div>' if s.get('n') else '')
            + '</div>' for s in b['x']) + '</div>')
    if t == 'box':
        body = ''.join(f'<p>{x}</p>' for x in b['x'])
        return (f'<div class="live"><div class="lk">{b.get("k", "Note")}</div>{body}</div>')
    if t == 'table':
        lt = set(b.get('lt') or [0])
        head = ''.join('<th' + (' class="lt"' if i in lt else '') + f'>{h}</th>'
                       for i, h in enumerate(b['head']))
        rows = ''
        for r in b['rows']:
            cells = ''
            for i, c in enumerate(r):
                if i == 0:
                    cells += f'<th scope="row">{c}</th>'
                else:
                    cells += f'<td class="{"lt" if i in lt else "num dim"}">{c}</td>'
            rows += f'<tr>{cells}</tr>'
        cap = f'<figcaption>{b["cap"]}</figcaption>' if b.get('cap') else ''
        return (f'<figure><div class="scroll"><table><thead><tr>{head}</tr></thead>'
                f'<tbody>{rows}</tbody></table></div>{cap}</figure>')
    sys.exit(f'unknown block type {t!r} in desk-notes.json')


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>__TITLE__ &mdash; SCFL NewsRoom</title>
<meta name="scfl:kicker" content="__KICKER__">
<meta name="scfl:published" content="__DATE__">
<meta name="scfl:category" content="__CAT__">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SCFL NewsRoom">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:image" content="__SITE____SLUG__-og.jpg">
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
h1{font-weight:900;font-size:clamp(32px,6.4vw,50px);line-height:1.03;letter-spacing:-.022em;
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
ul.bul{margin:0 0 18px;padding-left:20px;max-width:62ch;}
ul.bul li{margin:0 0 8px;}
.stats{display:flex;flex-wrap:wrap;gap:24px 38px;margin:0 0 28px;padding-bottom:22px;
 border-bottom:1px solid var(--line);}
.stat .k{font-family:var(--sans);font-size:9.5px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.stat .v{font-size:30px;font-weight:900;line-height:1.15;font-variant-numeric:tabular-nums;}
.stat .n{font-family:var(--sans);font-size:11px;color:var(--muted);}
.pull{margin:30px 0;padding:0 0 0 20px;border-left:3px solid var(--red);font-size:21px;
 line-height:1.42;font-weight:700;max-width:46ch;letter-spacing:-.01em;}
figure{margin:0 0 28px;}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;}
table{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:13.5px;}
th,td{padding:7px 10px 7px 0;text-align:right;white-space:nowrap;vertical-align:baseline;}
thead th{font-size:9.5px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;
 color:var(--faint);border-bottom:1px solid var(--line);}
th.lt,td.lt,tbody th{text-align:left;white-space:normal;}
tbody th{font-weight:700;}
tbody tr+tr th,tbody tr+tr td{border-top:1px solid #f0ece3;}
td.num{font-variant-numeric:tabular-nums;}
td.dim{color:var(--muted);}
.dim{color:var(--faint);font-weight:400;}
tbody th .dim{font-family:var(--sans);font-size:10.5px;font-weight:700;letter-spacing:.08em;
 margin-left:5px;}
figcaption{font-family:var(--sans);font-size:11.5px;color:var(--muted);margin-top:9px;
 padding-top:8px;border-top:1px solid var(--line);max-width:70ch;}
.live{border:2px solid var(--red);border-radius:3px;padding:16px 18px;margin:0 0 28px;
 background:#fdf4f2;}
.live .lk{font-family:var(--sans);font-size:9.5px;font-weight:900;letter-spacing:.2em;
 text-transform:uppercase;color:var(--red);margin-bottom:8px;}
.live p{margin:0 0 10px;font-size:16px;line-height:1.55;max-width:62ch;}
.live p:last-child{margin-bottom:0;}
.more{margin-top:46px;border-top:1px solid var(--line);padding-top:18px;font-family:var(--sans);
 font-size:12.5px;line-height:1.6;color:var(--muted);max-width:74ch;}
.more a{color:var(--red);font-weight:700;}
.more b{color:var(--ink);}
</style></head>
<body><div class="wrap">
<div class="runhead">SCFL NewsRoom &middot; __FLAG__ &middot; __WHEN__</div>
<span class="flag">__FLAG__</span>
<h1>__HEAD__</h1>
<p class="dek">__DEK__</p>
<div class="byline">__BYLINE__</div>
<div class="rule"></div>
__BODY__
<div class="more">__MORE__</div>
</div></body></html>
"""

CARD = """<style>
:root{--red:#c20f16;--ink:#17181c;--faint:#9a958c;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;margin:0;}
html,body{width:1200px;height:630px;overflow:hidden;background:#efe9de;
 font-family:Georgia,'Times New Roman',serif;color:var(--ink);}
.card{position:relative;width:1200px;height:630px;overflow:hidden;background:#efe9de;
 border-top:9px solid var(--red);border-bottom:9px solid var(--red);
 padding:54px 64px 46px;display:flex;flex-direction:column;}
.flag{font-family:var(--sans);font-size:11.5px;font-weight:900;letter-spacing:.22em;
 text-transform:uppercase;color:var(--red);}
h1{font-size:__FS__px;line-height:1;letter-spacing:-.026em;font-weight:900;margin-top:18px;
 max-width:20ch;}
h1 em{font-style:normal;color:var(--red);}
.rule{width:64px;height:3px;background:var(--red);margin:24px 0 20px;}
.dek{font-style:italic;color:#4b4b52;font-size:21px;line-height:1.38;max-width:44ch;}
.ft{margin-top:auto;display:flex;align-items:flex-end;justify-content:space-between;gap:30px;
 font-family:var(--sans);}
.ft .l{font-size:12px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;
 color:var(--faint);}
.ft .st{display:flex;gap:30px;text-align:right;}
.ft .k{font-size:9.5px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;
 color:var(--faint);}
.ft .v{font-family:Georgia,serif;font-size:30px;font-weight:900;line-height:1.1;
 font-variant-numeric:tabular-nums;}
</style>
<div class="card">
 <div class="flag">__FLAG__</div>
 <h1>__HEAD__</h1>
 <div class="rule"></div>
 <div class="dek">__DEK__</div>
 <div class="ft"><div class="l">SCFL NewsRoom &middot; Desk Notes</div>
  <div class="st">__STATS__</div></div>
</div>"""


def card(n, out):
    """A share card, because a note that is sent is a note that is read.

    The headline sets at 68px and steps down for a long one: a note's title is
    a sentence more often than a magazine headline is, and at a fixed size the
    long ones ran off the bottom of the card.
    """
    head = n['headline']
    plain = re.sub(r'<[^>]+>', '', head)
    fs = 68 if len(plain) <= 26 else 58 if len(plain) <= 40 else 48
    st = ''.join(f'<div><div class="k">{s["k"]}</div><div class="v">{s["v"]}</div></div>'
                 for s in (n.get('cardstats') or [])[:2])
    doc = (CARD.replace('__FS__', str(fs)).replace('__FLAG__', n['flag'])
               .replace('__HEAD__', head).replace('__DEK__', n['dek'])
               .replace('__STATS__', st))
    ad.shoot(doc, out, 'note-card')


def build_one(n, make_card=True):
    slug = n['slug']
    out = os.path.join(ROOT, f'scfl-note-{slug}.html')
    body = '\n'.join(blk(b) for b in n['body'])
    src = n.get('sources') or []
    more = (f'<b>How this was worked out.</b> ' + n.get('method', '')
            + (('<br>Checked against: ' + ' &middot; '.join(f'<code>{E(s)}</code>' for s in src))
               if src else '')
            + '<br>A desk note: short, dated, and kept because the question will be asked again. '
            + 'Rebuilt by <code>scripts/build_notes.py</code> from <code>desk-notes.json</code>.')
    html = (PAGE.replace('__TITLE__', E(re.sub(r'<[^>]+>', '', n['headline'])))
                .replace('__KICKER__', E(f'{n["flag"]} &middot; {when(n["date"])}'))
                .replace('__CAT__', E(n['category']))
                .replace('__DATE__', n['date'])
                .replace('__DESC__', E(re.sub(r'<[^>]+>', '', n['dek'])))
                .replace('__SITE__', SITE)
                .replace('__SLUG__', f'scfl-note-{slug}')
                .replace('__FLAG__', n['flag'])
                .replace('__WHEN__', when(n['date']))
                .replace('__HEAD__', n['headline'])
                .replace('__DEK__', n['dek'])
                .replace('__BYLINE__', n.get('byline', 'The SCFL NewsRoom'))
                .replace('__BODY__', body)
                .replace('__MORE__', more))
    open(out, 'w', encoding='utf-8').write(html)
    print(f'  wrote scfl-note-{slug}.html ({len(html):,} chars, {len(n["body"])} blocks)')
    og = os.path.join(ROOT, f'scfl-note-{slug}-og.jpg')
    if make_card and not os.path.exists(og):
        try:
            card(n, og)
        except SystemExit as e:
            print(f'  ! card for {slug}: {e}')


def main():
    want = set(sys.argv[1:])
    d = json.load(open(STORE, encoding='utf-8'))
    notes = [n for n in d['notes'] if not want or n['slug'] in want]
    if want and not notes:
        sys.exit('no note with that slug -- have: '
                 + ', '.join(n['slug'] for n in d['notes']))
    for n in sorted(notes, key=lambda n: n['date'], reverse=True):
        build_one(n)
    print(f'{len(notes)} note{"" if len(notes) == 1 else "s"} built')


if __name__ == '__main__':
    main()
