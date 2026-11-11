from PIL import Image, ImageDraw, ImageFilter, ImageFont
import random
random.seed(11)

# ---- the projection, straight out of Camera::convertMapToScreen -----------
# screenX = x*(W/2) - y*(W/2)
# screenY = x*(W/4) + y*(W/4) - z*((H + W/4)/2)
# with spriteWidth W=32, spriteHeight H=40:
SW, SH = 32, 40
DX   = SW//2          # 16  - half-width of a tile step
DY   = SW//4          #  8  - half-height of a tile step  -> floor diamond 32x16, 2:1
DZ   = (SH + SW//4)//2 # 24  - one storey. 24 against a 32 tile: 3:4.
BLOCK = 10            # one base-view square = one 10x10 map block (XBASE_xx)

CON=(150,150,148); CON_L=(120,120,118); CON_R=(96,96,95)
WT=(188,188,185);  WL=(142,142,140);   WR=(100,100,99)
OL=(130,144,110);  OL_L=(102,115,86);  OL_R=(80,92,66)
ST=(160,164,168);  ST_L=(119,123,129); ST_R=(92,96,102)
AMB=(208,172,54);  DARK=(30,30,32);    RED=(168,58,52)

def sh(c,f): return tuple(max(0,min(255,int(v*f))) for v in c)

class Scene:
    def __init__(s,w,h,ox,oy):
        s.im=Image.new('RGBA',(w,h),(0,0,0,0)); s.d=ImageDraw.Draw(s.im)
        s.ox,s.oy=ox,oy
    def P(s,x,y,z=0): return (s.ox+(x-y)*DX, s.oy+(x+y)*DY - z*DZ)
    def grain(s,pts,base,g=8,lines=None):
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        x0,y0=int(min(xs))-1,int(min(ys))-1; x1,y1=int(max(xs))+2,int(max(ys))+2
        w,h=x1-x0,y1-y0
        if w<1 or h<1: return
        pa=Image.new('RGB',(w,h),base); px=pa.load()
        for yy in range(h):
            for xx in range(w):
                n=random.randint(-g,g); r,gg,b=px[xx,yy]
                px[xx,yy]=(max(0,min(255,r+n)),max(0,min(255,gg+n)),max(0,min(255,b+n)))
        if lines:
            pd=ImageDraw.Draw(pa)
            for a,b in lines: pd.line([(a[0]-x0,a[1]-y0),(b[0]-x0,b[1]-y0)], fill=sh(base,.82))
        m=Image.new('L',(w,h),0)
        ImageDraw.Draw(m).polygon([(p[0]-x0,p[1]-y0) for p in pts], fill=255)
        s.im.paste(pa,(x0,y0),m)
    def floor(s,x,y,col=CON,lane=None):
        p=[s.P(x,y),s.P(x+1,y),s.P(x+1,y+1),s.P(x,y+1)]
        s.grain(p,col,7)
        s.d.line([p[0],p[1]],fill=sh(col,.9)); s.d.line([p[0],p[3]],fill=sh(col,.9))
        if lane=='x': s.d.line([s.P(x,y+.5),s.P(x+1,y+.5)],fill=AMB,width=2)
        if lane=='y': s.d.line([s.P(x+.5,y),s.P(x+.5,y+1)],fill=AMB,width=2)
        if lane=='hz':
            for k in range(3):
                a=s.P(x+k/3.,y); b=s.P(x+(k+.5)/3.,y); c=s.P(x+(k+.5)/3.,y+1); e=s.P(x+k/3.,y+1)
                s.d.polygon([a,b,c,e],fill=AMB if k%2==0 else DARK)
    def prism(s,x,y,w,l,levels,top,left,right,z=0,courses=0,stencil=False):
        h=levels
        t =[s.P(x,y,z+h),s.P(x+w,y,z+h),s.P(x+w,y+l,z+h),s.P(x,y+l,z+h)]
        lf=[s.P(x,y+l,z+h),s.P(x+w,y+l,z+h),s.P(x+w,y+l,z),s.P(x,y+l,z)]
        rf=[s.P(x+w,y,z+h),s.P(x+w,y+l,z+h),s.P(x+w,y+l,z),s.P(x+w,y,z)]
        ll=[];rl=[]
        for k in range(1,max(1,courses)):
            f=k/courses*h*DZ
            ll.append(((lf[0][0],lf[0][1]+f),(lf[1][0],lf[1][1]+f)))
            rl.append(((rf[0][0],rf[0][1]+f),(rf[1][0],rf[1][1]+f)))
        s.grain(rf,right,7,rl); s.grain(lf,left,7,ll); s.grain(t,top,6)
        s.d.line(t+[t[0]],fill=sh(top,1.1))
        if stencil:
            c=s.P(x+w/2,y+l,z+h*.55); s.d.rectangle([c[0]-4,c[1]-2,c[0]+4,c[1]+2],fill=sh(AMB,.85))
    def contact(s,x,y,w,l):
        c=s.P(x+w/2,y+l/2)
        g=Image.new('RGBA',(int(w*DX*2.4)+8,int(l*DY*2.6)+8),(0,0,0,0))
        ImageDraw.Draw(g).ellipse([0,0,g.width-1,g.height-1],fill=(0,0,0,80))
        g=g.filter(ImageFilter.GaussianBlur(2))
        s.im.alpha_composite(g,(int(c[0]-g.width/2),int(c[1]-g.height/2+2)))
    def crate(s,x,y,z=0,sz=.9):
        if z==0: s.contact(x,y,sz,sz)
        s.prism(x,y,sz,sz,.9,OL,OL_L,OL_R,z=z,courses=3,stencil=True)
    def fence(s,x,y,axis,ln,h=1.7):
        a0=s.P(x,y,h); a1=s.P(x+ln,y,h) if axis=='x' else s.P(x,y+ln,h)
        b0=s.P(x,y,0); b1=s.P(x+ln,y,0) if axis=='x' else s.P(x,y+ln,0)
        lay=Image.new('RGBA',s.im.size,(0,0,0,0)); ld=ImageDraw.Draw(lay)
        n=int(ln*DX*2/5)
        for k in range(n+1):
            f=k/n
            p0=(a0[0]+(a1[0]-a0[0])*f,a0[1]+(a1[1]-a0[1])*f)
            p1=(b0[0]+(b1[0]-b0[0])*f,b0[1]+(b1[1]-b0[1])*f)
            ld.line([p0,(p1[0]+6,p1[1])],fill=(198,202,206,90))
            ld.line([p0,(p1[0]-6,p1[1])],fill=(198,202,206,90))
        s.im.alpha_composite(lay)
        s.d.line([a0,a1],fill=ST,width=2)
        for i in range(int(ln)+1):
            f=i/max(1,int(ln))
            s.d.line([(a0[0]+(a1[0]-a0[0])*f,a0[1]+(a1[1]-a0[1])*f),
                      (b0[0]+(b1[0]-b0[0])*f,b0[1]+(b1[1]-b0[1])*f)],fill=ST_L,width=2)
    def shell(s,n,m,openings=()):
        """perimeter wall, two storeys, with gaps where a corridor joins"""
        for i in range(n):
            if ('n',i) not in openings: s.prism(i,-0.2,1,0.2,2,WT,WL,WR,courses=4)
        for j in range(m):
            if ('w',j) not in openings: s.prism(-0.2,j,0.2,1,2,WT,WL,WR,courses=4)

def facility(name, n=BLOCK, m=BLOCK, build=None, pad=(70,120,70,40)):
    w = (n+m)*DX + pad[0]+pad[2]
    h = (n+m)*DY + 2*DZ + pad[1]+pad[3]
    s = Scene(int(w),int(h), int(m*DX+pad[0]), int(pad[1]))
    for q in range(n+m-1):
        for x in range(n):
            y=q-x
            if 0<=y<m: build['floor'](s,x,y)
    s.shell(n,m, build.get('openings',()))
    build['props'](s)
    return s.im

# ------------------------------------------------------------ the four
def lift_floor(s,x,y):
    mid = 3<=x<=6 and 3<=y<=6
    s.floor(x,y, sh(CON,.78) if mid else CON, 'hz' if (x in (0,9) and 4<=y<=5) else None)
def lift_props(s):
    s.contact(3,3,4,4)
    s.prism(3,3,4,4,.35,ST,ST_L,ST_R,courses=1)
    for k in range(4):
        s.d.polygon([s.P(3+k,2.9,.35),s.P(3.5+k,2.9,.35),s.P(3.5+k,3.1,.35),s.P(3+k,3.1,.35)],
                    fill=AMB if k%2==0 else DARK)
    s.prism(4.2,4.2,1.6,1.6,.55,sh(ST,1.1),ST_L,ST_R,z=.35)
    for cx,cy in ((2.4,2.4),(6.6,2.4),(2.4,6.6),(6.6,6.6)):
        s.prism(cx,cy,.4,.4,2,ST,ST_L,ST_R)

def barr_floor(s,x,y): s.floor(x,y, (168,166,160) if 4<=x<=5 else CON)
def barr_props(s):
    for row,by in ((0,0.6),(1,7.4)):
        for i in range(3):
            bx=0.9+i*2.8
            s.contact(bx,by,1.1,2.4)
            s.prism(bx,by,1.1,2.4,.28,ST,ST_L,ST_R)                      # the frame, low
            s.prism(bx+.05,by+.05,1.0,0.7,.40,(214,214,208),(178,178,172),(148,148,144))
            s.prism(bx+.05,by+.75,1.0,1.6,.36,OL,OL_L,OL_R)              # olive blanket
            s.d.line([s.P(bx,by,.28),s.P(bx,by+2.4,.28)],fill=sh(ST_L,.8))
    for i in range(2):
        s.prism(8.4,1.0+i*2.2,.5,1.4,1.7,ST,ST_L,ST_R,courses=2)

def arm_floor(s,x,y): s.floor(x,y,CON,'x' if y==4 else None)
def arm_props(s):
    for i in range(3):
        s.contact(0.6+i*0.1,0.5,2.6,0.9)
    s.prism(0.4,0.4,8.6,0.9,1.9,ST,ST_L,ST_R,courses=3)
    for k in range(16):
        s.d.line([s.P(0.6+k*.52,0.4,.5),s.P(0.6+k*.52,0.4,1.7)],fill=sh(OL,1.1),width=2)
    for side_x in (0.4, 8.2):
        s.prism(side_x,2.0,0.9,6.0,1.8,ST,ST_L,ST_R,courses=3)
    for (cx,cy) in ((3.0,3.0),(5.2,3.0),(3.0,5.6),(5.2,5.6)):
        s.crate(cx,cy); s.crate(cx,cy,z=.9)
    s.fence(2.4,2.4,'x',4.6)

def hang_floor(s,x,y):
    s.floor(x,y, CON if y>6 else sh(CON,.92))
def hang_props(s):
    s.prism(0,0,20,0.25,2,WT,WL,WR,courses=4)
    for k in range(20):
        s.d.line([s.P(k+.5,0.25,0),s.P(k+.5,0.25,2)],fill=sh(ST_L,.95),width=2)
    for x in (4.5,14.5):
        s.contact(x,16.5,1.2,1.2)
        s.prism(x,16.5,1.2,1.2,.5,ST,ST_L,ST_R)
    for k in range(10):
        s.d.polygon([s.P(k*2,19.7),s.P(k*2+1,19.7),s.P(k*2+1,20),s.P(k*2,20)],
                    fill=AMB if k%2==0 else DARK)
    s.d.line([s.P(10,2),s.P(10,18)],fill=AMB,width=3)
    s.d.line([s.P(6,10),s.P(14,10)],fill=AMB,width=3)

F = {
 'ACCESS LIFT':   facility('lift', build={'floor':lift_floor,'props':lift_props}),
 'BARRACKS':      facility('barr', build={'floor':barr_floor,'props':barr_props}),
 'ARMOURY':       facility('arm',  build={'floor':arm_floor, 'props':arm_props}),
 'HANGAR':        facility('hang', 20,20, build={'floor':hang_floor,'props':hang_props}),
}
for k,v in F.items(): print(k, v.size)
import pickle; pickle.dump({k:v.tobytes() for k,v in F.items()}, open('/dev/null','wb'))
for k,v in F.items(): v.save('/tmp/fac_%s.png'%k.split()[0].lower())
