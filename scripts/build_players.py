#!/usr/bin/env python3
"""Build players.json — the Ledger behind the app's player pages.

Every player who has ever appeared in an SCFL trade gets an entry: each deal he
was part of, who sent him, who got him, what went back, and where he sits today.

    python3 scripts/build_players.py

Sources: trades.json (256 deals, 2021-2026) and scfl-rosters.json (current
rosters + positions). Names in the ledger are hand-typed and full of variants
("Diontate Johnson", "Zack Wilson", bare surnames), so they are canonicalised
conservatively -- see resolve_names(). The build refuses to write if the asset
count changes, which catches a merge that silently swallowed a real player.
"""
import json, os, re, collections, difflib, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Roster exports use their own labels; map only the unambiguous ones. Forty2V has
# no confident match in the trade ledger, so it keeps its own name rather than
# being guessed into an existing franchise.
ROSTER_ALIAS = {
 'New Wod Order': 'New World Order', '*THE MACHINES*': 'The Machines',
 'Beaver Eaters': 'The Beaver Eaters', 'Gumbas': 'Hairy Gumbas',
 'Lil’ Chops': 'Lil Chops', 'StillTheCream': 'Still The Creamiest',
 'Master-Jeti': 'The Jet-I', 'BIG BLUE': 'Big Blue',
}
# Franchises rename constantly; these are the same shop across the ledger.
TEAM_ALIAS = {
 'The Jet - I': 'The Jet-I', 'Porky’s': 'Lil Chops', "Porky's": 'Lil Chops',
 'The A-Team': 'Lil Chops', 'Disciples of Darnold': 'Lil Chops',
}


# The ledger is hand-typed, so the most common spelling is sometimes the wrong
# one. These are real players; print their names correctly.
DISPLAY_FIX = {
 'Chubba Hubbard': 'Chuba Hubbard', 'Demarco Douglas': 'Demario Douglas',
 'Darrel Henderson': 'Darrell Henderson', 'Taysum Hill': 'Taysom Hill',
 'Khail Herbert': 'Khalil Herbert', "D'onta Foreman": "D'Onta Foreman",
 'Donavan Peoples Jones': 'Donovan Peoples-Jones', 'Deandre Hopkins': 'DeAndre Hopkins',
 'Amon-Ra St Brown': 'Amon-Ra St. Brown', 'JK Dobbins': 'J.K. Dobbins',
 'Jamis Winston': 'Jameis Winston', 'Jacoby Meyers': 'Jakobi Meyers',
 'Jacory Croskey-Merritt': 'Jacory Croskey-Merritt', 'Shaduer Sanders': 'Shedeur Sanders',
 'Montegomery': 'David Montgomery', 'Dandre Swift': "D'Andre Swift",
 'Rocshon Johnson': 'Roschon Johnson', 'Alexander Mattison': 'Alexander Mattison',
 'A. Mattison': 'Alexander Mattison', 'Isiah Likely': 'Isaiah Likely',
 'Elic Ayomanor': 'Elic Ayomanor', 'Jeff Wilson Jr': 'Jeff Wilson Jr.',
 'Odell Beckham Jr': 'Odell Beckham Jr.', 'Marvin Jones Jr': 'Marvin Jones Jr.',
 'Brian Robinson Jr': 'Brian Robinson Jr.', 'Tony Jones Jr': 'Tony Jones Jr.',
 'TJ Hockenson': 'T.J. Hockenson', 'Zach Ertz': 'Zach Ertz',
}

def norm(n):
    n = n.lower().replace('.', '').replace("'", '').replace('’', '').replace('-', ' ')
    n = re.sub(r'\b(jr|iii|ii|sr)\b', '', n)
    return re.sub(r'\s+', ' ', n).strip()

def resolve_names(counts):
    """Canonical name per player. Two conservative rules, no free-form fuzzing:
    1. strings that are identical once normalised collapse together;
    2. a bare surname folds into a full name only when exactly one full name in
       the data ends with it.
    Near-miss typos are merged only when the surnames themselves clearly match,
    and the most frequently used spelling wins."""
    canon = {}
    by_norm = collections.defaultdict(list)
    for n in counts: by_norm[norm(n)].append(n)
    for k, v in by_norm.items():
        best = max(v, key=lambda x: (counts[x], len(x)))
        for x in v: canon[x] = best
    full = [n for n in counts if len(norm(n).split()) > 1]
    for n in [x for x in counts if len(norm(x).split()) == 1]:
        hits = {canon[f] for f in full if norm(f).split()[-1] == norm(n)}
        if len(hits) == 1: canon[n] = sorted(hits)[0]
    reps = sorted({canon[n] for n in counts})
    for i, a in enumerate(reps):
        for b in reps[i + 1:]:
            ka, kb = norm(a), norm(b)
            if ka == kb or canon.get(a) == canon.get(b): continue
            if len(ka.split()) < 2 or len(kb.split()) < 2: continue
            if difflib.SequenceMatcher(None, ka, kb).ratio() <= 0.87: continue
            if difflib.SequenceMatcher(None, ka.split()[-1], kb.split()[-1]).ratio() <= 0.75: continue
            keep, drop = (a, b) if counts[a] >= counts[b] else (b, a)
            for n in list(canon):
                if canon[n] == drop: canon[n] = keep
    return canon

def build():
    T = json.load(open(os.path.join(ROOT, 'trades.json'), encoding='utf-8'))['trades']
    counts = collections.Counter()
    for x in T:
        for s in x['sides']:
            for g in s['gets']:
                if 'player' in g: counts[g['player'].strip()] += 1
    canon = resolve_names(counts)
    team = lambda t: TEAM_ALIAS.get(t.strip(), t.strip())

    players = collections.defaultdict(lambda: {'trades': [], 'teams': []})
    assets = 0
    for x in T:
        season = x.get('season')
        for s in x['sides']:
            others = [o for o in x['sides'] if o is not s]
            back = [g.get('player') or g.get('pick') for o in others for g in o['gets']]
            mates = [DISPLAY_FIX.get(canon.get((g.get('player') or '').strip(), g.get('player')),
                                    canon.get((g.get('player') or '').strip(), g.get('player')))
                     for g in s['gets'] if 'player' in g]
            for g in s['gets']:
                if 'player' not in g: continue
                assets += 1
                _c = canon[g['player'].strip()]
                name = DISPLAY_FIX.get(_c, _c)
                p = players[name]
                p['trades'].append({'s': season, 'to': team(s['team']),
                                    'from': [team(o['team']) for o in others],
                                    'with': [m for m in mates if m != name],
                                    'back': back})
                p['teams'].append(team(s['team']))
    assert assets == sum(counts.values()), 'player-asset count changed during canonicalisation'

    rost = json.load(open(os.path.join(ROOT, 'scfl-rosters.json'), encoding='utf-8'))
    now = {}
    for t, roster in rost['teams'].items():
        for pl in roster:
            now[norm(pl['name'])] = {'team': ROSTER_ALIAS.get(t.strip(), t.strip()),
                                     'pos': pl.get('pos')}
    out = []
    for name, p in players.items():
        cur = now.get(norm(name)) or {}
        trades = sorted(p['trades'], key=lambda t: (t['s'] or 0))
        # the route he actually took: collapse only consecutive repeats, so a
        # player returning to a former team still shows the return
        path = []
        for t in trades:
            if not path or path[-1] != t['to']: path.append(t['to'])
        out.append({'n': name, 'pos': cur.get('pos'), 'team': cur.get('team'),
                    'moves': len(trades), 'teams': sorted(set(p['teams'])),
                    'path': path, 'trades': trades})
    out.sort(key=lambda p: (-p['moves'], p['n']))
    payload = {'note': 'built by scripts/build_players.py from trades.json + scfl-rosters.json',
               'season': rost.get('season'), 'count': len(out), 'players': out}
    json.dump(payload, open(os.path.join(ROOT, 'players.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    return out, counts, canon

if __name__ == '__main__':
    out, counts, canon = build()
    merged = len(counts) - len({canon[n] for n in counts})
    rostered = sum(1 for p in out if p['team'])
    print(f"players: {len(out)}  (from {len(counts)} raw strings, {merged} variants merged)")
    print(f"player-assets indexed: {sum(p['moves'] for p in out)}")
    print(f"currently rostered: {rostered} | no longer in the league: {len(out) - rostered}")
    print("\nmost-traded:")
    for p in out[:8]:
        print(f"   {p['moves']}x  {p['n']:26s} {' -> '.join(p['teams'])[:78]}")
