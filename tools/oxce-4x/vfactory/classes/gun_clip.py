# Firing clip for John: a turret GUN vehicle as the game draws it (hull + turret layers), the hull still and the turret turning to aim,
# 3-round bursts alternating between the barrels, the package's muzzle flash, and the game's own tracer (projectiles row of the
# weapon's bulletSprite: frame 0 the head, 1-9 the trail).
# usage: python3 gun_clip.py pkg_dir scale gun_name "x,y,z;x,y,z" bullet_row projectiles_rgb.png out.gif [headings: first = hull]
import sys, json, math
from PIL import Image, ImageDraw
P, SC, GUN, BAR, ROW, PROJ, OUT = sys.argv[1:8]; HDS = (sys.argv[8] if len(sys.argv) > 8 else 'NE,E,SE').split(',')
K = 90.50966799187809 * float(SC); B = [tuple(map(float, t.split(','))) for t in BAR.split(';')]; ROW = int(ROW)
pr = Image.open(PROJ).convert('RGBA'); TR = [pr.crop((k * 48, (ROW - 11) * 48, k * 48 + 48, (ROW - 11) * 48 + 48)) for k in range(10)]
m = json.load(open(f'{P}/manifest.json')); AX, AY = m['anchor']; H8 = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
e = math.radians(30); d = (math.cos(e) / math.sqrt(2), math.cos(e) / math.sqrt(2), math.sin(e)); f = tuple(-x for x in d)
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a): l = math.sqrt(sum(x * x for x in a)); return tuple(x / l for x in a)
R = norm(cross(f, (0, 0, 1))); U = cross(R, f)
def scr(v, hd):
    a = math.radians(180 - 45 * H8.index(hd)); x, y = v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a)
    w = (x, y, v[2]); return (K * sum(p * q for p, q in zip(w, R)), -K * sum(p * q for p, q in zip(w, U)))
W, H = 1100, 640
def ground():
    g = Image.new('RGBA', (W, H), (122, 114, 86, 255)); dd = ImageDraw.Draw(g)
    for k in range(-20, 40):
        dd.line([(k * 64 - 600, 0), (k * 64 - 600 + 2 * H, H)], fill=(110, 103, 77, 255)); dd.line([(k * 64, 0), (k * 64 - 2 * H, H)], fill=(110, 103, 77, 255))
    return g
fx = {}
for x in m['fx_frames']:
    if x.get('weapon') == GUN and x.get('heading'): fx.setdefault(x['heading'], []).append(x)
HULL = HDS[0]; fr = next(x for x in m['frames'] if x['look'] == 'clean' and x['heading'] == HULL and x.get('state', 'm0') == 'm0')
body = Image.open(f'{P}/{fr["file"]}').convert('RGBA'); off = fr['turret_paste_offset']; ox, oy = 420, 380; frames = []
def tur(td):
    t = next(x for x in m['turret'] if x['look'] == 'clean' and x['heading'] == td); return Image.open(f'{P}/{t["file"]}').convert('RGBA'), t
def shot(c, td, rounds, flash):
    t_img, t = tur(td); pv = t['pivot']; tpx, tpy = ox + off[0] - pv[0], oy + off[1] - pv[1]
    c.alpha_composite(body, (ox - AX, oy - AY)); c.alpha_composite(t_img, (tpx, tpy))
    for (x, y, dx, dy, age) in rounds:                                  # tracer: head + the trail behind it
        for k in range(9, -1, -1):
            px, py = x - dx * 7 * k, y - dy * 7 * k
            if k <= age * 3: c.alpha_composite(TR[k], (int(px - 24), int(py - 24)))
    if flash:
        mx, my, st = flash; fxs = sorted(fx.get(td, []), key=lambda q: q['frame'])
        if st < len(fxs): g = Image.open(f'{P}/{fxs[st]["file"]}').convert('RGBA'); a = fxs[st]['anchor']; c.alpha_composite(g, (int(mx - a[0]), int(my - a[1])))
    return tpx, tpy, t
prev = None
for hd in HDS:
    if prev:                                                             # turn the turret an eighth at a time
        i0, i1 = H8.index(prev), H8.index(hd); step = 1 if (i1 - i0) % 8 <= 4 else -1; i = i0
        while i != i1:
            i = (i + step) % 8
            for _ in range(3): c = ground(); shot(c, H8[i], [], None); frames.append(c)
    prev = hd
    c0 = ground(); tpx, tpy, t = shot(c0, hd, [], None)
    mz = t['muzzles'][GUN]['xy']; dsx, dsy = t['muzzles'][GUN]['dir_screen']; L = math.hypot(dsx, dsy); dsx, dsy = dsx / L, dsy / L
    mid = scr(((B[0][0] + B[1][0]) / 2, (B[0][1] + B[1][1]) / 2, (B[0][2] + B[1][2]) / 2), hd)
    muz = [(tpx + mz[0] + scr(b, hd)[0] - mid[0], tpy + mz[1] + scr(b, hd)[1] - mid[1]) for b in B]
    rounds = []
    for n in range(26):
        flash = None
        if n < 12 and n % 2 == 0:                                        # 2 bursts of 3, barrels alternating
            k = (n // 2) % len(muz); rounds.append([muz[k][0], muz[k][1], dsx, dsy, 0]); flash = (muz[k][0], muz[k][1], 0)
        elif n < 12: k = ((n - 1) // 2) % len(muz); flash = (muz[k][0], muz[k][1], 1)
        c = ground(); shot(c, hd, [tuple(r) for r in rounds], flash); frames.append(c)
        for r in rounds: r[0] += r[2] * 34; r[1] += r[3] * 34; r[4] += 1
        rounds = [r for r in rounds if -60 < r[0] < W + 60 and -60 < r[1] < H + 60]
frames = [x.convert('RGB').resize((W * 3 // 4, H * 3 // 4), Image.LANCZOS) for x in frames]
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=70, loop=0); print('CLIP', OUT, len(frames))
