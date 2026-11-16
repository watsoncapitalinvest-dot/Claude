#!/usr/bin/env python3
"""Act 1 Cobra simulation, v3: option C, the full hidden network (STORY, 16 Nov 2026).

v3 = v2 + John 13:43/13:51 (BUILD 13:55 note): Cobra starts with 3 front companies, 2 depots, 2 cells, all
hidden; cell strikes from month 2; terror is not Drome-only (rarer and smaller before a Drome).

v2 header follows.

v1 (act1_cobra_sim.py) modelled the game as shipped. This models the proposed Act 1
(GAME LOGIC doc, "Act 1 as the game actually runs it today", John 10:01 "incentivize,
never force", 11:10 "C"). Nothing is forced; every new rule is a named constant.

Usage: python3 act1_cobra_sim_v2.py [runs]
"""
import random, statistics, sys, yaml, os

HERE = os.path.dirname(os.path.abspath(__file__))
SITES = {
    'FRONT':     dict(cost=400, funds=120, uf=10, mat=0,  um=0,  mc=0,  benches=0, odds=66, loot=60),
    'FACTORY':   dict(cost=600, funds=0,   uf=40, mat=80, um=0,  mc=48, benches=0, odds=44, loot=0),
    'CAMP':      dict(cost=500, funds=0,   uf=30, mat=0,  um=20, mc=0,  benches=0, odds=26, loot=0),
    'DEPOT':     dict(cost=300, funds=0,   uf=10, mat=0,  um=0,  mc=0,  benches=0, odds=26, loot=0),
    'LAB':       dict(cost=200, funds=0,   uf=25, mat=0,  um=10, mc=0,  benches=1, odds=45, loot=0),
    'BROADCAST': dict(cost=450, funds=0,   uf=30, mat=0,  um=0,  mc=0,  benches=0, odds=18, loot=0),
    'DROME':     dict(cost=450, funds=0,   uf=50, mat=0,  um=30, mc=0,  benches=4, odds=0,  loot=200),
}
MONTHS = 18
BUILD_START = 2
WELL_SUPPLIED = 50
KIT_CAP = {0: 0, 3: 1, 8: 2, 14: 3}

# ---- fix 4: the hidden starting network ----------------------------------------
START = dict(funds=400, materiel=150, sites=['FRONT'] * 3 + ['DEPOT'] * 2 + ['CELL'] * 2, hidden_find_mult=0.5)
OFFMAP_BENCHES = 3            # fix 5: Cobra Commander's own lab, off the map, can't be raided in Act 1
# ---- fix 3: front companies under the planner, capped ---------------------------
def front_cap(other_sites):
    return 2 + other_sites // 3
# ---- fix 2: crime that pays before the Drome ------------------------------------
CRIME_ODDS = 0.25             # per launcher per month, before a Drome (v2 0.40; option C has 5 launchers at start)
CRIME_PAYS = 150              # a robbery that gets away
CELL_FROM_MONTH = None        # option C: cells exist from day 1
TERROR_FIRST_MONTH = 4        # Cobra can stage a terror attack for money and Fear
TERROR_PRE_DROME = 0.15       # network terror, a month, before a Drome (rarer and smaller)
CELL_STRIKE_FROM = 2          # NEW mission: a cell hits a civilian target
CELL_STRIKE_ODDS = 0.20       # per cell per month
TERROR_PER_DROME = 0.9
# ---- fix 1: Cobra Commander's will --------------------------------------------
DROME_FROM = 8
DONOR_STEP = 50               # backers' money, per month past month 8, cumulative
START_BUILDING_AT = 0.5       # starts building once half the cost is saved
MIN_BUILD_MONTHS = 2
# ---- the network sends money to a region going broke (John 13 Nov, ledger 1.7) ----
TRANSFER_FROM = 2
TRANSFER_TARGET_SITES = 4     # Cobra wants at least this many working sites in the region
TRANSFER_PER_MISSING = 150    # flown in as a cargo run the Joes can intercept
B_NEEDS_MONTHS = 2            # ending B: the network stays broken this long, after month 8
# ---- fix 5: research incentive ---------------------------------------------------
PUSH_PAST_LATEST = 2.0        # past its window, Cobra puts double behind a topic

# the Drome can only be found once the interrogation spine has located it (Terror Drome
# Plans raid); month the player's spine gets there, from pacing.py's Act 1 estimates
SPINE_LOCATES_DROME = dict(absent=None, cautious=12, typical=10.5, aggressive=9.5)

STYLES = {
    'absent':     dict(find=0.0,  raids=0.0, factory=0.0, intercept=0.0,  respond=0.0, assault=0.0),
    'cautious':   dict(find=0.25, raids=0.5, factory=0.3, intercept=0.05, respond=0.3, assault=0.5),
    'typical':    dict(find=0.40, raids=1.0, factory=0.6, intercept=0.15, respond=0.5, assault=0.8),
    'aggressive': dict(find=0.55, raids=2.0, factory=0.9, intercept=0.30, respond=0.7, assault=1.0),
}

def load_tree():
    t = yaml.safe_load(open(os.path.join(HERE, 'cobra_tree.yml')))['cobraResearchTopics']
    out = []
    for x in t:
        e = x.get('earliestMonth')
        if x.get('doneAtStart') or e is None or e > 12:
            continue
        tier = next((int(u.split(':')[1]) for u in x.get('unlocks', []) if u.startswith('kitTier:')), None)
        out.append(dict(name=x['type'].replace('STR_COBRA_', ''), dept=x['department'], cost=x['cost'],
                        mpp=x.get('materielPerProgress', 0) or 0, early=e, late=x.get('latestMonth'),
                        req=[r.replace('STR_COBRA_', '') for r in x.get('requires', [])], tier=tier))
    return out
TREE = load_tree()

def run(style, rng):
    st = STYLES[style]
    sites = [dict(type=t, found=False, hidden=True) for t in START['sites']]
    funds, mat = START['funds'], START['materiel']
    done, prog = {}, {t['name']: 0 for t in TREE}
    drome = dict(saved=0, building=None, built=None)   # building: month started
    L = dict(end=None, version=None, terror=0, first_terror=None, rifles=None, dry=0, peak=0,
             fronts=0, crime_paid=0, strikes=0, drome_built=None, drome_started=None)
    factory_live = rng.random() >= st['factory']
    loc = SPINE_LOCATES_DROME[style]
    spine_m = None if loc is None else loc + rng.uniform(-1.5, 1.5)
    for m in range(MONTHS):
        if m == 2 and factory_live:
            sites.append(dict(type='FACTORY', found=True, hidden=False))
        types = [s['type'] for s in sites]
        econ = [t for t in types if t in SITES]
        # income, upkeep, production
        inc = sum(SITES[t]['funds'] for t in econ if SITES[t]['funds'] and rng.random() >= st['intercept'])
        funds = max(0, funds + inc - sum(SITES[t]['uf'] for t in econ))
        mat = max(0, mat - sum(SITES[t]['um'] for t in econ))
        for t in econ:
            if SITES[t]['mat']:
                pay = min(funds, SITES[t]['mc']); funds -= pay
                mat += SITES[t]['mat'] * pay // SITES[t]['mc']
        has_drome = 'DROME' in types
        if m >= TRANSFER_FROM:
            missing = max(0, TRANSFER_TARGET_SITES - len(econ))
            if missing and rng.random() >= st['intercept']:
                funds += TRANSFER_PER_MISSING * missing
        # fix 2: crime before the Drome
        if not has_drome:
            launchers = types.count('FRONT') + types.count('CELL')
            for _ in range(launchers):
                if rng.random() < CRIME_ODDS:
                    if rng.random() < st['respond']:
                        for s in sites:           # a caught crime is a lead
                            if s['type'] in ('FRONT', 'CELL') and not s['found']:
                                s['found'] = True; break
                    else:
                        funds += CRIME_PAYS; L['crime_paid'] += 1
            if m >= CELL_STRIKE_FROM:
                L['strikes'] += sum(1 for _ in range(types.count('CELL')) if rng.random() < CELL_STRIKE_ODDS)
            if m >= TERROR_FIRST_MONTH and rng.random() < TERROR_PRE_DROME:
                L['terror'] += 1; L['first_terror'] = L['first_terror'] if L['first_terror'] is not None else m
        else:
            n = sum(1 for _ in range(types.count('DROME')) if rng.random() < TERROR_PER_DROME)
            if n:
                L['terror'] += n; L['first_terror'] = L['first_terror'] if L['first_terror'] is not None else m
        # research: off-map benches + labs + Drome
        benches = OFFMAP_BENCHES + sum(SITES[t]['benches'] for t in econ)
        busy = set()
        for t in TREE:
            if t['name'] in done or m < t['early'] or t['dept'] in busy or benches <= 0:
                continue
            if any(r not in done for r in t['req']):
                continue
            busy.add(t['dept']); benches -= 1
            pts = 10 * (PUSH_PAST_LATEST if t['late'] is not None and m >= t['late'] else 1)
            if t['mpp']:
                pts = min(pts, mat // t['mpp']); mat -= int(pts * t['mpp'])
            prog[t['name']] += pts
            if prog[t['name']] >= t['cost']:
                done[t['name']] = m
        # fix 1: Cobra Commander's will (from month 8, the Drome comes first after the reserve)
        reserve = sum(SITES[t]['uf'] for t in econ)
        if m >= DROME_FROM and not has_drome:
            drome['saved'] += DONOR_STEP * (m - DROME_FROM + 1)
            spare = max(0, funds - reserve); drome['saved'] += spare; funds -= spare
            if drome['building'] is None and drome['saved'] >= SITES['DROME']['cost'] * START_BUILDING_AT:
                drome['building'] = m; L['drome_started'] = m
                sites.append(dict(type='DROME_BUILDING', found=False, hidden=False))
            if (drome['building'] is not None and drome['saved'] >= SITES['DROME']['cost']
                    and m - drome['building'] >= MIN_BUILD_MONTHS):
                for s in sites:
                    if s['type'] == 'DROME_BUILDING':
                        s['type'] = 'DROME'
                drome['built'] = m; L['drome_built'] = m
        # the planner (real rules) for everything else, fix 3 caps the fronts
        econ = [s['type'] for s in sites if s['type'] in SITES]
        if m >= BUILD_START and not (m >= DROME_FROM and not has_drome):
            planning = 'DROME' in econ
            net_f = sum(SITES[t]['funds'] - SITES[t]['uf'] for t in econ)
            net_m = sum(SITES[t]['mat'] - SITES[t]['um'] for t in econ)
            others = len([t for t in econ if t != 'FRONT'])
            for t, r in SITES.items():
                if t == 'DROME': continue
                have = econ.count(t)
                earner = r['funds'] > r['uf']; maker = r['mat'] > r['um']
                if t == 'FRONT':
                    wanted = have < front_cap(others)
                elif not planning: wanted = have == 0
                elif net_f <= 0: wanted = earner
                elif net_m < 0 and maker: wanted = True
                else: wanted = have == 0
                if wanted and funds - reserve >= r['cost'] and rng.random() * 100 < r['odds']:
                    funds -= r['cost']; sites.append(dict(type=t, found=False, hidden=False)); econ.append(t)
        # the player
        loc = SPINE_LOCATES_DROME[style]
        for s in sites:
            p = st['find'] * (START['hidden_find_mult'] if s['hidden'] else 1)
            if s['type'] in ('DROME', 'DROME_BUILDING'):
                p = 1.0 if (loc is not None and m >= spine_m) else 0.0
            if not s['found'] and rng.random() < p:
                s['found'] = True
        prio = ['DROME', 'DROME_BUILDING', 'FACTORY', 'FRONT', 'CELL', 'LAB', 'DEPOT', 'CAMP', 'BROADCAST']
        n = int(st['raids']) + (1 if rng.random() < st['raids'] % 1 else 0)
        for _ in range(n):
            found = sorted([s for s in sites if s['found']], key=lambda s: prio.index(s['type']))
            if not found: break
            tgt = found[0]
            if tgt['type'] in ('DROME', 'DROME_BUILDING'):
                if rng.random() < st['assault']:
                    L['end'] = m; L['version'] = 'A: Drome assault (finished)' if tgt['type'] == 'DROME' else 'A: Drome assault (unfinished)'
                    break
                continue
            sites.remove(tgt)
            if tgt['type'] in SITES: funds = max(0, funds - SITES[tgt['type']]['loot'])
            if tgt['type'] == 'DEPOT': mat = 0
        if L['end'] is not None: break
        # ending B: the network broken after month 8
        econ = [s['type'] for s in sites]
        if m >= DROME_FROM and not any(t in econ for t in ('FRONT', 'FACTORY', 'DROME', 'DROME_BUILDING')):
            L['broken'] = L.get('broken', 0) + 1
            if L['broken'] >= B_NEEDS_MONTHS:
                L['end'] = m; L['version'] = 'B: network broken'; break
        else:
            L['broken'] = 0
        # the Drome strike if left alone 3 months
        if drome['built'] is not None and m - drome['built'] >= 3:
            L['end'] = m; L['version'] = 'Drome strike'; break
        if L['rifles'] is None and done.get('RIFLES') is not None and mat >= WELL_SUPPLIED:
            L['rifles'] = m
        if mat < WELL_SUPPLIED: L['dry'] += 1
        L['peak'] = max(L['peak'], len(sites)); L['fronts'] = max(L['fronts'], econ.count('FRONT'))
    return L

def main():
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    rng = random.Random(1)
    print(f'Act 1 v3 (option C: full hidden network), {runs} runs, up to {MONTHS} months')
    for style in STYLES:
        Ls = [run(style, rng) for _ in range(runs)]
        def med(k):
            v = [l[k] for l in Ls if l[k] is not None]
            return f'{statistics.median(v):g} ({len(v) * 100 // runs}%)' if v else 'never'
        vers = {}
        for l in Ls: vers[l['version'] or 'not over by month 18'] = vers.get(l['version'] or 'not over by month 18', 0) + 1
        vtxt = ', '.join(f'{k} {v * 100 // runs}%' for k, v in sorted(vers.items(), key=lambda x: -x[1]))
        print(f'\n{style}: Act 1 ends month {med("end")}; {vtxt}')
        print(f'  first terror month {med("first_terror")}, terror attacks {statistics.median(l["terror"] for l in Ls):g}, '
              f'robberies that paid {statistics.median(l["crime_paid"] for l in Ls):g}, cell strikes {statistics.median(l["strikes"] for l in Ls):g}')
        print(f'  Drome started {med("drome_started")}, finished {med("drome_built")}; rifles in the field {med("rifles")}; '
              f'months on sidearms {statistics.median(l["dry"] for l in Ls):g}; peak sites {statistics.median(l["peak"] for l in Ls):g}, '
              f'peak fronts {statistics.median(l["fronts"] for l in Ls):g}')

if __name__ == '__main__':
    main()
