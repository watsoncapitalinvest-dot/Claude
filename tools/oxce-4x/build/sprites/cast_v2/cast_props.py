"""Props for the cartoon cast: headgear bound to the Head bone and simple weapons. Flat cartoon materials with ID output.
 BUILD SESSION COPY of cast_v2_1p6cm.zip scripts/props/cast_props.py (CAST, 12 Nov). Changes: paths re-pointed (env CAST_V2 = the
 unzipped cast_v2_1p6cm folder; swell_ch49 / bandolier_fit from ../greenshirts, the same files as the kits) and
 --save-blend PATH: save the built man for render_char.py and exit before the render loop - empty-handed (no gun,
 no pistol), no clip, no camera, bone-parented props re-bound as skin (Armature modifier), textures packed.
"""
import os, bpy, bmesh, math, struct, sys, numpy as np
from mathutils import Vector, Matrix
CAST_V2 = os.environ.get('CAST_V2', '/tmp/claude-0/ws/cast_v2/cast_v2_1p6cm')
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, '..', 'cast'))      # make_beret (only for model != 'brim')

def _lin(c): return (c / 255) ** 2.2

def flat_mat(name, rgb, gid):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    o_ = nt.nodes.new('ShaderNodeOutputMaterial'); eb = nt.nodes.new('ShaderNodeEmission')
    eb.inputs['Color'].default_value = tuple(_lin(c) for c in rgb) + (1,)
    comb = nt.nodes.new('ShaderNodeCombineColor'); comb.inputs[0].default_value = gid / 40.0
    camd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
    nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
    ei = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], ei.inputs['Color'])
    sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'
    nt.links.new(eb.outputs[0], sw.inputs[1]); nt.links.new(ei.outputs[0], sw.inputs[2]); nt.links.new(sw.outputs[0], o_.inputs['Surface'])
    return m

def cel_mat(name, rgb, gid):
    """Flat base + one shadow (x0.66) + one highlight (x1.12), light fixed in the object's own space."""
    m = flat_mat(name, rgb, gid); nt = m.node_tree
    eb = [n for n in nt.nodes if n.type == 'EMISSION'][0]
    geo = nt.nodes.new('ShaderNodeNewGeometry'); vt = nt.nodes.new('ShaderNodeVectorTransform')
    vt.vector_type = 'NORMAL'; vt.convert_from = 'WORLD'; vt.convert_to = 'OBJECT'
    nt.links.new(geo.outputs['Normal'], vt.inputs['Vector'])     # build session: inputs[0] is the hidden LightIndex in Blender 5.3 - the normal never arrived, every cel prop came out one flat tone
    dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
    dot.inputs[1].default_value = Vector((-0.45, -0.6, 0.66)).normalized()
    nt.links.new(vt.outputs[0], dot.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp; cr.interpolation = 'CONSTANT'
    cr.elements[0].position = 0.0; cr.elements[0].color = [_lin(c * 0.66) for c in rgb] + [1]
    cr.elements[1].position = 0.48; cr.elements[1].color = [_lin(c) for c in rgb] + [1]
    e3 = cr.elements.new(0.86); e3.color = [_lin(min(255, c * 1.12)) for c in rgb] + [1]
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -1; mr.inputs['From Max'].default_value = 1
    nt.links.new(dot.outputs['Value'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], eb.inputs['Color'])
    return m

def bind_skin(o, arm, bone):
    """Rigid-skin a prop to one bone (armature modifier, weight 1) - follows the bone exactly like the body does,
    including a non-uniform build scale on the armature's root (bone parenting skews there)."""
    vg = o.vertex_groups.new(name=bone); vg.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    m = o.modifiers.new('arm', 'ARMATURE'); m.object = arm

def bind(o, arm, bone):
    b = arm.data.bones[bone]
    o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = b.name
    o.matrix_parent_inverse = (arm.matrix_world @ b.matrix_local @ Matrix.Translation((0, b.length, 0))).inverted()

def _obj(name, V, F, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in V], [], F); me.validate()
    for p in me.polygons: p.use_smooth = smooth
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); return o

HELMET_STL = os.path.join(CAST_V2, 'assets', 'Modern_Army_Helmet.stl')
def helmet(Wn, arm, rgb, scale=1.33, back=0.038, up=0.035, gid=36):
    raw = open(HELMET_STL, 'rb').read(); n = struct.unpack('<I', raw[80:84])[0]
    T = np.frombuffer(raw[84:84 + n * 50], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))['v'].reshape(-1, 3).astype(np.float64)
    o = _obj('helmet', T, [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(n)], smooth=False)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.05); bpy.ops.object.mode_set(mode='OBJECT')
    dm = o.modifiers.new('dec', 'DECIMATE'); dm.ratio = 0.06; bpy.ops.object.modifier_apply(modifier='dec'); o.select_set(False)
    for p in o.data.polygons: p.use_smooth = True
    HV = np.array([v.co[:] for v in o.data.vertices]); lo, hi = HV.min(0), HV.max(0)
    top = Wn[:, 2].max(); sk = Wn[Wn[:, 2] > top - 0.06]
    sc = scale * (sk[:, 0].max() - sk[:, 0].min()) / (hi[0] - lo[0])
    tgt = Vector((float(sk[:, 0].mean()), float(sk[:, 1].mean()) + back, float(top) + up))
    o.data.transform(Matrix.Translation(tgt) @ Matrix.Scale(sc, 4) @ Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -hi[2])))
    o.data.materials.append(cel_mat('helmet_mat', rgb, gid)); bind_skin(o, arm, 'mixamorig:Head'); return o

def beret(Wn, arm, rgb, band_below_top, side=-1.0, gid=36, model='brim', fit=None, **kw):
    top = float(Wn[:, 2].max())
    if model == 'brim':
        from beret_fit import fit_beret
        V, F = fit_beret(Wn, **(fit or {}))
    else:
        from beret import make_beret
        V, F, _ = make_beret(Wn[Wn[:, 2] > top - 0.2], top - band_below_top, side=side, **kw)
    o = _obj('beret', V, F); o.data.materials.append(cel_mat('beret_mat', rgb, gid)); bind(o, arm, 'mixamorig:Head'); return o

def headset(Wn, arm, rgb=(40, 40, 44), gid=38):
    """Band over the top of the head, two ear cups, a mic boom from the left cup to the mouth."""
    top = float(Wn[:, 2].max()); hy = float(Wn[Wn[:, 2] > top - 0.06][:, 1].mean())
    ear_z = top - 0.115
    sl = Wn[np.abs(Wn[:, 2] - ear_z) < 0.015]
    xl, xr = float(sl[:, 0].max()) + 0.012, float(sl[:, 0].min()) - 0.012
    ey = float(sl[np.abs(sl[:, 0]) > 0.6 * max(abs(xl), abs(xr))][:, 1].mean()) if len(sl) else hy
    bm = bmesh.new()
    def cyl(p, axis, r, h, segs=16):
        mat = Matrix.Translation(p) @ (Vector((0, 0, 1)).rotation_difference(axis).to_matrix().to_4x4())
        bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=h, matrix=mat)
    def box(a, b, w):
        d = (b - a); L = d.length; z = d.normalized(); y = Vector((0, 0, 1)) if abs(z.z) < 0.9 else Vector((0, 1, 0))
        x = y.cross(z).normalized(); y = z.cross(x)
        mat = Matrix.Translation((a + b) / 2) @ Matrix((x, y, z)).transposed().to_4x4() @ Matrix.Diagonal((w, w, L, 1))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mat)
    cyl(Vector((xl, ey, ear_z)), Vector((1, 0, 0)), 0.034, 0.022)
    cyl(Vector((xr, ey, ear_z)), Vector((1, 0, 0)), 0.034, 0.022)
    # band: arc over the head from cup to cup
    pts = []
    for i in range(13):
        t = math.pi * i / 12; x = (xl + xr) / 2 + (xl - xr) / 2 * math.cos(t)
        z = ear_z + 0.02 + (top + 0.012 - ear_z - 0.02) * math.sin(t); pts.append(Vector((x, ey, z)))
    for a, b in zip(pts[:-1], pts[1:]): box(a, b, 0.014)
    # mic boom from the left cup forward to the mouth
    mouth = Vector((0.025, hy - 0.11, top - 0.205))
    box(Vector((xl, ey - 0.01, ear_z - 0.01)), mouth, 0.008)
    cyl(mouth, Vector((1, 0, 0)), 0.012, 0.03)
    me = bpy.data.meshes.new('headset'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('headset', me); bpy.context.collection.objects.link(o)
    o.data.materials.append(cel_mat('headset_mat', rgb, gid)); bind(o, arm, 'mixamorig:Head'); return o

GUNS = '/mnt/user-data/uploads/GIJoe_XCOM_4x/Reference/models/guns/'
def weapon(kind):
    """Returns (object, G_LOCAL, F_LOCAL): barrel along +X, grip point and fore-hand point in gun space."""
    if kind == 'xmlr':
        # Flash's laser rifle: XMLR-3A (Thingiverse 4566164, Mark2Design, CC-BY). Muzzle turned to +X.
        raw = open(os.path.join(CAST_V2, 'assets', 'XMLR-3A.stl'), 'rb').read(); n = struct.unpack('<I', raw[80:84])[0]
        T = np.frombuffer(raw[84:84 + n * 50], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))['v'].reshape(-1, 3).astype(np.float64)
        k = float(os.environ.get('XMLR_LEN', '0.95')) / 72.9
        T = np.stack([-T[:, 0], T[:, 1] + 27.0, T[:, 2] - 33.0], 1) * k
        g = _obj('xmlr', T, [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(n)], smooth=False)
        bpy.context.view_layer.objects.active = g; g.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.0002); bpy.ops.object.mode_set(mode='OBJECT')
        g.select_set(False)
        g.data.materials.append(cel_mat('xmlr_mat', (64, 66, 74), 30))
        return g, Vector((-11.2, 0, -6.0)) * k, Vector((9.2, 0, -3.0)) * k
    if kind in ('m16', 'm60'):
        f = {'m16': 'grunt_M-16.glb', 'm60': 'rock-n-roll_M-60.glb'}[kind]
        before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=GUNS + f)
        new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
        for o in new: o.parent = None
        for o in new: o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
        if len(new) > 1:
            bpy.ops.object.select_all(action='DESELECT')
            for o in new: o.select_set(True)
            bpy.context.view_layer.objects.active = new[0]; bpy.ops.object.join()
        g = new[0]; g.data.materials.clear(); g.data.materials.append(flat_mat('gun_flat', (60, 62, 66), 30))
        G, F = {'m16': ((-0.317, 0, -0.065), (0.07, 0, 0.040)), 'm60': ((-0.205, 0, -0.03), (0.16, 0, 0.0))}[kind]
        return g, Vector(G), Vector(F)
    bm = bmesh.new()
    def cyl(p, r, L, segs=20, axis=Vector((1, 0, 0))):
        mat = Matrix.Translation(p) @ (Vector((0, 0, 1)).rotation_difference(axis).to_matrix().to_4x4())
        bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=L, matrix=mat)
    def cube(c, sx, sy, sz):
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(c) @ Matrix.Diagonal((sx, sy, sz, 1)))
    if kind == 'bazooka':          # M20 style: 1.4 m tube, flared rear, pistol grip + fore grip underneath
        cyl(Vector((0.05, 0, 0)), 0.045, 1.40); cyl(Vector((-0.63, 0, 0)), 0.058, 0.14); cyl(Vector((0.72, 0, 0)), 0.052, 0.06)
        cube(Vector((-0.12, 0, -0.08)), 0.035, 0.03, 0.10); cube(Vector((0.18, 0, -0.08)), 0.035, 0.03, 0.10)
        rgb, G, F = (86, 104, 62), (-0.12, 0, -0.10), (0.18, 0, -0.10)
    elif kind == 'mortar':         # 60 mm tube carried like a rifle, base plate at the rear
        cyl(Vector((0.05, 0, 0)), 0.042, 0.80); cube(Vector((-0.37, 0, 0)), 0.025, 0.16, 0.16)
        cube(Vector((-0.10, 0, -0.06)), 0.04, 0.03, 0.08)
        rgb, G, F = (82, 96, 60), (-0.10, 0, -0.08), (0.20, 0, -0.05)
    elif kind == 'laser':          # chunky sci-fi rifle with a power pack
        cube(Vector((0.0, 0, 0.0)), 0.70, 0.06, 0.10); cyl(Vector((0.48, 0, 0.02)), 0.022, 0.30)
        cube(Vector((-0.10, 0, -0.10)), 0.05, 0.035, 0.12); cube(Vector((0.12, 0, -0.08)), 0.16, 0.05, 0.07)
        cube(Vector((-0.40, 0, -0.01)), 0.14, 0.05, 0.12)
        rgb, G, F = (70, 76, 92), (-0.10, 0, -0.10), (0.16, 0, -0.06)
    me = bpy.data.meshes.new(kind); bm.to_mesh(me); bm.free()
    g = bpy.data.objects.new(kind, me); bpy.context.collection.objects.link(g)
    g.data.materials.append(cel_mat(kind + '_mat', rgb, 30))
    return g, Vector(G), Vector(F)

def pistol(arm, rgb=(56, 58, 64)):
    """A sidearm bound to the right hand (rest-pose fit, same hold as Snake Eyes' Uzi 'pistol' hold)."""
    bm = bmesh.new()
    def cube(c, sx, sy, sz, rot=None):
        M = Matrix.Translation(c) @ (rot or Matrix.Identity(4)) @ Matrix.Diagonal((sx, sy, sz, 1))
        bmesh.ops.create_cube(bm, size=1.0, matrix=M)
    cube(Vector((0.055, 0, 0.045)), 0.20, 0.032, 0.040)                       # slide / barrel, forward of the fist
    cube(Vector((-0.01, 0, 0.0)), 0.035, 0.03, 0.10, Matrix.Rotation(math.radians(-15), 4, 'Y'))   # grip in the fist
    cube(Vector((0.025, 0, 0.005)), 0.04, 0.012, 0.02)                         # trigger guard
    me = bpy.data.meshes.new('pistol'); bm.to_mesh(me); bm.free()
    g = bpy.data.objects.new('pistol', me); bpy.context.collection.objects.link(g)
    g.data.materials.append(cel_mat('pistol_mat', rgb, 30))
    hb = arm.data.bones['mixamorig:RightHand']
    wrist = arm.matrix_world @ hb.head_local
    fist = wrist + Vector((-0.075, 0.0, -0.03))          # rest T-pose: fingers -X, palm down, thumb -Y
    Rg = Matrix(((-1, 0, 0), (0, 0, -1), (0, -1, 0))).transposed()   # barrel along the knuckles, top toward the thumb
    g.matrix_world = Matrix.Translation(fist) @ Rg.to_4x4()
    bind(g, arm, 'mixamorig:RightHand')
    return g


HEADSET_FBX = os.path.join(CAST_V2, 'assets', 'Headphone.fbx')
def headset_hx(Hv, arm, hs=None, gid=38):
    """REGJOE's approved Breaker headset (prop_headset_breaker.zip, build49.py) - same fit numbers, skin-bound.
    Hv: world points of the head + hair (rest)."""
    hs = hs or {"scale": 1.18, "dz": 0.004, "dy": 0.0, "color": [40, 40, 44], "mic": True, "mic_side": "left",
                "mic_fwd": 0.035, "mic_drop": 0.228, "mic_r": 0.0055, "ball_r": 0.017, "mic_cup_dz": -0.025}
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=HEADSET_FBX)
    new = [o for o in bpy.data.objects if o not in before]
    ho = [o for o in new if o.type == 'MESH'][0]
    for o in new:
        if o is not ho and o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
    ho.parent = None; ho.data.transform(ho.matrix_world); ho.matrix_world = Matrix.Identity(4)
    hv = np.array([v.co[:] for v in ho.data.vertices])
    top = Hv[:, 2].max(); band = Hv[Hv[:, 2] > top - 0.09]
    hw = band[:, 0].max() - band[:, 0].min(); hcx = (Hv[:, 0].max() + Hv[:, 0].min()) / 2
    ear = Hv[(Hv[:, 2] > top - 0.15) & (Hv[:, 2] < top - 0.09)]; ey = (ear[:, 1].max() + ear[:, 1].min()) / 2
    k = hw * hs.get('scale', 1.25) / (hv[:, 0].max() - hv[:, 0].min()); hv = hv * k
    hv[:, 0] += hcx - (hv[:, 0].max() + hv[:, 0].min()) / 2
    hv[:, 1] += ey + hs.get('dy', 0.0) - (hv[:, 1].max() + hv[:, 1].min()) / 2
    hv[:, 2] += top + hs.get('dz', 0.008) - hv[:, 2].max()
    for v, p in zip(ho.data.vertices, hv): v.co = Vector(p)
    col = hs.get('color', [34, 34, 38])
    m1 = flat_mat('HS1', col, gid); m0 = flat_mat('HS0', [c * 0.6 for c in col], gid)
    ho.data.materials.clear(); ho.data.materials.append(m1); ho.data.materials.append(m0)
    L = Vector((-0.45, -0.6, 0.55)).normalized()
    for p in ho.data.polygons: p.material_index = 0 if p.normal.dot(L) > 0.1 else 1
    outs = [ho]
    if hs.get('mic'):
        cx0 = hv[:, 0].min() + 0.01 if hs.get('mic_side', 'left') == 'left' else hv[:, 0].max() - 0.01
        face = Hv[(Hv[:, 2] > top - 0.2) & (Hv[:, 2] < top - 0.16)]
        mouth = Vector((hcx + (0.018 if cx0 > hcx else -0.018), face[:, 1].min() - hs.get('mic_fwd', 0.03), top - hs.get('mic_drop', 0.19)))
        side = hv[:, 0] < hv[:, 0].min() + 0.02 if cx0 < hcx else hv[:, 0] > hv[:, 0].max() - 0.02
        cz = (hv[side, 2].min() + hv[side, 2].max()) / 2; cyy = (hv[side, 1].min() + hv[side, 1].max()) / 2
        cup = Vector((cx0, cyy, cz + hs.get('mic_cup_dz', 0.0)))
        cu = bpy.data.curves.new('mic', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = hs.get('mic_r', 0.0055); cu.bevel_resolution = 2
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(1)
        for bp, co in zip(sp.bezier_points, (cup, mouth)):
            bp.co = co; bp.handle_left_type = bp.handle_right_type = 'AUTO'
        mo = bpy.data.objects.new('mic', cu); bpy.context.scene.collection.objects.link(mo)
        bpy.context.view_layer.objects.active = mo
        for o in bpy.data.objects: o.select_set(o is mo)
        bpy.ops.object.convert(target='MESH')
        bpy.ops.mesh.primitive_uv_sphere_add(radius=hs.get('ball_r', 0.016), location=mouth)
        ball = bpy.context.active_object
        for o in (mo, ball):
            o.data.materials.append(m1); o.data.materials.append(m0); outs.append(o)
    for o in outs: bind_skin(o, arm, 'mixamorig:Head')
    return outs


BANDOLIER_STL = '/tmp/claude-0/ws/band/Playmobil/files/PM_Bandolier_Final_5.stl'   # crossed belts, Thingiverse 6643916 (public domain)
def bandolier(body_meshes, arm, rgb=(228, 172, 60), gid=33, stl=None, z_lo=0.585, z_hi=0.835, off=0.007, decimate=0.5, bullets=None, bullet_fit=None, x_scale=1.0, smooth_r=0.04):
    """Crossed bandoliers wrapped onto the (swelled) rest torso and skinned with the nearest body vertex's weights."""
    from mathutils import kdtree
    raw = open(stl or BANDOLIER_STL, 'rb').read(); n = struct.unpack('<I', raw[80:84])[0]
    T = np.frombuffer(raw[84:84 + n * 50], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))['v'].reshape(-1, 3).astype(np.float64)
    o = _obj('bandolier', T, [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(n)], smooth=False)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.02); bpy.ops.object.mode_set(mode='OBJECT')
    if decimate < 1:
        dm = o.modifiers.new('dec', 'DECIMATE'); dm.ratio = decimate; bpy.ops.object.modifier_apply(modifier='dec')
    o.select_set(False)
    for p in o.data.polygons: p.use_smooth = True
    # torso shell of the body (rest, world), arms excluded
    P = np.concatenate([np.array([ob.matrix_world @ v.co for v in ob.data.vertices]) for ob in body_meshes])
    h = P[:, 2].max() / 0.845 if P[:, 2].max() < 1.6 else P[:, 2].max()
    tor = P[(np.abs(P[:, 0]) < 0.24) & (P[:, 2] > z_lo * h - 0.03) & (P[:, 2] < z_hi * h + 0.03)]
    yc = float(np.median(tor[:, 1]))
    V = np.array([v.co[:] for v in o.data.vertices]); lo, hi = V.min(0), V.max(0)
    # fit the model's box onto the torso box
    tl, th = tor.min(0), tor.max(0)
    V = (V - lo) / (hi - lo); Vn = V.copy()
    _xm = (tl[0] + th[0]) / 2; V[:, 0] = _xm + (V[:, 0] - 0.5) * (th[0] - tl[0]) * x_scale; V[:, 1] = tl[1] + V[:, 1] * (th[1] - tl[1]); V[:, 2] = z_lo * h + V[:, 2] * (z_hi - z_lo) * h
    # wrap: push each vertex radially (around the torso axis) onto the body surface + off
    ang_b = np.arctan2(tor[:, 1] - yc, tor[:, 0]); rad_b = np.hypot(tor[:, 0], tor[:, 1] - yc)
    ang_v = np.arctan2(V[:, 1] - yc, V[:, 0]); rv = np.hypot(V[:, 0], V[:, 1] - yc)
    # model's own radius relative to its mean centreline keeps thickness
    out = V.copy(); Rv = np.empty(len(V))
    for i in range(len(V)):
        m = (np.abs(tor[:, 2] - V[i, 2]) < 0.025) & (np.abs(np.angle(np.exp(1j * (ang_b - ang_v[i])))) < 0.25)
        Rv[i] = rad_b[m].max() if m.any() else rv[i]
    # smooth the wrap radius over ~4 cm so the belt lies in a clean line instead of zig-zagging over every body bump
    from scipy.spatial import cKDTree
    tr = cKDTree(np.c_[ang_v * 0.15, V[:, 2]]); Rs = np.array([Rv[nb].mean() for nb in tr.query_ball_point(np.c_[ang_v * 0.15, V[:, 2]], smooth_r)])
    for i in range(len(V)):
        out[i, 0] = np.cos(ang_v[i]) * (Rs[i] + off); out[i, 1] = yc + np.sin(ang_v[i]) * (Rs[i] + off)
    for v, p in zip(o.data.vertices, out): v.co = Vector(p)
    o.data.materials.append(cel_mat('bandolier_mat', rgb, gid))
    objs = [o]
    if bullets:
        objs.append(_bullets(Vn, out, yc, bullets, **(bullet_fit or {})))
    # skin with the nearest body vertex's weights
    kd_items = []
    for ob in body_meshes:
        gi = {g.index: g.name for g in ob.vertex_groups}
        for v in ob.data.vertices: kd_items.append(((ob.matrix_world @ v.co), [(gi[g.group], g.weight) for g in v.groups]))
    kd = kdtree.KDTree(len(kd_items))
    for i, (co, _) in enumerate(kd_items): kd.insert(co, i)
    kd.balance()
    for ob in objs:
        groups = {}
        for v in ob.data.vertices:
            _, idx, _ = kd.find(v.co)
            for name, w in kd_items[idx][1]:
                if name not in groups: groups[name] = ob.vertex_groups.new(name=name)
                groups[name].add([v.index], w, 'REPLACE')
        m = ob.modifiers.new('arm', 'ARMATURE'); m.object = arm
    return o

def _bullets(Vn, out, yc, rgb, spacing=0.021, r=0.0062, length=0.034, gid=33, grid=120, shoulder_band=0.07):
    """Cartridges in the bandolier loops: trace each belt's centreline in the model's own (x, z) layout,
    front and back halves separately, then lay a brass cylinder across the belt every `spacing` metres
    on the belt's outer face (the wrapped vertices near that spot, furthest from the torso axis)."""
    from scipy import ndimage as ndi
    bm = bmesh.new()
    Ro = np.hypot(out[:, 0], out[:, 1] - yc)
    # trace in the wrapped belt's own front / back projection (what the camera sees), not the model's layout
    lo3, hi3 = out.min(0), out.max(0); Q = (out - lo3) / (hi3 - lo3)
    zt = hi3[2] - shoulder_band
    def lay(c, dirv, nrm):
        dirv = dirv / (np.linalg.norm(dirv) + 1e-9); nrm = nrm / (np.linalg.norm(nrm) + 1e-9)
        ax = np.cross(nrm, dirv); ax /= np.linalg.norm(ax) + 1e-9
        mat = Matrix.Translation(Vector(c + nrm * r * 1.5)) @ (Vector((0, 0, 1)).rotation_difference(Vector(ax)).to_matrix().to_4x4())
        bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r * 0.8, depth=length, matrix=mat)
    # over the shoulders: the strap's top runs front-to-back; walk it in y on each side, on its upper face
    for sgn in (-1, 1):
        S = out[(out[:, 2] > zt - 0.01) & (np.sign(out[:, 0]) == sgn)]
        if len(S) < 10: continue
        ys = np.arange(S[:, 1].min(), S[:, 1].max(), 0.004); C = []
        for y0 in ys:
            b = S[np.abs(S[:, 1] - y0) < 0.006]
            if len(b) < 3: continue
            C.append([b[:, 0].mean(), y0, b[:, 2].max()])
        C = ndi.gaussian_filter1d(np.array(C), 2, axis=0)
        seg = np.linalg.norm(np.diff(C, axis=0), axis=1); sc = np.concatenate([[0], np.cumsum(seg)])
        for t in np.arange(spacing * 0.5, sc[-1], spacing):
            i = min(np.searchsorted(sc, t), len(C) - 1); i0 = max(i - 1, 0); c = C[i]
            lay(c, C[min(i + 1, len(C) - 1)] - C[i0], np.array([0.0, c[1] - yc, c[2] - (zt - 0.05)]))
    for half in (out[:, 1] < yc, out[:, 1] >= yc):
        q = Q[half]; P = out[half]; R = Ro[half]
        m = np.zeros((grid, grid), bool)
        m[np.clip((q[:, 2] * (grid - 1)).astype(int), 0, grid - 1), np.clip((q[:, 0] * (grid - 1)).astype(int), 0, grid - 1)] = True
        m = ndi.binary_closing(m, iterations=2)
        cl = {0: [], 1: []}
        for zi in range(grid):
            lab, nr = ndi.label(m[zi])
            if nr != 2: continue                         # skip the crossing and the ragged ends
            for k in (1, 2):
                xs = np.nonzero(lab == k)[0]; xc = xs.mean() / (grid - 1); z = zi / (grid - 1)
                # belt 0 runs from the left shoulder (low x at the top) down to the right; belt 1 the other way
                b = 0 if (xc < 0.5) == (z > 0.5) else 1
                cl[b].append((xc, z))
        for b in (0, 1):
            pts = np.array(sorted(cl[b], key=lambda t: t[1]))
            if len(pts) < 4: continue
            # centreline in 3D: outer-face position of the vertices near each (x, z)
            C = []
            for xc, z in pts:
                d = np.hypot(q[:, 0] - xc, q[:, 2] - z); near = d < 0.025
                if P[near].size and P[near][:, 2].mean() > zt: continue      # shoulder band is laid separately
                if near.sum() < 3: continue
                Pn = P[near]; mc = Pn.mean(0); ang = np.arctan2(mc[1] - yc, mc[0])
                C.append(np.array([np.cos(ang) * R[near].max(), yc + np.sin(ang) * R[near].max(), mc[2]]))
            C = np.array(C)
            if len(C) < 4: continue
            C = ndi.gaussian_filter1d(C, 4, axis=0)
            seg = np.linalg.norm(np.diff(C, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
            # leave the crossing (a gap in the run) bare: split where consecutive centre points jump
            for t in np.arange(spacing * 0.5, s[-1], spacing):
                i = min(np.searchsorted(s, t), len(C) - 1); i0 = max(i - 1, 0)
                if seg[min(i0, len(seg) - 1)] > 0.03: continue
                c = C[i]; dirv = C[min(i + 1, len(C) - 1)] - C[i0]
                if np.linalg.norm(dirv) < 1e-6: continue
                dirv /= np.linalg.norm(dirv)
                nrm = np.array([c[0], c[1] - yc, 0.0]); nrm /= np.linalg.norm(nrm) + 1e-9
                ax = np.cross(nrm, dirv); ax /= np.linalg.norm(ax) + 1e-9
                ctr = c + nrm * r * 1.5
                mat = Matrix.Translation(Vector(ctr)) @ (Vector((0, 0, 1)).rotation_difference(Vector(ax)).to_matrix().to_4x4())
                bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r * 0.8, depth=length, matrix=mat)
    me = bpy.data.meshes.new('bullets'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('bullets', me); bpy.context.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    o.data.materials.append(cel_mat('bullets_mat', rgb, gid)); print('bandolier bullets', len(me.vertices) // 16)
    return o


VISOR_FBX = os.path.join(CAST_V2, 'assets', 'SM_Helmet_embedded.fbx')
def helmet_visor(Wn, arm, rgb, scale=1.22, back=0.012, up=0.02, gid=36, visor_rgb=(196, 222, 232), visor_alpha=0.45):
    """Open-face helmet with a clear visor (John's download, 12 Nov) - Flash. Shell cel-shaded, visor see-through."""
    before = set(bpy.data.objects); bpy.ops.import_scene.fbx(filepath=VISOR_FBX)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
    for o in meshes:
        o.parent = None; o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
    shell = [o for o in meshes if 'Visor' not in o.name]; vis = [o for o in meshes if 'Visor' in o.name]
    S = np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for o in shell]); lo, hi = S.min(0), S.max(0)
    top = Wn[:, 2].max(); sk = Wn[Wn[:, 2] > top - 0.06]
    sc = scale * (sk[:, 0].max() - sk[:, 0].min()) / (hi[0] - lo[0])
    tgt = Vector((float(sk[:, 0].mean()), float(sk[:, 1].mean()) + back, float(top) + up))
    M = Matrix.Translation(tgt) @ Matrix.Scale(sc, 4) @ Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -hi[2]))
    for o in meshes:
        o.data.transform(M); o.data.materials.clear()
        for p in o.data.polygons: p.use_smooth = True
    for o in shell: o.data.materials.append(cel_mat('vhelm_mat', rgb, gid))
    vm = bpy.data.materials.new('visor_mat'); vm.use_nodes = True; nt = vm.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = tuple((c / 255) ** 2.2 for c in visor_rgb) + (1,)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs[0].default_value = visor_alpha
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    tr2 = nt.nodes.new('ShaderNodeBsdfTransparent'); sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'
    nt.links.new(mx.outputs[0], sw.inputs[1]); nt.links.new(tr2.outputs[0], sw.inputs[2]); nt.links.new(sw.outputs[0], out.inputs['Surface'])
    for o in vis: o.data.materials.append(vm)
    for o in meshes: bind_skin(o, arm, 'mixamorig:Head')
    return meshes


GEAR_KIT = os.path.join(_HERE, '..', 'greenshirts')     # bandolier_fit.py as shipped in duke_build_v4.zip          # DESIGN's gear_kit_ch49.zip, used as-is
def bandolier_x_sweep(body_meshes, arm, rgb, bullets=None, top=(0.115, 1.475), bottom=(-0.150, 1.035), lift2=0.006,
                      spacing=0.020, r=0.0058, gid=33):
    """Rock 'n Roll's crossed belts = DESIGN's add_bandolier_sweep called twice (left-shoulder->right-hip and the mirror),
    no pouches. Second strap sits lift2 further out so they cross cleanly. Cartridges (CAST addition) are laid across
    each strap's outer face from the strap's own swept ring, skipped where the other strap covers it, and skinned with
    the same torso-only rule as the kit (arm/hand weight >= 0.15 excluded)."""
    import sys as _s
    if GEAR_KIT not in _s.path: _s.path.insert(0, GEAR_KIT)
    from bandolier_fit import add_bandolier_sweep
    from scipy.spatial import cKDTree
    s1 = add_bandolier_sweep(body_meshes, arm, cel_mat, top=top, bottom=bottom, strap_rgb=rgb, strap_id=gid, pouches=())
    s2 = add_bandolier_sweep(body_meshes, arm, cel_mat, top=(-top[0], top[1]), bottom=(-bottom[0], bottom[1]),
                             gap=0.004 + lift2, strap_rgb=rgb, strap_id=gid, pouches=())
    if not bullets: return [s1, s2]
    rings = []
    for s in (s1, s2):
        V = np.array([v.co[:] for v in s.data.vertices]); n = len(V) // 4
        R = V[:4 * n].reshape(n, 4, 3)
        ctr = (R[:, 2] + R[:, 3]) / 2; acr = R[:, 1] - R[:, 0]; out = R[:, 3] - R[:, 0]
        rings.append((ctr, acr / np.linalg.norm(acr, axis=1)[:, None], out / np.linalg.norm(out, axis=1)[:, None]))
    bm = bmesh.new()
    for k, (ctr, acr, out) in enumerate(rings):
        other = cKDTree(rings[1 - k][0])
        seg = np.linalg.norm(np.diff(np.vstack([ctr, ctr[:1]]), axis=0), axis=1); s_ = np.concatenate([[0], np.cumsum(seg)])
        for t in np.arange(spacing / 2, s_[-1], spacing):
            i = min(np.searchsorted(s_, t), len(ctr) - 1)
            if k == 0 and other.query(ctr[i])[0] < 0.035: continue          # under the other strap at the crossings
            c = ctr[i] + out[i] * r * 1.1
            mat = Matrix.Translation(Vector(c)) @ (Vector((0, 0, 1)).rotation_difference(Vector(acr[i])).to_matrix().to_4x4())
            bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r * 0.8, depth=0.036, matrix=mat)
    me = bpy.data.meshes.new('bullets'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('bullets', me); bpy.context.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth = True
    me.materials.append(cel_mat('bullets_mat', bullets, gid))
    # torso-only skin (same rule as bandolier_fit)
    allv, owner = [], []
    for o_ in body_meshes:
        gi = {vg.index: vg.name for vg in o_.vertex_groups}
        for vv in o_.data.vertices:
            if sum(g.weight for g in vv.groups if any(q in gi[g.group] for q in ('Arm', 'Hand'))) < 0.15:
                allv.append((o_.matrix_world @ vv.co)[:]); owner.append((o_, vv.index))
    _, nn = cKDTree(np.array(allv)).query(np.array([v.co[:] for v in me.vertices]))
    groups = {}
    for vi, j in enumerate(nn):
        o_, bi = owner[j]
        for g in o_.data.vertices[bi].groups:
            groups.setdefault(o_.vertex_groups[g.group].name, []).append((vi, g.weight))
    for name, lst in groups.items():
        vg = ob.vertex_groups.new(name=name)
        for vi, w in lst: vg.add([vi], w, 'REPLACE')
    md = ob.modifiers.new('arm', 'ARMATURE'); md.object = arm
    print('bandolier_x_sweep cartridges', len(me.vertices) // 16)
    return [s1, s2, ob]
