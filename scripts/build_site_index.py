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
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'site-index.json')

# Pages that exist to be screenshotted (share cards, teasers) rather than
# read, or that aren't part of the catalog for another explicit reason.
SKIP = {'index.html', 'manifest.json'}

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


if __name__ == '__main__':
    build()
