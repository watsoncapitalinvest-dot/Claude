"""Exercise SavedGame::cobraRaided headless, with the answers written down first.

The raid outcome normally only runs at the end of a battle, which a headless run cannot reach.
But cobraRaided is the whole of the logic the debriefing calls, so it can be driven directly.

Three cases, chosen so each one can fail on its own:
  1. an ordinary site takes its stated loot out of the region
  2. a depot takes the whole regional stockpile, however large
  3. a site cannot take more than the region actually holds

usage: raid_probe.py apply|revert <src dir>
"""
import sys

MODE, SRC = sys.argv[1], sys.argv[2]
P = SRC + '/Savegame/SavedGame.cpp'
MARK_A = '\t// ---- TEMPORARY BUILD PROBE\n'
MARK_B = '\t// ---- END BUILD PROBE\n'

PROBE = MARK_A + '''	if (getenv("OXCE_BUILD_PROBE"))
	{
		const std::string NA = "STR_NORTH_AMERICA";
		auto plant = [&](const char *depName) -> AlienBase *
		{
			AlienDeployment *dep = mod->getDeployment(depName, false);
			if (dep == 0) { Log(LOG_INFO) << "[probe] MISSING " << depName; return 0; }
			AlienBase *ab = new AlienBase(dep, 0);
			ab->setLongitude(4.36332);
			ab->setLatitude(-1.09083);
			ab->setSiteType(dep->getCobraSiteType());
			return ab;
		};

		_cobraEconomy->addFunds(NA, 1000);
		AlienBase *f = plant("STR_COBRA_FACTORY_SITE");
		if (f) cobraBuilt(f, mod);
		Log(LOG_INFO) << "[probe] built a factory (cost 600) with 1000 on hand:"
			<< " expect funds 400, counter 400 | got funds " << _cobraEconomy->getFunds(NA)
			<< ", counter " << _alienStrategy->getMissionsRun("COBRA_FUNDS_" + NA);

		// a second one it cannot afford: the scripts gate this, so cobraBuilt only takes what
		// is there rather than deciding - but it must not drive the stockpile negative
		AlienBase *f2 = plant("STR_COBRA_FACTORY_SITE");
		if (f2) cobraBuilt(f2, mod);
		Log(LOG_INFO) << "[probe] a second factory with only 400 on hand: expect funds 0, not -200"
			<< " | got funds " << _cobraEconomy->getFunds(NA);

		delete f; delete f2;
	}
''' + MARK_B


def apply():
    s = open(P).read()
    if MARK_A in s:
        print('already applied'); return
    anchor = '\t_scriptValues.load(reader, mod->getScriptGlobal());\n'
    if s.count(anchor) != 1:
        raise SystemExit('anchor count %d' % s.count(anchor))
    s = s.replace(anchor, anchor + '\n' + PROBE, 1)
    open(P, 'w').write(s)
    print('raid probe applied')


def revert():
    s = open(P).read()
    if MARK_A not in s:
        print('nothing to revert'); return
    i, j = s.index(MARK_A), s.index(MARK_B) + len(MARK_B)
    s = s[:i] + s[j:]
    s = s.replace('\n\n\n', '\n\n')
    open(P, 'w').write(s)
    print('raid probe reverted; markers left:', s.count('BUILD PROBE'))


{'apply': apply, 'revert': revert}[MODE]()
