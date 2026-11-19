"""John 20:50 'if they're clipping, move them or cut out where it clipped': delete the hull faces any drum cuts into."""
import bpy,sys,bmesh
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1]); O=bpy.data.objects
def W(o):
    mw=o.matrix_world; return BVHTree.FromPolygons([mw@v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])
h=O['GJCHASSIS']; H=W(h); kill=set()
for n in [k for k in O.keys() if k.startswith('DC_')]: kill|={b for a,b in W(O[n]).overlap(H)}
bm=bmesh.new(); bm.from_mesh(h.data); bm.faces.ensure_lookup_table(); bmesh.ops.delete(bm,geom=[bm.faces[i] for i in kill],context='FACES'); bm.to_mesh(h.data); bm.free()
print('cut',len(kill)); bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1],compress=True)
