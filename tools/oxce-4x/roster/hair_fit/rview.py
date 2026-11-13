"""python3 rview.py mesh.npz mask.npy out.png  - Blender workbench, front / side / back / 3-4, hair red"""
import sys, numpy as np, bpy, math
from mathutils import Vector
d=np.load(sys.argv[1]); V,F=d['V'],d['F']; M=np.load(sys.argv[2]) if sys.argv[2]!='-' else np.zeros(len(F),np.uint8)
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('m'); me.from_pydata(V.tolist(),[],F.tolist()); me.update()
ob=bpy.data.objects.new('m',me); bpy.context.scene.collection.objects.link(ob)
ca=me.color_attributes.new('c','BYTE_COLOR','CORNER')
col=np.where(M[:,None]==1,[0.85,0.15,0.12,1],[0.6,0.6,0.62,1]).astype(np.float32)
ca.data.foreach_set('color',np.repeat(col,3,axis=0).ravel())
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.color_type='VERTEX'; sc.display.shading.light='STUDIO'
sc.render.resolution_x=sc.render.resolution_y=360
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera=cam; cam.data.type='ORTHO'
lo,hi=V.min(0),V.max(0); c=Vector(((lo+hi)/2).tolist()); cam.data.ortho_scale=float((hi-lo).max())*1.05
from PIL import Image; ims=[]
for i,yaw in enumerate([0,90,180,35]):
    a=math.radians(yaw); dvec=Vector((math.sin(a),-math.cos(a),0.05)); cam.location=c+dvec*2
    cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler(); sc.render.filepath=f'/tmp/claude-0/bar/_v{i}.png'
    bpy.ops.render.render(write_still=True); ims.append(Image.open(sc.render.filepath).convert('RGB'))
W=Image.new('RGB',(360*4,360)); [W.paste(im,(i*360,0)) for i,im in enumerate(ims)]; W.save(sys.argv[3])
