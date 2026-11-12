"""Garment-ID maps for the pilot (Ace paint on Ch15 / Ch20), which shipped without any: each texel goes to the
nearest garment colour of the Ace recipe (base, x0.58 / x0.62 shadow or x1.13 highlight tone). Dark paint (black
gear AND the ink lines painted into the sheets) only counts as black gear where it is thick; thin ink strokes take
the id of the paint around them, so the ink pass does not outline every painted line twice.
Written ids: suit cloth 20, everything else 21. The ink pass is told to treat 21 as 20 for its lines
(render_cast.sh ink(): INKJOIN=21:20), so these maps add NO lines - the Ace sheets already have their garment
borders inked in, and a full per-garment map (tried: vest 21, gear 22, white 23, skin 24, blue 25) put a second
ink line on every painted strap and dappled the hands. Their only job is PENIDS=20: pen shading on the suit
cloth, never on the vest, gear, hands or helmet. The head (Ch20) keeps a flat id 2.
Usage: python3 gs_pilot_ids.py <pilot_ace dir> <out dir>"""
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
src, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
PAL = {20: (214, 160, 44), 21: (232, 98, 48), 22: (30, 30, 34), 23: (238, 238, 232), 24: (236, 176, 118), 25: (40, 62, 130)}
HEAD = {23: 26, 21: 27, 22: 28}           # head sheet: white -> helmet, orange-red -> stripe, dark -> visor
for f in ('Ch15_1001', 'Ch15_1002'):
    img = np.asarray(Image.open(f'{src}/{f}_Diffuse.png').convert('RGB')).astype(np.float32)
    best = np.full(img.shape[:2], 1e9, np.float32); lab = np.zeros(img.shape[:2], np.uint8)
    for v, c in PAL.items():
        for t in (1.0, 0.58, 0.62, 1.13):
            dd = np.linalg.norm(img - np.minimum(np.array(c, np.float32) * t, 255), axis=-1)
            b = dd < best; best[b] = dd[b]; lab[b] = v
    dark = lab == 22
    thick = ndi.binary_dilation(ndi.binary_opening(dark, iterations=3), iterations=3) & dark
    thin = dark & ~thick
    _, (iy, ix) = ndi.distance_transform_edt(thin, return_indices=True)     # nearest non-thin texel
    lab[thin] = lab[iy[thin], ix[thin]]
    lab = ndi.median_filter(lab, size=3)
    lab = np.where(lab == 20, 20, 21).astype(np.uint8)
    enc = np.round(lab.astype(np.float32) * 255 / 40).astype(np.uint8)
    Image.fromarray(enc).save(f'{out}/id_{f}_Diffuse.png')
    print(f, {int(v): int((lab == v).sum()) for v in np.unique(lab)})
