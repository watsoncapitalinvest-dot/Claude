"""Does the game actually read the ruleset key this feature is tuned by?

The fourth inert feature of the day was found by a campaign log, not by a test. `cobraEconomy:`
was written into the scratchpad's gijoe_tuning.rul, built, shipped and documented - and the game
reads its mod from ~/.local/share/openxcom/mods/GIJoe4x, which never got the block. The lookup
compared the region's materiel against a threshold of zero, so every region on earth reported
itself well supplied and the whole feature was off. It compiled, it ran, and it did nothing.

That is not a thing a diff catches, because the two trees are deliberately NOT mirrors: the
installed copy holds John's own files (gijoe_frontops, gijoe_chuckles, gijoe_intro) that the
scratchpad has never had, and it is sometimes ahead on shared ones. So this does not sync
anything. It asks one question per key: is the key present in the ruleset tree the game loads?

A key the engine reads and no loaded file sets is the signature of the bug. It is reported as a
failure whether or not the scratchpad has it, because the scratchpad is not what runs.

usage: check_loaded.py <engine src dir> <loaded mod dir> [more mod dirs...]
"""
import sys, os, re, glob

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(2)

SRC = sys.argv[1]
MOD_DIRS = sys.argv[2:]

# Each entry: the ruleset block the engine reads, and the file in src that reads it. The pair is
# the point - a key with no reader is dead ruleset, a reader with no key is a dead feature, and
# the two failures read identically from inside the game.
KEYS = [
    ('cobraEconomy', 'Mod/Mod.cpp'),
    ('penetration', 'Mod/Mod.cpp'),
    ('cobraProjects', 'Mod/Mod.cpp'),
]

# Per-rule fields, checked the same way: the engine parses them, so at least one loaded file had
# better set them or the number they default to is the number the game runs on.
# A key added to the engine and not added here passes the audit by being invisible, which is the
# guard failing in exactly the way it exists to prevent. cobraPayoutFunds was added and the audit
# still said "every key the engine reads is set" - because it only ever read this list.
FIELDS = [
    ('cobraPayoutFunds', 'Mod/AlienDeployment.cpp'),
    ('maxKitTierByMonth', 'Mod/Mod.cpp'),
    ('productionMinimumPercent', 'Mod/Mod.cpp'),
    ('materielCostFunds', 'Mod/RuleCobraSite.cpp'),
    ('projectProgressPerMonth', 'Mod/RuleCobraSite.cpp'),
    ('garrisonBonus', 'Mod/RuleCobraSite.cpp'),
    ('garrisonRankUnlock', 'Mod/RuleCobraSite.cpp'),
    ('runsThePlanning', 'Mod/RuleCobraSite.cpp'),
    ('incomeNeedsShipment', 'Mod/RuleCobraSite.cpp'),
]


def loaded_text():
    """Every ruleset byte the game will read, from the dirs the game will read them from."""
    out = []
    for d in MOD_DIRS:
        if not os.path.isdir(d):
            out.append(('%s MISSING' % d, ''))
            continue
        for f in sorted(glob.glob(os.path.join(d, '**', '*.rul'), recursive=True)):
            out.append((f, open(f, encoding='utf-8', errors='ignore').read()))
    return out


def strip_comments(t):
    """A key sitting in a comment is not a key. The doc block above cobraEconomy: explains the
    feature at length and mentions the name repeatedly, so counting raw occurrences would have
    passed on the very file that was missing the setting."""
    return '\n'.join(l for l in t.split('\n') if not l.lstrip().startswith('#'))


files = loaded_text()
if not files:
    print('no ruleset files found in: %s' % ' '.join(MOD_DIRS))
    sys.exit(1)

bad = []
for key, reader in KEYS + FIELDS:
    rp = os.path.join(SRC, reader)
    reads = os.path.isfile(rp) and key in open(rp, encoding='utf-8', errors='ignore').read()
    setters = [os.path.basename(f) for f, t in files
               if re.search(r'^\s*%s\s*:' % re.escape(key), strip_comments(t), re.M)]
    if reads and not setters:
        bad.append((key, 'engine reads it, no loaded ruleset sets it - runs on the default'))
    elif not reads and setters:
        bad.append((key, 'set in %s, no engine code reads it' % ', '.join(setters)))
    else:
        print('  ok   %-22s %s' % (key, ', '.join(setters) if setters else '(unused both sides)'))

print('')
print('%d ruleset files in the tree the game loads: %s' % (len(files), ' '.join(MOD_DIRS)))
if bad:
    for key, why in bad:
        print('  FAIL %-22s %s' % (key, why))
    print('')
    print('The scratchpad copy is not what runs. Copy the changed file into the loaded dir.')
    sys.exit(1)
print('every key the engine reads is set by a file the game loads')
