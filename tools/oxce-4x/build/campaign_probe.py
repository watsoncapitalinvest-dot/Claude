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
		// Where Cobra actually built, which is the claim the region lock makes and the one  // CAMPROBE
		// thing nobody has watched over a campaign. A site outside North America is not a     // CAMPROBE
		// balance question - it is a raid that lands on an X-COM map.                         // CAMPROBE
		std::map<std::string, int> regions;                                    // CAMPROBE
		for (auto* ab : _alienBases)                                           // CAMPROBE
		{                                                                      // CAMPROBE
			if (ab->getSiteType().empty()) continue;                           // CAMPROBE
			Region* rg = locateRegion(*ab);                                    // CAMPROBE
			std::string rn = rg ? rg->getRules()->getType() : "(nowhere)";     // CAMPROBE
			regions[rn.substr(rn.rfind('_') + 1)]++;                           // CAMPROBE
		}                                                                      // CAMPROBE
		std::ostringstream where;                                              // CAMPROBE
		for (const auto& r : regions) where << r.first << "x" << r.second << " ";// CAMPROBE
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
		// What a raid on each Cobra site would meet. Calls the real lookup against real        // CAMPROBE
		// campaign state - regions, bases, the lot - so the month a camp appears, the sites    // CAMPROBE
		// in its region must change and nothing else may.                                      // CAMPROBE
		// Cumulative, off the base itself. Sampling _missionSites once a month would miss a    // CAMPROBE
		// terror site that lives a few days, and would read as "the Drome launched nothing"     // CAMPROBE
		// when it had launched five. The engine already counts them; use its number.           // CAMPROBE
		// The first version of this counted every generated mission and was useless: John's     // CAMPROBE
		// front ops run supply missions at 6% a DAY, so the total read 63 before the Drome      // CAMPROBE
		// even existed and the Drome's own contribution vanished into it. A number that moves   // CAMPROBE
		// whether or not the thing under test is present measures nothing.                      // CAMPROBE
		//                                                                                       // CAMPROBE
		// Nothing but the Drome generates terror missions, so counting those by TYPE is the     // CAMPROBE
		// question actually being asked.                                                        // CAMPROBE
		int launched = 0, terror = 0;                                          // CAMPROBE
		for (auto* ab : _alienBases) launched += ab->getGenMissionCount();     // CAMPROBE
		for (auto* am : _activeMissions)                                       // CAMPROBE
		{                                                                      // CAMPROBE
			if (am->getRules().getType() == "STR_ALIEN_TERROR") ++terror;      // CAMPROBE
		}                                                                      // CAMPROBE
		int lost = 0, shippers = 0;                                            // CAMPROBE
		for (auto* ab : _alienBases)                                           // CAMPROBE
		{                                                                      // CAMPROBE
			if (ab->getSiteType().empty()) continue;                           // CAMPROBE
			const RuleCobraSite* r = mod->getCobraSite(ab->getSiteType());     // CAMPROBE
			if (r && r->getIncomeNeedsShipment()) ++shippers;                  // CAMPROBE
			lost += ab->getShipmentsLost();                                    // CAMPROBE
		}                                                                      // CAMPROBE
		std::ostringstream gar;                                                // CAMPROBE
		{                                                                      // CAMPROBE
			std::map<std::string, std::string> seen;                           // CAMPROBE
			for (auto* ab : _alienBases)                                       // CAMPROBE
			{                                                                  // CAMPROBE
				if (ab->getSiteType().empty()) continue;                       // CAMPROBE
				Region* rg = locateRegion(*ab);                                // CAMPROBE
				if (!rg) continue;                                             // CAMPROBE
				std::string rn = rg->getRules()->getType();                    // CAMPROBE
				CobraGarrison g = cobraGarrison(mod, ab->getLongitude(),       // CAMPROBE
					ab->getLatitude(), true);                                  // CAMPROBE
				std::ostringstream one;                                        // CAMPROBE
				one << "+" << g.bonus << "/cap" << g.rankUnlock;               // CAMPROBE
				seen[rn.substr(rn.rfind('_') + 1)] = one.str();                // CAMPROBE
			}                                                                  // CAMPROBE
			for (const auto& kv : seen) gar << kv.first << kv.second << " ";   // CAMPROBE
		}                                                                      // CAMPROBE
		Log(LOG_INFO) << "[camp] " << _time->getYear() << "-"                  // CAMPROBE
			<< _time->getMonth() << "  funds=" << _cobraEconomy->getTotalFunds()// CAMPROBE
			<< "  sites=" << _alienBases.size()                                // CAMPROBE
			<< "  have[ " << have.str() << "]  wants[ " << want.str()          // CAMPROBE
			<< "]  where[ " << where.str() << "]  garrison[ " << gar.str()     // CAMPROBE
			<< "]  shippers=" << shippers << " lostNow=" << lost               // CAMPROBE
			<< " terrorLive=" << terror << " launched=" << launched            // CAMPROBE
			<< " liveMissions=" << _activeMissions.size()                      // CAMPROBE
			<< " missionSites=" << _missionSites.size();                       // CAMPROBE
		if (!other.str().empty())                                              // CAMPROBE
			Log(LOG_INFO) << "[camp]        untagged[ " << other.str() << "]"; // CAMPROBE
		// A raid, on demand, through exactly the path the debriefing uses, so the planner's   // CAMPROBE
		// response to losing something is observed rather than asserted. OXCE_CAMP_RAID is a  // CAMPROBE
		// month number; at that month Cobra's best earner is taken off the board.             // CAMPROBE
		// Cobra wants a training camp and rolls 26% a month for it, so waiting on the dice to  // CAMPROBE
		// test the camp is waiting on luck. This turns one site it already owns into a camp at  // CAMPROBE
		// the named month, so the garrison line either flips the month after or the lookup is   // CAMPROBE
		// wrong. The negative case needs no help - the campaign supplies it all by itself.      // CAMPROBE
		const char* plantEnv = getenv("OXCE_CAMP_PLANT");                      // CAMPROBE
		// OXCE_CAMP_PLANT=<month>:<SHORT>, e.g. 7:TERROR_DROME. Turns one front company into   // CAMPROBE
		// that type, so the thing under test exists on a known month instead of when the dice   // CAMPROBE
		// get round to it - the Drome rolls 13% a month and waiting on it is waiting on luck.   // CAMPROBE
		if (plantEnv && *plantEnv)                                                          // CAMPROBE
		{                                                                      // CAMPROBE
			std::string pe(plantEnv);                                          // CAMPROBE
			size_t colon = pe.find(':');                                       // CAMPROBE
			int when = atoi(pe.substr(0, colon).c_str());                      // CAMPROBE
			std::string what = colon == std::string::npos                      // CAMPROBE
				? std::string("STR_COBRA_TRAINING_CAMP")                       // CAMPROBE
				: "STR_COBRA_" + pe.substr(colon + 1);                         // CAMPROBE
			if (_time->getMonth() == when)                                     // CAMPROBE
			{                                                                  // CAMPROBE
				for (auto* ab : _alienBases)                                   // CAMPROBE
				{                                                              // CAMPROBE
					if (ab->getSiteType() != "STR_COBRA_FRONT_COMPANY") continue;// CAMPROBE
					// BOTH halves, or this plants a chimera. setSiteType is what the economy   // CAMPROBE
					// and the planner read; genMission lives on the DEPLOYMENT, which is a     // CAMPROBE
					// different pointer entirely. Setting only the first made a base that was  // CAMPROBE
					// a Terror Drome to cobraPlan and a front company to everything else, and  // CAMPROBE
					// four months of "the Drome launches nothing" was this line, not the mod.  // CAMPROBE
					ab->setSiteType(what);                                     // CAMPROBE
					std::string depName = "STR_COBRA_" +                       // CAMPROBE
						what.substr(std::string("STR_COBRA_").size()) + "_SITE";// CAMPROBE
					AlienDeployment* dep = mod->getDeployment(depName);        // CAMPROBE
					if (dep) ab->setDeployment(dep);                           // CAMPROBE
					Log(LOG_INFO) << "[camp] PLANTED " << what                 // CAMPROBE
						<< " deployment=" << (dep ? depName : "NOT FOUND");    // CAMPROBE
					break;                                                     // CAMPROBE
				}                                                              // CAMPROBE
			}                                                                  // CAMPROBE
		}                                                                      // CAMPROBE
		// Shoot down one Cobra cargo flight, through the engine's own path: set the UFO to      // CAMPROBE
		// DESTROYED and let the real cleanup run, which is where the hook lives. Setting the     // CAMPROBE
		// site's counter by hand instead would test the consequence and skip the thing most      // CAMPROBE
		// likely to be wrong, which is whether a dead UFO can be traced back to the site that    // CAMPROBE
		// sent it.                                                                               // CAMPROBE
		// An EMPTY env var is still a valid pointer, and campaign_ff.sh passes "${SHOOT:-}" which
		// sets it to "" rather than leaving it unset. So getenv came back truthy with nothing
		// behind it, atoi("") gave 0, and the control run was shooting cargo down as eagerly as
		// the test run. Both halves of the comparison reported the same thing and it looked
		// like the feature firing when it should not.
		const char* shootEnv = getenv("OXCE_CAMP_SHOOTDOWN");                  // CAMPROBE
		if (shootEnv && *shootEnv && _time->getMonth() >= atoi(shootEnv))                   // CAMPROBE
		{                                                                      // CAMPROBE
			int downed = 0;                                                    // CAMPROBE
			for (auto* u : _ufos)                                              // CAMPROBE
			{                                                                  // CAMPROBE
				if (u->getStatus() == Ufo::DESTROYED) continue;                // CAMPROBE
				AlienMission* am = u->getMission();                            // CAMPROBE
				if (!am || !am->getAlienBase()) continue;                      // CAMPROBE
				const AlienBase* src = am->getAlienBase();                     // CAMPROBE
				if (src->getSiteType().empty()) continue;                      // CAMPROBE
				const RuleCobraSite* r = mod->getCobraSite(src->getSiteType());// CAMPROBE
				if (!r || !r->getIncomeNeedsShipment()) continue;              // CAMPROBE
				// Mark it the way the dogfight does, or the hook correctly ignores it - which   // CAMPROBE
				// is the whole point of the predicate being tested.                             // CAMPROBE
				u->setShotDownByCraftId(CraftId("STR_INTERCEPTOR", 1));        // CAMPROBE
				u->setStatus(Ufo::DESTROYED);                                  // CAMPROBE
				Log(LOG_INFO) << "[camp] SHOTDOWN a shipment from "            // CAMPROBE
					<< src->getSiteType();                                     // CAMPROBE
				++downed;                                                      // CAMPROBE
				break;                                                         // CAMPROBE
			}                                                                  // CAMPROBE
			if (!downed) Log(LOG_INFO) << "[camp] SHOTDOWN found no cargo in the air";// CAMPROBE
			// Try again every month until one is caught. A supply run is only airborne part of  // CAMPROBE
			// the time, so a single attempt on one month boundary mostly finds empty sky - the  // CAMPROBE
			// first run of this reported "no cargo in the air" and proved nothing.              // CAMPROBE
		}                                                                      // CAMPROBE
		const char* raidEnv = getenv("OXCE_CAMP_RAID");                        // CAMPROBE
		if (raidEnv && *raidEnv && _time->getMonth() == atoi(raidEnv))                     // CAMPROBE
		{                                                                      // CAMPROBE
			// Take a type Cobra has exactly one of. Raiding one front company out of seven  // CAMPROBE
			// proves nothing: the planner still owns six, so of course it does not rebuild.  // CAMPROBE
			// The claim being tested is that losing its ONLY one puts that type back on the  // CAMPROBE
			// list, and only a unique site can test it.                                      // CAMPROBE
			std::map<std::string, int> count;                                  // CAMPROBE
			for (auto* ab : _alienBases)                                       // CAMPROBE
				if (!ab->getSiteType().empty()) count[ab->getSiteType()]++;    // CAMPROBE
			for (auto it = _alienBases.begin(); it != _alienBases.end(); ++it) // CAMPROBE
			{                                                                  // CAMPROBE
				if ((*it)->getSiteType().empty()) continue;                    // CAMPROBE
				if (count[(*it)->getSiteType()] != 1) continue;                // CAMPROBE
				int denied = cobraRaided(*it, mod);                            // CAMPROBE
				Log(LOG_INFO) << "[camp] RAIDED " << (*it)->getSiteType()      // CAMPROBE
					<< " denied=" << denied;                                   // CAMPROBE
				clearLinksForAlienBase(*it, mod);                              // CAMPROBE
				delete *it;                                                    // CAMPROBE
				_alienBases.erase(it);                                         // CAMPROBE
				break;                                                         // CAMPROBE
			}                                                                  // CAMPROBE
		}                                                                      // CAMPROBE
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
