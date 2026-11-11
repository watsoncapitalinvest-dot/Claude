"""Temporary instrumentation: does the generator actually spawn the camp's extra men?

The campaign run proves the LOOKUP - a camp in the region flips +0/cap4 to +1/cap-1 against real
save state. It proves nothing about the two lines that use the answer. Those are a += inside a
loop and a continue above it, which is exactly the kind of thing that has been read, believed and
wrong twice today.

A New Battle has no alien bases, so the real lookup correctly returns a bonus of zero and the
battle cannot show the effect. OXCE_GAR_FORCE sets the bonus by hand instead, so the same map can
be fought with and without and the unit counts compared. Forcing it is the point: a test where
the number under test is zero is not a test.

usage: gar_probe.py apply|revert <src dir>
"""
import sys, os

MODE, SRC = sys.argv[1], sys.argv[2]
MARK = '// GARPROBE'
TARGET = os.path.join(SRC, 'Battlescape', 'BattlescapeGenerator.cpp')

ANCHOR = """	// A cap that would skip EVERY rank entry is a battle with no enemies in it."""

PROBE = """	if (getenv("OXCE_GAR_FORCE"))                                              // GARPROBE
	{                                                                          // GARPROBE
		garrison.bonus = atoi(getenv("OXCE_GAR_FORCE"));                       // GARPROBE
	}                                                                          // GARPROBE
	if (getenv("OXCE_GAR_CAP") && *getenv("OXCE_GAR_CAP"))                     // GARPROBE
	{                                                                          // GARPROBE
		garrison.rankUnlock = atoi(getenv("OXCE_GAR_CAP"));                    // GARPROBE
	}                                                                          // GARPROBE
	// A New Battle has no Cobra economy to be short of anything, so the real lookup correctly  // GARPROBE
	// reports the region as supplied and the battle cannot show the effect. Forcing it is the  // GARPROBE
	// point: a test where the thing under test is never false is not a test.                   // GARPROBE
	if (getenv("OXCE_GAR_STARVED"))                                            // GARPROBE
	{                                                                          // GARPROBE
		garrison.wellSupplied = false;                                         // GARPROBE
	}                                                                          // GARPROBE
	// The other half of running dry, and a separate knob on purpose: the two shortages are     // GARPROBE
	// meant to be distinguishable on the map, so the test has to be able to produce each one    // GARPROBE
	// without the other. Forced together they would prove only that the garrison got worse.    // GARPROBE
	if (getenv("OXCE_GAR_BROKE") && *getenv("OXCE_GAR_BROKE"))                 // GARPROBE
	{                                                                          // GARPROBE
		garrison.headcountPenalty = atoi(getenv("OXCE_GAR_BROKE"));            // GARPROBE
	}                                                                          // GARPROBE
	// A New Battle sits at month 0, so the calendar ceiling there is always tier 0 and the      // GARPROBE
	// battle cannot show the ceiling MOVING - which is the whole claim. This asks the real      // GARPROBE
	// lookup what it would answer at a given month, so 0, 3 and 8 can be compared against      // GARPROBE
	// the ruleset table. The table is read, not bypassed: a wrong table still fails.           // GARPROBE
	if (getenv("OXCE_GAR_MONTH") && *getenv("OXCE_GAR_MONTH"))                 // GARPROBE
	{                                                                          // GARPROBE
		garrison.maxKitTier = _game->getMod()->getCobraKitTierCap(             // GARPROBE
			(size_t)atoi(getenv("OXCE_GAR_MONTH")));                           // GARPROBE
	}                                                                          // GARPROBE
	if (getenv("OXCE_GAR_LOG"))                                                // GARPROBE
	{                                                                          // GARPROBE
		Log(LOG_INFO) << "[gar] deployment=" << deployment->getType()          // GARPROBE
			<< " bonus=" << garrison.bonus << " cap=" << garrison.rankUnlock   // GARPROBE
			<< " thin=" << garrison.headcountPenalty                           // GARPROBE
			<< " supplied=" << (garrison.wellSupplied ? 1 : 0)                 // GARPROBE
			<< " kitCap=" << garrison.maxKitTier;                              // GARPROBE
	}                                                                          // GARPROBE
""" + ANCHOR

# The spawn line is the wrong place to read the kit from: itemLevel is not declared until
# after it, and a probe that logs a number before it exists does not compile - which is the
# cheap version of the mistake this whole probe exists to catch. Log it where the engine
# actually kits the man: after the clamp to itemSets.size()-1, so the tier printed is the
# tier he is issued from and not a value that is about to be corrected.
# A second anchor, on the headcount arithmetic itself. The total unit count is not evidence here:
# New Battle rolls dQty and extraQty per rank entry, so the baseline ran 10, 15, 7 and 7 units
# across four runs of the same map with nothing forced. Comparing totals across runs cannot show
# a penalty of one per entry. Logging the before and after of the subtraction can, exactly, and
# it is immune to the dice.
QTY_ANCHOR = """		if (garrison.headcountPenalty > 0 && quantity > 0)
"""

QTY_PROBE = """		if (getenv("OXCE_GAR_LOG"))                                                 // GARPROBE
		{                                                                          // GARPROBE
			Log(LOG_INFO) << "[gar] rank=" << dd.alienRank << " qty=" << quantity     // GARPROBE
				<< " minus" << garrison.headcountPenalty;                              // GARPROBE
		}                                                                          // GARPROBE
""" + QTY_ANCHOR

COUNT_ANCHOR = """					for (auto& itemType : dd.itemSets.at(itemLevel).items)
"""

COUNT_PROBE = """					if (getenv("OXCE_GAR_LOG"))                                    // GARPROBE
					{                                                                  // GARPROBE
						Log(LOG_INFO) << "[gar] spawned rank=" << dd.alienRank         // GARPROBE
							<< " kit=" << itemLevel << "/" << (dd.itemSets.size() - 1)   // GARPROBE
							<< " first=" << (dd.itemSets.at(itemLevel).items.empty()     // GARPROBE
								? std::string("none")                                      // GARPROBE
								: dd.itemSets.at(itemLevel).items.front())                 // GARPROBE
							<< " " << alienName;                                         // GARPROBE
					}                                                                  // GARPROBE
""" + COUNT_ANCHOR

src = open(TARGET, encoding='utf-8').read()

if MODE == 'apply':
    if MARK in src:
        print('already applied')
        sys.exit(0)
    for name, anchor in (('force', ANCHOR), ('count', COUNT_ANCHOR), ('qty', QTY_ANCHOR)):
        if src.count(anchor) != 1:
            print('ANCHOR %s appears %d times - do not guess' % (name, src.count(anchor)))
            sys.exit(1)
    src = src.replace(ANCHOR, PROBE, 1)
    src = src.replace(COUNT_ANCHOR, COUNT_PROBE, 1)
    src = src.replace(QTY_ANCHOR, QTY_PROBE, 1)
    open(TARGET, 'w', encoding='utf-8').write(src)
    print('applied')
else:
    out = '\n'.join(l for l in src.split('\n') if MARK not in l)
    open(TARGET, 'w', encoding='utf-8').write(out)
    print('reverted; markers left:', out.count(MARK))
