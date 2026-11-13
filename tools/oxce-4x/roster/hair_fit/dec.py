import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/mnt/user-data/uploads/Downloads/young_girl_with_long_hair.glb')
ms=[o for o in bpy.data.objects if o.type=='MESH']
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active=ms[0]; bpy.ops.object.join()
o=bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.0003); bpy.ops.object.mode_set(mode='OBJECT')
m=o.modifiers.new('d','DECIMATE'); m.ratio=60000/len(o.data.polygons); bpy.ops.object.modifier_apply(modifier='d')
me=o.data; me.calc_loop_triangles()
V=np.array([v.co[:] for v in me.vertices]); F=np.array([t.vertices[:] for t in me.loop_triangles])
np.savez('/tmp/claude-0/bar/bust.npz',V=V,F=F); print(V.shape,F.shape,V.min(0),V.max(0))
c=V[np.abs(V[:,0]-np.median(V[:,0]))<0.01]; i=c[:,1].argmin(); print('nose tip (most -y, centre):',c[i])
