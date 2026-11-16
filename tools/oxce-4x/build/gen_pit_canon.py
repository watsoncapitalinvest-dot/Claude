#!/usr/bin/env python3
"""The Pit's base-defence battle map: MAPS' canon Pit (BRIEF_FOR_BUILD_PitBase, PIT_MODULES_v1).

    python3 build/gen_pit_canon.py <unpacked pit_canon.zip>

MAPS draws the map (46 x 32 x 7, .MAP2: Utility at the bottom, a double-height layer above it, Quarters,
Training, Operations, Staging, and the upper walls of the garage on top). BUILD does three things to it:

1. pads it to 50 x 40 (map blocks must be a multiple of 10 on a side; the pad is empty ground past the block);
2. sets the start points: MAPS' 47 nodes are all rank 0, which lets Cobra and the Joes start anywhere. Staging
   (the garage under the vehicle elevator) and the alternate escape tunnel off Utility become Cobra's ways in;
   every other node is a Joe's, and Joe start points are added through Operations, Training, Quarters and
   Utility so a full barracks has somewhere to stand. The stair and shaft nodes are linked level to level so
   Cobra's patrols can go down;
3. writes gijoe_pit_canon.rul: terrain, map script, the STR_PIT_DEFENSE deployment (its Cobra force is copied
   from STR_BASE_DEFENSE in gijoe_cobra_kit.rul, so the calendar's kit ladder still holds: rerun this after
   gen_cobra_kit.py) and pitBattle: the module slots the engine fills at battle start from what is built.

The map, routes and the PHATCH / PITB terrain are traced off Fred Broca's Pit I maps, so they stay out of the
public repo (gitignored) and reach John by zip. The ruleset is mechanics and is committed; the engine only uses
the canon Pit when MAPS/PITCANON.MAP2 is present, and falls back to the old room-by-room map otherwise.
"""
import json, os, random, shutil, struct, sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.join(HERE, '..', 'mod')
PX, PY = 50, 40                     # padded size

# Slot groups (pit_canon_v4, built to CAST's PIT_BUILD_SPEC_v1). A group is a set of rooms on the map and the
# facilities that can stand in them, in the order they claim slots. Each built facility takes the next slot and
# that slot gets the facility's room fit-out (its module) copied from MAPS' showcase map (PITSHOW, every slot
# filled); a slot nobody has built is bare. `accept` = which of the showcase's modules mean that facility: a slot
# whose showcase module is accepted is copied from the same slot (an exact fit, door side and all); otherwise the
# first showcase slot holding an accepted module at the same size and turn. A fit-out copied from ANOTHER slot
# brings only floors and objects (that slot's walls are not this one's); from the same slot it brings all four. Rooms with no facility in the game
# yet (Pentagon Hook-up, Briefing, Hologram, Situation Analysis, Archives, Computer Banks, MG nests, Ammo Dump,
# Backup Data Vault) stay as the Day 1 map draws them.
SLOT_GROUPS = [
    {'slots': ['ops_sit'], 'facilities': ['STR_ACCESS_LIFT'], 'accept': {'STR_ACCESS_LIFT': ['Command Center']}},
    {'slots': ['ops_comms', 'ops_g1', 'ops_g2'],
     'facilities': ['STR_HYPER_WAVE_DECODER', 'STR_JOE_COMMS_CENTER', 'STR_COMPUTER_STATION'],
     'accept': {'STR_HYPER_WAVE_DECODER': ['SIGINT'], 'STR_JOE_COMMS_CENTER': ['Comms Room'],
                'STR_COMPUTER_STATION': ['Computer Station']}},
    {'slots': ['trn_ex1', 'trn_ex2', 'trn_rng1', 'trn_rng2'], 'facilities': ['STR_TRAINING_ROOM'],
     'accept': {'STR_TRAINING_ROOM': ['Training Room', 'Rifle Range']}},
    {'slots': ['trn_g1', 'trn_g2'], 'facilities': ['STR_RECRUITING_OFFICE'],
     'accept': {'STR_RECRUITING_OFFICE': ['Recruiting Office']}},
    {'slots': ['qtr_nco1', 'qtr_nco2', 'qtr_nco3', 'qtr_nco4', 'qtr_off1', 'qtr_off2', 'qtr_off3', 'qtr_off4'],
     'facilities': ['STR_LIVING_QUARTERS'],
     'accept': {'STR_LIVING_QUARTERS': ['Bunks', 'Barracks', 'Living Quarters', 'Suites']}},
    {'slots': ['qtr_rec'], 'facilities': ['STR_INFIRMARY_ROOM'], 'accept': {'STR_INFIRMARY_ROOM': ['Infirmary', 'Infirmary Cot']}},
    {'slots': ['utl_cls1', 'utl_cls2', 'utl_cls3', 'utl_cls4'],
     'facilities': ['STR_LABORATORY', 'STR_PSIONIC_LABORATORY', 'STR_MIND_SHIELD'],
     'accept': {'STR_LABORATORY': ['lab_bench'], 'STR_PSIONIC_LABORATORY': ['Brainwave Lab'], 'STR_MIND_SHIELD': ['Jammer']}},
    {'slots': ['utl_hold'], 'facilities': ['STR_ALIEN_CONTAINMENT'],
     'accept': {'STR_ALIEN_CONTAINMENT': ['Holding Block', 'Detention Block']}},
    {'slots': ['stg_s1', 'stg_s2'], 'facilities': ['STR_WORKSHOP'], 'accept': {'STR_WORKSHOP': ['Workbench']}},
]
NAMES = {'STR_ACCESS_LIFT': 'Command Center', 'STR_HYPER_WAVE_DECODER': 'Signals Intelligence Center',
         'STR_JOE_COMMS_CENTER': 'Comms Room', 'STR_COMPUTER_STATION': 'Computer Station',
         'STR_TRAINING_ROOM': 'Training Room', 'STR_RECRUITING_OFFICE': 'Recruiting Office',
         'STR_LIVING_QUARTERS': 'Barracks', 'STR_INFIRMARY_ROOM': 'Infirmary', 'STR_LABORATORY': 'Lab Bench',
         'STR_PSIONIC_LABORATORY': 'Brainwave Laboratory', 'STR_MIND_SHIELD': 'Jammer',
         'STR_ALIEN_CONTAINMENT': 'Detention Block', 'STR_WORKSHOP': 'Workbench'}
PRIVATE_SETS = ('PIT', 'PHATCH', 'PITB', 'PITART', 'PITFLR', 'PITC', 'PITROT',
                'PITM', 'PITEXIT', 'PITDEC', 'PITVEH', 'PITTOMA', 'PITTUG', 'PITMECH')  # v29: ROSTER renders, John's kits, unknown-licence props: private


def load_map(p):
    d = open(p, 'rb').read()
    Y, X, Z = d[0], d[1], d[2]
    v = list(struct.unpack('<%dH' % ((len(d) - 3) // 2), d[3:]))
    assert len(v) == X * Y * Z * 4, (len(v), X, Y, Z)
    return X, Y, Z, v


def main(root):
    os.makedirs(os.path.join(MOD, 'MAPS'), exist_ok=True)
    src = os.path.join(root, 'dist_pitcanon_day1')
    show = os.path.join(root, 'dist_pitcanon_showcase')
    X, Y, Z, v = load_map(os.path.join(src, 'MAPS', 'PITCANON.MAP2'))
    SX, SY, SZ, _ = load_map(os.path.join(show, 'MAPS', 'PITSHOW.MAP2'))
    assert (SX, SY, SZ) == (X, Y, Z)
    shutil.copy(os.path.join(show, 'MAPS', 'PITSHOW.MAP2'), os.path.join(MOD, 'MAPS', 'PITSHOW.MAP2'))
    a = json.load(open(os.path.join(show, 'PITSHOW_terrain.json')))['mapDataSets']
    assert a == json.load(open(os.path.join(src, 'PITCANON_terrain.json')))['mapDataSets'], "showcase must share the sets"
    assert X <= PX and Y <= PY, (X, Y)

    def part(layer, x, y, k):
        return v[((layer * Y + y) * X + x) * 4 + k]

    # 1. pad
    out = []
    for layer in range(Z):
        for y in range(PY):
            for x in range(PX):
                out += [part(layer, x, y, k) for k in range(4)] if (x < X and y < Y) else [0, 0, 0, 0]
    os.makedirs(os.path.join(MOD, 'MAPS'), exist_ok=True)
    with open(os.path.join(MOD, 'MAPS', 'PITCANON.MAP2'), 'wb') as f:
        f.write(bytes([PY, PX, Z]) + struct.pack('<%dH' % len(out), *out))

    # 2. routes. RMP z counts from the top layer (file order).
    rmp = open(os.path.join(src, 'ROUTES', 'PITCANON.RMP'), 'rb').read()
    nodes = [bytearray(rmp[i:i + 24]) for i in range(0, len(rmp), 24)]
    floors = sorted({n[2] for n in nodes})          # the five levels that have nodes
    staging, utility = floors[0], floors[-1]
    ESCAPE = [(44, 8), (44, 7), (43, 8)]           # the alternate escape tunnel off Utility (x 43-44, y 6-9)
    cobra_ranks = [2, 2, 4, 2, 5, 2, 7, 3, 2, 8]   # soldier-heavy, a leader at the elevator
    for i, n in enumerate(nodes):
        n[20] = cobra_ranks[i % len(cobra_ranks)] if n[2] == staging else 1   # 1 = NR_XCOM, a Joe's
        n[23] = 5

    def walkable(layer, x, y):
        return part(layer, x, y, 0) and not part(layer, x, y, 3) and not part(layer, x, y, 1) and not part(layer, x, y, 2)

    taken = {(n[1], n[0], n[2]) for n in nodes}

    def add(x, y, layer, rank):
        if (x, y, layer) in taken:
            return False
        taken.add((x, y, layer))
        b = bytearray(24)
        b[0], b[1], b[2] = y, x, layer
        for j in range(5):
            b[4 + j * 3] = 255
        b[20], b[23] = rank, 5
        nodes.append(b)
        return True

    for (x, y) in ESCAPE:
        if walkable(utility, x, y):
            add(x, y, utility, 2)
    rnd = random.Random(1515)
    POOL = (33, 40, 12, 27)                         # Training's pool water: nobody starts in it
    for layer, rank, want in [(staging, None, 22)] + [(f, 1, 14) for f in floors[1:]]:
        cells = [(x, y) for y in range(8, Y) for x in range(1, X) if walkable(layer, x, y)
                 and not (layer == floors[2] and POOL[0] <= x <= POOL[1] and POOL[2] <= y <= POOL[3])]
        rnd.shuffle(cells)
        got = 0
        for (x, y) in cells:
            if got >= want:
                break
            if any(abs(x - a) + abs(y - b) < 3 for (a, b, l) in taken if l == layer):
                continue
            if add(x, y, layer, rank if rank else cobra_ranks[got % len(cobra_ranks)]):
                got += 1

    # link the stairwell (37, 9) and the escape shaft (8, 6) nodes level to level
    def free_link(n, target):
        for j in range(5):
            if n[4 + j * 3] == 255:
                n[4 + j * 3] = target
                return

    for (sx, sy) in [(37, 9), (8, 6)]:
        col = sorted([i for i, n in enumerate(nodes) if (n[1], n[0]) == (sx, sy)], key=lambda i: nodes[i][2])
        for a, b in zip(col, col[1:]):
            free_link(nodes[a], b)
            free_link(nodes[b], a)
    assert len(nodes) <= 250
    os.makedirs(os.path.join(MOD, 'ROUTES'), exist_ok=True)
    with open(os.path.join(MOD, 'ROUTES', 'PITCANON.RMP'), 'wb') as f:
        f.write(b''.join(bytes(n) for n in nodes))

    # terrain: PIT and LABSCI are already in the mod (same files); PHATCH and PITB are new
    for f in os.listdir(os.path.join(src, 'TERRAIN')):
        dst = os.path.join(MOD, 'TERRAIN', f)
        if not os.path.exists(dst) or open(dst, 'rb').read() != open(os.path.join(src, 'TERRAIN', f), 'rb').read():
            if f.split('.')[0].split('_')[0] not in PRIVATE_SETS:
                raise SystemExit('refusing to overwrite a terrain file another map uses: ' + f)
            shutil.copy(os.path.join(src, 'TERRAIN', f), dst)

    # 3. ruleset
    sets = json.load(open(os.path.join(src, 'PITCANON_terrain.json')))['mapDataSets']
    slots = {s['id']: s for lv in json.load(open(os.path.join(src, 'PITCANON_slots.json')))['slots'].values() for s in lv}
    kit = yaml.safe_load(open(os.path.join(MOD, 'Ruleset', 'gijoe_cobra_kit.rul')))
    base = next(d for d in kit['alienDeployments'] if d['type'] == 'STR_BASE_DEFENSE')

    def rect(sid):
        s = slots[sid]
        xs = [t[0] for t in s['tiles']]
        ys = [t[1] for t in s['tiles']]
        return {'id': sid, 'z': s['level_z'], 'x': min(xs), 'y': min(ys),
                'w': max(xs) - min(xs) + 1, 'h': max(ys) - min(ys) + 1}

    sj = json.load(open(os.path.join(src, 'PITCANON_slots.json')))
    day1 = sj['installed_day1']
    showmod = json.load(open(os.path.join(show, 'PITCANON_slots.json')))['installed_day1']
    shape = lambda sid: (slots[sid]['size'], bool(slots[sid].get('rotated')), rect(sid)['w'], rect(sid)['h'])
    groups, report = [], []
    for g in SLOT_GROUPS:
        frm = {}
        for sid in g['slots']:
            # bare: this slot as Day 1 draws it if it is empty there, else another Day 1 slot of the same shape
            if sid not in day1:
                frm['|' + sid] = 'D:' + sid
            else:
                order = g['slots'] + [s for s in slots if slots[s]['level_z'] == slots[sid]['level_z']] + list(slots)
                alt = [s for s in order if s not in day1 and shape(s) == shape(sid)]
                if alt: frm['|' + sid] = 'D:' + alt[0]
                else: report.append('%s has no bare slot of its shape on Day 1' % sid)
            for fac in g['facilities']:
                ok = g['accept'][fac]
                if showmod.get(sid) in ok:
                    frm[fac + '|' + sid] = 'S:' + sid
                else:
                    order = g['slots'] + list(slots)
                    alt = [s for s in order if showmod.get(s) in ok and shape(s) == shape(sid)]
                    if alt: frm[fac + '|' + sid] = 'S:' + alt[0]
                    else: report.append('%s has no %s fit-out of its shape' % (sid, NAMES[fac]))
        groups.append({'facilities': g['facilities'], 'slots': g['slots'], 'from': frm})
    allslots = [rect(s) for s in slots]

    # 4. FREE PLACEMENT (PIT_FLOORS_v1 s.1 v2; John 16 Nov "build it now"): each floor's sheet, the modules and Day 1.
    # Until MAPS delivers permanent-only floors and a module library with footprints (NOTE_FOR_MAPS_PitFreePlacementModules),
    # the sheet is read off the Day 1 map with the old slots' furniture taken out, and each module is the showcase
    # fit-out of the slot that held it (its size; a turned copy where the showcase has it in a turned slot).
    FLOOR_OF = {'stg': 1, 'ops': 2, 'trn': 3, 'qtr': 4, 'utl': 5}
    zof = {}
    for sid, s in slots.items():
        zof.setdefault(FLOOR_OF.get(sid[:3]), s['level_z'])
    bays = [s for s in slots if s.startswith('stg_bay')]
    open_slots = [s for s in slots if s not in bays]
    floors_out = []
    for fl, z in sorted((k, v) for k, v in zof.items() if k):
        layer = Z - 1 - z
        inslot = set()
        for sid in open_slots:
            if slots[sid]['level_z'] == z:
                r = rect(sid)
                inslot |= {(r['x'] + i, r['y'] + j) for i in range(r['w']) for j in range(r['h'])}
        inbay = set()
        for sid in bays:
            if slots[sid]['level_z'] == z:
                r = rect(sid)
                inbay |= {(r['x'] + i, r['y'] + j) for i in range(r['w']) for j in range(r['h'])}
        rows = []
        for y in range(PY):
            row = ''
            for x in range(PX):
                m = 0
                if x < X and y < Y:
                    if part(layer, x, y, 0): m |= 1
                    if part(layer, x, y, 1): m |= 2
                    if part(layer, x, y, 2): m |= 4
                    if (part(layer, x, y, 3) and (x, y) not in inslot) or (x, y) in inbay: m |= 8
                row += '%x' % m
            rows.append(row)
        floors_out.append({'floor': fl, 'z': z, 'mask': ''.join(rows)})
    modules_out, day1_out = [], {}
    for g in SLOT_GROUPS:
        for fac in g['facilities']:
            if any(m['facility'] == fac for m in modules_out): continue
            names = g['accept'][fac]
            name = next((n for n in names if n in showmod.values()), None)
            if not name:
                report.append('no showcase fit-out for %s: it places as an empty room' % NAMES[fac]); continue
            held = [s for s in slots if showmod.get(s) == name]
            held.sort(key=lambda s: bool(slots[s].get('rotated')))
            b = rect(held[0])
            mod = {'facility': fac, 'name': NAMES[fac], 'w': b['w'], 'h': b['h'], 'lib': [b['x'], b['y'], b['z']]}
            tn = [s for s in held if (rect(s)['w'], rect(s)['h']) == (b['h'], b['w']) and b['w'] != b['h']]
            if tn:
                r = rect(tn[0]); mod['turned'] = [r['x'], r['y'], r['z']]
            # where an old save's rooms (and New Battle's) go first: the canon rooms of their family that fit them
            pref = []
            for sid in g['slots']:
                r = rect(sid)
                if (r['w'], r['h']) == (mod['w'], mod['h']): pref.append([r['x'], r['y'], 0])
                elif 'turned' in mod and (r['w'], r['h']) == (mod['h'], mod['w']): pref.append([r['x'], r['y'], 1])
            if pref: mod['prefer'] = pref
            modules_out.append(mod)
    hangar_spots = [[rect(s)['x'], rect(s)['y']] for s in sorted(bays)]
    if hangar_spots:
        modules_out.append({'facility': 'STR_HANGAR', 'name': 'Motor Pool Bay', 'w': rect(bays[0])['w'], 'h': rect(bays[0])['h'], 'spots': hangar_spots})
    for sid, name in day1.items():
        r = rect(sid)
        if sid in bays:
            day1_out['STR_HANGAR'] = [r['x'], r['y'], 0]; continue
        for g in SLOT_GROUPS:
            for fac in g['facilities']:
                if name in g['accept'][fac] and fac not in day1_out:
                    m = next((m for m in modules_out if m['facility'] == fac), None)
                    turned = 1 if m and (m['w'], m['h']) != (r['w'], r['h']) else 0
                    day1_out[fac] = [r['x'], r['y'], turned]
    clear = [[rect(s)['z'], rect(s)['x'], rect(s)['y'], rect(s)['w'], rect(s)['h']] for s in open_slots]
    pit_place = {'w': PX, 'h': PY, 'floors': floors_out, 'modules': modules_out, 'day1': day1_out, 'clear': clear}
    rul = {
        'terrains': [{'name': 'PITCANON', 'mapDataSets': sets,
                      'mapBlocks': [{'name': 'PITCANON', 'width': PX, 'length': PY, 'height': Z}]}],
        'mapScripts': [{'type': 'PITCANON_SCRIPT', 'commands': [{'type': 'addBlock', 'size': [PX // 10, PY // 10]}]}],
        'alienDeployments': [{'type': 'STR_PIT_DEFENSE', 'data': base['data'],
                              'width': PX, 'length': PY, 'height': Z,
                              'terrains': ['PITCANON'], 'script': 'PITCANON_SCRIPT', 'shade': 0,
                              'briefing': {'palette': 0, 'title': 'STR_PIT_DEFENSE_TITLE', 'desc': 'STR_PIT_DEFENSE_BRIEFING'}}],
        'pitBattle': {'deployment': 'STR_PIT_DEFENSE', 'map': 'PITCANON', 'library': 'PITSHOW', 'slots': allslots, 'groups': groups},
        'pitPlace': pit_place,
        'extraStrings': [{'type': 'en-US', 'strings': {
            'STR_PIT_DEFENSE': 'The Pit (base defence)',
            'STR_PIT_DEFENSE_TITLE': 'THE PIT IS UNDER ATTACK',
            'STR_PIT_SLOTS_FULL': 'No room left for it: every room on that floor that can hold it is in use.',
            'STR_PIT_DOES_NOT_FIT': "It doesn't fit there.",
            'STR_PIT_SEALS_OFF': 'That would seal off part of the floor.',
            'STR_PIT_BAY_ONLY': 'A Motor Pool Bay goes in one of the garage bays.',
            'STR_PIT_FITS': 'It fits here. Click to build.',
            'STR_PIT_PLACE_HOW': 'Drop it where it fits on its floor. Right-click or R turns it.',
            'STR_PIT_PLACE_HOW_FIXED': 'Drop it where it fits on its floor.',
            'STR_PIT_SURFACE_NOTE': 'Surface defences are installed in their hiding places, not placed.',
            'STR_DAYS_SHORT': 'days',
            'STR_PIT_DEFENSE_BRIEFING': "Cobra has found the Pit. They are coming down the vehicle elevator into the garage on Staging, and through the old escape tunnel under Utility.{NEWLINE}Hold every level. Nobody gets past Operations."}}],
    }
    hdr = ('# GENERATED by build/gen_pit_canon.py from MAPS\' pit_canon.zip: do not edit by hand.\n'
           '# The Pit\'s base-defence battle (BRIEF_FOR_BUILD_PitBase, PIT_MODULES_v1). The map itself is private\n'
           '# (gitignored, zip only); without MAPS/PITCANON.MAP2 the engine keeps the old room-by-room map.\n')
    with open(os.path.join(MOD, 'Ruleset', 'gijoe_pit_canon.rul'), 'w') as f:
        f.write(hdr + yaml.safe_dump(rul, sort_keys=False, width=140))
    for r in report: print('  note:', r)
    print('map %dx%dx%d padded to %dx%d; %d nodes (%d Cobra, %d Joe)' % (
        X, Y, Z, PX, PY, len(nodes), sum(1 for n in nodes if n[20] != 1), sum(1 for n in nodes if n[20] == 1)))


if __name__ == '__main__':
    main(sys.argv[1])
