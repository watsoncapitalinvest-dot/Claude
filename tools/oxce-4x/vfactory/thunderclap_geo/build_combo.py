"""Thunderclap, all three hitched (travel mode): the battle tractor (tracked, front) + the cannon base (TechnoViper3D kit platform,
legs-up base, short 'transport' cannon, seat, two rear mini-guns) + the battle trailer (wheeled, rear).
Positions from the kit's own layout, which lays the three out hitched along kit +Y (front tractor 189..412, platform -227..235,
rear tractor -385..-187); the kit frame is turned so kit +Y = model +X (front). Cannon on its trunnion, elevated ELEV deg like the box art.
python3 build_combo.py d_tractor.blend d_trailer.blend KIT_FILES out.blend [elev]"""
import bpy, bmesh, sys, os, math, tempfile, numpy as np
from mathutils import Vector, Matrix
from PIL import Image
TR, TL, KD, OUT = sys.argv[1:5]; FIRE = os.environ.get('MODE') == 'fire'   # MODE=fire: parked firing position (legs down, long barrel, the two unhitched)
ELEV = float(sys.argv[5]) if len(sys.argv) > 5 else (40.0 if FIRE else 22.0)
GAP = 110.0 if FIRE else 0.0
TMP = tempfile.mkdtemp()
bpy.ops.wm.open_mainfile(filepath=TR)
for o in list(bpy.data.objects):
    if o.name == 'fullfly': bpy.data.objects.remove(o)
# kit frame -> model frame: X = kitY, Y = -kitX, Z = kitZ + dz
K2M = Matrix(((0, 1, 0, 0), (-1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
for o in bpy.data.objects:
    if o.type == 'MESH': o.data.transform(Matrix.Translation((300.5 + GAP, -1.0, 0.0)))
with bpy.data.libraries.load(TL) as (src, dst): dst.objects = [n for n in src.objects if n != 'fullfly']
for o in dst.objects:
    bpy.context.scene.collection.objects.link(o)
    if o.type == 'MESH': o.data = o.data.copy(); o.data.transform(Matrix.Translation((-286.25 - GAP, 6.5, 0.0)))
PAL = {'olive': (60, 72, 60), 'olive_dk': (44, 54, 46), 'deck': (112, 122, 120), 'gun': (118, 126, 132), 'gun_dk': (78, 84, 90),
       'barrel': (196, 198, 196), 'tan': (214, 200, 170), 'orange': (244, 128, 28), 'legs': (122, 128, 136)}
MAT = {}
def mat(n):
    if n in MAT: return MAT[n]
    p = f'{TMP}/col_tc_{n}.png'; Image.new('RGB', (4, 4), PAL[n]).save(p)
    im = bpy.data.images.load(p); im.pack()
    m = bpy.data.materials.new(f'tc_{n}'); m.use_nodes = True; nt = m.node_tree
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; t.interpolation = 'Closest'
    nt.links.new(t.outputs[0], nt.nodes['Principled BSDF'].inputs['Base Color']); MAT[n] = m; return m
def load(n, name, faces=20000):
    bpy.ops.wm.stl_import(filepath=f'{KD}/Thunderclap_{n}.stl'); o = bpy.context.selected_objects[0]; o.name = name
    if len(o.data.polygons) > faces:
        d = o.modifiers.new('d', 'DECIMATE'); d.ratio = faces / len(o.data.polygons)
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier='d')
    o.data.uv_layers.new(name='uv')     # one-colour images: any UV works, the renderer's texture pass needs one
    return o
def paint(o, rule, names):
    o.data.materials.clear()
    for n in names: o.data.materials.append(mat(n))
    idx = {n: i for i, n in enumerate(names)}
    for p in o.data.polygons: p.material_index = idx[rule(Vector(p.center), Vector(p.normal))]
DZ = -1.5 if FIRE else 3.0   # fire: hull sits on the legs-down base's hub; platform: front hitch sits 1.5 mm lower, rear 7.5 higher than the layout; split
# --- platform (kit coords while painting) ---
pl = load('Platform', 'platform', 30000)
def pl_rule(c, n):
    if abs(c.y - 15.7) < 70 and c.z > 125: return 'gun'          # trunnion towers
    if c.z > 128 and n.z > 0.6: return 'deck'                      # deck tops
    if abs(c.y) > 200: return 'deck'                               # end rails
    if abs(c.x) > 44 or c.z < 70 or n.z < -0.5: return 'olive'     # outer hull skin
    return 'deck'
paint(pl, pl_rule, ['olive', 'deck', 'gun'])
# --- legs-up base: plate under the pivot pin (pin bottom at kit z 24), legs folded up beside the hull ---
if FIRE:
    bs = load('Platform_Base_-_Legs_Down', 'base'); bs.data.transform(Matrix.Translation((0, 10.7, 224.5)))   # flat on the ground, hub under the pivot pin
else:
    bs = load('Platform_Base_-_Legs_Up', 'base'); bs.data.transform(Matrix.Translation((0, 0, 128.0)))
paint(bs, lambda c, n: 'legs', ['legs'])
# --- cannon (short = transport barrel), trunnion on the tower hole (kit Y 15.7, Z 140.7) ---
PIV = Vector((0, 15.7, 140.7)); ROT = Matrix.Translation(PIV) @ Matrix.Rotation(math.radians(ELEV), 4, 'X') @ Matrix.Translation(-PIV)
cn = load('Cannon_Long' if FIRE else 'Cannon_Short', 'cannon', 30000); cn.data.transform(Matrix.Translation((0, 0, -117.8 if FIRE else -391.9)))
BARREL_Y = 300 if FIRE else 220
def cn_rule(c, n):
    if c.y > BARREL_Y: return 'barrel'
    if c.z < 150: return 'gun_dk'          # elevation gear sector under the breech
    return 'gun'
paint(cn, cn_rule, ['gun', 'gun_dk', 'barrel']); cn.data.transform(ROT)
st = load('Cannon_Seat', 'seat'); st.data.transform(Matrix.Translation((70.0, 0, -117.8)))   # bar into the cannon; the seat box sits against its side (photos 18/19); paint(st, lambda c, n: 'tan', ['tan']); st.data.transform(ROT)
OBJ = [pl, bs, cn, st]
# --- rear mini-guns on posts at the rear tub corners (photos 18/19/22): stood up, seated on the deck by ray ---
g0 = load('_Mounted_Gun', 'mg')
v = np.array([x.co for x in g0.data.vertices]); g0.data.transform(Matrix.Translation(Vector(-(v.min(0) + v.max(0)) / 2)))
g0.data.transform(Matrix.Rotation(math.radians(90), 4, 'Y'))       # post (kit +X end is its foot) -> up
g0.data.transform(Matrix.Rotation(math.radians(180), 4, 'Z'))      # barrels (kit +Y) -> aft, as in photos 19/22
paint(g0, lambda c, n: 'orange', ['orange'])
g1 = g0.copy(); g1.data = g0.data.copy(); bpy.context.scene.collection.objects.link(g1)
g1.data.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
bm = bmesh.new(); bm.from_mesh(g1.data); bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(g1.data); bm.free()
bpy.context.view_layer.update()
for g, sx, nm in ((g0, 46.0, 'mg_R'), (g1, -46.0, 'mg_L')):
    hit = pl.ray_cast(Vector((sx, -92.0, 400)), Vector((0, 0, -1))); zt = hit[1].z if hit[0] else 140.0
    vv = np.array([x.co for x in g.data.vertices]); c = (vv.min(0) + vv.max(0)) / 2
    post = vv[vv[:, 2] < vv[:, 2].min() + 5]; px, py = post[:, 0].mean(), post[:, 1].mean()   # the post's foot goes on the spot
    g.data.transform(Matrix.Translation((sx - px, -92.0 - py, zt - vv[:, 2].min()))); g.name = nm
    print('MG', nm, 'deck z', round(zt, 1)); OBJ.append(g)
for o in OBJ: o.data.transform(Matrix.Translation((0, 0, DZ))); o.data.transform(K2M)
for o in bpy.data.objects:
    if o.type == 'MESH':
        v = np.array([o.matrix_world @ x.co for x in o.data.vertices])
        print(o.name.ljust(20), np.round(v.min(0), 1), np.round(v.max(0), 1))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
