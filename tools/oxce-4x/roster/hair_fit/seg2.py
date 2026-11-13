import numpy as np, sys
d=np.load('bust.npz'); V,F=d['V'],d['F']; C=V[F].mean(1)
P=dict(rx=0.075,rz=0.115,yth=-0.03,jaw=-0.075,backy=-0.02,maxx=0.125,bottom=-0.165)
for a in sys.argv[1:]: k,v=a.split('='); P[k]=float(v)
ell=((C[:,0])/P['rx'])**2+((C[:,2]-0.015)/P['rz'])**2
face=(ell<1)&(C[:,1]<P['yth'])
low=C[:,2]<P['jaw']
keep_low=low&(C[:,1]>P['backy'])&(np.abs(C[:,0])<P['maxx'])&(C[:,2]>P['bottom'])
hair=(~face&~low)|keep_low
# drop tiny islands: keep largest connected components by face adjacency (vertex-shared)
import scipy.sparse as sp, scipy.sparse.csgraph as cg
idx=np.where(hair)[0]; f=F[idx]; nV=len(V)
A=sp.coo_matrix((np.ones(len(idx)*3),(np.repeat(np.arange(len(idx)),3),f.ravel())),shape=(len(idx),nV)).tocsr()
G=A@A.T; n,lab=cg.connected_components(G,directed=False); sz=np.bincount(lab)
good=np.isin(lab,np.where(sz>=150)[0]); hair[idx[~good]]=False
np.save('mask.npy',hair.astype(np.uint8)); print('hair faces',hair.sum(),'components kept',(sz>=150).sum(),'of',n)
