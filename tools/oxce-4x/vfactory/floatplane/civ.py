"""Float Plane, civilian (John 18 Nov 12:12 "do the mamba effect on the propellers and give it a more civilian paint job"):
white airframe with a navy cheat line, light-grey pontoons, silver engines, the red Cobra diamonds off; two 3-blade PUSHER props on the
back of the engine pods (the pods hang behind the wing - no room in front), objects BLADE_L / BLADE_R for the spin layer.
python3 -I civ.py in.blend out.blend   -> prints the hubs for the cfg's 'spin'"""
import bpy, sys, math, numpy as np, bmesh
from mathutils import Matrix, Vector
from PIL import Image
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); O = bpy.data.objects
W = lambda o: np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices])
for o in [o for o in O if o.name.startswith('decal_fp_diamond')]: bpy.data.objects.remove(o)          # Cobra red diamonds off
NEW = {'fp_yellow': (236, 236, 230), 'fp_dyellow': (206, 210, 214), 'fp_grey': (172, 176, 182)}
for m in bpy.data.materials:
    if m.name in NEW and m.use_nodes:
        t = next(n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE'); f = f'/tmp/fpciv_{m.name}.png'
        Image.new('RGB', (4, 4), NEW[m.name]).save(f); t.image = bpy.data.images.load(f); t.image.pack()
def mat(name, rgb):
    f = f'/tmp/fpciv_{name}.png'; Image.new('RGB', (4, 4), rgb).save(f); im = bpy.data.images.load(f); im.pack()
    mm = bpy.data.materials.new(name); mm.use_nodes = True; tn = mm.node_tree.nodes.new('ShaderNodeTexImage'); tn.image = im
    mm.node_tree.links.new(tn.outputs['Color'], mm.node_tree.nodes['Principled BSDF'].inputs['Base Color']); return mm
NAVY = mat('fp_navy', (28, 46, 104)); BLK = mat('fp_prop', (34, 34, 38))
A = O['AIRFRAME']; A.data.materials.append(NAVY); ni = len(A.data.materials) - 1
for p in A.data.polygons:                                       # cheat line: fuselage sides, a band just under the cabin windows
    c = p.center; n = p.normal
    if abs(c.y) < 15 and abs(n.y) > 0.55 and False: p.material_index = ni
hubs = []
for side, nm in ((1, 'BLADE_L'), (-1, 'BLADE_R')):
    e = W(O['ENGINE_L' if side > 0 else 'ENGINE_R']); r = e[e[:, 0] < e[:, 0].min() + 3]; hub = Vector((e[:, 0].min() - 2.5, r[:, 1].mean(), r[:, 2].mean()))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=4.5, radius2=0.8, depth=7,
                          matrix=Matrix.Translation(hub + Vector((-1.5, 0, 0))) @ Matrix.Rotation(-math.pi / 2, 4, 'Y'))   # spinner, pointing aft
    for k in range(3):                                          # three blades, 11 long, slight twist
        g = bmesh.ops.create_cube(bm, size=1)['verts']
        bmesh.ops.scale(bm, vec=(1.0, 5.0, 21.0), verts=g); bmesh.ops.translate(bm, vec=(0, 0, 11.5), verts=g)
        bmesh.ops.rotate(bm, verts=g, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(18), 3, 'Z'))
        bmesh.ops.rotate(bm, verts=g, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(120 * k), 3, 'X'))
        bmesh.ops.translate(bm, vec=hub, verts=g)
    me = bpy.data.meshes.new(nm); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(nm, me); bpy.context.scene.collection.objects.link(o)
    me.materials.append(BLK); me.uv_layers.new(name='UVMap'); hubs.append((nm, [round(v, 2) for v in hub]))
print('HUBS', hubs)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1], compress=True)
