#!/usr/bin/env python3
"""Pull the league's transaction log off Sleeper, week by week, and commit it.

    python3 scripts/fetch_transactions.py                 # every week so far
    python3 scripts/fetch_transactions.py --week 4        # just one
    python3 scripts/fetch_transactions.py --report        # read it back, no fetch

WHY THIS EXISTS

The IR study (scfl-ir-study.html) names one thing as the strongest evidence
nobody has: whether a team at the injured-reserve cap ever actually DROPPED a
man it wanted to keep. Everything else the study measures is friction -- a
roster slot doing nothing -- and friction is a ceiling on inconvenience, not a
measure of damage. A drop is the first thing in the whole argument that is a
real loss rather than an annoyance.

The transaction log is where that would show, and only there. So it gets pulled
once and kept, the same way ir-watch.json is kept: written from the live API,
committed, never rewritten.

WHAT A TRANSACTION DOES AND DOES NOT SAY

It says who was added and dropped, by which roster, in which week. It does NOT
say whether the dropped man was injured at the time -- Sleeper's player table
carries today's injury status, not September's, and a man dropped hurt in week
3 who has since healed reads healthy now. Asking the player table is how you
get a confident wrong answer.

ir-watch.json is the fix. It records, per team per week, the names of the
injured men sitting on that team's ACTIVE roster at the moment of the snapshot.
That is a point-in-time record, so a drop can be joined against the snapshot
that preceded it: was this man, on this roster, on the stranded list the last
time anybody looked? scripts/ir_drops.py does that join. This file only
fetches.

Public read-only endpoints, no login. api.sleeper.app is blocked inside the
Claude Code container, so this runs on a GitHub runner --
.github/workflows/fetch-transactions.yml -- and the result comes back as a
committed file.
"""
import argparse, json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://api.sleeper.app/v1'
OUT = os.path.join(ROOT, 'transactions.json')
IRW = os.path.join(ROOT, 'ir-watch.json')
CACHE = os.path.join(ROOT, '.sleeper-players.json')
UA = {'User-Agent': 'pressbox-transactions/1.0'}


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
                         'api.sleeper.app is blocked inside the Claude Code container --\n'
                         'run the fetch-transactions workflow instead.')
        time.sleep(1.5 * (i + 1))


def players_db():
    if os.path.exists(CACHE) and time.time() - os.path.getmtime(CACHE) < 86400:
        return json.load(open(CACHE, encoding='utf-8'))
    print('  fetching the NFL player table (~5MB, cached a day)...')
    db = get('/players/nfl')
    json.dump(db, open(CACHE, 'w', encoding='utf-8'))
    return db


def league_id(arg):
    """The league the IR log is already keyed to, unless told otherwise.

    Taking it from ir-watch.json rather than from a repository variable means
    the two files cannot drift onto different leagues, which is the one way
    this join could go quietly wrong.
    """
    if arg:
        return arg
    if os.path.exists(IRW):
        rows = json.load(open(IRW, encoding='utf-8'))['rows']
        if rows:
            return rows[-1]['league_id']
    sys.exit('no league id: pass --league-id, or run ir_watch.py first')


def fetch(a):
    lid = league_id(a.league_id)
    lg = get(f'/league/{lid}')
    if not lg:
        sys.exit(f'no league {lid}')
    state = get('/state/nfl') or {}
    season = int(lg.get('season') or state.get('season') or time.gmtime().tm_year)
    now = int(state.get('week') or 0)
    weeks = [a.week] if a.week else list(range(0, max(now, 1) + 1))

    users = {u['user_id']: u for u in (get(f'/league/{lid}/users') or [])}
    rosters = get(f'/league/{lid}/rosters') or []

    def team_of(r):
        u = users.get(r.get('owner_id')) or {}
        return (u.get('metadata') or {}).get('team_name') or u.get('display_name') \
            or f"roster {r.get('roster_id')}"

    names = {r['roster_id']: team_of(r) for r in rosters}
    db = players_db()

    def man(pid):
        p = db.get(str(pid)) or {}
        # The NFL's own id, so a drop can be joined to nflverse's weekly roster
        # and injury feeds without going through a name. Sleeper stores it with
        # a LEADING SPACE on a good number of players; joining on the raw value
        # silently matches nothing.
        g = (p.get('gsis_id') or '').strip()
        return {'pid': str(pid),
                'gsis': g,
                'name': p.get('full_name') or p.get('last_name') or str(pid),
                'pos': p.get('position') or '?',
                'nfl': p.get('team') or ''}

    rows = []
    for w in weeks:
        tx = get(f'/league/{lid}/transactions/{w}') or []
        for t in tx:
            adds = [dict(man(p), roster_id=r) for p, r in (t.get('adds') or {}).items()]
            drops = [dict(man(p), roster_id=r) for p, r in (t.get('drops') or {}).items()]
            rows.append({
                'week': w,
                'type': t.get('type'),
                'status': t.get('status'),
                'created': t.get('created'),
                'roster_ids': t.get('roster_ids') or [],
                'bid': (t.get('settings') or {}).get('waiver_bid'),
                'adds': adds,
                'drops': drops,
                'picks': len(t.get('draft_picks') or []),
            })
        print(f'  week {w}: {len(tx)} transactions')
        time.sleep(0.4)

    rows.sort(key=lambda r: (r['week'], r['created'] or 0))
    doc = {'note': 'Sleeper transaction log, pulled once and not rewritten. '
                   'scripts/fetch_transactions.py',
           'stamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
           'season': season, 'league': lg.get('name'), 'league_id': lid,
           'weeks': weeks, 'rosters': {str(k): v for k, v in names.items()},
           'rows': rows}
    # A single-week pull tops up the file rather than replacing it, so catching
    # up a missed week cannot wipe the ones already banked.
    if a.week and os.path.exists(OUT):
        old = json.load(open(OUT, encoding='utf-8'))
        keep = [r for r in old['rows'] if r['week'] != a.week]
        doc['rows'] = sorted(keep + rows, key=lambda r: (r['week'], r['created'] or 0))
        doc['weeks'] = sorted({r['week'] for r in doc['rows']})
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"  wrote {os.path.basename(OUT)}: {len(doc['rows'])} transactions, "
          f"weeks {min(doc['weeks'])}-{max(doc['weeks'])}")
    return doc


def report(doc):
    rows = doc['rows']
    if not rows:
        print('nothing logged')
        return
    kinds = {}
    for r in rows:
        kinds[r['type']] = kinds.get(r['type'], 0) + 1
    print(f"\n{doc['league']} {doc['season']} — {len(rows)} transactions")
    print('  ' + ', '.join(f'{k} {v}' for k, v in sorted(kinds.items(), key=lambda x: -x[1])))
    print(f"\n{'wk':>3} {'all':>5} {'done':>5} {'adds':>5} {'drops':>6}")
    for w in sorted({r['week'] for r in rows}):
        g = [r for r in rows if r['week'] == w]
        ok = [r for r in g if r['status'] == 'complete']
        print(f"{w:>3} {len(g):>5} {len(ok):>5} "
              f"{sum(len(r['adds']) for r in ok):>5} {sum(len(r['drops']) for r in ok):>6}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--league-id', default=os.environ.get('SCFL_LEAGUE_ID', ''))
    ap.add_argument('--week', type=int, default=0, help='one week only (tops up the file)')
    ap.add_argument('--report', action='store_true')
    a = ap.parse_args()
    if a.report:
        if not os.path.exists(OUT):
            sys.exit('no transactions.json yet')
        report(json.load(open(OUT, encoding='utf-8')))
        return
    report(fetch(a))


if __name__ == '__main__':
    main()
