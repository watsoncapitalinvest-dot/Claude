#!/usr/bin/env python3
"""Is everything this desk has made actually saved and actually sendable?

    python3 scripts/check_filed.py

The rule it enforces: if a thing exists in article format, somebody liked it
enough to want it shared. So it has to be three things, not one.

  Saved     -- committed, not sitting untracked in a container that gets
               reclaimed. Pages have been lost this way before.
  Filed     -- in site-index.json, so it is findable from The Full Record and
               from the app rather than only from a chat link that scrolls away.
  Sendable  -- a title, a share blurb, and a share card that exists on disk.
               A page whose og:image points at a file nobody built comes up
               blank in every app it is pasted into, and the sender cannot see
               that from their end.

It is a check, not a fixer: it prints what is wrong and what to run, and exits
non-zero so it can sit in front of a publish. Nothing here writes a file.
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, 'site-index.json')

TITLE = re.compile(r'<title>([^<]*)</title>')
DESC = re.compile(r'og:description"\s+content="([^"]*)"')
IMG = re.compile(r'og:image"\s+content="([^"]*)"')
PUB = re.compile(r'scfl:published"\s+content="([^"]*)"')

# Pages that are deliberately not articles: the app itself, the catalog, and
# the share-card templates that exist to be screenshotted rather than read.
# Kept in step with SKIP/KNOWN_TITLELESS in build_site_index.py on purpose --
# if the two ever disagree, this check is the one that will say so.
NOT_ARTICLES = {'index.html', 'scfl-index.html', 'microfichegate-teaser.html'}


def git(*args):
    return subprocess.run(['git'] + list(args), cwd=ROOT,
                          capture_output=True, text=True).stdout


def main():
    try:
        cat = json.load(open(INDEX, encoding='utf-8'))
    except Exception as e:
        sys.exit(f'cannot read site-index.json ({e}) -- run scripts/build_site_index.py')
    filed = {e['url'] for c in cat['categories'] for e in c['items']}

    # what git thinks is uncommitted, by path
    dirty = {}
    for line in git('status', '--porcelain').splitlines():
        if len(line) > 3:
            dirty[line[3:].strip()] = line[:2].strip()

    pages = sorted(f for f in os.listdir(ROOT)
                   if f.endswith('.html') and os.path.isfile(os.path.join(ROOT, f))
                   and f not in NOT_ARTICLES)
    for sub in ('jeopardy', 'tradewar'):
        p = f'{sub}/index.html'
        if os.path.exists(os.path.join(ROOT, p)):
            pages.append(p)

    unfiled, unsaved, unsendable, undated = [], [], [], []
    for rel in pages:
        text = open(os.path.join(ROOT, rel), encoding='utf-8', errors='replace').read(6000)
        tm = TITLE.search(text)
        if not tm or not tm.group(1).strip():
            continue                      # not an article; build_site_index says so too
        if rel not in filed:
            unfiled.append(rel)
        if rel in dirty:
            unsaved.append((rel, dirty[rel]))
        if not PUB.search(text):
            undated.append(rel)
        why = []
        if not DESC.search(text):
            why.append('no og:description')
        im = IMG.search(text)
        if not im:
            why.append('no og:image')
        else:
            # resolve the card against the page's own folder, not the repo root.
            # Doing it at the root reported jeopardy/og.jpg and tradewar/og.jpg
            # as missing when both have sat beside their pages all along, which
            # is the kind of false alarm that gets a check ignored.
            fn = im.group(1).rsplit('/', 1)[-1]
            folder = os.path.dirname(rel)
            here = os.path.join(ROOT, folder, fn) if folder else os.path.join(ROOT, fn)
            if fn and not fn.startswith('data:') and not os.path.exists(here):
                why.append(f'og:image {os.path.join(folder, fn) if folder else fn} does not exist')
        if why:
            unsendable.append((rel, '; '.join(why)))

    # a note in the store that was never rendered is the other direction of the
    # same mistake: written down, and still not a page anybody can open
    unbuilt = []
    store = os.path.join(ROOT, 'desk-notes.json')
    if os.path.exists(store):
        for n in json.load(open(store, encoding='utf-8'))['notes']:
            if not os.path.exists(os.path.join(ROOT, f'scfl-note-{n["slug"]}.html')):
                unbuilt.append(n['slug'])

    print(f'{len(pages)} pages scanned, {len(filed)} in the catalog')
    bad = 0
    def report(rows, head, fix):
        nonlocal bad
        if not rows:
            return
        bad += len(rows)
        print(f'\n{head}')
        for r in rows:
            print('  ' + (f'{r[0]:42s} {r[1]}' if isinstance(r, tuple) else r))
        print(f'  -> {fix}')

    report(unfiled, 'NOT IN THE CATALOG:', 'python3 scripts/build_site_index.py')
    report(unsaved, 'NOT COMMITTED:', 'git add + commit, then push')
    report(unbuilt, 'IN desk-notes.json BUT NOT BUILT:', 'python3 scripts/build_notes.py')
    report(unsendable, 'WILL NOT SHARE PROPERLY:', 'build the missing card, or fix the meta tag')
    # a missing date only costs the catalog its sort order, so it is said
    # plainly and does not fail the check
    if undated:
        print('\nno scfl:published (catalog falls back to the first commit date):')
        for r in undated:
            print('  ' + r)

    if bad:
        print(f'\n{bad} thing{"" if bad == 1 else "s"} to put right.')
        sys.exit(1)
    print('\nEverything is saved, filed and sendable.')


if __name__ == '__main__':
    main()
