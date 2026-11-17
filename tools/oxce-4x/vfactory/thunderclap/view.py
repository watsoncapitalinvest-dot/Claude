# python3 view.py in.obj|in.blend out.png [tex]  -> 4 ortho views (front +X? we show -Y side, +Y side, front, top) with texture
import bpy, sys, math, mathutils
src, out = sys.argv[1], sys.argv[2]
if src.endswith('.blend'): bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=src, forward_axis='NEGATIVE_Z', up_axis='Y')
objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
pts=[o.matrix_world@v.co for o in objs for v in o.data.vertices]
mn=mathutils.Vector([min(p[i] for p in pts) for i in range(3)]); mx=mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
c=(mn+mx)/2; size=max(mx-mn)*1.15; print('BBOX',tuple(round(x,2) for x in mn),tuple(round(x,2) for x in mx))
sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.render.resolution_x=sc.render.resolution_y=500; sc.render.film_transparent=False
w=bpy.data.worlds.new('w'); w.color=(0.8,0.8,0.8); sc.world=w
w.color=(0.55,0.55,0.55)
for rot in ((0.7,0.2,0.6),(0.9,0,3.6)):
    L=bpy.data.lights.new('s','SUN'); L.energy=3; lo=bpy.data.objects.new('s',L); sc.collection.objects.link(lo); lo.rotation_euler=rot
L=bpy.data.lights.new('s','SUN'); L.energy=4; lo=bpy.data.objects.new('s',L); sc.collection.objects.link(lo); lo.rotation_euler=(0.7,0.2,0.6)
cam=bpy.data.cameras.new('c'); cam.type='ORTHO'; cam.ortho_scale=size; co=bpy.data.objects.new('c',cam); sc.collection.objects.link(co); sc.camera=co
from PIL import Image
views={'+X':(1,0,0),'-X':(-1,0,0),'+Y':(0,1,0),'-Y':(0,-1,0),'top':(0,0,1),'iso':(1,-1,0.8)}
ims=[]
for n,d in views.items():
    d=mathutils.Vector(d).normalized(); co.location=c+d*size*3
    co.rotation_euler=(0,0,0) if n=='top' else (-d).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'/tmp/v_{n}.png'; bpy.ops.render.render(write_still=True); ims.append((n,Image.open(f'/tmp/v_{n}.png').copy()))
S=Image.new('RGB',(1500,1000),'white')
from PIL import ImageDraw
for k,(n,im) in enumerate(ims): S.paste(im.convert('RGB'),((k%3)*500,(k//3)*500)); ImageDraw.Draw(S).text(((k%3)*500+5,(k//3)*500+5),n,fill='red')
S.save(out)
