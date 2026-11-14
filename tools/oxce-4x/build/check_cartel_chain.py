#!/usr/bin/env python3
"""Walks the cartel arc (STORY_CartelArc_v1) through the mod's rulesets and reports any broken link.

    python3 build/check_cartel_chain.py

Every step, and every fallback for when a step goes wrong, must lead on to the factory. A link is a rule
that has to exist in a file the game loads: an item that comes home, the topic that reads it, the topic it
opens, the mission script that keys on it, the deployment and its map. Engine-side links (the stash house
placed on Day 1, the tail finding it, the logbook from the wreck) are listed and checked by name only.
"""
import glob
import os
import sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, '..', 'mod'))


class Loose(yaml.SafeLoader):
    pass


def _any(loader, suffix, node):
    return None


Loose.add_multi_constructor('', _any)

R = {'research': {}, 'items': {}, 'alienDeployments': {}, 'alienMissions': {}, 'missionScripts': {}, 'leads': {},
     'terrains': {}, 'mapScripts': {}, 'ufos': {}, 'spyOperations': {}, 'gijoeBounties': {}}
for f in sorted(glob.glob(os.path.join(MOD, 'Ruleset', '*.rul'))):
    try:
        d = yaml.load(open(f, encoding='utf-8'), Loader=Loose) or {}
    except Exception as e:
        print(f'PARSE {os.path.basename(f)}: {e}')
        continue
    for k in R:
        v = d.get(k)
        if k == 'gijoeBounties' and isinstance(v, dict):
            R[k].update(v)
        elif isinstance(v, list):
            for e in v:
                if isinstance(e, dict):
                    key = e.get('name') or e.get('type') or e.get('id')
                    if key:
                        R[k].setdefault(key, {}).update(e)
    cap = d.get('capture')
    if isinstance(cap, dict):
        for op in cap.get('spyOperations', []) or []:
            if isinstance(op, dict) and op.get('type'):
                R['spyOperations'][op['type']] = op
maps = {os.path.splitext(os.path.basename(p))[0].upper() for p in glob.glob(os.path.join(MOD, 'MAPS', '*'))}

bad = []


def need(cond, what):
    print(('  ok   ' if cond else '  FAIL ') + what)
    if not cond:
        bad.append(what)


def research(n):
    return n in R['research']


def unlocks(a, b):
    r = R['research'].get(a, {})
    return b in (r.get('unlocks') or []) or b in (r.get('getOneFree') or [])


def opens(b, a):
    """b becomes available after a: a unlocks it, or b depends on a"""
    return unlocks(a, b) or a in (R['research'].get(b, {}).get('dependencies') or [])


def item_topic(i):
    return i in R['items'] and research(i) and R['research'][i].get('needItem')


def scripted(mission, trigger):
    for s in R['missionScripts'].values():
        w = s.get('missionWeights') or {}
        names = set()
        for v in w.values():
            names |= set((v or {}).keys())
        if mission in names and trigger in (s.get('researchTriggers') or {}):
            return True
    return False


def deployment_ok(dep):
    d = R['alienDeployments'].get(dep)
    if not d:
        return False
    for t in d.get('terrains') or []:
        tr = R['terrains'].get(t)
        if not tr:
            return False
        for b in tr.get('mapBlocks') or []:
            if b.get('name', '').upper() not in maps:
                return False
    return True


def lead_counts(lead, key):
    return key in ((R['leads'].get(lead) or {}).get('research') or {})


print('STEP 1  the ranch')
need('STR_CARTEL_RANCH_MISSION' in R['alienMissions'], 'the ranch mission exists')
need(deployment_ok('STR_CARTEL_RANCH'), 'the ranch deployment and its map')
for i in ('STR_CARTEL_LEDGER', 'STR_CRATE_SERIAL_PLATE', 'STR_COBRA_STENCIL'):
    need(i in (R['gijoeBounties'].get('STR_CARTEL_RANCH') or []), f'{i} comes home from the ranch')
    need(item_topic(i), f'{i} is an item with a topic that reads it')
    need(lead_counts('STR_LEAD_CARTEL_SUPPLIER', i), f'{i} counts toward the lead')
need(item_topic('STR_CARTEL_BOSS'), 'the boss taken alive is a topic')
need(lead_counts('STR_LEAD_CARTEL_SUPPLIER', 'STR_CARTEL_BOSS'), 'the boss counts toward the lead')

print('STEP 2  the flight (from the ledger OR the boss)')
need(opens('STR_CARTEL_FLIGHT_ROUTE', 'STR_CARTEL_LEDGER'), 'the ledger opens the flight route')
need(opens('STR_CARTEL_FLIGHT_ROUTE', 'STR_CARTEL_BOSS'), 'the boss opens the flight route (boss path)')
need(deployment_ok('STR_CARTEL_STASH_HOUSE'), 'the stash house deployment and its map (placed by the engine on Day 1)')
need('STR_CARTEL_FLIGHT' in ((R['alienDeployments'].get('STR_CARTEL_STASH_HOUSE') or {}).get('genMission') or {}), 'the stash house sends cartel flights')
need('STR_CARTEL_PLANE' in R['ufos'] and 'STR_CARTEL_FLIGHT' in R['alienMissions'], 'the cartel plane and its flight mission')
need(item_topic('STR_CARTEL_LOGBOOK'), 'shot down instead: the logbook (engine gives it from the wreck) is read by a topic')
need((R['leads'].get('STR_LEAD_CARTEL_STASH') or {}).get('revealSiteType') == 'STR_CARTEL_STASH_HOUSE', 'the logbook reveals the stash house')
need(research('STR_CARTEL_STASH_HOUSE') and (R['alienDeployments'].get('STR_CARTEL_STASH_HOUSE') or {}).get('unlockedResearch') == 'STR_CARTEL_STASH_HOUSE', 'raiding the stash house counts')

print('STEP 3  Scarlett\'s operation')
op = R['spyOperations'].get('STR_OP_SCARLETT_STASH_HOUSE') or {}
need(bool(op), 'Operation Quiet Courier exists')
need(set(op.get('requiresAny') or []) >= {'STR_CARTEL_FLIGHT_ROUTE', 'STR_CARTEL_LOGBOOK'}, 'it opens from the flight route or the logbook')
need('STR_INFORMANT_TIP' in (op.get('items') or {}), 'it brings home the informant\'s tip')
need(item_topic('STR_INFORMANT_TIP'), 'the tip is read by a topic')

print('STEP 4  the robbery')
need(scripted('STR_ARMORED_CAR_AMBUSH_MISSION', 'STR_INFORMANT_TIP'), 'tipped: the robbery appears ahead of time')
need(deployment_ok('STR_ARMORED_CAR_AMBUSH'), 'the robbery deployment and its map')
need(item_topic('STR_ROBBERY_LEADER'), 'the leader taken alive is a topic')
need('STR_GETAWAY_PAPERS' in (R['gijoeBounties'].get('STR_ARMORED_CAR_AMBUSH') or []), 'the van\'s papers come home from a won robbery')
amb = R['alienDeployments'].get('STR_ARMORED_CAR_AMBUSH') or {}
need(amb.get('unlockedResearchOnFailure') == 'STR_ROBBERY_MISSED' and amb.get('unlockedResearchOnDespawn') == 'STR_ROBBERY_MISSED', 'lost or ignored: the robbery is marked missed')
need(scripted('STR_CARTEL_SAFEHOUSE_MISSION', 'STR_ROBBERY_MISSED'), 'missed with an informant: the safehouse raid appears')
need(deployment_ok('STR_CARTEL_SAFEHOUSE'), 'the safehouse deployment and its map')
need((R['alienDeployments'].get('STR_CARTEL_SAFEHOUSE') or {}).get('missionBountyItem') == 'STR_GETAWAY_PAPERS', 'the safehouse gives the papers')
need(opens('STR_SLOW_MONEY_TRACE', 'STR_ROBBERY_MISSED'), 'missed: the slow money trace opens')

print('STEP 5  the bank')
for a in ('STR_ROBBERY_LEADER', 'STR_GETAWAY_PAPERS', 'STR_SLOW_MONEY_TRACE'):
    need(opens('STR_BORDER_BANK_TRACE', a), f'{a} opens the border bank trace')
need((R['leads'].get('STR_LEAD_CARTEL_SUPPLIER') or {}).get('research', {}).get('STR_BORDER_BANK_TRACE', 0) >= (R['leads'].get('STR_LEAD_CARTEL_SUPPLIER') or {}).get('threshold', 100), 'the bank trace always fills the lead')
need('STR_FACTORY_LEAD_SOLVED' in ((R['leads'].get('STR_LEAD_CARTEL_SUPPLIER') or {}).get('grantResearch') or []), 'the full lead hands over STR_FACTORY_LEAD_SOLVED')

print('STEP 6  the factory')
need(scripted('STR_ABANDONED_FACTORY_MISSION', 'STR_FACTORY_LEAD_SOLVED'), 'the lead solved: the factory appears')
back = [s for s in R['missionScripts'].values() if 'STR_ABANDONED_FACTORY_MISSION' in str(s.get('missionWeights')) and (s.get('researchTriggers') or {}).get('STR_FACTORY_LEAD_SOLVED') is False]
need(bool(back), 'the arc ignored: the factory turns up anyway (backstop)')
need(deployment_ok('STR_ABANDONED_FACTORY'), 'the factory deployment and its map')
need('STR_FACTORY_SCHEDULE' in (R['gijoeBounties'].get('STR_ABANDONED_FACTORY') or []) and item_topic('STR_FACTORY_SCHEDULE'), 'the payoff (the production schedule) comes home and is read')

print()
print('BROKEN LINKS:', len(bad))
sys.exit(1 if bad else 0)
