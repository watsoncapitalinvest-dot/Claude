# VFACTORY size-class re-renders (STORY's BRIEF_FOR_VFACTORY_VehicleScale, John 16:16): ROSTER's source blends at the class scale.
import json
VB = '/home/claude/vb'; RO = '/home/claude/rt/veh'
def base(name, scale, foot, fp, blend, states, muzzles, faction, readme):
    return {'name': name, 'faction': faction, 'flyer': False, 'out': f'{RO}/out/{name}_cls', 'scale': scale, 'foot_frame': foot, 'footprint': fp,
            'lanes': 2, 'blends': {'clean': f'{VB}/{blend}/{blend}/{blend}_clean.blend', 'damaged': f'{VB}/{blend}/{blend}/{blend}_damaged.blend'},
            'states': states, 'state_info': {}, 'muzzles': muzzles, 'guns': [], 'gun_fx_scale': 0.6, 'launchers': [],
            'layers_note': 'BODY at the anchor (tiles + overhang) -> TURRET layer (turret/<name>_turret_<look>_<heading>.png) with its pivot at body anchor + turret_paste_offset.',
            'states_note': ', '.join(states), 'weapons': {'note': ''}, 'movement': {}, 'readme': readme,
            'preview': {'canvas': [1100, 760], 'start': [330, 520], 'start_heading': 'NE', 'altitude': 0, 'ground': [120, 112, 84], 'script': []}}
R = 'SIZE-CLASS RE-RENDER (VFACTORY, 17 Nov 2026) from ROSTER\'s source blend (Reference\\vehicle_blends). PRIVATE GAME ASSETS.\n'
cf = {}
# VAMP gun fit: 2x3, was 0.052 in 2x2 -> x2.114
c = base('vamp', round(0.052 * 2.114, 5), 3, [2, 3], 'vamp', {'m0': ['GJTURRET']}, {'muzzle': [2.111, 0.429, 10.539, 1, 0, 0]}, 'Joe',
         R + 'V.A.M.P. gun fit, class 2x3 (installed as size 3 until rectangles). Scale 0.10993 = 0.052 x 2.114 (95% long / 56% short).\n')
c['turret'] = {'objs': ['GJTURRET'], 'pivot': [-5.579, 0.429, 9.191], 'muzzles': {'mg': [2.111, 0.429, 10.539, 1, 0, 0]}, 'note': 'twin MG head turns on its own'}
c['preview']['script'] = [['move', 'NE', 2], ['gun', ['mg']], ['tturn', 'SE'], ['gun', ['mg']], ['tturn', 'NE'], ['wait', 6]]
cf['vamp'] = c
# VAMP Mk II rocket fit: 2x3 -> x2.016; 4 rockets leave the pod
rk = ['rocket1', 'rocket2', 'rocket3', 'rocket4']
st = {f'm{4 - i}': ['rocket_fly'] + rk[:i] for i in range(5)}
mz = {r: [-4.46, y, 11.25, 1, 0, 0] for r, y in zip(rk, (3.0, 1.0, -1.0, -3.0))}
c = base('vamp_mk2', round(0.052 * 2.016, 5), 3, [2, 3], 'vamp_mk2', st, mz, 'Joe',
         R + 'V.A.M.P. Mk II rocket fit, class 2x3 (installed as size 3). Scale 0.10483 = 0.052 x 2.016 (95% long / 53% short). States m4..m0: rockets leave the pod, rocket1 first.\n')
c['launchers'] = [{'name': 'rkt', 'muzzles': rk, 'fx_scale': 0.22, 'from_tube': True}]
c['preview']['script'] = [['move', 'NE', 2]] + [['missile', r, f'm{3 - i}', 'rkt', 11.25] for i, r in enumerate(rk)] + [['wait', 6]]
cf['vamp_mk2'] = c
# H.I.S.S.: tank class 3x4, was 0.0672 in 3x3 -> x1.89
c = base('hiss', round(0.0672 * 1.89, 5), 4, [3, 4], 'hiss', {'m0': ['GJTURRET01']}, {'muzzle': [2.22, 0.06, 17.34, 1, 0, 0]}, 'Cobra',
         R + 'Cobra H.I.S.S., class 3x4 (installed as size 4 until rectangles). Scale 0.12701 = 0.0672 x 1.89 (95% long / 43% short).\n')
c['turret'] = {'objs': ['GJTURRET01'], 'pivot': [-4.27, 0.0, 13.42], 'muzzles': {'cannon': [2.22, 0.06, 17.34, 1, 0, 0]}, 'note': 'twin cannon turret turns on its own'}
c['preview']['script'] = [['move', 'NE', 2], ['gun', ['cannon']], ['tturn', 'SE'], ['gun', ['cannon']], ['tturn', 'NE'], ['wait', 6]]
cf['hiss'] = c
# MOBAT: tank class 3x4, was 0.089 -> x1.37
c = base('mobat', round(0.089 * 1.37, 5), 4, [3, 4], 'mobat', {'m0': ['GJTURRET', 'GJBARREL01']}, {'muzzle': [16.032, 0.0, 8.08, 1, 0, 0]}, 'Joe',
         R + 'M.O.B.A.T., class 3x4 (installed as size 4 until rectangles). Scale 0.12193 = 0.089 x 1.37 (95% long / 51% short).\n')
c['turret'] = {'objs': ['GJTURRET', 'GJBARREL01'], 'pivot': [0.0, 0.0, 6.662], 'muzzles': {'main': [16.032, 0.0, 8.08, 1, 0, 0]}, 'note': 'main gun turret turns on its own'}
c['preview']['script'] = [['move', 'NE', 2], ['gun', ['main']], ['tturn', 'SE'], ['gun', ['main']], ['tturn', 'NE'], ['wait', 6]]
cf['mobat'] = c
for k, v in cf.items(): json.dump(v, open(f'cfg_{k}.json', 'w'), indent=1)
print({k: (v['scale'], v['foot_frame']) for k, v in cf.items()})
