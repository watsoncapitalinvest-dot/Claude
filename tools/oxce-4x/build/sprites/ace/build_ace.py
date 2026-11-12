"""Ace (named Joe pilot) - ace_look.zip scripts/build_ace.py, patched for the build session exactly as the greenshirt
pilot's build_gs_pilot.py was:
    python3 build_ace.py -- cfg_ace_build.json [--save-blend OUT.blend]
  - materials: flat emission + IDSWITCH (input 2: R = garment id / 40, G = camera depth 8..12 m). Body ids from
    ace_ids.py (= greenshirts/gs_pilot_ids.py on Ace's own paint): suit 20, rest 21 (INKJOIN=21:20 at ink time);
    hoses 29; helmet (Ch20, visor cut open) 26; Duke face inside it (Ch33) 2, so PENFACE shades the face only
  - bones / vertex groups renamed to mixamorig:, empty-handed, no clip, cameras/lights/unused slots dropped, packed
  - --save-blend overrides cfg out_blend (this script has no render loop; render_anim.py is the design preview)
Everything else (slimming swell, leg-gear removal, hose recolour, visor cut, head layers, nudge) is the zip's code."""
import bpy, bmesh, sys, os, json, numpy as np, math
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(argv[0]))
if '--save-blend' in argv: cfg['out_blend'] = argv[argv.index('--save-blend') + 1]
X = np.load(cfg['xf'])
s, off, a_ymax, b_ymax = float(X['s']), X['off'], float(X['a_ymax']), float(X['b_ymax'])
A_DZ = float(X['amin'][1]) * 0.01 - (-0.0255) if False else None
# raw<->world maps (from bbox matching)
a_zoff = cfg['a_zoff']; b_zoff = cfg['b_zoff']
def a_r2w(p): return np.stack([p[..., 0] * 0.01, -p[..., 2] * 0.01, p[..., 1] * 0.01 + a_zoff], -1)
def b_w2r(w): return np.stack([w[..., 0] / 0.01, (w[..., 2] - b_zoff) / 0.01, -w[..., 1] / 0.01], -1)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=cfg['body'])
armA = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
meshA = [o for o in bpy.data.objects if o.type == 'MESH'][0]
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=cfg['head'])
newobjs = [o for o in bpy.data.objects if o not in before]
headB = [o for o in newobjs if o.type == 'MESH' and o.name.startswith(cfg.get('head_obj', 'Ch33_Body'))][0]

def emis_mat(name, img_path=None, color=None, gid=2, id_path=None):
    """beauty = flat emission (texture or colour); IDSWITCH input 2 = R garment id / 40, G = depth 8..12 m"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    if img_path:
        tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(img_path, check_existing=True); tx.interpolation = 'Closest'
        nt.links.new(tx.outputs[0], em.inputs[0])
    else:
        em.inputs[0].default_value = (*[(c / 255) ** 2.2 for c in color], 1)
    comb = nt.nodes.new('ShaderNodeCombineColor')
    if id_path:
        it = nt.nodes.new('ShaderNodeTexImage'); it.image = bpy.data.images.load(id_path, check_existing=True)
        it.image.colorspace_settings.name = 'Non-Color'; it.interpolation = 'Closest'
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(it.outputs['Color'], sep.inputs[0]); nt.links.new(sep.outputs[0], comb.inputs[0])
    else:
        comb.inputs[0].default_value = gid / 40.0
    camd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
    nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
    ei = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], ei.inputs['Color'])
    sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'; sw.inputs[0].default_value = 0.0
    nt.links.new(em.outputs[0], sw.inputs[1]); nt.links.new(ei.outputs[0], sw.inputs[2]); nt.links.new(sw.outputs[0], out.inputs[0])
    return m

# --- body A: textures, clip above neck cut
for i, slot in enumerate(meshA.material_slots):
    slot.material = emis_mat(f'A{i}', os.path.join(cfg['a_tex'], cfg['a_tex_files'][i]), id_path=os.path.join(cfg['id_dir'], 'id_' + cfg['a_tex_files'][i]))
mw = meshA.matrix_world; mwi = mw.inverted()
zc = 0.01 * cfg['clipcut'] * a_ymax + a_zoff
bm = bmesh.new(); bm.from_mesh(meshA.data)
co_l = mwi @ Vector((0, 0, zc)); nrm_l = (mwi.to_3x3() @ Vector((0, 0, 1))).normalized()
geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co_l, plane_no=nrm_l, clear_outer=True)
sw = cfg.get('swell', 0)
if sw:
    bm.normal_update()
    for v in bm.verts:
        w = mw @ v.co; ax = abs(w.x); z = w.z
        if ax > 0.62: f = 0.0                                  # hands
        elif ax > 0.25: f = 0.75 * min(1, (0.62 - ax) / 0.08)  # arms, fading at the wrist
        else: f = 1.0
        if z < 0.5: f *= 0.75
        if z < 0.26: f *= max(0.0, (z - 0.12) / 0.14)          # fade over the boot tops
        n = (mw.to_3x3() @ v.normal).normalized()
        w2 = w + n * sw * f
        if 1.12 < z < 1.56 and ax < 0.32:                        # chest / shoulders wider
            k = cfg.get('chest_widen', 0.045) * min(1, (z - 1.12) / 0.08) * min(1, (1.56 - z) / 0.06) * min(1, (0.32 - ax) / 0.08 + 0.0)
            w2.x *= 1 + k
        v.co = mwi @ w2

if cfg.get('remove_parts'):
    cents = np.array(json.load(open(cfg['remove_parts'])))
    recol = np.array(json.load(open(cfg['recolor_parts']))) if cfg.get('recolor_parts') else None; recol_faces = set()
    bm.verts.ensure_lookup_table(); seen = set(); kill = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; seen.add(v.index); comp = []
        while st:
            x = st.pop(); comp.append(x)
            for e in x.link_edges:
                w = e.other_vert(x)
                if w.index not in seen: seen.add(w.index); st.append(w)
        c = np.mean([np.array(mw @ q.co) for q in comp], 0)
        if np.min(np.linalg.norm(cents - c, axis=1)) < 0.01: kill += comp
        elif recol is not None and np.min(np.linalg.norm(recol - c, axis=1)) < 0.01: recol_faces |= {f for q in comp for f in q.link_faces}
        elif len(comp) < cfg.get('small_n', 0) and c[2] < cfg.get('small_z', 0): kill += comp
    if recol is not None and recol_faces:
        meshA.data.materials.append(emis_mat('RECOL', color=cfg['recolor_color'], gid=29)); ri = len(meshA.data.materials) - 1
        for f in recol_faces: f.material_index = ri
        print('recoloured faces', len(recol_faces))
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); print('removed verts', len(kill))
if cfg.get('armband'):
    ab = cfg['armband']; nm = len(meshA.material_slots)
    meshA.data.materials.append(emis_mat('AW', color=[238, 238, 232])); meshA.data.materials.append(emis_mat('AR', color=[196, 32, 32]))
    for f in bm.faces:
        c = mw @ f.calc_center_median()
        if ab['x0'] <= c.x <= ab['x1'] and c.z > ab['zmin']:
            xm = (ab['x0'] + ab['x1']) / 2; w = ab['x1'] - ab['x0']
            front = c.y < ab['yfront']; red = front and (abs(c.x - xm) < w * 0.14 or abs(c.z - ab['zc']) < w * 0.14) and abs(c.z - ab['zc']) < w * 0.42
            f.material_index = nm + (1 if red else 0)
bm.to_mesh(meshA.data); bm.free()

# --- head B: move verts into A raw space, then to world; keep head part; reparent to A armature
for mod in list(headB.modifiers): headB.modifiers.remove(mod)
W = np.array([headB.matrix_world @ v.co for v in headB.data.vertices])
br = b_w2r(W)
ar = br * s + off
Wn = a_r2w(ar)
keepv = (br[:, 1] >= (0.845 - cfg['overlap']) * b_ymax) & (np.abs(br[:, 0]) < 0.075 * b_ymax)
headB.parent = None; headB.matrix_world = Matrix.Identity(4)
for v, p in zip(headB.data.vertices, Wn): v.co = Vector(p)
bm = bmesh.new(); bm.from_mesh(headB.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.where(~keepv)[0]], context='VERTS')
zb = 0.01 * (cfg['clipcut'] - cfg['overlap']) * a_ymax + a_zoff
geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, zb), plane_no=(0, 0, -1), clear_outer=True)
bm.to_mesh(headB.data); bm.free()
import re
for g in headB.vertex_groups: g.name = re.sub(r'^mixamorig\d*:', 'mixamorig:', g.name)
for i, slot in enumerate(headB.material_slots):
    slot.material = emis_mat(f'B{i}', os.path.join(cfg['b_tex'], cfg['b_tex_files'][i]), gid=cfg.get('head_gid', 2))
hairB = None
if cfg.get('hair_color'):
    hairB = [o for o in newobjs if o.name.startswith('Ch33_Hair')][0]
    for mod in list(hairB.modifiers): hairB.modifiers.remove(mod)
    Wh_ = np.array([hairB.matrix_world @ v.co for v in hairB.data.vertices])
    Wn_ = a_r2w(b_w2r(Wh_) * s + off)
    hairB.parent = None; hairB.matrix_world = Matrix.Identity(4)
    for v, p in zip(hairB.data.vertices, Wn_): v.co = Vector(p)
    for g in hairB.vertex_groups: g.name = g.name.replace('mixamorig7:', 'mixamorig:')
    hm = emis_mat('HAIR', color=cfg['hair_color'])
    for slot in hairB.material_slots: slot.material = hm
for o in newobjs:
    if o is not headB and o is not hairB: bpy.data.objects.remove(o, do_unlink=True)

def bind(o):
    o.parent = armA; o.matrix_parent_inverse = armA.matrix_world.inverted()
    m = o.modifiers.new('arm', 'ARMATURE'); m.object = armA
bind(headB)
if cfg.get('head_delete_region'):
    hd = cfg['head_delete_region']
    from PIL import Image as _I
    reg = np.asarray(_I.open(hd['regions']).convert('L')); RH = reg.shape[0]
    vals = set(v * 20 for v in hd['values'])
    bm = bmesh.new(); bm.from_mesh(headB.data); uvl = bm.loops.layers.uv.active
    kill = []
    for f in bm.faces:
        u = sum(l[uvl].uv.x for l in f.loops) / len(f.loops); v = sum(l[uvl].uv.y for l in f.loops) / len(f.loops)
        px = reg[min(RH - 1, int((1 - v % 1) * RH)), min(RH - 1, int((u % 1) * RH))]
        if int(px) in vals: kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(headB.data); bm.free(); print('visor faces removed', len(kill))
if cfg.get('extra_head'):
    eh = cfg['extra_head']; X2 = np.load(eh['xf']); s2, off2 = float(X2['s']), X2['off']
    before3 = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=eh['fbx'])
    new3 = [o for o in bpy.data.objects if o not in before3]
    hb = [o for o in new3 if o.type == 'MESH' and o.name.startswith(eh['obj'])][0]
    for mod in list(hb.modifiers): hb.modifiers.remove(mod)
    W2 = np.array([hb.matrix_world @ v.co for v in hb.data.vertices]); br2 = b_w2r(W2)
    by2 = float(X2['b_ymax'])
    keep2 = (br2[:, 1] >= (0.845 - eh.get('overlap', 0.03)) * by2) & (np.abs(br2[:, 0]) < 0.075 * by2)
    Wn2 = a_r2w(br2 * s2 + off2 + np.array(eh.get('nudge', [0, 0, 0])) * a_ymax)
    hb.parent = None; hb.matrix_world = Matrix.Identity(4)
    for v, p in zip(hb.data.vertices, Wn2): v.co = Vector(p)
    bm = bmesh.new(); bm.from_mesh(hb.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.where(~keep2)[0]], context='VERTS')
    bm.to_mesh(hb.data); bm.free()
    import re
    for g in hb.vertex_groups: g.name = re.sub(r'^mixamorig\d*:', 'mixamorig:', g.name)
    for slot in hb.material_slots: slot.material = emis_mat('F_' + slot.name, eh['tex'], gid=eh.get('gid', 2))
    for o in new3:
        if o is not hb: bpy.data.objects.remove(o, do_unlink=True)
    bind(hb); print('extra head added')
if hairB: bind(hairB)

# --- helmet
HM = np.load(cfg['helmet_full']) if cfg.get('helmet_full') else X['HM']
if len(HM) and cfg.get('helmet', True):
    Wh = a_r2w(HM.reshape(-1, 3))
    me = bpy.data.meshes.new('helmet'); n = len(HM)
    me.from_pydata([tuple(p) for p in Wh], [], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(n)])
    hob = bpy.data.objects.new('helmet', me); bpy.context.scene.collection.objects.link(hob)
    col = cfg['helmet_color']
    me.materials.append(emis_mat('H1', color=col)); me.materials.append(emis_mat('H0', color=[c * 0.66 for c in col]))
    mp = HM.reshape(-1, 3); hcen = np.array([(mp[:, 0].min() + mp[:, 0].max()) / 2, mp[:, 1].min(), (mp[:, 2].min() + mp[:, 2].max()) / 2])
    L = np.array([-0.45, 0.55, 0.7]); L /= np.linalg.norm(L)
    nr = HM.mean(1) - hcen; nr[:, 1] *= 1.3
    lit = (nr @ L) / np.linalg.norm(nr, axis=1) > cfg.get('helmet_cut', 0.05)
    for p, l in zip(me.polygons, lit): p.material_index = 0 if l else 1
    if cfg.get('medic'):
        me.materials.append(emis_mat('HW', color=[238, 238, 232])); me.materials.append(emis_mat('HR', color=[196, 32, 32]))
        Wt = a_r2w(HM.mean(1)); zlo, zhi = Wh[:, 2].min(), Wh[:, 2].max(); hh = zhi - zlo
        cx, cy = (Wh[:, 0].min() + Wh[:, 0].max()) / 2, (Wh[:, 1].min() + Wh[:, 1].max()) / 2
        b0, b1 = zlo + cfg.get('band', [0.42, 0.62])[0] * hh, zlo + cfg.get('band', [0.42, 0.62])[1] * hh
        for p, c in zip(me.polygons, Wt):
            az = math.degrees(math.atan2(c[0] - cx, -(c[1] - cy)))
            inband = b0 <= c[2] <= b1
            near = min(abs(((az - a0) + 180) % 360 - 180) for a0 in (0, 90, 180, -90))
            if inband: p.material_index = 2
            mid = (b0 + b1) / 2; bh = (b1 - b0)
            if (near < 9 and abs(c[2] - mid) < bh * 0.42) or (near < 3.2 and abs(c[2] - mid) < bh * 0.42) : p.material_index = 3
            if near < 3.2 and abs(c[2] - mid) < bh * 0.42: p.material_index = 3
            if near < 9 and abs(c[2] - mid) < bh * 0.14: p.material_index = 3
            if near < 9 and abs(c[2] - mid) >= bh * 0.14 and near >= 3.2 and inband: p.material_index = 2
    me = hob.data
    vg = hob.vertex_groups.new(name='mixamorig:Head'); vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    me.validate()
    bmh = bmesh.new(); bmh.from_mesh(me); bmesh.ops.remove_doubles(bmh, verts=bmh.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bmh, faces=bmh.faces); bmh.to_mesh(me); bmh.free()
    bind(hob)

import re as _re
for b_ in armA.data.bones: b_.name = _re.sub(r'mixamorig\d*:', 'mixamorig:', b_.name)
for o_ in list(bpy.data.objects):
    for vg in getattr(o_, 'vertex_groups', []): vg.name = _re.sub(r'mixamorig\d*:', 'mixamorig:', vg.name)
    if o_.type in ('CAMERA', 'LIGHT'): bpy.data.objects.remove(o_)
for o_ in [o for o in bpy.data.objects if o.type == 'MESH']:          # drop material slots no face uses
    used = {p.material_index for p in o_.data.polygons}
    for i in reversed(range(len(o_.data.materials))):
        if i not in used:
            for p in o_.data.polygons:
                if p.material_index > i: p.material_index -= 1
            o_.data.materials.pop(index=i)
armA.animation_data_clear()
for a_ in list(bpy.data.actions): bpy.data.actions.remove(a_)
armA.name = 'Armature'; bpy.data.orphans_purge(do_recursive=True); bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=cfg['out_blend'])
print('saved scene')
