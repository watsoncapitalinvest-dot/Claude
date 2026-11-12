import bpy, sys, os, json, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
blend, animfbx, outdir, mode = argv[0], argv[1], argv[2], argv[3]
yaw = float(argv[4]) if len(argv) > 4 else 35.0
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
armA = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
before = set(bpy.data.objects); acts = set(bpy.data.actions)
bpy.ops.import_scene.fbx(filepath=animfbx)
act = [a for a in bpy.data.actions if a not in acts][0]
for o in [o for o in bpy.data.objects if o not in before]: bpy.data.objects.remove(o, do_unlink=True)
armA.animation_data_create(); armA.animation_data.action = act
if mode=='rest': armA.data.pose_position='REST'
try:
    armA.animation_data.action_slot = act.slots[0]
except Exception as e: print('slot', e)
# strip root motion on the ground plane (keep bob)
def fcurves(a):
    try: return list(a.fcurves)
    except Exception:
        out = []
        for l in a.layers:
            for st in l.strips:
                for cb in st.channelbags: out += list(cb.fcurves)
        return out
for fc in fcurves(act):
    if 'Hips' in fc.data_path and fc.data_path.endswith('location') and fc.array_index in (0, 2):
        k0 = fc.keyframe_points[0].co[1]
        for k in fc.keyframe_points:
            k.co[1] = k0; k.handle_left[1] = k0; k.handle_right[1] = k0
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
sc.frame_start, sc.frame_end = f0, (f0 if mode in ('still','rest') else f1 - 1)
# camera: orthographic 3/4 from front, slightly above
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.3
r = 6.0; el = math.radians(float(os.environ.get('ELEV','10'))); az = math.radians(yaw)
tgt = Vector((0, 0, 0.9))
cam.location = tgt + Vector((r * math.cos(el) * math.sin(az), -r * math.cos(el) * math.cos(az), r * math.sin(el)))
d = tgt - cam.location; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
# render settings
sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.use_denoising = False; sc.cycles.device = 'CPU'
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.render.resolution_x, sc.render.resolution_y = 500, 640; sc.render.film_transparent = False
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.58, 0.58, 0.62, 1); bg.inputs[1].default_value = 1
sc.render.use_freestyle = True; sc.render.line_thickness_mode = 'ABSOLUTE'; sc.render.line_thickness = 1.2
ls = sc.view_layers[0].freestyle_settings.linesets[0] if sc.view_layers[0].freestyle_settings.linesets else sc.view_layers[0].freestyle_settings.linesets.new('L')
hc = bpy.data.collections.new('HELM'); sc.collection.children.link(hc)
for o in bpy.data.objects:
    if o.name.startswith('helmet'):
        for c in list(o.users_collection): c.objects.unlink(o)
        hc.objects.link(o)
ls.select_by_collection = True; ls.collection = hc; ls.collection_negation = 'EXCLUSIVE'
ls2 = sc.view_layers[0].freestyle_settings.linesets.new('H'); ls2.select_by_collection = True; ls2.collection = hc
ls2.select_by_edge_types = True; ls2.select_silhouette = False; ls2.select_border = False; ls2.select_crease = False; ls2.select_external_contour = True; ls2.select_contour = True
ls2.linestyle = bpy.data.linestyles.new('LS2'); ls2.linestyle.color = (0.04, 0.04, 0.04); ls2.linestyle.thickness = 1.2
ls.select_by_visibility = True; ls.select_silhouette = True; ls.select_border = False; ls.select_crease = False
ls.linestyle = ls.linestyle or bpy.data.linestyles.new('LS')
ls.linestyle.color = (0.04, 0.04, 0.04); ls.linestyle.thickness = 1.2
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = os.path.join(outdir, 'f_')
bpy.ops.render.render(animation=True)
print('frames', f0, sc.frame_end)
