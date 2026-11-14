"""ROSTER stat model (John 12 Nov 21:16: unnamed cap stays 75-80% of named; named Joes very good, by rank and specialty).
named = specialty template (E-5 baseline) + rank bonus + 25% of the secondary's lead + canon nudge; fixed for the game.
unnamed (per specialty): cap = 78% of template; start = min(decided greenshirt start, 70% of template)."""
import json
K = ['TU', 'Sta', 'HP', 'Brav', 'React', 'Fire', 'Throw', 'Str', 'Melee']
T = {  # E-5 named template per specialty ("very good")
 'Command':            [80, 80, 58, 90, 80, 82, 72, 52, 66],
 'Infantry':           [80, 85, 60, 80, 80, 88, 76, 56, 70],
 'Heavy Weapons':      [74, 90, 66, 80, 72, 84, 72, 72, 66],
 'Martial Arts':       [90, 85, 56, 90, 90, 76, 82, 56, 100],
 'Covert Ops & Intel': [84, 78, 54, 85, 86, 84, 78, 46, 78],
 'Comms & Tech':       [76, 74, 52, 75, 76, 78, 70, 46, 60],
 'Medic':              [76, 78, 54, 85, 74, 68, 70, 46, 58],
 'Pilot':              [74, 72, 52, 80, 88, 78, 66, 46, 56],
 'Airborne':           [82, 88, 58, 85, 82, 84, 76, 56, 72],
 'Recon & Sniper':     [78, 80, 54, 80, 86, 95, 74, 48, 64],
 'Demolitions & Engineering': [74, 80, 58, 78, 74, 78, 88, 58, 62],
 'Armor & Vehicles':   [74, 78, 58, 78, 80, 80, 68, 56, 62],
 'Naval & Divers':     [78, 90, 58, 80, 78, 80, 74, 58, 68],
 'Arctic & Mountain':  [80, 92, 60, 80, 78, 84, 74, 58, 66],
}
# rank bonus: experience shows in bravery, reactions, firing, TU
RANK = {'E-4': -3, 'E-5': 0, 'E-6': 2, 'E-7': 4, 'E-8': 6, 'E-9': 7, 'O-2': 3, 'O-3': 5, 'O-4': 6, 'O-6': 8, 'W-4': 5}
OFFICER_BRAV = {'O-2': 5, 'O-3': 5, 'O-4': 5, 'O-6': 10, 'W-4': 4}
J = [  # name, rank, primary, secondary, nudge
 ('Hawk', 'O-6', 'Command', 'Comms & Tech', {}),
 ('Duke', 'E-8', 'Command', None, {'Fire': 3}),
 ('Roadblock', 'E-6', 'Heavy Weapons', None, {'Str': 10, 'HP': 6, 'TU': -4}),
 ("Rock 'n Roll", 'E-7', 'Heavy Weapons', None, {'Sta': 5, 'Str': 5}),
 ('Grand Slam', 'E-5', 'Heavy Weapons', 'Comms & Tech', {}),
 ('Short-Fuze', 'E-6', 'Heavy Weapons', 'Demolitions & Engineering', {'Throw': 4}),
 ('Zap', 'E-4', 'Heavy Weapons', 'Demolitions & Engineering', {}),
 ('Grunt', 'E-5', 'Infantry', None, {'React': 5}),
 ('Stalker', 'E-9', 'Infantry', 'Command', {'Sta': 5}),
 ('Breaker', 'E-5', 'Comms & Tech', None, {}),
 ('Flash', 'E-5', 'Comms & Tech', None, {'Fire': 4}),
 ('Scarlett', 'E-5', 'Covert Ops & Intel', 'Martial Arts', {}),
 ('Snake Eyes', 'E-8', 'Martial Arts', None, {'Melee': 10, 'React': 4}),
 ('Doc', 'O-3', 'Medic', None, {'Fire': -18}),
 ('Ace', 'O-3', 'Pilot', None, {'React': 4}),
 ('Airborne', 'E-7', 'Airborne', 'Medic', {}),
]
GS = dict(zip(K, [55, 60, 35, 40, 50, 55, 55, 30, 45]))  # decided greenshirt start (DAY1_SETUP §7)
CAP = {'TU': 99, 'Sta': 100, 'HP': 80, 'Brav': 100, 'React': 100, 'Fire': 110, 'Throw': 110, 'Str': 90, 'Melee': 120}
def named(rank, prim, sec, nudge):
    v = dict(zip(K, T[prim])); r = RANK[rank]
    if sec:
        for k, s in zip(K, T[sec]): v[k] += max(0, s - v[k]) * 0.25
    v['Brav'] += 2 * r + OFFICER_BRAV.get(rank, 0); v['React'] += r; v['Fire'] += r; v['TU'] += r / 2
    for k, d in nudge.items(): v[k] += d
    out = {k: min(CAP[k], int(round(v[k]))) for k in K}
    out['Brav'] = min(100, int(round(out['Brav'] / 10.0)) * 10)    # OXCE bravery steps of 10
    return out
def unnamed(prim):
    t = dict(zip(K, T[prim]))
    cap = {k: int(round(0.78 * t[k])) for k in K}
    start = {k: min(GS[k], int(round(0.70 * t[k]))) for k in K}
    cap['Brav'] = int(cap['Brav'] // 10 * 10); start['Brav'] = int(start['Brav'] // 10 * 10)
    return start, cap
def main():
    res = {'named': {n: dict(rank=r, primary=p, secondary=s, stats=named(r, p, s, nd)) for n, r, p, s, nd in J},
           'unnamed': {p: dict(zip(('start', 'cap'), unnamed(p))) for p in T}}
    import os; json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stats_day1.json'), 'w'), indent=1)
    print('%-13s %-4s %-26s' % ('Joe', 'rank', 'specialty') + ' '.join('%5s' % k for k in K))
    for n, d in res['named'].items():
        print('%-13s %-4s %-26s' % (n, d['rank'], d['primary'][:26]) + ' '.join('%5d' % d['stats'][k] for k in K))
    print()
    for p, d in res['unnamed'].items():
        print('%-27s start ' % p[:27] + ' '.join('%4d' % d['start'][k] for k in K) + '  | cap ' + ' '.join('%4d' % d['cap'][k] for k in K))
if __name__ == '__main__':
    main()
