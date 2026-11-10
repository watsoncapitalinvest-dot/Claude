"""Does the shipment contain everything the rulesets in it name?

A ruleset that names a file the mod does not have is not a warning. OXCE logs FATAL and the game
does not reach the main menu, so the whole evening is gone before the first battle. That happened
with the one file nobody thought of as having assets: gijoe_items_new.rul had been sitting in the
repo for a day naming 22 painted PNGs that had never been copied anywhere, and it went out inside
a zip labelled as a mod update.

The shape of the mistake is worth naming, because it is not carelessness. The rulesets were
verified. The art was verified. What was never verified is that the two were in the same place,
and that is exactly the kind of gap that only shows up at the moment of use.

So this runs over the shipment as assembled, not over the working tree: a file that exists in the
scratchpad and not in the zip is the failure being looked for, and checking the scratchpad would
report success.

Set names like BIGOBS.PCK are references to vanilla sets rather than files to carry, so only
paths under Resources/ are required to be present - those are the mod's own.

usage: check_shipment.py <shipment dir> [<fallback dir>...]
       exits non-zero and names what is missing
"""
import sys, os, re, glob

SHIP = sys.argv[1]
FALLBACK = sys.argv[2:]          # places the user is known to already have, e.g. their mod folder

OWNED = re.compile(r'(Resources|MAPS|ROUTES|TERRAIN|UFOPAEDIA)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+')

missing, checked = [], 0
for rul in sorted(glob.glob(os.path.join(SHIP, '**', '*.rul'), recursive=True)):
    text = open(rul, encoding='utf-8', errors='replace').read()
    refs = sorted(set(m.group(0) for m in OWNED.finditer(text)))
    gone = []
    for ref in refs:
        checked += 1
        if os.path.exists(os.path.join(SHIP, ref)):
            continue
        if any(os.path.exists(os.path.join(f, ref)) for f in FALLBACK):
            continue
        gone.append(ref)
    print('   %-30s %3d referenced, %d not in the shipment'
          % (os.path.basename(rul), len(refs), len(gone)))
    for g in gone:
        missing.append((os.path.basename(rul), g))

print('\n   %d references checked across the shipment' % checked)
if missing:
    print('\n   THE GAME WILL NOT START. OXCE treats a missing resource as FATAL, so each of')
    print('   these stops the build at the loading screen:')
    for rul, ref in missing:
        print('      %s  ->  %s' % (rul, ref))
    sys.exit(1)
print('   every file the rulesets name is present')
