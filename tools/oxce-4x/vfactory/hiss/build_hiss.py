# Cobra H.I.S.S. rework (VFACTORY, 17 Nov; John 18:29 "let's go through them one at a time").
# The Generals model's turret (GJTURRET01) is a rocket rack; the 1983 toy's is a round gunner pod with dorsal-mounted twin
# 30mm automatic cannons (blueprint). It is replaced by the real turret from Jabberwock's print, drawn from his own toy
# (Thingiverse 776353, version 3 with the gunner), placed on the old pivot so the turret still turns to aim.
# Print: millimetres, lying on its back: +Z = along the barrels, +Y = up, X = width. Scale from the print's hull: 247 mm long
# against the Generals hull's 29 units -> 0.1174 units per mm.
# usage: python3 -I build_hiss.py in.blend turret.stl out.blend
import bpy, sys, tempfile, numpy as np
from mathutils import Matrix, Vector
from PIL import Image
IN, STL, OUT = sys.argv[-3:]; bpy.ops.wm.open_mainfile(filepath=IN); TMP = tempfile.mkdtemp()
K = 29.0 / 247.0; PIV = Vector((-4.27, 0.0, 13.42)); POD = Vector((31.75, 0.0, 30.0))   # pod centre in print mm (x, y-base, z)
def mat(name, rgb):
    p = f'{TMP}/{name}.png'; Image.new('RGB', (4, 4), rgb).save(p); im = bpy.data.images.load(p); im.pack()
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; t.interpolation = 'Closest'
    nt.links.new(t.outputs[0], nt.nodes['Principled BSDF'].inputs['Base Color']); m.diffuse_color = (*[c / 255 for c in rgb], 1); return m
for o in list(bpy.data.objects):                                   # the rocket rack, and any damage sticker that sat on it
    if o.name == 'GJTURRET01' or o.name.startswith('decal_t_'): bpy.data.objects.remove(o)
bpy.ops.wm.stl_import(filepath=STL); t = bpy.context.selected_objects[0]; t.name = 'GJTURRET01'; me = t.data
V = np.array([v.co[:] for v in me.vertices])
# classify on print coordinates before moving: gunner (above the pod ring, inside it), barrels (front), pod
M = {'pod': mat('hiss_t_pod', (34, 34, 38)), 'barrel': mat('hiss_t_barrel', (22, 22, 24)), 'bore': mat('hiss_t_bore', (6, 6, 6)),
     'gunner': mat('hiss_t_gunner', (40, 62, 120)), 'visor': mat('hiss_t_visor', (20, 20, 22))}
keys = list(M)
for k in keys: me.materials.append(M[k])
for p in me.polygons:
    c = Vector(np.mean([V[i] for i in p.vertices], 0).tolist())
    if c.z > 116.5: k = 'bore'
    elif c.z > 74: k = 'barrel'
    elif 10 < c.z < 40 and c.y > 23 and 18 < c.x < 46: k = 'visor' if c.y > 38.5 else 'gunner'
    else: k = 'pod'
    p.material_index = keys.index(k)
# print (x, y, z) -> world (z, x, y) about the pod centre, scaled, on the old pivot
R = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
me.transform(Matrix.Translation(-POD)); me.transform(R); me.transform(Matrix.Scale(K, 4)); me.transform(Matrix.Translation(PIV))
me.uv_layers.new(name='UVMap')
W = np.array([v.co[:] for v in me.vertices]); print('TURRET x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (W[:, 0].min(), W[:, 0].max(), W[:, 1].min(), W[:, 1].max(), W[:, 2].min(), W[:, 2].max()))
tips = [PIV + K * (R.to_3x3() @ (Vector(p) - POD)) for p in ((14.6, 31.7, 119.0), (48.9, 31.7, 119.0))]
print('MUZZLES', ' '.join('%.3f,%.3f,%.3f' % tuple(v) for v in tips))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print('BUILT', OUT)
