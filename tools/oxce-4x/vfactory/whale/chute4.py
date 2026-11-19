"""John 20:41: 'remove those discs and the bumps in the frame, it's a chute that rolls out depth charges' - the Generals rack piece goes,
an inclined chute (floor + two side rails, olive) carries the six drums down to the stern edge."""
import bpy,sys,bmesh,math
import numpy as np
from mathutils import Vector, Matrix
src,out=sys.argv[-2:]; bpy.ops.wm.open_mainfile(filepath=src); O=bpy.data.objects
h=O['GJCHASSIS']; me=h.data; mw=h.matrix_world; V=np.array([(mw@v.co)[:] for v in me.vertices])
bm=bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
kill=[f for f in bm.faces if all((-18.9<(mw@v.co).x<-15.0) and (-8.6<(mw@v.co).y<-3.4) and ((mw@v.co).z>9.0) for v in f.verts)]
print('rack faces removed',len(kill)); bmesh.ops.delete(bm,geom=kill,context='FACES'); bm.to_mesh(me); bm.free()
# the chute: a short slatted ramp from the bottom of the column down over the stern edge (the grey slatted piece in the photo)
def plate(name,x0,x1,z0,z1,y0,y1,t):
    bm=bmesh.new(); v=[bm.verts.new((x,y,z+dz)) for (x,z) in ((x0,z0),(x1,z1)) for dz in (0,t) for y in (y0,y1)]
    for f in [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]: bm.faces.new([v[i] for i in f])
    m=bpy.data.meshes.new(name); bm.to_mesh(m); o=bpy.data.objects.new(name,m); bpy.context.scene.collection.objects.link(o); m.uv_layers.new(name='UV')
    m.materials.append(O['CANNON_L'].data.materials[0]); return o
# John 20:44-20:47: the drums roll DOWN toward the ship's side (outboard), out over the hull edge - a cross-ship slatted chute
def yplate(name,y0,y1,z0,z1,x0,x1,t):
    bm=bmesh.new(); v=[bm.verts.new((x,y,z+dz)) for (y,z) in ((y0,z0),(y1,z1)) for dz in (0,t) for x in (x0,x1)]
    for f in [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]: bm.faces.new([v[i] for i in f])
    m=bpy.data.meshes.new(name); bm.to_mesh(m); o=bpy.data.objects.new(name,m); bpy.context.scene.collection.objects.link(o); m.uv_layers.new(name='UV')
    m.materials.append(O['CANNON_L'].data.materials[0]); return o
# chute under John's drum line (20:49): z(y) = 9 + 0.513 (y + 10.56), floor one drum radius below; exits outboard past drum 1
zf=lambda y: 9+0.513*(y+10.56)-0.72
Y0,Y1=-3.9,-11.7
yplate('CHUTE_FLOOR',Y0,Y1,zf(Y0)-0.15,zf(Y1)-0.15,-18.3,-15.65,0.15)
yplate('CHUTE_RAIL_A',Y0,Y1,zf(Y0),zf(Y1),-18.5,-18.3,0.55)
yplate('CHUTE_RAIL_B',Y0,Y1,zf(Y0),zf(Y1),-15.65,-15.45,0.55)
bpy.ops.wm.save_as_mainfile(filepath=out,compress=True)
