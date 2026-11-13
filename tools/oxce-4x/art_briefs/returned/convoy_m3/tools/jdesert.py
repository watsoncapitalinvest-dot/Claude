"""JDESERT: open desert for the convoy raid (BUILD spec 13 Nov). Named JDESERT, not DESERT: vanilla has a DESERT terrain.
Ground on this map sits at level 1; level 0 under it is filled with EARTH blocks, so the dry wash can be sunk one level.
Index = MCD index = frame."""
import math, random
from kitlib import *
SET = 'JDESERT'
SAND = (0.88, 0.76, 0.54)
DIRT = (0.74, 0.58, 0.40)
REDROCK = (0.72, 0.48, 0.34)
REDROCK_D = (0.58, 0.36, 0.25)

def fl(name, ox=0, oy=0, rot=0, tint=(1, 1, 1), size=2.6):
    def f(p):
        p.tint = tint; p.ground((1, 1, 1), tex=TX(name, ox, oy, size=size, rot=rot)); p.tint = (1, 1, 1)
    return f
def rockfloor(seed):
    def f(p):
        fl('a1', 0.1 * seed, 0.3 * seed, tint=(0.9, 0.72, 0.6))(p)
        rnd = random.Random(seed)
        for i in range(4):
            p.blob(rnd.uniform(.2, S - .2), -rnd.uniform(.2, S - .2), 0.0, rnd.uniform(.12, .25), rnd.uniform(.1, .2), 0.05,
                   REDROCK, sub=1, rough=0.25, ink=False, seed=seed * 10 + i)
    return f

# ---------------------------------------------------------------- blocks (full cell, one level; stack for 2)
def block(kind, seed):
    """earth: packed dirt (level-0 fill, wash banks). rock: red rock ridge with strata and ledges."""
    def f(p):
        rnd = random.Random(seed)
        if kind == 'earth':
            p.box(0, S, -S, 0, 0, H, (0.70, 0.55, 0.38))
            for i in range(10):                  # clods and stones on the two faces the camera sees
                if i % 2: x, y = rnd.uniform(.1, S - .1), -S - 0.01
                else: x, y = S + 0.01, -rnd.uniform(.1, S - .1)
                p.blob(x, y, rnd.uniform(.15, H - .15), rnd.uniform(.06, .13), rnd.uniform(.06, .13), rnd.uniform(.05, .1),
                       (0.60, 0.46, 0.32) if i % 3 else ROCK, sub=1, rough=0.25, ink=False, seed=seed * 13 + i)
            p.box(0, S, -S, 0, H - 0.02, H, (0.80, 0.68, 0.50), ink=False)           # sun-bleached top
            return
        p.box(0, S, -S, 0, 0, H, REDROCK)
        for z in (0.45, 0.95, 1.4):
            zz = z + rnd.uniform(-.06, .06)
            p.box(0, S, -S - 0.01, -S + 0.0, zz, zz + 0.05, REDROCK_D, ink=False)
            p.box(S, S + 0.01, -S, 0, zz + 0.03, zz + 0.08, REDROCK_D, ink=False)
        for i in range(3):
            p.blob(rnd.uniform(.2, S - .2), -S + rnd.uniform(-0.02, 0.1), rnd.uniform(.3, 1.6), rnd.uniform(.2, .35), 0.14,
                   rnd.uniform(.12, .2), REDROCK, sub=1, rough=0.25, seed=seed * 7 + i)
    return f
def headwall(p):                        # concrete headwall face where the culvert opens into the wash
    block('earth', 77)(p)
    p.box(-0.02, S + 0.02, -S - 0.08, -S + 0.2, 0, 0.9, CONCRETE)

def ramp(direction, half):
    """smooth dirt slope climbing toward `direction` (n, s, e, w). lo: 0 -> H/2, hi: H/2 -> H.
    Pair with terrain level -8 / -16 (stair records), like the ranch stairs."""
    import bmesh
    def f(p):
        zs, ze = (0.0, H / 2) if half == 'lo' else (H / 2, H)
        prof = [(0, 0), (S, 0), (S, ze), (0, zs)]           # (t along the climb, z)
        def P(t, c, z):
            if direction == 'n': return (c, -S + t, z)
            if direction == 's': return (c, -t, z)
            if direction == 'e': return (t, -c, z)
            return (S - t, -c, z)
        bm, layer = p.bm, p.col
        A = [[bm.verts.new(P(t, c, z)) for (t, z) in prof if not (half == 'lo' and t == 0 and z == 0 and False)] for c in (0, S)]
        fs = []
        for i in range(4):
            j = (i + 1) % 4
            if (A[0][i].co - A[0][j].co).length < 1e-6: continue
            fs.append(bm.faces.new((A[0][i], A[0][j], A[1][j], A[1][i])))
        fs.append(bm.faces.new(A[0][::-1])); fs.append(bm.faces.new(A[1]))
        bmesh.ops.recalc_face_normals(bm, faces=fs); bm.normal_update()
        p.tint = (0.85, 0.68, 0.5); p._paint(bm, layer, fs, DIRT, 0, TX('a1', 0.2, 0.1)); p.tint = (1, 1, 1)
        rnd = random.Random(hash((direction, half)) % 1000)
        for i in range(4):                                   # a few stones on the slope
            t, c = rnd.uniform(.2, S - .2), rnd.uniform(.2, S - .2)
            z = zs + (ze - zs) * t / S
            x, y, _ = P(t, c, z); p.blob(x, y, z, 0.1, 0.09, 0.07, ROCK, sub=1, rough=0.2, seed=i + 3)
    return f

# ---------------------------------------------------------------- vegetation and rocks
def scrub(seed):                        # creosote / brittlebush: no cover
    def f(p):
        rnd = random.Random(seed)
        for i in range(rnd.randint(2, 3)):
            cx, cy = rnd.uniform(.3, S - .3), -rnd.uniform(.3, S - .3)
            for k in range(5):
                p.blob(cx + rnd.uniform(-.12, .12), cy + rnd.uniform(-.12, .12), rnd.uniform(.1, .3), rnd.uniform(.1, .16),
                       rnd.uniform(.1, .16), rnd.uniform(.08, .12), (0.48 + rnd.uniform(-.05, .05), 0.50, 0.26), seed=seed * 9 + i * 5 + k)
    return f
def cactus(seed):                       # saguaro-style column with arms: thin cover
    def f(p):
        rnd = random.Random(seed); cx, cy = S / 2 + rnd.uniform(-.1, .1), -S / 2 + rnd.uniform(-.1, .1)
        G = (0.36, 0.52, 0.30)
        h = rnd.uniform(1.5, 1.85)
        p.cyl(cx, cy, 0, h, 0.13, G, seg=10); p.blob(cx, cy, h, 0.13, 0.13, 0.1, G, sub=1, rough=0)
        for (dx, dy, z0, z1) in ((0.28, 0.0, 0.7, 1.35), (-0.25, 0.05, 0.9, 1.5))[:1 + seed % 2]:
            p.rod((cx, cy, z0), (cx + dx, cy + dy, z0), 0.08, G, ink=True, seg=8)
            p.cyl(cx + dx, cy + dy, z0 - 0.05, z1, 0.08, G, seg=8); p.blob(cx + dx, cy + dy, z1, 0.08, 0.08, 0.06, G, sub=1, rough=0)
        for z in (0.3, 0.8, 1.2): p.cyl(cx, cy, z, z + 0.02, 0.135, (0.30, 0.44, 0.24), seg=10)
    return f
def smallrocks(seed):                   # half cover
    def f(p):
        rnd = random.Random(seed)
        p.blob(S / 2 + rnd.uniform(-.1, .1), -S / 2, 0.25, 0.5, 0.42, 0.42, REDROCK, sub=2, rough=0.25, seed=seed)
        p.blob(S / 2 + 0.35, -S / 2 + 0.25, 0.12, 0.22, 0.2, 0.2, ROCK, sub=1, rough=0.2, seed=seed + 1)
    return f
def boulder(seed):                      # big boulder, about one level: full cover
    def f(p):
        p.blob(S / 2, -S / 2, 0.75, 0.66, 0.62, 0.85, REDROCK, sub=2, rough=0.22, seed=seed)
        p.blob(S / 2 + 0.3, -S / 2 - 0.3, 0.2, 0.3, 0.28, 0.25, REDROCK_D, sub=1, rough=0.2, seed=seed + 2)
    return f
def deadtree(p):
    for (a, b, r) in (((0.65, -0.65, 0), (0.6, -0.6, 1.1), 0.07), ((0.6, -0.6, 0.9), (0.25, -0.35, 1.45), 0.04),
                      ((0.62, -0.62, 1.0), (1.0, -0.8, 1.6), 0.04), ((0.6, -0.6, 1.1), (0.7, -0.3, 1.8), 0.03)):
        p.rod(a, b, r, (0.55, 0.50, 0.44), ink=True, seg=6)

KIT = [
    ('sand_a', False, fl('a4', 0, 0)), ('sand_b', False, fl('a4', .5, .3)), ('sand_c', False, fl('a4', .2, .7, rot=math.pi / 2)),
    ('dirt_a', False, fl('a1', 0, 0, tint=(0.88, 0.74, 0.58))), ('dirt_b', False, fl('a1', .4, .6, tint=(0.88, 0.74, 0.58))),
    ('gravel_a', False, fl('a3', 0, 0, tint=(0.92, 0.88, 0.82))), ('gravel_b', False, fl('a3', .5, .5, tint=(0.92, 0.88, 0.82))),
    ('rockfloor_a', False, rockfloor(1)), ('rockfloor_b', False, rockfloor(2)), ('rockfloor_c', False, rockfloor(3)),
    ('wash_a', False, fl('a4', .3, .1, tint=(0.92, 0.88, 0.8))), ('wash_b', False, fl('a4', .7, .4, tint=(0.92, 0.88, 0.8))),
    ('earth_a', True, block('earth', 1)), ('earth_b', True, block('earth', 2)),
    ('rock_a', True, block('rock', 3)), ('rock_b', True, block('rock', 4)), ('rock_c', True, block('rock', 5)),
    ('headwall', True, headwall),
    ('ramp_n_lo', True, ramp('n', 'lo')), ('ramp_n_hi', True, ramp('n', 'hi')),
    ('ramp_s_lo', True, ramp('s', 'lo')), ('ramp_s_hi', True, ramp('s', 'hi')),
    ('scrub_a', True, scrub(1)), ('scrub_b', True, scrub(2)), ('scrub_c', True, scrub(3)),
    ('cactus_a', True, cactus(1)), ('cactus_b', True, cactus(2)),
    ('rocks_a', True, smallrocks(11)), ('rocks_b', True, smallrocks(12)),
    ('boulder_a', True, boulder(21)), ('boulder_b', True, boulder(22)), ('deadtree', True, deadtree),
]
def spot(kind):                 # John 01:09: clue spots and reward spots shown as blue tiles
    def f(p):
        p.box(0, S, -S, 0, -0.01, 0.0, (0.16, 0.42, 0.92), ink=False)
        p.box(0.06, S - 0.06, -S + 0.06, -0.06, 0.0, 0.004, (0.30, 0.58, 1.0), ink=False)
        c = (S / 2, -S / 2)
        if kind == 'clue':             # white ring with a dot (look here)
            for k in range(16):
                a0 = k * 2 * math.pi / 16
                p.box(c[0] + 0.36 * math.cos(a0) - 0.04, c[0] + 0.36 * math.cos(a0) + 0.04, c[1] + 0.36 * math.sin(a0) - 0.04, c[1] + 0.36 * math.sin(a0) + 0.04, 0.004, 0.008, (0.97, 0.97, 1.0), ink=False)
            p.box(c[0] - 0.08, c[0] + 0.08, c[1] - 0.08, c[1] + 0.08, 0.004, 0.008, (0.97, 0.97, 1.0), ink=False)
        else:                          # white star (reward spot)
            for k in range(5):
                a = math.pi / 2 + k * 2 * math.pi / 5
                for t in range(6):
                    rr = 0.42 * (1 - t / 6)
                    x, y = c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)
                    w = 0.03 + 0.05 * t / 6
                    p.box(x - w, x + w, y - w, y + w, 0.004, 0.008, (0.97, 0.97, 1.0), ink=False)
            p.box(c[0] - 0.13, c[0] + 0.13, c[1] - 0.13, c[1] + 0.13, 0.004, 0.008, (0.97, 0.97, 1.0), ink=False)
    return f
KIT += [('spot_clue', False, spot('clue')), ('spot_reward', False, spot('reward'))]
FULL = dict(loft=[6] * 12, walk=255, los=1, armor=255, block=1)
MCDSPEC = {}
for n, _, _ in KIT:
    if n.startswith(('sand', 'dirt', 'gravel', 'rockfloor', 'wash')): MCDSPEC[n] = ('DESERT', 21, {})
MCDSPEC['spot_clue'] = ('DESERT', 21, {}); MCDSPEC['spot_reward'] = ('DESERT', 21, {})
for n in ('earth_a', 'earth_b', 'rock_a', 'rock_b', 'rock_c', 'headwall'): MCDSPEC[n] = ('MOUNT', 2, dict(FULL, type=3))
for d in 'ns':
    MCDSPEC['ramp_%s_lo' % d] = ('URBAN', 21, {}); MCDSPEC['ramp_%s_hi' % d] = ('URBAN', 22, {})
MCDSPEC.update({
    'scrub_a': ('DESERT', 16, dict(loft=[0] * 12, walk=4, los=0)), 'scrub_b': ('DESERT', 16, dict(loft=[0] * 12, walk=4, los=0)),
    'scrub_c': ('DESERT', 16, dict(loft=[0] * 12, walk=4, los=0)),
    'cactus_a': ('FRNITURE', 10, dict(walk=255, loft=[25] * 9 + [0] * 3)), 'cactus_b': ('FRNITURE', 10, dict(walk=255, loft=[25] * 9 + [0] * 3)),
    'rocks_a': ('FRNITURE', 17, dict(loft=[33] * 5 + [0] * 7, walk=255, armor=80)), 'rocks_b': ('FRNITURE', 17, dict(loft=[33] * 5 + [0] * 7, walk=255, armor=80)),
    'boulder_a': ('FRNITURE', 17, dict(loft=[33] * 10 + [0] * 2, walk=255, armor=120, los=1)),
    'boulder_b': ('FRNITURE', 17, dict(loft=[33] * 10 + [0] * 2, walk=255, armor=120, los=1)),
    'deadtree': ('FRNITURE', 10, dict(walk=255, loft=[25] * 10 + [0] * 2)),
})
