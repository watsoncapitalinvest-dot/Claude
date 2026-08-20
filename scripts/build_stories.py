#!/usr/bin/env python3
"""Build stories.json — the manifest behind the app's Story Vault.

Every standalone page in the repo root is a story unless it opts out. Pages
describe themselves through their own <title>/OG tags plus two optional hints:

    <meta name="scfl:kicker"    content="Investigations · Aug 2026">
    <meta name="scfl:published" content="2026-08-18">
    <meta name="scfl:vault"     content="skip">     <- keep it out of the vault

Anything not supplied is derived: the cover from og:image, the date from the
commit that added the file. Run it by hand or let the Pages workflow do it.
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'stories.json')
ALWAYS_SKIP = {'index.html'}

def meta(html, *, prop=None, name=None):
    attr, val = ('property', prop) if prop else ('name', name)
    m = re.search(r'<meta[^>]+%s=["\']%s["\'][^>]*content=["\']([^"\']*)["\']'
                  % (attr, re.escape(val)), html, re.I)
    if m: return m.group(1).strip()
    m = re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*%s=["\']%s["\']'
                  % (attr, re.escape(val)), html, re.I)
    return m.group(1).strip() if m else ''

def unescape(t):
    for a, b in [('&mdash;', '—'), ('&ndash;', '–'), ('&amp;', '&'),
                 ('&rsquo;', '’'), ('&lsquo;', '‘'), ('&hellip;', '…'),
                 ('&middot;', '·'), ('&quot;', '"'), ('&#39;', "'")]:
        t = t.replace(a, b)
    return t.strip()

def added_date(path):
    """Publication date = the commit that first added the file."""
    for args in (['git', 'log', '--diff-filter=A', '--follow', '--format=%aI', '-1', '--', path],
                 ['git', 'log', '--format=%aI', '-1', '--', path]):
        try:
            out = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=20)
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip().split('T')[0]
        except Exception:
            pass
    return ''

def title_of(html, fname):
    t = meta(html, prop='og:title')
    if not t:
        m = re.search(r'<title>(.*?)</title>', html, re.S | re.I)
        t = m.group(1) if m else fname.replace('.html', '').replace('-', ' ').title()
    t = unescape(re.sub(r'\s+', ' ', t))
    # drop a trailing publication tag: "Headline — SCFL Investigations"
    return re.sub(r'\s+[—–-]\s+(SCFL|Skirt Chasers)\b.*$', '', t).strip() or t

def build():
    stories = []
    for fname in sorted(os.listdir(ROOT)):
        if not fname.endswith('.html') or fname in ALWAYS_SKIP:
            continue
        html = open(os.path.join(ROOT, fname), encoding='utf-8', errors='replace').read()
        head = html[:html.lower().find('</head>') + 7] if '</head>' in html.lower() else html[:8000]
        if meta(head, name='scfl:vault').lower() == 'skip':
            print('  skip  ', fname); continue
        cover = meta(head, prop='og:image').rsplit('/', 1)[-1] or 'newsroom-og.jpg'
        if not os.path.exists(os.path.join(ROOT, cover)):
            cover = 'newsroom-og.jpg'
        stories.append({
            'file': fname,
            'title': title_of(head, fname),
            'cover': cover,
            'kicker': unescape(meta(head, name='scfl:kicker')) or 'The SCFL NewsRoom',
            'blurb': unescape(meta(head, prop='og:description'))[:180],
            'date': meta(head, name='scfl:published') or added_date(fname),
        })
    stories.sort(key=lambda s: (s['date'] or '0000-00-00', s['file']), reverse=True)
    payload = {'builtBy': 'scripts/build_stories.py', 'count': len(stories), 'stories': stories}
    tmp = OUT + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    os.replace(tmp, OUT)
    return stories

if __name__ == '__main__':
    st = build()
    for s in st:
        print(f"  {s['date'] or '----------'}  {s['file']:38s} {s['kicker'][:26]:28s} {s['title'][:44]}")
    print(f"\nwrote stories.json — {len(st)} stories")
    if '--check' in sys.argv:
        changed = subprocess.run(['git', 'diff', '--quiet', '--', 'stories.json'], cwd=ROOT).returncode
        sys.exit(1 if changed else 0)
