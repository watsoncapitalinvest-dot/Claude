"""Build animated Duke in Blender: Ch49 body (painted) + Ch33 head (cartoon hair) bound to Ch49's skeleton,
Mixamo walk applied with forward drift removed. Renders beauty + part-ID frames for the ink pass."""
import bpy, bmesh, sys, os, math, json
from mathutils import Vector, Matrix
import numpy as np
D = '/mnt/user-data/uploads/Downloads/'
WS = '/tmp/claude-0/ws/'
CUT = 0.845
CLIP = sys.argv[sys.argv.index('--clip') + 1] if '--clip' in sys.argv else WS + 'mix/packs/Rifle 8-Way Locomotion Pack/walk forward.fbx'
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else WS + 'anim/frames'
DIRS = [int(x) for x in sys.argv[sys.argv.index('--dirs') + 1].split(',')] if '--dirs' in sys.argv else list(range(1, 9))
STEP = int(sys.argv[sys.argv.index('--step') + 1]) if '--step' in sys.argv else 2
FMAX = int(sys.argv[sys.argv.index('--fmax') + 1]) if '--fmax' in sys.argv else 999
RES = (512, 640)

bpy.ops.wm.read_factory_settings(use_empty=True)
def imp(p, tag):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new: o.name = tag + '|' + o.name
    return new
A = imp(D + 'Withdrawing Sword (2).fbx', 'B')
Hd = imp(D + 'Withdrawing Sword (7).fbx', 'H')
An = imp(CLIP, 'C')
arm = [o for o in A if o.type == 'ARMATURE'][0]
arm_h = [o for o in Hd if o.type == 'ARMATURE'][0]
arm_c = [o for o in An if o.type == 'ARMATURE'][0]
clip = arm_c.animation_data.action; clip.use_fake_user = True

def world_coords(o):
    M = o.matrix_world; return np.array([M @ v.co for v in o.data.vertices])
def bake_unparent(o):
    mw = o.matrix_world.copy(); o.parent = None; o.data.transform(mw); o.matrix_world = Matrix.Identity(4)

body_meshes = [o for o in A if o.type == 'MESH']
h49 = max(world_coords(o)[:, 2].max() for o in body_meshes)
# neck ring of the body, measured before cutting
allb = np.concatenate([world_coords(o) for o in body_meshes])
ring_b = allb[(allb[:, 2] > (CUT - 0.02) * h49) & (allb[:, 2] < CUT * h49)].mean(0)

def cut_faces(o, keep_fn):
    W = world_coords(o)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    kill = [f for f in bm.faces if not keep_fn(W[[v.index for v in f.verts]].mean(0))]
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(o.data); bm.free()

for o in body_meshes:
    cut_faces(o, lambda c: c[2] < CUT * h49)
    bake_unparent(o); o.modifiers[0].object = arm if o.modifiers else None

head_keep = []
hb = [o for o in Hd if o.type == 'MESH' and o.name.endswith('Ch33_Body')][0]
h33 = world_coords(hb)[:, 2].max()
W33 = world_coords(hb)
ring_h = W33[(W33[:, 2] > CUT * h33) & (W33[:, 2] < (CUT + 0.02) * h33)].mean(0)
s = h49 / h33
off = Vector(ring_b) - Vector(ring_h) * s
for o in [o for o in Hd if o.type == 'MESH']:
    nm = o.name.split('|')[1]
    if nm not in ('Ch33_Body', 'Ch33_Hair'):
        bpy.data.objects.remove(o); continue
    if nm == 'Ch33_Body':
        cut_faces(o, lambda c: c[2] >= CUT * h33 and abs(c[0]) < 0.075 * h33)
    bake_unparent(o)
    o.data.transform(Matrix.Translation(off) @ Matrix.Scale(s, 4))
    for vg in o.vertex_groups: vg.name = vg.name.replace('mixamorig7:', 'mixamorig:')
    mod = [m for m in o.modifiers if m.type == 'ARMATURE'][0]; mod.object = arm
    head_keep.append(o)
for o in (arm_h, arm_c): bpy.data.objects.remove(o)

# ---- apply the clip, remove forward travel on the hips ----
arm.animation_data_clear(); arm.animation_data_create()
arm.animation_data.action = clip
if hasattr(arm.animation_data, 'action_slot') and clip.slots: arm.animation_data.action_slot = clip.slots[0]
def fcurves(act):
    if hasattr(act, 'fcurves') and len(act.fcurves): return list(act.fcurves)
    out = []
    for L in act.layers:
        for st in L.strips:
            for cb in st.channelbags: out += list(cb.fcurves)
    return out
hip = [fc for fc in fcurves(clip) if fc.data_path == 'pose.bones["mixamorig:Hips"].location']
rng = [(fc, max(k.co[1] for k in fc.keyframe_points) - min(k.co[1] for k in fc.keyframe_points)) for fc in hip]
fwd = []
for fc, r in rng:
    xs = np.array([k.co[0] for k in fc.keyframe_points]); ys = np.array([k.co[1] for k in fc.keyframe_points])
    a, b = np.polyfit(xs, ys, 1)
    if abs(a) * (xs.max() - xs.min()) > 30:            # a channel that drifts > 30 cm over the clip = travel
        for k in fc.keyframe_points:
            k.co[1] -= a * k.co[0] + b - (a * xs[0] + b); k.handle_left[1] = k.co[1]; k.handle_right[1] = k.co[1]
        fwd.append(fc.array_index)
fs, fe = [int(x) for x in clip.frame_range]
print('clip frames', fs, fe, 'drift removed on hips axes', fwd)

# ---- materials: flat emission from the painted textures; part-ID colour attribute ----
def load(p): return bpy.data.images.load(p, check_existing=True)
tex_for = {'Ch49_1001': WS + 'duke_out/Ch49_1001_Diffuse.png', 'Ch49_1002': WS + 'duke_out/Ch49_1002_Diffuse.png',
           'Ch33_1002': WS + 'anim/tex/Ch33_hair_duke.png', 'Ch33_1001': WS + 'anim/tex/Ch33_face_duke.png'}
PART = {'Head': 0, 'Neck': 0, 'HeadTop_End': 0}
def part_of(bone):
    b = bone.replace('mixamorig:', '')
    if b in PART: return 0
    if b.startswith('Left') and any(k in b for k in ('Arm', 'Hand', 'Shoulder')): return 2
    if b.startswith('Right') and any(k in b for k in ('Arm', 'Hand', 'Shoulder')): return 3
    if b.startswith('Left'): return 4
    if b.startswith('Right'): return 5
    return 1
def set_ids(o, base):
    gname = {vg.index: vg.name for vg in o.vertex_groups}
    me = o.data
    vpart = np.zeros(len(me.vertices), int)
    for v in me.vertices:
        if v.groups:
            g = max(v.groups, key=lambda g: g.weight); vpart[v.index] = part_of(gname[g.group])
    attr = me.color_attributes.new('pid', 'FLOAT_COLOR', 'CORNER')
    for poly in me.polygons:
        ps = [vpart[me.loops[li].vertex_index] for li in poly.loop_indices]
        p = max(set(ps), key=ps.count)
        sheet = me.materials[poly.material_index].name if me.materials else ''
        pid = base(p, sheet)
        for li in poly.loop_indices: attr.data[li].color = (pid / 40.0, 0, 0, 1)
for o in body_meshes: set_ids(o, lambda p, sh: (20 if sh == 'Ch_49_body1' else 30) + p)
for o in head_keep: set_ids(o, lambda p, sh: 1 if 'Hair' in o.name else 2)

def rebuild_material(m):
    nt = m.node_tree; img = None; alpha_img = None
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            for inp in ('Base Color', 'Alpha'):
                if n.inputs[inp].links:
                    im = n.inputs[inp].links[0].from_node.image
                    key = [k for k in tex_for if k in im.filepath]
                    if inp == 'Base Color': img = load(tex_for[key[0]]) if key else im
                    else: alpha_img = im
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Closest' if 'hair' in (img.filepath if img else '') else 'Linear'
    emB = nt.nodes.new('ShaderNodeEmission'); nt.links.new(t.outputs['Color'], emB.inputs['Color'])
    key = [k for k in ('Ch49_1001', 'Ch49_1002') if img is not None and k in img.filepath]
    comb = nt.nodes.new('ShaderNodeCombineColor')
    if key:
        it = nt.nodes.new('ShaderNodeTexImage'); it.image = load(WS + f'anim/tex/id_{key[0]}_Diffuse.png')
        it.image.colorspace_settings.name = 'Non-Color'; it.interpolation = 'Closest'
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(it.outputs['Color'], sep.inputs[0])
        nt.links.new(sep.outputs[0], comb.inputs[0])
    else:
        comb.inputs[0].default_value = (1 if 'hair' in m.name.lower() else 2) / 40.0
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
mats = set()
for o in body_meshes + head_keep:
    for m in o.data.materials:
        if m and m.name not in mats: rebuild_material(m); mats.add(m.name)
def id_mode(on):
    for m in bpy.data.materials:
        if m.node_tree and 'IDSWITCH' in m.node_tree.nodes: m.node_tree.nodes['IDSWITCH'].inputs[0].default_value = 1.0 if on else 0.0

# ---- camera / render ----
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
sc.render.film_transparent = True; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'; sc.cycles.use_denoising = False
sc.cycles.max_bounces = 1; sc.cycles.transparent_max_bounces = 16
world = bpy.data.worlds.new('w'); sc.world = world
tgt = bpy.data.objects.new('tgt', None); bpy.context.collection.objects.link(tgt); tgt.location = (0, 0, 0.50 * h49)
cam_d = bpy.data.cameras.new('cam'); cam_d.type = 'ORTHO'; cam_d.ortho_scale = 1.12 * h49
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
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath='/mnt/user-data/uploads/GIJoe_XCOM_4x/Reference/models/guns/grunt_M-16.glb')
    gun = [o for o in bpy.data.objects if o not in before and o.type == 'MESH'][0]
    bpy.context.view_layer.objects.active = gun
    gun.parent = None; gun.data.transform(gun.matrix_world); gun.matrix_world = Matrix.Identity(4)
    gm = bpy.data.materials.new('gun_flat'); gm.use_nodes = True; nt = gm.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    o_ = nt.nodes.new('ShaderNodeOutputMaterial')
    eb = nt.nodes.new('ShaderNodeEmission'); eb.inputs['Color'].default_value = (0.045, 0.048, 0.055, 1)   # dark gunmetal (sRGB ~ 60,62,66)
    comb = nt.nodes.new('ShaderNodeCombineColor'); comb.inputs[0].default_value = 30 / 40.0
    camd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
    nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
    ei = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], ei.inputs['Color'])
    sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'
    nt.links.new(eb.outputs[0], sw.inputs[1]); nt.links.new(ei.outputs[0], sw.inputs[2]); nt.links.new(sw.outputs[0], o_.inputs['Surface'])
    gun.data.materials.clear(); gun.data.materials.append(gm)
    G_LOCAL = Vector((-0.317, 0.0, -0.065)); F_LOCAL = Vector((0.07, 0.0, 0.040))   # grip centre, handguard axis
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
                pts.append(co.reshape(-1, 3)[idx]); o.evaluated_get(dg).to_mesh_clear()
            return Vector(np.concatenate(pts).mean(0))
        rh, lh = hand('Right'), hand('Left')
        dl = F_LOCAL - G_LOCAL                                  # gun-space grip->handguard direction
        tilt = math.atan2(dl.z, dl.x)
        d = (lh - rh).normalized()
        upw = Vector((0, 0, 1)); up = (upw - d * upw.dot(d)).normalized()
        y = up.cross(d)
        R = Matrix((d, y, up)).transposed() @ Matrix.Rotation(tilt, 3, 'Y')   # so the grip->handguard line hits both hands
        loc = rh - R @ G_LOCAL
        gun.matrix_world = Matrix.Translation(loc) @ R.to_4x4()
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
    print('direction', k, 'done', len(frames), 'frames', flush=True)
json.dump({'frames': len(frames), 'dirs': DIRS, 'h49': float(h49)}, open(f'{OUT}/meta.json', 'w'))
