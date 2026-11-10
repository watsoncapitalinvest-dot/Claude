"""Temporary instrumentation: what does the planner actually do over a campaign?

Every piece of the economy was verified on its own and none of it has run for six months in a
row. The planner especially: its four test scenarios were states I constructed, and a state I
construct is one I already believe in. A campaign builds its own states, including the ones
nobody thought to write down - the month Cobra is solvent but has nothing affordable, the month a
raid takes its only earner, the month it owns one of everything and the list goes empty.

So this logs one line a month: what Cobra holds, what it wants, and what it has. Read down the
column and the policy is either visible or it is not.

Placed at the end of cobraMonthly, after the plan is published, so the line is what the mission
scripts are about to act on rather than what they acted on last month.

usage: campaign_probe.py apply|revert <src dir>
"""
import sys, os

MODE, SRC = sys.argv[1], sys.argv[2]
MARK = '// CAMPROBE'
TARGET = os.path.join(SRC, 'Savegame', 'SavedGame.cpp')

ANCHOR = '\tcobraPlan(mod);\n'

PROBE = ANCHOR + """	if (getenv("OXCE_CAMP_PROBE"))                                             // CAMPROBE
	{                                                                          // CAMPROBE
		std::ostringstream have, want;                                         // CAMPROBE
		for (const auto& id : mod->getCobraSitesList())                        // CAMPROBE
		{                                                                      // CAMPROBE
			int n = 0;                                                         // CAMPROBE
			for (auto* ab : _alienBases)                                       // CAMPROBE
			{                                                                  // CAMPROBE
				if (ab->getSiteType() == id) ++n;                              // CAMPROBE
			}                                                                  // CAMPROBE
			std::string shortId = id.substr(id.rfind('_') + 1);                // CAMPROBE
			if (n) have << shortId << "x" << n << " ";                         // CAMPROBE
			if (_alienStrategy->getMissionsRun("COBRA_BUILD_" + id) > 0)       // CAMPROBE
				want << shortId << " ";                                        // CAMPROBE
		}                                                                      // CAMPROBE
		std::map<std::string, int> untagged;                                   // CAMPROBE
		for (auto* ab : _alienBases)                                           // CAMPROBE
		{                                                                      // CAMPROBE
			if (ab->getSiteType().empty())                                     // CAMPROBE
			{                                                                  // CAMPROBE
				const AlienDeployment* d = ab->getDeployment();                // CAMPROBE
				untagged[d ? d->getType() : "(no deployment)"]++;              // CAMPROBE
			}                                                                  // CAMPROBE
		}                                                                      // CAMPROBE
		std::ostringstream other;                                              // CAMPROBE
		for (const auto& u : untagged)                                         // CAMPROBE
			other << u.first << "x" << u.second << " ";                        // CAMPROBE
		Log(LOG_INFO) << "[camp] " << _time->getYear() << "-"                  // CAMPROBE
			<< _time->getMonth() << "  funds=" << _cobraEconomy->getTotalFunds()// CAMPROBE
			<< "  sites=" << _alienBases.size()                                // CAMPROBE
			<< "  have[ " << have.str() << "]  wants[ " << want.str()          // CAMPROBE
			<< "]  untagged[ " << other.str() << "]";                          // CAMPROBE
	}                                                                          // CAMPROBE
"""

src = open(TARGET, encoding='utf-8').read()

if MODE == 'apply':
    if MARK in src:
        print('already applied')
        sys.exit(0)
    if src.count(ANCHOR) != 1:
        print('ANCHOR appears %d times - do not guess' % src.count(ANCHOR))
        sys.exit(1)
    open(TARGET, 'w', encoding='utf-8').write(src.replace(ANCHOR, PROBE, 1))
    print('applied')
else:
    out = '\n'.join(l for l in src.split('\n') if MARK not in l)
    open(TARGET, 'w', encoding='utf-8').write(out)
    print('reverted; markers left:', out.count(MARK))
