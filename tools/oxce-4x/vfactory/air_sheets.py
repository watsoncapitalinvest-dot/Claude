"""Air-fight unit sheets from the real air/sea packages (BUILD-1's spec, NOTE_FOR_VFACTORY_AirFightJets 18 Nov 01:25; John 01:09
"bigger size like we did with seabattle", 01:12 "big, as packaged"). drawingRoutine 23 whole-body sheets, one picture per frame:
  cell = N*128 x N*160 at 4x, the picture's anchor (model origin on the ground) over the middle of the N x N footprint
  N >= 3: 4 cells a row; frames 0-7 the engine directions (package headings N..NW), 8-15 one death sequence
  N == 2: 8 cells a row; 0-7 headings, 8 + heading * 8 + f the death per heading
Death (8 frames): the damaged look, hit flash, fire and smoke, the jet dropping and darkening out of the picture.
Writes <mod>/Resources/VehiclesPrivate/air_<name>_body.png (game palette) + _rgb.png: gitignored. NOT Resources/Units (public).
python3 air_sheets.py <packages dir> <mod dir> name=package[:state[:sea]] [...]   (":sea" = sinks instead of falling)"""
import json, os, sys
import numpy as np
from PIL import Image, ImageEnhance
PKG, MOD = sys.argv[1:3]; JOBS = [a.split('=') for a in sys.argv[3:]]
HEAD = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
PAL = Image.open(os.path.join(MOD, "Resources", "Units", "hawk_body.png")).getpalette()

def quantize(rgba):
    a = np.array(rgba).astype(np.int32); out = np.zeros(a.shape[:2], np.uint8); m = a[..., 3] > 127
    P = np.array(PAL, np.int32).reshape(-1, 3)[1:255]; f = a[..., :3][m]; idx = np.empty(len(f), np.int64)
    for i in range(0, len(f), 20000):
        idx[i:i + 20000] = ((f[i:i + 20000][:, None, :] - P[None]) ** 2).sum(-1).argmin(1) + 1
    out[m] = idx; im = Image.fromarray(out, "P"); im.putpalette(PAL); return im

def cell(pic, anchor, n, dy=0, dark=1.0, alpha=1.0):
    W, H = 128 * n, 160 * n; c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if dark != 1.0: a = pic.getchannel("A"); pic = ImageEnhance.Brightness(pic.convert("RGB")).enhance(dark).convert("RGBA"); pic.putalpha(a)
    if alpha != 1.0: a = np.array(pic); a[..., 3] = (a[..., 3] * alpha).astype(np.uint8); pic = Image.fromarray(a, "RGBA")
    x, y = W // 2 - anchor[0], 112 * n - anchor[1] + dy
    l, t = max(0, -x), max(0, -y); pic = pic.crop((l, t, min(pic.width, W - x), min(pic.height, H - y)))
    if pic.width > 0 and pic.height > 0: c.alpha_composite(pic, (x + l, y + t))
    return c

def blob(c, x, y, r, col, a):
    if a <= 0 or r <= 0: return
    R = int(r * 2.2) + 2; yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
    al = np.clip(1.25 * np.exp(-(xx ** 2 + yy ** 2) / (2 * (r * 0.75) ** 2)), 0, 1) * a * 255
    im = np.zeros((2 * R + 1, 2 * R + 1, 4), np.uint8); im[..., :3] = col; im[..., 3] = np.clip(al, 0, 255)
    c.alpha_composite(Image.fromarray(im, "RGBA"), (int(x) - R, int(y) - R))

def death(pic, anchor, n):
    """8 frames: hit flash -> burning -> falling, darkening and fading; fire and a smoke trail ride with it"""
    out = []; rng = np.random.default_rng(7)
    bb = pic.getbbox(); cx = (bb[0] + bb[2]) / 2 - anchor[0]; cy = (bb[1] + bb[3]) / 2 - anchor[1]   # body centre from the anchor
    spots = [(cx + rng.uniform(-0.25, 0.25) * (bb[2] - bb[0]), cy + rng.uniform(-0.2, 0.2) * (bb[3] - bb[1])) for _ in range(3)]
    for f in range(8):
        drop = int(f * f * 2.2 * n)
        c = cell(pic, anchor, n, dy=drop, dark=1 - f * 0.08, alpha=1 - max(0, f - 3) * 0.2)
        W = 128 * n; ox, oy = W // 2, 112 * n + drop
        if f == 0: blob(c, ox + cx, oy + cy, 9 * n, (255, 240, 200), 0.95); blob(c, ox + cx, oy + cy, 16 * n, (255, 150, 40), 0.7)
        for k, (sx, sy) in enumerate(spots):
            if f >= 1:
                for t in range(min(f, 5)):                       # smoke left behind, higher up (it stays while the jet falls)
                    blob(c, ox + sx + t * 2, oy + sy - t * (2.2 * n * (2 * f - 1) / max(1, f)) - 4, (4 + t * 2.5) * n * 0.6, (95, 90, 84), 0.5 - t * 0.08)
                blob(c, ox + sx, oy + sy, (5 + (f % 2) * 2) * n * 0.6, (255, 120, 30), 0.85 - f * 0.06)
                blob(c, ox + sx, oy + sy, 2.5 * n * 0.6, (255, 230, 150), 0.9 - f * 0.08)
        out.append(c)
    return out

def sink(pic, anchor, n):
    """8 frames for a boat (sea battles): hit flash, fire, then settling into the water - lower, darker, sea-tinted, fading, with
    smoke above and a ring of foam where it goes down"""
    out = []; bb = pic.getbbox(); cx = (bb[0] + bb[2]) / 2 - anchor[0]; cy = (bb[1] + bb[3]) / 2 - anchor[1]
    for f in range(8):
        drop = int(f * 2.5 * n); p2 = pic
        if f >= 3:                                           # the water takes it: tint toward sea blue-green
            a = np.array(pic).astype(np.float32); k = min(0.7, (f - 2) * 0.14)
            a[..., :3] = a[..., :3] * (1 - k) + np.array([34, 96, 110]) * k; p2 = Image.fromarray(a.astype(np.uint8), 'RGBA')
        c = cell(p2, anchor, n, dy=drop, dark=1 - f * 0.06, alpha=1 - max(0, f - 3) * 0.22)
        W = 128 * n; ox, oy = W // 2, 112 * n
        if f == 0: blob(c, ox + cx, oy + cy, 9 * n, (255, 240, 200), 0.95); blob(c, ox + cx, oy + cy, 16 * n, (255, 150, 40), 0.7)
        if 1 <= f <= 4: blob(c, ox + cx, oy + cy + drop, (5 + f) * n * 0.6, (255, 120, 30), 0.8 - f * 0.12)
        for t in range(min(f, 5)):
            blob(c, ox + cx + t * 3, oy + cy - 6 * n - t * 5 * n * 0.6, (4 + t * 2.5) * n * 0.6, (95, 90, 84), 0.5 - t * 0.08)
        if f >= 3:                                           # foam where it goes under
            for k in range(6):
                ang = k * 1.047 + f * 0.3; r = (6 + f * 2) * n * 0.6
                blob(c, ox + cx + np.cos(ang) * r, oy + cy + 4 * n + np.sin(ang) * r * 0.5, 2.2 * n * 0.6, (225, 238, 240), 0.7 - (f - 3) * 0.12)
        out.append(c)
    return out

for name, spec in JOBS:
    pk, st, mode = (spec.split(':') + ['m0', 'air'])[:3]
    if not st: st = 'm0'
    dies = sink if mode == 'sea' else death
    root = os.path.join(PKG, pk); man = json.load(open(os.path.join(root, 'manifest.json')))
    n = max(man['footprint']); anchor = man['anchor']; W, H = 128 * n, 160 * n
    def fr(look, h):
        e = next(x for x in man['frames'] if x['look'] == look and x['heading'] == h and x.get('state', st) == st)
        pic = Image.open(os.path.join(root, e['file'])).convert('RGBA')
        if man.get('spin'):                              # rotor blades are their own layer in the package (helicopters): one blade
            sp = next((x for x in man['spin'] if x['heading'] == h), None)   # angle, frozen - the air fight has no rotor animation
            if sp: pic.alpha_composite(Image.open(os.path.join(root, sp['file'])).convert('RGBA'))
        return pic
    clean = [fr('clean', h) for h in HEAD]
    dmg = [fr('damaged', h) for h in HEAD]
    per = 8 if n == 2 else 4
    frames = clean + (sum((dies(dmg[h], anchor, n) for h in range(8)), []) if n == 2 else dies(dmg[2], anchor, n))
    S = Image.new('RGBA', (per * W, -(-len(frames) // per) * H), (0, 0, 0, 0))
    for i, p in enumerate(frames):
        S.alpha_composite(p if p.size == (W, H) else cell(p, anchor, n), ((i % per) * W, (i // per) * H))
    D = os.path.join(MOD, 'Resources', 'VehiclesPrivate'); os.makedirs(D, exist_ok=True)   # private: renders of John's models stay out of the public repo
    S.save(os.path.join(D, f'air_{name}_body_rgb.png'))
    quantize(S).save(os.path.join(D, f'air_{name}_body.png'))
    print('AIR', name, 'N', n, 'frames', len(frames), 'sheet', S.size, 'from', pk, st)
