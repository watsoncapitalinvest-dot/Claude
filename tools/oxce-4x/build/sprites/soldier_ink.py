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

def _shade_for(idimg):
    """the geometry-shading pass next to an ID frame (render_char.py --shade writes <frame>_shade.png)"""
    p = getattr(idimg, 'filename', '') or ''
    if p.endswith('_id.png') and os.path.exists(p[:-7] + '_shade.png'):
        return Image.open(p[:-7] + '_shade.png')
    return None


def pen_pass(img, idb, fg, shade, size):
    """Comic pen shading = the shade branch of the design chat's compose_factory.py ink() (Duke v3), same rules:
    a shadow tone (x0.70) where the sculpted folds turn from the key light and pen strokes along the sharpest fold
    edges, on the garment ids in PENIDS only; PENFACE=1 adds a light shadow + short strokes on the face/neck.
    Env: PENIDS (e.g. 3,6), PENPCT (93), PENDARK (0.62), PENFACE, PENFACEIDS (2,16), PENFACEDARK (0.72),
    PENFACETONE (0.84), PENFACEPCT (95). Applies the shadow tones to img; returns (pen, facepen) stroke masks."""
    H = idb.shape[0]; sc_ = max(1, round(H / 640))
    S = np.asarray(shade.convert('L').resize(size, Image.BILINEAR)).astype(np.float32)
    S = ndi.gaussian_filter(S, 1.2 * sc_ / 2)
    gm = np.hypot(ndi.sobel(S, 0), ndi.sobel(S, 1))
    cloth = fg & np.isin(idb, [int(x) for x in os.environ['PENIDS'].split(',')])
    pen = np.zeros_like(fg); facepen = None
    if cloth.sum() > 50:
        ref = np.percentile(S[cloth], 70)
        dark = cloth & (S < ref * float(os.environ.get('PENDARK', 0.62)))
        dark = ndi.binary_opening(ndi.binary_closing(dark, iterations=1), iterations=sc_)
        img[dark] = img[dark] * 0.70
        ridge = cloth & (gm > np.percentile(gm[cloth], float(os.environ.get('PENPCT', 93)))) & ndi.binary_erosion(fg, iterations=2 * sc_)
        ridge &= dark | ndi.binary_dilation(dark, iterations=1)
        lab, n = ndi.label(ridge, structure=np.ones((3, 3)))
        if n:
            sz = ndi.sum(ridge, lab, range(1, n + 1)); ridge &= np.isin(lab, [i for i, z in enumerate(sz, 1) if z >= 10 * sc_ * sc_])
        pen |= ridge
    if os.environ.get('PENFACE'):
        face = fg & np.isin(idb, [int(x) for x in os.environ.get('PENFACEIDS', '2,16').split(',')]) & ndi.binary_erosion(fg, iterations=2 * sc_)
        if face.sum() > 200:
            fref = np.percentile(S[face], 70)
            fd = face & (S < fref * float(os.environ.get('PENFACEDARK', 0.72)))
            fd = ndi.binary_opening(ndi.binary_closing(fd, iterations=1), iterations=sc_)
            img[fd] = img[fd] * float(os.environ.get('PENFACETONE', 0.84))
            fr = face & (gm > np.percentile(gm[face], float(os.environ.get('PENFACEPCT', 95)))) & (fd | ndi.binary_dilation(fd, iterations=1))
            lab, n = ndi.label(fr, structure=np.ones((3, 3)))
            if n:
                sz = ndi.sum(fr, lab, range(1, n + 1)); fr &= np.isin(lab, [i for i, z in enumerate(sz, 1) if z >= 14 * sc_ * sc_])
            facepen = fr
    return pen, facepen


def ink_frame(beauty, idimg, shade=None):
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
    # throat V (garment id 16, painted skin by fix_collar.py): joins the neck skin (id 2) with no line and no
    # depth-jump ink inside it (compose_factory.py's rule; no older id map uses 16, so nothing else changes)
    ide = np.where(idb == 16, 2, idb); nod = idb == 16
    # INKJOIN="a:b,...": id a draws its lines as if it were id b (an id kept apart only for PENIDS, e.g. the pilot)
    for pair in [x for x in os.environ.get('INKJOIN', '').split(',') if x.strip()]:
        ja, jb = (int(v) for v in pair.split(':')); ide = np.where(ide == ja, jb, ide)
    for dy, dx in ((0, 1), (1, 0)):
        a1 = ide[:H - dy, :W - dx]; a2 = ide[dy:, dx:]
        n1 = nod[:H - dy, :W - dx] | nod[dy:, dx:]
        d1 = dep[:H - dy, :W - dx]; d2 = dep[dy:, dx:]
        diff = ((a1 != a2) & ((a1 > 0) | (a2 > 0))) | ((a1 > 0) & (a2 > 0) & (np.abs(d1 - d2) > DZ) & (a1 != 1) & (a2 != 1) & ~n1)
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
    # Roadblock-method fold lines (TERMIDS="3,6,11", TERMMIN=90): the design chat's compose_factory.py TERMIDS block
    # (Duke v4 / cast v3), same logic, same place in the order (after the soft hair blur, on the undilated outline):
    # inside chosen garments, a line where the baked shadow tone meets the lit tone; long pieces only. Drawn with the
    # pen (x0.25 + INK x0.75) further down. Unset -> nothing here runs and the output is unchanged.
    term = None
    if os.environ.get('TERMIDS'):
        lum = img.mean(-1); term = np.zeros_like(fg)
        for g in [int(x) for x in os.environ['TERMIDS'].split(',') if x.strip()]:
            m = (idb == g) & ndi.binary_erosion(fg, iterations=2)
            if m.sum() < 200: continue
            sh = m & (lum < np.percentile(lum[m], 75) * 0.79)
            sh = ndi.gaussian_filter(sh.astype(np.float32), 2.5) > 0.5
            ed = sh & ~ndi.binary_erosion(sh, iterations=1) & m
            term |= ed & (ndi.maximum_filter(idb, 3) == ndi.minimum_filter(idb, 3))
        lab, n = ndi.label(term, structure=np.ones((3, 3)))
        if n:
            sz = ndi.sum(term, lab, range(1, n + 1)); term &= np.isin(lab, [i for i, z in enumerate(sz, 1) if z >= int(os.environ.get('TERMMIN', 45))])
        tsc = max(1, round(H / 640))
        if tsc > 1: term = ndi.binary_dilation(term, iterations=max(0, tsc // 2)) & fg
    e = (ndi.binary_dilation(e, iterations=1) & fg)         # ~3 px at 2x, kept on the figure -> ~1.5 px at final size
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
    # comic pen shading from the geometry pass (render_char.py --shade); only when PENIDS is set
    pen = None; facepen = None
    if os.environ.get('PENIDS'):
        if shade is None: shade = _shade_for(idimg)
        if shade is not None:
            pen, facepen = pen_pass(img, idb, fg, shade, SIZE)
    if term is not None: pen = term if pen is None else (pen | term)     # one pen mask, inked once (as compose_factory)
    if pen is not None:
        img[pen & ~e] = img[pen & ~e] * 0.25 + INK * 0.75
        if facepen is not None: fp = facepen & ~e & ~pen; img[fp] = img[fp] * 0.45 + INK * 0.55
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

