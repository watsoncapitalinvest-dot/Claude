#!/usr/bin/env python3
"""Recovery/ebb-and-flow analysis for the Study — see docs/STUDY-RECOVERY-FINDINGS.md.

    python3 scripts/study_recovery.py

Pure read-only analysis over history.json (18 seasons, 2008-2025) resolved
through scfl-franchises.json's owner-handle map -- the same real standings
the Trade Court's pick model and the Franchise Directory already use. No
output file; this prints the same numbers that went into the findings doc,
so re-running it after a new season is committed re-derives everything
(nothing here is hand-copied from a one-off analysis).
"""
import json, os, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return json.load(f)

def rank_trajectories():
    fr = load('scfl-franchises.json')
    hist = load('history.json')
    handles = fr['handles']
    by_season = {}
    for s in hist['seasons']:
        owner_by_teamid = {t['id']: t['owner'] for t in s['teams']}
        ranks = {}
        for row in s.get('standings', []):
            owner = owner_by_teamid.get(row['teamId'])
            key = handles.get(owner)
            if key and row.get('rank'):
                ranks[key] = row['rank']
        by_season[s['year']] = ranks
    traj = {}
    for year in sorted(by_season):
        for key, rank in by_season[year].items():
            traj.setdefault(key, []).append((year, rank))
    return fr, traj

def franchise_profiles(fr, traj):
    franchises = {f['key']: f for f in fr['franchises']}
    active_keys = [k for k, f in franchises.items() if f.get('active')]
    results = []
    for key in active_keys:
        t = sorted(traj.get(key, []))
        if len(t) < 3:
            continue
        worst = max(t, key=lambda x: x[1])
        best = min(t, key=lambda x: x[1])
        titles = set(franchises[key].get('titles', []))
        swings = []
        for i in range(1, len(t)):
            y0, r0 = t[i - 1]
            y1, r1 = t[i]
            if y1 == y0 + 1:
                swings.append((y0, r0, y1, r1, r0 - r1))
        biggest_recovery = max(swings, key=lambda s: s[4], default=None)
        biggest_collapse = min(swings, key=lambda s: s[4], default=None)
        vol = statistics.pstdev([r for _, r in t]) if len(t) > 1 else 0
        results.append({
            'key': key, 'club': franchises[key]['club'], 'manager': franchises[key].get('manager'),
            'seasons': len(t), 'worst': worst, 'best': best, 'titles': sorted(titles),
            'biggest_recovery': biggest_recovery, 'biggest_collapse': biggest_collapse,
            'volatility': round(vol, 2), 'recent': t[-3:],
        })
    results.sort(key=lambda r: -r['volatility'])
    return results

def title_hangovers(fr, traj):
    franchises = {f['key']: f for f in fr['franchises']}
    out = []
    for key, f in franchises.items():
        t = dict(traj.get(key, []))
        for ty in f.get('titles', []):
            nxt = t.get(ty + 1)
            if nxt is not None:
                out.append({'club': f['club'], 'title_year': ty, 'next_year_rank': nxt, 'hangover': nxt > 8})
    return out

def recovery_times(fr, traj):
    franchises = {f['key']: f for f in fr['franchises']}
    out = []
    for key, f in franchises.items():
        if not f.get('active'):
            continue
        t = sorted(traj.get(key, []))
        for i, (y, r) in enumerate(t):
            if r >= 14:
                for y2, r2 in t[i + 1:]:
                    if r2 <= 3:
                        out.append(y2 - y)
                        break
    return out

def trade_activity_vs_volatility(fr, profiles):
    """dossier.json keys each manager entry by TEAM name, not the person --
    resolve on club (with alias fallback for the parenthetical variants),
    not on the 'manager' field, which only coincidentally matches for a
    few teams where we don't have the real person's name on file."""
    import os, re
    dossier = json.load(open(os.path.join(ROOT, 'dossier.json'), encoding='utf-8'))
    alias_to_key = {}
    for f in fr['franchises']:
        alias_to_key[f['club'].lower()] = f['key']
        for a in f.get('aliases', []):
            alias_to_key[a.lower()] = f['key']
    vol_by_key = {p['key']: p['volatility'] for p in profiles}
    rows = []
    for m in dossier.get('managers', []):
        tp = m.get('tradingProfile')
        if not tp:
            continue
        base = re.split(r'[(/]', m['name'])[0].strip().lower()
        key = alias_to_key.get(base) or alias_to_key.get(m['name'].lower())
        if key and key in vol_by_key:
            rows.append((m['name'], tp['trades'], vol_by_key[key]))
    if len(rows) < 3:
        return rows, None
    xs = [r[1] for r in rows]
    ys = [r[2] for r in rows]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    r = cov / (sx * sy) if sx * sy else 0
    return rows, r

if __name__ == '__main__':
    fr, traj = rank_trajectories()
    profiles = franchise_profiles(fr, traj)
    vols = [p['volatility'] for p in profiles]
    print(f"Field volatility: mean {statistics.mean(vols):.2f}, median {statistics.median(vols)}, "
          f"min {min(vols)}, max {max(vols)}")
    for p in profiles:
        z = (p['volatility'] - statistics.mean(vols)) / statistics.pstdev(vols)
        print(f"  {p['club']:20} vol={p['volatility']:5} (z={z:+.2f})  worst={p['worst']}  best={p['best']}  titles={p['titles']}")

    print("\nTitle hangovers (finished bottom-half the year after winning it):")
    hangovers = title_hangovers(fr, traj)
    for h in hangovers:
        if h['hangover']:
            print(f"  {h['club']}: won {h['title_year']}, finished {h['next_year_rank']}th the next year")
    print(f"  {sum(h['hangover'] for h in hangovers)}/{len(hangovers)} champions hangover'd")

    rt = recovery_times(fr, traj)
    print(f"\nRecovery time (rank>=14 -> next rank<=3): n={len(rt)}, "
          f"mean={statistics.mean(rt):.1f}yrs, median={statistics.median(rt)}, range {min(rt)}-{max(rt)}")

    rows, r = trade_activity_vs_volatility(fr, profiles)
    print(f"\nTrade activity vs. volatility (n={len(rows)}):")
    for name, trades, vol in sorted(rows, key=lambda x: -x[1]):
        print(f"  {name:45} trades={trades:3}  volatility={vol}")
    if r is not None:
        print(f"  correlation r = {r:.3f}")
