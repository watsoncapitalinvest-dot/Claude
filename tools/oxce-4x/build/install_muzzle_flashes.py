"""Muzzle flashes (John 15 Nov 19:56 plan; "build muzzle flashes" 16 Nov 13:53).

Art is John's downloads, licence unknown: PRIVATE. The sheets this writes are gitignored and go in the zip only.
  cartoon fire: muzzle_flashs.zip (m_1..m_16, 256x256, pointing right)
  ion (lasers, pulse): Reactorcore Art "Muzzle Effects" - Muzzle Large Ion, Muzzle Big Ion (pointing right)

Writes MUZZLE.PCK as four sheets of 192x192 frames, the flash's root at the frame centre, turned to 16 screen
directions (frame = base + variant * 16 + direction; direction k points k * 22.5 degrees clockwise from screen-right):
  0    fire, normal    (8 variants)      128  fire, heavy  (8 variants)
  256  ion, normal     (6 variants)      352  ion, heavy   (6 variants)
The engine (Map::drawMuzzle, set by ProjectileFlyBState) picks the set and direction per round.

usage: python3 build/install_muzzle_flashes.py <unzipped muzzle_flashs folder> <unzipped "RC Art - Muzzle Effects" folder>
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
FIRE_PICK = [1, 2, 3, 4, 7, 8, 9, 12]          # the eight cartoon flashes without side spikes read best small
SETS = [('fire', 'normal', 0, 64), ('fire', 'heavy', 128, 100), ('ion', 'normal', 256, 60), ('ion', 'heavy', 352, 92)]


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
    sm = crop.resize((max(1, int(crop.width * k)), max(1, int(crop.height * k))), Image.LANCZOS)
    canvas = Image.new('RGBA', (F, F), (0, 0, 0, 0))
    canvas.alpha_composite(sm, (F // 2, F // 2 - int(ry * k)))
    return canvas.rotate(-angle, resample=Image.BICUBIC, center=(F // 2, F // 2))


def main(fire_dir, rc_dir):
    pal, legal, lp = mws.palette_and_legal()
    fire = [Image.open(os.path.join(fire_dir, 'm_%d.png' % i)).convert('RGBA') for i in FIRE_PICK]
    ion = []
    for d in ('Muzzle Large Ion', 'Muzzle Big Ion'):
        p = os.path.join(rc_dir, 'Sprites', d)
        ion += [Image.open(os.path.join(p, f)).convert('RGBA') for f in sorted(os.listdir(p)) if f.endswith('.png')]
    assert len(ion) == 6, len(ion)
    lines = ['# Muzzle flashes: written by build/install_muzzle_flashes.py - edit the script, not this file.',
             '# The pictures are John\'s downloads (licence unknown): gitignored, zip only.',
             'extraSprites:']
    for kind, size, base, length in SETS:
        srcs = fire if kind == 'fire' else ion
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
    print('MUZZLE.PCK: 448 frames, %dx%d' % (F, F))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
