#!/usr/bin/env python3
"""Rooms ART paints whole (FACILITY_ART_SPEC: 192 px a square, magenta FF00FF outside the room)
-> the base view's frames.

    python3 build/install_room_art.py <delivery dir> --ufo <dir holding GEODATA/ GEOGRAPH/>

For each <room>.png (j_bivouac.png, ...): magenta becomes transparent, the picture is cut into its
grid squares, and each square is written as mod/Resources/Base/facilities/<room>_<i>_hi.png (RGBA,
the sharp twin the base view draws) plus <room>_<i>.png (the 8-bit frame, rebuilt from the same
picture with install_stocked_rooms' palette snapping). Squares are numbered left to right, top to
bottom, as the vanilla frames are. A room with no frame index yet in gijoe_base_facilities.rul is
reported, not wired.
"""
import os, sys, re
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import install_stocked_rooms as isr

ROOT = os.path.normpath(os.path.join(HERE, '..'))
FAC = os.path.join(ROOT, 'mod', 'Resources', 'Base', 'facilities')
RUL = os.path.join(ROOT, 'mod', 'Ruleset', 'gijoe_base_facilities.rul')


def keyed(im):
    a = np.asarray(im.convert('RGB')).astype(int)
    mag = (a[..., 0] > 200) & (a[..., 1] < 70) & (a[..., 2] > 200)
    out = np.dstack([a.astype(np.uint8), np.where(mag, 0, 255).astype(np.uint8)])
    return Image.fromarray(out, 'RGBA')


def main():
    src = sys.argv[1]; ufo = sys.argv[sys.argv.index('--ufo') + 1]
    pal, uses = isr.palette(ufo)
    rul = open(RUL).read()
    for f in sorted(os.listdir(src)):
        if not f.endswith('.png'): continue
        room = f[:-4]
        im = keyed(Image.open(os.path.join(src, f)))
        w, h = im.width // 192, im.height // 192
        i = 0
        for y in range(h):
            for x in range(w):
                sq = im.crop((x * 192, y * 192, x * 192 + 192, y * 192 + 192))
                sq.save(os.path.join(FAC, '%s_%d_hi.png' % (room, i)))
                isr.to_8bit(sq, pal, uses).save(os.path.join(FAC, '%s_%d.png' % (room, i)))
                i += 1
        wired = re.search(r'Resources/Base/facilities/%s_0\.png' % re.escape(room), rul)
        print('%-24s %dx%d  %s' % (room, w, h, 'wired' if wired else 'NOT in gijoe_base_facilities.rul yet'))


if __name__ == '__main__':
    main()
