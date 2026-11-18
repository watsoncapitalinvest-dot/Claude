"""Mauler M.B.T. toy pass (John 17 Nov 22:23 "continue"). The Generals model is already the 1985 toy's shape (checked against Jabberwock's
kit, Thingiverse 3167750, measured from a real toy): long gun in its box sleeve with the holes, side skirts, smoke-grenade launchers on
the turret sides. Added here: the toy's two antennas on the back of the turret (a fan site's description of the toy: two antennae at the
turret rear). They are turret objects (GJANTENNA), so they turn with it.
Also: the Generals texture's G.I.JOE logos (on the side skirts, where the toy has only small LOCK labels) and its small flag are
painted out (inpainted from the tan around them); the toy's own stickers go on as decals (make_decals.py + decals.json, from the
toy's sticker sheet John sent 22:32).
python3 build_mauler.py in.blend out.blend"""
import bpy, bmesh, sys, math
from mathutils import Matrix, Vector
SRC, OUT = sys.argv[-2:]
bpy.ops.wm.open_mainfile(filepath=SRC)
import numpy as np, cv2
im = bpy.data.images['gjcmauler.dds']; W, H = im.size
A = (np.array(im.pixels[:]).reshape(H, W, 4)[::-1] * 255).astype(np.uint8); rgb = np.ascontiguousarray(A[..., :3])
for x, y, w, h in [(124, 597, 28, 91), (172, 596, 27, 91), (216, 596, 28, 91), (622, 946, 74, 26), (424, 429, 28, 27)]:   # logo / flag clusters (top-left origin)
    x0, y0, x1, y1 = x - 2, y - 2, x + w + 2, y + h + 2
    r = rgb[y0:y1, x0:x1].astype(int); R, G, B = r[..., 0], r[..., 1], r[..., 2]
    tan = (R > G) & (G > B) & (R - B > 25) & (G > 0.45 * R) & (R < 230)        # anything that is not the hull tan
    mask = np.zeros(rgb.shape[:2], np.uint8); mask[y0:y1, x0:x1] = (~tan * 255).astype(np.uint8)
    rgb = cv2.inpaint(rgb, cv2.dilate(mask, np.ones((3, 3), np.uint8)), 5, cv2.INPAINT_TELEA)
A[..., :3] = rgb
im2 = bpy.data.images.new('gjcmauler_toy', W, H, alpha=True); im2.pixels = (A[::-1].astype(np.float32) / 255).ravel(); im2.pack()
for mt in bpy.data.materials:
    if mt.node_tree:
        for n in mt.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image == im: n.image = im2
def lin(c): return tuple(((v / 255) ** 2.2) for v in c) + (1,)
m = bpy.data.materials.new('ml_antenna'); m.use_nodes = True; m.diffuse_color = lin((40, 38, 34))
m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = lin((40, 38, 34))
bm = bmesh.new()
for y in (4.6, -4.6):                                    # rear corners of the turret roof (x -8.8 .. 4.6, y +-6.6, top ~z 14.5)
    base = Vector((-7.6, y, 14.2))
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.32, radius2=0.32, depth=0.5)       # the mount
    bmesh.ops.translate(bm, vec=base + Vector((0, 0, 0.25)), verts=g['verts'])
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.09, radius2=0.05, depth=5.5)       # the whip, leaning back a little (5.5: taller is cut by the 4x5 frame top)
    M = Matrix.Translation(base + Vector((-0.35, 0, 0.5 + 2.75))) @ Matrix.Rotation(math.radians(-7), 4, 'Y')
    bmesh.ops.transform(bm, matrix=M, verts=g['verts'])
me = bpy.data.meshes.new('GJANTENNA'); bm.to_mesh(me); bm.free(); me.materials.append(m); me.uv_layers.new(name='UV')
ob = bpy.data.objects.new('GJANTENNA', me); bpy.context.scene.collection.objects.link(ob)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print('SAVED', OUT)
