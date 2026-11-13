"""BOXTRUCK: Cobra box truck built from walls/floors/objects so units can enter the cab and the box (BUILD spec 13 Nov).
Truck footprint 6 x 3 cells (local i 0-5 east, j 0-2 south): box i 0-3, cab i 4-5 (front east). Roofs on the next level.
Every part has a wreck chain via its 'dies into' record: ok -> shot -> burn -> hulk.
The rear roll-up door is a UFO-type door with 8 animation frames (rear_f0..f7)."""
import math, random
from kitlib import *
SET = 'BOXTRUCK'
WHITE = (0.93, 0.93, 0.90)
CAB = (0.30, 0.31, 0.33)
CAB_L = (0.40, 0.41, 0.43)
CHASSIS = (0.14, 0.14, 0.15)
GLASS = (0.26, 0.33, 0.40)
CHROME = (0.82, 0.84, 0.86)
TYRE = (0.12, 0.12, 0.12)
STATES = ['ok', 'shot', 'burn', 'hulk']
ST = {'s': 'ok'}

def C(rgb, glass=False):
    """colour for the current wreck state"""
    s = ST['s']
    if s == 'ok': return rgb
    if s == 'shot': return (rgb[0] * 0.5, rgb[1] * 0.5, rgb[2] * 0.52) if glass else rgb
    if s == 'burn':
        k = 0.42; return (rgb[0] * k + 0.06, rgb[1] * k + 0.03, rgb[2] * k)
    k = 0.2; return (rgb[0] * k + 0.12, rgb[1] * k + 0.07, rgb[2] * k + 0.04)     # hulk: soot and rust
def holes(p, origin, u, v, w, h):
    if ST['s'] in ('shot', 'burn'): p.decal(origin, u, v, w, h, 'decal_b8c_bulletholes.png')
def flames(p, cx, cy, z, seed):
    if ST['s'] != 'burn': return
    rnd = random.Random(seed)
    for i in range(5):
        x, y = cx + rnd.uniform(-.3, .3), cy + rnd.uniform(-.3, .3)
        p.blob(x, y, z + rnd.uniform(0.05, 0.2), rnd.uniform(.12, .2), rnd.uniform(.12, .2), rnd.uniform(.25, .45), (0.98, 0.55, 0.12), sub=1, rough=0.3, ink=False, seed=seed + i)
        p.blob(x, y, z + rnd.uniform(0.3, 0.45), 0.08, 0.08, 0.18, (1.0, 0.85, 0.25), sub=1, rough=0.3, ink=False, seed=seed + 20 + i)
    for i in range(3):
        p.blob(cx + rnd.uniform(-.2, .2), cy + rnd.uniform(-.2, .2), z + 0.9 + i * 0.3, 0.25, 0.25, 0.2, (0.22, 0.21, 0.21), sub=1, rough=0.2, ink=False, seed=seed + 40 + i)

def wl(p, axis, a0, a1, z0, z1, rgb, th=T, off=0.0, ink=False):
    keep = keep_west if axis == 'w' else keep_north
    if axis == 'w': return p.box(off, off + th, -a1, -a0, z0, z1, rgb, ink=ink, mark=keep)
    return p.box(a0, a1, -off - th, -off, z0, z1, rgb, ink=ink, mark=keep)
def face(axis, a, z):           # a point just outside the visible face of a wall (south face of n, east face of w)
    return (T + 0.004, -a, z) if axis == 'w' else (a, -T - 0.004, z)
def uv(axis): return ((0, -1, 0), (0, 0, 1)) if axis == 'w' else ((1, 0, 0), (0, 0, 1))

TOPZ = H * 0.98
def wheel_n(p, a, flat=False):  # tyre under a north-slot side panel, seen on its south face
    r = 0.42 if not flat else 0.36
    zc = r if not flat else 0.3
    hub = ST['s'] == 'hulk'
    p.rod((a, -T - 0.02, zc), (a, -T - 0.3, zc), r if not hub else 0.3, C(TYRE) if not hub else (0.30, 0.20, 0.14), ink=True, seg=12)
    p.rod((a, -T - 0.3, zc), (a, -T - 0.32, zc), 0.2, C(CHROME), ink=True, seg=10)
    if flat and not hub: p.box(a - 0.45, a + 0.45, -T - 0.3, -T - 0.02, 0.0, 0.08, C(TYRE))

def box_side(kind='plain', flat=False):
    def f(p):
        wl(p, 'n', 0, S, 0.0, 0.5, C(CHASSIS))                                  # chassis rail / skirt
        if ST['s'] != 'hulk':
            wl(p, 'n', 0, S, 0.5, TOPZ, C(WHITE)); wl(p, 'n', 0, S, 0.5, 0.58, C((0.70, 0.70, 0.68)), th=T + 0.03)
            for a in (0.0, S / 2): wl(p, 'n', a, a + 0.04, 0.58, TOPZ, C((0.78, 0.78, 0.76)), th=T + 0.015)   # panel ribs
        else:                                                                     # burnt skin gone: frame ribs only
            for a in (0.0, S / 3, 2 * S / 3): wl(p, 'n', a, a + 0.08, 0.5, TOPZ, C(WHITE), th=0.08)
            wl(p, 'n', 0, S, TOPZ - 0.1, TOPZ, C(WHITE), th=0.1)
        if kind == 'axle': wheel_n(p, S / 2, flat)
        holes(p, face('n', 0.2, 0.8), *uv('n'), 0.6, 0.6)
        flames(p, S / 2, -0.4, TOPZ - 0.4, 3)
    return f

def rear_door(frame=0):         # roll-up door on the west end of the box (UFO door: frame 0 closed .. 7 open)
    def f(p):
        up = frame / 7.0
        wl(p, 'w', 0, S, 0.0, 0.5, C(CHASSIS))
        z_bot = 0.5 + up * (TOPZ - 0.6)
        for k in range(10):
            z0 = 0.5 + k * (TOPZ - 0.5) / 10
            if z0 + 0.01 < z_bot: continue
            wl(p, 'w', 0.05, S - 0.05, max(z0, z_bot), z0 + (TOPZ - 0.5) / 10, C(WHITE if k % 2 else (0.84, 0.84, 0.82)), th=0.05, off=0.035)
        wl(p, 'w', 0, 0.06, 0.5, TOPZ, C((0.6, 0.6, 0.6)), th=T); wl(p, 'w', S - 0.06, S, 0.5, TOPZ, C((0.6, 0.6, 0.6)), th=T)
        wl(p, 'w', 0, S, TOPZ - 0.12, TOPZ, C((0.6, 0.6, 0.6)), th=T)
        if frame == 0: wl(p, 'w', S / 2 - 0.1, S / 2 + 0.1, 0.55, 0.62, C(CHROME), th=0.02, off=0.085)
        holes(p, face('w', 0.3, 0.9), *uv('w'), 0.55, 0.55)
        flames(p, 0.4, -S / 2, TOPZ - 0.5, 7)
    return f

def box_front(p):               # partition between box (west) and cab (east), seen from the cab side
    wl(p, 'w', 0, S, 0.0, 0.5, C(CHASSIS))
    wl(p, 'w', 0, S, 0.5, TOPZ, C(WHITE) if ST['s'] != 'hulk' else C(WHITE))
    wl(p, 'w', 0, S, 0.5, 1.0, C(CAB), th=0.02, off=T)
    flames(p, 0.4, -S / 2, TOPZ - 0.4, 9)

def cab_side(kind):
    """kind: 'win' (side window), 'door', 'door_open', 'axle', 'axle_flat' (north slot along the cab)."""
    def f(p):
        wl(p, 'n', 0, S, 0.0, 0.45, C(CHASSIS))
        if kind == 'door_open':
            wl(p, 'n', 0, 0.12, 0.45, TOPZ, C(CAB)); wl(p, 'n', S - 0.12, S, 0.45, TOPZ, C(CAB)); wl(p, 'n', 0, S, TOPZ - 0.15, TOPZ, C(CAB))
            p.box(S - 0.12, S - 0.06, -T - 1.0, -T, 0.5, 1.75, C(CAB), mark=keep_north)             # door swung out (east hinge)
            return
        wl(p, 'n', 0, S, 0.45, 1.1, C(CAB)); wl(p, 'n', 0, S, 1.7, TOPZ, C(CAB))
        wl(p, 'n', 0, 0.15, 1.1, 1.7, C(CAB)); wl(p, 'n', S - 0.15, S, 1.1, 1.7, C(CAB))
        if ST['s'] == 'hulk': pass
        else:
            wl(p, 'n', 0.15, S - 0.15, 1.1, 1.7, C(GLASS, True), th=0.03, off=0.045)
            if ST['s'] in ('shot', 'burn'):
                for (a0, a1) in ((0.4, 0.43), (0.7, 0.73)): wl(p, 'n', a0, a1, 1.15, 1.65, (0.85, 0.88, 0.9), th=0.005, off=T)   # cracks
        wl(p, 'n', 0, S, 1.0, 1.06, C(CAB_L), th=T + 0.02)
        if kind == 'door':
            wl(p, 'n', 0.12, 0.16, 0.45, 1.75, C(CHASSIS), th=0.005, off=T)
            wl(p, 'n', S - 0.16, S - 0.12, 0.45, 1.75, C(CHASSIS), th=0.005, off=T)
            wl(p, 'n', S - 0.4, S - 0.25, 0.95, 0.99, C(CHROME), th=0.03, off=T)                         # handle
            for z in (0.15, 0.35): wl(p, 'n', 0.3, S - 0.3, z, z + 0.04, C(CHROME), th=0.25, off=T)       # step
        if kind.startswith('axle'): wheel_n(p, S / 2, kind == 'axle_flat')
        holes(p, face('n', 0.3, 0.55), *uv('n'), 0.55, 0.55)
        flames(p, S / 2, -0.4, 1.5, 11)
    return f

def cab_front(pos):             # west slot of the cell east of the cab: windscreen, grille, lights, bumper. pos: l, c, r (north..south)
    def f(p):
        wl(p, 'w', 0, S, 0.0, 0.25, C(CHASSIS))
        wl(p, 'w', 0, S, 0.25, 1.1, C(CAB)); wl(p, 'w', 0, S, 1.75, TOPZ, C(CAB))
        a0 = 0.12 if pos == 'l' else 0.0; a1 = S - 0.12 if pos == 'r' else S
        wl(p, 'w', 0, a0, 1.1, 1.75, C(CAB)); wl(p, 'w', a1, S, 1.1, 1.75, C(CAB))
        if ST['s'] != 'hulk': wl(p, 'w', a0, a1, 1.1, 1.75, C(GLASS, True), th=0.03, off=0.045)
        wl(p, 'w', 0, S, 0.25, 0.42, C(CHROME), th=T + 0.1)                                           # bumper
        for z in (0.55, 0.68, 0.81, 0.94): wl(p, 'w', 0.1, S - 0.1, z, z + 0.05, C(CHROME if pos == 'c' else CAB_L), th=0.03, off=T)   # grille bars
        if pos in ('l', 'r') and ST['s'] != 'hulk':
            a = 0.3 if pos == 'l' else S - 0.5
            wl(p, 'w', a, a + 0.22, 0.55, 0.75, (0.98, 0.96, 0.8) if ST['s'] == 'ok' else C((0.98, 0.96, 0.8), True), th=0.03, off=T)
        holes(p, face('w', 0.3, 1.15), *uv('w'), 0.6, 0.5)
        flames(p, 0.5, -S / 2, 1.2, 13)
    return f

def roof(rgb, seed):
    def f(p):
        if ST['s'] == 'hulk' and rgb == WHITE:
            for a in (0.1, S / 2): p.box(a, a + 0.08, -S, 0, -0.06, 0.0, C(WHITE), ink=True)              # roof skin burnt away
            return
        p.box(0, S, -S, 0, -0.06, 0.0, C(rgb), ink=False)
        if rgb == WHITE:
            for k in range(4): p.box(k * S / 4, k * S / 4 + 0.03, -S, 0, 0.0, 0.01, C((0.80, 0.80, 0.78)), ink=False)
        else:
            p.box(0.2, S - 0.2, -S + 0.3, -0.3, 0.0, 0.08, C(CAB_L))
        flames(p, S / 2, -S / 2, 0.0, seed)
    return f
def floor(kind):
    def f(p):
        if kind == 'box':
            for k in range(6):
                y0 = -S + k * S / 6
                p.box(0, S, y0 + 0.01, y0 + S / 6 - 0.01, 0.0, 0.03, C((0.62, 0.48, 0.32) if k % 2 else (0.56, 0.43, 0.28)), ink=False)
        else:
            p.box(0, S, -S, 0, 0.0, 0.03, C((0.22, 0.22, 0.23)), ink=False)
            for k in range(6): p.box(0.1, S - 0.1, -S + 0.1 + k * 0.2, -S + 0.14 + k * 0.2, 0.03, 0.035, C((0.30, 0.30, 0.31)), ink=False)
        if ST['s'] in ('burn', 'hulk'):
            for i in range(4): p.box(0.1 + 0.27 * i, 0.3 + 0.27 * i, -0.4 - 0.2 * i, -0.2 - 0.2 * i, 0.035, 0.04, (0.08, 0.08, 0.08), ink=False)
    return f
def engine(p):                  # engine 'doghouse' between the seats (cab-over): the objective part
    p.box(0.25, 1.05, -1.0, -0.3, 0.0, 0.9, C(CAB_L))
    p.box(0.3, 1.0, -0.95, -0.35, 0.9, 0.95, C(CHASSIS))
    if ST['s'] != 'ok':                                                       # cover shot through: engine showing
        p.box(0.35, 0.95, -0.85, -0.45, 0.6, 1.1, C((0.42, 0.44, 0.40)))
        for x in (0.45, 0.65, 0.85): p.cyl(x, -0.65, 1.1, 1.16, 0.06, C(STEEL), seg=6)
    for (x, y) in ((0.15, -0.15), (0.15, -1.15)):                             # seat backs either side
        p.box(1.05, 1.25, y - 0.1, y + 0.1, 0.4, 1.1, C((0.45, 0.30, 0.22)))
    flames(p, 0.65, -0.65, 0.9, 17)
def fuel_tank(p):               # saddle tank hung under the cab, in the road cell beside it
    if ST['s'] == 'hulk':
        p.box(0.2, 1.1, -0.35, -0.05, 0.25, 0.35, C(CHROME)); return
    p.rod((0.15, -0.3, 0.55), (1.15, -0.3, 0.55), 0.26, C(CHROME), ink=True, seg=14)
    for x in (0.35, 0.95): p.rod((x, -0.3, 0.55), (x + 0.04, -0.3, 0.55), 0.27, C(CHASSIS), ink=True, seg=14)
    p.cyl(0.7, -0.3, 0.8, 0.86, 0.06, C(CHASSIS), seg=8)
    flames(p, 0.65, -0.3, 0.6, 19)

BASE = [   # (name, ink, builder, has wreck chain)
    ('box_side', True, box_side()), ('box_side_axle', True, box_side('axle')), ('box_side_flat', True, box_side('axle', True)),
    ('box_rear', True, rear_door(0)), ('box_front', True, box_front),
    ('cab_win', True, cab_side('win')), ('cab_door', True, cab_side('door')), ('cab_axle', True, cab_side('axle')),
    ('cab_axle_flat', True, cab_side('axle_flat')),
    ('cab_front_l', True, cab_front('l')), ('cab_front_c', True, cab_front('c')), ('cab_front_r', True, cab_front('r')),
    ('box_roof', False, roof(WHITE, 21)), ('cab_roof', False, roof(CAB, 23)),
    ('box_floor', False, floor('box')), ('cab_floor', False, floor('cab')),
    ('engine', True, engine), ('fuel_tank', True, fuel_tank),
]
def staged(fn, st):
    def f(p):
        ST['s'] = st
        try: fn(p)
        finally: ST['s'] = 'ok'
    return f
KIT = []
for (n, ink, fn) in BASE:
    for st in STATES: KIT.append((n if st == 'ok' else '%s_%s' % (n, st), ink, staged(fn, st)))
KIT.append(('cab_door_open', True, cab_side('door_open')))
for k in range(1, 8): KIT.append(('box_rear_f%d' % k, True, rear_door(k)))       # animation frames of the roll-up door

# ---------------------------------------------------------------- MCD
TEMPL = {'w': ('URBAN', 8), 'n': ('URBAN', 7)}
SIDE_N = ('box_side', 'box_side_axle', 'box_side_flat', 'cab_win', 'cab_door', 'cab_axle', 'cab_axle_flat')
WEST = ('box_rear', 'box_front', 'cab_front_l', 'cab_front_c', 'cab_front_r')
def chain(n):
    return [n] + ['%s_%s' % (n, s) for s in STATES[1:]]
MCDSPEC = {}
for (n, _, _) in BASE:
    names = chain(n)
    for k, nm in enumerate(names):
        nxt = names[k + 1] if k + 1 < len(names) else None
        burning = nm.endswith('_burn')
        extra = dict(die=nxt) if nxt else {}
        if burning: extra.update(fuel=20, flam=40)
        if n in SIDE_N:
            arm = {'box': 12}.get(n[:3], 20)                                  # box skin: thin, bullets punch through
            MCDSPEC[nm] = ('URBAN', 7, dict(extra, armor=arm, type=2))
        elif n in WEST:
            MCDSPEC[nm] = ('URBAN', 8, dict(extra, armor=12 if n.startswith('box') else 20, type=1))
        elif n in ('box_roof', 'cab_roof', 'box_floor', 'cab_floor'):
            MCDSPEC[nm] = ('BARN', 19, dict(extra, armor=20, type=0))
        elif n == 'engine':
            MCDSPEC[nm] = ('FRNITURE', 17, dict(extra, armor=40, walk=255, loft=[33] * 6 + [0] * 6, type=3, special=14 if k == 0 else 0))
        elif n == 'fuel_tank':
            MCDSPEC[nm] = ('URBITS', 24, dict(extra, armor=10, walk=255, type=3, he=50 if k < 2 else 0, fuel=30 if k < 2 else 0))
# the cab door opens to its open record; the rear roll-up is a UFO door animated over 8 frames
MCDSPEC['cab_door'] = ('URBAN', 30, dict(MCDSPEC['cab_door'][2], alt='cab_door_open', door=1))
MCDSPEC['cab_door_open'] = ('URBAN', 30, dict(loft=[0] * 12, walk=0, los=0, block=0, door=0, type=2, armor=20, die='cab_door_shot'))
MCDSPEC['box_rear'] = ('URBAN', 8, dict(MCDSPEC['box_rear'][2], ufodoor=1, frames=['box_rear'] + ['box_rear_f%d' % k for k in range(1, 8)]))
for k in range(1, 8): MCDSPEC['box_rear_f%d' % k] = ('URBAN', 8, dict(type=1, armor=12))   # frame-only records (not placed on the map)

# ---------------------------------------------------------------- cargo stacked in the front half of the box (leaves 2 x 3 floor free)
def cargo(p):
    COB = (0.22, 0.34, 0.62)
    for (x0, y0, z0, w, d, h) in ((0.1, -1.2, 0.03, 0.55, 0.5, 0.5), (0.7, -1.2, 0.03, 0.5, 0.5, 0.5), (0.1, -0.65, 0.03, 1.1, 0.5, 0.55),
                                  (0.2, -1.15, 0.53, 0.5, 0.45, 0.45), (0.75, -0.6, 0.58, 0.4, 0.45, 0.4)):
        p.box(x0, x0 + w, y0, y0 + d, z0, z0 + h, C(COB) if ST['s'] != 'hulk' else C(COB))
        p.box(x0 - 0.005, x0 + w + 0.005, y0 - 0.005, y0 + d + 0.005, z0 + h * 0.45, z0 + h * 0.55, C((0.75, 0.75, 0.72)), ink=False)
    if ST['s'] == 'ok': p.decal((0.25, -1.205, 0.12), (1, 0, 0), (0, 0, 1), 0.3, 0.3, 'decal_b1_cobra_stencil.png')
    flames(p, 0.6, -0.8, 0.9, 29)
KIT += [('cargo', True, staged(cargo, 'ok')), ('cargo_hulk', True, staged(cargo, 'hulk'))]
MCDSPEC['cargo'] = ('FRNITURE', 17, dict(die='cargo_hulk', armor=20, walk=255, loft=[33] * 6 + [0] * 6))
MCDSPEC['cargo_hulk'] = ('FRNITURE', 17, dict(armor=20, walk=255, loft=[33] * 4 + [0] * 8))
