# The CMF-1's round (John 18 Nov 00:14 "use a better graphic"): a 40mm-style HE grenade - olive body, yellow HE band, copper driving
# band, rounded nose - rendered side-on (nose right) with the battle camera's light, transparent background.
# usage: python3 cmf_round.py out.png [px_long]
import bpy, math, sys
OUT = sys.argv[1]; PX = int(sys.argv[2]) if len(sys.argv) > 2 else 256
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
def lin(c): return tuple((v / 255) ** 2.2 for v in c) + (1,)
def mat(n, c, metal=0.0, rough=0.5):
    m = bpy.data.materials.new(n); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(c); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough; return m
OL, YE, CU, DK = mat('olive', (84, 92, 52), 0.1, 0.55), mat('yellow', (222, 186, 40), 0.0, 0.5), mat('copper', (196, 112, 60), 0.8, 0.3), mat('dark', (40, 42, 34), 0.2, 0.6)
def prof(pts, m):                                   # lathe a profile [(x, r)] about the x axis
    import bmesh
    bm = bmesh.new(); seg = 32; rings = []
    for x, r in pts:
        rings.append([bm.verts.new((x, r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg))) for k in range(seg)])
    for a, b in zip(rings, rings[1:]):
        for k in range(seg): bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    me = bpy.data.meshes.new(m.name); bm.to_mesh(me); bm.free(); me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(m.name, me); sc.collection.objects.link(ob); return ob
prof([(-0.50, 0.30), (-0.50, 0.40), (-0.42, 0.40)], DK)                                        # base
prof([(-0.42, 0.41), (-0.30, 0.41)], CU)                                                       # driving band
prof([(-0.30, 0.40), (0.05, 0.40)], OL)                                                        # body
prof([(0.05, 0.40), (0.15, 0.40)], YE)                                                         # HE band
prof([(0.15, 0.40)] + [(0.15 + 0.38 * math.sin(t * math.pi / 2), 0.40 * math.cos(t * math.pi / 2) + 0.001) for t in [i / 10 for i in range(1, 11)]], OL)  # ogive nose
prof([(0.52, 0.06), (0.56, 0.04), (0.57, 0.001)], DK)                                          # fuze tip
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.3; cam.location = (0.03, -5, 0); cam.rotation_euler = (math.pi / 2, 0, 0)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 4.0; sun.rotation_euler = (math.radians(50), math.radians(-25), math.radians(-30))
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.35, 0.35, 0.35)
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.render.film_transparent = True; sc.render.resolution_x = PX; sc.render.resolution_y = PX
sc.render.filepath = OUT; bpy.ops.render.render(write_still=True); print('ROUND', OUT)
