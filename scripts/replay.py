#!/usr/bin/env python3
"""Replay a fantasy week as a football game, using real plays in real order.

    python3 scripts/replay.py --week 4
    python3 scripts/replay.py --week 4 --game 3 --verbose

The idea, in one line: a 30-yard touchdown catch on Monday night really
happened, and it really was the last thing that moved the score, so in the
fantasy game it is a 30-yard touchdown catch late in the fourth. Nothing is
invented. The plays are real, the yardage is real, the order is real. The only
thing synthesised is the clock they are laid on.

That matters because it is what makes a sentence like "X scored a late 30-yard
touchdown to put Y ahead for the win" checkable rather than merely plausible.
Y really did take the lead on that play.

HOW THE CLOCK WORKS

Every play has an absolute moment: its game's kickoff plus how far into that
game it came. Sorting a matchup's plays by that gives the true order in which
fantasy points landed across the week. Those are then laid onto sixty minutes
by the window the NFL game sat in -- Thursday night opens the first quarter,
the Sunday afternoon slate runs through the second and third, Sunday night
starts the fourth and Monday night closes it. So "late fourth quarter" and
"Monday night" mean the same thing, which is the point.

WHAT IT REFUSES TO DO

A player's points computed from plays will not always equal the points Sleeper
credited him -- a stat correction, a missing id, a team defence that no single
play explains. The difference is carried as a residual, placed at the end of
that player's NFL game, and marked. Residuals keep the running score honest
(it ends exactly where Sleeper says it ends) but they are never narratable:
nothing downstream may describe a residual as a play, because it isn't one.

Inputs:  week-data/{season}-w{week}.json   (scripts/fetch_week.py, via Actions)
         nflverse play-by-play + players.csv  (downloaded, cached)
Output:  week-data/{season}-w{week}-replay.json
"""
import argparse, csv, gzip, io, json, os, re, sys, urllib.request
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')
CACHE = os.path.join(ROOT, '.nflverse')
PBP_URL = 'https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{s}.csv.gz'
IDS_URL = 'https://github.com/nflverse/nflverse-data/releases/download/players/players.csv'

# Where each NFL broadcast window lands on the fantasy game clock, in seconds
# elapsed of 3600. Thursday opens it; Monday night closes it.
WINDOWS = [
    ('THU', 'Thursday night', 0, 420),
    ('SUNAM', 'the Sunday early games', 420, 1800),
    ('SUNPM', 'the Sunday late games', 1800, 2700),
    ('SNF', 'Sunday night', 2700, 3180),
    ('MON', 'Monday night', 3180, 3600),
]
WIN_ORDER = {w[0]: i for i, w in enumerate(WINDOWS)}


def fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 10000:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f'  downloading {os.path.basename(path)}...')
    req = urllib.request.Request(url, headers={'User-Agent': 'scfl-newsroom/1.0'})
    with urllib.request.urlopen(req, timeout=180) as r, open(path, 'wb') as f:
        f.write(r.read())
    return path


# ---- id crosswalk ----------------------------------------------------------
NORM = lambda s: re.sub(r'[^a-z]', '', (s or '').lower())
SUFFIX = re.compile(r'\b(jr|sr|ii|iii|iv|v)\b\.?', re.I)
canon = lambda s: NORM(SUFFIX.sub('', s or ''))


def crosswalk():
    """espn_id -> gsis_id, and (name, pos) -> gsis_id, from nflverse players.csv."""
    p = fetch(IDS_URL, os.path.join(CACHE, 'players.csv'))
    by_espn, by_name = {}, {}
    for x in csv.DictReader(open(p, encoding='utf-8', errors='replace')):
        g = x.get('gsis_id')
        if not g:
            continue
        if x.get('espn_id'):
            by_espn[str(x['espn_id']).strip()] = g
        key = (canon(x.get('display_name')), (x.get('position') or '').upper())
        by_name.setdefault(key, g)
    return by_espn, by_name


clean = lambda v: '' if v in (None, '') else str(v).strip()


def resolve(pl, by_espn, by_name, evmap=None):
    """A starter's gsis id, trying the reliable keys before the fuzzy one.

    Two traps here, both of which cost a real player a real afternoon:

    Sleeper stores gsis_id with a leading space (' 00-0035640'). Every id is
    stripped before use, which is why clean() exists rather than str().

    And an id that resolves to nothing is not a match. Trying gsis first and
    stopping there silently lost every player whose gsis was present-but-wrong,
    because the name fallback never ran. So all candidates are generated, and
    the first one the play data actually knows about wins.
    """
    cands = []
    if clean(pl.get('gsis_id')):
        cands.append((clean(pl['gsis_id']), 'gsis'))
    e = clean(pl.get('espn_id'))
    if e and e in by_espn:
        cands.append((by_espn[e], 'espn'))
    g = by_name.get((canon(pl.get('name')), (pl.get('pos') or '').upper()))
    if g:
        cands.append((g, 'name'))
    if evmap is not None:
        for gid, how in cands:
            if gid in evmap:
                return gid, how
    return cands[0] if cands else (None, None)


# ---- the plays -------------------------------------------------------------
def kickoff(row):
    """Absolute kickoff as (datetime, window code)."""
    d = row.get('game_date') or ''
    t = (row.get('start_time') or '').split(',')[-1].strip()
    try:
        dt = datetime.strptime(d, '%Y-%m-%d')
    except ValueError:
        return None, 'SUNAM'
    hh = 13
    m = re.match(r'(\d{1,2}):(\d{2})', t)
    if m:
        hh = int(m.group(1))
        dt = dt.replace(hour=hh, minute=int(m.group(2)))
    wd = dt.weekday()                       # Mon=0 .. Sun=6
    if wd == 0:
        w = 'MON'
    elif wd in (3, 4, 5):                   # Thu/Fri/Sat
        w = 'THU'
    elif wd == 6:
        w = 'SUNAM' if hh < 15 else ('SUNPM' if hh < 19 else 'SNF')
    else:
        w = 'SUNAM'
    return dt, w


def num(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


# nflverse and Sleeper disagree about three franchises' abbreviations
TEAM_ALIAS = {'LA': 'LAR', 'LAR': 'LAR', 'LV': 'LV', 'OAK': 'LV', 'STL': 'LAR',
              'SD': 'LAC', 'WAS': 'WAS', 'WSH': 'WAS', 'ARZ': 'ARI', 'BLT': 'BAL',
              'CLV': 'CLE', 'HST': 'HOU', 'JAC': 'JAX'}
tm = lambda t: TEAM_ALIAS.get((t or '').upper(), (t or '').upper())


def play_events(season, week, sc):
    """Every play that moved a fantasy score, as attributions per gsis id.

    Returns {gsis: [event, ...]} where an event carries the points it was worth,
    when it happened, and a plain description of what it actually was.
    """
    p = fetch(PBP_URL.format(s=season), os.path.join(CACHE, f'pbp_{season}.csv.gz'))
    out = {}
    dst = {}          # team defences, keyed by abbreviation, not a player id
    games = {}
    with gzip.open(p, 'rt', encoding='utf-8', errors='replace') as f:
        for r in csv.DictReader(f):
            if r.get('week') != str(week) or (r.get('season_type') or 'REG') != 'REG':
                continue
            gid = r.get('game_id')
            if gid not in games:
                games[gid] = kickoff(r)
            ko, win = games[gid]
            if ko is None:
                continue
            elapsed = 3600 - num(r.get('game_seconds_remaining'), 0)
            abs_ts = ko.timestamp() + elapsed
            base = dict(game_id=gid, window=win, abs_ts=abs_ts,
                        nfl_qtr=r.get('qtr'), nfl_clock=r.get('time'),
                        posteam=r.get('posteam'))

            def add(pid, pts, kind, text, yards=None, td=False):
                if not pid or not pts:
                    return
                out.setdefault(pid, []).append(dict(
                    base, pts=round(pts, 3), kind=kind, text=text,
                    yards=yards, td=bool(td), residual=False))

            # ---- team defence: the parts of it that ARE a single play ----
            # Points allowed is a whole-game stat and stays in the residual,
            # but a sack, a takeaway and a defensive score are all plays and
            # can be told as plays.
            dt = tm(r.get('defteam'))
            if dt:
                def dadd(pts, kind, text, td=False):
                    if not pts:
                        return
                    dst.setdefault(dt, []).append(dict(
                        base, pts=round(pts, 3), kind=kind, text=text,
                        yards=None, td=bool(td), residual=False))
                if r.get('sack') == '1':
                    dadd(num(sc.get('sack'), 1.0), 'sack', 'a sack')
                if r.get('interception') == '1':
                    dadd(num(sc.get('int'), 2.0), 'dint', 'an interception')
                if r.get('fumble_lost') == '1':
                    dadd(num(sc.get('def_st_fum_rec'), 2.0), 'drec', 'a fumble recovery')
                if r.get('return_touchdown') == '1' or r.get('touchdown') == '1' and \
                        tm(r.get('td_team')) == dt:
                    dadd(num(sc.get('def_td'), 6.0), 'dtd', 'a defensive touchdown', True)

            ptd = r.get('pass_touchdown') == '1'
            rtd = r.get('rush_touchdown') == '1'
            py, ry, cy = num(r.get('passing_yards')), num(r.get('rushing_yards')), num(r.get('receiving_yards'))

            # passing
            if r.get('passer_player_id') and (py or ptd):
                pts = py * num(sc.get('pass_yd')) + (num(sc.get('pass_td')) if ptd else 0)
                nm = r.get('passer_player_name') or ''
                txt = (f'{int(py)}-yard touchdown pass' if ptd else f'{int(py)}-yard pass')
                add(r['passer_player_id'], pts, 'pass', txt, int(py), ptd)
            # receiving
            if r.get('receiver_player_id') and (cy or ptd):
                pts = cy * num(sc.get('rec_yd')) + num(sc.get('rec')) + (num(sc.get('rec_td')) if ptd else 0)
                txt = (f'{int(cy)}-yard touchdown catch' if ptd else f'{int(cy)}-yard catch')
                add(r['receiver_player_id'], pts, 'rec', txt, int(cy), ptd)
            # rushing
            if r.get('rusher_player_id') and (ry or rtd):
                pts = ry * num(sc.get('rush_yd')) + (num(sc.get('rush_td')) if rtd else 0)
                txt = (f'{int(ry)}-yard touchdown run' if rtd else f'{int(ry)}-yard run')
                add(r['rusher_player_id'], pts, 'rush', txt, int(ry), rtd)
            # turnovers charged to the man who threw or lost it
            if r.get('interception') == '1' and r.get('passer_player_id'):
                add(r['passer_player_id'], num(sc.get('pass_int')), 'int', 'an interception')
            if r.get('fumble_lost') == '1':
                fid = r.get('fumbled_1_player_id') or r.get('rusher_player_id') or r.get('receiver_player_id')
                add(fid, num(sc.get('fum_lost')), 'fum', 'a lost fumble')
            # two-point conversions, which are their own play and were
            # otherwise landing in the residual
            if r.get('two_point_conv_result') == 'success':
                if r.get('passer_player_id'):
                    add(r['passer_player_id'], num(sc.get('pass_2pt'), 2.0), 'conv',
                        'a two-point conversion pass')
                if r.get('receiver_player_id'):
                    add(r['receiver_player_id'], num(sc.get('rec_2pt'), 2.0), 'conv',
                        'a two-point conversion catch')
                if r.get('rusher_player_id'):
                    add(r['rusher_player_id'], num(sc.get('rush_2pt'), 2.0), 'conv',
                        'a two-point conversion run')
            # kicking
            fg = r.get('field_goal_result')
            if fg == 'made' and r.get('kicker_player_id'):
                d = int(num(r.get('kick_distance'), 0))
                # the long-kick keys are fgm_50_59 and fgm_60p; there is no
                # fgm_50p, and guessing it silently underpaid every long field
                # goal in the league by two points
                key = ('fgm_60p' if d >= 60 else 'fgm_50_59' if d >= 50 else
                       'fgm_40_49' if d >= 40 else 'fgm_30_39' if d >= 30 else
                       'fgm_20_29' if d >= 20 else 'fgm_0_19')
                add(r['kicker_player_id'], num(sc.get(key), 3.0), 'fg', f'a {d}-yard field goal', d)
            if r.get('extra_point_result') == 'good' and r.get('kicker_player_id'):
                add(r['kicker_player_id'], num(sc.get('xpm'), 1.0), 'xp', 'an extra point')
    # when each game ended, for parking residuals
    ends = {g: (ko.timestamp() + 3600 if ko else 0, win) for g, (ko, win) in games.items()}
    return out, ends, dst


# ---- assembling one matchup ------------------------------------------------
def fantasy_clock(window, rank, n):
    """Lay the r-th of n plays in a window onto that window's slice of 60:00."""
    lo, hi = next((a, b) for c, _, a, b in WINDOWS if c == window)
    t = lo + (hi - lo) * ((rank + 0.5) / max(n, 1))
    t = max(0, min(3599, t))
    q = min(4, int(t // 900) + 1)
    rem = 900 - (t - (q - 1) * 900)
    return dict(sec=round(t), qtr=q, clock=f'{int(rem // 60):02d}:{int(rem % 60):02d}')


def build_game(game, evmap, ends, by_espn, by_name, misses, dst=None):
    sides = []
    for t in game['teams']:
        evs, resid = [], 0.0
        for pl in t['starters']:
            if (pl.get('pos') or '').upper() == 'DEF':
                gid, how = tm(pl.get('nfl') or pl.get('id')), 'team'
                mine = list((dst or {}).get(gid, []))
            else:
                gid, how = resolve(pl, by_espn, by_name, evmap)
                mine = list(evmap.get(gid, [])) if gid else []
            got = sum(e['pts'] for e in mine)
            want = float(pl.get('points') or 0)
            if not gid or (how != 'team' and not mine and float(pl.get('points') or 0)):
                misses.append(f"{pl['name']} ({pl.get('pos')}/{pl.get('nfl')})")
            for e in mine:
                evs.append(dict(e, player=pl['name'], pos=pl.get('pos'), nfl=pl.get('nfl')))
            # residual: real points we could not pin to a play. Kept so the
            # running score lands on the true final, flagged so no writer can
            # turn it into a sentence about something that happened.
            d = round(want - got, 2)
            if abs(d) >= 0.05:
                resid += d
                when, win = ends.get(next((e['game_id'] for e in mine), ''), (0, 'SUNPM'))
                if not when:
                    when, win = 0, 'SUNPM'
                evs.append(dict(player=pl['name'], pos=pl.get('pos'), nfl=pl.get('nfl'),
                                pts=d, kind='residual', text='', yards=None, td=False,
                                residual=True, abs_ts=when, window=win,
                                game_id='', nfl_qtr='', nfl_clock='', posteam=pl.get('nfl')))
        sides.append({'team': t['team'], 'final': t['points'], 'events': evs,
                      'residual': round(resid, 2)})

    A, B = sides
    allev = ([dict(e, side=0) for e in A['events']] + [dict(e, side=1) for e in B['events']])
    # unknown kickoff sorts last within its window rather than to 1970
    allev.sort(key=lambda e: (WIN_ORDER.get(e['window'], 9), e['abs_ts'] or 9e18))
    bywin = {}
    for e in allev:
        bywin.setdefault(e['window'], []).append(e)
    for win, lst in bywin.items():
        for i, e in enumerate(lst):
            e['fc'] = fantasy_clock(win, i, len(lst))

    run = [0.0, 0.0]
    lead = None
    flips, timeline = [], []
    for e in allev:
        before = run[0] - run[1]
        run[e['side']] = round(run[e['side']] + e['pts'], 2)
        after = round(run[0] - run[1], 2)
        now = 0 if after > 0 else (1 if after < 0 else None)
        e['score'] = [round(run[0], 2), round(run[1], 2)]
        e['lead'] = after
        # a flip is a real change of who is winning, not a tie being broken back
        if now is not None and now != lead and abs(after) > 0.001:
            # Taking the first lead of the game is not a lead CHANGE -- there
            # was nothing to change. Only flag it once somebody has already led.
            if lead is not None:
                e['go_ahead'] = True
                flips.append(e)
            lead = now
        timeline.append(e)

    narratable = [e for e in timeline if not e['residual']]
    tds = [e for e in narratable if e['td']]
    go = flips[-1] if flips else None
    # the play that won it: last lead change, but only if it is a real play
    if go and go.get('residual'):
        go = next((e for e in reversed(flips) if not e['residual']), None)

    return {
        'matchup_id': game['matchup_id'],
        'teams': [{'team': s['team'], 'final': s['final'], 'residual': s['residual']} for s in sides],
        'winner': A['team'] if A['final'] >= B['final'] else B['team'],
        'margin': round(abs(A['final'] - B['final']), 2),
        'lead_changes': len(flips),
        'go_ahead': go,
        'touchdowns': len(tds),
        'timeline': timeline,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, required=True)
    ap.add_argument('--season', default='2026')
    ap.add_argument('--game', type=int, default=-1)
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()

    src = os.path.join(WDIR, f'{a.season}-w{a.week}.json')
    if not os.path.exists(src):
        sys.exit(f'no {src} -- run the fetch-week workflow first')
    wd = json.load(open(src, encoding='utf-8'))
    sc = wd['scoring'] or {}

    by_espn, by_name = crosswalk()
    evmap, ends, dst = play_events(a.season, a.week, sc)
    print(f'  {sum(len(v) for v in evmap.values()):,} scoring attributions across '
          f'{len(evmap):,} players and {len(dst)} defences in week {a.week}')

    misses = []
    games = [build_game(g, evmap, ends, by_espn, by_name, misses, dst) for g in wd['games']]

    tot = sum(1 for g in wd['games'] for t in g['teams'] for p in t['starters'])
    print(f'  unmatched starters: {len(misses)}/{tot}')
    if misses and a.verbose:
        for m in misses[:20]:
            print('     ', m)
    for g in games:
        res = sum(abs(t['residual']) for t in g['teams'])
        print(f"    {g['teams'][0]['team']} {g['teams'][0]['final']} - "
              f"{g['teams'][1]['final']} {g['teams'][1]['team']}  "
              f"| {g['lead_changes']} lead change(s), {g['touchdowns']} TDs, "
              f"residual {res:.1f}")

    out = {'league': wd['league'], 'season': wd['season'], 'week': wd['week'],
           'builtFrom': 'nflverse play-by-play + Sleeper week data',
           'windows': [{'code': c, 'label': l, 'from': a0, 'to': b0} for c, l, a0, b0 in WINDOWS],
           'games': games}
    dst = os.path.join(WDIR, f'{a.season}-w{a.week}-replay.json')
    json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'  wrote {os.path.relpath(dst, ROOT)}')

    if a.game >= 0:
        g = games[a.game]
        print(f"\n--- {g['teams'][0]['team']} vs {g['teams'][1]['team']} ---")
        for e in g['timeline']:
            if e['residual'] and not a.verbose:
                continue
            tag = ' <<< GO AHEAD' if e.get('go_ahead') else ''
            star = '*' if e['td'] else ' '
            print(f"  Q{e['fc']['qtr']} {e['fc']['clock']} {star} {e['player'][:22]:<23}"
                  f"{(e['text'] or e['kind'])[:30]:<31} {e['pts']:+6.2f}  "
                  f"{e['score'][0]:6.2f}-{e['score'][1]:<6.2f}{tag}")


if __name__ == '__main__':
    main()
