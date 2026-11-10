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
MARK_A = '\t// ---- TEMPORARY POOL PROBE\n'
MARK_B = '\t// ---- END POOL PROBE\n'

PROBE = MARK_A + '''	if (getenv("OXCE_POOL_PROBE"))
	{
		const std::string NA = "STR_NORTH_AMERICA", EU = "STR_EUROPE";
		_cobraEconomy->addFunds(NA, 100);
		_cobraEconomy->addFunds(EU, 500);
		Log(LOG_INFO) << "[probe] NA 100 + Europe 500; expect total 600 | got "
			<< _cobraEconomy->getTotalFunds();

		// a site in NA costing 400: NA pays its 100, Europe covers the other 300
		int took = _cobraEconomy->spendFunds(NA, 400);
		Log(LOG_INFO) << "[probe] spend 400 preferring NA: expect took 400, NA 0, Europe 200"
			<< " | got took " << took << ", NA " << _cobraEconomy->getFunds(NA)
			<< ", Europe " << _cobraEconomy->getFunds(EU);

		// more than Cobra has anywhere: takes what exists, never goes negative
		int took2 = _cobraEconomy->spendFunds(NA, 900);
		Log(LOG_INFO) << "[probe] spend 900 with 200 left: expect took 200, total 0"
			<< " | got took " << took2 << ", total " << _cobraEconomy->getTotalFunds();

		_cobraEconomy->mirrorToCounters(*_alienStrategy);
		Log(LOG_INFO) << "[probe] COBRA_FUNDS_TOTAL counter: expect 0 | got "
			<< _alienStrategy->getMissionsRun("COBRA_FUNDS_TOTAL");
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
    print('raid probe reverted; markers left:', s.count('POOL PROBE'))


{'apply': apply, 'revert': revert}[MODE]()
