"""The design chat's ink pass (compose.py ink_frame), returning RGBA for the game."""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
BG = np.array([200, 200, 205], np.float32)
import os
# Duke's golden hair unless HAIR="r,g,b" is set (the cast recipes give each man's hair colour)
if os.environ.get('HAIR'):
    HAIR_BASE = np.array([float(x) for x in os.environ['HAIR'].split(',')], np.float32)
    HAIR_SHADOW = HAIR_BASE * 0.86; HAIR_LINE = np.clip(HAIR_BASE * 0.39, 0, 255)
else:
    HAIR_BASE = np.array([246, 182, 22], np.float32); HAIR_SHADOW = np.array([212, 140, 20], np.float32); HAIR_LINE = np.array([96, 58, 14], np.float32)
INK = np.array([40, 26, 18], np.float32)
SIZE = (512, 640); FINAL = (256, 320); DZ = 0.10

def ink_frame(beauty, idimg):
    b = beauty.resize(SIZE, Image.LANCZOS); a = np.asarray(b).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3] / 255.0
    idrgb = np.asarray(idimg.convert('RGB').resize(SIZE, Image.NEAREST)).astype(np.float32)
    idb = np.round(idrgb[..., 0] / 255 * 40).astype(np.int16)
    dep = idrgb[..., 1] / 255.0 * 4.0                        # metres, camera depth
    idb[al < 0.5] = 0
    img = rgb * al[..., None] + BG * (1 - al[..., None])
    H, W = idb.shape
    # hair: one clean mass
    hair = idb == 1
    if hair.any():
        r = 4; disk = np.hypot(*np.mgrid[-r:r+1, -r:r+1]) <= r
        clean = ndi.binary_fill_holes(ndi.binary_closing(hair, structure=disk))
        clean = ndi.binary_opening(clean, structure=np.hypot(*np.mgrid[-1:2, -1:2]) <= 1)
        gap = clean & ~hair & ((idb == 0) | (idb == 2)); img[gap] = HAIR_BASE; idb[gap] = 1
        spike = hair & ~clean; img[spike] = BG; idb[spike] = 0
        # flat two-tone fill over the whole cleaned hair shape (hides scalp showing between strands)
        lum = ndi.gaussian_filter(img.mean(-1), 2.5)
        thr = np.percentile(lum[clean], 30)
        tone = ndi.median_filter((lum > thr).astype(np.uint8), size=7)
        img[clean] = np.where(tone[clean][:, None] == 1, HAIR_BASE, HAIR_SHADOW)
        idb[clean] = 1
    fg = idb > 0
    e = np.zeros_like(fg); eh = np.zeros_like(fg); soft = np.zeros_like(fg)
    for dy, dx in ((0, 1), (1, 0)):
        a1 = idb[:H - dy, :W - dx]; a2 = idb[dy:, dx:]
        d1 = dep[:H - dy, :W - dx]; d2 = dep[dy:, dx:]
        diff = ((a1 != a2) & ((a1 > 0) | (a2 > 0))) | ((a1 > 0) & (a2 > 0) & (np.abs(d1 - d2) > DZ) & (a1 != 1) & (a2 != 1))
        hp = (a1 == 1) | (a2 == 1)
        outer = diff & hp & (((a1 == 1) & (a2 == 0)) | ((a1 == 0) & (a2 == 1)))
        sj = diff & hp & ~outer
        ee = diff & ~hp
        e[:H - dy, :W - dx] |= ee; e[dy:, dx:] |= ee
        eh[:H - dy, :W - dx] |= outer & (a1 == 1); eh[dy:, dx:] |= outer & (a2 == 1)
        soft[:H - dy, :W - dx] |= sj & (a1 == 1); soft[dy:, dx:] |= sj & (a2 == 1)
    e &= ndi.binary_dilation(fg, iterations=1) & (fg | ndi.binary_dilation(fg, iterations=1))
    e &= fg                                                     # line sits on the figure
    near_hair = ndi.binary_dilation(idb == 1, iterations=2); touches_bg = ndi.binary_dilation(idb == 0, iterations=1)
    e &= ~(near_hair & ~touches_bg)
    lab, n = ndi.label(e, structure=np.ones((3, 3)))
    if n:
        sz = ndi.sum(e, lab, range(1, n + 1)); e &= np.isin(lab, [i for i, z in enumerate(sz, 1) if z >= 10])
    if soft.any():
        band = ndi.binary_dilation(soft, iterations=1) & fg & ~e
        blur = np.stack([ndi.gaussian_filter(img[..., c], 0.8) for c in range(3)], -1); img[band] = blur[band]
    e = (ndi.binary_dilation(e, iterations=1) & fg)          # ~3 px at 2x, kept on the figure -> ~1.5 px at final size
    eh = ndi.binary_dilation(eh, iterations=1) & (idb == 1) & ~e
    # pen fold lines inside chosen garments (FOLD_IDS env, e.g. "6"): ink where the cel shadow meets the lit tone
    # pen lines inside chosen garments: FOLD_IDS="6:0.42,20:0.35" (garment id : share of it that counts as shadow).
    # Ink where the cel shadow meets the lit tone -> cloth folds on trousers, muscle carving on skin.
    for spec in [x for x in os.environ.get('FOLD_IDS', '').split(',') if x.strip()]:
        parts = spec.split(':'); fid = parts[0]; pct = parts[1] if len(parts) > 1 else '0.42'
        blur = float(parts[2]) if len(parts) > 2 else float(os.environ.get('FOLD_BLUR', '2.2')); fmin = int(parts[3]) if len(parts) > 3 else int(os.environ.get('FOLD_MIN', '30'))
        gm = idb == int(fid)
        if gm.sum() < 50: continue
        lum = ndi.gaussian_filter(img.mean(-1), blur)
        shadow = gm & (lum < np.percentile(lum[gm], 100 * float(pct)))
        shadow = ndi.binary_closing(ndi.binary_opening(shadow, iterations=2), iterations=1)
        fe = shadow & ~ndi.binary_erosion(shadow, iterations=1) & ndi.binary_erosion(gm, iterations=3)
        fl, fn = ndi.label(fe, structure=np.ones((3, 3)))
        if fn:
            fz = ndi.sum(fe, fl, range(1, fn + 1)); fe &= np.isin(fl, [i for i, z in enumerate(fz, 1) if z >= fmin])
        img[fe & ~e] = INK
    img[e] = INK
    img[eh] = HAIR_LINE
    # with alpha, for the game: the figure's own mask, downscaled premultiplied so
    # the edge carries no grey from the preview background
    alpha = (idb > 0).astype(np.float32)
    pm = np.dstack([img * alpha[..., None], alpha * 255])
    small = [np.asarray(Image.fromarray(pm[..., c].clip(0, 255).astype(np.uint8)).resize(FINAL, Image.LANCZOS)).astype(np.float32) for c in range(4)]
    a = small[3] / 255.0
    rgb = np.dstack(small[:3]) / np.maximum(a, 1e-3)[..., None]
    return Image.fromarray(np.dstack([rgb.clip(0, 255), small[3]]).astype(np.uint8), 'RGBA')

