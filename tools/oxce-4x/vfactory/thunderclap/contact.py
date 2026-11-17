import bpy, numpy as np, bmesh, sys
from mathutils.bvhtree import BVHTree
def tree(o):
    bm=bmesh.new(); d=o.data.copy(); d.transform(o.matrix_world); bm.from_mesh(d); return BVHTree.FromBMesh(bm)
def gap(a,b):
    tb=tree(b); return min(tb.find_nearest(a.matrix_world@v.co)[3] for v in list(a.data.vertices)[::3])
f=sys.argv[1]; bpy.ops.wm.open_mainfile(filepath=f); O=bpy.data.objects
pairs=[p.split(':') for p in sys.argv[2].split(',')]
for a,b in pairs: print('CHK',a,'->',b,'gap mm',round(gap(O[a],O[b]),2))
P=np.array([o.matrix_world@v.co for o in O if o.type=='MESH' for v in o.data.vertices]); print('CHK ground z',round(P[:,2].min(),2))
