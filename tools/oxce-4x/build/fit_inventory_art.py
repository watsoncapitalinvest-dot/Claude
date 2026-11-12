#!/usr/bin/env python3
"""Make a painted equipment page fit the game exactly, using its own pixels.

    python3 build/fit_inventory_art.py <installed TAC01_hi.png> <out.png>

The first painting (Nov 11) came back right everywhere except the edges: the
painter ran a riveted frame round the page and moved the compartments that
touch it inwards - the right hand 4 base px narrower, the right leg and the
ground tray's first and last columns cut by the border. The game's slots stay
where they are, so anything put there sat half on the frame.

Nothing is warped. Each misfit compartment is replaced by a correctly painted
twin from the SAME painting - the left hand for the right, the left leg for the
right leg, the ground tray's neighbouring column for its end columns - copied
pixel for pixel onto the slot the game really uses. Measured afterwards with
the same detector the check uses.
"""
import sys
from PIL import Image

K = 6


def box(x0, y0, x1, y1):
    return tuple(int(round(v * K)) for v in (x0, y0, x1, y1))


# (source rect, destination x, destination y) in base px; rects include the rim
MOVES = [
    ((127.5, 62.5, 161.0, 111.5), 0.0, 62.5),     # left hand  -> right hand
    ((127.5, 119.5, 161.0, 137.5), 0.0, 119.5),   # left leg   -> right leg
    ((15.5, 151.5, 32.5, 200.0), 0.0, 151.5),     # ground col 1 -> col 0
    ((287.5, 151.5, 304.5, 200.0), 303.5, 151.5), # ground col 18 -> col 19
]


def main(src, out):
    im = Image.open(src).convert('RGBA')
    for (x0, y0, x1, y1), dx, dy in MOVES:
        piece = im.crop(box(x0, y0, x1, y1))
        im.paste(piece, (int(round(dx * K)), int(round(dy * K))))
    im.save(out)
    print('wrote', out)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
