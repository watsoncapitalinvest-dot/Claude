"""generic: python3 build_set.py <module> <rendered dir> <dist dir>   -> TERRAIN/<SET>.* (+_4X, _4X.png, MCD)
MCDSPEC override keys: die/alt (part names), loft (12 ints), walk (TU walk/slide/fly), walkonly (TU walk/slide),
door, los, he (explosive strength), tlevel, block, lift (gravlift flag)."""
import sys, os, glob, importlib
import bpy, struct  # set modules import bmesh
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xcom import mcd as vmcd, palette
bp = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build.py')).read()
exec(bp[bp.index('PAL = palette(4)'):bp.index('files = sorted')])           # quant(), pck()
from xcom import palette
mod = importlib.import_module(sys.argv[1]); SRC, DST = sys.argv[2], sys.argv[3]; SET = mod.SET
os.makedirs(os.path.join(DST, 'TERRAIN'), exist_ok=True)
names = [n for n, _, _ in mod.KIT]
files = [os.path.join(SRC, '%02d_%s.png' % (i, n)) for i, n in enumerate(names)]
assert all(os.path.exists(f) for f in files), [f for f in files if not os.path.exists(f)]
IDX = {n: i for i, n in enumerate(names)}
hd = [quant(f, 128, 160) for f in files]; lo = [quant(f, 32, 40) for f in files]
for suf, fr in (('_4X', hd), ('', lo)):
    d, t = pck(fr)
    open(os.path.join(DST, 'TERRAIN', SET + suf + '.PCK'), 'wb').write(d)
    open(os.path.join(DST, 'TERRAIN', SET + suf + '.TAB'), 'wb').write(t)
COLS = 8; rows = (len(files) + COLS - 1) // COLS
sheet = Image.new('RGBA', (COLS * 128, rows * 160), (0, 0, 0, 0))
for i, f in enumerate(files): sheet.paste(Image.open(f).convert('RGBA'), ((i % COLS) * 128, (i // COLS) * 160))
sheet.save(os.path.join(DST, 'TERRAIN', SET + '_4X.png'))
V = {}
def rec(name):
    st, r, kw = mod.MCDSPEC[name]
    if st not in V: V[st] = vmcd(st)
    e = bytearray(V[st][r]); i = IDX[name]
    for q in range(8): e[q] = i
    e[44] = 0; e[46] = 0
    for k, v in kw.items():
        if k == 'die': e[44] = IDX[v]
        elif k == 'alt': e[46] = IDX[v]
        elif k == 'loft': e[8:20] = bytes(v)
        elif k == 'walk': e[39] = v; e[40] = v; e[41] = v
        elif k == 'walkonly': e[39] = v; e[40] = v
        elif k == 'door': e[35] = v
        elif k == 'los': e[31] = v
        elif k == 'he': e[54] = 0; e[55] = v
        elif k == 'tlevel': e[48] = v & 0xFF
        elif k == 'block': e[36] = v; e[37] = v
        elif k == 'lift': e[34] = v
        elif k == 'type': e[53] = v
        elif k == 'armor': e[42] = v
        elif k == 'ufodoor': e[30] = v
        elif k == 'frames': e[0:8] = bytes(IDX[n] for n in v)
        elif k == 'fuel': e[57] = v
        elif k == 'flam': e[45] = v
        elif k == 'special': e[59] = v
        elif k == 'he_type': e[54] = v
        else: raise KeyError(k)
    return e
missing = set(names) - set(mod.MCDSPEC); assert not missing, missing
open(os.path.join(DST, 'TERRAIN', SET + '.MCD'), 'wb').write(b''.join(bytes(rec(n)) for n in names))
print(SET, len(names), 'parts')
