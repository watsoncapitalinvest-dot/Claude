"""Temporary instrumentation: did the penetration matrix come out of the ruleset?

`penetration:` is a top-level key this fork invented, and OXCE ignores a top-level key it does
not know without a word. So a tuning file that is never read looks exactly like a tuning file
whose numbers did not help, and the way that failure gets found is John spending an evening
changing a line that does nothing.

Printed from the TileEngine constructor rather than from the loader, because that proves the
whole chain - ruleset to Mod to the object that actually shoots - rather than just the parse.

usage: pen_probe.py apply|revert <src dir>
"""
import sys, os

MODE, SRC = sys.argv[1], sys.argv[2]
MARK = '// PENPROBE'
TARGET = os.path.join(SRC, 'Battlescape', 'TileEngine.cpp')

ANCHOR = """	_penPass(mod->getPenetrationPass()), _penMaxWalls(mod->getPenetrationMaxWalls())
{
"""

PROBE = ANCHOR + """	if (getenv("OXCE_PEN_PROBE"))                                              // PENPROBE
	{                                                                          // PENPROBE
		static const char* N[6] =                                              // PENPROBE
			{"unknown", "light", "wood", "masonry", "concrete", "metal"};      // PENPROBE
		Log(LOG_INFO) << "[penprobe] maxWalls=" << _penMaxWalls;               // PENPROBE
		for (int i = 0; i < 6; ++i)                                            // PENPROBE
		{                                                                      // PENPROBE
			Log(LOG_INFO) << "[penprobe] " << N[i] << " cost=" << _penCost[i]  // PENPROBE
				<< " energyCost=" << _penEnergyCost[i]                         // PENPROBE
				<< " pass=" << _penPass[i];                                    // PENPROBE
		}                                                                      // PENPROBE
	}                                                                          // PENPROBE
"""

src = open(TARGET, encoding='utf-8').read()

if MODE == 'apply':
    if MARK in src:
        print('already applied')
        sys.exit(0)
    if ANCHOR not in src:
        print('ANCHOR NOT FOUND - the constructor moved, do not guess')
        sys.exit(1)
    open(TARGET, 'w', encoding='utf-8').write(src.replace(ANCHOR, PROBE, 1))
    print('applied')
else:
    out = '\n'.join(l for l in src.split('\n') if MARK not in l)
    open(TARGET, 'w', encoding='utf-8').write(out)
    print('reverted; markers left:', out.count(MARK))
