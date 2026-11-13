"""Convoy raid map M3CONVOY: two Cobra box trucks stopped on a desert highway (BUILD spec 13 Nov). 50 x 40 x 4, fixed.
GROUND IS LEVEL 1 (z 1): level 0 is solid earth so the dry wash and the culvert can sit one level down.
python3 m3map.py -> dist_m3/MAPS/M3CONVOY.MAP, dist_m3/ROUTES/M3CONVOY.RMP, m3_preview.png (MAXZ=n limits levels drawn)
Terrain order: BLANKS, JDESERT, JROAD, CSEMI. (John 00:33: this mission's convoy is Cobra semis.)"""
import sys, os, json, math, random, importlib
import bpy
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
D = 'dist_m3/TERRAIN/'
SETS = [('JDESERT', 'jdesert'), ('JROAD', 'jroad'), ('CSEMI', 'csemi')]
base = 2; OFF, IDX, FR, RECS = {}, {}, {}, [None, None]
for s, m in SETS:
    names = [n for n, _, _ in importlib.import_module(m).KIT]
    OFF[s] = base; base += len(names); IDX[s] = {n: i for i, n in enumerate(names)}
    sh = Image.open(D + s + '_4X.png').convert('RGBA'); cols = sh.width // 128
    FR[s] = [sh.crop(((i % cols) * 128, (i // cols) * 160, (i % cols) * 128 + 128, (i // cols) * 160 + 160)) for i in range(len(names))]
    mm = open(D + s + '.MCD', 'rb').read(); RECS += [mm[i * 62:(i + 1) * 62] for i in range(len(mm) // 62)]
assert base - 1 <= 255
W, L, Z, G = 50, 40, 4, 1
T = {}
def put(x, y, z, s, n, slot=None):
    if not (0 <= x < W and 0 <= y < L and 0 <= z < Z): return
    g = OFF[s] + IDX[s][n]
    if slot is None: slot = RECS[g][53]                 # floor 0 / west wall 1 / north wall 2 / object 3, from the MCD
    T.setdefault((x, y, z), [0, 0, 0, 0])[slot] = g
def clear(x, y, z, slot):
    if (x, y, z) in T: T[(x, y, z)][slot] = 0
def Dz(x, y, n, z=G): put(x, y, z, 'JDESERT', n)
def Rd(x, y, n, z=G): put(x, y, z, 'JROAD', n)
def Bt(x, y, n, z=G): put(x, y, z, 'CSEMI', n)
def obj(x, y, z): return T.get((x, y, z), [0] * 4)[3]
r = random.Random(1983)
WASH = range(29, 34)
DITCH = [(11, 18), (11, 19), (11, 20), (11, 21)]
CULVERT = [(11, y) for y in range(22, 29)]
HOLES = set()                                          # cells where the ground level is open (looking down into level 0)

# ---------------------------------------------------------------- level 0: earth everywhere except the wash, culvert and ditch
for x in range(W):
    for y in range(L):
        if y in WASH: Dz(x, y, r.choice(['wash_a', 'wash_b']), z=0); HOLES.add((x, y))
        elif (x, y) in CULVERT: Rd(x, y, 'culvert_floor', z=0)
        elif (x, y) in DITCH: Dz(x, y, r.choice(['sand_a', 'sand_b']), z=0); HOLES.add((x, y))
        else: Dz(x, y, 'earth_a' if (x * 7 + y * 3) % 5 else 'earth_b', z=0)
Dz(10, 28, 'headwall', z=0); Dz(12, 28, 'headwall', z=0)
Dz(11, 19, 'ramp_n_lo', z=0); Dz(11, 18, 'ramp_n_hi', z=0)                 # ditch climbs north out of the culvert
for (x, lo, hi) in ((6, 32, 33), (17, 32, 33)):                             # wash exits south (LZ side)
    Dz(x, lo, 'ramp_s_lo', z=0); Dz(x, hi, 'ramp_s_hi', z=0)
for (x, lo, hi) in ((25, 30, 29), (40, 30, 29), (46, 30, 29)):              # wash exits north (toward the trucks)
    Dz(x, lo, 'ramp_n_lo', z=0); Dz(x, hi, 'ramp_n_hi', z=0)
for k in range(14):                                                          # rocks and scrub in the wash bed
    x, y = r.randrange(W), r.choice(list(WASH))
    if not obj(x, y, 0) and x not in (6, 11, 17, 25, 40, 46): Dz(x, y, r.choice(['rocks_a', 'rocks_b', 'scrub_a', 'deadtree']), z=0)

# ---------------------------------------------------------------- level 1: ground
for x in range(W):
    for y in range(L):
        if (x, y) in HOLES: continue
        if 22 <= y <= 27: continue                                           # highway laid below
        if 34 <= y and x <= 10: Dz(x, y, r.choice(['dirt_a', 'dirt_b']))     # LZ: flat packed dirt
        elif 13 <= y <= 19 and 38 <= x <= 46: Dz(x, y, r.choice(['gravel_a', 'gravel_b']))
        else: Dz(x, y, r.choice(['sand_a', 'sand_b', 'sand_c', 'dirt_a', 'sand_a', 'sand_b']))
ROWS = {22: 'shoulder', 23: 'asphalt_edge_n', 24: 'asphalt', 25: 'asphalt_lane', 26: 'asphalt_edge_s', 27: 'shoulder'}
for x in range(W):
    for y, k in ROWS.items():
        if k == 'shoulder': Rd(x, y, r.choice(['shoulder_a', 'shoulder_b']))
        elif k == 'asphalt': Rd(x, y, r.choice(['asphalt_a', 'asphalt_b']))
        else: Rd(x, y, k)
for y in range(22, 28): Rd(40, y, 'spike_strip')
for x in range(38, 40):
    for y in (25, 26): Rd(x, y, 'asphalt_skid')
for x in (20, 21):
    for y in (25, 26): Rd(x, y, 'asphalt_skid')

# ---------------------------------------------------------------- ridge (x 6-44, y 2-9): one level up, a two-level core
def ridge_cell(x, y):
    if not (6 <= x <= 44 and 2 <= y <= 9): return 0
    edge = min(x - 6, 44 - x, y - 2, 9 - y)
    if edge == 0 and r.random() < 0.35: return 0
    core = 14 <= x <= 36 and 2 <= y <= 6 and not (min(x - 14, 36 - x, y - 2, 6 - y) == 0 and r.random() < 0.3)
    return 2 if core else 1
R = {(x, y): ridge_cell(x, y) for x in range(W) for y in range(L)}
for (x, y), h in R.items():
    for k in range(h): Dz(x, y, r.choice(['rock_a', 'rock_b', 'rock_c']), z=G + k)
    if h: Dz(x, y, r.choice(['rockfloor_a', 'rockfloor_b', 'rockfloor_c']), z=G + h)
for (x, lo, hi) in ((12, 10, 9), (30, 10, 9), (42, 10, 9)):                  # ramps up onto the ridge from the slope
    R[(x, hi)] = 0; clear(x, hi, G, 3); clear(x, hi, G + 1, 0)
    Dz(x, lo, 'ramp_n_lo'); Dz(x, hi, 'ramp_n_hi'); Dz(x, hi, 'rockfloor_a')
    if not R.get((x, hi - 1)): R[(x, hi - 1)] = 1; Dz(x, hi - 1, 'rock_a'); Dz(x, hi - 1, 'rockfloor_b', z=G + 1)
for (x, lo, hi) in ((20, 7, 6), (32, 7, 6)):                                 # ramps up onto the core
    if R.get((x, lo)) != 1: R[(x, lo)] = 1; Dz(x, lo, 'rock_a'); Dz(x, lo, 'rockfloor_a', z=G + 1)
    R[(x, hi)] = 1; clear(x, hi, G + 1, 3); clear(x, hi, G + 2, 0)
    Dz(x, lo, 'ramp_n_lo', z=G + 1); Dz(x, hi, 'ramp_n_hi', z=G + 1); Dz(x, hi, 'rockfloor_c', z=G + 1)
    if R.get((x, hi - 1)) != 2:
        R[(x, hi - 1)] = 2; Dz(x, hi - 1, 'rock_b', z=G + 1); Dz(x, hi - 1, 'rockfloor_a', z=G + 2)
for k in range(26):                                                          # boulders and rocks on the ridge tops (cover up there)
    x, y = r.randrange(6, 45), r.randrange(2, 10)
    h = R.get((x, y), 0)
    if h and not obj(x, y, G + h) and (x, y) not in ((12, 9), (30, 9), (42, 9), (20, 6), (32, 6), (20, 7), (32, 7), (12, 8), (30, 8), (42, 8), (20, 5), (32, 5)):
        Dz(x, y, r.choice(['boulder_a', 'boulder_b', 'rocks_a', 'rocks_b', 'scrub_b']), z=G + h)

# ---------------------------------------------------------------- scrub slope (y 10-21): no cover except a few thin cacti
for k in range(80):
    x, y = r.randrange(W), r.randrange(10, 22)
    if (x, y) in HOLES or obj(x, y, G) or (38 <= x <= 46 and 13 <= y <= 19) or (x, y) in ((12, 10), (30, 10), (42, 10)): continue
    Dz(x, y, r.choice(['scrub_a', 'scrub_b', 'scrub_c', 'scrub_a', 'cactus_a', 'cactus_b']) if k % 7 else 'deadtree')
for k in range(40):                                                          # scrub south of the road and round the LZ
    x, y = r.randrange(W), r.choice([28, 34, 35, 36, 37, 38, 39])
    if (x, y) in HOLES or obj(x, y, G) or (x <= 11 and y >= 34) or (x, y) == (11, 28): continue
    Dz(x, y, r.choice(['scrub_a', 'scrub_b', 'scrub_c', 'cactus_a', 'rocks_a']))

# ---------------------------------------------------------------- road-crew yard (x 38-46, y 13-19)
JR = json.load(open('jroad_cells.json'))
def big(obj_, ox, oy, z0=G):
    for (i, j, l, n) in JR[obj_]: put(ox + i, oy + j, z0 + l, 'JROAD', n)
big('grader', 39, 13)
tx0, tx1, ty0, ty1 = 42, 45, 16, 18                                          # site trailer, one room
for x in range(tx0, tx1 + 1):
    for y in range(ty0, ty1 + 1): Rd(x, y, 'trailer_floor'); Rd(x, y, 'trailer_roof', z=G + 1)
for y in range(ty0, ty1 + 1):
    Rd(tx0, y, 'trailer_door_w' if y == 17 else 'trailer_wall_w'); Rd(tx1 + 1, y, 'trailer_win_w' if y == 17 else 'trailer_wall_w')
for x in range(tx0, tx1 + 1):
    Rd(x, ty0, 'trailer_win_n' if x in (43, 45) else 'trailer_wall_n'); Rd(x, ty1 + 1, 'trailer_win_n' if x == 44 else 'trailer_wall_n')
Rd(44, 17, 'plan_table'); Rd(45, 16, 'locker')
for (x, y, n) in ((38, 17, 'gravel_pile_a'), (39, 18, 'gravel_pile_b'), (46, 13, 'gravel_pile_a'), (40, 19, 'cones'), (44, 20, 'barrier'), (38, 20, 'cones')):
    Rd(x, y, n)

# ---------------------------------------------------------------- billboard (x 24-26, y 19), poles, burnt car
big('billboard', 24, 19)
Rd(25, 19, 'bb_lift'); Rd(25, 19, 'bb_ladder')
Rd(24, 19, 'bb_deck', z=G + 1); Rd(26, 19, 'bb_deck', z=G + 1); Rd(25, 19, 'bb_liftdeck', z=G + 1)
for x in range(2, W, 6):
    if x == 11 or (24 <= x <= 26): x += 1
    if obj(x, 21, G): continue
    Rd(x, 21, 'pole_lo'); Rd(x, 21, 'pole_hi', z=G + 1)
big('car', 3, 22)

# ---------------------------------------------------------------- the two Cobra semis (16 x 2: trailer i 0-9, deck 10-11, sleeper 12, cab 13, hood 14-15)
SC = json.load(open('csemi_cells.json'))
def semi(ox, oy):
    for i in range(10):
        for j in range(2):
            Bt(ox + i, oy + j, 'trl_floor'); Bt(ox + i, oy + j, 'trl_roof', z=G + 2)
        Bt(ox + i, oy, 'trl_side_lo'); Bt(ox + i, oy, 'trl_side_hi', z=G + 1)     # north side: wheels would sit outside, unseen
    for (i, j, l, n) in SC['trls_ok']: put(ox + i, oy + j, G + l, 'CSEMI', n, slot=2)
    for j in range(2):
        Bt(ox, oy + j, 'trl_rear'); Bt(ox, oy + j, 'trl_rear_hi', z=G + 1)
        Bt(ox + 10, oy + j, 'trl_front_lo'); Bt(ox + 10, oy + j, 'trl_front_hi', z=G + 1)
        for i in (10, 11): Bt(ox + i, oy + j, 'deck_floor')
        Bt(ox + 12, oy + j, 'sleeper_floor'); Bt(ox + 13, oy + j, 'cab_floor')
        Bt(ox + 12, oy + j, 'cab_roof', z=G + 1); Bt(ox + 13, oy + j, 'cab_roof', z=G + 1)
        Bt(ox + 12, oy + j, 'sleeper_back'); Bt(ox + 14, oy + j, 'windscreen')
    for i in (10, 11): Bt(ox + i, oy, 'deck_side'); Bt(ox + i, oy + 2, 'deck_side')
    Bt(ox + 12, oy, 'sleeper_side'); Bt(ox + 12, oy + 2, 'sleeper_side')
    Bt(ox + 13, oy, 'cab_door'); Bt(ox + 13, oy + 2, 'cab_door')
    Bt(ox + 12, oy, 'stacks', z=G + 1)
    for (i, j, l, n) in SC['hood_ok']: put(ox + 14 + i, oy + j, G + l, 'CSEMI', n)
    Bt(ox + 12, oy - 1, 'fuel_tank'); Bt(ox + 12, oy + 2, 'fuel_tank')
    Bt(ox + 13, oy, 'lockbox')                                              # the rig's paperwork (clue spot: vehicle)
    for (i, j) in ((2, 0), (4, 0), (6, 0), (8, 0), (3, 1), (5, 1), (7, 1), (9, 1)):     # Cobra crates (open like doors), staggered
        Bt(ox + i, oy + j, 'crate_a' if (i + j) % 3 else 'crate_b')
semi(4, 25)      # rig 2 (rear)
semi(22, 25)     # rig 1 (lead), stopped short of the spike strip at x 40

# ---------------------------------------------------------------- blue marker tiles on every clue spot and reward spot (John 01:09)
SHOW_SPOTS = os.environ.get('SHOW_SPOTS', '1') == '1'     # set SHOW_SPOTS=0 to build the map without the markers
def _free_floor(x, y, z):
    t = T.get((x, y, z), [0] * 4)
    return bool(t[0]) and not (t[3] and RECS[t[3]][39] == 255)
def cells_with(set_, names, z=G):
    ids = [OFF[set_] + IDX[set_][n] for n in names]
    return sorted([[x, y, zz] for (x, y, zz), t in T.items() if zz == z and t[3] in ids])
LOOKOUT = sorted([[x, y, G + 2] for (x, y), h in R.items() if h == 2 and x >= 31 and _free_floor(x, y, G + 2)])
LOOKOUT += [[24, 19, G + 1], [26, 19, G + 1]]                       # billboard deck (the middle cell is the ladder lift: left alone)
CLUE_CELLS = cells_with('CSEMI', ['crate_a', 'crate_b']) + cells_with('CSEMI', ['lockbox']) + cells_with('JROAD', ['plan_table', 'locker'])
REWARD_CELLS = (LOOKOUT + [[11, 28, 0], [11, 18, 0], [25, 30, 0], [40, 30, 0], [46, 30, 0]]           # culvert mouth, ditch, wash ramps
                + cells_with('CSEMI', ['fuel_tank'])
                + [[4, 25, G], [4, 26, G], [22, 25, G], [22, 26, G], [17, 26, G], [35, 26, G]])            # breach: trailer rear doors, cab doors
if SHOW_SPOTS:
    for (x, y, z) in CLUE_CELLS: put(x, y, z, 'JDESERT', 'spot_clue', slot=0)
    for (x, y, z) in REWARD_CELLS:
        if [x, y, z] not in CLUE_CELLS: put(x, y, z, 'JDESERT', 'spot_reward', slot=0)

# ---------------------------------------------------------------- write MAP
data = bytes([L, W, Z])
for z in range(Z - 1, -1, -1):
    for y in range(L):
        for x in range(W): data += bytes(T.get((x, y, z), [0, 0, 0, 0]))
os.makedirs('dist_m3/MAPS', exist_ok=True); open('dist_m3/MAPS/M3CONVOY.MAP', 'wb').write(data)

# ---------------------------------------------------------------- routes
def walkable(x, y, z):
    if not (0 <= x < W and 0 <= y < L): return False
    t = T.get((x, y, z), [0] * 4)
    return bool(t[0]) and not (t[3] and RECS[t[3]][39] == 255)
# (x, y, level, rank, spawn weight, patrol flag, unit type)   rank: 1 XCOM, 2 soldier, 4 leader
N = [(17, 26, G, 2, 8, 1, 0), (35, 26, G, 2, 8, 1, 0),                     # 0-1 drivers, in each cab
     (3, 24, G, 2, 6, 4, 0), (3, 28, G, 2, 6, 4, 0), (38, 24, G, 2, 6, 4, 0), (38, 28, G, 2, 6, 4, 0),   # 2-5 corner guards
     (33, 24, G, 4, 10, 2, 0),                                                # 6 officer beside the lead rig
     (41, 16, G, 2, 6, 3, 0),                                                 # 7 lookout in the yard
     (20, 26, G, 2, 3, 10, 0),                                                # 8 the gap between the rigs: high guard priority
     (20, 23, G, 2, 0, 5, 0), (20, 28, G, 2, 0, 5, 0), (10, 22, G, 2, 0, 5, 0), (16, 22, G, 2, 0, 5, 0),
     (30, 22, G, 2, 0, 5, 0), (42, 22, G, 2, 0, 5, 0), (40, 19, G, 2, 0, 5, 0), (43, 14, G, 2, 0, 4, 0),  # 9-16 patrol
     (48, 23, G, 2, 0, 3, 0), (48, 24, G, 2, 0, 3, 0), (48, 25, G, 2, 0, 3, 0), (48, 26, G, 2, 0, 3, 0)]  # 17-20 reinforcement edge
for k, nd in enumerate(N):
    x, y, lv = nd[:3]
    if walkable(x, y, lv): continue
    best = min(((abs(dx) + abs(dy), x + dx, y + dy) for dx in range(-3, 4) for dy in range(-3, 4) if walkable(x + dx, y + dy, lv)))
    print('node', k, 'moved', (x, y), '->', best[1:]); N[k] = (best[1], best[2]) + tuple(nd[2:])
LZN = [(x, y, G, 1, 5, 0, 0) for y in (34, 35, 36, 37, 38) for x in (2, 4, 6, 8, 10)]
LINKS = [(2, 9, 0), (9, 4, 0), (4, 5, 0), (5, 10, 0), (10, 3, 0), (3, 2, 0), (8, 9, 0), (8, 10, 0), (6, 4, 0), (6, 9, 0),
         (0, 10, 0), (1, 5, 0), (2, 11, 4), (11, 12, 4), (12, 13, 4), (13, 14, 4), (14, 15, 0), (15, 7, 0), (7, 16, 0),
         (14, 17, 4), (17, 18, 4), (18, 19, 4), (19, 20, 4), (20, 4, 4), (13, 9, 4)]
adj = {i: [] for i in range(len(N))}
for a, b, t in LINKS: adj[a].append((b, t)); adj[b].append((a, t))
ALL = N + LZN
rmp = b''
for i, (x, y, lv, rank, w, flag, utype) in enumerate(ALL):
    rec = bytearray(24); rec[0] = y; rec[1] = x; rec[2] = Z - 1 - lv
    links = adj.get(i, [])
    assert len(links) <= 5, i
    for k in range(5):
        if k < len(links):
            j, t = links[k]; rec[4 + k * 3] = j; rec[5 + k * 3] = min(255, int(round(math.hypot(N[j][0] - x, N[j][1] - y)))); rec[6 + k * 3] = t
        else: rec[4 + k * 3] = 255
    rec[19] = utype; rec[20] = rank; rec[21] = flag; rec[23] = w
    rmp += bytes(rec)
os.makedirs('dist_m3/ROUTES', exist_ok=True); open('dist_m3/ROUTES/M3CONVOY.RMP', 'wb').write(rmp)
bad = [i for i, nd in enumerate(ALL) if not walkable(nd[0], nd[1], nd[2])]

# ---------------------------------------------------------------- preview
setof = []
for s, _ in SETS: setof += [(s, i) for i in range(len(IDX[s]))]
missing = 0
def spr(g):
    global missing
    if g - 2 >= len(setof): missing += 1; return None
    s, i = setof[g - 2]; return FR[s][i]
qx, qy, lv = 64, 32, 96
img = Image.new('RGBA', ((W + L) * qx + 128, (W + L) * qy + Z * lv + 200), (40, 50, 44, 255))
ox, oy = L * qx, Z * lv
mz = int(os.environ.get('MAXZ', '9'))
for z in range(min(Z, mz)):
    for y in range(L):
        for x in range(W):
            t = T.get((x, y, z))
            if not t: continue
            for g in t:
                if g:
                    sp = spr(g)
                    if sp: img.alpha_composite(sp, (ox + (x - y) * qx - qx, oy + (x + y) * qy - z * lv))
img.save(os.environ.get('OUT', 'm3_preview.png'))
print('MAP', len(data), 'bytes; nodes', len(ALL), '(bad', bad, '); max id', max(max(v) for v in T.values()), 'of', base - 1, '; missing ids', missing)

# ---------------------------------------------------------------- smart-play spots + clue spots (SMART_PLAY_SPOTS.md, CLUE_SYSTEM_DESIGN.md) -> JSON for BUILD
lookout = LOOKOUT + [[25, 19, G + 1]]
spots = {
    'blue_tiles': 'spot_clue (ring) on clue spots, spot_reward (star) on reward spots; build with SHOW_SPOTS=0 for none',
    'note': 'tile coords [x, y, level]; ground is level 1. lookout = warn of reinforcements one turn early (Joe standing there at the start of the enemy turn).',
    'lookout': lookout,
    'reinforcement_edge': [[48, y, G] for y in (23, 24, 25, 26)],
    'key_man': {'route_node': 6, 'what': 'Cobra officer beside the lead rig: alive = reinforcement timer runs (BUILD rule); take him alive = living clue'},
    'hidden_routes': {'culvert': [[11, y, 0] for y in range(18, 29)], 'dry_wash': 'y 29-33 on level 0, ramps up at x 25/40/46 (north) and x 6/17 (south)'},
    'perch': {'billboard_deck': [[24, 19, G + 1], [25, 19, G + 1], [26, 19, G + 1]], 'ridge': 'every rock top, level 2-3'},
    'use_the_environment': {'fuel_tanks': cells_with('CSEMI', ['fuel_tank'])},
    'breach_points': {'trailer_rear_doors': [[4, 25, G], [4, 26, G], [22, 25, G], [22, 26, G]],
                      'cab_doors': 'north and south side of each cab (x 17 and 35)', 'trailer_roofs': 'level 3, thin'},
    'careful_with_explosives': 'cargo crates inside the trailers: blast them and the paper clues burn',
    'clue_spots': {'crate': cells_with('CSEMI', ['crate_a', 'crate_b']),
                   'vehicle': cells_with('CSEMI', ['lockbox']),
                   'desk': cells_with('JROAD', ['plan_table']),
                   'cabinet': cells_with('JROAD', ['locker']),
                   'body': 'officer (node 6), drivers (nodes 0, 1)'},
}
json.dump(spots, open('dist_m3/M3CONVOY_spots.json', 'w'), indent=1)
print('lookout tiles', len(lookout), '; crate spots', len(spots['clue_spots']['crate']), '; vehicle spots', spots['clue_spots']['vehicle'])
