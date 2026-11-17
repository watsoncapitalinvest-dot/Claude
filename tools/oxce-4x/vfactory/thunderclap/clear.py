# clearance under every vertex of a part to the hull below it: max = how far any part of it floats
import bpy, bmesh, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[1]); O = bpy.data.objects
bm = bmesh.new()
for n in sys.argv[3].split(','):
    d = O[n].data.copy(); d.transform(O[n].matrix_world); bm.from_mesh(d)
tr = BVHTree.FromBMesh(bm); o = O[sys.argv[2]]; P = np.array([o.matrix_world @ v.co for v in o.data.vertices])
low = P[P[:, 2] < P[:, 2].min() + 6]
g = [p[2] - h[0].z for p in low for h in [tr.ray_cast(Vector((p[0], p[1], p[2] - 0.01)), Vector((0, 0, -1)))] if h[0]]
print('CLEAR', sys.argv[2], 'underside min gap', round(min(g), 2), 'median', round(float(np.median(g)), 2), 'max', round(max(g), 2), 'mm')
