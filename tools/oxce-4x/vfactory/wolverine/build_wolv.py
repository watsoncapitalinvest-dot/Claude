"""Wolverine to the 1983 toy (John 18:29 toy pass; refs: 3DJoes photo set). Works on ROSTER's Generals blend.
python3 build_wolv.py in.blend out.blend
- Hull olive -> the toy's green; missile pods green like the hull (they were grey): the pod faces' texels are recoloured in a copy of the texture.
- The G.I.JOE logos printed on the hull texture come off (the toy carries the logo on the pods, added as decals).
- Missiles: light grey all over (toy), not white with red tips.
The markings (pod logos, stars, WOLVERINE, UNITED STATES + flag, DANGER, RELAY 23/24) go on after, by damage_generic.py."""
import bpy, sys, numpy as np, cv2
from PIL import Image, ImageDraw
SRC, OUT = sys.argv[-2:]
bpy.ops.wm.open_mainfile(filepath=SRC)
im = bpy.data.images['gjwolv.dds']; W, H = im.size
A = (np.array(im.pixels[:]).reshape(H, W, 4)[::-1] * 255).astype(np.uint8)
rgb = A[..., :3].copy()
# 1. hull logos off (clusters found by colour: red / blue / white on the green; UV boxes, top-left origin)
for x0, y0, x1, y1 in [(766, 233, 790, 322), (437, 713, 478, 825), (5, 762, 41, 798), (743, 793, 763, 840)]:
    r = rgb[y0:y1, x0:x1].astype(int); R, G, B = r[..., 0], r[..., 1], r[..., 2]
    m = ~((G > R + 6) & (G > B + 6))                       # anything that is not hull green
    mask = np.zeros(rgb.shape[:2], np.uint8); mask[y0:y1, x0:x1] = (m * 255).astype(np.uint8)
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
    rgb = cv2.inpaint(rgb, mask, 5, cv2.INPAINT_TELEA)
# 2. turret green: texels under every GJTURRET face (pods, pylon, hub - all green on the toy)
t = bpy.data.objects['GJTURRET']; uv = t.data.uv_layers.active.data
pm = Image.new('L', (W, H), 0); d = ImageDraw.Draw(pm)
for p in t.data.polygons:
    c = t.matrix_world @ p.center
    if True:
        d.polygon([(uv[li].uv[0] * W, (1 - uv[li].uv[1]) * H) for li in p.loop_indices], fill=255)
pm = cv2.dilate(np.asarray(pm), np.ones((5, 5), np.uint8)) > 0
hull = rgb.reshape(-1, 3).astype(int); g = hull[(hull[:, 1] > hull[:, 0] + 8) & (hull[:, 1] > hull[:, 2] + 8)]
gsrc = np.median(g, 0); gmed = np.array([58.0, 84.0, 56.0]); glum = gmed.mean()   # toy green (3DJoes photos: R ~ B, not the Generals olive)
isg = (rgb[..., 1].astype(int) > rgb[..., 0] + 8) & (rgb[..., 1].astype(int) > rgb[..., 2] + 8)
rgb[isg] = np.clip(rgb[isg].astype(float) * (gmed / gsrc)[None, :], 0, 255).astype(np.uint8)   # whole hull: olive -> toy green
lum = rgb[..., :3].astype(float).mean(-1)
grey = pm & ~isg   # pod texels not already green
ref = np.median(lum[grey]) if grey.any() else glum
new = np.clip(gmed[None, :] * (lum[grey] / ref)[:, None], 0, 255)
rgb[grey] = new.astype(np.uint8)
print('POD texels recoloured', int(grey.sum()), 'hull olive', gsrc.round(), '-> toy green', gmed, 'grey ref', round(float(ref), 1))
A[..., :3] = rgb
im2 = bpy.data.images.new('gjwolv_toy', W, H, alpha=True); im2.pixels = (A[::-1].astype(np.float32) / 255).ravel(); im2.pack()
for m in bpy.data.materials:
    if m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image == im: n.image = im2
# 3. missiles grey (toy): body / tip light grey, ring and fin a step darker
GREY = {'wolv_msl_white': (0.24, 0.25, 0.25), 'wolv_msl_tip': (0.30, 0.31, 0.31), 'wolv_msl_ring': (0.15, 0.155, 0.16), 'wolv_msl_fin': (0.19, 0.195, 0.2)}   # linear; ~135-150 sRGB after the cel light (0.42 read white)
for n, c in GREY.items():
    m = bpy.data.materials.get(n)
    if m:
        m.diffuse_color = (*c, 1)
        bp = m.node_tree.nodes.get('Principled BSDF') if m.node_tree else None
        if bp: bp.inputs['Base Color'].default_value = (*c, 1)
print('BUILT', OUT)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
