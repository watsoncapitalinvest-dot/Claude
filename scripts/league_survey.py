#!/usr/bin/env python3
"""How many IR slots do other 16-team dynasty leagues actually run?

    python3 scripts/league_survey.py              # one hop out
    python3 scripts/league_survey.py --hops 2     # and their leaguemates' leagues
    python3 scripts/league_survey.py --report     # read the survey back, no fetch

WHY

The IR study carries one claim nobody could test: "leagues our size run two to
four slots." It sat on the scoreboard as UNTESTED because the study had no data
on any league but this one. This gets some.

HOW THE SAMPLE IS DRAWN, AND WHAT IS WRONG WITH IT

Sleeper has no search. You cannot ask it for every 16-team dynasty league, only
for a league by id or for the leagues a given USER is in. So the sample is
drawn by walking outward from this league: every manager here, every other
2026 NFL league they play in, and -- at two hops -- everyone in THOSE leagues
and their leagues in turn.

That is a snowball sample, not a random one, and it is biased in a way worth
saying out loud: these are the leagues of people who play in a 16-team
superflex dynasty league, so they will skew larger, deeper and more dynasty
than the Sleeper average. For the question actually being asked -- what do
leagues LIKE OURS do -- that bias runs the right way. For "what does the
average league do", it would be worthless.

Filters: NFL, the current season, exactly 16 rosters, and Sleeper's own
dynasty flag (settings.type == 2). Keeper leagues (type 1) are counted
separately, never folded in.

WHAT IS RECORDED, AND WHAT DELIBERATELY IS NOT

Slot counts, roster shapes and settings. No league names, no league ids, no
user names, no indication of which manager's membership led where. This repo
is public and the question is "how many slots", not "who plays where" --
sixteen other people's hobby leagues are nobody's business but theirs. The
method is written down instead, so anyone can re-run it and get the same
distribution.

api.sleeper.app is blocked inside the Claude Code container, so this runs on a
GitHub runner -- .github/workflows/league-survey.yml -- and the result comes
back as a committed file.
"""
import argparse, json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://api.sleeper.app/v1'
OUT = os.path.join(ROOT, 'league-survey.json')
IRW = os.path.join(ROOT, 'ir-watch.json')
UA = {'User-Agent': 'pressbox-league-survey/1.0'}
QB_SLOTS = {'QB', 'SUPER_FLEX'}


def get(path, soft=False):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(API + path, headers=UA),
                                        timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (404, 429):
                if e.code == 429:
                    time.sleep(3 * (i + 1))
                    continue
                return None
            if i == 2:
                return None if soft else sys.exit(f'{API}{path}: {e}')
        except Exception as e:
            if i == 2:
                if soft:
                    return None
                sys.exit(f'could not reach {API}{path}\n  {e}\n\n'
                         'api.sleeper.app is blocked inside the Claude Code container --\n'
                         'run the league-survey workflow instead.')
        time.sleep(1.2 * (i + 1))


def tenure(lid, memo):
    """How many consecutive seasons this league has run ON SLEEPER.

    Sleeper chains a league to its own prior year with previous_league_id, so
    following that back and counting gives on-platform tenure.

    WHAT IT IS NOT is league age. Our own history came off ESPN -- the repo's
    history.json says so in its first field -- so any league that migrated
    reads younger here than it is, and that includes this one. The number is a
    FLOOR for everybody, which is the only way it can be compared at all. A
    walk that quietly reported it as age would make every migrated league look
    like a startup.
    """
    n, cur = 1, lid
    while cur:
        if cur in memo:
            return n - 1 + memo[cur]
        lg = get(f'/league/{cur}', soft=True)
        prev = (lg or {}).get('previous_league_id')
        if not prev or prev == cur:
            break
        cur = prev
        n += 1
        time.sleep(0.2)
    memo[lid] = n
    return n


def shape(lg):
    """One league, reduced to the settings the argument is about.

    No name and no id: see the note at the top of this file.
    """
    s = lg.get('settings') or {}
    pos = lg.get('roster_positions') or []
    start = [p for p in pos if p != 'BN']
    return {
        'teams': lg.get('total_rosters'),
        'type': s.get('type'),                       # 0 redraft, 1 keeper, 2 dynasty
        'ir': s.get('reserve_slots'),
        'taxi': s.get('taxi_slots') or 0,
        'starters': len(start),
        'bench': len([p for p in pos if p == 'BN']),
        'superflex': sum(1 for p in start if p in QB_SLOTS) >= 2,
        'ppr': (lg.get('scoring_settings') or {}).get('rec'),
        'playoff_teams': s.get('playoff_teams'),
        # which designations Sleeper will let a manager shelve. A league that
        # allows only true IR is stricter than ours whatever its slot count,
        # so the raw number alone would not be comparing like with like.
        'allow': {k[len('reserve_allow_'):]: v for k, v in s.items()
                  if k.startswith('reserve_allow_')},
    }


def home_only(a):
    """Record OUR league's own settings into an existing survey, nothing else.

    The walk deliberately skips the home league -- it is the thing being
    compared, not a sample point -- and the first version left it out of the
    file entirely, which made the comparison impossible to finish. A raw slot
    count is not comparable on its own: a league with five slots that admits
    only true IR is stricter than one with three that admits Out, Doubtful and
    PUP, and in this sample the permissive leagues turn out to carry MORE
    slots rather than fewer. So the baseline needs its own eligibility flags
    sitting next to everyone else's.

    Merging into the existing file rather than re-walking keeps the 8,000-odd
    leagues already banked; a fresh walk would draw a slightly different
    sample and quietly change every figure.
    """
    if not os.path.exists(OUT):
        sys.exit('no league-survey.json yet -- run the walk first')
    doc = json.load(open(OUT, encoding='utf-8'))
    lid = a.league_id
    if not lid and os.path.exists(IRW):
        rows = json.load(open(IRW, encoding='utf-8'))['rows']
        lid = rows[-1]['league_id'] if rows else ''
    lg = get(f'/league/{lid}') if lid else None
    if not lg:
        sys.exit(f'could not read the home league {lid!r}')
    doc['home'] = shape(lg)
    doc['home']['seasons'] = tenure(lid, {})
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"  recorded the home league: {doc['home']['ir']} IR slots, "
          f"{sum(1 for v in doc['home']['allow'].values() if v)} designations allowed, "
          f"{doc['home']['seasons']} seasons on Sleeper")
    return doc


def survey(a):
    season = a.season
    if not season:
        season = str((get('/state/nfl') or {}).get('season') or time.gmtime().tm_year)
    home = a.league_id
    if not home and os.path.exists(IRW):
        rows = json.load(open(IRW, encoding='utf-8'))['rows']
        home = rows[-1]['league_id'] if rows else ''
    if not home:
        sys.exit('no league id: pass --league-id, or run ir_watch.py first')

    seen_u, seen_l, found, memo = set(), set(), [], {}
    frontier = [u['user_id'] for u in (get(f'/league/{home}/users') or [])]
    print(f'  hop 0: {len(frontier)} managers in the home league')
    seen_l.add(home)

    for hop in range(1, a.hops + 1):
        nxt, calls, hits = [], 0, 0
        for uid in frontier:
            if uid in seen_u or calls >= a.cap:
                continue
            seen_u.add(uid)
            calls += 1
            for lg in (get(f'/user/{uid}/leagues/nfl/{season}', soft=True) or []):
                lid = lg.get('league_id')
                if not lid or lid in seen_l:
                    continue
                seen_l.add(lid)
                sh = shape(lg)
                # Chain-walking costs a call per prior season, so it is spent
                # only on the leagues this study can actually compare against.
                if a.chains and sh['teams'] == 16:
                    sh['seasons'] = tenure(lid, memo)
                found.append(sh)
                if sh['teams'] == 16 and sh['type'] == 2:
                    hits += 1
                nxt.append((sh, lid))
            time.sleep(0.25)
        print(f'  hop {hop}: {calls} managers asked, {len(found)} leagues seen, '
              f'{hits} new 16-team dynasty')
        if hop >= a.hops:
            break
        # Widen through the leagues most likely to CONTAIN what we are looking
        # for, which is not the same as the leagues that already match. The
        # first version of this walked onward only through 16-team leagues and
        # found none at hop 1, so the frontier emptied and the walk stopped
        # dead. A manager in a 12-team dynasty is a perfectly good route to a
        # 16-team one; a 10-team redraft is a poorer one. So: biggest and most
        # dynasty first, and spend the budget there.
        nxt.sort(key=lambda x: (-(x[0]['type'] or 0), -(x[0]['teams'] or 0)))
        frontier = []
        for sh, lid in nxt[:a.cap]:
            for u in (get(f'/league/{lid}/users', soft=True) or []):
                if u.get('user_id') not in seen_u:
                    frontier.append(u['user_id'])
            time.sleep(0.25)
        print(f'          {len(frontier)} new managers to ask next')

    doc = {'note': 'Snowball sample of leagues reachable from this one. No names or ids '
                   'are recorded -- see the header of scripts/league_survey.py.',
           'stamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
           'season': int(season), 'hops': a.hops,
           'managers_asked': len(seen_u), 'leagues_seen': len(found),
           'leagues': found}
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'  wrote {os.path.basename(OUT)}: {len(found)} leagues')
    return doc


def report(doc):
    lg = doc['leagues']
    h = doc.get('home')
    if h:
        print(f"\nOURS: {h['teams']} teams, {h['ir']} IR slots, {h['taxi']} taxi, "
              f"{h['starters']}+{h['bench']}, "
              f"{'superflex' if h['superflex'] else 'single QB'}, "
              f"{sum(1 for v in h['allow'].values() if v)} of "
              f"{len(h['allow'])} designations allowed")
    print(f"\n{doc['leagues_seen']} leagues from {doc['managers_asked']} managers, "
          f"{doc['season']}, {doc['hops']} hop(s)")
    for label, sel in (('ALL', lambda l: True),
                       ('16-team', lambda l: l['teams'] == 16),
                       ('16-team dynasty', lambda l: l['teams'] == 16 and l['type'] == 2),
                       ('16-team dynasty superflex',
                        lambda l: l['teams'] == 16 and l['type'] == 2 and l['superflex'])):
        g = [l for l in lg if sel(l)]
        if not g:
            print(f'\n{label}: none')
            continue
        d = {}
        for l in g:
            d[l['ir']] = d.get(l['ir'], 0) + 1
        print(f'\n{label}: {len(g)} leagues')
        for k in sorted(d, key=lambda x: (x is None, x)):
            print(f"    {str(k) + ' IR slots':>14}  {d[k]:>3}  "
                  f"{100*d[k]/len(g):>5.1f}%  {'#' * d[k]}")
        ir = sorted(l['ir'] for l in g if l['ir'] is not None)
        if ir:
            print(f"    mean {sum(ir)/len(ir):.2f}, median "
                  f"{ir[len(ir)//2]}, range {min(ir)}-{max(ir)}")
            if h and h['ir'] is not None:
                at = sum(1 for v in ir if v <= h['ir'])
                print(f"    ours ({h['ir']}): {at} of {len(ir)} leagues run that many or "
                      f"fewer = bottom {100*at/len(ir):.0f}%")


def tenure_report(doc):
    """Does on-platform tenure predict slot count?

    The question put to this desk was not "are those leagues younger" but the
    thing that follows from it -- whether a league's settings deserve less
    weight for being new. That only matters if tenure and slots are related,
    so the cross-tab is the test, not the age distribution on its own.
    """
    g = [l for l in doc['leagues']
         if l['teams'] == 16 and l.get('seasons') and l['ir'] is not None]
    if not g:
        print('\nno tenure data -- re-run the walk with --chains')
        return
    h = doc.get('home') or {}
    med = lambda xs: sorted(xs)[len(sorted(xs)) // 2] if xs else None
    print(f"\nSEASONS ON SLEEPER (a floor, not league age -- see tenure() in this file)")
    print(f"  ours: {h.get('seasons')}  (and {h.get('seasons')} is only the Sleeper era)")
    for label, sel in (('16-team', lambda l: True),
                       ('16-team dynasty', lambda l: l['type'] == 2)):
        gg = [l for l in g if sel(l)]
        if not gg:
            continue
        ten = sorted(l['seasons'] for l in gg)
        print(f"\n  {label}: {len(gg)} leagues with tenure known")
        print(f"    median {ten[len(ten)//2]} seasons, range {min(ten)}-{max(ten)}")
        if h.get('seasons'):
            older = sum(1 for t in ten if t >= h['seasons'])
            print(f"    as old as ours or older: {older} of {len(ten)} "
                  f"({100*older/len(ten):.0f}%)")
        print(f"    {'tenure':>12} {'leagues':>8} {'median IR':>10}")
        buckets = [(1, 1), (2, 3), (4, 5), (6, 99)]
        for lo, hi in buckets:
            b = [l for l in gg if lo <= l['seasons'] <= hi]
            if b:
                lab = f'{lo}' if lo == hi else (f'{lo}-{hi}' if hi < 99 else f'{lo}+')
                print(f"    {lab + ' seasons':>12} {len(b):>8} "
                      f"{med([l['ir'] for l in b]):>10}")
        if h.get('seasons'):
            old = [l for l in gg if l['seasons'] >= h['seasons']]
            if old:
                print(f"    leagues as old as ours: {len(old)}, median "
                      f"{med([l['ir'] for l in old])} IR slots, "
                      f"{sum(1 for l in old if l['ir'] <= 2)} of {len(old)} at 2 or fewer")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--league-id', default=os.environ.get('SCFL_LEAGUE_ID', ''))
    ap.add_argument('--season', default='')
    ap.add_argument('--hops', type=int, default=1)
    ap.add_argument('--cap', type=int, default=400, help='managers asked per hop')
    ap.add_argument('--chains', action='store_true',
                    help='also count seasons on Sleeper for 16-team leagues')
    ap.add_argument('--home-only', action='store_true',
                    help="record our own league's settings into an existing survey")
    ap.add_argument('--report', action='store_true')
    a = ap.parse_args()
    if a.home_only:
        report(home_only(a))
        return
    if a.report:
        if not os.path.exists(OUT):
            sys.exit('no league-survey.json yet')
        d = json.load(open(OUT, encoding='utf-8'))
        report(d)
        tenure_report(d)
        return
    report(survey(a))


if __name__ == '__main__':
    main()
