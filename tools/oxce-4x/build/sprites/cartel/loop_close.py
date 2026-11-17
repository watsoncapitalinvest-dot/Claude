# Make a non-looping clip loop: over its last N frames every bone rotation eases back to frame 1 (hips location left alone,
# render_char flattens that). python3 -I loop_close.py CLIPS.blend ACTION N
import bpy, sys
lib, name, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
bpy.ops.wm.open_mainfile(filepath=lib)
a = bpy.data.actions[name]; fe = int(a.frame_range[1]); f0 = fe - n
def ease(t): return t * t * (3 - 2 * t)
cb = a.layers[0].strips[0].channelbags[0]
groups = {}
for fc in cb.fcurves:
    if fc.data_path.endswith('rotation_quaternion'): groups.setdefault(fc.data_path, {})[fc.array_index] = fc
from mathutils import Quaternion
for path, d in groups.items():
    q = {f: Quaternion([d[i].evaluate(f) for i in range(4)]) for f in range(1, fe + 1)}
    q1 = q[1]
    if q[f0].dot(q1) < 0: q1 = -q1
    new = {f: (q[f] if f <= f0 else q[f].slerp(q1, ease((f - f0) / n))) for f in range(1, fe + 1)}
    for i in range(4):
        fc = d[i]; fc.keyframe_points.clear(); fc.keyframe_points.add(fe)
        for k, f in enumerate(range(1, fe + 1)):
            kp = fc.keyframe_points[k]; kp.co = (f, new[f][i]); kp.interpolation = 'LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=lib, compress=True)
print('loop closed', name, 'frames', f0, '-', fe)
