"""The battlefield's shots, drawn: one 48x48 sheet of projectile rows plus its full-colour twin.

    python3 make_projectile_sheet.py [--rocket DIR] [--missile DIR] [--preview out.png]

writes mod/Resources/Projectiles/projectiles.png      8-bit, the battlescape palette
       mod/Resources/Projectiles/projectiles_rgb.png  RGBA, the colour HiColor draws

The engine strings BULLET_SPRITES = 35 particles along the flight path, frame 0 the head and
frames 1..34 the tail, one row of 35 per bulletSprite. So a shot's LENGTH is how many of its 35
frames have anything in them, and its shape is the head. Rows here start at bulletSprite 11 (frame
385, the first frame past vanilla's eleven rows), so vanilla's own bullets are untouched.

The look is John's (12 Nov): Saturday-morning cartoon. Joe fire is BLUE, Cobra fire is RED. Round
heads are drawn procedurally - a soft glow, a flat cartoon core, an ink outline where it reads at
this size (the pulse blob and the grenade; a tracer is too small for one). Rockets and missiles
point where they fly: their row is followed by a row of eight bodies by screen direction, rendered
from a 3D model by sprites/render_projectile.py, and the item says `bulletDirectional: true`.

The 48-pixel cell is sized for the rocket: a body about 40 px long side-on at 4x, a quarter of a
man's height. Everything round sits in the middle of it.
"""
import os
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, '..', 'mod'))
OUTDIR = os.path.join(MOD, 'Resources', 'Projectiles')
CELL, FRAMES, SS = 48, 35, 4
FIRST_ROW = 11                       # bulletSprite of the first row in this sheet (frame 385)


def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


# --------------------------------------------------------------------------- drawing
yy, xx = np.mgrid[0:CELL * SS, 0:CELL * SS].astype(np.float32)
C = CELL * SS / 2.0


def disc(r, cx=0.0, cy=0.0):
    """anti-aliased disc, radius and offset in final pixels"""
    d = np.hypot(xx - (C + cx * SS), yy - (C + cy * SS)) / SS
    return np.clip(r - d + 0.5, 0, 1)


def glow(sigma, peak, cx=0.0, cy=0.0):
    d = np.hypot(xx - (C + cx * SS), yy - (C + cy * SS)) / SS
    return peak * np.exp(-0.5 * (d / sigma) ** 2)


class Layer:
    """premultiplied RGBA accumulator, painted back to front"""
    def __init__(self):
        self.rgb = np.zeros((CELL * SS, CELL * SS, 3), np.float32)
        self.a = np.zeros((CELL * SS, CELL * SS), np.float32)

    def over(self, alpha, colour):
        alpha = np.clip(alpha, 0, 1)
        self.rgb = self.rgb * (1 - alpha[..., None]) + np.array(colour, np.float32) * alpha[..., None]
        self.a = self.a * (1 - alpha) + alpha
        return self

    def image(self, fade=1.0):
        a = self.a * fade
        rgb = self.rgb / np.maximum(self.a[..., None], 1e-6)
        im = np.dstack([np.clip(rgb, 0, 255), np.clip(a * 255, 0, 255)]).astype(np.uint8)
        return Image.fromarray(im, 'RGBA').resize((CELL, CELL), Image.LANCZOS)


def blank():
    return Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))


# --------------------------------------------------------------------------- the shots
def tracer(t, heavy=False):
    """small yellow-white head, short warm tail. t = 0 head .. 1 end of tail"""
    s = (1.25 if heavy else 1.0) * (1 - 0.55 * t)
    warm = np.array([255, 205, 90]) * (1 - t) + np.array([255, 140, 40]) * t
    L = Layer().over(glow(3.2 * s, 0.75), warm)
    L.over(disc(2.4 * s), (255, 236, 170) if t > 0 else (255, 250, 225))
    if t == 0:
        L.over(disc(1.3 * s), (255, 255, 255))
    return L.image((1 - t) ** 1.1)


def laser(t, side):
    """a bolt: bright white core, coloured rim, long glow; the tail is the same bolt fading"""
    glow_c, rim_c = {'joe': ((40, 130, 255), (110, 195, 255)),
                     'cobra': ((255, 40, 30), (255, 120, 90))}[side]
    s = 1 - 0.45 * t
    L = Layer().over(glow(5.5 * s, 0.85), glow_c)
    L.over(disc(4.2 * s), rim_c)
    L.over(disc(2.5 * s), (255, 255, 255))
    return L.image((1 - t) ** 0.8)


def pulse(t, side):
    """a fat blob with a hot centre and an ink rim: shorter and chunkier than a laser"""
    body, hot, ink, halo = {'cobra': ((225, 30, 120), (255, 135, 205), (70, 0, 40), (255, 40, 150)),
                            'joe': ((30, 110, 235), (140, 205, 255), (0, 25, 70), (60, 150, 255))}[side]
    s = 1 - 0.5 * t
    r = 7.5 * s
    L = Layer().over(glow(r * 1.05, 0.6), halo)
    if t < 0.5:
        L.over(disc(r + 1.2), ink)
    L.over(disc(r), body)
    L.over(disc(r * 0.62, -0.18 * r, -0.18 * r), hot)
    L.over(disc(r * 0.28, -0.22 * r, -0.22 * r), (255, 255, 255))
    return L.image((1 - t) ** 1.0)


def ball():
    """grenade / M-32 round: a dark round ball with an ink rim and one highlight, no glow"""
    L = Layer().over(disc(6.2), (16, 16, 14))
    L.over(disc(5.0), (58, 62, 50))
    L.over(disc(3.3, 0.9, 0.9), (40, 43, 34))          # the one cel shadow tone, lower right
    L.over(disc(1.4, -1.8, -1.8), (150, 156, 135))     # highlight
    return L.image()


def flame(t):
    """exhaust right behind a rocket's tail"""
    s = 1 - 0.4 * t
    L = Layer().over(glow(4.0 * s, 0.8), (255, 120, 20))
    L.over(disc(3.0 * s), (255, 190, 60))
    L.over(disc(1.6 * s), (255, 250, 210))
    return L.image(1 - 0.5 * t)


def puff(t):
    """a cartoon smoke puff: flat pale grey, one shade tone, a soft grey line round it"""
    r = 4.0 + 7.0 * t
    L = Layer().over(disc(r + 1.0), (110, 110, 112))
    L.over(disc(r), (226, 226, 222))
    L.over(disc(r * 0.7, 0.35 * r, 0.35 * r) * disc(r), (178, 178, 176))
    return L.image(0.92 * (1 - t) ** 1.3)


def trail(frames_fn, length, start=0):
    """frames start..length-1 drawn by frames_fn(t), t from 0 at `start` to 1 at the end"""
    row = [blank() for _ in range(FRAMES)]
    for i in range(start, length):
        row[i] = frames_fn((i - start) / max(length - 1 - start, 1))
    return row


def smoke_row(head):
    row = [blank() for _ in range(FRAMES)]
    row[0] = head
    for i in range(3, 6):
        row[i] = flame((i - 3) / 2)
    for i in range(5, 26):
        p = puff((i - 5) / 20)
        if i < 6:
            q = row[i].copy(); q.alpha_composite(p); p = q
        row[i] = p
    return row


def body_row(src):
    if not src:
        return None
    out = []
    for d in range(8):
        im = Image.open(os.path.join(src, 'dir%d.png' % d)).convert('RGBA')
        c = blank()
        c.alpha_composite(im, ((CELL - im.width) // 2, (CELL - im.height) // 2))
        out.append(c)
    return out + [blank() for _ in range(FRAMES - 8)]


# --------------------------------------------------------------------------- the sheet
rocket_dirs = body_row(arg('--rocket'))
missile_dirs = body_row(arg('--missile'))
ROWS = [
    ('tracer',       trail(lambda t: tracer(t), 7)),
    ('tracer_heavy', trail(lambda t: tracer(t, True), 9)),
    ('laser_joe',    trail(lambda t: laser(t, 'joe'), 30)),
    ('laser_cobra',  trail(lambda t: laser(t, 'cobra'), 30)),
    ('pulse_cobra',  trail(lambda t: pulse(t, 'cobra'), 8)),
    ('pulse_joe',    trail(lambda t: pulse(t, 'joe'), 8)),
    ('ball',         [ball()] + [blank() for _ in range(FRAMES - 1)]),
    ('rocket',       smoke_row(rocket_dirs[2] if rocket_dirs else ball())),
    ('rocket_dirs',  rocket_dirs or [blank()] * FRAMES),
    ('missile',      smoke_row(missile_dirs[2] if missile_dirs else ball())),
    ('missile_dirs', missile_dirs or [blank()] * FRAMES),
]

rgba = Image.new('RGBA', (CELL * FRAMES, CELL * len(ROWS)), (0, 0, 0, 0))
for r, (name, frames) in enumerate(ROWS):
    for i, f in enumerate(frames):
        rgba.alpha_composite(f, (i * CELL, r * CELL))


def palette():
    pal = Image.open(os.path.join(MOD, 'Resources', 'Cobra', 'hold_pistol.png')).getpalette()
    legal = np.arange(1, 256, dtype=np.uint8)
    lp = np.array([pal[int(i) * 3:int(i) * 3 + 3] for i in legal], dtype=np.int32)
    return pal, legal, lp


def quantise(im, pal, legal, lp):
    """8-bit twin: only what is solid (alpha >= 128) gets an index. The soft glow lives in the
    _rgb twin alone and is blended there over whatever full colour is underneath."""
    a = np.asarray(im).astype(np.int32)
    flat = a[..., :3].reshape(-1, 3)
    out = np.zeros(flat.shape[0], np.uint8)
    solid = a[..., 3].reshape(-1) >= 128
    f = flat[solid]
    for k in range(0, len(f), 4096):
        ch = f[k:k + 4096]
        rm = (ch[:, None, 0] + lp[None, :, 0]) // 2
        d = ((512 + rm) * (ch[:, None, 0] - lp[None, :, 0]) ** 2 // 256 + 4 * (ch[:, None, 1] - lp[None, :, 1]) ** 2
             + (767 - rm) * (ch[:, None, 2] - lp[None, :, 2]) ** 2 // 256)
        idx = np.where(solid)[0][k:k + 4096]
        out[idx] = legal[d.argmin(axis=1)]
    p = Image.fromarray(out.reshape(a.shape[:2]), 'P')
    p.putpalette(pal)
    return p


os.makedirs(OUTDIR, exist_ok=True)
pal, legal, lp = palette()
rgba.save(os.path.join(OUTDIR, 'projectiles_rgb.png'))
quantise(rgba, pal, legal, lp).save(os.path.join(OUTDIR, 'projectiles.png'))
for r, (name, frames) in enumerate(ROWS):
    used = sum(1 for f in frames if f.getbbox())
    print('  bulletSprite %2d  %-13s %2d frames' % (FIRST_ROW + r, name, used))
print('wrote %s  %dx%d  subX/subY %d  first frame %d'
      % (os.path.join(OUTDIR, 'projectiles.png'), rgba.width, rgba.height, CELL, FIRST_ROW * FRAMES))

prev = arg('--preview')
if prev:
    bg = Image.new('RGBA', rgba.size, (70, 78, 64, 255))
    bg.alpha_composite(rgba)
    bg.resize((rgba.width, rgba.height)).save(prev)
