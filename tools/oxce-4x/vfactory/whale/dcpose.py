"""after k launches: drum i (i>=k) sits at position i-k (they roll down toward position 1); the first k are gone. Turrets -50, all SAMs gone."""
import bpy,sys,math
from mathutils import Matrix, Vector
POS=[[-16.99,-10.56,9],[-16.94,-9.3,9.6],[-16.94,-8.13,10.23],[-16.99,-7.02,10.71],[-16.97,-5.94,11.25],[-16.99,-4.65,12.03]]
src,k,out=sys.argv[-3:]; k=int(k); bpy.ops.wm.open_mainfile(filepath=src); O=bpy.data.objects
for n,cy in (('TURRET_L',2.15),('TURRET_R',-2.1)):
    o=O[n]; M=Matrix.Translation(Vector((-0.3,cy,0)))@Matrix.Rotation(math.radians(-50),4,'Z')@Matrix.Translation(Vector((0.3,-cy,0)))
    o.data.transform(o.matrix_world.inverted()@M@o.matrix_world)
for n in [x for x in O.keys() if x.startswith('MSL_')]: bpy.data.objects.remove(O[n])
for i in range(6):
    o=O[f'DC_{i}']
    if i<k: bpy.data.objects.remove(o); continue
    d=Vector(POS[i-k])-Vector(POS[i]); o.data.transform(Matrix.Translation(d))
bpy.ops.wm.save_as_mainfile(filepath=out)
