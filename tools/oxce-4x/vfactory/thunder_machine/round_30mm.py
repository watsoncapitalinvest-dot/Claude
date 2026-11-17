# The 30x113mm chain-gun round (Thingiverse 3867008 by MYSE4321, CC BY; John's catalog card 13m) as the Thunder Machine's
# projectile (John 18:00 "make the ammo shells shoot out of the chain guns"). Brass case, dark steel projectile, a short
# tracer glow behind. Writes a blend for the catalog + an 8-direction head sheet for gjBulletHeadSheet (frame 0 = nose up,
# clockwise, like missile_heads.py). Size: the vehicle's own scale x ENLARGE (a true-size round is ~13 px; 1.5 reads).
# usage: python3 -I round_30mm.py round.stl out_dir vehicle_scale
import bpy, bmesh, sys, os, math, subprocess, numpy as np
from mathutils import Matrix, Vector
from PIL import Image
STL, OUT, VS = sys.argv[-3], sys.argv[-2], float(sys.argv[-1]); ENLARGE = 1.5; os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=STL); o = bpy.context.selected_objects[0]; o.name = 'round'
me = o.data; V = np.array([v.co[:] for v in me.vertices]); ext = np.ptp(V, 0); ax = int(np.argmax(ext))
# point the long axis along +X, nose (narrow end) forward
R = {0: Matrix.Identity(4), 1: Matrix.Rotation(-math.pi / 2, 4, 'Z'), 2: Matrix.Rotation(math.pi / 2, 4, 'Y')}[ax]; me.transform(R)
V = np.array([v.co[:] for v in me.vertices]); c = (V.min(0) + V.max(0)) / 2; me.transform(Matrix.Translation(Vector((-c).tolist())))
V = np.array([v.co[:] for v in me.vertices]); x0, x1 = V[:, 0].min(), V[:, 0].max()
r_near = lambda x: np.hypot(V[np.abs(V[:, 0] - x) < (x1 - x0) * 0.03][:, 1], V[np.abs(V[:, 0] - x) < (x1 - x0) * 0.03][:, 2]).max()
if r_near(x0 + (x1 - x0) * 0.05) < r_near(x1 - (x1 - x0) * 0.05): me.transform(Matrix.Rotation(math.pi, 4, 'Z'))   # nose to +X
V = np.array([v.co[:] for v in me.vertices]); L = np.ptp(V[:, 0])
# real size: a 30x113mm round is ~0.2 m; 0.1625 m per Thunder Machine model unit -> length in model units
me.transform(Matrix.Scale((0.20 / 0.1625) / L, 4)); V = np.array([v.co[:] for v in me.vertices]); x0, x1 = V[:, 0].min(), V[:, 0].max()
def mat(n, rgb):
    m = bpy.data.materials.new(n); m.diffuse_color = (*[c / 255 for c in rgb], 1); m.use_nodes = True
    p = f'/tmp/{n}.png'; Image.new('RGB', (4, 4), rgb).save(p); im = bpy.data.images.load(p); im.pack()
    t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = im; m.node_tree.links.new(t.outputs[0], m.node_tree.nodes['Principled BSDF'].inputs['Base Color']); return m
me.materials.append(mat('brass', (190, 150, 62))); me.materials.append(mat('steel', (70, 72, 76)))
cut = x0 + (x1 - x0) * 0.62                                        # the case is the rear ~60%, the projectile the front
for p in me.polygons: p.material_index = 1 if (o.matrix_world @ p.center).x > cut else 0
me.uv_layers.new(name='UVMap'); o.location = (0, 0, 5)
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/round_30x113.blend'); print('LEN_UNITS %.3f' % (x1 - x0))
