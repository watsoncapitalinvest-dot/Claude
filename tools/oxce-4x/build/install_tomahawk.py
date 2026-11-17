#!/usr/bin/env python3
"""MAPS' Tomahawk landing crafts (BRIEF_FOR_BUILD_TomahawkCraft / Gunship / Missile / GunshipMissile, 16 Nov) -> the game.

    python3 build/install_tomahawk.py DOORGUN_DIR

The four maps, routes and terrain sets are copied in by hand from the zips (private: gitignored) and padded to 20 x 30 by
build/pad_map2.py. This script makes the door-gun turret's unit sheet from MAPS' doorgun/ frames (128 x 160, 8 facings, idle
used for every clip: 1x1 layout = clip*64 + facing*8 + f, as gen_vehicles.py) into Resources/VehiclesPrivate, plus the twin.
"""
import os, sys
import numpy as np
from PIL import Image

D = sys.argv[1]
MOD = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mod'))
PAL = Image.open(os.path.join(MOD, 'Resources', 'Units', 'hawk_body.png')).getpalette()
OUT = os.path.join(MOD, 'Resources', 'VehiclesPrivate')
os.makedirs(OUT, exist_ok=True)

def quantize(rgba):
    a = np.array(rgba).astype(np.int32)
    out = np.zeros(a.shape[:2], np.uint8)
    m = a[..., 3] > 127
    P = np.array(PAL, np.int32).reshape(-1, 3)[1:255]
    f = a[..., :3][m]
    idx = np.empty(len(f), np.int64)
    for i in range(0, len(f), 20000):
        ch = f[i:i + 20000]
        idx[i:i + 20000] = ((ch[:, None, :] - P[None]) ** 2).sum(-1).argmin(1) + 1
    out[m] = idx
    im = Image.fromarray(out, 'P'); im.putpalette(PAL)
    return im

sheet = Image.new('RGBA', (2048, 5120), (0, 0, 0, 0))
for clip in range(8):
    for d in range(8):
        fr = Image.open(os.path.join(D, 'doorgun_d%d_idle.png' % d)).convert('RGBA')
        for f in range(8):
            n = clip * 64 + d * 8 + f
            sheet.alpha_composite(fr, ((n % 16) * 128, (n // 16) * 160))
sheet.save(os.path.join(OUT, 'tom_doorgun_body_rgb.png'))
quantize(sheet).save(os.path.join(OUT, 'tom_doorgun_body.png'))
print('door gun sheet: 512 frames')
