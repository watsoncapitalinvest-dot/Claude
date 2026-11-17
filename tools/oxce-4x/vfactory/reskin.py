"""VFACTORY reskin: change decals on a finished ROSTER package and re-issue it, rendering only what changed.
python3 reskin.py PKG_DIR ROSTER_CFG WORK_DIR OUT_PKG_DIR 'img1,img2' 'missing=r,g,b;...' MASK.png [FULL=1]

1. sigil_swap.py puts the new picture into the named decal images of the package's own source blend (and restores unpacked
   flat-colour textures so the re-render matches ROSTER's frames pixel for pixel).
2. Renders the clean look of the FIRST state at all 8 headings with ROSTER's render_vehicle.py (same camera, light, ink).
3. Every frame (all states, clean and damaged) = ROSTER's old frame with only the changed pixels replaced:
   changed = where the new first-state render differs from the old first-state frame. A pixel is copied only if the old frame
   equals the old first-state clean frame there (a removed store or a damage sticker on that pixel keeps its own pixel).
   Where a removed store touches the changed area the state/heading is rendered in full (FULL=1 renders every state).
4. Tiles and overhang re-cut with ROSTER pkg.py's cutter; manifest sha256 / pieces / reassembly re-written; turntable rebuilt.
Resume-safe: renders already on disk are kept. Prints a JSON report at the end."""
import sys, os, json, shutil, subprocess, hashlib, time, glob
import numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
PKG, CFG, WORK, OUT, IMGS, FIX, MASK = sys.argv[1:8]; FULL = os.environ.get('FULL') == '1'
RT = '/home/claude/rt'; VF = os.path.dirname(os.path.abspath(__file__)); H = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
FR = {1: (128, 160, 64, 128), 2: (256, 224, 128, 160), 3: (384, 288, 192, 192), 4: (512, 352, 256, 224), 5: (640, 416, 320, 256), 6: (768, 480, 384, 288),
      7: (896, 544, 448, 320), 8: (1024, 608, 512, 352), 9: (1152, 672, 576, 384), 10: (1280, 736, 640, 416)}
t0 = time.time(); os.makedirs(WORK, exist_ok=True)
N = os.path.basename(PKG.rstrip('/')); man = json.load(open(f'{PKG}/manifest.json')); cfg = json.load(open(CFG))
W, Hh = man['frame']; FOOT = next(k for k, v in FR.items() if v[:2] == (W, Hh)); AX, AY = FR[FOOT][2:]; SC = str(man['model_scale'])
states = list(dict.fromkeys(f['state'] for f in man['frames'])); hide = cfg['states']
assert all(s in hide for s in states), ('state missing from cfg', states, list(hide))
S0 = states[0]
run = lambda a, env=None: subprocess.run(['python3', '-I'] + a, env=dict(os.environ, **(env or {})), capture_output=True, text=True)

# 1. blend
blend = glob.glob(f'{PKG}/*_source.blend')[0]; sig = f'{WORK}/sig.blend'; ns = f'{WORK}/ns.blend'
if not os.path.exists(ns):
    r = run([f'{VF}/sigil_swap.py', blend, sig, MASK, IMGS, FIX]); print(''.join(l + '\n' for l in r.stdout.splitlines() if l.startswith(('SIGIL', 'FIXED'))), end='')
    if not os.path.exists(sig): sys.exit('swap failed\n' + r.stderr[-2000:])
    c2 = dict(cfg, out=WORK); json.dump(c2, open(f'{WORK}/cfg.json', 'w'))
    run([f'{RT}/gen/strip.py', sig, f'{WORK}/cfg.json', 'nospin', ns])
    assert os.path.exists(ns), 'strip failed'

# 2. renders
lanes = 1 if FOOT >= 6 else 2
def render(st, k):
    out = f'{WORK}/r/{st}_clean_{H[k]}.png'
    if os.path.exists(out): return out
    tmp = f'{WORK}/r/_{st}_{k}'; os.makedirs(tmp, exist_ok=True)
    for _ in range(3):
        run([f'{RT}/ttt/tools/render_vehicle.py', ns, tmp, st, 'clean', str(k), SC], {'SHADE': 'detail', 'FOOT': str(FOOT), 'HIDE': ','.join(hide[st])})
        f = glob.glob(f'{tmp}/*.png')
        if f: shutil.move(f[0], out); break
    shutil.rmtree(tmp, ignore_errors=True); return out
os.makedirs(f'{WORK}/r', exist_ok=True)
jobs = [(st, k) for st in (states if FULL else [S0]) for k in range(8)]
with ThreadPoolExecutor(lanes) as ex: list(ex.map(lambda j: render(*j), jobs))
n_render = len(jobs)

# 3. patch
ld = lambda p: np.asarray(Image.open(p).convert('RGBA')).astype(np.int16)
fmap = {(f['look'], f['state'], f['heading']): f for f in man['frames']}
if os.path.exists(OUT): shutil.rmtree(OUT)
shutil.copytree(PKG, OUT)
rep = dict(package=N, foot=FOOT, scale=SC, states=len(states), frames=len(man['frames']), rendered_first=n_render, rendered_extra=0, changed_px={}, sticker_kept_px=0, full_check=None)
new0 = {h: ld(f'{WORK}/r/{S0}_clean_{h}.png') for h in H}; old0 = {h: ld(f"{PKG}/{fmap[('clean', S0, h)]['file']}") for h in H}
chg = {h: (new0[h] != old0[h]).any(-1) for h in H}
for h in H:
    rep['changed_px'][h] = int(chg[h].sum())
    if chg[h].any():
        ys, xs = np.nonzero(chg[h]); assert (np.ptp(ys) + 1) * (np.ptp(xs) + 1) < 0.25 * W * Hh, f'{h}: change area too large - texture mismatch?'
newframes = {}
TOL = 3   # ROSTER's own re-renders differ by +-1 in places: that is noise, not a store or a sticker
near = lambda a, b, eq: (np.abs(a - b) <= TOL).all(-1) if eq else (np.abs(a - b) > TOL).any(-1)
for (look, st, h), f in fmap.items():
    old = ld(f'{PKG}/{f["file"]}')
    if look == 'clean' and st == S0: newframes[(look, st, h)] = new0[h]; continue
    oldc = ld(f"{PKG}/{fmap[('clean', st, h)]['file']}")
    if st != S0 and not FULL and (near(oldc, old0[h], False) & chg[h]).any():          # a removed store touches the changed area
        render(st, H.index(h)); rep['rendered_extra'] += 1
    if os.path.exists(f'{WORK}/r/{st}_clean_{h}.png') and st != S0:
        src_new, src_old = ld(f'{WORK}/r/{st}_clean_{h}.png'), oldc
        cm = (src_new != src_old).any(-1)
    else:
        src_new, src_old, cm = new0[h], old0[h], chg[h]
    if look == 'clean': copy = cm
    else:
        same = near(old, src_old, True); copy = cm & same
        tint = cm & ~same & (np.abs(old - src_old) <= 40).all(-1)   # light soot / weathering over the decal: carry the tint onto the new decal
        rep['sticker_kept_px'] += int((cm & ~same & ~tint).sum()); rep['tinted_px'] = rep.get('tinted_px', 0) + int(tint.sum())
    nf = old.copy(); nf[copy] = src_new[copy]
    if look != 'clean': nf[tint] = np.clip(src_new[tint] + (old[tint] - src_old[tint]), 0, 255)
    newframes[(look, st, h)] = nf

# 4. re-cut (ROSTER pkg.py's cutter, unchanged)
TA = (64, 112)
def iso(x, y): return (x / 64 + y / 32) / 2, (y / 32 - x / 64) / 2
yy, xx = np.mgrid[0:Hh, 0:W]; u, v = iso(xx - AX, yy - AY)
def cutter(fx, fy):
    ci, cj = (fx - 1) / 2, (fy - 1) / 2
    OFF = {(i, j): (round(AX + (i - ci) * 64 - (j - cj) * 64 - TA[0]), round(AY + (i - ci) * 32 + (j - cj) * 32 - TA[1])) for j in range(fy) for i in range(fx)}
    cent = {t: iso(o[0] + TA[0] - AX, o[1] + TA[1] - AY) for t, o in OFF.items()}
    own = np.stack([np.maximum(abs(u - c[0]), abs(v - c[1])) + 1e6 * ~((xx >= o[0]) & (xx < o[0] + 128) & (yy >= o[1]) & (yy < o[1] + 160)) for c, o in zip(cent.values(), OFF.values())]).argmin(0)
    return OFF, own
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest(); cuts = {}; mism = 0
for (look, st, h), im16 in newframes.items():
    f = fmap[(look, st, h)]; im = im16.astype(np.uint8); Image.fromarray(im, 'RGBA').save(f'{OUT}/{f["file"]}'); f['sha256'] = sha(f'{OUT}/{f["file"]}')
    if 'pieces' not in f: continue
    for p in f['pieces']: os.remove(f'{OUT}/{p["file"]}')
    if f.get('overhang'): os.remove(f'{OUT}/{f["overhang"]}')
    key = tuple(f['footprint']); cuts.setdefault(key, cutter(*key)); OFF, own = cuts[key]
    nm = os.path.splitext(os.path.basename(f['file']))[0]; rec = np.zeros_like(im); pieces = []
    for kk, (t, o) in enumerate(OFF.items()):
        part = np.where((own == kk)[..., None], im, 0).astype(np.uint8); x0, y0 = max(o[0], 0), max(o[1], 0); tl = np.zeros((160, 128, 4), np.uint8)
        sub = part[y0:max(o[1] + 160, 0), x0:max(o[0] + 128, 0)]
        if sub.size: tl[y0 - o[1]:y0 - o[1] + sub.shape[0], x0 - o[0]:x0 - o[0] + sub.shape[1]] = sub; rec[y0:y0 + sub.shape[0], x0:x0 + sub.shape[1]] += sub
        if not tl[..., 3].any(): continue
        fn = f'tiles/{nm}_tile_{t[0]}_{t[1]}.png'; Image.fromarray(tl, 'RGBA').save(f'{OUT}/{fn}'); pieces.append({'tile': list(t), 'paste_offset': list(o), 'anchor': list(TA), 'file': fn})
    cov = (rec[..., 3] > 0) | (im[..., 3] == 0); ovh = np.where((~cov)[..., None], im, 0).astype(np.uint8); ohf = None
    if ovh[..., 3].any(): ohf = f'tiles/{nm}_overhang.png'; Image.fromarray(ovh, 'RGBA').save(f'{OUT}/{ohf}'); rec = rec + ovh
    f['pieces'] = pieces; f['overhang'] = ohf
    f['reassembly_mismatch_px'] = int(((rec != im).any(-1) & ((im[..., 3] > 0) | (rec[..., 3] > 0))).sum()); mism += f['reassembly_mismatch_px']
man['decal_note'] = ('17 Nov 2026 (VFACTORY, John 09:47): the Cobra sigil replaces the diamond placeholder (' + IMGS + '), drawn in the diamond\'s own colour. '
                     'Only the pixels the decal covers changed; everything else is ROSTER\'s frame unchanged.')
json.dump(man, open(f'{OUT}/manifest.json', 'w'), indent=1)
rep['reassembly_mismatch_total'] = mism
# decals_src: the new picture under the old name
for nm in IMGS.split(','):
    for p in glob.glob(f'{OUT}/decals_src/{nm}'):
        r = run(['-c', f"import bpy;bpy.ops.wm.open_mainfile(filepath='{sig}');im=bpy.data.images['{nm}'];im.filepath_raw='{p}';im.file_format='PNG';im.save()"])
shutil.copy(sig, glob.glob(f'{OUT}/*_source.blend')[0])
tt = glob.glob(f'{OUT}/*_turntable.gif')
if tt:
    alt = 64 if man.get('flyer') else 0
    run([f'{RT}/gen/turntable.py', OUT, N, str(alt), tt[0], '1.2'])
rep['seconds'] = round(time.time() - t0, 1)
print('REPORT ' + json.dumps(rep))
