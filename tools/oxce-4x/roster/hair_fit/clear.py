import numpy as np
from scipy.spatial import cKDTree
d=dict(np.load('baroness_hair_bust.npz')); V=d['V'].astype(float); H=np.load('ch47_head.npy')
cen=np.array([0,0.01,1.64]); GAP=0.004
def unit(a): return (a-cen)/np.linalg.norm(a-cen,axis=1,keepdims=True)
uh=unit(H); rh=np.linalg.norm(H-cen,axis=1); t=cKDTree(uh)
for it in range(3):
    uv=unit(V); rv=np.linalg.norm(V-cen,axis=1)
    lst=t.query_ball_point(uv, r=np.radians(5))      # head verts within ~5 degrees of the hair vertex direction
    need=np.array([rh[l].max()+GAP if len(l) else 0 for l in lst])
    push=np.maximum(need-rv,0)
    # smooth the push over neighbours so strands don't kink
    tv=cKDTree(V); nb=tv.query(V,k=8)[1]; push=np.maximum(push, push[nb].mean(1)*0.8)
    V=cen+uv*(rv+push)[:,None]
    print(f'pass {it}: moved {(push>0).sum()} verts, max {push.max()*1000:.1f} mm')
# re-test
uv=unit(V); rv=np.linalg.norm(V-cen,axis=1); tv=cKDTree(uv)
dist,nn=tv.query(uh); poke=(rh>rv[nn])&(dist<np.radians(3))
print('head verts still poking:',poke.sum(),'worst %.1f mm'%((rh-rv[nn])[poke].max()*1000 if poke.any() else 0))
d['V']=V.astype(np.float32); np.savez('baroness_hair_bust.npz',**d)
