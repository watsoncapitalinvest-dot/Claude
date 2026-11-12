"""+1.6 cm fuller build for the Mixamo Ch49 (WW2) body - John's body-size rule (12 Nov 2026).
Exact code used for Duke final (duke_build_v3) and the Cobra troopers; lifted out of factory_blend.py so any
Blender-Python build script can call it.

    from swell_ch49 import swell_ch49
    swell_ch49(body_meshes, swell=0.016, collar_z=0.845 * h49 - 0.006)

WHEN to call it (order matters):
  1. import the Ch49 FBX; cut the head off (body kept below 0.845 x height)
  2. apply the object transform into the mesh data (matrix_world -> identity), so co is in metres, z up, feet at 0
  3. >>> swell_ch49(...) <<<   - on the REST mesh, before any pose/animation is applied
  4. swap the head on, bind to the armature, pose/animate, render
Because only the rest-pose vertex positions move (not the bones, weights or UVs), the rig and every Mixamo animation
keep working unchanged.

body_meshes: the Ch49 mesh objects (Ch49 has two: 'Ch49_body1' and 'Ch49_body2'). Requires numpy + scipy.
"""
import numpy as np


def _sheet(o):
    """which Ch49 texture sheet the object uses ('1002' = shirt/trousers layer, '1001' = webbing/gear/hands/boots)"""
    for m in o.data.materials:
        if m and m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image and '1002' in (n.image.name + n.image.filepath):
                    return '1002'
    return ''


def swell_ch49(body_meshes, swell=0.016, collar_z=None, layer_dist=0.03, layer_gap=0.002):
    SW = {}
    for o in body_meshes:
        me = o.data
        gi = {vg.index: vg.name for vg in o.vertex_groups}
        co = np.array([v.co[:] for v in me.vertices])
        nr = np.array([v.normal[:] for v in me.vertices])               # smooth vertex normals of the rest mesh
        # bone-group weights decide how much each vertex is pushed
        w_hand = np.zeros(len(co)); w_torso = np.zeros(len(co))
        for v in me.vertices:
            for g in v.groups:
                n = gi[g.group]
                if 'Hand' in n: w_hand[v.index] += g.weight
                if any(k in n for k in ('Spine', 'Hips', 'Shoulder', 'Neck')): w_torso[v.index] += g.weight
        z = co[:, 2]
        boots = np.clip((0.40 - z) / 0.08, 0, 1)                          # fade to zero over the boot tops (z 0.32-0.40 m)
        # push distance: 0.75 x swell on limbs rising to 1.10 x swell on the torso; hands and boots untouched
        amt = swell * (0.75 + 0.35 * np.clip(w_torso, 0, 1)) * (1 - np.clip(w_hand, 0, 1)) * (1 - boots)
        if collar_z is not None:
            # at the cut collar edge push straight OUT (drop the vertical part of the normal): the open edge's normals
            # are uneven and otherwise push the collar up and down into a saw-tooth around the neck
            top = np.clip((z - (collar_z - 0.05)) / 0.03, 0, 1)[:, None]
            flat = nr.copy(); flat[:, 2] = 0
            flat /= np.maximum(np.linalg.norm(flat, axis=1, keepdims=True), 1e-6)
            nr = nr * (1 - top) + flat * top
        new = co + nr * amt[:, None]
        # broader chest/shoulders: +4.5% in x between z 1.05 and the shoulders, torso-weighted
        chest = np.clip((z - 1.05) / 0.15, 0, 1) * np.clip((1.52 - z) / 0.06, 0, 1) * np.clip(w_torso, 0, 1)
        new[:, 0] *= 1 + 0.045 * chest
        SW[o.name] = (co, new, nr)
    # LAYER LOCK - do not skip. Ch49's webbing/pouches/buttons sit 2-10 mm above the shirt on a separate mesh. Pushed
    # separately, the shirt pokes through them (saw-toothed, broken strap edges). So every vertex of the gear mesh that
    # lies within 3 cm of the shirt layer copies the push of the nearest shirt vertex, plus 2 mm so it stays on top.
    from scipy.spatial import cKDTree
    base = ([o for o in body_meshes if _sheet(o) == '1002'] or [max(body_meshes, key=lambda o: len(o.data.vertices))])[0]
    b0, b1, _ = SW[base.name]; tree = cKDTree(b0)
    for o in body_meshes:
        c0, c1, nr = SW[o.name]
        if o is not base:
            dist, nn = tree.query(c0)
            on = dist < layer_dist
            c1 = c1.copy(); c1[on] = c0[on] + (b1[nn[on]] - b0[nn[on]]) + nr[on] * layer_gap
            print('swell: layer-locked', o.name, int(on.sum()), 'of', len(c0), 'verts to', base.name)
        o.data.vertices.foreach_set('co', c1.ravel()); o.data.update()
    print('swell', swell, 'base layer', base.name)
