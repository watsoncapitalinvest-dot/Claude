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
import argparse, csv, gzip, io, json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TX = os.path.join(ROOT, 'transactions.json')
IRW = os.path.join(ROOT, 'ir-watch.json')
OUT = os.path.join(ROOT, 'ir-drops.json')
CACHE = os.path.join(ROOT, '.cache')
NFLV = 'https://github.com/nflverse/nflverse-data/releases/download'

# What counts as hurt in the NFL's own records, matched as closely as the two
# feeds allow to the Sleeper designations the rest of this study uses.
# Questionable is excluded here exactly as it is there.
RES_STATUS = {'RES', 'EXE'}             # reserve/injured, PUP, NFI, suspended
REPORT_OUT = {'Out', 'Doubtful'}        # week-to-week, for men still on the active roster


def grab(path, name):
    """nflverse file, cached in the gitignored .cache. Returns rows or None."""
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, name)
    if not os.path.exists(p) or os.path.getsize(p) < 1024:
        try:
            with urllib.request.urlopen(f'{NFLV}/{path}', timeout=180) as r:
                raw = r.read()
            if name.endswith('.gz'):
                raw = gzip.decompress(raw)
            open(p, 'wb').write(raw)
        except Exception as e:
            print(f'  could not fetch {path}: {e}')
            return None
    return list(csv.DictReader(io.StringIO(open(p, encoding='utf-8').read())))


def norm(s):
    return ''.join(c for c in (s or '').lower() if c.isalnum())


def nfl_index(season):
    """Who the NFL had unavailable, and how to find a Sleeper player in it.

    IDENTITY. Sleeper's own gsis_id field is blank for most players -- it is
    missing even for Bijan Robinson -- so it cannot carry the join on its own,
    and nflverse publishes no sleeper_id to meet it with. What the weekly
    roster feed does carry is full name, NFL team, position, week AND gsis_id
    together, which is a far tighter key than a name alone: the week and the
    team do most of the work, and the full names here are real names rather
    than the pbp abbreviations that once aged a father in place of his son.
    Anything still ambiguous after name, team and position is counted and
    dropped rather than guessed.
    """
    rost = grab(f'weekly_rosters/roster_weekly_{season}.csv',
                f'roster_weekly_{season}.csv')
    inj = grab(f'injuries/injuries_{season}.csv', f'injuries_{season}.csv')
    if not rost and not inj:
        return None
    hurt, idx = {}, {}
    for r in (rost or []):
        g, w = r.get('gsis_id'), r.get('week')
        if not g or not w:
            continue
        w = int(w)
        idx.setdefault((w, norm(r.get('full_name'))), []).append(
            {'gsis': g, 'team': (r.get('team') or '').upper(),
             'pos': (r.get('position') or '').upper()})
        if r.get('status') in RES_STATUS:
            hurt[(g, w)] = f"NFL {r['status']}"
    for r in (inj or []):
        g, w = r.get('gsis_id'), r.get('week')
        if g and w and r.get('report_status') in REPORT_OUT:
            hurt.setdefault((g, int(w)), r['report_status'])
    return {'hurt': hurt, 'idx': idx, 'weeks': sorted({w for _, w in hurt})}


def resolve(ix, name, team, pos, week):
    """A Sleeper player -> his gsis_id in a given week, or None if unsure."""
    c = ix['idx'].get((week, norm(name))) or []
    if len(c) > 1 and team:
        c = [x for x in c if x['team'] == (team or '').upper()] or c
    if len(c) > 1 and pos:
        c = [x for x in c if x['pos'] == (pos or '').upper()] or c
    return c[0]['gsis'] if len(c) == 1 else None


def iso_ms(s):
    """ir-watch stamps are ISO Z; transactions are epoch ms. One scale."""
    import calendar, time as _t
    return calendar.timegm(_t.strptime(s, '%Y-%m-%dT%H:%M:%SZ')) * 1000


def crunch(use_nfl=True):
    if not os.path.exists(TX):
        sys.exit('no transactions.json -- run the fetch-transactions workflow first')
    tx = json.load(open(TX, encoding='utf-8'))
    irw = json.load(open(IRW, encoding='utf-8'))['rows']
    snaps = sorted(({'at': iso_ms(r['stamp']), 'week': r['week'],
                     'teams': {t['roster_id']: t for t in r['teams']}} for r in irw),
                   key=lambda s: s['at'])
    ix = nfl_index(tx['season']) if use_nfl else None
    unsure = 0

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
                   'player': d['name'], 'pos': d['pos'], 'gsis': d.get('gsis', ''),
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
            # The snapshot is weekly, so a man signed on Thursday, hurt on
            # Sunday and dropped on Tuesday was never in one. The NFL's own
            # records close that gap -- and only that gap: a drop the snapshot
            # already caught is left exactly as the snapshot scored it, so the
            # two methods can never disagree about the same drop.
            rec['nfl'] = ''
            if ix and not rec['was_stranded'] and rec['week'] in ix['weeks']:
                w = rec['week']
                g = rec['gsis'] or resolve(ix, d['name'], d.get('nfl'), d['pos'], w)
                if g:
                    rec['gsis'] = g
                    # The week of the drop. A looser test that also accepted
                    # the week before would catch a man ruled out on Sunday and
                    # cut on Tuesday, and would also catch one who had already
                    # returned -- so it is reported separately rather than
                    # folded into the count.
                    rec['nfl'] = ix['hurt'].get((g, w)) or ''
                    rec['nfl_prev'] = ix['hurt'].get((g, w - 1)) or ''
                    # SEVERITY matters, and the two feeds are not equivalent.
                    # NFL RES is reserve/injured or PUP -- weeks out, the kind
                    # of man an IR slot exists for. A bare 'Out' is one game,
                    # and a Wednesday snapshot cannot see it because it is
                    # usually declared on the Friday. Including short-term
                    # Outs is faithful to this paper's stated definition of
                    # injured, which does count them; but burning a slot on a
                    # man back the following week would be poor management, so
                    # the severe subset is carried separately rather than
                    # merged away.
                    rec['severe'] = rec['nfl'].startswith('NFL ')
                else:
                    unsure += 1
            if rec['was_stranded'] and rec['ir_full']:
                boxes['cap_cost'].append(rec)
            elif rec['was_stranded']:
                boxes['own_choice'].append(rec)
            elif rec['nfl'] and rec['ir_full']:
                rec['found_by'] = 'nflverse'
                boxes['cap_cost'].append(rec)
            elif rec['nfl']:
                rec['found_by'] = 'nflverse'
                boxes['own_choice'].append(rec)
            else:
                boxes['churn'].append(rec)
    boxes['unresolved'] = unsure
    return tx, boxes, n_drops


def enrich(tx, boxes):
    """Questions the classification does not answer, added once, here.

    How long the man had been held -- a flyer signed and cut inside a
    fortnight was never an asset anybody was holding on to -- and whether any
    OTHER side wanted him afterwards, which is the only available measure of
    what the loss was actually worth.
    """
    rows = tx['rows']
    for key in ('cap_cost', 'own_choice'):
        for d in boxes[key]:
            held = [r['week'] for r in rows if r['status'] == 'complete'
                    and r['week'] <= d['week']
                    for a in r['adds'] if a['name'] == d['player']
                    and a['roster_id'] == d['roster_id']]
            last_add = max(held) if held else None
            d['held_from'] = last_add
            d['weeks_held'] = (d['week'] - last_add) if held else None
            d['claimed_since'] = sorted({
                (tx['rosters'].get(str(a['roster_id'])) or '').strip()
                for r in rows if r['status'] == 'complete' and r['week'] >= d['week']
                for a in r['adds'] if a['name'] == d['player']
                and a['roster_id'] != d['roster_id']})
            d['found_by'] = d.get('found_by', 'snapshot')
    return boxes


def exposure(irw_rows):
    """Stranded man-weeks with the injured reserve full, and with a slot free.

    The denominator: a drop can only be forced where there was a man to shelve
    AND nowhere to put him, so both populations have to be sized before a
    handful of drops means anything.
    """
    full = sum(t['stranded'] for r in irw_rows for t in r['teams'] if t['ir_full'])
    free = sum(t['stranded'] for r in irw_rows for t in r['teams'] if not t['ir_full'])
    return full, free


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    tx, b, n = crunch()
    b = enrich(tx, b)
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
        irw = json.load(open(IRW, encoding='utf-8'))['rows']
        full, free = exposure(irw)
        done = sum(1 for r in tx['rows'] if r['status'] == 'complete')
        vol = []
        for w in sorted({r['week'] for r in tx['rows']}):
            gw = [r for r in tx['rows'] if r['week'] == w]
            mv = [r for r in gw if r['status'] == 'complete'
                  and r['type'] in ('free_agent', 'waiver')]
            vol.append({'week': w, 'moves': len(mv),
                        'adds': sum(len(r['adds']) for r in mv),
                        'drops': sum(len(r['drops']) for r in mv),
                        'movers': len({p['roster_id'] for r in mv
                                       for p in r['adds'] + r['drops']}),
                        'failed': sum(1 for r in gw if r['status'] == 'failed')})
        json.dump({'note': 'Drops joined to the IR snapshot taken before them, then to the '
                           "NFL's own weekly roster and injury records. scripts/ir_drops.py",
                   'league': tx['league'], 'season': tx['season'],
                   'drops_total': n, 'drops_judged': obs,
                   'rows_total': len(tx['rows']), 'rows_done': done,
                   'exposure_full': full, 'exposure_free': free,
                   'counts': {k: (len(v) if isinstance(v, list) else v)
                              for k, v in b.items()},
                   'forced': b['cap_cost'], 'own_choice': b['own_choice'],
                   'vol': vol},
                  open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'\n  wrote {os.path.basename(OUT)}')


if __name__ == '__main__':
    main()
