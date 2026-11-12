"""Cobra Soldier + Officer on Ch49 (Duke's approved body + garment maps): recipe recolour via prep_textures, gloves on the
hands (skin id), black harness/belt/boots, sigil printed on the shirt front (under the harness straps), Duke's masked face."""
import sys, os, json, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prep_textures import body_sheet
CH = sys.argv[1]; PM = '/tmp/claude-0/fac/posmap'
EMB = np.asarray(Image.open('/mnt/user-data/uploads/Downloads/Cobra_emblem_current.png').convert('RGBA')).astype(np.float32)
BLUE = (24, 62, 160); BLACK = (30, 30, 34)
CHARS = {'cobra_soldier': ('Cobra Soldier', BLUE, {'red': (236, 22, 20), 'black': (20, 20, 24)}),
         'cobra_officer': ('Cobra Officer', BLACK, {'red': (206, 210, 218), 'black': (26, 40, 96)}),
         # 1983 Viper Pilot = the Trooper repainted: blue gloves, black mask/straps/knee pads/boots, SILVER sigil
         'viper_pilot': ('Viper Pilot', BLUE, {'red': (206, 210, 218), 'black': (20, 20, 24)})}
if os.environ.get('ONLY_CHARS'): CHARS = {k: v for k, v in CHARS.items() if k in os.environ['ONLY_CHARS'].split(',')}
def up(a): return np.repeat(np.repeat(a, 2, 0), 2, 1)
face = Image.open('/tmp/claude-0/fac/Ch33_face_duke_cobramask.png')
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
        clear = has & (ids == 57) & (N[..., 1] < -0.2) & (np.abs(X) < 0.105) & (Z > 1.20) & (Z < 1.47)
        img[clear] = np.array(BLUE, np.float32) * np.clip(shade[clear], 0.66, 1.0)[:, None]; ids[clear] = 19
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
        legs = has & (ids == 38) & (X > 0.0)                                   # his left leg (viewer's right), as in the art
        for zc in (0.70, 0.61):
            put(legs & (np.abs(Z - zc) < 0.012), BLACK, 12)                     # thigh straps
        if cid in ('cobra_soldier', 'viper_pilot'):
            for sx in (1, -1):
                kp = has & (ids == 38) & (N[..., 1] < -0.25) & ((((X - sx * 0.122) / 0.052) ** 2 + ((Z - 0.505) / 0.062) ** 2) < 1)
                put(kp, BLACK, 13)                                              # knee pads
        else:
            for sx in (1, -1):
                pch = has & np.isin(ids, (19, 57)) & (N[..., 1] < -0.3) & (np.abs(X - sx * 0.058) < 0.028) & (Z > 1.195) & (Z < 1.262)
                put(pch, BLACK, 14)                                             # chest pouches under the sigil
            sp = has & (ids == 57) & (Z > 1.425)
            put(sp, (196, 198, 204), 15)                                        # silver shoulder-strap tops
        Image.fromarray(ids.astype(np.uint8)).save(f'{d}/id_Ch49_{s}_Diffuse.png')
        W = 0.150; cz = 1.345
        front = has & (N[..., 1] < -0.45) & (np.abs(X) < W / 2) & (np.abs(Z - cz) < W * 0.62) & (ids == 19)   # shirt only: straps stay on top
        u = X[front] / W + 0.5; v = 0.5 - (Z[front] - cz) / (W * EMB.shape[0] / EMB.shape[1])
        ex = np.clip((u * EMB.shape[1]).astype(int), 0, EMB.shape[1] - 1); ey = np.clip((v * EMB.shape[0]).astype(int), 0, EMB.shape[0] - 1)
        e = EMB[ey, ex]; on = (e[:, 3] > 128) & (v >= 0) & (v <= 1)
        c = np.where((e[:, 0] > 120)[:, None], np.array(sig['red'], np.float32), np.array(sig['black'], np.float32))
        fy, fx = np.nonzero(front); img[fy[on], fx[on]] = c[on]
        Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(f'{d}/Ch49_{s}.png')
        print(cid, s, 'sigil texels', int(on.sum()))
    face.save(f'{d}/face.png'); Image.open('/mnt/user-data/uploads/Reference/models/mixamo/painted/duke/anim/Ch33_hair_duke.png').save(f'{d}/hair.png')
    json.dump({'id': cid, 'name': name, 'drop_hair': True, 'hair_tones': [[0, 0, 0]] * 3, 'mirror': False, 'helmet': list(BLUE)}, open(f'{d}/meta.json', 'w'))
