#!/usr/bin/env python3
"""Rendered clips -> the game's whole-body soldier sheet, its 8-bit twin and hand anchors.

    python3 assemble_sheet.py <render dir> <mod Units dir> <stem>

LAYOUT (UnitSprite::drawRoutineWhole reads it the same way):
    cell 128 x 160 (4x), 16 cells a row
    frame = clip * 64 + dir * 8 + f      clips: stand walk kneel aim death
    dir is the game's direction, 0 = up-right on screen, clockwise.
The figure is scaled once for the whole sheet so the standing man is as tall as
the current soldiers (116 px at 4x) and his feet sit on row 152, centred.

Writes <stem>_body.png (8-bit), <stem>_body_rgb.png (RGBA) and
<stem>_body_anchors.txt: one line per frame, "frame rx ry lx ly" - the right
and left hand in cell pixels at 4x - for the game to hold weapons by.
"""
import json
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..')))
import soldier_ink as ink                                    # noqa: E402
import make_weapon_sprites as mws                            # noqa: E402

CLIPS = ['stand', 'walk', 'kneel', 'aim', 'death', 'pstand', 'pwalk', 'pkneel']   # the last three (one-handed) only when rendered
CW, CH, COLS = 128, 160, 16
TALL, FEET_Y, CENTRE_X = 116, 152, 64


def render_dir(d):
    return ((d + 1) % 8) + 1          # game 0 (up-right) = render 2 'away-right'


def main(src, out_dir, stem):
    meta = json.load(open(os.path.join(src, 'meta.json')))
    nf = meta['frames']
    k = ink.FINAL[0] / meta['res'][0]
    # one scale for the sheet: from the standing man facing the camera
    probe = ink.ink_frame(Image.open(f'{src}/stand/d5_f00_beauty.png').convert('RGBA'), Image.open(f'{src}/stand/d5_f00_id.png'))
    ys = np.nonzero(np.asarray(probe)[..., 3] > 40)[0]
    feet5 = meta['anchors']['stand/5/0']['feet'][1] * k
    s = TALL / (feet5 - ys.min())
    print('scale %.3f (standing figure %d px at render size)' % (s, feet5 - ys.min()))
    clips = [c for c in CLIPS if c in meta['clips']]
    rows = (len(clips) * 64 + COLS - 1) // COLS
    sheet = Image.new('RGBA', (COLS * CW, rows * CH), (0, 0, 0, 0))
    lines = []
    for ci, clip in enumerate(clips):
        for d in range(8):
            kdir = render_dir(d)
            fx, fy = [v * k for v in meta['anchors'][f'stand/{kdir}/0']['feet']]
            for f in range(nf):
                p = f'{src}/{clip}/d{kdir}_f{f:02d}'
                fr = ink.ink_frame(Image.open(p + '_beauty.png').convert('RGBA'), Image.open(p + '_id.png'))
                big = fr.resize((round(fr.width * s), round(fr.height * s)), Image.LANCZOS)
                ox, oy = round(CENTRE_X - fx * s), round(FEET_Y - fy * s)
                cell = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
                cell.alpha_composite(big, (max(0, ox), max(0, oy)), (max(0, -ox), max(0, -oy)))
                n = ci * 64 + d * 8 + f
                sheet.alpha_composite(cell, ((n % COLS) * CW, (n // COLS) * CH))
                a = meta['anchors'][f'{clip}/{kdir}/{f}']
                rx, ry = [v * k * s for v in a['rh']]
                lx, ly = [v * k * s for v in a['lh']]
                lines.append('%d %.1f %.1f %.1f %.1f' % (n, rx + ox, ry + oy, lx + ox, ly + oy))
        print('clip', clip, 'placed')
    pal, legal, lp = mws.palette_and_legal()
    a = np.asarray(sheet).copy()
    a[..., 3] = np.where(a[..., 3] > 100, 255, 0)
    # quantise in strips: the whole sheet at once is millions of pixels times
    # the palette, more memory than the container has
    rows_ = []
    for y0 in range(0, a.shape[0], CH):
        rows_.append(np.asarray(mws.quantise(Image.fromarray(a[y0:y0 + CH], 'RGBA'), pal, legal, lp)))
    base = Image.fromarray(np.vstack(rows_), 'P'); base.putpalette(pal)
    sheet.save(os.path.join(out_dir, f'{stem}_body_rgb.png'))
    base.save(os.path.join(out_dir, f'{stem}_body.png'))
    open(os.path.join(out_dir, f'{stem}_body_anchors.txt'), 'w').write('\n'.join(lines) + '\n')
    print('wrote %s_body.png, %s_body_rgb.png (%dx%d), %d anchors' % (stem, stem, sheet.width, sheet.height, len(lines)))


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
