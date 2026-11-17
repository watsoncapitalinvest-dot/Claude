"""Bullets you can see (John 17 Nov 00:08). The tracer, heavy tracer and grenade-ball cells drew a head a fifth of a tile
across: about 13 screen pixels at 1920 wide, which reads as a speck. This grows every cell of those three rows 1.6x about
its centre, inside the same 48x48 cell, in both the paletted and the RGBA sheet. Lasers, pulse, rockets and missiles
already fill their cells and are left alone.
Run once after build/make_projectile_sheet.py; it refuses a sheet already grown.
"""
import os, sys
from PIL import Image
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mod', 'Resources', 'Projectiles')
ROWS, F, FIRST = (11, 12, 17), 1.6, 11
rgb = Image.open(os.path.join(D, 'projectiles_rgb.png')).convert('RGBA')
bb = rgb.crop((0, 0, 48, 48)).getbbox()
if bb and bb[2] - bb[0] > 24:
    sys.exit('already grown (row 11 head is %d wide)' % (bb[2] - bb[0]))
pal = Image.open(os.path.join(D, 'projectiles.png'))
def grow(im, resample):
    for r in ROWS:
        y = (r - FIRST) * 48
        for c in range(35):
            cell = im.crop((c * 48, y, c * 48 + 48, y + 48))
            n = int(round(48 * F))
            big = cell.resize((n, n), resample)
            o = (n - 48) // 2
            im.paste(big.crop((o, o, o + 48, o + 48)), (c * 48, y))
grow(rgb, Image.LANCZOS); grow(pal, Image.NEAREST)
rgb.save(os.path.join(D, 'projectiles_rgb.png')); pal.save(os.path.join(D, 'projectiles.png'))
print('grown rows', ROWS, 'x', F)
