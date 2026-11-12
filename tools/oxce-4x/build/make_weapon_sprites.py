#!/usr/bin/env python3
"""Turn ONE side-on picture of a weapon into the game's three sprites.

    python3 build/make_weapon_sprites.py <art.png> <name> [--write]

The art arrives on flat magenta (FF00FF), barrel pointing LEFT, which is what
GUN_ART_TO_GAME_SPRITES.txt asks for. From it this writes, replacing what the
item uses today:

  Resources/Items/big_<name>.png      32x48 8-bit   inventory, base resolution
  Resources/Items/big_<name>_hi.png   128x192 RGBA  inventory, sharp twin
  Resources/Items/floor_<name>.png    128x160 8-bit lying on the ground
  Resources/Items/floor_<name>_rgb.png 128x160 RGBA ground, colour twin
  Resources/Weapons/hold_<name>.png   1024x160 8-bit held, 8 facings

INVENTORY: X-COM stands a rifle UPRIGHT, muzzle up, in a 1-wide x 3-tall slot -
decoded from the original BIGOBS frame 1, whose rifle occupies x 0..15 of 32
and y 5..45 of 48. So the side-on art is turned a quarter clockwise and fitted
into the left 64 x 192 of the twin.

GROUND and HELD: fitted onto the geometry the item ALREADY has, frame by frame:
the axis, length and centre of the existing sprite's ink. That keeps the gun
exactly where the game puts it today, so new art cannot make placement worse.
(Where the game puts it today is itself wrong for these soldiers - see the
note in the commit that added this - and that is fixed in the placement, not
here.) The muzzle is the upper end in a held frame: soldiers carry the rifle
angled up across the chest, read off the original frames' magazines.

Facings where the body hides most of the gun are a few pixels of muzzle or butt
showing past the torso. Those keep their existing shape, recoloured to the new
gun - nobody can tell a twelve-pixel tip's model, and inventing the hidden pose
would be a guess.

Colours are matched to the battlescape palette using only the indices X-COM's
own weapon sprites use, by the redmean distance. Index 0 is transparent.
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, '..', 'mod'))
UNITS = '/mnt/user-data/uploads/XCom UFO Defense/XCOM/UNITS'
sys.path.insert(0, HERE)
import pck                                                  # noqa: E402


def load_art(path):
    """Key out the magenta, including the pink fringe a resample leaves behind."""
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    magentaish = ((r + b) / 2 - g > 110) & (r > 150) & (b > 150)
    alpha = np.where(magentaish, 0, 255).astype(np.uint8)
    ys, xs = np.nonzero(alpha)
    rgba = np.dstack([a.astype(np.uint8), alpha])[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return Image.fromarray(rgba, 'RGBA')


def palette_and_legal():
    pal = Image.open(os.path.join(MOD, 'Resources', 'Cobra', 'hold_pistol.png')).getpalette()
    used = set()
    for name, w, h in (('HANDOB', 32, 40), ('FLOOROB', 32, 40), ('BIGOBS', 32, 48)):
        for fr in pck.read_pck('%s/%s.PCK' % (UNITS, name), '%s/%s.TAB' % (UNITS, name), w, h):
            used |= set(np.unique(fr).tolist())
    used.discard(0)
    legal = np.array(sorted(used), dtype=np.uint8)
    lp = np.array([pal[int(i) * 3:int(i) * 3 + 3] for i in legal], dtype=np.int32)
    return pal, legal, lp


def quantise(rgba, pal, legal, lp):
    a = np.asarray(rgba).astype(np.int32)
    flat = a[..., :3].reshape(-1, 3)
    rm = (flat[:, None, 0] + lp[None, :, 0]) // 2
    d = ((512 + rm) * (flat[:, None, 0] - lp[None, :, 0]) ** 2 // 256
         + 4 * (flat[:, None, 1] - lp[None, :, 1]) ** 2
         + (767 - rm) * (flat[:, None, 2] - lp[None, :, 2]) ** 2 // 256)
    idx = legal[d.argmin(axis=1)].reshape(a.shape[:2])
    idx[a[..., 3] < 128] = 0
    im = Image.fromarray(idx.astype(np.uint8), 'P')
    im.putpalette(pal)
    return im


def ink_geometry(mask):
    ys, xs = np.nonzero(mask)
    P = np.vstack([xs, ys]).T.astype(float)
    c = P.mean(0)
    w, v = np.linalg.eigh(np.cov((P - c).T))
    ax = v[:, np.argmax(w)]
    t = (P - c) @ ax
    s = (P - c) @ np.array([-ax[1], ax[0]])
    return c, ax, t.max() - t.min() + 1, s.max() - s.min() + 1, (t.min(), t.max())


def place(art, size, centre, muzzle, length, thick=None):
    """Draw `art` (barrel left) with its muzzle along `muzzle`, `length` long."""
    W, H = art.size
    sx = length / W
    sy = (thick / H) if thick else sx
    m = np.asarray(muzzle, float); m /= np.linalg.norm(m)
    v = np.array([-m[1], m[0]])
    if v[1] < 0 or (abs(v[1]) < 1e-6 and v[0] < 0):
        v = -v                         # the gun's own "down" faces screen-down
    src = np.asarray(art).astype(np.float32)
    out = np.zeros((size[1], size[0], 4), np.float32)
    yy, xx = np.mgrid[0:size[1], 0:size[0]]
    dx, dy = xx + 0.5 - centre[0], yy + 0.5 - centre[1]
    a = dx * -m[0] + dy * -m[1]        # along the gun, muzzle -> stock
    b = dx * v[0] + dy * v[1]
    u = a / sx + W / 2.0
    w_ = b / sy + H / 2.0
    ok = (u >= 0) & (u < W - 1) & (w_ >= 0) & (w_ < H - 1)
    u0 = np.clip(u.astype(int), 0, W - 2); w0 = np.clip(w_.astype(int), 0, H - 2)
    fu = (u - u0)[..., None]; fw = (w_ - w0)[..., None]
    smp = (src[w0, u0] * (1 - fu) * (1 - fw) + src[w0, u0 + 1] * fu * (1 - fw)
           + src[w0 + 1, u0] * (1 - fu) * fw + src[w0 + 1, u0 + 1] * fu * fw)
    out[ok] = smp[ok]
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')
    # re-centre on the INK, not the box: the magazine hangs below the axis
    al = np.asarray(img)[..., 3]
    ys, xs = np.nonzero(al > 128)
    if len(xs):
        shift = (int(round(centre[0] - xs.mean())), int(round(centre[1] - ys.mean())))
        moved = Image.new('RGBA', size, (0, 0, 0, 0))
        moved.paste(img, shift, img)
        img = moved
    return img


def main(art_path, name, write):
    art = load_art(art_path)
    pal, legal, lp = palette_and_legal()
    print('art %dx%d after keying; %d palette entries usable' % (art.width, art.height, len(legal)))
    items = os.path.join(MOD, 'Resources', 'Items')
    weap = os.path.join(MOD, 'Resources', 'Weapons')
    out = {}

    # INVENTORY: upright, muzzle up, left 64 px of the 128 x 192 twin
    up = art.rotate(-90, expand=True, resample=Image.BICUBIC)
    k = min(60 / up.width, 184 / up.height)
    up = up.resize((max(1, int(up.width * k)), max(1, int(up.height * k))), Image.LANCZOS)
    big_hi = Image.new('RGBA', (128, 192), (0, 0, 0, 0))
    big_hi.paste(up, ((64 - up.width) // 2, (192 - up.height) // 2), up)
    out['big_hi'] = big_hi
    out['big'] = quantise(big_hi.resize((32, 48), Image.LANCZOS), pal, legal, lp)

    # GROUND: onto the existing floor sprite's line, muzzle at its right-hand end
    cur = np.asarray(Image.open(os.path.join(items, 'floor_%s.png' % name)))
    c, ax, L, T, _ = ink_geometry(cur > 0)
    muz = ax if ax[0] > 0 else -ax
    floor = place(art, (128, 160), c, muz, L, thick=art.height * L / art.width * 0.62)
    out['floor_rgb'] = floor
    out['floor'] = quantise(floor, pal, legal, lp)

    # HELD: frame by frame onto the existing strip
    strip = np.asarray(Image.open(os.path.join(weap, 'hold_%s.png' % name)))
    held = Image.new('RGBA', (1024, 160), (0, 0, 0, 0))
    tone = np.asarray(art)[..., :3][np.asarray(art)[..., 3] > 128]
    # the gun's MID and LIGHT tones: its darkest quarter made the tips vanish
    dark, mid = np.percentile(tone, 45, axis=0), np.percentile(tone, 88, axis=0)
    for d in range(8):
        fr = strip[:, d * 128:(d + 1) * 128]
        n = int((fr > 0).sum())
        if n == 0:
            continue
        c, ax, L, T, _ = ink_geometry(fr > 0)
        if L >= 40:
            muz = ax if ax[1] < 0 else -ax            # muzzle is the upper end
            g = place(art, (128, 160), c, muz, L)
            # NEVER WIDER THAN WHAT WAS THERE. The fitted gun is clipped to a
            # margin round the existing frame's ink, because where the body
            # hides the middle of a gun the old frame shows two pieces - muzzle
            # one side, butt the other - and a whole gun fitted between them
            # was drawn straight across the soldier's chest.
            from PIL import ImageFilter
            keep = Image.fromarray(((fr > 0) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(11))
            ga = np.asarray(g).copy()
            ga[..., 3] = np.minimum(ga[..., 3], np.asarray(keep))
            g = Image.fromarray(ga, 'RGBA')
            print('  frame %d: fitted, length %.0f, muzzle (%+.2f,%+.2f), clipped to the old outline'
                  % (d, L, muz[0], muz[1]))
        else:
            # a tip showing past the body: keep the shape, take the new gun's tones
            rgba = np.zeros((160, 128, 4), np.uint8)
            m = fr > 0
            lum = np.asarray(Image.fromarray(fr, 'P').convert('L')).astype(float)
            t = (lum - lum[m].min()) / max(1.0, np.ptp(lum[m])) if m.any() else lum
            for ch in range(3):
                rgba[..., ch] = np.where(m, dark[ch] + (mid[ch] - dark[ch]) * t, 0).astype(np.uint8)
            rgba[..., 3] = np.where(m, 255, 0)
            g = Image.fromarray(rgba, 'RGBA')
            print('  frame %d: body hides the gun, %d px of tip kept and recoloured' % (d, n))
        held.paste(g, (d * 128, 0), g)
    out['hold'] = quantise(held, pal, legal, lp)
    out['hold_rgba'] = held

    preview = Image.new('RGB', (1024 + 160 + 160, 200), (40, 44, 40))
    preview.paste(held, (0, 20), held)
    preview.paste(floor, (1034, 20), floor)
    bh = big_hi.resize((107, 160), Image.LANCZOS)
    preview.paste(bh, (1200, 20), bh)
    prev_path = '/tmp/weapon_preview_%s.png' % name
    preview.save(prev_path)
    print('preview %s' % prev_path)

    if write:
        out['big'].save(os.path.join(items, 'big_%s.png' % name))
        out['big_hi'].save(os.path.join(items, 'big_%s_hi.png' % name))
        out['floor'].save(os.path.join(items, 'floor_%s.png' % name))
        out['floor_rgb'].save(os.path.join(items, 'floor_%s_rgb.png' % name))
        out['hold'].save(os.path.join(weap, 'hold_%s.png' % name))
        print('written to mod/Resources/Items and Weapons')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], '--write' in sys.argv)
