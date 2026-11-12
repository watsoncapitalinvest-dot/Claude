r"""Cartoon-cast member -> a factory char dir (cc\<name>\ sheets + Duke's base garment-ID maps + meta.json), with the
ID maps moved to follow the cast's own belt: repaint2.py painted the belt at 0.600-0.642 x height and made the
0.49-0.60 band shirt, while Duke's maps still put belt (id 5) on the old 0.49-0.53 hip band. Without this the ink
draws the belt edges across the shirt and none at the painted belt, and tighten_paint.py flattens the wrong colours.
  python3 cast_dir.py <cc dir> <name> <out root>"""
import sys, os, json, shutil, numpy as np
from PIL import Image
cc, name, root = sys.argv[1:4]
src = f'{cc}/{name}'; d = f'{root}/{name}'; os.makedirs(d, exist_ok=True)
PM = os.environ.get('POSMAP', '/tmp/claude-0/ws/posmap49'); DUKE = os.environ.get('DUKE_IDS', '/mnt/user-data/uploads/GIJoe_XCOM_4x/Reference/models/mixamo/painted/duke/anim')
rec = json.load(open(f'{src}/{name}_cartoon.json')); H = json.load(open(f'{PM}/meta.json'))['h49']
b0, b1 = [f * H for f in rec.get('belt_band', [0.60, 0.642])]
def up(a): return np.repeat(np.repeat(a, 2, 0), 2, 1)
SHIRT, BELT, TROU = 19, 32, 38
for s in ('1001', '1002'):
    im = Image.open(f'{src}/Ch49_{s}_Diffuse.png').convert('RGB')        # some sheets are 4096: the posmap tools work at 2048
    (im.resize((2048, 2048), Image.LANCZOS) if im.size != (2048, 2048) else im).save(f'{d}/Ch49_{s}.png')
    ids = np.asarray(Image.open(f'{DUKE}/id_Ch49_{s}_Diffuse.png').convert('L')).copy()
    P = up(np.load(f'{PM}/pos_Ch49_{s}.npy')); has = ~np.isnan(P[..., 0]); X, Z = np.nan_to_num(P[..., 0]), np.nan_to_num(P[..., 2])
    torso = has & (np.abs(X) < 0.30) & (Z > 0.75) & (Z < 1.25) & np.isin(ids, (SHIRT, BELT, TROU))
    new = ids.copy()
    new[torso & (Z >= b0) & (Z <= b1)] = BELT
    new[torso & (Z > b1)] = SHIRT
    new[torso & (Z < b0) & (Z >= 0.49 * H)] = SHIRT
    new[torso & (Z < 0.49 * H) & (ids == BELT)] = TROU
    print(name, s, 'texels re-id', int((new != ids).sum()))
    Image.fromarray(new).save(f'{d}/id_Ch49_{s}_Diffuse.png')
for f in ('face.png', 'hair.png', 'face18.png'):
    if os.path.exists(f'{src}/{f}'): shutil.copy(f'{src}/{f}', f'{d}/{f}')
hair = rec['colors']['hair']
json.dump({'id': name, 'name': name, 'drop_hair': False, 'mirror': False, 'skin': rec['colors']['skin'],
           'shirt': rec['colors']['shirt'], 'collar': rec['colors']['collar'],
           'hair_tones': [hair, [c * 0.86 for c in hair], [c * 0.39 for c in hair]]}, open(f'{d}/meta.json', 'w'), indent=1)
