#!/usr/bin/env python3
"""The equipment screen's backdrop, painted fresh: TAC01.SCR and its sharp twin.

    python3 build/make_inventory_bg.py [--write]

John: "the font and lines and buttons need to be redone in the inventory
screen". The old screen is X-COM's: a black field, one-pixel grey grid lines
zoomed into four-pixel bars, and pink bevelled buttons painted into the 1994
background. This replaces the background with the geoscape console's own
language - painted steel, cut wells, stencilled keys - so the two screens read
as one machine.

THE SLOTS ARE PAINTED HERE, ON THE ENGINE'S OWN RECTANGLES. Every slot cell is
a well cut into the plate at exactly the cell the inventory ruleset gives it
(SLOT 16x16, hands 32x48, ground from y 152 to the bottom). The engine still
draws its 8-bit grid; HiUI claims those pixels and lets this painting show
through, so the "lines" become the steel lands between wells - drawn at display
resolution, never zoomed. A slot can therefore only be where its well is.

THE BUTTONS ARE PAINTED ON THE WIDGET RECTANGLES in InventoryState.cpp
(BattlescapeButton is an invisible hitbox over the background), for the same
reason: a key can only be drawn where it is clicked.

Writes, into mod/Resources/Backgrounds:
    TAC01.png      320 x 200  8-bit, battlescape palette
    TAC01_hi.png   1920 x 1200 RGBA, 6x
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_panel as mp                                     # noqa: E402

MOD = os.path.normpath(os.path.join(HERE, '..', 'mod'))
K = mp.K
W, H = 320, 200


def px(v):
    return int(round(v * K))


# ------------------------------------------------------------- the layout
# standard/xcom1/inventories.rul, which this mod does not override:
# (id, x, y, cells) with cells as (col, row); hands are one 2x3 well.
SLOT = 16
INVS = [
    ('RIGHT_SHOULDER', 16, 37, [(0, 0), (1, 0)]),
    ('LEFT_SHOULDER', 112, 37, [(0, 0), (1, 0)]),
    ('BACK_PACK', 192, 37, [(c, r) for r in range(3) for c in range(3)]),
    ('BELT', 192, 104, [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (3, 1)]),
    ('RIGHT_LEG', 0, 120, [(0, 0), (1, 0)]),
    ('LEFT_LEG', 128, 120, [(0, 0), (1, 0)]),
]
HANDS = [('RIGHT_HAND', 0, 63), ('LEFT_HAND', 128, 63)]   # 32 x 48
GROUND_Y = 152

# InventoryState.cpp: (label, x, y, w, h). The art is drawn ON these.
KEYS = [('OK', 237, 1, 35, 22), ('<', 273, 1, 23, 22), ('>', 297, 1, 23, 22),
        ('UNLOAD', 288, 32, 32, 25), ('GROUND', 289, 137, 32, 15)]

PLATE      = (40, 45, 35)       # darker than the geoscape plate: items must read on it
PLATE_LIT  = (58, 64, 50)


def plate(img):
    w, h = img.size
    rng = np.random.default_rng(23)
    a = np.zeros((h, w, 3), np.float32)
    a[:, :] = PLATE
    streak = rng.normal(0, 2.6, (1, w)).repeat(h, axis=0) + rng.normal(0, 0.9, (h, w))
    a += streak[:, :, None]
    yy, xx = np.mgrid[0:h, 0:w]
    a += ((1.0 - (xx / w) * 0.5 - (yy / h) * 0.5) * 10.0)[:, :, None]
    np.clip(a, 0, 255, out=a)
    img.paste(Image.fromarray(a.astype(np.uint8)))


def cell(d, x0, y0, x1, y1):
    """A well cut inside one slot rectangle (base coords, edges inclusive of the
    engine's grid line). The land left round it IS the grid line."""
    X0, Y0, X1, Y1 = px(x0 + 1.15), px(y0 + 1.15), px(x1 - 0.15), px(y1 - 0.15)
    r = px(0.9)
    d.rounded_rectangle([X0 - 2, Y0 - 2, X1 + 2, Y1 + 2], r + 2, fill=mp.RIM_DARK)
    d.rounded_rectangle([X0 - 1, Y0, X1 + 2, Y1 + 2], r + 2, fill=(96, 104, 80))
    d.rounded_rectangle([X0 - 2, Y0 - 2, X1, Y1], r + 2, fill=mp.RIM_DARK)
    d.rounded_rectangle([X0, Y0, X1, Y1], r, fill=(15, 16, 13))


def key(img, d, label, x, y, w, h):
    """A raised console key on the button's own hitbox, label stencilled on it."""
    X0, Y0, X1, Y1 = px(x + 0.6), px(y + 0.6), px(x + w - 0.6), px(y + h - 0.6)
    r = px(1.4)
    d.rounded_rectangle([X0 + 3, Y0 + 4, X1 + 3, Y1 + 4], r, fill=(14, 15, 12))       # shadow
    d.rounded_rectangle([X0, Y0, X1, Y1], r, fill=mp.OLIVE_DARK)
    d.rounded_rectangle([X0 + 2, Y0 + 2, X1 - 2, Y1 - 3], r - 1, fill=mp.OLIVE)
    # lit top, darker foot: the key stands out of the plate
    for i in range(px(2.2)):
        a = int(70 * (1 - i / px(2.2)))
        d.line([X0 + r // 2, Y0 + 2 + i, X1 - r // 2, Y0 + 2 + i], fill=(190, 198, 160, a))
    d.rounded_rectangle([X0, Y0, X1, Y1], r, outline=(22, 25, 18), width=2)
    cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2 - 1
    ink = (226, 222, 196)
    if label in ('<', '>'):
        s = min(X1 - X0, Y1 - Y0) * 0.24
        sgn = -1 if label == '<' else 1
        pts = [(cx + sgn * s * 1.1, cy), (cx - sgn * s * 0.8, cy - s), (cx - sgn * s * 0.8, cy + s)]
        d.polygon([(p[0] + 2, p[1] + 2) for p in pts], fill=(24, 27, 20))
        d.polygon(pts, fill=ink)
        return
    if label == 'GROUND':
        # the ground strip scrolls: an arrow pointing along it
        s = (Y1 - Y0) * 0.26
        L = (X1 - X0) * 0.30
        d.rectangle([cx - L, cy - s * 0.32, cx + L * 0.25, cy + s * 0.32], fill=ink)
        d.polygon([(cx + L, cy), (cx + L * 0.2, cy - s), (cx + L * 0.2, cy + s)], fill=ink)
        return
    # text keys: largest stencil size that leaves a margin inside the key
    size = px(9)
    while size > 8:
        f = mp.stencil_font(size)
        bb = f.getbbox(label)
        if bb[2] - bb[0] <= (X1 - X0) * 0.80 and bb[3] - bb[1] <= (Y1 - Y0) * 0.50:
            break
        size -= 1
    f = mp.stencil_font(size)
    bb = f.getbbox(label)
    tx = cx - (bb[0] + bb[2]) / 2
    ty = cy - (bb[1] + bb[3]) / 2
    m = mp.stencil(img, (tx, ty), label, size, 255)
    sh = Image.new('RGBA', img.size, (24, 27, 20, 0))
    sh.putalpha(m.point(lambda v: int(v * 0.85)))
    img.paste(sh, (2, 2), sh)
    face = Image.new('RGBA', img.size, ink + (0,))
    face.putalpha(m)
    img.paste(face, (0, 0), face)


def screw(d, x, y):
    mp.screw(d, x, y)


def build():
    img = Image.new('RGB', (W * K, H * K))
    plate(img)
    d = ImageDraw.Draw(img, 'RGBA')

    # the ground tray: a sunken bed the ground cells sit in, to the bottom edge
    d.rectangle([0, px(GROUND_Y - 1.2), W * K, H * K], fill=(28, 31, 24))
    d.line([0, px(GROUND_Y - 1.2), W * K, px(GROUND_Y - 1.2)], fill=(20, 22, 17), width=3)

    for _, x, y, cells in INVS:
        for c, r in cells:
            cell(d, x + c * SLOT, y + r * SLOT, x + (c + 1) * SLOT, y + (r + 1) * SLOT)
    for _, x, y in HANDS:
        cell(d, x, y, x + 2 * SLOT, y + 3 * SLOT)
    for x in range(0, W, SLOT):
        for y in range(GROUND_Y, H, SLOT):
            cell(d, x, y, x + SLOT, min(H + 0.6, y + SLOT))

    for k in KEYS:
        key(img, d, *k)

    # fasteners in the open metal
    for x, y in ((176, 146), (240, 146), (316, 66), (316, 130), (110, 100)):
        screw(d, x, y)
    return img


def palette_and_legal():
    pal = Image.open(os.path.join(MOD, 'Resources', 'Cobra', 'hold_pistol.png')).getpalette()
    import make_weapon_sprites as mws
    _, legal, lp = mws.palette_and_legal()
    return pal, legal, lp


def main(write):
    hi = build().convert('RGBA')
    pal, legal, lp = palette_and_legal()
    import make_weapon_sprites as mws
    base = mws.quantise(hi.resize((W, H), Image.LANCZOS), pal, legal, lp)
    prev = '/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad/inv_bg_preview.png'
    hi.save(prev)
    print('preview', prev)
    if write:
        out = os.path.join(MOD, 'Resources', 'Backgrounds')
        hi.save(os.path.join(out, 'TAC01_hi.png'))
        base.save(os.path.join(out, 'TAC01.png'))
        print('written TAC01.png (320x200) and TAC01_hi.png (1920x1200)')


if __name__ == '__main__':
    main('--write' in sys.argv)
