#!/usr/bin/env python3
"""The ground under an air fight -> terrain sets the battle engine can load (DOGFIGHT_DESIGN_v1 sections 2, 13).

    python3 build/make_air_terrain.py ART_DIR

ART_DIR is Reference\\dogfight_art.zip unpacked: 01_ground/sky_<kind>_<1-8>.png, 128 x 64 diamonds
(desert, farm, forest, mountain, ocean, town). For each kind writes, in mod/:
  TERRAIN/AIR_<KIND>.MCD           8 floors, each cloned from the stock grass floor (indestructible)
  TERRAIN/AIR_<KIND>.PCK/.TAB      32 x 40 frames;  AIR_<KIND>_4X.PCK/.TAB + _4X.png at 128 x 160
  MAPS/AIR<K>0..3.MAP, ROUTES/...  10 x 10 x 5 blocks: the ground picture on floor 0, four empty decks
The air fight's map script fills the 40 x 40 sky with those blocks at random.
"""
import os
import struct
import sys
import random
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, '..', 'mod'))
ART = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/df'
STOCK = '/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad/oxc/oxce/build/bin/UFO/TERRAIN/CULTIVAT.MCD'
PAL_FROM = os.path.join(MOD, 'TERRAIN', 'OUTHALL.PCK')  # palette comes from the battle palette below
KINDS = ['desert', 'farm', 'forest', 'mountain', 'ocean', 'town']


def battle_palette():
    sys.path.insert(0, '/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad/hd')
    from pck import palette
    return np.array(palette(4), np.int32)


def quant(rgba, PAL):
    a = np.array(rgba).astype(np.int32)
    out = np.zeros(a.shape[:2], np.uint8)
    m = a[..., 3] > 127
    U = PAL[1:255]
    f = a[..., :3][m]
    if len(f):
        out[m] = ((f[:, None, :] - U[None]) ** 2).sum(-1).argmin(1) + 1
    return out


def pck(frames):
    data = b''; offs = []
    for f in frames:
        offs.append(len(data)); h, w = f.shape; rows = 0
        while rows < h and not f[rows].any(): rows += 1
        out = bytearray([min(rows, 254)]); flat = f[rows:].ravel(); i = 0; n = len(flat); last = n
        while last > 0 and flat[last - 1] == 0: last -= 1
        while i < last:
            if flat[i] == 0:
                j = i
                while j < last and flat[j] == 0 and j - i < 255: j += 1
                out += bytes([254, j - i]); i = j
            else:
                out.append(int(flat[i]) if flat[i] not in (254, 255) else 253); i += 1
        out.append(255); data += bytes(out)
    return data, b''.join(struct.pack('<I', o) for o in offs)


def main():
    PAL = battle_palette()
    grass = bytearray(open(STOCK, 'rb').read()[0:62])
    for kind in KINDS:
        K = kind.upper()
        cells4 = []
        for i in range(1, 9):
            d = Image.open(os.path.join(ART, '01_ground', f'sky_{kind}_{i}.png')).convert('RGBA')
            c = Image.new('RGBA', (128, 160), (0, 0, 0, 0))
            c.alpha_composite(d, (0, 96))          # the floor diamond's place in a 4x tile frame
            cells4.append(c)
        hd = [quant(c, PAL) for c in cells4]
        lo = [quant(c.resize((32, 40), Image.LANCZOS), PAL) for c in cells4]
        t = os.path.join(MOD, 'TERRAIN')
        for suffix, fr in (('_4X', hd), ('', lo)):
            d, tab = pck(fr)
            open(os.path.join(t, f'AIR_{K}{suffix}.PCK'), 'wb').write(d)
            open(os.path.join(t, f'AIR_{K}{suffix}.TAB'), 'wb').write(tab)
        sheet = Image.new('RGBA', (1024, 160), (0, 0, 0, 0))
        for i, c in enumerate(cells4):
            sheet.alpha_composite(c, (i * 128, 0))
        sheet.save(os.path.join(t, f'AIR_{K}_4X.png'))
        mcd = b''
        for i in range(8):
            e = bytearray(grass)
            for k in range(8): e[k] = i         # the frame
            e[42] = 255                          # armour: the ground below can't be shot up
            e[44] = 0; e[46] = 0                 # no death or alternate tile
            mcd += bytes(e)
        open(os.path.join(t, f'AIR_{K}.MCD'), 'wb').write(mcd)
        # four 10 x 10 x 5 blocks of random ground; MAP byte = 2 (BLANKS) + floor index
        rnd = random.Random(kind)
        for b in range(4):
            out = bytearray([10, 10, 5])
            for z in range(5):                    # top level first
                for y in range(10):
                    for x in range(10):
                        floor = 2 + rnd.randrange(8) if z == 4 else 0
                        out += bytes([floor, 0, 0, 0])
            open(os.path.join(MOD, 'MAPS', f'AIR{K[:3]}{b}.MAP'), 'wb').write(out)
            open(os.path.join(MOD, 'ROUTES', f'AIR{K[:3]}{b}.RMP'), 'wb').write(b'')
        print(kind, 'done')


def sea(sea_art):
    """The sea under a sea fight (SEA_BATTLES_DESIGN_v1 section 2): three floors - the sea floor (0), the water
    surface (1) that boats sit on and that hides what is below it, and the air above (2).
    SEA_ART is Reference\\sea_art.zip unpacked: 02_floor/floor_ocean_<1-8>.png, 01_surface/sea_ocean_<1-8>.png."""
    PAL = battle_palette()
    grass = bytearray(open(STOCK, 'rb').read()[0:62])
    cells4 = []
    for kind, n in (('02_floor/floor_ocean_', 8), ('01_surface/sea_ocean_', 8)):
        for i in range(1, n + 1):
            d = Image.open(os.path.join(sea_art, f'{kind}{i}.png')).convert('RGBA')
            c = Image.new('RGBA', (128, 160), (0, 0, 0, 0))
            c.alpha_composite(d, (0, 96))
            cells4.append(c)
    hd = [quant(c, PAL) for c in cells4]
    lo = [quant(c.resize((32, 40), Image.LANCZOS), PAL) for c in cells4]
    t = os.path.join(MOD, 'TERRAIN')
    for suffix, fr in (('_4X', hd), ('', lo)):
        d, tab = pck(fr)
        open(os.path.join(t, f'SEA_OCEAN{suffix}.PCK'), 'wb').write(d)
        open(os.path.join(t, f'SEA_OCEAN{suffix}.TAB'), 'wb').write(tab)
    sheet = Image.new('RGBA', (1024, 320), (0, 0, 0, 0))
    for i, c in enumerate(cells4):
        sheet.alpha_composite(c, ((i % 8) * 128, (i // 8) * 160))
    sheet.save(os.path.join(t, 'SEA_OCEAN_4X.png'))
    mcd = b''
    for i in range(16):
        e = bytearray(grass)
        for k in range(8): e[k] = i
        e[42] = 255; e[44] = 0; e[46] = 0
        mcd += bytes(e)
    open(os.path.join(t, 'SEA_OCEAN.MCD'), 'wb').write(mcd)
    rnd = random.Random('sea')
    for b in range(4):
        out = bytearray([10, 10, 3])
        for z in range(3):                       # top level first: air, surface, sea floor
            for y in range(10):
                for x in range(10):
                    if z == 0: v = 0
                    elif z == 1: v = 2 + 8 + rnd.randrange(8)   # the water surface
                    else: v = 2 + rnd.randrange(8)             # the sea floor
                    out += bytes([v, 0, 0, 0])
        open(os.path.join(MOD, 'MAPS', f'SEAOCE{b}.MAP'), 'wb').write(out)
        open(os.path.join(MOD, 'ROUTES', f'SEAOCE{b}.RMP'), 'wb').write(b'')
    print('sea done')


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--sea':
        sea(sys.argv[2])
    else:
        main()
