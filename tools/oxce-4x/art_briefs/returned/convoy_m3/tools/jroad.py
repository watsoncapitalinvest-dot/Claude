"""JROAD: desert highway for the convoy raid (BUILD spec 13 Nov). Named JROAD (vanilla-safe name).
Asphalt with lane/edge lines, gravel shoulder, culvert, telephone poles, spike strip, burnt-out car, road-crew yard
(gravel piles, grader, site trailer), Extensive Enterprises billboard (2 levels, climbable, deck at level 1).
render: python3 render_big.py jroad <outdir>"""
import math, json, os, random
from kitlib import *
SET = 'JROAD'
HERE = os.path.dirname(os.path.abspath(__file__))
ASPH = (0.30, 0.31, 0.33)
LINEY = (0.92, 0.76, 0.18)
LINEW = (0.94, 0.94, 0.92)
GRAVEL = (0.66, 0.62, 0.56)
YELLOW = (0.92, 0.70, 0.12)
DARK = (0.15, 0.15, 0.16)
SOOT = (0.18, 0.16, 0.15)
RUST = (0.45, 0.25, 0.14)
TRAILER = (0.90, 0.88, 0.80)

def asphalt(seed, line=None):
    def f(p):
        rnd = random.Random(seed)
        def paint(x, y, c, r):
            k = 0.93 + 0.14 * rnd.random()
            return (ASPH[0] * k, ASPH[1] * k, ASPH[2] * k)
        p.ground((1, 1, 1), n=16, paint=paint)
        if line == 'lane':                       # dashed yellow centre line on the north edge
            p.box(0.15, 0.95, -0.06, 0.0, 0.0, 0.006, LINEY, ink=False)
        elif line == 'edge_n':
            p.box(0, S, -0.12, -0.04, 0.0, 0.006, LINEW, ink=False)
        elif line == 'edge_s':
            p.box(0, S, -S + 0.04, -S + 0.12, 0.0, 0.006, LINEW, ink=False)
        elif line == 'skid':
            for dy in (-0.35, -0.95): p.box(0.0, S, dy - 0.07, dy + 0.07, 0.0, 0.004, (0.16, 0.16, 0.17), ink=False)
        elif line == 'spikes':                   # spike strip laid across the road (north-south)
            p.box(0.55, 0.75, -S, 0, 0.0, 0.03, (0.20, 0.20, 0.22), ink=False)
            for k in range(9):
                y = -0.07 - k * 0.14
                p.box(0.58, 0.62, y - 0.02, y + 0.02, 0.03, 0.08, STEEL, ink=False); p.box(0.68, 0.72, y - 0.09, y - 0.05, 0.03, 0.08, STEEL, ink=False)
    return f
def shoulder(seed):
    def f(p):
        p.tint = (0.95, 0.92, 0.88); p.ground((1, 1, 1), tex=TX('a3', 0.3 * seed, 0.5 * seed, size=2.6)); p.tint = (1, 1, 1)
        rnd = random.Random(seed)
        for i in range(5):
            p.blob(rnd.uniform(.15, S - .15), -rnd.uniform(.15, S - .15), 0.0, 0.06, 0.05, 0.03, GRAVEL, sub=1, rough=0.2, ink=False, seed=seed * 11 + i)
    return f
def culvert_floor(p):           # inside the pipe: curved concrete sides, a trickle of sand
    p.box(0, S, -S, 0, 0.0, 0.05, CONCRETE, ink=False)
    for k in range(5):
        a = (k + 1) * math.pi / 12
        w = 0.65 * (1 - math.cos(a))
        p.box(0.0, 0.08 + w * 0.3, -S, 0, 0.05 + 0.25 * math.sin(a) * k / 5, 0.1 + 0.3 * k / 5, (0.58, 0.58, 0.56), ink=False)
        p.box(S - 0.08 - w * 0.3, S, -S, 0, 0.05 + 0.25 * math.sin(a) * k / 5, 0.1 + 0.3 * k / 5, (0.58, 0.58, 0.56), ink=False)
    p.box(0.45, 0.85, -S, 0, 0.05, 0.07, (0.84, 0.74, 0.55), ink=False)

# ---------------------------------------------------------------- telephone pole (2 levels: lo + hi), broken stump
def pole_lo(p):
    p.cyl(S / 2, -S / 2, 0, H, 0.11, (0.42, 0.30, 0.20), seg=10)
    p.box(S / 2 - 0.12, S / 2 + 0.12, -S / 2 - 0.13, -S / 2 - 0.1, 1.2, 1.4, (0.85, 0.82, 0.70))      # tag plate
def pole_hi(p):
    p.cyl(S / 2, -S / 2, 0, 1.5, 0.1, (0.42, 0.30, 0.20), seg=10)
    p.box(S / 2 - 0.06, S / 2 + 0.06, -S / 2 - 0.75, -S / 2 + 0.75, 1.1, 1.22, (0.42, 0.30, 0.20))       # crossarm
    for dy in (-0.65, -0.25, 0.25, 0.65):
        p.cyl(S / 2, -S / 2 + dy, 1.22, 1.36, 0.04, (0.30, 0.55, 0.45), seg=6)                         # glass insulators
def pole_stump(p):
    p.cyl(S / 2, -S / 2, 0, 0.6, 0.11, (0.30, 0.22, 0.15), seg=10)
    p.rod((S / 2, -S / 2, 0.55), (S / 2 + 0.9, -S / 2 - 0.5, 0.15), 0.1, (0.42, 0.30, 0.20), ink=True, seg=8)

# ---------------------------------------------------------------- yard props
def gravel_pile(seed):
    def f(p):
        p.blob(S / 2, -S / 2, 0.0, 0.64, 0.6, 0.7 + 0.1 * seed, GRAVEL, sub=2, rough=0.08, seed=seed)
        rnd = random.Random(seed)
        for i in range(8):
            a = rnd.uniform(0, 2 * math.pi)
            p.blob(S / 2 + 0.5 * math.cos(a), -S / 2 + 0.5 * math.sin(a), 0.05, 0.06, 0.05, 0.04, (0.55, 0.52, 0.47), sub=1, rough=0.2, ink=False, seed=seed * 5 + i)
    return f
def cones(p):
    for (x, y) in ((0.35, -0.4), (0.9, -0.85)):
        p.box(x - 0.14, x + 0.14, y - 0.14, y + 0.14, 0, 0.03, (0.9, 0.4, 0.1))
        for k in range(4):
            r = 0.1 - k * 0.02
            p.cyl(x, y, 0.03 + k * 0.12, 0.15 + k * 0.12, r, (0.95, 0.45, 0.12) if k != 2 else LINEW, seg=8)
def barrier(p):                 # striped road-work sawhorse
    for x in (0.2, S - 0.25):
        p.rod((x, -0.5, 0), (x, -0.6, 0.85), 0.03, (0.9, 0.9, 0.9), ink=True, seg=4); p.rod((x, -0.75, 0), (x, -0.6, 0.85), 0.03, (0.9, 0.9, 0.9), ink=True, seg=4)
    for k in range(5):
        x0 = 0.1 + k * 0.22
        p.box(x0, x0 + 0.22, -0.64, -0.58, 0.6, 0.85, (0.95, 0.45, 0.12) if k % 2 else LINEW)

# ---------------------------------------------------------------- site trailer (one room, enterable)
def tslab(p, axis, a0, a1, z0, z1, rgb, th=T, off=0.0, ink=False):
    keep = keep_west if axis == 'w' else keep_north
    if axis == 'w': return p.box(off, off + th, -a1, -a0, z0, z1, rgb, ink=ink, mark=keep)
    return p.box(a0, a1, -off - th, -off, z0, z1, rgb, ink=ink, mark=keep)
def twall(axis, kind):
    TOPZ = 2.3
    def f(p):
        def body(a0, a1, z0, z1):
            tslab(p, axis, a0, a1, z0, z1, TRAILER)
            for z in [0.5 + 0.25 * k for k in range(7)]:
                if z0 < z < z1: tslab(p, axis, a0, a1, z - 0.015, z, (0.72, 0.70, 0.64), th=0.008, off=T)
        tslab(p, axis, 0, S, 0.0, 0.45, (0.25, 0.25, 0.27))                     # skirt (trailer on blocks)
        if kind == 'wall': body(0, S, 0.45, H)
        elif kind == 'win':
            body(0, S, 0.45, 1.0); body(0, S, 1.6, H); body(0, 0.3, 1.0, 1.6); body(S - 0.3, S, 1.0, 1.6)
            tslab(p, axis, 0.3, S - 0.3, 1.0, 1.6, (0.25, 0.30, 0.35), th=0.03, off=0.045)
            for (a0, a1, z0, z1) in ((0.26, S - 0.26, 0.96, 1.0), (0.26, S - 0.26, 1.6, 1.64), (S / 2 - .02, S / 2 + .02, 1.0, 1.6)):
                tslab(p, axis, a0, a1, z0, z1, (0.55, 0.55, 0.55), th=0.05, off=T - 0.02)
        else:
            body(0, 0.25, 0.45, H); body(S - 0.25, S, 0.45, H); body(0.25, S - 0.25, 1.9, H)
            if kind == 'door':
                tslab(p, axis, 0.27, S - 0.27, 0.45, 1.9, (0.80, 0.78, 0.70), th=0.05, off=0.035)
                tslab(p, axis, 0.4, S - 0.4, 1.4, 1.7, (0.25, 0.30, 0.35), th=0.01, off=0.085)
            for st in range(2):                                               # metal steps outside
                z = 0.15 + st * 0.15
                if axis == 'w': p.box(T + 0.05 + st * 0.0, T + 0.5 - st * 0.18, -S + 0.3, -0.3, z, z + 0.04, STEEL)
                else: p.box(0.3, S - 0.3, -T - 0.5 + st * 0.18, -T - 0.05, z, z + 0.04, STEEL)
        tslab(p, axis, 0, S, H - 0.08, H, (0.70, 0.70, 0.66), th=T + 0.04, off=-0.02, ink=True)
    return f
def trailer_floor(p):
    p.box(0, S, -S, 0, 0.0, 0.03, (0.55, 0.50, 0.40), ink=False)
    for k in range(5): p.box(0, S, -S + k * S / 5, -S + k * S / 5 + 0.01, 0.03, 0.032, (0.45, 0.40, 0.32), ink=False)
def trailer_roof(p):
    p.ground((1, 1, 1), tex=TX('a10', size=2.6, rot=math.pi / 2)); p.box(0, S, -S, 0, -0.08, -0.01, (0.6, 0.62, 0.64), ink=False)
def plan_table(p):
    x0, x1, y0, y1, h = 0.1, S - 0.1, -1.0, -0.2, 0.9
    p.box(x0, x1, y0, y1, h - 0.05, h, (0.70, 0.62, 0.45))
    for (x, y) in ((x0, y0), (x1 - 0.05, y0), (x0, y1 - 0.05), (x1 - 0.05, y1 - 0.05)): p.box(x, x + 0.05, y, y + 0.05, 0, h - 0.05, STEEL)
    p.box(x0 + 0.1, x1 - 0.2, y0 + 0.1, y1 - 0.1, h, h + 0.005, (0.85, 0.88, 0.95))         # road plans
    p.decal((x0 + 0.15, y0 + 0.15, h + 0.008), (1, 0, 0), (0, 1, 0), 0.4, 0.4, 'decal_b7b_shipping.png')
    p.rod((x1 - 0.3, y0 + 0.4, h), (x1 - 0.3, y0 + 0.4, h + 0.2), 0.04, (0.9, 0.9, 0.9), seg=6)  # coffee flask
def locker_open(p):
    locker(p)
    p.box(0.25, 0.27, -1.0, -0.6, 0, 1.8, (0.42, 0.50, 0.42))                                   # left door swung open
    p.box(0.3, 0.6, -0.55, -0.15, 1.2, 1.22, (0.30, 0.30, 0.30))                                  # shelf, a jacket hanging
    p.box(0.33, 0.58, -0.45, -0.25, 0.7, 1.2, (0.55, 0.35, 0.18))
def locker(p):
    for k in range(2):
        x = 0.25 + k * 0.42
        p.box(x, x + 0.4, -0.6, -0.12, 0, 1.8, (0.42, 0.50, 0.42))
        for z in (1.5, 1.55, 1.6): p.box(x + 0.08, x + 0.32, -0.61, -0.6, z, z + 0.02, DARK)

# ---------------------------------------------------------------- billboard: deck floor, ladder, lift floor (+ big face/legs object)
def bb_deck(p):
    p.box(0, S, -S, -0.1, -0.05, 0.0, (0.45, 0.47, 0.48), ink=True)
    for k in range(10): p.box(k * S / 10, k * S / 10 + 0.03, -S, -0.1, 0.0, 0.01, (0.32, 0.33, 0.34), ink=False)
    p.box(0, S, -S, -S + 0.04, 0.85, 0.9, STEEL, ink=True)                                    # guard rail on the open side
    for x in (0.05, S / 2): p.box(x, x + 0.04, -S, -S + 0.04, 0, 0.9, STEEL, ink=True)
def bb_ladder(p):
    for a in (0.45, 0.85): p.box(a - 0.03, a + 0.03, -S + 0.14, -S + 0.2, 0, H, STEEL)
    for z in [0.15 + 0.3 * k for k in range(7)]: p.box(0.45, 0.85, -S + 0.15, -S + 0.18, z, z + 0.035, STEEL)
def bb_lift(p): shoulder(9)(p)
def bb_liftdeck(p): bb_deck(p)

# ---------------------------------------------------------------- big objects
BILLBOARD = (3, 1, 3)           # 3 cells wide (x), face on the north edge of the row, levels ground+0..+2
def build_billboard(p):
    for x in (0.65, 3 * S - 0.65):                                                         # two steel legs
        p.box(x - 0.13, x + 0.13, -0.5, -0.24, 0, 2 * H + 0.3, (0.42, 0.44, 0.46))
        p.rod((x, -0.37, 0.4), (x + (0.5 if x < 1 else -0.5), -0.37, H - 0.3), 0.04, (0.42, 0.44, 0.46), ink=True, seg=4)
    z0, z1 = H + 0.25, 2 * H + 0.95
    p.box(0.05, 3 * S - 0.05, -0.24, -0.08, z0, z1, (0.85, 0.85, 0.82))                    # board
    p.decal((0.12, -0.245, z0 + 0.07), (1, 0, 0), (0, 0, 1), 3 * S - 0.24, z1 - z0 - 0.14, 'decal_ee_billboard.png')
    for x in (0.6, 1.95, 3.3):                                                             # floodlights on arms
        p.rod((x, -0.3, z0 - 0.05), (x, -0.95, z0 - 0.05), 0.025, DARK, ink=True, seg=4)
        p.box(x - 0.1, x + 0.1, -1.05, -0.9, z0 - 0.15, z0, DARK)
CAR = (3, 2, 1)                 # burnt-out 1970s sedan, nose east
def build_car(p):
    cy = -S
    body = (0.22, 0.20, 0.19)
    p.box(0.2, 3.7, cy - 0.85, cy + 0.85, 0.3, 0.85, body)
    p.box(1.1, 2.7, cy - 0.78, cy + 0.78, 0.85, 1.25, body)
    for (x0, x1) in ((1.15, 1.85), (1.95, 2.65)):
        p.box(x0, x1, cy - 0.79, cy + 0.79, 0.9, 1.2, (0.08, 0.08, 0.08))                  # empty window holes
    p.box(2.7, 2.75, cy - 0.7, cy + 0.7, 0.88, 1.2, (0.08, 0.08, 0.08))
    for (x0, x1, y0, y1) in ((0.4, 1.0, cy - 0.86, cy - 0.5), (2.9, 3.5, cy + 0.3, cy + 0.86), (1.4, 2.2, cy - 0.3, cy + 0.4)):
        p.box(x0, x1, y0, y1, 0.86 if y0 > cy - 0.5 else 0.35, 0.87 if y0 > cy - 0.5 else 0.8, RUST)   # rust patches
    p.decal((0.5, cy - 0.852, 0.35), (1, 0, 0), (0, 0, 1), 0.6, 0.45, 'decal_b8a_rust.png')
    for x in (0.75, 3.1):
        for s_ in (-1, 1):
            p.rod((x, cy + s_ * 0.85, 0.22), (x, cy + s_ * 0.95, 0.22), 0.22, (0.35, 0.33, 0.31), ink=True, seg=10)   # bare rims
    p.box(0.25, 3.65, cy - 0.85, cy + 0.85, 0.0, 0.3, (0.12, 0.11, 0.10))                  # sitting on the rims, low
GRADER = (6, 2, 2)              # motor grader, nose east, cab at the rear (west)
def build_grader(p):
    cy = -S
    p.box(1.8, 7.2, cy - 0.18, cy + 0.18, 0.75, 1.05, YELLOW)                               # long arched frame
    p.box(6.9, 7.6, cy - 0.5, cy + 0.5, 0.45, 1.1, YELLOW)                                   # front nose
    p.box(0.3, 2.3, cy - 1.0, cy + 1.0, 0.65, 1.55, YELLOW)                                  # engine housing
    p.box(0.35, 2.25, cy - 1.01, cy + 1.01, 0.9, 1.3, DARK)                                  # vent grille band
    p.box(1.4, 2.6, cy - 0.85, cy + 0.85, 1.55, 2.9, YELLOW)                                 # cab
    p.box(1.42, 2.58, cy - 0.86, cy + 0.86, 1.95, 2.75, (0.30, 0.36, 0.42))                 # cab glass
    p.box(1.3, 2.7, cy - 0.95, cy + 0.95, 2.9, 3.0, YELLOW)
    p.rod((0.5, cy + 0.6, 1.55), (0.5, cy + 0.6, 2.4), 0.06, DARK, ink=True, seg=6)           # exhaust stack
    p.box(3.6, 3.75, cy - 1.25, cy + 1.25, 0.05, 0.6, (0.55, 0.57, 0.58))                   # moldboard blade (angled feel)
    p.box(3.75, 3.85, cy - 1.25, cy + 1.25, 0.05, 0.15, STEEL)
    p.rod((3.7, cy, 0.6), (4.6, cy, 0.8), 0.06, YELLOW, ink=True, seg=6)
    for (x, r) in ((0.6, 0.55), (1.9, 0.55), (7.25, 0.5)):
        for s_ in (-1, 1): p.rod((x, cy + s_ * 0.85, r), (x, cy + s_ * 1.2, r), r, (0.13, 0.13, 0.13), ink=True, seg=12)
    p.decal((0.6, cy - 1.011, 0.7), (1, 0, 0), (0, 0, 1), 1.0, 0.5, 'decal_b8b_oil.png')

SINGLES = [
    ('asphalt_a', False, asphalt(1)), ('asphalt_b', False, asphalt(2)), ('asphalt_lane', False, asphalt(3, 'lane')),
    ('asphalt_edge_n', False, asphalt(4, 'edge_n')), ('asphalt_edge_s', False, asphalt(5, 'edge_s')),
    ('asphalt_skid', False, asphalt(6, 'skid')), ('spike_strip', False, asphalt(7, 'spikes')),
    ('shoulder_a', False, shoulder(1)), ('shoulder_b', False, shoulder(2)), ('culvert_floor', False, culvert_floor),
    ('pole_lo', True, pole_lo), ('pole_hi', True, pole_hi), ('pole_stump', True, pole_stump),
    ('gravel_pile_a', True, gravel_pile(1)), ('gravel_pile_b', True, gravel_pile(2)), ('cones', True, cones), ('barrier', True, barrier),
    ('trailer_wall_w', True, twall('w', 'wall')), ('trailer_wall_n', True, twall('n', 'wall')),
    ('trailer_win_w', True, twall('w', 'win')), ('trailer_win_n', True, twall('n', 'win')),
    ('trailer_door_w', True, twall('w', 'door')), ('trailer_door_w_open', True, twall('w', 'open')),
    ('trailer_door_n', True, twall('n', 'door')), ('trailer_door_n_open', True, twall('n', 'open')),
    ('trailer_floor', False, trailer_floor), ('trailer_roof', False, trailer_roof),
    ('plan_table', True, plan_table), ('locker', True, locker), ('locker_open', True, locker_open),
    ('bb_deck', True, bb_deck), ('bb_ladder', True, bb_ladder), ('bb_lift', False, bb_lift), ('bb_liftdeck', True, bb_liftdeck),
]
NO_BLOCKERS = ('billboard',)       # its ground row stays open except the two legs
BIGS = [('billboard', build_billboard, BILLBOARD), ('car', build_car, CAR), ('grader', build_grader, GRADER)]
MAN = os.path.join(HERE, 'jroad_cells.json')
CELLS = json.load(open(MAN)) if os.path.exists(MAN) else {}
KIT = [(n, ink, fn) for (n, ink, fn) in SINGLES]
for (obj, _, _) in BIGS:
    for (i, j, l, name) in CELLS.get(obj, []): KIT.append((name, True, None))

OPEN = dict(loft=[0] * 12, walk=0, los=0, block=0, door=0)
MCDSPEC = {}
for n in ('asphalt_a', 'asphalt_b', 'asphalt_lane', 'asphalt_edge_n', 'asphalt_edge_s', 'asphalt_skid', 'shoulder_a', 'shoulder_b',
          'culvert_floor', 'trailer_floor', 'trailer_roof'):
    MCDSPEC[n] = ('DESERT', 21, {})
MCDSPEC.update({
    'spike_strip': ('DESERT', 21, {}),
    'pole_lo': ('FRNITURE', 10, dict(walk=255, armor=30, die='pole_stump')), 'pole_hi': ('FRNITURE', 10, dict(walk=255, armor=30)),
    'pole_stump': ('FRNITURE', 10, dict(walk=255, loft=[25] * 3 + [0] * 9)),
    'gravel_pile_a': ('FRNITURE', 17, dict(loft=[33] * 5 + [0] * 7, walk=255, armor=60)),
    'gravel_pile_b': ('FRNITURE', 17, dict(loft=[33] * 5 + [0] * 7, walk=255, armor=60)),
    'cones': ('FRNITURE', 10, dict(loft=[0] * 12, walk=4)), 'barrier': ('FRNITURE', 10, dict(loft=[0] * 12, walk=6)),
    'trailer_wall_w': ('URBAN', 8, {}), 'trailer_wall_n': ('URBAN', 7, {}),
    'trailer_win_w': ('URBAN', 10, {}), 'trailer_win_n': ('URBAN', 9, {}),
    'trailer_door_w': ('URBAN', 29, dict(alt='trailer_door_w_open')), 'trailer_door_w_open': ('URBAN', 29, dict(OPEN)),
    'trailer_door_n': ('URBAN', 30, dict(alt='trailer_door_n_open')), 'trailer_door_n_open': ('URBAN', 30, dict(OPEN)),
    'plan_table': ('FRNITURE', 0, {}), 'locker': ('FRNITURE', 19, dict(alt='locker_open')), 'locker_open': ('FRNITURE', 19, {}),
    'bb_deck': ('BARN', 19, {}), 'bb_ladder': ('FRNITURE', 10, dict(walk=4, loft=[0] * 12)),
    'bb_lift': ('DESERT', 21, dict(lift=1)), 'bb_liftdeck': ('BARN', 19, dict(lift=1)),
})
FACE = set()
for (obj, _, _) in BIGS:
    for (i, j, l, name) in CELLS.get(obj, []):
        if obj == 'billboard':
            if l == 0: MCDSPEC[name] = ('FRNITURE', 10, dict(walk=255, loft=[25] * 12, armor=60))       # legs
            else: MCDSPEC[name] = ('URBAN', 31, dict(type=2, armor=30, loft=[16] * 12))                   # face: a north wall
        elif obj == 'car': MCDSPEC[name] = ('FRNITURE', 17, dict(loft=[33] * 6 + [0] * 6, walk=255, armor=40))
        else: MCDSPEC[name] = ('FRNITURE', 17, dict(loft=[33] * (12 if l == 0 else 6) + ([0] * 6 if l else []), walk=255, armor=60))
