# Look editor behind the app's "Edit look" window: swap a model's skins, recolour garments, add/remove gear.
#   python dress.py --blend M.blend --list                       -> prints JSON: materials, gear
#   python dress.py --blend M.blend --spec SPEC.json --out O.blend
#   python dress.py --blend M.blend --template MATERIAL --out guide.png   -> the skin with the model's seams drawn on
#   python dress.py --blend M.blend --faceview front.png                   -> the face seen from the front (+ .json mapping)
#   SPEC may also hold "face": {photo, photo_pts, model_pts, strength, cartoon, match} - see apply_face()
#   and "body": {photo, points {shoulder_l..ankle_r: [x,y]}, back_photo, back_points, strength, cartoon, fit} - apply_body()
# SPEC: {"skins": {"<material>": "C:/path/skin.png"}, "colours": {"<material>": [r,g,b] | null}, "gear": [...] | absent}
#   colours null = back to the texture's own colours.  gear absent = leave gear as it is; [] = no gear.
#   props_add: [{file, attach: head|face|chest|back|hip_l|hip_r|hand_r|hand_l, size, up, forward, side (cm), turn, tilt, roll (deg)}]
#   props_remove: [object name]
#   gear entries: ["bandana",[r,g,b]] ["cap",[r,g,b]] ["dome",[r,g,b]] ["vest",[r,g,b],[r,g,b]] ["sunglasses",[r,g,b]] ["chain",[r,g,b]]
import bpy, bmesh, json, sys, math, os
import numpy as np
from mathutils import Vector


def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


BLEND = arg('--blend')
bpy.ops.wm.open_mainfile(filepath=BLEND)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
AW = arm.matrix_world
GEARMAT = 'cartel_gear'


def is_gear(o): return o.type == 'MESH' and (o.get('gear_kind') or o.name.startswith('Gear'))


def lin(c): return [((x / 255) / 12.92 if x / 255 <= 0.04045 else ((x / 255 + 0.055) / 1.055) ** 2.4) for x in c]


def srgb(v): return [int(round(255 * (12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055))) for x in v]


def body_meshes(): return [o for o in bpy.data.objects if o.type == 'MESH' and not is_gear(o)]


def mat_nodes(m):
    if not (m and m.use_nodes): return None, None
    tex = [n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE']
    em = [n for n in m.node_tree.nodes if n.type in ('EMISSION', 'BSDF_PRINCIPLED')]
    return (tex[0] if tex else None), (em[0] if em else None)


def colour_input(em): return em.inputs['Color'] if em.type == 'EMISSION' else em.inputs['Base Color']


def tint_of(m):
    """The recolour on a material, if it has one (the cartel builder's multiply-by-colour)."""
    tex, em = mat_nodes(m)
    if not em or not colour_input(em).links: return None
    n = colour_input(em).links[0].from_node
    if n.type == 'MIX' and n.blend_type == 'MULTIPLY' and n.data_type == 'RGBA': return n
    if n.type == 'MIX':                                   # hue-keyed recolour: Mix(select) fed by a multiply
        for i in n.inputs:
            for l in i.links:
                if l.from_node.type == 'MIX' and l.from_node.blend_type == 'MULTIPLY': return l.from_node
    return None


def materials():
    out, seen = [], set()
    for o in body_meshes():
        for m in o.data.materials:
            if not m or m.name in seen or m.name == GEARMAT: continue
            seen.add(m.name); tex, em = mat_nodes(m)
            t = tint_of(m)
            out.append({'name': m.name, 'image': tex.image.name if tex and tex.image else None,
                        'meshes': [x.name for x in body_meshes() if m.name in [mm.name for mm in x.data.materials if mm]],
                        'tinted': bool(t), 'tint': (list(m['tint_rgb']) if 'tint_rgb' in m else None)})
    return out


def mean_lum(m, img):
    w, h = img.size; px = np.array(img.pixels[:]).reshape(h, w, 4)
    uv = []
    for o in body_meshes():
        idx = [i for i, mm in enumerate(o.data.materials) if mm and mm.name == m.name]
        if not idx or not o.data.uv_layers.active: continue
        loops = o.data.uv_layers.active.data
        for p in o.data.polygons:
            if p.material_index in idx: uv += [loops[li].uv[:] for li in p.loop_indices]
    if not uv: return float((px[..., :3] @ np.array([0.2126, 0.7152, 0.0722])).mean())
    uv = np.array(uv); xs = np.clip((uv[:, 0] % 1) * w, 0, w - 1).astype(int); ys = np.clip((uv[:, 1] % 1) * h, 0, h - 1).astype(int)
    return float((px[ys, xs, :3] @ np.array([0.2126, 0.7152, 0.0722])).mean())


def clear_tint(m):
    tex, em = mat_nodes(m)
    if tex and em: m.node_tree.links.new(tex.outputs['Color'], colour_input(em))
    for k in ('tint_rgb', 'tint_ref'):
        if k in m: del m[k]


def set_tint(m, rgb):
    tex, em = mat_nodes(m)
    if not (tex and em and tex.image): return
    nt = m.node_tree
    t = tint_of(m)
    if not t:
        bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(tex.outputs['Color'], bw.inputs[0])
        t = nt.nodes.new('ShaderNodeMix'); t.data_type = 'RGBA'; t.blend_type = 'MULTIPLY'; t.clamp_result = True
        t.inputs['Factor'].default_value = 1.0
        nt.links.new(bw.outputs[0], t.inputs['A']); nt.links.new(t.outputs['Result'], colour_input(em))
    ref = mean_lum(m, tex.image); s = 1.0 / max(ref, 0.03)
    t.inputs['B'].default_value = [min(x * s, 8) for x in lin(rgb)] + [1]
    m['tint_rgb'] = list(rgb); m['tint_ref'] = ref


def set_skin(m, path):
    tex, em = mat_nodes(m)
    if not tex: return
    img = bpy.data.images.load(path, check_existing=False); img.pack()
    tex.image = img


# ---------------- gear (the cartel builder's pieces, measured off this model)
def measure():
    V, G, HV = [], [], []
    for o in body_meshes():
        names = {vg.index: vg.name.replace('mixamorig:', '') for vg in o.vertex_groups}
        hair = 'hair' in o.name.lower() or any('hair' in (m.name.lower() if m else '') for m in o.data.materials[:1])
        mw = o.matrix_world
        for v in o.data.vertices:
            g = max(v.groups, key=lambda g: g.weight).group if v.groups else -1
            if hair: HV.append(tuple(mw @ v.co))
            else: V.append(tuple(mw @ v.co)); G.append(names.get(g, ''))
    return np.array(V), np.array(G), (np.array(HV) if HV else np.zeros((0, 3)))


def build_gear(spec):
    for o in [o for o in bpy.data.objects if is_gear(o)]: bpy.data.objects.remove(o, do_unlink=True)
    for me in [m for m in bpy.data.meshes if m.users == 0]: bpy.data.meshes.remove(me)
    arm['gear_spec'] = json.dumps(spec)
    if not spec: return
    V, G, HAIRV = measure()
    bone_head = lambda b: AW @ arm.data.bones['mixamorig:' + b].head_local
    bone_tail = lambda b: AW @ arm.data.bones['mixamorig:' + b].tail_local
    head = V[G == 'Head']
    hz0 = head[:, 2].min(); hz1 = max(head[:, 2].max(), HAIRV[:, 2].max() if len(HAIRV) else 0)
    H = head[:, 2].max() - hz0; cx, cy = np.median(head[:, 0]), np.median(head[:, 1])
    GEAR = []

    def band(P, z0, z1): return P[(P[:, 2] >= z0) & (P[:, 2] <= z1)]

    def ellipse(P, z0, z1, m):
        s = band(P, z0, z1)
        if len(s) < 8: s = band(P, z0 - 0.02, z1 + 0.02)
        return np.abs(s[:, 0] - cx).max() + m, (cy - s[:, 1].min()) + m, (s[:, 1].max() - cy) + m

    def ring(ax, af, ab, z, n, drop=None):
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n; c = math.cos(a)
            y = cy - af * c if c > 0 else cy - ab * c
            pts.append((cx + ax * math.sin(a), y, z - (drop(c) if drop else 0)))
        return pts

    def tube(rows, rgb, bonefn, kind, cap_top=False):
        bm = bmesh.new(); n = len(rows[0]); vs = [[bm.verts.new(p) for p in r] for r in rows]
        for j in range(len(rows) - 1):
            for i in range(n): bm.faces.new((vs[j][i], vs[j][(i + 1) % n], vs[j + 1][(i + 1) % n], vs[j + 1][i]))
        if cap_top: bm.faces.new(vs[-1][::-1])
        GEAR.append((bm, rgb, bonefn, kind))

    hb = lambda p: 'Head'

    def bandana(rgb):
        rows = []
        for k, z in enumerate(np.linspace(hz0 + 0.10 * H, hz0 + 0.42 * H, 4)):
            ax, af, ab = ellipse(head, z - 0.01, z + 0.01, 0.009)
            rows.append(ring(ax, af, ab, z, 28, (lambda c: 0.07 * max(0, c) ** 2) if k == 0 else None))
        tube(rows, rgb, hb, 'bandana')

    def dome(rgb, zcut, m, kind, brim=0.0):
        ax = af = ab = 0
        for z in np.linspace(zcut, zcut + 0.25 * H, 5):
            a = ellipse(head, z - 0.012, z + 0.012, m); ax, af, ab = max(ax, a[0]), max(af, a[1]), max(ab, a[2])
        sz = (hz1 - zcut) + m * 0.8; rows = []
        for t in np.linspace(0, 1, 9):
            th = t * math.pi / 2; r = 0.0 if t == 1 else math.cos(th)
            rows.append(ring(ax * r, af * r, ab * r, zcut + sz * math.sin(th), 28))
        tube(rows, rgb, hb, kind)
        if brim:
            inner = ring(ax, af, ab, zcut, 28); outer = []
            for i, p in enumerate(inner):
                c = math.cos(2 * math.pi * i / 28)
                outer.append((p[0] + (p[0] - cx) * 0.15 * max(0, c), p[1] - brim * max(0, c) ** 1.5, p[2] - 0.006))
            tube([inner, outer], rgb, hb, kind)

    def sunglasses(rgb):
        ze = hz0 + 0.53 * H; ax, af, ab = ellipse(head, ze - 0.01, ze + 0.01, 0.007)
        bm = bmesh.new(); top, bot = [], []
        for i in range(13):
            a = -1.25 + 2.5 * i / 12; p = (cx + ax * math.sin(a), cy - af * math.cos(a))
            bot.append(bm.verts.new((p[0], p[1], ze - 0.016))); top.append(bm.verts.new((p[0], p[1], ze + 0.014)))
        for i in range(12): bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
        GEAR.append((bm, rgb, hb, 'sunglasses'))

    def chain(rgb):
        neck = V[(G == 'Neck') | (G == 'Spine2')]; zn = bone_head('Neck')[2] - 0.005
        s = neck[(neck[:, 2] > zn - 0.02) & (neck[:, 2] < zn + 0.02)]
        ax = np.abs(s[:, 0] - cx).max() * 0.75 + 0.012; af = (cy - s[:, 1].min()) + 0.012; ab = (s[:, 1].max() - cy) + 0.01
        r1 = ring(ax, af, ab, zn, 32, lambda c: 0.12 * max(0, c) ** 2)
        chest = V[G == 'Spine2']
        def front(p):
            near = chest[np.abs(chest[:, 2] - p[2]) < 0.02]
            return min(p[1], np.percentile(near[:, 1], 1) - 0.006) if (p[1] < cy and len(near)) else p[1]
        r1 = [(p[0], front(p), p[2]) for p in r1]; r2 = [(p[0], p[1] - 0.004, p[2] - 0.018) for p in r1]
        tube([r2, r1], rgb, lambda p: 'Spine2' if p[2] < zn - 0.03 else 'Neck', 'chain')

    def vest(rgb, prgb=None):
        prgb = prgb or [int(c * 0.8) for c in rgb]
        xs = abs(bone_head('LeftArm')[0] - cx) * 0.92
        torso = V[(np.abs(V[:, 0] - cx) < xs) & ~np.isin(G, ['Head', 'Neck'])]
        za = bone_head('Spine')[2] + 0.03; zb = bone_tail('Spine2')[2] - 0.035; rows = []
        for z in np.linspace(za, zb, 7):
            s = torso[np.abs(torso[:, 2] - z) < 0.015]
            rows.append(ring(np.abs(s[:, 0] - cx).max() + 0.018, (cy - s[:, 1].min()) + 0.022, (s[:, 1].max() - cy) + 0.018, z, 32))
        rows[-1] = [(cx + (p[0] - cx) * 0.8, p[1], p[2]) for p in rows[-1]]
        zs = [bone_head(b)[2] for b in ('Spine1', 'Spine2')]
        sp = lambda p: 'Spine' if p[2] < zs[0] else ('Spine1' if p[2] < zs[1] else 'Spine2')
        tube(rows, rgb, sp, 'vest')
        zp = za + 0.25 * (zb - za); s = torso[np.abs(torso[:, 2] - zp) < 0.02]; fy = s[:, 1].min() - 0.024
        for dx in (-0.075, 0.0, 0.075):
            bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
            for v in bm.verts: v.co = Vector((cx + dx + v.co.x * 0.062, fy - 0.016 + v.co.y * 0.034, zp + 0.02 + v.co.z * 0.085))
            GEAR.append((bm, prgb, sp, 'vest'))

    for g in spec:
        k, a = g[0], g[1:]
        if k == 'bandana': bandana(*a)
        elif k == 'cap': dome(a[0], hz0 + 0.66 * H, 0.014, 'cap', brim=0.075)
        elif k == 'dome': dome(a[0], hz0 + 0.60 * H, 0.022, 'dome')
        elif k == 'sunglasses': sunglasses(*a)
        elif k == 'chain': chain(*a)
        elif k == 'vest': vest(*a)

    gmat = bpy.data.materials.get(GEARMAT)
    if not gmat:
        gmat = bpy.data.materials.new(GEARMAT); gmat.use_nodes = True; nt = gmat.node_tree
        for n in list(nt.nodes): nt.nodes.remove(n)
        out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
        at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'gcol'
        geo = nt.nodes.new('ShaderNodeNewGeometry'); dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
        dot.inputs[1].default_value = Vector((0.35, -0.55, 0.76)).normalized()
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.2; mr.inputs['From Max'].default_value = 1.0
        mr.inputs['To Min'].default_value = 0.5; mr.inputs['To Max'].default_value = 1.05
        mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
        nt.links.new(geo.outputs['Normal'], dot.inputs[0]); nt.links.new(dot.outputs['Value'], mr.inputs['Value'])
        nt.links.new(at.outputs['Color'], mul.inputs['A']); nt.links.new(mr.outputs['Result'], mul.inputs['B'])
        nt.links.new(mul.outputs['Result'], em.inputs['Color']); nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    for idx, (bm, rgb, bonefn, kind) in enumerate(GEAR):
        me = bpy.data.meshes.new('gear%d' % idx); bm.normal_update(); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new('Gear%d' % idx, me); bpy.context.scene.collection.objects.link(ob)
        ob['gear_kind'] = kind; me.materials.append(gmat)
        ca = me.color_attributes.new('gcol', 'FLOAT_COLOR', 'CORNER'); c = lin(rgb) + [1]
        for l in ca.data: l.color = c
        for b in set(bonefn(tuple(v.co)) for v in me.vertices): ob.vertex_groups.new(name='mixamorig:' + b)
        for v in me.vertices: ob.vertex_groups['mixamorig:' + bonefn(tuple(v.co))].add([v.index], 1.0, 'REPLACE')
        ob.parent = arm; ob.matrix_parent_inverse = arm.matrix_world.inverted()
        mod = ob.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
        for p in me.polygons: p.use_smooth = True


ATTACH = {   # where a gear file goes: bone it rides on, how it is sized
    'head': 'Head', 'face': 'Head', 'chest': 'Spine2', 'back': 'Spine2', 'hip_l': 'Hips', 'hip_r': 'Hips',
    'hand_r': 'RightHand', 'hand_l': 'LeftHand'}


def to_emission(m):
    """A gear file's own material, made flat like the rest of the model (no lights in these renders): its colour or
    texture straight to an emission, with its own fixed outline part so it never counts against the material limit."""
    nt = m.node_tree; out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']
    out = out[0] if out else nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']
    src = None; col = (0.5, 0.5, 0.5, 1)
    if bsdf:
        bc = bsdf[0].inputs['Base Color']
        if bc.links: src = bc.links[0].from_socket
        else: col = tuple(bc.default_value)
    em = nt.nodes.new('ShaderNodeEmission')
    if src: nt.links.new(src, em.inputs['Color'])
    else: em.inputs['Color'].default_value = col
    # outline part: constant id (the 40-step id code 39) so the ink pass outlines it as one piece
    idc = nt.nodes.new('ShaderNodeEmission'); idc.inputs['Color'].default_value = (39 / 40.0, 0.5, 0, 1)
    sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'; sw.inputs[0].default_value = 0.0
    nt.links.new(em.outputs[0], sw.inputs[1]); nt.links.new(idc.outputs[0], sw.inputs[2])
    nt.links.new(sw.outputs[0], out.inputs['Surface'])


def add_prop(p):
    """p: {file, attach, size, up, forward, side, turn, tilt, roll}  (size x, cm, degrees)"""
    before = set(bpy.data.objects)
    f = p['file']; ext = os.path.splitext(f)[1].lower()
    if ext in ('.glb', '.gltf'): bpy.ops.import_scene.gltf(filepath=f)
    elif ext == '.fbx': bpy.ops.import_scene.fbx(filepath=f)
    elif ext == '.obj': bpy.ops.wm.obj_import(filepath=f)
    else: raise SystemExit('gear file must be .glb .gltf .fbx or .obj: ' + f)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    if not meshes: raise SystemExit('no mesh in ' + f)
    # one mesh, transforms applied, materials kept in order (no evaluated copies: editing those crashes Blender)
    bm = bmesh.new(); mats = []
    for o in meshes:
        me0 = o.data.copy(); me0.transform(o.matrix_world)
        base = len(mats); mats += list(me0.materials)
        for poly in me0.polygons: poly.material_index += base
        bm.from_mesh(me0); bpy.data.meshes.remove(me0)
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    name = os.path.splitext(os.path.basename(f))[0]
    me = bpy.data.meshes.new('prop_' + name); bm.to_mesh(me); bm.free()
    for m in mats:
        if m and 'IDSWITCH' not in m.node_tree.nodes: to_emission(m)
        me.materials.append(m)
    co = np.array([v.co[:] for v in me.vertices]); lo, hi = co.min(0), co.max(0); ctr = (lo + hi) / 2; ext3 = hi - lo
    # body measurements for the attach point
    V, G, HV = measure()
    bh = lambda b: AW @ arm.data.bones['mixamorig:' + b].head_local
    head = V[G == 'Head']; hz0, hz1 = head[:, 2].min(), head[:, 2].max(); H = hz1 - hz0
    cx, cy = float(np.median(head[:, 0])), float(np.median(head[:, 1]))
    hw = np.abs(head[:, 0] - cx).max() * 2
    xs = abs(bh('LeftArm')[0] - cx) * 0.92
    torso = V[(np.abs(V[:, 0] - cx) < xs) & np.isin(G, ['Spine1', 'Spine2'])]
    tw = np.abs(torso[:, 0] - cx).max() * 2 if len(torso) else 0.35
    a = p.get('attach', 'head')
    if a == 'head':   target, size_on, anchor = hw * 1.15, ext3[0], (cx, cy, hz0 + 0.62 * H, 'bottom')
    elif a == 'face': target, size_on, anchor = hw * 0.9, ext3[0], (cx, head[:, 1].min() - 0.01, hz0 + 0.5 * H, 'back')
    elif a == 'chest': target, size_on, anchor = tw, ext3[0], (cx, torso[:, 1].min() - 0.005, bh('Spine2')[2], 'back')
    elif a == 'back': target, size_on, anchor = tw * 0.9, ext3[0], (cx, torso[:, 1].max() + 0.005, bh('Spine2')[2], 'front')
    elif a in ('hip_l', 'hip_r'):
        sx = 1 if a == 'hip_l' else -1; target, size_on = 0.25, ext3[2]
        anchor = (cx + sx * xs * 0.95, cy, bh('Hips')[2] - 0.05, 'centre')
    else:
        hand = bh('RightHand' if a == 'hand_r' else 'LeftHand'); target, size_on = 0.6, max(ext3)
        anchor = (hand[0], hand[1], hand[2], 'centre')
    k = (target / max(size_on, 1e-6)) * float(p.get('size', 1.0))
    co = (co - ctr) * k; ext3 = ext3 * k
    def rot(co, axis, deg):
        r = math.radians(float(deg))
        if not r: return co
        c, s_ = math.cos(r), math.sin(r); i, j = {'x': (1, 2), 'y': (0, 2), 'z': (0, 1)}[axis]
        a, b = co[:, i].copy(), co[:, j].copy(); co[:, i], co[:, j] = a * c - b * s_, a * s_ + b * c
        return co
    co = rot(co, 'x', p.get('tilt', 0)); co = rot(co, 'y', p.get('roll', 0)); co = rot(co, 'z', p.get('turn', 0))
    ext3 = co.max(0) - co.min(0)
    ax, ay, az, side = anchor
    off = np.array([ax, ay, az], float)
    if side == 'bottom': off[2] += ext3[2] / 2
    elif side == 'back': off[1] -= ext3[1] / 2          # sits in front of the surface (front is -Y)
    elif side == 'front': off[1] += ext3[1] / 2
    off += np.array([float(p.get('side', 0)), -float(p.get('forward', 0)), float(p.get('up', 0))]) / 100.0
    co = co + off
    for v, c in zip(me.vertices, co): v.co = c
    ob = bpy.data.objects.new('Prop_' + name, me); bpy.context.scene.collection.objects.link(ob)
    ob['gear_prop'] = json.dumps(p); bone = ATTACH.get(a, 'Head')
    vg = ob.vertex_groups.new(name='mixamorig:' + bone); vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    ob.parent = arm; ob.matrix_parent_inverse = arm.matrix_world.inverted()
    mod = ob.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
    return ob.name


def props_now():
    return [{'name': o.name, **json.loads(o['gear_prop'])} for o in bpy.data.objects if o.get('gear_prop')]


def template(mat_name, out_png):
    """The skin as it is, with the model's seams drawn on - the guide an AI paints over."""
    from PIL import Image, ImageDraw
    m = bpy.data.materials[mat_name]; tex, _ = mat_nodes(m)
    w, h = tex.image.size
    px = (np.array(tex.image.pixels[:]).reshape(h, w, 4)[::-1] * 255).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(px, 'RGBA').convert('RGB'); d = ImageDraw.Draw(im)
    for o in body_meshes():
        idx = [i for i, mm in enumerate(o.data.materials) if mm and mm.name == mat_name]
        if not idx or not o.data.uv_layers.active: continue
        uv = o.data.uv_layers.active.data
        for poly in o.data.polygons:
            if poly.material_index not in idx: continue
            pts = [((uv[li].uv[0] % 1) * w, (1 - uv[li].uv[1] % 1) * h) for li in poly.loop_indices]
            d.line(pts + [pts[0]], fill=(255, 0, 255), width=1)
    im.save(out_png)


# ---------------- face from photo
def face_tris():
    """Front-facing head triangles of the skin: per triangle its UVs (texture pixels), rest-pose world points,
    facing (how much it looks to the front, -Y), and the material that holds the face."""
    rows = []
    for o in body_meshes():
        if any('hair' in (m.name.lower() if m else '') for m in o.data.materials[:1]) or 'hair' in o.name.lower(): continue
        names = {vg.index: vg.name.replace('mixamorig:', '') for vg in o.vertex_groups}
        if not o.data.uv_layers.active: continue
        me = o.data; me.calc_loop_triangles(); uv = me.uv_layers.active.data; mw = o.matrix_world
        nm = mw.to_3x3().normalized()
        def dom(vi):
            gs = me.vertices[vi].groups
            return names.get(max(gs, key=lambda g: g.weight).group, '') if gs else ''
        for t in me.loop_triangles:
            if not all(dom(v) in ('Head', 'HeadTop_End') for v in t.vertices): continue
            m = me.materials[t.material_index] if me.materials else None
            if not m: continue
            tex, _ = mat_nodes(m)
            if not (tex and tex.image): continue
            n = (nm @ t.normal).normalized(); facing = -n.y
            if facing < 0.15: continue
            rows.append((m.name, [uv[l].uv[:] for l in t.loops], [(mw @ me.vertices[v].co)[:] for v in t.vertices], facing))
    if not rows: raise SystemExit('no front-facing head found on this model')
    count = {}
    for r in rows: count[r[0]] = count.get(r[0], 0) + 1
    mat = max(count, key=count.get)
    rows = [r for r in rows if r[0] == mat]
    return mat, np.array([r[1] for r in rows]), np.array([r[2] for r in rows]), np.array([r[3] for r in rows])


def face_texels(mat):
    """Every skin texel on the front of the head: texel x,y, world x,z (and y for depth), facing."""
    m = bpy.data.materials[mat]; tex, _ = mat_nodes(m); W, H = tex.image.size
    _, UV, P, F = face_tris()
    out = []
    for uv, p, f in zip(UV, P, F):
        t = np.c_[uv[:, 0] * W, (1 - uv[:, 1]) * H]               # texture pixel coords (row 0 = top)
        x0, y0 = np.floor(t.min(0)).astype(int); x1, y1 = np.ceil(t.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, W)), np.arange(max(y0, 0), min(y1 + 1, H)))
        if xs.size == 0: continue
        px = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
        a, b, c = t; v0, v1 = b - a, c - a; d = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(d) < 1e-9: continue
        r = px - a; l1 = (r[:, 0] * v1[1] - v1[0] * r[:, 1]) / d; l2 = (v0[0] * r[:, 1] - r[:, 0] * v0[1]) / d; l0 = 1 - l1 - l2
        ins = (l0 >= -1e-3) & (l1 >= -1e-3) & (l2 >= -1e-3)
        if not ins.any(): continue
        w3 = np.c_[l0[ins], l1[ins], l2[ins]]; wp = w3 @ p
        out.append(np.c_[xs.ravel()[ins], ys.ravel()[ins], wp[:, 0], wp[:, 2], wp[:, 1], np.full(ins.sum(), f)])
    return tex, np.vstack(out)


def faceview(out_png):
    """The model's face seen from the front, built from the skin texels (so clicks map exactly to the texture)."""
    from PIL import Image
    mat, *_ = face_tris(); tex, T = face_texels(mat); W, H = tex.image.size
    img = (np.array(tex.image.pixels[:]).reshape(H, W, 4)[::-1] * 255).clip(0, 255).astype(np.uint8)
    x, z = T[:, 2], T[:, 3]; x0, x1, z0, z1 = x.min(), x.max(), z.min(), z.max()
    size = 360; s = (x1 - x0) / size; h = int((z1 - z0) / s) + 1
    view = np.zeros((h, size + 1, 4), np.uint8); depth = np.full((h, size + 1), 1e9)
    u = ((x - x0) / s).astype(int); v = ((z1 - z) / s).astype(int)
    order = np.argsort(-T[:, 4])                      # far first, near last wins (front is -Y = smaller y)
    for i in order:
        view[v[i], u[i], :3] = img[int(T[i, 1]), int(T[i, 0]), :3]; view[v[i], u[i], 3] = 255
    im = Image.fromarray(view, 'RGBA')
    from PIL import ImageFilter
    filled = im
    for k in (3, 5):                                   # close the speckle where the texture is spread thin
        grown = filled.filter(ImageFilter.MaxFilter(k)); grown.alpha_composite(filled); filled = grown
    filled.save(out_png)
    json.dump({'material': mat, 'x0': float(x0), 'z1': float(z1), 's': float(s)}, open(out_png + '.json', 'w'))


def cartoon(im, level):
    from PIL import ImageFilter
    if level <= 0: return im
    k = {1: 3, 2: 5, 3: 7}.get(int(level), 5); n = {1: 24, 2: 16, 3: 10}.get(int(level), 16)
    im = im.filter(ImageFilter.MedianFilter(k))
    return im.quantize(colors=n, method=0).convert('RGB')


def apply_face(f):
    """f: {photo, photo_pts [[x,y]x3: left eye, right eye, mouth], model_pts [[x,z]x3 world], strength, cartoon,
    match}. Maps the photo onto the face texels through the affine that takes model points to photo points."""
    from PIL import Image
    mat, *_ = face_tris(); tex, T = face_texels(mat); W, H = tex.image.size
    img = np.array(tex.image.pixels[:]).reshape(H, W, 4)[::-1].copy()          # float 0..1, row 0 = top
    photo = cartoon(Image.open(f['photo']).convert('RGB'), f.get('cartoon', 2))
    ph = np.asarray(photo).astype(np.float32) / 255.0; PH, PW = ph.shape[:2]
    Q = np.array(f['model_pts'], float); P = np.array(f['photo_pts'], float)
    A = np.linalg.solve(np.c_[Q, np.ones(3)], P)                               # [x z 1] @ A = [px py]
    eye_c = Q[:2].mean(0); mouth = Q[2]; ed = np.linalg.norm(Q[0] - Q[1]); em = np.linalg.norm(eye_c - mouth)
    ctr = eye_c + (mouth - eye_c) * 0.45
    rx, rz = ed * 1.05, em * 1.75
    d = np.sqrt(((T[:, 2] - ctr[0]) / rx) ** 2 + ((T[:, 3] - ctr[1]) / rz) ** 2)
    mask = np.clip((1.0 - d) / 0.35, 0, 1) * np.clip((T[:, 5] - 0.15) / 0.35, 0, 1)
    uv = np.c_[T[:, 2], T[:, 3], np.ones(len(T))] @ A
    ok = (uv[:, 0] >= 0) & (uv[:, 0] < PW - 1) & (uv[:, 1] >= 0) & (uv[:, 1] < PH - 1) & (mask > 0)
    T, uv, mask = T[ok], uv[ok], mask[ok]
    x0 = np.floor(uv[:, 0]).astype(int); y0 = np.floor(uv[:, 1]).astype(int); fx = uv[:, 0] - x0; fy = uv[:, 1] - y0
    col = (ph[y0, x0] * ((1 - fx) * (1 - fy))[:, None] + ph[y0, x0 + 1] * (fx * (1 - fy))[:, None] +
           ph[y0 + 1, x0] * ((1 - fx) * fy)[:, None] + ph[y0 + 1, x0 + 1] * (fx * fy)[:, None])
    tx, ty = T[:, 0].astype(int), T[:, 1].astype(int)
    old = img[ty, tx, :3]
    # skin match: shift the photo's average toward the body's average over the same area
    wsum = mask.sum() + 1e-6
    shift = ((old * mask[:, None]).sum(0) - (col * mask[:, None]).sum(0)) / wsum
    col = np.clip(col + shift * float(f.get('match', 0.6)), 0, 1)
    a = (mask * float(f.get('strength', 0.9)))[:, None]
    img[ty, tx, :3] = old * (1 - a) + col * a
    new = bpy.data.images.new(tex.image.name.split('.')[0] + '_face', W, H, alpha=True)
    new.pixels[:] = img[::-1].ravel(); new.pack(); tex.image = new
    m = bpy.data.materials[mat]; m['face_from'] = os.path.basename(f['photo'])


# ---------------- whole body (clothes) from photo
# photo points, picture-left first: shoulder, shoulder, elbow, elbow, wrist, wrist, hip, hip, knee, knee, ankle, ankle
BODY_POINTS = ['shoulder_l', 'shoulder_r', 'elbow_l', 'elbow_r', 'wrist_l', 'wrist_r',
               'hip_l', 'hip_r', 'knee_l', 'knee_r', 'ankle_l', 'ankle_r']


def model_joints(back=False):
    """The model's joints in its front view (world x, z), named by picture side. Seen from the front, the picture's
    left is the character's RIGHT; seen from behind it is his LEFT."""
    bh = lambda b: AW @ arm.data.bones['mixamorig:' + b].head_local
    L, R = ('Right', 'Left') if not back else ('Left', 'Right')
    J = {'shoulder_l': bh(L + 'Arm'), 'shoulder_r': bh(R + 'Arm'), 'elbow_l': bh(L + 'ForeArm'), 'elbow_r': bh(R + 'ForeArm'),
         'wrist_l': bh(L + 'Hand'), 'wrist_r': bh(R + 'Hand'), 'hip_l': bh(L + 'UpLeg'), 'hip_r': bh(R + 'UpLeg'),
         'knee_l': bh(L + 'Leg'), 'knee_r': bh(R + 'Leg'), 'ankle_l': bh(L + 'Foot'), 'ankle_r': bh(R + 'Foot')}
    return {k: np.array([v.x, v.z]) for k, v in J.items()}


def body_texels():
    """Every skin texel of the body (not hair, not gear): image, texel x/y, world xyz, facing (+front), bone."""
    per_img = {}
    for o in body_meshes():
        if 'hair' in o.name.lower() or any('hair' in (m.name.lower() if m else '') for m in o.data.materials[:1]): continue
        if not o.data.uv_layers.active: continue
        names = {vg.index: vg.name.replace('mixamorig:', '') for vg in o.vertex_groups}
        me = o.data; me.calc_loop_triangles(); uvl = me.uv_layers.active.data; mw = o.matrix_world; nm = mw.to_3x3().normalized()
        dom = [names.get(max(v.groups, key=lambda g: g.weight).group, '') if v.groups else '' for v in me.vertices]
        co = np.array([(mw @ v.co)[:] for v in me.vertices])
        for t in me.loop_triangles:
            m = me.materials[t.material_index] if me.materials else None
            if not m or 'hair' in m.name.lower(): continue
            tex, _ = mat_nodes(m)
            if not (tex and tex.image): continue
            bs = [dom[v] for v in t.vertices]; bone = max(set(bs), key=bs.count)
            img = tex.image; W, H = img.size
            uv = np.array([uvl[l].uv[:] for l in t.loops]); tp = np.c_[uv[:, 0] % 1 * W, (1 - uv[:, 1] % 1) * H]
            p = co[list(t.vertices)]; facing = -(nm @ t.normal).normalized().y
            x0, y0 = np.floor(tp.min(0)).astype(int); x1, y1 = np.ceil(tp.max(0)).astype(int)
            xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, W)), np.arange(max(y0, 0), min(y1 + 1, H)))
            if xs.size == 0: continue
            px = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]; a, b, c = tp; v0, v1 = b - a, c - a
            d = v0[0] * v1[1] - v1[0] * v0[1]
            if abs(d) < 1e-9: continue
            r = px - a; l1 = (r[:, 0] * v1[1] - v1[0] * r[:, 1]) / d; l2 = (v0[0] * r[:, 1] - r[:, 0] * v0[1]) / d; l0 = 1 - l1 - l2
            ins = (l0 >= -1e-3) & (l1 >= -1e-3) & (l2 >= -1e-3)
            if not ins.any(): continue
            wp = np.c_[l0[ins], l1[ins], l2[ins]] @ p
            per_img.setdefault(img.name, []).append(
                (np.c_[xs.ravel()[ins], ys.ravel()[ins], wp, np.full(ins.sum(), facing)], bone))
    return per_img


def region(bone):
    b = bone
    for side in ('Left', 'Right'):
        if b.startswith(side):
            rest = b[len(side):]
            if rest == 'Arm': return side, 'upper_arm'
            if rest == 'ForeArm': return side, 'forearm'
            if rest.startswith('Hand'): return side, 'hand'
            if rest == 'UpLeg': return side, 'thigh'
            if rest == 'Leg': return side, 'shin'
            if rest.startswith('Foot') or rest.startswith('Toe'): return side, 'foot'
            if rest == 'Shoulder': return None, 'torso'
    return None, 'torso'                      # Hips, Spine*, Neck, Head (the face feature refines the head)


SEG = {'upper_arm': ('shoulder', 'elbow', 1.0), 'forearm': ('elbow', 'wrist', 1.0), 'hand': ('wrist', None, 0.4),
       'thigh': ('hip', 'knee', 1.0), 'shin': ('knee', 'ankle', 1.0), 'foot': ('ankle', None, 0.18)}


def bleed(ph):
    """Find the person against a plain background (the border's colour) and paint every background pixel with the
    nearest person pixel, so a sample that lands just outside the outline picks up clothes, not the wall."""
    from scipy import ndimage
    bw = max(4, min(ph.shape[:2]) // 60)
    border = np.concatenate([ph[:bw].reshape(-1, 3), ph[-bw:].reshape(-1, 3), ph[:, :bw].reshape(-1, 3), ph[:, -bw:].reshape(-1, 3)])
    bg = np.median(border, 0)
    diff = np.abs(ndimage.uniform_filter(ph, size=(5, 5, 1)) - bg).max(2)
    person = diff > 0.10
    person = ndimage.binary_opening(person, iterations=2); person = ndimage.binary_closing(person, iterations=3)
    lab, n = ndimage.label(person)
    if n == 0: return ph
    sizes = ndimage.sum(person, lab, range(1, n + 1)); person = lab == (1 + int(np.argmax(sizes)))
    person = ndimage.binary_fill_holes(person)
    if person.mean() > 0.95 or person.mean() < 0.02: return ph          # no clear background: leave the photo as is
    core = ndimage.binary_erosion(person, iterations=max(3, bw // 2))   # borrow colour from well inside the outline
    if core.mean() < 0.01: core = person
    _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
    return ph[iy, ix]


def apply_body(spec):
    """spec: {photo, points {name: [x,y] photo px}, back_photo?, back_points?, strength, cartoon, fit}"""
    from PIL import Image
    def load(path, pts, back):
        im = cartoon(Image.open(path).convert('RGB'), spec.get('cartoon', 1))
        ph = bleed(np.asarray(im).astype(np.float32) / 255.0)
        P = {k: np.array([v[0], -v[1]], float) for k, v in pts.items()}          # photo, y up
        return ph, P, model_joints(back)
    views = [load(spec['photo'], spec['points'], False)]
    if spec.get('back_photo'): views.append(load(spec['back_photo'], spec['back_points'], True))
    per_img = body_texels(); fit = float(spec.get('fit', 0.85)); strength = float(spec.get('strength', 1.0))

    def sample(ph, uvY):
        PH, PW = ph.shape[:2]; x = np.clip(uvY[:, 0], 0, PW - 1.001); y = np.clip(-uvY[:, 1], 0, PH - 1.001)
        x0, y0 = x.astype(int), y.astype(int); fx, fy = (x - x0)[:, None], (y - y0)[:, None]
        return (ph[y0, x0] * (1 - fx) * (1 - fy) + ph[y0, x0 + 1] * fx * (1 - fy) + ph[y0 + 1, x0] * (1 - fx) * fy + ph[y0 + 1, x0 + 1] * fx * fy)

    def map_view(view, xz, bone_key, hw):
        ph, P, J = view
        side, reg = bone_key
        if reg == 'torso':
            Q = np.array([J['shoulder_l'], J['shoulder_r'], J['hip_l'], J['hip_r']])
            Pp = np.array([P['shoulder_l'], P['shoulder_r'], P['hip_l'], P['hip_r']])
            A, *_ = np.linalg.lstsq(np.c_[Q, np.ones(4)], Pp, rcond=None)
            return np.c_[xz, np.ones(len(xz))] @ A
        # picture side of this limb: front view - character Right is picture left; back view - character Left
        pic = ('l' if side == 'Right' else 'r') if view is views[0] or not spec.get('back_photo') else ('l' if side == 'Left' else 'r')
        j0, j1, ext = SEG[reg]
        a, A_ = J[j0 + '_' + pic], P[j0 + '_' + pic]
        if j1: b, B_ = J[j1 + '_' + pic], P[j1 + '_' + pic]
        else:
            prev = {'wrist': 'elbow', 'ankle': 'knee'}[j0]
            b = a + (a - J[prev + '_' + pic]) * ext; B_ = A_ + (A_ - P[prev + '_' + pic]) * ext
        d = b - a; L2 = max(d @ d, 1e-9); t = ((xz - a) @ d) / L2
        n = np.array([-d[1], d[0]]) / np.sqrt(L2); sl = (xz - a - np.outer(t, d)) @ n
        D = B_ - A_; N = np.array([-D[1], D[0]]) / max(np.linalg.norm(D), 1e-9)
        sc = np.linalg.norm(P['shoulder_l'] - P['ankle_l']) / max(np.linalg.norm(J['shoulder_l'] - J['ankle_l']), 1e-9)
        return A_ + np.outer(t, D) + np.outer(np.clip(sl / max(hw, 1e-4), -1, 1) * hw * sc * fit, N)

    touched = set()
    for img_name, chunks in per_img.items():
        img = bpy.data.images[img_name]; W, H = img.size
        px = np.array(img.pixels[:]).reshape(H, W, 4)[::-1].copy()
        groups = {}
        for arr, bone in chunks: groups.setdefault(region(bone), []).append(arr)
        for key, arrs in groups.items():
            if key[1] == 'hand': continue                           # the model keeps its own hands (skin)
            T = np.vstack(arrs); xz = T[:, [2, 4]]
            if key[1] != 'torso':                                   # this limb's half-width on the model
                j0, j1, ext = SEG[key[1]]; J = views[0][2]; pic = 'l' if key[0] == 'Right' else 'r'
                a = J[j0 + '_' + pic]
                b = J[j1 + '_' + pic] if j1 else a + (a - J[{'wrist': 'elbow', 'ankle': 'knee'}[j0] + '_' + pic]) * ext
                d = b - a; n = np.array([-d[1], d[0]]) / max(np.linalg.norm(d), 1e-9)
                t = ((xz - a) @ d) / max(d @ d, 1e-9); hw = np.percentile(np.abs((xz - a - np.outer(t, d)) @ n), 90)
            else: hw = 1.0
            front = sample(views[0][0], map_view(views[0], xz, key, hw))
            if len(views) > 1:
                back = sample(views[1][0], map_view(views[1], xz, key, hw))
                wf = np.clip((T[:, 5] + 0.2) / 0.4, 0, 1)[:, None]; col = front * wf + back * (1 - wf)
            else: col = front
            tx, ty = T[:, 0].astype(int), T[:, 1].astype(int)
            px[ty, tx, :3] = px[ty, tx, :3] * (1 - strength) + col * strength
        new = bpy.data.images.new(img_name.split('.')[0] + '_body', W, H, alpha=True)
        new.pixels[:] = px[::-1].ravel(); new.pack()
        for m in bpy.data.materials:
            tex, _ = mat_nodes(m)
            if tex and tex.image and tex.image.name == img_name:
                tex.image = new; clear_tint(m); touched.add(m.name)
    return sorted(touched)


def gear_now():
    if 'gear_spec' in arm: return json.loads(arm['gear_spec'])
    kinds = sorted(set(o.get('gear_kind', 'unknown') for o in bpy.data.objects if is_gear(o)))
    return [[k] for k in kinds]


if '--faceview' in sys.argv:
    faceview(arg('--faceview')); print('DRESS_OK', arg('--faceview')); sys.exit(0)

if '--template' in sys.argv:
    template(arg('--template'), arg('--out')); print('DRESS_OK', arg('--out')); sys.exit(0)

if '--list' in sys.argv:
    print('DRESS_JSON ' + json.dumps({'materials': materials(), 'gear': gear_now(), 'props': props_now()}))
    sys.exit(0)

spec = json.load(open(arg('--spec')))
for name, path in spec.get('skins', {}).items():
    m = bpy.data.materials.get(name)
    if m and path: set_skin(m, path)
for name, rgb in spec.get('colours', {}).items():
    m = bpy.data.materials.get(name)
    if not m: continue
    if rgb is None: clear_tint(m)
    else: set_tint(m, rgb)
if spec.get('body'): apply_body(spec['body'])
if spec.get('face'): apply_face(spec['face'])
if 'gear' in spec: build_gear(spec['gear'])
for n in spec.get('props_remove', []):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o, do_unlink=True)
for p in spec.get('props_add', []): add_prop(p)
out = arg('--out', BLEND)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print('DRESS_OK', out)
