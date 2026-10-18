#!/usr/bin/env python3
"""Did the IR cap ever actually cost anyone a player?

    python3 scripts/ir_drops.py            # the join, printed
    python3 scripts/ir_drops.py --json     # and written to ir-drops.json

THE QUESTION

Everything the IR study measures is friction: a roster slot doing nothing.
Friction is a ceiling on inconvenience, not a measure of loss. The one thing
that would turn it into a real cost is a side at the cap DROPPING an injured
man it would otherwise have shelved -- so the study names the transaction log
as the strongest evidence nobody has.

This is that join.

HOW IT IS DONE, AND WHY NOT THE OBVIOUS WAY

The obvious way is to look up each dropped player's injury status. That gives a
confident wrong answer: Sleeper's player table carries TODAY'S status, so a man
dropped hurt in September who has since healed reads healthy now, and one
dropped healthy who got hurt later reads injured.

ir-watch.json is the point-in-time record instead. Every Wednesday it writes,
per roster, the names of the injured men sitting on that roster's ACTIVE list
and whether its injured reserve was full. So a drop is joined to the snapshot
TAKEN BEFORE IT -- by timestamp, not by week label, because waivers clear
within hours of the snapshot and a week label cannot order those two.

A drop then falls into one of four boxes, and only one of them is evidence:

    dropped man was stranded + IR was full   <- the cap cost this team a player
    dropped man was stranded + IR had room   <- their own choice, not the cap
    dropped man was healthy   + IR was full   } ordinary roster churn
    dropped man was healthy   + IR had room   }

WHAT IT CANNOT SEE

A snapshot is weekly. A man signed on Thursday, hurt on Sunday and dropped on
Tuesday was never in one, so he cannot be counted either way -- those drops are
reported separately as unobserved rather than silently scored as healthy.
Rosters are keyed by roster_id throughout; franchises get renamed mid-season
and a name key drops a renamed team out of the join entirely.
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TX = os.path.join(ROOT, 'transactions.json')
IRW = os.path.join(ROOT, 'ir-watch.json')
OUT = os.path.join(ROOT, 'ir-drops.json')


def iso_ms(s):
    """ir-watch stamps are ISO Z; transactions are epoch ms. One scale."""
    import calendar, time as _t
    return calendar.timegm(_t.strptime(s, '%Y-%m-%dT%H:%M:%SZ')) * 1000


def crunch():
    if not os.path.exists(TX):
        sys.exit('no transactions.json -- run the fetch-transactions workflow first')
    tx = json.load(open(TX, encoding='utf-8'))
    irw = json.load(open(IRW, encoding='utf-8'))['rows']
    snaps = sorted(({'at': iso_ms(r['stamp']), 'week': r['week'],
                     'teams': {t['roster_id']: t for t in r['teams']}} for r in irw),
                   key=lambda s: s['at'])

    def before(t):
        """The last snapshot taken strictly before this transaction."""
        prev = None
        for s in snaps:
            if s['at'] < t:
                prev = s
            else:
                break
        return prev

    boxes = {'cap_cost': [], 'own_choice': [], 'churn': [], 'unobserved': []}
    n_drops = 0
    for r in tx['rows']:
        if r['status'] != 'complete':
            continue
        when = r['created']
        snap = before(when) if when else None
        for d in r['drops']:
            n_drops += 1
            rid = d['roster_id']
            team = (snap or {}).get('teams', {}).get(rid) if snap else None
            rec = {'week': r['week'], 'type': r['type'], 'roster_id': rid,
                   'team': tx['rosters'].get(str(rid), f'roster {rid}'),
                   'player': d['name'], 'pos': d['pos'],
                   'snapshot_week': snap['week'] if snap else None,
                   'added_back': [a['name'] for a in r['adds']
                                  if a['roster_id'] == rid]}
            if not team:
                boxes['unobserved'].append(rec)
                continue
            rec['ir_used'] = team['ir_used']
            rec['ir_full'] = bool(team['ir_full'])
            stranded = team.get('stranded_names') or []
            rec['was_stranded'] = d['name'] in stranded
            rec['stranded_then'] = stranded
            if rec['was_stranded'] and rec['ir_full']:
                boxes['cap_cost'].append(rec)
            elif rec['was_stranded']:
                boxes['own_choice'].append(rec)
            else:
                boxes['churn'].append(rec)
    return tx, boxes, n_drops


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    tx, b, n = crunch()
    obs = n - len(b['unobserved'])
    print(f"\n{tx['league']} {tx['season']} — {len(tx['rows'])} transactions, {n} drops")
    print(f"  {obs} drops fall after a snapshot and can be judged; "
          f"{len(b['unobserved'])} cannot.\n")
    print(f"  the cap cost them a player   {len(b['cap_cost']):>4}   "
          f"(dropped a stranded man WITH IR full)")
    print(f"  their own choice             {len(b['own_choice']):>4}   "
          f"(dropped a stranded man with a slot free)")
    print(f"  ordinary churn               {len(b['churn']):>4}   "
          f"(dropped man was not stranded)")
    print(f"  unobserved                   {len(b['unobserved']):>4}   "
          f"(no snapshot held him)")
    for k, label in (('cap_cost', 'DROPPED A STRANDED MAN WITH IR FULL'),
                     ('own_choice', 'dropped a stranded man with a slot free')):
        if b[k]:
            print(f'\n  {label}')
            for r in sorted(b[k], key=lambda r: (r['week'], r['team'])):
                back = f" -> added {', '.join(r['added_back'])}" if r['added_back'] else ''
                print(f"    wk{r['week']:<2} {r['team']:<22} {r['player']} "
                      f"({r['pos']}, {r['type']}){back}")
    if a.json:
        json.dump({'note': 'Drops joined to the IR snapshot taken before them. '
                           'scripts/ir_drops.py',
                   'league': tx['league'], 'season': tx['season'],
                   'drops_total': n, 'drops_judged': obs,
                   'counts': {k: len(v) for k, v in b.items()},
                   'boxes': b},
                  open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'\n  wrote {os.path.basename(OUT)}')


if __name__ == '__main__':
    main()
