"""One page out of a fast-forward run (OXCE_FASTFORWARD): what Cobra did in the year, month by month.

usage: python3 build/ff_summary.py <report.txt> <openxcom.log> [label]
The report is GeoscapeState::fastForward's; the log carries the [network] / [will] / [bludd] / [econ] lines.
"""
import re, sys, collections
rep, log = open(sys.argv[1]).read().splitlines(), open(sys.argv[2], errors='ignore').read().splitlines()
label = sys.argv[3] if len(sys.argv) > 3 else ''
head = rep[0] if rep else ''
month = lambda line: int(re.search(r'\(m(-?\d+)\)', line).group(1)) + 1 if re.search(r'\(m(-?\d+)\)', line) else None
events = collections.defaultdict(list)
cur = None
kit = {}
for line in rep:
    if line.startswith('== '):
        cur = month(line)
    elif 'Kit tier from research' in line and cur is not None:
        kit[cur] = int(re.search(r'research (-?\d+)', line).group(1))
    for tag in ('SITE', 'FOUND', 'GONE', 'RAIDED', 'STOPPED'):
        if re.search(r'\)\s+%s\s' % tag, line):
            events[month(line)].append((tag, line.split(tag, 1)[1].strip()))
net = [l.split('] ', 2)[-1] for l in log if '[network]' in l or '[will]' in l or '[bludd]' in l]
crimes = sum(1 for l in net if '-> ' in l and l.startswith('crime'))
strikes = sum(1 for l in net if '-> ' in l and l.startswith('strike'))
away = sum(1 for l in net if 'got away' in l)
stopped = sum(1 for l in net if ' stopped' in l and ' not stopped' not in l)
print('FAST-FORWARD YEAR %s' % label)
print(head)
print('Crimes started %d, cell strikes %d; got away %d, stopped %d' % (crimes, strikes, away, stopped))
for l in net:
    if any(k in l for k in ('broadcast', 'factory', 'Drome', 'Bludd', 'ending B', 'planted', 'grew into')):
        print('  ', l.replace('[network] ', '').replace('[will] ', '').replace('[bludd] ', ''))
print('Month by month (sites Cobra added, found, lost):')
for m in sorted(k for k in events if k is not None):
    c = collections.Counter('%s %s' % (t, re.sub(r'#\d+.*', '', d)) for t, d in events[m])
    print('  month %2d: %s' % (m, ', '.join('%s x%d' % (k, v) if v > 1 else k for k, v in c.items())))
print('Kit tier Cobra has researched, by month:', ' '.join('%d:%d' % (m, kit[m]) for m in sorted(kit)))
