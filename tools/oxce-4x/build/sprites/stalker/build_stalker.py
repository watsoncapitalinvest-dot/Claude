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
SAVE = sys.argv[sys.argv.index('--save-blend') + 1] if '--save-blend' in sys.argv else None
# John's 12 Nov Ch49 rules (duke_build_v3 factory_blend.py, via greenshirts/ch49_rules.py): --clean_collar, --swell 0.016
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'greenshirts')); import ch49_rules as RULES
CLEAN = '--clean_collar' in sys.argv; SWELL = float(sys.argv[sys.argv.index('--swell') + 1]) if '--swell' in sys.argv else 0.0   # build session: empty-handed .blend for render_char.py
os.environ.setdefault('CHAR_TEX', '/mnt/user-data/uploads/GIJoe_XCOM_4x/Reference/models/mixamo/painted/cast_cartoon/stalker')   # cc\\stalker\\ staged

bpy.ops.wm.read_factory_settings(use_empty=True)
def imp(p, tag):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new: o.name = tag + '|' + o.name
    return new
A = imp(D + 'Withdrawing Sword (2).fbx', 'B')
Hd = imp(D + 'Stealth Assassination (5).fbx', 'H')     # Ch18 head
An = imp(CLIP, 'C') if not SAVE else []
arm = [o for o in A if o.type == 'ARMATURE'][0]
arm_h = [o for o in Hd if o.type == 'ARMATURE'][0]
if not SAVE:
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
    RULES.cut_body(o, h49, CLEAN)
    bake_unparent(o); o.modifiers[0].object = arm if o.modifiers else None
if SWELL > 0: RULES.swell(body_meshes, h49, SWELL, CLEAN)

head_keep = []
hb = [o for o in Hd if o.type == 'MESH' and o.name.endswith('Ch18')][0]
arm_h.data.pose_position = 'REST'; bpy.context.view_layer.update()
h33 = world_coords(hb)[:, 2].max()
W33 = world_coords(hb)
ring_h = W33[(W33[:, 2] > CUT * h33) & (W33[:, 2] < (CUT + 0.02) * h33)].mean(0)
s = h49 / h33
off = Vector(ring_b) - Vector(ring_h) * s
# texture lookup for the Ch18 faces: drop the cap and earpiece, keep the sunglasses as their own part
img18 = [n.image for n in hb.data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE' and 'Diffuse' in n.image.filepath][0]
PX = np.array(img18.pixels[:]).reshape(img18.size[1], img18.size[0], 4)[..., :3]
RULES.cut_head(hb, h33, CLEAN)
bm = bmesh.new(); bm.from_mesh(hb.data); bm.faces.ensure_lookup_table(); uvly = bm.loops.layers.uv.active
Wh = world_coords(hb); hc_y = Wh[Wh[:, 2] > 0.9 * h33][:, 1].mean()
kill = []; glasses = []; hair = []
# split the dark parts (cap, sunglasses) into connected pieces and judge each piece whole
def is_dark(f):
    uv = np.mean([l[uvly].uv[:] for l in f.loops], 0)
    c = PX[int((uv[1] % 1) * (img18.size[1] - 1)), int((uv[0] % 1) * (img18.size[0] - 1))]
    return c.max() < 0.09, (c.min() > 0.45 and c.max() - c.min() < 0.12)
info = {f.index: is_dark(f) for f in bm.faces}
dark = set(i for i, (d, w) in info.items() if d)
seen = set(); pieces = []
for f in bm.faces:
    if f.index not in dark or f.index in seen: continue
    stack = [f]; piece = []; seen.add(f.index)
    while stack:
        g = stack.pop(); piece.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index in dark and h.index not in seen: seen.add(h.index); stack.append(h)
    pieces.append(piece)
for piece in pieces:
    P = np.array([Wh[[v.index for v in g.verts]].mean(0) for g in piece])
    zr = P[:, 2] / h33
    eye = (np.median(zr) > 0.895) and (np.median(zr) < 0.955) and (zr.max() < 0.957)
    print('dark piece', len(piece), 'z', round(float(zr.min()), 3), round(float(np.median(zr)), 3), round(float(zr.max()), 3), 'glasses' if eye else 'cap')
    kill.extend(piece)                      # Stalker: no cap, no sunglasses
for f in bm.faces:
    if f.index in dark: continue
    p = Wh[[v.index for v in f.verts]].mean(0); zr = p[2] / h33
    if info[f.index][1] and zr > 0.88: kill.append(f)                                       # earpiece coil
    elif zr > (0.962 if p[1] < hc_y - 0.03 else 0.93): hair.append(f)                           # short black hair
mats = hb.data.materials
GL = bpy.data.materials.new('glasses18'); HR = bpy.data.materials.new('hair18')
mats.append(GL); mats.append(HR)
for f in glasses: f.material_index = 1
for f in hair: f.material_index = 2
bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(hb.data); bm.free()
print('ch18 head: cap faces removed', len(kill), 'glasses', len(glasses), 'hair', len(hair))
bake_unparent(hb)
hb.data.transform(Matrix.Translation(off) @ Matrix.Scale(s, 4))
if CLEAN: RULES.tuck_neck(hb, h49)
mod = [m for m in hb.modifiers if m.type == 'ARMATURE'][0]; mod.object = arm
head_keep.append(hb)
for o in [o for o in Hd if o.type == 'MESH' and o is not hb]: bpy.data.objects.remove(o)

# ---- Stalker's black beret: modelled (band hugging the skull + soft crown draped to his right), bound to the Head bone ----
sys.path.insert(0, '/tmp/claude-0/ws/beret'); from beret import make_beret
Wn = world_coords(hb); top = float(Wn[:, 2].max())
BV, BF, _ = make_beret(Wn[Wn[:, 2] > top - 0.2], top - float(os.environ.get('BZ', '0.105')) * s, side=-1.0, puff=0.5, crown_r=0.97, droop=1.0)
bme = bpy.data.meshes.new('beret'); bme.from_pydata([tuple(v) for v in BV], [], BF); bme.validate()
for p_ in bme.polygons: p_.use_smooth = True
helmet = bpy.data.objects.new('beret', bme); bpy.context.collection.objects.link(helmet)
hbn = arm.data.bones['mixamorig:Head']
helmet.parent = arm; helmet.parent_type = 'BONE'; helmet.parent_bone = hbn.name
helmet.matrix_parent_inverse = (arm.matrix_world @ hbn.matrix_local @ Matrix.Translation((0, hbn.length, 0))).inverted()
HM = bpy.data.materials.new('helmet18'); helmet.data.materials.append(HM)
for o in ([arm_h] if SAVE else [arm_h, arm_c]): bpy.data.objects.remove(o)

def _apply_clip():
    global fs, fe
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

if not SAVE: _apply_clip()

# ---- materials: flat emission from the painted textures; part-ID colour attribute ----
def load(p): return bpy.data.images.load(p, check_existing=True)
CT = os.environ['CHAR_TEX']
_sh = lambda k: CT + f'/{k}.png' if os.path.exists(CT + f'/{k}.png') else CT + f'/{k}_Diffuse.png'   # build session char dir or cc\\<name>\\
tex_for = {'Ch49_1001': _sh('Ch49_1001'), 'Ch49_1002': _sh('Ch49_1002'),
           'Ch18_1001': CT + '/face18.png'}
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
        it = nt.nodes.new('ShaderNodeTexImage'); it.image = load(CT + f'/id_{key[0]}_Diffuse.png' if os.path.exists(CT + f'/id_{key[0]}_Diffuse.png') else WS + f'anim/tex/id_{key[0]}_Diffuse.png')
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
def flat_mat_into(m, rgb, gid):
    m.use_nodes = True; nt = m.node_tree
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
def cel_mat_into(m, rgb, gid):
    # flat cartoon tones baked to the object: light from front-left-above in the helmet's own space
    flat_mat_into(m, rgb, gid); nt = m.node_tree
    eb = [n for n in nt.nodes if n.type == 'EMISSION'][0]
    geo = nt.nodes.new('ShaderNodeNewGeometry'); vt = nt.nodes.new('ShaderNodeVectorTransform')
    vt.vector_type = 'NORMAL'; vt.convert_from = 'WORLD'; vt.convert_to = 'OBJECT'
    nt.links.new(geo.outputs['Normal'], vt.inputs[0])
    dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
    L = Vector((-0.45, -0.6, 0.66)).normalized(); dot.inputs[1].default_value = L
    nt.links.new(vt.outputs[0], dot.inputs[0])
    lin = lambda c: (c / 255) ** 2.2
    base = [lin(c) for c in rgb]; shad = [lin(c * 0.66) for c in rgb]; high = [lin(min(255, c * 1.12)) for c in rgb]
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp; cr.interpolation = 'CONSTANT'
    cr.elements[0].position = 0.0; cr.elements[0].color = shad + [1]
    cr.elements[1].position = 0.48; cr.elements[1].color = base + [1]
    e3 = cr.elements.new(0.86); e3.color = high + [1]
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -1; mr.inputs['From Max'].default_value = 1
    nt.links.new(dot.outputs['Value'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], eb.inputs['Color'])
HAIRC = [float(x) for x in os.environ.get('HAIR', '48,38,32').split(',')]
flat_mat_into(bpy.data.materials['glasses18'], (44, 64, 52), 35)          # green-tinted shades
flat_mat_into(bpy.data.materials['hair18'], (36, 30, 26), 37)            # short black hair
cel_mat_into(HM, (58, 92, 48), 36)               # green beret
mats = {'glasses18', 'hair18', 'helmet18'}
for o in body_meshes + head_keep:
    for m in o.data.materials:
        if m and m.name not in mats: rebuild_material(m); mats.add(m.name)
def id_mode(on):
    for m in bpy.data.materials:
        if m.node_tree and 'IDSWITCH' in m.node_tree.nodes: m.node_tree.nodes['IDSWITCH'].inputs[0].default_value = 1.0 if on else 0.0

if SAVE:      # build session: empty-handed (no M-16 / pistol), no clip, no camera; textures packed in
    import re as _re
    for b_ in arm.data.bones: b_.name = _re.sub(r'mixamorig\d*:', 'mixamorig:', b_.name)
    for o_ in bpy.data.objects:
        for vg in getattr(o_, 'vertex_groups', []): vg.name = _re.sub(r'mixamorig\d*:', 'mixamorig:', vg.name)
    arm.animation_data_clear()
    for a_ in list(bpy.data.actions): bpy.data.actions.remove(a_)
    arm.name = 'Armature'; bpy.data.orphans_purge(do_recursive=True); bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=SAVE); sys.exit(0)
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
    bpy.ops.import_scene.gltf(filepath='/mnt/user-data/uploads/GI-Joe-Silent-Storm/GIJoe_XCOM_4x/Reference/models/guns/grunt_M-16.glb')
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
