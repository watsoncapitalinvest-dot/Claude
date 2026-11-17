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


# WALK16 layout (BRIEF_FOR_BUILD_Walk16; UnitSprite::drawRoutineWhole reads it when a sheet has 896 frames):
# the six still clips at 8 facings x 8 frames, then four walks at 8 facings x 16 frames.
W16 = [('stand', 0, 8), ('kneel', 64, 8), ('aim', 128, 8), ('death', 192, 8), ('pstand', 256, 8), ('pkneel', 320, 8),
       ('walk', 384, 16), ('pwalk', 512, 16), ('swalk', 640, 16), ('ewalk', 768, 16)]


def load_meta(srcs):
    """One or more render dirs (the Walk16 walks are rendered on their own): clip -> (dir, frames), anchors merged."""
    meta, where = None, {}
    for s in srcs:
        m = json.load(open(os.path.join(s, 'meta.json')))
        cf = m.get('clipframes', {})
        for c in m['clips']:
            where[c] = (s, cf.get(c, m['frames']))
        if meta is None:
            meta = m
        else:
            meta['anchors'].update(m['anchors'])
    return meta, where


def main(src, out_dir, stem):
    srcs = src.split(',')
    meta, where = load_meta(srcs)
    src = srcs[0]
    w16 = os.environ.get('W16') == '1'
    nf = meta['frames']
    k = ink.FINAL[0] / meta['res'][0]
    # one scale for the sheet: from the standing man facing the camera
    probe = ink.ink_frame(Image.open(f'{src}/stand/d5_f00_beauty.png').convert('RGBA'), Image.open(f'{src}/stand/d5_f00_id.png'))
    ys = np.nonzero(np.asarray(probe)[..., 3] > 40)[0]
    feet5 = meta['anchors']['stand/5/0']['feet'][1] * k
    s = TALL / (feet5 - ys.min())
    # sheets rendered on a fixed reference height keep a tall man tall: scale so a
    # 1.78 m man (Duke) stands TALL px, everyone else in proportion
    if 'ref_h' in meta:
        s *= meta['h49'] / 1.78
    print('scale %.3f (standing figure %d px at render size)' % (s, feet5 - ys.min()))
    if w16:
        missing = [c for c, _, _ in W16 if c not in where]
        if missing:
            sys.exit('W16 sheet needs every clip; missing: %s' % ', '.join(missing))
        layout = W16
    else:
        layout = [(c, i * 64, 8) for i, c in enumerate([c for c in CLIPS if c in where])]
    clips = [c for c, _, _ in layout]
    rows = (max(b + 8 * n for _, b, n in layout) + COLS - 1) // COLS
    sheet = Image.new('RGBA', (COLS * CW, rows * CH), (0, 0, 0, 0))
    lines = []
    for clip, base, per in layout:
        csrc, cnf = where[clip]
        if cnf != per:
            sys.exit('clip %s rendered at %d frames, layout wants %d' % (clip, cnf, per))
        for d in range(8):
            kdir = render_dir(d)
            fx, fy = [v * k for v in meta['anchors'][f'stand/{kdir}/0']['feet']]
            for f in range(per):
                p = f'{csrc}/{clip}/d{kdir}_f{f:02d}'
                fr = ink.ink_frame(Image.open(p + '_beauty.png').convert('RGBA'), Image.open(p + '_id.png'))
                big = fr.resize((round(fr.width * s), round(fr.height * s)), Image.LANCZOS)
                ox, oy = round(CENTRE_X - fx * s), round(FEET_Y - fy * s)
                cell = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
                cell.alpha_composite(big, (max(0, ox), max(0, oy)), (max(0, -ox), max(0, -oy)))
                n = base + d * per + f
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
