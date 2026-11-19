"""John 20:23 'the outline on the depth charges is rough': the Generals rack drums (DC_0..5) give way to six modelled SD-30 drums."""
import bpy,sys
from mathutils import Matrix, Vector
src,drum,out=sys.argv[-3:]; bpy.ops.wm.open_mainfile(filepath=src); O=bpy.data.objects
for n in [k for k in O.keys() if k.startswith('DC_')]: bpy.data.objects.remove(O[n])
with bpy.data.libraries.load(drum) as (a,b): b.objects=['SD30_DEPTH_CHARGE']
src_o=b.objects[0]
for i in range(6):
    o=src_o.copy(); o.data=src_o.data.copy(); o.name=f'DC_{i}'; bpy.context.scene.collection.objects.link(o)
    o.data.transform(Matrix.Translation(Vector((-16.5,-7.55+0.7*i,12.25)))@Matrix.Scale(0.85,4,Vector((0,1,0)))); o.matrix_world=Matrix.Identity(4)
bpy.ops.wm.save_as_mainfile(filepath=out,compress=True)
