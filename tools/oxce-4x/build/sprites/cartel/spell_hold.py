# cast_spell -> cast_spell_hold: the arms never go overhead. Frames 1-17 arms ease rest(1) -> gather(18); 18-37 as
# animated (crouch, then hands pushed out at chest height); 37-56 held at the frame-37 push; 56-66 ease back to frame 66.
# Body, legs, head keep the original motion. python3 -I spell_hold.py CLIPS.blend ARM_SOURCE.blend
import bpy, sys
from mathutils import Quaternion
clips, armsrc = sys.argv[1], sys.argv[2]
idle = sys.argv[3] if len(sys.argv) > 3 else None
bpy.ops.wm.open_mainfile(filepath=clips)
with bpy.data.libraries.load(armsrc) as (s, d): d.objects = [n for n in s.objects]
arm = [o for o in d.objects if o and o.type == 'ARMATURE'][0]
bpy.context.scene.collection.objects.link(arm); arm.data.pose_position = 'POSE'
src = bpy.data.actions['cast_spell']
old = bpy.data.actions.get('cast_spell_hold')
if old: bpy.data.actions.remove(old)
new = src.copy(); new.name = 'cast_spell_hold'; new.use_fake_user = True
arm.animation_data_clear(); arm.animation_data_create(); arm.animation_data.action = src; arm.animation_data.action_slot = src.slots[0]
ARMS = [b.name for b in arm.pose.bones if any(k in b.name for k in ('Shoulder', 'Arm', 'Hand'))]
SPINE = ['mixamorig:Spine', 'mixamorig:Spine1', 'mixamorig:Spine2']
sc = bpy.context.scene
rest = None
if idle:   # arms-down start/end pose from a standing idle clip (frame 1)
    import re
    acts0, objs0 = set(bpy.data.actions), set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=idle)
    ia = [a for a in bpy.data.actions if a not in acts0][0]
    for l in ia.layers:
        for st in l.strips:
            for c in st.channelbags:
                for fc in c.fcurves: fc.data_path = re.sub(r'mixamorig\d+:', 'mixamorig:', fc.data_path)
    for o in [o for o in bpy.data.objects if o not in objs0]: bpy.data.objects.remove(o, do_unlink=True)
    arm.animation_data.action = ia; arm.animation_data.action_slot = ia.slots[0]
    sc.frame_set(1); rest = {b: arm.pose.bones[b].rotation_quaternion.copy() for b in ARMS}
    arm.animation_data.action = src; arm.animation_data.action_slot = src.slots[0]
    bpy.data.actions.remove(ia)
rot = {}
for f in range(1, 67):
    sc.frame_set(f)
    rot[f] = {b: arm.pose.bones[b].rotation_quaternion.copy() for b in ARMS + SPINE}
def ease(t): return t * t * (3 - 2 * t)
target = {}
for f in range(1, 67):
    if f <= 18:
        t = ease((f - 1) / 17); A = dict(rot[1]); A.update(rest or {})
        target[f] = {n: A[n].slerp(rot[18][n], t) for n in ARMS + SPINE}
    elif f <= 37: target[f] = rot[f]
    elif f <= 56: target[f] = rot[37]
    else:
        t = ease((f - 56) / 10); B = dict(rot[66]); B.update(rest or {})
        target[f] = {n: rot[37][n].slerp(B[n], t) for n in ARMS + SPINE}
# rewrite the arm rotation curves in the copy
cb = new.layers[0].strips[0].channelbags[0]
for n in ARMS + SPINE:
    path = f'pose.bones["{n}"].rotation_quaternion'
    for fc in [fc for fc in cb.fcurves if fc.data_path == path]: cb.fcurves.remove(fc)
    for i in range(4):
        fc = cb.fcurves.new(path, index=i, group_name=n)
        fc.keyframe_points.add(66)
        for k, f in enumerate(range(1, 67)):
            kp = fc.keyframe_points[k]; kp.co = (f, target[f][n][i]); kp.interpolation = 'LINEAR'
# frames 1-17, every other bone: ease straight from the frame-1 stand into the frame-18 crouch (no wind-up flourish)
done = {f'pose.bones["{n}"].rotation_quaternion' for n in ARMS + SPINE}
for fc in list(cb.fcurves):
    if fc.data_path in done: continue
    v1, v18 = fc.evaluate(1), fc.evaluate(18)
    vals = {f: fc.evaluate(f) for f in range(1, 67)}
    for f in range(1, 18): vals[f] = v1 + (v18 - v1) * ease((f - 1) / 17)
    fc.keyframe_points.clear(); fc.keyframe_points.add(66)
    for k, f in enumerate(range(1, 67)):
        kp = fc.keyframe_points[k]; kp.co = (f, vals[f]); kp.interpolation = 'LINEAR'
bpy.data.objects.remove(arm, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=clips, compress=True)
print('cast_spell_hold', len(ARMS), 'arm bones rebaked')
