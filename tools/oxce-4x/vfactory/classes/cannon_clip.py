# Firing clip for John: a turret CANNON vehicle (MOBAT), hull still, turret turning to aim, one main-gun shot per heading (the
# package's muzzle flash scaled up to a tank gun, a shell streak flying out, a fireball and smoke where it lands), then a short burst from the
# turret-top machine gun if one is given (its muzzle projected from model space with the battle camera).
# The shell, the burst and the MG tracers are drawn here (the game uses its own projectile sprites); the game shows no recoil, so none here.
# usage: python3 cannon_clip.py pkg_dir scale gun_name "mx,my,mz" out.gif [headings] [mg "gx,gy,gz"]
#   mx,my,mz = the main gun muzzle in model units (the manifest's muzzle xy is that point); gx,gy,gz = the MG muzzle
import sys, json, math
from PIL import Image, ImageDraw
P, SC, GUN, MZ, OUT = sys.argv[1:6]; HDS = (sys.argv[6] if len(sys.argv) > 6 else 'NE,E,SE').split(',')
MG = tuple(map(float, sys.argv[7].split(','))) if len(sys.argv) > 7 else None
K = 90.50966799187809 * float(SC); MZ = tuple(map(float, MZ.split(',')))
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
flash = {}; imp = sorted([x for x in m['fx_frames'] if x['weapon'] == 'impact'], key=lambda q: q['frame'])
for x in m['fx_frames']:
    if x['weapon'] == GUN: flash.setdefault(x['heading'], []).append(x)
for k in flash: flash[k].sort(key=lambda q: q['frame'])
fr = next(x for x in m['frames'] if x['look'] == 'clean' and x['heading'] == HDS[0] and x.get('state', 'm0') == 'm0')
body = Image.open(f'{P}/{fr["file"]}').convert('RGBA'); off = fr['turret_paste_offset']; ox, oy = 330, 420; frames = []
def tur(td): t = next(x for x in m['turret'] if x['look'] == 'clean' and x['heading'] == td); return Image.open(f'{P}/{t["file"]}').convert('RGBA'), t
def base(td):
    c = ground(); ti, t = tur(td); pv = t['pivot']; tp = (ox + off[0] - pv[0], oy + off[1] - pv[1])
    c.alpha_composite(body, (ox - AX, oy - AY)); c.alpha_composite(ti, tp); return c, t, tp
def fx(c, img, a, x, y, sc=1.0):
    g = Image.open(f'{P}/{img}').convert('RGBA')
    if sc != 1.0: g = g.resize((int(g.width * sc), int(g.height * sc)), Image.LANCZOS); a = (a[0] * sc, a[1] * sc)
    c.alpha_composite(g, (int(x - a[0]), int(y - a[1])))
def boom(c, x, y, k):                                                   # a cannon-sized burst: fireball, then smoke (the game uses its own explosion)
    o = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(o); r = 10 + 7 * k
    if k < 5: dr.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=(255, 170 - 20 * k, 60, 230 - 30 * k)); dr.ellipse((x - r * 0.5, y - r * 0.4, x + r * 0.5, y + r * 0.3), fill=(255, 240, 180, 230 - 40 * k))
    for j in range(3):
        rr = r * (0.6 + 0.2 * j); cy = y - 6 * k - 8 * j
        dr.ellipse((x - rr + 9 * (j - 1), cy - rr * 0.6, x + rr + 9 * (j - 1), cy + rr * 0.6), fill=(70, 66, 60, max(0, 170 - 14 * k)))
    c.alpha_composite(o)
def out(c): frames.append(c.convert('RGB').resize((W * 3 // 4, H * 3 // 4), Image.LANCZOS))
prev = None
for hd in HDS:
    if prev:
        i0, i1 = H8.index(prev), H8.index(hd); st = 1 if (i1 - i0) % 8 <= 4 else -1; i = i0
        while i != i1:
            i = (i + st) % 8
            for _ in range(3): out(base(H8[i])[0])
    prev = hd
    for _ in range(4): out(base(hd)[0])
    c, t, tp = base(hd); mz = t['muzzles'][GUN]; mx, my = tp[0] + mz['xy'][0], tp[1] + mz['xy'][1]
    dx, dy = mz['dir_screen']; L = math.hypot(dx, dy); dx, dy = dx / L, dy / L
    fl = flash.get(hd, []); dist = 300                                  # the shell lands 300 px out
    for n in range(22):                                                 # main gun: flash, shell, impact
        c, _, _ = base(hd); dr = ImageDraw.Draw(c)
        if n < len(fl): fx(c, fl[n]['file'], fl[n]['anchor'], mx + dx * 8, my + dy * 8, 3.0)   # the package flash, scaled to a tank gun
        s = 40 * n
        if s < dist:
            x0, y0, x1, y1 = mx + dx * max(0, s - 36), my + dy * max(0, s - 36), mx + dx * s, my + dy * s
            dr.line([(x0, y0), (x1, y1)], fill=(255, 214, 120, 255), width=3); dr.ellipse((x1 - 3, y1 - 3, x1 + 3, y1 + 3), fill=(255, 250, 220, 255))
        else:
            boom(c, mx + dx * dist, my + dy * dist, (s - dist) // 40)
        out(c)
    if MG:                                                              # the commander's MG: one burst
        a, b = scr(MG, hd), scr(MZ, hd); gx, gy = mx + a[0] - b[0], my + a[1] - b[1]; rounds = []
        for n in range(16):
            c, _, _ = base(hd); dr = ImageDraw.Draw(c)
            if n < 8 and n % 2 == 0:
                rounds.append(0); dr.ellipse((gx - 5, gy - 5, gx + 5, gy + 5), fill=(255, 230, 150, 230))
            for j in range(len(rounds)):
                s = rounds[j] * 34; rounds[j] += 1
                if s < 380: dr.line([(gx + dx * s, gy + dy * s), (gx + dx * (s + 18), gy + dy * (s + 18))], fill=(255, 200, 90, 255), width=2)
            out(c)
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=70, loop=0)
print('CLIP', OUT, len(frames))
