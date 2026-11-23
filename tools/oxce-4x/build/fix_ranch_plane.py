"""The cartel ranch's light aircraft came out in broken pieces (John's screens 148, 191).

M1RANCH.MAP places SMUGGLR parts 0..49 in a 7x7 block as if they were the plane in order, but the
SMUGGLR set's parts are numbered differently (0/1 are platforms, the plane's frames are scattered),
so the map assembles the wrong pieces. The stash-house map's plane (STASH set, parts 51..87, drawn
whole on the Cobra cell map) is copied in its place: STASH is appended to the ranch's terrain sets
and the map is written as M1RANCH.MAP2 (2-byte part ids: STASH's ids land past 255).
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, 'mod')
def mcd(s): return os.path.getsize(os.path.join(M, 'TERRAIN', s + '.MCD')) // 62

def load(name):
    d = open(os.path.join(M, 'MAPS', name), 'rb').read()
    Y, X, Z = d[0], d[1], d[2]
    t = list(d[3:])
    return Y, X, Z, t

rY, rX, rZ, r = load('M1RANCH.MAP')
sY, sX, sZ, s = load('STASH1.MAP')
smug0 = 2 + mcd('BSCRUB') + mcd('BARNYRD') + mcd('RANCH')          # SMUGGLR in the ranch's own order
stash_ranch0 = smug0 + mcd('SMUGGLR')                                  # STASH appended after it
stash_map0 = 2 + mcd('JDESERT')                                        # STASH in the stash map's order
def idx(Y, X, Z, x, y, lvl, k): return (((Z - 1 - lvl) * Y + y) * X + x) * 4 + k

# 1. clear the broken plane (SMUGGLR 0..49) round x37..43, y2..8, levels 0..1
cleared = 0
for lvl in (0, 1):
    for y in range(0, 10):
        for x in range(35, 46):
            for k in range(4):
                i = idx(rY, rX, rZ, x, y, lvl, k)
                if smug0 <= r[i] < smug0 + 50: r[i] = 0; cleared += 1
# 2. the stash map's plane (objects 51..87, x5..12 y7..13, its levels 1..2) onto ranch levels 0..1
dx, dy = 32, -5
placed = 0
for lvl in (1, 2):
    for y in range(7, 14):
        for x in range(5, 13):
            v = s[idx(sY, sX, sZ, x, y, lvl, 3)]
            if stash_map0 + 51 <= v <= stash_map0 + 87:
                ti = idx(rY, rX, rZ, x + dx, y + dy, lvl - 1, 3)
                if r[ti] not in (0,): print('overwrites', x + dx, y + dy, lvl - 1, r[ti])
                r[ti] = v - stash_map0 + stash_ranch0; placed += 1
# 3. the loose wing pieces left beside it (SMUGGLR 50..57, x31..34 y9..10): gone
for y in (9, 10):
    for x in range(31, 35):
        for k in range(4):
            i = idx(rY, rX, rZ, x, y, 0, k)
            if smug0 + 50 <= r[i] < smug0 + 58: r[i] = 0; cleared += 1
# 4. the pickup (SMUGGLR 58..65, x26..29 y37..38) had its front in the wrong tile: the stash map's pickup
#    (STASH 116..123, x30..33 y23..24 on its level 1) in its place
for y in (37, 38):
    for x in range(26, 30):
        i = idx(rY, rX, rZ, x, y, 0, 3)
        if smug0 + 58 <= r[i] < smug0 + 66: r[i] = 0
for y in (23, 24):
    for x in range(30, 34):
        v = s[idx(sY, sX, sZ, x, y, 1, 3)]
        if stash_map0 + 116 <= v <= stash_map0 + 123:
            r[idx(rY, rX, rZ, x - 4, y + 14, 0, 3)] = v - stash_map0 + stash_ranch0; placed += 1
out = bytes([rY, rX, rZ]) + b''.join(v.to_bytes(2, 'little') for v in r)
open(os.path.join(M, 'MAPS', 'M1RANCH.MAP2'), 'wb').write(out)
print('cleared', cleared, 'placed', placed, 'STASH at', stash_ranch0)
