#!/usr/bin/env python3
"""Offline audit tool for the trade-value model -- NOT a build step the app
consumes. Its output (tradeValues.json, gitignored) is a real, explainable
number on every asset in every trade in trades.json (256 deals, 2021-2026),
computed at the trade's own season, never with hindsight.

    python3 scripts/build_trade_values.py

This script was the prototype for what actually shipped: the app's existing
Trade Court (index.html: tcChatAssetVal / expectedFuturePickValue /
dpValueAt) got upgraded in place with the two real improvements this script
proved out, rather than shipping a second, competing value system. See "How
this actually shipped" at the bottom of docs/TRADE-VALUE-MODEL.md. Keep this
script around as an independent, inspectable cross-check -- it's what
validated the live JS regression fit bit-for-bit (a/b/sigma/n all match
exactly) before that code went live.

Design and methodology: docs/TRADE-VALUE-MODEL.md. Short version:

  PLAYERS  -> dp-values.json's Aug-of-that-season DynastyProcess snapshot.
              Verified contemporaneous (a rookie's own draft-year Aug value
              reflects preseason hype, not outcome -- see the design doc).
  PICKS    -> draft-intel.json's pickValueChart (already calibrated to 235
              real SCFL trades) for an exact-slot pick ("2021 pick 26").
              A round-only future pick ("2022 2nd (DoD)") gets an expected
              value instead: the pick-owning franchise's most recently
              COMPLETED season rank feeds a regression fitted from real
              rank-to-rank persistence in history.json (18 seasons, 266
              consecutive-season pairs -- correlation is weak, r^2 ~ 0.03,
              so this stays close to a league-average assumption on
              purpose; fantasy standings just don't carry over much).
  CLASSES  -> a small (+-15% capped) multiplier per draft-class year, from
              that class's rookies' first-available (still contemporaneous)
              dp-values snapshot vs. the all-class average.
  LIFECYCLE-> a label (rookie/ascending/established/declining/aged-out)
              read off the shape of each player's own dp-values curve --
              cosmetic, layered on top of the number, not a separate model.

Every asset keeps its resolved value AND how it was resolved (exact slot,
expected value, dp-values hit, name-fix applied, unresolved fallback) so
nothing here is a black box. Assets that can't be resolved (an untracked
DST, a genuine data gap) get value 0 and are logged in "unresolved", not
silently guessed.
"""
import json, os, re, sys, collections, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import build_players as bp  # reuse the already-verified name/team canonicalization

def load(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return json.load(f)

# ---------------------------------------------------------------------------
# Franchise identity: every team-name string and every pick-tag abbreviation
# in trades.json, resolved to one franchise key via scfl-franchises.json.
# ---------------------------------------------------------------------------
FR = load('scfl-franchises.json')
ALIAS_TO_KEY = {}
CLUB_OF = {}
MANAGER_OF = {}
for f in FR['franchises']:
    ALIAS_TO_KEY[f['club']] = f['key']
    for a in f.get('aliases', []):
        ALIAS_TO_KEY[a] = f['key']
    CLUB_OF[f['key']] = f['club']
    MANAGER_OF[f['key']] = f.get('manager')

def team_key(team_name):
    k = ALIAS_TO_KEY.get(team_name.strip())
    if not k:
        raise ValueError(f'unresolved team name: {team_name!r}')
    return k

# Pick-tag abbreviations seen in trades.json (verified against the full list
# of distinct parenthetical tags -- see the build log below for the audit).
TAG_MAP = {
    'machines': 'machines',
    'creams': 'stillthecream',
    'dragons': 'smokedragons', 'smoke dragons': 'smokedragons',
    'hitters': 'heavyhitters', 'heavy hitters': 'heavyhitters',
    'jet-i': 'masterjeti', 'jeti': 'masterjeti', 'jet-': 'masterjeti',
    'klowns': 'killerklowns',
    'nwo': 'newworldorder',
    'wookies': 'wookieleaks', 'wookie leaks': 'wookieleaks',
    'pop': 'powersofpain', 'power of pain': 'powersofpain', 'powers of pain': 'powersofpain',
    'guidos': 'guidohaters', 'guido haters': 'guidohaters',
    'a-team': 'lilchops', 'chops': 'lilchops', 'porkys': 'lilchops', 'dod': 'lilchops',
    'beavers': 'beavereaters', 'sdft': 'beavereaters',
    'collars': 'horsecollars',
    'pce': 'porkchopexpress', 'pork chop express': 'porkchopexpress',
    'gumbas': 'gumbas',
}

# One verified data-entry typo: a 2024-season trade references a "2017 1st"
# future pick, which is impossible (2017 is long past). "2027 1st (Porkys)"
# is a real, separately-existing entry in the same shape -- almost certainly
# a digit transposition. Hand-verified, not an auto-correct heuristic.
PICK_YEAR_FIXES = {'2017 1st (Porkys)': 2027}

def norm_tag(s):
    return s.strip().lower().replace('’', '').replace("'", '')

def parse_pick(raw, trade_season):
    s = raw.strip()
    fixed_year = PICK_YEAR_FIXES.get(s)
    s2 = re.sub(r'(\d)n\s*Rd\s*Pick', r'\1nd', s, flags=re.I)
    s2 = re.sub(r'\blate\s+', '', s2, flags=re.I)
    s2 = re.sub(r'\bRd\.?\s*Pick\b', '', s2, flags=re.I)
    s2 = re.sub(r'\s+', ' ', s2).strip()

    m = re.match(r'^(\d{4})\s+pick\s+(\d+)$', s2, re.I)
    if m:
        return {'kind': 'exact', 'year': fixed_year or int(m.group(1)), 'slot': int(m.group(2)), 'raw': raw}

    m = re.match(r'^(\d{4})\s+(1st|2nd)\s*\((\d+)(st|nd|rd|th)\)$', s2, re.I)
    if m:
        year, rnd, ord_slot = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        overall = ord_slot if rnd == '1st' else 16 + ord_slot
        return {'kind': 'exact', 'year': fixed_year or year, 'slot': overall, 'raw': raw}

    m = re.match(r'^(\d{4})\s+(1st|2nd)\s*\(([^)]+)\)$', s2, re.I)
    if m:
        year, rnd, tag = int(m.group(1)), m.group(2).lower(), norm_tag(m.group(3))
        return {'kind': 'round', 'year': fixed_year or year, 'round': 1 if rnd == '1st' else 2,
                'tag': m.group(3), 'owner_key': TAG_MAP.get(tag), 'raw': raw}

    m = re.match(r'^(\d{4})\s+(1st|2nd)$', s2, re.I)
    if m:
        year, rnd = int(m.group(1)), m.group(2).lower()
        return {'kind': 'round', 'year': fixed_year or year, 'round': 1 if rnd == '1st' else 2,
                'tag': None, 'owner_key': None, 'raw': raw}

    return {'kind': 'unparsed', 'raw': raw}

# ---------------------------------------------------------------------------
# Slot-probability model, fit from real data -- see docs/TRADE-VALUE-MODEL.md.
# rank_next = A + B * rank_prior, residual ~ Normal(0, SIGMA), fit on 266
# consecutive-season (rank_t, rank_t+1) pairs, 2008-2025, franchise-resolved.
# ---------------------------------------------------------------------------
HIST = load('history.json')
RANK_BY_SEASON = {}  # year -> {franchise_key: rank}
for s in HIST['seasons']:
    owner_by_teamid = {t['id']: t['owner'] for t in s['teams']}
    ranks = {}
    for row in s.get('standings', []):
        owner = owner_by_teamid.get(row['teamId'])
        key = FR['handles'].get(owner)
        if key:
            ranks[key] = row['rank']
    RANK_BY_SEASON[s['year']] = ranks

def _fit_rank_regression():
    years = sorted(RANK_BY_SEASON.keys())
    pairs = []
    for y0, y1 in zip(years, years[1:]):
        if y1 != y0 + 1:
            continue
        r0, r1 = RANK_BY_SEASON[y0], RANK_BY_SEASON[y1]
        for k in r0:
            if k in r1:
                pairs.append((r0[k], r1[k]))
    n = len(pairs)
    mx = sum(p[0] for p in pairs) / n
    my = sum(p[1] for p in pairs) / n
    sxx = sum((p[0] - mx) ** 2 for p in pairs)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pairs)
    b = sxy / sxx
    a = my - b * mx
    resid = [p[1] - (a + b * p[0]) for p in pairs]
    sigma = (sum(x * x for x in resid) / (n - 2)) ** 0.5
    return {'a': a, 'b': b, 'sigma': sigma, 'n': n, 'league_mean_rank': mx}

RANK_MODEL = _fit_rank_regression()

def most_recent_rank(franchise_key, before_season):
    """The franchise's rank in its last COMPLETED season strictly before
    before_season -- never the season the pick is actually for."""
    for y in range(before_season - 1, before_season - 6, -1):
        r = RANK_BY_SEASON.get(y, {}).get(franchise_key)
        if r is not None:
            return r
    return None

def slot_probabilities(prior_rank, years_out):
    """P(final rank = k) for k=1..16. years_out==1 uses the fitted
    regression; 2+ years out the fit is already close to flat (r^2 ~ .03
    at one year), so it's treated as fully uninformative -- a defensible
    simplification stated plainly rather than compounding a weak fit."""
    if prior_rank is None or years_out >= 2:
        return {k: 1 / 16 for k in range(1, 17)}
    mean = RANK_MODEL['a'] + RANK_MODEL['b'] * prior_rank
    sigma = RANK_MODEL['sigma']
    weights = {k: pow(2.718281828, -((k - mean) ** 2) / (2 * sigma * sigma)) for k in range(1, 17)}
    total = sum(weights.values())
    return {k: w / total for k, w in weights.items()}

# ---------------------------------------------------------------------------
# Pick values: draft-intel.json's SCFL-calibrated 32-slot curve.
# ---------------------------------------------------------------------------
DI = load('draft-intel.json')
PICK_CHART = {int(k): v for k, v in DI['pickValueChart'].items()}

def rank_to_slot(rank, rnd):
    """Worst record picks first (verified against draft.json / 2025
    standings -- rank 16 = worst finish gets round-1 slot 1)."""
    base = 17 - rank
    return base if rnd == 1 else base + 16

def expected_pick_value(prior_rank, rnd, years_out):
    probs = slot_probabilities(prior_rank, years_out)
    return sum(p * PICK_CHART[rank_to_slot(k, rnd)] for k, p in probs.items())

# ---------------------------------------------------------------------------
# Class-quality modifier: each draft class's rookies, first-available
# (still contemporaneous) dp-values snapshot vs. the all-class average.
# ---------------------------------------------------------------------------
DPV = load('dp-values.json')
DPV_YEARS = DPV['years']
DPV_V = DPV['v']

def _dp_norm(name):
    n = name.lower()
    n = re.sub(r"[.'’-]", '', n)
    n = re.sub(r'\b(jr|sr|ii|iii|iv)\b', '', n)
    return re.sub(r'\s+', ' ', n).strip()

DPV_BY_NORM = {_dp_norm(k): k for k in DPV_V}

def _class_quality_modifiers():
    # index 0 (2021) is the dataset's first year -- "first non-null value in
    # 2021" can't distinguish an actual 2021 rookie from a decade-long
    # veteran who simply already existed when the data starts (McCaffrey,
    # Mahomes both show up here). Only 2022+ classes are reliable: a value
    # appearing for the first time in, say, 2024 really does mean rookie.
    class_values = collections.defaultdict(list)
    for name, series in DPV_V.items():
        first_idx = next((i for i, v in enumerate(series) if v is not None), None)
        if first_idx is None or first_idx == 0:
            continue
        class_values[DPV_YEARS[first_idx]].append(series[first_idx])
    overall_avg = statistics.mean(v for vs in class_values.values() for v in vs)
    mods = {}
    for year, vals in class_values.items():
        if len(vals) < 8:  # too few rookies with a value that year to trust the signal
            continue
        ratio = statistics.mean(vals) / overall_avg
        mods[year] = max(0.85, min(1.15, ratio))
    return mods, overall_avg

CLASS_MODIFIER, CLASS_OVERALL_AVG = _class_quality_modifiers()

# ---------------------------------------------------------------------------
# Player values: dp-values.json at the trade's own season, name-resolved via
# build_players.py's canonicalization plus a short hand-verified fix list
# for the names that canonicalization alone couldn't place.
# ---------------------------------------------------------------------------
_players_out, _counts, _CANON = bp.build()

TRADE_NAME_FIX = {
    'Alan Lazard': 'Allen Lazard', 'Alex Pierce': 'Alec Pierce', 'Bagent': 'Tyson Bagent',
    'Buckey Irving': 'Bucky Irving', 'Callaway': 'Marquez Callaway',
    'Darrington Evans': 'Darrynton Evans', 'David Bellinger': 'Daniel Bellinger',
    'Dontavian Wicks': 'Dontayvion Wicks', 'Emeri Demercado': 'Emari Demercado',
    'Gadsden': 'Oronde Gadsden', 'Isaiah Pacheco': 'Isiah Pacheco', 'Pacheco': 'Isiah Pacheco',
    'Jalen Hyatt': 'Jalin Hyatt', 'Jayden Blue': 'Jaydon Blue', 'Jonu Smith': 'Jonnu Smith',
    'Mattison': 'Alexander Mattison', 'Mike Wilson': 'Michael Wilson', 'Mostert': 'Raheem Mostert',
    'Naheim Hines': 'Nyheim Hines', 'Rashaad White': 'Rachaad White', 'Rashad Bateman': 'Rashod Bateman',
    'Rhmonde Stevenson': 'Rhamondre Stevenson', 'Uzomah': 'C.J. Uzomah',
    "Aiden O'Connell": "Aidan O'Connell",
}
KNOWN_DST = {'Jets Defense', 'KC Defense', 'Panthers Defense', 'Pittsburgh D', 'Titans Defense'}

def canonical_player_name(raw):
    c = _CANON.get(raw.strip(), raw.strip())
    c = bp.DISPLAY_FIX.get(c, c)
    return TRADE_NAME_FIX.get(c, c)

def player_value(raw_name, season):
    name = canonical_player_name(raw_name)
    if raw_name.strip() in KNOWN_DST:
        return {'value': 0, 'matched': False, 'reason': 'dst-not-modeled', 'canonical': name}
    key = DPV_BY_NORM.get(_dp_norm(name))
    if not key:
        return {'value': 0, 'matched': False, 'reason': 'no-dp-values-match', 'canonical': name}
    try:
        idx = DPV_YEARS.index(season)
    except ValueError:
        idx = len(DPV_YEARS) - 1 if season > DPV_YEARS[-1] else 0
    series = DPV_V[key]
    v = series[idx]
    if v is None:
        # Walk BACKWARD only, to the most recent already-known snapshot --
        # never forward. Forward would price the asset off a value the
        # market hadn't set yet at trade time (real hindsight: 15 of 17
        # such gaps in this dataset are unproven rookies who simply hadn't
        # been valued yet). No prior value at all means the market truly
        # had no read on him yet -- 0 is the honest answer, not a guess.
        for j in range(idx - 1, -1, -1):
            if series[j] is not None:
                v = series[j]
                break
    return {'value': v or 0, 'matched': True, 'canonical': key, 'season_used': DPV_YEARS[idx],
            'notYetValued': v is None}

def lifecycle_tag(dp_key, season):
    """As-of-trade-time only -- uses the curve through this season's index,
    never later years. A player who later declines still reads 'ascending'
    or 'established' for an earlier trade if that's what was knowable then."""
    series = DPV_V.get(dp_key)
    if not series:
        return None
    idx = DPV_YEARS.index(season) if season in DPV_YEARS else (
        0 if season < DPV_YEARS[0] else len(DPV_YEARS) - 1)
    prefix = series[:idx + 1]
    vals = [(i, v) for i, v in enumerate(prefix) if v is not None]
    if not vals:
        return None
    first_idx = vals[0][0]
    peak_idx, peak_val = max(vals, key=lambda x: x[1])
    cur_idx, cur_val = vals[-1]
    if cur_idx == first_idx:
        return 'rookie'
    if cur_val <= 2:
        return 'aged-out'
    if cur_idx == peak_idx:
        return 'ascending'
    if cur_val >= 0.85 * peak_val:
        return 'established'
    if cur_val <= 0.6 * peak_val:
        return 'declining'
    return 'established'

# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------
def resolve_pick(p, trade, side, unresolved_log):
    if p['kind'] == 'unparsed':
        unresolved_log.append({'type': 'pick-unparsed', 'raw': p['raw'], 'season': trade['season']})
        return {'raw': p['raw'], 'value': 0, 'resolved': 'unparsed'}
    if p['kind'] == 'exact':
        v = PICK_CHART.get(p['slot'])
        if v is None:
            unresolved_log.append({'type': 'pick-bad-slot', 'raw': p['raw'], 'slot': p['slot']})
            return {'raw': p['raw'], 'value': 0, 'resolved': 'bad-slot'}
        return {'raw': p['raw'], 'value': v, 'resolved': 'exact-slot', 'slot': p['slot'], 'year': p['year']}
    # round-only
    owner_key = p['owner_key']
    if owner_key is None and p['tag'] is None:
        others = [s2 for s2 in trade['sides'] if s2 is not side]
        if len(others) == 1:
            owner_key = team_key(others[0]['team'])
        else:
            unresolved_log.append({'type': 'pick-ambiguous-owner', 'raw': p['raw'], 'season': trade['season']})
    elif owner_key is None:
        unresolved_log.append({'type': 'pick-unknown-tag', 'raw': p['raw'], 'tag': p['tag']})
    years_out = p['year'] - trade['season']
    prior_rank = most_recent_rank(owner_key, trade['season']) if owner_key else None
    base_v = expected_pick_value(prior_rank, p['round'], max(years_out, 1))
    mod = CLASS_MODIFIER.get(p['year'], 1.0)
    return {'raw': p['raw'], 'value': round(base_v * mod, 1), 'resolved': 'expected-value',
            'round': p['round'], 'year': p['year'], 'owner': CLUB_OF.get(owner_key, owner_key),
            'ownerPriorRank': prior_rank, 'classModifier': round(mod, 3)}

def build():
    T = load('trades.json')['trades']
    unresolved = []
    out_trades = []
    for t in T:
        season = t['season']
        out_sides = []
        for side in t['sides']:
            key = team_key(side['team'])
            assets = []
            total = 0
            for g in side['gets']:
                if 'player' in g:
                    pv = player_value(g['player'], season)
                    if not pv['matched']:
                        unresolved.append({'type': 'player-unmatched', 'raw': g['player'],
                                            'canonical': pv['canonical'], 'season': season, 'reason': pv['reason']})
                    tag = lifecycle_tag(pv.get('canonical'), season) if pv['matched'] else None
                    assets.append({'kind': 'player', 'name': g['player'], 'value': pv['value'],
                                    'matched': pv['matched'], 'lifecycle': tag})
                    total += pv['value']
                elif 'pick' in g:
                    p = parse_pick(g['pick'], season)
                    pr = resolve_pick(p, t, side, unresolved)
                    assets.append({'kind': 'pick', **pr})
                    total += pr['value']
            out_sides.append({'team': side['team'], 'franchiseKey': key, 'assets': assets,
                                'total': round(total, 1)})
        totals = [s['total'] for s in out_sides]
        out_trades.append({'season': season, 'sides': out_sides,
                            'differential': round(max(totals) - min(totals), 1) if len(totals) > 1 else 0})

    payload = {
        'note': 'built by scripts/build_trade_values.py from trades.json -- see docs/TRADE-VALUE-MODEL.md',
        'methodology': {
            'players': 'dp-values.json Aug snapshot for the trade\'s own season',
            'picksExact': 'draft-intel.json pickValueChart, direct lookup',
            'picksFuture': 'expected value over a slot-probability model fit from history.json '
                            f"({RANK_MODEL['n']} real consecutive-season pairs, r^2 tiny -- see design doc)",
            'classModifier': f'+-15% cap, {len(CLASS_MODIFIER)} classes with enough rookie data to trust',
            'rankRegression': {'a': round(RANK_MODEL['a'], 3), 'b': round(RANK_MODEL['b'], 3),
                                'sigma': round(RANK_MODEL['sigma'], 3), 'n': RANK_MODEL['n']},
        },
        'count': len(out_trades),
        'unresolvedCount': len(unresolved),
        'unresolved': unresolved,
        'trades': out_trades,
    }
    with open(os.path.join(ROOT, 'tradeValues.json'), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    return payload

if __name__ == '__main__':
    payload = build()
    print(f"trades valued: {payload['count']}")
    print(f"unresolved items: {payload['unresolvedCount']}")
    by_type = collections.Counter(u['type'] for u in payload['unresolved'])
    for k, v in by_type.items():
        print(f"  {k}: {v}")
    diffs = sorted(payload['trades'], key=lambda t: -t['differential'])[:5]
    print('\nlargest differentials:')
    for t in diffs:
        teams = ' vs '.join(f"{s['team']} ({s['total']})" for s in t['sides'])
        print(f"  {t['season']}  {teams}  -> diff {t['differential']}")
