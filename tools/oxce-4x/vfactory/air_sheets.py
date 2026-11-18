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
# The mod's own cartoon battle effects (ART's set, gijoe_battle_effects.rul X1.PCK; John 18 Nov 02:01 "make the explosions from the
# gi joe explosion animations"): 4 rows of 8 - 0-7 small blast, 8-15 big blast, 16-23 fire, 24-31 smoke. Each row is cut to the box
# that holds all 8 of its frames, so the animation keeps its own centre.
def _row(a):
    fr = [Image.open(os.path.join(MOD, 'Resources', 'Effects', f'x1_{i:02d}_rgb.png')).convert('RGBA') for i in range(a, a + 8)]
    bbs = [f.getbbox() for f in fr if f.getbbox()]; box = (min(b[0] for b in bbs), min(b[1] for b in bbs), max(b[2] for b in bbs), max(b[3] for b in bbs))
    return [f.crop(box) for f in fr]
BLAST, FIRE, SMOKE = _row(8), _row(16), _row(24)
BURST = _row(0)                                          # the small blast: a ball that bursts from its middle - the mid-air one
def _each(r): return [f.crop(f.getbbox()) if f.getbbox() else f for f in r]
BURST_EACH = _each(BURST); BURST_MAXW = max(f.width for f in BURST_EACH)
POINTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blast_points.json')))
SIZE = {'s': 0.16, 'r': 0.30, 'b': 0.50}                 # the drawing's widest frame, as a share of the plane's width (the click page's rings)
BLAST_W = BLAST[0].width                                  # the row's full width: every frame is scaled by the same factor
BLAST_EACH = [f.crop(f.getbbox()) if f.getbbox() else f for f in BLAST]   # each frame cut to its own drawing
def blast(c, f, x, y, w, base=False):
    """the big blast, frame f, at the row's scale (w = the whole row's width on screen). Jets: each frame's drawing centred on
    (x, y), so the flash starts in the middle of the jet and the ball grows round it (John 18 Nov 02:04 "the animation should
    start higher"). Boats (base=True): each frame stands on y, the waterline - the art is a ground blast."""
    k = w / BLAST_W; a = BLAST_EACH[f]; a = a.resize((max(1, int(a.width * k)), max(1, int(a.height * k))), Image.LANCZOS)
    c.alpha_composite(a, (int(x - a.width / 2), int(y - a.height) if base else int(y - a.height / 2)))
def fx(c, art, x, y, w, bottom=False):
    """paste effect art scaled to width w, centred on (x, y) (or standing on it, bottom=True)"""
    k = w / art.width; a = art.resize((max(1, int(art.width * k)), max(1, int(art.height * k))), Image.LANCZOS)
    c.alpha_composite(a, (int(x - a.width / 2), int(y - (a.height if bottom else a.height / 2))))

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
    l, t = max(0, -x), max(0, -y); r, b = min(pic.width, W - x), min(pic.height, H - y)
    if r > l and b > t: c.alpha_composite(pic.crop((l, t, r, b)), (x + l, y + t))   # nothing left in the cell (fallen out): empty
    return c

def blob(c, x, y, r, col, a):
    if a <= 0 or r <= 0: return
    R = int(r * 2.2) + 2; yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
    al = np.clip(1.25 * np.exp(-(xx ** 2 + yy ** 2) / (2 * (r * 0.75) ** 2)), 0, 1) * a * 255
    im = np.zeros((2 * R + 1, 2 * R + 1, 4), np.uint8); im[..., :3] = col; im[..., 3] = np.clip(al, 0, 255)
    c.alpha_composite(Image.fromarray(im, "RGBA"), (int(x) - R, int(y) - R))

def death(pic, anchor, n):
    """8 frames, a jet shot down: the mod's big blast where it was hit (it stays in the sky), the jet falling out of it faster each
    frame, darkening and fading, burning (the mod's fire frames) as it goes"""
    out = []; bb = pic.getbbox(); cx = (bb[0] + bb[2]) / 2 - anchor[0]; cy = (bb[1] + bb[3]) / 2 - anchor[1]; bw = bb[2] - bb[0]
    for f in range(8):
        drop = int(f * f * 2.2 * n)
        c = cell(pic, anchor, n, dy=drop, dark=1 - f * 0.08, alpha=1 - max(0, f - 3) * 0.2)
        W = 128 * n; ox, oy = W // 2, 112 * n
        if f >= 1: fx(c, FIRE[min(7, 2 + f // 2)], ox + cx, oy + cy + drop + bw * 0.05, bw * 0.28, bottom=True)
        blast(c, f, ox + cx, oy + cy + bw * 0.06, bw * 0.75, base=True)   # John 02:10 "still pretty low": the ball stands on the jet and rises over it
        out.append(c)
    return out

def _at(pic, anchor, pt):
    """a mark (fractions of the picture's opaque box) -> offset from the anchor"""
    bb = pic.getbbox(); return bb[0] + pt[0] * (bb[2] - bb[0]) - anchor[0], bb[1] + pt[1] * (bb[3] - bb[1]) - anchor[1]

def burst(c, f, x, y, w):
    """the small blast, frame f, its widest frame w wide, each frame centred on (x, y)"""
    k = w / BURST_MAXW; a = BURST_EACH[f]; a = a.resize((max(1, int(a.width * k)), max(1, int(a.height * k))), Image.LANCZOS)
    c.alpha_composite(a, (int(x - a.width / 2), int(y - a.height / 2)))

def boom(c, f, x, y, size, bw):
    if size == 'b': blast(c, f, x, y + bw * 0.04, bw * SIZE['b'] * BLAST_W / max(b.width for b in BLAST_EACH), base=True)
    else: burst(c, f, x, y, bw * SIZE[size])

def death2(pic, anchor, n, pts):
    """John 18 Nov 02:15-02:23: shot down = his two marks go off one after the other (mark 1, then mark 2 two frames later), at the
    sizes he chose; the plane drops out from under them burning at both"""
    out = []; bw = pic.getbbox()[2] - pic.getbbox()[0]; W = 128 * n; ox, oy = W // 2, 112 * n
    (x1, y1), (x2, y2) = _at(pic, anchor, pts[0]), _at(pic, anchor, pts[1] if len(pts) > 1 else pts[0])
    for f in range(8):
        drop = int(max(0, f - 2) ** 2 * 2.2 * n)
        c = cell(pic, anchor, n, dy=drop, dark=1 - max(0, f - 1) * 0.08, alpha=1 - max(0, f - 4) * 0.22)
        if f >= 1: fx(c, FIRE[min(7, 2 + f // 2)], ox + x1, oy + y1 + drop + bw * 0.03, bw * 0.14, bottom=True)
        if f >= 3 and len(pts) > 1: fx(c, FIRE[min(7, f)], ox + x2, oy + y2 + drop + bw * 0.03, bw * 0.16, bottom=True)
        boom(c, f, ox + x1, oy + y1, pts[0][2], bw)
        if f >= 2 and len(pts) > 1: boom(c, min(7, round((f - 2) * 7 / 5)), ox + x2, oy + y2, pts[1][2], bw)
        out.append(c)
    return out

def direct(pic, anchor, n, pts):
    """John 02:23 / 02:36: a direct (critical) hit = one big blast on his D mark (the third mark; 02:41); the plane drops out of it"""
    out = []; bw = pic.getbbox()[2] - pic.getbbox()[0]; W = 128 * n; ox, oy = W // 2, 112 * n
    x2, y2 = _at(pic, anchor, pts[2] if len(pts) > 2 else pts[-1])
    for f in range(8):
        drop = int(f * f * 2.2 * n)
        c = cell(pic, anchor, n, dy=drop, dark=1 - f * 0.1, alpha=1 - max(0, f - 3) * 0.22)
        if f >= 1: fx(c, FIRE[min(7, 2 + f // 2)], ox + x2, oy + y2 + drop + bw * 0.03, bw * 0.22, bottom=True)
        boom(c, f, ox + x2, oy + y2, 'b', bw)
        out.append(c)
    return out

def sink(pic, anchor, n):
    """8 frames, a boat sunk: the mod's big blast on the hull, then it settles into the water - lower, sea-tinted, darker, fading,
    still burning (the mod's fire frames) and leaving the mod's smoke, with a ring of foam where it goes under"""
    out = []; bb = pic.getbbox(); cx = (bb[0] + bb[2]) / 2 - anchor[0]; cy = (bb[1] + bb[3]) / 2 - anchor[1]; bw = bb[2] - bb[0]
    for f in range(8):
        drop = int(f * 2.5 * n); p2 = pic
        if f >= 3:
            a = np.array(pic).astype(np.float32); k = min(0.7, (f - 2) * 0.14)
            a[..., :3] = a[..., :3] * (1 - k) + np.array([34, 96, 110]) * k; p2 = Image.fromarray(a.astype(np.uint8), 'RGBA')
        c = cell(p2, anchor, n, dy=drop, dark=1 - f * 0.06, alpha=1 - max(0, f - 3) * 0.22)
        W = 128 * n; ox, oy = W // 2, 112 * n
        if f >= 3:                                           # foam where it goes under
            for k in range(6):
                ang = k * 1.047 + f * 0.3; r = (6 + f * 2) * n * 0.6
                blob(c, ox + cx + np.cos(ang) * r, oy + cy + 4 * n + np.sin(ang) * r * 0.5, 2.2 * n * 0.6, (225, 238, 240), 0.7 - (f - 3) * 0.12)
        if 1 <= f <= 6: fx(c, FIRE[min(7, 1 + f)], ox + cx, oy + cy + drop + bw * 0.04, bw * 0.3, bottom=True)
        blast(c, f, ox + cx, oy + bb[3] - anchor[1] - bw * 0.08, bw * 0.75, base=True)
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
    if mode != 'sea' and name in POINTS and n >= 3:     # frames 8-15 shot down (his marks), 16-23 direct hit (big blast on mark 2)
        frames = clean + death2(dmg[2], anchor, n, POINTS[name]) + direct(dmg[2], anchor, n, POINTS[name])
    else:
        frames = clean + (sum((dies(dmg[h], anchor, n) for h in range(8)), []) if n == 2 else dies(dmg[2], anchor, n))
    S = Image.new('RGBA', (per * W, -(-len(frames) // per) * H), (0, 0, 0, 0))
    for i, p in enumerate(frames):
        S.alpha_composite(p if p.size == (W, H) else cell(p, anchor, n), ((i % per) * W, (i // per) * H))
    D = os.path.join(MOD, 'Resources', 'VehiclesPrivate'); os.makedirs(D, exist_ok=True)   # private: renders of John's models stay out of the public repo
    S.save(os.path.join(D, f'air_{name}_body_rgb.png'))
    quantize(S).save(os.path.join(D, f'air_{name}_body.png'))
    print('AIR', name, 'N', n, 'frames', len(frames), 'sheet', S.size, 'from', pk, st)
