#!/usr/bin/env python3
"""Every trade the league has ever made, from Sleeper, season by season.

    python3 scripts/fetch_trade_history.py          # walks back from this season
    python3 scripts/fetch_trade_history.py --from <league_id>

Written because the Obvibase reconstruction cannot be trusted and a chat count
cannot replace it.

What the Obvibase file gets wrong, checked against Sleeper for 2026, the one
season all three sources cover:

    Sleeper     29 trades, The Machines in 8
    Obvibase     6 trades, The Machines in 2
    chat room   19 banners, The Machines named in 5

and across 2021-2025 the Obvibase file gives The Machines exactly thirteen
deals every single season -- the only franchise of the sixteen whose count
never moves, while the league total swings between 38 and 62. The official
room, counted independently, gives 13, 5, 8, 11, 3. So the flat line is an
artefact of the export, not a habit of the manager.

Sleeper is the league's own record and chains backwards: each season's league
carries `previous_league_id`, so one walk reaches every season the league has
been on the platform. That is the number to publish.

api.sleeper.app is blocked from the agent container. Run this from the
fetch-trade-history workflow; it comes back through git like the week files.
"""
import argparse, importlib.util, json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'trade-history.json')
_s = importlib.util.spec_from_file_location('ft', os.path.join(ROOT, 'scripts',
                                                               'fetch_transactions.py'))
ft = importlib.util.module_from_spec(_s); sys.modules['ft'] = ft; _s.loader.exec_module(ft)

WEEKS = range(0, 19)            # 0 covers the whole offseason, where most deals land


def season_trades(lid, db):
    lg = ft.get(f'/league/{lid}')
    if not lg:
        return None
    users = {u['user_id']: u for u in (ft.get(f'/league/{lid}/users') or [])}
    rosters = ft.get(f'/league/{lid}/rosters') or []

    def team_of(r):
        u = users.get(r.get('owner_id')) or {}
        return ((u.get('metadata') or {}).get('team_name') or u.get('display_name')
                or f"roster {r.get('roster_id')}")

    names = {r['roster_id']: team_of(r) for r in rosters}
    owners = {r['roster_id']: r.get('owner_id') for r in rosters}

    def man(pid):
        p = db.get(str(pid)) or {}
        return {'pid': str(pid), 'name': p.get('full_name') or p.get('last_name') or str(pid),
                'pos': p.get('position') or '?'}

    out = []
    for w in WEEKS:
        for t in (ft.get(f'/league/{lid}/transactions/{w}') or []):
            if t.get('type') != 'trade' or t.get('status') != 'complete':
                continue
            out.append({
                'week': w, 'created': t.get('created'),
                'roster_ids': t.get('roster_ids') or [],
                'adds': [dict(man(p), roster_id=r) for p, r in (t.get('adds') or {}).items()],
                'drops': [dict(man(p), roster_id=r) for p, r in (t.get('drops') or {}).items()],
                'picks': [{'season': d.get('season'), 'round': d.get('round'),
                           'from': d.get('previous_owner_id'), 'to': d.get('owner_id'),
                           'original': d.get('roster_id')}
                          for d in (t.get('draft_picks') or [])],
            })
        time.sleep(0.25)
    out.sort(key=lambda r: (r['week'], r['created'] or 0))
    return {'season': int(lg.get('season')), 'league_id': lid, 'league': lg.get('name'),
            'previous': lg.get('previous_league_id'),
            'rosters': {str(k): v for k, v in names.items()},
            'owners': {str(k): v for k, v in owners.items()},
            'trades': out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='start', default='', help='league id to start the walk at')
    a = ap.parse_args()
    lid = a.start or ft.league_id('')
    db = ft.players_db()

    seasons, seen = [], set()
    while lid and lid not in seen:
        seen.add(lid)
        s = season_trades(lid, db)
        if not s:
            break
        seasons.append(s)
        print(f"  {s['season']}  {len(s['trades']):>3} trades  ({s['league']})")
        lid = s['previous']

    seasons.sort(key=lambda s: s['season'])
    doc = {'note': "Every completed trade in the league's Sleeper history, walked back "
                   'through previous_league_id. scripts/fetch_trade_history.py',
           'stamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
           'seasons': [s['season'] for s in seasons],
           'count': sum(len(s['trades']) for s in seasons),
           'bySeason': seasons}
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"\n{doc['count']} trades across {len(seasons)} seasons "
          f"({seasons[0]['season']}-{seasons[-1]['season']}) -> {os.path.basename(OUT)}")


if __name__ == '__main__':
    main()
