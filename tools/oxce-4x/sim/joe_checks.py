"""G.I. JOE 4x - JOE LAB's Checks: grade a campaign run against the fixes made to the first two months (BUILD-1, 18 Nov
2026; John 14:57 "Can you make an app that runs these tests and combine it into my current testing app").

A run is the folder a campaign simulation writes (timeline.txt, screens.txt, battles.txt, result.txt, log.txt). Each check
reads only those files and answers one of:
  PASS         the run shows the fix working, with the line that proves it
  FAIL         the run shows the bug, with the line that proves it
  NOT REACHED  the run never got to the part this check is about (a short run, or the dice went another way) - not a fault
  LOOK         a number worth a glance, not a pass or fail (timings against STORY's plan)

Used by joe_lab.py (the Checks tab). Also runs on its own:  py -3.13 joe_checks.py <run folder> [<run folder> ...]
"""
import os, re, sys

PASS, FAIL, NOTREACHED, LOOK = 'PASS', 'FAIL', 'NOT REACHED', 'LOOK'


def _read(p):
    try:
        return open(p, encoding='utf-8', errors='replace').read()
    except OSError:
        return ''


class Run:
    def __init__(self, d):
        self.dir = d
        self.timeline = []                     # (day, text)
        for l in _read(os.path.join(d, 'timeline.txt')).splitlines():
            m = re.match(r'day (\d+)\s+\S+\s+(.*)$', l)
            if m: self.timeline.append((int(m.group(1)), m.group(2)))
        self.screens = []                      # (number, day, state, [lines])
        cur = None
        for l in _read(os.path.join(d, 'screens.txt')).splitlines():
            m = re.match(r'== screen_(\d+)\s+day (\d+)\s+(\S+)', l)
            if m:
                st = re.sub(r'^N8OpenXcom\d+|E$', '', m.group(3))
                cur = (int(m.group(1)), int(m.group(2)), st, []); self.screens.append(cur)
            elif cur is not None and l.strip():
                cur[3].append(l.strip())
        self.battles = [l for l in _read(os.path.join(d, 'battles.txt')).splitlines() if l.strip()]
        self.result = _read(os.path.join(d, 'result.txt')).strip()
        self.log = _read(os.path.join(d, 'log.txt'))
        self.last_day = self.timeline[-1][0] if self.timeline else 0
        # a game from 18 Nov 15:00 on logs the broadcast and every cartel take-off; an older one does not
        self.markers = any('(markers 2)' in t for _, t in self.timeline[:3])

    def first(self, pattern):
        """the first timeline line matching a regex: (day, text), or None"""
        r = re.compile(pattern)
        for day, t in self.timeline:
            if r.search(t): return day, t
        return None

    def all(self, pattern):
        r = re.compile(pattern)
        return [(day, t) for day, t in self.timeline if r.search(t)]


def _shot(s):
    return f'screen {s[0]:03d}, day {s[1]}'


# --------------------------------------------------------------------------------------------------------- the checks
# Each: (id, the question in plain words, function(run) -> (verdict, evidence))

def c_finished(r):
    if r.result.startswith('CAMPAIGN END'): return PASS, r.result
    if not r.timeline: return FAIL, 'no timeline at all: the game did not start the campaign'
    if r.result.startswith('STOPPED'): return NOTREACHED, 'stopped by you on day %d' % r.last_day
    return FAIL, 'the game shut down on day %d; last thing it did: %s' % (r.last_day, r.timeline[-1][1])


def c_errors(r):
    if not r.log: return NOTREACHED, 'no log.txt in the run folder'
    bad = [l for l in r.log.splitlines() if '[ERROR]' in l or '[FATAL]' in l]
    if not bad: return PASS, 'no errors in the game log'
    return FAIL, '%d error line(s); first: %s' % (len(bad), bad[0][:160])


def c_stall(r):
    s = r.first(r'^STALL')
    return (FAIL, 'day %d: %s' % s) if s else (PASS, 'something new happened at least every 30 days')


def c_heads(r):
    d0 = [s for s in r.screens if s[1] <= 1]
    if not r.screens: return NOTREACHED, 'no screens.txt (the run kept no screen log)'
    dep = [s for s in d0 if s[2] == 'DepartmentsState']
    app = [s for s in d0 if s[2] == 'AppointHeadState']
    if app: return FAIL, '%d separate "Appoint a head" box(es) on day 0-1, first %s' % (len(app), _shot(app[0]))
    if len(dep) == 1: return PASS, 'one Departments screen with the posts filled (%s)' % _shot(dep[0])
    if not dep: return NOTREACHED, 'no Departments screen on day 0-1 (nothing to appoint?)'
    return FAIL, 'the Departments screen came up %d times on day 0-1' % len(dep)


def c_intel_open(r):
    hit = r.first(r'RESEARCHED STR_CARTEL_(LEDGER|FLIGHT_ROUTE)|RESEARCHED STR_COBRA_STENCIL|RESEARCHED STR_CRATE_SERIAL_PLATE')
    ranch = r.first(r'LANDING at STR_CARTEL_RANCH')
    if not ranch: return NOTREACHED, 'the ranch was never raided'
    if hit and hit[0] <= 20: return PASS, 'day %d: %s' % hit
    if hit: return FAIL, 'the first cartel clue took until day %d: %s' % hit
    if r.last_day < 20: return NOTREACHED, 'run ended on day %d' % r.last_day
    return FAIL, 'no cartel clue researched after the ranch (Intel topics locked?)'


def c_route(r):
    ranch = r.first(r'LANDING at STR_CARTEL_RANCH')
    route = r.first(r'RESEARCHED STR_CARTEL_FLIGHT_ROUTE')
    if route: return PASS, 'day %d: flight route read' % route[0]
    if not ranch: return NOTREACHED, 'the ranch was never raided'
    if r.last_day < 30: return NOTREACHED, 'run ended on day %d' % r.last_day
    return FAIL, 'the flight route was never researched (the ranch dead end?)'


def c_scripted_run(r):
    route = r.first(r'RESEARCHED STR_CARTEL_FLIGHT_ROUTE')
    if not route: return NOTREACHED, 'the flight route was never read'
    fl = [x for x in r.all(r'^CARTEL FLIGHT takes off') if x[0] >= route[0]]
    if not r.markers: return NOTREACHED, 'an older game: it does not log take-offs'
    if not fl:
        if r.last_day < route[0] + 4: return NOTREACHED, 'run ended %d day(s) after the route was read' % (r.last_day - route[0])
        return FAIL, 'route read day %d, no cartel flight by day %d' % (route[0], r.last_day)
    gap = fl[0][0] - route[0]
    early = [x for x in r.all(r'^CARTEL FLIGHT takes off') if x[0] < route[0]]
    if early: return FAIL, 'a cartel flight took off on day %d, before the route was read (random flights should be gone)' % early[0][0]
    if gap <= 3: return PASS, 'route read day %d, first run day %d (%d flight(s) in all)' % (route[0], fl[0][0], len(fl))
    return FAIL, 'route read day %d but the first run waited until day %d' % (route[0], fl[0][0])


def c_no_dogfight(r):
    if not r.first(r'^TAIL '): return NOTREACHED, 'no flight was tailed'
    if not r.screens: return NOTREACHED, 'no screens.txt'
    dog = [s for s in r.screens if s[2] == 'DogfightState']
    return (FAIL, 'a dogfight window opened, %s' % _shot(dog[0])) if dog else (PASS, 'tailed with no dogfight window')


def c_tail_fuel(r):
    tails = r.all(r'^TAIL ')
    if not tails: return NOTREACHED, 'no flight was tailed'
    low = [x for x in r.all(r'^LOW FUEL') if x[0] >= tails[0][0]]
    return (FAIL, 'day %d: %s, after tailing on day %d' % (low[0][0], low[0][1], tails[0][0])) if low else (PASS, 'no low-fuel warning while tailing')


def c_stash(r):
    tails = r.all(r'^TAIL ')
    found = r.first(r'COBRA SITE found: STR_CARTEL_STASH_HOUSE')
    if found and tails and tails[0][0] <= found[0]: return PASS, 'tailed day %d, stash house found day %d' % (tails[0][0], found[0])
    if found: return PASS, 'stash house found day %d (Scarlett or the tail)' % found[0]
    if not tails: return NOTREACHED, 'no flight was tailed'
    return FAIL, 'tailed %d time(s) (first day %d) and the stash house was never found' % (len(tails), tails[0][0])


def c_stash_raid(r):
    found = r.first(r'COBRA SITE found: STR_CARTEL_STASH_HOUSE')
    if not found: return NOTREACHED, 'the stash house was never found'
    raid = [b for b in r.battles if 'STASH' in b]
    if raid: return PASS, raid[0][:120]
    land = r.first(r'LANDING at .*STASH')
    if land: return FAIL, 'landed at the stash house day %d but no battle result' % land[0]
    if r.last_day - found[0] < 3: return NOTREACHED, 'found on day %d, run ended day %d' % (found[0], r.last_day)
    return FAIL, 'found on day %d and never raided' % found[0]


def c_tip(r):
    tip = r.first(r'RESEARCHED STR_INFORMANT_TIP')
    if not tip: return NOTREACHED, "Scarlett's tip never came"
    rob = r.first(r'MISSION appears: STR_ARMORED_CAR')
    if rob and rob[0] < tip[0]: return LOOK, 'the robbery came on day %d, before the tip (day %d)' % (rob[0], tip[0])
    if rob and rob[0] - tip[0] <= 4: return PASS, 'tip day %d, robbery on the map day %d' % (tip[0], rob[0])
    if rob: return FAIL, 'tip day %d but the robbery waited until day %d' % (tip[0], rob[0])
    if r.last_day - tip[0] <= 4: return NOTREACHED, 'run ended %d day(s) after the tip' % (r.last_day - tip[0])
    return FAIL, 'tip day %d and no robbery by day %d' % (tip[0], r.last_day)


def c_no_cobra_early(r):
    b = r.first(r'^BROADCAST')
    cobra = r.first(r'(MISSION appears|COBRA SITE found): STR_COBRA_')
    if not r.markers: return NOTREACHED, 'an older game: it does not log the broadcast'
    if not b:
        if cobra: return FAIL, 'no broadcast, yet day %d: %s' % cobra
        return PASS, 'no broadcast and no Cobra by day %d' % r.last_day
    if cobra and cobra[0] < b[0]: return FAIL, 'broadcast day %d, but day %d: %s' % (b[0], cobra[0], cobra[1])
    return PASS, 'broadcast day %d; first Cobra job %s' % (b[0], ('day %d' % cobra[0]) if cobra else 'not yet')


def c_debrief_title(r):
    deb = [s for s in r.screens if s[2] == 'DebriefingState']
    if not deb: return NOTREACHED, 'no debrief screens'
    bad = [s for s in deb if any('Terror Drome' in l for l in s[3])]
    return (FAIL, '"Terror Drome" on a debrief, %s' % _shot(bad[0])) if bad else (PASS, '%d debrief(s), none says Terror Drome' % len(deb))


def c_cartel_words(r):
    deb = [s for s in r.screens if s[2] == 'DebriefingState' and any('CARTEL' in l.upper() for l in s[3])]
    if not deb: return NOTREACHED, 'no cartel debrief seen'
    bad = [s for s in deb if any('Cobra men' in l or 'COBRA KILLED' in l.upper() for l in s[3])]
    return (FAIL, 'a cartel debrief says Cobra, %s' % _shot(bad[0])) if bad else (PASS, '%d cartel debrief(s), no "Cobra men"' % len(deb))


def c_intel_dupes(r):
    boards = [s for s in r.screens if s[2] == 'IntelBoardState']
    if not boards: return NOTREACHED, 'the Intel board never came up'
    for s in boards:
        body = [l for l in s[3] if not l.startswith('[') and l not in ('INTEL BOARD',)]
        seen = set()
        for l in body:
            if l in seen: return FAIL, 'the same line twice, %s: %s' % (_shot(s), l[:100])
            seen.add(l)
    return PASS, '%d Intel board screen(s), no line repeated' % len(boards)


def c_words(r):
    if not r.screens: return NOTREACHED, 'no screens.txt'
    for s in r.screens:
        for l in s[3]:
            for w in ('Small Rocket', 'Eddie Murphy', 'Murphy', 'Alien', 'UFO', 'X-COM', 'XCOM'):
                if re.search(r'\b%s\b' % re.escape(w), l): return FAIL, '"%s", %s: %s' % (w, _shot(s), l[:100])
    return PASS, 'no X-COM leftovers ("Small Rocket", "Murphy", "Alien", "UFO", "X-COM") in %d screens' % len(r.screens)


def c_fuel_shown(r):
    if not r.screens: return NOTREACHED, 'no screens.txt'
    for s in r.screens:
        for l in s[3]:
            m = re.match(r'FUEL: (\d+)%', l)
            if m and int(m.group(1)) > 100: return FAIL, '%s: %s' % (_shot(s), l)
    return PASS, 'every fuel gauge 100% or under'


def c_factory(r):
    lead = r.first(r'RESEARCHED STR_FACTORY_LEAD_SOLVED')
    if not lead: return LOOK, 'the factory lead never came (the factory reopens on its own about day 55)'
    return LOOK if lead[0] > 55 else PASS, 'factory lead day %d (target: before day 55)' % lead[0]


CHECKS = [
    ('finished',   'The campaign ran to the end without the game shutting down', c_finished),
    ('errors',     'No errors in the game log', c_errors),
    ('stall',      'Never 30 days with nothing new', c_stall),
    ('heads',      'Day 1: one Departments screen, not four Appoint-Head boxes', c_heads),
    ('intel',      'Intel topics open after the ranch (a cartel clue by day 20)', c_intel_open),
    ('route',      'The flight route gets researched (no ranch dead end)', c_route),
    ('script',     'The cartel flight comes 2 days after the route is read', c_scripted_run),
    ('dogfight',   'Tailing the cartel plane never opens a dogfight', c_no_dogfight),
    ('fuel',       'The A.P.C. does not run low on fuel tailing it', c_tail_fuel),
    ('stash',      'Tailing the plane finds the stash house', c_stash),
    ('stashraid',  'The stash house gets raided', c_stash_raid),
    ('tip',        "Scarlett's tip brings the robbery within days", c_tip),
    ('broadcast',  'No Cobra jobs or Cobra sites before the broadcast', c_no_cobra_early),
    ('dromes',     'Debriefs never say "Terror Drome" for a Cobra site', c_debrief_title),
    ('cartel',     'Cartel debriefs say cartel, not Cobra', c_cartel_words),
    ('board',      'The Intel board never repeats a line', c_intel_dupes),
    ('words',      'No X-COM leftovers on screen', c_words),
    ('fuelpct',    'No fuel gauge over 100%', c_fuel_shown),
    ('factory',    'The factory lead comes before the factory reopens (day 55)', c_factory),
]

# What a campaign run cannot see: these stay on the list for John's eyes.
BY_EYE = [
    'Popups open at once (no bare picture over the map)',
    'Fast battles: the warning plate shows, and battles feel quicker',
    'Tanks: drive the V.A.M.P. through sandbags on the Test Range',
    'The Windows 64-bit game starts minimised from Play_4x.bat',
]


def grade(d):
    r = Run(d)
    out = []
    for cid, q, fn in CHECKS:
        try: v, ev = fn(r)
        except Exception as e: v, ev = FAIL, 'the check itself broke: %r' % e
        out.append((cid, q, v, ev))
    return out


def report(dirs):
    lines = []
    for d in dirs:
        lines.append('== ' + d)
        for cid, q, v, ev in grade(d):
            lines.append(f'  {v:12} {q}\n               {ev}')
    return '\n'.join(lines)


if __name__ == '__main__':
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    rep = report(sys.argv[1:])
    print(rep)
    sys.exit(1 if '  FAIL ' in rep else 0)
