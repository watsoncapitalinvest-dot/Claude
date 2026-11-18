"""Cobra Ferret toy pass (John 17 Nov 22:49 "go"; 22:52 the toy's instruction sheet, blueprint and photos). The Generals Ferret is
close to the 1985 toy - blue body, black tyres on blue hubs, the long cannon with its breech box over the right side, the forward
twin .50 cal on its mount, a Com-Bat rocket on each side, XO2 on the sides - with two differences:
- it carries a three-rocket rack on a post at each rear corner. The toy has none (blueprint and photos: two Com-Bat rockets on the
  foot pegs, and that is all; the game's Ferret carries those two). The racks come off: orange faces behind x -4.4 above the
  side rockets, and every non-blue face behind x -4.7 above z 4.5 (the racks' shaded faces; the breech box ends at x -4.2).
- its weapons are orange; the toy's are red. Orange texels go red (same shading); the two Com-Bat rockets (body blue here) go red.
- (23:04 "fix the decals") its Cobra sigils are on the body sides; the toy's are on the right-side fenders with ATV. The side ones
  are painted out here; the toy's stickers go on as decals (make_decals.py, decals.json).
The model is one mesh of loose triangles, so parts are picked by their texture colour and position, not by object.
python3 build_ferret.py in.blend out.blend"""
import bpy, bmesh, sys
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
# the Com-Bat rockets on the foot pegs (|y| 4.1-4.7, z 1.6-2.5, between the wheel hubs): red on the toy, body blue here -> a flat toy red
mr = bpy.data.materials.new('fr_red'); mr.use_nodes = True; lr = tuple((v / 255) ** 2.2 for v in (206, 34, 36)) + (1,)
mr.diffuse_color = lr; mr.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = lr
me.materials.append(mr); k = len(me.materials) - 1; n = 0
for p in me.polygons:
    c = Mw @ p.center
    if 4.1 < abs(c.y) < 4.75 and 1.6 < c.z < 2.5 and -2.2 < c.x < 3.3: p.material_index = k; n += 1   # between the hubs (wheel centres x -3.1, 4.2)
print('Com-Bat rocket faces -> red', n)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print('SAVED', OUT)
