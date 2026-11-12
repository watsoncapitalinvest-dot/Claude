"""Fit a downloaded bandolier (Playmobil STL loop, z-up) onto the swelled Ch49 rest body, skin-bound.
Method (after CAST's cast_props.bandolier description): decimate -> orient (strap runs from his LEFT shoulder to his
RIGHT hip, mirrored if needed) -> box-fit to the torso -> radial wrap onto the shirt surface (keeps the strap's own
thickness and the pouches' depth) -> weights copied from the nearest body vertex (Armature modifier) ->
two cel materials: strap and pouches get separate garment ids so every pouch gets an ink outline."""
import bpy, numpy as np
from mathutils import Vector


def _shirt_layer(body_meshes):
    for o in body_meshes:
        for m in o.data.materials:
            if m and m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and n.image and '1002' in (n.image.name + n.image.filepath): return o
    return max(body_meshes, key=lambda o: len(o.data.vertices))


POUCHES = (0.28, 0.48, 0.68); POUCH = (0.064, 0.072, 0.032); NARROW = 0.6; SMOOTH_IT = 12     # along, across, depth (m)


def add_bandolier(stl, body_meshes, arm, cel_material, strap_rgb=(88, 105, 51), pouch_rgb=(88, 105, 51),
                  ratio=0.08, gap=0.005, zlo=0.93, zhi=1.50, strap_id=9, pouch_id=10):
    bpy.ops.wm.stl_import(filepath=stl)
    ob = bpy.context.selected_objects[0]; bpy.context.view_layer.objects.active = ob
    if ratio < 1:
        md = ob.modifiers.new('dec', 'DECIMATE'); md.ratio = ratio; bpy.ops.object.modifier_apply(modifier='dec')
    me = ob.data; ob.matrix_world.identity()
    V = np.array([v.co[:] for v in me.vertices], np.float64)
    V -= (V.min(0) + V.max(0)) / 2
    # strap direction on the projection: x~z correlation must be positive (high on his left = +x)
    if np.corrcoef(V[:, 0], V[:, 2])[0, 1] < 0: V[:, 0] *= -1; mirrored = True
    else: mirrored = False
    # body: shirt layer only (the webbing is hidden on characters that wear the bandolier)
    shirt = _shirt_layer(body_meshes)
    B = np.array([(shirt.matrix_world @ v.co)[:] for v in shirt.data.vertices])
    tor = B[(B[:, 2] > zlo) & (B[:, 2] < zhi) & (np.abs(B[:, 0]) < 0.24)]
    lo, hi = np.percentile(tor, 1, 0), np.percentile(tor, 99, 0)
    pl, ph = V.min(0), V.max(0)
    V = lo + (V - pl) / (ph - pl) * (hi - lo)                         # box-fit
    # radial wrap: per (angle, height) bin, outer shirt radius vs the prop's inner radius
    NA, DZ = 72, 0.01
    def polar(P, c):
        d = P[:, :2] - c; return np.arctan2(d[:, 1], d[:, 0]), np.hypot(d[:, 0], d[:, 1])
    zb = lambda z: np.clip(((z - zlo) / DZ).astype(int), 0, int((zhi - zlo) / DZ))
    nz = int((zhi - zlo) / DZ) + 1
    cen = np.zeros((nz, 2))
    for k in range(nz):
        s = tor[np.abs(tor[:, 2] - (zlo + (k + 0.5) * DZ)) < DZ]
        cen[k] = s[:, :2].mean(0) if len(s) else tor[:, :2].mean(0)
    bz = zb(B[:, 2]); ab, rb = polar(B, cen[bz]); ia = ((ab + np.pi) / (2 * np.pi) * NA).astype(int) % NA
    rbody = np.full((nz, NA), np.nan)
    sel = (B[:, 2] > zlo - 0.02) & (B[:, 2] < zhi + 0.02) & (np.abs(B[:, 0]) < 0.30)
    for k, a, r in zip(bz[sel], ia[sel], rb[sel]):
        if not (rbody[k, a] >= r): rbody[k, a] = r
    from scipy import ndimage as ndi
    msk = np.isnan(rbody)
    if msk.any():
        idx = ndi.distance_transform_edt(msk, return_distances=False, return_indices=True); rbody = rbody[tuple(idx)]
    vz = zb(V[:, 2]); av, rv = polar(V, cen[vz]); iv = ((av + np.pi) / (2 * np.pi) * NA).astype(int) % NA
    rin = np.full((nz, NA), np.inf)
    np.minimum.at(rin, (vz, iv), rv)
    shift = rbody + gap - rin; bad = ~np.isfinite(shift)
    if bad.any():
        idx = ndi.distance_transform_edt(bad, return_distances=False, return_indices=True); shift = shift[tuple(idx)]
    shift = ndi.gaussian_filter(shift, (1.5, 2.0), mode=('nearest', 'wrap'))      # smooth: no tearing between bins
    fz = np.clip((V[:, 2] - zlo) / DZ - 0.5, 0, nz - 1); fa = (av + np.pi) / (2 * np.pi) * NA - 0.5
    sv = ndi.map_coordinates(np.concatenate([shift, shift[:, :1]], 1), [fz, fa % NA], order=1, mode='nearest')
    excess = rv - rin[vz, iv]
    rnew = rv + sv
    V[:, 0] = cen[vz, 0] + np.cos(av) * rnew; V[:, 1] = cen[vz, 1] + np.sin(av) * rnew
    if NARROW < 1:
        # narrow the strap: pull each vertex toward its local centroid (the strap centre line), then restore its radius
        from scipy.spatial import cKDTree
        tr = cKDTree(V); cnt = np.array([V[i].mean(0) for i in tr.query_ball_point(V, 0.045)])
        V = cnt + NARROW * (V - cnt)
        vz2 = zb(V[:, 2]); a2, r2 = polar(V, cen[vz2])
        V[:, 0] = cen[vz2, 0] + np.cos(a2) * rnew; V[:, 1] = cen[vz2, 1] + np.sin(a2) * rnew
    for i, v in enumerate(me.vertices): v.co = Vector(V[i])
    me.update()
    sm = ob.modifiers.new('sm', 'SMOOTH'); sm.factor = 0.7; sm.iterations = SMOOTH_IT
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier='sm')
    V = np.array([v.co[:] for v in me.vertices], np.float64)
    # strap material; then simple box pouches along the FRONT run of the strap (the art's three ammo pouches)
    me.materials.clear()
    me.materials.append(cel_material('bandolier_strap', strap_rgb, strap_id)); me.materials.append(cel_material('bandolier_pouch', pouch_rgb, pouch_id))
    for p in me.polygons: p.material_index = 0; p.use_smooth = True
    import bmesh
    front = V[(V[:, 1] < np.interp(V[:, 2], zlo + (np.arange(nz) + 0.5) * DZ, cen[:, 1]) - 0.02)]
    c0 = front.mean(0); X2 = front[:, [0, 2]] - c0[[0, 2]]
    d2 = np.linalg.svd(X2, full_matrices=False)[2][0]; d2 = d2 if d2[1] < 0 else -d2      # running down the chest
    t = X2 @ d2; tmin, tmax = t.min(), t.max()
    bm = bmesh.new(); bm.from_mesh(me)
    for f in POUCHES:
        tc = tmin + f * (tmax - tmin); near = front[np.abs(t - tc) < 0.012]
        c = near.mean(0) if len(near) else c0
        k = int(np.clip((c[2] - zlo) / DZ, 0, nz - 1)); n = np.array([c[0] - cen[k, 0], c[1] - cen[k, 1], 0.0]); n /= np.linalg.norm(n) + 1e-9
        u = np.array([d2[0], 0.0, d2[1]]); u -= n * (u @ n); u /= np.linalg.norm(u); w = np.cross(n, u)
        ctr = c + n * (POUCH[2] / 2 + 0.007)
        res = bmesh.ops.create_cube(bm, size=1.0); vs = res['verts']
        for v_ in vs:
            q = np.array(v_.co[:]); p_ = ctr + u * q[0] * POUCH[0] + w * q[1] * POUCH[1] + n * q[2] * POUCH[2]; v_.co = Vector(p_)
        for fc in {f_ for v_ in vs for f_ in v_.link_faces}: fc.material_index = 1
    bm.to_mesh(me); bm.free(); me.update()
    V = np.array([v.co[:] for v in me.vertices]); npouch = sum(p.material_index for p in me.polygons)
    # skin: copy weights from the nearest body vertex (any body mesh)
    from scipy.spatial import cKDTree
    allv, owner = [], []
    for o in body_meshes:
        W = np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices]); allv.append(W); owner += [(o, i) for i in range(len(W))]
    tree = cKDTree(np.concatenate(allv)); _, nn = tree.query(V)
    groups = {}
    for vi, j in enumerate(nn):
        o, bi = owner[j]
        for g in o.data.vertices[bi].groups:
            name = o.vertex_groups[g.group].name
            groups.setdefault(name, []).append((vi, g.weight))
    for name, lst in groups.items():
        vg = ob.vertex_groups.new(name=name)
        for vi, w in lst: vg.add([vi], w, 'REPLACE')
    md = ob.modifiers.new('arm', 'ARMATURE'); md.object = arm
    print('bandolier', stl.split('/')[-1], 'verts', len(V), 'mirrored', mirrored, 'pouch faces', npouch, 'of', len(me.polygons))
    return ob


def add_bandolier_sweep(body_meshes, arm, cel_material, top=(0.115, 1.475), bottom=(-0.150, 1.035), width=0.046,
                        thick=0.007, gap=0.004, strap_rgb=(88, 105, 51), pouch_rgb=(88, 105, 51), strap_id=9, pouch_id=10,
                        pouches=(0.22, 0.45, 0.68), pouch=(0.062, 0.066, 0.030), n_samp=220, over_gear=False, rsmooth=3.0):
    """Clean procedural bandolier: the loop where a tilted plane (through his LEFT shoulder top and RIGHT hip, containing
    the front-back axis) meets the shirt surface, swept as a flat band of constant width; box pouches on the front run.
    Skinned from the nearest TORSO vertex only (arm-weighted vertices excluded) so arm swings don't drag it."""
    import bmesh
    from scipy import ndimage as ndi
    from scipy.spatial import cKDTree
    if over_gear:      # lay it over the X-harness too (John: keep the X): outer surface of shirt + gear, minus hands
        B = []
        for o_ in body_meshes:
            gi = {vg.index: vg.name for vg in o_.vertex_groups}
            for vv in o_.data.vertices:
                if sum(g.weight for g in vv.groups if 'Hand' in gi[g.group]) < 0.2: B.append((o_.matrix_world @ vv.co)[:])
        B = np.array(B)
    else:
        shirt = _shirt_layer(body_meshes)
        B = np.array([(shirt.matrix_world @ v.co)[:] for v in shirt.data.vertices])
    t3 = np.array([top[0], 0.0, top[1]]); b3 = np.array([bottom[0], 0.0, bottom[1]])
    dirv = (t3 - b3) / np.linalg.norm(t3 - b3); yax = np.array([0.0, 1.0, 0.0])
    nrm = np.cross(dirv, yax); nrm /= np.linalg.norm(nrm)            # plane normal
    tor = B[(np.abs(B[:, 0]) < 0.21) | (B[:, 2] < 1.22)]
    tor = tor[(tor[:, 2] > bottom[1] - 0.08) & (tor[:, 2] < top[1] + 0.06)]
    c = (t3 + b3) / 2; c[1] = np.median(tor[:, 1])
    sl = tor[np.abs((tor - c) @ nrm) < 0.012]
    e1 = dirv; e2 = yax - (yax @ e1) * e1; e2 /= np.linalg.norm(e2)  # in-plane axes
    q = sl - c; ang = np.arctan2(q @ e2, q @ e1); rad = np.hypot(q @ e1, q @ e2)
    NB = 180; ib = ((ang + np.pi) / (2 * np.pi) * NB).astype(int) % NB
    rb = np.full(NB, np.nan)
    for i_, r_ in zip(ib, rad):
        if not (rb[i_] >= r_): rb[i_] = r_
    good = ~np.isnan(rb)
    xs = np.arange(NB); rb = np.interp(xs, xs[good], rb[good], period=NB)
    rb = ndi.maximum_filter1d(rb, 5, mode='wrap') if over_gear else rb      # ride over strap edges, don't dip between
    rb = ndi.gaussian_filter1d(rb, rsmooth, mode='wrap')
    th = np.linspace(-np.pi, np.pi, n_samp, endpoint=False)
    r = np.interp((th + np.pi) / (2 * np.pi) * NB, np.arange(NB + 1), np.append(rb, rb[0]))
    outd = np.outer(np.cos(th), e1) + np.outer(np.sin(th), e2)
    P = c + outd * (r + gap)[:, None]
    me = bpy.data.meshes.new('bandolier'); ob = bpy.data.objects.new('bandolier', me); bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new(); ring = []
    for i in range(n_samp):
        o = outd[i]; a = P[i] - nrm * width / 2; b_ = P[i] + nrm * width / 2
        ring.append([bm.verts.new(Vector(a)), bm.verts.new(Vector(b_)), bm.verts.new(Vector(b_ + o * thick)), bm.verts.new(Vector(a + o * thick))])
    for i in range(n_samp):
        A, Bq = ring[i], ring[(i + 1) % n_samp]
        for k in range(4):
            bm.faces.new((A[k], A[(k + 1) % 4], Bq[(k + 1) % 4], Bq[k]))
    # pouches on the front run (outward direction facing -y), spaced from the shoulder down to the hip
    front = [i for i in range(n_samp) if outd[i] @ yax < -0.25]
    itop = max(front, key=lambda j: P[j][2]); ibot = min(front, key=lambda j: P[j][2])
    for f in pouches:                                                  # evenly along the straight front run
        tgt = P[itop] + f * (P[ibot] - P[itop]); i = min(front, key=lambda j: np.linalg.norm(P[j] - tgt))
        o = outd[i]; tng = P[(i + 1) % n_samp] - P[i - 1]; tng /= np.linalg.norm(tng)
        ctr = P[i] + o * (thick + pouch[2] / 2)
        res = bmesh.ops.create_cube(bm, size=1.0)
        for v_ in res['verts']:
            qv = np.array(v_.co[:]); v_.co = Vector(ctr + tng * qv[0] * pouch[0] + nrm * qv[1] * pouch[1] + o * qv[2] * pouch[2])
        for fc in {f_ for v_ in res['verts'] for f_ in v_.link_faces}: fc.material_index = 1
        # detail (John: "detail onto the pouches"): a flap over the top half of the front face + a snap button
        upv = tng if tng[2] >= 0 else -tng                    # along the strap, toward the shoulder = the pouch's top
        def slab(cen, ax, mat):
            r_ = bmesh.ops.create_cube(bm, size=1.0)
            for v_ in r_['verts']:
                qv = np.array(v_.co[:]); v_.co = Vector(cen + sum(vec * qv[k] * sz for k, (vec, sz) in enumerate(ax)))
            for fc in {f_ for v_ in r_['verts'] for f_ in v_.link_faces}: fc.material_index = mat
        front_face = ctr + o * (pouch[2] / 2)
        slab(front_face + upv * pouch[0] * 0.26 + o * 0.0025, ((upv, pouch[0] * 0.50), (nrm, pouch[1] * 1.06), (o, 0.005)), 2)   # flap
        slab(front_face + upv * pouch[0] * 0.04 + o * 0.0055, ((upv, 0.011), (nrm, 0.011), (o, 0.004)), 3)                       # snap
    bm.normal_update(); bm.to_mesh(me); bm.free()
    me.materials.append(cel_material('bandolier_strap', strap_rgb, strap_id)); me.materials.append(cel_material('bandolier_pouch', pouch_rgb, pouch_id))
    me.materials.append(cel_material('bandolier_flap', tuple(min(255, int(c * 1.10)) for c in pouch_rgb), 12))
    me.materials.append(cel_material('bandolier_snap', (52, 40, 24), 15))
    bmesh_ = None
    # torso-only skinning
    V = np.array([v.co[:] for v in me.vertices]); allv, owner = [], []
    for o_ in body_meshes:
        gi = {vg.index: vg.name for vg in o_.vertex_groups}
        for vv in o_.data.vertices:
            armw = sum(g.weight for g in vv.groups if any(k in gi[g.group] for k in ('Arm', 'Hand')))
            if armw < 0.15: allv.append((o_.matrix_world @ vv.co)[:]); owner.append((o_, vv.index))
    _, nn = cKDTree(np.array(allv)).query(V)
    groups = {}
    for vi, j in enumerate(nn):
        o_, bi = owner[j]
        for g in o_.data.vertices[bi].groups:
            groups.setdefault(o_.vertex_groups[g.group].name, []).append((vi, g.weight))
    for name, lst in groups.items():
        vg = ob.vertex_groups.new(name=name)
        for vi, w in lst: vg.add([vi], w, 'REPLACE')
    md = ob.modifiers.new('arm', 'ARMATURE'); md.object = arm
    print('bandolier sweep: plane slice pts', len(sl), 'samples', n_samp, 'front', len(front))
    return ob
