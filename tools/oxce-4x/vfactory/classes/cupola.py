"""Cupola layer for a gen/ vehicle (John 17 Nov 22:01: "apply the turret rule where the machine gun rotates faster, less tu than the
turret"): cfg['cupola'] = {objs, pivot, muzzles} - a second turret riding on the turret, turning on its own (engine gjCupolaSheet).
Renders the cupola alone about its own pivot, 8 headings, clean + damaged (PART=turret, so its pivot sits at the frame anchor like the
turret's), into the package as cupola/<name>_cupola_<look>_<heading>.png, and works out where it sits for each TURRET heading:
the cupola pivot's offset from the turret pivot, turned with the turret and projected with the battle camera (30 deg, ppu 90.51 x scale).
CHECK: with the old turret frames that still carried the cupola (OLD_TURRET dir), turret + cupola at the same heading must match them.
python3 cupola.py cfg.json [OLD_TURRET_dir]"""
import json, sys, os, subprocess, shutil, hashlib, math
from PIL import Image, ImageChops
cfg = json.load(open(sys.argv[1])); N = cfg['name']; CU = cfg['cupola']; T = cfg['turret']; P = f'/home/claude/rt/veh/pkg/{N}'
O = cfg['out'] + '/cupola'; os.makedirs(O + '/log', exist_ok=True); H = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
R = '/home/claude/rt/ttt/tools/render_vehicle.py'; SC = cfg['scale']
MZ = ';'.join(f'{n}:{p[0]},{p[1]},{p[2]}@{p[3]},{p[4]},{p[5]}' for n, p in CU['muzzles'].items())
for look, b in cfg['blends'].items():
    for k in range(8):
        out = subprocess.run(['python3', '-I', R, b, O, 'cupola', look, str(k), str(SC)], capture_output=True, text=True,
                             env=dict(os.environ, SHADE='detail', FOOT=str(cfg['foot_frame']), PART='turret', TURRET=','.join(CU['objs']),
                                      TPIV=','.join(str(v) for v in CU['pivot']), MUZZLES=MZ,
                                      HIDE='decal_t_*')).stdout   # the turret's markings ride the turret layer, not this one
        open(f'{O}/log/{look}_{k}.txt', 'w').write('\n'.join(l for l in out.splitlines() if l.startswith('MUZZLE')))
m = json.load(open(f'{P}/manifest.json')); AX, AY = m['anchor']; shutil.rmtree(f'{P}/cupola', ignore_errors=True); os.makedirs(f'{P}/cupola')
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest(); rd = lambda f: {l.split()[1]: l.split() for l in open(f) if l.startswith('MUZZLE')}
K = 90.50966799187809 * SC; e = math.radians(30); d = (math.cos(e) / math.sqrt(2), math.cos(e) / math.sqrt(2), math.sin(e)); f = tuple(-x for x in d)
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a): l = math.sqrt(sum(x * x for x in a)); return tuple(x / l for x in a)
Rv = norm(cross(f, (0, 0, 1))); Uv = cross(Rv, f)
def scr(v, k):
    a = math.radians(180 - 45 * k); x, y = v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a)
    w = (x, y, v[2]); return (K * sum(p * q for p, q in zip(w, Rv)), -K * sum(p * q for p, q in zip(w, Uv)))
rel = [c - t for c, t in zip(CU['pivot'], T['pivot'])]
offs = {h: [round(scr(rel, k)[0]), round(scr(rel, k)[1])] for k, h in enumerate(H)}   # package px: cupola image vs turret image, per turret heading
cup = []
for look in cfg['blends']:
    for k, h in enumerate(H):
        fn = f'cupola/{N}_cupola_{look}_{h}.png'; shutil.copy(f'{O}/cupola_{look}_{h}.png', f'{P}/{fn}'); ms = rd(f'{O}/log/{look}_{k}.txt')
        cup.append({'file': fn, 'look': look, 'heading': h, 'heading_is': 'cupola', 'size': m['frame'], 'pivot': [AX, AY], 'sha256': sha(f'{P}/{fn}'),
                    'muzzles': {q: {'xy': [float(ms[q][2]), float(ms[q][3])], 'dir_screen': [float(ms[q][5]), float(ms[q][6])]} for q in CU['muzzles']}})
m['cupola'] = {'frames': cup, 'offset_in_turret': offs, 'note': 'CUPOLA: draw cupola/<name>_cupola_<look>_<cupola heading>.png over the turret, its '
               'top-left at the turret picture\'s top-left + offset_in_turret[TURRET heading] (package px). It turns on its own (engine gjCupolaSheet).',
               'rules': CU.get('note', '')}
json.dump(m, open(f'{P}/manifest.json', 'w'), indent=1); print(N, 'cupola frames', len(cup), 'offsets', offs)
if len(sys.argv) > 2:                                                   # the check: new turret + cupola == old turret that carried it
    worst = 0
    for h in H:
        new = Image.open(f'{P}/turret/{N}_turret_clean_{h}.png').convert('RGBA'); old = Image.open(f'{sys.argv[2]}/{N}_turret_clean_{h}.png').convert('RGBA')
        c = Image.open(f'{P}/cupola/{N}_cupola_clean_{h}.png').convert('RGBA'); comp = new.copy(); comp.alpha_composite(c, tuple(offs[h]))
        diff = ImageChops.difference(comp.getchannel('A'), old.getchannel('A')).point(lambda v: 255 if v > 128 else 0)
        n = sum(diff.histogram()[255:]); worst = max(worst, n); print('CHECK', h, 'pixels that differ in coverage:', n)
    print('CHECK worst', worst)
