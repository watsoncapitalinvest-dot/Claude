# Firing clip for John: a turret missile vehicle (hull + turret layers as the game draws them) at three headings, every tube firing
# in turn (pods alternate), the package's own full-size missile flying from each tube's nose with the launch smoke at its tail.
# Tube noses: model points projected with the battle camera (30 deg, ppu 90.51 x scale), offset from the turret's 'rack' muzzle.
# usage: python3 fire_clip.py pkg_dir scale "x,y,z;x,y,z;..." out.gif [headings]
import sys, json, math
from PIL import Image, ImageDraw
P, SC, TUBES, OUT = sys.argv[1:5]; HDS = (sys.argv[5] if len(sys.argv) > 5 else 'NE,E,SE').split(',')
SC = float(SC); K = 90.50966799187809 * SC
T = [tuple(map(float, t.split(','))) for t in TUBES.split(';')]
m = json.load(open(f'{P}/manifest.json')); AX, AY = m['anchor']; H8 = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
e = math.radians(30); d = (math.cos(e) / math.sqrt(2), math.cos(e) / math.sqrt(2), math.sin(e)); f = tuple(-x for x in d)
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a): l = math.sqrt(sum(x * x for x in a)); return tuple(x / l for x in a)
R = norm(cross(f, (0, 0, 1))); U = cross(R, f)
def scr(v, hd):                                                     # model vector -> screen pixels at heading hd (render_vehicle turns the model 180-45k)
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
    if x['weapon'] != 'impact': fx.setdefault(x['heading'], []).append(x)
frames = []
for hd in HDS:
    fr = next(x for x in m['frames'] if x['look'] == 'clean' and x['heading'] == hd and x.get('state', 'm0') == 'm0')
    body = Image.open(f'{P}/{fr["file"]}').convert('RGBA'); tr = next(x for x in m['turret'] if x['look'] == 'clean' and x['heading'] == hd)
    tur = Image.open(f'{P}/{tr["file"]}').convert('RGBA'); off = fr['turret_paste_offset']; pv = tr['pivot']
    mf = m['missile_full']['by_heading'][hd]; ms = Image.open(f'{P}/{mf["file"]}').convert('RGBA'); nx, ny = mf['nose_px']; tx, ty = mf['tail_px']
    dx, dy = mf['flight_dir_screen']; L = math.hypot(dx, dy); dx, dy = dx / L, dy / L
    fxs = sorted(fx.get(hd, []), key=lambda x: x['frame'])
    ox, oy = 360, 400; tpx, tpy = ox + off[0] - pv[0], oy + off[1] - pv[1]          # turret image top-left
    mz = tr['muzzles']['rack']['xy']; m0 = (tpx + mz[0], tpy + mz[1]); s0 = scr(T[0], hd)
    noses = [(m0[0] + scr(t, hd)[0] - s0[0], m0[1] + scr(t, hd)[1] - s0[1]) for t in T]
    order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]; live = []
    for n in range(12 * 3 + 22):
        c = ground(); c.alpha_composite(body, (ox - AX, oy - AY)); c.alpha_composite(tur, (tpx, tpy))
        if n % 3 == 0 and n // 3 < 12: k = order[n // 3]; live.append([noses[k][0], noses[k][1], 0])
        for s in live:
            x, y, age = s; sx, sy = x - (nx - tx), y - (ny - ty)                      # the tail, where the launch smoke sits
            if age < len(fxs):
                g = Image.open(f'{P}/{fxs[age]["file"]}').convert('RGBA'); ga = fxs[age]['anchor']; c.alpha_composite(g, (int(sx - ga[0]), int(sy - ga[1])))
            px, py = int(x - nx), int(y - ny)
            if -100 < px < W and -100 < py < H: c.alpha_composite(ms, (px, py))
            s[0] += dx * 24; s[1] += dy * 24; s[2] += 1
        frames.append(c.convert('RGB').resize((W * 3 // 4, H * 3 // 4), Image.LANCZOS))
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=70, loop=0)
print('CLIP', OUT, len(frames))
