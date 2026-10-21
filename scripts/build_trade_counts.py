#!/usr/bin/env python3
"""Eleven seasons of trade VOLUME, from the league's own Obvibase ledger.

    python3 scripts/build_trade_counts.py --src ~/obvibase-trades.tsv

Writes trade-counts.json: one row a franchise a season, 2016 to 2026, and
nothing else. No players, no picks, no assets -- just how many deals each
franchise was a party to. That is the one figure the magazine kept getting
wrong, and it is now checkable.

WHY THIS EXISTS
---------------
trades.json is the itemised ledger: 256 deals with the players and picks in
them, 2021 forward, reconstructed from a different Obvibase export. It is what
the Trade Audit prices. But a reconstruction cannot check itself, and the
Machines' row in it reads 13-13-13-13-13 across five seasons -- a flat line in
a league whose own total swung 53, 62, 54, 43, 38. That looked like a data
fault serious enough to pull a published article over, and it was: the article
came down.

The master export settles it. Counted the same way, the Machines go 13, 11,
13, 12, 12. Every other franchise agrees between the two sources to within two
a season, and six of the sixteen agree exactly. So the flat line was not a
corruption. It was a genuinely metronomic trading habit plus four rows the two
exports disagree on, and the mistake was in the inference, not the ledger.

The claim that came out of the flat line -- the metronome -- is gone, because
it is not true. Everything else in the audit stood up, which is only knowable
because there are now two sources.

The export is where the itemised window comes from too, and it is worth
saying out loud: trade COUNTS go back to 2016, eleven seasons. The player and
pick detail starts in 2021. So a five-year window is a limit of the itemised
data, not of the league's trading, and the copy has to say that rather than
implying the market began in 2021.

THE SOURCE FILE IS NOT IN THIS REPO
-----------------------------------
`--src` is a tab-separated export of John's Obvibase ledger, kept outside this
repository the way every other raw source is. This script turns it into the
derived counts, which are facts about trades the whole league announced, and
those go in. Re-run it when the ledger is re-exported.

The 2026 column does not come from the export. The export was pulled on
2025-12-03 and holds four post-deadline deals; Sleeper's own transaction log
(transactions.json) has twenty-nine by week six. So 2026 is counted from
Sleeper and labelled part-season, and the Trade Audit's window stops at 2025.

READING THE EXPORT
------------------
Two tables pasted side by side -- the league row, then the trades -- so every
line repeats the league's eight columns before the thirteen that matter. Teams
are era names: twenty-four of them for sixteen chairs, with Yo Mama, The OX
45s, Porky's, Disciples of Darnold and a 'Darnod' typo all needing to resolve
through scfl-franchises.json or a franchise loses its past.

Multi-leg blockbusters carry fractional trade numbers (20.1, 20.2) and one
2019 block is numbered 1901-1905. Legs of one deal are folded into one deal,
so a three-team trade counts once for each of the three and not twice for the
middleman. There are nine of them in eleven seasons.

A franchise that will not resolve is NAMED in the output and the build fails,
rather than quietly dropping a side.
"""
import argparse, collections, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = 'trade-counts.json'

# The export's own column names, in the second of the two pasted tables.
COLS = ('Season', 'Season Trade #', 'Team A', 'Team B')

# Renames the stored alias table has not caught up with. The first is the
# export's own typo; the rest are the 2026 Sleeper names, and they are the same
# four scripts/history.py has to carry for the same reason.
ALIAS = {'disciplesofdarnod': 'lilchops', 'nwo': 'newworldorder',
         'gumbas': 'gumbas', 'phinsphag': 'heavyhitters',
         'forty2v': 'horsecollars'}

norm = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower())


def resolver():
    fr = json.load(open(os.path.join(ROOT, 'scfl-franchises.json'),
                        encoding='utf-8'))
    look = dict(ALIAS)
    club = {}
    for f in fr['franchises']:
        look[norm(f['club'])] = f['key']
        for a in f.get('aliases') or []:
            look.setdefault(norm(a), f['key'])
        club[f['key']] = f['club']
    look.update({norm(k): v for k, v in fr['lookup'].items()})
    return look, club, {f['key'] for f in fr['franchises'] if f.get('active')}


def read_export(path, look):
    """-> {(season, deal no): {franchise keys}}, with legs folded into deals."""
    rows = [l.rstrip('\n').split('\t') for l in open(path, encoding='utf-8')]
    hdr = rows[0]
    # The league table's columns come first and share four names with the
    # trade table, so the index is taken from the LAST occurrence of each.
    at = {c: max(i for i, h in enumerate(hdr) if h == c) for c in COLS}
    need = max(at.values())
    deals, unresolved = collections.defaultdict(set), collections.Counter()
    for r in rows[1:]:
        if len(r) <= need:            # the paste's own trailing line
            continue
        side = set()
        for c in ('Team A', 'Team B'):
            k = look.get(norm(r[at[c]]))
            if k:
                side.add(k)
            else:
                unresolved[r[at[c]]] += 1
        # 20.1 and 20.2 are legs of deal 20; the 2019 block numbered 1901-1905
        # is five separate deals and int() leaves it alone.
        deals[(r[at['Season']], int(float(r[at['Season Trade #']])))] |= side
    if unresolved:
        print('  UNRESOLVED FRANCHISES — the count would be wrong:')
        for n, c in unresolved.most_common():
            print(f'    {c:4}  {n}')
        sys.exit(1)
    return deals


def sleeper_2026(look):
    """2026 from Sleeper, because the Obvibase export predates the season."""
    p = os.path.join(ROOT, 'transactions.json')
    if not os.path.exists(p):
        return None, None, None
    d = json.load(open(p, encoding='utf-8'))
    ros = {int(k): look.get(norm(v)) for k, v in d['rosters'].items()}
    bad = sorted({v for k, v in d['rosters'].items() if not ros[int(k)]})
    if bad:
        print('  UNRESOLVED 2026 ROSTERS:', bad)
        sys.exit(1)
    per = collections.Counter()
    n = 0
    for t in d['rows']:
        if t.get('type') != 'trade' or t.get('status') != 'complete':
            continue
        n += 1
        for rid in t['roster_ids']:
            per[ros[rid]] += 1
    return str(d['season']), n, per


def reconcile(tol=2):
    """The itemised ledger against the master counts, season by season.

    trades.json is a reconstruction and cannot check itself. This is the
    check: for every franchise and every season the two sources both cover,
    how far apart are they. Returns a row a franchise and the worst gap found,
    so the Trade Audit can refuse to publish a count the master export does
    not back -- which is the whole reason the first printing came down.

    `tol` is how far apart the two may be in one season before the ledger is
    called unsafe. Two is not a guess: it is the largest gap the sixteen
    current franchises actually show, and six of them show none at all.

    The part-seasons are left out. 2026 is six weeks of Sleeper against four
    post-deadline rows in an export pulled in December, so a gap there says
    nothing about the ledger.
    """
    cp = os.path.join(ROOT, OUT)
    if not os.path.exists(cp):
        return None
    cnt = json.load(open(cp, encoding='utf-8'))
    look, club, _ = resolver()
    master = {r['key']: r['bySeason'] for r in cnt['franchises']}
    part = set(cnt.get('partSeasons') or [])

    tj = json.load(open(os.path.join(ROOT, 'trades.json'), encoding='utf-8'))
    led = collections.defaultdict(collections.Counter)
    seen = collections.Counter()
    for t in tj['trades']:
        s = str(t['season'])
        seen[s] += 1
        for k in {look.get(norm(x['team'])) for x in t['sides']}:
            if k:
                led[k][s] += 1
    span = sorted(s for s in seen if s not in part
                  and any(s in m for m in master.values()))

    rows, worst, exact = [], 0, 0
    for k in sorted(led, key=lambda k: -sum(led[k].values())):
        gaps = {s: led[k].get(s, 0) - master.get(k, {}).get(s, 0) for s in span}
        hi = max(abs(v) for v in gaps.values()) if gaps else 0
        worst = max(worst, hi)
        exact += not hi
        rows.append({'key': k, 'club': club.get(k, k), 'gaps': gaps,
                     'worst': hi,
                     'ledger': sum(led[k].get(s, 0) for s in span),
                     'master': sum(master.get(k, {}).get(s, 0) for s in span)})
    return {'span': span, 'rows': rows, 'worst': worst, 'exact': exact,
            'tol': tol, 'ok': worst <= tol,
            'ledger': sum(seen[s] for s in span),
            'master': sum(cnt['leagueTotals'][s] for s in span)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='the Obvibase TSV export')
    a = ap.parse_args()
    look, club, active = resolver()
    deals = read_export(os.path.expanduser(a.src), look)

    per = collections.defaultdict(collections.Counter)
    tot = collections.Counter()
    for (s, _), ks in deals.items():
        tot[s] += 1
        for k in ks:
            per[k][s] += 1
    legs = collections.Counter()
    multi = sum(1 for ks in deals.values() if len(ks) > 2)

    # 2026 is Sleeper's, and it replaces the export's four post-deadline rows.
    sy, sn, sper = sleeper_2026(look)
    part = []
    if sy:
        tot[sy] = sn
        for k in list(per) + list(sper):
            per[k][sy] = sper.get(k, 0)
        part.append(sy)

    seasons = sorted(tot)
    out = {
        'note': ('Trade volume only -- how many deals each franchise was a '
                 'party to, a season. No assets: the itemised ledger is '
                 'trades.json and starts in 2021. Built by '
                 'scripts/build_trade_counts.py from an Obvibase export kept '
                 'outside this repo; the part-season column comes from '
                 'Sleeper.'),
        'span': [seasons[0], seasons[-1]],
        'seasons': seasons,
        'partSeasons': part,
        'leagueTotals': {s: tot[s] for s in seasons},
        'multiTeamDeals': multi,
        'franchises': [
            {'key': k, 'club': club.get(k, k), 'active': k in active,
             'bySeason': {s: per[k].get(s, 0) for s in seasons},
             'total': sum(per[k].get(s, 0) for s in seasons)}
            for k in sorted(per, key=lambda k: -sum(per[k].values()))],
    }
    p = os.path.join(ROOT, OUT)
    json.dump(out, open(p, 'w', encoding='utf-8'), indent=1)

    print(f'  {OUT}: {sum(tot.values())} deals, {seasons[0]}-{seasons[-1]}, '
          f'{len(per)} franchises, {multi} with three teams in them')
    print('  ' + 'franchise'.ljust(20)
          + ''.join(s[2:].rjust(5) for s in seasons) + '  total')
    for row in out['franchises']:
        print('  ' + row['club'].ljust(20)
              + ''.join(str(row['bySeason'][s] or '.').rjust(5) for s in seasons)
              + str(row['total']).rjust(7))
    print('  ' + 'LEAGUE'.ljust(20)
          + ''.join(str(tot[s]).rjust(5) for s in seasons)
          + str(sum(tot.values())).rjust(7)
          + ('   (' + ', '.join(part) + ' part-season)' if part else ''))

    r = reconcile()
    if r:
        print()
        print(f'  trades.json against these counts, {r["span"][0]}-'
              f'{r["span"][-1]}: {r["ledger"]} deals against {r["master"]}, '
              f'{r["exact"]} of {len(r["rows"])} franchises exact, worst '
              f'single-season gap {r["worst"]}'
              + ('' if r['ok'] else f' — OVER TOLERANCE ({r["tol"]})'))
        for row in r['rows']:
            if row['worst']:
                print('    ' + row['club'].ljust(20)
                      + ' '.join(f'{s[2:]}{v:+d}' for s, v in row['gaps'].items()
                                 if v))


if __name__ == '__main__':
    main()
