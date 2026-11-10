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
MARK_A = '\t// ---- TEMPORARY RAID PROBE\n'
MARK_B = '\t// ---- END RAID PROBE\n'

PROBE = MARK_A + '''	if (getenv("OXCE_RAID_PROBE"))
	{
		const std::string NA = "STR_NORTH_AMERICA";
		auto plant = [&](const char *depName) -> AlienBase *
		{
			AlienDeployment *dep = mod->getDeployment(depName, false);
			if (dep == 0) { Log(LOG_INFO) << "[probe] MISSING " << depName; return 0; }
			AlienBase *ab = new AlienBase(dep, 0);
			ab->setId(getId("STR_ALIEN_BASE"));
			ab->setLongitude(4.36332);
			ab->setLatitude(-1.09083);
			ab->setSiteType(dep->getCobraSiteType());
			ab->setDiscovered(true);
			return ab;
		};

		// 1. an ordinary site takes its stated loot: a front company loots 60 funds
		_cobraEconomy->addFunds(NA, 500);
		_cobraEconomy->addMateriel(NA, 200);
		AlienBase *fc = plant("STR_COBRA_FRONT_COMPANY_SITE");
		int r1 = fc ? cobraRaided(fc, mod) : -1;
		Log(LOG_INFO) << "[probe] case 1 front company: expect returned 60, funds 440, materiel 200"
			<< " | got returned " << r1 << ", funds " << _cobraEconomy->getFunds(NA)
			<< ", materiel " << _cobraEconomy->getMateriel(NA);

		// 2. a depot takes everything the region had banked
		AlienBase *dp = plant("STR_COBRA_DEPOT_SITE");
		int r2 = dp ? cobraRaided(dp, mod) : -1;
		Log(LOG_INFO) << "[probe] case 2 depot: expect returned 640, funds 0, materiel 0"
			<< " | got returned " << r2 << ", funds " << _cobraEconomy->getFunds(NA)
			<< ", materiel " << _cobraEconomy->getMateriel(NA);

		// 3. cannot take more than is there: 20 on hand against a 60 loot
		_cobraEconomy->addFunds(NA, 20);
		AlienBase *fc2 = plant("STR_COBRA_FRONT_COMPANY_SITE");
		int r3 = fc2 ? cobraRaided(fc2, mod) : -1;
		Log(LOG_INFO) << "[probe] case 3 clamp: expect returned 20, funds 0"
			<< " | got returned " << r3 << ", funds " << _cobraEconomy->getFunds(NA);

		delete fc; delete dp; delete fc2;
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
    print('raid probe reverted; markers left:', s.count('RAID PROBE'))


{'apply': apply, 'revert': revert}[MODE]()
