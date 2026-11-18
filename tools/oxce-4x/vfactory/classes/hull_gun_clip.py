# Firing clip for John: a one-layer vehicle whose guns are fixed to the hull (Cobra Ferret: twin .50 cal forward, a Com-Bat rocket on
# each foot peg). The vehicle turns to aim (no turret), the guns burst - barrels alternating, flash at each muzzle, tracers flying
# forward - and one rocket leaves its peg at each heading with smoke at its tail. Muzzles are model points projected with the battle
# camera (checked against the package's own muzzle: exact). Tracers, flashes and rockets are drawn here (the game uses its own
# projectile sprites). The pegs stay loaded in the picture: the model's rockets are not separate parts, so there are no store frames.
# usage: python3 hull_gun_clip.py pkg_dir "x,y,z;x,y,z" "x,y,z;x,y,z" out.gif [headings] [zoom]   (guns; rocket noses)
import sys, json, math
from PIL import Image, ImageDraw
P, GUNS, ROCKETS, OUT = sys.argv[1:5]; HDS = (sys.argv[5] if len(sys.argv) > 5 else 'NE,E').split(','); Z = int(sys.argv[6]) if len(sys.argv) > 6 else 2
pts = lambda s: [tuple(map(float, t.split(','))) for t in s.split(';')]
G, RK = pts(GUNS), pts(ROCKETS)
m = json.load(open(f'{P}/manifest.json')); AX, AY = m['anchor']; K = 90.50966799187809 * m['model_scale']; H8 = m['heading_order']
e = math.radians(30); d = (math.cos(e) / math.sqrt(2), math.cos(e) / math.sqrt(2), math.sin(e)); f = tuple(-x for x in d)
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a): l = math.sqrt(sum(x * x for x in a)); return tuple(x / l for x in a)
R = norm(cross(f, (0, 0, 1))); U = cross(R, f)
def scr(v, hd):
    a = math.radians(180 - 45 * H8.index(hd)); x, y = v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a)
    w = (x, y, v[2]); return (K * sum(p * q for p, q in zip(w, R)), -K * sum(p * q for p, q in zip(w, U)))
W, H = 560, 330; ox, oy = 170, 230
def ground():
    g = Image.new('RGBA', (W, H), (122, 114, 86, 255)); dd = ImageDraw.Draw(g)
    for k in range(-20, 40):
        dd.line([(k * 32 - 300, 0), (k * 32 - 300 + 2 * H, H)], fill=(110, 103, 77, 255)); dd.line([(k * 32, 0), (k * 32 - 2 * H, H)], fill=(110, 103, 77, 255))
    return g
def body(hd):
    fr = next(x for x in m['frames'] if x['look'] == 'clean' and x['heading'] == hd and x.get('state', 'm0') in ('m0', None))
    return Image.open(f'{P}/{fr["file"]}').convert('RGBA')
frames = []
def out(c): frames.append(c.convert('RGB').resize((W * Z, H * Z), Image.LANCZOS))
def base(hd): c = ground(); c.alpha_composite(body(hd), (ox - AX, oy - AY)); return c
def at(v, hd): s = scr(v, hd); return ox + s[0], oy + s[1]
for si, hd in enumerate(HDS):
    if si:                                                   # turn the whole vehicle an eighth at a time
        a, b = H8.index(HDS[si - 1]), H8.index(hd)
        for j in range(1, (b - a) % 8 + 1):
            for _ in range(3): out(base(H8[(a + j) % 8]))
    for _ in range(4): out(base(hd))
    fx, fy = scr((1, 0, 0), hd); L = math.hypot(fx, fy); dx, dy = fx / L, fy / L
    rounds = []
    for n in range(20):                                      # twin .50 cal: two bursts of three, barrels alternating
        c = base(hd); dr = ImageDraw.Draw(c)
        if n < 12 and n % 2 == 0:
            gx, gy = at(G[(n // 2) % len(G)], hd); rounds.append([gx, gy])
            dr.ellipse((gx - 4, gy - 3, gx + 4, gy + 3), fill=(255, 236, 160, 255)); dr.ellipse((gx - 2 + dx * 4, gy - 2 + dy * 4, gx + 2 + dx * 4, gy + 2 + dy * 4), fill=(255, 255, 230, 255))
        for r in rounds:
            dr.line([(r[0], r[1]), (r[0] + dx * 10, r[1] + dy * 10)], fill=(255, 205, 90, 255), width=2); r[0] += dx * 22; r[1] += dy * 22
        out(c)
    nx, ny = max((at(r, hd) for r in RK), key=lambda q: q[1]); v = 1.0; trail = []   # the near-side peg (lower on screen): drawn over the body
    for n in range(18):                                      # one Com-Bat rocket off its peg
        c = base(hd); dr = ImageDraw.Draw(c)
        for i, (tx, ty) in enumerate(trail[-8:]):
            r = 2 + (len(trail[-8:]) - i) * 0.6; dr.ellipse((tx - r, ty - r, tx + r, ty + r), fill=(150, 146, 138, 150))
        tail = (nx - dx * 9, ny - dy * 9); dr.line([tail, (nx, ny)], fill=(206, 34, 36, 255), width=3)
        px, py = -dy, dx; dr.polygon([tail, (tail[0] + px * 3 - dx * 2, tail[1] + py * 3 - dy * 2), (tail[0] - px * 3 - dx * 2, tail[1] - py * 3 - dy * 2)], fill=(206, 34, 36, 255))
        dr.ellipse((tail[0] - 2 - dx * 2, tail[1] - 2 - dy * 2, tail[0] + 2 - dx * 2, tail[1] + 2 - dy * 2), fill=(255, 200, 90, 255))
        trail.append(tail); nx += dx * v; ny += dy * v; v = min(18, v + 1.6)
        out(c)
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=70, loop=0); print('CLIP', OUT, len(frames))
