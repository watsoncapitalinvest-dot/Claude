"""Is a Ch49 body already on the +1.6 cm build? Measures a built .blend against plain "Withdrawing Sword (2).fbx".
  python3 measure_swell.py <a.blend> [more.blend ...]
Rest pose, world space, torso band (z 1.05-1.40 m, |x| < 0.20 m): for every body vertex there, the distance to the
nearest vertex of the plain Ch49 mesh. Median ~0 = plain body; ~16 mm = swollen (factory_blend --swell 0.016 pushes
the torso by 0.016 x 1.1 = 17.6 mm). Also the chest width at z 1.30 against the plain body."""
import bpy, sys, os, numpy as np
from scipy.spatial import cKDTree
CACHE = '/tmp/claude-0/ws/posmap49/plain_ch49_rest.npy'
def world(o):
    dg = bpy.context.evaluated_depsgraph_get(); me = o.evaluated_get(dg).to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); o.evaluated_get(dg).to_mesh_clear()
    M = np.array(o.matrix_world); return co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
def body_pts():
    for a in [o for o in bpy.data.objects if o.type == 'ARMATURE']: a.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and 'Ch49_body' in o.name]
    return np.concatenate([world(o) for o in obs]) if obs else None
if not os.path.exists(CACHE):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath='/mnt/user-data/uploads/Downloads/Withdrawing Sword (2).fbx')
    np.save(CACHE, body_pts())
P = np.load(CACHE); tree = cKDTree(P)
def band(Q): return Q[(Q[:, 2] > 1.05) & (Q[:, 2] < 1.40) & (np.abs(Q[:, 0]) < 0.20)]
def width(Q): s = Q[np.abs(Q[:, 2] - 1.30) < 0.01]; return s[:, 0].max() - s[:, 0].min()
for b in sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]:
    if not b.endswith('.blend'): continue
    bpy.ops.wm.open_mainfile(filepath=b); Q = body_pts()
    if Q is None: print('MEASURE', os.path.basename(b), 'no Ch49 body mesh'); continue
    d, _ = tree.query(band(Q))
    print('MEASURE %-28s torso offset median %5.1f mm (p90 %5.1f)  chest width %.3f m vs plain %.3f m  -> %s' % (
        os.path.basename(b), 1000 * np.median(d), 1000 * np.percentile(d, 90), width(Q), width(P),
        'SWOLLEN' if np.median(d) > 0.008 else 'plain'), flush=True)
