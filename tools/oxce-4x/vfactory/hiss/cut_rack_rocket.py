# H.I.S.S. rocket-rack variant (John 18:41: "the HISS missiles to be an upgrade through research for Cobra"). The Generals
# rack (GJTURRET01, 4 rockets) stays on this variant; one upper rocket is copied out as 'rocket_fly' for the full-size
# flying sprite (same rocket, same size). The standard H.I.S.S. carries the 1983 twin-cannon turret (build_hiss.py).
# usage: python3 -I cut_rack_rocket.py in.blend out.blend
import bpy, bmesh, sys, numpy as np
IN, OUT = sys.argv[-2:]; bpy.ops.wm.open_mainfile(filepath=IN)
t = bpy.data.objects['GJTURRET01']; bm = bmesh.new(); bm.from_mesh(t.data); bm.transform(t.matrix_world)
keep = {f for f in bm.faces if 0.6 < f.calc_center_median().y < 2.9 and f.calc_center_median().z > 18.15}
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in keep], context='FACES')
me = bpy.data.meshes.new('rocket_fly'); bm.to_mesh(me); bm.free()
for m in t.data.materials: me.materials.append(m)
o = bpy.data.objects.new('rocket_fly', me); bpy.context.scene.collection.objects.link(o); o.location = (0, 0, -500)
V = np.array([v.co[:] for v in me.vertices]); print('ROCKET faces', len(me.polygons), 'x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (V[:, 0].min(), V[:, 0].max(), V[:, 1].min(), V[:, 1].max(), V[:, 2].min(), V[:, 2].max()))
tip = V[V[:, 0] > V[:, 0].max() - 0.2].mean(0); print('TIP %.3f,%.3f,%.3f' % tuple(tip))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
