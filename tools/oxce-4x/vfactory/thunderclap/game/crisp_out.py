# VFACTORY: sharpen the guns and missiles (John 17 Nov 14:52) - turret layer whole, missile pixels in the body frames, full-size flight sprites
import sys, os, glob, json, hashlib, numpy as np
sys.path.insert(0, '/home/claude/tc'); from crisp import crisp
from PIL import Image
mode, a = sys.argv[1], sys.argv[2]
if mode in ('out', 'turret'):
    cfg = json.load(open(a)); O = cfg['out']; last = list(cfg['states'])[-1]; n = 0
    tur = sorted(glob.glob(f'{O}/turret/turret_*.png'))
    if tur:   # the turret is rendered alone, so its tone is stretched to white; bring its highlights down to the hull's (p90 ~175)
        L = np.concatenate([np.asarray(Image.open(f).convert('RGBA')).astype(float)[..., :3][np.asarray(Image.open(f))[..., 3] > 200].mean(1) for f in tur if 'clean' in f])
        k = min(1.0, 175 / max(np.percentile(L, 90), 1))
        for f in tur:
            a = np.asarray(Image.open(f).convert('RGBA')).astype(float); a[..., :3] *= k
            crisp(Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')).save(f); n += 1
        print('turret tone x', round(k, 3))
    for look in (('clean', 'damaged') if mode == 'out' else ()):
        for f in glob.glob(f'{O}/body/{look}/*_{look}_*.png'):
            st, _, h = os.path.basename(f)[:-4].split('_')
            if st == last: continue
            im = np.asarray(Image.open(f).convert('RGBA')).astype(int); ref = np.asarray(Image.open(f'{O}/body/{look}/{last}_{look}_{h}.png').convert('RGBA')).astype(int)
            from scipy import ndimage as ndi
            m = ndi.binary_dilation(np.abs(im - ref).sum(-1) > 30, iterations=1); crisp(Image.open(f), m).save(f); n += 1
    print('CRISP out', n)
else:
    P = a; mp = f'{P}/manifest.json'; m = json.load(open(mp))
    for k, v in m.items():
        if k.startswith('missile_full') and v:
            for h, e in v['by_heading'].items():
                f = f'{P}/{e["file"]}'; crisp(Image.open(f)).save(f); e['sha256'] = hashlib.sha256(open(f, 'rb').read()).hexdigest()
    json.dump(m, open(mp, 'w'), indent=1); print('CRISP missile_full')
