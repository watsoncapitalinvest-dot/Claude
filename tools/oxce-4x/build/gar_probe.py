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
	if (getenv("OXCE_GAR_CAP"))                                                // GARPROBE
	{                                                                          // GARPROBE
		garrison.rankUnlock = atoi(getenv("OXCE_GAR_CAP"));                    // GARPROBE
	}                                                                          // GARPROBE
	if (getenv("OXCE_GAR_LOG"))                                                // GARPROBE
	{                                                                          // GARPROBE
		Log(LOG_INFO) << "[gar] deployment=" << deployment->getType()          // GARPROBE
			<< " bonus=" << garrison.bonus << " cap=" << garrison.rankUnlock;  // GARPROBE
	}                                                                          // GARPROBE
""" + ANCHOR

COUNT_ANCHOR = """			BattleUnit *unit = addAlien(rule, dd.alienRank, outside);
"""

COUNT_PROBE = """			BattleUnit *unit = addAlien(rule, dd.alienRank, outside);
			if (getenv("OXCE_GAR_LOG"))                                        // GARPROBE
			{                                                                  // GARPROBE
				Log(LOG_INFO) << "[gar] spawned rank=" << dd.alienRank         // GARPROBE
					<< " " << alienName;                                       // GARPROBE
			}                                                                  // GARPROBE
"""

src = open(TARGET, encoding='utf-8').read()

if MODE == 'apply':
    if MARK in src:
        print('already applied')
        sys.exit(0)
    for name, anchor in (('force', ANCHOR), ('count', COUNT_ANCHOR)):
        if src.count(anchor) != 1:
            print('ANCHOR %s appears %d times - do not guess' % (name, src.count(anchor)))
            sys.exit(1)
    src = src.replace(ANCHOR, PROBE, 1)
    src = src.replace(COUNT_ANCHOR, COUNT_PROBE, 1)
    open(TARGET, 'w', encoding='utf-8').write(src)
    print('applied')
else:
    out = '\n'.join(l for l in src.split('\n') if MARK not in l)
    open(TARGET, 'w', encoding='utf-8').write(out)
    print('reverted; markers left:', out.count(MARK))
