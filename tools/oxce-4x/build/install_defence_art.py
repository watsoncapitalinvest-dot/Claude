#!/usr/bin/env python3
"""Install the graphics AI's base-defence pictures (art_briefs/BASE_DEFENCES_BRIEF.txt) as game sheets.

    python3 build/install_defence_art.py <folder with <kind>_d0..d7.png and <kind>_wreck.png> <kind>

<kind> is mg, missile, gate or checkpoint. Writes mod/Resources/Units/gj_def_<kind>_body.png (8-bit) and _body_rgb.png
(full colour), in the whole-body layout UnitSprite routine 23 reads for a one-tile unit: frame = clip * 64 + facing * 8 + f,
clips stand 0, walk 1, kneel 2, aim 3, death 4. A defence never moves, so stand, walk, kneel and aim all show the facing's
picture, and death plays the wreck (it is also what lies on the floor afterwards).
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_weapon_sprites as mws    # noqa: E402

src, kind = sys.argv[1], sys.argv[2]
CW, CH, COLS, CLIPS = 128, 160, 16, 5
OUT = os.path.normpath(os.path.join(HERE, '..', 'mod', 'Resources', 'Units'))
faces = [Image.open(os.path.join(src, f'{kind}_d{d}.png')).convert('RGBA') for d in range(8)]
wreck = Image.open(os.path.join(src, f'{kind}_wreck.png')).convert('RGBA')
for im in faces + [wreck]:
    assert im.size == (CW, CH), f'{im.size}: every picture must be 128 x 160'
n = CLIPS * 64
sheet = Image.new('RGBA', (COLS * CW, (n + COLS - 1) // COLS * CH), (0, 0, 0, 0))
for clip in range(CLIPS):
    for d in range(8):
        for f in range(8):
            k = clip * 64 + d * 8 + f
            pic = faces[d]
            if clip == 4:   # the death clip: the turret, then the wreck from the fourth frame on
                pic = faces[d] if f < 3 else wreck
            sheet.paste(pic, ((k % COLS) * CW, (k // COLS) * CH))
rgb = os.path.join(OUT, f'gj_def_{kind}_body_rgb.png')
sheet.save(rgb)
# the 8-bit sheet: quantise the nine pictures once each (the whole sheet at once runs out of memory), then lay them out
pal, legal, lp = mws.palette_and_legal()
def q8(im):
    a = np.asarray(im).copy(); a[..., 3] = np.where(a[..., 3] > 100, 255, 0)
    return mws.quantise(Image.fromarray(a, 'RGBA'), pal, legal, lp)
qf, qw = [q8(f) for f in faces], q8(wreck)
psheet = Image.new('P', sheet.size, 0); psheet.putpalette(qw.getpalette())
for clip in range(CLIPS):
    for d in range(8):
        for f in range(8):
            k = clip * 64 + d * 8 + f
            psheet.paste(qw if (clip == 4 and f >= 3) else qf[d], ((k % COLS) * CW, (k // COLS) * CH))
psheet.save(os.path.join(OUT, f'gj_def_{kind}_body.png'))
print('wrote', rgb, sheet.size)
