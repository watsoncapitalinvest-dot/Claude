import numpy as np
from scipy.spatial import cKDTree
d=dict(np.load('baroness_hair_bust.npz')); V=d['V'].astype(float); S=np.load('ch47_surf.npz'); P,N=S['P'],S['N']; GAP=0.005
t=cKDTree(P)
for it in range(4):
    dist,nn=t.query(V,k=6)
    # signed offset of each hair vertex from the body surface, along the body normal (averaged over 6 nearest)
    off=np.einsum('ikj,ikj->ik',V[:,None,:]-P[nn],N[nn]).mean(1); nrm=N[nn].mean(1); nrm/=np.linalg.norm(nrm,axis=1,keepdims=True)
    need=np.clip(GAP-off,0,None)*(dist[:,0]<0.05)
    tv=cKDTree(V); nb=tv.query(V,k=8)[1]; need=np.maximum(need,need[nb].mean(1)*0.7)
    V+=nrm*need[:,None]
    print(f'pass {it}: moved {(need>1e-5).sum()} verts, max {need.max()*1000:.1f} mm')
d['V']=V.astype(np.float32); np.savez('baroness_hair_bust.npz',**d)
dist,nn=t.query(V,k=6); off=np.einsum('ikj,ikj->ik',V[:,None,:]-P[nn],N[nn]).mean(1)
print('hair verts inside the body after:',((off<0)&(dist[:,0]<0.05)).sum())
