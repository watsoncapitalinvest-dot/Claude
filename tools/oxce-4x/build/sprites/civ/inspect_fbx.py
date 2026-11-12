"""Inspect a Mixamo FBX and unpack its textures: python3 inspect_fbx.py <fbx> <texdir>"""
import bpy, sys, os, json
import numpy as np
fbx, td = sys.argv[1], sys.argv[2]
os.makedirs(td, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
info = {'objects': [], 'images': []}
for o in bpy.data.objects:
    d = {'name': o.name, 'type': o.type}
    if o.type == 'MESH':
        M = o.matrix_world
        co = np.array([M @ v.co for v in o.data.vertices])
        d.update(verts=len(o.data.vertices), mats=[m.name if m else None for m in o.data.materials],
                 zmin=float(co[:, 2].min()), zmax=float(co[:, 2].max()), vg=o.vertex_groups[0].name if o.vertex_groups else None)
    if o.type == 'ARMATURE':
        d.update(bones=len(o.data.bones), first=o.data.bones[0].name, scale=list(o.scale))
    info['objects'].append(d)
for m in bpy.data.materials:
    if not m.node_tree: continue
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            for inp in ('Base Color', 'Alpha'):
                if n.inputs[inp].links:
                    fn = n.inputs[inp].links[0].from_node
                    info['images'].append([m.name, inp, fn.image.name if getattr(fn, 'image', None) else fn.type])
for im in list(bpy.data.images):
    if im.size[0] == 0: continue
    p = os.path.join(td, bpy.path.clean_name(im.name) + '.png')
    px = np.empty(im.size[0] * im.size[1] * 4, np.float32); im.pixels.foreach_get(px)
    from PIL import Image
    a = (px.reshape(im.size[1], im.size[0], 4)[::-1] * 255 + 0.5).clip(0, 255).astype(np.uint8)
    Image.fromarray(a, 'RGBA').save(p)
    info.setdefault('saved', []).append([im.name, im.size[0], im.size[1], im.channels, p])
print('JSON' + json.dumps(info))
