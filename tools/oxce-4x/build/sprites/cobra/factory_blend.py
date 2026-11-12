"""Character factory, stations 1/3/4/5 (Assemble, Arm, Animate, Render) - one Blender session for the whole roster.
Builds Ch49 body + Ch33 head on the shared Mixamo skeleton exactly like build_duke.py (the approved look),
then per character swaps in that character's painted textures and renders:
  inv/    front inventory figure (beauty + ID), arms down, hands empty, camera at chest height
  walk/   8 facings x rifle walk (beauty + ID), M-16 in both hands
Usage: python3 factory_blend.py --chars <dir> --ids duke,hawk,... [--only inv|walk] [--step 2] [--dirs 1,..8]

BUILD SESSION COPY (cobra_troopers_v3.zip / cobra_day1.zip scripts/factory_blend.py - the two are identical), patched
only for:
  --save-blend PATH   save ONE character (--ids <one>) empty-handed for render_char.py and exit, before the render loop:
                      that character's textures + garment-ID maps loaded into the materials and packed, drop_ids faces
                      deleted (Recruit's harness), hair mesh removed when meta drop_hair, helmet colour from meta,
                      no clip, no gun, no camera / lights
  paths               env GIJOE_REF (staged Reference), ANIM_IDS (Duke's base id maps), COBRA_HELMET_STL
Everything before the save (cut, swell + layer lock, clean collar, head swap, helmets, materials) is the zip's code.
"""
import bpy, bmesh, sys, os, math, json
from mathutils import Vector, Matrix
import numpy as np

def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
D = '/mnt/user-data/uploads/Downloads/'
REF = os.environ.get('GIJOE_REF', '/mnt/user-data/uploads/GIJoe_XCOM_4x/Reference/')
ANIM = os.environ.get('ANIM_IDS', REF + 'models/mixamo/painted/duke/anim/')
GUNP = REF + 'models/guns/grunt_M-16.glb'
SAVE = arg('--save-blend')
CLIP = arg('--clip', '/tmp/claude-0/ws/mix/packs/walk forward.fbx')
CH = arg('--chars'); IDS = arg('--ids').split(',')
ONLY = arg('--only', 'both'); STEP = int(arg('--step', 2))
DIRS = [int(x) for x in arg('--dirs', '1,2,3,4,5,6,7,8').split(',')]
CUT = 0.845

bpy.ops.wm.read_factory_settings(use_empty=True)
def imp(p, tag):
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new: o.name = tag + '|' + o.name
    return new
A = imp(D + 'Withdrawing Sword (2).fbx', 'B')
Hd = imp(D + 'Withdrawing Sword (7).fbx', 'H')
An = imp(CLIP, 'C') if not (SAVE or '--posmap' in sys.argv) else []
arm = [o for o in A if o.type == 'ARMATURE'][0]
arm_h = [o for o in Hd if o.type == 'ARMATURE'][0]
arm_c = [o for o in An if o.type == 'ARMATURE'][0] if An else None
clip = arm_c.animation_data.action if arm_c else None
if clip: clip.use_fake_user = True

def world_coords(o):
    M = o.matrix_world; return np.array([M @ v.co for v in o.data.vertices])
def bake_unparent(o):
    mw = o.matrix_world.copy(); o.parent = None; o.data.transform(mw); o.matrix_world = Matrix.Identity(4)
body_meshes = [o for o in A if o.type == 'MESH']
h49 = max(world_coords(o)[:, 2].max() for o in body_meshes)
allb = np.concatenate([world_coords(o) for o in body_meshes])
ring_b = allb[(allb[:, 2] > (CUT - 0.02) * h49) & (allb[:, 2] < CUT * h49)].mean(0)
def cut_faces(o, keep_fn):
    W = world_coords(o)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    kill = [f for f in bm.faces if not keep_fn(W[[v.index for v in f.verts]].mean(0))]
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(o.data); bm.free()
for o in body_meshes:
    if '--clean_collar' in sys.argv:
        # slice the body with a true plane (clean straight collar edge) instead of dropping whole polygons (jagged edge)
        M = o.matrix_world; Mi = M.inverted(); zc = CUT * h49 - float(arg('--collar_drop', 0.006))
        bm = bmesh.new(); bm.from_mesh(o.data)
        co_l = Mi @ Vector((0, 0, zc)); no_l = (Mi.to_3x3() @ Vector((0, 0, 1))).normalized()
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co_l, plane_no=no_l, clear_outer=True)
        bm.to_mesh(o.data); bm.free()
    else:
        cut_faces(o, lambda c: c[2] < CUT * h49)
    bake_unparent(o); o.modifiers[0].object = arm if o.modifiers else None
SWELL = float(arg('--swell', 0.0))
if SWELL > 0:
    # fuller build: push the body surface out along its normals (torso most, limbs a bit less; hands and boots untouched),
    # and widen the chest/shoulders a touch. Done on the rest mesh before skinning, so all animations still work.
    SW = {}
    for o in body_meshes:
        me = o.data; me.calc_normals_split() if hasattr(me, 'calc_normals_split') else None
        gi = {vg.index: vg.name for vg in o.vertex_groups}
        co = np.array([v.co[:] for v in me.vertices]); nr = np.array([v.normal[:] for v in me.vertices])
        w_hand = np.zeros(len(co)); w_torso = np.zeros(len(co))
        for v in me.vertices:
            for g in v.groups:
                n = gi[g.group]
                if 'Hand' in n: w_hand[v.index] += g.weight
                if any(k in n for k in ('Spine', 'Hips', 'Shoulder', 'Neck')): w_torso[v.index] += g.weight
        z = co[:, 2]
        boots = np.clip((0.40 - z) / 0.08, 0, 1)                    # fade out over the boot tops
        amt = SWELL * (0.75 + 0.35 * np.clip(w_torso, 0, 1)) * (1 - np.clip(w_hand, 0, 1)) * (1 - boots)
        if '--clean_collar' in sys.argv:
            # at the cut collar edge, push straight out (no vertical part): the open edge's normals are uneven and
            # pushed the collar up and down into a saw-tooth around the neck
            top = np.clip((z - (CUT * h49 - 0.05)) / 0.03, 0, 1)[:, None]
            flat = nr.copy(); flat[:, 2] = 0; flat /= np.maximum(np.linalg.norm(flat, axis=1, keepdims=True), 1e-6)
            nr = nr * (1 - top) + flat * top
        co = co + nr * amt[:, None]
        chest = np.clip((z - 1.05) / 0.15, 0, 1) * np.clip((1.52 - z) / 0.06, 0, 1) * np.clip(w_torso, 0, 1)
        co[:, 0] *= 1 + 0.045 * chest                               # broader chest/shoulders
        SW[o.name] = (np.array([v.co[:] for v in me.vertices]), co, nr)
    # layered gear (webbing, pouches) must move WITH the shirt under it, or the shirt pokes through it (saw-tooth edges):
    # every vertex of the smaller mesh lying on the main body copies the nearest body vertex's push, plus 2 mm on top
    from scipy.spatial import cKDTree
    def _sheet(o):
        for m in o.data.materials:
            if m and m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and n.image and '1002' in (n.image.name + n.image.filepath): return '1002'
        return ''
    main = ([o for o in body_meshes if _sheet(o) == '1002'] or [max(body_meshes, key=lambda o: len(o.data.vertices))])[0]   # the shirt/trouser layer
    print('swell base layer', main.name)
    m0, m1, _ = SW[main.name]; tree = cKDTree(m0)
    for o in body_meshes:
        c0, c1, nr = SW[o.name]
        if o is not main:
            dist, nn = tree.query(c0)
            on = dist < float(arg('--layer_dist', 0.03))
            c1 = c1.copy(); c1[on] = c0[on] + (m1[nn[on]] - m0[nn[on]]) + nr[on] * 0.002
            print('layer-locked', o.name, int(on.sum()), 'of', len(c0))
        o.data.vertices.foreach_set('co', c1.ravel()); o.data.update()
    print('swell', SWELL)
head_keep = []
hb = [o for o in Hd if o.type == 'MESH' and o.name.endswith('Ch33_Body')][0]
h33 = world_coords(hb)[:, 2].max(); W33 = world_coords(hb)
ring_h = W33[(W33[:, 2] > CUT * h33) & (W33[:, 2] < (CUT + 0.02) * h33)].mean(0)
s = h49 / h33; off = Vector(ring_b) - Vector(ring_h) * s
for o in [o for o in Hd if o.type == 'MESH']:
    nm = o.name.split('|')[1]
    if nm not in ('Ch33_Body', 'Ch33_Hair'):
        bpy.data.objects.remove(o); continue
    if nm == 'Ch33_Body':
        if '--clean_collar' in sys.argv:
            # clean plane cut for the neck bottom too (no zig-zag ink where the neck meets the collar)
            M = o.matrix_world; Mi = M.inverted(); zc = CUT * h33 - 0.012 * h33
            bm = bmesh.new(); bm.from_mesh(o.data)
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Mi @ Vector((0, 0, zc)),
                                   plane_no=(Mi.to_3x3() @ Vector((0, 0, 1))).normalized(), clear_inner=True)
            bm.to_mesh(o.data); bm.free()
            cut_faces(o, lambda c: abs(c[0]) < 0.075 * h33)
        else:
            cut_faces(o, lambda c: c[2] >= CUT * h33 and abs(c[0]) < 0.075 * h33)
    bake_unparent(o)
    o.data.transform(Matrix.Translation(off) @ Matrix.Scale(s, 4))
    if '--clean_collar' in sys.argv and nm == 'Ch33_Body':
        # tuck the neck bottom inside the collar so the two surfaces don't fight (saw-tooth line where neck meets collar)
        Wn = world_coords(o); zb = CUT * h49 - float(arg('--collar_drop', 0.006)); band = float(arg('--tuck_band', 0.035))
        nk = (Wn[:, 2] < zb + band) & (np.abs(Wn[:, 0]) < 0.09)
        if nk.any():
            ax = Wn[nk][:, :2].mean(0); Mi = o.matrix_world.inverted(); tk = float(arg('--tuck', 0.12))
            for i in np.nonzero(nk)[0]:
                f = 1 - tk * min(1.0, (zb + band - Wn[i, 2]) / band)
                p = Wn[i].copy(); p[:2] = ax + (p[:2] - ax) * f
                o.data.vertices[i].co = Mi @ Vector(p)
    for vg in o.vertex_groups: vg.name = vg.name.replace('mixamorig7:', 'mixamorig:')
    mod = [m for m in o.modifiers if m.type == 'ARMATURE'][0]; mod.object = arm
    head_keep.append(o)
hair_obj = [o for o in head_keep if o.name.endswith('Ch33_Hair')][0]
helmet = None
if '--helmet' in sys.argv:
    # 28mm Cobra-trooper helmet shell over Duke's head (mini face box mapped onto the Ch33 head box), bound to Head
    face_o = [o for o in head_keep if o.name.endswith('Ch33_Body')][0]
    HCo = world_coords(face_o); hlo, hhi = HCo.min(0), HCo.max(0)
    bpy.ops.wm.stl_import(filepath=os.environ.get('COBRA_HELMET_STL', '/tmp/claude-0/ws/cobra_v3src/tro/cobra_troopers_v3/helmet/cobra_head_28mm.stl'))
    ho = bpy.context.selected_objects[0]; bpy.context.view_layer.objects.active = ho
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    parts = sorted([o for o in bpy.data.objects if o.type == 'MESH' and o not in body_meshes and o not in head_keep], key=lambda p: -len(p.data.vertices))
    helmet, mface = parts[0], parts[1]
    H0 = np.array([v.co[:] for v in helmet.data.vertices]); cx, cy = (H0[:, 0].min() + H0[:, 0].max()) / 2, (H0[:, 1].min() + H0[:, 1].max()) / 2
    for p in (helmet, mface): p.data.transform(Matrix.Rotation(math.radians(-13.4), 4, 'Z') @ Matrix.Translation((-cx, -cy, 0)))
    F = np.array([v.co[:] for v in mface.data.vertices]); flo, fhi = F.min(0), F.max(0)
    for p in parts[1:]: bpy.data.objects.remove(p)
    S = (hhi - hlo) / (fhi - flo) * 1.03; S[2] = (hhi[2] - hlo[2]) / (fhi[2] - flo[2]); fc = (flo + fhi) / 2; hc = (hlo + hhi) / 2
    zz = HCo[:, 2]; band = HCo[(zz > hlo[2] + 0.35 * (hhi[2] - hlo[2])) & (zz < hlo[2] + 0.6 * (hhi[2] - hlo[2]))]
    nose_x = float(band[np.argmin(band[:, 1]), 0]); hc[0] = nose_x                                 # centre the helmet on the face's nose line
    fc[0] = float((F[F[:, 2] < flo[2] + 0.6 * (fhi[2] - flo[2])])[np.argmin(F[F[:, 2] < flo[2] + 0.6 * (fhi[2] - flo[2])][:, 1]), 0])   # and the mini's nose line
    print('helmet centred on nose x', round(nose_x, 4))
    helmet.data.transform(Matrix.Translation(Vector(hc)) @ Matrix.Diagonal((S[0], S[1], S[2], 1)) @ Matrix.Translation(Vector(-fc)))
    HW = np.array([v.co[:] for v in helmet.data.vertices])
    zb = HW[(HW[:, 1] < hc[1] - 0.05) & (np.abs(HW[:, 0] - hc[0]) < 0.03), 2].min(); SH = float(arg('--helmet_scale', 0.90))
    helmet.data.transform(Matrix.Translation((hc[0], hc[1], zb)) @ Matrix.Diagonal((max(SH, 0.96), max(SH, 0.96), SH, 1)) @ Matrix.Translation((-hc[0], -hc[1], -zb)))
    for poly in helmet.data.polygons: poly.use_smooth = True
    HELMET_BADGE = '--helmet_badge' in sys.argv
    if HELMET_BADGE:   # small silver badge on the helmet front (Crimson Guard): faces on the front-centre above the brow lip
        HW2 = np.array([v.co[:] for v in helmet.data.vertices]); hb_lo, hb_hi = HW2.min(0), HW2.max(0)
        bm_m = bpy.data.materials.new('helmet_badge')
        badge_faces = []
        for poly in helmet.data.polygons:
            c = np.array(poly.center[:]); n = poly.normal
            if n.y < -0.5 and abs(c[0] - (hb_lo[0] + hb_hi[0]) / 2) < 0.016 and c[2] > zb + 0.035 and c[2] < zb + 0.085: badge_faces.append(poly.index)
    vg = helmet.vertex_groups.new(name='mixamorig:Head'); vg.add(list(range(len(helmet.data.vertices))), 1.0, 'REPLACE')
    md = helmet.modifiers.new('arm', 'ARMATURE'); md.object = arm
for o in (arm_h, arm_c):
    if o is not None: bpy.data.objects.remove(o)

if '--posmap' in sys.argv:
    # texel -> rest-pose position + normal, per texture sheet (for painting decals by body position)
    R = 1024; OUTP = arg('--posmap')
    def sheet_of(m):
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED' and n.inputs['Base Color'].links:
                p = n.inputs['Base Color'].links[0].from_node.image.filepath
                for k in ('Ch49_1001', 'Ch49_1002', 'Ch33_1001', 'Ch33_1002'):
                    if k in p: return k
    maps = {}
    for o in body_meshes + head_keep:
        me = o.data; me.calc_loop_triangles()
        uv = np.array([d.uv[:] for d in me.uv_layers.active.data]); co = np.array([v.co[:] for v in me.vertices])
        for t in me.loop_triangles:
            sh = sheet_of(me.materials[t.material_index])
            if sh is None: continue
            P, N = maps.setdefault(sh, (np.full((R, R, 3), np.nan, np.float32), np.zeros((R, R, 3), np.float32)))
            L = list(t.loops); V = list(t.vertices)
            u = uv[L] % 1.0 * R; u[:, 1] = R - u[:, 1]; p = co[V]
            x0, y0 = np.floor(u.min(0)).astype(int); x1, y1 = np.ceil(u.max(0)).astype(int)
            xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, R)), np.arange(max(y0, 0), min(y1 + 1, R)))
            q = np.stack([xs.ravel() + .5, ys.ravel() + .5], 1)
            a, b, c = u; den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-9: continue
            l1 = ((b[1] - c[1]) * (q[:, 0] - c[0]) + (c[0] - b[0]) * (q[:, 1] - c[1])) / den
            l2 = ((c[1] - a[1]) * (q[:, 0] - c[0]) + (a[0] - c[0]) * (q[:, 1] - c[1])) / den
            l3 = 1 - l1 - l2; ok = (l1 >= -.02) & (l2 >= -.02) & (l3 >= -.02)
            if not ok.any(): continue
            pos = l1[ok, None] * p[0] + l2[ok, None] * p[1] + l3[ok, None] * p[2]
            P[ys.ravel()[ok], xs.ravel()[ok]] = pos; N[ys.ravel()[ok], xs.ravel()[ok]] = t.normal[:]
    os.makedirs(OUTP, exist_ok=True)
    for k, (P, N) in maps.items(): np.save(f'{OUTP}/pos_{k}.npy', P); np.save(f'{OUTP}/nrm_{k}.npy', N)
    json.dump({'h49': float(h49)}, open(f'{OUTP}/meta.json', 'w')); print('POSMAP DONE', list(maps)); sys.exit(0)

# hips drift removal on the clip
def fcurves(act):
    if hasattr(act, 'fcurves') and len(act.fcurves): return list(act.fcurves)
    out = []
    for L in act.layers:
        for st in L.strips:
            for cb in st.channelbags: out += list(cb.fcurves)
    return out
for fc in ([] if clip is None else [fc for fc in fcurves(clip) if fc.data_path == 'pose.bones["mixamorig:Hips"].location']):
    xs = np.array([k.co[0] for k in fc.keyframe_points]); ys = np.array([k.co[1] for k in fc.keyframe_points])
    a, b = np.polyfit(xs, ys, 1)
    if abs(a) * (xs.max() - xs.min()) > 30:
        for k in fc.keyframe_points:
            k.co[1] -= a * k.co[0] + b - (a * xs[0] + b); k.handle_left[1] = k.co[1]; k.handle_right[1] = k.co[1]
fs, fe = [int(x) for x in clip.frame_range] if clip else (1, 2)

# ---- materials: emission from swappable images + part-ID pass ----
IMG = {k: bpy.data.images.new('slot_' + k, 8, 8, alpha=True) for k in ('Ch49_1001', 'Ch49_1002', 'face', 'hair')}
idimg = {k: bpy.data.images.load(f'{ANIM}id_{k}_Diffuse.png') for k in ('Ch49_1001', 'Ch49_1002')}
for im in idimg.values(): im.colorspace_settings.name = 'Non-Color'
def slot_for(path):
    for k in ('Ch49_1001', 'Ch49_1002'):
        if k in path: return k
    if 'Ch33_1002' in path: return 'hair'
    if 'Ch33_1001' in path: return 'face'
def rebuild_material(m):
    nt = m.node_tree; slot = None; alpha_img = None
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            for inp in ('Base Color', 'Alpha'):
                if n.inputs[inp].links:
                    im = n.inputs[inp].links[0].from_node.image
                    if inp == 'Base Color': slot = slot_for(im.filepath)
                    else: alpha_img = im
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = IMG[slot] if slot else None
    t.interpolation = 'Closest' if slot == 'hair' else 'Linear'
    emB = nt.nodes.new('ShaderNodeEmission'); nt.links.new(t.outputs['Color'], emB.inputs['Color'])
    comb = nt.nodes.new('ShaderNodeCombineColor')
    if slot in idimg:
        it = nt.nodes.new('ShaderNodeTexImage'); it.image = idimg[slot]; it.interpolation = 'Closest'
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(it.outputs['Color'], sep.inputs[0])
        nt.links.new(sep.outputs[0], comb.inputs[0])
    else:
        comb.inputs[0].default_value = (1 if slot == 'hair' else 2) / 40.0
    camd = nt.nodes.new('ShaderNodeCameraData')
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
    nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
    emI = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], emI.inputs['Color'])
    sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'; sw.inputs[0].default_value = 0.0
    nt.links.new(emB.outputs[0], sw.inputs[1]); nt.links.new(emI.outputs[0], sw.inputs[2])
    final = sw.outputs[0]
    if alpha_img is not None:
        ta = nt.nodes.new('ShaderNodeTexImage'); ta.image = alpha_img
        gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5
        nt.links.new(ta.outputs['Alpha'], gt.inputs[0])
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(gt.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(final, mx.inputs[2])
        final = mx.outputs[0]
    nt.links.new(final, out.inputs['Surface'])
done = set()
for o in body_meshes + head_keep:
    for m in o.data.materials:
        if m and m.name not in done: rebuild_material(m); done.add(m.name)
def cel_material(name, rgb, idv):
    """flat colour + one cel shadow tone from a fixed key light, with the ID-pass switch (for untextured add-ons)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    g = nt.nodes.new('ShaderNodeNewGeometry'); dp = nt.nodes.new('ShaderNodeVectorMath'); dp.operation = 'DOT_PRODUCT'
    dp.inputs[1].default_value = Vector((-0.45, -0.55, 0.70)).normalized(); nt.links.new(g.outputs['Normal'], dp.inputs[0])
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = -0.05; nt.links.new(dp.outputs['Value'], gt.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.name = 'CEL'; nt.links.new(gt.outputs[0], mix.inputs['Factor'])
    lin = [((c / 255) ** 2.2) for c in rgb]
    mix.inputs['B'].default_value = lin + [1]; mix.inputs['A'].default_value = [x * 0.66 ** 2.2 for x in lin] + [1]
    eb = nt.nodes.new('ShaderNodeEmission'); nt.links.new(mix.outputs['Result'], eb.inputs['Color'])
    comb = nt.nodes.new('ShaderNodeCombineColor'); comb.inputs[0].default_value = idv / 40.0
    camd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
    nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
    ei = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], ei.inputs['Color'])
    sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'; o_ = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(eb.outputs[0], sw.inputs[1]); nt.links.new(ei.outputs[0], sw.inputs[2]); nt.links.new(sw.outputs[0], o_.inputs['Surface'])
    return m

if '--cg_helmet' in sys.argv:
    # Crimson Guard helmet, built from simple shapes: a round dome over Duke's head whose front IS a smooth black faceplate,
    # a silver eye slit across the faceplate, and a raised silver ridge from the forehead over the crown.
    face_o = [o for o in head_keep if o.name.endswith('Ch33_Body')][0]
    HCo = world_coords(face_o); hlo, hhi = HCo.min(0), HCo.max(0)
    zz = HCo[:, 2]; band = HCo[(zz > hlo[2] + 0.35 * (hhi[2] - hlo[2])) & (zz < hlo[2] + 0.6 * (hhi[2] - hlo[2]))]
    nose = band[np.argmin(band[:, 1])]; nx = float(nose[0])
    eye = HCo[(zz > 1.62) & (zz < 1.68)]
    half_w = max(nx - eye[:, 0].min(), eye[:, 0].max() - nx)
    cy = (eye[:, 1].min() + eye[:, 1].max()) / 2; ry0 = (eye[:, 1].max() - eye[:, 1].min()) / 2
    top = hhi[2]; cz = 1.640
    GROW = float(arg('--cg_grow', 0.010))                       # how far the shell stands off the head
    rx, ry, rz = half_w + GROW, ry0 + GROW + 0.006, (top + GROW + 0.004) - cz
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=192, v_segments=128, radius=1.0)
    for v in bm.verts:
        # fitted, upright shell: superellipse in x/y (flatter sides, not a ball), plain ellipse vertically
        x, y, z = v.co.x, v.co.y, v.co.z
        r = max(np.hypot(x, y), 1e-6); k = 0.80
        sx = np.sign(x) * abs(x / r) ** k * r; sy = np.sign(y) * abs(y / r) ** k * r
        fwd = max(0.0, -sy - 0.35) / 0.65 * max(0.0, 1 - abs(z) / 0.9)          # bulge only the front, around face height
        v.co = Vector((nx + sx * rx, cy + sy * ry - 0.020 * fwd ** 1.5, cz + z * rz))
    BROW = float(arg('--cg_brow', 1.684)); SLIT_Z = float(arg('--cg_slit', 1.640)); CHIN = 1.548
    def plate_halfw(z):      # shield-shaped faceplate: full width at the brow, narrowing to a rounded point at the chin
        f = np.clip((z - CHIN) / (BROW - CHIN), 0, 1)
        return 0.020 + 0.058 * np.sqrt(f)
    def in_plate(c, n):   # arched top edge, shield sides
        top_z = BROW - 0.016 * ((c.x - nx) / 0.078) ** 2
        return n.y < -0.25 and CHIN - 0.004 < c.z < top_z and abs(c.x - nx) < plate_halfw(c.z)
    # open the bottom: back and sides come down to the jaw; under the shield point it's open for the neck
    kill = [f for f in bm.faces if f.calc_center_median().z < 1.512 or (f.calc_center_median().z < CHIN and f.normal.y < -0.15 and abs(f.calc_center_median().x - nx) < 0.07)]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.normal_update(); bm.faces.ensure_lookup_table()
    for f in bm.faces:
        c = f.calc_center_median(); n = f.normal; f.material_index = 0
        if in_plate(c, n): f.material_index = 1                                                            # faceplate
        if f.material_index == 1 and abs(c.z - SLIT_Z) < 0.0055 and abs(c.x - nx) < 0.045: f.material_index = 2   # eye slit
    # silver crest badge: short and wide, stepped, on the forehead just above the faceplate
    crest = [f for f in bm.faces if f.material_index == 0 and f.normal.y < -0.35
             and BROW + 0.006 < f.calc_center_median().z < BROW + 0.050
             and abs(f.calc_center_median().x - nx) < (0.024 - 0.10 * (f.calc_center_median().z - BROW - 0.006))]
    ex = bmesh.ops.extrude_face_region(bm, geom=crest)
    for v in [g for g in ex['geom'] if isinstance(g, bmesh.types.BMVert)]: v.co += v.normal * 0.006
    for f in [g for g in ex['geom'] if isinstance(g, bmesh.types.BMFace)]: f.material_index = 3
    for f in crest: f.material_index = 3
    me_ = bpy.data.meshes.new('cg_helmet'); bm.to_mesh(me_); bm.free()
    cgh = bpy.data.objects.new('cg_helmet', me_); bpy.context.collection.objects.link(cgh)
    for poly in me_.polygons: poly.use_smooth = True
    for col, idv in (((176, 26, 32), 5), ((18, 18, 22), 6), ((205, 207, 214), 3), ((205, 207, 214), 4)):
        me_.materials.append(cel_material(f'cg_{idv}', col, idv))
    vg = cgh.vertex_groups.new(name='mixamorig:Head'); vg.add(list(range(len(me_.vertices))), 1.0, 'REPLACE')
    md = cgh.modifiers.new('arm', 'ARMATURE'); md.object = arm
    print('CG helmet', len(me_.polygons), 'faces; nose x', round(nx, 4), 'radii', round(rx, 3), round(ry, 3), round(rz, 3))
if '--hull_helmet' in sys.argv:
    # Crimson Guard helmet built from the toy photos (cg_helmet_hull.py -> npz, normalised: z 0 chin .. 1 crown)
    d_ = np.load(arg('--hull_helmet')); hv, hf, hm = d_['v'].astype(np.float64), d_['f'], d_['mat']
    face_o = [o for o in head_keep if o.name.endswith('Ch33_Body')][0]
    HCo = world_coords(face_o); hlo, hhi = HCo.min(0), HCo.max(0); zz = HCo[:, 2]
    band = HCo[(zz > hlo[2] + 0.35 * (hhi[2] - hlo[2])) & (zz < hlo[2] + 0.6 * (hhi[2] - hlo[2]))]
    nx = float(band[np.argmin(band[:, 1]), 0])
    CHIN = float(arg('--hull_chin', 1.540)); CROWN = float(hhi[2]) + float(arg('--hull_top', 0.016))
    S = (CROWN - CHIN) * float(arg('--hull_scale', 1.0))
    eye = HCo[(zz > 1.60) & (zz < 1.70)]; ymid = (eye[:, 1].min() + eye[:, 1].max()) / 2
    hmid = (hv[:, 1].min() + hv[:, 1].max()) / 2
    pos = np.stack([nx + hv[:, 0] * S, ymid + (hv[:, 1] - hmid) * S + float(arg('--hull_dy', 0.0)), CHIN + hv[:, 2] * (CROWN - CHIN)], 1)
    me_ = bpy.data.meshes.new('hull_helmet'); me_.from_pydata(pos.tolist(), [], hf.tolist()); me_.update()
    hh = bpy.data.objects.new('hull_helmet', me_); bpy.context.collection.objects.link(hh)
    for col, idv in (((176, 26, 32), 5), ((18, 18, 22), 6), ((205, 207, 214), 3), ((205, 207, 214), 4)):
        mm = cel_material(f'hull_{idv}', col, idv); me_.materials.append(mm)
        [n for n in mm.node_tree.nodes if n.type == 'MATH'][0].inputs[1].default_value = -0.35   # smaller, softer-placed shadow side
    me_.polygons.foreach_set('material_index', hm.tolist()); me_.update()
    for poly in me_.polygons: poly.use_smooth = True
    vg = hh.vertex_groups.new(name='mixamorig:Head'); vg.add(list(range(len(me_.vertices))), 1.0, 'REPLACE')
    md = hh.modifiers.new('arm', 'ARMATURE'); md.object = arm
    # how much of Duke's head pokes out of the shell (checked against the shell's own slices)
    print('hull helmet: chin', CHIN, 'crown', round(CROWN, 3), 'size', round(S, 3), 'nose x', round(nx, 4))
HELMET_MAT = None
if helmet is not None:
    HELMET_MAT = bpy.data.materials.new('helmet'); HELMET_MAT.use_nodes = True; nt = HELMET_MAT.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    g = nt.nodes.new('ShaderNodeNewGeometry'); dp = nt.nodes.new('ShaderNodeVectorMath'); dp.operation = 'DOT_PRODUCT'
    dp.inputs[1].default_value = Vector((-0.45, -0.55, 0.70)).normalized(); nt.links.new(g.outputs['Normal'], dp.inputs[0])
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = -0.05; nt.links.new(dp.outputs['Value'], gt.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.name = 'CEL'; nt.links.new(gt.outputs[0], mix.inputs['Factor'])
    eb = nt.nodes.new('ShaderNodeEmission'); nt.links.new(mix.outputs['Result'], eb.inputs['Color'])
    comb = nt.nodes.new('ShaderNodeCombineColor'); comb.inputs[0].default_value = 5 / 40.0
    camd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
    nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
    ei = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], ei.inputs['Color'])
    sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'; o_ = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(eb.outputs[0], sw.inputs[1]); nt.links.new(ei.outputs[0], sw.inputs[2]); nt.links.new(sw.outputs[0], o_.inputs['Surface'])
    helmet.data.materials.clear(); helmet.data.materials.append(HELMET_MAT)
    if '--helmet_badge' in sys.argv and badge_faces:
        BADGE = HELMET_MAT.copy(); BADGE.name = 'helmet_badge_mat'; helmet.data.materials.append(BADGE)
        cel = BADGE.node_tree.nodes['CEL']; lin = [((c / 255) ** 2.2) for c in (205, 207, 214)]
        cel.inputs['B'].default_value = lin + [1]; cel.inputs['A'].default_value = [x * 0.66 ** 2.2 for x in lin] + [1]
        BADGE.node_tree.nodes['Combine Color'].inputs[0].default_value = 3 / 40.0 if 'Combine Color' in BADGE.node_tree.nodes else 3 / 40.0
        for i in badge_faces: helmet.data.polygons[i].material_index = 1
        print('helmet badge faces', len(badge_faces))
def id_mode(on):
    for m in bpy.data.materials:
        if m.node_tree and 'IDSWITCH' in m.node_tree.nodes: m.node_tree.nodes['IDSWITCH'].inputs[0].default_value = 1.0 if on else 0.0

def _alive(o):
    try: o.name; return True
    except ReferenceError: return False
if SAVE:
    cid = IDS[0]; d = os.path.join(CH, cid); meta = json.load(open(f'{d}/meta.json'))
    for k, f in (('Ch49_1001', 'Ch49_1001.png'), ('Ch49_1002', 'Ch49_1002.png'), ('face', 'face.png'), ('hair', 'hair.png')):
        im = bpy.data.images.load(f'{d}/{f}'); im.name = f'{cid}_{f}'
        for m in bpy.data.materials:
            if m.node_tree:
                for n in m.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and n.image is IMG[k]: n.image = im
    for k in idimg:
        p = f'{d}/id_{k}_Diffuse.png'
        if os.path.exists(p): idimg[k].filepath = p; idimg[k].reload()
        else: print('WARNING no per-character id map', p, '- Duke base map kept')
    drop = meta.get('drop_ids', [])
    if drop:                     # as _apply_drop(), but the faces are deleted instead of masked at render time
        from PIL import Image as _PI
        def _slot(m):
            for n in (m.node_tree.nodes if m and m.node_tree else []):
                if n.type == 'TEX_IMAGE' and n.image is not None:
                    for k_ in ('Ch49_1001', 'Ch49_1002'):
                        if n.image.name == f'{cid}_{k_}.png': return k_
        for o in body_meshes:
            me = o.data; uvl = me.uv_layers.active.data
            cen = np.array([np.mean([uvl[li].uv[:] for li in p_.loop_indices], 0) for p_ in me.polygons])
            sh = [_slot(me.materials[p_.material_index]) for p_ in me.polygons]; kill = np.zeros(len(cen), bool)
            for slot in ('Ch49_1001', 'Ch49_1002'):
                p_ = f'{d}/id_{slot}_Diffuse.png'
                if not os.path.exists(p_): continue
                ids = np.asarray(_PI.open(p_)); ids = ids[..., 0] if ids.ndim == 3 else ids; H, W = ids.shape
                msk = np.array([s_ == slot for s_ in sh])
                if not msk.any(): continue
                px = ((cen[msk, 0] % 1) * W).astype(int).clip(0, W - 1); py = ((1 - cen[msk, 1] % 1) * H).astype(int).clip(0, H - 1)
                kill[np.nonzero(msk)[0]] = np.isin(ids[py, px], drop)
            bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.nonzero(kill)[0]], context='FACES'); bm.to_mesh(me); bm.free()
            print('drop', o.name, int(kill.sum()), 'faces deleted (ids', drop, ')')
    if meta.get('drop_hair') and _alive(hair_obj): bpy.data.objects.remove(hair_obj)
    if HELMET_MAT is not None and 'helmet' in meta:
        lin = [((c / 255) ** 2.2) for c in meta['helmet']]; cel = HELMET_MAT.node_tree.nodes['CEL']
        cel.inputs['B'].default_value = lin + [1]; cel.inputs['A'].default_value = [x * 0.66 ** 2.2 for x in lin] + [1]
    hh_ = bpy.data.objects.get('hull_helmet')
    if hh_ is not None:
        # render_char.py allows 6 material slots in all (3 + 6 per slot <= 40); the hull's 4 cel materials make 7. Fold
        # them into ONE with the same look: colour + garment id per face as attributes, same key light, same -0.35 cut.
        me_ = hh_.data; HC = [(176, 26, 32), (18, 18, 22), (205, 207, 214), (205, 207, 214)]; HI = [5, 6, 3, 4]
        ac = me_.color_attributes.new('hcol', 'FLOAT_COLOR', 'CORNER'); ai = me_.color_attributes.new('hid', 'FLOAT_COLOR', 'CORNER')
        for poly in me_.polygons:
            c = [(x / 255) ** 2.2 for x in HC[poly.material_index]] + [1.0]; iv = (HI[poly.material_index] / 40.0, 0, 0, 1)
            for li in poly.loop_indices: ac.data[li].color = c; ai.data[li].color = iv
        m = bpy.data.materials.new('hull_helmet'); m.use_nodes = True; nt = m.node_tree
        for n in list(nt.nodes): nt.nodes.remove(n)
        g = nt.nodes.new('ShaderNodeNewGeometry'); dp = nt.nodes.new('ShaderNodeVectorMath'); dp.operation = 'DOT_PRODUCT'
        dp.inputs[1].default_value = Vector((-0.45, -0.55, 0.70)).normalized(); nt.links.new(g.outputs['Normal'], dp.inputs[0])
        gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = -0.35; nt.links.new(dp.outputs['Value'], gt.inputs[0])
        atc = nt.nodes.new('ShaderNodeAttribute'); atc.attribute_name = 'hcol'
        dk = nt.nodes.new('ShaderNodeVectorMath'); dk.operation = 'SCALE'; dk.inputs['Scale'].default_value = 0.66 ** 2.2
        nt.links.new(atc.outputs['Color'], dk.inputs[0])
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.name = 'CEL'; nt.links.new(gt.outputs[0], mix.inputs['Factor'])
        nt.links.new(dk.outputs['Vector'], mix.inputs['A']); nt.links.new(atc.outputs['Color'], mix.inputs['B'])
        eb = nt.nodes.new('ShaderNodeEmission'); nt.links.new(mix.outputs['Result'], eb.inputs['Color'])
        ati = nt.nodes.new('ShaderNodeAttribute'); ati.attribute_name = 'hid'
        sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(ati.outputs['Color'], sp.inputs[0])
        comb = nt.nodes.new('ShaderNodeCombineColor'); nt.links.new(sp.outputs[0], comb.inputs[0])
        camd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
        nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
        ei = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], ei.inputs['Color'])
        sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'; sw.inputs[0].default_value = 0.0; o_ = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(eb.outputs[0], sw.inputs[1]); nt.links.new(ei.outputs[0], sw.inputs[2]); nt.links.new(sw.outputs[0], o_.inputs['Surface'])
        me_.materials.clear(); me_.materials.append(m)
        me_.polygons.foreach_set('material_index', [0] * len(me_.polygons)); me_.update()
        print('hull helmet: 4 cel materials folded into one (per-face colour + id attributes)')
    for o in list(bpy.data.objects):
        if o.type in ('CAMERA', 'LIGHT', 'EMPTY'): bpy.data.objects.remove(o)
    for o in [o for o in bpy.data.objects if o.type == 'MESH']:          # drop material slots no face uses
        used = {p_.material_index for p_ in o.data.polygons}
        for i in reversed(range(len(o.data.materials))):
            if i not in used:
                for p_ in o.data.polygons:
                    if p_.material_index > i: p_.material_index -= 1
                o.data.materials.pop(index=i)
    arm.animation_data_clear()
    for a_ in list(bpy.data.actions): bpy.data.actions.remove(a_)
    arm.name = 'Armature'; bpy.data.orphans_purge(do_recursive=True); bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=SAVE); print('SAVED', SAVE); sys.exit(0)

# ---- gun ----
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GUNP)
gun = [o for o in bpy.data.objects if o not in before and o.type == 'MESH'][0]
for o in [o for o in bpy.data.objects if o not in before and o is not gun]: o.hide_render = True
gun.parent = None; gun.data.transform(gun.matrix_world); gun.matrix_world = Matrix.Identity(4)
gm = bpy.data.materials.new('gun_flat'); gm.use_nodes = True; nt = gm.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
o_ = nt.nodes.new('ShaderNodeOutputMaterial')
eb = nt.nodes.new('ShaderNodeEmission'); eb.inputs['Color'].default_value = (0.045, 0.048, 0.055, 1)
comb = nt.nodes.new('ShaderNodeCombineColor'); comb.inputs[0].default_value = 30 / 40.0
camd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange')
mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
ei = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], ei.inputs['Color'])
sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'
nt.links.new(eb.outputs[0], sw.inputs[1]); nt.links.new(ei.outputs[0], sw.inputs[2]); nt.links.new(sw.outputs[0], o_.inputs['Surface'])
gun.data.materials.clear(); gun.data.materials.append(gm)
G_LOCAL = Vector((-0.317, 0.0, -0.065)); F_LOCAL = Vector((0.07, 0.0, 0.040))
HAND_IDX = {}
for o in body_meshes:
    gi = {vg.index: vg.name for vg in o.vertex_groups}
    for side in ('Left', 'Right'):
        idx = [v.index for v in o.data.vertices
               if sum(g.weight for g in v.groups if gi[g.group].startswith(f'mixamorig:{side}Hand')) > 0.6]
        if idx: HAND_IDX.setdefault(side, []).append((o, np.array(idx)))
def place_gun():
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    def hand(side):
        pts = []
        for o, idx in HAND_IDX[side]:
            me = o.evaluated_get(dg).to_mesh()
            co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co)
            pts.append(co.reshape(-1, 3)[idx]); o.evaluated_get(dg).to_mesh_clear()
        return Vector(np.concatenate(pts).mean(0))
    rh, lh = hand('Right'), hand('Left')
    dl = F_LOCAL - G_LOCAL; tilt = math.atan2(dl.z, dl.x)
    d = (lh - rh).normalized(); upw = Vector((0, 0, 1)); up = (upw - d * upw.dot(d)).normalized(); y = up.cross(d)
    R = Matrix((d, y, up)).transposed() @ Matrix.Rotation(tilt, 3, 'Y')
    gun.matrix_world = Matrix.Translation(rh - R @ G_LOCAL) @ R.to_4x4()

# ---- render setup ----
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.render.resolution_percentage = 100
sc.render.film_transparent = True; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'; sc.cycles.use_denoising = False
sc.cycles.max_bounces = 1; sc.cycles.transparent_max_bounces = 16
sc.world = bpy.data.worlds.new('w')
tgt = bpy.data.objects.new('tgt', None); bpy.context.collection.objects.link(tgt)
cam_d = bpy.data.cameras.new('cam'); cam_d.type = 'ORTHO'
cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
FACING = {1: (0, 1), 2: (.707, .707), 3: (1, 0), 4: (.707, -.707), 5: (0, -1), 6: (-.707, -.707), 7: (-1, 0), 8: (-.707, .707)}
def place_camera(k, el):
    fx, fy = FACING[k]; phi = math.atan2(fy, fx) + math.pi / 2
    a = Vector((math.sin(phi), math.cos(phi), 0))
    cam.location = tgt.location - a * 10 * math.cos(el) + Vector((0, 0, 10 * math.sin(el)))
SHADE = '--shade' in sys.argv
if SHADE:
    # geometry-shading pass for pen work: plain white diffuse under a fixed key light (the sculpted cloth folds)
    SHADE_MAT = bpy.data.materials.new('shade_override'); SHADE_MAT.use_nodes = True
    _b = SHADE_MAT.node_tree.nodes['Principled BSDF']; _b.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1); _b.inputs['Roughness'].default_value = 1.0
    _sun = bpy.data.objects.new('key', bpy.data.lights.new('key', 'SUN')); _sun.data.energy = 3.0; _sun.data.angle = 0.05
    bpy.context.collection.objects.link(_sun); _sun.hide_render = True
def shoot(path):
    id_mode(False); sc.cycles.samples = 8; sc.cycles.filter_width = 1.0; sc.view_settings.view_transform = 'Standard'
    sc.render.filepath = path + '_beauty.png'; bpy.ops.render.render(write_still=True)
    id_mode(True); sc.cycles.samples = 1; sc.cycles.filter_width = 0.01; sc.view_settings.view_transform = 'Raw'
    sc.render.filepath = path + '_id.png'; bpy.ops.render.render(write_still=True)
    if SHADE:
        # key light from upper-left-front of the CAMERA, so fold shadows read the same in every facing
        fwd = (tgt.location - cam.location).normalized(); right = fwd.cross(Vector((0, 0, 1))).normalized(); upv = right.cross(fwd)
        ldir = (fwd * 0.55 - right * 0.55 + upv * 0.62).normalized()
        _sun.rotation_euler = ldir.to_track_quat('-Z', 'Y').to_euler(); _sun.hide_render = False
        bpy.context.view_layer.material_override = SHADE_MAT; sc.world.color = (0.05, 0.05, 0.05)
        sc.cycles.samples = 16; sc.cycles.filter_width = 1.0; sc.view_settings.view_transform = 'Standard'
        sc.render.filepath = path + '_shade.png'; bpy.ops.render.render(write_still=True)
        bpy.context.view_layer.material_override = None; _sun.hide_render = True

def rest_pose_arms_down():
    arm.animation_data_clear()
    for pb in arm.pose.bones: pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    for side, ang in (('Left', 72), ('Right', -72)):
        pb = arm.pose.bones[f'mixamorig:{side}Arm']
        W = arm.matrix_world @ pb.matrix; piv = W.to_translation()
        R = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(ang), 4, 'Y') @ Matrix.Translation(-piv)
        pb.matrix = arm.matrix_world.inverted() @ R @ W
        bpy.context.view_layer.update()
    for side, ang in (('Left', 8), ('Right', -8)):           # slight elbow bend, hands relaxed
        pb = arm.pose.bones[f'mixamorig:{side}ForeArm']
        W = arm.matrix_world @ pb.matrix; piv = W.to_translation()
        R = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(ang), 4, 'X') @ Matrix.Translation(-piv)
        pb.matrix = arm.matrix_world.inverted() @ R @ W
        bpy.context.view_layer.update()
def walk_pose():
    arm.animation_data_clear(); arm.animation_data_create(); arm.animation_data.action = clip
    if hasattr(arm.animation_data, 'action_slot') and clip.slots: arm.animation_data.action_slot = clip.slots[0]

_FACEUV = {}
def _mat_slot(m):
    for n in (m.node_tree.nodes if m and m.use_nodes else []):
        if n.type == 'TEX_IMAGE' and n.image is not None:
            for k, im in IMG.items():
                if n.image == im: return k
    return None
def _apply_drop(drop, d):
    """hide (Mask modifier) every body face whose garment ID (per-character ID map, at the face's UV centre) is in
    drop - e.g. the webbing harness on a character who doesn't wear one. Works for beauty, ID and shade passes."""
    from PIL import Image as _PI
    for o in body_meshes:
        md = o.modifiers.get('DROP')
        if not drop:
            if md: md.show_render = md.show_viewport = False
            continue
        if o.name not in _FACEUV:
            me = o.data; uvl = me.uv_layers.active.data
            cen = np.array([np.mean([uvl[li].uv[:] for li in p.loop_indices], 0) for p in me.polygons])
            sh = [_mat_slot(me.materials[p.material_index]) for p in me.polygons]
            _FACEUV[o.name] = (cen, sh)
        cen, sh = _FACEUV[o.name]; kill = np.zeros(len(cen), bool)
        for slot in ('Ch49_1001', 'Ch49_1002'):
            p = f'{d}/id_{slot}_Diffuse.png'
            if not os.path.exists(p): continue
            ids = np.asarray(_PI.open(p)); ids = ids[..., 0] if ids.ndim == 3 else ids; H, W = ids.shape
            m = np.array([s_ == slot for s_ in sh])
            if not m.any(): continue
            px = ((cen[m, 0] % 1) * W).astype(int).clip(0, W - 1); py = ((1 - cen[m, 1] % 1) * H).astype(int).clip(0, H - 1)
            kill[np.nonzero(m)[0]] = np.isin(ids[py, px], drop)
        verts = sorted({v for i in np.nonzero(kill)[0] for v in o.data.polygons[i].vertices})
        vg = o.vertex_groups.get('DROP') or o.vertex_groups.new(name='DROP')
        vg.remove(list(range(len(o.data.vertices)))); vg.add(verts, 1.0, 'REPLACE')
        if md is None:
            md = o.modifiers.new('DROP', 'MASK'); md.vertex_group = 'DROP'; md.invert_vertex_group = True
            o.modifiers.move(len(o.modifiers) - 1, 0)
        md.show_render = md.show_viewport = True
        print('drop', o.name, int(kill.sum()), 'faces')
def load_char(cid):
    d = os.path.join(CH, cid); meta = json.load(open(f'{d}/meta.json'))
    for k, f in (('Ch49_1001', 'Ch49_1001.png'), ('Ch49_1002', 'Ch49_1002.png'), ('face', 'face.png'), ('hair', 'hair.png')):
        IMG[k].source = 'FILE'; IMG[k].filepath = f'{d}/{f}'; IMG[k].reload()
    for k in idimg:                                   # per-character garment-ID map (e.g. harness hidden) if present
        p = f'{d}/id_{k}_Diffuse.png'
        idimg[k].filepath = p if os.path.exists(p) else f'{ANIM}id_{k}_Diffuse.png'; idimg[k].reload()
    hair_obj.hide_render = bool(meta['drop_hair'])
    _apply_drop(meta.get('drop_ids', []), d)
    if HELMET_MAT is not None and 'helmet' in meta:
        lin = [((c / 255) ** 2.2) for c in meta['helmet']]; cel = HELMET_MAT.node_tree.nodes['CEL']
        cel.inputs['B'].default_value = lin + [1]; cel.inputs['A'].default_value = [x * 0.66 ** 2.2 for x in lin] + [1]
    return d, meta

frames = list(range(fs, fe, STEP))
for cid in IDS:
    d, meta = load_char(cid)
    if ONLY in ('both', 'inv'):
        rest_pose_arms_down(); gun.hide_render = True
        sc.render.resolution_x, sc.render.resolution_y = 1280, 3200
        tgt.location = (0, 0, 0.5 * h49); cam_d.ortho_scale = 1.10 * h49 * 3200 / 3200
        place_camera(5, 0.0)
        os.makedirs(f'{d}/inv', exist_ok=True); shoot(f'{d}/inv/front')
    if ONLY in ('both', 'walk'):
        walk_pose(); gun.hide_render = False
        sc.render.resolution_x, sc.render.resolution_y = 512, 640
        tgt.location = (0, 0, 0.5 * h49); cam_d.ortho_scale = 1.12 * h49
        os.makedirs(f'{d}/walk', exist_ok=True)
        for k in DIRS:
            place_camera(k, math.radians(30))
            for i, f in enumerate(frames):
                sc.frame_set(f); place_gun(); shoot(f'{d}/walk/d{k}_f{i:02d}')
        json.dump({'frames': len(frames), 'dirs': DIRS, 'h49': float(h49)}, open(f'{d}/walk/meta.json', 'w'))
    print('CHAR DONE', cid, flush=True)
