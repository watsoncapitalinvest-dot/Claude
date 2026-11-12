#!/usr/bin/env python3
"""Take a repainted geoscape panel back from the graphics AI and install it.

    python3 build/install_panel_art.py <delivered.png> <PALETTES.DAT> [--write]

The plate went out as panel_for_weathering_384x1200.png with a guide. This is
the return trip, and it does NOT warp anything: the lesson of the old panels is
that bending art to fit is what made them a collage. It scales the delivery to
384 x 1200 and then MEASURES it against LAYOUT in make_panel.py - the same table
the engine's rectangles come from - and refuses if a slot or a control has
moved. Only if it passes does it cut the readout labels back in and install.

Checks, all in base pixels against the layout:
  every recess    still dark inside (text is printed there at run time)
  every control   the arrow or roller is actually drawn inside its click box
  label fields    still plain metal, so the engraving lands on bare paint
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_panel as mp                                    # noqa: E402

K, W, H = mp.K, mp.W, mp.H


def crop_panel(im):
    """The delivery may come on a white or transparent page; keep the panel."""
    a = np.asarray(im.convert('RGBA')).astype(int)
    ink = (a[:, :, :3].min(axis=2) < 235) & (a[:, :, 3] > 128)
    cols = np.nonzero(ink.mean(axis=0) > 0.5)[0]
    x0, x1 = cols.min(), cols.max() + 1
    rows = np.nonzero(ink[:, x0:x1].mean(axis=1) > 0.5)[0]
    y0, y1 = rows.min(), rows.max() + 1
    return im.convert('RGB').crop((x0, y0, x1, y1)), (x0, y0, x1, y1)


def dark_fraction(a, x, y, w, h, inset=1.4):
    """Share of a rect's interior that is recess-dark, ignoring its bevelled rim."""
    X0, Y0 = mp.px(x + inset), mp.px(y + inset)
    X1, Y1 = mp.px(x + w - inset), mp.px(y + h - inset)
    blk = a[Y0:Y1, X0:X1]
    return float((blk.sum(axis=2) < 150).mean())


def control_fraction(a, x, y, w, h):
    """Share of a click box covered by a drawn control rather than flat plate.

    Controls are lit metal - arrows and knurled rollers - and stand out from the
    olive plate by being neutral and bright. Measured as pixels that are both."""
    blk = a[mp.px(y):mp.px(y + h), mp.px(x):mp.px(x + w)]
    r, g, b = blk[:, :, 0], blk[:, :, 1], blk[:, :, 2]
    neutral = (np.abs(r - g) < 28) & (np.abs(g - b) < 34)
    lum = blk.sum(axis=2)
    return float((neutral & (lum > 240)).mean())


def plain(a, x, y, w, h):
    """A label field must be bare paint: neither recess-dark nor busy."""
    blk = a[mp.px(y + 0.5):mp.px(y + h - 0.5), mp.px(x):mp.px(x + w)].astype(float)
    return float((blk.sum(axis=2) < 150).mean()), float(blk.sum(axis=2).std())


def main(src, pal, write):
    raw = Image.open(src)
    panel, box = crop_panel(raw)
    print('delivered %s, panel at x %d..%d y %d..%d (%dx%d)' %
          (raw.size, box[0], box[2], box[1], box[3], panel.width, panel.height))
    sx, sy = W * K / panel.width, H * K / panel.height
    print('scale to 384x1200: x %.3f y %.3f (%.1f%% difference between axes)'
          % (sx, sy, 100 * abs(sx - sy) / sy))
    fitted = panel.resize((W * K, H * K), Image.LANCZOS)
    a = np.asarray(fitted).astype(int)

    fails = []
    print('\nRECESSES - must be dark inside, text prints here')
    rects = [(n, x, y, w, h) for n, x, y, w, h in mp.COMMAND]
    rects += [('speed%d' % i, *r) for i, r in enumerate(mp.SPEED)]
    rects += [('clock', *mp.CLOCK_WELL), ('date', *mp.DATE_WELL)]
    rects += [(t.lower(), 2 + mp.EXTRA_LABEL_W, y, 60 - mp.EXTRA_LABEL_W, 8) for t, y in mp.EXTRA]
    for n, x, y, w, h in rects:
        f = dark_fraction(a, x, y, w, h)
        ok = f >= 0.90
        if not ok:
            fails.append('recess %s only %.0f%% dark' % (n, 100 * f))
        print('  %-12s %5.1f%% dark  %s' % (n, 100 * f, 'ok' if ok else 'MOVED OR LIT'))

    print('\nCONTROLS - the drawn control must sit in its click box')
    for n, x, y, w, h in mp.CONTROLS:
        f = control_fraction(a, x, y, w, h)
        ok = f >= 0.12
        if not ok:
            fails.append('control %s only %.0f%% covered' % (n, 100 * f))
        print('  %-12s %5.1f%% covered  %s' % (n, 100 * f, 'ok' if ok else 'NOT ON ITS BOX'))

    print('\nLABEL FIELDS - must be plain metal for the engraving')
    for t, y in mp.EXTRA:
        d, sd = plain(a, 3, y, mp.EXTRA_LABEL_W - 2, 8)
        ok = d < 0.10
        if not ok:
            fails.append('label field %s is %.0f%% dark' % (t, 100 * d))
        print('  %-12s dark %4.1f%%, texture %.0f  %s' % (t, 100 * d, sd, 'ok' if ok else 'NOT PLAIN'))

    if fails:
        print('\nREFUSED - %d problem(s):' % len(fails))
        for f in fails:
            print('   ' + f)
        return 1

    mp.engrave_labels(fitted)
    print('\nall checks pass; labels engraved')
    if not write:
        fitted.save('/tmp/panel_candidate.png')
        print('dry run: /tmp/panel_candidate.png (use --write to install)')
        return 0

    canvas = Image.new('RGBA', (1920, 1200), (0, 0, 0, 0))
    canvas.paste(fitted.convert('RGBA'), (1536, 0))
    hi = os.path.join(HERE, '..', 'mod', 'Resources', 'Backgrounds', 'GEOBORD_hi.png')
    canvas.save(hi)
    print('installed %s' % os.path.normpath(hi))
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2], '--write' in sys.argv))
