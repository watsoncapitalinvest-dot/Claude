#!/usr/bin/env python3
"""Air fight aircraft -> unit sheets for drawing routine 23 (DOGFIGHT_DESIGN_v1 section 13).

    python3 build/make_air_units.py SRC_DIR

SRC_DIR holds the straight-down top views (1024x1024, nose up, magenta background):
craft_skystriker_top.png, craft_tomahawk_top.png (Reference\\aircraft_cartoon.zip).
Each aircraft's 8 headings are made from its one top view, the way section 13 asks: turn it to the
heading, turn 45 degrees onto the grid, squash the height by half for the battle camera.

Writes mod/Resources/Units/air_<name>_body.png (palette, like the soldier sheets) and its _rgb.png twin:
2048 x 5120, cells 128 x 160, frame = clip * 64 + heading * 8 + f; clips stand, walk, kneel, aim, death.
Every clip but death is the same picture (an aircraft has no legs); death sinks and darkens it.

STAND-INS: only the Skystriker and the Tomahawk have top views. Every other aircraft is the nearer of the
two, repainted in its side's colours, until its own top view (or 3D render) arrives. The table says which.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, '..', 'mod'))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'art', 'topviews')
PAL_FROM = os.path.join(MOD, 'Resources', 'Units', 'hawk_body.png')

# name: (top view, tint (r,g,b) or None, scale of the tile it fills, stand-in?)
AIRCRAFT = {
    'skystriker':     ('craft_skystriker_top.png', None, 0.95, False),
    'conquest':       ('craft_skystriker_top_wings_back.png', (235, 235, 245), 0.85, True),
    'phantom':        ('craft_skystriker_top_wings_back.png', (60, 60, 70), 0.85, True),
    'tomahawk':       ('craft_tomahawk_top.png', None, 0.95, False),
    'rattler':        ('craft_skystriker_top.png', (40, 70, 170), 0.95, True),
    'firebat':        ('craft_skystriker_top_wings_back.png', (120, 30, 40), 0.85, True),
    'night_raven':    ('craft_skystriker_top_wings_back.png', (25, 25, 35), 0.9, True),
    'cartel_plane':   ('craft_tomahawk_top.png', (215, 200, 160), 0.75, True),
    # vessels: top views from John's 3D kits by build/render_topview.py (BUILD's quick renderer)
    'cobra_ship':     ('craft_cobra_ship_top.png', None, 1.0, False),
    'devilfish':      ('craft_devilfish_top.png', None, 0.9, False),
    'moray':          ('craft_moray_top.png', None, 0.95, False),
    'moccasin':       ('craft_moccasin_top.png', None, 0.9, False),
    'raft':           ('craft_raft_top.png', None, 0.6, False),
}

# 2x2 aircraft (transports, the bomber): 256 x 320 cells, 8 a row; frames 0-7 the headings, then
# 8 + heading * 8 + f the death frames (engine: UnitSprite::drawRoutineWhole, size 2)
BIG = {
    'tomahawk_big':   ('craft_tomahawk_top.png', None, 0.95, False),
    'condor':         ('craft_skystriker_top_wings_back.png', (30, 40, 90), 0.95, True),
}


def unmagenta(im):
    a = np.array(im.convert('RGB')).astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    key = (r > 180) & (b > 180) & (g < 110)
    alpha = np.where(key, 0, 255).astype(np.uint8)
    out = np.dstack([a.astype(np.uint8), alpha])
    return Image.fromarray(out, 'RGBA')


def tint(im, rgb):
    if not rgb:
        return im
    a = np.array(im).astype(np.float32)
    lum = (a[..., :3] @ np.array([0.3, 0.59, 0.11]))[..., None] / 255.0
    col = np.array(rgb, np.float32)[None, None, :]
    # keep the line work: dark stays dark, light takes the colour
    mixed = np.clip(col * (0.35 + 0.9 * lum), 0, 255)
    a[..., :3] = a[..., :3] * 0.25 + mixed * 0.75
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def heading(top, d, scale, width=120):
    """OpenXcom heading d (0 = map north = screen up-right, clockwise) -> the iso picture"""
    plan = top.rotate(-45 * d, resample=Image.BICUBIC, expand=True)    # nose to the heading on the plan
    iso = plan.rotate(-45, resample=Image.BICUBIC, expand=True)        # the plan onto the grid
    iso = iso.resize((iso.width, iso.height // 2), Image.LANCZOS)      # the battle camera's squash
    bbox = iso.getbbox()
    iso = iso.crop(bbox) if bbox else iso
    k = width * scale / max(iso.width, 1)
    return iso.resize((max(1, int(iso.width * k)), max(1, int(iso.height * k))), Image.LANCZOS)


def cell(pic, dy=0, dark=1.0, alpha=1.0, big=False):
    W, H, cy = (256, 320, 224) if big else (128, 160, 112)
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if dark != 1.0:
        pic = ImageEnhance.Brightness(pic).enhance(dark)
    if alpha != 1.0:
        a = np.array(pic); a[..., 3] = (a[..., 3] * alpha).astype(np.uint8); pic = Image.fromarray(a, 'RGBA')
    # hangs in the middle of its tile: centre on row 112 (the floor diamond's centre is row 128)
    c.alpha_composite(pic, (W // 2 - pic.width // 2, cy - pic.height // 2 + dy))
    return c


def quantize(rgba, pal):
    a = np.array(rgba).astype(np.int32)
    out = np.zeros(a.shape[:2], np.uint8)
    m = a[..., 3] > 127
    P = np.array(pal, np.int32).reshape(-1, 3)[1:255]
    f = a[..., :3][m]
    idx = np.empty(len(f), np.int64)
    for i in range(0, len(f), 20000):
        ch = f[i:i + 20000]
        idx[i:i + 20000] = ((ch[:, None, :] - P[None]) ** 2).sum(-1).argmin(1) + 1
    out[m] = idx
    im = Image.fromarray(out, 'P')
    im.putpalette(pal)
    return im


def main():
    pal = Image.open(PAL_FROM).getpalette()
    units = os.path.join(MOD, 'Resources', 'Units')
    only = sys.argv[2:]   # names to build (default: all)
    for name, (src, rgb, scale, standin) in AIRCRAFT.items():
        if only and name not in only: continue
        top = tint(unmagenta(Image.open(os.path.join(SRC, src))), rgb)
        sheet = Image.new('RGBA', (2048, 5120), (0, 0, 0, 0))
        for d in range(8):
            pic = heading(top, d, scale)
            for clip in range(5):
                for f in range(8):
                    if clip == 4:   # death: it drops and darkens
                        c = cell(pic, dy=f * 5, dark=1.0 - f * 0.08, alpha=1.0 - f * 0.1)
                    else:
                        c = cell(pic)
                    fr = clip * 64 + d * 8 + f
                    sheet.alpha_composite(c, ((fr % 16) * 128, (fr // 16) * 160))
        sheet.save(os.path.join(units, f'air_{name}_body_rgb.png'))
        quantize(sheet, pal).save(os.path.join(units, f'air_{name}_body.png'))
        print(name, 'stand-in' if standin else 'own art')
    for name, (src, rgb, scale, standin) in BIG.items():
        if only and name not in only: continue
        top = tint(unmagenta(Image.open(os.path.join(SRC, src))), rgb)
        sheet = Image.new('RGBA', (2048, 2880), (0, 0, 0, 0))
        for d in range(8):
            pic = heading(top, d, scale, width=240)
            frames = [(d, cell(pic, big=True))]
            for f in range(8):
                frames.append((8 + d * 8 + f, cell(pic, dy=f * 10, dark=1.0 - f * 0.08, alpha=1.0 - f * 0.1, big=True)))
            for fr, c in frames:
                sheet.alpha_composite(c, ((fr % 8) * 256, (fr // 8) * 320))
        sheet.save(os.path.join(units, f'air_{name}_body_rgb.png'))
        quantize(sheet, pal).save(os.path.join(units, f'air_{name}_body.png'))
        print(name, '2x2', 'stand-in' if standin else 'own art')


if __name__ == '__main__':
    main()
