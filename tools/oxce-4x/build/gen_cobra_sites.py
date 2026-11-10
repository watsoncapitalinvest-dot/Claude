"""Generate the eight Cobra site deployments, and the missions that place them.

Derived from the deployment that already works rather than written out eight times. The mod's
Cobra raid runs on vanilla's STR_TERROR_MISSION with terrains overridden to [] so the globe
texture picks North American ground; every one of these is that same entry with a new name, a
marker, the site type it carries, and alienBase set.

Copying the garrison wholesale is the point. The data block - seven unit entries with their
weapon sets - is the thing a hand-written deployment gets subtly wrong, and a site with no data
has no defenders at all.

alienBase only affects New Battle and the statistics screens; it does not touch map generation,
which comes from the terrain's own script. So the map these raid is the map the Cobra raid
already produces, and that is what makes generating them from it safe.

usage: gen_cobra_sites.py <vanilla alienDeployments.rul> <vanilla alienMissions.rul>
           <gijoe_cobra_economy.rul> <out.rul>
"""
import sys, yaml, collections

VANILLA_DEP, VANILLA_MIS, ECONOMY, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

# site type -> (short name for the deployment, how often Cobra tries to place one)
# The weights are John's to tune like every other number here. They are ordered so the two
# earners are the most common thing Cobra builds, because a network that cannot pay for itself
# never gets off the ground.
# the third column is executionOdds, the fourth the build cost in funds; the cost must match
# gijoe_cobra_economy.rul, so it is read from there rather than repeated here
BOOTSTRAP = 'STR_COBRA_FRONT_COMPANY'   # the one site Cobra can always build
# Where Cobra may build. Set to None for worldwide; the engine's own region table then
# chooses and spawnAlienBase finds land on its own. Locked to North America for now because
# that is the only region with G.I. Joe terrain - a raid anywhere else lands on an X-COM map.
# Nothing else depends on this: funds are already pooled across regions and the state model is
# keyed by region, so widening it later is this one line.
REGION_LOCK = 'STR_NORTH_AMERICA'

BOOTSTRAP_MAX = 6                        # how many, before it must pay its way
ODDS_SCALE = 2.2                         # how hard Cobra pushes; see the note below

SITES = [
    ('STR_COBRA_FRONT_COMPANY',     'FRONT_COMPANY',     30),
    ('STR_COBRA_FACTORY',           'FACTORY',           20),
    ('STR_COBRA_TRAINING_CAMP',     'TRAINING_CAMP',     12),
    ('STR_COBRA_DEPOT',             'DEPOT',             12),
    ('STR_COBRA_RESEARCH_LAB',      'RESEARCH_LAB',       8),
    ('STR_COBRA_TERROR_DROME',      'TERROR_DROME',       6),
    ('STR_COBRA_BROADCAST_STATION', 'BROADCAST_STATION',  8),
    ('STR_COBRA_HIDDEN_HQ',         'HIDDEN_HQ',          4),
]


def load_entry(path, key, name):
    for e in yaml.safe_load(open(path))[key]:
        if e.get('type') == name:
            return e
    raise SystemExit('no %s in %s' % (name, path))


terror = load_entry(VANILLA_DEP, 'alienDeployments', 'STR_TERROR_MISSION')
base_mission = load_entry(VANILLA_MIS, 'alienMissions', 'STR_ALIEN_BASE')

deployments, missions, scripts = [], [], []
costs = {}
for e in yaml.safe_load(open(ECONOMY))['cobraSites']:
    costs[e['type']] = e.get('buildCostFunds', 0)

for site_type, short, weight in SITES:
    cost = costs.get(site_type, 0)
    dep_name = 'STR_COBRA_%s_SITE' % short
    dep = dict(terror)                       # the working garrison, map size and briefing
    dep['type'] = dep_name
    dep['terrains'] = []                     # let the globe texture choose North American ground
    dep['alienBase'] = True
    dep['cobraSiteType'] = site_type
    # its own marker, so the globe says which kind of site it is rather than 'Cobra Site'
    # eight times. The site type doubles as the marker name, so one language entry serves both.
    dep['markerName'] = site_type
    dep['markerIcon'] = 7
    # a site sits there until it is raided, unlike a terror mission that packs up and leaves
    dep.pop('duration', None)
    dep.pop('despawnPenalty', None)
    deployments.append(dep)

    mis_name = 'STR_COBRA_BUILD_%s' % short
    mis = dict(base_mission)
    mis['type'] = mis_name
    mis['siteType'] = dep_name               # this is what decides the deployment the base gets
    mis['points'] = 20
    # One approach wave instead of vanilla's five. Cobra is establishing a site, not running a
    # year-long campaign to build one, and five waves means five chances to be shot down first.
    mis['waves'] = [{'ufo': 'STR_SMALL_SCOUT', 'count': 1, 'trajectory': 'P5', 'timer': 1000}]
    missions.append(mis)

    script = {
        'type': 'cobraBuild%s' % short.title().replace('_', ''),
        'missionWeights': {0: {mis_name: 100}},
        # Cobra builds only what it can pay for, which is the decision John made: sites are
        # gone when raided and rebuilt when affordable. The counter is the economy's own
        # regional funds, mirrored into the map the scripts already gate on, so this needs
        # no scheduling code - which was the whole point of mirroring them there.
        'firstMonth': 0,
        'executionOdds': min(100, int(round(weight * ODDS_SCALE))),
        'useTable': False,
        'startDelay': 60,
    }
    if REGION_LOCK:
        script['regionWeights'] = {0: {REGION_LOCK: 100}}
    if site_type == BOOTSTRAP:
        # The earner is not gated on funds, or nothing is ever built: Cobra starts with
        # nothing, so nothing is affordable, so it never earns. Capped by maxRuns instead,
        # which is a ruleset number rather than a seed value hidden in the engine. Cobra's
        # front companies are its bootstrap; everything else it has to pay for.
        script['varName'] = 'cobraFrontCompanies'
        script['maxRuns'] = BOOTSTRAP_MAX
    else:
        script['missionVarName'] = 'COBRA_FUNDS_TOTAL'
        script['counterMin'] = cost
    scripts.append(script)

out = collections.OrderedDict()
out['alienDeployments'] = deployments
out['alienMissions'] = missions
out['missionScripts'] = scripts

header = '''# GENERATED by scripts/gen_cobra_sites.py - do not hand-edit.
#
# Eight Cobra site deployments, the missions that place them, and the scripts that run those.
# Every deployment is vanilla's STR_TERROR_MISSION with terrains cleared, a marker, the site
# type it carries and alienBase set, so the garrison and the map are the ones the mod's Cobra
# raid already produces.
#
# The economics live in gijoe_cobra_economy.rul, keyed by cobraSiteType. The link runs one way:
# the deployment names the site type, the site rule prices it.
#
# executionOdds is how hard Cobra tries to place each kind, and like every number in the
# economy it is John's to tune. The two earners are weighted highest because a network that
# cannot pay for itself never gets started.
'''
with open(OUT, 'w') as f:
    f.write(header)
    f.write(yaml.dump(dict(out), default_flow_style=False, sort_keys=False))

print('wrote %s: %d deployments, %d missions, %d scripts'
      % (OUT, len(deployments), len(missions), len(scripts)))
