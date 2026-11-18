"""Muzzle flashes (John 15 Nov 19:56 plan; "build muzzle flashes" 16 Nov 13:53; 18 Nov 01:49 "we need a new muzzle flash
like i downloaded" - the fire flashes are now RC Art's pixel-art set, sized by calibre).

Art is John's downloads, licence unknown: PRIVATE. The sheets this writes are gitignored and go in the zip only.
  fire: Reactorcore Art "Muzzle Effects" - the !Fire singles (by size group) and Muzzle Big / Large / Mega Fire
  ion (lasers, pulse): the same pack's Muzzle Large Ion, Muzzle Big Ion (pointing right)

Writes MUZZLE.PCK as sheets of 192x192 frames, the flash's root at the frame centre, turned to 16 screen directions
(frame = base + variant * 16 + direction; direction k points k * 22.5 degrees clockwise from screen-right):
  0    fire, normal  (rifles, shotguns)     128  fire, heavy (heavy MGs, autocannon)
  256  ion, normal                          352  ion, heavy
  448  fire, small   (pistols, SMGs)        576  fire, cannon (57mm and up)
The engine (Map::drawMuzzle, set by ProjectileFlyBState) picks the set by the round's gjMuzzleFlash
(build/gen_tracers_by_calibre.py) and the direction per round.

usage: python3 build/install_muzzle_flashes.py <unzipped "RC Art - Muzzle Effects" folder>
"""
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_weapon_sprites as mws

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.join(HERE, '..', 'mod')
OUT = os.path.join(MOD, 'Resources', 'Effects')
F = 192
DIRS = 16
# RC Art's !Fire singles come in size groups of 2-4 near-identical frames; eight variants per set, by calibre
FIRE_PICKS = {
    'small':  ['!Fire/%d Fire.png' % i for i in (6, 7, 8, 43, 44, 45, 50, 51)],      # 15-19 px: pistols, SMGs
    'normal': ['!Fire/%d Fire.png' % i for i in (12, 13, 14, 18, 19, 20, 46, 47)],   # 23-27 px: rifles
    'heavy':  ['!Fire/%d Fire.png' % i for i in (0, 1, 2, 9, 10, 11, 26, 27)],       # 31-40 px: .50s, autocannon
    'cannon': ['Muzzle Big Fire/Muzzle Big Fire_%d.png' % i for i in (1, 2, 3)] + ['Muzzle Large Fire/%s' % f for f in ('LF1', 'LF2', 'LF3')]
              + ['Muzzle Mega Fire/%s' % f for f in ('MF1', 'MF2')],
}
# (kind, size, base, length of the flash in the 192 cell)
SETS = [('fire', 'normal', 0, 56), ('fire', 'heavy', 128, 80), ('ion', 'normal', 256, 60), ('ion', 'heavy', 352, 92),
        ('fire', 'small', 448, 36), ('fire', 'cannon', 576, 94)]


def root_and_crop(im):
    a = np.asarray(im)[..., 3]
    ys, xs = np.nonzero(a > 40)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    # the root: the flash's left end, at the height of its brightest part
    lum = np.asarray(im.convert('L')).astype(int) * (a > 40)
    cy = int(np.argmax(lum[:, x0:x0 + max(4, (x1 - x0) // 6)].sum(axis=1)))
    return im.crop((x0, y0, x1 + 1, y1 + 1)), cy - y0


def frame(src, length, angle):
    crop, ry = root_and_crop(src)
    k = length / crop.width
    # pixel art: blow it up by whole pixels first so it stays crisp, then to the exact length
    n = max(1, int(np.ceil(k)))
    crop = crop.resize((crop.width * n, crop.height * n), Image.NEAREST)
    k, ry = k / n, ry * n
    sm = crop.resize((max(1, int(crop.width * k)), max(1, int(crop.height * k))), Image.LANCZOS)
    canvas = Image.new('RGBA', (F, F), (0, 0, 0, 0))
    canvas.alpha_composite(sm, (F // 2, F // 2 - int(ry * k)))
    return canvas.rotate(-angle, resample=Image.BICUBIC, center=(F // 2, F // 2))


def rc_frames(sp, rel):
    """a single, or one cell of a 3-wide Large / Mega strip (LF1..3, MF1..3)"""
    if rel.split('/')[-1][:2] in ('LF', 'MF'):
        strip = Image.open(os.path.join(sp, 'Muzzle Large Fire.png' if 'LF' in rel else 'Muzzle Mega Fire.png')).convert('RGBA')
        h = strip.height; i = int(rel[-1]) - 1
        return strip.crop((i * h, 0, (i + 1) * h, h))
    return Image.open(os.path.join(sp, rel)).convert('RGBA')


def main(rc_dir):
    pal, legal, lp = mws.palette_and_legal()
    sp = os.path.join(rc_dir, 'Sprites')
    fire_sets = {k: [rc_frames(sp, r) for r in v] for k, v in FIRE_PICKS.items()}
    ion = []
    for d in ('Muzzle Large Ion', 'Muzzle Big Ion'):
        p = os.path.join(rc_dir, 'Sprites', d)
        ion += [Image.open(os.path.join(p, f)).convert('RGBA') for f in sorted(os.listdir(p)) if f.endswith('.png')]
    assert len(ion) == 6, len(ion)
    lines = ['# Muzzle flashes: written by build/install_muzzle_flashes.py - edit the script, not this file.',
             '# The pictures are John\'s downloads (licence unknown): gitignored, zip only.',
             'extraSprites:']
    for kind, size, base, length in SETS:
        srcs = fire_sets[size] if kind == 'fire' else ion
        sheet = Image.new('RGBA', (F * DIRS, F * len(srcs)), (0, 0, 0, 0))
        for v, s in enumerate(srcs):
            for d in range(DIRS):
                sheet.alpha_composite(frame(s, length, d * 360.0 / DIRS), (d * F, v * F))
        a = np.asarray(sheet).copy()
        a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
        name = 'muzzle_%s_%s.png' % (kind, size)
        q = Image.new('P', sheet.size, 0); q.putpalette(pal)
        for y in range(0, sheet.height, F):          # a frame at a time: the whole sheet at once runs out of memory
            for x in range(0, sheet.width, F):
                q.paste(mws.quantise(Image.fromarray(a[y:y + F, x:x + F], 'RGBA'), pal, legal, lp), (x, y))
        q.save(os.path.join(OUT, name))
        sheet.save(os.path.join(OUT, name.replace('.png', '_rgb.png')))   # HiColor's true-colour twin
        # OXCE cuts a sheet row by row: width/height are the whole sheet's, subX/subY one frame's
        lines += ['  - type: MUZZLE.PCK', '    width: %d' % sheet.width, '    height: %d' % sheet.height,
                  '    subX: %d' % F, '    subY: %d' % F, '    files:', '      %d: Resources/Effects/%s' % (base, name)]
    out = os.path.join(MOD, 'Ruleset', 'gijoe_muzzle_flashes.rul')
    open(out, 'w').write('\n'.join(lines) + '\n')
    print('MUZZLE.PCK: %d sets, %dx%d' % (len(SETS), F, F))


if __name__ == '__main__':
    main(sys.argv[1])
