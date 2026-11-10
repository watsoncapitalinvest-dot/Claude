"""Face-on painted panels -> wall tiles, plus the addendum's isometric objects.
A wall tile's face is a parallelogram in the 512x640 render: one tile long, one level (384px) tall.
usage: apply_walls.py <art dir>"""
import sys, glob, json, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
ART=sys.argv[1]; SS=4; FW,FH=128*SS,160*SS; LEVEL=384.0     # one level, in render pixels
def cut(path):
    a=np.array(Image.open(path).convert('RGB')).astype(np.float32)
    m=np.minimum(a[...,0],a[...,2])-a[...,1]; al=np.clip((150-m)/90,0,1)
    M=np.array([255,0,255],np.float32); rgb=np.clip((a-(1-al[...,None])*M)/np.maximum(al[...,None],0.05),0,255)
    pink=(np.minimum(rgb[...,0],rgb[...,2])-rgb[...,1])>15
    rgb[...,0]=np.where(pink,np.minimum(rgb[...,0],rgb[...,1]+12),rgb[...,0]); rgb[...,2]=np.where(pink,np.minimum(rgb[...,2],rgb[...,1]+22),rgb[...,2])
    return Image.fromarray(np.dstack([rgb,al*255]).astype(np.uint8),'RGBA')
def trim(im):           # the painter left magenta margins on some; crop to the art
    bb=im.getbbox(); return im.crop(bb) if bb else im
def tile_path(folder,name):
    names=json.load(open(f'{folder}/names.json')); i=names.index(name)
    return (glob.glob(f'{folder}/{i:02d}_{name}.png')+glob.glob(f'{folder}/{i:03d}_{name}.png'))[0]
def panel(im,axis,shade,frac=None,hang=False):
    """Map a face-on panel onto the west ('w') or north ('n') wall plane of one tile.
    frac overrides the height the image's own aspect implies; hang pins it to the top of the wall."""
    w,h=im.size; Hpx=LEVEL*(frac if frac else h/w)
    yoff=(LEVEL-Hpx) if hang else 0.0               # a banner hangs from the top; everything else stands on the floor
    if axis=='w': coef=(-w/256.0,0,w,  0.5*h/Hpx, h/Hpx, h*(yoff+Hpx-512)/Hpx)
    else:         coef=( w/256.0,0,-w, -0.5*h/Hpx, h/Hpx, h*(yoff+Hpx-256)/Hpx)
    out=im.transform((FW,FH),Image.AFFINE,coef,Image.BICUBIC)
    a=np.array(out).astype(np.float32); a[...,:3]*=shade      # sun from the upper left: the west face is the shaded one
    return Image.fromarray(np.clip(a,0,255).astype(np.uint8),'RGBA')
PANELS={   # tile stem -> source image ; tiles exist as <stem>_w and <stem>_n
 'natiles':  {'picket':'fence_picket','chain':'fence_chain','rail':'fence_rail','hedge':'hedge',
              'parapet':'parapet','rubble_wall':'rubble_house',
              'shop':('shop_front',1.0,False),'shopR':('shop_front_plain',1.0,False)},
 'cobratiles':{'razor':'razor_wire','cell':'bars_cell','banner':('banner_cobra_e',0.72,True),'crubble':'rubble_concrete'},
 'wildtiles': {'wrubble':'rubble_adobe'},
 'mtntiles':  {'mrubble':'rubble_mine'}}
src={}
import os
def img(n):
    if n not in src:
        p=f'{ART}/{n}.png'
        if not os.path.exists(p): p=f'bldart/{n}.png'
        src[n]=trim(cut(p))
    return src[n]
n=0
for folder,m in PANELS.items():
    names=set(json.load(open(f'{folder}/names.json')))
    for stem,art in m.items():
        frac,hang=(None,False)
        if isinstance(art,tuple): art,frac,hang=art
        for axis,shade in (('w',0.84),('n',1.0)):
            t=f'{stem}_{axis}'
            if t not in names: continue
            panel(img(art),axis,shade,frac,hang).save(tile_path(folder,t)); n+=1
# ---- isometric objects, same treatment as the props
def contact(im):
    a=np.array(im)[...,3]>128; H,W=a.shape; cols=np.where(a.any(0))[0]; out=np.zeros((H,W),np.float32)
    if not len(cols): return Image.new('RGBA',im.size,(0,0,0,0))
    low=np.array([np.where(a[:,x])[0][-1] if a[:,x].any() else -1 for x in range(W)]); gb=low.max(); xc=np.mean(np.where(low>=gb-2*SS)[0])
    for x in cols:
        if low[x]>=gb-(abs(x-xc)*0.5+12*SS): out[max(0,low[x]-5*SS):low[x]+1,x]=1
    out=ndimage.binary_dilation(out>0,iterations=2*SS).astype(np.float32)
    out=np.roll(out,(int(1.5*SS),int(1.5*SS)),(0,1)); out=ndimage.gaussian_filter(out,2.2*SS)*0.62*255
    return Image.merge('RGBA',[Image.new('L',im.size,12),Image.new('L',im.size,16),Image.new('L',im.size,26),Image.fromarray(np.clip(out,0,255).astype(np.uint8))])
OBJ={('cobratiles','flagpole'):('flagpole_e',60,140),('cobratiles','crubble'):('rubble_pile',104,60)}
for (folder,name),(art,mw,mh) in OBJ.items():
    if name not in json.load(open(f'{folder}/names.json')): continue
    im=img(art); k=min(mw*SS/im.width,mh*SS/im.height); im=im.resize((max(1,round(im.width*k)),max(1,round(im.height*k))),Image.LANCZOS)
    pad=8*SS; big=Image.new('RGBA',(im.width+2*pad,im.height+2*pad),(0,0,0,0)); big.alpha_composite(im,(pad,pad))
    g=contact(big); g.alpha_composite(big)
    bottom=min(158*SS,133*SS+im.width//4)
    can=Image.new('RGBA',(FW,FH),(0,0,0,0)); can.alpha_composite(g,(64*SS-im.width//2-pad,max(0,bottom-im.height)-pad))
    can.save(tile_path(folder,name)); n+=1
# ---- stairs: one painted flight, cut across the two tiles it occupies (same split as the vehicles)
names=json.load(open('natiles/names.json'))
if 'stairs_y0' in names:
    im=img('stairs_straight'); k=min(150*SS/im.width,120*SS/im.height)
    im=im.resize((round(im.width*k),round(im.height*k)),Image.LANCZOS)
    CW,CH=192*SS,192*SS; cx,cy=96*SS,150*SS
    can=Image.new('RGBA',(CW,CH),(0,0,0,0)); can.alpha_composite(im,(cx-im.width//2,cy-im.height))
    a=np.array(can); y1=a.copy(); y1[:,cx:]=0; y0=a.copy(); y0[:,:cx]=0
    f0=Image.fromarray(y0).crop((64*SS,0,192*SS,160*SS)); f1=Image.fromarray(y1).crop((0,32*SS,128*SS,192*SS))
    f0.save(tile_path('natiles','stairs_y0')); f1.save(tile_path('natiles','stairs_y1'))
    f0.transpose(Image.FLIP_LEFT_RIGHT).save(tile_path('natiles','stairs_x0'))
    f1.transpose(Image.FLIP_LEFT_RIGHT).save(tile_path('natiles','stairs_x1')); n+=4
print(n,'tiles')
