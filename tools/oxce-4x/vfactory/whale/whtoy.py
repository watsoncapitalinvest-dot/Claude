"""Killer W.H.A.L.E.: toy-accurate cannons (#8) and quad SAM launchers (#14) from John's downloads (Thingiverse 5170333 cannon + missile,
the WHALE Missile Launcher STL) replace the Generals mesh's ones. Toy mm -> hull units: 50 / 482.6."""
import bpy,sys,math,bmesh
import numpy as np
from mathutils import Matrix, Vector
src,out=sys.argv[-2:]; bpy.ops.wm.open_mainfile(filepath=src); O=bpy.data.objects; S=50/482.6
D='/home/claude/in/whale_parts/'
def imp(f,name):
    before=set(O.keys()); bpy.ops.wm.stl_import(filepath=f); o=[O[k] for k in O.keys() if k not in before][0]; o.name=name; return o
def mat_of(n): return O[n].data.materials[:]
OLmats=mat_of('CANNON_L'); WHm=O['MSL_L_00'].data.materials[0]; GMm=O['TURRET_L'].data.materials[1]
# drop the cut cannons and missiles, and the Generals launcher boxes
for n in [k for k in O.keys() if k.startswith(('CANNON_','MSL_'))]: bpy.data.objects.remove(O[n])
h=O['GJCHASSIS']; mw=h.matrix_world; bm=bmesh.new(); bm.from_mesh(h.data); bm.faces.ensure_lookup_table()
kill=[f for f in bm.faces if all((-6.6<(mw@v.co).x<-1.4) and (5.0<abs((mw@v.co).y)<8.7) and ((mw@v.co).z>13.0) for v in f.verts)]
print('launcher faces removed',len(kill)); bmesh.ops.delete(bm,geom=kill,context='FACES'); bm.to_mesh(h.data); bm.free()
def place(o,M):
    o.data.uv_layers.new(name='UV') if not o.data.uv_layers else None; o.data.transform(M); o.matrix_world=Matrix.Identity(4); o.data.update()
def centre_axis(o,ax,lo_frac):
    V=np.array([v.co[:] for v in o.data.vertices]); a,b=V[:,ax].min(),V[:,ax].max(); s=V[V[:,ax]>a+lo_frac*(b-a)]; return V, s.mean(0)
# cannons: STL long axis +z = muzzle; barrel axis from the upper 60%
for name,y in (('CANNON_L',7.4),('CANNON_R',-7.4)):
    o=imp(D+'files/whale_cannon.stl',name); V,c=centre_axis(o,2,0.4); zmin=V[:,2].min()
    R=Matrix.Rotation(math.radians(90),4,'Y')                     # +z -> +x
    M=Matrix.Translation(Vector((2.6,y,11.45)))@Matrix.Scale(S,4)@R@Matrix.Translation(Vector((-c[0],-c[1],-zmin)))
    place(o,M); o.data.materials.clear(); [o.data.materials.append(m) for m in OLmats]
    for p in o.data.polygons: p.material_index = 1 if p.center.x>12.0 else 0
    W=np.array([v.co[:] for v in o.data.vertices]); print(name,W.min(0).round(2),W.max(0).round(2))
# launchers: tube mouths on the STL's -z face; mouths face the bow, raised 30 deg; 4 missiles in the tubes
for side,y in (('L',6.65),('R',-6.65)):
    o=imp(D+'GI+Joe+Killer+WHALE+Missle+Launcher.stl','LAUNCHER_'+side); V=np.array([v.co[:] for v in o.data.vertices]); c=(V.min(0)+V.max(0))/2
    face=V[V[:,2]<V[:,2].min()+3]; fc=(face.min(0)+face.max(0))/2
    R=Matrix.Rotation(math.radians(-30),4,'Y')@Matrix.Rotation(math.radians(90),4,'Y')   # +z (the four mouths) -> +x, then tip up
    T=Matrix.Translation(Vector((-4.2,y,15.6)))@Matrix.Scale(S,4)@R@Matrix.Translation(Vector(-c))
    place(o,T); o.data.materials.clear(); o.data.materials.append(OLmats[0])
    for i,(tx,ty) in enumerate(((130.5,127.0),(142.5,127.0),(130.5,141.0),(142.5,141.0))):   # mouth centres measured on the STL
        m=imp(D+'files/whale_missile.stl',f'MSL_{side}_{i}'); MV=np.array([v.co[:] for v in m.data.vertices]); mc=(MV.min(0)+MV.max(0))/2
        tube=Vector((tx, ty, V[:,2].max()+2))       # in the tube, a third sticking out of the mouth
        M=T@Matrix.Translation(tube)@Matrix.Translation(Vector(-mc))
        place(m,M); m.data.materials.clear(); m.data.materials.append(WHm)
    W=np.array([v.co[:] for v in o.data.vertices]); print('LAUNCHER',side,W.min(0).round(2),W.max(0).round(2))
bpy.ops.wm.save_as_mainfile(filepath=out,compress=True)
