"""Belt up at the waist on Ch49 (Duke's art: shirt tucked in, belt with a square buckle, trousers start under it).
Ch49's own belt (garment id 32) is a low hip band under a ragged shirt hem; this repaints by body position:
  - old hip band + shirt below the new belt -> trousers (shirt tucked in, ragged hem gone)
  - new belt band Z0..Z1 over shirt/trousers (keeps id 32 so it gets its ink outline), webbing stays on top
  - square buckle frame front centre (own id 17 so it's outlined)
Usage: python3 belt_up.py <char_dir> [belt_rgb|-|trou] [z0] [z1] [buckle_rgb]   (trou = tuck the shirt in, no belt)   (defaults: Ch49 belt colour, 0.975, 1.035, belt x0.62)"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
PM = '/tmp/claude-0/fac/posmap'
d = sys.argv[1]
def up(a): return np.repeat(np.repeat(a, 2, 0), 2, 1)
def enc(i): return int(round(i * 255 / 40))
Z0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.975; Z1 = float(sys.argv[4]) if len(sys.argv) > 4 else 1.035
SHIRT, BELT, TROU, BUCKLE = 19, 32, 38, enc(17)
for s in ('1001', '1002'):
    P = up(np.load(f'{PM}/pos_Ch49_{s}.npy')); N = up(np.load(f'{PM}/nrm_Ch49_{s}.npy')); has = ~np.isnan(P[..., 0])
    X, Y, Z = (np.nan_to_num(P[..., k]) for k in range(3))
    ip = f'{d}/id_Ch49_{s}_Diffuse.png'; ids = np.asarray(Image.open(ip)); ids = (ids[..., 0] if ids.ndim == 3 else ids).copy()
    img = np.asarray(Image.open(f'{d}/Ch49_{s}.png').convert('RGB')).astype(np.float32)
    tr = has & (ids == TROU) & (Z > 0.75) & (Z < 0.88)
    if tr.sum() < 500: continue
    trou = np.median(img[tr], 0)
    ob = has & (ids == BELT)
    if ob.sum() < 500 and not (len(sys.argv) > 2 and sys.argv[2] != '-'):
        print(s, 'no belt on this sheet - skipped'); continue
    belt = np.array([float(v) for v in sys.argv[2].split(',')], np.float32) if len(sys.argv) > 2 and sys.argv[2] not in ('-', 'trou') else trou
    if len(sys.argv) > 2 and sys.argv[2] == 'trou':
        # no belt: just tuck the shirt in (old hip band + shirt below Z1 -> trousers, no band, no buckle) - for figures
        # whose only belt is the webbing belt (Cobra troopers); removes the ragged Ch49 hem with a single clean waist seam
        low = has & (np.abs(X) < 0.30) & (Z > 0.80) & (Z < 1.10) & (ob | ((ids == SHIRT) & (Z < Z1)))
        img[low] = trou; ids[low] = TROU
        g = ndi.binary_dilation(low, iterations=4) & ~has; img[g] = trou; ids[g] = TROU
        Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(f'{d}/Ch49_{s}.png'); Image.fromarray(ids.astype(np.uint8)).save(ip)
        print(s, 'tucked (no belt)', int(low.sum())); continue
    torso = has & (np.abs(X) < 0.30) & (Z > 0.80) & (Z < 1.10)
    low = torso & (ob | ((ids == SHIRT) & (Z < Z0)))                  # old hip band + shirt tail -> trousers
    img[low] = trou; ids[low] = TROU
    band = torso & np.isin(ids, (SHIRT, TROU)) & (Z >= Z0) & (Z <= Z1)
    img[band] = belt; ids[band] = BELT
    # square buckle frame (art: open rectangle), darker brass
    bz = (Z0 + Z1) / 2; hw, hh, t = 0.024, (Z1 - Z0) / 2 + 0.006, 0.0075
    box = has & (N[..., 1] < -0.5) & (np.abs(X) < hw) & (np.abs(Z - bz) < hh)
    inner = (np.abs(X) < hw - t) & (np.abs(Z - bz) < hh - t)
    fr = box & ~inner
    bk = np.array([float(v) for v in sys.argv[5].split(',')], np.float32) if len(sys.argv) > 5 else belt * 0.62
    img[fr] = bk; ids[fr] = BUCKLE
    # bleed into UV-border texels the position map missed
    gap = ~has
    for m, c, v in ((low, trou, TROU), (band, belt, BELT), (fr, bk, BUCKLE)):
        g = ndi.binary_dilation(m, iterations=4) & gap; img[g] = c; ids[g] = v
    Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(f'{d}/Ch49_{s}.png'); Image.fromarray(ids.astype(np.uint8)).save(ip)
    print(s, 'to trousers', int(low.sum()), 'belt', int(band.sum()), 'buckle', int(fr.sum()), 'belt col', belt, 'trou', trou)
