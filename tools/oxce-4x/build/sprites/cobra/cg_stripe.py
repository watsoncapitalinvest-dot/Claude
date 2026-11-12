"""Crimson Guard leg stripes, redrawn by position: a continuous silver stripe down the outermost line of each trouser leg.
(paint_crimson.py picked the stripe by surface normal, which Ch49's uneven mesh breaks into fragments.)
Usage: python3 cg_stripe.py <char_dir> [width_m=0.011]"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
PM = '/tmp/claude-0/fac/posmap'
d = sys.argv[1]; WID = float(sys.argv[2]) if len(sys.argv) > 2 else 0.011
def up(a): return np.repeat(np.repeat(a, 2, 0), 2, 1)
def enc(i): return int(round(i * 255 / 40))
TROU, STRIPE, SILVER = 38, enc(15), np.array((200, 202, 208), np.float32)
for s in ('1001', '1002'):
    P = up(np.load(f'{PM}/pos_Ch49_{s}.npy')); has = ~np.isnan(P[..., 0])
    X, Y, Z = (np.nan_to_num(P[..., k]) for k in range(3))
    ip = f'{d}/id_Ch49_{s}_Diffuse.png'; ids = np.asarray(Image.open(ip)); ids = (ids[..., 0] if ids.ndim == 3 else ids).copy()
    img = np.asarray(Image.open(f'{d}/Ch49_{s}.png').convert('RGB')).astype(np.float32)
    trou_m = has & (ids == TROU)
    if trou_m.sum() < 1000: continue
    red = np.median(img[trou_m], 0)
    old = has & (ids == STRIPE); img[old] = red; ids[old] = TROU            # remove the fragmented stripe
    leg = has & (ids == TROU) & (Z > 0.40) & (Z < 0.92)
    new = np.zeros_like(leg)
    for sg in (1, -1):
        side = leg & (np.sign(X) == sg)
        for z0 in np.arange(0.40, 0.92, 0.01):
            b = side & (Z >= z0) & (Z < z0 + 0.01)
            if b.sum() < 20: continue
            xm = np.percentile(np.abs(X[b]), 99.5)
            yc = np.median(Y[b & (np.abs(X) > xm - 0.004)])
            new |= b & (np.abs(X) > xm - WID) & (np.abs(Y - yc) < 0.03)
    new = ndi.binary_closing(new, iterations=2) & leg
    img[new] = SILVER; ids[new] = STRIPE
    g = ndi.binary_dilation(new, iterations=3) & ~has; img[g] = SILVER; ids[g] = STRIPE
    Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(f'{d}/Ch49_{s}.png'); Image.fromarray(ids.astype(np.uint8)).save(ip)
    print(s, 'old stripe', int(old.sum()), 'new stripe', int(new.sum()))
