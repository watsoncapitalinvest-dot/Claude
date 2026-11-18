# Firing clip for John: a one-layer vehicle whose weapons are fixed to the hull (Cobra Ferret: twin .50 cal forward, the CMF-1
# 10-round launcher along its right side, a Com-Bat rocket on each foot peg). The vehicle turns to aim (no turret). At each heading:
# a .50 cal burst (barrels alternating), a CMF-1 ripple from the end of its tube, then one Com-Bat leaves its peg - the package's own
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
    mz = frm(hd, STATES[fired])['muzzles'][CAN]['xy']; cx, cy = ox - AX + mz[0], oy - AY + mz[1]; slugs = []
    for n in range(16):                                      # CMF-1: a ripple of three slugs from the end of the tube
        c, _ = base(hd); dr = ImageDraw.Draw(c)
        if n in (0, 3, 6):
            slugs.append([cx, cy]); dr.ellipse((cx - 7, cy - 5, cx + 7, cy + 5), fill=(255, 220, 140, 255)); dr.ellipse((cx - 3 + dx * 5, cy - 3 + dy * 5, cx + 3 + dx * 5, cy + 3 + dy * 5), fill=(255, 255, 230, 255))
        for sl in slugs:
            dr.line([(sl[0] - dx * 8, sl[1] - dy * 8), (sl[0], sl[1])], fill=(140, 200, 255, 255), width=3); dr.ellipse((sl[0] - 2, sl[1] - 2, sl[0] + 2, sl[1] + 2), fill=(230, 245, 255, 255))
            sl[0] += dx * 26; sl[1] += dy * 26
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
