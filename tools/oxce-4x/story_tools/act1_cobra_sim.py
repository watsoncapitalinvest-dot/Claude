#!/usr/bin/env python3
"""Act 1 Cobra simulation (STORY, 16 Nov 2026).

Runs Cobra's economy and planner month by month over Act 1 against three player
styles, using the numbers the game actually ships (gijoe_cobra_economy.rul,
zz_gijoe_terror_source.rul, gijoe_cobra_sites.rul build scripts, gijoe_frontops.rul,
gijoe_tuning.rul) and the planner's rules as written in SavedGame::cobraPlan.

It is a model, not the game: where the game rolls dice it rolls the same odds;
where the player acts it uses a simple style. Every assumption is a named
constant below. Usage: python3 act1_cobra_sim.py [runs] [--no-frontops]
"""
import random, statistics, sys

# ---- the shipped numbers -------------------------------------------------
SITES = {  # type: dict(cost, funds, upkeep_f, mat, upkeep_m, mat_cost, benches, odds)
    'FRONT':     dict(cost=400, funds=120, uf=10, mat=0,  um=0,  mc=0,  benches=0, odds=66, loot_f=60),
    'FACTORY':   dict(cost=600, funds=0,   uf=40, mat=80, um=0,  mc=48, benches=0, odds=44, loot_f=0),
    'CAMP':      dict(cost=500, funds=0,   uf=30, mat=0,  um=20, mc=0,  benches=0, odds=26, loot_f=0),
    'DEPOT':     dict(cost=300, funds=0,   uf=10, mat=0,  um=0,  mc=0,  benches=0, odds=26, loot_f=0),
    'LAB':       dict(cost=200, funds=0,   uf=25, mat=0,  um=10, mc=0,  benches=1, odds=45, loot_f=0),
    'DROME':     dict(cost=450, funds=0,   uf=50, mat=0,  um=30, mc=0,  benches=4, odds=25, loot_f=200),
    'BROADCAST': dict(cost=450, funds=0,   uf=30, mat=0,  um=0,  mc=0,  benches=0, odds=18, loot_f=0),
    'HQ':        dict(cost=1200, funds=0,  uf=80, mat=0,  um=20, mc=0,  benches=2, odds=9,  loot_f=200),
}
BUILD_START_MONTH = 2        # startDelay 60 days on every build script
FRONTOPS_ODDS = 75           # gijoe_frontops.rul cobraFronts: from month 1, no maxRuns, ungated
ECON_FRONT_MAXRUNS = 6
WELL_SUPPLIED = 50           # materiel banked to arm at the month's tier
WELL_PAID_MONTHS = 3         # months of upkeep banked to field a full garrison
KIT_CAP = {0: 0, 3: 1, 8: 2, 14: 3}
TERROR_PER_DROME = 0.9       # genMissionFreq 3 % a day
BENCH_POINTS = 10
# BUILD's placeholder projects that matter in Act 1 (gijoe_cobra_economy.rul cobraProjects)
PROJECTS = [  # name, dept, cost, mat per point, earliest, latest, kit tier
    ('Rifles', 'ARMORY', 40, 2, 3, 8, 1),
    ('Lasers', 'ARMORY', 90, 3, 8, 14, 2),
    ('Body armor', 'ARMORY', 60, 2, 10, None, None),
    ('H.I.S.S.', 'MOTOR_POOL', 70, 3, 8, 12, None),
    ('Rattler', 'AIR_WING', 80, 3, 6, None, None),
    ('Patrol boats', 'NAVY', 50, 2, 6, None, None),
    ('Recruitment', 'TROOPS', 40, 1, 4, None, None),
    ('Medicine', 'BIOLOGY', 50, 2, 10, None, None),
]
MONTHS = 15

# ---- player styles (assumptions) -----------------------------------------
STYLES = {
    #            find a site/month   raids/month  hits factory before its date   intercepts a supply flight
    'cautious':   dict(find=0.25, raids=0.5, factory=0.3, intercept=0.05),
    'typical':    dict(find=0.40, raids=1.0, factory=0.6, intercept=0.15),
    'aggressive': dict(find=0.55, raids=2.0, factory=0.9, intercept=0.30),
    'absent':     dict(find=0.0,  raids=0.0, factory=0.0, intercept=0.0),
}

def kit_cap(m):
    return max(v for k, v in KIT_CAP.items() if k <= m)

def run(style, frontops=True, rng=random):
    st = STYLES[style]
    sites = []            # list of dicts: type, found
    funds, mat = 0, 0
    econ_fronts_built = 0
    done, progress = {}, {p[0]: 0 for p in PROJECTS}
    log = dict(drome=None, rifles=None, lasers=None, hiss=None, rattler=None,
               terror=0.0, dry_months=0, thin_months=0, raids=0, peak_sites=0, fronts_peak=0)
    factory_live = rng.random() >= st['factory']
    for m in range(MONTHS):
        # story: the abandoned factory comes back in month 2 if not hit first (day 50-60)
        if m == 2 and factory_live:
            sites.append(dict(type='FACTORY', found=True))
        # --- income, upkeep, production (summed, then applied) ---
        owned = [s['type'] for s in sites]
        inc = sum(SITES[t]['funds'] for t in owned
                  if not (SITES[t]['funds'] and rng.random() < st['intercept']))
        upk = sum(SITES[t]['uf'] for t in owned)
        funds = max(0, funds + inc - upk)
        mat = max(0, mat - sum(SITES[t]['um'] for t in owned))
        for t in owned:
            if SITES[t]['mat']:
                pay = min(funds, SITES[t]['mc'])
                funds -= pay
                mat += SITES[t]['mat'] * pay // SITES[t]['mc']
        # --- research: one project per department, benches shared ---
        benches = sum(SITES[t]['benches'] for t in owned)
        depts_busy = set()
        for name, dept, cost, mpp, early, late, tier in PROJECTS:
            if name in done or m < early or dept in depts_busy:
                continue
            if late is not None and m >= late:
                done[name] = m; continue
            if benches <= 0:
                continue
            depts_busy.add(dept); benches -= 1
            pts = BENCH_POINTS
            if mpp:
                pts = min(pts, mat // mpp)
                mat -= pts * mpp
            progress[name] += pts
            if progress[name] >= cost:
                done[name] = m
        # --- the planner (SavedGame::cobraPlan) ---
        owned = [s['type'] for s in sites]
        net_f = sum(SITES[t]['funds'] - SITES[t]['uf'] for t in owned)
        net_m = sum(SITES[t]['mat'] - SITES[t]['um'] for t in owned)
        planning = 'DROME' in owned or 'HQ' in owned
        has_earner = 'FRONT' in owned
        wants = []
        if m >= BUILD_START_MONTH:
            for t, r in SITES.items():
                have = owned.count(t)
                earner = r['funds'] > r['uf']; maker = r['mat'] > r['um']
                if not planning: wanted = True
                elif net_f <= 0: wanted = earner
                elif net_m < 0 and maker: wanted = True
                else: wanted = have == 0
                afford = funds >= r['cost'] or (t == 'FRONT' and not has_earner)
                if t == 'FRONT' and econ_fronts_built >= ECON_FRONT_MAXRUNS:
                    wanted = False
                if wanted and afford:
                    wants.append(t)
        for t in wants:
            if rng.random() * 100 < SITES[t]['odds']:
                if t != 'FRONT' or has_earner:
                    if funds < SITES[t]['cost']:
                        continue
                    funds -= SITES[t]['cost']
                sites.append(dict(type=t, found=False))
                if t == 'FRONT': econ_fronts_built += 1
                if t == 'DROME' and log['drome'] is None: log['drome'] = m
        if frontops and m >= 1 and rng.random() * 100 < FRONTOPS_ODDS:
            sites.append(dict(type='FRONT', found=False))
        # --- terror ---
        log['terror'] += TERROR_PER_DROME * sum(1 for s in sites if s['type'] == 'DROME')
        # --- the player: find, then raid the best found site ---
        for s in sites:
            if not s['found'] and rng.random() < st['find']:
                s['found'] = True
        n = int(st['raids']) + (1 if rng.random() < st['raids'] % 1 else 0)
        prio = ['DROME', 'FACTORY', 'FRONT', 'LAB', 'DEPOT', 'CAMP', 'BROADCAST', 'HQ']
        for _ in range(n):
            found = [s for s in sites if s['found']]
            if not found: break
            found.sort(key=lambda s: prio.index(s['type']))
            tgt = found[0]; sites.remove(tgt); log['raids'] += 1
            funds = max(0, funds - SITES[tgt['type']]['loot_f'])
            if tgt['type'] == 'DEPOT': mat = 0
        # --- what the garrisons look like ---
        upkeep = sum(SITES[s['type']]['uf'] for s in sites)
        if mat < WELL_SUPPLIED: log['dry_months'] += 1
        if funds < upkeep * WELL_PAID_MONTHS: log['thin_months'] += 1
        log['peak_sites'] = max(log['peak_sites'], len(sites))
        log['fronts_peak'] = max(log['fronts_peak'], sum(1 for s in sites if s['type'] == 'FRONT'))
    for k, nm in (('rifles', 'Rifles'), ('lasers', 'Lasers'), ('hiss', 'H.I.S.S.'), ('rattler', 'Rattler')):
        log[k] = done.get(nm)
    log['funds_end'] = funds; log['sites_end'] = len(sites)
    log['types_end'] = sorted(set(s['type'] for s in sites))
    return log

def summarise(style, runs, frontops):
    logs = [run(style, frontops) for _ in range(runs)]
    def med(k):
        v = [l[k] for l in logs if l[k] is not None]
        return (statistics.median(v), len(v) * 100 // runs) if v else (None, 0)
    out = {k: med(k) for k in ('drome', 'rifles', 'lasers', 'hiss', 'rattler')}
    for k in ('terror', 'dry_months', 'thin_months', 'raids', 'peak_sites', 'fronts_peak', 'funds_end', 'sites_end'):
        out[k] = statistics.median(l[k] for l in logs)
    return out

if __name__ == '__main__':
    runs = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 500
    frontops = '--no-frontops' not in sys.argv
    random.seed(1)
    print(f'Act 1 Cobra sim, {runs} runs each, {MONTHS} months, frontops={"on" if frontops else "off"}')
    print('event = median month it happens (month 0 = Jan 1982), % of runs where it happens at all')
    for style in STYLES:
        o = summarise(style, runs, frontops)
        ev = ' '.join(f'{k}={o[k][0]}({o[k][1]}%)' for k in ('drome', 'rifles', 'lasers', 'hiss', 'rattler'))
        print(f'{style:10s} {ev} | terror={o["terror"]:.1f} dry={o["dry_months"]} thin={o["thin_months"]} '
              f'raids={o["raids"]} peakSites={o["peak_sites"]} peakFronts={o["fronts_peak"]} '
              f'endSites={o["sites_end"]} endFunds={o["funds_end"]}')
