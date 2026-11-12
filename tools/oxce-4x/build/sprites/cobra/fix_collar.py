"""Clean collar for Ch49 characters: repaint the shirt collar as a smooth ring around the neck (body space, via the
position maps) in both the texture and the garment-ID map, so the ink line along the collar is a clean curve instead
of the ragged Mixamo paint edge. Use with factory_blend.py --clean_collar (plane cuts at the neck).
Usage: python3 fix_collar.py <char_dir> [collar_rgb] [shirt_rgb] [rx] [ry] [zmin]
  defaults: collar = median of the current collar texels, COLLAR_GAP env = front V half-width (default 0.034 m), shirt = median shirt texel, rx 0.115, ry 0.100, zmin 1.44"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
PM = '/tmp/claude-0/fac/posmap'
d = sys.argv[1]
def rgb(i, dflt):
    return np.array([float(v) for v in sys.argv[i].split(',')], np.float32) if len(sys.argv) > i and sys.argv[i] != '-' else dflt
def up(a): return np.repeat(np.repeat(a, 2, 0), 2, 1)
RX = float(sys.argv[4]) if len(sys.argv) > 4 else 0.115; RY = float(sys.argv[5]) if len(sys.argv) > 5 else 0.100
ZMIN = float(sys.argv[6]) if len(sys.argv) > 6 else 1.44
CX, CY = 0.0, 0.01                                   # neck axis in the Ch49 rest frame
COL_ID, SHIRT_ID, OPEN = 26, 19, (19, 26, 255, 45)   # 45 here = the old throat patch, not boots       # encoded id values (round(id*255/40))
SHIRT_REF = None
for s in ('1002', '1001'):                         # 1002 first: it holds the shirt; 1001 reuses its colours
    P = up(np.load(f'{PM}/pos_Ch49_{s}.npy')); has = ~np.isnan(P[..., 0])
    X, Y, Z = (np.nan_to_num(P[..., k]) for k in range(3))
    ip = f'{d}/id_Ch49_{s}_Diffuse.png'; ids = np.asarray(Image.open(ip)); ids = (ids[..., 0] if ids.ndim == 3 else ids).copy()
    img = np.asarray(Image.open(f'{d}/Ch49_{s}.png').convert('RGB')).astype(np.float32)
    old = has & (ids == COL_ID)
    col = rgb(2, np.median(img[old], 0) if old.sum() > 500 else np.array((63, 87, 32), np.float32))
    sh = has & (ids == SHIRT_ID) & (Z > 1.38)
    shirt = rgb(3, SHIRT_REF if SHIRT_REF is not None else (np.median(img[sh], 0) if sh.sum() > 500 else np.array((242, 176, 55), np.float32)))
    if SHIRT_REF is None: SHIRT_REF = shirt
    e = ((X - CX) / RX) ** 2 + ((Y - CY) / RY) ** 2
    zone = has & (Z > 1.36) & (e < 2.6) & np.isin(ids, OPEN)          # the area we own around the neck
    ring = zone & (e < 1.0) & (Z > ZMIN)
    # open front: a V at the throat, widest at the collar top, closing to a point lower down (skin shows through)
    GAP = float(__import__('os').environ.get('COLLAR_GAP', '0.034'))          # half-width at the collar top (m); 0 = closed
    vee = ring & (Y < CY - 0.02) & (np.abs(X - CX) < GAP * np.clip((Z - 1.425) / (1.505 - 1.425), 0, 1))
    if s not in __import__('os').environ.get('COLLAR_GAP_SHEETS', '1001,1002'): vee &= False
    ring &= ~vee
    body = zone & ~ring & ~vee
    img[ring] = col; ids[ring] = COL_ID
    img[vee] = np.array((250, 170, 76), np.float32); ids[vee] = 102     # Duke's body skin tone; id 16 = throat V (compose joins it to the neck, no inner ink)
    fix = body & (ids != SHIRT_ID)                                      # old ragged collar/undershirt outside the ring -> shirt
    img[fix] = shirt; ids[fix] = SHIRT_ID
    # bleed into the UV-island border texels the position map missed (else old collar paint shows as dashes on seams)
    gap = ~has
    for m, c, v in ((fix, shirt, SHIRT_ID), (ring, col, COL_ID), (vee, np.array((250, 170, 76), np.float32), 102)):
        g = ndi.binary_dilation(m, iterations=5) & gap
        img[g] = c; ids[g] = v
    Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(f'{d}/Ch49_{s}.png')
    Image.fromarray(ids.astype(np.uint8)).save(ip)
    print(s, 'ring', int(ring.sum()), 'to shirt', int(fix.sum()), 'collar', col, 'shirt', shirt)
