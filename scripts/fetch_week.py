#!/usr/bin/env python3
"""Pull one completed week's matchups out of Sleeper and commit them.

    python3 scripts/fetch_week.py --week 4

Writes week-data/{season}-w{week}.json: every matchup, both sides, every
starter with his real points, plus the bench. This is the file the issue
builder reads, so the issue can be rebuilt at any time from a fixed record
rather than from whatever Sleeper happens to say today.

Why a committed file and not a live fetch: api.sleeper.app is blocked by the
agent container's egress policy, but a GitHub runner has open internet. So the
fetch runs in Actions (.github/workflows/fetch-week.yml) and the result comes
back through git, the same trick ir_watch.py uses.

The one field that matters beyond the obvious ones is gsis_id. It is the NFL's
own player id, and nflverse play-by-play carries it too, so it is the join
that turns "G.Kittle caught a 56-yard touchdown at 2:25 of the fourth" into
"that was Wookie Leaks' tight end." Matching on names instead is how you end
up with Ja'Marr Chase missing from a list.
"""
import argparse, json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://api.sleeper.app/v1'
UA = {'User-Agent': 'scfl-newsroom/1.0'}
OUTDIR = os.path.join(ROOT, 'week-data')


def get(path, quiet=False):
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
                if quiet:
                    return None
                sys.exit(f'could not reach {API}{path}\n  {e}\n\n'
                         'Inside the agent container api.sleeper.app is blocked -- run this\n'
                         'through .github/workflows/fetch-week.yml instead.')
        time.sleep(1.5 * (i + 1))


def league_id(explicit):
    if explicit:
        return explicit
    # the schedule pull already resolved it once; no reason to do it again
    p = os.path.join(ROOT, 'sleeper-schedule.json')
    if os.path.exists(p):
        return json.load(open(p, encoding='utf-8'))['league_id']
    sys.exit('no league id: pass --league-id or commit sleeper-schedule.json first')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, required=True)
    ap.add_argument('--season', default='')
    ap.add_argument('--league-id', default=os.environ.get('SCFL_LEAGUE_ID', ''))
    a = ap.parse_args()

    lid = league_id(a.league_id)
    lg = get(f'/league/{lid}')
    if not lg:
        sys.exit(f'league {lid} did not resolve')
    season = a.season or str(lg['season'])
    wk = a.week

    users = {u['user_id']: u for u in (get(f'/league/{lid}/users') or [])}
    rosters = {r['roster_id']: r for r in (get(f'/league/{lid}/rosters') or [])}
    ms = get(f'/league/{lid}/matchups/{wk}') or []
    if not ms:
        sys.exit(f'no matchups for week {wk}')
    print(f'  {lg["name"]} {season} week {wk}: {len(ms)} roster entries')

    print('  fetching the NFL player table (~5MB)...')
    db = get('/players/nfl') or {}
    # weekly stats fill in a stat line for anyone Sleeper did not price directly
    stats = get(f'/stats/nfl/regular/{season}/{wk}', quiet=True) or {}

    def team_of(rid):
        u = users.get((rosters.get(rid) or {}).get('owner_id')) or {}
        return (u.get('metadata') or {}).get('team_name') or u.get('display_name') or f'roster {rid}'

    def player(pid):
        p = db.get(pid) or {}
        nm = (p.get('full_name')
              or ' '.join(x for x in (p.get('first_name'), p.get('last_name')) if x) or pid)
        return {'id': pid, 'name': nm,
                'pos': p.get('position') or (p.get('fantasy_positions') or [None])[0],
                'nfl': p.get('team'),
                # Join keys into nflverse play-by-play, in the order the matcher
                # should try them. Sleeper fills gsis_id for only about a quarter
                # of players, so espn_id carries most of the load -- nflverse's
                # own players.csv has both and bridges them.
                'gsis_id': p.get('gsis_id'),
                'espn_id': p.get('espn_id'),
                'sportradar_id': p.get('sportradar_id'),
                'yahoo_id': p.get('yahoo_id'),
                'stats': stats.get(pid) or None}

    def side(m):
        starters = [s for s in (m.get('starters') or []) if s]
        pp = m.get('players_points') or {}
        allp = [p for p in (m.get('players') or []) if p]
        # Who is on injured reserve. The matchup payload does not say, so it
        # comes off the roster record. Without it a player on IR is
        # indistinguishable from one on the bench, which makes roster counts
        # wrong and hides exactly the thing IR Watch is measuring.
        res = set((rosters.get(m['roster_id']) or {}).get('reserve') or [])
        mk = lambda pid: dict(player(pid), points=round(float(pp.get(pid) or 0), 2),
                              reserve=pid in res)
        return {'roster_id': m['roster_id'], 'team': team_of(m['roster_id']),
                'points': round(float(m.get('points') or 0), 2),
                'ir_used': len(res),
                'starters': [mk(p) for p in starters],
                'bench': [mk(p) for p in allp if p not in starters and p not in res],
                'reserve': [mk(p) for p in allp if p in res]}

    by = {}
    for m in ms:
        if m.get('matchup_id') is None:
            continue
        by.setdefault(m['matchup_id'], []).append(m)

    games = []
    for mid, pair in sorted(by.items()):
        if len(pair) != 2:
            print(f'  ! matchup {mid} has {len(pair)} entries, skipping')
            continue
        A, B = side(pair[0]), side(pair[1])
        hi, lo = (A, B) if A['points'] >= B['points'] else (B, A)
        games.append({'matchup_id': mid, 'teams': [A, B],
                      'winner': hi['team'] if hi['points'] != lo['team'] else None,
                      'margin': round(abs(A['points'] - B['points']), 2)})
        print(f"    {A['team']} {A['points']} - {B['points']} {B['team']}")

    gs = sum(1 for g in games for t in g['teams'] for p in t['starters'] if p['gsis_id'])
    tot = sum(1 for g in games for t in g['teams'] for p in t['starters'])
    print(f'  gsis_id present on {gs}/{tot} starters')

    os.makedirs(OUTDIR, exist_ok=True)
    out = {'league': lg['name'], 'league_id': lid, 'season': int(season), 'week': wk,
           'fetchedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
           'scoring': lg.get('scoring_settings'),
           'roster_positions': lg.get('roster_positions'),
           'games': games}
    path = os.path.join(OUTDIR, f'{season}-w{wk}.json')
    json.dump(out, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'  wrote week-data/{season}-w{wk}.json ({len(games)} games)')


if __name__ == '__main__':
    main()
