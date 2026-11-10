"""The Cobra sigil pad on the compound floor - emb0..emb3.

Not an embankment, whatever the name says: na_blocks lays the four of them as a 2x2 of floor
inside a concrete fill, and together they are one big Cobra sigil painted on the ground.

The sigil itself is already drawn correctly and split across the four tiles in the right places,
so it is kept exactly as it is. What is replaced is the ground under it, which was flat grey at
150 against the surrounding concrete floor's 119 - no texture and thirty levels too bright, so
the pad read as a white patch rather than as paint on the same slab.

usage: apply_cobra_pad.py <materials dir>
"""
import sys, json, glob, numpy as np
from PIL import Image

MAT = sys.argv[1]
SS = 4
FW, FH = 128 * SS, 160 * SS
N = 1024
FOLDER = 'cobratiles'


def even(im):
    a = np.array(im.convert('RGB')).astype(np.float32)
    a = a[256:768, 256:768]; n = a.shape[0]
    t = np.abs(np.linspace(-1, 1, n)); w = np.clip((1 - t) * 2.2, 0, 1)
    w2 = np.maximum(np.outer(w, np.ones(n)), 0) * np.outer(np.ones(n), w)
    r = np.roll(a, (n // 2, n // 2), (0, 1))
    return np.clip(a * w2[..., None] + r * (1 - w2[..., None]), 0, 255).astype(np.uint8)


def diamond(tex):
    T = Image.fromarray(tex); n = T.width
    hw, hh = 64 * SS, 32 * SS; cx, cy = 64 * SS, 128 * SS
    a = n / (2 * hw); b = n / (2 * hh)
    coef = (a, b, -a * cx - b * (cy - hh), -a, b, a * cx - b * (cy - hh))
    out = T.convert('RGBA').transform((FW, FH), Image.AFFINE, coef, Image.BICUBIC)
    yy, xx = np.mgrid[0:FH, 0:FW]
    inside = (np.abs(xx + 0.5 - cx) / hw + np.abs(yy + 0.5 - cy) / hh) <= 1.0
    o = np.array(out); o[..., 3] = np.where(inside, 255, 0)
    return Image.fromarray(o)


def tile_path(name):
    names = json.load(open(f'{FOLDER}/names.json'))
    i = names.index(name)
    return (glob.glob(f'{FOLDER}/{i:02d}_{name}.png') + glob.glob(f'{FOLDER}/{i:03d}_{name}.png'))[0]


# The slab under the paint is the compound's own floor tile, not a material square.
#
# Generating a concrete_mil diamond here looked obviously right and was wrong: 'conc' is not
# built from concrete_mil - it is not in apply_mats' FLATS at all - so a generated slab came out
# at 66 against the floor's 119 and the pad went from a patch thirty levels too bright to one
# fifty levels too dark. Taking the floor tile itself means the pad matches whatever 'conc'
# becomes later, including if it is repainted.
slab = np.array(Image.open(tile_path('conc')).convert('RGBA')).astype(np.float32)

names = set(json.load(open(f'{FOLDER}/names.json')))
done, missing = 0, []
for i in range(4):
    t = f'emb{i}'
    if t not in names:
        missing.append(t); continue
    p = tile_path(t)
    a = np.array(Image.open(p).convert('RGBA')).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3]
    # how red a pixel is, which is what tells the paint from the slab it is painted on
    red = np.clip((rgb[..., 0] - np.maximum(rgb[..., 1], rgb[..., 2]) - 15) / 60.0, 0, 1)
    red *= (al > 8)
    out = slab.copy()
    out[..., :3] = slab[..., :3] * (1 - red[..., None]) + rgb * red[..., None]
    # the pad keeps the footprint it had, not the whole diamond
    out[..., 3] = np.maximum(np.minimum(slab[..., 3], al), red * 255)
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA').save(p)
    done += 1

print('cobra pad tiles', done)
if missing:
    print('no such tile:', ' '.join(missing))
