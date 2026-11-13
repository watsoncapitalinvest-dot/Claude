import bpy, numpy as np, sys
S=float(sys.argv[1]) if len(sys.argv)>1 else 1.0; TARGET=int(sys.argv[2]) if len(sys.argv)>2 else 6000
d=np.load('bust.npz'); V,F=d['V'],d['F']; m=np.load('mask.npy').astype(bool)
Fh=F[m]; used=np.unique(Fh); remap=-np.ones(len(V),int); remap[used]=np.arange(len(used)); Vh=V[used]; Fh=remap[Fh]
nb=np.array([-0.0034,-0.1155,0.0085]); nc=np.array([0.0,-0.1016,1.6366])
Vh=(Vh-nb)*S+nc
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new('h'); me.from_pydata(Vh.tolist(),[],Fh.tolist()); me.update()
ob=bpy.data.objects.new('h',me); bpy.context.scene.collection.objects.link(ob); bpy.context.view_layer.objects.active=ob; ob.select_set(True)
md=ob.modifiers.new('d','DECIMATE'); md.ratio=min(1,TARGET/len(me.polygons)); bpy.ops.object.modifier_apply(modifier='d')
me=ob.data; me.calc_loop_triangles()
V2=np.array([v.co[:] for v in me.vertices]); F2=np.array([t.vertices[:] for t in me.loop_triangles])
# outward: faces should point away from the head centre
cen=np.array([0,0.01,1.64]); Cc=V2[F2].mean(1); N=np.cross(V2[F2[:,1]]-V2[F2[:,0]],V2[F2[:,2]]-V2[F2[:,0]])
out=np.einsum('ij,ij->i',N,Cc-cen)>0; print('faces facing out', out.mean().round(3))
if out.mean()<0.5: F2=F2[:,::-1].copy()
# penetration: Ch47 head verts that are OUTSIDE the hair shell (closer to camera than hair along the radial ray)
H=np.load('ch47_head.npy')
from scipy.spatial import cKDTree
t=cKDTree(V2); dist,nn=t.query(H)
# a head vertex pokes out if it is further from the centre than its nearest hair vertex AND close to it laterally
rh=np.linalg.norm(H-cen,axis=1); rv=np.linalg.norm(V2[nn]-cen,axis=1)
poke=(rh>rv)&(dist<0.03)
print('hair', len(V2),'verts',len(F2),'tris; z',V2[:,2].min().round(3),V2[:,2].max().round(3),'| Ch47 head verts poking through:',poke.sum(),'of',len(H),'worst %.1f mm'%((rh-rv)[poke].max()*1000 if poke.any() else 0))
zref=1.62; wh=np.clip((V2[:,2]-1.48)/(zref-1.48),0,1)
np.savez('baroness_hair_bust.npz',V=V2.astype(np.float32),F=F2.astype(np.int32),zone=np.zeros(len(F2),np.uint8),wh=wh.astype(np.float32))
np.save('poke.npy',H[poke])
