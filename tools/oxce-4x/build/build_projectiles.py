"""Painted projectile heads -> the 35-frame trail sheet the engine actually wants.

The engine draws a weapon's shot as BULLET_SPRITES = 35 particles strung along the flight
path, taking frames bulletSprite*35 .. bulletSprite*35+34. Vanilla's sheet is 105x33 at
subX/subY 3: thirty-five columns by eleven rows, one row per weapon, frame 0 the head and the
rest a thinning tail. So the art is one head per weapon and the tail is generated.

Two things decide how a shot reads, and neither is the artist's job:

  LENGTH is how many of the 35 frames are non-empty. A short burst fades out by frame 8; a
  long energy bolt is still drawing at frame 30.

  FALLOFF is how fast the particles shrink and dim along that length.

The sprite is never rotated - Map.cpp blits it centred and axis-aligned whatever direction the
shot travels - so a head must be radially symmetric. This script checks that and refuses art
that is not, because the failure only shows up in seven directions out of eight and is easy to
miss in a screenshot of the eighth.

usage: build_projectiles.py <heads dir> <out.png> [--cell N]
"""
import sys, os
import numpy as np
from PIL import Image

HEADS, OUT = sys.argv[1], sys.argv[2]
CELL = int(sys.argv[sys.argv.index('--cell') + 1]) if '--cell' in sys.argv else 16
FRAMES = 35

# weapon -> (file stem, trail length in frames, how fast it fades)
# Length is the lever John asked for: "a laser a pixel or so taller but much longer" is a long
# trail, not a long sprite. These are placeholders like every other number in the mod.
WEAPONS = [
    ('rifle',    'p_rifle',    10, 1.5),
    ('smg',      'p_smg',       8, 1.8),
    ('hmg',      'p_hmg',      14, 1.3),
    ('sniper',   'p_sniper',   12, 1.9),
    ('rocket',   'p_rocket',   20, 0.9),
    ('pulse',    'p_pulse',    30, 0.7),
]


def cut(path):
    """lift the head off its magenta, the same key the rest of the pipeline uses"""
    a = np.array(Image.open(path).convert('RGB')).astype(np.float32)
    m = np.minimum(a[..., 0], a[..., 2]) - a[..., 1]
    al = np.clip((150 - m) / 90, 0, 1)
    M = np.array([255, 0, 255], np.float32)
    rgb = np.clip((a - (1 - al[..., None]) * M) / np.maximum(al[..., None], 0.05), 0, 255)
    im = Image.fromarray(np.dstack([rgb, al * 255]).astype(np.uint8), 'RGBA')
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def radial_error(im):
    """How far from radially symmetric the head is, 0 is perfect.

    Compared against its own 90-degree rotation rather than against a circle, so a head may be
    any shape it likes as long as it reads the same from every direction - which is the only
    thing the engine's lack of rotation actually requires."""
    # Padded to square, never resized to square. Resizing stretches a 48x4 streak into a solid
    # block, and a solid block looks the same rotated, so the check scored a perfect streak as
    # perfectly symmetric. Found by feeding it a streak on purpose.
    side = max(im.size)
    sq = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    sq.alpha_composite(im.convert('RGBA'), ((side - im.width) // 2, (side - im.height) // 2))
    a = np.array(sq.resize((64, 64), Image.LANCZOS)).astype(np.float32)
    b = np.rot90(a, 1, (0, 1))
    w = a[..., 3] / 255.0
    if w.sum() < 1:
        return 0.0
    diff = np.abs(a[..., :3] - b[..., :3]).mean(-1) * w
    return float(diff.sum() / max(w.sum(), 1e-6)) / 255.0


def particle(head, scale, alpha):
    """one trail particle: the head, smaller and fainter"""
    n = max(1, int(round(CELL * scale)))
    p = head.resize((n, n), Image.LANCZOS)
    a = np.array(p).astype(np.float32)
    a[..., 3] *= alpha
    cell = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    cell.alpha_composite(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA'),
                         ((CELL - n) // 2, (CELL - n) // 2))
    return cell


sheet = Image.new('RGBA', (CELL * FRAMES, CELL * len(WEAPONS)), (0, 0, 0, 0))
missing, rejected, built = [], [], []
for row, (name, stem, length, falloff) in enumerate(WEAPONS):
    path = os.path.join(HEADS, stem + '.png')
    if not os.path.exists(path):
        missing.append(stem)
        continue
    head = cut(path)
    err = radial_error(head)
    if err > 0.12:
        rejected.append('%s (asymmetry %.2f - it has a long axis, so it will point the wrong '
                        'way in 7 directions of 8)' % (stem, err))
        continue
    # square it off so the particle scales evenly
    side = max(head.size)
    sq = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    sq.alpha_composite(head, ((side - head.width) // 2, (side - head.height) // 2))

    for i in range(FRAMES):
        if i >= length:
            break                      # beyond the trail's length the frame stays empty
        t = i / max(length - 1, 1)     # 0 at the head, 1 at the tail
        scale = 1.0 - 0.72 * (t ** (1.0 / max(falloff, 0.1)))
        alpha = (1.0 - t) ** falloff
        sheet.alpha_composite(particle(sq, scale, alpha), (i * CELL, row * CELL))
    built.append('%-8s row %d  %2d frames  falloff %.1f' % (name, row, length, falloff))

for b in built:
    print('  ', b)
if missing:
    print('   MISSING, row left blank:', ' '.join(missing))
for r in rejected:
    print('   REJECTED:', r)

if built:
    sheet.save(OUT)
    print('\nwrote %s  %dx%d  (subX/subY %d, %d frames per weapon)'
          % (OUT, sheet.width, sheet.height, CELL, FRAMES))
    print('ruleset needs:  width: %d  height: %d  subX: %d  subY: %d'
          % (sheet.width, sheet.height, CELL, CELL))
else:
    print('\nnothing built')
