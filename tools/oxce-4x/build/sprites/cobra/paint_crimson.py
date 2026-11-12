"""Crimson Guard (1985) on Ch49, from the 3DJoes toy photos; derived from the Cobra-trooper build (Cobra Soldier + Officer on Ch49 (Duke's approved body + garment maps): recipe recolour via prep_textures, gloves on the
hands (skin id), black harness/belt/boots, sigil printed on the shirt front (under the harness straps), Duke's masked face."""
import sys, os, json, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prep_textures import body_sheet
CH = sys.argv[1]; PM = '/tmp/claude-0/fac/posmap'
EMB = np.asarray(Image.open('/mnt/user-data/uploads/Downloads/Cobra_emblem_current.png').convert('RGBA')).astype(np.float32)
BLUE = (172, 24, 30)          # "BLUE" = this figure's uniform colour: Crimson Guard red
BLACK = (30, 30, 34); SILVER = (200, 202, 208)
CHARS = {'crimson_guard': ('Crimson Guard', BLACK, {'red': SILVER, 'black': (24, 24, 28)})}
def up(a): return np.repeat(np.repeat(a, 2, 0), 2, 1)
face = Image.open('/tmp/claude-0/fac/Ch33_face_crimsonguard.png')   # full black faceplate
for cid, (name, gloves, sig) in CHARS.items():
    d = f'{CH}/{cid}'; os.makedirs(d, exist_ok=True)
    col = {'shirt': BLUE, 'collar': BLUE, 'belt': BLACK, 'trousers': BLUE, 'boots': BLACK, 'webbing': BLACK, 'hair': BLUE, 'skin': gloves}
    for s in ('1001', '1002'):
        img = np.asarray(body_sheet(s, col, None)).astype(np.float32).copy()
        ids = np.asarray(Image.open(f'/mnt/user-data/uploads/Reference/models/mixamo/painted/duke/anim/id_Ch49_{s}_Diffuse.png'))
        ids = ids[..., 0] if ids.ndim == 3 else ids
        P = up(np.load(f'{PM}/pos_Ch49_{s}.npy')); N = up(np.load(f'{PM}/nrm_Ch49_{s}.npy')); has = ~np.isnan(P[..., 0])
        X, Z = np.nan_to_num(P[..., 0]), np.nan_to_num(P[..., 2])
        ids = ids.copy(); Y = np.nan_to_num(P[..., 1])
        flat = np.asarray(Image.open(f'/mnt/user-data/uploads/Reference/models/mixamo/painted/duke/anim/flat_Ch49_{s}_Diffuse.png').convert('RGB')).astype(np.float32)
        shade = np.clip(flat.mean(-1) / np.mean((242, 176, 55)), 0.3, 1.3)
        # open the chest: harness centre (diagonal strap + its pouches) becomes shirt, so the sigil shows between the shoulder straps
        clear = (ids == 57)
        img[clear] = np.array(BLUE, np.float32); ids[clear] = np.where(Z[clear] > 0.92, 19, 38)   # flat: no ghost of the removed harness
        # undershirt V at the throat -> uniform blue (high collar look)
        vneck = has & (np.abs(X) < 0.06) & (Z > 1.38) & (N[..., 1] < -0.2) & ~np.isin(ids, (19, 38, 45, 32))
        img[vneck] = BLUE; ids[vneck] = 26
        # --- pen work: fold creases + seams from Ch49's shaded cloth texture, baked in as thin ink (they move with the cloth) ---
        from scipy import ndimage as ndi
        orig = np.asarray(Image.open(f'/mnt/user-data/uploads/Reference/models/mixamo/painted/duke/Ch49_{s}_Diffuse.png').convert('RGB')).astype(np.float32).mean(-1)
        cloth = np.isin(ids, (19, 38))
        dog = ndi.gaussian_filter(orig, 2.5) - ndi.gaussian_filter(orig, 10)
        crease = cloth & (dog < -2.2 * np.median(np.abs(dog[cloth])))
        crease &= ndi.binary_erosion(cloth, iterations=8)                      # not on island borders (seam ticks)
        crease = ndi.binary_opening(crease, iterations=1)
        lab, n = ndi.label(crease, np.ones((3, 3)))
        if n:
            sz = ndi.sum(crease, lab, range(1, n + 1)); crease &= np.isin(lab, [i for i, z in enumerate(sz, 1) if z >= 180])
        img[crease] = img[crease] * 0.2 + np.array((40, 26, 18), np.float32) * 0.8
        # --- a little detail, per the art (painted pieces, each with its own garment ID so it gets an ink outline) ---
        def enc(g): return int(round(g * 255 / 40))
        def put(mask, colr, g):
            img[mask] = np.array(colr, np.float32) * np.clip(shade[mask], 0.66, 1.0)[:, None]; ids[mask] = enc(g)
        shirt = has & (ids == 19); trou = has & (ids == 38)
        # silver aiguillette: braided cord from his right shoulder (x<0) looping down the front of the chest
        pts = np.array([(-0.175, 1.47), (-0.165, 1.40), (-0.150, 1.33), (-0.125, 1.28), (-0.095, 1.30), (-0.085, 1.37), (-0.10, 1.44)])
        dd = np.full(X.shape, 9.0)
        for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
            vx, vz = x1 - x0, z1 - z0; tt = np.clip(((X - x0) * vx + (Z - z0) * vz) / (vx * vx + vz * vz), 0, 1)
            dd = np.minimum(dd, np.hypot(X - (x0 + tt * vx), Z - (z0 + tt * vz)))
        put(shirt & (N[..., 1] < -0.15) & (dd < 0.019), SILVER, 12)
        # black epaulettes on both shoulder tops
        put(shirt & (N[..., 2] > 0.45) & (np.abs(X) > 0.135) & (np.abs(X) < 0.215) & (Z > 1.455), BLACK, 13)
        # silver cuff bands
        put(shirt & (np.abs(np.abs(X) - 0.598) < 0.011), SILVER, 14)
        # silver stripe down the outer seam of each trouser leg
        put(trou & (np.sign(N[..., 0]) == np.sign(X)) & (np.abs(N[..., 0]) > 0.80) & (np.abs(N[..., 1]) < 0.16) & (Z > 0.40) & (Z < 0.90), SILVER, 15)
        # black thigh holster, his left leg (x>0), outer side
        put(trou & (X > 0.0) & (N[..., 0] > 0.55) & (Z > 0.60) & (Z < 0.80) & (np.abs(N[..., 1]) < 0.55), BLACK, 16)
        # belt up at the waist (as on the toy): hip band (Ch49's belt ID) becomes red uniform, new black belt + silver buckle higher
        hip = has & (ids == 32)
        img[hip] = np.array(BLUE, np.float32); ids[hip] = 38
        shirt = has & (ids == 19)
        put((shirt | (has & (ids == 38))) & (Z > 0.985) & (Z < 1.040), BLACK, 18)
        put(has & (ids == enc(18)) & (N[..., 1] < -0.5) & (np.abs(X) < 0.024) & (Z > 0.992) & (Z < 1.033), SILVER, 19)
        # small silver badges: rank badge on the left chest, emblem on the left sleeve
        put(shirt & (N[..., 1] < -0.5) & (np.abs(X - 0.075) < 0.030) & (np.abs(Z - 1.43) < 0.010), SILVER, 17)
        put(shirt & (N[..., 2] > 0.5) & (np.abs(X - 0.30) < 0.022) & (np.abs(Y) < 0.025), SILVER, 17)
        Image.fromarray(ids.astype(np.uint8)).save(f'{d}/id_Ch49_{s}_Diffuse.png')
        W = 0.165; cz = 1.300; cx = 0.0
        front = has & (N[..., 1] < -0.45) & (np.abs(X - cx) < W / 2) & (np.abs(Z - cz) < W * 0.62) & (ids == 19)   # shirt only: straps stay on top
        u = (X[front] - cx) / W + 0.5; v = 0.5 - (Z[front] - cz) / (W * EMB.shape[0] / EMB.shape[1])
        ex = np.clip((u * EMB.shape[1]).astype(int), 0, EMB.shape[1] - 1); ey = np.clip((v * EMB.shape[0]).astype(int), 0, EMB.shape[0] - 1)
        e = EMB[ey, ex]; on = (e[:, 3] > 128) & (v >= 0) & (v <= 1)
        c = np.where((e[:, 0] > 120)[:, None], np.array(sig['red'], np.float32), np.array(sig['black'], np.float32))
        fy, fx = np.nonzero(front); img[fy[on], fx[on]] = c[on]
        Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(f'{d}/Ch49_{s}.png')
        print(cid, s, 'sigil texels', int(on.sum()))
    face.save(f'{d}/face.png'); Image.open('/mnt/user-data/uploads/Reference/models/mixamo/painted/duke/anim/Ch33_hair_duke.png').save(f'{d}/hair.png')
    json.dump({'id': cid, 'name': name, 'drop_hair': True, 'hair_tones': [[0, 0, 0]] * 3, 'mirror': False, 'helmet': [176, 26, 32]}, open(f'{d}/meta.json', 'w'))
