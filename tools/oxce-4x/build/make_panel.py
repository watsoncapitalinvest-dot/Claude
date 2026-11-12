#!/usr/bin/env python3
"""Draw the geoscape side panel from the engine's own layout, at 4x and at 1x.

    python3 build/make_panel.py <out dir> [--rects]

John: "it looks like a collage. cant we create the whole thing fresh".

It did, and this is why. Every previous panel was a painting made somewhere else
and then bent to fit: the slots came back evenly spaced where the engine's are
not, so fit_panel_art.py warped bands onto rectangles, flattened ribs that
landed under text, and deepened recesses that were in the wrong place. Each step
was a correct local fix and together they are a patchwork.

So the direction is reversed. LAYOUT below is the single source of truth. This
script draws the panel from it, and prints the widget rectangles for
GeoscapeState from the same table, so the painted recess and the rectangle the
engine draws text into cannot drift apart - there is nothing to fit, because
they were never separate.

Everything is in BASE units on a 64x200 panel, panel-local: x 0..64 is base
x 256..320, and y 0..200 is the sidebar's own height. The 4x sheet is exactly
6x that, 384x1200, which is what HiUI requires of a twin.

What is new here, at John's request: four readouts the conversion needs and
vanilla has no room for - goodwill, Cobra escalation, Terror Dromes and intel.
Their labels are ENGRAVED INTO THE METAL rather than drawn by the engine, which
is only possible because this script owns the artwork: it costs no runtime text
widget and it cannot collide with the value printed beside it.

The space for them comes from dropping nothing. The weekday, day, month and
year share one row where vanilla spends two and a half, and the speed buttons
and control cluster are tightened. Vanilla's layout is not a constraint; its
widget sizes are, because they are what the engine draws into.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

K = 6                                   # 4x sheet is 6x the 64x200 base panel
W, H = 64, 200
TTF = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'

# Lifted from the first pass, where the plate read as flat and the wells took
# over. A recess only looks cut if the metal around it is clearly brighter than
# the hole, and at sprite size that gap has to be bigger than it would be in life.
OLIVE      = (92, 100, 74)
OLIVE_LIT  = (132, 140, 108)
OLIVE_DARK = (52, 58, 44)
WELL       = (11, 11, 9)
RIM_LIGHT  = (168, 176, 140)
RIM_DARK   = (26, 30, 22)
AMBER      = (214, 138, 42)
RED        = (176, 40, 34)

# ---------------------------------------------------------------- the layout
# A row is (name, x, y, w, h). These ARE the widget rectangles; see --rects.
COMMAND = [('INTERCEPT', 2, 0, 60, 11), ('BASES', 2, 12, 60, 11),
           ('GRAPHS', 2, 24, 60, 11), ('INTEL FILES', 2, 36, 60, 11),
           ('OPTIONS', 2, 48, 60, 11), ('FUNDING', 2, 60, 60, 11)]
# TIGHTENED, at John's word: "some of the spacing needs to be tightened up".
# The readout rows drop from a 9 pitch to 8 and the whole lower half moves up,
# which buys the control cluster 28 base px where it had 24 and was cramped.
# Nothing here changes a widget's HEIGHT - the text still has the room it had -
# only the air between them.
CLOCK_WELL = (2, 73, 60, 16)            # hours, separators, minutes, seconds
DATE_WELL  = (2, 90, 60, 9)             # day, month, year on one row
# label engraved in the metal, value well to its right
EXTRA = [('GOODWILL', 100), ('COBRA', 108), ('DROMES', 116), ('INTEL', 124)]
EXTRA_LABEL_W = 24                      # engraved; the value well takes the rest
SPEED = [(2, 134, 29, 11), (33, 134, 29, 11),
         (2, 146, 29, 11), (33, 146, 29, 11),
         (2, 158, 29, 11), (33, 158, 29, 11)]
CLUSTER_Y = 171                         # to y=200
# The six controls inside the cluster, as (name, x, y, w, h). The ART IS DRAWN
# ON THESE, so an arrow can never sit anywhere but on its own hitbox - which is
# the fault that made the old panel's right arrow zoom the globe.
CONTROLS = [('rotateUp',    28, 173, 8, 8),
            ('rotateLeft',  17, 182, 9, 8),
            ('rotateRight', 38, 182, 9, 8),
            ('rotateDown',  28, 191, 8, 8),
            ('zoomOut',      3, 176, 12, 20),
            ('zoomIn',      49, 176, 12, 20)]


def px(v):
    return int(round(v * K))


def stencil_font(size):
    return ImageFont.truetype(TTF, size)


def stencil(draw_img, xy, text, size, fill):
    """Draw text with stencil bridges cut through it.

    A military stencil is a solid face with gaps where the cutter left bridges.
    Cutting them as two thin horizontal bands across the whole word is crude on
    paper and correct here, because at this size the alternative - per-glyph
    bridges at the junctions - closes up into mush.
    """
    f = stencil_font(size)
    tmp = Image.new('L', draw_img.size, 0)
    ImageDraw.Draw(tmp).text(xy, text, font=f, fill=255)
    bb = tmp.getbbox()
    if bb:
        d = ImageDraw.Draw(tmp)
        h = bb[3] - bb[1]
        for frac in (0.34, 0.70):
            y = bb[1] + h * frac
            d.rectangle([bb[0] - 1, y, bb[2] + 1, y + max(1, h * 0.085)], fill=0)
    return tmp


def noise(size, amount, seed):
    rng = np.random.default_rng(seed)
    a = rng.normal(0, amount, (size[1], size[0]))
    return a


def metal(img):
    """Fill the body with painted olive steel: streaks, grain, light upper-left."""
    w, h = img.size
    a = np.zeros((h, w, 3), np.float32)
    a[:, :] = OLIVE
    # vertical brushed streaks, the way a rolled panel is finished
    rng = np.random.default_rng(7)
    streak = rng.normal(0, 4.0, (1, w)).repeat(h, axis=0)
    streak += rng.normal(0, 1.2, (h, w))
    a += streak[:, :, None]
    # a broad diagonal lift from the upper left so the whole plate reads as lit
    yy, xx = np.mgrid[0:h, 0:w]
    lift = (1.0 - (xx / w) * 0.45 - (yy / h) * 0.55) * 16.0
    a += lift[:, :, None]
    a += noise((w, h), 2.2, 11)[:, :, None]
    np.clip(a, 0, 255, out=a)
    img.paste(Image.fromarray(a.astype(np.uint8)))


INSET = 0.7       # base px of metal kept inside each widget rect, top and bottom


def well(d, x, y, w, h, radius=None):
    """Cut a recess inside the widget rect, leaving metal between neighbours.

    The wells are drawn INSET from the rectangle rather than filling it. The
    engine's rows are 11 and 12 apart, so a well drawn to the full rect leaves
    one base pixel of metal between it and the next and the panel reads as a
    stack of black bars with olive edges. Inset, there is a visible land between
    every pair, and the text - which is about 5 tall and centred in the rect -
    still falls well inside the hole.
    """
    X0, Y0 = px(x + INSET * 0.4), px(y + INSET)
    X1, Y1 = px(x + w - INSET * 0.4), px(y + h - INSET)
    r = radius if radius is not None else max(3, int(K * 0.8))
    # shadow the metal casts into the hole, upper left
    d.rounded_rectangle([X0 - 3, Y0 - 3, X1 + 3, Y1 + 3], r + 3, fill=RIM_DARK)
    # and the light catching the lower lip
    d.rounded_rectangle([X0 - 2, Y0 - 1, X1 + 3, Y1 + 3], r + 2, fill=RIM_LIGHT)
    d.rounded_rectangle([X0 - 3, Y0 - 3, X1 + 1, Y1 + 1], r + 2, fill=RIM_DARK)
    d.rounded_rectangle([X0, Y0, X1, Y1], r, fill=WELL)
    # the floor is not flat black; a readout well catches a little light low down
    for i in range(7):
        t = i / 7.0
        c = tuple(int(WELL[j] + (30 - j * 5) * t) for j in range(3))
        d.rounded_rectangle([X0 + 1, Y1 - int((Y1 - Y0) * 0.26 * t) - 1, X1 - 1, Y1 - 1],
                            max(1, r - 2), outline=c)


def lamp(d, x, y, colour):
    X, Y = px(x), px(y)
    d.rounded_rectangle([X, Y, X + px(1.2), Y + px(2.2)], 3, fill=(20, 22, 18))
    d.rounded_rectangle([X + 1, Y + 1, X + px(1.2) - 1, Y + px(2.2) - 1], 3, fill=colour)


def screw(d, x, y):
    X, Y, r = px(x), px(y), px(0.9)
    d.ellipse([X - r, Y - r, X + r, Y + r], fill=(96, 104, 84), outline=(40, 44, 34))
    d.line([X - r + 2, Y, X + r - 2, Y], fill=(44, 48, 38), width=2)


def engrave_labels(img):
    """Cut GOODWILL, COBRA, DROMES and INTEL into the metal of `img`, in place.

    A function of its own so it can be run over artwork that came back from the
    graphics AI: the plate goes out unlabelled, so weathering cannot smear the
    lettering, and the labels are cut back in crisp afterwards.

    ONE SIZE THAT FITS THE LONGEST LABEL, NOT A SIZE THAT SUITS THE SHORTEST.
    Set at a fixed 5 base px, GOODWILL and DROMES ran straight under the value
    well beside them. The label column is EXTRA_LABEL_W wide and that is a hard
    edge, so the size is measured down until the longest of the four clears it,
    and all four are set at that size - four sizes would read as four machines.
    """
    size = px(5.4)
    while size > 6:
        f = stencil_font(size)
        if max(f.getbbox(t)[2] for t, _ in EXTRA) <= px(EXTRA_LABEL_W - 3.5):
            break
        size -= 1
    lab = Image.new('L', img.size, 0)
    for text, y in EXTRA:
        t = stencil(img, (px(3.2), px(y + 1.3)), text, size, 255)
        lab = Image.composite(Image.new('L', img.size, 255), lab, t)
    # The catch goes down FIRST and the groove on top of it, so the lit edge
    # shows along the bottom of the cut instead of being painted over by it.
    lit = Image.new('RGBA', img.size, (0, 0, 0, 0))
    lit.putalpha(lab.filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: int(v * 0.55)))
    img.paste(Image.new('RGB', img.size, (186, 194, 156)), (0, 3), lit)
    groove = Image.new('RGBA', img.size, (0, 0, 0, 0))
    groove.putalpha(lab.point(lambda v: int(v * 0.88)))
    img.paste(Image.new('RGB', img.size, (22, 25, 18)), (0, 0), groove)


def build(labels=True):
    img = Image.new('RGB', (W * K, H * K))
    metal(img)
    d = ImageDraw.Draw(img, 'RGBA')

    # outer rails, so the panel reads as a plate bolted on rather than a crop
    d.rectangle([0, 0, px(1.2), H * K], fill=OLIVE_DARK)
    d.rectangle([W * K - px(1.2), 0, W * K, H * K], fill=OLIVE_DARK)
    d.rectangle([0, 0, px(0.4), H * K], fill=OLIVE_LIT)

    for name, x, y, w, h in COMMAND:
        well(d, x, y, w, h)
    for x, y, w, h in SPEED:
        well(d, x, y, w, h)
    well(d, *CLOCK_WELL)
    well(d, *DATE_WELL)

    # the four new readouts: value wells, and the labels engraved beside them
    for text, y in EXTRA:
        well(d, 2 + EXTRA_LABEL_W, y, 60 - EXTRA_LABEL_W, 8, radius=3)
    if labels:
        engrave_labels(img)

    # fasteners and indicator lamps in the metal between the groups
    for y in (72.0, 101.0, 138.0, 175.0):
        screw(d, 1.0, y)
        screw(d, 63.0, y)
    for y, c in ((12.5, AMBER), (36.5, RED), (60.5, AMBER), (152.5, RED)):
        lamp(d, 0.2, y, c)
        lamp(d, 62.6, y, c)

    cluster(d)
    return img


def cluster(d):
    """Arrows and zoom rollers, drawn ON the hitboxes in CONTROLS."""
    d.rounded_rectangle([px(1.5), px(CLUSTER_Y), px(62.5), px(199.5)], px(1.5),
                        fill=OLIVE_DARK, outline=RIM_LIGHT, width=2)
    for name, x, y, w, h in CONTROLS:
        X0, Y0, X1, Y1 = px(x), px(y), px(x + w), px(y + h)
        if name.startswith('rotate'):
            cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
            s = min(X1 - X0, Y1 - Y0) * 0.46
            pts = {'rotateUp':    [(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)],
                   'rotateDown':  [(cx, cy + s), (cx - s, cy - s), (cx + s, cy - s)],
                   'rotateLeft':  [(cx - s, cy), (cx + s, cy - s), (cx + s, cy + s)],
                   'rotateRight': [(cx + s, cy), (cx - s, cy - s), (cx - s, cy + s)]}[name]
            d.polygon([(p[0] + 2, p[1] + 2) for p in pts], fill=(30, 34, 26))
            d.polygon(pts, fill=(158, 166, 134), outline=(206, 212, 180))
        else:
            d.rounded_rectangle([X0, Y0, X1, Y1], px(1.2), fill=(34, 38, 30),
                                outline=RIM_LIGHT, width=2)
            n = 9
            for i in range(n):
                yy = Y0 + 4 + (Y1 - Y0 - 8) * i / (n - 1)
                v = 70 + int(90 * abs(1 - 2 * i / (n - 1)))
                d.line([X0 + 4, yy, X1 - 4, yy], fill=(v, v + 6, v - 8), width=2)


def guide(img):
    """The same plate with every rectangle the engine uses outlined in magenta.

    Handed to whoever repaints the panel, so 'do not move the slots' is a
    picture and not a sentence.
    """
    g = img.convert('RGB').copy()
    d = ImageDraw.Draw(g)
    M = (255, 0, 255)
    rects = [r[1:] for r in COMMAND] + list(SPEED) + [CLOCK_WELL, DATE_WELL]
    rects += [(2 + EXTRA_LABEL_W, y, 60 - EXTRA_LABEL_W, 8) for _, y in EXTRA]
    for x, y, w, h in rects:
        d.rectangle([px(x), px(y), px(x + w) - 1, px(y + h) - 1], outline=M, width=3)
    for _, x, y, w, h in CONTROLS:
        d.rectangle([px(x), px(y), px(x + w) - 1, px(y + h) - 1], outline=(0, 255, 255), width=3)
    for _, y in EXTRA:
        d.rectangle([px(3), px(y + 0.5), px(2 + EXTRA_LABEL_W - 1), px(y + 7.5)], outline=(255, 200, 0), width=2)
    return g


def main(out_dir, want_rects=False):
    img = build()
    os.makedirs(out_dir, exist_ok=True)
    plain = build(labels=False)
    plain.convert('RGBA').save(os.path.join(out_dir, 'panel_for_weathering_384x1200.png'))
    guide(plain).save(os.path.join(out_dir, 'panel_guide_384x1200.png'))
    hi = img.convert('RGBA')
    os.makedirs(out_dir, exist_ok=True)
    hi_path = os.path.join(out_dir, 'panel_hi.png')
    hi.save(hi_path)
    base = img.resize((W, H), Image.LANCZOS)
    base.save(os.path.join(out_dir, 'panel_base.png'))
    print('wrote %s (%dx%d) and panel_base.png (%dx%d)' % (hi_path, *hi.size, W, H))

    if want_rects:
        print()
        print('--- rectangles for GeoscapeState, base coords (x is screenWidth-N) ---')
        for name, x, y, w, h in COMMAND:
            print('  %-12s TextButton(%d, %d, screenWidth-%d, screenHeight/2-100+%d)'
                  % (name, w, h, W - x, y))
        for i, (x, y, w, h) in enumerate(SPEED):
            print('  speed%-7d TextButton(%d, %d, screenWidth-%d, screenHeight/2-100+%d)'
                  % (i, w, h, W - x, y))
        for name, x, y, w, h in CONTROLS:
            print('  %-12s InteractiveSurface(%d, %d, screenWidth-%d, screenHeight/2-100+%d)'
                  % (name, w, h, W - x, y))
        x, y, w, h = CLOCK_WELL
        print('  clock well   x %d..%d  y %d..%d' % (x, x + w, y, y + h))
        x, y, w, h = DATE_WELL
        print('  date well    x %d..%d  y %d..%d' % (x, x + w, y, y + h))
        for t, y in EXTRA:
            print('  %-12s value well x %d..%d  y %d..%d'
                  % (t, 2 + EXTRA_LABEL_W, 62, y, y + 8))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], '--rects' in sys.argv)
