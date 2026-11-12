"""Regular Joes ("greenshirts") v3 - rifleman / medic on the swollen Ch49 body, Duke's Ch33 head, helmet.
The design chat's gs\\scripts\\build49.py, patched for the build session:
  python3 build_gs49.py -- cfg_<look>.json            (cfg out_blend = the .blend render_char.py takes)
Materials are flat emission with an IDSWITCH: Ch49 garment ids from Duke's id maps (WS anim/tex),
head 2, helmet 36 for every helmet material (ink = outer contour only), medic armband 38.
Empty-handed, no clip, textures packed."""
import bpy, bmesh, sys, os, json, numpy as np, math
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(argv[0]))
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
meshesA = [o for o in bpy.data.objects if o.type == 'MESH']
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=cfg['head'])
newobjs = [o for o in bpy.data.objects if o not in before]
headB = [o for o in newobjs if o.name.startswith('Ch33_Body')][0]

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

def id_map_for(sheet_fn):
    """Duke's Ch49 garment-id map for this sheet; for the medic, the white armband + red cross get id 38."""
    src = os.path.join(cfg['id_dir'], 'id_' + sheet_fn)
    if not cfg.get('medic'): return src
    from PIL import Image
    ida = np.asarray(Image.open(src).convert('RGB')).copy()
    tex = np.asarray(Image.open(os.path.join(cfg['a_tex'], sheet_fn)).convert('RGB').resize(ida.shape[1::-1], Image.NEAREST)).astype(int)
    white = tex.min(-1) > 205
    red = (tex[..., 0] > 150) & (tex[..., 1] < 80) & (tex[..., 2] < 80)
    mark = white | red
    ida[mark, 0] = round(38 * 255 / 40)
    dst = os.path.join(os.path.dirname(cfg['out_blend']), 'id_medic_' + sheet_fn)
    Image.fromarray(ida).save(dst); print('medic armband id 38 texels', int(mark.sum()), 'in', sheet_fn)
    return dst

zc = 0.01 * cfg['clipcut'] * a_ymax + a_zoff
for meshA in meshesA:
    for slot in meshA.material_slots:
        nm = slot.material.name if slot.material else ''
        fn = cfg['a_mat_tex'].get(nm.split('.')[0])
        slot.material = emis_mat('A_' + nm, os.path.join(cfg['a_tex'], fn), id_path=id_map_for(fn)) if fn else emis_mat('A_' + nm, color=[255, 0, 255])
    mw = meshA.matrix_world; mwi = mw.inverted()
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
for g in headB.vertex_groups: g.name = g.name.replace('mixamorig7:', 'mixamorig:')
for i, slot in enumerate(headB.material_slots):
    slot.material = emis_mat(f'B{i}', os.path.join(cfg['b_tex'], cfg['b_tex_files'][i]), gid=2)
hairB = None
if cfg.get('hair_color'):
    hairB = [o for o in newobjs if o.name.startswith('Ch33_Hair')][0]
    for mod in list(hairB.modifiers): hairB.modifiers.remove(mod)
    Wh_ = np.array([hairB.matrix_world @ v.co for v in hairB.data.vertices])
    Wn_ = a_r2w(b_w2r(Wh_) * s + off)
    hairB.parent = None; hairB.matrix_world = Matrix.Identity(4)
    for v, p in zip(hairB.data.vertices, Wn_): v.co = Vector(p)
    for g in hairB.vertex_groups: g.name = g.name.replace('mixamorig7:', 'mixamorig:')
    hm = emis_mat('HAIR', color=cfg['hair_color'], gid=1)
    for slot in hairB.material_slots: slot.material = hm
for o in newobjs:
    if o is not headB and o is not hairB: bpy.data.objects.remove(o, do_unlink=True)

def bind(o):
    o.parent = armA; o.matrix_parent_inverse = armA.matrix_world.inverted()
    m = o.modifiers.new('arm', 'ARMATURE'); m.object = armA
bind(headB)
if hairB: bind(hairB)

# --- helmet
HM = np.load(cfg['helmet_full']) if cfg.get('helmet_full') else X['HM']
if len(HM) and cfg.get('helmet', True):
    Wh = a_r2w(HM.reshape(-1, 3))
    me = bpy.data.meshes.new('helmet'); n = len(HM)
    me.from_pydata([tuple(p) for p in Wh], [], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(n)])
    hob = bpy.data.objects.new('helmet', me); bpy.context.scene.collection.objects.link(hob)
    col = cfg['helmet_color']
    me.materials.append(emis_mat('H1', color=col, gid=36)); me.materials.append(emis_mat('H0', color=[c * 0.66 for c in col], gid=36))
    mp = HM.reshape(-1, 3); hcen = np.array([(mp[:, 0].min() + mp[:, 0].max()) / 2, mp[:, 1].min(), (mp[:, 2].min() + mp[:, 2].max()) / 2])
    L = np.array([-0.45, 0.55, 0.7]); L /= np.linalg.norm(L)
    nr = HM.mean(1) - hcen; nr[:, 1] *= 1.3
    lit = (nr @ L) / np.linalg.norm(nr, axis=1) > cfg.get('helmet_cut', 0.05)
    for p, l in zip(me.polygons, lit): p.material_index = 0 if l else 1
    if cfg.get('medic'):
        me.materials.append(emis_mat('HW', color=[238, 238, 232], gid=36)); me.materials.append(emis_mat('HR', color=[196, 32, 32], gid=36))
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

# render_char.py counts every material against its 40-step id range, so the helmet's 2-4 flat colours become
# ONE material whose colour comes from a face-corner attribute (same look; helmet id 36 throughout), and
# material slots no face uses (the Ch49 eyelashes, cut away above the neck) are dropped.
hel = bpy.data.objects.get('helmet')
if hel is not None:
    hme = hel.data
    def beauty_rgb(m):
        sw = m.node_tree.nodes['IDSWITCH']; return tuple(sw.inputs[1].links[0].from_node.inputs[0].default_value)
    pal = [beauty_rgb(m) for m in hme.materials]
    at = hme.color_attributes.new('hcol', 'FLOAT_COLOR', 'CORNER')
    for poly in hme.polygons:
        c = pal[poly.material_index]
        for li in poly.loop_indices: at.data[li].color = c
    hm1 = emis_mat('helmet', color=[0, 0, 0], gid=36); nt = hm1.node_tree
    em = nt.nodes['IDSWITCH'].inputs[1].links[0].from_node
    attn = nt.nodes.new('ShaderNodeAttribute'); attn.attribute_name = 'hcol'; nt.links.new(attn.outputs['Color'], em.inputs[0])
    hme.materials.clear(); hme.materials.append(hm1)
    for poly in hme.polygons: poly.material_index = 0
for o_ in [o for o in bpy.data.objects if o.type == 'MESH']:
    used = {p.material_index for p in o_.data.polygons}
    for i in reversed(range(len(o_.data.materials))):
        if i not in used:
            for p in o_.data.polygons:
                if p.material_index > i: p.material_index -= 1
            o_.data.materials.pop(index=i)
import re
for b_ in armA.data.bones: b_.name = re.sub(r'mixamorig\d*:', 'mixamorig:', b_.name)
for o_ in bpy.data.objects:
    for vg in getattr(o_, 'vertex_groups', []): vg.name = re.sub(r'mixamorig\d*:', 'mixamorig:', vg.name)
    if o_.type in ('CAMERA', 'LIGHT'): bpy.data.objects.remove(o_)
armA.animation_data_clear()
for a_ in list(bpy.data.actions): bpy.data.actions.remove(a_)
armA.name = 'Armature'; bpy.data.orphans_purge(do_recursive=True); bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=cfg['out_blend'])
print('saved scene')
