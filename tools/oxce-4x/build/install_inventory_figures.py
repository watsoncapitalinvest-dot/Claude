#!/usr/bin/env python3
"""Install soldier figures for the equipment screen (INVENTORY_FIGURE_BRIEF.txt).

    python3 build/install_inventory_figures.py <delivery dir> <name>=<inv file stem> ... [--write]
    e.g.  ... snake_eyes=snake duke=duke roadblock=roadblock chuckles=chuckles

Each delivery is 640 x 1600 on magenta. The figure is keyed out, cropped to its
own outline and stood in the figure panel of the equipment page: feet on base
row 143, centred on base column 80.5, 94 base px tall - where the game has
always drawn the soldier, and inside the panel the painted page frames.

Two files per soldier, written over the old ones:
    Resources/Inventory/<stem>_inv.png      320 x 200, 8-bit, the game's own copy
    Resources/Inventory/<stem>_inv_hi.png   1920 x 1200, RGBA, what is shown
Both come from the same placement, so the sharp figure covers exactly the
pixels the 8-bit one does.
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_weapon_sprites as mws                          # noqa: E402

INV = os.path.normpath(os.path.join(HERE, '..', 'mod', 'Resources', 'Inventory'))
K = 6
FEET, CENTRE, TALL = 144, 80.5, 94


def keyed(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = ((r + b) / 2 - g)
    alpha = np.clip(255 - (m - 70) * 255 / 80, 0, 255).astype(np.uint8)
    spill = alpha < 250
    a[..., 0] = np.where(spill, np.minimum(r, g + 25), r)
    a[..., 2] = np.where(spill, np.minimum(b, g + 25), b)
    im = Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), 'RGBA')
    return im.crop(im.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox())


def place(fig):
    h = TALL * K
    w = max(1, round(fig.width * h / fig.height))
    fig = fig.resize((w, h), Image.LANCZOS)
    hi = Image.new('RGBA', (320 * K, 200 * K), (0, 0, 0, 0))
    hi.paste(fig, (round(CENTRE * K - w / 2), FEET * K - h), fig)
    return hi


def main(src, pairs, write):
    pal, legal, lp = mws.palette_and_legal()
    for name, stem in pairs:
        path = os.path.join(src, 'inv_%s.png' % name)
        hi = place(keyed(path))
        small = hi.resize((320, 200), Image.LANCZOS)
        a = np.asarray(small).copy()
        a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
        base = mws.quantise(Image.fromarray(a, 'RGBA'), pal, legal, lp)
        bb = Image.fromarray((np.asarray(base) > 0).astype(np.uint8) * 255).getbbox()
        print('%-12s -> %s_inv: base box x %d..%d y %d..%d' % (name, stem, bb[0], bb[2] - 1, bb[1], bb[3] - 1))
        if write:
            hi.save(os.path.join(INV, '%s_inv_hi.png' % stem))
            base.save(os.path.join(INV, '%s_inv.png' % stem))
    if write:
        print('written to', INV)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 2:
        sys.exit(__doc__)
    main(args[0], [tuple(p.split('=')) for p in args[1:]], '--write' in sys.argv)
