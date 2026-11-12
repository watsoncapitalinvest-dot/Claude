"""Cobra Recruit (Year 1) on Ch49, from BRIEF_Regular_Troops.txt #6: a street criminal before uniforms reach his cell.
Black ski mask (eyes only), navy zip jacket, faded jeans, black boots, plain blue cloth band on the left upper arm (the only
Cobra mark - NO emblem), black belt with an empty hip holster, fingerless black gloves. The webbing harness is hidden
(meta drop_ids -> factory_blend.py Mask modifier), so he reads as NOT military.
Usage: python3 paint_recruit.py <chars_dir>   then bake_creases -> fix_collar (COLLAR_GAP=0) -> belt_up -> tighten_paint"""
import sys, os, json, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prep_textures import body_sheet
CH = sys.argv[1]; PM = '/tmp/claude-0/fac/posmap'; A = '/mnt/user-data/uploads/Reference/models/mixamo/painted/duke/anim/'
NAVY = (30, 36, 64); DENIM = (72, 100, 150); BLACK = (28, 28, 32); SKIN = (250, 170, 76); BAND = (24, 62, 160)
def up(a): return np.repeat(np.repeat(a, 2, 0), 2, 1)
def enc(g): return int(round(g * 255 / 40))
cid = 'cobra_recruit'; d = f'{CH}/{cid}'; os.makedirs(d, exist_ok=True)
col = {'shirt': NAVY, 'collar': NAVY, 'belt': BLACK, 'trousers': DENIM, 'boots': BLACK, 'webbing': NAVY, 'hair': NAVY, 'skin': SKIN}
for s in ('1001', '1002'):
    img = np.asarray(body_sheet(s, col, None)).astype(np.float32).copy()
    ids = np.asarray(Image.open(f'{A}id_Ch49_{s}_Diffuse.png')); ids = (ids[..., 0] if ids.ndim == 3 else ids).copy()
    P = up(np.load(f'{PM}/pos_Ch49_{s}.npy')); N = up(np.load(f'{PM}/nrm_Ch49_{s}.npy')); has = ~np.isnan(P[..., 0])
    X, Y, Z = (np.nan_to_num(P[..., k]) for k in range(3))
    flat = np.asarray(Image.open(f'{A}flat_Ch49_{s}_Diffuse.png').convert('RGB')).astype(np.float32)
    shade = np.clip(flat.mean(-1) / np.mean((242, 176, 55)), 0.3, 1.3)
    def put(mask, colr, g):
        img[mask] = np.array(colr, np.float32) * np.clip(shade[mask], 0.66, 1.0)[:, None]; ids[mask] = enc(g)
    # throat / undershirt -> jacket (zipped up)
    vneck = has & (np.abs(X) < 0.07) & (Z > 1.36) & ~np.isin(ids, (19, 38, 45, 32, 57, 70))
    img[vneck] = NAVY; ids[vneck] = 26
    # fingerless gloves: hand from the wrist to mid-hand black, fingers bare
    hand = has & (ids == 70) & (np.abs(X) > 0.60)
    put(hand & (np.abs(X) < 0.775), BLACK, 12)
    # plain blue cloth band, his left upper arm (x > 0)
    put(has & (ids == 19) & (X > 0.300) & (X < 0.345), BAND, 13)
    # zip: thin silver line down the jacket front
    put(has & (ids == 19) & (N[..., 1] < -0.5) & (np.abs(X) < 0.0045) & (Z > 1.04) & (Z < 1.47), (150, 154, 166), 14)
    # cheap black hip holster (empty), his right hip, outer side
    put(has & (ids == 38) & (X < 0) & (N[..., 0] < -0.55) & (Z > 0.80) & (Z < 0.94) & (np.abs(Y) < 0.06), BLACK, 15)
    Image.fromarray(ids.astype(np.uint8)).save(f'{d}/id_Ch49_{s}_Diffuse.png')
    Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(f'{d}/Ch49_{s}.png')
    print(s, 'done')
Image.open('/tmp/claude-0/x/add/Ch33_face_skimask_black_cobrarecruit.png').save(f'{d}/face.png')
Image.open(f'{A}Ch33_hair_duke.png').save(f'{d}/hair.png')
json.dump({'id': cid, 'name': 'Cobra Recruit', 'drop_hair': True, 'hair_tones': [[0, 0, 0]] * 3, 'mirror': False,
           'drop_ids': [57]}, open(f'{d}/meta.json', 'w'), indent=1)
