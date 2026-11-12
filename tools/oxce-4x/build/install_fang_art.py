#!/usr/bin/env python3
"""Install the Cobra FANG pictures (art_briefs/COBRA_VEHICLES_MONTHS_1_3.txt).

    python3 build/install_fang_art.py [delivery dir] [--write]

The delivery dir defaults to art_briefs/returned/fang, where the pictures are
kept exactly as they came back; a dir given here is copied there first (with
--write). Without --write it checks and reports only.

The FANG is the vanilla STR_SMALL_SCOUT (every early Cobra contact is one).

  fang_dossier.png   -> the DOSSIERS article's whole-page picture, custom palette
                        Resources/Intel/UP_FANG.png + UP_FANG_hi.png (1920x1200)
                        gijoe_intel.rul: JOE_UP_FANG_CPAL, and the STR_SMALL_SCOUT
                        article's rect_text / rect_stats beside the craft. The
                        engine's UFO article reads image_id since 12 Nov (before
                        that it could only show the interception strip).
  fang_intercept.png -> the interception window's preview of the craft,
                        160 x 52 on PAL_GEOSCAPE, the size of vanilla previewMid
                        Resources/Cobra/fang_intercept.png + _hi.png (960x312)
                        gijoe_cobra_craft_art.rul: JOE_FANG_INTERCEPT and the
                        ufo's modSprite. DogfightState draws the twin with
                        HiUI::spriteIn.
  fang_top.png and   -> cleaned only, for the battle map that is not built yet
  the four extras       (no art-to-tileset pipeline): art_briefs/returned/fang/clean/.
                        They do not ship with the mod.

Keying is build/clean_objects.py's: every pixel either takes the nearest solid
subject colour or becomes background, so there is no pink fringe at any size.
Loose specks of under 16 px left in the background are dropped and counted.

Refuses (exit 1, nothing written) when a required picture is missing or the
wrong size, the background is not near-magenta at the border, the subject
touches the edge (cropped), the subject is too small or too large a share of
the frame, or the pink edge is a halo rather than a fringe (more than HALO
blended pixels per outline pixel). The extras are checked the
same way but only warn: they were not asked for.
"""
import os
import shutil
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import install_craft_art as craft            # noqa: E402  the dossier page is built exactly as the craft ones

ROOT = os.path.normpath(os.path.join(HERE, '..'))
MOD = os.path.join(ROOT, 'mod')
RES = os.path.join(MOD, 'Resources')
KEEP = os.path.join(ROOT, 'art_briefs', 'returned', 'fang')
CLEAN = os.path.join(KEEP, 'clean')

REQUIRED = {                     # name: (size rule, subject share of frame)
    'fang_dossier.png': ('long>=1536', (0.15, 0.75)),
    'fang_intercept.png': ((1280, 768), (0.05, 0.6)),
    'fang_top.png': ((1024, 1024), (0.05, 0.75)),
}
EXTRAS = ['fang_front.png', 'fang_rear.png', 'fang_opposite_side.png', 'fang_rear_three_quarter.png']

K_PREV = 6
PREV_W, PREV_H = 160, 52          # vanilla dogfight previewMid
PANEL = (28, 72, 116)             # the preview's blue panel, PAL_GEOSCAPE 106
GRID = (72, 104, 160)             # its grid lines, PAL_GEOSCAPE 85
SPECK = 16
HALO = 2.5


# ---------------------------------------------------------------- keying
def pinkness(rgb):
    """clean_objects.py's measure: magenta is high R, high B, low G with R ~ B."""
    p = np.clip((np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1]) / 255.0, 0, 1)
    return p * np.clip(1 - np.abs(rgb[..., 0] - rgb[..., 2]) / 80.0, 0, 1)


def key(im):
    """-> (RGBA with hard alpha, stats). Same rule as clean_objects.py."""
    a = np.asarray(im.convert('RGBA')).astype(float)
    rgb = a[..., :3].copy()
    rgb[a[..., 3] < 128] = (255, 0, 255)
    pink = pinkness(rgb)
    bg = pink > 0.55
    solid = pink < 0.15
    edge = ~bg & ~solid
    if edge.any():
        idx = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
        rgb[edge] = rgb[idx[0][edge], idx[1][edge]]
    lab, n = ndimage.label(~bg)
    specks = 0
    if n > 1:
        sizes = ndimage.sum(~bg, lab, range(1, n + 1))
        for i, sz in enumerate(sizes, 1):
            if sz < SPECK:
                bg[lab == i] = True
                specks += 1
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    rgb[bg] = 0
    out = Image.fromarray(np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), alpha]), 'RGBA')
    outline = int((~bg & ~ndimage.binary_erosion(~bg)).sum())
    return out, {'blended': int(edge.sum()), 'specks': specks, 'halo': edge.sum() / max(1, outline),
                 'share': float((~bg).mean()), 'bg_border': border_share(bg)}


def border_share(bg):
    return float(np.concatenate([bg[0], bg[-1], bg[:, 0], bg[:, -1]]).mean())


def check(path, rule, share):
    errs = []
    im = Image.open(path)
    if rule == 'long>=1536':
        if max(im.size) < 1536:
            errs.append('long side %d, wanted at least 1536' % max(im.size))
    elif rule and im.size != rule:
        errs.append('size %dx%d, wanted %dx%d' % (im.size + rule))
    art, st = key(im)
    if st['bg_border'] < 0.999:
        errs.append('border only %.1f%% background - subject cropped or background not magenta' % (100 * st['bg_border']))
    if not share[0] < st['share'] < share[1]:
        errs.append('subject covers %.0f%% of the picture' % (100 * st['share']))
    # a painter's fringe is about one pixel deep (0.6-0.75 blended px per outline
    # px on the first delivery); a glow, soft shadow or airbrushed edge is several
    if st['halo'] > HALO:
        errs.append('%.1f blended px per outline px - a glow or shadow, not a hard edge' % st['halo'])
    return errs, art, st


def crop(art):
    return art.crop(art.getchannel('A').getbbox())


def flat(art, colour=(255, 0, 255)):
    """Keyed art back on pure FF00FF, the form the other cleaned pictures are kept in."""
    bg = Image.new('RGBA', art.size, colour + (255,))
    bg.alpha_composite(art)
    return bg.convert('RGB')


# ---------------------------------------------------------------- the intercept preview
def geo_palette():
    """PAL_GEOSCAPE. earth.png is saved on it (gijoe_globe_earth.rul), index for index."""
    pal = Image.open(os.path.join(RES, 'Globe', 'earth.png')).getpalette()[:768]
    legal = np.arange(1, 256, dtype=np.uint8)
    lp = np.array([pal[int(i) * 3:int(i) * 3 + 3] for i in legal], dtype=np.int32)
    return pal, legal, lp


def preview(art):
    """160x52 + 960x312: the blue gridded panel of the vanilla previews, the FANG
    side-on in the middle. Fully opaque, so the twin covers the whole strip."""
    W, H = PREV_W * K_PREV, PREV_H * K_PREV
    hi = Image.new('RGBA', (W, H), PANEL + (255,))
    d = ImageDraw.Draw(hi)
    step = 10 * K_PREV
    for gx in range(W // 2 % step, W, step):
        d.line([(gx, 0), (gx, H)], fill=GRID + (255,), width=2)
    for gy in range(H // 2 % step, H, step):
        d.line([(0, gy), (W, gy)], fill=GRID + (255,), width=2)
    fang = craft.fit(crop(art), W - 12 * K_PREV, H - 4 * K_PREV)
    hi.alpha_composite(fang, ((W - fang.width) // 2, (H - fang.height) // 2))
    small = hi.resize((PREV_W, PREV_H), Image.LANCZOS)
    return craft.nearest(small, *geo_palette()), hi.convert('RGB')


# ---------------------------------------------------------------- main
def main(src, write):
    errors, jobs = [], {}
    for name, (rule, share) in REQUIRED.items():
        path = os.path.join(src, name)
        if not os.path.exists(path):
            errors.append('%s: missing' % name)
            print('%-30s MISSING' % name)
            continue
        errs, art, st = check(path, rule, share)
        print('%-30s %-8s %5.1f%% subject, %d blended edge px keyed, %d specks dropped'
              % (name, 'ok' if not errs else 'REFUSED', 100 * st['share'], st['blended'], st['specks']))
        for e in errs:
            print('    ' + e)
        errors += ['%s: %s' % (name, e) for e in errs]
        jobs[name] = art
    extras = {}
    for name in EXTRAS:
        path = os.path.join(src, name)
        if not os.path.exists(path):
            print('%-30s absent (extra, not needed)' % name)
            continue
        errs, art, st = check(path, None, (0.05, 0.8))
        print('%-30s %-8s %5.1f%% subject, %d blended edge px keyed, %d specks dropped'
              % (name, 'ok' if not errs else 'WARN', 100 * st['share'], st['blended'], st['specks']))
        for e in errs:
            print('    ' + e)
        extras[name] = art
    if errors:
        sys.exit('nothing written: %d problem(s)' % len(errors))

    dossier8, dossier_hi = craft.dossier(crop(jobs['fang_dossier.png']))
    prev8, prev_hi = preview(jobs['fang_intercept.png'])
    print('dossier   -> Intel/UP_FANG       %d colours + 32 kept for the page' % len(np.unique(np.asarray(dossier8))))
    print('intercept -> Cobra/fang_intercept %dx%d, %d PAL_GEOSCAPE colours, no index 0: %s'
          % (prev8.width, prev8.height, len(np.unique(np.asarray(prev8))), bool((np.asarray(prev8) > 0).all())))
    if not write:
        print('checked only (add --write)')
        return

    os.makedirs(KEEP, exist_ok=True)
    if os.path.abspath(src) != os.path.abspath(KEEP):
        for name in list(REQUIRED) + EXTRAS:
            p = os.path.join(src, name)
            if os.path.exists(p):
                shutil.copyfile(p, os.path.join(KEEP, name))
                os.chmod(os.path.join(KEEP, name), 0o644)
    os.makedirs(CLEAN, exist_ok=True)
    for name, art in [('fang_top.png', jobs['fang_top.png'])] + sorted(extras.items()):
        flat(art).save(os.path.join(CLEAN, name))
    os.makedirs(os.path.join(RES, 'Intel'), exist_ok=True)
    os.makedirs(os.path.join(RES, 'Cobra'), exist_ok=True)
    dossier8.save(os.path.join(RES, 'Intel', 'UP_FANG.png'))
    dossier_hi.save(os.path.join(RES, 'Intel', 'UP_FANG_hi.png'))
    prev8.save(os.path.join(RES, 'Cobra', 'fang_intercept.png'))
    prev_hi.save(os.path.join(RES, 'Cobra', 'fang_intercept_hi.png'))
    print('written: Intel/UP_FANG(_hi), Cobra/fang_intercept(_hi), %d cleaned to %s'
          % (1 + len(extras), os.path.relpath(CLEAN, ROOT)))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0] if args else KEEP, '--write' in sys.argv)
