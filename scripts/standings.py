#!/usr/bin/env python3
"""The season's table, built from the weeks already on disk.

    python3 scripts/standings.py --through 4

A game report that does not say what the result did to anybody's season is not
a report, it is a box score with adjectives. This supplies the part that was
missing: what each team's record became, what it was before, whether they are
on a run or in a hole, where they sit in their division and in the league, and
how far they are from the playoff line.

Everything comes from week-data/{season}-w*.json, so it only knows about weeks
that have actually been fetched. Divisions, the playoff cutoff and the length
of the regular season come from sleeper-schedule.json.
"""
import argparse, glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')
TEAM = lambda s: (s or '').strip().strip('*').strip()


def league():
    """Division membership, keyed by roster id rather than by team name.

    The schedule file was written in August and two franchises have renamed
    since -- this league has a rule that forces one every year -- so a name is
    not an identity. Roster ids do not move. The schedule's own week listings
    give the name-to-roster mapping as it was then, which is what bridges the
    old names in divisions.of to the teams playing now.
    """
    p = os.path.join(ROOT, 'sleeper-schedule.json')
    d = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    div = d.get('divisions') or {}
    rid = {}
    for games in (d.get('weeks') or {}).values():
        for g in games:
            if g.get('home') and g.get('home_roster'):
                rid[TEAM(g['home'])] = g['home_roster']
            if g.get('away') and g.get('away_roster'):
                rid[TEAM(g['away'])] = g['away_roster']
    of_rid = {}
    for nm, dv in (div.get('of') or {}).items():
        r = rid.get(TEAM(nm))
        if r is not None:
            of_rid[r] = dv
    return {
        'names': {int(k): v for k, v in (div.get('names') or {}).items()},
        'of': {TEAM(k): v for k, v in (div.get('of') or {}).items()},
        'of_rid': of_rid,
        'playoff_week': d.get('playoff_week_start') or 15,
        'teams': len(div.get('of') or {}) or 16,
    }


def weeks_on_disk(season):
    out = []
    for f in glob.glob(os.path.join(WDIR, f'{season}-w*.json')):
        m = re.search(r'-w(\d+)\.json$', f)
        if m and 'replay' not in f and 'stories' not in f:
            out.append(int(m.group(1)))
    return sorted(out)


def build(season, through):
    """Records after every week up to `through`, plus the week-by-week trail."""
    L = league()
    have = [w for w in weeks_on_disk(season) if w <= through]
    if not have:
        return None
    rows = {}
    trail = {}            # team -> [(week, 'W'/'L'/'T', pf, pa, opp)]
    for wk in have:
        d = json.load(open(os.path.join(WDIR, f'{season}-w{wk}.json'), encoding='utf-8'))
        for g in d['games']:
            a, b = g['teams']
            an, bn = TEAM(a['team']), TEAM(b['team'])
            ap, bp = a['points'], b['points']
            for nm, pf, pa, opp, rid in ((an, ap, bp, bn, a.get('roster_id')),
                                         (bn, bp, ap, an, b.get('roster_id'))):
                r = rows.setdefault(nm, {'team': nm, 'w': 0, 'l': 0, 't': 0,
                                         'pf': 0.0, 'pa': 0.0, 'roster_id': rid,
                                         'div': L['of_rid'].get(rid) or L['of'].get(nm)})
                res = 'T' if pf == pa else ('W' if pf > pa else 'L')
                r['w' if res == 'W' else 'l' if res == 'L' else 't'] += 1
                r['pf'] = round(r['pf'] + pf, 2)
                r['pa'] = round(r['pa'] + pa, 2)
                trail.setdefault(nm, []).append((wk, res, pf, pa, opp))

    for nm, r in rows.items():
        t = trail[nm]
        r['games'] = len(t)
        r['record'] = f"{r['w']}-{r['l']}" + (f"-{r['t']}" if r['t'] else '')
        # the record BEFORE the last week counted, for "moved to" / "fell to"
        pw = sum(1 for x in t[:-1] if x[1] == 'W')
        pl = sum(1 for x in t[:-1] if x[1] == 'L')
        pt = sum(1 for x in t[:-1] if x[1] == 'T')
        r['prev_record'] = f'{pw}-{pl}' + (f'-{pt}' if pt else '')
        r['last'] = t[-1][1]
        # current streak
        k, s = 1, t[-1][1]
        for x in reversed(t[:-1]):
            if x[1] == s:
                k += 1
            else:
                break
        r['streak'] = f'{s}{k}'
        r['streak_n'], r['streak_kind'] = k, s
        r['trail'] = t

    order = sorted(rows.values(), key=lambda r: (-r['w'], -r['pf']))
    for i, r in enumerate(order):
        r['seed'] = i + 1
    for dv in set(x['div'] for x in rows.values() if x['div']):
        dl = sorted((r for r in rows.values() if r['div'] == dv),
                    key=lambda r: (-r['w'], -r['pf']))
        for i, r in enumerate(dl):
            r['div_rank'] = i + 1
            r['div_name'] = L['names'].get(dv, f'Division {dv}')
            r['div_size'] = len(dl)
    return {'season': season, 'through': max(have), 'weeks': have,
            'playoff_week': L['playoff_week'], 'teams': len(rows),
            'table': order, 'by_team': rows,
            'div_names': L['names']}


ORD = {1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth', 6: 'sixth',
       7: 'seventh', 8: 'eighth'}


def situation(st, team):
    """One clause describing where a result left them. Prose, not a table.

    The streak is only worth saying when the record does not already say it: a
    team at 3-0 on a three-game winning run is one fact, not two.
    """
    r = st['by_team'].get(TEAM(team))
    if not r:
        return ''
    moved = 'moved to' if r['last'] == 'W' else ('fell to' if r['last'] == 'L' else 'drew to')
    s = f"{moved} {r['record']}"
    perfect = r['streak_n'] == r['games']          # unbeaten or winless; record says it
    if r['streak_n'] >= 2 and not perfect:
        if r['streak_kind'] == 'W':
            s += (' and a second straight win' if r['streak_n'] == 2
                  else f" and {ORD.get(r['streak_n'], str(r['streak_n']))} in a row")
        else:
            s += (' and a second straight defeat' if r['streak_n'] == 2
                  else f" and {ORD.get(r['streak_n'], str(r['streak_n']))} straight defeat")
    if r.get('div_rank'):
        s += f", {ORD.get(r['div_rank'], r['div_rank'])} in {r['div_name']}"
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--season', default='2026')
    ap.add_argument('--through', type=int, default=99)
    a = ap.parse_args()
    st = build(a.season, a.through)
    if not st:
        sys.exit('no week data on disk yet')
    print(f"{st['season']} through week {st['through']} "
          f"(weeks on disk: {', '.join(map(str, st['weeks']))})\n")
    print(f"{'':3}{'team':<24}{'rec':>7}{'PF':>9}{'PA':>9}  {'strk':<5}{'division'}")
    for r in st['table']:
        print(f"{r['seed']:>2} {r['team'][:23]:<24}{r['record']:>7}{r['pf']:>9.1f}"
              f"{r['pa']:>9.1f}  {r['streak']:<5}"
              f"{r.get('div_name','')} #{r.get('div_rank','-')}")


if __name__ == '__main__':
    main()
