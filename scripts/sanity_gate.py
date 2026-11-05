#!/usr/bin/env python3
"""Refuse to publish an issue whose numbers are wrong.

    python3 scripts/sanity_gate.py --week 7
    python3 scripts/sanity_gate.py --week 7 --strict    # warnings fail too

At SCFL's scale John is the check: he reads the issue before it goes out and a
wrong figure gets caught by a person. A free product running itself for leagues
nobody here has met has no such person, and the dangerous failure is not the
crash -- a crash is loud and nothing publishes. It is the confident wrong
number.

The measured example, which is why this file exists: waiver_depth reported 27
players who would upgrade a lineup on a 10-team league, where the figure runs
2 to 5 in any league. It did not crash. It did not warn. It wrote a file and
exited zero, and in a retail product that number is now in a magazine eleven
strangers are reading.

So: every check below is something that CANNOT be true of a real week. None of
them is a matter of taste, and none of them fires on an unusual-but-possible
afternoon -- a gate that cries wolf gets switched off.

Exit 0 to publish, 1 to hold.
"""
import argparse, importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')
_w = importlib.util.spec_from_file_location(
    'week_state', os.path.join(ROOT, 'scripts', 'week_state.py'))
week_state = importlib.util.module_from_spec(_w); _w.loader.exec_module(week_state)


def load(path):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p, encoding='utf-8'))
    except (ValueError, OSError):
        return None


class Gate:
    def __init__(self):
        self.fail, self.warn, self.ok = [], [], []

    def check(self, cond, msg, hard=True):
        if cond:
            self.ok.append(msg)
        elif hard:
            self.fail.append(msg)
        else:
            self.warn.append(msg)
        return cond


def run(season, week, strict=False):
    g = Gate()
    wd = load(f'week-data/{season}-w{week}.json')
    if not g.check(wd is not None, f'week file {season}-w{week}.json exists'):
        return g

    games = wd.get('games') or []
    teams = [t for gm in games for t in gm['teams']]

    # ---- the week was actually played -------------------------------------
    # Both tells, because one alone has flipped a conclusion twice. They are
    # derived in week_state.py and nowhere else: this file held its own copy at
    # 7 per cent, four other scripts held theirs, and week 8 -- a finished week
    # at 7.5 -- was held here and silently dropped by the rest.
    #
    # The gate is not alone on this. The replay check below reconciles every
    # rebuilt final against the week file out of play-by-play that carries only
    # finished games: genuinely independent, and the stronger tell. These two
    # are the cheap first pass, and a gate that cries wolf gets switched off.
    ok, why = week_state.played(wd)
    g.check(ok, f'the week has been played -- {why}')
    g.check(not week_state.unusual(wd),
            f'the zero-starter share is inside the ordinary band -- {why}', hard=False)

    # ---- the table is whole ------------------------------------------------
    g.check(len(games) >= 1, f'{len(games)} games')
    g.check(len(teams) == len(games) * 2, 'every game has two sides')
    rids = [t.get('roster_id') for t in teams]
    g.check(len(set(rids)) == len(rids), 'no franchise appears twice in a week')
    g.check(all(r is not None for r in rids), 'every side has a roster_id')
    g.check(all((t.get('team') or '').strip() for t in teams), 'every side has a name')

    # ---- the replay reconciles to the week ---------------------------------
    rp = load(f'week-data/{season}-w{week}-replay.json')
    if rp:
        drift = []
        for gm, rg in zip(games, rp.get('games') or []):
            for t, rt in zip(gm['teams'], rg.get('teams') or []):
                a, b = float(t['points']), float(rt.get('final', rt.get('points', 0)) or 0)
                if abs(a - b) > 0.011:
                    drift.append(f'{t["team"]} {a} vs {b}')
        g.check(not drift, 'every rebuilt final matches the week file'
                + (f' -- off: {"; ".join(drift[:3])}' if drift else ''))

    # ---- waiver depth is in the range any league produces -------------------
    # 2 to 5 a week is what everybody means when they say the wire is bare, and
    # 2026's eight weeks ran 2,3,4,5,5,5,5,6. The band is wrong at BOTH ends:
    #
    #   too high -- a double-digit figure means the replacement bar was computed
    #   from the wrong pool, which is the 27-upgrade bug this gate exists for.
    #   too low  -- zero is not a bare wire, it is an unmeasured one. Week 8
    #   reported 0 upgrades and 0 players beating a replacement starter, against
    #   11-21 every other week, because waiver_depth was reading a cache that
    #   had stopped at week 7. The old floor of 0 waved it straight through.
    wv = load('ir-waiver-depth.json')
    if wv:
        row = next((r for r in wv.get('rows', []) if r.get('week') == week), None)
        # The 27-waiver bug is the reason this whole file exists, and for week 8
        # the check did not run at all: nothing in the weekly chain computed the
        # row, so the gate skipped its own headline check and said nothing. A
        # check that is quietly absent is worse than one that fails.
        g.check(row is not None,
                f'waiver depth has a row for week {week} to check', hard=False)
        if row:
            n = row.get('upgrade_skill')
            g.check(isinstance(n, int) and 1 <= n <= 12,
                    f'waiver upgrades = {n} (2026 ran 2-6; zero means the pool '
                    'was never measured, over 12 means the bar came from the '
                    'wrong pool)')
            # The same tell, further up the funnel and harder to fake: the men
            # who merely beat a replacement starter ran 11-21 all season. A
            # tape missing the week reports both as nothing.
            b = row.get('startable_skill')
            g.check(isinstance(b, int) and b >= 1,
                    f'{b} unowned players beat a replacement starter '
                    '(2026 ran 11-21; zero means the tape has no such week)')
            slots = row.get('slots') or {}
            if slots:
                g.check(abs(sum(slots.values()) - len(teams) * 10) <= len(teams) * 6,
                        f'slot pool {sum(slots.values())} is plausible for {len(teams)} teams')

    # ---- the issue is sendable ---------------------------------------------
    # A page whose card was never built arrives as a grey rectangle in every
    # app it is pasted into, and the sender cannot see that from their end.
    issue = os.path.join(ROOT, f'scfl-week-{week}-issue.html')
    if os.path.exists(issue):
        s = open(issue, encoding='utf-8', errors='replace').read()
        g.check('Traceback' not in s, 'no stack trace in the page')
        g.check('<title>' in s, 'the page has a title')
        g.check('og:description' in s, 'the page has an og:description')
        og = [l for l in s.split('"') if l.endswith(('.jpg', '.png', '.webp'))
              and 'og' in l]
        g.check(bool(og) or 'og:image' in s, 'the page has an og:image')
        g.check(len(s) > 20000, f'the page has content ({len(s)//1024} KB)')
        # undefined/NaN reaching a reader is always a bug, never a style
        for token in ('undefined', 'NaN', 'None-', '[object Object]'):
            g.check(f'>{token}<' not in s, f'no bare {token!r} in the rendered page')

    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', required=True, type=int)
    ap.add_argument('--season', type=int, default=2026)
    ap.add_argument('--strict', action='store_true', help='warnings fail too')
    a = ap.parse_args()

    g = run(a.season, a.week, a.strict)
    for m in g.ok:
        print(f'  ok    {m}')
    for m in g.warn:
        print(f'  warn  {m}')
    for m in g.fail:
        print(f'  FAIL  {m}')
    bad = g.fail + (g.warn if a.strict else [])
    print(f'\n{len(g.ok)} passed, {len(g.warn)} warned, {len(g.fail)} failed')
    if bad:
        print('HOLD -- this issue does not publish.')
        sys.exit(1)
    print('clear to publish.')


if __name__ == '__main__':
    main()
