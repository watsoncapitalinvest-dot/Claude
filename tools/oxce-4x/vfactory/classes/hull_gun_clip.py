# Firing clip for John: a one-layer vehicle whose weapons are fixed to the hull (Cobra Ferret: twin .50 cal forward, the CMF-1
# 10-round launcher along its right side, a Com-Bat rocket on each foot peg). The vehicle turns to aim (no turret). At each heading:
# a .50 cal burst (barrels alternating), a CMF-1 ripple of grenades fired flat from the end of its tube, then one Com-Bat leaves its peg - the package's own
# full-size rocket, and the vehicle picture switches to the next store state (the peg empties, as gjStoreStates shows it in the game);
# the body stays in front of the rocket until it is clear (clip_mask.py). Muzzles: model points (guns) and the package manifest's
# muzzle names (cannon, rockets) [deploy states per rocket 'dL1,dL2;dR1,dR2'], projected with the battle camera. Tracers, flashes, slugs and smoke are drawn here.
# usage: python3 hull_gun_clip.py pkg_dir "x,y,z;x,y,z" cannon_muzzle rocket1,rocket2 out.gif [headings] [zoom] [deploy]
import sys, os, json, math
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from clip_mask import occluder, draw as mdraw
P, GUNS, CAN, RKS, OUT = sys.argv[1:6]; HDS = (sys.argv[6] if len(sys.argv) > 6 else 'NE,E').split(','); Z = int(sys.argv[7]) if len(sys.argv) > 7 else 2
G = [tuple(map(float, t.split(','))) for t in GUNS.split(';')]; RK = RKS.split(',')
DEP = [g.split(',') for g in sys.argv[8].split(';')] if len(sys.argv) > 8 else []   # deploy states per rocket (John 23:28: rams push it out, then it fires)
m = json.load(open(f'{P}/manifest.json')); AX, AY = m['anchor']; K = 90.50966799187809 * m['model_scale']; H8 = m['heading_order']
STATES = [s.strip() for s in m['states_note'].split(',')]               # loaded first
FL = m['weapons'].get('missile_flight', {'start_px_per_frame': 1.5, 'accel_px_per_frame2': 1.5, 'max_px_per_frame': 26})
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
def frm(hd, st): return next(x for x in m['frames'] if x['look'] == 'clean' and x['heading'] == hd and x.get('state') == st)
def veh(hd, st): v = Image.new('RGBA', (W, H), (0, 0, 0, 0)); v.alpha_composite(Image.open(f'{P}/{frm(hd, st)["file"]}').convert('RGBA'), (ox - AX, oy - AY)); return v
frames = []; fired = 0
def out(c): frames.append(c.convert('RGB').resize((W * Z, H * Z), Image.LANCZOS))
import numpy as np
SMOKE = (196, 190, 178)
def blob(c, x, y, r, col, a):                        # a soft round blob (gaussian alpha), colour col, peak alpha a
    if a <= 0 or r <= 0: return
    R = int(r * 2.2) + 2; yy, xx = np.mgrid[-R:R + 1, -R:R + 1]; al = np.clip(1.25 * np.exp(-(xx ** 2 + yy ** 2) / (2 * (r * 0.75) ** 2)), 0, 1) * a * 255
    im = np.zeros((2 * R + 1, 2 * R + 1, 4), np.uint8); im[..., :3] = col; im[..., 3] = np.clip(al, 0, 255)
    c.alpha_composite(Image.fromarray(im, 'RGBA'), (int(x) - R, int(y) - R))
def flash(c, x, y, dx, dy, k):                      # muzzle flash: a hot core and a short tongue along the shot
    for t, r, col in ((0, 6, (255, 150, 40)), (0, 3.5, (255, 240, 190)), (5, 4, (255, 190, 80)), (9, 2.5, (255, 220, 140))):
        blob(c, x + dx * t, y + dy * t, r * k, col, 0.95 * k)
def fireball(c, x, y, t):                            # an HE burst: white-yellow core, orange ball, then rising grey smoke
    if t < 5:
        blob(c, x, y, 6 + t * 2.8, (255, 110, 25), 1.0 - t * 0.12); blob(c, x, y, 3 + t * 1.6, (255, 200, 80), 0.95 - t * 0.17)
        if t < 3: blob(c, x, y, 2.5 + t, (255, 250, 220), 1 - t * 0.3)
    s = max(0, t - 2); blob(c, x + 1, y - 3 - s * 1.6, 5 + s * 1.8, (110, 104, 96), min(0.75, 0.25 * s + 0.2) * (1 - t / 14))
    blob(c, x - 3, y - 1 - s * 1.0, 4 + s * 1.4, (140, 132, 120), min(0.6, 0.2 * s + 0.15) * (1 - t / 14))
_rp = os.environ.get('CMF_ROUND')
if _rp:
    ROUND = Image.open(_rp).convert('RGBA'); ROUND = ROUND.crop(ROUND.getbbox()); _k = float(os.environ.get('CMF_ROUND_PX', '5')) / ROUND.width
    ROUND = ROUND.resize((max(1, round(ROUND.width * _k)), max(1, round(ROUND.height * _k))), Image.LANCZOS)
    from PIL import ImageEnhance; _a = ROUND.getchannel('A'); ROUND = ImageEnhance.Brightness(ROUND.convert('RGB')).enhance(1.6).convert('RGBA'); ROUND.putalpha(_a)
else:
    ROUND = Image.new('RGBA', (8, 6), (52, 58, 40, 255))
def base(hd): c = ground(); v = veh(hd, STATES[fired]); c.alpha_composite(v); return c, v
for si, hd in enumerate(HDS):
    if si:
        a, b = H8.index(HDS[si - 1]), H8.index(hd)
        for j in range(1, (b - a) % 8 + 1):
            for _ in range(3): out(base(H8[(a + j) % 8])[0])
    for _ in range(4): out(base(hd)[0])
    fx, fy = scr((1, 0, 0), hd); L = math.hypot(fx, fy); dx, dy = fx / L, fy / L
    rounds = []
    for n in range(18):                                      # twin .50 cal: two bursts of three, barrels alternating
        c, _ = base(hd); dr = ImageDraw.Draw(c)
        if n < 12 and n % 2 == 0:
            s = scr(G[(n // 2) % len(G)], hd); gx, gy = ox + s[0], oy + s[1]; rounds.append([gx, gy])
            dr.ellipse((gx - 4, gy - 3, gx + 4, gy + 3), fill=(255, 236, 160, 255))
        for r in rounds:
            dr.line([(r[0], r[1]), (r[0] + dx * 10, r[1] + dy * 10)], fill=(255, 205, 90, 255), width=2); r[0] += dx * 22; r[1] += dy * 22
        out(c)
    # CMF-1 (John 18 Nov 00:04 "it's a ten round grenade launcher basically, not a machine gun"; 00:11 "the grenades shoot like a
    # cannon"; 00:14 "use a better graphic"): three rendered 40mm-style HE rounds (vfactory/ferret/cmf_round.py, env CMF_ROUND) fired
    # flat from the end of the tube in a ripple - soft muzzle flash and smoke, a faint trail, a fireball and smoke where each hits
    mz = frm(hd, STATES[fired])['muzzles'][CAN]['xy']; cx, cy = ox - AX + mz[0], oy - AY + mz[1]
    ang = math.degrees(math.atan2(-dy, dx)); rnd = ROUND.rotate(ang, resample=Image.BICUBIC, expand=True)
    nades, puffs, booms = [], [], []
    for n in range(26):
        c, _ = base(hd)
        if n in (0, 4, 8):
            nades.append([cx, cy, 0]); puffs.append([cx, cy, 0])
        for pf in puffs:
            if pf[2] < 9: blob(c, pf[0] + dx * (4 + pf[2] * 1.5), pf[1] + dy * (4 + pf[2] * 1.5) - pf[2] * 0.8, 3 + pf[2] * 1.3, SMOKE, 0.55 * (1 - pf[2] / 9))
            if pf[2] < 2: flash(c, cx + dx * 5, cy + dy * 5, dx, dy, 1.0 if pf[2] == 0 else 0.5)
            pf[2] += 1
        for g in nades[:]:
            g[2] += 1; g[0] += dx * 12; g[1] += dy * 12
            if g[2] > 6: booms.append([g[0], g[1], 0]); nades.remove(g); continue
            for k in range(1, 5): blob(c, g[0] - dx * 5 * k, g[1] - dy * 5 * k, 1.6 + k * 0.5, SMOKE, 0.35 - k * 0.07)
            c.alpha_composite(rnd, (int(g[0] - rnd.width / 2), int(g[1] - rnd.height / 2)))
        for b in booms:
            if b[2] < 12: fireball(c, b[0], b[1], b[2])
            b[2] += 1
        out(c)
    if fired < len(RK):                                      # one Com-Bat off its peg: the package's own rocket, the peg empties
        dep = DEP[fired] if fired < len(DEP) else []
        for ds in dep:                                       # the rams push it out from between the wheels
            for _ in range(3): c = ground(); c.alpha_composite(veh(hd, ds)); out(c)
        out_st = dep[-1] if dep else STATES[fired]
        name = RK[fired]; mf = m['missile_full']['by_heading'][hd]; ms = Image.open(f'{P}/{mf["file"]}').convert('RGBA')
        nx, ny = mf['nose_px']; tx, ty = mf['tail_px']; fdx, fdy = mf['flight_dir_screen']; L = math.hypot(fdx, fdy); fdx, fdy = fdx / L, fdy / L
        mz = frm(hd, out_st)['muzzles'][name]['xy']; x0, y0 = ox - AX + mz[0], oy - AY + mz[1]
        mask = occluder(veh(hd, out_st), veh(hd, STATES[fired + 1]), ms, (int(x0 - nx), int(y0 - ny))); fired += 1
        x, y, v, trail = x0, y0, FL['start_px_per_frame'], []
        for n in range(20):
            c, cur = base(hd); dr = ImageDraw.Draw(c); sx, sy = x - (nx - tx), y - (ny - ty)
            for i, (qx, qy) in enumerate(trail[-8:]):
                r = 2 + (len(trail[-8:]) - i) * 0.7; dr.ellipse((qx - r, qy - r, qx + r, qy + r), fill=(150, 146, 138, 150))
            dr.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=(255, 200, 90, 255)); trail.append((sx, sy))
            mdraw(c, ms, (int(x - nx), int(y - ny)), mask, cur)
            x += fdx * v; y += fdy * v; v = min(FL['max_px_per_frame'], v + FL['accel_px_per_frame2'])
            out(c)
for _ in range(8): out(base(HDS[-1])[0])
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=70, loop=0); print('CLIP', OUT, len(frames))
