import bpy,sys,math,bmesh
from PIL import Image
glb,png=sys.argv[-2:]; bpy.ops.wm.read_factory_settings(use_empty=True)
# SD-30 depth charge, as the toy's (ill. 19: two halves pressed together, ribbed drum): dia 2.6, length 2.2 hull units
bm=bmesh.new(); R=1.3; L=0.8; segs=40
prof=[(0,R*0.3),(0.04,R*0.88),(0.12,R),(0.42,R),(0.46,R*0.9),(0.54,R*0.9),(0.58,R),(0.88,R),(0.96,R*0.88),(1,R*0.3)]   # toy: two ribbed halves pressed together
rings=[]
for t,r in prof:
    rings.append([bm.verts.new((r*math.cos(2*math.pi*k/segs), L*t-L/2, r*math.sin(2*math.pi*k/segs))) for k in range(segs)])   # axis along y, like the rack
for a,b in zip(rings[:-1],rings[1:]):
    for k in range(segs): bm.faces.new((a[k],a[(k+1)%segs],b[(k+1)%segs],b[k]))
bm.faces.new(rings[0]); bm.faces.new(rings[-1][::-1])
me=bpy.data.meshes.new('sd30'); bm.to_mesh(me); o=bpy.data.objects.new('SD30_DEPTH_CHARGE',me); bpy.context.scene.collection.objects.link(o)
me.uv_layers.new(name='UV')
f='/tmp/dc_black.png'; Image.new('RGB',(4,4),(34,34,36)).save(f); m=bpy.data.materials.new('dc'); m.use_nodes=True; tn=m.node_tree.nodes.new('ShaderNodeTexImage'); tn.image=bpy.data.images.load(f)
m.node_tree.links.new(tn.outputs['Color'],m.node_tree.nodes['Principled BSDF'].inputs['Base Color']); me.materials.append(m)
for p in me.polygons: p.use_smooth=True
bpy.ops.object.select_all(action='SELECT'); bpy.ops.export_scene.gltf(filepath=glb,use_selection=True)
sc=bpy.context.scene; cam=bpy.data.cameras.new('c'); cam.type='ORTHO'; cam.ortho_scale=4; co=bpy.data.objects.new('c',cam); sc.collection.objects.link(co)
from mathutils import Vector
co.location=Vector((3,-4,3)); co.rotation_euler=(-co.location).to_track_quat('-Z','Y').to_euler(); sc.camera=co
sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='TEXTURE'; sc.render.film_transparent=True
sc.render.resolution_x=600; sc.render.resolution_y=400; sc.render.filepath=png; bpy.ops.render.render(write_still=True); print('faces',len(me.polygons))
