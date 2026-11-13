"""+1.6 cm fuller build (John's body-size rule) for ANY Mixamo body, in a finished look .blend.
Same push as swell_ch49.py (DESIGN's exact code for Ch49), extended for bodies that keep their own head and
for blends whose body mesh is not world-space:
  - push per vertex = swell x (0.75 + 0.35 x torso weight); hands and boots (z 0.32-0.40 m fade) untouched;
    chest/shoulders +4.5% wider between z 1.05 and 1.52 m, torso-weighted          (as swell_ch49)
  - the body's OWN HEAD is not pushed (x (1 - Head weight)): on Ch49 the head is cut off and replaced
    unswollen, so the head stays the size it was on every body
  - worked in world metres and written back through the object's matrix (FBX bodies carry a 0.01 scale)
  - skin-bound props (swords, packs) move rigidly with the body under them, so nothing sinks into the swell
Only rest-pose vertex positions move: bones, weights, UVs and textures are untouched, every clip still plays.

    python3 swell_body.py in.blend out.blend [--swell 0.016] [--body Ch45]
"""
import argparse, sys
import numpy as np


def world(o):
    me = o.data; n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    nr = np.empty(n * 3); me.vertices.foreach_get('normal', nr); nr = nr.reshape(-1, 3)
    M = np.array(o.matrix_world); R = M[:3, :3]
    w = co @ R.T + M[:3, 3]
    wn = nr @ np.linalg.inv(R)                         # normals transform by the inverse-transpose
    wn /= np.maximum(np.linalg.norm(wn, axis=1, keepdims=True), 1e-9)
    return co, w, wn, M


def put_world(o, w, M):
    loc = (w - M[:3, 3]) @ np.linalg.inv(M[:3, :3]).T
    o.data.vertices.foreach_set('co', loc.ravel()); o.data.update()


def swell_body(body, props, swell=0.016):
    co, w, nr, M = world(body)
    gi = {vg.index: vg.name for vg in body.vertex_groups}
    w_hand = np.zeros(len(co)); w_torso = np.zeros(len(co)); w_head = np.zeros(len(co))
    for v in body.data.vertices:
        for g in v.groups:
            n = gi[g.group]
            if 'Hand' in n: w_hand[v.index] += g.weight
            if any(k in n for k in ('Spine', 'Hips', 'Shoulder', 'Neck')): w_torso[v.index] += g.weight
            if n.endswith('Head') or 'HeadTop' in n: w_head[v.index] += g.weight
    z = w[:, 2]
    boots = np.clip((0.40 - z) / 0.08, 0, 1)
    amt = swell * (0.75 + 0.35 * np.clip(w_torso, 0, 1)) * (1 - np.clip(w_hand, 0, 1)) * (1 - boots) * (1 - np.clip(w_head, 0, 1))
    new = w + nr * amt[:, None]
    chest = np.clip((z - 1.05) / 0.15, 0, 1) * np.clip((1.52 - z) / 0.06, 0, 1) * np.clip(w_torso, 0, 1)
    new[:, 0] *= 1 + 0.045 * chest
    put_world(body, new, M)
    print(f'swell {swell} on {body.name}: {len(co)} verts, push {amt.min()*100:.2f}-{amt.max()*100:.2f} cm, '
          f'head verts held {(w_head > 0.5).sum()}, hands {(w_hand > 0.5).sum()}')
    from scipy.spatial import cKDTree
    tree = cKDTree(w); d = new - w
    import re
    groups = {}                                               # parts of one prop (guard0, hilt0, scabbard0) move together
    for p in props: groups.setdefault(re.sub(r'^[A-Za-z_]+', '', p.name) or p.name, []).append(p)
    for key, parts in groups.items():
        data = [world(p) for p in parts]
        pw = np.vstack([x[1] for x in data])
        dist, nn = tree.query(pw)
        k = nn[np.argsort(dist)[:max(1, len(pw) // 2)]]        # the body under the half of the prop nearest to it
        shift = d[k].mean(0)
        for p, (_, w_, _, PM) in zip(parts, data): put_world(p, w_ + shift, PM)
        print(f'  prop {"+".join(p.name for p in parts)}: moved with the body {np.linalg.norm(shift)*100:.2f} cm')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('inp'); ap.add_argument('out')
    ap.add_argument('--swell', type=float, default=0.016); ap.add_argument('--body')
    a = ap.parse_args()
    import bpy
    bpy.ops.wm.open_mainfile(filepath=a.inp)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers)]
    body = next(o for o in meshes if o.name == a.body) if a.body else max(meshes, key=lambda o: len(o.data.vertices))
    swell_body(body, [o for o in meshes if o is not body], a.swell)
    bpy.ops.wm.save_as_mainfile(filepath=a.out, compress=True)
    print('saved', a.out)
