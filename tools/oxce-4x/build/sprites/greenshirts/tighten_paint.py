"""Tighten the paint on Ch49 body textures: smooth the ragged edges between colour regions and clear stray specks.
1. Garment-ID map: masked majority filter (only real texels vote, UV-island borders untouched), so region edges
   become smooth curves instead of the Mixamo paint's ragged steps. Hand-made decals (throat V, buckle, ...) are kept.
2. Colour: texels whose region changed get that region's flat colour.
3. Pen/crease marks inside shirt + trousers: drop small specks (< MINPEN texels), smooth the kept strokes.
Usage: python3 tighten_paint.py <char_dir> [size=9] [minpen=500]"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
PM = __import__('os').environ.get('POSMAP', '/tmp/claude-0/ws/posmap49')   # factory_ch49.py --posmap output
d = sys.argv[1]; SZ = int(sys.argv[2]) if len(sys.argv) > 2 else 9; MINPEN = int(sys.argv[3]) if len(sys.argv) > 3 else 500
def up(a): return np.repeat(np.repeat(a, 2, 0), 2, 1)
def enc(i): return int(round(i * 255 / 40))
KEEP = {enc(i) for i in range(12, 20)} | {102}            # decals (thigh straps, buckle, badges, throat V ...) stay as painted
CLOTH = (19, 38)
for s in ('1001', '1002'):
    has = ~np.isnan(up(np.load(f'{PM}/pos_Ch49_{s}.npy'))[..., 0])
    ip = f'{d}/id_Ch49_{s}_Diffuse.png'; ids = np.asarray(Image.open(ip)); ids = (ids[..., 0] if ids.ndim == 3 else ids).copy()
    img = np.asarray(Image.open(f'{d}/Ch49_{s}.png').convert('RGB')).astype(np.float32)
    # flat colour per region = median of its non-pen texels
    lum = img.mean(-1); flat = {}
    for v in np.unique(ids[has]):
        m = has & (ids == v)
        if m.sum() < 50: continue
        flat[v] = np.median(img[m & (lum > np.median(lum[m]) * 0.6)], 0) if (m & (lum > np.median(lum[m]) * 0.6)).any() else np.median(img[m], 0)
    # 1. masked majority filter
    vals = [v for v in flat if v not in KEEP]
    best = np.full(ids.shape, -1.0, np.float32); win = ids.copy()
    for v in vals:
        c = ndi.uniform_filter((has & (ids == v)).astype(np.float32), SZ)
        b = c > best; best[b] = c[b]; win[b] = v
    ch = has & (win != ids) & ~np.isin(ids, list(KEEP)) & np.isin(win, vals)
    ids[ch] = win[ch]
    for v in vals:
        m = ch & (ids == v); img[m] = flat[v]
    # 3. pen marks in cloth: keep long strokes, drop specks, smooth edges
    npen = 0
    for v in (() if __import__('os').environ.get('NOPEN') else CLOTH):      # NOPEN=1 for camo: its dark patches are not pen specks
        if v not in flat: continue
        m = has & (ids == v)
        pen = m & (img.mean(-1) < flat[v].mean() * 0.55)
        lab, n = ndi.label(pen, np.ones((3, 3)))
        if n:
            sz = ndi.sum(pen, lab, range(1, n + 1)); small = np.isin(lab, [i for i, z in enumerate(sz, 1) if z < MINPEN])
            img[small] = flat[v]; pen &= ~small
        sm = ndi.binary_opening(ndi.binary_closing(pen, iterations=2), iterations=1) & m
        img[pen & ~sm] = flat[v]
        add = sm & ~pen; img[add] = flat[v] * 0.2 + np.array((40, 26, 18), np.float32) * 0.8
        npen += int(sm.sum())
    Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(f'{d}/Ch49_{s}.png'); Image.fromarray(ids.astype(np.uint8)).save(ip)
    print(s, 'region texels smoothed', int(ch.sum()), 'pen texels kept', npen)
