"""pose: turret yaw (deg, both turrets about their tub centres), hide list -> blend"""
import bpy,sys,math
from mathutils import Matrix, Vector
src,yaw,hide,out=sys.argv[-4:]; bpy.ops.wm.open_mainfile(filepath=src); O=bpy.data.objects
for n,cy in (('TURRET_L',2.15),('TURRET_R',-2.1)):
    o=O[n]; M=Matrix.Translation(Vector((-0.3,cy,0)))@Matrix.Rotation(math.radians(float(yaw)),4,'Z')@Matrix.Translation(Vector((0.3,-cy,0)))
    o.data.transform(o.matrix_world.inverted()@M@o.matrix_world); o.data.update()
for h in [x for x in hide.split(',') if x]: bpy.data.objects.remove(O[h])
bpy.ops.wm.save_as_mainfile(filepath=out)
