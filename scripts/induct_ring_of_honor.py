#!/usr/bin/env python3
"""Close out a year's SCFL Ring of Honor ballot.

Run this by hand once the league has actually decided who's going in —
this script doesn't decide anything itself, it just records the call and
retires those candidates from the open ballot so next year starts clean.
Per the league's own house rule from the chat (Feb 2025): vote in two most
years, sometimes a bonus third, sometimes just one when someone needs to be
snubbed. There's no vote-count auto-cutoff here on purpose — turnout on an
ntfy-backed, no-login board is not a reliable enough signal to induct on by
itself. A human reads the board and decides.

Usage:
  python3 scripts/induct_ring_of_honor.py --year 2026 a-jameis-winston a-derrick-lewis
  python3 scripts/induct_ring_of_honor.py --year 2026 a-jameis-winston --note "the inaugural class"
  python3 scripts/induct_ring_of_honor.py --list        # show current vote tallies to decide from
"""
import argparse, json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES = os.path.join(ROOT, 'ring-of-honor.json')
INDUCTED = os.path.join(ROOT, 'ring-of-honor-inducted.json')
BOOK = os.path.join(ROOT, 'ring-of-honor-votes.json')
TOPIC = 'scfl-ringofhonor-d2748099'


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def all_candidates():
    data = load(CANDIDATES)
    return {c['id']: c for c in data['people'] + data['athletes']}


def vote_counts():
    book = load(BOOK) if os.path.exists(BOOK) else {'entries': []}
    entries = list(book.get('entries', []))
    try:
        req = urllib.request.Request(
            f'https://ntfy.sh/{TOPIC}/json?poll=1&since=all', headers={'User-Agent': 'scfl-induct'})
        with urllib.request.urlopen(req, timeout=15) as r:
            for line in r.read().decode('utf-8', 'replace').splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    env = json.loads(line)
                    if env.get('event') == 'message' and env.get('message'):
                        row = json.loads(env['message'])
                        if isinstance(row, dict) and row.get('id'):
                            entries.append(row)
                except Exception:
                    pass
    except Exception as e:
        print(f'  (could not reach the live wire: {e} — using the last harvested book only)')
    seen, merged = set(), []
    for e in entries:
        if e.get('id') and e['id'] not in seen:
            seen.add(e['id']); merged.append(e)
    counts = {}
    for e in merged:
        if e.get('kind') == 'vote' and e.get('candidate'):
            counts[e['candidate']] = counts.get(e['candidate'], 0) + 1
    return counts


def cmd_list():
    cands = all_candidates()
    already = {e['id'] for e in load(INDUCTED)['inducted']} if os.path.exists(INDUCTED) else set()
    counts = vote_counts()
    open_ids = [cid for cid in cands if cid not in already]
    open_ids.sort(key=lambda cid: -counts.get(cid, 0))
    print(f'{"votes":>6}  {"id":<26} name')
    for cid in open_ids:
        print(f'{counts.get(cid, 0):>6}  {cid:<26} {cands[cid]["name"]}')
    if already:
        print(f'\nAlready in the ring ({len(already)}): ' + ', '.join(sorted(already)))


def cmd_induct(ids, year, note):
    cands = all_candidates()
    unknown = [i for i in ids if i not in cands]
    if unknown:
        sys.exit(f'Unknown candidate id(s): {", ".join(unknown)} — run --list to see valid ids.')
    inducted_doc = load(INDUCTED) if os.path.exists(INDUCTED) else {'note': '', 'inducted': []}
    existing = {e['id'] for e in inducted_doc['inducted']}
    dupes = [i for i in ids if i in existing]
    if dupes:
        sys.exit(f'Already inducted: {", ".join(dupes)}')
    counts = vote_counts()
    for cid in ids:
        c = cands[cid]
        inducted_doc['inducted'].append({
            'id': cid,
            'name': c['name'],
            'category': c['category'],
            'team': c.get('team'),
            'year': year,
            'votesAtInduction': counts.get(cid, 0),
            'note': note or '',
        })
        print(f'Inducted: {c["name"]} ({year})')
    inducted_doc['updated'] = f'{year}'
    with open(INDUCTED, 'w', encoding='utf-8') as f:
        json.dump(inducted_doc, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'\nwrote {INDUCTED} — {len(inducted_doc["inducted"])} in the ring total')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('ids', nargs='*', help='candidate ids to induct, e.g. a-jameis-winston')
    p.add_argument('--year', type=int, help='class year, e.g. 2026')
    p.add_argument('--note', default='', help='optional note about this class')
    p.add_argument('--list', action='store_true', help='show open candidates with current vote tallies')
    args = p.parse_args()
    if args.list or not args.ids:
        cmd_list()
    else:
        if not args.year:
            sys.exit('--year is required when inducting (e.g. --year 2026)')
        cmd_induct(args.ids, args.year, args.note)
