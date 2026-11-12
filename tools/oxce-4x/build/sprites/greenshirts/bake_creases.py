"""Pen-shading step 1 of 2: bake the cloth's fold creases into a character's Ch49 textures as thin ink.
Creases come from Ch49's original shaded cloth texture (difference of Gaussians), only on the shirt (ID 19) and
trousers (ID 38), away from UV-island borders. Step 2 is at render time: factory_blend.py --shade, then
compose_factory.py with PENIDS=3,6 PENPCT=76 PENDARK=0.72 (shadow tone + pen strokes along the sculpted folds).
Usage: python3 bake_creases.py <char_dir_with_Ch49_1001.png_and_Ch49_1002.png> [id_map_dir]"""
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
A = __import__('os').environ.get('DUKE_DIR', '/mnt/user-data/uploads/GIJoe_XCOM_4x/Reference/models/mixamo/painted/duke/')      # Ch49_100x_Diffuse.png (shaded cloth) + anim/id maps
d = sys.argv[1]; idd = sys.argv[2] if len(sys.argv) > 2 else None
for s in ('1001', '1002'):
    p = f'{d}/Ch49_{s}.png'; img = np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
    idp = f'{idd}/id_Ch49_{s}_Diffuse.png' if idd and os.path.exists(f'{idd}/id_Ch49_{s}_Diffuse.png') else f'{A}anim/id_Ch49_{s}_Diffuse.png'
    ids = np.asarray(Image.open(idp)); ids = ids[..., 0] if ids.ndim == 3 else ids
    orig = np.asarray(Image.open(f'{A}Ch49_{s}_Diffuse.png').convert('RGB')).astype(np.float32).mean(-1)
    dog = ndi.gaussian_filter(orig, 2.5) - ndi.gaussian_filter(orig, 10)
    total = 0
    for gid in (19, 38):
        cl = ids == gid
        if cl.sum() < 1000: continue
        cr = cl & (dog < -1.8 * np.median(np.abs(dog[cl]))) & ndi.binary_erosion(cl, iterations=8)
        cr = ndi.binary_opening(cr, iterations=1); lab, n = ndi.label(cr, np.ones((3, 3)))
        if n: sz = ndi.sum(cr, lab, range(1, n + 1)); cr &= np.isin(lab, [i for i, z in enumerate(sz, 1) if z >= 150])
        img[cr] = img[cr] * 0.2 + np.array((40, 26, 18), np.float32) * 0.8; total += int(cr.sum())
    Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(p); print(s, 'crease texels', total)
