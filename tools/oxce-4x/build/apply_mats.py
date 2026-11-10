"""Seamless materials + face-on doors/windows -> wall tiles, and the flat floors/roof slabs.
A wall tile's face is one tile wide by one level (384 render px) tall, so one 1024 square = one tile.
usage: apply_mats.py <materials dir>"""
import sys, os, glob, json, numpy as np
from PIL import Image
from scipy import ndimage
MAT=sys.argv[1]; SS=4; FW,FH=128*SS,160*SS; LEVEL=384.0; N=1024

def cut(path):                              # magenta key, same as the props
    a=np.array(Image.open(path).convert('RGB')).astype(np.float32)
    m=np.minimum(a[...,0],a[...,2])-a[...,1]; al=np.clip((150-m)/90,0,1)
    M=np.array([255,0,255],np.float32); rgb=np.clip((a-(1-al[...,None])*M)/np.maximum(al[...,None],0.05),0,255)
    pink=(np.minimum(rgb[...,0],rgb[...,2])-rgb[...,1])>15
    rgb[...,0]=np.where(pink,np.minimum(rgb[...,0],rgb[...,1]+12),rgb[...,0])
    rgb[...,2]=np.where(pink,np.minimum(rgb[...,2],rgb[...,1]+22),rgb[...,2])
    im=Image.fromarray(np.dstack([rgb,al*255]).astype(np.uint8),'RGBA')
    bb=im.getbbox(); return im.crop(bb) if bb else im

BOOST={'adobe':1.7}        # adobe's grain is real but fine; at 128px a tile it flattens to a plain field
_m={}
def mat(name):
    if name not in _m:
        im=Image.open(f'{MAT}/materials/{name}.png').convert('RGB')
        if im.size!=(N,N): im=im.resize((N,N),Image.LANCZOS)
        if name in BOOST:
            a=np.array(im).astype(np.float32); a=np.clip(a.mean((0,1))+(a-a.mean((0,1)))*BOOST[name],0,255)
            im=Image.fromarray(a.astype(np.uint8))
        _m[name]=im
    return _m[name]
_d={}
def dw(name):
    if name not in _d: _d[name]=cut(f'{MAT}/doors_windows/{name}.png')
    return _d[name]

def plain(matname):                         # a material square, no opening
    return mat(matname).convert('RGBA')

def emblem(base, frac=0.46, rgb=(228, 58, 46)):
    """The Cobra sigil on a panel. The art is flat ink on white paper, so the paper is keyed out
    and the ink recoloured; on dark steel it stays red, which is what reads at tile size."""
    a = np.array(Image.open('cobra_logo.png').convert('RGB')).astype(np.float32)
    mx, mn = a.max(-1), a.min(-1)
    al = np.clip((235 - mn) / 60, 0, 1) * np.clip((mx - mn) / 40 + (255 - mx) / 60, 0, 1)
    k = np.clip(a.mean(-1, keepdims=True) / 200.0, 0.55, 1.0)
    im = Image.fromarray(np.dstack([np.array(rgb, np.float32) * k, np.clip(al, 0, 1) * 255]).astype(np.uint8), 'RGBA')
    bb = im.getbbox()
    if bb: im = im.crop(bb)
    h = int(N * frac); w = max(1, round(im.width * h / im.height))
    im = im.resize((w, h), Image.LANCZOS)
    out = base.copy(); out.alpha_composite(im, ((N - w) // 2, (N - h) // 2)); return out

def place(base,art,hfrac,anchor):
    """anchor 'floor' sits it on the bottom edge; a number is the top edge as a fraction of the square."""
    im=dw(art) if isinstance(art,str) else art
    h=int(N*hfrac); w=max(1,round(im.width*h/im.height))
    if w>int(N*0.94): w=int(N*0.94); h=max(1,round(im.height*w/im.width))
    im=im.resize((w,h),Image.LANCZOS)
    y=N-h if anchor=='floor' else int(N*anchor)
    out=base.copy(); out.alpha_composite(im,((N-w)//2,y)); return out

def opening(base,wfrac,hfrac,anchor,arch=False,rolled=None):
    """Cut a dark hole in the wall: an open archway or a retracted roll-up door."""
    w=int(N*wfrac); h=int(N*hfrac); x=(N-w)//2; y=N-h if anchor=='floor' else int(N*anchor)
    yy,xx=np.mgrid[0:h,0:w]; m=np.ones((h,w),np.float32)
    if arch:                                                    # round the top corners
        r=w/2.0; cy=r; m=np.where((yy<cy)&(((xx-w/2.0)**2+(yy-cy)**2)>r*r),0.0,m)
    dark=np.zeros((h,w,3),np.float32)
    dark[...,0]=26; dark[...,1]=22; dark[...,2]=20
    dark*= (0.55+0.45*np.clip(yy/max(1,h*0.8),0,1))[...,None]   # a little light reaching the floor inside
    hole=Image.fromarray(np.dstack([dark,m*255]).astype(np.uint8),'RGBA')
    out=base.copy()
    sh=Image.fromarray(np.dstack([np.zeros((h,w,3),np.uint8),(ndimage.gaussian_filter(m,14)*110).astype(np.uint8)]),'RGBA')
    out.alpha_composite(sh,(x,y)); out.paste(hole,(x,y),hole)
    if rolled is not None:                                      # the drum of the raised door
        d=dw(rolled); dh=int(h*0.17); dwd=w; d=d.resize((dwd,dh),Image.LANCZOS); out.alpha_composite(d,(x,y))
    return out

def panel(im,axis,shade,frac=1.0):
    w,h=im.size; Hpx=LEVEL*frac
    if axis=='w': coef=(-w/256.0,0,w,  0.5*h/Hpx, h/Hpx, h*(Hpx-512)/Hpx)
    else:         coef=( w/256.0,0,-w, -0.5*h/Hpx, h/Hpx, h*(Hpx-256)/Hpx)
    out=im.transform((FW,FH),Image.AFFINE,coef,Image.BICUBIC)
    a=np.array(out).astype(np.float32); a[...,:3]*=shade
    return Image.fromarray(np.clip(a,0,255).astype(np.uint8),'RGBA')

# ---- flat tiles: the same treatment the ground textures get
def even(im):
    a=np.array(im.convert('RGB')).astype(np.float32)
    a=a[256:768,256:768]; n=a.shape[0]; t=np.abs(np.linspace(-1,1,n)); w=np.clip((1-t)*2.2,0,1)
    w2=np.maximum(np.outer(w,np.ones(n)),0)*np.outer(np.ones(n),w)
    r=np.roll(a,(n//2,n//2),(0,1)); return np.clip(a*w2[...,None]+r*(1-w2[...,None]),0,255).astype(np.uint8)
def diamond(tex):
    T=Image.fromarray(tex); n=T.width; hw,hh=64*SS,32*SS; cx,cy=64*SS,128*SS
    a=n/(2*hw); b=n/(2*hh); coef=(a,b,-a*cx-b*(cy-hh), -a,b,a*cx-b*(cy-hh))
    out=T.convert('RGBA').transform((FW,FH),Image.AFFINE,coef,Image.BICUBIC)
    yy,xx=np.mgrid[0:FH,0:FW]; inside=(np.abs(xx+0.5-cx)/hw+np.abs(yy+0.5-cy)/hh)<=1.0
    o=np.array(out); o[...,3]=np.where(inside,255,0); return Image.fromarray(o)

def tile_path(folder,name):
    names=json.load(open(f'{folder}/names.json')); i=names.index(name)
    return (glob.glob(f'{folder}/{i:02d}_{name}.png')+glob.glob(f'{folder}/{i:03d}_{name}.png'))[0]

# mine_timber came back as a mine portal with posts and a lintel, so it cannot tile.
# It is exactly what mineframe wants, and the planking is recovered from the barn boards.
def planking():
    a=np.array(mat('barn_board')).astype(np.float32)
    g=a.mean(-1,keepdims=True)                                  # strip the red paint, keep the grain
    a=g*np.array([1.06,0.99,0.88])+np.array([6,4,0]); return Image.fromarray(np.clip(a,0,255).astype(np.uint8))

# ---- what goes where
WALLS={
 'natiles':{
  'wallW':plain('siding_white'),      'winW':place(plain('siding_white'),'window_shutter',0.46,0.22),
  'doorW':place(plain('siding_white'),'door_wood',0.84,'floor'),
  'dooropenW':place(plain('siding_white'),'door_wood_open',0.84,'floor'),
  'wallB':plain('siding_blue'),       'winB':place(plain('siding_blue'),'window_house',0.44,0.24),
  'doorB':place(plain('siding_blue'),'door_wood',0.84,'floor'),
  'dooropenB':place(plain('siding_blue'),'door_wood_open',0.84,'floor'),
  'wallY':plain('siding_yellow'),     'winY':place(plain('siding_yellow'),'window_house',0.44,0.24),
  'doorY':place(plain('siding_yellow'),'door_wood',0.84,'floor'),
  'dooropenY':place(plain('siding_yellow'),'door_wood_open',0.84,'floor'),
  'wallK':plain('brick_red'),         'winK':place(plain('brick_red'),'window_house',0.44,0.24),
  'doorK':place(plain('brick_red'),'door_wood',0.84,'floor'),
  'dooropenK':place(plain('brick_red'),'door_wood_open',0.84,'floor'),
  'barn':plain('barn_board'),         'barndoor':place(plain('barn_board'),'door_barn',0.88,'floor')},
 'cobratiles':{
  'bunker':plain('concrete_mil'),     'slit':place(plain('concrete_mil'),'window_slit',0.17,0.33),
  'blast':place(plain('steel_plate'),'door_steel',0.86,'floor'),
  'blastopen':place(plain('steel_plate'),'door_steel_open',0.86,'floor'),
  'corr':plain('corrugated'),         'corrsign':emblem(plain('corrugated')),
  'roll':place(plain('corrugated'),'door_rollup',0.80,'floor'),
  'rollopen':opening(plain('corrugated'),0.72,0.80,'floor',rolled='door_rollup'),
  'glass':place(plain('steel_plate'),'window_glass',0.80,0.10),
  'glassdoor':place(plain('steel_plate'),'window_glass',0.86,'floor'),   # the shop door is a house door; Cobra gets the dark-framed glass
  'sandwall':plain('sandbag')},
 'wildtiles':{
  'adobe':plain('adobe'),             'adobewin':place(plain('adobe'),'window_adobe',0.40,0.26),
  'adobearch':opening(plain('adobe'),0.56,0.78,'floor',arch=True),
  'cabin':plain('log_cabin'),         'cabinwin':place(plain('log_cabin'),'window_cabin',0.42,0.26),
  'cabinarch':opening(plain('log_cabin'),0.54,0.78,'floor')},
 'mtntiles':{
  'minewall':planking().convert('RGBA'),
  'mineframe':Image.open(f'{MAT}/materials/mine_timber.png').convert('RGBA')},
}
FLATS={'natiles':{'lino':'lino_check','scorched':'scorched'},
       'cobratiles':{'metalroof':'roof_metal','concroof':'roof_concrete','ctile':'plaster_white',
                     'grate':'floor_grate','hazard':'floor_hazard','ccarpet':'carpet_dark'},
       'wildtiles':{'adoberoof':'roof_adobe'},
       'mtntiles':{'snowcap':'snow_cap','trail':'trail_dirt','rock2':'rock_dark'}}
# a solid block: the two faces you can see, and the top one level up
CUBES={'mtntiles':{'cliff':('cliff_rock','rock_dark'),'cliffsnow':('cliff_rock','snow_cap')}}

def cube(side,top):
    out=Image.new('RGBA',(FW,FH),(0,0,0,0))
    for axis,shade in (('w',0.84),('n',1.0)): out.alpha_composite(panel(plain(side),axis,shade))
    lid=diamond(even(mat(top)))
    out.alpha_composite(lid,(0,-int(LEVEL)))      # the top face sits one level above the floor
    return out

nw=nf=0; missing=[]
for folder,m in WALLS.items():
    names=set(json.load(open(f'{folder}/names.json')))
    for stem,src in m.items():
        for axis,shade in (('w',0.84),('n',1.0)):
            t=f'{stem}_{axis}'
            if t not in names: missing.append(t); continue
            panel(src,axis,shade).save(tile_path(folder,t)); nw+=1
for folder,m in FLATS.items():
    names=set(json.load(open(f'{folder}/names.json')))
    for stem,src in m.items():
        if stem not in names: missing.append(stem); continue
        diamond(even(mat(src))).save(tile_path(folder,stem)); nf+=1
nc=0
for folder,m in CUBES.items():
    names=set(json.load(open(f'{folder}/names.json')))
    for stem,(side,top) in m.items():
        if stem not in names: missing.append(stem); continue
        cube(side,top).save(tile_path(folder,stem)); nc+=1
print('walls',nw,'flats',nf,'cubes',nc)
if missing: print('no such tile:',' '.join(missing))
