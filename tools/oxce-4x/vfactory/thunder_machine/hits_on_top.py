# markings stand clear of the slanted sides (0.1), and on the damaged look the hit stickers go over them (0.22)
import bpy, sys
from mathutils import Vector
P = sys.argv[-1]; bpy.ops.wm.open_mainfile(filepath=P); n = 0
for o in bpy.data.objects:
    lift = 0.22 if (o.name.startswith('decal_hit') or o.name.startswith('decal_t_hit')) else (0.1 if o.name.startswith('decal_tm_') else 0)
    if lift:
        me = o.data; nrm = (o.matrix_world.to_3x3() @ me.polygons[0].normal).normalized(); o.location += nrm * lift; n += 1
bpy.ops.wm.save_as_mainfile(filepath=P, compress=True); print('LIFTED', n)
