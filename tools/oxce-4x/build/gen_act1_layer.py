"""Act 1 campaign layer, pieces 1-5 (BRIEF_FOR_DESIGN_Act1Layer_Part1 + BRIEF_FOR_BUILD_Act1Layer_Part1_Answers, approved by
John 17 Nov ~01:30; "build time" 01:35). Writes mod/Ruleset/zz_gijoe_act1_layer.rul: the rules the engine's CobraNetwork reads.

What is here and why:
  cobraNetwork        the hidden starting network, crime and cell-strike chances, the broadcast and factory dates, the
                      candidate towns (towns 20k-500k in the middle of the country; junctions for depots). Engine:
                      Geoscape/CobraNetwork.cpp.
  cobraSites          STR_COBRA_CELL: no economy; its strikes fill a purse, and at 300 it becomes a front company.
  alienDeployments    the cell hideout (the stash house map, 4-8 troopers on the site ladder); the bank job on the globe;
                      the cell strikes (3 maps x 3 sizes); payouts on the four crimes (150) and strikes (80).
  alienMissions       the rules the crime and strike sites are spawned under.
  missionScripts      the old uncapped front-company scripts switched off (piece 4): the planner and the start network
                      own front companies now.
  leads               the broadcast trace reveals a CELL (the one nearest the Pit), never the Drome.
  events              the broadcast, the factory reopened / wrecked (with STORY's cutscenes), the 7-day factory warning.
usage: python3 build/gen_act1_layer.py
"""
import copy, os, yaml
HERE = os.path.dirname(os.path.abspath(__file__))
RUL = os.path.join(HERE, '..', 'mod', 'Ruleset')
sites = yaml.safe_load(open(os.path.join(RUL, 'gijoe_cobra_sites.rul')))
front = next(d for d in sites['alienDeployments'] if d['type'] == 'STR_COBRA_FRONT_COMPANY_SITE')
trooper = copy.deepcopy(front['data'][0])            # rank 5, the six-tier kit ladder the calendar clamps
assert trooper['alienRank'] == 5

def troopers(lo, hi):
    t = copy.deepcopy(trooper); t['lowQty'] = lo; t['highQty'] = hi; t['dQty'] = 1; t['percentageOutsideUfo'] = 100
    return t

def officer():
    t = copy.deepcopy(trooper); t['lowQty'] = 1; t['highQty'] = 1; t['dQty'] = 0; t['customUnitType'] = 'STR_ROBBERY_LEADER'   # no Cobra officer unit exists yet; the robbery leader is the one with a leader's AI
    t['percentageOutsideUfo'] = 100
    return t

# Candidate towns: name, lon, lat (degrees, north positive), kind. Towns of 20k-500k away from the big cities;
# junctions are highway/rail crossroads between them (depots). Rolled each campaign (answers 1a).
TOWNS = [
 ('Amarillo', -101.83, 35.22, 'town'), ('Lubbock', -101.86, 33.58, 'town'), ('Wichita', -97.34, 37.69, 'town'),
 ('Topeka', -95.69, 39.05, 'town'), ('Lincoln', -96.70, 40.81, 'town'), ('Sioux Falls', -96.73, 43.55, 'town'),
 ('Rapid City', -103.23, 44.08, 'town'), ('Casper', -106.31, 42.87, 'town'), ('Billings', -108.50, 45.78, 'town'),
 ('Pueblo', -104.61, 38.25, 'town'), ('Grand Junction', -108.55, 39.06, 'town'), ('Albuquerque', -106.65, 35.08, 'town'),
 ('Odessa', -102.37, 31.85, 'town'), ('Abilene', -99.73, 32.45, 'town'), ('Springfield', -93.29, 37.21, 'town'),
 ('Joplin', -94.51, 37.08, 'town'), ('Fort Smith', -94.40, 35.39, 'town'), ('Shreveport', -93.75, 32.53, 'town'),
 ('Cedar Rapids', -91.67, 41.98, 'town'), ('Peoria', -89.59, 40.69, 'town'), ('Evansville', -87.57, 37.97, 'town'),
 ('Fargo', -96.79, 46.88, 'town'), ('Boise', -116.20, 43.62, 'town'), ('Reno', -119.81, 39.53, 'town'),
 ('Flagstaff', -111.65, 35.20, 'town'), ('El Paso', -106.44, 31.76, 'town'), ('Waco', -97.15, 31.55, 'town'),
 ('Tulsa', -95.99, 36.15, 'town'), ('Little Rock', -92.29, 34.75, 'town'), ('Chattanooga', -85.31, 35.05, 'town'),
 ('Salina', -97.61, 38.84, 'junction'), ('North Platte', -100.77, 41.12, 'junction'), ('Cheyenne', -104.82, 41.14, 'junction'),
 ('Tucumcari', -103.72, 35.17, 'junction'), ('Big Spring', -101.48, 32.25, 'junction'), ('Kearney', -99.08, 40.70, 'junction'),
 ('Effingham', -88.54, 39.12, 'junction'), ('Texarkana', -94.05, 33.43, 'junction'), ('Rock Springs', -109.20, 41.59, 'junction'),
 ('Gallup', -108.74, 35.53, 'junction'), ('Ogallala', -101.72, 41.13, 'junction'), ('Dodge City', -100.02, 37.75, 'junction'),
]
out = {}
out['cobraNetwork'] = {
    'on': True,
    'towns': ['%s,%.2f,%.2f,%s' % t for t in TOWNS],
    'startFronts': 3, 'startDepots': 2, 'startCells': 2, 'startFunds': 400, 'startMateriel': 150,
    'headStartFrontPerMonths': 6, 'headStartCellPerMonths': 6, 'headStartDepotPerMonths': 12,
    'minKmFromPit': 300, 'nearKmFromPit': 1500,
    'crimeChance': 25, 'strikeChance': 20, 'strikeFirstMonth': 1,        # month 2 of the campaign
    'diffChance': [75, 100, 125, 150, 150],                              # beginner..superhuman, % of the base chance
    'diffFind': [75, 50, 50, 40, 35],                                    # % of the usual spotting chance for Cobra sites
    'crimePayout': 150, 'strikePayout': 80, 'cellGrowsAt': 300,
    'scannerHours': 12, 'tipoffDays': [2, 3], 'tipoffResearch': ['STR_INFORMANT_NETWORK', 'STR_SIGNALS_INTELLIGENCE_CENTER'],
    'frontCrimes': ['STR_ARMORED_CAR_AMBUSH', 'STR_COBRA_CONVOY', 'STR_COBRA_VAN_STOP'],
    'cellCrimes': ['STR_COBRA_BANK_JOB', 'STR_COBRA_VAN_STOP'],
    'crimeAlerts': {'STR_ARMORED_CAR_AMBUSH': 'ARMORED_CAR', 'STR_COBRA_CONVOY': 'CONVOY', 'STR_COBRA_VAN_STOP': 'VAN_STOP',
                    'STR_COBRA_BANK_JOB': 'BANK_ROBBERY'},
    'strikeTargets': ['POLICE,TOWN', 'GAS_STATION,GAS', 'SHOPPING_STREET,TOWN', 'BANK,BANK', 'SUBSTATION,TOWN'],
    'broadcastDays': [20, 60], 'factoryDays': [50, 60], 'factoryWarnDays': 7,
    'factoryLon': -102.08, 'factoryLat': 31.99,                         # West Texas, always
    'factoryWonResearch': 'STR_HQ_ARRIVAL_WON', 'factoryScheduleResearch': 'STR_FACTORY_REACTIVATION_DATE',
}
out['cobraSites'] = [{'type': 'STR_COBRA_CELL', 'upkeepFunds': 0, 'buildCostFunds': 0, 'revealOnRaid': 1},
                     {'type': 'STR_COBRA_TERROR_DROME_BUILDING', 'upkeepFunds': 0, 'buildCostFunds': 0}]
deps = []
cell = {'type': 'STR_COBRA_CELL_SITE', 'data': [troopers(4, 8)], 'width': 50, 'length': 40, 'height': 4,
        'terrains': ['STASH1'], 'script': 'STASH1_SCRIPT', 'shade': 8, 'alienBase': True, 'cobraSiteType': 'STR_COBRA_CELL',
        'markerName': 'STR_COBRA_CELL_SITE', 'markerIcon': 9,
        'briefing': {'palette': 0, 'title': 'STR_BRIEFING_COBRA_CELL_TITLE', 'desc': 'STR_BRIEFING_COBRA_CELL'}}
deps.append(cell)
bank = {'type': 'STR_COBRA_BANK_JOB', 'data': [troopers(5, 7), dict(officer(), customUnitType='STR_ROBBERY_LEADER')],
        'civilians': 8, 'robberExit': [[30, 2, 0], [30, 3, 0], [31, 2, 0], [31, 3, 0], [32, 2, 0], [32, 3, 0], [29, 2, 0], [29, 3, 0]],
        'robberLoot': ['STR_BANDED_CASH'], 'robberLeader': 'STR_ROBBERY_LEADER', 'quietUntilAlarm': True,
        'width': 50, 'length': 40, 'height': 3, 'terrains': ['BANK1'], 'script': 'BANK1_SCRIPT', 'shade': 0,
        'duration': [12, 24], 'markerName': 'STR_COBRA_BANK_JOB', 'markerIcon': 22, 'cobraPayoutFunds': 150, 'despawnPenalty': 20,
        'briefing': {'palette': 0, 'title': 'STR_MAP_BANK_ROBBERY', 'desc': 'STR_MAP_BANK_ROBBERY_BRIEFING'}}
deps.append(bank)
for t in ('STR_ARMORED_CAR_AMBUSH', 'STR_COBRA_CONVOY', 'STR_COBRA_VAN_STOP'):
    deps.append({'type': t, 'cobraPayoutFunds': 150, 'despawnPenalty': 20})
MAPS = {'GAS': (['VSTOWN'], 'VSTOWN_SCRIPT', 50, 40, 3, 8), 'BANK': (['BANK1'], 'BANK1_SCRIPT', 50, 40, 3, 8),
        'TOWN': (['CITYDAY'], 'CITY_SCRIPT', 100, 100, 4, 16)}
for m, (ter, scr, w, l, h, civ) in MAPS.items():
    for tier, (lo, hi, off) in enumerate([(4, 6, False), (5, 7, True), (6, 8, True)], 1):
        d = {'type': 'STR_COBRA_CELL_STRIKE_%s_%d' % (m, tier), 'data': [troopers(lo, hi)] + ([officer()] if off else []),
             'civilians': civ, 'width': w, 'length': l, 'height': h, 'terrains': ter, 'script': scr, 'shade': 0,
             'duration': [12, 24], 'markerName': 'STR_COBRA_CELL_STRIKE', 'markerIcon': 22, 'despawnPenalty': 30,   # pays the cell's purse (engine), not the region
             'briefing': {'palette': 0, 'title': 'STR_BRIEFING_CELL_STRIKE_TITLE', 'desc': 'STR_BRIEFING_CELL_STRIKE'}}
        deps.append(d)
# Piece 6: the Drome while it is being built (Cobra Commander's will). Raidable: the assault on it is the 'unfinished' version.
dr = next(d for d in sites['alienDeployments'] if d['type'] == 'STR_COBRA_TERROR_DROME_SITE')
bld = copy.deepcopy(dr)
bld['type'] = 'STR_COBRA_TERROR_DROME_BUILDING_SITE'
bld['cobraSiteType'] = 'STR_COBRA_TERROR_DROME_BUILDING'
bld['markerName'] = 'STR_COBRA_TERROR_DROME_BUILDING'
for k in ('genMission', 'genMissionFreq'):
    bld.pop(k, None)
for e in bld.get('data', []):          # a construction crew and its guards: two thirds of a finished Drome's garrison
    e['lowQty'] = max(1, e.get('lowQty', 1) * 2 // 3); e['highQty'] = max(e['lowQty'], e.get('highQty', 1) * 2 // 3)
bld['briefing'] = {'palette': 0, 'title': 'STR_BRIEFING_DROME_ASSAULT_TITLE', 'desc': 'STR_BRIEFING_DROME_ASSAULT_UNFINISHED'}
deps.append(bld)
# Piece 7: Major Bludd's hunt. The hunters' own deployments with Bludd leading them (gijoe_cobra_file.rul).
cf = yaml.safe_load(open(os.path.join(RUL, 'gijoe_cobra_file.rul')))
for src, dst in (('STR_HUNTER_AMBUSH', 'STR_BLUDD_AMBUSH'), ('STR_HUNTER_RAID', 'STR_BLUDD_RAID')):
    h = copy.deepcopy(next(d for d in cf['alienDeployments'] if d['type'] == src))
    h['type'] = dst
    lead = copy.deepcopy(h['data'][0]); lead.update({'alienRank': 4, 'customUnitType': 'STR_MAJOR_BLUDD_UNIT', 'lowQty': 1, 'highQty': 1, 'dQty': 0})
    h['data'].append(lead)
    deps.append(h)
# Piece 6: the Drome strikes the nearest Joe base, three months after it is finished (the hunters' gate map for now).
ds = copy.deepcopy(next(d for d in cf['alienDeployments'] if d['type'] == 'STR_HUNTER_RAID'))
ds['type'] = 'STR_COBRA_DROME_STRIKE'
ds['data'] = [troopers(10, 14), officer(), dict(officer(), lowQty=1, highQty=2)]
ds['duration'] = [72, 72]
ds['markerName'] = 'STR_COBRA_DROME_STRIKE'
ds['briefing'] = {'palette': 0, 'title': 'STR_BRIEFING_DROME_STRIKE_TITLE', 'desc': 'STR_BRIEFING_DROME_STRIKE'}
deps.append(ds)
out['gijoeBounties'] = {'STR_BLUDD_AMBUSH': ['STR_BLUDD_CALLING_CARD'], 'STR_BLUDD_RAID': ['STR_BLUDD_CALLING_CARD']}
out['alienDeployments'] = deps
out['alienMissions'] = [
    {'type': 'STR_COBRA_CRIME_MISSION', 'points': 0, 'objective': 3, 'raceWeights': {0: {'STR_COBRA': 100}},
     'waves': [{'ufo': 'STR_COBRA_BANK_JOB', 'count': 1, 'trajectory': 'P0', 'timer': 60, 'objective': True}]},
    {'type': 'STR_COBRA_CELL_STRIKE_MISSION', 'points': 0, 'objective': 3, 'raceWeights': {0: {'STR_COBRA': 100}},
     'waves': [{'ufo': 'STR_COBRA_CELL_STRIKE_TOWN_1', 'count': 1, 'trajectory': 'P0', 'timer': 60, 'objective': True}]},
]
out['missionScripts'] = [{'type': 'cobraFronts', 'executionOdds': 0}, {'type': 'cobraFrontOpening', 'executionOdds': 0}]
out['leads'] = [{'type': 'STR_LEAD_COBRA_CELL', 'revealSiteType': 'STR_COBRA_CELL'}]
out['events'] = [
    {'name': 'STR_EVENT_COBRA_BROADCAST', 'description': 'STR_EVENT_COBRA_BROADCAST_DESCRIPTION',
     'everyItemList': ['STR_BROADCAST_RECORDING'], 'timer': 60},
    {'name': 'STR_EVENT_FACTORY_REACTIVATED', 'description': 'STR_EVENT_FACTORY_REACTIVATED_DESCRIPTION',
     'cutscene': 'act1FactoryReopened', 'timer': 60},
    {'name': 'STR_EVENT_FACTORY_WRECKED', 'description': 'STR_CUT_FACTORY_B2', 'cutscene': 'act1FactoryWrecked', 'timer': 60},
    {'name': 'STR_EVENT_COBRA_RETREATS', 'description': 'STR_EVENT_COBRA_RETREATS_DESCRIPTION', 'timer': 60},
    {'name': 'STR_EVENT_FACTORY_WARNING', 'description': 'STR_EVENT_FACTORY_WARNING_DESCRIPTION', 'timer': 60},
]
strs = {'STR_COBRA_CELL': 'Cobra Cell', 'STR_COBRA_CELL_SITE': 'Cobra Cell', 'STR_COBRA_BANK_JOB': 'Bank Job',
        'STR_COBRA_CELL_STRIKE': 'Cell Strike', 'STR_COBRA_CRIME_MISSION': 'Cobra Crime', 'STR_COBRA_CELL_STRIKE_MISSION': 'Cell Strike',
        'STR_EVENT_FACTORY_WRECKED': 'THE GATES ARE CHAINED', 'STR_COBRA_TERROR_DROME_BUILDING': 'Terror Drome (building)', 'STR_COBRA_DROME_STRIKE': 'Drome Strike'}
out['extraStrings'] = [{'type': 'en-US', 'strings': strs}, {'type': 'en-GB', 'strings': dict(strs)}]
hdr = ('# GENERATED by build/gen_act1_layer.py: edit the script, not this file.\n'
       '# Act 1 campaign layer, pieces 1-5 (BRIEF_FOR_BUILD_Act1Layer_Part1_Answers, approved 17 Nov). Engine: Geoscape/CobraNetwork.cpp.\n')
open(os.path.join(RUL, 'zz_gijoe_act1_layer.rul'), 'w').write(hdr + yaml.safe_dump(out, sort_keys=False, width=200, default_flow_style=None))
print('zz_gijoe_act1_layer.rul:', len(deps), 'deployments,', len(TOWNS), 'towns')
