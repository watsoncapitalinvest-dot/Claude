#!/usr/bin/env python3
"""How well is each roster actually managed? A control for the IR study.

    python3 scripts/manager_quality.py            # the table
    python3 scripts/manager_quality.py --json     # and manager-quality.json

WHY THIS EXISTS

The IR study found three sides that dropped an injured man while holding a
free injured-reserve slot, and read that as evidence the counterfactual's
filling assumption is too generous. The obvious objection is that it may be
evidence about three particular managers instead, and the same objection
applies with far more force to the headline finding: if the sides that keep
hitting the cap are simply the sides that hoard injured players, then the cap
"binding" is partly self-inflicted and section 1 is measuring management.

So manager quality needs a number, measured in a way that has nothing to do
with injured reserve.

WHAT IS MEASURED

Lineup efficiency: points actually started, against the most points that
roster could legally have started that week.

The optimum respects slot eligibility, which is the whole difficulty. This
league starts QB, RB, RB, WR, WR, WR, TE, SUPER_FLEX, K, DEF. A manager who
"left a 20-point RB on the bench" did nothing wrong if every RB seat was
already filled by someone better -- the men were never competing for the same
chair. So the optimum takes the best man for each positional seat and then
the best remaining QB/RB/WR/TE for the superflex, which is optimal here
because the flex is a strict superset of the positional slots.

Men on injured reserve are excluded: they could not have been started.

WHAT IT CANNOT SEE, AND IT MATTERS

A player ruled out an hour before kickoff punishes the manager here exactly as
much as one ruled out on the Wednesday. That is the convention and it is not
really fair, but it applies to all sixteen equally, and over six weeks the
luck in it washes out faster than the skill does.

It is also one measure of management, not the whole of it. Drafting, trading
and waiver work are all invisible to it. A manager can set a perfect lineup
every week from a badly built roster and score 97% here.
"""
import argparse, glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Gitignored on purpose -- see the entry in .gitignore. The aggregate goes in
# the study; the sixteen-name ranking does not go in a public repo.
OUT = os.path.join(ROOT, 'manager-quality.json')
FLEX = {'SUPER_FLEX': {'QB', 'RB', 'WR', 'TE'},
        'FLEX': {'RB', 'WR', 'TE'},
        'REC_FLEX': {'WR', 'TE'},
        'WRRB_FLEX': {'RB', 'WR'}}


def week_files():
    """Played weeks only, by the two-tell test the desk uses everywhere.

    A partial week file looks exactly like a finished one. min(points) >= 30
    catches a week nobody has played; the share of starters on exactly 0
    catches a week half played, which finished weeks run at 1-6% and a Sunday
    evening reads at 10%. One tell alone has flipped a conclusion twice.
    """
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, 'week-data', '*.json'))):
        m = re.match(r'^(\d{4})-w(\d+)\.json$', os.path.basename(p))
        if not m:
            continue
        d = json.load(open(p, encoding='utf-8'))
        sides = [s for g in d['games'] for s in g['teams']]
        pts = [s['points'] for s in sides]
        st = [p2 for s in sides for p2 in s['starters']]
        zeros = sum(1 for p2 in st if p2['points'] == 0) / max(len(st), 1)
        if pts and min(pts) >= 30 and zeros < 0.07:
            out.append(d)
        else:
            print(f"  skipping {os.path.basename(p)}: min {min(pts) if pts else 0:.1f}, "
                  f"{100*zeros:.0f}% of starters on zero")
    return out


def best_lineup(slots, pool):
    """The most points this pool could legally have started.

    Positional seats take the best man of that position; the flex seats then
    take the best men left who are eligible for them. Filling the restrictive
    seats first is safe because a flex seat accepts anything a positional seat
    does, so no swap into a positional seat can free up a better flex pick.
    """
    left = sorted(pool, key=lambda p: -p['points'])
    total, used = 0.0, []
    for s in slots:
        if s in FLEX or s == 'BN':
            continue
        for p in left:
            if p['pos'] == s:
                total += p['points']
                used.append(p)
                left.remove(p)
                break
    for s in slots:
        if s not in FLEX:
            continue
        for p in left:
            if p['pos'] in FLEX[s]:
                total += p['points']
                used.append(p)
                left.remove(p)
                break
    return total, used


def crunch():
    weeks = week_files()
    if not weeks:
        sys.exit('no played weeks found')
    slots = [s for s in weeks[-1]['roster_positions'] if s != 'BN']
    teams = {}
    for d in weeks:
        for g in d['games']:
            for s in g['teams']:
                rid = s['roster_id']
                # Keyed on roster_id throughout. Franchises get renamed
                # mid-season here and a name key drops a renamed side out of
                # the table entirely.
                t = teams.setdefault(rid, {'roster_id': rid, 'name': s['team'].strip(),
                                           'weeks': []})
                t['name'] = s['team'].strip()          # the latest name wins
                pool = [p for p in s['starters'] + s['bench'] if not p.get('reserve')]
                best, _ = best_lineup(slots, pool)
                act = sum(p['points'] for p in s['starters'])
                t['weeks'].append({'week': d['week'], 'actual': round(act, 2),
                                   'best': round(best, 2),
                                   'left': round(best - act, 2),
                                   'eff': (act / best) if best else None})
    for t in teams.values():
        e = [w['eff'] for w in t['weeks'] if w['eff'] is not None]
        t['eff'] = sum(e) / len(e) if e else None
        t['left_per_week'] = sum(w['left'] for w in t['weeks']) / len(t['weeks'])
        t['actual_total'] = round(sum(w['actual'] for w in t['weeks']), 2)
        t['best_total'] = round(sum(w['best'] for w in t['weeks']), 2)
    ranked = sorted(teams.values(), key=lambda t: -(t['eff'] or 0))
    for i, t in enumerate(ranked, 1):
        t['rank'] = i
    return {'note': 'Lineup efficiency: points started against the best legal lineup, '
                    'respecting slot eligibility. scripts/manager_quality.py',
            'weeks': [d['week'] for d in weeks], 'slots': slots,
            'teams': {str(t['roster_id']): t for t in ranked}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    d = crunch()
    print(f"\nlineup efficiency, weeks {min(d['weeks'])}-{max(d['weeks'])}\n")
    print(f"{'#':>3} {'team':<24} {'eff':>7} {'pts left/wk':>12} {'started':>9} {'best':>9}")
    for t in d['teams'].values():
        print(f"{t['rank']:>3} {t['name']:<24} {100*t['eff']:>6.1f}% "
              f"{t['left_per_week']:>12.1f} {t['actual_total']:>9.1f} {t['best_total']:>9.1f}")
    if a.json:
        json.dump(d, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f"\n  wrote {os.path.basename(OUT)}")


if __name__ == '__main__':
    main()
