"""Roadblock on the Mixamo Brute body: his own sculpted muscles, trousers, boots and moustache, repainted flat
cartoon (paint_bru.py). Renders beauty + part-ID frames for the ink pass (cast_cartoon/compose_char.py)."""
import bpy, bmesh, sys, os, math, json, struct, glob
from mathutils import Vector, Matrix
import numpy as np
D = '/mnt/user-data/uploads/Downloads/'
WS = '/tmp/claude-0/ws/'; B = WS + 'bru/'
# build session: painted sheets live in Reference\models\mixamo\painted\roadblock\tex (staged here)
TEX = os.environ.get('RB_TEX', '/mnt/user-data/uploads/GIJoe_XCOM_4x/Reference/models/mixamo/painted/roadblock/tex/')
SAVE = sys.argv[sys.argv.index('--save-blend') + 1] if '--save-blend' in sys.argv else None
CLIP = sys.argv[sys.argv.index('--clip') + 1] if '--clip' in sys.argv else WS + 'mix/packs/Rifle 8-Way Locomotion Pack/walk forward.fbx'
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else B + 'frames'
DIRS = [int(x) for x in sys.argv[sys.argv.index('--dirs') + 1].split(',')] if '--dirs' in sys.argv else list(range(1, 9))
STEP = int(sys.argv[sys.argv.index('--step') + 1]) if '--step' in sys.argv else 2
FMAX = int(sys.argv[sys.argv.index('--fmax') + 1]) if '--fmax' in sys.argv else 999
RES = (512, 640)
TARGET_H = float(os.environ.get('RB_HEIGHT', '1.90'))      # Brute is 2.15 m; Roadblock is big but not a giant
bpy.ops.wm.read_factory_settings(use_empty=True)
def imp(p, tag):
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new: o.name = tag + '|' + o.name
    return new
A = imp(D + 'Brute.fbx', 'B')
An = imp(CLIP, 'C') if not SAVE else []      # --save-blend: no clip, the renderer applies its own
arm = [o for o in A if o.type == 'ARMATURE'][0]
if not SAVE:
    arm_c = [o for o in An if o.type == 'ARMATURE'][0]
    clip = arm_c.animation_data.action; clip.use_fake_user = True
import re
for b in arm.data.bones: b.name = re.sub(r'mixamorig\d*:', 'mixamorig:', b.name)
def world_coords(o):
    M = o.matrix_world; return np.array([M @ v.co for v in o.data.vertices])
KEEP = {'MaleBruteA_Body': 'body', 'MaleBruteA_Bottoms': 'bottoms', 'MaleBruteA_Shoes': 'shoes', 'MaleBruteA_Moustaches': 'mous', 'MaleBruteA_Eyes': 'eyes'}
body_meshes = []
for o in [o for o in A if o.type == 'MESH']:
    k = o.name.split('|')[-1]
    if k not in KEEP: bpy.data.objects.remove(o); continue
    o['tag'] = KEEP[k]; body_meshes.append(o)
    for vg in o.vertex_groups: vg.name = re.sub(r'mixamorig\d*:', 'mixamorig:', vg.name)
arm.data.pose_position = 'REST'; bpy.context.view_layer.update()
h0 = max(world_coords(o)[:, 2].max() for o in body_meshes)
arm.scale = arm.scale * (TARGET_H / h0); bpy.context.view_layer.update()
h49 = max(world_coords(o)[:, 2].max() for o in body_meshes)
print('height', round(h0, 3), '->', round(h49, 3))
FRAME_H = float(os.environ.get('FRAME_H', '1.80'))       # frame everyone by the same reference height
if not SAVE: bpy.data.objects.remove(arm_c)

# ---- leg gear: thigh straps + holster + pouch bound to the thigh bones ----
sys.path.insert(0, WS + 'props'); import cast_props as CP
legs = [o for o in body_meshes if o['tag'] == 'bottoms']
PL = np.concatenate([world_coords(o) for o in legs])
def _leg_frame(side, frac):
    b_ = arm.data.bones['mixamorig:%sUpLeg' % side]
    h_ = np.array(arm.matrix_world @ b_.head_local); t_ = np.array(arm.matrix_world @ b_.tail_local)
    ax = (t_ - h_) / np.linalg.norm(t_ - h_); c = h_ + frac * (t_ - h_)
    u = np.cross(ax, [0, 1, 0]); u /= np.linalg.norm(u); v = np.cross(ax, u)
    rel = PL - c; al = rel @ ax; sel = (np.abs(al) < 0.025) & (np.sign(PL[:, 0]) == np.sign(h_[0]))
    rad = rel[sel] - np.outer(al[sel], ax)
    return b_.name, c, ax, u, v, rad, np.sign(h_[0])
def thigh_ring(side, frac, width, rgb, gid, name, pad=0.006):
    bn, c, ax, u, v, rad, sx = _leg_frame(side, frac)
    N = 28; ang = np.arctan2(rad @ v, rad @ u); rr = np.linalg.norm(rad, axis=1)
    R = []
    for k in range(N):
        a0 = -np.pi + 2 * np.pi * k / N; d = np.abs((ang - a0 + np.pi) % (2 * np.pi) - np.pi) < np.pi / N * 1.5
        R.append(rr[d].max() if d.any() else (rr.max() if len(rr) else 0.08))
    R = np.array(R) + pad
    V = []
    for s_ in (-width / 2, width / 2):
        for k in range(N):
            a0 = -np.pi + 2 * np.pi * k / N; V.append(c + s_ * ax + R[k] * (np.cos(a0) * u + np.sin(a0) * v))
    F = [(k, (k + 1) % N, N + (k + 1) % N, N + k) for k in range(N)]
    o = CP._obj(name, np.array(V), F); o.data.materials.append(CP.cel_mat(name + '_m', rgb, gid)); CP.bind(o, arm, bn)
    return o
def box_on_thigh(side, frac, size, rgb, gid, name, out=0.0):
    """box sitting on the outside of the thigh. size = (along leg, front-back, thickness)"""
    bn, c, ax, u, v, rad, sx = _leg_frame(side, frac)
    side_dir = np.array([sx, 0, 0.0]); side_dir -= (side_dir @ ax) * ax; side_dir /= np.linalg.norm(side_dir)
    surf = (rad @ side_dir).max() if len(rad) else 0.08
    fb = np.cross(ax, side_dir)
    cc = c + side_dir * (surf + size[2] / 2 + out)
    V = [cc + i * size[0] / 2 * ax + j * size[1] / 2 * fb + k * size[2] / 2 * side_dir for i in (-1, 1) for j in (-1, 1) for k in (-1, 1)]
    F = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    o = CP._obj(name, np.array(V), F, smooth=False); o.data.materials.append(CP.cel_mat(name + '_m', rgb, gid)); CP.bind(o, arm, bn)
    return o
if os.environ.get('RB_LEGGEAR', '1') == '1':
    GREEN, BLACK = (104, 150, 54), (34, 34, 38)
    thigh_ring('Right', 0.52, 0.026, GREEN, 31, 'strapR1'); thigh_ring('Right', 0.72, 0.026, GREEN, 31, 'strapR2')
    box_on_thigh('Right', 0.62, (0.17, 0.085, 0.035), GREEN, 32, 'pouchR')
    thigh_ring('Left', 0.56, 0.026, BLACK, 33, 'strapL')
    box_on_thigh('Left', 0.40, (0.19, 0.075, 0.04), BLACK, 34, 'holsterL')
    box_on_thigh('Left', 0.20, (0.07, 0.04, 0.035), (60, 58, 56), 35, 'gripL', out=-0.005)
arm.data.pose_position = 'POSE'

# ---- the clip, forward travel removed on the hips ----
def _apply_clip():
    global fs, fe
    arm.animation_data_clear(); arm.animation_data_create()
    for fc in (clip.fcurves if hasattr(clip, 'fcurves') and len(clip.fcurves) else []): fc.data_path = re.sub(r'mixamorig\d*:', 'mixamorig:', fc.data_path)
    arm.animation_data.action = clip
    if hasattr(arm.animation_data, 'action_slot') and clip.slots: arm.animation_data.action_slot = clip.slots[0]
    def fcurves(act):
        if hasattr(act, 'fcurves') and len(act.fcurves): return list(act.fcurves)
        out = []
        for L in act.layers:
            for st in L.strips:
                for cb in st.channelbags: out += list(cb.fcurves)
        return out
    for fc in fcurves(clip): fc.data_path = re.sub(r'mixamorig\d*:', 'mixamorig:', fc.data_path)
    for fc in [fc for fc in fcurves(clip) if fc.data_path == 'pose.bones["mixamorig:Hips"].location']:
        xs = np.array([k.co[0] for k in fc.keyframe_points]); ys = np.array([k.co[1] for k in fc.keyframe_points])
        a_, b_ = np.polyfit(xs, ys, 1)
        if abs(a_) * (xs.max() - xs.min()) > 30:
            for k in fc.keyframe_points:
                k.co[1] -= a_ * k.co[0] + b_ - (a_ * xs[0] + b_); k.handle_left[1] = k.co[1]; k.handle_right[1] = k.co[1]
    fs, fe = [int(x) for x in clip.frame_range]
    # ---- hip carry: upper body from another clip (e.g. the rifle idle, gun held at the hip), legs from the walk ----
    UPPER = os.environ.get('UPPER_CLIP')
    if UPPER:
        Au = imp(UPPER, 'U'); arm_u = [o for o in Au if o.type == 'ARMATURE'][0]; cu = arm_u.animation_data.action
        ufs, ufe = [int(x) for x in cu.frame_range]; ulen = max(1, ufe - ufs)
        UP_BONES = ('Spine', 'Spine1', 'Spine2', 'Neck', 'Head', 'Shoulder', 'Arm', 'ForeArm', 'Hand')
        def bone_of(dp):
            m_ = re.search(r'pose.bones\["mixamorig\d*:([A-Za-z]+?)(\d*)"\]', dp)
            return m_.group(1) if m_ else None
        def upper(b):
            if b is None: return False
            b2 = b.replace('Left', '').replace('Right', '')
            return b2 in UP_BONES or b2.startswith('Hand')
        ucurves = {(re.sub(r'mixamorig\d*:', 'mixamorig:', fc.data_path), fc.array_index): fc for fc in fcurves(cu)}
        n_rep = 0
        for fc in fcurves(clip):
            if not upper(bone_of(fc.data_path)) or fc.data_path.endswith('location'): continue
            uf = ucurves.get((fc.data_path, fc.array_index))
            if uf is None: continue
            for k in fc.keyframe_points:
                t = ufs + ((k.co[0] - fs) % ulen); v = uf.evaluate(t)
                k.co[1] = v; k.handle_left[1] = v; k.handle_right[1] = v
            n_rep += 1
        print('upper body from', os.path.basename(UPPER), 'curves replaced', n_rep)
        for o in Au: bpy.data.objects.remove(o)

if not SAVE: _apply_clip()

# ---- materials: painted flat textures + garment-ID textures (per mesh) ----
def load(p): return bpy.data.images.load(p, check_existing=True)
def id_nodes(nt, id_src):
    comb = nt.nodes.new('ShaderNodeCombineColor')
    if isinstance(id_src, float): comb.inputs[0].default_value = id_src
    else: nt.links.new(id_src, comb.inputs[0])
    camd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
    nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
    ei = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], ei.inputs['Color']); return ei
def painted_mat(tag, uvname):
    m = bpy.data.materials.new('rb_' + tag); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); uv = nt.nodes.new('ShaderNodeUVMap'); uv.uv_map = uvname
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = load(TEX + f'{tag}.png'); nt.links.new(uv.outputs[0], t.inputs[0])
    it = nt.nodes.new('ShaderNodeTexImage'); it.image = load(TEX + f'id_{tag}.png'); it.image.colorspace_settings.name = 'Non-Color'
    it.interpolation = 'Closest'; nt.links.new(uv.outputs[0], it.inputs[0])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(it.outputs['Color'], sep.inputs[0])
    emB = nt.nodes.new('ShaderNodeEmission'); nt.links.new(t.outputs['Color'], emB.inputs['Color'])
    ei = id_nodes(nt, sep.outputs[0])
    sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'
    nt.links.new(emB.outputs[0], sw.inputs[1]); nt.links.new(ei.outputs[0], sw.inputs[2]); nt.links.new(sw.outputs[0], out.inputs['Surface'])
    return m
def flat_mat(name, rgb, gid):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); eb = nt.nodes.new('ShaderNodeEmission')
    eb.inputs['Color'].default_value = tuple((c / 255) ** 2.2 for c in rgb) + (1,)
    ei = id_nodes(nt, gid / 40.0)
    sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'
    nt.links.new(eb.outputs[0], sw.inputs[1]); nt.links.new(ei.outputs[0], sw.inputs[2]); nt.links.new(sw.outputs[0], out.inputs['Surface'])
    return m
for o in body_meshes:
    tag = o['tag']
    m = flat_mat('rb_eyes', (40, 26, 18), 29) if tag == 'eyes' else painted_mat(tag, o.data.uv_layers[0].name)
    o.data.materials.clear(); o.data.materials.append(m)
def id_mode(on):
    for m in bpy.data.materials:
        if m.node_tree and 'IDSWITCH' in m.node_tree.nodes: m.node_tree.nodes['IDSWITCH'].inputs[0].default_value = 1.0 if on else 0.0

if SAVE:      # build session: Roadblock empty-handed (no .50 cal), no clip, no camera; textures packed in
    arm.animation_data_clear()
    for o in list(bpy.data.objects):
        if o.type in ('CAMERA', 'LIGHT'): bpy.data.objects.remove(o)
    for a_ in list(bpy.data.actions): bpy.data.actions.remove(a_)
    arm.name = 'Armature'; bpy.data.orphans_purge(do_recursive=True); bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=SAVE); sys.exit(0)
# ---- guns ----
def stl_mesh(paths, name):
    V = []; F = []
    for p in paths:
        raw = open(p, 'rb').read(); n = struct.unpack('<I', raw[80:84])[0]
        T = np.frombuffer(raw[84:84 + n * 50], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))['v'].reshape(-1, 3).astype(np.float64)
        b0 = len(V); V.extend(T.tolist()); F.extend([(b0 + 3 * i, b0 + 3 * i + 1, b0 + 3 * i + 2) for i in range(n)])
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.validate()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.01); bpy.ops.object.mode_set(mode='OBJECT')
    o.select_set(False); return o
def make_gun(kind):
    if kind == 'm2':
        # Roadblock's .50 cal (Thingiverse 4566542, Mark2Design, CC-BY): receiver + barrel + carry handle, no tripod/belt
        P_ = WS + 'm2/files/files/'
        g = stl_mesh([P_ + '50_Box.stl', P_ + '50_Barrel.stl', P_ + '50_Handle.stl'], 'm2')
        k = float(os.environ.get('M2_LEN', '1.25')) / 146.6
        g.data.transform(Matrix.Diagonal((k, k, k, 1)) @ Matrix.Translation((0, 10.65, -13.9)))
        for p in g.data.polygons: p.use_smooth = False
        g.data.materials.append(CP.cel_mat('m2_mat', (58, 60, 64), 30))
        G = Vector((-66, 0, -2)) * k; F = Vector((-6.5, 0, -2)) * k   # hands along the barrel line: gun stays level at the hip
        return g, G, F
    g, G, F = CP.weapon(kind); return g, G, F
# ---- camera / render ----
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
sc.render.film_transparent = True; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'; sc.cycles.use_denoising = False
sc.cycles.max_bounces = 1; sc.cycles.transparent_max_bounces = 16
world = bpy.data.worlds.new('w'); sc.world = world
tgt = bpy.data.objects.new('tgt', None); bpy.context.collection.objects.link(tgt); tgt.location = (0, 0, 0.52 * h49)
cam_d = bpy.data.cameras.new('cam'); cam_d.type = 'ORTHO'; cam_d.ortho_scale = 1.12 * max(FRAME_H, h49 * 1.02)
cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
EL = math.radians(30)
FACING = {1: (0, 1), 2: (.707, .707), 3: (1, 0), 4: (.707, -.707), 5: (0, -1), 6: (-.707, -.707), 7: (-1, 0), 8: (-.707, .707)}
def place_camera(k):
    fx, fy = FACING[k]; alpha = math.atan2(fy, fx); phi = alpha + math.pi / 2
    a = Vector((math.sin(phi), math.cos(phi), 0))
    cam.location = tgt.location - a * 10 * math.cos(EL) + Vector((0, 0, 10 * math.sin(EL)))

GUN = '--nogun' not in sys.argv
if GUN:
    gun, G_LOCAL, F_LOCAL = make_gun(os.environ.get('GUNKIND', 'm2'))
    HAND_IDX = {}
    for o in body_meshes:
        gi = {vg.index: vg.name for vg in o.vertex_groups}
        for side in ('Left', 'Right'):
            idx = [v.index for v in o.data.vertices
                   if sum(g.weight for g in v.groups if gi[g.group].startswith(f'mixamorig:{side}Hand')) > 0.6]
            if idx: HAND_IDX.setdefault(side, []).append((o, np.array(idx)))
    print('hand verts', {k: sum(len(i) for _, i in v) for k, v in HAND_IDX.items()})
    def place_gun():
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        def hand(side):
            pts = []
            for o, idx in HAND_IDX[side]:
                me = o.evaluated_get(dg).to_mesh()
                co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co)
                Mw = np.array(o.matrix_world); pc = co.reshape(-1, 3)[idx]
                pts.append(pc @ Mw[:3, :3].T + Mw[:3, 3]); o.evaluated_get(dg).to_mesh_clear()
            return Vector(np.concatenate(pts).mean(0))
        rh, lh = hand('Right'), hand('Left')
        dl = F_LOCAL - G_LOCAL                                  # gun-space grip->handguard direction
        tilt = math.atan2(dl.z, dl.x)
        d = (lh - rh); d.z *= float(os.environ.get('GUN_PITCH', '0.3')); d = d.normalized()   # heavy gun: keep it near level
        upw = Vector((0, 0, 1)); up = (upw - d * upw.dot(d)).normalized()
        y = up.cross(d)
        R = Matrix((d, y, up)).transposed() @ Matrix.Rotation(tilt, 3, 'Y')   # so the grip->handguard line hits both hands
        loc = rh - R @ G_LOCAL
        gun.matrix_world = Matrix.Translation(loc) @ R.to_4x4()
        if os.environ.get("GUNDBG"): print("GUN", gun.name, tuple(round(c, 3) for c in loc), gun.dimensions[:], len(gun.data.vertices), "rh", tuple(round(c,3) for c in rh), "lh", tuple(round(c,3) for c in lh))
os.makedirs(OUT, exist_ok=True)
frames = list(range(fs, fe, STEP))[:FMAX]
if os.environ.get('REST'): arm.data.pose_position = 'REST'
for k in DIRS:
    place_camera(k)
    for i, f in enumerate(frames):
        sc.frame_set(f)
        if GUN: place_gun()
        id_mode(False); sc.cycles.samples = 8; sc.cycles.filter_width = 1.0; sc.view_settings.view_transform = 'Standard'
        sc.render.filepath = f'{OUT}/d{k}_f{i:02d}_beauty.png'; bpy.ops.render.render(write_still=True)
        id_mode(True); sc.cycles.samples = 1; sc.cycles.filter_width = 0.01; sc.view_settings.view_transform = 'Raw'
        sc.render.filepath = f'{OUT}/d{k}_f{i:02d}_id.png'; bpy.ops.render.render(write_still=True)
    print('direction', k, 'done', len(frames), 'frames', flush=True)
json.dump({'frames': len(frames), 'dirs': DIRS, 'h49': float(h49)}, open(f'{OUT}/meta.json', 'w'))
