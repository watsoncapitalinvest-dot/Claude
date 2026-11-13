"""compose a test block from several sets the way the game draws it (full-colour path), and write its MAP."""
import sys, struct, random, importlib, os
import bpy
from PIL import Image
sys.path.insert(0, '.')
D = 'dist_m1/TERRAIN/'
SETS = ['BSCRUB', 'BARNYRD']; MODS = {'BSCRUB': 'bscrub', 'BARNYRD': 'barnyard'}
base = 2; OFF = {}; NAMES = {}; FR = {}
for s in SETS:
    m = importlib.import_module(MODS[s]); names = [n for n, _, _ in m.KIT]
    OFF[s] = base; base += len(names); NAMES[s] = {n: i for i, n in enumerate(names)}
    sh = Image.open(D + s + '_4X.png').convert('RGBA'); cols = sh.width // 128
    FR[s] = [sh.crop(((i % cols) * 128, (i // cols) * 160, (i % cols) * 128 + 128, (i // cols) * 160 + 160)) for i in range(len(names))]
def gid(s, n): return OFF[s] + NAMES[s][n]
W = L = 20; Z = 4; T = {}
def put(x, y, z, slot, s, n): T.setdefault((x, y, z), [0, 0, 0, 0])[slot] = gid(s, n)
r = random.Random(3)
for x in range(W):
    for y in range(L):
        if y >= 17: put(x, y, 0, 0, 'BSCRUB', r.choice(['water_a', 'water_b']))
        elif y == 16: put(x, y, 0, 0, 'BSCRUB', 'mud_a')
        elif x <= 3: put(x, y, 0, 0, 'BSCRUB', r.choice(['sand_a', 'sand_b']))
        elif x in (6, 7) and y < 10: put(x, y, 0, 0, 'BSCRUB', 'road_ns_a' if x == 6 else 'road_ns_b')
        else: put(x, y, 0, 0, 'BSCRUB', r.choice(['caliche_a', 'caliche_b', 'caliche_c', 'caliche_d', 'scrub_a', 'scrub_b', 'caliche_a']))
for y in range(0, 15):
    if y not in (6, 7): put(4, y, 0, 1, 'BSCRUB', 'bank_w')
for x in range(W):
    if x % 3: put(x, 15, 0, 3, 'BSCRUB', 'cane')
for x in range(10, 16):
    for y in range(2, 7):
        put(x, y, 0, 0, 'BARNYRD', 'cbarn_a' if (x + y) % 3 else 'straw')
        if x >= 13: put(x, y, 1, 0, 'BARNYRD', 'roof_tin')      # half roofed so the inside stays visible
for y in range(2, 7): put(10, y, 0, 1, 'BARNYRD', 'barndoor_w' if y == 4 else ('barnwin_w' if y == 3 else 'barnwall_w'))
for x in range(10, 16):
    put(x, 2, 0, 2, 'BARNYRD', 'barnwall_n')
    put(x, 7, 0, 2, 'BARNYRD', 'barndoor_n' if x == 12 else ('barnwin_n' if x == 14 else 'barnwall_n'))
for y in range(2, 7): put(16, y, 0, 1, 'BARNYRD', 'barnwall_w')
for (x, y, n) in ((11, 3, 'crate_a'), (12, 3, 'crate_b'), (11, 5, 'table_scale'), (12, 5, 'table'), (14, 3, 'bales'), (15, 6, 'crate_open')):
    put(x, y, 0, 3, 'BARNYRD', n)
for (x, y, n) in ((9, 8, 'drum'), (9, 9, 'drum'), (13, 9, 'hay'), (17, 8, 'crate_c')):
    put(x, y, 0, 3, 'BARNYRD', n)
for x in range(8, 20): put(x, 11, 0, 2, 'BARNYRD', 'gate_n' if x == 12 else 'fence_n')
put(18, 1, 0, 0, 'BARNYRD', 'tower_lift'); put(18, 1, 0, 3, 'BARNYRD', 'tower_legs')
put(18, 1, 1, 0, 'BARNYRD', 'tower_deck'); put(18, 1, 1, 1, 'BARNYRD', 'tower_rail_w'); put(18, 1, 1, 2, 'BARNYRD', 'tower_rail_n')
put(19, 1, 1, 1, 'BARNYRD', 'tower_rail_w'); put(18, 2, 1, 2, 'BARNYRD', 'tower_rail_n')
put(18, 1, 2, 0, 'BARNYRD', 'tower_roof')
put(17, 13, 0, 0, 'BARNYRD', 'mill_lift'); put(17, 13, 0, 3, 'BARNYRD', 'mill_legs')
put(17, 13, 1, 0, 'BARNYRD', 'mill_deck'); put(17, 13, 2, 3, 'BARNYRD', 'mill_wheel')
for (x, y, n) in ((2, 3, 'rock_a'), (1, 9, 'rock_b'), (2, 12, 'pebbles'), (8, 14, 'mesquite_a'), (5, 1, 'mesquite_b'),
                  (9, 13, 'prickly_pear'), (19, 7, 'snag'), (15, 13, 'stock_tank'), (3, 6, 'tyre_marker')):
    put(x, y, 0, 3, 'BSCRUB', n)
for y in range(0, 6): put(9, y, 0, 1, 'BSCRUB', 'bfence_w')
setof = []
for s in SETS: setof += [(s, i) for i in range(len(NAMES[s]))]
def spr(g): s, i = setof[g - 2]; return FR[s][i]
qx, qy, lv = 64, 32, 96
img = Image.new('RGBA', ((W + L) * qx + 128, (W + L) * qy + Z * lv + 200), (52, 64, 56, 255))
ox, oy = L * qx, Z * lv
for z in range(Z):
    for y in range(L):
        for x in range(W):
            t = T.get((x, y, z))
            if not t: continue
            for g in t:
                if g: img.alpha_composite(spr(g), (ox + (x - y) * qx - qx, oy + (x + y) * qy - z * lv))
img.save('m1test_full.png')
data = bytes([L, W, Z])
for z in range(Z - 1, -1, -1):
    for y in range(L):
        for x in range(W): data += bytes(T.get((x, y, z), [0, 0, 0, 0]))
os.makedirs('dist_m1/MAPS', exist_ok=True); open('dist_m1/MAPS/M1TEST.MAP', 'wb').write(data)
print('ok', img.size, 'max id', max(max(v) for v in T.values()))
