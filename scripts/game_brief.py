#!/usr/bin/env python3
"""Everything a writer needs about one week, in one place.

    python3 scripts/game_brief.py --week 4

The replay knows the chronology, the standings know the season, and the week
data knows the lineups. A writer needs all three at once and needs them dense,
so this prints the brief: what happened, in what order, what it did to both
teams' seasons, who did it, and what each manager left on the bench.

This is the hand-off point. Everything upstream is derived and checkable;
everything downstream is writing. A model -- or a person -- writes from this,
rather than from a template that can only ever rearrange the same clauses.
"""
import argparse, importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')
_t = importlib.util.spec_from_file_location('sd', os.path.join(ROOT, 'scripts', 'standings.py'))
sd = importlib.util.module_from_spec(_t); sys.modules['sd'] = sd; _t.loader.exec_module(sd)
TEAM = lambda s: (s or '').strip().strip('*').strip()
SLOT_OK = {'QB': {'QB'}, 'RB': {'RB'}, 'WR': {'WR'}, 'TE': {'TE'}, 'K': {'K'},
           'DEF': {'DEF'}, 'FLEX': {'RB', 'WR', 'TE'}, 'WRRB_FLEX': {'RB', 'WR'},
           'REC_FLEX': {'WR', 'TE'}, 'SUPER_FLEX': {'QB', 'RB', 'WR', 'TE'}}


def regret(team, slots):
    lineup = list(zip(slots, team['starters']))
    best = None
    for b in team['bench']:
        bp = (b.get('pos') or '').upper()
        if not bp or (b.get('points') or 0) <= 0:
            continue
        for slot, st in lineup:
            if bp not in SLOT_OK.get(slot, {slot}):
                continue
            gain = (b.get('points') or 0) - (st.get('points') or 0)
            if gain > 0 and (best is None or gain > best[2]):
                best = (b, st, gain)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, required=True)
    ap.add_argument('--season', default='2026')
    ap.add_argument('--game', type=int, default=-1)
    a = ap.parse_args()
    rp = json.load(open(os.path.join(WDIR, f'{a.season}-w{a.week}-replay.json'), encoding='utf-8'))
    wd = json.load(open(os.path.join(WDIR, f'{a.season}-w{a.week}.json'), encoding='utf-8'))
    st = sd.build(a.season, a.week)
    W = {w['code']: w['label'] for w in rp['windows']}
    slots = [x for x in (wd.get('roster_positions') or []) if x != 'BN']

    for gi, (g, gw) in enumerate(zip(rp['games'], wd['games'])):
        if a.game >= 0 and gi != a.game:
            continue
        A, B = g['teams']
        an, bn = TEAM(A['team']), TEAM(B['team'])
        print('=' * 78)
        print(f'[{gi}] {an} {A["final"]}  vs  {bn} {B["final"]}   margin {g["margin"]}  '
              f'lead changes {g["lead_changes"]}')
        for nm in (an, bn):
            r = (st or {}).get('by_team', {}).get(nm)
            if r:
                print(f'   {nm:<22} {r["prev_record"]} -> {r["record"]}  {r["streak"]}  '
                      f'PF {r["pf"]:.0f} PA {r["pa"]:.0f}  seed {r["seed"]}  '
                      f'{r.get("div_name","")} #{r.get("div_rank","-")}')
                print(f'   {"":<22} season: ' +
                      ', '.join(f'w{w}{res}({pf:.0f}-{pa:.0f} v {TEAM(opp)})'
                                for w, res, pf, pa, opp in r['trail']))
        tl = [e for e in g['timeline'] if not e['residual']]
        print('   -- swings and scores --')
        for e in tl:
            if not (e['td'] or e.get('go_ahead') or e['pts'] >= 4 or e['kind'] in ('int', 'fum')):
                continue
            tag = '  <<GO AHEAD' if e.get('go_ahead') else ''
            side = an if e['side'] == 0 else bn
            print(f"     Q{e['fc']['qtr']} {e['fc']['clock']} {W.get(e['window'],''):<22}"
                  f"{e['player'][:19]:<20}{(e['text'] or e['kind'])[:28]:<29}"
                  f"{e['pts']:+6.2f}  {e['score'][0]:6.2f}-{e['score'][1]:<6.2f}{tag}")
        for si, t in enumerate(gw['teams']):
            tot = {}
            for e in tl:
                if e['side'] == si:
                    tot[e['player']] = tot.get(e['player'], 0) + e['pts']
            print(f'   {TEAM(t["team"]):<22} ' +
                  ', '.join(f'{n} {v:.1f}' for n, v in
                            sorted(tot.items(), key=lambda x: -x[1])[:5]))
            r = regret(t, slots)
            if r:
                print(f'   {"":<22} bench: {r[0]["name"]} {r[0]["points"]:.1f} '
                      f'for {r[1]["name"]} {r[1]["points"]:.1f} (+{r[2]:.1f})')
            lo = [p for p in t['starters'] if p['pos'] not in ('K', 'DEF')
                  and (p.get('points') or 0) <= 3]
            if lo:
                print(f'   {"":<22} flat: ' +
                      ', '.join(f'{p["name"]} {p["points"]:.1f}' for p in lo))


if __name__ == '__main__':
    main()
