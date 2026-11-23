#!/usr/bin/env python3
"""Death clips that stay in the cell (John 22 Nov: "the dead bodies ... clip").

    HAIR=.. FOLD_IDS=.. [PEN..] python3 death_patch.py RENDER_DIR SHEET_STEM

The walk16 sheets' death clip ("death from the front") falls toward the camera in most facings and runs off the bottom
of the 128 x 160 cell, so the body comes out cut flat. RENDER_DIR holds the same man rendered (render_char.py) with
three deaths: death (from the front: falls back), deathb (from the back: falls forward), deathr (from the right: falls
to his left). For each of the eight facings this picks the one that loses least off the bottom (then the sides), and
writes it over frames 192 + facing * 8 + f of mod/Resources/Units/<stem>_body.png and _body_rgb.png. Nothing else in
the sheet changes. Placement and scale are taken from the sheet's own first death frame (he is still standing there),
so the new fall starts exactly where the old one did.
"""
import json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..')))
import soldier_ink as ink                                    # noqa: E402
import make_weapon_sprites as mws                            # noqa: E402

CW, CH, COLS, BASE = 128, 160, 16, 192
MOD = os.path.normpath(os.path.join(HERE, '..', '..', 'mod', 'Resources', 'Units'))
src, stem = sys.argv[1], sys.argv[2]
meta = json.load(open(os.path.join(src, 'meta.json')))
clips = [c for c in ('death', 'deathb', 'deathr') if c in meta['clips']]
rgb_path, p_path = os.path.join(MOD, stem + '_body_rgb.png'), os.path.join(MOD, stem + '_body.png')
sheet = Image.open(rgb_path).convert('RGBA')
if sheet.height // CH * COLS < 896:
    sys.exit('%s is not a walk16 sheet' % stem)


def render_dir(d):
    return ((d + 1) % 8) + 1


def cell(n):
    return sheet.crop(((n % COLS) * CW, (n // COLS) * CH, (n % COLS) * CW + CW, (n // COLS) * CH + CH))


def bbox(im):
    a = np.asarray(im)[..., 3] > 40
    ys, xs = np.nonzero(a)
    return (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None


def inked(clip, kdir, f):
    p = f'{src}/{clip}/d{kdir}_f{f:02d}'
    return ink.ink_frame(Image.open(p + '_beauty.png').convert('RGBA'), Image.open(p + '_id.png'))


report, chosen = [], {}
for d in range(8):
    kdir = render_dir(d)
    old0 = bbox(cell(BASE + d * 8))                       # the old fall's first frame: standing
    best = None
    for clip in clips:
        frames = [inked(clip, kdir, f) for f in range(8)]
        b0 = bbox(frames[0])
        s = (old0[3] - old0[1]) / max(1, b0[3] - b0[1])   # same height as the sheet's own standing frame
        bigs = [fr.resize((round(fr.width * s), round(fr.height * s)), Image.LANCZOS) for fr in frames]
        nb0 = bbox(bigs[0])
        ox = round((old0[0] + old0[2]) / 2 - (nb0[0] + nb0[2]) / 2)
        oy = old0[3] - nb0[3]
        # what runs off: bottom rows past the cell, the sides past the cell (sides can be moved back in, as assemble does)
        boxes = [bbox(b) for b in bigs[4:]]
        below = max(0, max(bx[3] + oy for bx in boxes) - (CH - 1))
        lo = min(bx[0] for bx in [bbox(b) for b in bigs]) + ox
        hi = max(bx[2] for bx in [bbox(b) for b in bigs]) + ox
        wide = max(0, (hi - lo) - (CW - 3))
        score = below * 10 + wide
        if best is None or score < best[0]:
            best = (score, clip, bigs, ox, oy, lo, hi, below, wide)
    score, clip, bigs, ox, oy, lo, hi, below, wide = best
    dx = 0
    if hi - lo > CW - 3: dx = round((CW - 1 - hi - lo) / 2)
    elif lo < 1: dx = 1 - lo
    elif hi > CW - 2: dx = CW - 2 - hi
    ox += dx
    chosen[d] = clip
    report.append('facing %d: %s%s%s' % (d, clip, ', %d px still below' % below if below else '', ', %d px too wide' % wide if wide else ''))
    for f, big in enumerate(bigs):
        # what still runs off the bottom is eased up over the fall (none at the first frame, all of it by the last),
        # so he does not hop at the start and the body lies whole
        bx = bbox(big)
        need = max(0, bx[3] + oy - (CH - 1)) if bx else 0
        fy = oy - min(need, round(below * f / 7)) if below else oy
        fy = min(fy, oy - need) if need and f >= 4 else fy
        c = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
        c.alpha_composite(big, (max(0, ox), max(0, fy)), (max(0, -ox), max(0, -fy)))
        n = BASE + d * 8 + f
        sheet.paste(c, ((n % COLS) * CW, (n // COLS) * CH))

# the 8-bit sheet: quantise only the death rows, paste them over the existing ones
pal, legal, lp = mws.palette_and_legal()
pimg = Image.open(p_path)
a = np.asarray(sheet).copy()
a[..., 3] = np.where(a[..., 3] > 100, 255, 0)
pa = np.asarray(pimg).copy()
for row in range(BASE // COLS, (BASE + 64) // COLS):
    y0 = row * CH
    q = np.asarray(mws.quantise(Image.fromarray(a[y0:y0 + CH], 'RGBA'), pal, legal, lp))
    pa[y0:y0 + CH] = q
out = Image.fromarray(pa, 'P'); out.putpalette(pimg.getpalette())
sheet.save(rgb_path)
out.save(p_path)
print(stem, '\n  ' + '\n  '.join(report))
