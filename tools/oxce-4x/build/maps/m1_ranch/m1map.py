"""Mission 1 map: the cartel ranch on the Rio Grande. 50 x 40 x 4, fixed layout (MAP_DESIGN_M1 section 4).
python3 m1map.py -> dist_m1/MAPS/M1RANCH.MAP, dist_m1/ROUTES/M1RANCH.RMP, m1ranch_preview.png
Terrain order for the ruleset: BLANKS, BSCRUB, BARNYRD, RANCH, SMUGGLR."""
import sys, os, json, math, random, importlib, struct
import bpy
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
D = 'dist_m1/TERRAIN/'
SETS = [('BSCRUB', 'bscrub'), ('BARNYRD', 'barnyard'), ('RANCH', 'ranch'), ('SMUGGLR', 'smuggler')]
base = 2; OFF, IDX, FR = {}, {}, {}
for s, m in SETS:
    names = [n for n, _, _ in importlib.import_module(m).KIT]
    OFF[s] = base; base += len(names); IDX[s] = {n: i for i, n in enumerate(names)}
    sh = Image.open(D + s + '_4X.png').convert('RGBA'); cols = sh.width // 128
    FR[s] = [sh.crop(((i % cols) * 128, (i // cols) * 160, (i % cols) * 128 + 128, (i // cols) * 160 + 160)) for i in range(len(names))]
assert base - 1 <= 255, base
W, L, Z = 50, 40, 4
T = {}
def put(x, y, z, slot, s, n):
    if not (0 <= x < W and 0 <= y < L and 0 <= z < Z): return
    T.setdefault((x, y, z), [0, 0, 0, 0])[slot] = OFF[s] + IDX[s][n]
def B(x, y, n, z=0, slot=3): put(x, y, z, slot, 'BSCRUB', n)
def Y(x, y, n, z=0, slot=3): put(x, y, z, slot, 'BARNYRD', n)
def R(x, y, n, z=0, slot=3): put(x, y, z, slot, 'RANCH', n)
def obj_at(x, y, z): return T.get((x, y, z), [0] * 4)[3]
r = random.Random(1982)

# ---------------------------------------------------------------- ground
for x in range(W):
    for y in range(L):
        if y >= 35: B(x, y, r.choice(['water_a', 'water_b']), slot=0)
        elif y == 34: B(x, y, 'mud_a', slot=0)
        elif 1 <= x <= 5 and 10 <= y <= 33: B(x, y, r.choice(['sand_a', 'sand_b']), slot=0)
        else: B(x, y, r.choice(['caliche_a', 'caliche_b', 'caliche_c', 'caliche_d', 'scrub_a', 'scrub_b', 'caliche_a', 'caliche_b']), slot=0)
for y in range(0, 11):                                   # ranch road in from the north edge
    B(6, y, 'road_ns_a', slot=0); B(7, y, 'road_ns_b', slot=0)
for x in range(6, 24):                                   # turns east along the fence to the north gate
    B(x, 11, 'road_ew_a', slot=0); B(x, 12, 'road_ew_b', slot=0)
for y in range(11, 13):
    for x in (24, 25): B(x, y, 'road_ns_a' if x == 24 else 'road_ns_b', slot=0)
for x in range(13, 47):                                  # airstrip
    for y in range(2, 8): B(x, y, 'strip_a' if (x + y) % 2 else 'strip_b', slot=0)
for y in range(10, 34):                                  # arroyo banks (sunken creek bed x 1-5)
    B(1, y, 'bank_w', slot=1); B(6, y, 'bank_w', slot=1)
for x in range(1, 6):
    B(x, 10, 'bank_n', slot=2)
R(8, 9, 'ranch_sign')

# ---------------------------------------------------------------- compound fence and gates (x 8-44, y 13-29)
for x in range(8, 45):
    if x in (24, 25): Y(x, 13, 'gate_n', slot=2)
    else: Y(x, 13, 'fence_n', slot=2)
    Y(x, 30, 'fence_n', slot=2)
for y in range(13, 30):
    Y(8, y, 'gate_w' if y == 21 else 'fence_w', slot=1)
    Y(45, y, 'fence_w', slot=1)

# ---------------------------------------------------------------- watchtower (north-east corner)
tx, ty = 43, 14
Y(tx, ty, 'tower_lift', slot=0); Y(tx, ty, 'tower_legs')
Y(tx, ty, 'tower_deck', z=1, slot=0); Y(tx, ty, 'tower_rail_w', z=1, slot=1); Y(tx, ty, 'tower_rail_n', z=1, slot=2)
Y(tx + 1, ty, 'tower_rail_w', z=1, slot=1); Y(tx, ty + 1, 'tower_rail_n', z=1, slot=2)
Y(tx, ty, 'tower_roof', z=2, slot=0)

# ---------------------------------------------------------------- bunkhouse (x 10-16, y 18-24), 1 storey
bx0, bx1, by0, by1 = 10, 16, 18, 24
for x in range(bx0, bx1 + 1):
    for y in range(by0, by1 + 1):
        R(x, y, 'floor_bunk', slot=0); R(x, y, 'roof_house', z=1, slot=0)
for y in range(by0, by1 + 1):
    R(bx0, y, 'bdoor_w' if y == 21 else ('bwin_w' if y in (19, 23) else 'bwall_w'), slot=1)
    R(bx1 + 1, y, 'bdoor_w' if y == 22 else ('bwin_w' if y == 19 else 'bwall_w'), slot=1)
for x in range(bx0, bx1 + 1):
    R(x, by0, 'bwin_n' if x in (12, 15) else 'bwall_n', slot=2)
    R(x, by1 + 1, 'bwin_n' if x == 13 else 'bwall_n', slot=2)
for (x, y, n) in ((11, 18, 'bunk'), (13, 18, 'bunk'), (15, 18, 'bunk'), (11, 24, 'bunk'), (15, 24, 'bunk'),
                  (12, 19, 'footlocker'), (14, 19, 'footlocker'), (12, 23, 'gun_rack'), (13, 21, 'ktable'),
                  (12, 21, 'chair'), (14, 21, 'chair'), (16, 24, 'stove')):
    R(x, y, n)

# ---------------------------------------------------------------- ranch house (x 19-31, y 18-25) + porch (y 16-17), 2 storeys
hx0, hx1, hy0, hy1 = 19, 31, 18, 25
STAIR = {(24, 24): 'stair_lo', (24, 23): 'stair_hi'}
for x in range(hx0, hx1 + 1):
    for y in range(hy0, hy1 + 1):
        kitchen = x >= 26 and y <= 21
        R(x, y, 'floor_lino' if kitchen else ('floor_wood' if (x + y) % 2 else 'floor_wood_b'), slot=0)
        if (x, y) not in STAIR and (x, y) != (24, 22):
            R(x, y, 'floor_wood' if (x + y) % 2 else 'floor_wood_b', z=1, slot=0)    # upstairs floor (open over the stairs)
        R(x, y, 'roof_house', z=2, slot=0)
for (x, y), n in STAIR.items(): R(x, y, n)
for x in range(hx0, hx1 + 1):                            # porch
    for y in (16, 17):
        R(x, y, 'floor_porch', slot=0); R(x, y, 'roof_house', z=1, slot=0)
for x in range(hx0, hx1 + 1, 3): R(x, 16, 'porch_post')
R(hx1, 16, 'porch_post')
for y in (16, 17): R(hx0, y, 'porch_rail_w', slot=1); R(hx1 + 1, y, 'porch_rail_w', slot=1)
for z in (0, 1):                                         # exterior walls, both storeys
    for y in range(hy0, hy1 + 1):
        R(hx0, y, 'hwin_w' if y in (20, 23) else 'hwall_w', z=z, slot=1)
        R(hx1 + 1, y, 'hdoor_w' if (z == 0 and y == 22) else ('hwin_w' if y in (19, 24) else 'hwall_w'), z=z, slot=1)
    for x in range(hx0, hx1 + 1):
        front = 'hdoor_n' if (z == 0 and x == 25) else ('hwin_n' if x in (21, 23, 28, 30) else 'hwall_n')
        back = 'hdoor_n' if (z == 0 and x == 27) else ('hwin_n' if x in (21, 29) else 'hwall_n')
        R(x, hy0, front, z=z, slot=2); R(x, hy1 + 1, back, z=z, slot=2)
for y in range(hy0, hy1 + 1):                            # ground floor: living room | kitchen + hall
    R(26, y, 'idoor_w' if y in (20, 24) else 'iwall_w', slot=1)
for x in range(26, hx1 + 1): R(x, 22, 'idoor_n' if x == 28 else 'iwall_n', slot=2)
for (x, y, n) in ((20, 19, 'sofa'), (20, 21, 'tv'), (22, 19, 'chair'), (19, 24, 'gun_rack'),
                  (27, 18, 'counter'), (28, 18, 'counter_drawer'), (29, 18, 'stove'), (30, 18, 'counter'), (31, 18, 'fridge'),
                  (28, 20, 'ktable'), (27, 20, 'chair'), (29, 20, 'chair'), (30, 24, 'file_cab')):
    R(x, y, n)
for y in range(hy0, hy1 + 1):                            # upstairs: bedroom (west) | boss's office (east)
    R(26, y, 'idoor_w' if y == 23 else 'iwall_w', z=1, slot=1)
for x in range(hx0, 26): R(x, 21, 'idoor_n' if x == 22 else 'iwall_n', z=1, slot=2)
for (x, y, n) in ((20, 18, 'bed'), (22, 18, 'footlocker'), (19, 23, 'chair'),
                  (28, 19, 'desk'), (28, 20, 'office_chair'), (31, 18, 'safe'), (30, 18, 'file_cab'), (31, 21, 'file_cab'), (27, 24, 'sofa')):
    R(x, y, n, z=1)

# ---------------------------------------------------------------- barn / stash barn (x 34-43, y 18-27)
ax0, ax1, ay0, ay1 = 34, 43, 18, 27
for x in range(ax0, ax1 + 1):
    for y in range(ay0, ay1 + 1):
        Y(x, y, 'straw' if r.random() < 0.25 else ('cbarn_a' if (x + y) % 2 else 'cbarn_b'), slot=0)
        Y(x, y, 'roof_tin', z=1, slot=0)
for y in range(ay0, ay1 + 1):
    Y(ax0, y, 'barndoor_w' if y == 22 else ('barnwin_w' if y in (19, 25) else 'barnwall_w'), slot=1)
    Y(ax1 + 1, y, 'barnwall_w', slot=1)
for x in range(ax0, ax1 + 1):
    Y(x, ay0, 'barndoor_n' if x == 38 else ('barnwin_n' if x in (35, 42) else 'barnwall_n'), slot=2)
    Y(x, ay1 + 1, 'barndoor_n' if x == 40 else 'barnwall_n', slot=2)
CRATES = [(36, 20), (37, 20), (36, 21), (40, 20), (41, 20), (41, 21), (36, 25), (37, 25)]
for k, (x, y) in enumerate(CRATES): Y(x, y, ['crate_a', 'crate_b', 'crate_c'][k % 3])
for (x, y, n) in ((39, 23, 'table_scale'), (40, 23, 'table'), (38, 23, 'table'), (42, 26, 'bales'), (42, 25, 'bales'),
                  (35, 26, 'hay'), (37, 17, 'drum'), (39, 17, 'drum'), (33, 22, 'drum'), (33, 23, 'drum')):
    Y(x, y, n)

# ---------------------------------------------------------------- windmill + stock tank (outside, east)
mx, my = 47, 23
Y(mx, my, 'mill_lift', slot=0); Y(mx, my, 'mill_legs'); Y(mx, my, 'mill_deck', z=1, slot=0); Y(mx, my, 'mill_wheel', z=2)
B(46, 25, 'stock_tank')

# ---------------------------------------------------------------- big objects: plane on the strip, pickup, skiff
CELLS = json.load(open('smuggler_cells.json'))
def big(obj, ox, oy):
    for (i, j, l, n) in CELLS[obj]: put(ox + i, oy + j, l, 3, 'SMUGGLR', n)
big('plane', 37, 0)
big('pickup', 31, 9)
big('skiff', 26, 37)
for x in range(27, 31):                                  # boat landing over the water (y 35-36)
    for y in (35, 36): put(x, y, 0, 0, 'SMUGGLR', 'dock_deck_a' if (x + y) % 2 else 'dock_deck_b')
put(27, 36, 0, 3, 'SMUGGLR', 'dock_piling'); put(30, 35, 0, 3, 'SMUGGLR', 'dock_ladder')
for (x, y) in ((40, 9), (41, 9), (42, 9)): Y(x, y, 'bales')        # unloaded bales by the plane's door

for x in range(14, 47, 4):                               # runway edge markers (old tyres, painted white)
    for y in (1, 8):
        if not obj_at(x, y, 0): B(x, y, 'tyre_marker')

# ---------------------------------------------------------------- vegetation, cane, rocks
for x in range(W):                                        # carrizo cane along the bank, path open to the landing
    for y in (31, 32, 33):
        if 26 <= x <= 31: continue
        if r.random() < 0.75 and not obj_at(x, y, 0): B(x, y, 'cane')
def free(x, y):
    inside = 8 <= x <= 45 and 13 <= y <= 30
    strip = 13 <= x <= 46 and 0 <= y <= 9
    lz = x <= 11 and y <= 9
    return not inside and not strip and not lz and not obj_at(x, y, 0) and y < 31 and not (6 <= x <= 7) and not (11 <= y <= 12 and x < 26)
for k in range(70):
    x, y = r.randrange(W), r.randrange(L)
    if free(x, y): B(x, y, r.choice(['mesquite_a', 'mesquite_b', 'prickly_pear', 'prickly_pear', 'rock_a', 'rock_b', 'pebbles']))
for (x, y) in ((2, 14), (4, 19), (3, 26), (2, 30)): B(x, y, r.choice(['rock_a', 'snag']))   # arroyo cover

# ---------------------------------------------------------------- write MAP
data = bytes([L, W, Z])
for z in range(Z - 1, -1, -1):
    for y in range(L):
        for x in range(W): data += bytes(T.get((x, y, z), [0, 0, 0, 0]))
os.makedirs('dist_m1/MAPS', exist_ok=True); open('dist_m1/MAPS/M1RANCH.MAP', 'wb').write(data)

# ---------------------------------------------------------------- routes (RMP)
# rank: 0 civilian, 2 soldier, 4 leader. node = (x, y, level, rank, spawn weight, patrol flag)
N = [
 (40, 8, 0, 2, 6, 3), (43, 9, 0, 2, 6, 3),                 # 0-1 plane unloaders
 (43, 14, 1, 2, 8, 1),                                      # 2 tower guard (deck)
 (11, 20, 0, 2, 6, 2), (14, 22, 0, 2, 6, 2), (15, 20, 0, 2, 6, 2),   # 3-5 bunkhouse
 (22, 16, 0, 2, 6, 4), (28, 16, 0, 2, 6, 4),               # 6-7 porch
 (38, 21, 0, 2, 6, 3),                                      # 8 barn
 (28, 33, 0, 2, 6, 3),                                      # 9 boat landing path
 (29, 20, 1, 4, 10, 0),                                     # 10 the boss, upstairs office
 (41, 4, 0, 0, 5, 0), (42, 27, 0, 0, 5, 0),                # 11-12 civilians: plane cockpit side, barn back corner
 (25, 14, 0, 2, 3, 6),                                      # 13 north gate (guard priority)
 (33, 15, 0, 2, 0, 5), (33, 29, 0, 2, 0, 5), (17, 28, 0, 2, 0, 5), (36, 12, 0, 2, 0, 5),   # 14-17 patrol waypoints
 (25, 27, 0, 2, 0, 5), (24, 22, 0, 2, 0, 2),               # 18 back door, 19 hall
]
LINKS = [(0, 1), (0, 17), (17, 14), (14, 7), (7, 6), (6, 13), (13, 17), (2, 14), (3, 4), (4, 5), (3, 16), (16, 18),
         (18, 15), (15, 8), (8, 14), (18, 9), (9, 15), (19, 6), (19, 18), (10, 19), (11, 0), (12, 8), (5, 6), (12, 15)]
# every node must stand on a free, floored cell: nudge to the nearest one if a prop or the plane is in the way
RECS = [None, None]
for s_, _ in SETS:
    m_ = open(D + s_ + '.MCD', 'rb').read(); RECS += [m_[i * 62:(i + 1) * 62] for i in range(len(m_) // 62)]
def walkable(x, y, z):
    if not (0 <= x < W and 0 <= y < L): return False
    t = T.get((x, y, z), [0] * 4)
    if not t[0]: return False
    return not (t[3] and RECS[t[3]][39] == 255)
for k, nd in enumerate(N):
    x, y, lv = nd[:3]
    if walkable(x, y, lv): continue
    best = min(((abs(dx) + abs(dy), x + dx, y + dy) for dx in range(-4, 5) for dy in range(-4, 5) if walkable(x + dx, y + dy, lv)))
    print('node', k, 'moved', (x, y), '->', best[1:]); N[k] = (best[1], best[2]) + tuple(nd[2:])
adj = {i: [] for i in range(len(N))}
for a, b in LINKS: adj[a].append(b); adj[b].append(a)
rmp = b''
for i, (x, y, lv, rank, w, flag) in enumerate(N):
    rec = bytearray(24); rec[0] = y; rec[1] = x; rec[2] = Z - 1 - lv; rec[3] = 0
    for k in range(5):
        if k < len(adj[i]):
            j = adj[i][k]; dx, dy = N[j][0] - x, N[j][1] - y
            rec[4 + k * 3] = j; rec[5 + k * 3] = min(255, int(round(math.hypot(dx, dy)))); rec[6 + k * 3] = 0
        else:
            rec[4 + k * 3] = 255
    assert len(adj[i]) <= 5, i
    rec[19] = 0; rec[20] = rank; rec[21] = flag; rec[22] = 0; rec[23] = w
    rmp += bytes(rec)
os.makedirs('dist_m1/ROUTES', exist_ok=True); open('dist_m1/ROUTES/M1RANCH.RMP', 'wb').write(rmp)

# ---------------------------------------------------------------- preview (the game's draw order)
setof = []
for s, _ in SETS: setof += [(s, i) for i in range(len(IDX[s]))]
def spr(g): s, i = setof[g - 2]; return FR[s][i]
qx, qy, lv = 64, 32, 96
img = Image.new('RGBA', ((W + L) * qx + 128, (W + L) * qy + Z * lv + 200), (40, 50, 44, 255))
ox, oy = L * qx, Z * lv
for z in range(Z):
    if z >= int(os.environ.get('MAXZ', '9')): break
    for y in range(L):
        for x in range(W):
            t = T.get((x, y, z))
            if not t: continue
            for g in t:
                if g: img.alpha_composite(spr(g), (ox + (x - y) * qx - qx, oy + (x + y) * qy - z * lv))
img.save(os.environ.get('OUT', 'm1ranch_preview.png'))
print('MAP', len(data), 'bytes; RMP', len(N), 'nodes; max part id', max(max(v) for v in T.values()), '; image', img.size)
