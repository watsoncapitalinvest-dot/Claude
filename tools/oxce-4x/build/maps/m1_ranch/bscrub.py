"""BSCRUB: Texas border ground set (missions 1, later border/desert maps). Index = MCD index = frame."""
import math, random
import bmesh
from kitlib import *
SET = 'BSCRUB'

def fl(name, ox=0, oy=0, rot=0, tone=None):
    def f(p):
        paint = (lambda x, y, c, r: (tone, tone, tone)) if tone else None
        p.ground((1, 1, 1), tex=TX(name, ox, oy, rot=rot), paint=paint)
    return f

def bank(axis):
    """low earth berm along the cell's west (x=0) or north (y=0) edge: a trapezoid prism the full cell length,
    no ink (so runs of bank tiles join without seams), textured like the caliche."""
    def f(p):
        bm, layer = p.noink, p.ncol
        base, top, h = 0.55, 0.18, 0.5
        prof = [(0, 0), (base, 0), (top + 0.08, h), (0.04, h)]       # across, up
        def P(a, c, z):     # a = along edge, c = across into the cell
            return (c, -a, z) if axis == 'w' else (a, -c, z)
        A = [[bm.verts.new(P(a, c, z)) for (c, z) in prof] for a in (0, S)]
        fs = []
        for i in range(4):
            j = (i + 1) % 4
            fs.append(bm.faces.new((A[0][i], A[0][j], A[1][j], A[1][i])))
        fs.append(bm.faces.new(A[0][::-1])); fs.append(bm.faces.new(A[1]))
        bmesh.ops.recalc_face_normals(bm, faces=fs); bm.normal_update()
        p._paint(bm, layer, fs, CALICHE, 0, TX('a1', .3, .3))
    return f

def mesquite(seed):
    def f(p):
        rnd = random.Random(seed); cx, cy = S / 2 + rnd.uniform(-.1, .1), -S / 2 + rnd.uniform(-.1, .1)
        for k in range(3):
            p.rod((cx, cy, 0), (cx + rnd.uniform(-.25, .25), cy + rnd.uniform(-.25, .25), rnd.uniform(.45, .75)), 0.035, BARK, ink=True)
        for i in range(7):
            a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(0.05, 0.36)
            p.blob(cx + r * math.cos(a), cy + r * math.sin(a), rnd.uniform(0.5, 0.95),
                   rnd.uniform(0.2, 0.3), rnd.uniform(0.2, 0.3), rnd.uniform(0.11, 0.16), LEAF, seed=seed + i)
    return f

def prickly(p):
    rnd = random.Random(31); cx, cy = S / 2, -S / 2
    pads = [(0, 0, 0.22, 0.3), (0.18, 0.05, 0.45, 0.6), (-0.15, -0.05, 0.42, 0.25), (0.05, -0.1, 0.7, 0.4), (-0.2, 0.08, 0.62, -0.3)]
    for (dx, dy, z, ang) in pads:      # flat oval pads, standing on edge
        ca, sa = math.cos(ang), math.sin(ang)
        p.blob(cx + dx, cy + dy, z, 0.2 * ca + 0.05, 0.2 * sa + 0.05, 0.2, (0.36, 0.52, 0.24), sub=2, rough=0.05, seed=int(z * 100))
    for i in range(6):
        p.blob(cx + rnd.uniform(-.2, .2), cy + rnd.uniform(-.15, .15), rnd.uniform(0.75, 0.9), 0.04, 0.04, 0.04, (0.86, 0.72, 0.2), sub=1, rough=0)

def rock_a(p): rock(p, 5)
def rock_b(p):
    p.blob(S / 2 - 0.1, -S / 2, 0.25, 0.55, 0.5, 0.5, ROCK, sub=2, rough=0.25, seed=41)
    p.blob(S / 2 + 0.38, -S / 2 + 0.2, 0.15, 0.25, 0.22, 0.25, ROCK, sub=1, rough=0.2, seed=42)
def pebbles(p):
    rnd = random.Random(51)
    for i in range(6):
        p.blob(rnd.uniform(.2, S - .2), -rnd.uniform(.2, S - .2), 0.03, rnd.uniform(.08, .14), rnd.uniform(.07, .12), 0.07, ROCK, sub=1, rough=0.2, seed=60 + i)

def cane(p):
    rnd = random.Random(71)
    for i in range(60):
        x, y = rnd.uniform(.1, S - .1), -rnd.uniform(.1, S - .1)
        h = rnd.uniform(1.4, 1.85); lean = (rnd.uniform(-.12, .12), rnd.uniform(-.12, .12))
        col = (0.62, 0.62, 0.34) if rnd.random() < .5 else (0.50, 0.56, 0.28)
        p.rod((x, y, 0), (x + lean[0], y + lean[1], h), 0.028, col, ink=False, seg=4)
        for k in range(2):     # leaf blades
            z = rnd.uniform(.6, h - .1); a = rnd.uniform(0, 6.28)
            p.rod((x + lean[0] * z / h, y + lean[1] * z / h, z), (x + 0.32 * math.cos(a), y + 0.32 * math.sin(a), z - 0.25), 0.015, (0.46, 0.54, 0.26), ink=False, seg=3)

def snag(p):
    cx, cy = S / 2, -S / 2; B = (0.52, 0.46, 0.38)
    p.rod((cx, cy, 0), (cx + .05, cy, 1.5), 0.07, B, ink=True)
    for (a, b, c, d) in ((.9, .3, -.1, 1.4), (1.1, -.35, .05, 1.7), (.6, .1, .3, 1.15)):
        p.rod((cx + .02, cy, a), (cx + b, cy + c, d), 0.035, B, ink=True)

def tyre(p):
    cx, cy = S / 2, -S / 2
    p.cyl(cx, cy, 0, 0.22, 0.38, (0.93, 0.93, 0.9), seg=20)
    p.cyl(cx, cy, 0.22, 0.225, 0.2, (0.3, 0.3, 0.3), seg=20)

def stock_tank(p):
    cx, cy = S / 2, -S / 2
    p.cyl(cx, cy, 0, 0.62, 0.58, STEEL, seg=24, tex=TX('a10', size=1.3))
    p.cyl(cx, cy, 0.62, 0.64, 0.6, (0.6, 0.62, 0.64), seg=24)
    p.cyl(cx, cy, 0.5, 0.56, 0.54, (0.42, 0.5, 0.36), seg=24)     # water inside

def bfence(axis):
    """ranch barbed-wire fence: wooden post at the cell start + 3 wires"""
    def f(p):
        post = (0.05, -0.05)
        p.box(post[0] - .05, post[0] + .05, post[1] - .05, post[1] + .05, 0, 1.25, (0.55, 0.42, 0.28))
        for z in (0.45, 0.8, 1.12):
            a, b = ((0, 0, z), (S, 0, z)) if axis == 'n' else ((0, 0, z), (0, -S, z))
            p.rod(a, b, 0.008, (0.35, 0.35, 0.36), ink=False, seg=4)
    return f

KIT = [
    ('caliche_a', False, fl('a1', 0, 0)), ('caliche_b', False, fl('a1', .5, 0)),
    ('caliche_c', False, fl('a1', 0, .5)), ('caliche_d', False, fl('a1', .5, .5)),
    ('scrub_a', False, fl('a2', 0, 0)), ('scrub_b', False, fl('a2', .5, .5)),
    ('road_ns_a', False, fl('a3', 0, 0, rot=math.pi / 2)), ('road_ns_b', False, fl('a3', 0, .5, rot=math.pi / 2)),
    ('road_ew_a', False, fl('a3', 0, 0)), ('road_ew_b', False, fl('a3', .5, 0)),
    ('strip_a', False, fl('a1', .25, .25, tone=1.18)), ('strip_b', False, fl('a1', .75, .25, tone=1.18)),
    ('sand_a', False, fl('a4', 0, 0)), ('sand_b', False, fl('a4', .5, .5)),
    ('water_a', False, fl('a5', 0, 0)), ('water_b', False, fl('a5', .5, 0)),
    ('mud_a', False, fl('a6', 0, 0)),
    ('bank_w', False, bank('w')), ('bank_n', False, bank('n')),
    ('bfence_w', True, bfence('w')), ('bfence_n', True, bfence('n')),
    ('mesquite_a', True, mesquite(3)), ('mesquite_b', True, mesquite(17)),
    ('prickly_pear', True, prickly), ('rock_a', True, rock_a), ('rock_b', True, rock_b),
    ('pebbles', True, pebbles), ('cane', True, cane), ('snag', True, snag),
    ('tyre_marker', True, tyre), ('stock_tank', True, stock_tank),
]

# MCD: (vanilla set, record, overrides). See build_set.py for the override keys.
_floor = ('DESERT', 0, {})
MCDSPEC = {n: _floor for n, _, _ in KIT if n.split('_')[0] in ('caliche', 'scrub', 'road', 'strip', 'sand', 'mud')}
MCDSPEC.update({
    'water_a': ('DESERT', 0, dict(walkonly=255)), 'water_b': ('DESERT', 0, dict(walkonly=255)),
    'bank_w': ('CULTIVAT', 18, dict(loft=[9] * 4 + [0] * 8, walk=6, los=0)),
    'bank_n': ('CULTIVAT', 19, dict(loft=[10] * 4 + [0] * 8, walk=6, los=0)),
    'bfence_w': ('CULTIVAT', 18, {}), 'bfence_n': ('CULTIVAT', 19, {}),
    'mesquite_a': ('DESERT', 10, {}), 'mesquite_b': ('DESERT', 10, {}),
    'prickly_pear': ('DESERT', 16, {}),
    'rock_a': ('DESERT', 12, {}), 'rock_b': ('DESERT', 14, {}),
    'pebbles': ('DESERT', 11, {}), 'tyre_marker': ('DESERT', 11, {}),
    'cane': ('CULTIVAT', 4, dict(loft=[6] + [78] * 7 + [0] * 4, los=1, walk=6)),
    'snag': ('DESERT', 12, dict(loft=[1] * 8 + [0] * 4)),
    'stock_tank': ('FRNITURE', 17, dict(loft=[33] * 4 + [0] * 8)),
})
