# Firing clip for John: a turret missile vehicle (hull + turret layers as the game draws them), the hull still and the turret turning
# to aim (headings list: first = hull), every tube firing in turn (pods alternate), each one leaving the turret (turret store states), the pod's face in front of it until clear (clip_mask.py), the package's own full-size missile flying from each tube's nose with the launch smoke at its tail.
# Tube noses: model points projected with the battle camera (30 deg, ppu 90.51 x scale), offset from the turret's 'rack' muzzle.
# usage: python3 fire_clip.py pkg_dir scale "x,y,z;x,y,z;..." out.gif [headings]
import sys, json, math
from PIL import Image, ImageDraw, ImageChops
sys.path.insert(0, __import__('os').path.dirname(__file__)); from clip_mask import occluder, draw as mdraw
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
    def veh(k):                                                      # hull + turret with k missiles gone, alone on a clip canvas
        v = Image.new('RGBA', (W, H), (0, 0, 0, 0)); v.alpha_composite(body, (ox - AX, oy - AY)); v.alpha_composite(turret_img(hd, k)[0], (tpx, tpy)); return v
    for n in range(len(burst) * 3 + 20):
        if n % 3 == 0 and n // 3 < len(burst):                       # launch: the pod's face stays in front of it until clear (clip_mask.py)
            k = burst[n // 3]; x0, y0 = noses[k]
            live.append([x0, y0, 0, occluder(veh(k), veh(k + 1), ms, (int(x0 - nx), int(y0 - ny)))]); fired = k + 1
        cur = veh(fired); c = ground(); c.alpha_composite(cur)
        for s in live:
            x, y, age, mask = s; sx, sy = x - (nx - tx), y - (ny - ty)   # the tail, where the launch smoke sits
            if age < len(fxs):
                g = Image.open(f'{P}/{fxs[age]["file"]}').convert('RGBA'); ga = fxs[age]['anchor']; c.alpha_composite(g, (int(sx - ga[0]), int(sy - ga[1])))
            px, py = int(x - nx), int(y - ny)
            if -100 < px < W and -100 < py < H: mdraw(c, ms, (px, py), mask, cur)
        for s in live: s[0] += dx * 24; s[1] += dy * 24; s[2] += 1
        frames.append(c.convert('RGB').resize((W * 3 // 4, H * 3 // 4), Image.LANCZOS))
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=70, loop=0)
print('CLIP', OUT, len(frames))
