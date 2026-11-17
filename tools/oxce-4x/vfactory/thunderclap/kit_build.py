"""Thunderclap tractor (tracked) and trailer vehicle (wheeled), assembled from TechnoViper3D's kit (Thingiverse 6696177, 1:1 toy mm,
non-commercial) and painted to the 1984 toy photos. John 14:06: the kit is the whole thing, connected.
python3 kit_build.py tractor|trailer KIT_FILES_DIR out.blend
Output: mm, ground at z 0, +X = front, model centred. Objects: hull parts, 'turret' (pivot at its seat), stores msl_* (fire one by one).
Positions: kit assembly where the kit has it (wheeled cab, its missile rack, antenna, tracked body); measured joins for the rest
(treads under the fenders, wheel axles in the chassis box holes, chassis stub into the cab, guns on their roof posts);
the tracked vehicle's four side missiles from the toy photos (two per side: one high toward the rear, one low and forward)."""
import bpy, bmesh, sys, os, math, tempfile
import numpy as np
from mathutils import Vector, Matrix
from PIL import Image, ImageDraw
V, KD, OUT = sys.argv[1:4]
bpy.ops.wm.read_factory_settings(use_empty=True)
TMP = tempfile.mkdtemp()
PAL = {'cream': (226, 214, 184), 'grey': (112, 118, 128), 'grey_lt': (150, 156, 166), 'grey_dk': (74, 78, 86), 'gun': (150, 156, 166),
       'gun_dk': (60, 64, 70), 'black': (30, 30, 33), 'glass': (64, 54, 46), 'orange': (244, 128, 28), 'skirt': (140, 146, 154),
       'red': (196, 30, 36), 'white': (238, 238, 236), 'blue': (30, 52, 140), 'shield': (40, 80, 170), 'yellow': (236, 196, 40)}
MAT = {}
def mat(n):
    if n in MAT: return MAT[n]
    p = f'{TMP}/col_tk_{n}.png'; Image.new('RGB', (4, 4), PAL[n]).save(p)
    im = bpy.data.images.load(p); im.pack()
    m = bpy.data.materials.new(f'tk_{n}'); m.use_nodes = True; nt = m.node_tree
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; t.interpolation = 'Closest'
    nt.links.new(t.outputs[0], nt.nodes['Principled BSDF'].inputs['Base Color']); MAT[n] = m; return m
def load(n, name=None, faces=6000):
    bpy.ops.wm.stl_import(filepath=f'{KD}/Thunderclap_{n}.stl'); o = bpy.context.selected_objects[0]; o.name = name or n
    if len(o.data.polygons) > faces:
        d = o.modifiers.new('d', 'DECIMATE'); d.ratio = faces / len(o.data.polygons)
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier='d')
    return o
def vv(o): return np.array([o.matrix_world @ v.co for v in o.data.vertices])
def move(o, d): o.data.transform(Matrix.Translation(Vector(d)))
def mirror_x(o):
    o.data.transform(Matrix.Scale(-1, 4, (1, 0, 0))); bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(o.data); bm.free()
def dup(o, name):
    c = o.copy(); c.data = o.data.copy(); c.name = name; bpy.context.scene.collection.objects.link(c); return c
def paint(o, rule, names):
    o.data.materials.clear()
    for n in names: o.data.materials.append(mat(n))
    idx = {n: i for i, n in enumerate(names)}
    for p in o.data.polygons: p.material_index = idx[rule(Vector(p.center), Vector(p.normal))]
def flat(o, n): paint(o, lambda c, nn: n, [n])
def split_loose(o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    return list(bpy.context.selected_objects)
def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); objs[0].name = name; return objs[0]
def front_sign(o, zmin):
    """+1 if the windshield (big sloped glass face high up) faces +y, else -1"""
    s = 0.0
    for p in o.data.polygons:
        if p.center.z > zmin and p.normal.z > 0.25 and abs(p.normal.y) > 0.35: s += p.area * np.sign(p.normal.y)
    return 1 if s > 0 else -1

def seat_on(obj, hulls, skip_below=0.0):
    """drop obj until its underside (ignoring the lowest skip_below mm: a peg that goes into a hole) rests on the hulls straight below it"""
    from mathutils.bvhtree import BVHTree as _B
    bm_ = bmesh.new()
    for h in hulls:
        d_ = h.data.copy(); d_.transform(h.matrix_world); bm_.from_mesh(d_)
    tr_ = _B.FromBMesh(bm_); G_ = vv(obj); zmin = G_[:, 2].min() + skip_below; gaps = []
    for p in G_[G_[:, 2] >= zmin][::4]:
        h_ = tr_.ray_cast(Vector((p[0], p[1], p[2] - 0.01)), Vector((0, 0, -1)))
        if h_[0]: gaps.append(p[2] - h_[0].z)
    g = min(gaps) if gaps else 0.0; move(obj, (0, 0, -g)); return g
stores = []
if V == 'tractor':
    body = load('Front_Tractor', 'hull', 9000)
    fs = front_sign(body, 85); print('FRONT +y' if fs > 0 else 'FRONT -y')
    t1 = load('Front_Tread_2x', 'tread_R', 5000)
    # the print has the tread at its assembled height and length; only moved sideways for the bed. Its inner face (x 122) goes flush on
    # the lower hull side (x 35); the 10 mm hook tab (x 112) then sits in the hull's indentation (x 21..35), per instruction step 2.
    move(t1, (35 - 122, 0, 0))
    t2 = dup(t1, 'tread_L'); mirror_x(t2)
    # finned twin cannon: its 2.8 mm peg into the hole in the vehicle top (kit roof boss x 12..28, y 315..325, top z 137.5), step 8
    gun = load('Front_Tractor_Gun', 'turret', 5000); G = vv(gun)
    peg = G[G[:, 2] < G[:, 2].min() + 2]; pc = (peg.min(0) + peg.max(0)) / 2
    if fs > 0: gun.data.transform(Matrix.Translation(Vector((pc[0], pc[1], 0))) @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Translation(Vector((-pc[0], -pc[1], 0))))
    G = vv(gun); peg = G[G[:, 2] < G[:, 2].min() + 2]; pc = (peg.min(0) + peg.max(0)) / 2
    B = vv(body); boss = B[B[:, 2] > B[:, 2].max() - 3]; poc = (boss.min(0) + boss.max(0)) / 2
    move(gun, (poc[0] - pc[0], poc[1] - pc[1], B[:, 2].max() - (G[:, 2].min() + 2.8)))
    dropped = seat_on(gun, [body], 3.0)
    # the kit's thin post leaves the gun body ~25 mm over the roof and the post vanishes at game size, so the gun reads as floating.
    # Blueprint (ref 03, item 7): the gun body sits just over the cab top. Sink the post until the body (the wide part) clears it by 5 mm.
    G = vv(gun); zs = np.linspace(G[:, 2].min(), G[:, 2].max(), 60); wmax = np.ptp(G[:, 1])
    def _w(z):
        sl = G[(G[:, 2] >= z) & (G[:, 2] < z + 1.5)]; return np.ptp(sl[:, 1]) if len(sl) else 0
    body_bot = next(z for z in zs if _w(z) > 0.5 * wmax)
    under = G[:, 2].min() + 0.0
    from mathutils.bvhtree import BVHTree as _B
    _bm = bmesh.new(); _d = body.data.copy(); _bm.from_mesh(_d); _tr = _B.FromBMesh(_bm)
    wide = G[(G[:, 2] >= body_bot) & (G[:, 2] < body_bot + 2)]
    roof_under = max(_tr.ray_cast(Vector((p[0], p[1], p[2] - 0.01)), Vector((0, 0, -1)))[0].z for p in wide[::3] if _tr.ray_cast(Vector((p[0], p[1], p[2] - 0.01)), Vector((0, 0, -1)))[0])
    sink = max(0.0, body_bot - (roof_under + 5.0)); move(gun, (0, 0, -sink)); dropped += sink
    # the gun's finned rear rides over the tall engine block, so it cannot come lower; give it a solid pedestal (toy bracket, photo 25)
    G = vv(gun); body_bot -= sink
    _rz = _tr.ray_cast(Vector((pc[0] + (poc[0] - pc[0]), pc[1] + (poc[1] - pc[1]), body_bot)), Vector((0, 0, -1)))[0]
    roof_at_post = _rz.z if _rz else body_bot - 20
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=9.0, depth=body_bot - roof_at_post + 2, location=(poc[0], poc[1], (body_bot + roof_at_post) / 2))
    ped = bpy.context.active_object; ped.name = 'pedestal'; bpy.ops.object.transform_apply(location=True)
    print('GUN tractor dropped', round(dropped, 2), 'post sunk', round(sink, 2), 'pedestal h', round(body_bot - roof_at_post, 1))
    pivot = Vector((poc[0], poc[1], B[:, 2].max() - dropped))
    # three kit missiles on the two side tabs (step 8; kit tabs measured): right tab x +60, y 268..283, z 62..67 holds ONE;
    # left double tab x -58, y 243..289, z 62..73 holds TWO, the upper one further back (toy photo 25)
    m0 = load('Front_Missile_3x', 'msl_proto', 3000)
    if fs > 0: m0.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))
    M = vv(m0); move(m0, tuple(-(M.min(0) + M.max(0)) / 2)); r = 2.8
    for name, (x, y, z) in (('msl_R1', (60 + r, 275.5, 64.5 + r)), ('msl_L1', (-58 - r, 278.0, 62.0 + r)), ('msl_L2', (-58 - r, 254.0, 73.4 + r))):
        m = dup(m0, name); move(m, (x, y, z)); stores.append(m)
    bpy.data.objects.remove(m0)
    B = vv(body); y0, y1 = B[:, 1].min(), B[:, 1].max(); L = y1 - y0
    def along(t): return (y1 - t * L) if fs > 0 else (y0 + t * L)
    # paint (toy): cream cab + upper front, grey rear block and lower hull, smoked glass, black treads
    B = vv(body); zc = B[:, 2].min(); H = np.ptp(B[:, 2]); cab_rear = along(0.62)
    def r_body(c, n):
        fwd = (c.y - cab_rear) * fs                                   # >0 = ahead of the rear block
        if c.z < zc + 0.48 * H: return 'grey'                         # grey lower hull up to the fender line (toy)
        if fwd < 0: return 'grey'
        if c.z > zc + 0.62 * H and n.z > 0.2 and n.y * fs > 0.3: return 'glass'      # windshield
        if c.z > zc + 0.6 * H and abs(n.x) > 0.85 and fwd > 0.25 * L and c.z < zc + 0.92 * H: return 'glass'  # side windows
        return 'cream'
    paint(body, r_body, ['grey', 'cream', 'glass'])
    for t in (t1, t2): paint(t, lambda c, n: 'grey_dk' if abs(n.x) > 0.9 and abs(c.x) > 60 and c.z > 12 and c.z < 48 else 'black', ['black', 'grey_dk'])
    paint(gun, lambda c, n: 'gun_dk' if c.z > pivot.z + 25 else 'gun', ['gun', 'gun_dk'])
    ped = bpy.data.objects['pedestal']; flat(ped, 'gun_dk'); gun = join([gun, ped], 'turret')
    for s in stores: paint(s, lambda c, n: 'orange', ['orange'])
    hull_objs = [body, t1, t2]
else:
    top = load('Rear_Tractor_Top', 'hull', 9000); fs = 1                  # antenna end (y -370) is the rear: front = +y
    box = load('Rear_Tractor_Bottom', 'chassis', 3000); w1 = load('Rear_Tractor_Wheels_2x', 'wheels_L', 4000)
    rack = load('Rear_Missile_Rack', 'rackset', 10**9); ant = load('Antenna', 'antenna', 600); stand = load('Front_Missile_Rack_Stand', 'launcher', 1000)
    move(box, (0, 0, 50.5)); move(w1, (0, 0, 118.5)); w2 = dup(w1, 'wheels_R'); mirror_x(w2)
    # rack stand under the kit's in-place rack
    R = vv(rack); S = vv(stand); move(stand, ((R[:, 0].min() + R[:, 0].max()) / 2 - (S[:, 0].min() + S[:, 0].max()) / 2,
                                             (R[:, 1].min() + R[:, 1].max()) / 2 - (S[:, 1].min() + S[:, 1].max()) / 2, R[:, 2].min() - S[:, 2].max()))
    # the kit stores the rack ~26 mm over the roof; on the toy it stands on the left-side ledge beside the cab: drop stand + rack onto it
    from mathutils.bvhtree import BVHTree as _B
    _bm = bmesh.new(); _bm.from_mesh(top.data); _tr = _B.FromBMesh(_bm); S = vv(stand); sc_ = (S.min(0) + S.max(0)) / 2
    _h = _tr.ray_cast(Vector((sc_[0], sc_[1], 1000)), Vector((0, 0, -1))); dz = (_h[0].z if _h[0] else 50) - S[:, 2].min()
    print('RACK drop', round(dz, 1), 'ledge z', round(_h[0].z, 1) if _h[0] else None); move(stand, (0, 0, dz)); move(rack, (0, 0, dz))
    # the kit rack = three missiles in three lanes + a crossbar plate under them with a half-disc mount (measured on the STL:
    # lanes centred at kit x -63, -43.5, -23.5, half-width 7.6; plate/half-disc below the missile bodies, z < 167.5, y -296..-265).
    # Faces are classified in kit coordinates (before the drop), so use the drop-corrected z.
    rk = rack; rk.name = 'rackset'
    LANES = (-63.0, -43.5, -23.5); zplate = 167.5 + dz
    zp0, zp1 = 170.5 + dz, 175.5 + dz                                # crossbar plate (measured: faces down at 170.5, up at 175.5, y -306.2..-273.1)
    def owner(c, n=None):
        if -296 <= c.y <= -265 and c.z < zplate: return -1            # half-disc mount under the middle
        if n is not None and -306.5 <= c.y <= -272.8 and zp0 - 0.2 <= c.z <= zp1 + 0.2:
            if (abs(n.z) > 0.99 and (abs(c.z - zp0) < 0.2 or abs(c.z - zp1) < 0.2)) or (abs(n.y) > 0.99 and abs(c.y + 273.1) < 0.3) or (abs(n.x) > 0.99 and (c.x < -69.5 or c.x > -17.2)):
                return -1                                             # plate top / bottom / front edge / outer ends
        for k, xc in enumerate(LANES):
            if abs(c.x - xc) <= 9.0: return k                         # lanes out to the measured gaps between them
        return -1
    for k in range(3):
        bpy.ops.object.select_all(action='DESELECT'); rk.select_set(True); bpy.context.view_layer.objects.active = rk
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
        vx = [v.co.x for v in rk.data.vertices]
        for p in rk.data.polygons:
            o_ = owner(p.center, p.normal)
            if o_ >= 0 and max(abs(vx[i] - LANES[o_]) for i in p.vertices) > 9.0: o_ = -1   # a face reaching outside its lane = crossbar
            if p.center.y > -270.0: o_ = int(np.argmin([abs(p.center.x - xc) for xc in LANES]))   # ahead of the plate there is only missile (nose tips)
            p.select = bool(o_ == k)
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
        m = [o for o in bpy.context.selected_objects if o != rk][0]; m.name = f'msl_{k + 1}'; stores.append(m)
    bpy.ops.object.select_all(action='DESELECT'); rk.select_set(True); bpy.context.view_layer.objects.active = rk
    rk.name = 'launcher_cradle'
    # nose tips: tiny islands left on the cradle go back to the missile in their lane
    isl = split_loose(rk); keep = max(isl, key=lambda o: len(o.data.polygons)); back = []
    for o_ in isl:
        if o_ is keep: continue
        if len(o_.data.polygons) < 60:
            cx = vv(o_)[:, 0].mean(); k_ = int(np.argmin([abs(cx - xc) for xc in LANES])); join([stores[k_], o_], stores[k_].name); back.append(k_)
        else: keep = join([keep, o_], keep.name)
    rk = keep; rk.name = 'launcher_cradle'; print('RACK nose tips returned to', back)
    for o_, nf in [(rk, 1500)] + [(m_, 3000) for m_ in stores]:
        if len(o_.data.polygons) > nf:
            d_ = o_.modifiers.new('d', 'DECIMATE'); d_.ratio = nf / len(o_.data.polygons)
            bpy.context.view_layer.objects.active = o_; bpy.ops.object.modifier_apply(modifier='d')
    # gun: round base on the roof seat (the roof's highest feature)
    gun = load('Rear_Tractor_Gun', 'turret', 5000); G = vv(gun)
    base = G[G[:, 2] < G[:, 2].min() + 4]; bc = (base.min(0) + base.max(0)) / 2
    # barrel end = larger x-spread end is the base side in the print (y-max); muzzle must face +y (front)
    if np.ptp(G[G[:, 1] > G[:, 1].max() - 8][:, 2]) > np.ptp(G[G[:, 1] < G[:, 1].min() + 8][:, 2]):
        gun.data.transform(Matrix.Translation(Vector((bc[0], bc[1], 0))) @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Translation(Vector((-bc[0], -bc[1], 0))))
    G = vv(gun); base = G[G[:, 2] < G[:, 2].min() + 4]; bc = (base.min(0) + base.max(0)) / 2
    Tt = vv(top); roof = Tt[Tt[:, 2] > Tt[:, 2].max() - 1.5]; rc = (roof.min(0) + roof.max(0)) / 2   # roof peg = the gun hole (step 13)
    seat = 125.0 + (Tt[:, 2].min() - 37.5)                           # the round seat around the peg is the z 125 roof plane
    move(gun, (rc[0] - bc[0], rc[1] - bc[1], seat - G[:, 2].min()))
    dropped = seat_on(gun, [top], 3.0); print('GUN trailer dropped', round(dropped, 2)); pivot = Vector((rc[0], rc[1], seat - dropped))
    # paint (toy): cream cab, smoked front screen, black deck/chassis, grey vented skirts over black tyres, orange antenna + rack
    Tt = vv(top); zc = Tt[:, 2].min(); H = np.ptp(Tt[:, 2]); yf = Tt[:, 1].max(); L = np.ptp(Tt[:, 1])
    def r_top(c, n):
        if c.z < zc + 0.22 * H: return 'black'                       # deck
        if n.z > 0.2 and n.y > 0.3 and c.z > zc + 0.45 * H: return 'glass'
        if abs(n.x) > 0.85 and c.y > yf - 0.35 * L and c.z > zc + 0.5 * H and c.z < zc + 0.9 * H: return 'glass'
        return 'cream'
    paint(top, r_top, ['cream', 'black', 'glass'])
    paint(box, lambda c, n: 'skirt' if abs(n.x) > 0.85 else 'grey_dk', ['skirt', 'grey_dk'])
    for w in (w1, w2): paint(w, lambda c, n: 'skirt' if abs(n.x) > 0.9 and abs(c.x) > 52 else 'black', ['black', 'skirt'])   # grey hub covers (toy skirts)
    for o in [ant, stand, rk] + stores: flat(o, 'orange')
    flat(gun, 'gun')
    hull_objs = [top, box, w1, w2, ant, stand, rk]

# ---- to game axes: +X front, centred, ground 0 ----
allo = [o for o in bpy.context.scene.objects if o.type == 'MESH']
R = Matrix.Rotation(-math.pi / 2 if fs > 0 else math.pi / 2, 4, 'Z')
for o in allo: o.data.transform(R)
P = np.vstack([vv(o) for o in allo]); c = (P.min(0) + P.max(0)) / 2; sh = Vector((-c[0], -c[1], -P[:, 2].min()))
for o in allo: move(o, sh)
pivot = R @ pivot + sh
bpy.context.scene.cursor.location = pivot
t = bpy.data.objects['turret']; bpy.ops.object.select_all(action='DESELECT'); t.select_set(True); bpy.context.view_layer.objects.active = t; bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
# decals: G.I.JOE block + bars (bars toward the nose each side), Thunder Clap shield; raycast flush onto the hull sides
from mathutils.bvhtree import BVHTree
bm = bmesh.new()
for o in hull_objs:
    d = o.data.copy(); d.transform(o.matrix_world); bm.from_mesh(d)
tree = BVHTree.FromBMesh(bm)
def decal_img(kind):
    p = f'{TMP}/dec_{kind}.png'
    if kind.startswith('stripe'):
        im = Image.new('RGB', (160, 40), PAL['cream']); d = ImageDraw.Draw(im); L_ = kind == 'stripeL'
        bx = (90, 6, 159, 34) if L_ else (0, 6, 70, 34); d.rectangle(bx, fill=(24, 32, 90)); d.text((bx[0] + 8, 13), 'G.I.JOE', fill=PAL['white'])
        for k, cc in enumerate(('red', 'white', 'blue')): d.rectangle(((0, 8 + k * 9, 85, 15 + k * 9) if L_ else (74, 8 + k * 9, 159, 15 + k * 9)), fill=PAL[cc])
    else:
        im = Image.new('RGB', (64, 72), PAL['cream']); d = ImageDraw.Draw(im)
        d.polygon([(6, 6), (58, 6), (58, 38), (32, 68), (6, 38)], fill=PAL['shield'], outline=(250, 250, 250)); d.polygon([(32, 14), (46, 44), (18, 44)], fill=PAL['yellow'])
    im.save(p); return p
def dmat(kind):
    m = bpy.data.materials.get('dec_' + kind)
    if m is None:
        m = bpy.data.materials.new('dec_' + kind); m.use_nodes = True; nt = m.node_tree
        t_ = nt.nodes.new('ShaderNodeTexImage'); t_.image = bpy.data.images.load(decal_img(kind)); t_.image.pack(); t_.interpolation = 'Closest'
        nt.links.new(t_.outputs[0], nt.nodes['Principled BSDF'].inputs['Base Color'])
    return m
def decal(kind, x, z, w, h):
    for side in (1, -1):
        hit = tree.ray_cast(Vector((x, side * 400, z)), Vector((0, -side, 0)))
        if not hit[0] or abs(hit[1].y) < 0.6: print('DECAL SKIP', kind, x, z, side); continue
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, hit[0].y + side * 0.5, z), rotation=(math.pi / 2, 0, 0 if side < 0 else math.pi))
        o = bpy.context.active_object; o.name = f'decal_{kind}_{"L" if side > 0 else "R"}'; o.scale = (w, h, 1); bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(dmat('stripeL' if (kind == 'stripe' and side > 0) else kind))
P = np.vstack([vv(o) for o in hull_objs]); Lx = np.ptp(P[:, 0]); Hz = vv(bpy.data.objects['hull'])[:, 2].max()   # cab height, not the antenna
if V == 'tractor': decal('stripe', 0.12 * Lx, 0.72 * Hz, 55, 13); decal('shield', -0.08 * Lx, 0.62 * Hz, 16, 18)
else: decal('stripe', 0.2 * Lx, 0.56 * Hz, 50, 12); decal('shield', -0.1 * Lx, 0.7 * Hz, 16, 18)
for o in bpy.context.scene.objects:
    if o.type == 'MESH' and not o.data.uv_layers: o.data.uv_layers.new()
P = np.vstack([vv(o) for o in bpy.context.scene.objects if o.type == 'MESH'])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print('BUILT', V, 'size mm', np.ptp(P, 0).round(1), 'pivot', tuple(round(x, 1) for x in pivot), 'stores', [s.name for s in stores])
