"""Thunderclap tractor / trailer vehicle: MAPS' cut of John's Generals mesh -> painted game model with the toy's weapons.
python3 build.py tractor|trailer in_dir out.blend
Model units = Generals units (0.26 m). +X = front. Z up, ground at 0.
Paint follows the 1984 toy photos (Reference\\vehicles_generals\\thunderclap_ref): cream upper body, grey hull, black running gear,
smoked glass, orange missiles, grey guns. One 4x4 PNG per colour (ROSTER's convention, flat cel paint)."""
import bpy, bmesh, sys, os, math, tempfile
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from PIL import Image
V, IN, OUT = sys.argv[1:4]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=f'{IN}/thunderclap_{V}.obj', forward_axis='NEGATIVE_Z', up_axis='Y')
src = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
bpy.context.view_layer.objects.active = src; src.select_set(True); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
TMP = tempfile.mkdtemp()
PAL = {'cream': (226, 214, 184), 'cream_sh': (196, 184, 156), 'grey': (112, 118, 128), 'grey_dk': (78, 82, 90), 'gun': (150, 156, 166),
       'black': (30, 30, 33), 'tyre': (36, 36, 38), 'skirt': (132, 138, 146), 'glass': (64, 54, 46), 'orange': (244, 128, 28),
       'red': (196, 30, 36), 'white': (238, 238, 236), 'blue': (30, 52, 140), 'shield': (40, 80, 170), 'yellow': (236, 196, 40)}
MAT = {}
def mat(n):
    if n in MAT: return MAT[n]
    p = f'{TMP}/col_tc_{n}.png'; Image.new('RGB', (4, 4), PAL[n]).save(p)
    im = bpy.data.images.load(p); im.pack()
    m = bpy.data.materials.new(f'tc_{n}'); m.use_nodes = True; nt = m.node_tree
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; t.interpolation = 'Closest'
    nt.links.new(t.outputs[0], nt.nodes['Principled BSDF'].inputs['Base Color']); nt.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.8
    MAT[n] = m; return m
def setmats(o, names):
    o.data.materials.clear()
    for n in names: o.data.materials.append(mat(n))

# weld + split loose parts
bpy.context.view_layer.objects.active = src; src.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.01)
bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
parts = [o for o in bpy.context.scene.objects if o.type == 'MESH']
def bb(o):
    v = np.array([o.matrix_world @ x.co for x in o.data.vertices]); return v.min(0), v.max(0)
info = sorted([(o, *bb(o)) for o in parts], key=lambda r: -len(r[0].data.polygons))
for o in parts:
    for uv in list(o.data.uv_layers): pass

def bisect(o, co, no):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no)
    bm.to_mesh(o.data); bm.free()
def paint(o, rule, names):
    setmats(o, names); idx = {n: i for i, n in enumerate(names)}
    for p in o.data.polygons: p.material_index = idx[rule(Vector(p.center), Vector(p.normal))]

if V == 'tractor':
    body = info[0][0]; tracks = [r[0] for r in info[1:3]]
    for z in (5.0,): bisect(body, (0, 0, z), (0, 0, 1))
    bisect(body, (-2.5, 0, 0), (1, 0, 0))
    def r_body(c, n):
        if c.z < 5.0: return 'grey'
        if c.x < -2.5: return 'grey'                                   # rear engine block with the fins
        if c.x > 2.6 and c.z > 6.2 and n.x > 0.3 and n.z > -0.2: return 'glass'   # sloped windshield
        if c.x > 1.5 and c.z > 6.4 and abs(n.y) > 0.8 and c.z < 8.8: return 'glass' if c.x > 4.5 else 'cream'  # side window ahead of door
        return 'cream'
    paint(body, r_body, ['grey', 'cream', 'glass'])
    for t in tracks: paint(t, lambda c, n: 'black' if abs(n.y) < 0.85 else 'tyre', ['black', 'tyre'])
    hull = [body] + tracks
else:
    body, chassis = info[0][0], info[1][0]; wheels = [r[0] for r in info[2:4]]; antenna = info[4][0]
    bisect(body, (2.0, 0, 0), (1, 0, 0))
    def r_body(c, n):
        if c.x > 1.0 and c.z > 6.0 and n.x > 0.3: return 'glass'     # front screen
        return 'cream'
    paint(body, r_body, ['cream', 'glass'])
    paint(chassis, lambda c, n: 'black' if n.z > 0.5 else 'grey_dk', ['black', 'grey_dk'])
    for w in wheels: paint(w, lambda c, n: 'skirt' if abs(n.y) > 0.8 else 'tyre', ['skirt', 'tyre'])   # grey vented skirt over the 6 wheels
    paint(antenna, lambda c, n: 'orange', ['orange'])
    hull = [body, chassis] + wheels + [antenna]

# surface height lookup on the hull (raycast down)
bm = bmesh.new()
for o in hull:
    t = o.data.copy(); t.transform(o.matrix_world); bm.from_mesh(t)
tree = BVHTree.FromBMesh(bm)
def top(x, y):
    h = tree.ray_cast(Vector((x, y, 50)), Vector((0, 0, -1))); return h[0].z if h[0] else 0

def add(prim, name, colour, loc, rot=(0, 0, 0), scale=(1, 1, 1), **kw):
    getattr(bpy.ops.mesh, prim)(location=loc, rotation=rot, **kw); o = bpy.context.active_object; o.name = name; o.scale = scale
    bpy.ops.object.transform_apply(scale=True); setmats(o, [colour]); return o
def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); objs[0].name = name; return objs[0]
def missile(name, at, length, r, yaw=0.0, pitch=0.0):
    """orange missile along +X: body, nose cone, 4 fins; origin at its middle"""
    parts = [add('primitive_cylinder_add', name + '_b', 'orange', (0, 0, 0), (0, math.pi / 2, 0), vertices=10, radius=r, depth=length * 0.72),
             add('primitive_cone_add', name + '_n', 'orange', (length * 0.36 + length * 0.12, 0, 0), (0, math.pi / 2, 0), vertices=10, radius1=r, depth=length * 0.24)]
    for k in range(4):
        a = k * math.pi / 2
        parts.append(add('primitive_cube_add', name + f'_f{k}', 'orange', (-length * 0.3, math.cos(a) * r * 1.6, math.sin(a) * r * 1.6), (a, 0, 0), size=1, scale=(length * 0.12, 0.05, r * 1.4)))
    m = join(parts, name); m.rotation_euler = (0, -pitch, yaw); m.location = at
    bpy.ops.object.select_all(action='DESELECT'); m.select_set(True); bpy.context.view_layer.objects.active = m; bpy.ops.object.transform_apply(rotation=True, location=False)
    return m

stores = []
if V == 'tractor':
    # twin blaster cannon turret on the cab roof (toy: long grey twin barrels with cooling fins, on a ring)
    tx, ty = 1.0, 0.3; tz = top(tx, ty)
    ring = add('primitive_cylinder_add', 'tr_ring', 'gun', (tx, ty, tz + 0.35), vertices=16, radius=1.3, depth=0.7)
    house = add('primitive_cube_add', 'tr_house', 'gun', (tx + 0.3, ty, tz + 1.3), size=1, scale=(3.4, 2.4, 1.2))
    guns = [ring, house]
    for s in (-0.75, 0.75):
        guns.append(add('primitive_cylinder_add', 'tr_brl', 'gun', (tx + 4.6, ty + s, tz + 1.35), (0, math.pi / 2, 0), vertices=10, radius=0.28, depth=6.6))
        guns.append(add('primitive_cube_add', 'tr_jacket', 'grey_dk', (tx + 2.6, ty + s, tz + 1.35), size=1, scale=(1.6, 0.7, 0.7)))
        for k in range(4): guns.append(add('primitive_cube_add', 'tr_fin', 'gun', (tx + 5.4 + k * 0.45, ty + s, tz + 1.35), size=1, scale=(0.12, 0.75, 0.75)))
    turret = join(guns, 'turret')
    # two orange missiles on each track fender (toy: pairs on racks above the tracks)
    for side, ys in (('L', 6.0), ('R', -6.0)):
        for k, dx in enumerate((-1.6, 1.6)):
            z = top(dx, ys) + 1.1
            stores.append(missile(f'msl_{side}{k + 1}', (dx, ys, z), 4.6, 0.32))
    pivot = Vector((tx, ty, tz))
else:
    # single-barrel blaster on a round base (blueprint item 2), cab roof
    tx, ty = 0.8, 0.0; tz = top(tx, ty)
    base = add('primitive_cylinder_add', 'tt_base', 'gun', (tx, ty, tz + 0.6), vertices=16, radius=1.5, depth=1.2)
    cap = add('primitive_cylinder_add', 'tt_cap', 'grey_dk', (tx, ty, tz + 1.35), vertices=16, radius=1.1, depth=0.3)
    house = add('primitive_cube_add', 'tt_house', 'gun', (tx + 0.8, ty, tz + 1.75), size=1, scale=(2.6, 1.3, 0.9))
    brl = add('primitive_cylinder_add', 'tt_brl', 'gun', (tx + 4.4, ty, tz + 1.8), (0, math.pi / 2, 0), vertices=10, radius=0.3, depth=5.2)
    muz = add('primitive_cylinder_add', 'tt_muz', 'grey_dk', (tx + 7.1, ty, tz + 1.8), (0, math.pi / 2, 0), vertices=10, radius=0.42, depth=0.6)
    sign = add('primitive_cube_add', 'tt_sign', 'yellow', (tx, ty - 1.52, tz + 0.7), size=1, scale=(1.2, 0.05, 0.6))
    turret = join([base, cap, house, brl, muz, sign], 'turret')
    # pivoting 3-missile launcher on the rear deck, right side (toy photos 11, 13, 15)
    lx, ly = -4.4, -2.6; lz = top(lx, ly)
    post = add('primitive_cylinder_add', 'ln_post', 'orange', (lx, ly, lz + 0.6), vertices=10, radius=0.35, depth=1.2)
    cradle = add('primitive_cube_add', 'ln_cradle', 'orange', (lx, ly, lz + 1.35), size=1, scale=(2.4, 1.9, 0.3))
    join([post, cradle], 'launcher')
    for k, dy in enumerate((-0.7, 0.0, 0.7)):
        stores.append(missile(f'msl_{k + 1}', (lx + 0.4, ly + dy, lz + 1.85 + (0.25 if k == 1 else 0)), 3.8, 0.3, pitch=math.radians(20)))
    pivot = Vector((tx, ty, tz))
# ---- decals: drawn here (bars, shield shape); placed flush on the hull side by raycast; both sides ----
from PIL import ImageDraw
def decal_img(kind):
    p = f'{TMP}/dec_tc_{kind}.png'
    if kind in ('stripe', 'stripeL'):
        im = Image.new('RGB', (160, 40), PAL['cream']); d = ImageDraw.Draw(im)
        d.rectangle((0, 6, 70, 34), fill=(24, 32, 90)); d.text((8, 13), 'G.I.JOE', fill=PAL['white'])     # plain lettering, toy-style block
        for k, c in enumerate(('red', 'white', 'blue')): d.rectangle((74, 8 + k * 9, 159, 15 + k * 9), fill=PAL[c])
        if kind == 'stripeL':   # left side sticker: bars toward the nose, lettering still reads left to right
            im = Image.new('RGB', (160, 40), PAL['cream']); d = ImageDraw.Draw(im)
            d.rectangle((90, 6, 159, 34), fill=(24, 32, 90)); d.text((98, 13), 'G.I.JOE', fill=PAL['white'])
            for k, c in enumerate(('red', 'white', 'blue')): d.rectangle((0, 8 + k * 9, 85, 15 + k * 9), fill=PAL[c])
    else:
        im = Image.new('RGB', (64, 72), PAL['cream']); d = ImageDraw.Draw(im)
        d.polygon([(6, 6), (58, 6), (58, 38), (32, 68), (6, 38)], fill=PAL['shield'], outline=(250, 250, 250))
        d.polygon([(32, 14), (46, 44), (18, 44)], fill=PAL['yellow'])
    im.save(p); return p
def dmat(kind):
    m = bpy.data.materials.get('dec_' + kind)
    if m is None:
        m = bpy.data.materials.new('dec_' + kind); m.use_nodes = True; nt = m.node_tree
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(decal_img(kind)); t.image.pack(); t.interpolation = 'Closest'
        nt.links.new(t.outputs[0], nt.nodes['Principled BSDF'].inputs['Base Color'])
    return m
def decal(kind, x, z, w, h):
    for side in (1, -1):
        m = dmat(kind + 'L' if (kind == 'stripe' and side > 0) else kind)
        h_ = tree.ray_cast(Vector((x, side * 30, z)), Vector((0, -side, 0)))
        if not h_[0] or abs(h_[1].y) < 0.6: print('DECAL SKIP', kind, x, z, side); continue
        y = h_[0].y + side * 0.06
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, z), rotation=(math.pi / 2, 0, 0 if side < 0 else math.pi))
        o = bpy.context.active_object; o.name = f'decal_{kind}_{"L" if side > 0 else "R"}'; o.scale = (w, h, 1)
        bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
if V == 'tractor':
    decal('stripe', 4.0, 7.6, 4.0, 1.0); decal('shield', -0.9, 7.2, 1.2, 1.35)
else:
    # the toy's wide black deck between the wheels and the cab
    deck = add('primitive_cube_add', 'deck', 'black', (0, 0, 3.55), size=1, scale=(13.8, 9.0, 0.9))
    decal('stripe', 2.4, 5.7, 3.2, 0.8); decal('shield', -0.6, 6.5, 1.2, 1.35)
# turret pivot at the ring centre
bpy.context.scene.cursor.location = pivot
bpy.ops.object.select_all(action='DESELECT'); turret.select_set(True); bpy.context.view_layer.objects.active = turret
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
for o in bpy.context.scene.objects:
    if o.type == 'MESH' and not o.data.uv_layers: o.data.uv_layers.new()
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print('BUILT', V, 'turret pivot', tuple(round(x, 2) for x in pivot), 'stores', [s.name for s in stores])
