import bpy, numpy as np, json, sys
from mathutils import Vector
card=json.load(open('/tmp/claude-0/bar/pkg/C_BARONESS.look.json')); pr=[p for p in card['props'] if p['type']=='mesh_part'][0]; zc=pr['zones'][0]
bpy.ops.wm.open_mainfile(filepath='/tmp/claude-0/bar/pkg/baroness.blend')
old=bpy.data.objects['baroness_hair_0']; mat=old.data.materials[0]; arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
dd=np.load('/tmp/claude-0/bar/baroness_hair_bust.npz'); V,F,wh=dd['V'],dd['F'],dd['wh']
me=bpy.data.meshes.new('baroness_hair_0_v2'); me.from_pydata(V.tolist(),[],F.tolist()); me.update()
for p in me.polygons: p.use_smooth=True
Lk=Vector(pr.get('light',[-0.45,-0.6,0.66])).normalized(); cut=zc.get('cut',[-0.10,0.55])
sh_,bs_,hi_=(np.array(zc[k],float) for k in ('shadow','rgb','high'))
ca=me.color_attributes.new('cel','BYTE_COLOR','CORNER')
for poly in me.polygons:
    dt=poly.normal.dot(Lk); c_=sh_ if dt<cut[0] else (hi_ if dt>cut[1] else bs_)
    for li in poly.loop_indices: ca.data[li].color_srgb=tuple(c_/255.0)+(1.0,)
me.materials.append(mat)
name=old.name; bpy.data.objects.remove(old,do_unlink=True)
ob=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(ob)
g1=ob.vertex_groups.new(name=pr.get('bone','mixamorig:Head')); g2=ob.vertex_groups.new(name=pr.get('bone2','mixamorig:Spine2'))
for vi,w in enumerate(wh):
    if w>0: g1.add([vi],float(w),'REPLACE')
    if w<1: g2.add([vi],float(1-w),'REPLACE')
md=ob.modifiers.new('arm','ARMATURE'); md.object=arm
bpy.ops.wm.save_as_mainfile(filepath='/tmp/claude-0/bar/v2/baroness.blend',compress=True); print('saved', len(V), len(F))
