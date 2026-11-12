#!/usr/bin/env python3
"""Build a seven-segment font for the geoscape clock.

    python3 build/make_digital_font.py <out dir>

John: "the clock needs to be digital readout". A digital readout is not a
typeface choice, it is a different kind of object - seven bars switched on and
off - so it is drawn rather than set. Lit segments bright, UNLIT SEGMENTS FAINTLY
VISIBLE, which is the detail that makes a panel read as a real display instead
of numbers on black: on a dead LCD you can still see the eight.

It gets its own font, FONT_DIGITAL, rather than replacing the digits in
FONT_BIG, because FONT_BIG sets headings on every other screen in the game and a
seven-segment heading would be absurd. The mod ships its own Font.dat declaring
it; the engine resolves Language/Font.dat through FileMap, so a mod copy wins.

Cell is 10x16 with spacing 0 - narrower than FONT_BIG's 16 because segment
digits are upright and need no side bearing, which also buys room for the
seconds inside the clock well.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

K = 6
# CELL WIDTH IS SET BY THE SPACE THE CLOCK HAS, NOT BY WHAT LOOKS RIGHT ALONE.
# The clock well is 60 base px and the readout is HH:MM:SS - six digits and two
# separators. At the first attempt's 10-wide cell that needs 80, so the engine
# clipped every box and the display came out as loose segments. Six 7s and two
# colons is 50, which fits with room at both ends.
CW, CH = 7, 16                  # cell, base units
CHARS = '0123456789:'
COLS = 16                       # Font.dat lays cells out across the sheet width

# segment order: a(top) b(top right) c(bottom right) d(bottom) e(bottom left)
# f(top left) g(middle)
SEG = {
    '0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc',
    '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'afgbcd',
}
LIT = 255
DIM = 46                        # the unlit segment: present, not readable as a digit


def digit(d, x0, y0, w, h, segs, on):
    # PROPORTION AND THICKNESS, BOTH MEASURED OFF THE CELL RATHER THAN GUESSED.
    #
    # The first version drew into the whole cell: 30 wide by 84 tall, which is far
    # narrower than any real seven-segment digit, and took its bar thickness from
    # the HEIGHT, so each bar ended up 9 thick with 3 of mitre gap at each end -
    # about three visible pixels. On screen that was not a digit, it was scattered
    # sticks. Thickness comes off the WIDTH, and the gap is a fifth of it.
    t = max(3, int(w * 0.22))           # segment thickness
    g = max(1, t // 5)                  # gap at the mitres
    mid = y0 + h / 2
    bars = {
        'a': (x0 + t, y0, x0 + w - t, y0 + t),
        'g': (x0 + t, mid - t / 2, x0 + w - t, mid + t / 2),
        'd': (x0 + t, y0 + h - t, x0 + w - t, y0 + h),
        'f': (x0, y0 + t, x0 + t, mid - t / 2),
        'b': (x0 + w - t, y0 + t, x0 + w, mid - t / 2),
        'e': (x0, mid + t / 2, x0 + t, y0 + h - t),
        'c': (x0 + w - t, mid + t / 2, x0 + w, y0 + h - t),
    }
    for name, (ax, ay, bx, by) in bars.items():
        v = LIT if name in segs else DIM
        d.rectangle([ax + g, ay + g, bx - g, by - g], fill=v)


def build():
    W, H = COLS * CW, CH
    img = Image.new('L', (W * K, H * K), 0)
    d = ImageDraw.Draw(img)
    for i, c in enumerate(CHARS):
        cx, cy = i * CW * K, 0
        # a base pixel of bearing each side so neighbouring digits never touch
        # A seven-segment digit is about 1.8 times as tall as it is wide. The cell
        # is taller than that, so the digit is drawn to its own proportion and
        # centred in the cell rather than stretched to fill it.
        w = (CW - 2) * K
        h = min((CH - 2) * K, int(w * 1.85))
        x0 = cx + K
        y0 = cy + (CH * K - h) // 2
        if c == ':':
            # Narrow on purpose: the engine takes a character's advance from its
            # ink, so a colon drawn across the full cell would space like a digit.
            r = max(2, int(w * 0.14))
            cx = x0 + w / 2
            for fy in (0.34, 0.68):
                yy = y0 + h * fy
                d.ellipse([cx - r, yy - r, cx + r, yy + r], fill=LIT)
        else:
            digit(d, x0, y0, w, h, SEG[c], True)
    return img


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    big = build()
    W, H = COLS * CW, CH
    # hi sheet: coverage in ALPHA, which is the only channel HiUI reads
    hi = Image.merge('RGBA', (Image.new('L', big.size, 255),) * 3 + (big,))
    hi.save(os.path.join(out_dir, 'FontDigital_hi.png'))

    # base sheet: the font palette's values 1..5, 4 for lit and 2 for the ghost
    a = np.asarray(big.resize((W, H), Image.LANCZOS)).astype(int)
    out = np.zeros((H, W), np.uint8)
    out[a >= 110] = 4
    out[(a >= 18) & (a < 110)] = 2

    # THE BASE SHEET SETS THE ADVANCE, AND IT WAS MEASURING SHORT.
    #
    # Font::init takes a character's width from the last column of ink in its
    # BASE cell, and HiUI then crops the sharp glyph to exactly that width. The
    # unlit segments are faint by design, and downsampling a faint 6x bar to one
    # base pixel pushed the outermost columns under the threshold - so the engine
    # measured each digit a pixel or two narrower than it is drawn and cut the
    # right-hand segments off every one. On screen the clock came out as sticks.
    #
    # The drawn extent is known here exactly, so it is stamped into the base cell
    # as a single row of the faintest value. It costs one pixel row that no one
    # can see at 1x and it makes the advance equal to the glyph.
    for i, c in enumerate(CHARS):
        x0 = i * CW
        cell = np.asarray(big.crop((x0 * K, 0, (x0 + CW) * K, CH * K)))
        nz = np.nonzero((cell > 0).any(axis=0))[0]
        if not len(nz):
            continue
        left, right = int(nz.min() // K), int(np.ceil((nz.max() + 1) / K)) - 1
        for x in (left, right):
            if out[0, x0 + x] == 0:
                out[0, x0 + x] = 2
    im = Image.fromarray(out, mode='P')
    im.putpalette([0, 0, 0] * 256)
    im.save(os.path.join(out_dir, 'FontDigital.png'), optimize=False)
    print('FontDigital.png %dx%d, FontDigital_hi.png %dx%d, %d glyphs'
          % (W, H, hi.size[0], hi.size[1], len(CHARS)))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1])
