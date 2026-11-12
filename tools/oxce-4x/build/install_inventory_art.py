#!/usr/bin/env python3
"""Take the graphics AI's painting of the equipment screen back and install it.

    python3 build/install_inventory_art.py <delivered.png> [--write]

The page went out as inventory_for_painting_1920x1200.png with a guide
(INVENTORY_PAGE_PAINT_BRIEF.txt). Nothing is warped to fit: the delivery is
scaled to 1920 x 1200 and MEASURED against the layout in make_inventory_bg.py,
the same rectangles the engine draws from, and refused if something moved.

  every compartment   still dark inside (items are laid into it)
  every key           a key is actually painted in its box, not bare plate
  text and figure     still quiet metal, so live type and the figure read on it

Passing, it writes mod/Resources/Backgrounds/TAC01_hi.png. The engine then
shows the painting under the live type and key legends, resampled by area to
the exact size of the screen (HiUI::paintBackdrop).
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_inventory_bg as ib                              # noqa: E402

K, W, H = ib.K, ib.W, ib.H
MOD = ib.MOD


def region(a, x, y, w, h, inset=0.0):
    return a[ib.px(y + inset):ib.px(y + h - inset), ib.px(x + inset):ib.px(x + w - inset)]


def wells():
    for _, x, y, cells in ib.INVS:
        for c, r in cells:
            yield x + c * ib.SLOT, y + r * ib.SLOT, ib.SLOT, ib.SLOT
    for _, x, y in ib.HANDS:
        yield x, y, 2 * ib.SLOT, 3 * ib.SLOT
    for x in range(0, W, ib.SLOT):
        for y in range(ib.GROUND_Y, H, ib.SLOT):
            yield x, y, ib.SLOT, min(ib.SLOT, H - y)


def main(path, write):
    im = Image.open(path).convert('RGB')
    if im.size != (W * K, H * K):
        print('delivered %dx%d - scaled to %dx%d without changing its shape' % (*im.size, W * K, H * K))
        if abs(im.width / im.height - W / H) > 0.01:
            sys.exit('REFUSED: not the 1920 x 1200 shape (%.3f, want %.3f) - it was cropped or extended'
                     % (im.width / im.height, W / H))
        im = im.resize((W * K, H * K), Image.LANCZOS)
    a = np.asarray(im).astype(int)
    lum = a.sum(axis=2) / 3
    plate = float(np.median(lum))
    fails = []

    for x, y, w, h in wells():
        r = region(lum, x, y, w, h, inset=2.2)
        if r.size and float((r < 40).mean()) < 0.85:
            fails.append('compartment at %d,%d is not dark inside (%.0f%% dark)' % (x, y, 100 * (r < 40).mean()))
    for name, x, y, w, h in ib.KEYS:
        r = region(lum, x, y, w, h, inset=2.0)
        if abs(float(np.median(r)) - plate) < 6 and float(r.std()) < 6:
            fails.append('key %s: nothing painted in its box' % name)
    for name, x, y, w, h in ib.TEXT_ZONES + [(n, x, y, w, 8) for n, x, y, w in ib.LABELS]:
        r = region(lum, x, y, w, h)
        if float(r.std()) > 22:
            fails.append('text area %s is busy (contrast %.0f) - type will not read on it' % (name, r.std()))
    for name, box in (('figure', ib.DOLL), ('rank badge', ib.RANK)):
        r = region(lum, *box)
        if float(r.std()) > 26:
            fails.append('%s area has something drawn in it (contrast %.0f)' % (name, r.std()))

    if fails:
        print('REFUSED, %d problem(s):' % len(fails))
        for f in fails:
            print('  ' + f)
        sys.exit(1)
    print('passes: %d compartments dark, %d keys painted, text and figure areas quiet'
          % (sum(1 for _ in wells()), len(ib.KEYS)))
    if write:
        out = os.path.join(MOD, 'Resources', 'Backgrounds', 'TAC01_hi.png')
        im.convert('RGBA').save(out)
        print('installed', out)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], '--write' in sys.argv)
