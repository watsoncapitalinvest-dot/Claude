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

SETS = {'natiles': 'NAMER', 'cobratiles': 'COBRA', 'wildtiles': 'NAWILD', 'mtntiles': 'NAMTN',
        'tiles': 'GIJOE'}

# first rule that matches wins, so order matters
RULES = [
    # --- openings and flimsy things, before the walls they sit in
    ('light',    r'^(glass|glassdoor|hedge|picket|chain|rail|razor|camonet|cell|banner|drift|flowers|sage|corn|bush)'),
    ('light',    r'^(win[WBYK]|adobewin|cabinwin|slit)'),          # a window is its glass
    # --- the Joe and Cobra base set, which is steel before it is anything else.
    # Read off the art rather than off the names: both sides' walls are ribbed panel, Cobra's
    # doors are roller shutters and the Joes' are timber, and both roof decks are plate. This
    # block sits above the generic ^roof_ rule deliberately - roof_joe and roof_cobra were
    # matching it and coming out as shingle over rafters, which is a flat steel deck tagged as
    # a barn roof. Nothing errors when that happens; a rifle round just goes through a military
    # roof like it was a farmhouse.
    ('wood',     r'^joe_door'),
    ('metal',    r'^(joe_|cobra_|metalfloor$|barrels$)'),
    # Sandbags stop rifle rounds, which is the whole reason anyone stacks them. They were
    # landing on masonry by accident - the ground rule's 'sand' prefix matched 'sandbag_' - so
    # this says it on purpose, and says concrete, which is the slot that absorbs.
    ('concrete', r'^sandbag_'),
    # --- timber
    ('wood',     r'^(wall[WBY]|door[WBY]|dooropen[WBY]|barn|barndoor|shop|shopR)'),
    ('wood',     r'^(tree|crate)$'),               # the bare ones; crate_cobra is steel, below
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

# The three Joe craft have no tile names to match on, and they do not need any. build_craftmap.py
# and build_heli.py generate them by voxelising the aircraft's own mesh: index 0 is the landing
# pad the craft sits on, and every index after it is a cell of chassis. There is no tile in these
# sets that is not part of an aeroplane, so "metal" is read off how the file is built rather than
# chosen. Cells that hold only a rotor blade are written with no collision at all, so a shot never
# meets one and what they are tagged cannot matter.
#
# The one thing the pipeline cannot tell apart is a canopy from a fuselage panel - it samples the
# chassis mesh without reading its materials - so cockpit glass is steel here. Visible as a
# cockpit that stops bullets, overridable in one line now the tags are a ruleset.
CRAFT = {'JOEDEFI': 160, 'JOEHELO': 45, 'JOEPHANT': 45}

# BARN and CULTIVAT came with X-COM, so there is no name list to match on. These were read off
# the art, one tile at a time, from a contact sheet with the index drawn on each tile - the
# rendering is in build/render_tileset.py and takes seconds to redo if any of this looks wrong
# on the field. Indexed by MCD index; anything not listed falls to DEFAULT.
#
# The one genuine uncertainty is BARN 10-14. They are pale tan with a repeating chevron, which
# is either stacked straw bales or adobe brick, and the two want opposite materials. Called
# straw because tiles 3 and 4 are unmistakably hay bales in exactly that palette and texture,
# and 12 and 13 are the same wall with a gap in it rather than a built window. If a hay wall
# turns out to stop nothing when it should, this is the line.
VANILLA = {
    'BARN': dict(
        [(i, 'wood') for i in (0, 1, 2, 5, 6, 7, 8, 9, 15, 16, 17, 18, 20, 21, 22, 24)] +
        [(i, 'light') for i in (3, 4, 10, 11, 12, 13, 14, 23)] +
        [(i, 'masonry') for i in (19, 25, 26, 27, 28)]),
    'CULTIVAT': dict(
        [(i, 'masonry') for i in (0, 1, 2, 3, 6, 7, 10, 14, 15, 20, 31, 32, 35)] +
        [(i, 'light') for i in (4, 5, 8, 11, 16, 17, 18, 19, 21, 22, 23, 24, 27, 28, 33, 34, 36)] +
        [(i, 'wood') for i in (9, 12, 13, 25, 26, 29, 30)]),
}
VANILLA_LEN = {'BARN': 29, 'CULTIVAT': 37}

out, missing, counts = {}, [], {}
for terrain, n in CRAFT.items():
    mats = ['concrete'] + ['metal'] * (n - 1)
    for m in mats:
        counts[m] = counts.get(m, 0) + 1
    out[terrain] = mats

for terrain, n in VANILLA_LEN.items():
    table = VANILLA[terrain]
    gaps = [i for i in range(n) if i not in table]
    if gaps:
        missing.extend('%s[%d] not read off the art' % (terrain, i) for i in gaps)
    mats = [table.get(i, 'masonry') for i in range(n)]
    for m in mats:
        counts[m] = counts.get(m, 0) + 1
    out[terrain] = mats

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
print('tagged %d tiles across %d terrains' % (total, len(out)))
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
