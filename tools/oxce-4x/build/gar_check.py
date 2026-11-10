"""Check the garrison arithmetic exactly, rather than comparing unit totals between runs.

A New Battle rolls dQty and extraQty per rank entry, so four runs of the SAME map with nothing
forced came out at 10, 15, 7 and 7 units. A headcount penalty of one man per rank entry is
invisible against that, and "the starved run had fewer units" would have been luck reported as
a result.

So the probe logs each rank entry's quantity BEFORE the subtraction, and the spawn lines say how
many of that rank actually turned up. Given no UFO damage - a New Battle has none - the engine
spawns exactly `quantity` men, so the pass is arithmetic and not a trend:

    spawned(rank) == max(1, quantity_before - penalty)

and for the kit half, every spawned man in a starved run reports kit=0.

usage: gar_check.py <openxcom.log> <expected penalty> <expect starved: 0|1>
"""
import sys, re, collections

if len(sys.argv) < 4:
    print(__doc__)
    sys.exit(2)

LOG, PENALTY, STARVED = sys.argv[1], int(sys.argv[2]), sys.argv[3] == '1'

before = {}          # rank -> quantity as computed before the penalty
seen_penalty = {}    # rank -> the penalty the engine actually applied
spawned = collections.Counter()
kits = collections.Counter()

qty_re = re.compile(r'\[gar\] rank=(\d+) qty=(\d+) minus(\d+)')
spn_re = re.compile(r'\[gar\] spawned rank=(\d+) kit=(\d+)')

for line in open(LOG, encoding='utf-8', errors='ignore'):
    m = qty_re.search(line)
    if m:
        r, q, p = int(m.group(1)), int(m.group(2)), int(m.group(3))
        before[r] = q
        seen_penalty[r] = p
        continue
    m = spn_re.search(line)
    if m:
        spawned[int(m.group(1))] += 1
        kits[int(m.group(2))] += 1

fails = []

# The headcount half. The probe only logs the qty line when a penalty is in force, so with no
# penalty expected there is nothing to check here and an absent line is correct, not a miss.
if PENALTY > 0:
    if not before:
        fails.append('penalty %d expected but the engine never reached the subtraction - '
                     'the lookup did not set headcountPenalty' % PENALTY)
    for r, q in sorted(before.items()):
        want = max(1, q - PENALTY)
        got = spawned.get(r, 0)
        if seen_penalty[r] != PENALTY:
            fails.append('rank %d: engine applied minus%d, expected minus%d'
                         % (r, seen_penalty[r], PENALTY))
        if got != want:
            fails.append('rank %d: %d before, penalty %d, so expected %d on the map, got %d'
                         % (r, q, PENALTY, want, got))
        else:
            print('  ok   rank %d: %d - %d -> %d men, floor respected' % (r, q, PENALTY, want))
elif before:
    fails.append('no penalty expected, but the engine logged one for ranks %s'
                 % sorted(before))

# The kit half.
total = sum(kits.values())
if total == 0:
    fails.append('no men spawned at all - the battle did not generate')
elif STARVED:
    if kits.get(0, 0) != total:
        fails.append('starved run: expected every man on kit 0, got %s' % dict(kits))
    else:
        print('  ok   kit: all %d men on tier 0' % total)
else:
    # A baseline with no spread proves nothing about the clamp, so say so rather than pass.
    if len(kits) == 1 and 0 in kits:
        fails.append('baseline has no kit spread (all %d men already on tier 0) - this run '
                     'cannot show the clamp doing anything; raise alienTech' % total)
    else:
        print('  ok   kit: spread across tiers %s' % dict(kits))

print('')
if fails:
    for f in fails:
        print('  FAIL %s' % f)
    sys.exit(1)
print('arithmetic holds')
