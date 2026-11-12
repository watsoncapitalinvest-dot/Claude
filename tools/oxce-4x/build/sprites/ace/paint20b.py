import sys, os, numpy as np, json
from PIL import Image
from scipy import ndimage as ndi
from skimage.morphology import skeletonize, remove_small_objects
sys.path.insert(0, '/tmp/claude-0/gs')
import repaint2 as rp
fbx = '/mnt/user-data/uploads/Downloads/Ch20_nonPBR.fbx'
C = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
dn, sheets, tris = rp.geometry(fbx); maps = rp.label_maps(dn, tris, R=2048)
n = dn[0]; W = 2048
lab = maps[0]; x = rp.label_maps.xmaps[0]; y = rp.label_maps.ymaps[0]; z = rp.label_maps.zmaps[0]
valid = lab > 0
bake = np.load(C['bake']); bake = np.asarray(Image.fromarray(bake).resize((W, W), Image.BILINEAR))
src = np.asarray(sheets[n].convert('RGB').resize((W, W), Image.BILINEAR)).astype(np.float32); L = src.mean(-1)
ax = np.abs(x)
# ---- regions (ids) ----
R = np.zeros((W, W), np.uint8)
head = lab == 2
R[valid] = 1                                    # suit
R[valid & (y < C['boot_y'])] = 2               # boots
R[valid & (ax > C['hand_x'])] = 3              # hands
vest = valid & ~head & (y > C['vest'][0]) & (y < C['vest'][1]) & (ax < C['vest_x'])
R[vest] = 4
R[head] = 5                                     # helmet shell
R[head & (y < C.get('neck_y', 0)) & ~(z > C['face_z'])] = 1     # collar below the helmet = suit
# helmet details
front = z > C['face_z']
visor = head & front & (ax < C['visor_x']) & (y < C['visor'][1]) & (y > C['visor'][0] + C['visor_curve'] * (ax / C['visor_x']) ** 2 * -1 + C['visor_curve'])
R[visor] = 6
mask = head & front & (ax < C['mask_x']) & (y > C['mask'][0]) & (y < C['mask'][1])
R[mask] = 7
stripe = head & (ax < C['stripe_w']) & (y > C['stripe_y']) & ~visor
R[stripe] = 8
# vest harness straps + zip
strap = vest & front & ((np.abs(ax - C['strap_x']) < C['strap_w']) | (ax < 0.004) | (np.abs(y - C['chest_strap']) < C['strap_w']))
R[strap] = 9
# name patch (his left chest = +x), shoulder patch, kneeboard, thigh straps
name = vest & front & (x > C['name'][0]) & (x < C['name'][1]) & (y > C['name'][2]) & (y < C['name'][3])
R[name] = 10
sp = C['shoulder']; shp = valid & ~head & (np.hypot(x - sp[0], y - sp[1]) < sp[2]) & (z > sp[3])
R[shp] = 11; R[shp & (np.hypot(x - sp[0], y - sp[1]) < sp[2] * 0.45)] = 12
kb = C['kneeboard']; kbm = valid & (x > kb[0]) & (x < kb[1]) & (y > kb[2]) & (y < kb[3]) & (z > kb[4])
R[kbm] = 10
legstrap = valid & (lab == 6) & (np.abs(y - C['leg_strap']) < 0.005)
R[legstrap] = 9
# name tape letters: dark dashes
letters = name & (np.abs(y - (C['name'][2] + C['name'][3]) / 2) < 0.0035) & ((((x - C['name'][0]) / 0.009).astype(int) % 2) == 0) & (x > C['name'][0] + 0.006) & (x < C['name'][1] - 0.006)
COL = {1: 'suit', 2: 'boots', 3: 'skin', 4: 'vest', 5: 'helmet', 6: 'visor', 7: 'mask', 8: 'stripe', 9: 'strap', 10: 'patch', 11: 'sp_outer', 12: 'sp_inner'}
SH = {'skin': 0.56, 'suit': 0.58, 'vest': 0.58}
res = np.zeros((W, W, 3), np.float32); tone_all = np.ones((W, W), np.float32)
for rid, key in COL.items():
    m = R == rid
    if not m.any(): continue
    t = bake / max(np.median(bake[m]), 1e-4)
    tone = np.where(t < 0.74, SH.get(key, 0.62), np.where(t > 1.15, 1.13, 1.0)).astype(np.float32)
    if key in ('visor', 'mask', 'strap', 'patch', 'sp_inner', 'stripe'): tone = np.where(t < 0.74, 0.8, 1.0)
    tone_all[m] = tone[m]
tone_all = ndi.median_filter(tone_all, 5)
for rid, key in COL.items():
    m = R == rid
    res[m] = np.clip(np.array(C['colors'][key], np.float32) * tone_all[m][:, None], 0, 255)
INK = np.array([40, 26, 18], np.float32)
res[letters] = INK
# ink: region changes (inside the valid area only) - not on UV seams
ink = np.zeros((W, W), bool)
for rid in COL:
    m = R == rid
    if not m.any(): continue
    other = valid & ~m & ndi.binary_dilation(m, iterations=2)
    ink |= m & ndi.binary_dilation(other, iterations=2)
ink &= ~((R == 5) & ndi.binary_dilation(R == 8, iterations=3))   # no line around the helmet stripe
# fold strokes: shadow/lit boundary inside the suit and vest, long pieces only
for key_ids in ([1, 4],):
    m = np.isin(R, key_ids)
    sh = (tone_all < 0.9) & m
    edge = sh ^ ndi.binary_erosion(sh, iterations=1)
    edge &= ndi.binary_erosion(m, iterations=4)
    sk = skeletonize(ndi.binary_dilation(edge, iterations=1))
    sk = remove_small_objects(sk, max_size=C.get('fold_min', 45), connectivity=2)
    ink |= ndi.binary_dilation(sk, iterations=1)
res[ink] = INK
res[~valid] = np.array(C['colors']['suit'], np.float32)
Image.fromarray(res.astype(np.uint8)).save(f'{out}/{n}')
Image.fromarray((R * 20).astype(np.uint8)).save(f'{out}/regions.png')
print('ok', n)
