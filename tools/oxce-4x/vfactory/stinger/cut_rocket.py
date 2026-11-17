# Cobra Stinger (VFACTORY, 17 Nov; John 18:37 "continue"): the toy's weapon is ground-to-air rockets on a rack that turns 360
# (file card), not a "quad cannon". The Generals launcher (GJTURRET) carries three rockets. One is copied out of it as
# 'rocket_fly' (the same rocket, same size) for the full-size flying sprite (full_launch.py). The rack is untouched.
# usage: python3 -I cut_rocket.py in.blend out.blend
import bpy, bmesh, sys, numpy as np
IN, OUT = sys.argv[-2:]; bpy.ops.wm.open_mainfile(filepath=IN)
t = bpy.data.objects['GJTURRET']; M = t.matrix_world
bm = bmesh.new(); bm.from_mesh(t.data); bm.transform(M)
AX_Y, AX_Z, RMAX = 3.665, 13.611, 1.45                              # the rocket's own axis (through its tip) and fin span
def near(f):                                                         # John 18:43 "clean and accurate": nothing of the rack
    c = f.calc_center_median(); return -13.4 < c.x and ((c.y - AX_Y) ** 2 + (c.z - AX_Z) ** 2) ** 0.5 < RMAX and \
        all(((v.co.y - AX_Y) ** 2 + (v.co.z - AX_Z) ** 2) ** 0.5 < RMAX + 0.15 for v in f.verts)
cs = [f for f in bm.faces if near(f)]
keep = set(cs); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in keep], context='FACES')
me = bpy.data.meshes.new('rocket_fly'); bm.to_mesh(me); bm.free()
for m in t.data.materials: me.materials.append(m)
o = bpy.data.objects.new('rocket_fly', me); bpy.context.scene.collection.objects.link(o); o.location = (0, 0, -500)   # parked out of every render
V = np.array([v.co[:] for v in me.vertices]); print('ROCKET faces', len(me.polygons), 'x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (V[:, 0].min(), V[:, 0].max(), V[:, 1].min(), V[:, 1].max(), V[:, 2].min(), V[:, 2].max()))
tip = V[V[:, 0] > V[:, 0].max() - 0.2].mean(0); print('TIP %.3f,%.3f,%.3f' % tuple(tip))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
