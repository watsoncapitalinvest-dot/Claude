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
c = base('vamp', round(0.052 * 2.114, 5), 3, [2, 3], 'vamp_v2', {'m0': ['GJTURRET']}, {'muzzle': [5.14, 0.429, 10.55, 1, 0, 0]}, 'Joe',
         R + 'V.A.M.P. gun fit, class 2x3 (installed as size 3 until rectangles). Scale 0.10993 = 0.052 x 2.114 (95% long / 56% short).\n')
c['turret'] = {'objs': ['GJTURRET'], 'pivot': [-5.579, 0.429, 9.191], 'muzzles': {'mg': [5.14, 0.429, 10.55, 1, 0, 0]}, 'note': 'twin MG head turns on its own'}
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
# H.I.S.S.: tank class 3x4, was 0.0672 in 3x3 -> x1.89. Turret = the real 1983 turret (vfactory/hiss/build_hiss.py, John 18:29)
HM = {'cannonL': [6.179, 2.014, 17.142, 1, 0, 0], 'cannonR': [6.179, -2.014, 17.142, 1, 0, 0]}
c = base('hiss', round(0.0672 * 1.89, 5), 6, [3, 4], 'hiss_v2',   # FOOT 6 frame: the rear rack is taller than a FOOT 4 frame (SE heading clipped)
         {'m0': ['GJTURRET01']}, dict(HM), 'Cobra',
         R + 'Cobra H.I.S.S., class 3x4 (installed as size 4 until rectangles). Scale 0.12701 = 0.0672 x 1.89 (95% long / 43% short). Turret: the 1983 toy\'s gunner pod with dorsal twin 30mm automatic cannons (Thingiverse 776353 v3), replacing the Generals rocket rack.\n')
c['turret'] = {'objs': ['GJTURRET01'], 'pivot': [-4.27, 0.0, 13.42], 'muzzles': dict(HM), 'note': 'gunner pod with twin 30mm cannons'}
c['gun_fx_scale'] = 1.0
c['preview']['script'] = [['move', 'NE', 2], ['gun', ['cannonL', 'cannonR']], ['tturn', 'SE'], ['gun', ['cannonL', 'cannonR']], ['tturn', 'NE'], ['wait', 6]]
cf['hiss'] = c
# MOBAT: tank class 3x4, was 0.089 -> x1.37
c = base('mobat', round(0.089 * 1.37, 5), 4, [3, 4], 'mobat', {'m0': ['GJTURRET', 'GJBARREL01']}, {'muzzle': [16.032, 0.0, 8.08, 1, 0, 0]}, 'Joe',
         R + 'M.O.B.A.T., class 3x4 (installed as size 4 until rectangles). Scale 0.12193 = 0.089 x 1.37 (95% long / 51% short).\n')
c['turret'] = {'objs': ['GJTURRET', 'GJBARREL01'], 'pivot': [0.0, 0.0, 6.662], 'muzzles': {'main': [16.032, 0.0, 8.08, 1, 0, 0]}, 'note': 'main gun turret turns on its own'}
c['preview']['script'] = [['move', 'NE', 2], ['gun', ['main']], ['tturn', 'SE'], ['gun', ['main']], ['tturn', 'NE'], ['wait', 6]]
cf['mobat'] = c
for _c in cf.values():                                   # turret decals ride the turret layer: never on hull frames (17 Nov 20:32)
    if 'turret' in _c: _c['states'] = {k: v + ['decal_t_*'] for k, v in _c['states'].items()}
for k, v in cf.items(): json.dump(v, open(f'cfg_{k}.json', 'w'), indent=1)
print({k: (v['scale'], v['foot_frame']) for k, v in cf.items()})

# ---- second pass (John 17:13 "get the rest to official size"; Triple T 3x3 John 17:16) ----
# Scale = 0.95 x class side / model extent on the limiting axis, x 0.967 = the same calibration the first four got from their
# 8-heading sprite measurement (VAMP 0.964, H.I.S.S. 0.969), so the whole set is filled the same way. Barrels may overhang.
CAL = 0.967
def fit(L, W, fl, fs):
    a, b = 0.95 * fl / L, 0.95 * fs / W
    return round(min(a, b) * CAL, 5), ('long' if a <= b else 'short')
cf2 = {}
s, lim = fit(16.0, 9.4, 2, 1)     # Ferret ATV 1x2; guns fixed
c = base('ferret', s, 2, [1, 2], 'ferret', {'m0': []}, {'muzzle': [5.62, -3.56, 7.1, 1, 0, 0]}, 'Cobra',
         R + f'Cobra Ferret ATV, class 1x2 (installed as size 2). Scale {s} (was 0.0406; {lim} axis limits).\n')
c['guns'] = ['muzzle']; c['preview']['script'] = [['move', 'NE', 2], ['gun', ['muzzle']], ['wait', 6]]; cf2['ferret'] = c
s, lim = fit(30.0, 13.34, 3, 2)   # Stinger 2x3; ground-to-air rocket rack turret (file card: rotates 360); John 18:37 rework
SM = {'rk1': [-1.658, 3.665, 13.611, 1, 0, 0], 'rk3': [-1.658, -3.665, 13.611, 1, 0, 0]}
c = base('stinger', s, 3, [2, 3], 'stinger_v2', {'m0': ['GJTURRET']}, dict(SM), 'Cobra',
         R + f'Cobra Stinger, class 2x3 (installed as size 3). Scale {s} (was 0.0433; {lim} axis limits). Weapon: ground-to-air rockets (3 on the rack); the flying rocket is one of them cut out (vfactory/stinger/cut_rocket.py).\n')
c['turret'] = {'objs': ['GJTURRET'], 'pivot': [-7.48, 0.0, 6.86], 'muzzles': dict(SM), 'note': 'ground-to-air rocket rack, turns 360'}
c['launchers'] = [{'name': 'rkt', 'muzzles': ['rk1', 'rk3'], 'fx_scale': 0.25, 'from_tube': True}]
c['preview']['script'] = [['move', 'NE', 2], ['missile', 'rk1', 'm0', 'rkt', 13.6], ['missile', 'rk3', 'm0', 'rkt', 13.6], ['wait', 6]]
cf2['stinger'] = c
s, lim = fit(24.0, 11.0, 3, 2)    # Thunder Machine 2x3; rework (John 17:36-17:37): twin Penetrator Gatlings as a turret, detail, markings
GZ = 6.196; GM = {'gatL': [11.45, 0.62, GZ, 1, 0, 0], 'gatR': [11.45, -0.62, GZ, 1, 0, 0]}
c = base('thunder_machine', s, 3, [2, 3], 'thunder_machine_v2', {'m0': []}, dict(GM), 'Dreadnok',
         R + f'Dreadnok Thunder Machine, class 2x3 (installed as size 3). Scale {s} (was 0.0813; {lim} axis limits). Rework 17 Nov (vfactory/thunder_machine): twin 6-barrel Penetrator Gatlings on a fixed mount (fire forward only), side pipes, stack, jerry cans, push bar, Dreadnok markings. The old rear "rocket" points were the jet exhausts.\n')
c['guns'] = ['gatL', 'gatR']                                       # fixed, fire forward only (John 18:04: no turret)
c['gun_fx_scale'] = 1.3                                            # Gatlings: big flash
c['preview']['script'] = [['move', 'NE', 2], ['gun', ['gatL', 'gatR']], ['turn', 'SE'], ['gun', ['gatL', 'gatR']], ['wait', 6]]; cf2['thunder_machine'] = c
s, lim = fit(26.0, 16.02, 3, 2)   # Wolverine 2x3; missile turret, loaded
W12 = [f'wrk{i:02d}' for i in range(1, 13)]; M12 = [f'mouth{i:02d}' for i in range(1, 13)]
c = base('wolverine', s, 3, [2, 3], 'wolverine_v2', {'m0': ['GJTURRET', 'wrk_fly'] + W12 + M12}, {'muzzle': [-3.55, 6.43, 14.73, 1, 0, 0]}, 'Joe',
         R + f'Wolverine, class 2x3 (installed as size 3). Scale {s} (was 0.075; {lim} axis limits). Turret drawn loaded (12 missiles).\nTOY PASS (17 Nov): toy green hull and pods, grey missiles, toy markings (vfactory/wolverine/).\n')
c['turret'] = {'objs': ['GJTURRET'] + W12 + M12, 'pivot': [-7.47, 0.0, 7.48], 'muzzles': {'rack': [-3.55, 6.43, 14.73, 1, 0, 0]}, 'note': 'missile turret'}
c['preview']['script'] = [['move', 'NE', 2], ['gun', ['rack']], ['tturn', 'SE'], ['tturn', 'NE'], ['wait', 6]]; cf2['wolverine'] = c
s, lim = fit(33.01, 17.34, 5, 4)  # Mauler 4x5 (barrel included, as for the MOBAT)
c = base('mauler', s, 5, [4, 5], 'mauler', {'m0': ['GJTURRET01', 'GJBARREL01']}, {'muzzle': [17.51, 0.0, 13.57, 1, 0, 0]}, 'Joe',
         R + f'Mauler M.B.T., class 4x5 (installed as size 5). Scale {s} (was 0.1048; {lim} axis limits).\n')
c['turret'] = {'objs': ['GJTURRET01', 'GJBARREL01'], 'pivot': [-2.1, 0.0, 8.73], 'muzzles': {'main': [17.51, 0.0, 13.57, 1, 0, 0]}, 'note': 'main gun turret'}
c['preview']['script'] = [['move', 'NE', 2], ['gun', ['main']], ['tturn', 'SE'], ['gun', ['main']], ['tturn', 'NE'], ['wait', 6]]; cf2['mauler'] = c
s, lim = fit(26.0, 20.34, 3, 3)   # Triple T 3x3 (John 17:16); pods empty left first  (rendered FOOT 5: taller than the 3x3 frame)
c = base('triple_t', s, 5, [3, 3], 'triple_t', {'m2': [], 'm1': ['missile_L'], 'm0': ['missile_L', 'missile_R']},
         {'missile_L': [5.5, 8.9, 10.78, 1, 0, 0], 'missile_R': [5.5, -8.9, 10.78, 1, 0, 0]}, 'Joe',
         R + f'Triple T, class 3x3 (John 17:16). Scale {s} (was 0.05; {lim} axis limits). States m2..m0: left pod fires first.\n')
c['launchers'] = [{'name': 'pod', 'muzzles': ['missile_L', 'missile_R'], 'fx_scale': 0.3, 'from_tube': True}]
c['preview']['script'] = [['move', 'NE', 2], ['missile', 'missile_L', 'm1', 'pod', 10.78], ['missile', 'missile_R', 'm0', 'pod', 10.78], ['wait', 6]]
cf2['triple_t'] = c
# H.I.S.S. rocket-rack variant (John 18:41: Cobra research upgrade): the original Generals rack, 4 rockets, class 3x4
RM = {'rk1': [1.297, 1.649, 18.912, 1, 0, 0], 'rk2': [1.297, -1.649, 18.912, 1, 0, 0]}
c = base('hiss_rack', round(0.0672 * 1.89, 5), 6, [3, 4], 'hiss_rack', {'m0': ['GJTURRET01']}, dict(RM), 'Cobra',
         R + 'Cobra H.I.S.S. rocket-rack variant (Cobra research upgrade, John 18:41), class 3x4 (size 4). Scale 0.12701. The Generals rocket rack, 4 rockets; the flying rocket is one cut from the rack (vfactory/hiss/cut_rack_rocket.py).\n')
c['turret'] = {'objs': ['GJTURRET01'], 'pivot': [-4.27, 0.0, 13.42], 'muzzles': dict(RM), 'note': 'rocket rack, 4 rockets'}
c['launchers'] = [{'name': 'rkt', 'muzzles': ['rk1', 'rk2'], 'fx_scale': 0.25, 'from_tube': True}]
c['preview']['script'] = [['move', 'NE', 2], ['missile', 'rk1', 'm0', 'rkt', 18.9], ['missile', 'rk2', 'm0', 'rkt', 18.9], ['wait', 6]]
cf2['hiss_rack'] = c
for _c in cf2.values():                                   # turret decals ride the turret layer: never on hull frames (17 Nov 20:32)
    if 'turret' in _c: _c['states'] = {k: v + ['decal_t_*'] for k, v in _c['states'].items()}
for k, v in cf2.items(): json.dump(v, open(f'cfg_{k}.json', 'w'), indent=1)
print({k: (v['scale'], v['foot_frame']) for k, v in cf2.items()})
