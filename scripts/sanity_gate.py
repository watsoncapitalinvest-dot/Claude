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
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')


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
    # Both tells, because one alone has flipped a conclusion twice: a week
    # nobody has played scores near zero, and a week half played shows a pile
    # of starters on exactly 0. A finished week runs 1-6 per cent.
    pts = [t['points'] for t in teams]
    starters = [p for t in teams for p in t.get('starters', [])]
    zero = sum(1 for p in starters if p.get('points') == 0) / max(len(starters), 1)
    g.check(bool(pts) and min(pts) >= 30, f'every side scored 30+ (low {min(pts):.1f})'
            if pts else 'no scores at all')
    g.check(zero < 0.07, f'starters on exactly zero: {zero*100:.1f}% (a played week runs 1-6)')

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
    # 2 to 5 a week is what everybody means when they say the wire is bare.
    # A double-digit figure means the replacement bar was computed from the
    # wrong pool, which is exactly the bug this gate was written for.
    wv = load('ir-waiver-depth.json')
    if wv:
        row = next((r for r in wv.get('rows', []) if r.get('week') == week), None)
        if row:
            n = row.get('upgrade_skill')
            g.check(isinstance(n, int) and 0 <= n <= 12,
                    f'waiver upgrades = {n} (a real week runs 2-5; over 12 means '
                    'the bar came from the wrong pool)')
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
