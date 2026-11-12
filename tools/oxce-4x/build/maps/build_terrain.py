"""4x terrain set GIJOE: tiles/*.png -> GIJOE_4X.PCK/.TAB (128x160) + GIJOE.PCK/.TAB (32x40 fallback) + GIJOE.MCD"""
import json, struct, sys, numpy as np
from PIL import Image
sys.path.insert(0,'/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad/hd')
from pck import palette
OUT=sys.argv[1]
T='/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad/oxc/oxce/build/bin/UFO/TERRAIN/'
names=json.load(open('tiles/names.json'))
PAL=np.array(palette(4),np.int32); USE=np.arange(1,255); UP=PAL[USE]
def quant(path,fw,fh):
    im=Image.open(path).convert('RGBA'); big=np.array(im).astype(np.float32); k=im.width//fw
    a=big[...,3:4]/255.; pre=np.concatenate([big[...,:3]*a,a],-1).reshape(fh,k,fw,k,4).mean((1,3))
    al=pre[...,3]; m=al>0.5; rgb=np.where(al[...,None]>0,pre[...,:3]/np.maximum(al[...,None],1e-6),0)
    idx=np.zeros((fh,fw),np.uint8); f=rgb[m]
    idx[m]=USE[np.argmin(((f[:,None,:]-UP[None])**2).sum(-1),1)]; return idx
def pck(frames):
    data=b''; offs=[]
    for f in frames:
        offs.append(len(data)); h,w=f.shape; rows=0
        while rows<h and not f[rows].any(): rows+=1
        out=bytearray([min(rows,254)]); flat=f[rows:].ravel(); i=0; n=len(flat)
        # trailing transparency need not be written
        last=n
        while last>0 and flat[last-1]==0: last-=1
        while i<last:
            if flat[i]==0:
                j=i
                while j<last and flat[j]==0 and j-i<255: j+=1
                out+=bytes([254,j-i]); i=j
            else: out.append(int(flat[i]) if flat[i] not in (254,255) else 253); i+=1
        out.append(255); data+=bytes(out)
    tab=b''.join(struct.pack('<I',o) for o in offs)
    return data,tab
files=[f'tiles/{i:02d}_{n}.png' for i,n in enumerate(names)]
hd=[quant(f,128,160) for f in files]; lo=[quant(f,32,40) for f in files]
for suffix,fr in [('_4X',hd),('',lo)]:
    d,t=pck(fr); open(f'{OUT}/GIJOE{suffix}.PCK','wb').write(d); open(f'{OUT}/GIJOE{suffix}.TAB','wb').write(t)
# MCD: each entry cloned from a vanilla tile with the right behaviour, then retargeted
def mcd(n):
    d=open(T+n+'.MCD','rb').read(); return [bytearray(d[i:i+62]) for i in range(0,len(d),62)]
barn,cult=mcd('BARN'),mcd('CULTIVAT')
I={n:i for i,n in enumerate(names)}
spec={ # name: (template, die_name or None, alt_name or None, armor override)
 'grass':(cult[0],'dirt',None,None),'dirt':(cult[1],None,None,None),'concrete':(barn[2],'rubble',None,20),
 'metalfloor':(barn[2],'rubble',None,30),'rubble':(cult[1],None,None,None),
 'joe_w':(barn[6],'rubble_w' ,None,30),'joe_n':(barn[5],'rubble_w',None,30),
 'joe_door_w':(barn[17],None,'joe_door_n',30),'joe_door_n':(barn[18],None,'joe_door_w',30),
 'joe_star_w':(barn[6],None,None,30),'joe_star_n':(barn[5],None,None,30),
 'cobra_w':(barn[11],None,None,50),'cobra_n':(barn[10],None,None,50),
 'cobra_door_w':(barn[17],None,'cobra_door_n',50),'cobra_door_n':(barn[18],None,'cobra_door_w',50),
 'cobra_emb_w':(barn[11],None,None,50),'cobra_emb_n':(barn[10],None,None,50),
 'roof_joe':(barn[0],None,None,20),'roof_cobra':(barn[0],None,None,30),
 'tree':(cult[9],None,None,None),'pine':(cult[12],None,None,None),'bush':(cult[13],None,None,None),
 'sandbag_w':(cult[18],None,None,40),'sandbag_n':(cult[19],None,None,40),
 'crate':(barn[15],None,None,20),'barrels':(cult[13],None,None,15),'console':(barn[15],None,None,20),
 'flagpole':(cult[13],None,None,10),'rock':(cult[13],None,None,60),
}
out=b''
for n in names:
    tpl,die,alt,arm=spec[n]; e=bytearray(tpl)
    for k in range(8): e[k]=I[n]
    e[44]=I[die] if die in I else 0; e[46]=I[alt] if alt in I else 0
    if arm is not None: e[42]=arm
    if n in ('barrels','flagpole','rock'): e[39]=255  # impassable small objects
    if n=='flagpole': e[31]=0
    out+=bytes(e)
open(f'{OUT}/GIJOE.MCD','wb').write(out)
print(len(names),'tiles', {n:i for i,n in enumerate(names)})
