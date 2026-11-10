"""The painted equipment that had no sprite yet -> BIGOBS, FLOOROB and their twins.

apply_items.py repaints an item the mod had already drawn, taking the footprint off the old
sprite. These eleven have no old sprite of ours: they are still vanilla X-COM art, so the
footprint comes from the vanilla ruleset instead - invWidth/invHeight in 16px inventory slots,
and the frame numbers the item already uses. Nothing here is typed in by hand; it is read out
of items.rul, so a transcription slip cannot put a grenade on the medikit's frame.

The mapping is the one place a decision is made, and every line of it is an identity: the
picture is the thing the vanilla item already is. Where it was not - a box of sniper rounds
for a rifle that takes no ammo, binoculars for a mind probe - the item is left out and
reported, rather than reskinned into something it is not.

usage: apply_items_new.py <pack dir> <mod dir> <vanilla items.rul> [--write-rules]
"""
import sys, os, re, numpy as np
from PIL import Image

SRC, MOD, VANILLA = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = f'{MOD}/Resources/Items'
SLOT, K = 16, 4                       # inventory slot in px; sharp-twin upscale
FLOOR_W, FLOOR_H = 128, 160
FLOOR_CX, FLOOR_CY = 64, 124          # where the existing ground items sit, measured off floor_m4
FLOOR_PER_INV = 1.9                   # ground px per inventory px, same measurement

# picture -> the vanilla item it IS.  stem is what the file gets called in the mod.
MAP = [
    # ammunition
    ('a_rifle',    'STR_RIFLE_CLIP',        'rifleclip'),   # STANAG mag  -> the M4's magazine
    ('a_smg',      'STR_PISTOL_CLIP',       'smgclip'),     # stick mag   -> STR_PISTOL is the Uzi
    ('a_belt',     'STR_HC_AP_AMMO',        'belt50'),      # can + belt  -> the .50 cal is HEAVY_CANNON
    ('a_40mm_he',  'STR_AC_HE_AMMO',        'he40'),        # 40mm HE     -> the M-32 is AUTO_CANNON
    ('a_rocket',   'STR_SMALL_ROCKET',      'rocket'),      # rocket      -> the RPG-7 is ROCKET_LAUNCHER
    # explosives
    ('e_frag',     'STR_GRENADE',           'frag'),
    ('e_smoke',    'STR_SMOKE_GRENADE',     'smoke'),
    ('e_mine',     'STR_PROXIMITY_GRENADE', 'claymore'),    # claymore = a proximity mine
    ('e_charge',   'STR_HIGH_EXPLOSIVE',    'c4'),          # C4 block and detonator
    # kit
    ('k_medkit',   'STR_MEDI_KIT',          'medkit'),
    ('k_scanner',  'STR_MOTION_SCANNER',    'scanner'),
]


def vanilla():
    """frame numbers and inventory footprint, read out of the game's own ruleset"""
    src = open(VANILLA).read()
    out = {}
    for p in re.split(r'\n  - type: ', src)[1:]:
        name = p.split('\n')[0].strip()
        def g(k, d=None):
            m = re.search(r'\n    %s: (\S+)' % k, p)
            return m.group(1) if m else d
        out[name] = dict(big=g('bigSprite'), floor=g('floorSprite'),
                         w=int(g('invWidth', '1')), h=int(g('invHeight', '1')))
    return out


def cut(path):
    """lift the painting off its magenta, un-fringing the edge it bled into"""
    a = np.array(Image.open(path).convert('RGB')).astype(np.float32)
    m = np.minimum(a[..., 0], a[..., 2]) - a[..., 1]
    al = np.clip((150 - m) / 90, 0, 1)
    M = np.array([255, 0, 255], np.float32)
    rgb = np.clip((a - (1 - al[..., None]) * M) / np.maximum(al[..., None], 0.05), 0, 255)
    pink = (np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1]) > 15
    rgb[..., 0] = np.where(pink, np.minimum(rgb[..., 0], rgb[..., 1] + 12), rgb[..., 0])
    rgb[..., 2] = np.where(pink, np.minimum(rgb[..., 2], rgb[..., 1] + 22), rgb[..., 2])
    im = Image.fromarray(np.dstack([rgb, al * 255]).astype(np.uint8), 'RGBA')
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def orient(im, bw, bh):
    """A round lies on its side in a 2x1 belt pouch. Everything in the pack is painted upright,
    so a portrait picture going into a landscape box is turned rather than shrunk to a sliver.

    A square box is not a landscape one. Comparing the two aspects without saying so first laid
    every 1x1 grenade on its side in a cell that would have taken it standing up."""
    if bw == bh:
        return im
    if (im.width < im.height) != (bw < bh):
        return im.rotate(90, expand=True)
    return im


def fit(im, bw, bh):
    k = min(bw / im.width, bh / im.height)
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


def quant(rgba, ref):
    """8-bit in the reference sprite's palette; index 0 stays transparent.

    Matched on the redmean weighting rather than plain RGB distance, the same one the kit
    checker uses. Straight RGB treats a green error as costing what a red one costs, and olive
    drab sits close enough to the palette's browns that every grenade and rocket came out
    sepia. Weighting green four times keeps them olive."""
    pal = Image.open(ref).convert('P').getpalette()[:768]
    p = np.array(pal, np.int16).reshape(-1, 3)[:256].astype(np.float32)[1:]   # never pick index 0
    a = np.array(rgba)
    c = a[..., :3].astype(np.float32)[:, :, None, :]
    rbar = (c[..., 0] + p[None, None, :, 0]) * 0.5
    dr, dg, db = c[..., 0] - p[None, None, :, 0], c[..., 1] - p[None, None, :, 1], c[..., 2] - p[None, None, :, 2]
    d = (2 + rbar / 256) * dr ** 2 + 4 * dg ** 2 + (2 + (255 - rbar) / 256) * db ** 2
    idx = (d.argmin(-1) + 1).astype(np.uint8)
    idx[a[..., 3] < 128] = 0
    out = Image.fromarray(idx, 'P'); out.putpalette(pal)
    return out


def iso(im):
    """a top-down item laid flat on the ground: turn it 45 degrees and foreshorten"""
    big = im.rotate(-45, Image.BICUBIC, expand=True)
    big = big.resize((big.width, max(1, big.height // 2)), Image.LANCZOS)
    bb = big.getbbox()
    return big.crop(bb) if bb else big


def centred(art, W, H, cx, cy):
    can = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    can.alpha_composite(art, (int(cx - art.width / 2), int(cy - art.height / 2)))
    return can


V = vanilla()
PAL_BIG, PAL_FLOOR = f'{OUT}/big_m4.png', f'{OUT}/floor_m4.png'
rules, done, skipped = [], [], []

for art, item, stem in MAP:
    src = f'{SRC}/{art}.png'
    if not os.path.exists(src) or item not in V:
        skipped.append((art, item, 'no picture' if not os.path.exists(src) else 'not a vanilla item'))
        continue
    v = V[item]
    bw, bh = v['w'] * SLOT, v['h'] * SLOT
    pic = orient(cut(src), bw, bh)

    # --- inventory icon, in the slots the item already occupies (top-left of the 32x48 frame)
    f = fit(pic, bw, bh)
    can = centred(f, 32, 48, bw / 2, bh / 2)
    quant(can, PAL_BIG).save(f'{OUT}/big_{stem}.png')
    # its sharp twin at 4x, which is what the inventory actually draws
    fh = fit(pic, bw * K, bh * K)
    centred(fh, 32 * K, 48 * K, bw * K / 2, bh * K / 2).save(f'{OUT}/big_{stem}_hi.png')

    # --- the ground sprite, at the same world scale the painted rifles already use
    long_px = max(v['w'], v['h']) * SLOT * FLOOR_PER_INV
    g = iso(pic)
    g = fit(g, long_px, long_px)
    gcan = centred(g, FLOOR_W, FLOOR_H, FLOOR_CX, FLOOR_CY)
    quant(gcan, PAL_FLOOR).save(f'{OUT}/floor_{stem}.png')
    gcan.save(f'{OUT}/floor_{stem}_rgb.png')          # full colour against full-colour ground

    rules.append((stem, v['big'], v['floor']))
    done.append('%-14s %-24s big=%-3s floor=%-3s  %dx%d slots' % (art, item, v['big'], v['floor'], v['w'], v['h']))

print('wired %d items' % len(done))
for d in done: print('   ', d)
for a, i, why in skipped: print('    SKIPPED', a, i, '-', why)

if '--write-rules' in sys.argv:
    block = ['extraSprites:']
    for stem, big, floor in rules:
        block += ['  - type: BIGOBS.PCK', '    width: 32', '    height: 48', '    files:',
                  '      %s: Resources/Items/big_%s.png' % (big, stem),
                  '  - type: FLOOROB.PCK', '    width: %d' % FLOOR_W, '    height: %d' % FLOOR_H,
                  '    files:', '      %s: Resources/Items/floor_%s.png' % (floor, stem)]
    p = f'{MOD}/Ruleset/gijoe_items_new.rul'
    open(p, 'w').write('\n'.join(block) + '\n')
    print('\nwrote', p)
