"""Render the Cobra intel screen headless and write it to a PNG, so it can be looked at.

A screen is for looking at, and nothing else in this session's toolkit can see one. SDL's dummy
video driver still composes to a real surface in memory, and Screen::screenshot is public, so
the game can be made to load a save, push the state and save a picture without a display.

Temporary. apply() patches Game::run, revert() puts it back.

usage: intel_shot_probe.py apply|revert <src dir>
"""
import sys, re

MODE, SRC = sys.argv[1], sys.argv[2]
P = SRC + '/Engine/Game.cpp'
PSAVE = SRC + '/Savegame/SavedGame.cpp'

MARK_A = '\t// ---- TEMPORARY INTEL SHOT PROBE\n'
MARK_B = '\t// ---- END INTEL SHOT PROBE\n'

PROBE = MARK_A + '''	// Waits for -continue to finish loading the geoscape, pushes the intel screen, gives it a
	// few frames to compose, writes a PNG and quits. Frame counts rather than timers, because a
	// headless run has no reliable wall clock to lean on.
	if (getenv("OXCE_INTEL_SHOT"))
	{
		// Only start counting once the save is actually in. -continue loads through a state, so
		// at frame 150 of a headless run there may still be no SavedGame, and pushing the intel
		// screen then made getSavedGame() return null - getAlienBases() handed back 0x1e0, the
		// offset of _alienBases inside a SavedGame at address zero.
		static int probeFrames = 0;
		if (_save == 0)
		{
			probeFrames = 0;
		}
		else
		{
			++probeFrames;
		}
		if (probeFrames == 150)
		{
			pushState(new CobraIntelState);
		}
		else if (probeFrames == 170)
		{
			_screen->screenshot(getenv("OXCE_INTEL_SHOT"));
			_quit = true;
		}
		else if (probeFrames == 160)
		{
			// the row count is the functional check; the picture is incidental
			Log(LOG_INFO) << "[probe] intel screen pushed, states=" << _states.size();
		}
	}
''' + MARK_B


PLANT_A = '\t// ---- TEMPORARY INTEL PLANT\n'
PLANT_B = '\t// ---- END INTEL PLANT\n'
PLANT = PLANT_A + '''	// Three DISCOVERED Cobra sites in North America, so the intel screen has something to
	// report. Discovered matters: the screen counts only what the player has found, so planting
	// them undiscovered would prove nothing except that the empty path works.
	if (getenv("OXCE_INTEL_SHOT"))
	{
		// Built the way spawnAlienBase builds one: the deployment is the real Cobra site
		// deployment and the site type is read off it, rather than a deployment borrowed from
		// elsewhere with the type set by hand. AlienBase::getMarker() dereferences the
		// deployment as soon as a base is discovered - undiscovered it returns -1 and never
		// touches it - so a borrowed-and-missing deployment segfaults the globe, which is
		// exactly what the first run of this probe did.
		const char *plant[] = { "STR_COBRA_FRONT_COMPANY_SITE", "STR_COBRA_FRONT_COMPANY_SITE",
			"STR_COBRA_FACTORY_SITE" };
		for (const char *depName : plant)
		{
			AlienDeployment *dep = mod->getDeployment(depName, false);
			if (dep == 0)
			{
				Log(LOG_INFO) << "[probe] MISSING deployment " << depName;
				continue;
			}
			AlienBase *ab = new AlienBase(dep, 0);
			ab->setId(getId("STR_ALIEN_BASE"));
			ab->setLongitude(4.36332);
			ab->setLatitude(-1.09083);
			ab->setSiteType(dep->getCobraSiteType());
			ab->setDiscovered(true);
			_alienBases.push_back(ab);
		}
		Log(LOG_INFO) << "[probe] planted 3 discovered sites: 2 front companies + 1 factory";
		Log(LOG_INFO) << "[probe] expect 1 row, North America, found=3, funds=180, materiel=80";
	}
''' + PLANT_B


def apply():
    t = open(PSAVE).read()
    if PLANT_A not in t:
        anchor2 = '\t_scriptValues.load(reader, mod->getScriptGlobal());\n'
        if t.count(anchor2) != 1:
            raise SystemExit('savegame anchor count %d' % t.count(anchor2))
        t = t.replace(anchor2, anchor2 + '\n' + PLANT, 1)
        open(PSAVE, 'w').write(t)
        print('plant applied to', PSAVE)

    s = open(P).read()
    if MARK_A in s:
        print('already applied'); return
    anchor = '\t\t\t\t_screen->flip();\n'
    if s.count(anchor) != 1:
        raise SystemExit('anchor _screen->flip() appears %d times, expected 1' % s.count(anchor))
    s = s.replace(anchor, anchor + PROBE, 1)
    inc = '#include "../Geoscape/CobraIntelState.h"'
    if inc not in s:
        s = s.replace('#include "Game.h"', '#include "Game.h"\n' + inc, 1)
    open(P, 'w').write(s)
    print('probe applied to', P)


def revert():
    t = open(PSAVE).read()
    if PLANT_A in t:
        i, j = t.index(PLANT_A), t.index(PLANT_B) + len(PLANT_B)
        t = t[:i] + t[j:]
        t = t.replace('\n\n\n', '\n\n')
        open(PSAVE, 'w').write(t)
        print('plant reverted; markers left:', t.count('INTEL PLANT'))

    s = open(P).read()
    if MARK_A not in s:
        print('nothing to revert'); return
    i, j = s.index(MARK_A), s.index(MARK_B) + len(MARK_B)
    s = s[:i] + s[j:]
    s = s.replace('#include "Game.h"\n#include "../Geoscape/CobraIntelState.h"', '#include "Game.h"', 1)
    open(P, 'w').write(s)
    print('probe reverted; markers left:', s.count('INTEL SHOT PROBE'))


{'apply': apply, 'revert': revert}[MODE]()
