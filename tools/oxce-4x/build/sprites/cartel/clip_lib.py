# Import mixamo FBX clips, keep only their actions (bone paths normalised to mixamorig:), save a clip library .blend.
# python3 -I clip_lib.py OUT.blend name=path.fbx ...
import bpy, sys, re
out = sys.argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
keep = []
for a in sys.argv[2:]:
    name, path = a.split('=', 1)
    before = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False)
    new = [x for x in bpy.data.actions if x not in before]
    act = max(new, key=lambda x: len(x.fcurves) if hasattr(x, 'fcurves') else 0)
    for x in new:
        if x is not act: bpy.data.actions.remove(x)
    act.name = name; act.use_fake_user = True
    try:
        for fc in act.fcurves: fc.data_path = re.sub(r'mixamorig\d+:', 'mixamorig:', fc.data_path)
    except AttributeError:   # layered actions (Blender 4.4+)
        for l in act.layers:
            for s in l.strips:
                for cb in s.channelbags:
                    for fc in cb.fcurves: fc.data_path = re.sub(r'mixamorig\d+:', 'mixamorig:', fc.data_path)
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)
    for m in list(bpy.data.armatures): bpy.data.armatures.remove(m)
    for m in list(bpy.data.images): bpy.data.images.remove(m)
    print('clip', name, tuple(act.frame_range))
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
