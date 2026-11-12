r"""Greenshirt char dir from gs\<look>\ sheets: garment-ID maps that follow THIS paint, not Duke's.
gs repaint2.py moved the belt (0.535-0.580 x height) and put trousers below it, so on Duke's id maps the shirt /
belt / trouser ids sit in the wrong places (ink lines across the trousers, none at the real belt). Texels whose
Duke id is shirt, belt or trousers are re-assigned by their paint colour (nearest of the look's shirt / trousers /
belt colour, base or x0.66 shadow); painted pen marks take the id of the cloth around them.
Medic: the white armband and its red cross become id 14 (a decal id tighten_paint.py keeps).
Usage: python3 gs_ids.py <gs look dir> <duke id dir> <out char dir> <look json> [medic]"""
import sys, os, json, shutil, numpy as np
from PIL import Image
from scipy import ndimage as ndi
src, idd, out, look = sys.argv[1:5]; medic = len(sys.argv) > 5
os.makedirs(out, exist_ok=True)
L = json.load(open(look)); C = L.get('colors', L)
def enc(i): return int(round(i * 255 / 40))
SHIRT, BELT, TROU = 19, 32, 38
pal = {SHIRT: C['shirt'], TROU: C['trousers'], BELT: C['belt']}
INK = np.array((40, 26, 18), np.float32)
for s in ('1001', '1002'):
    img = np.asarray(Image.open(f'{src}/Ch49_{s}_Diffuse.png').convert('RGB')).astype(np.float32)
    ids = np.asarray(Image.open(f'{idd}/id_Ch49_{s}_Diffuse.png').convert('RGB'))[..., 0].copy()
    if ids.shape != img.shape[:2]: ids = np.asarray(Image.fromarray(ids).resize(img.shape[1::-1], Image.NEAREST)).copy()
    cl = np.isin(ids, (SHIRT, BELT, TROU))
    best = np.full(ids.shape, 1e9, np.float32); lab = ids.copy()
    for v, c in pal.items():
        for t in (1.0, 0.66, 0.86, 0.62):
            dd = np.linalg.norm(img - np.array(c, np.float32) * t, axis=-1)
            b = cl & (dd < best); best[b] = dd[b]; lab[b] = v
    pen = cl & (np.linalg.norm(img - INK, axis=-1) < best)          # ink marks: borrow the surrounding cloth's id
    known = cl & ~pen
    _, (iy, ix) = ndi.distance_transform_edt(~known, return_indices=True)
    lab[pen] = lab[iy[pen], ix[pen]]
    if medic:
        white = img.min(-1) > 205; red = (img[..., 0] > 150) & (img[..., 1] < 80) & (img[..., 2] < 80)
        band = ndi.binary_closing(white | red, iterations=2) & (white | red | ndi.binary_dilation(white, iterations=2))
        lab[band] = enc(14); print(s, 'medic armband texels', int(band.sum()))
    ch = int((lab != ids).sum()); ids = lab
    Image.fromarray(np.dstack([ids, np.zeros_like(ids), np.zeros_like(ids)]).astype(np.uint8)).save(f'{out}/id_Ch49_{s}_Diffuse.png')
    shutil.copy(f'{src}/Ch49_{s}_Diffuse.png', f'{out}/Ch49_{s}.png')
    print(s, 'texels re-id', ch, {v: int((ids == v).sum()) for v in (SHIRT, BELT, TROU)})
