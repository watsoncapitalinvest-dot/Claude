#!/usr/bin/env python3
"""Sharp twins of the game's OWN fonts: X-COM's letters, smooth at 6x.

    python3 build/make_fonts_smooth.py <Font.dat dir> <out dir>

John: "all the fonts need to be correct". The outline-font twins built tonight
(make_fonts.py) set DejaVu letters into X-COM's character widths. The engine
spaces text by the 8-bit sheet, so every condensed DejaVu glyph sat in a slot
cut for a broad 1994 letter: "L A U N C H  I N T E R C E P T I O N", and the
craft list read "T o m a h a w k". That cannot be fixed by fitting - the slot
is the wrong width for the letter.

So the general UI fonts go back to X-COM's own letters, and only the RENDERING
changes. The spacing then matches by construction, nothing can be gappy, and
nothing can overrun a box the original screens were laid out for.

The 8-bit glyphs are OUTLINED: values 1-3 are the stroke, 4-5 a dark rim drawn
round it for contrast on busy backgrounds. HiUI tints one coverage channel, so
taking every non-zero pixel as coverage swells each letter by its own outline -
the blobby look of the first sharp set. Coverage here is the STROKE only.

The stroke is upscaled 6x, blurred by about half a source pixel and pushed back
through a steep ramp around 0.5. That is a contour, not a resample: the edges
come out clean and curved where the pixels stepped, the way a vector trace of
the bitmap would, without the softness of a LANCZOS enlargement.

FONT_GEO_* are not touched: the geoscape panel buttons use them and are set in
the outline face fitted to the geo widths, which are narrow and suit it.
"""
import os
import sys
import numpy as np
import yaml
from PIL import Image, ImageFilter

K = 6
WANT = ('FontBig.png', 'FontSmall.png')
# The value is BRIGHTNESS within the glyph's palette ramp, not a yes/no: 1 is the
# lit stroke, 2 and 3 are progressively darker shading - and in the small font
# the 3s are mostly where a letter's COUNTER is, the hole in an R or a g. Taking
# 1-3 as solid filled those holes and READY read "AEADY". So each value carries
# the weight of its brightness; 4 and 5 are the dark contrast rim and carry none.
WEIGHT = {1: 1.0, 2: 0.62, 3: 0.22}


def smooth(mask, k=K):
    """A 0/1 bitmap -> 6x coverage with clean contoured edges."""
    h, w = mask.shape
    big = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8)).resize((w * k, h * k), Image.NEAREST)
    soft = np.asarray(big.filter(ImageFilter.GaussianBlur(k * 0.42))).astype(np.float32) / 255.0
    # steep ramp around the half level: a contour with about one display pixel
    # of anti-aliasing, not a blur
    a = np.clip((soft - 0.5) * 3.2 + 0.5, 0.0, 1.0)
    return (a * 255).astype(np.uint8)


def main(src_dir, out_dir):
    spec = yaml.safe_load(open(os.path.join(src_dir, 'Font.dat'), encoding='utf-8'))
    files = {img['file'] for e in spec['fonts'] for img in e['images']}
    for name in WANT:
        if name not in files:
            continue
        base = Image.open(os.path.join(src_dir, name))
        idx = np.asarray(base)
        stroke = np.zeros(idx.shape, np.float32)
        for v, w in WEIGHT.items():
            stroke[idx == v] = w
        cov = smooth(stroke)
        hi = Image.merge('RGBA', (Image.new('L', (cov.shape[1], cov.shape[0]), 255),) * 3
                         + (Image.fromarray(cov),))
        out = os.path.join(out_dir, name.replace('.png', '_hi.png'))
        hi.save(out)
        print('%-14s base %s -> %s, stroke weight %.0f' % (name, base.size, hi.size, float(stroke.sum())))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
