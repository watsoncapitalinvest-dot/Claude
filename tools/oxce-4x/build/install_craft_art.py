#!/usr/bin/env python3
"""Install the Tomahawk and Skystriker pictures (EARLY_CRAFT_BRIEF.txt).

    python3 build/install_craft_art.py [delivery dir] [--write] [--wings-spread]

The delivery dir defaults to mod/Resources/Craft, where the five pictures are
kept as they came back. Without --write it checks and reports only.

What goes where (STR_SKYRANGER is the Tomahawk, sprite 0; STR_INTERCEPTOR is
the Skystriker, sprite 3 - vanilla craft numbering, crafts.rul):

  top view -> BASEBITS.PCK frame sprite+33, 32 x 40, palette 1 (basescape)
              Resources/Base/craft_33.png  + craft_33_hi.png   Tomahawk
              Resources/Base/craft_36.png  + craft_36_hi.png   Skystriker
              The engine draws this frame for the craft parked in its hangar
              (BaseView.cpp, HiUI::nativeBaseView paints the _hi twin over
              it) and on the craft's equipment screen (CraftInfoState, 8-bit
              only - see the note at the end).
  dossier  -> the Intel article's own 320 x 200 picture, custom palette
              Resources/Intel/UP004.png + UP004_hi.png             Tomahawk
              Resources/Intel/UP002.png + UP002_hi.png             Skystriker
              gijoe_intel.rul already points STR_SKYRANGER / STR_INTERCEPTOR
              at JOE_UP004_CPAL / JOE_UP002_CPAL; the article's text and stats
              boxes are moved there so they sit beside the aircraft, not on it.

The Skystriker's hangar picture is the wings-back delivery: parked, a Tomcat
sweeps its wings, and in a 32-px-wide frame the swept outline is drawn larger.
--wings-spread uses the wings-out top view instead.

Refuses (exit 1, nothing written) when a picture is the wrong size, has no
magenta border, has a blended pink fringe, or a top view is not left-right
symmetric (i.e. not seen from directly above).
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, '..', 'mod'))
RES = os.path.join(MOD, 'Resources')
K_BASE = 6                       # hangar twin: 32x40 frame at 6x = 192x240
HI_W, HI_H = 1920, 1200          # dossier twin: 320x200 at 6x

TOP = {'tomahawk': 'craft_tomahawk_top.png',
       'skystriker': 'craft_skystriker_top_wings_back.png'}
TOP_SPREAD = 'craft_skystriker_top.png'
DOSSIER = {'tomahawk': 'v_joe_tomahawk.png', 'skystriker': 'v_joe_skystriker.png'}
FRAME = {'tomahawk': 33, 'skystriker': 36}          # BASEBITS sprite + 33
ARTICLE = {'tomahawk': 'UP004', 'skystriker': 'UP002'}

# Where the aircraft sits on the 320x200 article page, in base px. The buttons
# (y 5-20) and the title (5,24) take the top left; the text runs down the left
# under the title, the stats run full width along the bottom.
PIC_BOX = (124, 20, 316, 132)


# ---------------------------------------------------------------- checks
def magenta_share(a):
    return ((a[..., 0] > 245) & (a[..., 1] < 10) & (a[..., 2] > 245))


def check(path, size, top):
    errs = []
    im = Image.open(path)
    if im.size != size:
        errs.append('size %dx%d, wanted %dx%d' % (im.size + size))
        return errs, None
    a = np.asarray(im.convert('RGB')).astype(int)
    mag = magenta_share(a)
    border = np.concatenate([mag[0], mag[-1], mag[:, 0], mag[:, -1]])
    if border.mean() < 0.98:
        errs.append('border only %.0f%% magenta - subject cropped or background not FF00FF' % (100 * border.mean()))
    share = mag.mean()
    if not 0.2 < share < 0.95:
        errs.append('magenta covers %.0f%% of the picture' % (100 * share))
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    fringe = (((r + b) / 2 - g) > 120) & (abs(r - b) < 60) & ~mag
    edge = mag ^ np.asarray(Image.fromarray(mag.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(3))) .astype(bool)
    if fringe.sum() > max(50, 0.05 * edge.sum()):
        errs.append('%d blended pink pixels at the edge - edges must be hard' % fringe.sum())
    subj = ~mag
    if top:
        ys, xs = np.nonzero(subj)
        c = (xs.min() + xs.max()) / 2.0
        sh = int(round(im.width / 2.0 - c))
        m = np.roll(subj, sh, axis=1)
        iou = (m & m[:, ::-1]).sum() / float((m | m[:, ::-1]).sum())
        if iou < 0.9:
            errs.append('not symmetric left-right (%.2f) - not seen from directly above' % iou)
        h = ys.max() - ys.min() + 1
        if h < 0.5 * im.height:
            errs.append('subject only %d px tall - nose not up, or drawn too small' % h)
    return errs, im


def keyed(im):
    """Magenta out, alpha in, cropped to the subject."""
    a = np.asarray(im.convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (r + b) / 2 - g
    alpha = np.clip(255 - (m - 70) * 255 / 80, 0, 255).astype(np.uint8)
    spill = alpha < 250
    a[..., 0] = np.where(spill, np.minimum(r, g + 25), r)
    a[..., 2] = np.where(spill, np.minimum(b, g + 25), b)
    out = Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), 'RGBA')
    return out.crop(out.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox())


def fit(img, w, h):
    s = min(w / img.width, h / img.height)
    return img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)


# ---------------------------------------------------------------- palettes
def base_palette():
    """Palette 1 (basescape) out of a frame the mod already ships in it."""
    pal = Image.open(os.path.join(RES, 'Base', 'ground.png')).getpalette()[:768]
    pal += [0] * (768 - len(pal))
    n = len(Image.open(os.path.join(RES, 'Base', 'ground.png')).getpalette()) // 3
    legal = np.arange(1, min(n, 256), dtype=np.uint8)
    lp = np.array([pal[int(i) * 3:int(i) * 3 + 3] for i in legal], dtype=np.int32)
    return pal, legal, lp


def nearest(rgba, pal, legal, lp):
    a = np.asarray(rgba).astype(np.int32)
    flat = a[..., :3].reshape(-1, 3)
    rm = (flat[:, None, 0] + lp[None, :, 0]) // 2
    d = ((512 + rm) * (flat[:, None, 0] - lp[None, :, 0]) ** 2 // 256
         + 4 * (flat[:, None, 1] - lp[None, :, 1]) ** 2
         + (767 - rm) * (flat[:, None, 2] - lp[None, :, 2]) ** 2 // 256)
    idx = legal[d.argmin(axis=1)].reshape(a.shape[:2])
    idx[a[..., 3] < 128] = 0
    out = Image.fromarray(idx.astype(np.uint8), 'P')
    out.putpalette(pal)
    return out


def article_palette_tail():
    """Indices 224-255 of every Intel picture are PAL_UFOPAEDIA's own (the text,
    button and frame colours the article draws with); 1-223 are the picture's."""
    return Image.open(os.path.join(RES, 'Intel', 'UP001.png')).getpalette()[224 * 3:768]


# ---------------------------------------------------------------- builders
def hangar(top):
    """32x40 frame and its 192x240 twin, the craft fitted whole and centred."""
    W, H = 32 * K_BASE, 40 * K_BASE
    craft = fit(top, W - 2 * K_BASE, H - 2 * K_BASE)
    hi = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    hi.alpha_composite(craft, ((W - craft.width) // 2, (H - craft.height) // 2))
    small = hi.resize((32, 40), Image.LANCZOS)
    a = np.asarray(small).copy()
    a[..., 3] = np.where(a[..., 3] > 100, 255, 0)
    return nearest(Image.fromarray(a, 'RGBA'), *base_palette()), hi


def backdrop():
    """Dark briefing-room plate: a slate gradient and a faint plotting grid."""
    y = np.linspace(0, 1, HI_H)[:, None]
    top, bot = np.array([38, 48, 62]), np.array([14, 18, 24])
    g = (top[None, None, :] * (1 - y[..., None]) + bot[None, None, :] * y[..., None])
    g = np.repeat(g, HI_W, axis=1)
    x = np.linspace(-1, 1, HI_W)[None, :]
    yy = np.linspace(-1, 1, HI_H)[:, None]
    g *= (1 - 0.35 * np.clip(x ** 2 + yy ** 2 - 0.3, 0, 1))[..., None]
    im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(im)
    for gx in range(0, HI_W, 60):
        d.line([(gx, 0), (gx, HI_H)], fill=(52, 64, 78), width=1)
    for gy in range(0, HI_H, 60):
        d.line([(0, gy), (HI_W, gy)], fill=(52, 64, 78), width=1)
    return im


def dossier(v):
    k = HI_W // 320
    x0, y0, x1, y1 = [c * k for c in PIC_BOX]
    craft = fit(v, x1 - x0, y1 - y0)
    hi = backdrop().convert('RGBA')
    hi.alpha_composite(craft, (x0 + (x1 - x0 - craft.width) // 2, y0 + (y1 - y0 - craft.height) // 2))
    hi = hi.convert('RGB')
    small = hi.resize((320, 200), Image.LANCZOS)
    q = small.quantize(colors=223, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
    idx = np.asarray(q).astype(np.uint8) + 1                   # 1..223; 0 stays unused
    qp = q.getpalette()[:223 * 3]
    qp += [0] * (223 * 3 - len(qp))
    pal = [0, 0, 0] + qp + article_palette_tail()
    out = Image.fromarray(idx, 'P')
    out.putpalette(pal)
    return out, hi


# ---------------------------------------------------------------- main
def main(src, write, spread):
    top = dict(TOP)
    if spread:
        top['skystriker'] = TOP_SPREAD
    jobs, errors = [], []
    for name in ('tomahawk', 'skystriker'):
        for fn, size, is_top in ((top[name], (1024, 1024), True), (DOSSIER[name], (2048, 1280), False)):
            path = os.path.join(src, fn)
            if not os.path.exists(path):
                errors.append('%s: missing' % fn)
                continue
            errs, im = check(path, size, is_top)
            print('%-40s %s' % (fn, 'ok' if not errs else 'REFUSED'))
            for e in errs:
                print('    ' + e)
            errors += ['%s: %s' % (fn, e) for e in errs]
            jobs.append((name, is_top, im))
    if errors:
        sys.exit('nothing written: %d problem(s)' % len(errors))
    for name, is_top, im in jobs:
        art = keyed(im)
        if is_top:
            small, hi = hangar(art)
            stem = os.path.join(RES, 'Base', 'craft_%d' % FRAME[name])
            bb = Image.fromarray((np.asarray(small) > 0).astype(np.uint8) * 255).getbbox()
            print('%-11s hangar  -> craft_%d   8-bit box x %d..%d y %d..%d of 32x40'
                  % (name, FRAME[name], bb[0], bb[2] - 1, bb[1], bb[3] - 1))
        else:
            small, hi = dossier(art)
            stem = os.path.join(RES, 'Intel', ARTICLE[name])
            print('%-11s dossier -> %s     %d colours + 32 kept for the page' % (name, ARTICLE[name], len(np.unique(np.asarray(small)))))
        if write:
            small.save(stem + '.png')
            hi.save(stem + '_hi.png')
    print('written' if write else 'checked only (add --write)')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0] if args else os.path.join(RES, 'Craft'), '--write' in sys.argv, '--wings-spread' in sys.argv)
