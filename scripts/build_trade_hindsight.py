#!/usr/bin/env python3
"""The second lens: not what a trade was worth, but how it turned out.

    python3 scripts/build_trade_hindsight.py

Writes tradeHindsight.json -- every priced deal valued twice. Once at the
August it was made, which is what scripts/build_trade_values.py already does
and what the Trade Audit grades on. And once at today, which is the question
everybody in the league actually argues about: never mind what it looked like,
who won it?

THESE ARE DIFFERENT QUESTIONS AND THE ANSWERS DISAGREE ON PURPOSE.
------------------------------------------------------------------
The at-the-time number asks whether a manager made a defensible deal with what
was knowable at the table. It is the fair one, and it is the only one that can
convict or acquit anybody of anything, because nobody trades with a newspaper
from next year.

The today number asks who ended up holding the better end. It is the unfair
one -- it credits a manager for a player's hamstring and blames another for a
rookie who did not pan out -- and it is also the one the chat has been
shouting about since 2021. Both belong in the record. Neither replaces the
other, and the interesting rows are the ones where they disagree.

HOW A PICK BECOMES A PLAYER
---------------------------
A trade is only half players. The other half is picks, and a pick that has
since been used is not a pick any more -- it is whoever was taken with it.
drafts.json holds the results, 2021 to 2025, with each pick's ORIGINAL owner
as well as the team that made it, which is what lets a pick resolve:

  "2023 pick 9"        -> the ninth pick of 2023 -> the player taken there
  "2024 2nd (Chops)"   -> Lil Chops' own 2024 second -> the player taken there
  "2028 1st (PCE)"     -> not drafted yet; still priced as a pick, on today's
                          chart, discounted for the years still to wait

tradeValues.json already carries `owner` on every unslotted pick, which is the
only reason the second line works.

WHAT COUNTS AS GONE
-------------------
dp-values.json carries one value a player a season. A player with no value in
the current column is off the board -- retired, cut, out of the league -- and
is worth nothing now. That is not a gap in the data, it is the answer: a 2021
trade for a player nobody rosters in 2026 returned nothing, and saying so is
the whole point of the exercise.

A pick that cannot be resolved IS a gap, and those are counted out loud rather
than quietly zeroed. Every one of them makes a trade less certain, so a deal
carrying one is flagged and left out of the aggregate record.
"""
import collections, json, os, re, sys
import importlib.util as _ilu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_tv = _ilu.spec_from_file_location('tv', os.path.join(ROOT, 'scripts',
                                                      'build_trade_values.py'))
TV = _ilu.module_from_spec(_tv); sys.modules['tv'] = TV; _tv.loader.exec_module(TV)

OUT = 'tradeHindsight.json'
TC_WIN = 12                      # the Trade Court's threshold, as everywhere else

norm = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower())


def resolver():
    fr = json.load(open(os.path.join(ROOT, 'scfl-franchises.json'),
                        encoding='utf-8'))
    look = {'nwo': 'newworldorder', 'phinsphag': 'heavyhitters',
            'forty2v': 'horsecollars'}
    club = {}
    for f in fr['franchises']:
        look[norm(f['club'])] = f['key']
        for a in f.get('aliases') or []:
            look.setdefault(norm(a), f['key'])
        club[f['key']] = f['club']
    look.update({norm(k): v for k, v in fr['lookup'].items()})
    return look, club


def draft_index(look):
    """(year, overall pick) -> player, and (year, round, original owner) -> player."""
    d = json.load(open(os.path.join(ROOT, 'drafts.json'), encoding='utf-8'))
    by_slot, by_owner, years = {}, {}, set()
    for y, rows in d['years'].items():
        years.add(int(y))
        for r in rows:
            if not r.get('player'):
                continue
            by_slot[(int(y), int(r['pick']))] = r['player']
            k = look.get(norm(r.get('orig') or r.get('team')))
            if k:
                by_owner[(int(y), int(r['round']), k)] = r['player']
    return by_slot, by_owner, (max(years) if years else 0)


class Board:
    """dp-values.json, indexed so a player can be priced in any stored season."""

    def __init__(self):
        d = json.load(open(os.path.join(ROOT, 'dp-values.json'), encoding='utf-8'))
        self.years = d['years']
        self.v = d['v']
        self.now = d['years'][-1]

    def at(self, name, year):
        row = self.v.get(norm(name)) or self.v.get((name or '').lower().strip())
        if row is None:
            return None
        try:
            i = self.years.index(year)
        except ValueError:
            return None
        val = row[i] if i < len(row) else None
        return None if val is None else float(val)


def now_value(a, B, by_slot, by_owner, last_draft, look):
    """What this asset is worth TODAY. -> (value, what it became, note)."""
    if a['kind'] == 'player':
        v = B.at(a['name'], B.now)
        # No value in the current column means off the board, which is an
        # answer and not a hole: the trade returned nothing.
        return (0.0, a['name'], 'gone') if v is None else (v, a['name'], '')

    year = a.get('year')
    if year is not None and year <= last_draft:
        who = None
        if a.get('slot') is not None:
            who = by_slot.get((year, a['slot']))
        if who is None and a.get('owner'):
            k = look.get(norm(a['owner'])) or norm(a['owner'])
            who = by_owner.get((year, a.get('round') or 1, k))
        if who is None:
            return (None, None, 'unresolved')
        v = B.at(who, B.now)
        return (0.0, who, 'gone') if v is None else (v, who, 'drafted')

    # Still a pick. Price it on today's chart, discounted for the wait that
    # is LEFT rather than the wait there was when it was traded.
    out = max(0, (year or B.now) - B.now)
    if a.get('slot') is not None:
        base = TV.PICK_CHART.get(TV.rank_to_slot(a['slot'], 1) if False else a['slot'])
        base = base if base is not None else TV.PICK_CHART[min(a['slot'], 32)]
    else:
        rnd = a.get('round') or 1
        lo, hi = (1, 17) if rnd == 1 else (17, 33)
        base = sum(TV.PICK_CHART[s] for s in range(lo, hi)) / 16
    return (base * (TV.PICK_DECAY ** out), a['raw'], 'pending')


def main():
    look, club = resolver()
    by_slot, by_owner, last_draft = draft_index(look)
    B = Board()
    tv = json.load(open(os.path.join(ROOT, 'tradeValues.json'), encoding='utf-8'))

    out, skipped = [], 0
    for t in tv['trades']:
        if len(t['sides']) != 2:
            skipped += 1
            continue
        rec, bad = [], 0
        for s in t['sides']:
            then = s['total']
            now, items = 0.0, []
            for a in s['assets']:
                v, became, note = now_value(a, B, by_slot, by_owner, last_draft, look)
                if v is None:
                    bad += 1
                    items.append({'was': a.get('name') or a.get('raw'),
                                  'became': None, 'then': a.get('value'),
                                  'now': None, 'note': note})
                    continue
                now += v
                items.append({'was': a.get('name') or a.get('raw'),
                              'became': became if became != (a.get('name') or a.get('raw'))
                              else None,
                              'then': a.get('value'), 'now': round(v, 1),
                              'note': note})
            rec.append({'team': s['team'], 'key': s['franchiseKey'],
                        'then': round(then, 1), 'now': round(now, 1),
                        'assets': items})
        a, b = rec
        out.append({'season': t['season'], 'sides': rec,
                    'thenNet': round(a['then'] - b['then'], 1),
                    'nowNet': round(a['now'] - b['now'], 1),
                    'unresolved': bad})

    grade = lambda n: 'W' if n > TC_WIN else 'L' if n < -TC_WIN else 'E'
    firm = [x for x in out if not x['unresolved']]
    flips = sum(1 for x in firm if grade(x['thenNet']) != grade(x['nowNet']))
    rev = sum(1 for x in firm
              if {grade(x['thenNet']), grade(x['nowNet'])} == {'W', 'L'})

    d = {
        'note': ('Every two-team deal valued twice: at the August it was made, '
                 'and at today. Picks since used are resolved to the player '
                 'taken with them (drafts.json); picks not yet used are priced '
                 'on today chart for the wait that is left. A player with no '
                 'current value is off the board and worth nothing, which is '
                 'an answer rather than a gap. Built by '
                 'scripts/build_trade_hindsight.py.'),
        'nowSeason': B.now,
        'lastDraft': last_draft,
        'winThreshold': TC_WIN,
        'count': len(out),
        'skipped3way': skipped,
        'withUnresolved': sum(1 for x in out if x['unresolved']),
        'firm': len(firm),
        'changedVerdict': flips,
        'reversed': rev,
        'trades': out,
    }
    p = os.path.join(ROOT, OUT)
    json.dump(d, open(p, 'w', encoding='utf-8'), indent=1)
    print(f'  {OUT}: {len(out)} two-team deals, {skipped} three-team left out')
    print(f'  {len(firm)} fully resolved; {d["withUnresolved"]} carry a pick that '
          f'could not be resolved')
    print(f'  verdict changes between the two readings: {flips} '
          f'({rev} outright reversals, win to loss or back)')


if __name__ == '__main__':
    main()
