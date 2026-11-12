"""Animated Snake Eyes: Ch45 bodysuit body with the flat cartoon repaint, katana on the back, M-16 in both hands.
Same camera, ID render and ink pass as build_duke.py / compose.py."""
import bpy, sys, os, math, json
from mathutils import Vector, Matrix
import numpy as np
REF = os.environ.get('GIJOE_REF', '/mnt/user-data/uploads/GIJoe_XCOM_4x/Reference/')
BODY = REF + 'models/mixamo/bodies/body_ch45_lean_bodysuit.fbx'      # = Downloads\Prone Firing Rifle.fbx
WS = '/tmp/claude-0/ws/'; SE = os.environ.get('SE_TEX', REF + 'models/mixamo/painted/snake_eyes/')   # flat_/id_Ch45_1001_Diffuse.png
GUNF = REF + 'models/guns/grunt_M-16.glb'
SAVE = sys.argv[sys.argv.index('--save-blend') + 1] if '--save-blend' in sys.argv else None   # build session: empty-handed .blend for render_char.py
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
CLIP = arg('--clip', WS + 'mix/packs/Rifle 8-Way Locomotion Pack/walk forward.fbx')
OUT = arg('--out', SE + 'frames'); DIRS = [int(x) for x in arg('--dirs', '1,2,3,4,5,6,7,8').split(',')]
STEP = int(arg('--step', '2')); FMAX = int(arg('--fmax', '999')); RES = (512, 640)
bpy.ops.wm.read_factory_settings(use_empty=True)
def imp(p, tag):
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new: o.name = tag + '|' + o.name
    return new
A = imp(BODY, 'B'); An = imp(CLIP, 'C') if not SAVE else []
arm = [o for o in A if o.type == 'ARMATURE'][0]; arm_c = [o for o in An if o.type == 'ARMATURE'][0] if not SAVE else None
body = [o for o in A if o.type == 'MESH'][0]
for b in arm.data.bones: b.name = b.name.replace('mixamorig1:', 'mixamorig:')
for vg in body.vertex_groups: vg.name = vg.name.replace('mixamorig1:', 'mixamorig:')
if not SAVE: clip = arm_c.animation_data.action; clip.use_fake_user = True
for o in An:
    if o.name in bpy.data.objects: bpy.data.objects.remove(o)
arm.data.pose_position = 'REST'; bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get(); me = body.evaluated_get(dg).to_mesh()
V = np.array([body.matrix_world @ v.co for v in me.vertices]); body.evaluated_get(dg).to_mesh_clear()
H = float(V[:, 2].max())
# ---- katana on the back, bound to the upper spine ----
def back_y(x, z):
    m = (np.abs(V[:, 0] - x) < 0.04) & (np.abs(V[:, 2] - z) < 0.04)
    return float(V[m, 1].max()) if m.any() else 0.15
def flat_mat(name, rgb, gid):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    o_ = nt.nodes.new('ShaderNodeOutputMaterial'); eb = nt.nodes.new('ShaderNodeEmission')
    eb.inputs['Color'].default_value = tuple((c / 255) ** 2.2 for c in rgb) + (1,)
    comb = nt.nodes.new('ShaderNodeCombineColor'); comb.inputs[0].default_value = gid / 40.0
    camd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
    nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
    ei = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], ei.inputs['Color'])
    sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'
    nt.links.new(eb.outputs[0], sw.inputs[1]); nt.links.new(ei.outputs[0], sw.inputs[2]); nt.links.new(sw.outputs[0], o_.inputs['Surface'])
    return m
def box_between(p0, p1, w, t, mat, name):
    bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.object; o.name = name
    d = (p1 - p0); L = d.length; zax = d.normalized()
    yax = Vector((0, 1, 0)) if abs(zax.y) < 0.9 else Vector((0, 0, 1)); xax = yax.cross(zax).normalized(); yax = zax.cross(xax)
    R = Matrix((xax, yax, zax)).transposed().to_4x4()
    o.matrix_world = Matrix.Translation((p0 + p1) / 2) @ R @ Matrix.Diagonal((w, t, L, 1))
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    o.data.materials.append(mat); return o
guard_xz = Vector((0.085, 0, 1.565)); tip_xz = Vector((-0.20, 0, 1.00))
dirv = (guard_xz - tip_xz).normalized()
def onback(p, off=0.035): return Vector((p.x, back_y(p.x, min(max(p.z, 1.0), 1.55)) + off, p.z))
g = onback(guard_xz); tp = onback(tip_xz); top = g + Vector((dirv.x, 0, dirv.z)) * 0.24
M_SH = flat_mat('sheath', (58, 58, 64), 31); M_HD = flat_mat('hilt', (28, 28, 32), 32); M_GD = flat_mat('guard', (140, 136, 128), 33)
PROP = arg('--prop', 'none') if not SAVE else 'none'      # saved blend: scabbard + hilt on the back, nothing in hand
parts = [box_between(tp, g, 0.055, 0.03, M_SH, 'sheath')]
if PROP != 'katana':
    parts += [box_between(g, top, 0.032, 0.032, M_HD, 'hilt'),
              box_between(g - (top - g).normalized() * 0.006, g + (top - g).normalized() * 0.012, 0.085, 0.06, M_GD, 'guard')]
bpy.ops.object.select_all(action='DESELECT')
for p in parts: p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); sword = parts[0]; sword.name = 'katana'
bn = arm.data.bones['mixamorig:Spine2']
sword.parent = arm; sword.parent_type = 'BONE'; sword.parent_bone = bn.name
sword.matrix_parent_inverse = (arm.matrix_world @ bn.matrix_local @ Matrix.Translation((0, bn.length, 0))).inverted()

def bind_to_bone(o, bone_name):
    bn_ = arm.data.bones[bone_name]
    o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = bn_.name
    o.matrix_parent_inverse = (arm.matrix_world @ bn_.matrix_local @ Matrix.Translation((0, bn_.length, 0))).inverted()
hb = arm.data.bones['mixamorig:RightHand']
wrist = arm.matrix_world @ hb.head_local
GX = float(arg('--gx', '0.075')); GZ = float(arg('--gz', '-0.03')); GY = float(arg('--gy', '0.0'))
fist = wrist + Vector((-GX, GY, GZ))                    # rest T-pose: fingers along -X, palm down, thumb toward -Y
if PROP == 'uzi':
    import struct
    raw = open('/tmp/claude-0/ws/uzi2/files/Classified_Uzi.stl', 'rb').read(); n = struct.unpack('<I', raw[80:84])[0]
    tri = np.frombuffer(raw[84:84 + n * 50], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))['v'].reshape(-1, 3).astype(np.float64)
    sc_ = 0.45 / (tri[:, 0].max() - tri[:, 0].min())
    grip = np.array([-1.5, -7.73, 12.0]); tri = (tri - grip) * sc_      # grip point -> origin, metres, barrel +X, up +Z
    me_ = bpy.data.meshes.new('uzi'); me_.from_pydata([tuple(p) for p in tri], [], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(n)])
    me_.validate(); prop = bpy.data.objects.new('uzi', me_); bpy.context.collection.objects.link(prop)
    prop.data.materials.append(flat_mat('uzi_flat', (64, 66, 72), 30))
    if arg('--hold', 'carry') == 'pistol':
        Rg = Matrix(((-1, 0, 0), (0, 0, -1), (0, -1, 0))).transposed()  # aimed: barrel along the knuckles, top toward the thumb
    else:
        Rg = Matrix(((0, -1, 0), (0, 0, -1), (1, 0, 0))).transposed()   # carried: barrel along the thumb (forward when the arm hangs)
    prop.matrix_world = Matrix.Translation(fist) @ Rg.to_4x4()
    bind_to_bone(prop, 'mixamorig:RightHand')
elif PROP == 'katana':
    up_ = Vector((0, -1, 0))                                       # blade leaves the fist on the thumb side
    guard_p = fist + up_ * 0.05
    kb = [box_between(guard_p - up_ * 0.25, guard_p, 0.032, 0.032, M_HD, 'k_hilt'),
          box_between(guard_p - up_ * 0.01, guard_p + up_ * 0.012, 0.085, 0.07, M_GD, 'k_guard'),
          box_between(guard_p, guard_p + up_ * 0.70, 0.040, 0.022, flat_mat('blade', (200, 204, 210), 34), 'k_blade')]
    bpy.ops.object.select_all(action='DESELECT')
    for p in kb: p.select_set(True)
    bpy.context.view_layer.objects.active = kb[0]; bpy.ops.object.join(); prop = kb[0]
    bind_to_bone(prop, 'mixamorig:RightHand')
arm.data.pose_position = 'POSE'
def _apply_clip():
    global fs, fe
    # ---- clip with hip travel removed ----
    arm.animation_data_clear(); arm.animation_data_create(); arm.animation_data.action = clip
    if hasattr(arm.animation_data, 'action_slot') and clip.slots: arm.animation_data.action_slot = clip.slots[0]
    import re
    def fcurves(act):
        if hasattr(act, 'fcurves') and len(act.fcurves): return list(act.fcurves)
        out = []
        for Ly in act.layers:
            for st in Ly.strips:
                for cb in st.channelbags: out += list(cb.fcurves)
        return out
    for fc in fcurves(clip):
        if 'mixamorig' in fc.data_path: fc.data_path = re.sub(r'mixamorig\d*:', 'mixamorig:', fc.data_path)
    for fc in [f for f in fcurves(clip) if f.data_path == 'pose.bones["mixamorig:Hips"].location']:
        xs = np.array([k.co[0] for k in fc.keyframe_points]); ys = np.array([k.co[1] for k in fc.keyframe_points])
        a, b = np.polyfit(xs, ys, 1)
        if abs(a) * (xs.max() - xs.min()) > 30 and not ('--keepdrift' in sys.argv and fc.array_index == 1):
            for k in fc.keyframe_points:
                k.co[1] -= a * k.co[0] + b - (a * xs[0] + b); k.handle_left[1] = k.co[1]; k.handle_right[1] = k.co[1]
    fs, fe = [int(x) for x in clip.frame_range]
    if '--inplace' in sys.argv:                      # combat clips: take out slow travel, keep the quick shifts
        for fc in [f for f in fcurves(clip) if f.data_path == 'pose.bones["mixamorig:Hips"].location' and f.array_index in (0, 2)]:
            ys = np.array([k.co[1] for k in fc.keyframe_points]); w = 25
            pad = np.pad(ys, w, mode='edge'); sm = np.convolve(pad, np.ones(2 * w + 1) / (2 * w + 1), 'same')[w:-w]
            for k, v in zip(fc.keyframe_points, ys - sm + sm[0] * 0):
                k.co[1] = v; k.handle_left[1] = v; k.handle_right[1] = v

if not SAVE: _apply_clip()
# ---- body material: flat colour + garment ids ----
def load(p): return bpy.data.images.load(p, check_existing=True)
m = body.data.materials[0]; nt = m.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
out = nt.nodes.new('ShaderNodeOutputMaterial')
t = nt.nodes.new('ShaderNodeTexImage'); t.image = load(SE + 'flat_Ch45_1001_Diffuse.png'); t.interpolation = 'Closest'
emB = nt.nodes.new('ShaderNodeEmission'); nt.links.new(t.outputs['Color'], emB.inputs['Color'])
it = nt.nodes.new('ShaderNodeTexImage'); it.image = load(SE + 'id_Ch45_1001_Diffuse.png'); it.image.colorspace_settings.name = 'Non-Color'; it.interpolation = 'Closest'
sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(it.outputs['Color'], sep.inputs[0])
comb = nt.nodes.new('ShaderNodeCombineColor'); nt.links.new(sep.outputs[0], comb.inputs[0])
camd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange')
mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
emI = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], emI.inputs['Color'])
sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'
nt.links.new(emB.outputs[0], sw.inputs[1]); nt.links.new(emI.outputs[0], sw.inputs[2]); nt.links.new(sw.outputs[0], out.inputs['Surface'])
def id_mode(on):
    for mm in bpy.data.materials:
        if mm.node_tree and 'IDSWITCH' in mm.node_tree.nodes: mm.node_tree.nodes['IDSWITCH'].inputs[0].default_value = 1.0 if on else 0.0
if SAVE:
    import re as _re
    for b_ in arm.data.bones: b_.name = _re.sub(r'mixamorig\d*:', 'mixamorig:', b_.name)
    for vg in body.vertex_groups: vg.name = _re.sub(r'mixamorig\d*:', 'mixamorig:', vg.name)
    sword.name = 'scabbard_on_back'          # worn gear (sheathed katana), not a held weapon
    arm.animation_data_clear()
    for a_ in list(bpy.data.actions): bpy.data.actions.remove(a_)
    arm.name = 'Armature'; bpy.data.orphans_purge(do_recursive=True); bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=SAVE); sys.exit(0)
# ---- camera ----
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
sc.render.film_transparent = True; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'; sc.cycles.use_denoising = False
sc.cycles.max_bounces = 1; sc.cycles.transparent_max_bounces = 16; sc.world = bpy.data.worlds.new('w')
tgt = bpy.data.objects.new('tgt', None); bpy.context.collection.objects.link(tgt); tgt.location = (0, 0, 0.50 * H)
cam_d = bpy.data.cameras.new('cam'); cam_d.type = 'ORTHO'; cam_d.ortho_scale = 1.12 * H
cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
EL = math.radians(30)
FACING = {1: (0, 1), 2: (.707, .707), 3: (1, 0), 4: (.707, -.707), 5: (0, -1), 6: (-.707, -.707), 7: (-1, 0), 8: (-.707, .707)}
def place_camera(k):
    fx, fy = FACING[k]; phi = math.atan2(fy, fx) + math.pi / 2
    a = Vector((math.sin(phi), math.cos(phi), 0))
    cam.location = tgt.location - a * 10 * math.cos(EL) + Vector((0, 0, 10 * math.sin(EL)))
# ---- gun ----
GUN = '--nogun' not in sys.argv
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=GUNF) if GUN else None
gun = [o for o in bpy.data.objects if o not in before and o.type == 'MESH'][0] if GUN else None
if GUN: gun.parent = None; gun.data.transform(gun.matrix_world); gun.matrix_world = Matrix.Identity(4)
if GUN: gun.data.materials.clear(); gun.data.materials.append(flat_mat('gun_flat', (60, 62, 66), 30))
G_LOCAL = Vector((-0.317, 0.0, -0.065)); F_LOCAL = Vector((0.07, 0.0, 0.040))
gi = {vg.index: vg.name for vg in body.vertex_groups}; HAND = {}
for side in ('Left', 'Right'):
    HAND[side] = np.array([v.index for v in body.data.vertices
                           if sum(g.weight for g in v.groups if gi[g.group].startswith(f'mixamorig:{side}Hand')) > 0.6])
print('hand verts', {k: len(v) for k, v in HAND.items()}, 'height', H)
def place_gun():
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3); Mw = np.array(body.matrix_world)
    def hand(s): p = co[HAND[s]].mean(0); return Vector((Mw @ np.append(p, 1))[:3])
    rh, lh = hand('Right'), hand('Left')
    dl = F_LOCAL - G_LOCAL; tilt = math.atan2(dl.z, dl.x)
    d = (lh - rh).normalized(); up = (Vector((0, 0, 1)) - d * d.z).normalized(); y = up.cross(d)
    R = Matrix((d, y, up)).transposed() @ Matrix.Rotation(tilt, 3, 'Y')
    gun.matrix_world = Matrix.Translation(rh - R @ G_LOCAL) @ R.to_4x4()
os.makedirs(OUT, exist_ok=True)
frames = list(range(fs, fe, STEP))[:FMAX]
for k in DIRS:
    place_camera(k)
    for i, f in enumerate(frames):
        sc.frame_set(f)
        if GUN: place_gun()
        id_mode(False); sc.cycles.samples = 8; sc.cycles.filter_width = 1.0; sc.view_settings.view_transform = 'Standard'
        sc.render.filepath = f'{OUT}/d{k}_f{i:02d}_beauty.png'; bpy.ops.render.render(write_still=True)
        id_mode(True); sc.cycles.samples = 1; sc.cycles.filter_width = 0.01; sc.view_settings.view_transform = 'Raw'
        sc.render.filepath = f'{OUT}/d{k}_f{i:02d}_id.png'; bpy.ops.render.render(write_still=True)
    print('direction', k, 'done', flush=True)
json.dump({'frames': len(frames), 'dirs': DIRS, 'h': H}, open(f'{OUT}/meta.json', 'w'))
