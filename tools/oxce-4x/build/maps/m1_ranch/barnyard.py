"""BARNYRD: barn, yard gear, fences, watchtower, windmill (mission 1; reused for farms and cartel sites).
Index = MCD index = frame. Multi-level pieces (tower, windmill) are drawn per level; the map puts them at z 0/1/2."""
import math, random
import bmesh
from kitlib import *
SET = 'BARNYRD'
TOP = H * 0.98            # wall top
WOODP = (0.55, 0.42, 0.28)
PACK = (0.62, 0.50, 0.30)   # taped bundles (product)

def tfloor(name, ox=0, oy=0, rot=0, z=0.0):
    def f(p): p.ground((1, 1, 1), tex=TX(name, ox, oy, rot=rot), z=z)
    return f

def straw(p):
    p.ground((1, 1, 1), tex=TX('a7', .5, 0))
    rnd = random.Random(8)
    for i in range(40):          # loose straw on the barn floor
        x, y = rnd.uniform(.1, S - .1), -rnd.uniform(.1, S - .1); a = rnd.uniform(0, 3.14)
        p.rod((x, y, 0.01), (x + 0.22 * math.cos(a), y + 0.22 * math.sin(a), 0.015), 0.01, (0.86, 0.76, 0.42), seg=3)

# ---- barn walls: textured slab + white top trim; edge marks keep the run seamless
def wslab(p, axis, a0, a1, z0, z1, rgb=BARNRED, th=T, off=0.0, tex=None, ink=False):
    keep = keep_west if axis == 'w' else keep_north
    if axis == 'w': return p.box(off, off + th, -a1, -a0, z0, z1, rgb, ink=ink, mark=keep, tex=tex)
    return p.box(a0, a1, -off - th, -off, z0, z1, rgb, ink=ink, mark=keep, tex=tex)

def barn(axis, kind='wall'):
    def f(p):
        tx = TX('a9', 0, 0, size=2.6)
        if kind == 'wall':
            wslab(p, axis, 0, S, 0, TOP - 0.14, tex=tx)
        elif kind == 'window':
            wslab(p, axis, 0, S, 0, 0.75, tex=tx); wslab(p, axis, 0, S, 1.45, TOP - 0.14, tex=tx)
            wslab(p, axis, 0, 0.3, 0.75, 1.45, tex=tx); wslab(p, axis, S - 0.3, S, 0.75, 1.45, tex=tx)
            wslab(p, axis, 0.3, S - 0.3, 0.75, 1.45, (0.2, 0.24, 0.28), th=0.03, off=0.045)   # dark glass
            for (a0, a1, z0, z1) in ((0.26, S - 0.26, 0.71, 0.77), (0.26, S - 0.26, 1.43, 1.49),
                                     (0.26, 0.32, 0.71, 1.49), (S - 0.32, S - 0.26, 0.71, 1.49), (S / 2 - .03, S / 2 + .03, 0.75, 1.45)):
                wslab(p, axis, a0, a1, z0, z1, TRIM, th=0.05, off=T - 0.02)
        elif kind == 'door':
            wslab(p, axis, 0, S, 0, TOP - 0.14, tex=tx)
            for (a0, a1, z0, z1) in ((0.08, 0.15, 0, TOP - 0.2), (S - 0.15, S - 0.08, 0, TOP - 0.2), (0.08, S - 0.08, TOP - 0.27, TOP - 0.2)):
                wslab(p, axis, a0, a1, z0, z1, TRIM, th=0.03, off=T)
            zt = TOP - 0.27
            W = (lambda a_, z_: (T + 0.03, -a_, z_)) if axis == 'w' else (lambda a_, z_: (a_, -T - 0.03, z_))
            p.rod(W(0.17, 0.05), W(S - 0.17, zt), 0.045, TRIM, ink=True, seg=4)
            p.rod(W(S - 0.17, 0.05), W(0.17, zt), 0.045, TRIM, ink=True, seg=4)
        elif kind == 'open':
            wslab(p, axis, 0, 0.1, 0, TOP - 0.14, tex=tx); wslab(p, axis, S - 0.1, S, 0, TOP - 0.14, tex=tx)
            wslab(p, axis, 0, S, TOP - 0.36, TOP - 0.14, tex=tx)
        wslab(p, axis, 0, S, TOP - 0.14, TOP, TRIM, th=T + 0.04, off=-0.02)
    return f

def roof(p):        # flat tin roof sheet at the top of the barn walls (a floor on level 1)
    p.ground((1, 1, 1), tex=TX('a10', size=2.6, rot=math.pi / 2))
    p.box(0, S, -S, 0, -0.08, -0.01, (0.6, 0.62, 0.64), ink=False, tex=TX("a10", size=2.6))

# ---- crates (pilot crate with the artist's wood and stencils)
def crate_k(decs):
    def f(p):
        w, d, h = 0.95, 0.95, 0.78; x0, y0 = (S - w) / 2, -(S + d) / 2
        p.box(x0, x0 + w, y0, y0 + d, 0, h, WOOD, tex=TX('a11', size=1.6))
        for z in (0.06, 0.66):
            p.box(x0 - 0.015, x0 + w + 0.015, y0 - 0.015, y0 + 0.02, z, z + 0.07, WOOD_D)
            p.box(x0 + w - 0.02, x0 + w + 0.015, y0 - 0.015, y0 + d + 0.015, z, z + 0.07, WOOD_D)
        if decs[0]: p.decal((x0 + 0.1, y0 - 0.016, 0.16), (1, 0, 0), (0, 0, 1), 0.75, 0.375, decs[0])
        if decs[1]: p.decal((x0 + w + 0.016, y0 + 0.1, 0.16), (0, 1, 0), (0, 0, 1), 0.75, 0.375, decs[1])
    return f

def crate_open(p):
    w, d, h, t = 0.95, 0.95, 0.78, 0.05; x0, y0 = (S - w) / 2, -(S + d) / 2; tx = TX('a11', size=1.6)
    p.box(x0, x0 + w, y0, y0 + t, 0, h, WOOD, tex=tx); p.box(x0, x0 + w, y0 + d - t, y0 + d, 0, h, WOOD, tex=tx)
    p.box(x0, x0 + t, y0, y0 + d, 0, h, WOOD, tex=tx); p.box(x0 + w - t, x0 + w, y0, y0 + d, 0, h, WOOD, tex=tx)
    p.box(x0 + t, x0 + w - t, y0 + t, y0 + d - t, 0, 0.35, (0.80, 0.70, 0.40))
    p.box(x0 - 0.22, x0 - 0.17, y0 + 0.05, y0 + d - 0.05, 0, 0.62, WOOD_D, tex=tx)

def table(p, top=None):
    x0, x1, y0, y1, h = 0.12, S - 0.12, -S + 0.3, -0.3, 0.8
    p.box(x0, x1, y0, y1, h - 0.06, h, WOOD, tex=TX('a11', size=1.6))
    for (x, y) in ((x0 + .04, y0 + .04), (x1 - .1, y0 + .04), (x0 + .04, y1 - .1), (x1 - .1, y1 - .1)):
        p.box(x, x + .06, y, y + .06, 0, h - .06, WOOD_D)
    rnd = random.Random(5)
    for i in range(4 if top == 'scale' else 6):     # taped bundles
        bx, by = x0 + 0.1 + (i % 3) * 0.33, y0 + 0.08 + (i // 3) * 0.3
        p.box(bx, bx + 0.26, by, by + 0.2, h, h + 0.12, PACK)
        p.box(bx + 0.11, bx + 0.15, by - 0.005, by + 0.205, h + 0.002, h + 0.122, (0.82, 0.78, 0.6))
    if top == 'scale':
        sx, sy = x1 - 0.42, y1 - 0.34
        p.box(sx, sx + 0.3, sy, sy + 0.24, h, h + 0.05, (0.75, 0.76, 0.78))
        p.box(sx + 0.05, sx + 0.25, sy + 0.04, sy + 0.2, h + 0.05, h + 0.07, (0.85, 0.86, 0.88))
        p.box(sx + 0.22, sx + 0.29, sy + 0.2, sy + 0.24, h + 0.05, h + 0.25, (0.3, 0.3, 0.32))

def bales(p):        # stack of plastic-wrapped product bales
    for (x, y, z) in ((0.15, -1.15, 0), (0.62, -1.15, 0), (0.15, -0.72, 0), (0.62, -0.72, 0), (0.38, -0.95, 0.38)):
        p.box(x, x + 0.45, y, y + 0.4, z, z + 0.36, PACK)
        p.box(x + 0.19, x + 0.25, y - 0.005, y + 0.405, z + 0.002, z + 0.362, (0.82, 0.78, 0.6))

def hay(p):
    p.box(0.25, 1.05, -1.0, -0.3, 0, 0.42, (0.86, 0.74, 0.38), jitter=0.02)
    for x in (0.45, 0.85):
        p.box(x, x + 0.03, -1.005, -0.295, 0, 0.425, (0.55, 0.45, 0.25))

# ---- watchtower: legs + ladder (L0), deck with corner posts (L1), rails (L1 walls), roof (L2)
def tower_lift(p):
    p.ground((1, 1, 1), tex=TX('a1', .4, .1))
def tower_legs(p):
    for (x, y) in ((0.08, -0.08), (S - 0.08, -0.08), (0.08, -S + 0.08), (S - 0.08, -S + 0.08)):
        p.box(x - .06, x + .06, y - .06, y + .06, 0, H, WOODP)
    for (a, b) in (((0.08, -0.08, 0.2), (S - 0.08, -0.08, H - 0.2)), ((0.08, -S + .08, 0.2), (0.08, -0.08, H - 0.2))):
        p.rod(a, b, 0.03, WOODP, ink=True, seg=4)
    lx = S / 2                                     # ladder on the south face
    for dx in (-0.2, 0.2): p.box(lx + dx - .025, lx + dx + .025, -S + 0.02, -S + 0.07, 0, H, WOOD)
    for z in [0.25 + 0.3 * i for i in range(6)]: p.box(lx - 0.2, lx + 0.2, -S + 0.03, -S + 0.06, z, z + 0.04, WOOD)
def tower_deck(p):
    p.ground((1, 1, 1), tex=TX('a11', size=1.6))
    for (x, y) in ((0.08, -0.08), (S - 0.08, -0.08), (0.08, -S + 0.08), (S - 0.08, -S + 0.08)):
        p.box(x - .05, x + .05, y - .05, y + .05, 0, H, WOODP)
    p.box(S / 2 - 0.25, S / 2 + 0.25, -S + 0.05, -S + 0.55, 0.0, 0.01, (0.3, 0.22, 0.14))   # hatch
def tower_rail(axis):
    def f(p):
        tx = TX('a11', size=1.6)
        wslab(p, axis, 0, S, 0, 0.95, WOOD, th=0.06, tex=tx)
        wslab(p, axis, 0, S, 0.95, 1.02, WOOD_D, th=0.09, off=-0.015)
    return f
def tower_roof(p):
    bm, layer = p.bm, p.col
    h = 0.45; ov = 0.12
    c = [bm.verts.new(v) for v in ((-ov, ov, 0), (S + ov, ov, 0), (S + ov, -S - ov, 0), (-ov, -S - ov, 0))]
    ap = bm.verts.new((S / 2, -S / 2, h))
    fs = [bm.faces.new((c[i], c[(i + 1) % 4], ap)) for i in range(4)] + [bm.faces.new(c[::-1])]
    bmesh.ops.recalc_face_normals(bm, faces=fs); bm.normal_update()
    p._paint(bm, layer, fs, STEEL, 0, TX('a10', size=1.3))

# ---- windmill: lattice legs (L0), small deck + lattice (L1), wheel + vane (L2)
def lattice(p, z0, z1, w0, w1):
    c = S / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.rod((c + sx * w0, -c + sy * w0, z0), (c + sx * w1, -c + sy * w1, z1), 0.03, STEEL, ink=True, seg=4)
    for z in (z0 + 0.1, (z0 + z1) / 2):
        w = w0 + (w1 - w0) * (z - z0) / (z1 - z0)
        for (a, b) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            p.rod((c + a[0] * w, -c + a[1] * w, z), (c + b[0] * w, -c + b[1] * w, z), 0.015, STEEL, ink=False, seg=4)
def mill_lift(p): p.ground((1, 1, 1), tex=TX('a1', .7, .6))
def mill_legs(p):
    lattice(p, 0, H, 0.55, 0.36)
    lx = S / 2
    for z in [0.2 + 0.3 * i for i in range(6)]: p.box(lx - 0.12, lx + 0.12, -S / 2 - 0.4, -S / 2 - 0.37, z, z + 0.03, STEEL)
def mill_deck(p):
    p.ground((1, 1, 1), tex=TX('a11', size=1.6))
    lattice(p, 0, H, 0.36, 0.16)
def mill_wheel(p):
    c = S / 2; hub = (c + 0.12, -c - 0.12, 0.95)
    p.rod((c, -c, 0), (c, -c, 0.95), 0.06, STEEL, ink=True)
    p.box(c - .12, c + .12, -c - .15, -c + .15, 0.85, 1.05, (0.5, 0.52, 0.55))      # gearbox head
    n = 14; R0, R1 = 0.18, 0.8
    for i in range(n):               # wheel faces south-east (toward the viewer), vanes as thin panels
        a = 2 * math.pi * i / n
        u = Vector((0.7071, 0.7071, 0))   # wheel plane faces the viewer (SE)
        v0 = Vector(hub) + (u * math.cos(a) + Vector((0, 0, 1)) * math.sin(a)) * R0
        v1 = Vector(hub) + (u * math.cos(a) + Vector((0, 0, 1)) * math.sin(a)) * R1
        p.rod(tuple(v0), tuple(v1), 0.055, (0.86, 0.86, 0.84), ink=True, seg=4)
    p.rod(tuple(Vector(hub) + (u * math.cos(0) + Vector((0,0,1)) * 0) * 0), tuple(Vector(hub)), 0.01, STEEL)
    for i in range(n * 2):
        a0, a1 = 2 * math.pi * i / (2 * n), 2 * math.pi * (i + 1) / (2 * n)
        q0 = Vector(hub) + (u * math.cos(a0) + Vector((0, 0, 1)) * math.sin(a0)) * R1
        q1 = Vector(hub) + (u * math.cos(a1) + Vector((0, 0, 1)) * math.sin(a1)) * R1
        p.rod(tuple(q0), tuple(q1), 0.02, STEEL, ink=False, seg=4)
    # tail vane pointing back (north-west)
    p.rod((c, -c, 0.95), (c - 0.75, -c + 0.75, 1.0), 0.025, STEEL, ink=True, seg=4)
    p.box(c - 0.95, c - 0.65, -c + 0.62, -c + 0.68, 0.85, 1.25, (0.72, 0.18, 0.12))

KIT = [
    ('cbarn_a', False, tfloor('a7', 0, 0)), ('cbarn_b', False, tfloor('a7', .5, .5)), ('straw', False, straw),
    ('barnwall_w', True, barn('w')), ('barnwall_n', True, barn('n')),
    ('barnwin_w', True, barn('w', 'window')), ('barnwin_n', True, barn('n', 'window')),
    ('barndoor_w', True, barn('w', 'door')), ('barndoor_w_open', True, barn('w', 'open')),
    ('barndoor_n', True, barn('n', 'door')), ('barndoor_n_open', True, barn('n', 'open')),
    ('roof_tin', False, roof),
    ('crate_a', True, crate_k(('decal_b2a_machine_parts.png', 'decal_b2c_this_side_up.png'))),
    ('crate_b', True, crate_k(('decal_b2b_fragile.png', None))),
    ('crate_c', True, crate_k((None, 'decal_b2a_machine_parts.png'))),
    ('crate_open', True, crate_open),
    ('drum', True, drum),
    ('table', True, lambda p: table(p)), ('table_scale', True, lambda p: table(p, 'scale')),
    ('bales', True, bales), ('hay', True, hay),
    ('fence_w', True, lambda p: fence(p, 'w')), ('fence_n', True, lambda p: fence(p, 'n')),
    ('gate_w', True, lambda p: fence(p, 'w', 'gate')), ('gate_w_open', True, lambda p: fence(p, 'w', 'gate_open')),
    ('gate_n', True, lambda p: fence(p, 'n', 'gate')), ('gate_n_open', True, lambda p: fence(p, 'n', 'gate_open')),
    ('tower_lift', False, tower_lift), ('tower_legs', True, tower_legs), ('tower_deck', True, tower_deck),
    ('tower_rail_w', True, tower_rail('w')), ('tower_rail_n', True, tower_rail('n')), ('tower_roof', True, tower_roof),
    ('mill_lift', False, mill_lift), ('mill_legs', True, mill_legs), ('mill_deck', True, mill_deck), ('mill_wheel', True, mill_wheel),
]

OPEN = dict(loft=[0] * 12, walk=0, los=0, block=0, door=0)
MCDSPEC = {
    'cbarn_a': ('DESERT', 21, {}), 'cbarn_b': ('DESERT', 21, {}), 'straw': ('BARN', 19, {}),
    'barnwall_w': ('BARN', 6, {}), 'barnwall_n': ('BARN', 5, {}),
    'barnwin_w': ('BARN', 8, {}), 'barnwin_n': ('BARN', 7, dict(type=2)),          # vanilla windowed barn walls (see-through LOFT)
    'barndoor_w': ('BARN', 17, dict(alt='barndoor_w_open')), 'barndoor_w_open': ('BARN', 6, OPEN),
    'barndoor_n': ('BARN', 18, dict(alt='barndoor_n_open')), 'barndoor_n_open': ('BARN', 5, OPEN),
    'roof_tin': ('BARN', 19, {}),
    'crate_a': ('FRNITURE', 17, dict(alt='crate_open')), 'crate_b': ('FRNITURE', 17, dict(alt='crate_open')),
    'crate_c': ('FRNITURE', 17, dict(alt='crate_open')),
    'crate_open': ('FRNITURE', 17, dict(loft=[33] * 5 + [0] * 7, tlevel=-10)),
    'drum': ('URBITS', 24, dict(he=60)),
    'table': ('FRNITURE', 13, {}), 'table_scale': ('FRNITURE', 13, {}),
    'bales': ('FRNITURE', 16, dict(he=0)), 'hay': ('FRNITURE', 14, {}),
    'fence_w': ('URBITS', 12, {}), 'fence_n': ('URBITS', 13, {}),
    'gate_w': ('URBITS', 12, dict(door=1, walk=8, alt='gate_w_open')), 'gate_w_open': ('URBITS', 12, OPEN),
    'gate_n': ('URBITS', 13, dict(door=1, walk=8, alt='gate_n_open')), 'gate_n_open': ('URBITS', 13, OPEN),
    'tower_lift': ('DESERT', 0, dict(lift=1)),
    'tower_legs': ('DESERT', 11, dict(loft=[0] * 12, walk=0)),
    'tower_deck': ('BARN', 19, dict(lift=1)),
    'tower_rail_w': ('CULTIVAT', 18, dict(loft=[15] * 6 + [0] * 6)),
    'tower_rail_n': ('CULTIVAT', 19, dict(loft=[16] * 6 + [0] * 6)),
    'tower_roof': ('BARN', 19, {}),
    'mill_lift': ('DESERT', 0, dict(lift=1)),
    'mill_legs': ('DESERT', 11, dict(loft=[0] * 12, walk=0)),
    'mill_deck': ('BARN', 19, dict(lift=1)),
    'mill_wheel': ('DESERT', 11, dict(loft=[0] * 12, walk=0)),
}
