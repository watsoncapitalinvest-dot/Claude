"""SMUGGLER: twin-engine smuggling plane, 1970s pickup, river skiff (big objects cut into cells), boat landing.
Big objects: build_<obj>(p) models the whole thing in world metres on an nx x ny grid (cell (i, j): x i*S.., y -j*S..).
render_smuggler.py renders them with kitbig.cut_cells and writes smuggler_cells.json; KIT/MCDSPEC are read from it."""
import math, json, os, random
from mathutils import Vector
from kitlib import *
SET = 'SMUGGLR'
HERE = os.path.dirname(os.path.abspath(__file__))
PWHITE = (0.92, 0.92, 0.90); PRED = (0.78, 0.16, 0.12); PBLUE = (0.16, 0.30, 0.62)
GLASS = (0.20, 0.27, 0.34); DARK = (0.16, 0.16, 0.17); TYRE = (0.13, 0.13, 0.13)
TRUCK = (0.42, 0.55, 0.62); TRUCK_D = (0.30, 0.40, 0.46); CHROME = (0.80, 0.82, 0.84)
BOAT = (0.36, 0.45, 0.32); BOAT_IN = (0.62, 0.58, 0.48)

def wheel(p, x, y, z, r, w, axis='y'):
    """tyre as a short rod across `axis`, with a hub."""
    if axis == 'y':
        p.rod((x, y - w / 2, z), (x, y + w / 2, z), r, TYRE, ink=True, seg=10)
        p.rod((x, y - w / 2 - 0.01, z), (x, y - w / 2 - 0.02, z), r * 0.5, CHROME, ink=True, seg=8)
        p.rod((x, y + w / 2 + 0.01, z), (x, y + w / 2 + 0.02, z), r * 0.5, CHROME, ink=True, seg=8)

# ---------------------------------------------------------------- plane (nose east), 8 x 9 cells, 2 levels
PLANE = (8, 9, 2)
def build_plane(p):
    cy = -4.5 * S                      # centreline
    def sym(y): return (cy - y, cy + y)
    # fuselage: cabin box + stepped tail cone + rounded nose
    p.box(1.9, 7.4, cy - 0.72, cy + 0.72, 0.65, 2.0, PWHITE)
    for k, (x0, x1, hw, z0, z1) in enumerate(((1.2, 1.9, 0.6, 0.95, 1.95), (0.55, 1.2, 0.45, 1.2, 1.9), (0.1, 0.55, 0.3, 1.45, 1.85))):
        p.box(x0, x1, cy - hw, cy + hw, z0, z1, PWHITE)
    p.blob(7.75, cy, 1.25, 1.05, 0.72, 0.62, PWHITE, sub=2, rough=0.0)
    # cheat lines (red over blue) along both sides, and the belly
    for (z0, z1, c) in ((1.3, 1.42, PRED), (1.18, 1.3, PBLUE)):
        p.box(0.3, 8.2, cy - 0.735, cy + 0.735, z0, z1, c)
    # cockpit glazing and cabin windows (south side faces the viewer)
    p.box(6.7, 7.45, cy - 0.74, cy + 0.74, 1.55, 1.95, GLASS)
    p.box(7.0, 7.6, cy - 0.55, cy + 0.55, 1.85, 2.02, GLASS)
    for x in (3.0, 3.8, 5.3, 6.0):
        for s_ in (-1, 1):
            p.box(x, x + 0.45, cy + s_ * 0.725 - 0.01, cy + s_ * 0.725 + 0.01, 1.5, 1.78, GLASS)
    # open cargo door (south side): dark hole, door hinged up
    p.box(4.2, 5.0, cy - 0.745, cy - 0.73, 0.75, 1.75, DARK)
    p.box(4.2, 5.0, cy - 1.55, cy - 0.74, 1.76, 1.82, PWHITE)
    # fin (reaches level 1) and tailplane
    p.box(0.1, 1.3, cy - 0.06, cy + 0.06, 1.85, 3.3, PWHITE)
    p.box(0.1, 0.6, cy - 0.065, cy + 0.065, 2.6, 3.3, PRED)
    p.box(0.05, 0.95, cy - 2.1, cy + 2.1, 1.7, 1.8, PWHITE)
    # wings (low wing), red tips
    p.box(4.6, 6.0, -0.15, cy - 0.7, 1.0, 1.14, PWHITE)
    p.box(4.6, 6.0, cy + 0.7, -9 * S + 0.15, 1.0, 1.14, PWHITE)
    p.box(4.6, 6.0, -0.15, -0.55, 1.0, 1.15, PRED); p.box(4.6, 6.0, -9 * S + 0.55, -9 * S + 0.15, 1.0, 1.15, PRED)
    # engines with spinners and 2-blade props
    for y in sym(2.3):
        p.blob(6.3, y, 1.18, 1.05, 0.38, 0.34, PWHITE, sub=2, rough=0.0)
        p.box(5.6, 6.6, y - 0.39, y + 0.39, 1.15, 1.2, PRED)
        p.blob(7.42, y, 1.18, 0.16, 0.13, 0.13, PRED, sub=1, rough=0.0)
        p.rod((7.45, y - 0.95, 0.75), (7.45, y + 0.95, 1.6), 0.05, DARK, ink=True, seg=4)
        wheel(p, 6.1, y, 0.25, 0.25, 0.18)
        p.rod((6.1, y, 0.25), (6.1, y, 1.0), 0.05, STEEL, ink=True, seg=4)
    wheel(p, 8.2, cy, 0.2, 0.2, 0.14)
    p.rod((8.2, cy, 0.2), (8.0, cy, 0.85), 0.04, STEEL, ink=True, seg=4)
    p.decal((2.4, cy - 0.737, 0.8), (1, 0, 0), (0, 0, 1), 1.3, 0.3, 'decal_b8b_oil.png')

# ---------------------------------------------------------------- 1970s pickup (nose east), 4 x 2 cells
PICKUP = (4, 2, 1)
def build_pickup(p):
    cy = -S; x0 = 0.05
    p.box(x0 + 0.15, x0 + 5.0, cy - 0.95, cy + 0.95, 0.45, 1.05, TRUCK)             # body
    p.box(x0 + 3.5, x0 + 5.05, cy - 0.9, cy + 0.9, 1.05, 1.15, TRUCK_D)              # hood
    p.box(x0 + 2.2, x0 + 3.5, cy - 0.92, cy + 0.92, 1.05, 1.75, TRUCK)               # cab
    p.box(x0 + 3.45, x0 + 3.52, cy - 0.85, cy + 0.85, 1.12, 1.68, GLASS)            # windscreen
    p.box(x0 + 2.5, x0 + 3.3, cy - 0.93, cy + 0.93, 1.2, 1.65, GLASS)               # side windows
    p.box(x0 + 0.2, x0 + 2.15, cy - 0.85, cy + 0.85, 0.7, 1.05, DARK)               # bed well
    p.box(x0 + 5.0, x0 + 5.12, cy - 0.85, cy + 0.85, 0.5, 0.85, CHROME)             # grille
    p.box(x0 + 0.0, x0 + 0.15, cy - 0.95, cy + 0.95, 0.42, 0.55, CHROME)            # rear bumper
    p.box(x0 + 5.1, x0 + 5.22, cy - 0.98, cy + 0.98, 0.4, 0.52, CHROME)             # front bumper
    for (x, s_) in ((x0 + 5.12, -1), (x0 + 5.12, 1)):
        p.box(x, x + 0.03, cy + s_ * 0.65 - 0.12, cy + s_ * 0.65 + 0.12, 0.7, 0.85, (0.95, 0.92, 0.7))
    for x in (x0 + 0.95, x0 + 4.1):
        for s_ in (-1, 1): wheel(p, x, cy + s_ * 0.85, 0.38, 0.38, 0.28)
    for (bx, by) in ((0.45, -0.55), (1.15, -0.55), (0.45, 0.15)):                       # bales in the bed
        p.box(x0 + bx, x0 + bx + 0.6, cy + by, cy + by + 0.5, 1.05, 1.4, (0.62, 0.50, 0.30))

# ---------------------------------------------------------------- skiff with outboard (bow east), 4 x 2 cells, on water
SKIFF = (4, 2, 1)
def build_skiff(p):
    cy = -S
    p.box(0.4, 4.0, cy - 0.85, cy + 0.85, 0.02, 0.5, BOAT)
    p.box(0.5, 3.9, cy - 0.72, cy + 0.72, 0.18, 0.5, BOAT_IN)
    for k, (x0, x1, hw, z) in enumerate(((4.0, 4.4, 0.7, 0.08), (4.4, 4.75, 0.45, 0.14), (4.75, 5.0, 0.2, 0.2))):
        p.box(x0, x1, cy - hw, cy + hw, z, 0.52, BOAT)
    p.box(0.4, 5.0, cy - 0.86, cy + 0.86, 0.48, 0.53, (0.85, 0.82, 0.70))           # gunwale trim (no ink shading)
    for x in (1.6, 2.9): p.box(x, x + 0.3, cy - 0.72, cy + 0.72, 0.18, 0.4, (0.55, 0.42, 0.26))   # thwarts
    p.box(0.05, 0.45, cy - 0.2, cy + 0.2, 0.3, 0.95, DARK)                              # outboard
    p.box(0.1, 0.25, cy - 0.06, cy + 0.06, -0.1, 0.3, DARK)
    p.box(2.2, 2.7, cy - 0.5, cy + 0.2, 0.18, 0.5, (0.62, 0.50, 0.30))                  # two bundles
    p.box(3.1, 3.5, cy - 0.1, cy + 0.5, 0.18, 0.45, (0.62, 0.50, 0.30))

# ---------------------------------------------------------------- single-cell landing parts
def dock_deck(seed):
    def f(p):
        rnd = random.Random(seed)
        for k in range(6):              # planks run east-west
            y0 = -S + k * S / 6
            c = WOOD if k % 2 else (0.68, 0.51, 0.30)
            p.box(0, S, y0 + 0.01, y0 + S / 6 - 0.01, 0.05 + rnd.uniform(-.01, .01), 0.12, c, ink=False, tex=TX('a11', rnd.random(), 0, size=1.3))
        for x in (0.05, S - 0.15): p.box(x, x + 0.1, -S, 0, -0.25, 0.05, WOOD_D, ink=False)
    return f
def dock_piling(p):
    for (x, y) in ((0.12, -0.12), (S - 0.12, -S + 0.12)):
        p.cyl(x, y, -0.3, 0.75, 0.11, WOOD_D, seg=8)
        p.cyl(x, y, 0.75, 0.77, 0.12, (0.45, 0.33, 0.2), seg=8)
    p.box(0.6, 0.75, -0.7, -0.6, 0.12, 0.2, STEEL)                                      # cleat
    p.rod((0.68, -0.65, 0.18), (1.1, -1.3, 0.05), 0.02, (0.85, 0.80, 0.6), seg=4)         # rope to the skiff
def dock_ladder(p):
    for x in (0.45, 0.85): p.box(x, x + 0.05, -S + 0.02, -S + 0.08, -0.5, 0.6, STEEL)
    for z in (-0.3, 0.0, 0.3): p.box(0.45, 0.9, -S + 0.03, -S + 0.07, z, z + 0.04, STEEL)

SINGLES = [('dock_deck_a', False, dock_deck(1)), ('dock_deck_b', False, dock_deck(2)),
           ('dock_piling', True, dock_piling), ('dock_ladder', True, dock_ladder)]
BIGS = [('plane', build_plane, PLANE), ('pickup', build_pickup, PICKUP), ('skiff', build_skiff, SKIFF)]

# ---------------------------------------------------------------- KIT (names in frame order) and MCD records
MAN = os.path.join(HERE, 'smuggler_cells.json')
CELLS = json.load(open(MAN)) if os.path.exists(MAN) else {}
KIT = [(n, ink, fn) for (n, ink, fn) in SINGLES]
for (obj, _, _) in BIGS:
    for (i, j, l, name) in CELLS.get(obj, []): KIT.append((name, True, None))

LOW = dict(loft=[33] * 6 + [0] * 6, walk=255)                       # waist-high hull (pickup)
BOATL = dict(loft=[33] * 3 + [0] * 9, walk=255)                     # skiff
FULL = dict(loft=[33] * 12, walk=255)                                # fuselage, engines: full block (LOFTEMPS 33)
WING = dict(loft=[0] * 5 + [33, 33] + [0] * 5, walk=255)             # thin wing at ~1.1 m
MCDSPEC = {'dock_deck_a': ('BARN', 19, {}), 'dock_deck_b': ('BARN', 19, {}),
           'dock_piling': ('FRNITURE', 10, {}), 'dock_ladder': ('FRNITURE', 10, dict(walk=4, loft=[0] * 12))}
WINGS = json.load(open(os.path.join(HERE, 'smuggler_wing.json'))) if os.path.exists(os.path.join(HERE, 'smuggler_wing.json')) else []
for (obj, _, _) in BIGS:
    for (i, j, l, name) in CELLS.get(obj, []):
        if obj == 'plane':
            kw = dict(WING) if name in WINGS else dict(FULL)
            MCDSPEC[name] = ('FRNITURE', 17, dict(kw, he=0))
        else:
            MCDSPEC[name] = ('FRNITURE', 17, dict(BOATL if obj == 'skiff' else LOW))
