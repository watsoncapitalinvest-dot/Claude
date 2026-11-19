"""SD-30 drums from John's download (Thingiverse 3753806 aiwaloki, the toy's depth charge: dia 15.7 x 26.4 mm) on the W.H.A.L.E. stern slide.
Toy mm -> hull units 50/482.6, then x0.7 so six fit the Generals model's rack; axis across the hull, stacked up the slide."""
import bpy,sys,math
POS=[[-16.99,-10.56,9],[-16.94,-9.3,9.6],[-16.94,-8.13,10.23],[-16.99,-7.02,10.71],[-16.97,-5.94,11.25],[-16.99,-4.65,12.03]]
import numpy as np
from mathutils import Matrix, Vector
src,stl,out=sys.argv[-3:]; bpy.ops.wm.open_mainfile(filepath=src); O=bpy.data.objects
for n in [k for k in O.keys() if k.startswith('DC_')]: bpy.data.objects.remove(O[n])
before=set(O.keys()); bpy.ops.wm.stl_import(filepath=stl); s=[O[k] for k in O.keys() if k not in before][0]
V=np.array([v.co[:] for v in s.data.vertices]); c=(V.min(0)+V.max(0))/2
K=50/482.6*0.85; base=Matrix.Scale(K,4)@Matrix.Rotation(math.radians(90),4,'Y')@Matrix.Translation(Vector(-c))   # STL z (length) -> x: drums lie fore-aft (John's photo 20:42)
s.data.transform(base); s.matrix_world=Matrix.Identity(4); s.data.uv_layers.new(name='UV')
from PIL import Image
f='/home/claude/rt/v5/whale/col_wh_dc.png'; Image.new('RGB',(4,4),(40,40,44)).save(f); m=bpy.data.materials.new('wh_dc_toy'); m.use_nodes=True; tn=m.node_tree.nodes.new('ShaderNodeTexImage'); tn.image=bpy.data.images.load(f)
m.node_tree.links.new(tn.outputs['Color'],m.node_tree.nodes['Principled BSDF'].inputs['Base Color']); s.data.materials.clear(); s.data.materials.append(m)
for i in range(6):
    o=s if i==0 else s.copy(); 
    if i: o.data=s.data.copy(); bpy.context.scene.collection.objects.link(o)
    o.name=f'DC_{i}'
for i in range(6):
    O[f'DC_{i}'].data.transform(Matrix.Translation(Vector(POS[i])))   # John 20:49, placed in the editor; DC_0 = position 1, the exit
bpy.ops.wm.save_as_mainfile(filepath=out,compress=True); print('ok',len(s.data.polygons))
