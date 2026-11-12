"""John's 12 Nov Ch49 rules as functions, lifted unchanged from duke_build_v3 factory_blend.py, for the builders that
do not go through the factory (doc/build_doc.py, stalker/build_stalker.py - their Ch18 head):
  cut_body(o, h49, clean)          clean plane cut at the neck (--clean_collar) or the old whole-face cut
  swell(body_meshes, h49, amount, clean)   +amount along the normals, chest +4.5 %, gear layer locked to the shirt
  cut_head(o, h33, clean)          the head's neck bottom: clean plane cut, head part only
  tuck_neck(o, h49)                neck bottom tucked inside the collar
All take meshes already in world space where the factory has them (see the call sites)."""
import bmesh, numpy as np
from mathutils import Vector
CUT = 0.845
def world_coords(o):
    M = o.matrix_world; return np.array([M @ v.co for v in o.data.vertices])
def cut_faces(o, keep_fn):
    W = world_coords(o)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    kill = [f for f in bm.faces if not keep_fn(W[[v.index for v in f.verts]].mean(0))]
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(o.data); bm.free()
def cut_body(o, h49, clean, collar_drop=0.006):
    if not clean: return cut_faces(o, lambda c: c[2] < CUT * h49)
    M = o.matrix_world; Mi = M.inverted(); zc = CUT * h49 - collar_drop
    bm = bmesh.new(); bm.from_mesh(o.data)
    co_l = Mi @ Vector((0, 0, zc)); no_l = (Mi.to_3x3() @ Vector((0, 0, 1))).normalized()
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co_l, plane_no=no_l, clear_outer=True)
    bm.to_mesh(o.data); bm.free()
def swell(body_meshes, h49, SWELL, clean, layer_dist=0.03):
    """call after bake_unparent (mesh co = world)"""
    from scipy.spatial import cKDTree
    SW = {}
    for o in body_meshes:
        me = o.data
        gi = {vg.index: vg.name for vg in o.vertex_groups}
        co = np.array([v.co[:] for v in me.vertices]); nr = np.array([v.normal[:] for v in me.vertices])
        w_hand = np.zeros(len(co)); w_torso = np.zeros(len(co))
        for v in me.vertices:
            for g in v.groups:
                n = gi[g.group]
                if 'Hand' in n: w_hand[v.index] += g.weight
                if any(k in n for k in ('Spine', 'Hips', 'Shoulder', 'Neck')): w_torso[v.index] += g.weight
        z = co[:, 2]
        boots = np.clip((0.40 - z) / 0.08, 0, 1)
        amt = SWELL * (0.75 + 0.35 * np.clip(w_torso, 0, 1)) * (1 - np.clip(w_hand, 0, 1)) * (1 - boots)
        if clean:
            top = np.clip((z - (CUT * h49 - 0.05)) / 0.03, 0, 1)[:, None]
            flat = nr.copy(); flat[:, 2] = 0; flat /= np.maximum(np.linalg.norm(flat, axis=1, keepdims=True), 1e-6)
            nr = nr * (1 - top) + flat * top
        co = co + nr * amt[:, None]
        chest = np.clip((z - 1.05) / 0.15, 0, 1) * np.clip((1.52 - z) / 0.06, 0, 1) * np.clip(w_torso, 0, 1)
        co[:, 0] *= 1 + 0.045 * chest
        SW[o.name] = (np.array([v.co[:] for v in me.vertices]), co, nr)
    def _sheet(o):
        for m in o.data.materials:
            if m and m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and n.image and '1002' in (n.image.name + n.image.filepath): return '1002'
        return ''
    main = ([o for o in body_meshes if _sheet(o) == '1002'] or [max(body_meshes, key=lambda o: len(o.data.vertices))])[0]
    m0, m1, _ = SW[main.name]; tree = cKDTree(m0)
    for o in body_meshes:
        c0, c1, nr = SW[o.name]
        if o is not main:
            dist, nn = tree.query(c0); on = dist < layer_dist
            c1 = c1.copy(); c1[on] = c0[on] + (m1[nn[on]] - m0[nn[on]]) + nr[on] * 0.002
            print('layer-locked', o.name, int(on.sum()), 'of', len(c0))
        o.data.vertices.foreach_set('co', c1.ravel()); o.data.update()
    print('swell', SWELL, 'base layer', main.name)
def cut_head(o, h33, clean):
    """before the head is moved onto the body (head-model world space)"""
    if not clean: return cut_faces(o, lambda c: c[2] >= CUT * h33 and abs(c[0]) < 0.075 * h33)
    M = o.matrix_world; Mi = M.inverted(); zc = CUT * h33 - 0.012 * h33
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Mi @ Vector((0, 0, zc)),
                           plane_no=(Mi.to_3x3() @ Vector((0, 0, 1))).normalized(), clear_inner=True)
    bm.to_mesh(o.data); bm.free()
    cut_faces(o, lambda c: abs(c[0]) < 0.075 * h33)
def tuck_neck(o, h49, collar_drop=0.006, band=0.035, tk=0.12):
    """after the head is on the body (world space)"""
    Wn = world_coords(o); zb = CUT * h49 - collar_drop
    nk = (Wn[:, 2] < zb + band) & (np.abs(Wn[:, 0]) < 0.09)
    if nk.any():
        ax = Wn[nk][:, :2].mean(0); Mi = o.matrix_world.inverted()
        for i in np.nonzero(nk)[0]:
            f = 1 - tk * min(1.0, (zb + band - Wn[i, 2]) / band)
            p = Wn[i].copy(); p[:2] = ax + (p[:2] - ax) * f
            o.data.vertices[i].co = Mi @ Vector(p)
