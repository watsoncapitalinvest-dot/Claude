"""Generic craft terrain (craftmaps.json): heli/c_i_j_k.png cells -> JOEHELO(_4X).PCK/TAB + JOEHELO.MCD, MAPS/JOEHELO.MAP (10x10x3), ROUTES/JOEHELO.RMP."""
import sys, glob, re, struct, numpy as np
from PIL import Image
sys.path.insert(0,'/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad/hd'); from pck import load_pck, palette
src=open('build_terrain.py').read(); exec(src[src.index('PAL=np.array'):src.index('files=')])   # quant(), pck()
OUT=sys.argv[1]; import json; NAME=sys.argv[3]; C=json.load(open('craftmaps.json'))[NAME]; SET=C['set']; W,Lm,Z=C['W'],C['L'],C['Z']; T='/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad/oxc/oxce/build/bin/UFO/TERRAIN/'
# --- which cells hold hull (solid) vs only rotor blade (no collision): sample the chassis surface in the same transform heli.js uses
s=C['len']/C['model_len']; zs=C.get('zs',1); occ={}
V=[];F=[];cur=None
import re as _re
SK=_re.compile(r'FX|MUZZLE|LIGHT|SMOKE|EXPLO|GLOW|NVBUGGY|_PROP$|^PROPS|TREAD|HOUSECOLOR|BARREL|RECTANGLE|^PROPELLER')
for ln in open(C['file']):
    if ln.startswith('g '): cur=ln.split()[1]
    elif ln.startswith('v '): V.append([float(t) for t in ln.split()[1:]])
    elif ln.startswith('f ') and not SK.search(cur): F.append([int(t)-1 for t in ln.split()[1:]])
V=np.array(V); zo=-V[:,2].min() if C.get('zfix') else 0
P=np.stack([C['cx']+V[:,1]*s, C['cy']-V[:,0]*s,(V[:,2]+zo)*s*zs/1.5],1) if C.get('noseY') else np.stack([C['cx']+V[:,0]*s, C['cy']-V[:,1]*s,(V[:,2]+zo)*s*zs/1.5],1)
rng=np.random.default_rng(1)
for a,b,c in F:
    u=rng.random((400,2)); m=u.sum(1)>1; u[m]=1-u[m]
    pts=P[a]+u[:,:1]*(P[b]-P[a])+u[:,1:]*(P[c]-P[a])
    for q in np.floor(pts).astype(int): occ[tuple(q)]=occ.get(tuple(q),0)+1
hull={k for k,n in occ.items() if n>=60}
# --- frames
hd=[]; lo=[]
g4=load_pck(OUT+'/../TERRAIN/GIJOE_4X.PCK',OUT+'/../TERRAIN/GIJOE_4X.TAB',128,160) if False else None
cells=[]
for f in sorted(glob.glob(f'cm_{NAME}/c_*.png')):
    i,j,k=map(int,re.findall(r'\d+',f.split('/')[-1]))
    if Image.open(f).getbbox(): cells.append(((i,j,k),f))
pad4=np.array(load_pck(sys.argv[2]+'/GIJOE_4X.PCK',sys.argv[2]+'/GIJOE_4X.TAB',128,160)[2],np.uint8).reshape(160,128)
pad1=np.array(load_pck(sys.argv[2]+'/GIJOE.PCK',sys.argv[2]+'/GIJOE.TAB',32,40)[2],np.uint8).reshape(40,32)
hd.append(pad4); lo.append(pad1)
for _,f in cells: hd.append(quant(f,128,160)); lo.append(quant(f,32,40))
for suf,fr in [('_4X',hd),('',lo)]:
    d,t=pck(fr); open(f'{OUT}/TERRAIN/{SET}{suf}.PCK','wb').write(d); open(f'{OUT}/TERRAIN/{SET}{suf}.TAB','wb').write(t)
# --- MCD: 0 pad floor (start point), then one object per cell
pl=open(T+'PLANE.MCD','rb').read(); PL=[bytearray(pl[i:i+62]) for i in range(0,len(pl),62)]
def ent(tpl,frame):
    e=bytearray(tpl)
    for q in range(8): e[q]=frame
    e[44]=0; e[46]=0; return e
mcd=[ent(PL[2],0)]; mcd[0][59]=1
idx={}
for n,(c,_) in enumerate(cells):
    e=ent(PL[42],n+1)
    if c not in hull: e[8:20]=bytes(12); e[31]=0; e[36]=0   # rotor blade only: no collision, does not block sight or fire
    mcd.append(e); idx[c]=n+1
open(f'{OUT}/TERRAIN/{SET}.MCD','wb').write(b''.join(bytes(e) for e in mcd))
# --- MAP 10x10x3 (BLANKS = 2 entries first)
B=2; data=bytes([Lm,W,Z])
for z in range(Z-1,-1,-1):
    for y in range(Lm):
        for x in range(W):
            t=[0,0,0,0]
            if z==0: t[0]=B+0
            if (x,y,z) in idx: t[3]=B+idx[(x,y,z)]
            data+=bytes(t)
open(f'{OUT}/MAPS/{SET}.MAP','wb').write(data); open(f'{OUT}/ROUTES/{SET}.RMP','wb').write(b'')
print(len(cells),'cells,',len([c for c,_ in cells if c in hull]),'solid; ground hull',sorted((c[0],c[1]) for c,_ in cells if c in hull and c[2]==0))
