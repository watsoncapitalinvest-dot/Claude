"""PILOTBRN game files from the rendered kit (out/NN_name.png, 128x160 RGBA).

Writes into <dst>/:
  TERRAIN/PILOTBRN.PCK/.TAB      32x40 fallback (palettised)
  TERRAIN/PILOTBRN_4X.PCK/.TAB   128x160 palettised (mask + fallback), same frame order
  TERRAIN/PILOTBRN_4X.png        128x160 full-colour frames in a grid (the fork's HiColor path)
  TERRAIN/PILOTBRN.MCD           one record per part, cloned from vanilla records with the right behaviour
  MAPS/PILOTBRN.MAP, PILOTLZ.MAP 10x10x4 blocks; ROUTES/*.RMP
  Ruleset/pilot_maps.rul
PCK/TAB writers and the palette quantiser are BUILD's (tools/oxce-4x/build/maps/build_terrain.py).
"""
import sys, os, glob, struct, random
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xcom import palette, mcd as vmcd

SRC, DST = sys.argv[1], sys.argv[2]
SET = 'PILOTBRN'
for d in ('TERRAIN', 'MAPS', 'ROUTES', 'Ruleset'): os.makedirs(os.path.join(DST, d), exist_ok=True)

# ---- BUILD's quantiser + PCK writer (unchanged logic)
PAL = palette(4).astype(np.int32); USE = np.arange(1, 255); UP = PAL[USE]
def quant(path, fw, fh):
    im = Image.open(path).convert('RGBA'); big = np.array(im).astype(np.float32); k = im.width // fw
    a = big[..., 3:4] / 255.; pre = np.concatenate([big[..., :3] * a, a], -1).reshape(fh, k, fw, k, 4).mean((1, 3))
    al = pre[..., 3]; m = al > 0.5; rgb = np.where(al[..., None] > 0, pre[..., :3] / np.maximum(al[..., None], 1e-6), 0)
    idx = np.zeros((fh, fw), np.uint8); f = rgb[m]
    idx[m] = USE[np.argmin(((f[:, None, :] - UP[None]) ** 2).sum(-1), 1)]; return idx
def pck(frames):
    data = b''; offs = []
    for f in frames:
        offs.append(len(data)); h, w = f.shape; rows = 0
        while rows < h and not f[rows].any(): rows += 1
        out = bytearray([min(rows, 254)]); flat = f[rows:].ravel(); i = 0; n = len(flat)
        last = n
        while last > 0 and flat[last - 1] == 0: last -= 1
        while i < last:
            if flat[i] == 0:
                j = i
                while j < last and flat[j] == 0 and j - i < 255: j += 1
                out += bytes([254, j - i]); i = j
            else: out.append(int(flat[i]) if flat[i] not in (254, 255) else 253); i += 1
        out.append(255); data += bytes(out)
    tab = b''.join(struct.pack('<I', o) for o in offs)
    return data, tab

files = sorted(glob.glob(os.path.join(SRC, '*.png')))
names = [os.path.basename(f)[3:-4] for f in files]
IDX = {n: i for i, n in enumerate(names)}
hd = [quant(f, 128, 160) for f in files]
lo = [quant(f, 32, 40) for f in files]
for suf, fr in (('_4X', hd), ('', lo)):
    d, t = pck(fr)
    open(os.path.join(DST, 'TERRAIN', SET + suf + '.PCK'), 'wb').write(d)
    open(os.path.join(DST, 'TERRAIN', SET + suf + '.TAB'), 'wb').write(t)
COLS = 8; rows = (len(files) + COLS - 1) // COLS
sheet = Image.new('RGBA', (COLS * 128, rows * 160), (0, 0, 0, 0))
for i, f in enumerate(files): sheet.paste(Image.open(f).convert('RGBA'), ((i % COLS) * 128, (i // COLS) * 160))
sheet.save(os.path.join(DST, 'TERRAIN', SET + '_4X.png'))

# ---- MCD: clone a vanilla record with the right behaviour, then retarget frames / links
B, D, U, F = vmcd('BARN'), vmcd('DESERT'), vmcd('URBITS'), vmcd('FRNITURE')
def rec(tpl, name, **kw):
    e = bytearray(tpl); i = IDX[name]
    for q in range(8): e[q] = i                       # all 8 animation frames -> this part's frame
    e[44] = 0; e[46] = 0                              # die / alt: none unless set below
    for k, v in kw.items():
        if k == 'die': e[44] = IDX[v]
        elif k == 'alt': e[46] = IDX[v]
        elif k == 'loft': e[8:20] = bytes(v)
        elif k == 'walk': e[39] = v; e[40] = v; e[41] = v
        elif k == 'door': e[35] = v
        elif k == 'los': e[31] = v
        elif k == 'he': e[54] = 0; e[55] = v              # HE type 0 (explosive), strength
        elif k == 'tlevel': e[48] = v & 0xFF
        elif k == 'block': e[36] = v; e[37] = v           # blocks fire / smoke
    return e
OPEN = dict(loft=[0] * 12, walk=0, los=0, block=0, door=0)
R = {
    'caliche':         rec(D[0], 'caliche'),
    'scrub':           rec(D[1], 'scrub'),
    'concrete':        rec(D[21], 'concrete'),
    'barnwall_w':      rec(B[6], 'barnwall_w'),                    # west wall, LOFT 9, blocks sight
    'barnwall_n':      rec(B[5], 'barnwall_n'),                    # north wall, LOFT 10
    'barndoor_w':      rec(B[17], 'barndoor_w', alt='barndoor_w_open'),   # normal door -> swaps to open
    'barndoor_w_open': rec(B[6], 'barndoor_w_open', **OPEN),
    'crate':           rec(F[17], 'crate', alt='crate_open'),       # alt = opened crate (clue system: BUILD wires the open)
    'crate_open':      rec(F[17], 'crate_open', loft=[33] * 5 + [0] * 7, tlevel=-10),
    'drum':            rec(U[24], 'drum', he=60),                   # explodes
    'fence_n':         rec(U[13], 'fence_n'),                       # see-through chain link (stock fence LOFT 16)
    'gate_n':          rec(U[13], 'gate_n', door=1, walk=8, alt='gate_n_open'),
    'gate_n_open':     rec(U[13], 'gate_n_open', **OPEN),
    'bush':            rec(D[10], 'bush'),
    'rock':            rec(D[12], 'rock'),
}
assert set(R) == set(names), (set(R) ^ set(names))
open(os.path.join(DST, 'TERRAIN', SET + '.MCD'), 'wb').write(b''.join(bytes(R[n]) for n in names))

# ---- MAP blocks (BLANKS is mapDataSet 0 with 2 records, so part i is written as 2 + i)
W = Lm = 10; Z = 4
def block(tiles):
    data = bytes([Lm, W, Z])
    for z in range(Z - 1, -1, -1):
        for y in range(Lm):
            for x in range(W):
                t = tiles.get((x, y, z), [None] * 4)
                data += bytes([0 if p is None else 2 + IDX[p] for p in t])
    return data
rnd = random.Random(7)
T = {}
def put(x, y, slot, name, z=0):
    T.setdefault((x, y, z), [None] * 4)[slot] = name
for x in range(10):
    for y in range(10):
        inside = 5 <= x <= 9 and y <= 4
        put(x, y, 0, 'concrete' if inside else ('scrub' if (x < 4 and rnd.random() < 0.45) or rnd.random() < 0.12 else 'caliche'))
for y in range(5):
    put(5, y, 1, 'barndoor_w' if y == 2 else 'barnwall_w')     # barn west wall with the door
for x in range(5, 10):
    put(x, 5, 2, 'barnwall_n')                                    # barn south wall (north wall of row 5)
    put(x, 0, 2, 'barnwall_n')                                    # barn north wall on the block edge
for (x, y) in ((6, 1), (7, 1), (6, 3)): put(x, y, 3, 'crate')
put(8, 3, 3, 'crate_open')
for (x, y) in ((4, 1), (4, 3), (9, 4)): put(x, y, 3, 'drum')
for x in range(10): put(x, 8, 2, 'gate_n' if x == 2 else 'fence_n')
for (x, y) in ((1, 2), (3, 6), (8, 9), (0, 9)): put(x, y, 3, 'bush')
for (x, y) in ((1, 5), (6, 9)): put(x, y, 3, 'rock')
open(os.path.join(DST, 'MAPS', 'PILOTBRN.MAP'), 'wb').write(block(T))
LZ = {}
r2 = random.Random(9)
for x in range(10):
    for y in range(10):
        LZ[(x, y, 0)] = ['scrub' if r2.random() < 0.2 else 'caliche', None, None, None]
open(os.path.join(DST, 'MAPS', 'PILOTLZ.MAP'), 'wb').write(block(LZ))

# ---- RMP: 4 linked nodes on PILOTBRN (alien soldier rank, weight 5); bytes: y, x, z-from-top
def node(x, y, links, rank=2, weight=5, flag=3):
    b = bytearray([y, x, Z - 1, 0])
    for k in range(5):
        if k < len(links): tgt, dist = links[k]; b += bytes([tgt, dist, 0])
        else: b += bytes([255, 0, 0])
    b += bytes([0, rank, flag, 0, weight]); assert len(b) == 24; return bytes(b)
N = [(3, 3), (7, 6), (2, 6), (7, 2)]
def dist(a, b): return int(round(((N[a][0] - N[b][0]) ** 2 + (N[a][1] - N[b][1]) ** 2) ** 0.5))
links = {0: [1, 2, 3], 1: [0, 2], 2: [0, 1], 3: [0]}
rmp = b''.join(node(N[i][0], N[i][1], [(j, dist(i, j)) for j in links[i]]) for i in range(4))
open(os.path.join(DST, 'ROUTES', 'PILOTBRN.RMP'), 'wb').write(rmp)
open(os.path.join(DST, 'ROUTES', 'PILOTLZ.RMP'), 'wb').write(b'')

open(os.path.join(DST, 'Ruleset', 'pilot_maps.rul'), 'w').write("""# MAPS pilot: one barnyard block (PILOTBRN) + a flat landing-zone block (PILOTLZ), 4x full-colour terrain.
terrains:
  - name: PILOTBRN
    mapDataSets:
      - BLANKS
      - PILOTBRN
    mapBlocks:
      - name: PILOTBRN
        width: 10
        length: 10
        height: 4
        groups: [0]
      - name: PILOTLZ
        width: 10
        length: 10
        height: 4
        groups: [1]
""")
print('parts', len(names), names)
print('mcd bytes', len(names) * 62, ' map', os.path.getsize(os.path.join(DST, 'MAPS', 'PILOTBRN.MAP')))
