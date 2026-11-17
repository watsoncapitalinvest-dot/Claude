"""List a blend's images: packed or missing, and whether a decal image is a diamond (filled square rotated 45 on magenta).
blender-python: python3 scan_blend.py file.blend -> JSON lines"""
import bpy, sys, json, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
users = {}
for m in bpy.data.materials:
    if m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image: users.setdefault(n.image.name, []).append(m.name)
objs = {}
for o in bpy.data.objects:
    for s in o.material_slots:
        if s.material: objs.setdefault(s.material.name, []).append(o.name)
for im in bpy.data.images:
    w, h = im.size[:]; r = dict(name=im.name, packed=im.packed_file is not None, size=[w, h], mats=users.get(im.name, []))
    r['objs'] = sorted({o for m in r['mats'] for o in objs.get(m, [])})
    if w and h and w * h < 600 * 600:
        a = np.array(im.pixels[:]).reshape(h, w, 4)[::-1, :, :3]
        mg = (a[..., 0] > .9) & (a[..., 1] < .1) & (a[..., 2] > .9)
        fill = ~mg; r['fill_frac'] = round(float(fill.mean()), 3)
        if fill.any():
            ys, xs = np.nonzero(fill); cy, cx = ys.mean(), xs.mean()
            # diamond test: L1 distance from centre bounded
            rad = (np.abs(ys - cy) / (np.ptp(ys) / 2 + 1e-6) + np.abs(xs - cx) / (np.ptp(xs) / 2 + 1e-6)).max()
            r['diamond'] = bool(abs(fill.mean() - 0.5 * (np.ptp(ys) + 1) * (np.ptp(xs) + 1) / (w * h)) < 0.06 and rad < 1.1)
            cols = (a[fill] * 255).round().astype(int); u, c = np.unique(cols // 8 * 8, axis=0, return_counts=True)
            r['main_rgb'] = [int(x) for x in (a[fill][np.argsort(-c)[:1]] if False else cols[np.where((cols // 8 * 8 == u[c.argmax()]).all(1))[0]].mean(0))]
    print('IMG ' + json.dumps(r))
