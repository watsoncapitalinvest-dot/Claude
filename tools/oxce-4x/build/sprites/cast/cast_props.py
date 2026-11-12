"""Props for the cartoon cast: headgear bound to the Head bone and simple weapons. Flat cartoon materials with ID output."""
import bpy, bmesh, math, struct, sys, numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, '/tmp/claude-0/ws/beret')

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
    nt.links.new(geo.outputs['Normal'], vt.inputs[0])
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

def bind(o, arm, bone):
    b = arm.data.bones[bone]
    o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = b.name
    o.matrix_parent_inverse = (arm.matrix_world @ b.matrix_local @ Matrix.Translation((0, b.length, 0))).inverted()

def _obj(name, V, F, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in V], [], F); me.validate()
    for p in me.polygons: p.use_smooth = smooth
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); return o

HELMET_STL = '/tmp/claude-0/ws/helmet/files/Modern_Army_Helmet.stl'
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
    o.data.materials.append(cel_mat('helmet_mat', rgb, gid)); bind(o, arm, 'mixamorig:Head'); return o

def beret(Wn, arm, rgb, band_below_top, side=-1.0, gid=36, **kw):
    from beret import make_beret
    top = float(Wn[:, 2].max())
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

GUNS = '/mnt/user-data/uploads/GI-Joe-Silent-Storm/GIJoe_XCOM_4x/Reference/models/guns/'
def weapon(kind):
    """Returns (object, G_LOCAL, F_LOCAL): barrel along +X, grip point and fore-hand point in gun space."""
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
