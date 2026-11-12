#!/usr/bin/env python3
"""Typefaces the engine sets at DISPLAY resolution, not zoomed up from 8 bits.

    python3 build/make_typefaces.py [--write]

John, on the equipment screen: "it doesnt look crisp  build it from scratch".
The X-COM letters, however carefully smoothed, are 5-pixel drawings enlarged
four to six times - they read as soft pixel art, never as type. A screen built
from scratch sets real outlines at the size it is shown.

Each face is rendered once, large (EM px), into an alpha atlas with a metrics
file beside it. HiUI downsamples each glyph by area at draw time, so a label is
as sharp at 1080 lines as at 2160 and no size is baked in.

    Resources/UI/type_<face>.png    white, coverage in alpha
    Resources/UI/type_<face>.txt    "em asc desc cap" then one line per glyph:
                                    "code x y w h left top advance"   (atlas px)

Faces (both SIL Open Font Licence; the licences ship beside them):
    label    Oswald SemiBold - condensed military sans, for every label and readout
    stencil  Saira Stencil One - the console's key legends
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.normpath(os.path.join(HERE, '..', 'mod', 'Resources', 'UI'))
SRC = os.path.normpath(os.path.join(HERE, '..', 'fonts'))
EM = 96
# 150 and 151 hold the en and em dash, where Windows-1252 keeps them. The faces
# are Latin-1 otherwise; HiUI maps U+2013/U+2014 to these two codes, so a
# readout with nothing to say can print an en dash rather than a hyphen.
EXTRA = {150: '\u2013', 151: '\u2014'}
CHARS = [c for c in range(32, 127)] + sorted(EXTRA) + [c for c in range(160, 256)]


def glyph(c):
    return EXTRA.get(c, chr(c))
FACES = {
    'label': ('Oswald[wght].ttf', 600),
    'stencil': ('SairaStencilOne-Regular.ttf', None),
}


def build(face, path, weight):
    f = ImageFont.truetype(path, EM)
    if weight is not None:
        f.set_variation_by_axes([weight])
    asc, desc = f.getmetrics()
    cap = f.getbbox('H')
    cap_h = cap[3] - cap[1]
    cells = []
    for c in CHARS:
        ch = glyph(c)
        adv = f.getlength(ch)
        bb = f.getbbox(ch)                  # relative to the pen at the top of the ascent
        w, h = max(0, bb[2] - bb[0]), max(0, bb[3] - bb[1])
        cells.append((c, bb, w, h, adv))
    pad = 4
    cols = 16
    cw = max(w for _, _, w, _, _ in cells) + pad * 2
    chh = max(h for _, _, _, h, _ in cells) + pad * 2
    rows = (len(cells) + cols - 1) // cols
    atlas = Image.new('L', (cols * cw, rows * chh), 0)
    d = ImageDraw.Draw(atlas)
    lines = ['%d %d %d %d' % (EM, asc, desc, cap_h)]
    for i, (c, bb, w, h, adv) in enumerate(cells):
        ox, oy = (i % cols) * cw + pad, (i // cols) * chh + pad
        if w and h:
            d.text((ox - bb[0], oy - bb[1]), glyph(c), font=f, fill=255)
        # left/top: where the glyph's box sits relative to the pen (x) and the
        # top of the ascent (y), so layout needs nothing but these numbers
        lines.append('%d %d %d %d %d %d %d %.2f' % (c, ox, oy, w, h, bb[0], bb[1], adv))
    img = Image.merge('RGBA', (Image.new('L', atlas.size, 255),) * 3 + (atlas,))
    return img, '\n'.join(lines) + '\n'


def main(write):
    for face, (fname, weight) in FACES.items():
        img, txt = build(face, os.path.join(SRC, fname), weight)
        print('%-8s atlas %dx%d, %d glyphs' % (face, img.width, img.height, txt.count('\n') - 1))
        if write:
            img.save(os.path.join(UI, 'type_%s.png' % face))
            open(os.path.join(UI, 'type_%s.txt' % face), 'w').write(txt)
    if write:
        print('written to', UI)


if __name__ == '__main__':
    main('--write' in sys.argv)
