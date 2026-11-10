"""Read a pen_live run's log and say what penetration actually did.

Separate from the runner because a bash heredoc inside a bash heredoc is how you get a script
that silently runs the wrong half of itself.

The number that matters is the SURVIVED column. Penetration only gets a turn on a tile the shot
failed to destroy; a wall that breaks gives an opening rather than a penetration, which was a
deliberate design choice and is also the reason the feature can look dead in play.

usage: pen_live_report.py <openxcom.log>
"""
import sys, re
from collections import defaultdict

MAT = ['unknown', 'light', 'wood', 'masonry', 'concrete', 'metal']

hits, pens, onward = [], [], []
for ln in open(sys.argv[1], errors='replace'):
    m = re.search(r'\[pen\] TERRAIN mat=(\d+) power=(\d+) stoodUp=(\d)', ln)
    if m:
        hits.append(tuple(int(x) for x in m.groups()))
    m = re.search(r'\[pen\] PEN mat=(\d+) power=(\d+) cost=(\d+) -> (\d+)', ln)
    if m:
        pens.append(tuple(int(x) for x in m.groups()))
    m = re.search(r'\[pen\] ONWARD depth=(\d+) power=(\d+) found=(\d+) traj=(\d+)', ln)
    if m:
        onward.append(tuple(int(x) for x in m.groups()))

print('ranged shots that hit terrain: %d' % len(hits))
if not hits:
    print('  NONE. The battle produced no shots at terrain, so this run says nothing either way.')
    raise SystemExit(0)

stood = defaultdict(lambda: [0, 0])
power_up = defaultdict(list)
for mat, power, up in hits:
    stood[MAT[mat]][up] += 1
    power_up[MAT[mat]].append(power)

print('\n  material    destroyed   survived   survived%   mean power')
for k in MAT:
    d, u = stood[k]
    if d + u:
        print('  %-10s %7d %10d %9.0f%% %11.0f'
              % (k, d, u, 100.0 * u / (d + u), sum(power_up[k]) / len(power_up[k])))
td = sum(v[0] for v in stood.values())
tu = sum(v[1] for v in stood.values())
print('  %-10s %7d %10d %9.0f%%' % ('ALL', td, tu, 100.0 * tu / max(td + tu, 1)))

print('\npenetrate() was reached %d times, and passed power through on %d of them'
      % (len(pens), sum(1 for p in pens if p[3] > 0)))
for mat, power, cost, out in pens[:12]:
    print('    %-9s power %3d  cost %3d  ->  %3d' % (MAT[mat], power, cost, out))

print('\nonward re-traces: %d, of which found something behind the wall: %d'
      % (len(onward), sum(1 for o in onward if o[2] != 0)))
