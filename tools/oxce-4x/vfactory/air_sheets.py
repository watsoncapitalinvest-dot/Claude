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

WATER = np.array([30, 92, 108], np.float32)
def submerged(pic, drop, n):
    """John 18 Nov 14:37 "when they sink their color should be affected as if going under water", 14:39 his photo of colours above
    the surface, just below it and at depth: just under, reds go dark first, then greens; deep, everything turns blue-green and
    dim. So: every hull pixel within `drop` of the hull's bottom outline (the waterline - the hulls are cut there) is under water;
    each colour channel is absorbed by its own rate (red fastest, blue slowest), a blue-green water glow fills in, and the deepest
    parts fade out. The part still above the water keeps its own colour."""
    if drop <= 0: return pic
    a = np.array(pic).astype(np.float32); al = a[..., 3] > 8
    H = a.shape[0]; ys = np.arange(H)[:, None]
    bottom = np.where(al.any(0), H - 1 - np.argmax(al[::-1], 0), -1)[None, :]       # lowest hull pixel in each column
    depth = drop - (bottom - ys)                                                     # px under the water (> 0)
    under = depth > 0
    d = np.clip(depth / (10.0 * n), 0, None)[..., None]                              # depth in "metres" of the picture
    absorb = np.exp(-np.array([1.6, 0.55, 0.22], np.float32) * (0.35 + d))           # R, G, B kept; a step at the surface itself
    glow = np.array([18, 78, 104], np.float32) * (1 - np.exp(-0.9 * (0.35 + d)))     # the water's own blue-green fills in
    out = a[..., :3] * absorb + glow
    a[..., :3] = np.where(under[..., None], out, a[..., :3])
    fade = np.clip(1 - depth / (36.0 * n), 0.05, 1); fade[~under] = 1
    a[..., 3] *= fade
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')

def dived(pic, n, deep=0.0):
    """a submarine dived (John 14:41 "this is a sub, so those colours should affect it when it's submerged, and when it sinks get
    worse"): the whole hull just under the surface - only the top of the mast / periscope stays above - with the same per-channel
    absorption as submerged(); `deep` (0 = periscope depth, 1+ = going down) adds depth everywhere, so a sinking sub gets worse"""
    a = np.array(pic).astype(np.float32); al = a[..., 3] > 8
    if not al.any(): return pic
    ys = np.where(al.any(1))[0]; top, bot = ys[0], ys[-1]; hh = max(1, bot - top)
    yy = np.arange(a.shape[0])[:, None].astype(np.float32)
    cut = top + 0.10 * hh                                                           # above this line: the mast, still in the air
    d = (np.clip((yy - cut) / hh, 0, None) * 0.9 + 0.25 + deep * 1.4)[..., None]
    absorb = np.exp(-np.array([1.6, 0.55, 0.22], np.float32) * d)
    glow = np.array([18, 78, 104], np.float32) * (1 - np.exp(-0.9 * d))
    under = (yy > cut) & al
    a[..., :3] = np.where(under[..., None], a[..., :3] * absorb + glow, a[..., :3])
    fade = np.clip(0.92 - 0.25 * (yy - cut) / hh - deep * 0.45, 0.0, 1); fade = np.where(yy > cut, fade, max(0.0, 1 - deep * 1.2))
    a[..., 3] *= fade
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')

def dived_death(pic, anchor, n):
    """killed while dived: no fire under water - a dull flash, bubbles, and it goes deeper and darker until it is gone"""
    out = []; bb = pic.getbbox(); bw = bb[2] - bb[0]; W = 128 * n; ox, oy = W // 2, 112 * n
    cx = (bb[0] + bb[2]) / 2 - anchor[0]; cy = (bb[1] + bb[3]) / 2 - anchor[1]
    for f in range(8):
        c = cell(dived(pic, n, deep=f / 6.0), anchor, n, dy=int(f * 2.0 * n))
        if f <= 3:                                                                   # the hit: a pale flash seen through the water
            blob(c, ox + cx, oy + cy, bw * (0.10 + f * 0.05), (200, 235, 230), 0.55 - f * 0.12)
        for k in range(5 + f):                                                       # bubbles rising off it
            ang = k * 2.4 + f * 0.7; r = bw * (0.05 + 0.03 * (k % 4)); up = (f * 3 + k * 2) * n
            blob(c, ox + cx + np.cos(ang) * r * 3, oy + cy - up * 0.6 + np.sin(ang) * r, 1.6 * n, (220, 240, 245), 0.6 - f * 0.06)
        out.append(c)
    return out

def _foam(c, ox, oy, cx, cy, f, n, rr=6):
    for k in range(6):
        ang = k * 1.047 + f * 0.3; r = (rr + f * 2) * n * 0.6
        blob(c, ox + cx + np.cos(ang) * r, oy + cy + 4 * n + np.sin(ang) * r * 0.5, 2.2 * n * 0.6, (225, 238, 240), 0.7 - max(0, f - 3) * 0.12)

def sink2(pic, anchor, n, pts):
    """boats, John 14:37 "yes" (hits like the planes): shot down = blast on mark 1, mark 2 two frames later, then it goes under"""
    out = []; bb = pic.getbbox(); bw = bb[2] - bb[0]; W = 128 * n; ox, oy = W // 2, 112 * n
    cx = (bb[0] + bb[2]) / 2 - anchor[0]; cy = (bb[1] + bb[3]) / 2 - anchor[1]
    (x1, y1), (x2, y2) = _at(pic, anchor, pts[0]), _at(pic, anchor, pts[1] if len(pts) > 1 else pts[0])
    for f in range(8):
        drop = int(max(0, f - 2) * 3.2 * n)
        c = cell(submerged(pic, drop, n), anchor, n, dy=drop, dark=1 - max(0, f - 1) * 0.05)
        if f >= 3: _foam(c, ox, oy, cx, cy, f, n)
        if f >= 1: fx(c, FIRE[min(7, 2 + f // 2)], ox + x1, oy + y1 + drop + bw * 0.03, bw * 0.14, bottom=True)
        if f >= 3 and len(pts) > 1: fx(c, FIRE[min(7, f)], ox + x2, oy + y2 + drop + bw * 0.03, bw * 0.16, bottom=True)
        boom(c, f, ox + x1, oy + y1, pts[0][2], bw)
        if f >= 2 and len(pts) > 1: boom(c, min(7, round((f - 2) * 7 / 5)), ox + x2, oy + y2, pts[1][2], bw)
        out.append(c)
    return out

def sink_direct(pic, anchor, n, pts):
    """boats: a direct hit = one big blast on his D mark; it goes straight under"""
    out = []; bb = pic.getbbox(); bw = bb[2] - bb[0]; W = 128 * n; ox, oy = W // 2, 112 * n
    cx = (bb[0] + bb[2]) / 2 - anchor[0]; cy = (bb[1] + bb[3]) / 2 - anchor[1]
    xd, yd = _at(pic, anchor, pts[2] if len(pts) > 2 else pts[-1])
    for f in range(8):
        drop = int(f * 4.2 * n)
        c = cell(submerged(pic, drop, n), anchor, n, dy=drop, dark=1 - f * 0.05)
        if f >= 2: _foam(c, ox, oy, cx, cy, f, n)
        if f >= 1: fx(c, FIRE[min(7, 2 + f // 2)], ox + xd, oy + yd + drop + bw * 0.03, bw * 0.22, bottom=True)
        boom(c, f, ox + xd, oy + yd, 'b', bw)
        out.append(c)
    return out

def sink(pic, anchor, n):
    """8 frames, a boat sunk: the mod's big blast on the hull, then it settles into the water - lower, sea-tinted, darker, fading,
    still burning (the mod's fire frames) and leaving the mod's smoke, with a ring of foam where it goes under"""
    out = []; bb = pic.getbbox(); cx = (bb[0] + bb[2]) / 2 - anchor[0]; cy = (bb[1] + bb[3]) / 2 - anchor[1]; bw = bb[2] - bb[0]
    for f in range(8):
        drop = int(f * 2.5 * n)
        c = cell(submerged(pic, drop, n), anchor, n, dy=drop, dark=1 - f * 0.05)   # John 14:37: under-water colour, not a flat tint
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
    def fr(look, h, stopped=False):
        e = next(x for x in man['frames'] if x['look'] == look and x['heading'] == h and x.get('state', st) == st)
        pic = Image.open(os.path.join(root, e['file'])).convert('RGBA')
        if stopped and SPIN.get(h):                      # deaths: the rotor stops - one solid blade (the game's rotor layer is off)
            pic.alpha_composite(SPIN[h][0][0] if SPIN[h][0] else SPIN[h][1])
        return pic
    # John 18 Nov 11:06 "the airfight should absolutely have rotor animations", 11:14 look C3: rotors / props / fans are NOT in the body
    # frames any more; they go to their own sheet air_<name>_rotor.png that the engine draws over the body and cycles.
    SPIN = {}
    for h in HEAD:
        L = [x for x in (man.get('spin') or []) if x['heading'] == h]
        if not L: continue
        ang = [Image.open(os.path.join(root, x['file'])).convert('RGBA') for x in sorted([x for x in L if x.get('angle_deg') is not None], key=lambda x: x['angle_deg'])]
        blur = next((Image.open(os.path.join(root, x['file'])).convert('RGBA') for x in L if x.get('angle_deg') is None), None)
        SPIN[h] = (ang, blur)
    clean = [fr('clean', h) for h in HEAD]
    dmg = [fr('damaged', h, stopped=True) for h in HEAD]
    per = 8 if n == 2 else 4
    if mode == 'sub': dies = sink
    if mode in ('sea', 'sub') and name in POINTS and n >= 3:     # boats with John's marks: 8-15 shot down, 16-23 direct hit
        frames = clean + sink2(dmg[2], anchor, n, POINTS[name]) + sink_direct(dmg[2], anchor, n, POINTS[name])
    elif mode != 'sea' and name in POINTS and n >= 3:     # frames 8-15 shot down (his marks), 16-23 direct hit (big blast on mark 2)
        frames = clean + death2(dmg[2], anchor, n, POINTS[name]) + direct(dmg[2], anchor, n, POINTS[name])
    else:
        frames = clean + (sum((dies(dmg[h], anchor, n) for h in range(8)), []) if n == 2 else dies(dmg[2], anchor, n))
    if mode == 'sub':                                   # submarines: then the 8 headings DIVED, then killed while dived
        frames = frames + [cell(dived(c_pic, n), anchor, n) for c_pic in [fr('clean', h) for h in HEAD]]
        frames += sum((dived_death(dmg[h], anchor, n) for h in range(8)), []) if n == 2 else dived_death(dmg[2], anchor, n)
    # John 14:45 "yes": the GAME plays the death facing the way the craft flew. It needs the 8 DAMAGED headings (appended last) and
    # his marks in all 8 headings (vfactory/marks8/out/<name>.json, projected on the 3D model). air_<name>.json says where it all is.
    idx = {'headings': [0, 8]}
    if mode == 'sub':
        idx['dived'] = [len(frames) - (64 if n == 2 else 8) - 8, 8]; idx['dived_death'] = [len(frames) - (64 if n == 2 else 8), 64 if n == 2 else 8]
    if name in POINTS and n >= 3: idx['baked_shot_down'] = [8, 8]; idx['baked_direct_hit'] = [16, 8]
    else: idx['baked_death'] = [8, 64 if n == 2 else 8]
    idx['damaged_headings'] = [len(frames), 8]
    frames = frames + [cell(dmg[h], anchor, n) for h in range(8)]
    info = {'name': name, 'N': n, 'cell': [W, H], 'anchor_in_cell': [W // 2, 112 * n], 'per_row': per, 'frames': len(frames),
            'kind': 'sub' if mode == 'sub' else ('boat' if mode == 'sea' else 'aircraft'), 'index': idx,
            'heading_order': HEAD, 'rotor_sheet': bool(SPIN)}
    mk = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'marks8', 'out', f'{name}.json')
    if os.path.exists(mk):
        M = json.load(open(mk))
        info['marks'] = [{'which': ['first_hit', 'second_hit', 'direct_hit'][i], 'size': m['size'],
                          'per_heading': [{'dx': p[0], 'dy': p[1], 'seen': p[2]} for p in m['headings']]} for i, m in enumerate(M['marks']) if 'headings' in m]
    os.makedirs(os.path.join(MOD, 'Resources', 'VehiclesPrivate'), exist_ok=True); json.dump(info, open(os.path.join(MOD, 'Resources', 'VehiclesPrivate', f'air_{name}.json'), 'w'), indent=1)
    S = Image.new('RGBA', (per * W, -(-len(frames) // per) * H), (0, 0, 0, 0))
    for i, p in enumerate(frames):
        S.alpha_composite(p if p.size == (W, H) else cell(p, anchor, n), ((i % per) * W, (i // per) * H))
    D = os.path.join(MOD, 'Resources', 'VehiclesPrivate'); os.makedirs(D, exist_ok=True)   # private: renders of John's models stay out of the public repo
    S.save(os.path.join(D, f'air_{name}_body_rgb.png'))
    quantize(S).save(os.path.join(D, f'air_{name}_body.png'))
    print('AIR', name, 'N', n, 'frames', len(frames), 'sheet', S.size, 'from', pk, st)
    if SPIN:                                             # the rotor sheet: one row per heading (N, NE ... NW), K frames a row
        K = max(max(len(a), 1) for a, b in SPIN.values())  # each frame = the renderer's blur disc + the blade at that angle at 50%
        R = Image.new('RGBA', (K * W, 8 * H), (0, 0, 0, 0))
        for hi, h in enumerate(HEAD):
            if h not in SPIN: continue
            ang, blur = SPIN[h]
            for k in range(K):
                f = Image.new('RGBA', ang[0].size if ang else blur.size, (0, 0, 0, 0))
                if blur: f.alpha_composite(blur)
                if ang:
                    b = ang[k % len(ang)].copy(); a_ = b.getchannel('A').point(lambda v: v // 2); b.putalpha(a_); f.alpha_composite(b)
                R.alpha_composite(cell(f, anchor, n), (k * W, hi * H))
        R.save(os.path.join(D, f'air_{name}_rotor_rgb.png')); quantize(R).save(os.path.join(D, f'air_{name}_rotor.png'))
        print('ROTOR', name, K, 'frames a heading', R.size)
