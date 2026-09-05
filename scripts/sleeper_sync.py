#!/usr/bin/env python3
"""Pull the league's current state from Sleeper and refresh the local snapshots.

    python3 scripts/sleeper_sync.py                 # username drsexy, current season
    python3 scripts/sleeper_sync.py --user drsexy --season 2026
    python3 scripts/sleeper_sync.py --team "Smoke Dragons"   # shortlist for one team

Writes:
    scfl-rosters.json   every team's roster, replacing the stale snapshot
    waivers.json        every unowned, rostered-somewhere-in-the-NFL player,
                        ranked by dynasty value and by how hard the wider
                        fantasy world is claiming them right now

The app in index.html resolves the league the same way -- username to user_id
to the season's leagues -- but it does it in the browser and keeps the result in
localStorage, so nothing it fetches ever lands on disk. This puts it on disk.

Everything here is Sleeper's public read-only API. No login, no token, no
credentials of any kind. It will not run inside the Claude Code container --
api.sleeper.app is denied by the environment's egress policy -- so run it
locally, or add api.sleeper.app to the environment allowlist first.
"""
import argparse, json, os, re, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://api.sleeper.app/v1'
UA = {'User-Agent': 'scfl-newsroom/1.0'}
CACHE = os.path.join(ROOT, '.sleeper-players.json')   # 5MB; gitignored
canon = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower())


def get(path, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(API + path, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if i == tries - 1:
                raise
        except Exception as e:
            if i == tries - 1:
                sys.exit(f'could not reach {API}{path}\n  {e}\n\n'
                         'If this is the Claude Code container, api.sleeper.app is blocked by\n'
                         'the egress policy -- run this on your own machine instead.')
        time.sleep(1.5 * (i + 1))


def players_db(refresh=False):
    """The whole NFL player table. 5MB, changes slowly, so it is cached."""
    if not refresh and os.path.exists(CACHE) and time.time() - os.path.getmtime(CACHE) < 86400:
        return json.load(open(CACHE, encoding='utf-8'))
    print('  fetching the NFL player table (~5MB, cached for a day)...')
    db = get('/players/nfl')
    json.dump(db, open(CACHE, 'w', encoding='utf-8'))
    return db


def find_league(user, season):
    u = get(f'/user/{user}')
    if not u:
        sys.exit(f'no Sleeper user named {user!r}')
    lgs = get(f'/user/{u["user_id"]}/leagues/nfl/{season}') or []
    if not lgs:
        sys.exit(f'{user} is in no {season} NFL leagues')
    if len(lgs) == 1:
        return lgs[0]
    scfl = [l for l in lgs if 'scfl' in l['name'].lower() or 'skirt' in l['name'].lower()]
    if len(scfl) == 1:
        return scfl[0]
    print('  several leagues -- pick one with --league-id:')
    for l in lgs:
        print(f"    {l['league_id']}  {l['name']}")
    sys.exit(1)


def load_values():
    p = os.path.join(ROOT, 'dp-values.json')
    if not os.path.exists(p):
        return {}
    v = json.load(open(p, encoding='utf-8'))['v']
    return {canon(k): (s[-1] if s and s[-1] is not None else 0) for k, s in v.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--user', default='drsexy')
    ap.add_argument('--season', default='')
    ap.add_argument('--league-id', default='')
    ap.add_argument('--team', default='Smoke Dragons')
    ap.add_argument('--refresh-players', action='store_true')
    a = ap.parse_args()

    season = a.season or str((get('/state/nfl') or {}).get('season') or time.gmtime().tm_year)
    if a.league_id:
        lg = get(f'/league/{a.league_id}')
        if not lg:
            sys.exit(f'no league {a.league_id}')
    else:
        lg = find_league(a.user, season)
    state = get('/state/nfl') or {}
    print(f"league: {lg['name']} ({lg['league_id']}) | {season} "
          f"week {state.get('week', '?')} | {lg.get('total_rosters')} teams")

    users = {u['user_id']: u for u in (get(f"/league/{lg['league_id']}/users") or [])}
    rosters = get(f"/league/{lg['league_id']}/rosters") or []
    db = players_db(a.refresh_players)
    VAL = load_values()

    def label(r):
        u = users.get(r.get('owner_id')) or {}
        return (u.get('metadata') or {}).get('team_name') or u.get('display_name') or \
               f"roster {r.get('roster_id')}"

    def pname(pid):
        p = db.get(pid) or {}
        return (p.get('full_name') or
                ' '.join(x for x in (p.get('first_name'), p.get('last_name')) if x) or pid)

    teams, owned = {}, set()
    for r in rosters:
        ids = list(r.get('players') or [])
        owned |= set(ids)
        teams[label(r)] = [{'name': pname(i), 'pos': (db.get(i) or {}).get('position') or '?'}
                           for i in ids]
    out = {'league': lg['name'], 'leagueId': lg['league_id'], 'season': int(season),
           'week': state.get('week'), 'exportedAt': int(time.time() * 1000),
           'source': 'Sleeper API via scripts/sleeper_sync.py', 'teams': teams}
    json.dump(out, open(os.path.join(ROOT, 'scfl-rosters.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f"  wrote scfl-rosters.json -- {len(teams)} teams, {len(owned)} players owned")

    trend = {t['player_id']: t['count']
             for t in (get('/players/nfl/trending/add?lookback_hours=48&limit=200') or [])}
    FANTASY = {'QB', 'RB', 'WR', 'TE', 'K', 'DEF'}
    fa = []
    for pid, p in db.items():
        if pid in owned or (p.get('position') not in FANTASY):
            continue
        if not p.get('team'):                      # not on an NFL roster: no snaps, no points
            continue
        if p.get('status') in ('Inactive', 'Retired'):
            continue
        nm = pname(pid)
        fa.append({'id': pid, 'name': nm, 'pos': p['position'], 'nfl': p['team'],
                   'age': p.get('age'), 'depth': p.get('depth_chart_order'),
                   'value': VAL.get(canon(nm), 0), 'adds48h': trend.get(pid, 0),
                   'status': p.get('status')})
    fa.sort(key=lambda x: (-x['adds48h'], -x['value']))
    json.dump({'league': lg['name'], 'season': int(season), 'week': state.get('week'),
               'exportedAt': out['exportedAt'], 'count': len(fa), 'players': fa},
              open(os.path.join(ROOT, 'waivers.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f"  wrote waivers.json -- {len(fa)} unowned players on NFL rosters")

    mine = teams.get(a.team) or next((v for k, v in teams.items()
                                      if canon(a.team) in canon(k)), None)
    print(f"\nTOP OF THE WIRE (by adds in the last 48h)")
    print(f"  {'pos':<4}{'player':<26}{'nfl':<5}{'adds':>7}{'value':>7}  depth")
    for p in fa[:25]:
        print(f"  {p['pos']:<4}{p['name'][:25]:<26}{p['nfl']:<5}{p['adds48h']:>7,}"
              f"{p['value']:>7}  {p['depth'] if p['depth'] is not None else '-'}")
    if mine:
        need = {q for q in ('QB', 'RB', 'WR', 'TE')
                if sum(1 for x in mine if x['pos'] == q and VAL.get(canon(x['name']), 0) >= 5) < 2}
        print(f"\nFOR {a.team.upper()} -- thin at: {', '.join(sorted(need)) or 'nothing'}")
        for q in sorted(need):
            top = [p for p in fa if p['pos'] == q][:5]
            print(f"  {q}: " + ', '.join(f"{p['name']} ({p['nfl']}, {p['adds48h']:,} adds)"
                                         for p in top))
        drop = sorted(((VAL.get(canon(x['name']), 0), x['name'], x['pos']) for x in mine))[:6]
        print(f"  drop candidates: " + ', '.join(f'{n} ({v})' for v, n, _ in drop))


if __name__ == '__main__':
    main()
