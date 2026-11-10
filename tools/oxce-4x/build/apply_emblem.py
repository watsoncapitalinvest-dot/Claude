"""Put the Cobra sigil on the banner, the flag and the signed corrugated panel.
The emblem arrives as flat art on white, so the white is keyed out; on the dark red cloth it is
recoloured to read at tile size, and left red on dark steel where red already shows.
usage: apply_emblem.py <art dir>"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage
ART = sys.argv[1]

def logo(rgb=None, soft=1.0):
    a = np.array(Image.open('cobra_logo.png').convert('RGB')).astype(np.float32)
    mx, mn = a.max(-1), a.min(-1)
    al = np.clip((235 - mn) / 60, 0, 1)                    # white paper out, ink kept
    al *= np.clip((mx - mn) / 40 + (255 - mx) / 60, 0, 1)  # keep the grey anti-aliased rim too
    al = np.clip(al, 0, 1)
    if rgb is None:
        out = a
    else:
        k = np.clip(a.mean(-1, keepdims=True) / 200.0, 0.55, 1.0)   # keep the ink's own shading
        out = np.array(rgb, np.float32) * k
    im = Image.fromarray(np.dstack([out, al * 255 * soft]).astype(np.uint8), 'RGBA')
    bb = im.getbbox()
    return im.crop(bb) if bb else im

def cloth(path):
    """the bbox of the cloth itself, ignoring the magenta around it"""
    a = np.array(Image.open(path).convert('RGB')).astype(np.int16)
    mag = (np.minimum(a[..., 0], a[..., 2]) - a[..., 1]) > 60
    nz = np.argwhere(~mag)
    return int(nz[:, 1].min()), int(nz[:, 0].min()), int(nz[:, 1].max()) + 1, int(nz[:, 0].max()) + 1

def redcloth(path):
    """only the red cloth: the flag art also holds a grey pole and base, and measuring the emblem
    against the whole picture made it taller than the flag it had to sit on"""
    a = np.array(Image.open(path).convert('RGB')).astype(np.int16)
    mag = (np.minimum(a[..., 0], a[..., 2]) - a[..., 1]) > 60
    red = (a[..., 0] - np.maximum(a[..., 1], a[..., 2]) > 25) & ~mag
    red = ndimage.binary_opening(red, np.ones((9, 9)))
    nz = np.argwhere(red)
    return int(nz[:, 1].min()), int(nz[:, 0].min()), int(nz[:, 1].max()) + 1, int(nz[:, 0].max()) + 1

def place(src, dst, em, frac, cx=None, cy=None, only_red=False):
    base = Image.open(src).convert('RGB')
    x0, y0, x1, y1 = redcloth(src) if only_red else cloth(src)
    h = int((y1 - y0) * frac)
    w = max(1, round(em.width * h / em.height))
    e = em.resize((w, h), Image.LANCZOS)
    px = int(cx * (x1 - x0) + x0) - w // 2 if cx is not None else (x0 + x1) // 2 - w // 2
    py = int(cy * (y1 - y0) + y0) - h // 2 if cy is not None else (y0 + y1) // 2 - h // 2
    out = base.convert('RGBA'); out.alpha_composite(e, (px, py))
    out.convert('RGB').save(dst)
    return (x1 - x0, y1 - y0, w, h)

CREAM = (238, 232, 220)
print('banner  ', place(f'{ART}/banner_cobra.png', f'{ART}/banner_cobra_e.png', logo(CREAM), 0.62))
# the flag flies to the right of the pole: keep the sigil off the hoist and out of the fly's curl
print('flagpole', place(f'{ART}/flagpole.png', f'{ART}/flagpole_e.png', logo(CREAM), 0.52, cx=0.58, cy=0.46, only_red=True))
