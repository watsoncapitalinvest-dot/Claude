import sys, os, numpy as np, json
from PIL import Image
from scipy import ndimage as ndi
from skimage.morphology import skeletonize, remove_small_objects
sys.path.insert(0, '/tmp/claude-0/gs')
import repaint2 as rp
fbx = '/mnt/user-data/uploads/Downloads/Prone Firing Rifle (1).fbx'
C = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
W = 2048
cache = '/tmp/claude-0/pil/geo15.npz'
if not os.path.exists(cache):
    dn, sheets, tris = rp.geometry(fbx); maps = rp.label_maps(dn, tris, R=W)
    np.savez(cache, dn=np.array(dn), **{f'{k}{i}': v for i in range(len(dn)) for k, v in (('lab', maps[i]), ('x', rp.label_maps.xmaps[i]), ('y', rp.label_maps.ymaps[i]), ('z', rp.label_maps.zmaps[i]))},
             **{f'src{i}': np.asarray(sheets[n].convert('RGB').resize((W, W), Image.BILINEAR)) for i, n in enumerate(dn)})
G = np.load(cache); dn = list(G['dn'])
INK = np.array([40, 26, 18], np.float32)
for si, n in enumerate(dn):
    lab, x, y, z, src = (G[f'{k}{si}'] for k in ('lab', 'x', 'y', 'z', 'src'))
    valid = lab > 0; ax = np.abs(x)
    bake = np.load(C['bake'][si]); bake = np.asarray(Image.fromarray(bake).resize((W, W), Image.BILINEAR))
    Lb = ndi.gaussian_filter(src.astype(np.float32).mean(-1), W / 120)
    gear = ndi.median_filter((Lb < C['gear_L']).astype(np.uint8), 41) > 0
    R = np.zeros((W, W), np.uint8)
    R[valid] = 1                                                   # suit
    R[valid & gear & np.isin(lab, [3, 4])] = 4                      # chest plate -> life vest
    R[valid & gear & (lab == 5)] = C.get('belt_region', 9)          # belt
    R[valid & gear & (lab == 1)] = 9                                # arm straps
    R[valid & (lab == 7)] = 2                                       # boots
    R[valid & (ax > C['hand_x'])] = 3                               # hands
    front = z > C['front_z']
    v = R == 4
    strap = v & front & ((np.abs(ax - C['strap_x']) < C['strap_w']) | (ax < 0.004) | (np.abs(y - C['chest_strap']) < C['strap_w']))
    R[strap] = 9
    nm = C['name']; name = v & front & (x > nm[0]) & (x < nm[1]) & (y > nm[2]) & (y < nm[3]); R[name] = 10
    sp = C['shoulder']; shp = valid & (R == 1) & (np.hypot(x - sp[0], y - sp[1]) < sp[2]) & (z > sp[3])
    R[shp] = 11; R[shp & (np.hypot(x - sp[0], y - sp[1]) < sp[2] * 0.45)] = 12
    kb = C['kneeboard']; R[valid & (lab == 6) & (x > kb[0]) & (x < kb[1]) & (y > kb[2]) & (y < kb[3]) & (z > kb[4])] = 10
    R[valid & (lab == 6) & (np.abs(y - C['leg_strap']) < 0.005)] = 9
    letters = name & (np.abs(y - (nm[2] + nm[3]) / 2) < 0.0035) & ((((x - nm[0]) / 0.009).astype(int) % 2) == 0) & (x > nm[0] + 0.006) & (x < nm[1] - 0.006)
    COL = {1: 'suit', 2: 'boots', 3: 'skin', 4: 'vest', 9: 'strap', 10: 'patch', 11: 'sp_outer', 12: 'sp_inner'}
    SH = {'skin': 0.56, 'suit': 0.58, 'vest': 0.58}
    tone_all = np.ones((W, W), np.float32)
    for rid, key in COL.items():
        m = R == rid
        if not m.any(): continue
        t = bake / max(np.median(bake[m]), 1e-4)
        tone = np.where(t < 0.74, SH.get(key, 0.62), np.where(t > 1.15, 1.13, 1.0)).astype(np.float32)
        if key in ('strap', 'patch', 'sp_inner'): tone = np.where(t < 0.74, 0.8, 1.0).astype(np.float32)
        tone_all[m] = tone[m]
    tone_all = ndi.median_filter(tone_all, 5)
    if C.get('flat_knees'):
        kz = C['flat_knees']; km = valid & (lab == 6) & (y > kz[0]) & (y < kz[1])
        tone_all[km & (R == 1)] = 1.0
    res = np.zeros((W, W, 3), np.float32)
    for rid, key in COL.items():
        m = R == rid; res[m] = np.clip(np.array(C['colors'][key], np.float32) * tone_all[m][:, None], 0, 255)
    ink = np.zeros((W, W), bool)
    for rid in COL:
        m = R == rid
        if not m.any(): continue
        other = valid & ~m & ndi.binary_dilation(m, iterations=2)
        ink |= m & ndi.binary_dilation(other, iterations=2)
    m = np.isin(R, [1, 4]); sh = (tone_all < 0.9) & m
    if C.get('flat_knees'): m = m & ~km
    edge = (sh ^ ndi.binary_erosion(sh, iterations=1)) & ndi.binary_erosion(m, iterations=4)
    sk = remove_small_objects(skeletonize(ndi.binary_dilation(edge, iterations=1)), max_size=C.get('fold_min', 45), connectivity=2)
    ink |= ndi.binary_dilation(sk, iterations=1)
    res[ink] = INK; res[letters] = INK
    res[~valid] = np.array(C['colors']['suit'], np.float32)
    Image.fromarray(res.astype(np.uint8)).save(f'{out}/{n}')
print('ok', dn)
