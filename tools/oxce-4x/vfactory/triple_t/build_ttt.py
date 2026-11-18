"""Triple T toy pass (John 17 Nov 22:49 "go"; 22:50 the toy's instruction sheet and blueprint). ROSTER's blend already has the 1986
toy's colours (light grey body, green seat and underbody, black guns, missiles and rear grill - as 3DJoes describes the original)
and its stickers in the instruction sheet's places. The one thing that is not the toy: each ball turret carried TWO barrels.
The blueprint (item 7, "turret-mounted 30mm cannons"), the instruction sheet and Jabberwock's kit (3254370, measured from the toy)
all show ONE barrel per ball. This takes the twin barrels and their collars off each ball and fits one cannon on the ball's axis:
the same black, a little thicker, a collar at the muzzle, as long as the blueprint draws it (about twice the ball across).
python3 build_ttt.py in.blend out.blend"""
import bpy, bmesh, sys, math
from mathutils import Matrix, Vector
SRC, OUT = sys.argv[-2:]
bpy.ops.wm.open_mainfile(filepath=SRC)
for name in ('laser_L', 'laser_R'):
    o = bpy.data.objects[name]; W = o.matrix_world; Wi = W.inverted()
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    seen, parts = set(), []
    for v in bm.verts:                                   # loose parts: ball, mount, and the two barrels with their collars
        if v.index in seen: continue
        st, comp = [v], []; seen.add(v.index)
        while st:
            a = st.pop(); comp.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen: seen.add(b.index); st.append(b)
        parts.append(comp)
    ball = max(parts, key=len); bw = [W @ v.co for v in ball]
    cx = sum(p.x for p in bw) / len(bw); cy = sum(p.y for p in bw) / len(bw); cz = sum(p.z for p in bw) / len(bw)
    front = max(p.x for p in bw); dia = max(p.z for p in bw) - min(p.z for p in bw)
    gone = [v for comp in parts if comp is not ball and min((W @ v.co).x for v in comp) > -2.0 for v in comp]   # barrels + collars (x > -2)
    bmesh.ops.delete(bm, geom=gone, context='VERTS')
    def tube(x0, x1, r):
        g = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=r, radius2=r, depth=x1 - x0)
        M = Wi @ Matrix.Translation(((x0 + x1) / 2, cy, cz)) @ Matrix.Rotation(math.pi / 2, 4, 'Y')
        bmesh.ops.transform(bm, matrix=M, verts=g['verts'])
    tip = front + 2.0 * dia
    tube(front - 0.3, tip - 0.6, 0.34)                   # the 30mm cannon
    tube(tip - 0.6, tip, 0.44)                           # muzzle collar
    bm.to_mesh(o.data); bm.free()
    print(name, 'ball centre', round(cx, 2), round(cy, 2), round(cz, 2), 'cannon to x', round(tip, 2), 'removed', len(gone))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print('SAVED', OUT)
