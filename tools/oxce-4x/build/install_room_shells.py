#!/usr/bin/env python3
"""Install empty room shells from the graphics AI (BARE_ROOMS_BRIEF.txt).

    python3 build/install_room_shells.py <theme> <1x1.png> <2x1.png> <1x2.png> <2x2.png> [--write]

Each delivery is checked for the right shape (a 2x1 must be twice as wide as
tall), brought to exactly 192 px a square by area, and its magenta keyed out to
transparency - including the pink fringe a resample leaves on the edge - so
the base plan's grid shows round the room. Written to
mod/Resources/Base/shells/shell_<theme>_<WxH>.png, where the base view finds it.

It also reports where each door actually is against where the corridors meet
the room (the middle of every square edge), in base pixels, so a door that
came back out of place is known rather than noticed.
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'mod', 'Resources', 'Base', 'shells'))
SQ = 192
SIZES = [(1, 1), (2, 1), (1, 2), (2, 2)]


def key(im):
    a = np.asarray(im.convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = ((r + b) / 2 - g)
    alpha = np.clip(255 - (mag - 60) * 255 / 90, 0, 255)       # soft only in the fringe
    alpha[(r > 200) & (b > 200) & (g < 80)] = 0
    # pull the fringe's pink out: where partly keyed, take green as the cap
    spill = alpha < 250
    a[..., 0] = np.where(spill, np.minimum(r, g + 20), r)
    a[..., 2] = np.where(spill, np.minimum(b, g + 20), b)
    return Image.fromarray(np.dstack([a, alpha]).astype(np.uint8), 'RGBA')


def doors(img, w, h):
    """Door centres along each edge, from the grey door panels, in base px."""
    a = np.asarray(img).astype(int)
    grey = (np.abs(a[..., 0] - a[..., 1]) < 12) & (np.abs(a[..., 1] - a[..., 2]) < 14) & (a[..., 0] > 95) & (a[..., 3] > 200)
    res = {}
    W, H = w * SQ, h * SQ
    for name, band in (('top', grey[8:34, :]), ('bottom', grey[H - 34:H - 8, :])):
        col = band.mean(axis=0) > 0.35
        res[name] = runs(col, 6)
    for name, band in (('left', grey[:, 8:34]), ('right', grey[:, W - 34:W - 8])):
        row = band.mean(axis=1) > 0.35
        res[name] = runs(row, 6)
    return res


def runs(mask, k):
    out, start = [], None
    for i, v in enumerate(list(mask) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start > 12:
                out.append(round((start + i) / 2 / k, 1))
            start = None
    return out


def main(theme, paths, write):
    for (w, h), p in zip(SIZES, paths):
        im = Image.open(p)
        want = w / h
        got = im.width / im.height
        if abs(got - want) / want > 0.03:
            sys.exit('REFUSED %s: %dx%d is not a %dx%d room (ratio %.2f, want %.2f)' % (p, im.width, im.height, w, h, got, want))
        out = key(im.convert('RGB').resize((w * SQ, h * SQ), Image.LANCZOS))
        d = doors(out, w, h)
        expect_x = [16 + 32 * i for i in range(w)]
        expect_y = [16 + 32 * j for j in range(h)]
        print('%dx%d  doors top %s bottom %s (want %s)  left %s right %s (want %s)'
              % (w, h, d['top'], d['bottom'], expect_x, d['left'], d['right'], expect_y))
        if write:
            os.makedirs(OUT, exist_ok=True)
            out.save(os.path.join(OUT, 'shell_%s_%dx%d.png' % (theme, w, h)))
    if write:
        print('written to', OUT)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 5:
        sys.exit(__doc__)
    main(args[0], args[1:], '--write' in sys.argv)
