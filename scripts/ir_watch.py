#!/usr/bin/env python3
"""IR Watch — the season-long record of what expanding IR would actually cost.

    python3 scripts/ir_watch.py                 # snapshot this week, append to the log
    python3 scripts/ir_watch.py --report        # read the log back, no fetch
    python3 scripts/ir_watch.py --week 6        # label the snapshot a specific week

Run it once a week, ideally after Tuesday waivers clear. Each run appends one
row to ir-watch.json and never rewrites an old one, so by December the league
has the thing nobody had during the argument: a real record instead of a
preseason snapshot.

WHAT IT MEASURES, AND WHY THAT

A Sleeper IR slot does not hold a player who would otherwise be a free agent.
It holds a player who is already on your roster, and it frees an ACTIVE roster
spot, which the manager then fills from the wire. So the cost of an extra IR
spot is not the injured man. It is the healthy replacement his manager signs
with the spot that opens up -- one player off waivers per filled slot.

That makes the counterfactual computable rather than arguable. The number of
extra players that would leave the pool next week if IR went from 2 to 3 is the
number of managers who today hold an injured player on their ACTIVE roster
while their IR is full. Those managers are constrained right now. Everyone else
would not use the spot, so they cost the pool nothing.

Public read-only Sleeper endpoints. No login. It will not run inside the Claude
Code container -- api.sleeper.app is blocked by the egress policy -- so run it
on your own machine.
"""
import argparse, json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://api.sleeper.app/v1'
LOG = os.path.join(ROOT, 'ir-watch.json')
CACHE = os.path.join(ROOT, '.sleeper-players.json')
UA = {'User-Agent': 'pressbox-ir-watch/1.0'}
# Sleeper marks a man unavailable with one of these. Anything else is healthy.
HURT = {'IR', 'Out', 'Doubtful', 'PUP', 'Sus', 'NA', 'COV', 'DNR'}


def get(path):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(API + path, headers=UA),
                                        timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if i == 2:
                raise
        except Exception as e:
            if i == 2:
                sys.exit(f'could not reach {API}{path}\n  {e}\n\n'
                         'Inside the Claude Code container api.sleeper.app is blocked --\n'
                         'run this on your own machine.')
        time.sleep(1.5 * (i + 1))


def players_db():
    if os.path.exists(CACHE) and time.time() - os.path.getmtime(CACHE) < 86400:
        return json.load(open(CACHE, encoding='utf-8'))
    print('  fetching the NFL player table (~5MB, cached a day)...')
    db = get('/players/nfl')
    json.dump(db, open(CACHE, 'w', encoding='utf-8'))
    return db


def find_league(user, season):
    u = get(f'/user/{user}')
    if not u:
        sys.exit(f'no Sleeper user {user!r}')
    lgs = get(f'/user/{u["user_id"]}/leagues/nfl/{season}') or []
    if not lgs:
        sys.exit(f'{user} is in no {season} leagues')
    if len(lgs) == 1:
        return lgs[0]
    named = [l for l in lgs if 'scfl' in l['name'].lower() or 'skirt' in l['name'].lower()]
    if len(named) == 1:
        return named[0]
    for l in lgs:
        print(f"   {l['league_id']}  {l['name']}")
    sys.exit('several leagues -- pass --league-id')


def snapshot(a):
    season = a.season or str((get('/state/nfl') or {}).get('season') or time.gmtime().tm_year)
    state = get('/state/nfl') or {}
    week = a.week or state.get('week') or 0
    lg = get(f'/league/{a.league_id}') if a.league_id else find_league(a.user, season)
    rosters = get(f"/league/{lg['league_id']}/rosters") or []
    users = {u['user_id']: u for u in (get(f"/league/{lg['league_id']}/users") or [])}
    db = players_db()

    cap = (lg.get('settings') or {}).get('reserve_slots')
    if cap is None:
        cap = 2
    starters = len([p for p in (lg.get('roster_positions') or []) if p != 'BN'])

    def team_of(r):
        u = users.get(r.get('owner_id')) or {}
        return (u.get('metadata') or {}).get('team_name') or u.get('display_name') \
            or f"roster {r.get('roster_id')}"

    def hurt(pid):
        p = db.get(pid) or {}
        return (p.get('injury_status') in HURT) or (p.get('status') in HURT)

    owned, teams = set(), []
    for r in rosters:
        all_ids = list(r.get('players') or [])
        res = list(r.get('reserve') or [])
        active = [p for p in all_ids if p not in res]
        # the men who make the case: injured, but taking up an active spot
        stranded = [p for p in active if hurt(p)]
        owned |= set(all_ids)
        teams.append({
            'team': team_of(r), 'roster_id': r.get('roster_id'),
            'active': len(active), 'ir_used': len(res), 'ir_free': max(0, cap - len(res)),
            'ir_full': len(res) >= cap,
            'stranded': len(stranded),
            'stranded_names': [(db.get(p) or {}).get('full_name') or p for p in stranded][:8],
            # what this manager would actually do with one / two more slots
            'would_use_1': 1 if (len(res) >= cap and len(stranded) >= 1) else 0,
            'would_use_2': min(2, len(stranded)) if len(res) >= cap else 0,
        })

    pool = sum(1 for pid, p in db.items()
               if pid not in owned and p.get('team')
               and p.get('position') in {'QB', 'RB', 'WR', 'TE', 'K', 'DEF'}
               and p.get('status') not in ('Inactive', 'Retired'))

    row = {
        'stamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'season': int(season), 'week': int(week),
        'league': lg['name'], 'league_id': lg['league_id'],
        'ir_cap': cap, 'starters': starters, 'teams_n': len(rosters),
        'ir_used_total': sum(t['ir_used'] for t in teams),
        'ir_capacity_total': cap * len(rosters),
        'teams_at_cap': sum(1 for t in teams if t['ir_full']),
        'teams_empty_ir': sum(1 for t in teams if t['ir_used'] == 0),
        'stranded_total': sum(t['stranded'] for t in teams),
        'constrained': sum(1 for t in teams if t['ir_full'] and t['stranded'] > 0),
        'cost_plus1': sum(t['would_use_1'] for t in teams),
        'cost_plus2': sum(t['would_use_2'] for t in teams),
        'free_agents': pool,
        'teams': teams,
    }
    log = json.load(open(LOG, encoding='utf-8')) if os.path.exists(LOG) else \
        {'note': 'One row per week. Never rewritten. scripts/ir_watch.py', 'rows': []}
    log['rows'] = [r for r in log['rows'] if not (r['season'] == row['season']
                                                  and r['week'] == row['week'])]
    log['rows'].append(row)
    log['rows'].sort(key=lambda r: (r['season'], r['week']))
    json.dump(log, open(LOG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"  logged {lg['name']} week {week}")
    return log


def report(log):
    rows = log['rows']
    if not rows:
        print('no rows yet')
        return
    print(f"\n{'wk':>3} {'IR used':>9} {'at cap':>7} {'empty':>6} {'stranded':>9} "
          f"{'+1 costs':>9} {'+2 costs':>9} {'free agents':>12}")
    for r in rows:
        print(f"{r['week']:>3} {r['ir_used_total']:>4}/{r['ir_capacity_total']:<4} "
              f"{r['teams_at_cap']:>7} {r['teams_empty_ir']:>6} {r['stranded_total']:>9} "
              f"{r['cost_plus1']:>9} {r['cost_plus2']:>9} {r['free_agents']:>12,}")
    last = rows[-1]
    print(f"\nAs of week {last['week']}:")
    print(f"  {last['teams_at_cap']}/{last['teams_n']} teams have their IR full, "
          f"{last['teams_empty_ir']} have nobody on it.")
    print(f"  {last['stranded_total']} injured players are sitting on active rosters.")
    print(f"  {last['constrained']} teams are actually constrained "
          f"(IR full AND holding an injured man).")
    print(f"\n  A third IR spot would take {last['cost_plus1']} players off the wire "
          f"({100*last['cost_plus1']/max(last['free_agents'],1):.2f}% of the pool).")
    print(f"  A fourth would take {last['cost_plus2']} "
          f"({100*last['cost_plus2']/max(last['free_agents'],1):.2f}%).")
    if len(rows) > 1:
        a, b = rows[0], rows[-1]
        print(f"\n  Since week {a['week']}: IR use {a['ir_used_total']} -> {b['ir_used_total']}, "
              f"teams at cap {a['teams_at_cap']} -> {b['teams_at_cap']}, "
              f"free agents {a['free_agents']:,} -> {b['free_agents']:,}.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--user', default='drsexy')
    ap.add_argument('--season', default='')
    ap.add_argument('--league-id', default='')
    ap.add_argument('--week', type=int, default=0)
    ap.add_argument('--report', action='store_true')
    a = ap.parse_args()
    if a.report:
        report(json.load(open(LOG, encoding='utf-8')) if os.path.exists(LOG) else {'rows': []})
    else:
        report(snapshot(a))


if __name__ == '__main__':
    main()
