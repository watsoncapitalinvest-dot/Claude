#!/usr/bin/env python3
"""The itemised ledger, rebuilt from the register, WITH THE DATE EACH TRADE WAS MADE.

    python3 scripts/build_trade_ledger.py --a Team_A_Players.csv \
                                          --b Team_B_Players.csv

Writes trade-ledger.json: one row a deal -- season, date, both sides, every
player and pick in it. It supersedes trades.json, which was reconstructed from
an earlier export and carries no dates at all.

WHY THE DATE MATTERS, IN ONE TABLE
----------------------------------
Every price in the Trade Audit is currently taken from the August snapshot of
the trade's own season. That is defensible and it was the best available, but
it is not what a trade was worth when it was made. Of the 259 register trades
in the priced window:

    1 month before August    54
    the month of August      90
    one month after          31
    two months after         32
    three months after       36
    four months after        16

A hundred and fifteen of them -- forty-four per cent -- sit more than a month
from the snapshot they are priced at, and eighty-four are two months or more
into a season, which is exactly when a value moves most: the breakout has
broken out, the hamstring has gone. A November trade priced at August prices
is not a trade priced at the table.

The register has the date on every row. This is the file that carries it
forward.

WHAT IS AND IS NOT IN HERE
--------------------------
Legs of a multi-team trade are folded into one deal, so a three-team blockbuster
is one row with three sides rather than two rows with a middleman counted twice.
The 2019 block numbered 1901-1905 is one such deal; most are numbered 20.1,
20.2.

A standalone entry with one side blank is NOT a deal and is not here -- see
scripts/build_trade_counts.py, which states that rule and names the one entry
it excludes.

Relay assets are left where the register put them. The older trades.json
netted them out so a middleman was credited only with what he kept; that is
the right call for counting who gained what, and the wrong one for a file
whose job is to say what moved. A consumer that wants the netted view can do
it from here; one that wants the raw legs cannot get them back out of a file
that already netted them.
"""
import argparse, collections, json, os, sys
import importlib.util as _ilu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_tc = _ilu.spec_from_file_location('tc', os.path.join(ROOT, 'scripts',
                                                      'build_trade_counts.py'))
TC = _ilu.module_from_spec(_tc); sys.modules['tc'] = TC; _tc.loader.exec_module(TC)
OUT = 'trade-ledger.json'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--a', required=True)
    ap.add_argument('--b', required=True)
    a = ap.parse_args()
    look, club, _ = TC.resolver()
    trades, audit = TC.read_register(a.a, a.b, look)

    # Group by deal, the same way fold() counts them, so the ledger and the
    # counts can never describe a different set of trades.
    by_deal = collections.defaultdict(list)
    skipped = []
    for tid, t in trades.items():
        n = float(t['num'])
        block = n >= 1000
        leg = block or '.' in t['num']
        if not (t['a'] and t['b']) and not leg:
            skipped.append(tid)
            continue
        by_deal[(t['season'], 'block' if block else int(n))].append((tid, t))

    out = []
    for (season, num), legs in sorted(by_deal.items(),
                                      key=lambda kv: (kv[0][0], str(kv[0][1]))):
        # A side can appear in more than one leg of the same deal; its assets
        # are everything it gave across all of them.
        gave = collections.defaultdict(list)
        for _, t in legs:
            for key, side in zip(t['keys'], ('a', 'b')):
                gave[key] += t[side]
        ds = [t['date'] for _, t in legs if t.get('date')]
        date = min(ds) if ds else None
        out.append({
            'season': int(season),
            'date': date,
            'ids': sorted(tid for tid, _ in legs),
            'legs': len(legs),
            'sides': [{'team': club.get(k, k), 'franchiseKey': k,
                       'gives': gave[k]} for k in sorted(gave)],
        })

    d = {'note': ('The itemised ledger with dates, rebuilt from the league '
                  'Obvibase register by scripts/build_trade_ledger.py. One row '
                  'a deal, legs folded. `gives` is what that side sent; relay '
                  'assets are left where the register put them. Supersedes '
                  'trades.json, which has no dates.'),
         'span': [min(x['season'] for x in out), max(x['season'] for x in out)],
         'count': len(out),
         'excludedOneSided': skipped,
         'trades': out}
    p = os.path.join(ROOT, OUT)
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    per = collections.Counter(x['season'] for x in out)
    dated = sum(1 for x in out if x['date'])
    multi = sum(1 for x in out if len(x['sides']) > 2)
    print(f'  {OUT}: {len(out)} deals {d["span"][0]}-{d["span"][1]}, '
          f'{dated} with a date, {multi} with three or more sides')
    print('  ' + ' '.join(f'{s}:{n}' for s, n in sorted(per.items())))
    if skipped:
        print(f'  excluded (one side blank, not a leg): ids {skipped}')


if __name__ == '__main__':
    main()
