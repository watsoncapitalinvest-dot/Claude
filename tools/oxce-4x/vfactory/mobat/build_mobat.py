"""M.O.B.A.T. toy pass (John 17 Nov 21:40: "Keep model, swap gun"; 21:43 "add the machine gun ... to the turret too like the image";
21:44 the 3DJoes photo set of the 1982 toy; "thers better models i have of machine guns").
The Generals hull and turret stay. The Generals Gatling (GJBARREL01) becomes the toy's main gun, measured off the toy's side photo
against the hull length (muzzle where the Gatling's was, x 16.03): a boxy mantlet on the turret face, a thick sleeve, a long thin
tube, a collar and a thicker muzzle section, the dark bore; the square searchlight box beside it (the vehicle's right, as on the toy).
The commander's machine gun: John's M2 Browning model (Downloads m2-browning-machine-gun.zip, its own textures packed), on a short
post on the turret top in front of the hatch, pointing forward. It is a turret object (GJMG): it turns with the turret.
python3 build_mobat.py in.blend m2.blend out.blend droop_deg   (droop 0 for the clean look; the damaged look's bent barrel, nose down)"""
import bpy, bmesh, sys, math
from mathutils import Vector, Matrix
SRC, M2, OUT, DROOP = sys.argv[-4:]; DROOP = float(DROOP)
bpy.ops.wm.open_mainfile(filepath=SRC)
def lin(c): return tuple(((v / 255) ** 2.2) for v in c) + (1,)
def mat(n, c):
    m = bpy.data.materials.new(n); m.use_nodes = True; m.diffuse_color = lin(c)
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = lin(c); return m
GREEN, DARK = mat('mb_green', (56, 84, 50)), mat('mb_dark', (20, 22, 22))
AX_Z = 8.08                                                   # gun axis height (the Gatling's muzzle z)
bm = bmesh.new()
def tube(x0, x1, r, mi, seg=16):
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=x1 - x0)
    M = Matrix.Translation(((x0 + x1) / 2, 0, AX_Z)) @ Matrix.Rotation(math.pi / 2, 4, 'Y')
    bmesh.ops.transform(bm, matrix=M, verts=g['verts'])
    for f in {f for v in g['verts'] for f in v.link_faces}: f.material_index = mi
def box(x0, x1, y0, y1, z0, z1, mi):
    g = bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)), verts=g['verts'])
    for f in {f for v in g['verts'] for f in v.link_faces}: f.material_index = mi
box(7.3, 8.9, -1.45, 1.45, 7.0, 9.2, 0)                       # mantlet on the turret face (turret front x 7.78 at gun height)
tube(8.9, 10.0, 0.50, 0)                                      # sleeve
tube(10.0, 13.9, 0.34, 0)                                     # long thin tube
tube(13.9, 14.1, 0.46, 0)                                     # collar
tube(14.1, 16.03, 0.42, 0)                                    # muzzle section
tube(16.03, 16.06, 0.22, 1, 12)                               # bore
box(7.5, 8.9, -2.95, -1.55, 7.55, 9.0, 0)                     # searchlight box, vehicle's right
box(8.9, 8.95, -2.75, -1.75, 7.75, 8.8, 1)                    # its dark square window
if DROOP:                                                     # the damaged look: the barrel bent nose-down past the sleeve
    P = Vector((10.0, 0, AX_Z)); R = Matrix.Rotation(math.radians(DROOP), 3, 'Y')
    for v in bm.verts:
        if v.co.x > 10.0: v.co = R @ (v.co - P) + P
old = bpy.data.objects['GJBARREL01']; me = bpy.data.meshes.new('GJBARREL01_toy'); bm.to_mesh(me); bm.free()
me.materials.append(GREEN); me.materials.append(DARK); me.uv_layers.new(name='UV')
old.data = me; old.matrix_world = Matrix.Identity(4)          # same object name and place in the scene: the render cfg is unchanged
# --- the M2, from John's model ---
with bpy.data.libraries.load(M2) as (src, dst): dst.objects = [n for n in src.objects]
mg = next(o for o in dst.objects if o and o.type == 'MESH'); bpy.context.scene.collection.objects.link(mg)
mg.data = mg.data.copy(); mg.name = 'GJMG'
bm = bmesh.new(); bm.from_mesh(mg.data); W = mg.matrix_basis.copy()             # no parent: basis = its placement in the file
bmesh.ops.delete(bm, geom=[v for v in bm.verts if (W @ v.co).z < -0.45], context='VERTS')   # the long post and its foot plate: a short post
S, BASE = 3.0, Vector((2.0, 0.4, 10.2))                        # 3 model units a metre; post (local y 0.52, cut z -0.45) on the turret top
T = Matrix.Translation(BASE) @ Matrix.Diagonal((S, S, S, 1)) @ Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Translation((0, -0.52, 0.45)) @ W
bmesh.ops.transform(bm, matrix=T, verts=bm.verts[:]); bm.to_mesh(mg.data); bm.free(); mg.matrix_world = Matrix.Identity(4)
for m in mg.data.materials:
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image and not n.image.packed_file: n.image.pack()
vs = [v.co for v in mg.data.vertices]
print('GJMG', len(mg.data.polygons), 'x', round(min(v.x for v in vs), 2), round(max(v.x for v in vs), 2), 'z', round(min(v.z for v in vs), 2), round(max(v.z for v in vs), 2))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print('SAVED', OUT)
