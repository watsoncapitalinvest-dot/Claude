"""Render a soldier sheet from a ready-built character .blend (any body, not only Duke).

The design chat builds each character as a .blend: one armature (mixamorig: bones)
and skinned meshes whose materials are flat emission over painted textures (or flat
colours). This renders the same clips, facings, frames, camera and anchors as
render_soldier.py, so assemble_sheet.py takes the output unchanged.

    python3 render_char.py --blend joe.blend --clips stand=a.fbx,walk=b.fbx,... --out DIR
        [--frames 8] [--dirs 1,..,8] [--hair Ch33_hair]

The ID pass for the ink: red = a part id (material x limb, so a sleeve against the
chest gets its line), green = camera depth. Id 1 is reserved for hair by the ink.
"""
import bpy, sys, os, math, json
from mathutils import Vector
import numpy as np


def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


BLEND = arg('--blend')
CLIPS = dict(kv.split('=', 1) for kv in arg('--clips').split(','))
NF = int(arg('--frames', 8))
OUT = arg('--out')
DIRS = [int(x) for x in arg('--dirs', '1,2,3,4,5,6,7,8').split(',')]
HAIR = arg('--hair', '')
SHADE = '--shade' in sys.argv     # + <frame>_shade.png, the geometry pass for pen shading (factory_blend.py --shade)
RES = (512, 640)

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT'): bpy.data.objects.remove(o)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers) and not o.hide_render]
def fcurves(act):
    if hasattr(act, 'fcurves') and len(act.fcurves): return list(act.fcurves)
    out = []
    for L in act.layers:
        for st in L.strips:
            for cb in st.channelbags: out += list(cb.fcurves)
    return out


ACTIONS = {}
for name, path in CLIPS.items():
    before = set(bpy.data.objects); acts = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=path)
    act = [a for a in bpy.data.actions if a not in acts][0]
    act.use_fake_user = True; act.name = 'clip_' + name
    # clips downloaded with a skin carry their own prefix (mixamorig1:, mixamorig6: ...): point them at mixamorig:
    import re
    for fc in fcurves(act):
        dp = re.sub(r'mixamorig\d+:', 'mixamorig:', fc.data_path)
        if dp != fc.data_path: fc.data_path = dp
    ACTIONS[name] = act
    for o in [o for o in bpy.data.objects if o not in before]: bpy.data.objects.remove(o, do_unlink=True)


def apply_clip(clip, travel, fall=False):
    arm.animation_data_clear(); arm.animation_data_create()
    arm.animation_data.action = clip
    if hasattr(arm.animation_data, 'action_slot') and clip.slots: arm.animation_data.action_slot = clip.slots[0]
    if travel:
        for fc in fcurves(clip):
            if fc.data_path != 'pose.bones["mixamorig:Hips"].location': continue
            xs = np.array([k.co[0] for k in fc.keyframe_points]); ys = np.array([k.co[1] for k in fc.keyframe_points])
            a, b = np.polyfit(xs, ys, 1)
            if abs(a) * (xs.max() - xs.min()) > 30:
                for k in fc.keyframe_points:
                    k.co[1] -= a * (k.co[0] - xs[0]); k.handle_left[1] = k.co[1]; k.handle_right[1] = k.co[1]
    if fall:
        # a death keeps its drop (Y, vertical in the clip) but not its slide: the hips stay over the
        # tile, so the body lies across the cell instead of sliding out of the frame (it did, in facing 3)
        for fc in fcurves(clip):
            if fc.data_path == 'pose.bones["mixamorig:Hips"].location' and fc.array_index in (0, 2):
                k0 = fc.keyframe_points[0].co[1]
                for k in fc.keyframe_points:
                    k.co[1] = k0; k.handle_left[1] = k0; k.handle_right[1] = k0
    fs, fe = [int(x) for x in clip.frame_range]
    return fs, fe


def evaluated(o):
    dg = bpy.context.evaluated_depsgraph_get()
    me = o.evaluated_get(dg).to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co)
    o.evaluated_get(dg).to_mesh_clear()
    co = co.reshape(-1, 3)
    M = np.array(o.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


# rest height, with the first clip's first frame (feet on the floor)
arm.data.pose_position = 'REST'; bpy.context.view_layer.update()
H = max(evaluated(o)[:, 2].max() for o in meshes)
arm.data.pose_position = 'POSE'


# ---- part ids: material slot x limb ----
def part_of(bone):
    b = bone.replace('mixamorig:', '')
    if b in ('Head', 'Neck', 'HeadTop_End'): return 0
    if b.startswith('Left') and any(k in b for k in ('Arm', 'Hand', 'Shoulder')): return 2
    if b.startswith('Right') and any(k in b for k in ('Arm', 'Hand', 'Shoulder')): return 3
    if b.startswith('Left'): return 4
    if b.startswith('Right'): return 5
    return 1


matbase = {}
nxt = [3]
for o in meshes:
    for m in o.data.materials:
        if m and m.name not in matbase:
            if HAIR and HAIR in m.name: matbase[m.name] = None
            else: matbase[m.name] = nxt[0]; nxt[0] += 6
assert nxt[0] <= 40, 'too many materials for the 40-step id'
for o in meshes:
    gname = {vg.index: vg.name for vg in o.vertex_groups}
    me = o.data
    vpart = np.zeros(len(me.vertices), int)
    for v in me.vertices:
        if v.groups:
            g = max(v.groups, key=lambda g: g.weight); vpart[v.index] = part_of(gname.get(g.group, ''))
    attr = me.color_attributes.new('pid', 'FLOAT_COLOR', 'CORNER')
    for poly in me.polygons:
        ps = [vpart[me.loops[li].vertex_index] for li in poly.loop_indices]
        p = max(set(ps), key=ps.count)
        m = me.materials[poly.material_index] if me.materials else None
        base = matbase.get(m.name) if m else 3
        pid = 1 if base is None else base + p
        for li in poly.loop_indices: attr.data[li].color = (pid / 40.0, 0, 0, 1)


def add_idswitch(m):
    nt = m.node_tree; out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    if not out.inputs['Surface'].links: return
    beauty = out.inputs['Surface'].links[0].from_socket
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'pid'
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(at.outputs['Color'], sep.inputs[0])
    comb = nt.nodes.new('ShaderNodeCombineColor'); nt.links.new(sep.outputs[0], comb.inputs[0])
    camd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
    nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
    ei = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], ei.inputs['Color'])
    sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'; sw.inputs[0].default_value = 0.0
    nt.links.new(beauty, sw.inputs[1]); nt.links.new(ei.outputs[0], sw.inputs[2])
    nt.links.new(sw.outputs[0], out.inputs['Surface'])


for name in matbase:
    m = bpy.data.materials[name]
    # a blend built by the cast builders already carries its ID switch (garment-ID maps): keep it
    if m.node_tree and 'IDSWITCH' not in m.node_tree.nodes: add_idswitch(m)


def id_mode(on):
    for m in bpy.data.materials:
        if m.node_tree and 'IDSWITCH' in m.node_tree.nodes: m.node_tree.nodes['IDSWITCH'].inputs[0].default_value = 1.0 if on else 0.0


# ---- camera / render: identical to render_soldier.py ----
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.render.use_freestyle = False
sc.render.resolution_x, sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
sc.render.film_transparent = True; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.cycles.use_denoising = False
sc.cycles.max_bounces = 1; sc.cycles.transparent_max_bounces = 16
sc.world = bpy.data.worlds.new('w')
# Framed on a fixed reference height, not the man's own, so a tall man renders taller
# (Roadblock 1.90 m, Scarlett 1.70 m); lower and wider than render_soldier.py, whose
# frame cut the near boot off in facing 5.
REF = float(os.environ.get('REF_H', '1.80'))
tgt = bpy.data.objects.new('tgt', None); sc.collection.objects.link(tgt); tgt.location = (0, 0, 0.46 * REF)
cam_d = bpy.data.cameras.new('cam'); cam_d.type = 'ORTHO'; cam_d.ortho_scale = 1.26 * REF
cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
EL = math.radians(30)
FACING = {1: (0, 1), 2: (.707, .707), 3: (1, 0), 4: (.707, -.707), 5: (0, -1), 6: (-.707, -.707), 7: (-1, 0), 8: (-.707, .707)}


def place_camera(k):
    fx, fy = FACING[k]; alpha = math.atan2(fy, fx); phi = alpha + math.pi / 2
    a = Vector((math.sin(phi), math.cos(phi), 0))
    cam.location = tgt.location - a * 10 * math.cos(EL) + Vector((0, 0, 10 * math.sin(EL)))


if SHADE:
    # factory_blend.py --shade, unchanged: white diffuse override + one sun, re-aimed per facing
    SHADE_MAT = bpy.data.materials.new('shade_override'); SHADE_MAT.use_nodes = True
    _b = SHADE_MAT.node_tree.nodes['Principled BSDF']; _b.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1); _b.inputs['Roughness'].default_value = 1.0
    _sun = bpy.data.objects.new('key', bpy.data.lights.new('key', 'SUN')); _sun.data.energy = 3.0; _sun.data.angle = 0.05
    sc.collection.objects.link(_sun); _sun.hide_render = True


def shade_pass(path):
    """key light from the camera's upper-left-front, so fold shadows read the same in every facing"""
    fwd = (tgt.location - cam.location).normalized(); right = fwd.cross(Vector((0, 0, 1))).normalized(); upv = right.cross(fwd)
    ldir = (fwd * 0.55 - right * 0.55 + upv * 0.62).normalized()
    _sun.rotation_euler = ldir.to_track_quat('-Z', 'Y').to_euler(); _sun.hide_render = False
    wc = tuple(sc.world.color); bpy.context.view_layer.material_override = SHADE_MAT; sc.world.color = (0.05, 0.05, 0.05)
    sc.cycles.samples = 16; sc.cycles.filter_width = 1.0; sc.view_settings.view_transform = 'Standard'
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    bpy.context.view_layer.material_override = None; _sun.hide_render = True; sc.world.color = wc


HAND_IDX = {}
for o in meshes:
    gi = {vg.index: vg.name for vg in o.vertex_groups}
    for side in ('Left', 'Right'):
        idx = [v.index for v in o.data.vertices
               if sum(g.weight for g in v.groups if gi.get(g.group, '').startswith(f'mixamorig:{side}Hand')) > 0.6]
        if idx: HAND_IDX.setdefault(side, []).append((o, np.array(idx)))


def hand(side):
    return Vector(np.concatenate([evaluated(o)[idx] for o, idx in HAND_IDX[side]]).mean(0))


from bpy_extras.object_utils import world_to_camera_view


def px(co):
    v = world_to_camera_view(sc, cam, co); return [round(v.x * RES[0], 2), round((1 - v.y) * RES[1], 2)]


os.makedirs(OUT, exist_ok=True)
anchors = {}
for name, act in ACTIONS.items():
    fs, fe = apply_clip(act, any(w in name for w in ('walk', 'run')), name.startswith('death'))
    loop = not name.startswith('death')
    frames = [round(fs + (fe - fs) * i / (NF if loop else NF - 1)) for i in range(NF)]
    os.makedirs(f'{OUT}/{name}', exist_ok=True)
    for k in DIRS:
        place_camera(k)
        for i, f in enumerate(frames):
            sc.frame_set(f); bpy.context.view_layer.update()
            rh, lh = hand('Right'), hand('Left')
            hips = arm.matrix_world @ arm.pose.bones['mixamorig:Hips'].head
            anchors[f'{name}/{k}/{i}'] = {'rh': px(rh), 'lh': px(lh), 'feet': px(Vector((hips.x, hips.y, 0)))}
            id_mode(False); sc.cycles.samples = 8; sc.cycles.filter_width = 1.0; sc.view_settings.view_transform = 'Standard'
            sc.render.filepath = f'{OUT}/{name}/d{k}_f{i:02d}_beauty.png'; bpy.ops.render.render(write_still=True)
            id_mode(True); sc.cycles.samples = 1; sc.cycles.filter_width = 0.01; sc.view_settings.view_transform = 'Raw'
            sc.render.filepath = f'{OUT}/{name}/d{k}_f{i:02d}_id.png'; bpy.ops.render.render(write_still=True)
            if SHADE: shade_pass(f'{OUT}/{name}/d{k}_f{i:02d}_shade.png')
        print(name, 'direction', k, 'done', flush=True)
    json.dump({'frames': NF, 'dirs': DIRS, 'clips': list(ACTIONS), 'res': RES, 'h49': float(H), 'ref_h': REF, 'anchors': anchors},
              open(f'{OUT}/meta.json', 'w'))
