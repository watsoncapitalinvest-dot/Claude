#!/usr/bin/env python3
"""How DEEP the waiver wire is, not how many bodies are on it.

    python3 scripts/waiver_depth.py        # writes ir-waiver-depth.json

The IR debate turns on a claim nobody had measured: that expanding injured
reserve thins the waiver pool. ir_watch.py already counts free agents, but a
headcount is the wrong instrument -- it counted about 500 all season while every
manager in the league was saying the wire was bare. Both things were true. The
bodies were there; the usable players were not.

So this measures usable depth. A free agent counts as STARTABLE in a given week
if he outscored the worst man the league actually started at his position that
week -- i.e. he would have improved somebody's lineup. The thresholds come from
the league's own slots: 16 QB plus 16 superflex, 32 RB, 48 WR, 16 TE, 16 K,
16 DEF.

Kickers and defences are reported separately and kept out of the headline. Half
the league's kickers and half its defences are unrostered by construction, so
including them makes the wire look four times deeper than it plays.

Scoring is the same model used everywhere on this desk, validated against what
Sleeper actually paid: 262 of 263 rostered skill players exact in week 5, 17 of
17 kickers, 16 of 20 defences.

Input that is NOT in this repo: nflverse play-by-play, ~5MB, downloaded to the
cache on first run. That is why this writes a committed JSON rather than being
computed inside build_ir_study.py -- the page must build without a network.
"""
import collections, csv, gzip, json, os, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'ir-waiver-depth.json')
CACHE = os.path.join(ROOT, '.cache')
PBP = os.path.join(CACHE, 'pbp_2026.csv.gz')
PLAYERS = os.path.join(CACHE, 'players.csv')
PBP_URL = 'https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2026.csv.gz'
PL_URL = 'https://github.com/nflverse/nflverse-data/releases/download/players/players.csv'

# what the league actually starts each week: 16 teams x the slot list.
# SUPER_FLEX is counted as a QB slot -- every team in this league starts a
# second quarterback in it, so 32 is the real bar at the position.
SLOTS = {'QB': 32, 'RB': 32, 'WR': 48, 'TE': 16, 'K': 16, 'DEF': 16}
S = {'py': 0.02, 'ptd': 6, 'pint': -2, 'ry': 0.1, 'rtd': 6, 'recy': 0.1,
     'rectd': 6, 'fl': -2, 'tp': 2}
TEAM_AB = {'Arizona Cardinals': 'ARI', 'Atlanta Falcons': 'ATL', 'Baltimore Ravens': 'BAL',
 'Buffalo Bills': 'BUF', 'Carolina Panthers': 'CAR', 'Chicago Bears': 'CHI',
 'Cincinnati Bengals': 'CIN', 'Cleveland Browns': 'CLE', 'Dallas Cowboys': 'DAL',
 'Denver Broncos': 'DEN', 'Detroit Lions': 'DET', 'Green Bay Packers': 'GB',
 'Houston Texans': 'HOU', 'Indianapolis Colts': 'IND', 'Jacksonville Jaguars': 'JAX',
 'Kansas City Chiefs': 'KC', 'Las Vegas Raiders': 'LV', 'Los Angeles Chargers': 'LAC',
 'Los Angeles Rams': 'LA', 'Miami Dolphins': 'MIA', 'Minnesota Vikings': 'MIN',
 'New England Patriots': 'NE', 'New Orleans Saints': 'NO', 'New York Giants': 'NYG',
 'New York Jets': 'NYJ', 'Philadelphia Eagles': 'PHI', 'Pittsburgh Steelers': 'PIT',
 'San Francisco 49ers': 'SF', 'Seattle Seahawks': 'SEA', 'Tampa Bay Buccaneers': 'TB',
 'Tennessee Titans': 'TEN', 'Washington Commanders': 'WAS'}
ALIAS = {'LAR': ['LA', 'LAR'], 'LA': ['LA', 'LAR']}


def fetch(url, path):
    if os.path.exists(path):
        return path
    os.makedirs(CACHE, exist_ok=True)
    print(f'  downloading {os.path.basename(path)} ...')
    urllib.request.urlretrieve(url, path)
    return path


def forms(full):
    """pbp abbreviates first names, and uses two letters when a surname collides
    on the same team -- Bi.Robinson and Br.Robinson are both Atlanta."""
    a = full.replace('’', "'").split()
    if len(a) < 2:
        return [full]
    f, l = a[0], ' '.join(a[1:])
    out = []
    for p in (f[0], f[:2]):
        for last in (l, l.replace("'", ''), l.replace('.', '')):
            out.append(f'{p}.{last}')
    return out + [full]


def score():
    """Every scoring entity, by week, keyed name|team. See the module docstring
    for the validation this model passed."""
    fetch(PBP_URL, PBP)
    pts = collections.defaultdict(lambda: collections.defaultdict(float))
    kick = collections.defaultdict(lambda: collections.defaultdict(float))
    ev = collections.defaultdict(lambda: collections.defaultdict(float))
    allow, weeks = collections.defaultdict(dict), set()

    def add(n, t, w, v):
        if n and t:
            pts[(n, t)][w] += v
    with gzip.open(PBP, 'rt', encoding='utf-8', errors='replace') as fh:
        for r in csv.DictReader(fh):
            w = r.get('week')
            if not (w and w.isdigit()):
                continue
            w = int(w); weeks.add(w)
            f = lambda k: float(r.get(k) or 0)
            po, de = r.get('posteam'), r.get('defteam')
            if r.get('passer_player_name'):
                add(r['passer_player_name'], po, w, f('passing_yards') * S['py']
                    + (S['ptd'] if r.get('pass_touchdown') == '1' else 0)
                    + (S['pint'] if r.get('interception') == '1' else 0))
            if r.get('rusher_player_name'):
                add(r['rusher_player_name'], po, w, f('rushing_yards') * S['ry']
                    + (S['rtd'] if r.get('rush_touchdown') == '1' else 0))
            if r.get('receiver_player_name') and r.get('complete_pass') == '1':
                add(r['receiver_player_name'], po, w, f('receiving_yards') * S['recy']
                    + (S['rectd'] if r.get('pass_touchdown') == '1' else 0))
            if r.get('fumbled_1_player_name') and r.get('fumble_lost') == '1':
                add(r['fumbled_1_player_name'], po, w, S['fl'])
            if r.get('two_point_conv_result') == 'success':
                for k in ('passer_player_name', 'receiver_player_name', 'rusher_player_name'):
                    if r.get(k):
                        add(r[k], po, w, S['tp'])
            # kickers: ONLY field goals and extra points identify a kicker's
            # team. posteam on a kickoff is the receiving side.
            kid = r.get('kicker_player_name')
            if kid:
                if r.get('field_goal_attempt') == '1' and r.get('field_goal_result') == 'made':
                    d = float(r.get('kick_distance') or 0)
                    kick[(kid, po)][w] += 3.0 if d < 40 else 4.0 if d < 50 else 5.0
                if r.get('extra_point_attempt') == '1' and r.get('extra_point_result') == 'good':
                    kick[(kid, po)][w] += 1.0
            if de:
                if r.get('sack') == '1': ev[de][w] += 2
                if r.get('interception') == '1': ev[de][w] += 2
                if r.get('fumble_lost') == '1' and r.get('fumble_recovery_1_team') == de:
                    ev[de][w] += 2
                if r.get('safety') == '1': ev[de][w] += 4
                if r.get('touchdown') == '1' and r.get('td_team') == de: ev[de][w] += 6
            if r.get('home_score'):
                allow[r.get('home_team')][w] = float(r.get('away_score') or 0)
                allow[r.get('away_team')][w] = float(r.get('home_score') or 0)
    tier = lambda p: (10 if p == 0 else 7 if p <= 6 else 4 if p <= 13 else 2 if p <= 20
                      else 1 if p <= 27 else -1 if p <= 34 else -4)
    return pts, kick, ev, allow, sorted(weeks)


def positions():
    """name|team -> position, with a name-only fallback.

    Keyed on the team as well because an abbreviated surname collides: a
    name-only table put Josh Palmer at quarterback, because some other
    J. Palmer was read first. Same failure mode as the age lookup that
    once aged Marvin Harrison to 54.
    """
    fetch(PL_URL, PLAYERS)
    pos, loose, dupe = {}, {}, set()
    with open(PLAYERS, encoding='utf-8', errors='replace') as fh:
        for r in csv.DictReader(fh):
            n, p = r.get('display_name') or '', r.get('position') or ''
            t = r.get('latest_team') or ''
            if not (n and p):
                continue
            for f in forms(n):
                if t:
                    pos[f'{f}|{t}'] = p
                if f in loose and loose[f] != p:
                    dupe.add(f)                   # ambiguous: refuse to guess
                loose.setdefault(f, p)
    for f in dupe:
        loose.pop(f, None)
    return pos, loose


def build():
    pts, kick, ev, allow, _ = score()
    pos, loose = positions()
    tier = lambda p: (10 if p == 0 else 7 if p <= 6 else 4 if p <= 13 else 2 if p <= 20
                      else 1 if p <= 27 else -1 if p <= 34 else -4)
    U = {}
    for (n, t), d in pts.items():
        p = None
        for tt in ALIAS.get(t, [t]):
            p = p or pos.get(f'{n}|{tt}')
        p = p or loose.get(n)
        if p in ('QB', 'RB', 'WR', 'TE'):
            U[f'{n}|{t}'] = {'n': n, 't': t, 'p': p, 'wk': dict(d)}
    for (n, t), d in kick.items():
        U[f'K|{n}|{t}'] = {'n': n, 't': t, 'p': 'K', 'wk': dict(d)}
    for t, wk in allow.items():
        U[f'D|{t}'] = {'n': t, 't': t, 'p': 'DEF',
                       'wk': {w: ev[t].get(w, 0) + tier(pa) for w, pa in wk.items()}}

    def find(pl):
        for t in ALIAS.get(pl['nfl'], [pl['nfl']]):
            for f in forms(pl['name']):
                if f'{f}|{t}' in U:
                    return f'{f}|{t}'
        return None

    rows = []
    import glob, re as _re
    # match only the plain week files: -replay, -written and -stories are
    # derived and a loose rsplit on 'w' lets "2026-w5-written.json" through
    for path in sorted(glob.glob(os.path.join(ROOT, 'week-data', '2026-w*.json')),
                       key=lambda p: int(_re.search(r'w(\d+)\.json$', p).group(1))
                       if _re.search(r'w(\d+)\.json$', p) else 99):
        if not _re.search(r'/\d{4}-w\d+\.json$', path):
            continue
        d = json.load(open(path, encoding='utf-8'))
        wk = d['week']
        sc = [t['points'] for g in d['games'] for t in g['teams']]
        st = [p for g in d['games'] for t in g['teams'] for p in t['starters']]
        zero = sum(1 for p in st if p['points'] == 0) / max(len(st), 1)
        if not (sc and min(sc) >= 30 and zero < 0.07):      # the two tells
            continue
        owned = set()
        for g in d['games']:
            for t in g['teams']:
                for p in t['starters'] + t['bench'] + t.get('reserve', []):
                    if p['pos'] == 'K':
                        for f in forms(p['name']):
                            owned.add(f'K|{f}|{p["nfl"]}')
                    elif p['pos'] == 'DEF':
                        owned.add(f'D|{TEAM_AB.get(p["name"], p["name"])}')
                    else:
                        k = find(p)
                        if k:
                            owned.add(k)
        bar, mid = {}, {}
        for P, n in SLOTS.items():
            s = sorted((v['wk'][wk] for v in U.values() if v['p'] == P and wk in v['wk']),
                       reverse=True)
            # two bars. REPLACEMENT is the worst man the league actually started
            # at the position; MEDIAN is the middle one. Clearing replacement
            # means "better than somebody's worst option", which is a low bar and
            # counts a dozen-odd men a week. Clearing the median means "would
            # improve a real lineup", which is the handful everybody means when
            # they say the wire is bare.
            bar[P] = s[n - 1] if len(s) >= n else (s[-1] if s else 0)
            mid[P] = s[n // 2 - 1] if len(s) >= n // 2 else (s[-1] if s else 0)
        free = [(v['wk'][wk], v['p'], v['n']) for k, v in U.items()
                if k not in owned and wk in v['wk']]
        skill = [f for f in free if f[1] in ('QB', 'RB', 'WR', 'TE')]
        rows.append({
            'week': wk,
            'scored': len(free),
            'startable_all': sum(1 for f in free if f[0] >= bar[f[1]]),
            'startable_skill': sum(1 for f in skill if f[0] >= bar[f[1]]),
            'upgrade_skill': sum(1 for f in skill if f[0] >= mid[f[1]]),
            'upgrades': [{'name': n, 'pos': p, 'pts': round(v, 1)}
                         for v, p, n in sorted(skill, reverse=True) if v >= mid[p]],
            'top_skill': [{'name': n, 'pos': p, 'pts': round(v, 1)}
                          for v, p, n in sorted(skill, reverse=True)[:5]],
            'bar': {k: round(v, 2) for k, v in bar.items()},
            'median_bar': {k: round(v, 2) for k, v in mid.items()},
        })
    out = {'note': 'Usable waiver depth. upgrade_skill is the headline: unrostered QB/RB/WR/TE '
                   'who outscored the MEDIAN man the league started at their position that '
                   'week -- the men who would actually improve a lineup. startable_skill uses '
                   'the weaker replacement-level bar (the worst starter) and runs about four '
                   'times higher. A raw headcount of free agents is deliberately NOT reported: '
                   'it reads ~500 all season and measures nothing anybody cares about. '
                   'Written by scripts/waiver_depth.py; see that file for the model and its '
                   'validation. Weeks not yet played are skipped.',
           'slots': SLOTS, 'rows': rows}
    json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=1)
    print(f'wrote {os.path.basename(OUT)} ({len(rows)} played weeks)')
    for r in rows:
        print(f"  wk{r['week']}: {r['upgrade_skill']:2d} would upgrade a lineup, "
              f"{r['startable_skill']:2d} beat a replacement starter  "
              f"[{', '.join(u['name'] for u in r['upgrades'][:4]) or 'nobody'}]")


if __name__ == '__main__':
    build()
