"""V.A.M.P. to the 1982 toy (toy pass; refs: 3DJoes photo set). The shape is already the toy (ROSTER's blend is Jabberwock's
kit, Thingiverse 776303, measured from the toy); this paints it: light olive body, charcoal lower body (bumpers, rockers,
fender flares), green hubs in black tyres, black seats and grilles, dark gun on a green post, red tail lights.
python3 build_vamp.py in.blend out.blend"""
import bpy, sys, math
from mathutils import Vector
SRC, OUT = sys.argv[-2:]
bpy.ops.wm.open_mainfile(filepath=SRC)
def lin(c): return tuple(((v / 255) ** 2.2) for v in c) + (1,)
PAL = {'olive': (104, 132, 52), 'dark': (44, 46, 46), 'black': (22, 23, 24), 'hub': (96, 122, 48), 'gun': (50, 53, 54), 'red': (190, 26, 30)}
M = {}
for n, c in PAL.items():
    m = bpy.data.materials.new('vp_' + n); m.use_nodes = True; m.diffuse_color = lin(c)
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = lin(c); M[n] = m
def paint(o, rule):
    names = list(PAL); o.data.materials.clear()
    for n in names: o.data.materials.append(M[n])
    mw = o.matrix_world; R = mw.to_3x3()
    for p in o.data.polygons: p.material_index = names.index(rule(mw @ p.center, (R @ p.normal).normalized()))
WHEELS = [(8.35, 2.885), (-6.015, 2.885)]                # (x centre, radius): the tyres, z centre = radius
def body(c, n):
    ay = abs(c.y)
    if ay > 5.3: return 'dark'                          # fender flares: the widest surfaces (|y| 5.69; the body side is 5.23)
    if c.z < 3.4 and ay > 3.9: return 'dark'             # rocker panels under the doors
    if c.x > 11.6 and c.z < 4.3: return 'dark'           # front bumper
    if c.x < -11.2 and c.z < 4.6: return 'dark'          # rear bumper / lower tail
    if c.x > 12.1 and 4.6 < c.z < 6.2 and ay > 1.6 and n.x > 0.6: return 'black'   # grilles beside the nose
    if c.x < -12.0 and 5.6 < c.z < 6.6 and 2.2 < ay < 4.6 and n.x < -0.6: return 'red'   # tail lights
    if -5.2 < c.x < 4.8 and ay < 5.15 and 2.0 < c.z < 7.0 and (n.z < 0.8 or c.z < 6.0): return 'black'   # the cab tub: seats, floor, all inner walls - one clean black area, as on the toy
    return 'olive'
ch = bpy.data.objects['GJCHASSIS']                       # the kit's big triangles cross the colour lines: cut them small first
import bmesh
bm = bmesh.new(); bm.from_mesh(ch.data)
for _ in range(2):
    long_ = [e for e in bm.edges if e.calc_length() > 0.6]
    bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.to_mesh(ch.data); bm.free(); print('CHASSIS faces', len(ch.data.polygons))
paint(ch, body)
for k in range(4):                                       # tyres black, hubs green (the disc faces near the axle)
    t = bpy.data.objects[f'tire_{k}']; v = [t.matrix_world @ x.co for x in t.data.vertices]
    cx = (min(p.x for p in v) + max(p.x for p in v)) / 2; cz = (min(p.z for p in v) + max(p.z for p in v)) / 2
    paint(t, lambda c, n, cx=cx, cz=cz: 'hub' if math.hypot(c.x - cx, c.z - cz) < 1.75 and abs(n.y) > 0.5 else 'black')
paint(bpy.data.objects['GJTURRET'], lambda c, n: 'gun')
paint(bpy.data.objects['gun_post'], lambda c, n: 'olive')
# the toy's gun (3DJoes photos): two LONG thin barrels with cone flash hiders; the kit's are short and fat. Barrels = the
# vertices forward of x -1.2 above z 10.1; stretched forward x1.75 from x -1.2, thinned to 0.62 about each barrel's axis.
g = bpy.data.objects['GJTURRET']; X0, KX, KR = -1.2, 1.75, 0.62
mw = g.matrix_world; inv = mw.inverted()
W = [(v, mw @ v.co) for v in g.data.vertices]
bar = [(v, w, -0.23 if w.y < 0.43 else 1.09) for v, w in W if w.x > X0 and w.z > 9.3]   # (the damaged look's barrel droops: follow its axis)
def axis_z(x, yc):                                         # the barrel's centre height at x (mean of its vertices near x)
    zs = [w.z for _, w, c in bar if c == yc and abs(w.x - x) < 0.2]; return sum(zs) / len(zs)
AZ = {id(v): axis_z(w.x, yc) for v, w, yc in bar}
tips = {}
for v, w, yc in bar:
    zc = AZ[id(v)]; nw = Vector((X0 + (w.x - X0) * KX, yc + (w.y - yc) * KR, zc + (w.z - zc) * KR)); v.co = inv @ nw
    if nw.x > tips.get(yc, (-1e9, 0))[0]: tips[yc] = (nw.x, zc)
import bmesh
bm = bmesh.new(); bm.from_mesh(g.data)
for yc, (tx, tz) in tips.items():                          # flash hiders: a short cone on each muzzle, pointing forward
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.2, radius2=0.08, depth=0.55)
    vs = r['verts']; bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(math.radians(90), 3, 'Y'))
    bmesh.ops.translate(bm, verts=vs, vec=inv @ Vector((tx + 0.27, yc, tz)))
tip = max(t[0] for t in tips.values())
bm.to_mesh(g.data); bm.free(); paint(g, lambda c, n: 'gun')
print('GUN tip', round(tip + 0.55, 3))
print('BUILT', OUT)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
