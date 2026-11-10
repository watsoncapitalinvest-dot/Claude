"""Temporary instrumentation: did the material tags survive the trip into the game?

Three things stand between materials.json and a tile that stops a bullet, and all three fail
quietly. The ruleset might not be picked up at all. MCDPatch might load the key and never apply
it. And the dataset the patch names might not be the dataset the terrain loads, in which case
everything "works" and no tile is tagged. Printing a histogram per dataset at the moment the
patch has just been applied separates all three: a dataset that never prints was never loaded, a
dataset that prints all-zero was loaded and not patched.

usage: mat_probe.py apply|revert <src dir>
"""
import sys, re, os

MODE, SRC = sys.argv[1], sys.argv[2]
MARK = '// MATPROBE'

TARGET = os.path.join(SRC, 'Mod', 'MapDataSet.cpp')

ANCHOR = """	// apply any ruleset patches before validation
	if (patch)
	{
		patch->modifyData(this);
	}
"""

PROBE = ANCHOR + """	if (getenv("OXCE_MAT_PROBE"))                                              // MATPROBE
	{                                                                          // MATPROBE
		int h[6] = {0, 0, 0, 0, 0, 0};                                         // MATPROBE
		for (size_t i = 0; i < _objects.size(); ++i)                           // MATPROBE
		{                                                                      // MATPROBE
			int m = _objects[i]->getMaterial();                                // MATPROBE
			if (m >= 0 && m < 6) ++h[m];                                       // MATPROBE
		}                                                                      // MATPROBE
		Log(LOG_INFO) << "[matprobe] " << _name << " n=" << _objects.size()    // MATPROBE
			<< " unknown=" << h[0] << " light=" << h[1] << " wood=" << h[2]    // MATPROBE
			<< " masonry=" << h[3] << " concrete=" << h[4]                     // MATPROBE
			<< " metal=" << h[5] << (patch ? " PATCHED" : " no-patch");        // MATPROBE
	}                                                                          // MATPROBE
"""

src = open(TARGET, encoding='utf-8').read()

if MODE == 'apply':
    if MARK in src:
        print('already applied')
        sys.exit(0)
    if ANCHOR not in src:
        print('ANCHOR NOT FOUND - the file moved, do not guess')
        sys.exit(1)
    open(TARGET, 'w', encoding='utf-8').write(src.replace(ANCHOR, PROBE, 1))
    print('applied')
else:
    out = '\n'.join(l for l in src.split('\n') if MARK not in l)
    open(TARGET, 'w', encoding='utf-8').write(out)
    print('reverted; markers left:', out.count(MARK))
