#!/usr/bin/env python3
"""Every trade priced twice: the day it was made, and twelve months later.

    python3 scripts/build_trade_oneyear.py --ecr path/to/db_fpecr.csv.gz

Writes trade-oneyear.json.

WHY A YEAR AND NOT TODAY
------------------------
scripts/build_trade_hindsight.py already grades a deal on today's board, and
that answers "who is holding the better roster now". It is also unfair in a
way that gets worse the older the trade is: a 2021 deal has had five years to
be re-judged, a 2024 deal one. The two are not on the same footing and the
table silently rewards whoever traded most recently.

A fixed twelve months puts every deal on the same clock. It is long enough
for a rookie to have played a season and a buy-low to have paid or not, and
short enough that it is still recognisably the same player. It is the window
the league argues in -- nobody relitigates a 2021 trade on 2021 terms, they
relitigate it on how it looked the following summer.

WHAT A PICK BECOMES
-------------------
A pick valued a year later is usually not a pick any more. If its draft has
happened by then it is resolved to the player taken with it (drafts.json,
which carries each pick's original owner as well as the team that made it)
and that player is priced on the later date. If the draft is still ahead, it
stays a pick and is priced for the wait that is left.

COVERAGE, AND WHY IT STOPS
--------------------------
The dynasty-superflex consensus runs to 8 August 2025, so a trade needs to be
made before August 2024 to have a reading twelve months on. That gives 2021,
2022 and 2023 in full and part of 2024; 2025 has none. The file reports what
it could price rather than quietly dropping the rest, and a chart built from
it should say which seasons it covers.
"""
import argparse, collections, datetime, json, os, re, sys
import importlib.util as _ilu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_dv = _ilu.spec_from_file_location('dv', os.path.join(ROOT, 'scripts',
                                                      'build_trade_values_dated.py'))
DV = _ilu.module_from_spec(_dv); sys.modules['dv'] = DV; _dv.loader.exec_module(DV)
TV = DV.TV
OUT = 'trade-oneyear.json'
YEAR = 365
TC_WIN = 12
norm = DV.norm
D = datetime.date.fromisoformat


def draft_index():
    """(year, slot) -> player and (year, round, original owner key) -> player."""
    look, _, _ = _counts().resolver()
    d = json.load(open(os.path.join(ROOT, 'drafts.json'), encoding='utf-8'))
    by_slot, by_owner, seen = {}, {}, {}
    for y, rows in d['years'].items():
        for r in rows:
            if not r.get('player'):
                continue
            by_slot[(int(y), int(r['pick']))] = r['player']
            k = look.get(norm(r.get('orig') or r.get('team')))
            if k:
                by_owner[(int(y), int(r['round']), k)] = r['player']
            # the draft's own date is not in the file; the league drafts in
            # August, so a pick is treated as converted from 1 September.
            seen[int(y)] = datetime.date(int(y), 9, 1)
    return by_slot, by_owner, seen


def _counts():
    spec = _ilu.spec_from_file_location('tc2', os.path.join(ROOT, 'scripts',
                                                            'build_trade_counts.py'))
    m = _ilu.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ecr', required=True)
    a = ap.parse_args()
    dates, by = DV.read_ecr(os.path.expanduser(a.ecr))
    curve = DV.fit_curve(dates, by)
    mk = DV.Market(dates, by, curve)
    first, last = D(dates[0]), D(dates[-1])
    by_slot, by_owner, drafted_on = draft_index()
    look, club, _ = _counts().resolver()

    led = json.load(open(os.path.join(ROOT, 'trade-ledger.json'), encoding='utf-8'))
    out, dropped = [], collections.Counter()

    def value(raw, season, on, sides, me):
        """(dollars, what it was by then) at date `on`, or (None, reason)."""
        if DV.PICK.match(raw.replace('Rd ', 'rd ').replace('Round ', 'rd ')):
            txt = DV.register_pick_text(raw)
            p = TV.parse_pick(txt, season)
            yr = p.get('year')
            if yr and drafted_on.get(yr) and on >= drafted_on[yr]:
                who = None
                if p.get('kind') == 'exact':
                    who = by_slot.get((yr, p['slot']))
                if who is None:
                    k = p.get('owner_key') or (look.get(norm(p['tag'])) if p.get('tag') else None)
                    if k:
                        who = by_owner.get((yr, p.get('round') or 1, k))
                if who is not None:
                    v, _, _ = mk.price(who, on.isoformat())
                    return (v, who) if v is not None else (None, 'pick-player-unpriced')
            v, how, _ = DV.price_pick(raw, season, sides, me)
            return (v, raw) if v is not None and how not in ('unparsed', 'bad-slot') \
                else (None, 'pick-unparsed')
        v, _, _ = mk.price(raw, on.isoformat())
        return (v, raw) if v is not None else (None, 'player-unpriced')

    for t in led['trades']:
        if not t['date'] or len(t['sides']) != 2:
            continue
        d0 = D(t['date'])
        d1 = d0 + datetime.timedelta(days=YEAR)
        # Both ends must sit inside the consensus series. Without the floor,
        # a 2017 trade still "priced" -- every pick resolved and every player
        # came back as never-ranked, so an all-pick deal survived and a deal
        # with players in it was dropped. That is not a thin sample, it is a
        # biased one, and it put five seasons into the table that no market
        # reading stands behind.
        if d0 < first:
            dropped['before the consensus begins'] += 1
            continue
        if d1 > last:
            dropped['no +1yr reading'] += 1
            continue
        tsides = [{'team': x['team'], 'franchiseKey': x['franchiseKey']}
                  for x in t['sides']]
        rows, ok = [], True
        for s, tside in zip(t['sides'], tsides):
            g0 = g1 = 0.0
            items = []
            for raw in s['gives']:
                v0, _ = value(raw, t['season'], d0, tsides, tside)
                v1, became = value(raw, t['season'], d1, tsides, tside)
                if v0 is None or v1 is None:
                    ok = False
                    dropped[became if isinstance(became, str) else 'unpriced'] += 1
                    continue
                g0 += v0; g1 += v1
                items.append({'asset': raw, 'day': round(v0, 1),
                              'year': round(v1, 1),
                              'became': became if became != raw else None})
            rows.append({'team': s['team'], 'franchiseKey': s['franchiseKey'],
                         'gaveDay': round(g0, 1), 'gaveYear': round(g1, 1),
                         'assets': items})
        if not ok or len(rows) != 2:
            continue
        a_, b_ = rows
        for me, other in ((a_, b_), (b_, a_)):
            me['netDay'] = round(other['gaveDay'] - me['gaveDay'], 1)
            me['netYear'] = round(other['gaveYear'] - me['gaveYear'], 1)
        out.append({'season': t['season'], 'date': t['date'],
                    'asOf': d1.isoformat(), 'ids': t['ids'], 'sides': rows})

    g = lambda n: 'W' if n > TC_WIN else 'L' if n < -TC_WIN else 'E'
    held = sum(1 for t in out if g(t['sides'][0]['netDay']) == g(t['sides'][0]['netYear']))
    per = collections.defaultdict(lambda: {'n': 0, 'day': 0.0, 'year': 0.0})
    for t in out:
        for s in t['sides']:
            r = per[s['franchiseKey']]
            r['n'] += 1; r['day'] += s['netDay']; r['year'] += s['netYear']

    d = {'note': ('Every two-team trade priced on the day it was made and '
                  'again twelve months later, on the same curve. A pick whose '
                  'draft has happened by the later date is resolved to the '
                  'player taken with it. Built by '
                  'scripts/build_trade_oneyear.py.'),
         'window': YEAR, 'winThreshold': TC_WIN,
         'ecrSpan': [dates[0], dates[-1]],
         'seasons': sorted({t['season'] for t in out}),
         'count': len(out), 'verdictHeld': held,
         'notPriced': dict(dropped),
         'byFranchise': {k: {'club': club.get(k, k), **v} for k, v in per.items()},
         'trades': out}
    json.dump(d, open(os.path.join(ROOT, OUT), 'w', encoding='utf-8'), indent=1)
    print(f'  {OUT}: {len(out)} trades priced twice, seasons '
          f'{d["seasons"][0]}-{d["seasons"][-1]}')
    print(f'  verdict held after twelve months on {held} of {len(out)}')
    for k, v in sorted(dropped.items(), key=lambda x: -x[1]):
        print(f'    not priced: {v:4}  {k}')


if __name__ == '__main__':
    main()
