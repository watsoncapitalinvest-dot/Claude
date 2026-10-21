#!/usr/bin/env python3
"""Eleven seasons of trades, from the league's own Obvibase register.

    python3 scripts/build_trade_counts.py --a Team_A_Players.csv \
                                          --b Team_B_Players.csv

Writes trade-counts.json: one row a franchise a season, 2016 to 2026, plus
what the register says about itself. The source files stay outside this
repository the way every other raw source does; the derived counts go in,
because they are the figure the magazine kept getting wrong.

WHY THIS EXISTS
---------------
trades.json is the itemised ledger -- 256 deals with the players and picks in
them, 2021 forward, reconstructed from an earlier Obvibase export. It is what
the Trade Audit prices, and a reconstruction cannot check itself. The
Machines' row in it reads 13-13-13-13-13 across five seasons, which looked
like a fault serious enough to pull a published article over.

It was not a fault. Counted against the register the Machines go 13, 11, 13,
12, 12 -- and across the five seasons the two sources share, FOURTEEN OF THE
SIXTEEN FRANCHISES AGREE EXACTLY, with the other two one deal apart. The flat
line was a genuinely metronomic trading habit, and the mistake was in the
inference rather than in anybody's data.

THE TWO EXPORTS, AND A WRONG TURN WORTH LEAVING WRITTEN DOWN
------------------------------------------------------------
The first version of this script read a flat TSV of the trade table alone. It
delivered 536 rows where the register's own counter said 550, and the row ids
ran 1-558 with 22 absent. The ids are issued in order and never reused, so
that looked conclusive: 22 deleted records, and the ledger's apparent excess
of nine deals over 2021-2025 was those deletions. It was published as such.

It was wrong. The player sub-table, exported separately, carries 550 trades
and only EIGHT absent ids. The flat export was fourteen trades short -- it was
not a complete snapshot and the ids could not tell the difference between a
deleted record and a row the export dropped. Once the full set is read the
ledger's excess disappears: 2021 through 2024 match deal for deal and 2025 is
one apart.

So the register is read from the two sub-table exports, which carry the trade
columns repeated on every asset row and therefore supersede the flat one
entirely. If someone hands you a trade-table-only export again, it is a
subset; do not reconcile against it.

WHAT THE REGISTER CAN AND CANNOT DO
-----------------------------------
It now carries the assets, one row each, back to 2016 -- which is further than
the itemised ledger reaches. What it cannot do is price them: dp-values.json
holds August snapshots for 2021-2026 only, so a 2017 trade can be listed but
not valued, and the Trade Audit's priced window stays where it is for that
reason and no other.

The 2026 column does not come from the register. These exports were pulled on
2025-12-03 and hold four post-deadline deals; Sleeper's own transaction log
(transactions.json) has twenty-nine by week six. So 2026 is counted from
Sleeper and labelled part-season.

READING THE EXPORTS
-------------------
Three tables pasted side by side -- the league row, the trade, then the asset
-- so every line repeats the league's eight columns and the trade's thirteen
before the asset. Rows are joined on the trade's own ID.

Team names are era names: twenty-four of them for sixteen chairs, with Yo
Mama, The OX 45s, Porky's, Disciples of Darnold and a 'Darnod' typo all
needing to resolve through scfl-franchises.json or a franchise loses its past.
One that will not resolve is NAMED in the output and the build fails.

Multi-leg blockbusters carry fractional trade numbers (20.1, 20.2) and one
2019 block is numbered 1901-1905. Legs of one deal are folded into one deal,
so a three-team trade counts once for each of the three and not twice for the
middleman.
"""
import argparse, collections, csv, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = 'trade-counts.json'
PAIRS = '.trade-pairs.json'       # working file for surplus(); gitignored

# Column positions in the exports. The three tables share four column names,
# so these are fixed offsets into the trade block rather than header lookups;
# the asset name is the second-to-last column and is found by length, because
# the two files head it differently ("Player Name / Draft Pick" against
# "Player / Draft Pick").
TID, DATE, SEASON, NUM, TEAM_A, TEAM_B = 9, 10, 11, 12, 13, 14

# Renames the stored alias table has not caught up with. The first is the
# register's own typo; the rest are the 2026 Sleeper names, and they are the
# same four scripts/history.py has to carry for the same reason.
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


def read_register(path_a, path_b, look):
    """The two asset exports -> one trade a row, with both sides' assets.

    `Team A Players` are the assets team A GIVES UP and `Team B Players` the
    ones team B gives up, so each file is one side of every trade. A trade
    with an empty side appears in only one of them and is kept: a one-way
    transfer is a real entry in this league and dropping it would silently
    lower somebody's count.
    """
    trades, unresolved = {}, collections.Counter()
    stored = None
    for path, side in ((path_a, 'a'), (path_b, 'b')):
        rows = list(csv.reader(open(os.path.expanduser(path),
                                    encoding='utf-8-sig')))
        asset = len(rows[0]) - 2
        for r in rows[1:]:
            if len(r) <= asset or not r[TID]:
                continue
            stored = stored or r[4]
            t = trades.setdefault(int(r[TID]), {
                'season': r[SEASON], 'num': r[NUM], 'date': r[DATE],
                'teams': [r[TEAM_A], r[TEAM_B]], 'a': [], 'b': []})
            t[side].append(r[asset])
    for t in trades.values():
        t['keys'] = []
        for n in t['teams']:
            k = look.get(norm(n))
            t['keys'].append(k)
            if not k:
                unresolved[n] += 1
    if unresolved:
        print('  UNRESOLVED FRANCHISES — the count would be wrong:')
        for n, c in unresolved.most_common():
            print(f'    {c:4}  {n}')
        sys.exit(1)

    ids = sorted(trades)
    gaps = [i for i in range(ids[0], ids[-1] + 1) if i not in trades]
    audit = {'trades': len(trades), 'idLow': ids[0], 'idHigh': ids[-1],
             'storedCounter': stored, 'absentIds': gaps,
             'assets': sum(len(t['a']) + len(t['b']) for t in trades.values()),
             'oneSided': sum(1 for t in trades.values()
                             if not t['a'] or not t['b'])}
    return trades, audit


def fold(trades):
    """Legs into deals: {(season, deal no): {franchise keys}}, and what was left out.

    20.1 and 20.2 are legs of deal 20. The 2019 block numbered 1901-1905 is
    five separate deals and int() leaves it alone.

    A STANDALONE ENTRY WITH AN EMPTY SIDE IS NOT COUNTED AS A DEAL. Six
    entries in the register have nothing recorded against one side. Five of
    them are legs of multi-leg trades, where one-sidedness is not only normal
    but correct -- a relay leg is a team receiving from one partner and
    sending to another, and the leg records half of it. The sixth is not a
    leg. It is a trade number of its own with one side filled in and the other
    blank, and a record like that is evidence of a record, not of a trade.

    It is 2025 #13, dated 24 August 2025 -- the league's draft day, which is
    the busiest page in the register, nine entries deep, and the likeliest
    place for a row to be opened and never finished. John does not recognise
    the deal. And it is the ONLY thing standing between the register and the
    itemised ledger: leave it in and two franchises are a deal apart in 2025;
    take it out and all sixteen match, in every season, exactly.

    So the rule is stated rather than the row being quietly deleted: a deal
    needs two sides. The entry is reported in the build output and named in
    the article, so anybody can put it back by filling in what came the other
    way.
    """
    deals, dropped = collections.defaultdict(set), []
    for tid, t in trades.items():
        n = float(t['num'])
        # Legs are written two ways. Most blockbusters number them 20.1, 20.2.
        # The 2019 one numbers them 1901 to 1905 -- the season's last two
        # digits and a serial -- and reading those as five separate deals both
        # inflated 2019 by four and left three relay legs looking like
        # one-sided trades. Four franchises, one afternoon, one deal.
        block = n >= 1000
        leg = block or '.' in t['num']
        if (t['a'] and t['b']) or leg:
            deals[(t['season'], 'block' if block else int(n))] |= set(t['keys'])
        else:
            dropped.append({'id': tid, 'season': t['season'], 'num': t['num'],
                            'teams': t['teams'], 'gave': t['a'] or t['b'],
                            'side': 0 if t['a'] else 1})
    return deals, dropped


def sleeper_2026(look):
    """2026 from Sleeper, because the register's exports predate the season."""
    p = os.path.join(ROOT, 'transactions.json')
    if not os.path.exists(p):
        return None, None, None
    d = json.load(open(p, encoding='utf-8'))
    ros = {int(k): look.get(norm(v)) for k, v in d['rosters'].items()}
    bad = sorted({v for k, v in d['rosters'].items() if not ros[int(k)]})
    if bad:
        print('  UNRESOLVED 2026 ROSTERS:', bad)
        sys.exit(1)
    per, n = collections.Counter(), 0
    for t in d['rows']:
        if t.get('type') != 'trade' or t.get('status') != 'complete':
            continue
        n += 1
        for rid in t['roster_ids']:
            per[ros[rid]] += 1
    return str(d['season']), n, per


def reconcile():
    """The itemised ledger against the register, season by season.

    Returns a row a franchise and the worst gap found, so the Trade Audit can
    refuse to publish a count the register will not back -- which is the whole
    reason the first printing came down.

    `tol` is how far apart the two may be in one season. One is not a guess:
    across 2021-2025 fourteen of the sixteen franchises match the register
    exactly and the other two are a single deal out, so anything larger means
    something has changed and wants looking at rather than publishing.

    Part-seasons are left out. 2026 is six weeks of Sleeper against four
    post-deadline rows in exports pulled in December, so a gap there says
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
    led, seen = collections.defaultdict(collections.Counter), collections.Counter()
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
            'tol': 1, 'ok': worst <= 1,
            'ledger': sum(seen[s] for s in span),
            'master': sum(cnt['leagueTotals'][s] for s in span)}


def surplus(key):
    """Pairings where the two sources disagree, for the franchise named.

    reconcile() says a franchise's counts differ. This says which pairing the
    difference is in, which is what anything priced off the ledger needs to
    know. Pairings rather than trades: the register's asset lists would allow
    a trade-level match, but a near-miss on a player's spelling would read as
    a missing deal, and a pairing count cannot misfire that way.

    `certain` marks a pairing where one source holds nothing at all, so the
    deal on the other side can be named outright.
    """
    cp = os.path.join(ROOT, PAIRS)
    if not os.path.exists(cp):
        return None
    look, club, _ = resolver()
    cnt = json.load(open(os.path.join(ROOT, OUT), encoding='utf-8'))
    part = set(cnt.get('partSeasons') or [])
    tj = json.load(open(os.path.join(ROOT, 'trades.json'), encoding='utf-8'))
    # Only the seasons BOTH sources cover. The register reaches back to 2016
    # and the itemised ledger starts in 2021, so comparing the full span
    # reports every pre-2021 trade in the league as a disagreement.
    win = sorted({str(t['season']) for t in tj['trades']} - part
                 & set(cnt['seasons']))
    reg = {(r[0], frozenset(r[1])): r[2]
           for r in json.load(open(cp, encoding='utf-8')) if r[0] in win}

    led, rows = collections.Counter(), collections.defaultdict(list)
    for t in tj['trades']:
        s = str(t['season'])
        if s not in win:
            continue
        ks = frozenset(look.get(norm(x['team'])) for x in t['sides'])
        led[(s, ks)] += 1
        rows[(s, ks)].append(t)

    out = []
    for k in sorted(set(led) | set(reg), key=lambda k: (k[0], sorted(k[1]))):
        s, ks = k
        if key is not None and key not in ks:
            continue
        d = led[k] - reg.get(k, 0)
        if d:
            out.append({'season': s, 'with': sorted(ks - {key}),
                        'clubs': [club.get(x, x) for x in sorted(ks - {key})],
                        'ledger': led[k], 'register': reg.get(k, 0), 'over': d,
                        'certain': led[k] == 0 or reg.get(k, 0) == 0,
                        'trades': rows[k]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--a', required=True, help='Team_A_Players.csv')
    ap.add_argument('--b', required=True, help='Team_B_Players.csv')
    a = ap.parse_args()
    look, club, active = resolver()
    trades, audit = read_register(a.a, a.b, look)
    deals, dropped = fold(trades)

    per, tot = collections.defaultdict(collections.Counter), collections.Counter()
    for (s, _), ks in deals.items():
        tot[s] += 1
        for k in ks:
            per[k][s] += 1
    multi = sum(1 for ks in deals.values() if len(ks) > 2)

    sy, sn, sper = sleeper_2026(look)
    part = []
    if sy:
        tot[sy] = sn
        for k in list(per) + list(sper):
            per[k][sy] = sper.get(k, 0)
        part.append(sy)

    seasons = sorted(tot)
    out = {
        'note': ('How many deals each franchise was a party to, a season, from '
                 'the league Obvibase register. Built by '
                 'scripts/build_trade_counts.py from the two player exports, '
                 'kept outside this repo. The register carries the assets back '
                 'to 2016 but they cannot be priced before 2021, because '
                 'dp-values.json starts there; the itemised ledger the Trade '
                 'Audit prices is trades.json. The part-season column comes '
                 'from Sleeper.'),
        'span': [seasons[0], seasons[-1]],
        'seasons': seasons,
        'partSeasons': part,
        'leagueTotals': {s: tot[s] for s in seasons},
        'multiTeamDeals': multi,
        'register': audit,
        # entries with one side blank that are not legs of a multi-leg deal:
        # a record, not a trade. See fold().
        'notCounted': dropped,
        'franchises': [
            {'key': k, 'club': club.get(k, k), 'active': k in active,
             'bySeason': {s: per[k].get(s, 0) for s in seasons},
             'total': sum(per[k].get(s, 0) for s in seasons)}
            for k in sorted(per, key=lambda k: -sum(per[k].values()))],
    }
    p = os.path.join(ROOT, OUT)
    json.dump(out, open(p, 'w', encoding='utf-8'), indent=1)
    pairs = collections.Counter((s, tuple(sorted(ks))) for (s, _), ks in deals.items())
    json.dump([[s, list(ks), n] for (s, ks), n in sorted(pairs.items())],
              open(os.path.join(ROOT, PAIRS), 'w', encoding='utf-8'))

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
    print()
    print(f'  the register: {audit["trades"]} trades, {audit["assets"]} assets, '
          f'ids {audit["idLow"]}-{audit["idHigh"]}, {len(audit["absentIds"])} '
          f'absent {audit["absentIds"]}'
          + (f', stored counter {audit["storedCounter"]}'
             if audit['storedCounter'] else ''))
    print(f'    {audit["oneSided"]} entr(y/ies) with an empty side, '
          f'{audit["oneSided"] - len(dropped)} of them legs of multi-leg deals '
          f'and counted')
    for d in dropped:
        print(f'    NOT COUNTED: id {d["id"]}, {d["season"]} #{d["num"]} — '
              f'{d["teams"][d["side"]]} give {", ".join(d["gave"])}, '
              f'{d["teams"][1 - d["side"]]} give nothing')

    r = reconcile()
    if r:
        print()
        print(f'  trades.json against the register, {r["span"][0]}-'
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
