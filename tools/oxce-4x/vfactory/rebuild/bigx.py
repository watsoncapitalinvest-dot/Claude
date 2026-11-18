"""List / extract files from a Generals .BIG archive. python3 bigx.py file.big pattern outdir"""
import struct, sys, re, os
f = open(sys.argv[1], 'rb'); assert f.read(4) in (b'BIGF', b'BIG4'); f.read(4); n = struct.unpack('>I', f.read(4))[0]; f.read(4)
pat = re.compile(sys.argv[2], re.I); out = sys.argv[3]
for _ in range(n):
    off, size = struct.unpack('>II', f.read(8)); name = b''
    while (c := f.read(1)) != b'\0': name += c
    name = name.decode('latin1')
    if pat.search(name):
        pos = f.tell(); f.seek(off); data = f.read(size); f.seek(pos)
        p = os.path.join(out, os.path.basename(name.replace('\\', '/'))); open(p, 'wb').write(data); print(name, size)
