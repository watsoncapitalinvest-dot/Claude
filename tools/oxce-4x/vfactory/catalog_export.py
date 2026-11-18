"""Export catalog parts from a source blend: the named objects only -> <out>.glb (metres) + <out>_preview.png (3/4 view, transparent).
Prints L W H (m) and the triangle count for catalog_add.py. Objects are copied into a clean scene, so nothing else in the blend leaks in.
python3 catalog_export.py in.blend 'obj1,obj2' out_stem metres_per_unit"""
import bpy, sys, math
from mathutils import Vector
SRC, OBJS, OUT, MPU = sys.argv[-4], sys.argv[-3].split(','), sys.argv[-2], float(sys.argv[-1])
bpy.ops.wm.open_mainfile(filepath=SRC)
keep = [bpy.data.objects[n] for n in OBJS]
for o in list(bpy.data.objects):
    if o not in keep: bpy.data.objects.remove(o, do_unlink=True)
for o in keep:
    o.hide_render = False; o.hide_viewport = False; o.hide_set(False)
pts = [o.matrix_world @ Vector(c) for o in keep for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
mid = (lo + hi) / 2
for o in keep:                                            # centre on the origin, scale to metres
    o.matrix_world = __import__('mathutils').Matrix.Scale(MPU, 4) @ __import__('mathutils').Matrix.Translation(-mid) @ o.matrix_world
bpy.context.view_layer.update()
L, W, H = [(hi[i] - lo[i]) * MPU for i in range(3)]
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in keep if o.type == 'MESH')
for o in bpy.context.scene.objects: o.select_set(o in keep)
bpy.ops.export_scene.gltf(filepath=OUT + '.glb', export_format='GLB', use_selection=True)
sc = bpy.context.scene; R = max(L, W, H)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = R * 1.55
d = Vector((0.55, -1.0, 0.45)).normalized(); cam.location = d * R * 4; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 4.0
sun.rotation_euler = (math.radians(45), math.radians(-20), math.radians(-35))
if sc.world is None: sc.world = bpy.data.worlds.new('w')
sc.world.color = (0.4, 0.4, 0.4)
eng = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in eng else 'BLENDER_EEVEE'
sc.render.film_transparent = True; sc.render.resolution_x = 600; sc.render.resolution_y = 400; sc.render.resolution_percentage = 100
sc.render.filepath = OUT + '_preview.png'; bpy.ops.render.render(write_still=True)
print('EXPORT', OUT, 'L W H m', round(L, 3), round(W, 3), round(H, 3), 'tris', tris)
