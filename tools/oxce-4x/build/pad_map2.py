"""Pad a .MAP2 to a multiple of 10 on each side (OpenXcom map blocks must be). The pad is empty
(no tiles) past the east and south edges, so route node positions stay valid.
usage: python3 build/pad_map2.py mod/MAPS/HQAIR.MAP2"""
import struct, sys
p = sys.argv[1]
b = open(p, 'rb').read()
Y, X, Z = b[0], b[1], b[2]
v = struct.unpack('<%dH' % ((len(b) - 3) // 2), b[3:])
PX, PY = -(-X // 10) * 10, -(-Y // 10) * 10
out = []
for layer in range(Z):
    for y in range(PY):
        for x in range(PX):
            out += [v[((layer * Y + y) * X + x) * 4 + k] for k in range(4)] if (x < X and y < Y) else [0, 0, 0, 0]
open(p, 'wb').write(bytes([PY, PX, Z]) + struct.pack('<%dH' % len(out), *out))
print('%s: %dx%dx%d -> %dx%dx%d' % (p, X, Y, Z, PX, PY, Z))
