"""Cobra Ferret toy pass (John 17 Nov 22:49 "go"; 22:52 the toy's instruction sheet, blueprint and photos). The Generals Ferret is
close to the 1985 toy - blue body, black tyres on blue hubs, the long cannon with its breech box over the right side, the forward
twin .50 cal on its mount, a Com-Bat rocket on each side, XO2 on the sides - with two differences:
- it carries a three-rocket rack on a post at each rear corner. The toy has none (blueprint and photos: two Com-Bat rockets on the
  foot pegs, and that is all; the game's Ferret carries those two). The racks come off: orange faces behind x -4.4 above the
  side rockets, and every non-blue face behind x -4.7 above z 4.5 (the racks' shaded faces; the breech box ends at x -4.2).
- its weapons are orange; the toy's are red. Orange texels go red (same shading). 23:17: the side missiles become the toy's Com-Bat
  rockets as separate parts that leave the pegs (see below).
- (23:04 "fix the decals") its Cobra sigils are on the body sides; the toy's are on the right-side fenders with ATV. The side ones
  are painted out here; the toy's stickers go on as decals (make_decals.py, decals.json).
The model is one mesh of loose triangles, so parts are picked by their texture colour and position, not by object.
python3 build_ferret.py in.blend out.blend"""
import bpy, bmesh, sys, math
from mathutils import Matrix
import numpy as np
SRC, OUT = sys.argv[-2:]
bpy.ops.wm.open_mainfile(filepath=SRC)
im = bpy.data.images['gjcfert.dds']; W, H = im.size
A = (np.array(im.pixels[:]).reshape(H, W, 4) * 255).astype(np.uint8)      # bottom-left origin, as UVs are
rgb = A[..., :3].astype(int)
def orange(c): r, g, b = c; return r > 150 and 60 < g < 170 and b < 110 and r - g > 40
o = bpy.data.objects['GJCHASSIS']; me = o.data; uv = me.uv_layers.active.data; Mw = o.matrix_world
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); ul = bm.loops.layers.uv.active
gone = []
for f in bm.faces:
    c = Mw @ f.calc_center_median()
    if c.x > -4.4 or c.z < 3.0: continue
    u = sum(l[ul].uv.x for l in f.loops) / len(f.loops); v = sum(l[ul].uv.y for l in f.loops) / len(f.loops)
    px = rgb[min(H - 1, max(0, int(v * H))), min(W - 1, max(0, int(u * W)))]
    if orange(px): gone.append(f)
    elif c.x < -4.7 and c.z > 4.5 and not (px[2] > px[0] + 10):   # the racks' shaded faces: anything there that is not body blue
        gone.append(f)
bmesh.ops.delete(bm, geom=gone, context='FACES'); bm.to_mesh(me); bm.free()
print('rear racks: faces removed', len(gone))
# the Generals put the Cobra sigil on the body sides (four texture patches, found from the faces there); the toy has only XO2 there
# and carries the sigil on its right-side fenders (decals.json, John's own sigil). Red texels in those patches are inpainted from the blue.
import cv2
tl = np.ascontiguousarray(rgb[::-1].astype(np.uint8))                     # top-left origin, as the boxes are
for x, y, w, h in [(389, 689, 46, 26), (393, 745, 42, 34), (57, 881, 38, 50), (189, 961, 46, 38)]:
    x0, y0, x1, y1 = x - 6, y - 6, x + w + 6, y + h + 6
    r = tl[y0:y1, x0:x1].astype(int); notblue = ~(r[..., 2] > r[..., 0] + 10)
    mask = np.zeros(tl.shape[:2], np.uint8); mask[y0:y1, x0:x1] = (notblue * 255).astype(np.uint8)
    tl = cv2.inpaint(tl, cv2.dilate(mask, np.ones((3, 3), np.uint8)), 5, cv2.INPAINT_TELEA)
rgb = tl[::-1].astype(int)
# orange -> toy red, keeping each texel's shading (scale the red to the texel's brightness)
R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
m = (R > 120) & (G > 45) & (G < 175) & (B < 120) & (R - G > 35) & (R - B > 70)
lum = rgb[m].mean(-1); ref = np.median(lum)
red = np.array([206.0, 34.0, 36.0])
rgb[m] = np.clip(red[None, :] * (lum / ref)[:, None], 0, 255).astype(int)
A[..., :3] = rgb.astype(np.uint8)
im2 = bpy.data.images.new('gjcfert_toy', W, H, alpha=True); im2.pixels = (A.astype(np.float32) / 255).ravel(); im2.pack()
for mt in bpy.data.materials:
    if mt.node_tree:
        for n in mt.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image == im: n.image = im2
print('orange texels -> red', int(m.sum()))
# The Com-Bat rockets (John 23:17: "the 2 side missiles are small but they should shoot off the vehicle"). The Generals' side missiles
# are fused into the body mesh, so they cannot leave it: cut them out (between the wheel hubs, body component only - the wheels and
# hub caps are their own parts once the triangle soup is welded) and fit the toy's Com-Bat as two separate red parts, combat_L and
# combat_R, on short foot-peg stubs. The renderer hides them per store state: m2 both on, m1 the left one gone, m0 both gone.
def lin(c): return tuple((v / 255) ** 2.2 for v in c) + (1,)
def mat(n, c):
    m_ = bpy.data.materials.new(n); m_.use_nodes = True; m_.diffuse_color = lin(c); m_.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = lin(c); return m_
RED, YEL, DARK = mat('fr_red', (206, 34, 36)), mat('fr_yellow', (226, 184, 40)), mat('fr_dark', (30, 32, 40))
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
comp = {}; cid = 0
for v in bm.verts:
    if v in comp: continue
    st = [v]; comp[v] = cid
    while st:
        a = st.pop()
        for e in a.link_edges:
            b = e.other_vert(a)
            if b not in comp: comp[b] = cid; st.append(b)
    cid += 1
span = {}
for v, c in comp.items():
    x = (Mw @ v.co).x; lo, hi = span.get(c, (x, x)); span[c] = (min(lo, x), max(hi, x))
body_c = {c for c, (lo, hi) in span.items() if hi - lo > 8}                  # the body: the one part longer than a wheel
cut = [f for f in bm.faces if comp[f.verts[0]] in body_c and (lambda c: 4.05 < abs(c.y) < 4.8 and 1.55 < c.z < 2.6 and -2.5 < c.x < 3.6)(Mw @ f.calc_center_median())]
bmesh.ops.delete(bm, geom=cut, context='FACES'); bm.to_mesh(me); bm.free(); print('Generals side missiles: faces cut', len(cut))
AY, AZ = 4.45, 2.05                                                          # rocket axis: the old missiles' line
for side, sy in (('L', 1), ('R', -1)):
    bm = bmesh.new(); mats = {}
    def piece(g, mi):
        for f in {f for v in g['verts'] for f in v.link_faces}: f.material_index = mi
    def tube(x0, x1, r0, r1, mi, seg=10):
        g = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=x1 - x0)
        bmesh.ops.transform(bm, matrix=Matrix.Translation(((x0 + x1) / 2, sy * AY, AZ)) @ Matrix.Rotation(math.pi / 2, 4, 'Y'), verts=g['verts']); piece(g, mi)
    def fin(x0, x1, span, ang):
        g = bmesh.ops.create_cube(bm, size=1)
        M = Matrix.Translation(((x0 + x1) / 2, sy * AY, AZ)) @ Matrix.Rotation(ang, 4, 'X') @ Matrix.Translation((0, 0, span / 2)) @ Matrix.Diagonal((x1 - x0, 0.05, span, 1))
        bmesh.ops.transform(bm, matrix=M, verts=g['verts']); piece(g, 0)
    tube(-1.9, 2.9, 0.16, 0.16, 0); tube(2.9, 3.55, 0.16, 0.0, 0); tube(2.2, 2.45, 0.175, 0.175, 1); tube(-2.1, -1.9, 0.11, 0.13, 2)
    for k in range(4):
        fin(-1.9, -1.15, 0.55, k * math.pi / 2 + math.pi / 4); fin(1.2, 1.6, 0.36, k * math.pi / 2 + math.pi / 4)
    rm = bpy.data.meshes.new('combat_' + side); bm.to_mesh(rm); bm.free()
    for m_ in (RED, YEL, DARK): rm.materials.append(m_)
    rm.uv_layers.new(name='UV'); ob = bpy.data.objects.new('combat_' + side, rm); bpy.context.scene.collection.objects.link(ob)
# the foot-peg stubs the rockets ride on (stay on the body)
bm = bmesh.new()
for sy in (1, -1):
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.12, radius2=0.12, depth=0.7)
    bmesh.ops.transform(bm, matrix=Matrix.Translation((0.5, sy * 4.05, AZ)) @ Matrix.Rotation(math.pi / 2, 4, 'X'), verts=g['verts'])
pm = bpy.data.meshes.new('fr_pegs'); bm.to_mesh(pm); bm.free(); pm.materials.append(DARK); pm.uv_layers.new(name='UV')
bpy.context.scene.collection.objects.link(bpy.data.objects.new('fr_pegs', pm))
print('Com-Bat rockets: combat_L, combat_R; pegs')
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print('SAVED', OUT)
