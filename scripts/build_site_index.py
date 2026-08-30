#!/usr/bin/env python3
"""The Full Record -- a single catalog of every standalone page this desk has
shipped, so nothing is only findable by scrolling back through chat links.

    python3 scripts/build_site_index.py

Scans the repo root (plus the two arcade subfolders) for HTML pages that carry
a real <title> -- pages without one are share-card/teaser templates meant to
be screenshotted, not read, and are skipped on purpose. Each entry's blurb
comes straight from that page's own og:description, so the catalog can't say
something different from the page itself.

A page's date is its scfl:published meta tag when it has one; otherwise this
falls back to the date the file was first committed (git log), which is the
best available record for everything shipped before that tag existed.

Category is the one thing this script cannot infer honestly, so it's a
hand-maintained map below. Any HTML page with a <title> that isn't in
CATEGORY or SKIP fails the build -- the map is the checklist that keeps this
catalog from going stale the way the chat links did.

Writes site-index.json (categories -> entries). The standalone page
scfl-index.html and the in-app "The Full Record" view (index.html,
showSiteIndex()) both render this same file, so they can't disagree either.
"""
import datetime, importlib.util, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'site-index.json')
OG = os.path.join(ROOT, 'scfl-index-og.jpg')

_spec = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts', 'build_addendum.py'))
ad = importlib.util.module_from_spec(_spec)
sys.modules['ad'] = ad
_spec.loader.exec_module(ad)

# Pages that exist to be screenshotted (share cards, teasers) rather than
# read, or that aren't part of the catalog for another explicit reason.
SKIP = {'index.html', 'manifest.json', 'scfl-index.html'}  # scfl-index.html IS the catalog

CATEGORY = {
    # Heat & Rivalries
    'scfl-heat.html': 'Heat & Rivalries',
    'scfl-addendum.html': 'Heat & Rivalries',
    'scfl-gumbas.html': 'Heat & Rivalries',
    'scfl-offseason-heat.html': 'Heat & Rivalries',
    'scfl-grudge-report.html': 'Heat & Rivalries',
    # Investigations & Research
    'death-by-inaction.html': 'Investigations & Research',
    'scfl-wookie-curse.html': 'Investigations & Research',
    'scfl-shield-decoded.html': 'Investigations & Research',
    'scfl-magazine-oldest-dynasty.html': 'Investigations & Research',
    'scfl-research-oldest-dynasty.html': 'Investigations & Research',
    'scfl-research-champions-playoffs.html': 'Investigations & Research',
    'scfl-timeline-oldest-dynasty.html': 'Investigations & Research',
    # Trade Desk
    'scfl-jcm-trade-review.html': 'Trade Desk',
    'scfl-trade-court-godwin.html': 'Trade Desk',
    'trade-value-report.html': 'Trade Desk',
    # Season Coverage & Issues
    'scfl-kickoff-2026.html': 'Season Coverage & Issues',
    'draft-issue.html': 'Season Coverage & Issues',
    'scfl-post-draft-issue.html': 'Season Coverage & Issues',
    'scfl-2026-draft-grades-flip.html': 'Season Coverage & Issues',
    'scfl-2026-schedule.html': 'Season Coverage & Issues',
    'scfl-sportscenter.html': 'Season Coverage & Issues',
    'scfl-politics-wire-freeze-flip.html': 'Season Coverage & Issues',
    # Tools & Arcade
    'broadcast-demo.html': 'Tools & Arcade',
    'jeopardy/index.html': 'Tools & Arcade',
    'tradewar/index.html': 'Tools & Arcade',
}
# Manual explanation for why a page has no <title> (checked, not just assumed).
KNOWN_TITLELESS = {'microfichegate-teaser.html'}

TITLE = re.compile(r'<title>([^<]*)</title>')
DESC = re.compile(r'og:description"\s+content="([^"]*)"')
PUB = re.compile(r'scfl:published"\s+content="([^"]*)"')
KICKER = re.compile(r'scfl:kicker"\s+content="([^"]*)"')


def unescape(s):
    return (s.replace('&mdash;', '—').replace('&ndash;', '–')
             .replace('&rsquo;', '’').replace('&lsquo;', '‘')
             .replace('&ldquo;', '“').replace('&rdquo;', '”')
             .replace('&amp;', '&').replace('&#39;', '’'))


def git_add_date(relpath):
    try:
        out = subprocess.run(['git', 'log', '--diff-filter=A', '--follow',
                              '--format=%ad', '--date=short', '--', relpath],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        lines = [l for l in out.splitlines() if l]
        return lines[-1] if lines else None
    except Exception:
        return None


def candidates():
    for name in sorted(os.listdir(ROOT)):
        if name.endswith('.html') and os.path.isfile(os.path.join(ROOT, name)):
            yield name
    for sub in ('jeopardy', 'tradewar'):
        p = os.path.join(sub, 'index.html')
        if os.path.exists(os.path.join(ROOT, p)):
            yield p


def build():
    entries = []
    missing_category = []
    for rel in candidates():
        if rel in SKIP:
            continue
        text = open(os.path.join(ROOT, rel), encoding='utf-8', errors='replace').read(6000)
        tm = TITLE.search(text)
        if not tm or not tm.group(1).strip():
            if rel not in KNOWN_TITLELESS:
                print(f'  note: {rel} has no <title> and is not in KNOWN_TITLELESS -- skipped, check it')
            continue
        cat = CATEGORY.get(rel)
        if not cat:
            missing_category.append(rel)
            continue
        dm, pm, km = DESC.search(text), PUB.search(text), KICKER.search(text)
        date = pm.group(1) if pm else git_add_date(rel)
        entries.append({
            'title': unescape(tm.group(1).strip()),
            'desc': unescape(dm.group(1).strip()) if dm else '',
            'kicker': unescape(km.group(1).strip()) if km else '',
            'url': rel,
            'date': date,
            'category': cat,
        })

    if missing_category:
        sys.exit('refusing to write: no CATEGORY entry for ' + ', '.join(missing_category) +
                  ' -- add it to scripts/build_site_index.py')

    order = ['Season Coverage & Issues', 'Heat & Rivalries', 'Investigations & Research',
             'Trade Desk', 'Tools & Arcade']
    by_cat = {c: [] for c in order}
    for e in entries:
        by_cat[e['category']].append(e)
    for c in by_cat:
        by_cat[c].sort(key=lambda e: e['date'] or '', reverse=True)

    payload = {
        'note': 'built by scripts/build_site_index.py -- every standalone page with a <title>',
        'categories': [{'name': c, 'items': by_cat[c]} for c in order if by_cat[c]],
    }
    json.dump(payload, open(OUT, 'w'), indent=1)
    print(f'wrote {os.path.basename(OUT)} | {len(entries)} pages across {len(payload["categories"])} categories')
    for c in payload['categories']:
        print(f'  {c["name"]}: {len(c["items"])}')

    card(payload, entries)


CARD = """<style>
:root{--red:#c20f16;--ink:#17181c;--faint:#9a958c;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;margin:0;}
html,body{width:1200px;height:630px;overflow:hidden;background:#efe9de;
 font-family:Georgia,'Times New Roman',serif;color:var(--ink);}
.card{position:relative;width:1200px;height:630px;overflow:hidden;background:#efe9de;
 border-top:9px solid var(--red);border-bottom:9px solid var(--red);}
.pc{position:absolute;background:#fffdfb;border:1px solid #ded7ca;padding:14px 16px;
 overflow:hidden;box-shadow:0 10px 26px rgba(0,0,0,.17),0 2px 5px rgba(0,0,0,.09);}
.pc .cap{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.15em;
 text-transform:uppercase;color:var(--red);margin-bottom:10px;}
.p1{left:440px;top:78px;width:330px;transform:rotate(-1.6deg);}
.p2{left:790px;top:150px;width:360px;transform:rotate(1.4deg);}
table.cats{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:12px;}
table.cats td{padding:5px 0;vertical-align:middle;}
table.cats th{text-align:left;font-weight:700;white-space:nowrap;padding-right:10px;}
table.cats tr+tr td,table.cats tr+tr th{border-top:1px solid #eee7db;}
.cats .bar span{display:block;height:9px;background:var(--red);border-radius:0 2px 2px 0;min-width:3px;}
.cats .bar{width:100px;}
.cats .num{text-align:right;font-variant-numeric:tabular-nums;color:var(--faint);padding-left:8px;}
ul.recent{list-style:none;font-family:var(--sans);}
ul.recent li{padding:8px 0;border-top:1px solid #eee7db;}
ul.recent li:first-child{border-top:0;}
ul.recent .k{display:block;font-size:8.5px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;
 color:var(--red);}
ul.recent .t{display:block;font-size:13px;font-weight:700;line-height:1.3;margin-top:2px;}
.l{position:absolute;left:0;top:0;bottom:0;width:420px;z-index:9;
 padding:56px 30px 44px 52px;display:flex;flex-direction:column;
 background:linear-gradient(90deg,#efe9de 0%,#efe9de 72%,rgba(239,233,222,.94) 87%,
 rgba(239,233,222,0) 100%);}
.flag{font-family:var(--sans);font-size:11.5px;font-weight:900;letter-spacing:.22em;
 text-transform:uppercase;color:var(--red);}
h1{font-size:56px;line-height:.98;letter-spacing:-.026em;font-weight:900;margin-top:16px;}
h1 em{font-style:normal;color:var(--red);}
.rule{width:64px;height:3px;background:var(--red);margin:22px 0 18px;}
.dek{font-style:italic;color:#4b4b52;font-size:16px;line-height:1.4;max-width:24ch;}
.st{margin-top:auto;display:flex;gap:28px;}
.st .k{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.st .v{font-size:30px;font-weight:900;line-height:1.1;font-variant-numeric:tabular-nums;}
</style>
<div class="card">
 <div class="pc p1"><div class="cap">Every category</div>__CATS__</div>
 <div class="pc p2"><div class="cap">Recently published</div>__RECENT__</div>
 <div class="l">
  <div class="flag">The Record Room</div>
  <h1>The Full<br><em>Record</em></h1>
  <div class="rule"></div>
  <div class="dek">Every page this desk has published, in one place.</div>
  <div class="st">
   <div><div class="k">Pages</div><div class="v">__NP__</div></div>
   <div><div class="k">Categories</div><div class="v">__NC__</div></div>
  </div>
 </div>
</div>"""


def card(payload, entries):
    cats = payload['categories']
    cmax = max(len(c['items']) for c in cats)
    crows = ''.join(
        f'<tr><th>{ad.esc(c["name"])}</th>'
        f'<td class="bar"><span style="width:{100*len(c["items"])/cmax:.0f}%"></span></td>'
        f'<td class="num">{len(c["items"])}</td></tr>' for c in cats)
    cats_html = f'<table class="cats"><tbody>{crows}</tbody></table>'

    dated = sorted((e for e in entries if e['date']), key=lambda e: e['date'], reverse=True)[:4]
    recent_html = '<ul class="recent">' + ''.join(
        f'<li><span class="k">{ad.esc(e["category"])}</span><span class="t">{ad.esc(e["title"])}</span></li>'
        for e in dated) + '</ul>'

    doc = (CARD.replace('__CATS__', cats_html).replace('__RECENT__', recent_html)
               .replace('__NP__', str(len(entries))).replace('__NC__', str(len(cats))))
    ad.shoot(doc, OG, 'site-index-card')


if __name__ == '__main__':
    build()
