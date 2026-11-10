"""Tag every tile with the material a round has to get through.

An MCD gives a tile an armour number but no idea whether it is plywood or reinforced concrete.
The penetration matrix needs the material named, so this writes one out per terrain, indexed by
MCD record. The names.json index is the MCD record index - verified 1:1 against each file's size.

Five materials, chosen so each behaves differently under fire:
  light     glass, hedge, fences, cloth, netting      - stops almost nothing
  wood      clapboard, planking, doors, furniture     - rifle goes through, pistol sometimes
  masonry   brick, adobe, stucco, stone, rubble       - heavy weapons, rifles at close range
  concrete  military concrete, slabs, roadway         - heavy weapons only
  metal     steel plate, blast doors, vehicles, grate - heavy and laser; armour-dependent

Anything the rules do not name is reported rather than guessed.

usage: tag_materials.py  [--write <out.json>]
"""
import json, re, sys

SETS = {'natiles': 'NAMER', 'cobratiles': 'COBRA', 'wildtiles': 'NAWILD', 'mtntiles': 'NAMTN'}

# first rule that matches wins, so order matters
RULES = [
    # --- openings and flimsy things, before the walls they sit in
    ('light',    r'^(glass|glassdoor|hedge|picket|chain|rail|razor|camonet|cell|banner|drift|flowers|sage|corn|bush)'),
    ('light',    r'^(win[WBYK]|adobewin|cabinwin|slit)'),          # a window is its glass
    # --- timber
    ('wood',     r'^(wall[WBY]|door[WBY]|dooropen[WBY]|barn|barndoor|shop|shopR)'),
    ('wood',     r'^(cabin|cabinarch|minewall|mineframe|wood_floor|pallet|crate_wood|weaponrack)'),
    ('wood',     r'^(sofa|table|bed|counter|shelf|desk|bench|stopsign|mailbox|filing|maptable|deskpc)'),
    ('wood',     r'^(oak|maple|pine|mpine|mpine_snow|aspen|deadtree|joshua|cactus|prickly|haybale)'),
    ('wood',     r'^(roof_|gable|barnroof|stairs|parapet)'),        # shingle over rafters
    # --- brick, adobe, stone and their ruins
    ('masonry',  r'^(wallK|doorK|dooropenK|adobe|adobearch|rubble|rubble_wall|wrubble|mrubble|crubble)'),
    ('masonry',  r'^ramp_'),
    ('masonry',  r'^(boulder|mboulder|rocksmall|mesa|snowrock|cliff|cliffsnow|rock|rock2|scree|screepile)'),
    ('masonry',  r'^(lino|carpet|ccarpet|ctile|sidewalk|crosswalk|parking|gravel)'),
    # --- poured concrete and roadway
    ('concrete', r'^(bunker|conc|concroof|emb[0-3]|asphalt|road_|tar_roof|adoberoof|sandwall|sandbags|hazard)'),
    # --- steel
    ('metal',    r'^(blast|blastopen|corr|corrsign|roll|rollopen|plate|grate|metalroof|mast|dish)'),
    ('metal',    r'^(car_|jeep_|forklift|minecart|barrel_|console|server|generator|searchlight|flagpole|acunit|dumpster|hydrant|streetlight|pump|fridge|tv|crate_cobra|crate_stack|trashcan)'),
    ('metal',    r'^rail$'),
    # --- ground, which nothing penetrates because nothing shoots through the floor
    ('masonry',  r'^(grass|grass2|lawn|dirt|plowed|scorched|sand|sand2|cracked|snow|snow2|ice|snowcap|trail|alpgrass)'),
]

# One name, two materials, depending on the set it is in: 'rail' is a split-rail fence in the
# farm set and a mine rail in the mountain set. Terrain-specific overrides beat the rules.
OVERRIDE = {('NAMTN', 'rail'): 'metal'}

compiled = [(m, re.compile(p)) for m, p in RULES]

def material(name, terrain=None):
    if (terrain, name) in OVERRIDE:
        return OVERRIDE[(terrain, name)]
    for m, rx in compiled:
        if rx.match(name):
            return m
    return None

out, missing, counts = {}, [], {}
for folder, terrain in SETS.items():
    names = json.load(open(f'{folder}/names.json'))
    mats = []
    for i, n in enumerate(names):
        m = material(n, terrain)
        if m is None:
            missing.append(f'{terrain}[{i}] {n}')
            m = 'masonry'                    # recorded below, not silently accepted
        mats.append(m)
        counts[m] = counts.get(m, 0) + 1
    out[terrain] = mats

total = sum(counts.values())
print('tagged %d tiles across %d terrains' % (total, len(SETS)))
for m in ('light', 'wood', 'masonry', 'concrete', 'metal'):
    print('   %-9s %3d' % (m, counts.get(m, 0)))
if missing:
    print('\nNO RULE MATCHED - defaulted to masonry, needs a decision:')
    for x in missing: print('   ', x)
else:
    print('\nevery tile matched a rule')

if '--write' in sys.argv:
    p = sys.argv[sys.argv.index('--write') + 1]
    json.dump(out, open(p, 'w'), indent=1)
    print('\nwrote', p)
