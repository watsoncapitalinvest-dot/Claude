"""RANCH: ranch house (brick, 2 storeys), bunkhouse (painted siding), porch, stairs, furniture, safe, desk,
footlockers (mission 1; reused for farms, cartel and Dreadnok sites).
Index = MCD index = frame. Upper storey = the same walls and floors placed at z 1."""
import math, random
from kitlib import *
SET = 'RANCH'
TOP = H * 0.98
PLASTER = (0.88, 0.83, 0.70)
BASEB = (0.55, 0.40, 0.25)
SIDING = (0.90, 0.86, 0.74)
SIDING_L = (0.70, 0.66, 0.56)
GLASS = (0.22, 0.27, 0.32)
DOORW = (0.93, 0.92, 0.88)
OLIVE = (0.40, 0.42, 0.24)
WHITE = (0.90, 0.90, 0.88)
DARK = (0.18, 0.18, 0.20)
SOFA = (0.72, 0.42, 0.18)
MATT = (0.80, 0.78, 0.68)
BLANKET = (0.45, 0.30, 0.22)

def tfloor(name, ox=0, oy=0, size=2.6, rot=0, tint=(1, 1, 1)):
    def f(p):
        p.tint = tint; p.ground((1, 1, 1), tex=TX(name, ox, oy, size=size, rot=rot)); p.tint = (1, 1, 1)
    return f

def lino(p):        # 1970s kitchen checker
    def paint(x, y, c, r):
        a, b = int(x / (S / 4)), int(-y / (S / 4))
        return (0.86, 0.84, 0.76) if (a + b) % 2 else (0.62, 0.30, 0.20)
    p.ground((1, 1, 1), n=24, paint=paint)

def roof(p):
    p.ground((1, 1, 1), tex=TX('a10', size=2.6, rot=math.pi / 2))
    p.box(0, S, -S, 0, -0.08, -0.01, (0.6, 0.62, 0.64), ink=False, tex=TX("a10", size=2.6))

# ---------------------------------------------------------------- walls
def wslab(p, axis, a0, a1, z0, z1, rgb, th=T, off=0.0, tex=None, ink=False):
    keep = keep_west if axis == 'w' else keep_north
    if axis == 'w': return p.box(off, off + th, -a1, -a0, z0, z1, rgb, ink=ink, mark=keep, tex=tex)
    return p.box(a0, a1, -off - th, -off, z0, z1, rgb, ink=ink, mark=keep, tex=tex)

def W(axis, a, z, out):           # point on the outside face (south/east side of a west/north wall)
    return (out, -a, z) if axis == 'w' else (a, -out, z)

def wall(style, axis, kind='wall'):
    """style: 'brick' (ranch house), 'siding' (bunkhouse), 'plaster' (interior)."""
    def f(p):
        tx = TX('a12', 0, 0, size=2.0) if style == 'brick' else None
        rgb = {'brick': BARNRED, 'siding': SIDING, 'plaster': PLASTER}[style]
        def body(a0, a1, z0, z1):
            wslab(p, axis, a0, a1, z0, z1, rgb, tex=tx)
            if style == 'siding':          # lap lines on the outside face
                for z in [z for z in (0.35, 0.7, 1.05, 1.4, 1.75) if z0 < z < z1]:
                    wslab(p, axis, a0, a1, z - 0.02, z, SIDING_L, th=0.012, off=T)
            if style == 'plaster' and z0 == 0:
                wslab(p, axis, a0, a1, 0, 0.12, BASEB, th=0.012, off=T)
        if kind == 'wall':
            body(0, S, 0, TOP)
        elif kind == 'window':
            body(0, S, 0, 0.8); body(0, S, 1.5, TOP); body(0, 0.3, 0.8, 1.5); body(S - 0.3, S, 0.8, 1.5)
            wslab(p, axis, 0.3, S - 0.3, 0.8, 1.5, GLASS, th=0.03, off=0.045)
            for (a0, a1, z0, z1) in ((0.26, S - 0.26, 0.74, 0.8), (0.26, S - 0.26, 1.5, 1.56),
                                     (0.26, 0.32, 0.74, 1.56), (S - 0.32, S - 0.26, 0.74, 1.56), (S / 2 - .025, S / 2 + .025, 0.8, 1.5)):
                wslab(p, axis, a0, a1, z0, z1, TRIM, th=0.05, off=T - 0.02)
        elif kind in ('door', 'open'):
            body(0, 0.25, 0, TOP); body(S - 0.25, S, 0, TOP); body(0.25, S - 0.25, 1.85, TOP)
            for (a0, a1, z0, z1) in ((0.21, 0.27, 0, 1.89), (S - 0.27, S - 0.21, 0, 1.89), (0.21, S - 0.21, 1.83, 1.89)):
                wslab(p, axis, a0, a1, z0, z1, TRIM, th=0.04, off=T - 0.01)
            if kind == 'door':
                dc = DOORW if style != 'siding' else WOOD
                wslab(p, axis, 0.27, S - 0.27, 0, 1.83, dc, th=0.05, off=0.035)
                for (z0, z1) in ((0.15, 0.85), (1.0, 1.7)):          # raised panels
                    wslab(p, axis, 0.36, S - 0.36, z0, z1, dc, th=0.015, off=0.085)
                k = W(axis, S - 0.38, 0.95, 0.1)
                p.box(k[0] - 0.03, k[0] + 0.03, k[1] - 0.03, k[1] + 0.03, 0.93, 0.99, (0.85, 0.7, 0.2))
        if style != 'plaster':
            wslab(p, axis, 0, S, TOP - 0.1, TOP, TRIM, th=T + 0.04, off=-0.02)
    return f

# ---------------------------------------------------------------- porch, stairs, sign
def porch_post(p):
    p.box(0.02, 0.14, -0.14, -0.02, 0, TOP, WHITE)
def porch_rail(axis):
    def f(p):
        wslab(p, axis, 0, S, 0.85, 0.92, WHITE, th=0.07, ink=True)
        wslab(p, axis, 0, S, 0.0, 0.08, WHITE, th=0.07, ink=True)
        for a in [0.1 + 0.15 * i for i in range(8)]:
            wslab(p, axis, a, a + 0.04, 0.08, 0.85, WHITE, th=0.04, off=0.015, ink=True)
    return f

def stairs(half):
    """climbs northward (y from -S up to 0). lo: z 0 -> H/2, hi: H/2 -> H. Open riser side faces the viewer."""
    def f(p):
        n = 5; zb = 0 if half == 'lo' else H / 2
        for i in range(n):
            y0 = -S + i * S / n; z1 = zb + (i + 1) * (H / 2) / n
            p.box(0.1, S - 0.1, y0, y0 + S / n, zb if half == 'lo' else zb - 0.12, z1, WOOD, tex=TX('a11', size=1.3))
        for x in (0.07, S - 0.07):          # sloped stringers + hand rail on posts
            p.rod((x, -S, zb), (x, 0, zb + H / 2), 0.04, WOOD_D, ink=True, seg=4)
        x = S - 0.07
        p.rod((x, -S, zb + 0.85), (x, 0, zb + H / 2 + 0.85), 0.025, WOOD_D, ink=True, seg=4)
        for y, z in ((-S + 0.05, zb + H / 10), (-0.05, zb + H / 2)):
            p.rod((x, y, z), (x, y, z + 0.85), 0.02, WOOD_D, ink=True, seg=4)
    return f

def ranch_sign(p):
    w, h, z = 1.2, 0.3, 1.1; x0 = (S - w) / 2; y = -S / 2
    for x in (x0 + 0.05, x0 + w - 0.12):
        p.box(x, x + 0.07, y - 0.035, y + 0.035, 0, z + h + 0.1, WOOD_D)
    p.box(x0, x0 + w, y - 0.03, y + 0.03, z, z + h, WOOD)
    p.decal((x0 + 0.02, y - 0.032, z + 0.015), (1, 0, 0), (0, 0, 1), w - 0.04, h - 0.03, 'decal_b5_ranch_sign.png')

# ---------------------------------------------------------------- furniture
def legs(p, x0, x1, y0, y1, h, rgb, t=0.05):
    for (x, y) in ((x0, y0), (x1 - t, y0), (x0, y1 - t), (x1 - t, y1 - t)):
        p.box(x, x + t, y, y + t, 0, h, rgb)

def desk(opened=False):
    def f(p):
        x0, x1, y0, y1, h = 0.12, S - 0.12, -S + 0.35, -0.25, 0.76
        p.box(x0, x1, y0, y1, h - 0.05, h, WOOD_D, tex=TX('a11', size=1.3))
        p.box(x0, x0 + 0.42, y0, y1, 0, h - 0.05, WOOD, tex=TX('a11', size=1.3))     # drawer pedestal (west)
        p.box(x1 - 0.42, x1, y0, y1, 0, h - 0.05, WOOD, tex=TX('a11', size=1.3))     # (east)
        for z in (0.08, 0.3, 0.52):
            p.box(x1 - 0.38, x1 - 0.04, y0 - 0.01, y0, z, z + 0.18, WOOD_D)
            p.box(x1 - 0.24, x1 - 0.18, y0 - 0.025, y0 - 0.01, z + 0.08, z + 0.1, (0.85, 0.7, 0.2))
        if opened:      # top drawer pulled out, papers inside
            p.box(x1 - 0.38, x1 - 0.04, y0 - 0.38, y0, 0.52, 0.68, WOOD_D)
            p.box(x1 - 0.35, x1 - 0.07, y0 - 0.35, y0 - 0.03, 0.66, 0.665, (0.95, 0.93, 0.85))
        p.decal((x0 + 0.5, y0 + 0.08, h + 0.002), (1, 0, 0), (0, 1, 0), 0.32, 0.32, 'decal_b7c_memo.png')
        p.box(x0 + 0.1, x0 + 0.38, y1 - 0.3, y1 - 0.06, h, h + 0.1, DARK)               # phone
        p.box(x0 + 0.12, x0 + 0.36, y1 - 0.28, y1 - 0.08, h + 0.1, h + 0.13, (0.25, 0.25, 0.27))
    return f

def office_chair(p):
    c = S / 2
    p.cyl(c, -c, 0, 0.42, 0.04, DARK, seg=8)
    p.cyl(c, -c, 0, 0.04, 0.28, DARK, seg=5)
    p.box(c - 0.26, c + 0.26, -c - 0.24, -c + 0.24, 0.42, 0.52, (0.45, 0.28, 0.15))
    p.box(c - 0.26, c + 0.26, -c + 0.18, -c + 0.28, 0.52, 1.05, (0.45, 0.28, 0.15))

def safe(opened=False):
    def f(p):
        x0, x1, y0, y1, h = 0.3, 1.0, -0.95, -0.3, 1.05
        p.box(x0, x1, y0, y1, 0.06, h, (0.30, 0.34, 0.32))
        for (x, y) in ((x0, y0), (x1 - 0.08, y0), (x0, y1 - 0.08), (x1 - 0.08, y1 - 0.08)):
            p.box(x, x + 0.08, y, y + 0.08, 0, 0.06, DARK)
        if not opened:
            p.box(x0 + 0.06, x1 - 0.06, y0 - 0.02, y0, 0.12, h - 0.06, (0.36, 0.40, 0.38))
            p.rod((x0 + 0.35, y0 - 0.02, 0.7), (x0 + 0.35, y0 - 0.07, 0.7), 0.075, (0.85, 0.82, 0.70), ink=True, seg=10)
            p.box(x0 + 0.45, x0 + 0.58, y0 - 0.06, y0 - 0.02, 0.45, 0.5, (0.85, 0.82, 0.70))
            p.box(x0 + 0.1, x0 + 0.3, y0 - 0.025, y0 - 0.02, 0.9, 0.96, (0.85, 0.7, 0.2))   # brand plate
        else:           # door swung open to the west, inside shelves bare (ledger taken)
            p.box(x0 + 0.06, x1 - 0.06, y0 - 0.005, y0, 0.12, h - 0.06, (0.12, 0.13, 0.13))
            p.box(x0 + 0.08, x1 - 0.08, y0 + 0.01, y1 - 0.06, 0.55, 0.58, (0.30, 0.34, 0.32))
            p.box(x0 - 0.62, x0, y0 - 0.06, y0, 0.12, h - 0.06, (0.36, 0.40, 0.38))
            p.rod((x0 - 0.3, y0 - 0.06, 0.7), (x0 - 0.3, y0 - 0.11, 0.7), 0.075, (0.85, 0.82, 0.70), ink=True, seg=10)
    return f

def file_cab(p):
    x0, x1, y0, y1 = 0.35, 0.95, -0.95, -0.35
    p.box(x0, x1, y0, y1, 0, 1.3, (0.55, 0.58, 0.52))
    for z in (0.08, 0.5, 0.92):
        p.box(x0 + 0.05, x1 - 0.05, y0 - 0.015, y0, z, z + 0.36, (0.62, 0.65, 0.58))
        p.box(x0 + 0.22, x1 - 0.22, y0 - 0.035, y0 - 0.015, z + 0.24, z + 0.28, STEEL)

def bed(p):
    x0, x1, y0, y1 = 0.1, S - 0.1, -S + 0.05, -0.05
    p.box(x0, x1, y0, y1, 0.22, 0.42, MATT)
    p.box(x0 - 0.01, x1 + 0.01, y0 - 0.01, y1 - 0.45, 0.4, 0.46, BLANKET)
    p.box(x0 + 0.12, x1 - 0.12, y1 - 0.4, y1 - 0.1, 0.42, 0.52, WHITE)
    p.box(x0, x1, y1 - 0.08, y1, 0, 1.0, WOOD_D)                      # headboard (north)
    legs(p, x0, x1, y0, y1, 0.22, WOOD_D, 0.07)

def bunk(p):
    x0, x1, y0, y1 = 0.25, 1.05, -S + 0.05, -0.05
    for (x, y) in ((x0, y0), (x1 - 0.06, y0), (x0, y1 - 0.06), (x1 - 0.06, y1 - 0.06)):
        p.box(x, x + 0.06, y, y + 0.06, 0, 1.75, (0.35, 0.38, 0.30))
    for z in (0.3, 1.2):
        p.box(x0, x1, y0, y1, z, z + 0.16, MATT)
        p.box(x0 - 0.01, x1 + 0.01, y0 - 0.01, y1 - 0.4, z + 0.14, z + 0.2, (0.36, 0.40, 0.24))
        p.box(x0 + 0.1, x1 - 0.1, y1 - 0.35, y1 - 0.08, z + 0.16, z + 0.24, WHITE)
    for z in [0.5 + 0.25 * i for i in range(3)]:
        p.box(x1 - 0.05, x1, y0 + 0.3, y0 + 0.34, z, z + 0.03, (0.35, 0.38, 0.30))

def footlocker(opened=False):
    def f(p):
        x0, x1, y0, y1, h = 0.22, 1.08, -0.95, -0.45, 0.42
        p.box(x0, x1, y0, y1, 0, h, OLIVE)
        for x in (x0 + 0.04, x1 - 0.1):
            p.box(x, x + 0.06, y0 - 0.015, y1 + 0.015, 0, h + 0.005, (0.30, 0.31, 0.18))
        if not opened:
            p.box(x0 - 0.01, x1 + 0.01, y0 - 0.01, y1 + 0.01, h - 0.02, h + 0.03, (0.36, 0.38, 0.21))
            p.box((x0 + x1) / 2 - 0.05, (x0 + x1) / 2 + 0.05, y0 - 0.03, y0 - 0.01, h - 0.12, h - 0.02, STEEL)
            p.box(x0 + 0.25, x0 + 0.6, y0 - 0.012, y0 - 0.01, 0.12, 0.24, WHITE)       # stencil plate
        else:
            p.box(x0 + 0.03, x1 - 0.03, y0 + 0.03, y1 - 0.03, h - 0.06, h - 0.05, (0.15, 0.15, 0.12))
            p.box(x0 - 0.01, x1 + 0.01, y1, y1 + 0.05, h, h + 0.48, (0.36, 0.38, 0.21))   # lid up
    return f

def counter(kind='plain'):
    def f(p):
        x0, x1, y0, y1, h = 0.0, S, -0.75, -0.08, 0.9
        p.box(x0 + 0.02, x1 - 0.02, y0 + 0.05, y1, 0.08, h - 0.04, (0.62, 0.48, 0.30), tex=TX('a11', size=1.3))
        p.box(x0 + 0.04, x1 - 0.04, y0 + 0.06, y1 - 0.02, 0, 0.08, DARK)
        p.box(x0, x1, y0, y1, h - 0.04, h, (0.86, 0.80, 0.55))
        for a in (0.06, S / 2 + 0.03):        # cupboard doors
            p.box(a, a + S / 2 - 0.09, y0 + 0.035, y0 + 0.05, 0.12, h - 0.25, (0.70, 0.55, 0.34))
        dz = h - 0.21
        if kind in ('drawer', 'drawer_open'):
            d = 0.3 if kind == 'drawer_open' else 0.0
            p.box(0.1, S - 0.1, y0 + 0.035 - d, y0 + 0.05 + (0.35 if d else 0) - d, dz, dz + 0.15, (0.70, 0.55, 0.34))
            p.box(S / 2 - 0.1, S / 2 + 0.1, y0 + 0.02 - d, y0 + 0.035 - d, dz + 0.06, dz + 0.09, STEEL)
            if d: p.box(0.18, S - 0.18, y0 - d + 0.08, y0 + 0.3 - d, dz + 0.14, dz + 0.145, (0.95, 0.93, 0.85))
        if kind == 'plain':
            p.box(0.25, 0.75, y0 + 0.15, y1 - 0.15, h, h + 0.02, (0.75, 0.76, 0.78))      # sink
            p.box(0.27, 0.73, y0 + 0.17, y1 - 0.17, h + 0.005, h + 0.025, (0.45, 0.48, 0.5))
            p.rod((0.5, y1 - 0.1, h), (0.5, y1 - 0.25, h + 0.25), 0.015, STEEL, ink=True, seg=4)
    return f

def stove(p):
    x0, x1, y0, y1, h = 0.2, 1.1, -0.8, -0.1, 0.9
    p.box(x0, x1, y0, y1, 0, h, WHITE)
    p.box(x0 + 0.08, x1 - 0.08, y0 - 0.01, y0, 0.15, 0.62, (0.25, 0.25, 0.27))
    p.box(x0 + 0.2, x1 - 0.2, y0 - 0.04, y0 - 0.01, 0.66, 0.69, STEEL)
    for (cx, cy) in ((0.42, -0.6), (0.88, -0.6), (0.42, -0.3), (0.88, -0.3)):
        p.cyl(cx, cy, h, h + 0.02, 0.12, DARK, seg=10)
    p.box(x0, x1, y1 - 0.06, y1, h, h + 0.25, WHITE)

def fridge(p):
    x0, x1, y0, y1 = 0.3, 1.0, -0.85, -0.12
    p.box(x0, x1, y0, y1, 0, 1.8, (0.82, 0.78, 0.55))           # harvest gold, 1970s
    p.box(x0 + 0.02, x1 - 0.02, y0 - 0.01, y0, 1.18, 1.18 + 0.02, DARK)
    for (z0, z1) in ((0.3, 1.0), (1.3, 1.65)):
        p.box(x1 - 0.12, x1 - 0.08, y0 - 0.05, y0 - 0.01, z0, z1, STEEL)

def ktable(p):
    x0, x1, y0, y1, h = 0.15, S - 0.15, -S + 0.15, -0.15, 0.76
    p.box(x0, x1, y0, y1, h - 0.04, h, (0.86, 0.80, 0.55))
    p.box(x0, x1, y0, y1, h - 0.07, h - 0.04, STEEL)
    legs(p, x0 + 0.05, x1 - 0.05, y0 + 0.05, y1 - 0.05, h - 0.07, STEEL, 0.04)
    p.cyl(S / 2 - 0.2, -S / 2, h, h + 0.08, 0.05, WHITE, seg=8)      # mug
    p.box(S / 2, S / 2 + 0.3, -S / 2 - 0.1, -S / 2 + 0.12, h, h + 0.02, (0.95, 0.93, 0.85))   # newspaper

def chair(p):
    c = S / 2; s = 0.22
    p.box(c - s, c + s, -c - s, -c + s, 0.44, 0.49, WOOD)
    legs(p, c - s, c + s, -c - s, -c + s, 0.44, WOOD_D, 0.04)
    p.box(c - s, c + s, -c + s - 0.05, -c + s, 0.49, 0.95, WOOD_D)
    p.box(c - s, c + s, -c + s - 0.06, -c + s + 0.01, 0.8, 0.92, WOOD)

def sofa(p):
    x0, x1, y0, y1 = 0.05, S - 0.05, -0.95, -0.15
    p.box(x0, x1, y0, y1, 0.08, 0.42, SOFA)
    p.box(x0, x1, y1 - 0.2, y1, 0.42, 0.85, SOFA)
    for x in (x0, x1 - 0.16): p.box(x, x + 0.16, y0, y1, 0.42, 0.62, SOFA)
    for x in (x0 + 0.17, S / 2 + 0.01): p.box(x, x + S / 2 - 0.23, y0 + 0.03, y1 - 0.22, 0.42, 0.5, (0.80, 0.50, 0.22))
    legs(p, x0 + 0.05, x1 - 0.05, y0 + 0.05, y1 - 0.05, 0.08, WOOD_D, 0.05)

def tv(p):
    x0, x1, y0, y1 = 0.15, 1.15, -0.85, -0.25
    p.box(x0, x1, y0, y1, 0.0, 0.75, WOOD, tex=TX('a11', size=1.3))     # console cabinet
    p.box(x0 + 0.08, x0 + 0.65, y0 - 0.01, y0, 0.18, 0.62, (0.25, 0.30, 0.32))
    p.box(x0 + 0.12, x0 + 0.61, y0 - 0.015, y0 - 0.01, 0.22, 0.58, (0.35, 0.45, 0.48))
    for z in (0.5, 0.36): p.cyl(x0 + 0.82, y0 - 0.0, z, z + 0.001, 0.05, DARK, seg=8)
    p.rod((x0 + 0.82, y0 - 0.01, 0.5), (x0 + 0.82, y0 - 0.05, 0.5), 0.045, (0.85, 0.7, 0.2), seg=8)
    p.rod((x0 + 0.82, y0 - 0.01, 0.34), (x0 + 0.82, y0 - 0.05, 0.34), 0.045, (0.85, 0.7, 0.2), seg=8)
    p.rod((S / 2, -0.55, 0.75), (S / 2 - 0.3, -0.5, 1.2), 0.012, STEEL, ink=True, seg=4)       # rabbit ears
    p.rod((S / 2, -0.55, 0.75), (S / 2 + 0.3, -0.6, 1.2), 0.012, STEEL, ink=True, seg=4)

def gun_rack(p):
    x0, x1, y0, y1 = 0.15, 1.15, -0.4, -0.08
    p.box(x0, x1, y1 - 0.06, y1, 0.3, 1.7, WOOD_D, tex=TX('a11', size=1.3))    # back board against the north wall
    p.box(x0, x1, y0, y1, 0.3, 0.42, WOOD, tex=TX('a11', size=1.3))           # butt shelf
    p.box(x0, x1, y0 + 0.1, y1, 1.4, 1.47, WOOD, tex=TX('a11', size=1.3))      # barrel rest
    for i, x in enumerate((x0 + 0.2, x0 + 0.5, x0 + 0.8)):
        p.box(x - 0.04, x + 0.04, y0 + 0.1, y0 + 0.2, 0.42, 0.75, BARK)                   # stock
        p.rod((x, y0 + 0.15, 0.75), (x, y1 - 0.12, 1.55), 0.018, DARK, ink=True, seg=4)  # barrel

KIT = [
    ('floor_wood', False, tfloor('a11', 0, 0, size=1.3, rot=math.pi / 2)),
    ('floor_wood_b', False, tfloor('a11', .5, .3, size=1.3, rot=math.pi / 2)),
    ('floor_lino', False, lino),
    ('floor_porch', False, tfloor('a11', .2, .7, size=1.3, tint=(0.85, 0.85, 0.85))),
    ('floor_bunk', False, tfloor('a7', .3, .6)),
    ('roof_house', False, roof),
    ('hwall_w', True, wall('brick', 'w')), ('hwall_n', True, wall('brick', 'n')),
    ('hwin_w', True, wall('brick', 'w', 'window')), ('hwin_n', True, wall('brick', 'n', 'window')),
    ('hdoor_w', True, wall('brick', 'w', 'door')), ('hdoor_w_open', True, wall('brick', 'w', 'open')),
    ('hdoor_n', True, wall('brick', 'n', 'door')), ('hdoor_n_open', True, wall('brick', 'n', 'open')),
    ('bwall_w', True, wall('siding', 'w')), ('bwall_n', True, wall('siding', 'n')),
    ('bwin_w', True, wall('siding', 'w', 'window')), ('bwin_n', True, wall('siding', 'n', 'window')),
    ('bdoor_w', True, wall('siding', 'w', 'door')), ('bdoor_w_open', True, wall('siding', 'w', 'open')),
    ('bdoor_n', True, wall('siding', 'n', 'door')), ('bdoor_n_open', True, wall('siding', 'n', 'open')),
    ('iwall_w', True, wall('plaster', 'w')), ('iwall_n', True, wall('plaster', 'n')),
    ('idoor_w', True, wall('plaster', 'w', 'door')), ('idoor_w_open', True, wall('plaster', 'w', 'open')),
    ('idoor_n', True, wall('plaster', 'n', 'door')), ('idoor_n_open', True, wall('plaster', 'n', 'open')),
    ('porch_post', True, porch_post), ('porch_rail_w', True, porch_rail('w')), ('porch_rail_n', True, porch_rail('n')),
    ('stair_lo', True, stairs('lo')), ('stair_hi', True, stairs('hi')),
    ('ranch_sign', True, ranch_sign),
    ('desk', True, desk()), ('desk_open', True, desk(True)), ('office_chair', True, office_chair),
    ('safe', True, safe()), ('safe_open', True, safe(True)), ('file_cab', True, file_cab),
    ('bed', True, bed), ('bunk', True, bunk),
    ('footlocker', True, footlocker()), ('footlocker_open', True, footlocker(True)),
    ('counter', True, counter()), ('counter_drawer', True, counter('drawer')), ('counter_drawer_open', True, counter('drawer_open')),
    ('stove', True, stove), ('fridge', True, fridge), ('ktable', True, ktable), ('chair', True, chair),
    ('sofa', True, sofa), ('tv', True, tv), ('gun_rack', True, gun_rack),
]

OPEN = dict(loft=[0] * 12, walk=0, los=0, block=0, door=0)
def wall_pair(prefix, wt, wn, wiw, win, dw, dn):
    return {
        prefix + 'wall_w': ('URBAN', wt, {}), prefix + 'wall_n': ('URBAN', wn, {}),
        prefix + 'win_w': ('URBAN', wiw, {}), prefix + 'win_n': ('URBAN', win, {}),
        prefix + 'door_w': ('URBAN', dw, dict(alt=prefix + 'door_w_open')), prefix + 'door_w_open': ('URBAN', dw, OPEN),
        prefix + 'door_n': ('URBAN', dn, dict(alt=prefix + 'door_n_open')), prefix + 'door_n_open': ('URBAN', dn, OPEN),
    }
MCDSPEC = {
    'floor_wood': ('BARN', 19, {}), 'floor_wood_b': ('BARN', 19, {}), 'floor_lino': ('BARN', 19, {}),
    'floor_porch': ('BARN', 19, {}), 'floor_bunk': ('BARN', 19, {}), 'roof_house': ('BARN', 19, {}),
    'porch_post': ('FRNITURE', 10, dict(walk=255)),
    'porch_rail_w': ('CULTIVAT', 18, dict(loft=[15] * 6 + [0] * 6)), 'porch_rail_n': ('CULTIVAT', 19, dict(loft=[16] * 6 + [0] * 6)),
    'stair_lo': ('URBAN', 21, {}), 'stair_hi': ('URBAN', 22, {}),
    'ranch_sign': ('FRNITURE', 10, {}),
    'desk': ('FRNITURE', 0, dict(alt='desk_open')), 'desk_open': ('FRNITURE', 0, {}),
    'office_chair': ('FRNITURE', 2, {}),
    'safe': ('FRNITURE', 23, dict(alt='safe_open', armor=80)), 'safe_open': ('FRNITURE', 23, dict(armor=80)),
    'file_cab': ('FRNITURE', 19, {}),
    'bed': ('FRNITURE', 21, {}), 'bunk': ('FRNITURE', 22, {}),
    'footlocker': ('FRNITURE', 24, dict(alt='footlocker_open')), 'footlocker_open': ('FRNITURE', 24, {}),
    'counter': ('FRNITURE', 16, {}), 'counter_drawer': ('FRNITURE', 16, dict(alt='counter_drawer_open')),
    'counter_drawer_open': ('FRNITURE', 16, {}),
    'stove': ('FRNITURE', 17, {}), 'fridge': ('FRNITURE', 18, {}), 'ktable': ('FRNITURE', 0, {}), 'chair': ('FRNITURE', 3, {}),
    'sofa': ('FRNITURE', 8, {}), 'tv': ('FRNITURE', 5, {}), 'gun_rack': ('FRNITURE', 6, {}),
}
MCDSPEC.update(wall_pair('h', 32, 31, 34, 33, 27, 28))     # brick-strength house walls (armour 30), doors 27/28
MCDSPEC.update(wall_pair('b', 8, 7, 10, 9, 29, 30))        # wooden bunkhouse walls (armour 14)
MCDSPEC.update({k.replace('iwin', 'x'): v for k, v in wall_pair('i', 15, 14, 15, 14, 29, 30).items() if 'win' not in k})
