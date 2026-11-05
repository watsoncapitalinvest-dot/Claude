#!/usr/bin/env python3
"""Is this week finished? One answer, in one place.

    python3 scripts/week_state.py            # every week file on disk

A partial week file looks exactly like a real one. Sleeper serves the same
shape on a Thursday night as it does on a Tuesday, so "has the week been
played" has to be derived, and it is derived from two tells because one alone
has flipped an article's conclusion twice:

  - **the weakest score.** Nobody finishes a week under 30. A week nobody has
    played scores near nothing.
  - **starters on exactly zero.** A finished week has a handful: men who were
    inactive, hurt, or on a bye and started anyway. A week half played has a
    pile of them -- a whole broadcast window of starters who have not kicked
    off yet.

WHY THIS FILE EXISTS

The two tells were copied into five scripts, each with its own hardcoded
threshold and its own comment. The threshold was 7 per cent, measured over the
first five weeks of the season. Week 8 came in at 7.5 -- a finished week: 160
starters, eleven of the sixteen sides with exactly one inactive, the flattest
spread of the season, the lowest score 37.58, and every rebuilt final
reconciling against the tape. Four of the five scripts dropped it:

  - `waiver_depth.py` wrote "7 played weeks" and said nothing about the eighth
  - `build_week_issue.py` left week 8 out of the all-time rank a published page
    prints
  - `build_bigweeks.py` marked it not final
  - `manager_quality.py` skipped it (and was the only one that said so)

and the fifth, `sanity_gate.py`, held the issue. One number in five copies,
and a true week read as unplayed in all five. So it lives here now, the range
is measured rather than remembered, and every caller gets the same verdict and
a sentence saying why.

THE MEASURED RANGE

Zero-starter share over the eight finished weeks of 2026, in order:

    1.2  1.2  2.5  3.1  3.8  4.4  5.6  7.5

A Sunday evening with the night games to come reads 10 and up. So the line is
10, and 8 is where a week stops looking ordinary without being wrong.

Nothing here is the last word on its own. `sanity_gate.py` also reconciles
every rebuilt final against the week file out of play-by-play that carries
only finished games, which is genuinely independent and the stronger tell.
These two are the cheap first pass, and their job is to be right about an
ordinary week -- a check that cries wolf gets switched off, and then it catches
nothing at all.
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')

MIN_SCORE = 30.0      # nobody finishes a week under this
ZERO_HARD = 0.10      # at or above: the week is not finished
ZERO_WARN = 0.08      # at or above: unusual, worth a line, not wrong
RANGE = (0.012, 0.075)   # what 2026's eight finished weeks actually ran


def tells(wd):
    """The two tells and their inputs, computed once.

    Returns {'n', 'low', 'zero', 'zeros', 'starters'}. `low` is None on a week
    file with no games at all, which is itself a tell.
    """
    games = (wd or {}).get('games') or []
    sides = [t for g in games for t in (g.get('teams') or [])]
    pts = [t['points'] for t in sides if t.get('points') is not None]
    st = [p for t in sides for p in (t.get('starters') or [])]
    zeros = sum(1 for p in st if p.get('points') == 0)
    return {'n': len(games), 'low': min(pts) if pts else None,
            'zero': zeros / max(len(st), 1), 'zeros': zeros, 'starters': len(st)}


def played(wd):
    """(finished, why). `why` is a sentence either way, for the build output.

    Callers that skip a week are expected to print `why` rather than drop it
    quietly: a week silently missing from a table is the failure this file was
    written after.
    """
    t = tells(wd)
    if not t['n'] or t['low'] is None:
        return False, 'no games in the week file'
    if t['low'] < MIN_SCORE:
        return False, (f'lowest score {t["low"]:.1f} is under {MIN_SCORE:.0f} '
                       '-- the week has not been played')
    if t['zero'] >= ZERO_HARD:
        return False, (f'{t["zeros"]} of {t["starters"]} starters on exactly zero '
                       f'({t["zero"]*100:.1f}%) -- a half-played week reads '
                       f'{ZERO_HARD*100:.0f}+')
    note = ('; unusual but inside what a finished week does'
            if t['zero'] >= ZERO_WARN else '')
    return True, (f'lowest score {t["low"]:.1f}, '
                  f'{t["zeros"]}/{t["starters"]} starters on zero '
                  f'({t["zero"]*100:.1f}%){note}')


def unusual(wd):
    """True when a finished week sits above the ordinary band. Never a hold."""
    return ZERO_WARN <= tells(wd)['zero'] < ZERO_HARD


def weeks(season=None):
    """Every plain week file on disk, in week order, as (week, dict)."""
    out = []
    for p in sorted(glob.glob(os.path.join(WDIR, '*-w*.json'))):
        m = re.match(r'^(\d{4})-w(\d+)\.json$', os.path.basename(p))
        if not m or (season and m.group(1) != str(season)):
            continue
        try:
            out.append((int(m.group(2)), json.load(open(p, encoding='utf-8'))))
        except (ValueError, OSError):
            continue
    return sorted(out)


def main():
    rows = weeks(sys.argv[1] if len(sys.argv) > 1 else None)
    if not rows:
        sys.exit('no week files found')
    for w, wd in rows:
        ok, why = played(wd)
        print(f'  w{w:<3}{"final  " if ok else "OPEN   "}{why}')
    print(f'\n{sum(1 for _, wd in rows if played(wd)[0])} of {len(rows)} finished')


if __name__ == '__main__':
    main()
