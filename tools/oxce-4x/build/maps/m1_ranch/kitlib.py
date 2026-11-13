"""PILOTBRN tile kit: model every tile part in Blender and render it in the X-COM iso camera at 4x.

run: python3 kit.py <outdir>     (bpy 5.3.0 as a module)
One PNG per part, 128x160 RGBA, rendered at 4x supersample (512x640) then downsampled.

Geometry rules (one cell): Blender X = east, Y = north. Cell spans x 0..S, y -S..0.
West wall sits on x=0, north wall on y=0. Tile side S = 1.3 m, one level H = 1.95 m.
X-COM is not true orthographic: heights are squashed by sqrt(2/3) so one level = 96 px at 4x.
Lighting is baked: each face gets one of 3 cel tones from its normal (semi3 look),
colours are emitted flat, ink is Freestyle.
"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix

S, H = 1.3, 1.95
K = math.sqrt(2.0 / 3.0)                 # height squash
SS = 4                                   # supersample
FW, FH = 128 * SS, 160 * SS
PXM = 128 / (S * math.sqrt(2))           # px per metre at 4x (69.62)
L = Vector((0.3, -0.8, 1.2)).normalized()   # light from screen upper-left
INK_PX = 1.15                            # final ink width in px at 4x

def tone(n):
    d = n.dot(L)
    return 1.08 if d > 0.7 else (1.0 if d > 0.35 else 0.62)

# ---------------------------------------------------------------- scene
def reset():
    _MATS.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 16
    sc.cycles.use_denoising = False
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = FW, FH
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    # camera: viewer to the south-east, 30 deg elevation, orthographic
    c, s, a = math.cos(math.radians(30)), math.sin(math.radians(30)), 1 / math.sqrt(2)
    d = Vector((-c * a, c * a, -s))
    r = Vector((a, a, 0))
    u = r.cross(d)
    cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'
    cam.sensor_fit = 'HORIZONTAL'; cam.ortho_scale = S * math.sqrt(2)
    co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
    centre = Vector((0, 0, 0)) + u * (16 / PXM)   # cell top corner sits 16 px below frame centre
    co.matrix_world = Matrix.Translation(centre - d * 40) @ Matrix((r, u, -d)).transposed().to_4x4()
    cam.clip_end = 200
    # ink
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = 'ABSOLUTE'
    sc.render.line_thickness = 1.0
    fs = bpy.context.view_layer.freestyle_settings
    fs.crease_angle = math.radians(115)
    for ls in list(fs.linesets): fs.linesets.remove(ls)
    ink = bpy.data.collections.new('ink'); sc.collection.children.link(ink)
    noink = bpy.data.collections.new('noink'); sc.collection.children.link(noink)
    style = bpy.data.linestyles.new('ink'); style.color = (0, 0, 0); style.thickness = INK_PX * SS
    a_ = fs.linesets.new('shape'); a_.linestyle = style
    a_.select_by_visibility = True; a_.select_by_edge_types = True; a_.select_by_collection = True
    a_.collection = ink
    a_.select_silhouette = True; a_.select_border = True; a_.select_crease = True
    b_ = fs.linesets.new('marks'); b_.linestyle = style
    b_.select_by_visibility = True; b_.select_by_edge_types = True
    b_.select_silhouette = False; b_.select_border = False; b_.select_crease = False
    b_.select_edge_mark = True
    mat = bpy.data.materials.new('flat'); mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'col'
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(at.outputs['Color'], em.inputs['Color']); nt.links.new(em.outputs[0], out.inputs[0])
    return sc, ink, noink, mat

# ---------------------------------------------------------------- mesh helpers
class Part:
    def __init__(self, name, ink=True):
        self.name = name; self.ink = ink
        self.bm = bmesh.new(); self.col = self.bm.loops.layers.color.new('col')
        self.noink = bmesh.new(); self.ncol = self.noink.loops.layers.color.new('col')
        self.bm.edges.layers.int.new('fsmark'); self.noink.edges.layers.int.new('fsmark')
        self.bm.loops.layers.uv.new('UVMap'); self.noink.loops.layers.uv.new('UVMap')
        self.mkeys = ['flat']          # material slots shared by both meshes
        self.tint = (1.0, 1.0, 1.0)    # multiplies textured faces (set before a call, reset after)

    def mat(self, key):
        if key is None: return 0
        if key not in self.mkeys: self.mkeys.append(key)
        return self.mkeys.index(key)

    def _paint(self, bm, layer, faces, rgb, jitter, tex=None):
        mi = self.mat(tex)
        for f in faces:
            t = tone(f.normal) * (1 + random.uniform(-jitter, jitter))
            if tex: c = (t * self.tint[0], t * self.tint[1], t * self.tint[2], 1)
            else: c = (min(rgb[0] * t, 1), min(rgb[1] * t, 1), min(rgb[2] * t, 1), 1)
            for lp in f.loops: lp[layer] = c
            f.material_index = mi

    def box(self, x0, x1, y0, y1, z0, z1, rgb, ink=True, jitter=0.0, mark=None, tex=None):
        bm, layer = (self.bm, self.col) if ink else (self.noink, self.ncol)
        vs = [bm.verts.new((x, y, z)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
        idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        fs = [bm.faces.new([vs[i] for i in q]) for q in idx]
        bmesh.ops.recalc_face_normals(bm, faces=fs)      # outward, whatever order the corners came in (fix 12 Nov 21:30)
        bm.normal_update()
        self._paint(bm, layer, fs, rgb, jitter, tex)
        if mark: self._mark(bm, fs, mark)
        return fs

    def _mark(self, bm, faces, keep):
        fl = bm.edges.layers.int.get('fsmark')
        for f in faces:
            for e in f.edges:
                e[fl] = 1 if keep(e.verts[0].co, e.verts[1].co) else 0

    def cyl(self, cx, cy, z0, z1, r, rgb, seg=12, ink=True, jitter=0.0, tex=None):
        bm, layer = (self.bm, self.col) if ink else (self.noink, self.ncol)
        bot = [bm.verts.new((cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg), z0)) for i in range(seg)]
        top = [bm.verts.new((v.co.x, v.co.y, z1)) for v in bot]
        fs = [bm.faces.new((bot[i], bot[(i + 1) % seg], top[(i + 1) % seg], top[i])) for i in range(seg)]
        fs += [bm.faces.new(list(reversed(bot))), bm.faces.new(top)]
        bm.normal_update(); self._paint(bm, layer, fs, rgb, jitter, tex); return fs

    def rod(self, p0, p1, r, rgb, ink=False, seg=6):
        """thin cylinder between two points (wires, rails)"""
        bm, layer = (self.bm, self.col) if ink else (self.noink, self.ncol)
        p0, p1 = Vector(p0), Vector(p1); ax = (p1 - p0).normalized()
        t = ax.orthogonal().normalized(); b = ax.cross(t)
        r0 = [bm.verts.new(p0 + (t * math.cos(2 * math.pi * i / seg) + b * math.sin(2 * math.pi * i / seg)) * r) for i in range(seg)]
        r1 = [bm.verts.new(v.co + (p1 - p0)) for v in r0]
        fs = [bm.faces.new((r0[i], r0[(i + 1) % seg], r1[(i + 1) % seg], r1[i])) for i in range(seg)]
        bm.normal_update(); self._paint(bm, layer, fs, rgb, 0); return fs

    def blob(self, cx, cy, cz, rx, ry, rz, rgb, sub=2, rough=0.18, ink=True, seed=0):
        bm, layer = (self.bm, self.col) if ink else (self.noink, self.ncol)
        tmp = bmesh.new(); bmesh.ops.create_icosphere(tmp, subdivisions=sub, radius=1.0)
        rnd = random.Random(seed)
        for v in tmp.verts:
            k = 1 + rnd.uniform(-rough, rough)
            v.co = Vector((cx + v.co.x * rx * k, cy + v.co.y * ry * k, cz + v.co.z * rz * k))
        m = {}
        for v in tmp.verts: m[v] = bm.verts.new(v.co)
        fs = [bm.faces.new([m[v] for v in f.verts]) for f in tmp.faces]
        tmp.free(); bm.normal_update(); self._paint(bm, layer, fs, rgb, 0.04); return fs

    def ground(self, rgb, speck=(), n=24, seed=1, paint=None, z=0.0, tex=None):
        """flat cell floor as a grid of small quads with colour noise (no ink).
        paint(x, y, c) -> c lets a floor draw ruts, streaks, edges on top of the noise."""
        rnd = random.Random(seed); bm, layer = self.noink, self.ncol
        st = S / n
        for i in range(n):
            for j in range(n):
                x0, y0 = i * st, -S + j * st
                vs = [bm.verts.new((x0, y0, z)), bm.verts.new((x0 + st, y0, z)),
                      bm.verts.new((x0 + st, y0 + st, z)), bm.verts.new((x0, y0 + st, z))]
                f = bm.faces.new(vs)
                c = rgb
                for (p, sc) in speck:
                    if rnd.random() < p: c = sc
                if paint: c = paint(x0 + st / 2, y0 + st / 2, c, rnd)
                if tex:
                    col = (1.08, 1.08, 1.08, 1); f.material_index = self.mat(tex)
                    if paint: col = (c[0], c[1], c[2], 1)   # paint returns a tone multiplier when textured
                else:
                    k = 1 + rnd.uniform(-0.035, 0.035)
                    col = (c[0] * 1.08 * k, c[1] * 1.08 * k, c[2] * 1.08 * k, 1)
                for lp in f.loops: lp[layer] = col

    def decal(self, origin, u, v, w, h, img, lift=0.006):
        """flat image quad: origin = bottom-left corner on the surface, u/v = unit directions along width/height.
        Lifted off the surface along u x v by `lift` metres. No ink."""
        bm, layer = self.noink, self.ncol
        o, u, v = Vector(origin), Vector(u).normalized(), Vector(v).normalized()
        n = u.cross(v); o = o + n * lift
        pts = [o, o + u * w, o + u * w + v * h, o + v * h]
        f = bm.faces.new([bm.verts.new(p) for p in pts]); bm.normal_update()
        uvl = bm.loops.layers.uv.get('UVMap')
        for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
        t = tone(n)
        for lp in f.loops: lp[layer] = (t, t, t, 1)
        f.material_index = self.mat(('decal', img))
        return f

    def build(self, sc, inkc, noinkc, mat):
        for bm, coll, nm in ((self.bm, inkc, 'i'), (self.noink, noinkc, 'n')):
            if not bm.faces: continue
            me = bpy.data.meshes.new(self.name + nm)
            fl = bm.edges.layers.int.get('fsmark')
            bm.to_mesh(me)
            if fl is not None:
                attr = me.attributes.get('freestyle_edge') or me.attributes.new('freestyle_edge', 'BOOLEAN', 'EDGE')
                vals = [False] * len(me.edges)
                for e in bm.edges: vals[e.index] = bool(e[fl])
                attr.data.foreach_set('value', vals)
            for key in self.mkeys: me.materials.append(mat if key == 'flat' else make_mat(key))
            ob = bpy.data.objects.new(self.name + nm, me); coll.objects.link(ob)
            ob.scale = (1, 1, K)


ART = '/home/claude/art_in/'
_MATS = {}
def make_mat(key):
    """('tex', file, size_m, ox, oy): box-projected seamless texture x baked tone.
       ('decal', file): UV-mapped RGBA image x tone, transparent where alpha is 0."""
    if key in _MATS: return _MATS[key]
    m = bpy.data.materials.new(str(key)); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'col'
    im = nt.nodes.new('ShaderNodeTexImage'); im.image = bpy.data.images.load(ART + key[1], check_existing=True)
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1.0
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(im.outputs['Color'], mul.inputs[6]); nt.links.new(at.outputs['Color'], mul.inputs[7])
    nt.links.new(mul.outputs[2], em.inputs['Color'])
    if key[0] == 'tex':
        tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
        sz = key[2]; mp.inputs['Scale'].default_value = (1 / sz, 1 / sz, 1 / sz)
        mp.inputs['Location'].default_value = (key[3], key[4], 0)
        if len(key) > 5 and key[5]: mp.inputs['Rotation'].default_value = (0, 0, key[5])
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], im.inputs['Vector'])
        im.projection = 'BOX'; im.projection_blend = 0.0
        nt.links.new(em.outputs[0], out.inputs[0])
    else:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(im.outputs['Alpha'], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
        im.extension = 'CLIP'
    _MATS[key] = m
    return m

def TX(name, ox=0.0, oy=0.0, size=2.6, rot=0.0):
    """texture key: TX('a1', 0.5, 0) -> tex_a1_*.png, 2.6 m per repeat, offset in repeats"""
    import glob, os
    f = os.path.basename(glob.glob(ART + 'tex_%s_*.png' % name)[0])
    return ('tex', f, size, ox, oy, rot)

def render(part, path):
    sc, inkc, noinkc, mat = reset()
    part.build(sc, inkc, noinkc, mat)
    sc.render.use_freestyle = part.ink
    sc.render.filepath = path + '_big.png'
    bpy.ops.render.render(write_still=True)
    from PIL import Image
    im = Image.open(path + '_big.png').convert('RGBA')
    im = im.resize((128, 160), Image.LANCZOS)
    import numpy as np
    a = np.array(im); keep = a[..., 3] >= 128          # hard edges: every pixel fully solid or fully clear
    a[..., 3] = np.where(keep, 255, 0); a[~keep, :3] = 0
    Image.fromarray(a, 'RGBA').save(path + '.png'); os.remove(path + '_big.png')

# ---------------------------------------------------------------- palette (cartoon, flat)
CALICHE = (0.86, 0.78, 0.60)
CAL_DARK = (0.74, 0.65, 0.48)
SCRUB = (0.55, 0.53, 0.30)
CONCRETE = (0.62, 0.62, 0.60)
BARNRED = (0.74, 0.21, 0.15)
TRIM = (0.92, 0.89, 0.82)
WOOD = (0.74, 0.56, 0.32)
WOOD_D = (0.52, 0.37, 0.20)
DRUM = (0.72, 0.15, 0.10)
STEEL = (0.70, 0.72, 0.74)
WIRE = (0.58, 0.60, 0.62)
LEAF = (0.42, 0.46, 0.22)
BARK = (0.40, 0.29, 0.18)
ROCK = (0.68, 0.62, 0.53)
T = 0.12   # wall thickness

def keep_west(a, b):   # wall along y: drop vertical end edges (no seam between wall tiles)
    vert = abs(a.x - b.x) < 1e-4 and abs(a.y - b.y) < 1e-4
    end = abs(a.y) < 1e-4 or abs(a.y + S) < 1e-4
    return not (vert and end)

def keep_north(a, b):
    vert = abs(a.x - b.x) < 1e-4 and abs(a.y - b.y) < 1e-4
    end = abs(a.x) < 1e-4 or abs(a.x - S) < 1e-4
    return not (vert and end)

def barn_wall(p, axis, door=None):
    """axis 'w': along y at x=0..T ; 'n': along x at y=-T..0."""
    keep = keep_west if axis == 'w' else keep_north
    def seg(a0, a1, z0, z1, rgb, th=T, off=0.0):
        if axis == 'w': return p.box(off, off + th, -a1, -a0, z0, z1, rgb, ink=False, mark=keep)
        return p.box(a0, a1, -off - th, -off, z0, z1, rgb, ink=False, mark=keep)
    top = H * 0.98
    if door is None:
        # planks: separate boards so the plank lines come for free as marked edges
        n = 6
        for i in range(n):
            a0, a1 = S * i / n, S * (i + 1) / n
            seg(a0, a1, 0, top - 0.14, BARNRED, off=0.0 if i % 2 else 0.006)
    elif door == 'closed':
        seg(0, S, 0, top - 0.14, BARNRED)
        # white X brace and frame of a sliding barn door, proud of the wall
        fr = 0.07
        seg(0.08, 0.08 + fr, 0, top - 0.2, TRIM, th=0.03, off=T)
        seg(S - 0.08 - fr, S - 0.08, 0, top - 0.2, TRIM, th=0.03, off=T)
        seg(0.08, S - 0.08, top - 0.2 - fr, top - 0.2, TRIM, th=0.03, off=T)
        # the X: two flat boards on the diagonals, proud of the wall face
        zt = top - 0.27
        def W(a_, z_):
            return (T + 0.03, -a_, z_) if axis == 'w' else (a_, -T - 0.03, z_)
        p.rod(W(0.17, 0.05), W(S - 0.17, zt), 0.045, TRIM, ink=True, seg=4)
        p.rod(W(S - 0.17, 0.05), W(0.17, zt), 0.045, TRIM, ink=True, seg=4)
    elif door == 'open':
        seg(0, 0.1, 0, top - 0.14, BARNRED); seg(S - 0.1, S, 0, top - 0.14, BARNRED)
        seg(0, S, top - 0.36, top - 0.14, BARNRED)
    seg(0, S, top - 0.14, top, TRIM, th=T + 0.04, off=-0.02)    # trim board along the top

def fence(p, axis, kind='fence'):
    """chain link on the north edge (axis 'n') or west edge ('w')."""
    h = 1.55
    def P(a, z, off=0.0):
        return (a, -off, z) if axis == 'n' else (off, -a, z)
    # post at the cell's start corner + top rail (ink on the post and rail)
    post = (0.04, 0.04) if axis == 'n' else (0.04, -0.04)
    if kind in ('fence', 'gate'):
        p.cyl(post[0], post[1], 0, h + 0.05, 0.045, STEEL)
        a, b = P(0, h), P(S, h)
        p.rod(a, b, 0.03, STEEL, ink=True)
    if kind == 'gate':          # gate frame pipe rectangle
        for (a0, z0, a1, z1) in ((0.15, 0.1, 0.15, h - 0.1), (S - 0.1, 0.1, S - 0.1, h - 0.1),
                                 (0.15, 0.1, S - 0.1, 0.1), (0.15, h - 0.1, S - 0.1, h - 0.1)):
            p.rod(P(a0, z0, 0.01), P(a1, z1, 0.01), 0.028, STEEL, ink=True)
    if kind == 'gate_open':     # post, then the gate leaf swung 90 deg into the cell
        p.cyl(post[0], post[1], 0, h + 0.05, 0.045, STEEL)
        L_ = S - 0.25
        for (a0, z0, a1, z1) in ((0.12, 0.1, 0.12, h - 0.1), (L_, 0.1, L_, h - 0.1),
                                 (0.12, 0.1, L_, 0.1), (0.12, h - 0.1, L_, h - 0.1)):
            q = lambda a, z: (0.06, -a, z) if axis == 'n' else (a, -0.06, z)
            p.rod(q(a0, z0), q(a1, z1), 0.028, STEEL, ink=True)
        return
    # diamond mesh: diagonal wires both ways, no ink (they read as a grey mesh)
    a0, a1 = (0.15, S - 0.1) if kind == 'gate' else (0.0, S)
    step = 0.13
    k = -h
    while k < (a1 - a0):
        for sgn in (1, -1):
            # wire from (a0+k, 0) rising at 45 deg
            za, zb = 0.05, h - 0.02
            aa, ab = a0 + k + (0 if sgn > 0 else (zb - za)), a0 + k + ((zb - za) if sgn > 0 else 0)
            # clip to [a0, a1]
            def clip(aa, za, ab, zb):
                if aa > ab: aa, za, ab, zb = ab, zb, aa, za
                if ab < a0 or aa > a1: return None
                if aa < a0: za = za + (zb - za) * (a0 - aa) / (ab - aa); aa = a0
                if ab > a1: zb = za + (zb - za) * (a1 - aa) / (ab - aa); ab = a1
                return aa, za, ab, zb
            c = clip(aa, za, ab, zb)
            if c: p.rod(P(c[0], c[1], 0.005), P(c[2], c[3], 0.005), 0.007, WIRE, ink=False, seg=4)
        k += step

def crate(p, opened=False, seed=0):
    w, d, h = 0.95, 0.95, 0.78
    x0, y0 = (S - w) / 2, -(S + d) / 2
    if not opened:
        p.box(x0, x0 + w, y0, y0 + d, 0, h, WOOD, jitter=0.02)
        # slats: darker boards proud on the two visible faces
        for z in (0.12, 0.38, 0.64):
            p.box(x0 - 0.015, x0 + w + 0.015, y0 - 0.015, y0 + 0.02, z, z + 0.08, WOOD_D)
            p.box(x0 + w - 0.02, x0 + w + 0.015, y0 - 0.015, y0 + d + 0.015, z, z + 0.08, WOOD_D)
        p.box(x0 + 0.05, x0 + w - 0.05, y0 + 0.05, y0 + d - 0.05, h, h + 0.03, WOOD)  # lid
        for q in (0.3, 0.62):
            p.box(x0 + 0.05, x0 + w - 0.05, y0 + d * q, y0 + d * q + 0.07, h + 0.03, h + 0.05, WOOD_D)
    else:
        t = 0.05
        p.box(x0, x0 + w, y0, y0 + t, 0, h, WOOD)            # south side
        p.box(x0, x0 + w, y0 + d - t, y0 + d, 0, h, WOOD)    # north side
        p.box(x0, x0 + t, y0, y0 + d, 0, h, WOOD)            # west side
        p.box(x0 + w - t, x0 + w, y0, y0 + d, 0, h, WOOD)    # east side
        p.box(x0 + t, x0 + w - t, y0 + t, y0 + d - t, 0, 0.35, (0.80, 0.70, 0.40))  # straw inside
        # lid leaning against the south-west of the crate
        p.box(x0 - 0.22, x0 - 0.17, y0 + 0.05, y0 + d - 0.05, 0, 0.62, WOOD_D)

def drum(p):
    cx, cy = S / 2, -S / 2
    p.cyl(cx, cy, 0, 0.9, 0.29, DRUM, seg=16)
    for z in (0.3, 0.6):
        p.cyl(cx, cy, z, z + 0.035, 0.30, (0.55, 0.10, 0.07), seg=16)
    p.cyl(cx + 0.12, cy + 0.05, 0.9, 0.93, 0.04, STEEL, seg=8)   # bung

def bush(p, seed=3):
    rnd = random.Random(seed); cx, cy = S / 2, -S / 2
    p.rod((cx, cy, 0), (cx - 0.08, cy + 0.05, 0.4), 0.05, BARK, ink=True)
    p.rod((cx, cy, 0), (cx + 0.12, cy - 0.06, 0.35), 0.04, BARK, ink=True)
    for i in range(6):
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(0.1, 0.32)
        p.blob(cx + r * math.cos(a), cy + r * math.sin(a), rnd.uniform(0.35, 0.7),
               rnd.uniform(0.24, 0.34), rnd.uniform(0.24, 0.34), rnd.uniform(0.13, 0.18), LEAF, seed=seed + i)

def rock(p, seed=5):
    p.blob(S / 2, -S / 2, 0.2, 0.5, 0.42, 0.42, ROCK, sub=2, rough=0.22, seed=seed)
    p.blob(S / 2 + 0.32, -S / 2 - 0.25, 0.08, 0.2, 0.18, 0.16, ROCK, sub=1, rough=0.2, seed=seed + 9)

def floor(p, kind):
    if kind == 'caliche':
        p.ground(CALICHE, speck=((0.06, CAL_DARK), (0.03, (0.93, 0.87, 0.72))), seed=11)
    elif kind == 'scrub':
        p.ground(CALICHE, speck=((0.35, SCRUB), (0.12, CAL_DARK)), seed=12)
        rnd = random.Random(4)
        for i in range(7):    # little grass tufts (no ink)
            x, y = rnd.uniform(0.15, S - 0.15), -rnd.uniform(0.15, S - 0.15)
            for j in range(3):
                p.rod((x, y, 0), (x + rnd.uniform(-.06, .06), y + rnd.uniform(-.06, .06), rnd.uniform(.12, .22)), 0.012, (0.42, 0.45, 0.20), seg=4)
    elif kind == 'concrete':
        p.ground(CONCRETE, speck=((0.08, (0.55, 0.55, 0.53)),), seed=13)

