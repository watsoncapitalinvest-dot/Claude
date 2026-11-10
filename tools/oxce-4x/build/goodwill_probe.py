"""Exercise the broadcast station's goodwill erosion headless.

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
MARK_A = '\t// ---- TEMPORARY GOODWILL PROBE\n'
MARK_B = '\t// ---- END GOODWILL PROBE\n'

PROBE = MARK_A + '''	if (getenv("OXCE_GOODWILL_PROBE"))
	{
		const std::string NA = "STR_NORTH_AMERICA";
		AlienDeployment *dep = mod->getDeployment("STR_COBRA_BROADCAST_STATION_SITE", false);
		if (dep == 0) { Log(LOG_INFO) << "[probe] MISSING broadcast deployment"; }
		else
		{
			AlienBase *ab = new AlienBase(dep, 0);
			ab->setId(getId("STR_ALIEN_BASE"));
			ab->setLongitude(4.36332);
			ab->setLatitude(-1.09083);
			ab->setSiteType(dep->getCobraSiteType());
			_alienBases.push_back(ab);

			Region *r = locateRegion(*ab);
			Country *c = locateCountry(*ab);
			int before = r ? r->getActivityAlien().back() : -1;
			int cbefore = c ? c->getActivityAlien().back() : -1;
			cobraMonthly(mod);
			int after = r ? r->getActivityAlien().back() : -1;
			int cafter = c ? c->getActivityAlien().back() : -1;
			Log(LOG_INFO) << "[probe] broadcast station: expect region and country alien activity each +5";
			Log(LOG_INFO) << "[probe]   region  " << before << " -> " << after
				<< "   country " << cbefore << " -> " << cafter
				<< (c ? "" : "  (no country at that point, region only)");
		}
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
    print('raid probe reverted; markers left:', s.count('GOODWILL PROBE'))


{'apply': apply, 'revert': revert}[MODE]()
