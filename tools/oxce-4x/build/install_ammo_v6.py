#!/usr/bin/env python3
"""ART's ammo v6 (one magazine per size, John 13 Nov 2026) -> the ammunition the game has today.

    python3 build/install_ammo_v6.py <ammo dir from ammo_v6.zip> [--write-rules]

The pictures come drawn for the slots the brief asked for (64 px a slot at 4x, centred on a
128x192 canvas). The game draws an inventory picture from the TOP-LEFT of its frame, so each
picture is re-seated into its footprint there. Floor pictures are used as delivered.

Only the ammunition that exists as an item is wired; the rest (mortar, energy, fuel, shotgun)
is kept in art_briefs/returned/ammo_v6 for when those guns are items.
Writes Resources/Items/big_<stem>.png (+ _hi) and floor_<stem>.png (+ _rgb), and with
--write-rules Ruleset/gijoe_ammo_v6.rul (sprites + the new footprints).
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, '..', 'mod'))
OUT = os.path.join(MOD, 'Resources', 'Items')
SRC = sys.argv[1]

# art -> item, stem, (invWidth, invHeight), bigSprite frame, floorSprite frame (vanilla ids)
MAP = [
    ('mag_small',  'STR_PISTOL_CLIP',  'smgclip',    (1, 2), 4, 4),    # the Uzi's magazine
    ('mag_medium', 'STR_RIFLE_CLIP',   'rifleclip',  (1, 2), 2, 2),    # the M4's magazine
    ('mag_large',  'STR_HC_AP_AMMO',   'belt50',     (1, 2), 12, 12),  # the .50 cal's belt can
    ('mag_rocket', 'STR_SMALL_ROCKET', 'rocket',     (1, 2), 16, 16),  # the RPG's rocket
]
SLOT = 16  # base px per inventory slot; the sharp twin is 4x


def quant(rgba, ref):
    pal = Image.open(ref).convert('P').getpalette()[:768]
    p = np.array(pal, np.int16).reshape(-1, 3)[:256].astype(np.float32)[1:]
    a = np.array(rgba)
    c = a[..., :3].astype(np.float32)[:, :, None, :]
    rbar = (c[..., 0] + p[None, None, :, 0]) * 0.5
    dr, dg, db = c[..., 0] - p[None, None, :, 0], c[..., 1] - p[None, None, :, 1], c[..., 2] - p[None, None, :, 2]
    d = (2 + rbar / 256) * dr ** 2 + 4 * dg ** 2 + (2 + (255 - rbar) / 256) * db ** 2
    idx = (d.argmin(-1) + 1).astype(np.uint8)
    idx[a[..., 3] < 128] = 0
    out = Image.fromarray(idx, 'P')
    out.putpalette(pal)
    return out


def seat(art, w, h, k):
    """the picture, fitted to its footprint with a small margin, in the frame's top-left"""
    bb = art.getbbox()
    art = art.crop(bb)
    bw, bh = w * SLOT * k, h * SLOT * k
    m = 4 * k / 4
    s = min((bw - 2 * m) / art.width, (bh - 2 * m) / art.height)
    art = art.resize((max(1, round(art.width * s)), max(1, round(art.height * s))), Image.LANCZOS)
    can = Image.new('RGBA', (32 * k, 48 * k), (0, 0, 0, 0))
    can.alpha_composite(art, (int(bw / 2 - art.width / 2), int(bh / 2 - art.height / 2)))
    return can


rules_sprites, rules_items = [], []
for art, item, stem, (w, h), big, floor in MAP:
    a = Image.open(os.path.join(SRC, art + '_big.png')).convert('RGBA')
    hi = seat(a, w, h, 4)
    hi.save(os.path.join(OUT, f'big_{stem}_hi.png'))
    quant(seat(a, w, h, 1), os.path.join(OUT, 'big_m4.png')).save(os.path.join(OUT, f'big_{stem}.png'))
    f = Image.open(os.path.join(SRC, art + '_floor.png')).convert('RGBA')
    f.save(os.path.join(OUT, f'floor_{stem}_rgb.png'))
    quant(f, os.path.join(OUT, 'floor_m4.png')).save(os.path.join(OUT, f'floor_{stem}.png'))
    rules_sprites += ['  - type: BIGOBS.PCK', '    width: 32', '    height: 48', '    files:',
                      f'      {big}: Resources/Items/big_{stem}.png',
                      '  - type: FLOOROB.PCK', '    width: 128', '    height: 160', '    files:',
                      f'      {floor}: Resources/Items/floor_{stem}.png']
    rules_items += [f'  - type: {item}', f'    invWidth: {w}', f'    invHeight: {h}']
    print(f'{art:11s} -> {item:18s} {w}x{h}')

if '--write-rules' in sys.argv:
    txt = ['# Ammo v6 (ART, 13 Nov 2026): one magazine per size. build/install_ammo_v6.py.',
           '# Footprints follow the art: magazines, the belt can and the rocket are 1 x 2.',
           'extraSprites:'] + rules_sprites + ['', 'items:'] + rules_items
    open(os.path.join(MOD, 'Ruleset', 'zz_gijoe_ammo_v6.rul'), 'w').write('\n'.join(txt) + '\n')
    print('wrote Ruleset/zz_gijoe_ammo_v6.rul')
