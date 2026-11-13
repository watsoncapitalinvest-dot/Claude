"""CSEMI: the Cobra semi (John 00:33: "this one should be a semi"; look approved 12 Nov 16:41:
black tractor with red trim, Cobra-blue ribbed trailer, Cobra logo on the trailer and the door).
Rig = 16 x 2 cells (local i 0-15 east, j 0-1 south), cab east:
  trailer i 0-9 (2 levels tall, roof on level +2), tractor: fifth-wheel deck i 10-11, sleeper i 12, cab i 13, long hood i 14-15.
Walls/floors/objects so units can enter the trailer and the cab. Wreck chain ok -> shot -> burn -> hulk on every part.
Big pieces (trailer south side with the emblem, the hood) are modelled whole and cut per cell (render_csemi.py)."""
import math, random, os, json
from kitlib import *
SET = 'CSEMI'
HERE = os.path.dirname(os.path.abspath(__file__))
BLUE = (0.18, 0.30, 0.62)
BLUE_D = (0.13, 0.22, 0.48)
BLACK = (0.11, 0.11, 0.12)
RED = (0.80, 0.12, 0.10)
CHROME = (0.84, 0.86, 0.88)
CHASSIS = (0.13, 0.13, 0.14)
GLASS = (0.26, 0.33, 0.40)
TYRE = (0.12, 0.12, 0.12)
STATES = ['ok', 'shot', 'burn', 'hulk']
ST = {'s': 'ok'}
def C(rgb, glass=False):
    s = ST['s']
    if s == 'ok': return rgb
    if s == 'shot': return (rgb[0] * 0.5, rgb[1] * 0.5, rgb[2] * 0.52) if glass else rgb
    if s == 'burn': k = 0.42; return (rgb[0] * k + 0.06, rgb[1] * k + 0.03, rgb[2] * k)
    k = 0.2; return (rgb[0] * k + 0.12, rgb[1] * k + 0.07, rgb[2] * k + 0.04)
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
def staged(fn, st):
    def f(p):
        ST['s'] = st
        try: fn(p)
        finally: ST['s'] = 'ok'
    return f
def wl(p, axis, a0, a1, z0, z1, rgb, th=T, off=0.0, ink=False, y0=0.0):
    keep = keep_west if axis == 'w' else keep_north
    if axis == 'w': return p.box(off, off + th, -a1, -a0, z0, z1, rgb, ink=ink, mark=keep)
    return p.box(a0, a1, y0 - off - th, y0 - off, z0, z1, rgb, ink=ink, mark=keep)
def wheels(p, x, y0, zc=0.5, dual=True):       # tyre(s) seen from the south, outside a north-slot wall at y0
    hub = ST['s'] == 'hulk'
    p.rod((x, y0 - 0.02, zc), (x, y0 - 0.32, zc), 0.5 if not hub else 0.34, C(TYRE) if not hub else (0.30, 0.20, 0.14), ink=True, seg=14)
    p.rod((x, y0 - 0.32, zc), (x, y0 - 0.34, zc), 0.24, C(CHROME), ink=True, seg=10)

# ================================================================ TRAILER
TOP2 = 2 * H * 0.99
def trl_side(kind):
    """generic side panel, one level: lo (with chassis skirt), hi (top rail), axle (lo + tandem wheels). north side + burnt states."""
    def f(p):
        lo = kind in ('lo', 'axle')
        if ST['s'] == 'hulk':
            for a in (0.0, S / 2): wl(p, 'n', a, a + 0.08, 0.55 if lo else 0, H if lo else TOP2 - H, C(BLUE), th=0.08)
            if lo: wl(p, 'n', 0, S, 0.0, 0.55, C(CHASSIS))
            else: wl(p, 'n', 0, S, TOP2 - H - 0.12, TOP2 - H, C(BLUE), th=0.1)
        else:
            if lo:
                wl(p, 'n', 0, S, 0.0, 0.55, C(CHASSIS)); wl(p, 'n', 0, S, 0.55, H, C(BLUE))
                wl(p, 'n', 0, S, 0.55, 0.63, C(CHROME), th=T + 0.03)
            else:
                wl(p, 'n', 0, S, 0, TOP2 - H, C(BLUE)); wl(p, 'n', 0, S, TOP2 - H - 0.1, TOP2 - H, C(CHROME), th=T + 0.03)
            for a in [k * S / 4 for k in range(4)]:
                wl(p, 'n', a, a + 0.05, 0.63 if lo else 0, H if lo else TOP2 - H - 0.1, C(BLUE_D), th=T + 0.02)       # ribs
        if kind == 'axle': wheels(p, S / 2, -T)
        holes(p, (0.2, -T - 0.004, 0.9 if lo else 0.5), (1, 0, 0), (0, 0, 1), 0.6, 0.6)
        flames(p, S / 2, -0.4, (H - 0.5) if lo else 0.6, 3 if lo else 4)
    return f

TRAILER_SOUTH = (10, 3, 2)      # big object: the south side panel of the trailer (with emblem), cut per cell; wall sits in row 2
def build_trl_south(p):
    y0 = -2 * S
    wl(p, 'n', 0, 10 * S, 0.0, 0.55, C(CHASSIS), y0=y0)
    wl(p, 'n', 0, 10 * S, 0.55, TOP2, C(BLUE), y0=y0)
    wl(p, 'n', 0, 10 * S, 0.55, 0.63, C(CHROME), th=T + 0.03, y0=y0)
    wl(p, 'n', 0, 10 * S, TOP2 - 0.1, TOP2, C(CHROME), th=T + 0.03, y0=y0)
    wl(p, 'n', 0, 10 * S, 1.0, 1.08, C(RED), th=T + 0.012, y0=y0)                       # red pinstripe
    for k in range(40):
        a = k * S / 4
        wl(p, 'n', a, a + 0.05, 0.63, TOP2 - 0.1, C(BLUE_D), th=T + 0.02, y0=y0)
    if ST['s'] == 'ok':
        p.decal((3.4, y0 - T - 0.025, 1.2), (1, 0, 0), (0, 0, 1), 2.5, 2.5, 'decal_cobra_black.png')
        p.decal((3.35, y0 - T - 0.03, 1.25), (1, 0, 0), (0, 0, 1), 2.5, 2.5, 'decal_cobra_red.png')
    else:
        p.decal((3.4, y0 - T - 0.025, 1.2), (1, 0, 0), (0, 0, 1), 2.5, 2.5, 'decal_cobra_red.png')
        for (x, z) in ((1.2, 1.4), (3.0, 0.9), (6.8, 1.6), (9.0, 1.1), (5.2, 2.6)):
            p.decal((x, y0 - T - 0.035, z), (1, 0, 0), (0, 0, 1), 0.7, 0.7, 'decal_b8c_bulletholes.png')
    for x in (1.3 * S - 0.0, 2.2 * S):                                                       # tandem axles near the rear
        wheels(p, x, y0 - T)
    p.box(8.5 * S - 0.1, 8.5 * S + 0.1, y0 - T - 0.25, y0 - T - 0.1, 0.1, 0.55, C(CHROME))   # landing-gear leg
    p.box(8.5 * S - 0.18, 8.5 * S + 0.18, y0 - T - 0.3, y0 - T - 0.05, 0.0, 0.08, C(CHASSIS))
    p.box(0.0, 0.35, y0 - T - 0.3, y0 - T - 0.02, 0.05, 0.45, C(CHASSIS))                   # rear bumper guard
TRL_AXLE_I = (1, 2)

def trl_rear(frame=0):          # roll-up door, west end, lower level (UFO door frames 0..7)
    def f(p):
        up = frame / 7.0
        wl(p, 'w', 0, S, 0.0, 0.55, C(CHASSIS))
        zb = 0.55 + up * (H - 0.65)
        for k in range(10):
            z0 = 0.55 + k * (H - 0.55) / 10
            if z0 + 0.01 < zb: continue
            wl(p, 'w', 0.05, S - 0.05, max(z0, zb), z0 + (H - 0.55) / 10, C(CHROME if k % 2 else (0.74, 0.76, 0.78)), th=0.05, off=0.035)
        wl(p, 'w', 0, 0.06, 0.55, H, C(BLUE_D), th=T); wl(p, 'w', S - 0.06, S, 0.55, H, C(BLUE_D), th=T)
        if frame == 0: wl(p, 'w', S / 2 - 0.1, S / 2 + 0.1, 0.6, 0.67, C(BLACK), th=0.02, off=0.085)
        p.box(T + 0.03, T + 0.12, -S / 2 - 0.2, -S / 2 + 0.2, 0.35, 0.5, C(RED))                 # tail light bar
        holes(p, (T + 0.004, -0.3, 0.9), (0, -1, 0), (0, 0, 1), 0.55, 0.55)
        flames(p, 0.4, -S / 2, H - 0.5, 7)
    return f
def trl_rear_hi(p):
    wl(p, 'w', 0, S, 0, TOP2 - H, C(BLUE)); wl(p, 'w', 0, S, TOP2 - H - 0.1, TOP2 - H, C(CHROME), th=T + 0.03)
    wl(p, 'w', 0.05, S - 0.05, 0.0, 0.25, C((0.74, 0.76, 0.78)), th=0.05, off=0.035)           # door header / roll housing
    flames(p, 0.4, -S / 2, 0.6, 8)
def trl_front(lo):              # east end of the trailer (faces the tractor)
    def f(p):
        if lo: wl(p, 'w', 0, S, 0.0, 0.55, C(CHASSIS)); wl(p, 'w', 0, S, 0.55, H, C(BLUE))
        else: wl(p, 'w', 0, S, 0, TOP2 - H, C(BLUE)); wl(p, 'w', 0, S, TOP2 - H - 0.1, TOP2 - H, C(CHROME), th=T + 0.03)
        if lo: p.rod((T + 0.05, -0.4, 1.2), (T + 0.6, -0.4, 0.9), 0.025, C(RED), ink=True, seg=4)   # air lines (glad hands)
        flames(p, 0.4, -S / 2, 0.8, 9)
    return f
def trl_floor(p):
    for k in range(6):
        y0 = -S + k * S / 6
        p.box(0, S, y0 + 0.01, y0 + S / 6 - 0.01, 0.0, 0.03, C((0.60, 0.46, 0.30) if k % 2 else (0.54, 0.41, 0.26)), ink=False)
    if ST['s'] in ('burn', 'hulk'):
        for i in range(4): p.box(0.1 + 0.27 * i, 0.3 + 0.27 * i, -0.4 - 0.2 * i, -0.2 - 0.2 * i, 0.035, 0.04, (0.08, 0.08, 0.08), ink=False)
def trl_roof(p):
    if ST['s'] == 'hulk':
        for a in (0.1, S / 2): p.box(a, a + 0.08, -S, 0, -0.06, 0.0, C(CHROME), ink=True); return
    p.box(0, S, -S, 0, -0.06, 0.0, C((0.80, 0.82, 0.84)), ink=False)
    for k in range(4): p.box(k * S / 4, k * S / 4 + 0.03, -S, 0, 0.0, 0.01, C((0.66, 0.68, 0.70)), ink=False)
    flames(p, S / 2, -S / 2, 0.0, 21)
def cargo(p):
    COB = (0.22, 0.34, 0.62)
    for (x0, y0, z0, w, d, h) in ((0.1, -1.2, 0.03, 0.55, 0.5, 0.5), (0.7, -1.2, 0.03, 0.5, 0.5, 0.5), (0.1, -0.65, 0.03, 1.1, 0.5, 0.55),
                                  (0.2, -1.15, 0.53, 0.5, 0.45, 0.45), (0.75, -0.6, 0.58, 0.4, 0.45, 0.4)):
        p.box(x0, x0 + w, y0, y0 + d, z0, z0 + h, C((0.30, 0.42, 0.30)))
        p.box(x0 - 0.005, x0 + w + 0.005, y0 - 0.005, y0 + d + 0.005, z0 + h * 0.45, z0 + h * 0.55, C((0.75, 0.75, 0.72)), ink=False)
    if ST['s'] == 'ok': p.decal((0.25, -1.205, 0.12), (1, 0, 0), (0, 0, 1), 0.3, 0.3, 'decal_b1_cobra_stencil.png')
    flames(p, 0.6, -0.8, 0.9, 29)

# ================================================================ TRACTOR
CAB_TOP = H * 0.99
def deck_floor(p):              # fifth-wheel deck: frame rails, the coupling plate, mud flaps area
    p.box(0, S, -S, 0, -0.05, 0.0, C((0.30, 0.30, 0.31)), ink=False)
    for y in (-0.35, -0.95): p.box(0, S, y - 0.08, y + 0.08, 0.0, 0.45, C(CHASSIS))
    p.box(0.1, S - 0.1, -S + 0.15, -0.15, 0.45, 0.55, C((0.22, 0.22, 0.23)))
def deck_side(p):               # tandem drive wheels + rail on a north-slot edge (placed on the south side), with mud flap
    wl(p, 'n', 0, S, 0.25, 0.55, C(CHASSIS))
    wheels(p, S / 2, -T)
    p.box(S - 0.15, S - 0.1, -T - 0.4, -T - 0.05, 0.1, 0.75, C(BLACK))
    holes(p, (0.2, -T - 0.004, 0.3), (1, 0, 0), (0, 0, 1), 0.4, 0.3)
    flames(p, S / 2, -0.4, 0.6, 31)
def cab_wall(kind):
    """north-slot walls along the tractor: 'sleeper', 'door', 'door_open'. Black with a red trim stripe."""
    def f(p):
        wl(p, 'n', 0, S, 0.0, 0.5, C(CHASSIS))
        if kind == 'door_open':
            wl(p, 'n', 0, 0.12, 0.5, CAB_TOP, C(BLACK)); wl(p, 'n', S - 0.12, S, 0.5, CAB_TOP, C(BLACK)); wl(p, 'n', 0, S, CAB_TOP - 0.15, CAB_TOP, C(BLACK))
            p.box(S - 0.12, S - 0.06, -T - 1.0, -T, 0.6, 1.8, C(BLACK), mark=keep_north)
            return
        wl(p, 'n', 0, S, 0.5, 1.15, C(BLACK)); wl(p, 'n', 0, S, 1.65, CAB_TOP, C(BLACK))
        if kind == 'door':
            wl(p, 'n', 0, 0.2, 1.15, 1.65, C(BLACK)); wl(p, 'n', S - 0.15, S, 1.15, 1.65, C(BLACK))
            if ST['s'] != 'hulk': wl(p, 'n', 0.2, S - 0.15, 1.15, 1.65, C(GLASS, True), th=0.03, off=0.045)
            if ST['s'] == 'ok': p.decal((0.38, -T - 0.004, 0.6), (1, 0, 0), (0, 0, 1), 0.5, 0.5, 'decal_cobra_red.png')
            wl(p, 'n', S - 0.4, S - 0.25, 1.0, 1.04, C(CHROME), th=0.03, off=T)
            for z in (0.15, 0.35): wl(p, 'n', 0.25, S - 0.25, z, z + 0.04, C(CHROME), th=0.25, off=T)
        else:
            wl(p, 'n', 0, S, 1.15, 1.65, C(BLACK))
            wl(p, 'n', 0.4, 0.8, 1.25, 1.5, C(GLASS, True), th=0.02, off=T)                     # small sleeper window
        wl(p, 'n', 0, S, 0.85, 0.95, C(RED), th=T + 0.012)                                      # red trim
        holes(p, (0.3, -T - 0.004, 0.6), (1, 0, 0), (0, 0, 1), 0.5, 0.5)
        flames(p, S / 2, -0.4, 1.4, 11)
    return f
def sleeper_back(p):            # west wall of the sleeper (faces the trailer)
    wl(p, 'w', 0, S, 0.0, 0.5, C(CHASSIS)); wl(p, 'w', 0, S, 0.5, CAB_TOP, C(BLACK))
    wl(p, 'w', 0, S, 0.85, 0.95, C(RED), th=T + 0.012)
    flames(p, 0.4, -S / 2, 1.3, 13)
def windscreen(p):              # west wall of the hood cell: the windscreen between cab and hood
    wl(p, 'w', 0, S, 0.0, 1.15, C(BLACK)); wl(p, 'w', 0, S, CAB_TOP - 0.12, CAB_TOP, C(BLACK))
    wl(p, 'w', 0, 0.06, 1.15, CAB_TOP, C(BLACK)); wl(p, 'w', S - 0.06, S, 1.15, CAB_TOP, C(BLACK))
    if ST['s'] != 'hulk': wl(p, 'w', 0.06, S - 0.06, 1.15, CAB_TOP - 0.12, C(GLASS, True), th=0.03, off=0.045)
    if ST['s'] in ('shot', 'burn'):
        for a in (0.4, 0.8): wl(p, 'w', a, a + 0.03, 1.2, 1.8, (0.85, 0.88, 0.9), th=0.005, off=T)
    p.box(T, T + 0.06, -S + 0.1, -0.1, CAB_TOP - 0.05, CAB_TOP + 0.08, C(CHROME))               # sun visor
    flames(p, 0.4, -S / 2, 1.5, 15)
def cab_floor(p):
    p.box(0, S, -S, 0, 0.0, 0.03, C((0.22, 0.22, 0.23)), ink=False)
    p.box(0.3, 1.0, -0.6, -0.2, 0.03, 0.5, C((0.50, 0.12, 0.10)))                                 # seat (red vinyl)
    p.box(0.3, 0.42, -0.6, -0.2, 0.5, 1.0, C((0.50, 0.12, 0.10)))
    if ST['s'] in ('burn', 'hulk'):
        for i in range(3): p.box(0.1 + 0.3 * i, 0.3 + 0.3 * i, -1.0 + 0.1 * i, -0.8 + 0.1 * i, 0.035, 0.04, (0.08, 0.08, 0.08), ink=False)
def sleeper_floor(p):
    p.box(0, S, -S, 0, 0.0, 0.03, C((0.22, 0.22, 0.23)), ink=False)
    p.box(0.1, S - 0.1, -S + 0.1, -0.1, 0.03, 0.5, C((0.40, 0.36, 0.30)))                         # bunk
    p.box(0.15, S - 0.15, -S + 0.15, -0.15, 0.5, 0.6, C((0.62, 0.20, 0.16)))                      # blanket
def cab_roof(p):
    if ST['s'] == 'hulk':
        p.box(0.1, 0.2, -S, 0, -0.06, 0.0, C(BLACK), ink=True); return
    p.box(0, S, -S, 0, -0.06, 0.0, C(BLACK), ink=False)
    p.box(0.25, S - 0.25, -S + 0.25, -0.25, 0.0, 0.12, C((0.20, 0.20, 0.21)))                    # roof fairing
    for x in (0.2, S - 0.2): p.cyl(x, -S / 2, 0.12, 0.2, 0.06, C((0.95, 0.75, 0.2)), seg=6)       # marker lights
    flames(p, S / 2, -S / 2, 0.0, 23)
def stacks(p):                  # twin chrome exhaust stacks behind the sleeper (object on the sleeper roof cell, north + south)
    if ST['s'] == 'hulk':
        for y in (-0.15, -S + 0.15): p.cyl(0.15, y, -0.3, 0.3, 0.08, C(CHROME), seg=8)
        return
    for y in (-0.15, -S + 0.15):
        p.cyl(0.15, y, -0.6, 1.3, 0.08, C(CHROME), seg=10)
        p.cyl(0.15, y, 1.3, 1.34, 0.085, C(BLACK), seg=10)
def fuel_tank(p):
    if ST['s'] == 'hulk': p.box(0.2, 1.1, -0.35, -0.05, 0.25, 0.35, C(CHROME)); return
    p.rod((0.15, -0.3, 0.6), (1.15, -0.3, 0.6), 0.3, C(CHROME), ink=True, seg=14)
    for x in (0.35, 0.95): p.rod((x, -0.3, 0.6), (x + 0.04, -0.3, 0.6), 0.31, C(CHASSIS), ink=True, seg=14)
    p.cyl(0.7, -0.3, 0.9, 0.96, 0.06, C(CHASSIS), seg=8)
    flames(p, 0.65, -0.3, 0.6, 19)

HOOD = (2, 2, 1)                # big object: the long hood, fenders, grille, bumper, front wheels (cells i 14-15, j 0-1)
def build_hood(p):
    cy = -S
    p.box(0.0, 2 * S - 0.25, cy - 0.55, cy + 0.55, 0.75, 1.45, C(BLACK))                     # hood
    p.box(0.0, 2 * S - 0.25, cy - 0.56, cy + 0.56, 1.0, 1.08, C(RED))                        # red trim line
    p.box(0.05, 2 * S - 0.3, cy - 0.12, cy + 0.12, 1.45, 1.5, C(CHROME))                     # centre strip
    for s_ in (-1, 1):                                                                         # fenders
        yc = cy + s_ * 0.85
        p.box(0.6, 2 * S - 0.2, yc - 0.3, yc + 0.3, 0.6, 0.95, C(BLACK))
        p.rod((1.55, yc - 0.15, 0.5), (1.55, yc + 0.15, 0.5), 0.5 if ST['s'] != 'hulk' else 0.34, C(TYRE) if ST['s'] != 'hulk' else (0.30, 0.20, 0.14), ink=True, seg=14)
        p.rod((1.55, yc + s_ * 0.16, 0.5), (1.55, yc + s_ * 0.18, 0.5), 0.24, C(CHROME), ink=True, seg=10)
        p.cyl(0.25, yc, 1.0, 1.75, 0.13, C(CHROME), seg=10)                                    # air cleaners
        if ST['s'] != 'hulk': p.box(2 * S - 0.3, 2 * S - 0.22, yc - 0.18, yc + 0.18, 1.0, 1.25, C((0.98, 0.95, 0.8), True))   # headlights
    p.box(2 * S - 0.3, 2 * S - 0.2, cy - 0.5, cy + 0.5, 0.75, 1.45, C(CHROME))                  # grille
    for z in (0.85, 1.0, 1.15, 1.3): p.box(2 * S - 0.2, 2 * S - 0.18, cy - 0.45, cy + 0.45, z, z + 0.04, C(BLACK))
    p.box(2 * S - 0.22, 2 * S - 0.02, cy - 1.15, cy + 1.15, 0.35, 0.6, C(CHROME))              # bumper
    p.box(0.0, 2 * S - 0.25, cy - 0.5, cy + 0.5, 0.2, 0.75, C(CHASSIS))
    if ST['s'] in ('shot', 'burn'):
        p.decal((0.3, cy - 0.551, 0.9), (1, 0, 0), (0, 0, 1), 0.6, 0.45, 'decal_b8c_bulletholes.png')
        p.decal((1.6, cy - 1.151, 0.62), (1, 0, 0), (0, 0, 1), 0.5, 0.35, 'decal_b8c_bulletholes.png')
    flames(p, 1.2, cy, 1.45, 41)
ENGINE_CELL = (0, 1)            # the hood cell (i, j) that carries the objective flag: one engine block per rig

# ================================================================ KIT + MCD
SINGLE_BASE = [
    ('trl_side_lo', True, trl_side('lo')), ('trl_side_hi', True, trl_side('hi')), ('trl_side_axle', True, trl_side('axle')),
    ('trl_rear', True, trl_rear(0)), ('trl_rear_hi', True, trl_rear_hi), ('trl_front_lo', True, trl_front(True)), ('trl_front_hi', True, trl_front(False)),
    ('trl_floor', False, trl_floor), ('trl_roof', False, trl_roof),
    ('deck_floor', True, deck_floor), ('deck_side', True, deck_side),
    ('sleeper_side', True, cab_wall('sleeper')), ('cab_door', True, cab_wall('door')),
    ('sleeper_back', True, sleeper_back), ('windscreen', True, windscreen),
    ('cab_floor', False, cab_floor), ('sleeper_floor', False, sleeper_floor), ('cab_roof', False, cab_roof),
    ('stacks', True, stacks), ('fuel_tank', True, fuel_tank), ('cargo', True, cargo),
]
DOORS = ('trl_rear', 'cab_door')        # John 00:47: "i need to be able to blow off the doors" -> they die into an open doorway
SINGLES = []
for (n, ink, fn) in SINGLE_BASE:
    for st in (STATES if n not in DOORS else ['ok']): SINGLES.append((n if st == 'ok' else '%s_%s' % (n, st), ink, staged(fn, st)))
SINGLES.append(('cab_door_open', True, cab_wall('door_open')))
for k in range(1, 8): SINGLES.append(('trl_rear_f%d' % k, True, trl_rear(k)))


# ================================================================ crates (John 00:47: crates in the trailers he may be able to open, depending on BUILD)
OLIVE = (0.40, 0.42, 0.25)
OLIVE_D = (0.30, 0.31, 0.18)
def crate(decs):
    def f(p):
        w, d, h = 0.95, 0.9, 0.75; x0, y0 = (S - w) / 2, -(S + d) / 2
        p.tint = (0.62, 0.68, 0.42); p.box(x0, x0 + w, y0, y0 + d, 0, h, OLIVE, tex=TX('a11', size=1.6)); p.tint = (1, 1, 1)
        for z in (0.05, 0.62):
            p.box(x0 - 0.015, x0 + w + 0.015, y0 - 0.015, y0 + 0.02, z, z + 0.07, OLIVE_D)
            p.box(x0 + w - 0.02, x0 + w + 0.015, y0 - 0.015, y0 + d + 0.015, z, z + 0.07, OLIVE_D)
        p.box(x0 + 0.06, x0 + w - 0.06, y0 + 0.06, y0 + d - 0.06, h, h + 0.02, OLIVE_D)            # lid edge
        if decs[0]: p.decal((x0 + 0.2, y0 - 0.017, 0.14), (1, 0, 0), (0, 0, 1), 0.48, 0.48, decs[0])
        if decs[1]: p.decal((x0 + w + 0.017, y0 + 0.08, 0.16), (0, 1, 0), (0, 0, 1), 0.72, 0.36, decs[1])
        p.box(x0 + 0.05, x0 + 0.17, y0 - 0.02, y0 - 0.015, 0.5, 0.56, (0.85, 0.85, 0.80))           # serial plate
    return f
def crate_open(p):
    w, d, h, t = 0.95, 0.9, 0.75, 0.05; x0, y0 = (S - w) / 2, -(S + d) / 2; tx = TX('a11', size=1.6)
    p.tint = (0.62, 0.68, 0.42)
    p.box(x0, x0 + w, y0, y0 + t, 0, h, OLIVE, tex=tx); p.box(x0, x0 + w, y0 + d - t, y0 + d, 0, h, OLIVE, tex=tx)
    p.box(x0, x0 + t, y0, y0 + d, 0, h, OLIVE, tex=tx); p.box(x0 + w - t, x0 + w, y0, y0 + d, 0, h, OLIVE, tex=tx)
    p.tint = (1, 1, 1)
    p.box(x0 + t, x0 + w - t, y0 + t, y0 + d - t, 0, 0.45, (0.80, 0.70, 0.40))                      # packing straw
    for k in range(3):                                                                                   # rifles in the straw
        y = y0 + 0.22 + k * 0.22
        p.rod((x0 + 0.12, y, 0.5), (x0 + w - 0.12, y, 0.5), 0.03, (0.15, 0.15, 0.16), ink=True, seg=4)
        p.box(x0 + 0.12, x0 + 0.32, y - 0.04, y + 0.04, 0.46, 0.54, (0.42, 0.30, 0.18))
    p.tint = (0.62, 0.68, 0.42); p.box(x0 - 0.22, x0 - 0.17, y0 + 0.05, y0 + d - 0.05, 0, 0.62, OLIVE_D, tex=tx); p.tint = (1, 1, 1)   # lid leaning
def crate_broken(p):
    rnd = random.Random(5)
    for k in range(7):
        x, y = rnd.uniform(0.2, 1.0), -rnd.uniform(0.2, 1.1); a = rnd.uniform(0, math.pi)
        p.rod((x, y, 0.04), (x + 0.4 * math.cos(a), y + 0.4 * math.sin(a), 0.04 + rnd.uniform(0, 0.15)), 0.035, OLIVE_D, ink=True, seg=4)
    p.box(0.3, 1.0, -0.95, -0.35, 0.0, 0.12, (0.80, 0.70, 0.40), ink=False)
CRATES = [('crate_a', True, crate(('decal_b1_cobra_stencil.png', 'decal_b2a_machine_parts.png'))),
          ('crate_b', True, crate((None, 'decal_b2c_this_side_up.png'))),
          ('crate_open', True, crate_open), ('crate_broken', True, crate_broken)]
SINGLES += CRATES

def trl_rear_blown(p):          # rear door blown off: bent frame, shutter scraps hanging from the top, scorch on the floor edge
    wl(p, 'w', 0, S, 0.0, 0.55, C(CHASSIS))
    wl(p, 'w', 0, 0.06, 0.55, H, (0.25, 0.25, 0.27), th=T); wl(p, 'w', S - 0.06, S, 0.55, H, (0.25, 0.25, 0.27), th=T)
    for k, (a, l) in enumerate(((0.15, 0.35), (0.45, 0.2), (0.8, 0.45), (1.05, 0.25))):
        wl(p, 'w', a, a + 0.18, H - l, H, (0.55, 0.56, 0.58) if k % 2 else (0.40, 0.41, 0.43), th=0.03, off=0.04 + 0.05 * k)
    p.box(T, T + 0.5, -S + 0.1, -0.1, 0.0, 0.01, (0.10, 0.10, 0.10), ink=False)
def trl_rear_hi_blown(p):
    wl(p, 'w', 0, S, 0.25, TOP2 - H, (0.14, 0.18, 0.30)); wl(p, 'w', 0, S, TOP2 - H - 0.1, TOP2 - H, (0.45, 0.46, 0.48), th=T + 0.03)
    for a in (0.2, 0.7): p.rod((T + 0.05, -a, 0.25), (T + 0.35, -a - 0.2, 0.05), 0.03, (0.45, 0.46, 0.48), ink=True, seg=4)
def cab_door_blown(p):          # cab door gone: scorched frame
    wl(p, 'n', 0, S, 0.0, 0.5, C(CHASSIS))
    wl(p, 'n', 0, 0.12, 0.5, CAB_TOP, (0.08, 0.08, 0.08)); wl(p, 'n', S - 0.12, S, 0.5, CAB_TOP, (0.08, 0.08, 0.08))
    wl(p, 'n', 0, S, CAB_TOP - 0.15, CAB_TOP, (0.08, 0.08, 0.08))
    p.box(0.2, 1.0, -T - 0.9, -T - 0.3, 0.0, 0.05, (0.08, 0.08, 0.08), ink=True)                 # the door lying in the road
SINGLES += [('trl_rear_blown', True, trl_rear_blown), ('trl_rear_hi_blown', True, trl_rear_hi_blown), ('cab_door_blown', True, cab_door_blown)]

# ---------------------------------------------------------------- cab lockbox: the convoy's paperwork (clue spot type 'vehicle': manifest, fuel receipts, registration)
def lockbox(opened):
    def f(p):
        x0, x1, y0, y1, h = 0.35, 0.95, -0.95, -0.55, 0.42
        p.box(x0, x1, y0, y1, 0, h, (0.30, 0.32, 0.30))
        p.box(x0 + 0.02, x1 - 0.02, y0 - 0.01, y0, 0.15, 0.3, (0.24, 0.25, 0.24))
        if not opened:
            p.box(x0 - 0.01, x1 + 0.01, y0 - 0.01, y1 + 0.01, h, h + 0.04, (0.36, 0.38, 0.36))
            p.box(x0 + 0.25, x0 + 0.35, y0 - 0.03, y0 - 0.01, 0.3, 0.38, CHROME)
            p.box(x0 + 0.08, x0 + 0.5, y0 + 0.05, y1 - 0.05, h + 0.04, h + 0.06, (0.55, 0.40, 0.22))     # clipboard on the lid
            p.box(x0 + 0.12, x0 + 0.46, y0 + 0.08, y1 - 0.08, h + 0.06, h + 0.065, (0.95, 0.93, 0.85))
        else:
            p.box(x0 - 0.01, x1 + 0.01, y1, y1 + 0.04, h, h + 0.4, (0.36, 0.38, 0.36))                    # lid up
            p.box(x0 + 0.05, x1 - 0.05, y0 + 0.05, y1 - 0.05, h - 0.08, h - 0.06, (0.95, 0.93, 0.85))     # papers inside
    return f
SINGLES += [('lockbox', True, lockbox(False)), ('lockbox_open', True, lockbox(True))]
def _big(fn, st):
    def f(p): staged(fn, st)(p)
    return f
BIGS = [('trls_ok', _big(build_trl_south, 'ok'), TRAILER_SOUTH), ('trls_shot', _big(build_trl_south, 'shot'), TRAILER_SOUTH)]
for st in STATES: BIGS.append(('hood_%s' % st, _big(build_hood, st), HOOD))
NO_BLOCKERS = ('trls_ok', 'trls_shot')
MAN = os.path.join(HERE, 'csemi_cells.json')
CELLS = json.load(open(MAN)) if os.path.exists(MAN) else {}
KIT = list(SINGLES)
for (obj, _, _) in BIGS:
    for (i, j, l, name) in CELLS.get(obj, []): KIT.append((name, True, None))

SIDE_N = ('trl_side_lo', 'trl_side_hi', 'trl_side_axle', 'deck_side', 'sleeper_side', 'cab_door')
WEST = ('trl_rear', 'trl_rear_hi', 'trl_front_lo', 'trl_front_hi', 'sleeper_back', 'windscreen')
FLOORS = ('trl_floor', 'trl_roof', 'deck_floor', 'cab_floor', 'sleeper_floor', 'cab_roof')
def chain(n): return [n] + ['%s_%s' % (n, s) for s in STATES[1:]]
MCDSPEC = {}
def burnkw(nm): return dict(fuel=20, flam=40) if nm.endswith('_burn') else {}
for (n, _, _) in SINGLE_BASE:
    names = chain(n) if n not in DOORS else [n]
    for k, nm in enumerate(names):
        nxt = names[k + 1] if k + 1 < len(names) else None
        kw = dict(die=nxt) if nxt else {}
        kw.update(burnkw(nm))
        if n in SIDE_N: MCDSPEC[nm] = ('URBAN', 7, dict(kw, armor=12 if n.startswith('trl') else 25, type=2))
        elif n in WEST: MCDSPEC[nm] = ('URBAN', 8, dict(kw, armor=12 if n.startswith('trl') else 25, type=1))
        elif n in FLOORS: MCDSPEC[nm] = ('BARN', 19, dict(kw, armor=20, type=0))
        elif n == 'stacks': MCDSPEC[nm] = ('FRNITURE', 10, dict(kw, walk=255, loft=[25] * 12, type=3))
        elif n == 'fuel_tank': MCDSPEC[nm] = ('URBITS', 24, dict(kw, armor=10, walk=255, type=3, he=50 if k < 2 else 0, fuel=30 if k < 2 else 0))
        elif n == 'cargo': MCDSPEC[nm] = ('FRNITURE', 17, dict(kw, armor=20, walk=255, loft=[33] * 6 + [0] * 6, type=3))
MCDSPEC['cab_door'] = ('URBAN', 30, dict(MCDSPEC['cab_door'][2], alt='cab_door_open', door=1, armor=30, die='cab_door_blown'))
MCDSPEC['cab_door_open'] = ('URBAN', 30, dict(loft=[0] * 12, walk=0, los=0, block=0, door=0, type=2, armor=25, die='cab_door_blown'))
MCDSPEC['trl_rear'] = ('URBAN', 8, dict(MCDSPEC['trl_rear'][2], die='trl_rear_blown', armor=30, ufodoor=1, frames=['trl_rear'] + ['trl_rear_f%d' % k for k in range(1, 8)]))
for k in range(1, 8): MCDSPEC['trl_rear_f%d' % k] = ('URBAN', 8, dict(type=1, armor=12))
# big pieces: trailer south side cells are north walls; ok -> shot (same cell) -> generic burn -> generic hulk
for (i, j, l, name) in CELLS.get('trls_ok', []):
    g = 'trl_side_axle' if (l == 0 and i in TRL_AXLE_I) else ('trl_side_lo' if l == 0 else 'trl_side_hi')
    shot = 'trls_shot_%d_%d_%d' % (i, j, l)
    MCDSPEC[name] = ('URBAN', 7, dict(type=2, armor=12, die=shot if shot in [c[3] for c in CELLS.get('trls_shot', [])] else g + '_burn'))
for (i, j, l, name) in CELLS.get('trls_shot', []):
    g = 'trl_side_axle' if (l == 0 and i in TRL_AXLE_I) else ('trl_side_lo' if l == 0 else 'trl_side_hi')
    MCDSPEC[name] = ('URBAN', 7, dict(type=2, armor=12, die=g + '_burn'))
HOODNAMES = {st: {(c[0], c[1], c[2]): c[3] for c in CELLS.get('hood_%s' % st, [])} for st in STATES}
for k, st in enumerate(STATES):
    for key, name in HOODNAMES[st].items():
        nxt = HOODNAMES[STATES[k + 1]].get(key) if k + 1 < len(STATES) else None
        kw = dict(type=3, armor=40, walk=255, loft=[33] * 9 + [0] * 3)
        if nxt: kw['die'] = nxt
        kw.update(burnkw('_' + st))
        if st == 'ok' and key[:2] == ENGINE_CELL: kw['special'] = 14
        MCDSPEC[name] = ('FRNITURE', 17, kw)

for n in ('crate_a', 'crate_b'):
    MCDSPEC[n] = ('FRNITURE', 17, dict(alt='crate_open', die='crate_broken', armor=20, walk=255, loft=[33] * 5 + [0] * 7))
MCDSPEC['crate_open'] = ('FRNITURE', 17, dict(loft=[33] * 5 + [0] * 7, tlevel=-10, die='crate_broken', armor=20))
MCDSPEC['crate_broken'] = ('FRNITURE', 17, dict(loft=[0] * 12, walk=4, armor=10))

OPENWAY = dict(loft=[0] * 12, walk=0, los=0, block=0, door=0, armor=255)
MCDSPEC['trl_rear_blown'] = ('URBAN', 8, dict(OPENWAY, type=1))
MCDSPEC['cab_door_blown'] = ('URBAN', 7, dict(OPENWAY, type=2))
MCDSPEC['trl_rear_hi'] = ('URBAN', 8, dict(MCDSPEC['trl_rear_hi'][2], die='trl_rear_hi_blown'))
MCDSPEC['trl_rear_hi_blown'] = ('URBAN', 8, dict(type=1, armor=12, loft=[0] * 3 + [1] * 9))
MCDSPEC['lockbox'] = ('FRNITURE', 24, dict(alt='lockbox_open', armor=40, walk=255, loft=[33] * 3 + [0] * 9))
MCDSPEC['lockbox_open'] = ('FRNITURE', 24, dict(armor=40, walk=255, loft=[33] * 3 + [0] * 9))
