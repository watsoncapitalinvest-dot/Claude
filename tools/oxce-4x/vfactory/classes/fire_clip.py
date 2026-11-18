# Firing clip for John: a turret missile vehicle (hull + turret layers as the game draws them), the hull still and the turret turning
# to aim (headings list: first = hull), every tube firing in turn (pods alternate), each one leaving the turret (turret store states), the package's own full-size missile flying from each tube's nose with the launch smoke at its tail.
# Tube noses: model points projected with the battle camera (30 deg, ppu 90.51 x scale), offset from the turret's 'rack' muzzle.
# usage: python3 fire_clip.py pkg_dir scale "x,y,z;x,y,z;..." out.gif [headings]
import sys, json, math
from PIL import Image, ImageDraw, ImageChops
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
HULL = HDS[0]                                                        # the hull stays put; the turret turns to aim (engine turretType 0)
fr = next(x for x in m['frames'] if x['look'] == 'clean' and x['heading'] == HULL and x.get('state', 'm0') == 'm0')
body = Image.open(f'{P}/{fr["file"]}').convert('RGBA'); off = fr['turret_paste_offset']
ox, oy = 360, 400; per = -(-len(T) // len(HDS)); fired = 0; live = []
ST = m.get('turret_store_states')
def turret_img(td, k):                                               # k missiles gone (turret store states), loaded when there are none
    tr = next(x for x in m['turret'] if x['look'] == 'clean' and x['heading'] == td)
    f = f"turret/{m['asset']}_turret_clean_s{k}_{td}.png" if (k and ST) else tr['file']
    return Image.open(f'{P}/{f}').convert('RGBA'), tr
for si, hd in enumerate(HDS):
    steps = [hd] if si == 0 else [H8[(H8.index(HDS[si - 1]) + j) % 8] for j in range(1, (H8.index(hd) - H8.index(HDS[si - 1])) % 8 + 1)]
    for st in steps:                                                 # turning: a few frames per eighth of a turn
        for _ in range(4 if si else 2):
            tur, tr = turret_img(st, fired); pv = tr['pivot']; tpx, tpy = ox + off[0] - pv[0], oy + off[1] - pv[1]
            c = ground(); c.alpha_composite(body, (ox - AX, oy - AY)); c.alpha_composite(tur, (tpx, tpy))
            frames.append(c.convert('RGB').resize((W * 3 // 4, H * 3 // 4), Image.LANCZOS))
    mf = m['missile_full']['by_heading'][hd]; ms = Image.open(f'{P}/{mf["file"]}').convert('RGBA'); nx, ny = mf['nose_px']; tx, ty = mf['tail_px']
    dx, dy = mf['flight_dir_screen']; L = math.hypot(dx, dy); dx, dy = dx / L, dy / L
    fxs = sorted(fx.get(hd, []), key=lambda x: x['frame'])
    tr0 = next(x for x in m['turret'] if x['look'] == 'clean' and x['heading'] == hd); pv = tr0['pivot']; tpx, tpy = ox + off[0] - pv[0], oy + off[1] - pv[1]
    mz = tr0['muzzles']['rack']['xy']; m0 = (tpx + mz[0], tpy + mz[1]); s0 = scr(T[0], hd)
    noses = [(m0[0] + scr(t, hd)[0] - s0[0], m0[1] + scr(t, hd)[1] - s0[1]) for t in T]
    live = []; burst = list(range(fired, min(len(T), fired + per)))
    for n in range(len(burst) * 3 + 20):
        if n % 3 == 0 and n // 3 < len(burst): k = burst[n // 3]; live.append([noses[k][0], noses[k][1], 0, False]); fired = k + 1
        tur, _ = turret_img(hd, fired)
        c = ground(); c.alpha_composite(body, (ox - AX, oy - AY))
        under, over = [], []                                         # a missile still inside the pods is drawn under the turret,
        for s in live:                                               # and over it once it has flown clear (John 20:21)
            x, y, age, clear = s; px, py = int(x - nx), int(y - ny)
            if not clear:
                lay = Image.new('L', (W, H), 0); lay.paste(ms.getchannel('A'), (px, py))
                tl = Image.new('L', (W, H), 0); tl.paste(tur.getchannel('A'), (tpx, tpy))
                ov = sum(ImageChops.multiply(lay, tl).point(lambda v: 255 if v > 64 else 0).histogram()[255:])
                s[3] = clear = ov < 0.03 * sum(lay.point(lambda v: 255 if v > 64 else 0).histogram()[255:])
            (over if clear else under).append(s)
        def draw(group):
            for s in group:
                x, y, age = s[0], s[1], s[2]; sx, sy = x - (nx - tx), y - (ny - ty)   # the tail, where the launch smoke sits
                if age < len(fxs):
                    g = Image.open(f'{P}/{fxs[age]["file"]}').convert('RGBA'); ga = fxs[age]['anchor']; c.alpha_composite(g, (int(sx - ga[0]), int(sy - ga[1])))
                px, py = int(x - nx), int(y - ny)
                if -100 < px < W and -100 < py < H: c.alpha_composite(ms, (px, py))
        draw(under); c.alpha_composite(tur, (tpx, tpy)); draw(over)
        for s in live: s[0] += dx * 24; s[1] += dy * 24; s[2] += 1
        frames.append(c.convert('RGB').resize((W * 3 // 4, H * 3 // 4), Image.LANCZOS))
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=70, loop=0)
print('CLIP', OUT, len(frames))
