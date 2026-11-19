#!/usr/bin/env python3
"""The tablet look behind every menu screen (John 19 Nov: round-3 mockups approved, kit delivered).

    python3 build/make_tablet_backgrounds.py

The kit's bezel (Resources/UI/Tablet/frames/frame_screen.png) is 108 px thick at
1920x1200 - 18 base px. Every list screen in the engine sets its widgets from 8
base px in, so the full-size bezel would sit over buttons and list rows until each
screen is re-laid out (that is phase 2, screen by screen). Phase 1 draws the bezel
thinner: the frame is scaled down whole (so screws, the /// tab and the bottom keys
keep their shape) and then stretched back to 1920x1200 by repeating plain columns
and rows of the bezel - never through a feature. Inside: the mockups' dark green.

Writes mod/Resources/UI/Tablet/bg/tablet.png (320x200, 8-bit) + tablet_hi.png and
mod/Ruleset/zz_gijoe_tablet_backgrounds.rul (every screen install_screen_backgrounds.py
dresses, pointed at the tablet instead of a Pit room).
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
UI = os.path.join(ROOT, 'mod', 'Resources', 'UI', 'Tablet')
RUL = os.path.join(ROOT, 'mod', 'Ruleset', 'zz_gijoe_tablet_backgrounds.rul')
W, H = 1920, 1200
F = 0.40                      # bezel 108 px -> ~43 px, inside the 48 px the screens leave
INSIDE = (34, 43, 32)         # the mockups' panel green (sampled from round 3)

sys.path.insert(0, HERE)
from install_screen_backgrounds import SCREENS, to_8bit   # noqa: E402


def stretch_at(a, axis, cuts, total):
    """Grow array a along axis to total by repeating the single line at each cut."""
    need = total - a.shape[axis]
    parts, prev = [], 0
    per = [need // len(cuts) + (1 if i < need % len(cuts) else 0) for i in range(len(cuts))]
    for c, n in zip(cuts, per):
        parts.append(np.take(a, range(prev, c), axis=axis))
        line = np.take(a, [c], axis=axis)
        parts.append(np.repeat(line, n + 1, axis=axis))
        prev = c + 1
    parts.append(np.take(a, range(prev, a.shape[axis]), axis=axis))
    return np.concatenate(parts, axis=axis)


def frame():
    fr = Image.open(os.path.join(UI, 'frames', 'frame_screen.png')).convert('RGBA')
    sw, sh = round(W * F), round(H * F)
    small = np.asarray(fr.resize((sw, sh), Image.LANCZOS))
    # plain bezel columns/rows: clear of the screws, the /// tab, the raised top-right
    # step, the bottom keys and the side tabs (positions as fractions of the frame)
    cols = [round(sw * 0.25), round(sw * 0.66)]
    rows = [round(sh * 0.30), round(sh * 0.72)]
    a = stretch_at(small, 1, cols, W)
    a = stretch_at(a, 0, rows, H)
    return Image.fromarray(a, 'RGBA')


def main():
    out = os.path.join(UI, 'bg'); os.makedirs(out, exist_ok=True)
    bg = Image.new('RGBA', (W, H), INSIDE + (255,))
    bg.alpha_composite(frame())
    hi = bg.convert('RGB')
    hi.save(os.path.join(out, 'tablet_hi.png'))
    to_8bit(hi).save(os.path.join(out, 'tablet.png'))
    # plus screens the Pit rooms never dressed (they kept X-COM's stock pictures)
    cats = [c for cs in SCREENS.values() for c in cs] + ['baseInfo']
    with open(RUL, 'w') as f:
        f.write('# The tablet behind every menu screen (John 19 Nov). Written by build/make_tablet_backgrounds.py.\n')
        f.write('# Loads after gijoe_screen_backgrounds.rul, so it replaces the Pit rooms; delete it to get them back.\n')
        f.write('extraSprites:\n  - type: JOE_TABLET.SCR\n    singleImage: true\n    width: 320\n    height: 200\n')
        f.write('    files:\n      0: Resources/UI/Tablet/bg/tablet.png\ninterfaces:\n')
        for c in cats:
            f.write(f'  - type: {c}\n    backgroundImage: JOE_TABLET.SCR\n')
    print('tablet background written;', len(cats), 'screens')


if __name__ == '__main__':
    main()
