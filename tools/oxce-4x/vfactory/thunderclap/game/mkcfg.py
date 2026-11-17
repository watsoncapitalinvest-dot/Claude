# writes cfg_tractor.json / cfg_trailer.json for the gen/ chain (VFACTORY, 17 Nov 2026)
import json
SC = 0.01266   # fit.py 3 3 on the tractor (tighter of the two); the trailer uses the same scale so the pair matches
RO = '/home/claude/rt/veh'
COMMON_LAYERS = ("BODY at the anchor (tiled 3x3 + overhang) -> TURRET layer: turret/<name>_turret_<look>_<turret heading>.png drawn with its pivot "
                 "(frame anchor) at body anchor + the body frame's turret_paste_offset; the turret turns on its own. Missiles are part of BODY: each state hides the ones fired.")
def cfg(name, stores, store_mz, launcher, lname, turret, tur_note, weapons, mvt, readme, preview):
    hide0 = ['turret', 'decal_t_scorch']; states = {}; info = {}
    for i in range(len(stores) + 1):
        states[f'm{i}'] = hide0 + stores[:i]; info[f'm{i}'] = {f'{lname}_fired': i}
    return {'name': name, 'faction': 'Joe', 'flyer': False, 'out': f'{RO}/out/{name}_x', 'scale': SC, 'foot_frame': 3, 'footprint': [3, 3], 'lanes': 4,
            'blends': {'clean': f'{RO}/{name}_x/base.blend', 'damaged': f'{RO}/{name}_x/damaged.blend'}, 'states': states, 'state_info': info,
            'muzzles': store_mz, 'guns': [], 'gun_fx_scale': 0.6,
            'launchers': [{'name': launcher, 'muzzles': stores, 'fx_scale': 0.26}],
            'layers_note': COMMON_LAYERS,
            'states_note': f"m0 = all {len(stores)} {weapons['missile_name']} aboard; m1..m{len(stores)} = fired in this order: {', '.join(stores)}. Each store only changes its own spot.",
            'weapons': weapons, 'movement': mvt, 'readme': readme, 'preview': preview,
            'turret': {'objs': ['turret'], 'pivot': turret[0], 'muzzles': turret[1], 'note': tur_note}}
tr = cfg('thunderclap_tractor', ['missile_R1', 'missile_L1', 'missile_L2'],
    {'missile_R1': [14.0, -61.8, 65.75, 1, 0, 0], 'missile_L1': [16.5, 61.8, 63.25, 1, 0, 0], 'missile_L2': [-7.5, 61.8, 74.65, 1, 0, 0]},
    'lam', 'low_attack_missiles',
    ([19.43, -19.25, 131.25], {'mg999_L': [53.0, -0.3, 147.4, 1, 0, 0], 'mg999_R': [53.0, -38.2, 147.5, 1, 0, 0]}),
    'Roof turret: the MG-999 dual-barrelled pulsating assault weapon. Turns 360 on its own; both barrels fire together.',
    {'missile_name': 'multi-directional surface-to-surface low attack missiles',
     'note': 'THUNDERCLAP TRACTOR (TechnoViper3D kit, blueprint items 7 and 8). GUN: MG-999 dual-barrelled pulsating assault weapon in the roof turret '
             '(turret muzzles mg999_L/R). MISSILES: multi-directional surface-to-surface low attack missiles - the blueprint says two, the kit carries three '
             '(one right side, two left), fired missile_R1, missile_L1, missile_L2.'},
    {'note': 'TRACKED. Ground only; stand-in numbers in gen_vehicles.py until STORY sets them.'},
    'THUNDERCLAP TRACTOR - BATTLE-MAP RENDERS (VFACTORY, 17 Nov 2026) - PRIVATE GAME ASSETS, not for a public repo\n\n'
    'Built from John\'s TechnoViper3D Thunderclap kit (blueprints + instruction sheets). 3x3 (John 17 Nov 14:46), model scale 0.01266, 3x3 frame, SHADE detail.\n'
    'States m0-m3: low attack missiles fired one by one. Turret layer: MG-999. Damaged look: procedural hit stickers (scorch, bullet holes, dents, gouges).\n',
    {'canvas': [1100, 760], 'start': [330, 520], 'start_heading': 'NE', 'altitude': 0, 'ground': [120, 112, 84],
     'script': [['move', 'NE', 2], ['gun', ['mg999_L', 'mg999_R']], ['gun', ['mg999_L', 'mg999_R']], ['tturn', 'SE'], ['gun', ['mg999_L', 'mg999_R']], ['tturn', 'NE'],
                ['missile', 'missile_R1', 'm1', 'lam', 65.75], ['wait', 4], ['missile', 'missile_L1', 'm2', 'lam', 63.25], ['wait', 4], ['missile', 'missile_L2', 'm3', 'lam', 74.65], ['wait', 8]]})
tl = cfg('thunderclap_trailer', ['missile_1', 'missile_2', 'missile_3'],
    {'missile_1': [42.0, 56.21, 119.91, 1, 0, 0], 'missile_2': [42.0, 36.21, 120.54, 1, 0, 0], 'missile_3': [42.0, 16.21, 119.91, 1, 0, 0]},
    'zpj', 'zpj79_missiles',
    ([-7.19, -24.0, 124.97], {'blaster_L': [63.7, 11.0, 141.0, 1, 0, 0], 'blaster_R': [63.7, -24.0, 141.0, 1, 0, 0]}),
    'Roof turret: the rapid-fire computer-controlled blaster cannon on its synchronized digital tracking revolving turret. Turns 360 on its own.',
    {'missile_name': 'ZPJ-79 surface-to-surface delayed detonation cruise missiles',
     'note': 'THUNDERCLAP TRAILER (TechnoViper3D kit, blueprint items 2, 3, 4). GUN: rapid-fire computer-controlled blaster cannon on the synchronized digital tracking '
             'revolving turret (turret muzzles blaster_L/R). MISSILES: three ZPJ-79 surface-to-surface delayed detonation cruise missiles on the deck rack, fired missile_1, missile_2, missile_3.'},
    {'note': 'SIX WHEELS. Ground only; stand-in numbers in gen_vehicles.py until STORY sets them.'},
    'THUNDERCLAP TRAILER - BATTLE-MAP RENDERS (VFACTORY, 17 Nov 2026) - PRIVATE GAME ASSETS, not for a public repo\n\n'
    'Built from John\'s TechnoViper3D Thunderclap kit (blueprints + instruction sheets). 3x3 (John 17 Nov 14:46), model scale 0.01266 (same as the tractor), 3x3 frame, SHADE detail.\n'
    'States m0-m3: ZPJ-79 cruise missiles fired one by one. Turret layer: blaster cannon. Damaged look: procedural hit stickers (scorch, bullet holes, dents, gouges).\n',
    {'canvas': [1100, 760], 'start': [330, 520], 'start_heading': 'NE', 'altitude': 0, 'ground': [120, 112, 84],
     'script': [['move', 'NE', 2], ['gun', ['blaster_L', 'blaster_R']], ['tturn', 'E'], ['gun', ['blaster_L', 'blaster_R']], ['tturn', 'NE'],
                ['missile', 'missile_1', 'm1', 'zpj', 119.9], ['wait', 4], ['missile', 'missile_2', 'm2', 'zpj', 120.5], ['wait', 4], ['missile', 'missile_3', 'm3', 'zpj', 119.9], ['wait', 8]]})
json.dump(tr, open('cfg_tractor.json', 'w'), indent=1); json.dump(tl, open('cfg_trailer.json', 'w'), indent=1); print('ok')
