#!/usr/bin/env python3
"""Generals W3D (static models: buildings, playsets) -> OBJ + MTL, in world space.

    python3 w3d2obj.py model.w3d out_dir texture_dir

Reads the HIERARCHY (pivots), the HLOD (which mesh hangs on which pivot, LOD 0 only) and every
MESH (vertices, triangles, first-pass UVs, texture names). Meshes are moved by their pivot's
world transform. Textures are written next to the OBJ as PNG (the mod ships them as .dds).
Skinned meshes and animations are ignored (not needed for buildings).
"""
import os, struct, sys, math

def chunks(b, off=0, end=None):
    end = len(b) if end is None else end
    while off + 8 <= end:
        t, s = struct.unpack_from('<II', b, off)
        sub = bool(s & 0x80000000); s &= 0x7FFFFFFF
        yield t, off + 8, s, sub
        off += 8 + s

def cstr(b): return b.split(b'\0')[0].decode('latin1')

def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw*bx + ax*bw + ay*bz - az*by, aw*by - ax*bz + ay*bw + az*bx,
            aw*bz + ax*by - ay*bx + az*bw, aw*bw - ax*bx - ay*by - az*bz)

def qrot(q, v):
    x, y, z, w = q; vx, vy, vz = v
    # v' = q v q*
    ix = w*vx + y*vz - z*vy; iy = w*vy + z*vx - x*vz; iz = w*vz + x*vy - y*vx; iw = -x*vx - y*vy - z*vz
    return (ix*w + iw*-x + iy*-z - iz*-y, iy*w + iw*-y + iz*-x - ix*-z, iz*w + iw*-z + ix*-y - iy*-x)

def parse(path):
    b = open(path, 'rb').read()
    pivots, hlod, meshes = [], [], []
    for t, o, s, sub in chunks(b):
        if t == 0x100:
            for t2, o2, s2, _ in chunks(b, o, o + s):
                if t2 == 0x102:
                    for i in range(s2 // 60):
                        p = o2 + i * 60
                        name = cstr(b[p:p+16]); parent = struct.unpack_from('<i', b, p+16)[0]
                        tr = struct.unpack_from('<3f', b, p+20); q = struct.unpack_from('<4f', b, p+44)
                        pivots.append((name, parent, tr, q))
        elif t == 0x700:
            first = True
            for t2, o2, s2, _ in chunks(b, o, o + s):
                if t2 == 0x702 and first:
                    first = False
                    for t3, o3, s3, _ in chunks(b, o2, o2 + s2):
                        if t3 == 0x704:
                            bone = struct.unpack_from('<I', b, o3)[0]; name = cstr(b[o3+4:o3+36])
                            hlod.append((name, bone))
        elif t == 0x0:
            m = {'name': '', 'v': [], 'f': [], 'uv': [], 'tex': [], 'texid': None, 'hidden': False}
            for t2, o2, s2, sub2 in chunks(b, o, o + s):
                if t2 == 0x1F:
                    attrs = struct.unpack_from('<I', b, o2+4)[0]
                    m['name'] = cstr(b[o2+24:o2+40]) + '.' + cstr(b[o2+8:o2+24])
                    m['hidden'] = bool(attrs & 0x00001000)
                elif t2 == 0x02:
                    m['v'] = [struct.unpack_from('<3f', b, o2 + 12*i) for i in range(s2 // 12)]
                elif t2 == 0x20:
                    m['f'] = [struct.unpack_from('<3I', b, o2 + 32*i) for i in range(s2 // 32)]
                elif t2 == 0x30:
                    for t3, o3, s3, _ in chunks(b, o2, o2 + s2):
                        if t3 == 0x31:
                            for t4, o4, s4, _ in chunks(b, o3, o3 + s3):
                                if t4 == 0x32: m['tex'].append(cstr(b[o4:o4+s4]))
                elif t2 == 0x38 and not m['uv']:
                    for t3, o3, s3, _ in chunks(b, o2, o2 + s2):
                        if t3 == 0x48:
                            for t4, o4, s4, _ in chunks(b, o3, o3 + s3):
                                if t4 == 0x49 and m['texid'] is None:
                                    m['texid'] = list(struct.unpack_from('<%dI' % (s4 // 4), b, o4))
                                elif t4 == 0x4A and not m['uv']:
                                    m['uv'] = [struct.unpack_from('<2f', b, o4 + 8*i) for i in range(s4 // 8)]
            meshes.append(m)
    return pivots, hlod, meshes

def world(pivots):
    out = []
    for name, parent, tr, q in pivots:
        if parent >= 0 and parent < len(out):
            pt, pq = out[parent]
            r = qrot(pq, tr); out.append(((pt[0]+r[0], pt[1]+r[1], pt[2]+r[2]), qmul(pq, q)))
        else:
            out.append((tr, q))
    return out

def convert(path, out_dir, tex_dir, skip=()):
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    pivots, hlod, meshes = parse(path)
    W = world(pivots) if pivots else []
    bone_of = {n.lower(): bi for n, bi in hlod}
    stem = os.path.splitext(os.path.basename(path))[0]
    objp = os.path.join(out_dir, stem + '.obj'); mtlp = os.path.join(out_dir, stem + '.mtl')
    o = open(objp, 'w'); mt = open(mtlp, 'w'); o.write('mtllib %s.mtl\n' % stem)
    vbase = tbase = 1; mats = {}; used = []
    for m in meshes:
        if m['hidden'] or not m['v'] or not m['f']: continue
        if any(k in m['name'].lower() for k in skip): continue
        if hlod and m['name'].lower() not in bone_of: continue   # not in LOD 0
        tr, q = W[bone_of[m['name'].lower()]] if hlod and W else ((0, 0, 0), (0, 0, 0, 1))
        o.write('o %s\n' % m['name'])
        for v in m['v']:
            r = qrot(q, v); o.write('v %f %f %f\n' % (r[0]+tr[0], r[1]+tr[1], r[2]+tr[2]))
        uv = m['uv'] or [(0, 0)] * len(m['v'])
        for u in uv: o.write('vt %f %f\n' % (u[0], 1 - u[1]))
        ids = m['texid'] or [0]
        perface = len(ids) == len(m['f'])
        def matname(ti):
            tex = m['tex'][ti] if 0 <= ti < len(m['tex']) else None
            mat = 'mat_' + (os.path.splitext(tex)[0].lower() if tex else 'none')
            if mat not in mats:
                mats[mat] = tex
                mt.write('newmtl %s\nKd 1 1 1\n' % mat)
                if tex:
                    base = os.path.splitext(tex)[0].lower()
                    for ext in ('.dds', '.tga'):
                        src = os.path.join(tex_dir, base + ext)
                        if os.path.exists(src):
                            try:
                                Image.open(src).convert('RGBA').save(os.path.join(out_dir, base + '.png'))
                                mt.write('map_Kd %s.png\n' % base); used.append(base)
                            except Exception as e:
                                print('texture failed', src, e)
                            break
            return mat
        cur = None
        for fi, (a, b2, c) in enumerate(m['f']):
            mat = matname(ids[fi] if perface else ids[0])
            if mat != cur:
                o.write('usemtl %s\n' % mat); cur = mat
            o.write('f %d/%d %d/%d %d/%d\n' % (a+vbase, a+tbase, b2+vbase, b2+tbase, c+vbase, c+tbase))
        vbase += len(m['v']); tbase += len(uv)
    o.close(); mt.close()
    return objp, [m['name'] for m in meshes], used

if __name__ == '__main__':
    p, names, used = convert(*sys.argv[1:4])
    print(p); print('meshes:', names); print('textures:', used)
