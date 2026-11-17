# Dress a civilian .blend as a cartel member: recolour garments, add rigid gear (bandana, vest, helmet, cap, hat,
# sunglasses, chain) bound to the mixamo skeleton. Usage: python3 -I make_cartel.py SPEC.json NAME
import bpy, bmesh, json, sys, math
import numpy as np
from mathutils import Vector, Matrix

spec = json.load(open(sys.argv[1]))[sys.argv[2]]
bpy.ops.wm.open_mainfile(filepath=f"/tmp/claude-0/ws/civ/{spec['base']}.blend")
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
AW = arm.matrix_world

def bone_head(b): return AW @ arm.data.bones['mixamorig:' + b].head_local
def bone_tail(b): return AW @ arm.data.bones['mixamorig:' + b].tail_local

# ---- world rest vertices with their dominant bone ----
V, G, HAIRV = [], [], []
for o in meshes:
    names = {vg.index: vg.name.replace('mixamorig:', '') for vg in o.vertex_groups}
    hair = 'hair' in o.name.lower() or any('hair' in (m.name.lower() if m else '') for m in o.data.materials[:1])
    mw = o.matrix_world
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight).group if v.groups else -1
        (HAIRV if hair else V).append(tuple(mw @ v.co)); (G.append(names.get(g, '')) if not hair else None)
V = np.array(V); G = np.array(G); HAIRV = np.array(HAIRV) if HAIRV else np.zeros((0, 3))

head = V[G == 'Head']
hz0, hz1 = head[:, 2].min(), max(head[:, 2].max(), HAIRV[:, 2].max() if len(HAIRV) else 0)
H = head[:, 2].max() - hz0
cx, cy = np.median(head[:, 0]), np.median(head[:, 1])

def band(P, z0, z1):
    s = P[(P[:, 2] >= z0) & (P[:, 2] <= z1)]
    return s

def ellipse(P, z0, z1, m):
    s = band(P, z0, z1)
    if len(s) < 8: s = band(P, z0 - 0.02, z1 + 0.02)
    ax = np.abs(s[:, 0] - cx).max() + m
    af = (cy - s[:, 1].min()) + m      # front is -Y
    ab = (s[:, 1].max() - cy) + m
    return ax, af, ab

def ring_pts(ax, af, ab, z, n, drop=None):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n          # a=0 front (-Y)
        x = ax * math.sin(a); c = math.cos(a)
        y = cy - af * c if c > 0 else cy - ab * c
        zz = z - (drop(c) if drop else 0)
        pts.append((cx + x, y, zz))
    return pts

GEAR = []   # (bmesh, rgb, bonefn)

def tube(rows, rgb, bonefn, cap_top=False):
    bm = bmesh.new(); n = len(rows[0])
    vs = [[bm.verts.new(p) for p in r] for r in rows]
    for j in range(len(rows) - 1):
        for i in range(n):
            bm.faces.new((vs[j][i], vs[j][(i + 1) % n], vs[j + 1][(i + 1) % n], vs[j + 1][i]))
    if cap_top: bm.faces.new(vs[-1][::-1])
    GEAR.append((bm, rgb, bonefn))

def head_bone(p): return 'Head'

def bandana(rgb):
    z0, z1 = hz0 + 0.10 * H, hz0 + 0.42 * H
    rows = []
    for k, z in enumerate(np.linspace(z0, z1, 4)):
        ax, af, ab = ellipse(head, z - 0.01, z + 0.01, 0.009)
        drop = (lambda c: 0.07 * max(0, c) ** 2) if k == 0 else None
        rows.append(ring_pts(ax, af, ab, z, 28, drop))
    tube(rows, rgb, head_bone)

def dome(rgb, zcut, m, brim=0.0, top_extra=0.0):
    # smooth half-ellipsoid: footprint = widest head ring between zcut and the brow, height to the hair top
    allh = np.vstack([head, HAIRV]) if len(HAIRV) else head
    ax, af, ab = 0, 0, 0
    for z in np.linspace(zcut, zcut + 0.25 * H, 5):
        a = ellipse(head, z - 0.012, z + 0.012, m); ax, af, ab = max(ax, a[0]), max(af, a[1]), max(ab, a[2])
    sz = (hz1 - zcut) + m * 0.8 + top_extra
    rows = []
    for t in np.linspace(0, 1, 9):
        th = t * math.pi / 2; r = math.cos(th); z = zcut + sz * math.sin(th)
        if t == 1: r = 0.0
        rows.append(ring_pts(ax * r, af * r, ab * r, z, 28))
    tube(rows, rgb, head_bone)
    if brim:
        inner = ring_pts(ax, af, ab, zcut, 28); outer = []
        for i, p in enumerate(inner):
            c = math.cos(2 * math.pi * i / 28)
            outer.append((p[0] + (p[0] - cx) * 0.15 * max(0, c), p[1] - brim * max(0, c) ** 1.5, p[2] - 0.006))
        tube([inner, outer], rgb, head_bone)

def cowboy(rgb):
    allh = np.vstack([head, HAIRV]) if len(HAIRV) else head
    zc = hz0 + 0.72 * H
    ax, af, ab = ellipse(allh, zc - 0.012, zc + 0.012, 0.012)
    rows = [ring_pts(ax, af, ab, zc, 28), ring_pts(ax * 0.95, af * 0.92, ab * 0.92, hz1 + 0.07, 28)]
    tube(rows, rgb, head_bone, cap_top=True)
    # brim: flat ring, sides turned up
    inner = ring_pts(ax, af, ab, zc, 28)
    outer = []
    for i in range(28):
        a = 2 * math.pi * i / 28; s = abs(math.sin(a))
        outer.append((cx + (ax + 0.085) * math.sin(a), cy - (af + 0.085) * math.cos(a) if math.cos(a) > 0 else cy - (ab + 0.075) * math.cos(a), zc + 0.035 * s ** 2))
    tube([inner, outer], rgb, head_bone)

def sunglasses(rgb):
    ze = hz0 + 0.53 * H
    ax, af, ab = ellipse(head, ze - 0.01, ze + 0.01, 0.007)
    bm = bmesh.new(); top, bot = [], []
    for i in range(13):
        a = -1.25 + 2.5 * i / 12
        p = (cx + ax * math.sin(a), cy - af * math.cos(a))
        bot.append(bm.verts.new((p[0], p[1], ze - 0.016))); top.append(bm.verts.new((p[0], p[1], ze + 0.014)))
    for i in range(12): bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
    GEAR.append((bm, rgb, head_bone))

def chain(rgb):
    neck = V[(G == 'Neck') | (G == 'Spine2')]
    zn = bone_head('Neck')[2] - 0.005
    s = neck[(neck[:, 2] > zn - 0.02) & (neck[:, 2] < zn + 0.02)]
    ax = np.abs(s[:, 0] - cx).max() * 0.75 + 0.012; af = (cy - s[:, 1].min()) + 0.012; ab = (s[:, 1].max() - cy) + 0.01
    def drop(c): return 0.12 * max(0, c) ** 2
    r1 = ring_pts(ax, af, ab, zn, 32, drop)
    # follow the chest outward as it drops
    chest = V[(G == 'Spine2')]
    r1 = [(p[0], min(p[1], np.percentile(chest[np.abs(chest[:, 2] - p[2]) < 0.02][:, 1], 1) - 0.006) if (p[1] < cy and np.any(np.abs(chest[:, 2] - p[2]) < 0.02)) else p[1], p[2]) for p in r1]
    r2 = [(p[0], p[1] - 0.004, p[2] - 0.018) for p in r1]
    tube([r2, r1], rgb, lambda p: 'Spine2' if p[2] < zn - 0.03 else 'Neck')

def vest(rgb, pouch_rgb):
    xs = abs(bone_head('LeftArm')[0] - cx) * 0.92
    torso = V[(np.abs(V[:, 0] - cx) < xs) & ~np.isin(G, ['Head', 'Neck'])]
    za = bone_head('Spine')[2] + 0.03; zb = bone_tail('Spine2')[2] - 0.035
    rows = []
    for z in np.linspace(za, zb, 7):
        s = torso[np.abs(torso[:, 2] - z) < 0.015]
        ax = np.abs(s[:, 0] - cx).max() + 0.018; af = (cy - s[:, 1].min()) + 0.022; ab = (s[:, 1].max() - cy) + 0.018
        rows.append(ring_pts(ax, af, ab, z, 32))
    # narrow the top row's sides so the arms stay free
    rows[-1] = [(cx + (p[0] - cx) * 0.8, p[1], p[2]) for p in rows[-1]]
    zs = [bone_head(b)[2] for b in ('Spine1', 'Spine2')]
    sp = lambda p: 'Spine' if p[2] < zs[0] else ('Spine1' if p[2] < zs[1] else 'Spine2')
    tube(rows, rgb, sp)
    # three mag pouches across the front
    zp = za + 0.25 * (zb - za)
    s = torso[np.abs(torso[:, 2] - zp) < 0.02]; fy = s[:, 1].min() - 0.024
    for dx in (-0.075, 0.0, 0.075):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts: v.co = Vector((cx + dx + v.co.x * 0.062, fy - 0.016 + v.co.y * 0.034, zp + 0.02 + v.co.z * 0.085))
        GEAR.append((bm, pouch_rgb, sp))

# ---- build gear objects ----
gmat = bpy.data.materials.new('cartel_gear'); gmat.use_nodes = True
nt = gmat.node_tree; [nt.nodes.remove(n) for n in list(nt.nodes)]
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

def lin(c): return [((x / 255) / 12.92 if x / 255 <= 0.04045 else ((x / 255 + 0.055) / 1.055) ** 2.4) for x in c]

for k in spec.get('gear', []):
    kind, *args = k
    {'bandana': bandana, 'dome': lambda rgb: dome(rgb, hz0 + 0.60 * H, 0.022), 'cap': lambda rgb: dome(rgb, hz0 + 0.66 * H, 0.014, brim=0.075),
     'cowboy': cowboy, 'sunglasses': sunglasses, 'chain': chain, 'vest': vest}[kind](*args)

for idx, (bm, rgb, bonefn) in enumerate(GEAR):
    me = bpy.data.meshes.new(f'gear{idx}'); bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(f'Gear{idx}', me); bpy.context.scene.collection.objects.link(ob)
    me.materials.append(gmat)
    ca = me.color_attributes.new('gcol', 'FLOAT_COLOR', 'CORNER'); c = lin(rgb) + [1]
    for l in ca.data: l.color = c
    for b in set(bonefn(tuple(v.co)) for v in me.vertices): ob.vertex_groups.new(name='mixamorig:' + b)
    for v in me.vertices: ob.vertex_groups['mixamorig:' + bonefn(tuple(v.co))].add([v.index], 1.0, 'REPLACE')
    # outward-facing normals: flip if most face the centre
    ob.parent = arm; ob.matrix_parent_inverse = arm.matrix_world.inverted()
    mod = ob.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
    for p in me.polygons: p.use_smooth = True

# ---- garment recolour (luminance-preserving) ----
def mean_lum(o, img):
    w, h = img.size; px = np.array(img.pixels[:]).reshape(h, w, 4)
    uv = np.array([d.uv for d in o.data.uv_layers.active.data])
    xs = np.clip((uv[:, 0] % 1) * w, 0, w - 1).astype(int); ys = np.clip((uv[:, 1] % 1) * h, 0, h - 1).astype(int)
    c = px[ys, xs, :3]; return float((c @ np.array([0.2126, 0.7152, 0.0722])).mean())

def recolour(o, rgb, huekey=None):
    m0 = o.data.materials[0]; m = m0.copy(); m.name = m0.name + '_' + o.name
    o.data.materials[0] = m
    for i in range(1, len(o.data.materials)):
        if o.data.materials[i] == m0: o.data.materials[i] = m
    nt = m.node_tree; tex = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]; em = [n for n in nt.nodes if n.type == 'EMISSION'][0]
    ref = mean_lum(o, tex.image) if not huekey else 0.5
    bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(tex.outputs['Color'], bw.inputs[0])
    t = lin(rgb); s = 1.0 / max(ref, 0.03)
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1.0
    mix.clamp_result = True
    nt.links.new(bw.outputs[0], mix.inputs['A']); mix.inputs['B'].default_value = [min(x * s, 8) for x in t] + [1]
    res = mix.outputs['Result']
    if huekey:   # only pixels in a hue band (single-mesh bodies)
        hsv = nt.nodes.new('ShaderNodeSeparateColor'); hsv.mode = 'HSV'; nt.links.new(tex.outputs['Color'], hsv.inputs[0])
        lo = nt.nodes.new('ShaderNodeMath'); lo.operation = 'GREATER_THAN'; lo.inputs[1].default_value = huekey[0]
        hi = nt.nodes.new('ShaderNodeMath'); hi.operation = 'LESS_THAN'; hi.inputs[1].default_value = huekey[1]
        sa = nt.nodes.new('ShaderNodeMath'); sa.operation = 'GREATER_THAN'; sa.inputs[1].default_value = huekey[2]
        for n in (lo, hi): nt.links.new(hsv.outputs[0], n.inputs[0])
        nt.links.new(hsv.outputs[1], sa.inputs[0])
        a1 = nt.nodes.new('ShaderNodeMath'); a1.operation = 'MULTIPLY'; nt.links.new(lo.outputs[0], a1.inputs[0]); nt.links.new(hi.outputs[0], a1.inputs[1])
        a2 = nt.nodes.new('ShaderNodeMath'); a2.operation = 'MULTIPLY'; nt.links.new(a1.outputs[0], a2.inputs[0]); nt.links.new(sa.outputs[0], a2.inputs[1])
        sel = nt.nodes.new('ShaderNodeMix'); sel.data_type = 'RGBA'
        nt.links.new(a2.outputs[0], sel.inputs['Factor']); nt.links.new(tex.outputs['Color'], sel.inputs['A']); nt.links.new(res, sel.inputs['B'])
        res = sel.outputs['Result']
    nt.links.new(res, em.inputs['Color'])

for mesh_name, rgb, *hk in spec.get('tint', []):
    recolour(bpy.data.objects[mesh_name], rgb, hk[0] if hk else None)

bpy.ops.wm.save_as_mainfile(filepath=f"/tmp/claude-0/ws/chars/{sys.argv[2]}.blend", compress=True)
print('saved', sys.argv[2], len(GEAR), 'gear pieces', 'materials', len([m for m in bpy.data.materials if m.users]))
