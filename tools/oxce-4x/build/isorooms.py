from PIL import Image, ImageDraw, ImageFilter
import random
random.seed(23)

SW,SH = 32,40
DX,DY,DZ = SW//2, SW//4, (SH+SW//4)//2      # 16, 8, 24 - Camera::convertMapToScreen
N = 10                                       # one base square = one 10x10 XBASE block

CON=(150,150,148); WT=(190,190,187); WL=(143,143,141); WR=(100,100,99)
OL=(130,144,110);  OL_L=(102,115,86); OL_R=(80,92,66)
ST=(162,166,170);  ST_L=(120,124,130); ST_R=(93,97,103)
WHT=(212,214,210); WHT_L=(176,178,174); WHT_R=(144,146,143)
AMB=(208,172,54);  DARK=(30,30,32); RED=(170,60,54)
GLS=(120,168,182); GRN=(118,186,132)

def sh(c,f): return tuple(max(0,min(255,int(v*f))) for v in c)

class Room:
    def __init__(s,n=N,m=N,pad=(80,130,80,54)):
        s.n,s.m=n,m
        w=(n+m)*DX+pad[0]+pad[2]; h=(n+m)*DY+3*DZ+pad[1]+pad[3]
        s.im=Image.new('RGBA',(int(w),int(h)),(0,0,0,0)); s.d=ImageDraw.Draw(s.im)
        s.ox=int(m*DX+pad[0]); s.oy=int(pad[1])
    def P(s,x,y,z=0): return (s.ox+(x-y)*DX, s.oy+(x+y)*DY - z*DZ)
    def grain(s,pts,base,g=7,lines=None,lc=None):
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        x0,y0=int(min(xs))-1,int(min(ys))-1; x1,y1=int(max(xs))+2,int(max(ys))+2
        w,h=x1-x0,y1-y0
        if w<1 or h<1: return
        pa=Image.new('RGB',(w,h),base); px=pa.load()
        for yy in range(h):
            for xx in range(w):
                nn=random.randint(-g,g); r,gg,b=px[xx,yy]
                px[xx,yy]=(max(0,min(255,r+nn)),max(0,min(255,gg+nn)),max(0,min(255,b+nn)))
        if lines:
            pd=ImageDraw.Draw(pa)
            for a,b in lines: pd.line([(a[0]-x0,a[1]-y0),(b[0]-x0,b[1]-y0)],fill=lc or sh(base,.82))
        m=Image.new('L',(w,h),0)
        ImageDraw.Draw(m).polygon([(p[0]-x0,p[1]-y0) for p in pts],fill=255)
        s.im.paste(pa,(x0,y0),m)
    def tile(s,x,y,col=CON,mark=None):
        p=[s.P(x,y),s.P(x+1,y),s.P(x+1,y+1),s.P(x,y+1)]
        s.grain(p,col,6)
        s.d.line([p[0],p[1]],fill=sh(col,.9)); s.d.line([p[0],p[3]],fill=sh(col,.9))
        if mark=='x': s.d.line([s.P(x,y+.5),s.P(x+1,y+.5)],fill=AMB,width=2)
        if mark=='y': s.d.line([s.P(x+.5,y),s.P(x+.5,y+1)],fill=AMB,width=2)
    def lightpool(s,x,y,r=2.6,strength=46):
        c=s.P(x,y)
        g=Image.new('RGBA',(int(r*DX*2.6),int(r*DY*2.8)),(0,0,0,0))
        ImageDraw.Draw(g).ellipse([0,0,g.width-1,g.height-1],fill=(255,250,228,strength))
        g=g.filter(ImageFilter.GaussianBlur(9))
        s.im.alpha_composite(g,(int(c[0]-g.width/2),int(c[1]-g.height/2)))
    def contact(s,x,y,w,l,a=85):
        c=s.P(x+w/2,y+l/2)
        g=Image.new('RGBA',(int(w*DX*2.5)+10,int(l*DY*2.8)+10),(0,0,0,0))
        ImageDraw.Draw(g).ellipse([0,0,g.width-1,g.height-1],fill=(0,0,0,a))
        g=g.filter(ImageFilter.GaussianBlur(3))
        s.im.alpha_composite(g,(int(c[0]-g.width/2),int(c[1]-g.height/2+2)))
    def prism(s,x,y,w,l,h,top,left,right,z=0,courses=0,lc=None):
        t =[s.P(x,y,z+h),s.P(x+w,y,z+h),s.P(x+w,y+l,z+h),s.P(x,y+l,z+h)]
        lf=[s.P(x,y+l,z+h),s.P(x+w,y+l,z+h),s.P(x+w,y+l,z),s.P(x,y+l,z)]
        rf=[s.P(x+w,y,z+h),s.P(x+w,y+l,z+h),s.P(x+w,y+l,z),s.P(x+w,y,z)]
        ll=[];rl=[]
        for k in range(1,max(1,courses)):
            f=k/courses*h*DZ
            ll.append(((lf[0][0],lf[0][1]+f),(lf[1][0],lf[1][1]+f)))
            rl.append(((rf[0][0],rf[0][1]+f),(rf[1][0],rf[1][1]+f)))
        s.grain(rf,right,6,rl,lc); s.grain(lf,left,6,ll,lc); s.grain(t,top,5)
        s.d.line(t+[t[0]],fill=sh(top,1.1))
    def wall(s,x,y,axis,ln,h=2.0,t=0.2):
        if axis=='x': s.prism(x,y,ln,t,h,WT,WL,WR,courses=4)
        else:         s.prism(x,y,t,ln,h,WT,WL,WR,courses=4)
    def partition(s,x,y,axis,ln,h=1.25):
        s.wall(x,y,axis,ln,h,0.14)
    def pipe(s,x,y,axis,ln,z=1.72,col=(128,132,124)):
        a=s.P(x,y,z); b=s.P(x+ln,y,z) if axis=='x' else s.P(x,y+ln,z)
        s.d.line([a,b],fill=col,width=4); s.d.line([(a[0],a[1]-1),(b[0],b[1]-1)],fill=sh(col,1.2),width=1)
        for k in range(int(ln)+1):
            f=k/max(1,int(ln))
            p=(a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f)
            s.d.rectangle([p[0]-2,p[1]-3,p[0]+2,p[1]+3],fill=sh(col,.78))
    def strip(s,x,y,axis,ln,z=1.86):
        a=s.P(x,y,z); b=s.P(x+ln,y,z) if axis=='x' else s.P(x,y+ln,z)
        s.d.line([a,b],fill=(246,242,214),width=3)
        g=Image.new('RGBA',s.im.size,(0,0,0,0))
        ImageDraw.Draw(g).line([a,b],fill=(255,248,210,70),width=11)
        s.im.alpha_composite(g.filter(ImageFilter.GaussianBlur(5)))
    def panel(s,x,y,wall_axis,w=1.2,h=.5,z=1.25,col=(58,66,70),lit=GLS):
        if wall_axis=='n': a=s.P(x,0.2,z); b=s.P(x+w,0.2,z)
        else:              a=s.P(0.2,x,z); b=s.P(0.2,x+w,z)
        hh=h*DZ
        s.d.polygon([a,b,(b[0],b[1]+hh),(a[0],a[1]+hh)],fill=col)
        s.d.polygon([(a[0]+2,a[1]+3),(b[0]-2,b[1]+3),(b[0]-2,b[1]+hh-3),(a[0]+2,a[1]+hh-3)],fill=lit)
        for k in range(3):
            s.d.line([(a[0]+4,a[1]+6+k*4),(b[0]-5,b[1]+6+k*4)],fill=sh(lit,1.3))
    def crate(s,x,y,z=0,sz=.85):
        if z==0: s.contact(x,y,sz,sz)
        s.prism(x,y,sz,sz,.85,OL,OL_L,OL_R,z=z,courses=3)
        c=s.P(x+sz/2,y+sz,z+.46); s.d.rectangle([c[0]-4,c[1]-2,c[0]+4,c[1]+2],fill=sh(AMB,.85))
    def locker(s,x,y,n=1):
        s.contact(x,y,.5*n,.72)
        s.prism(x,y,.5*n,.72,1.15,ST,ST_L,ST_R)
        for k in range(n):
            c=s.P(x+.5*k+.25,y+.72,.58)
            s.d.line([s.P(x+.5*k,y+.72,0),s.P(x+.5*k,y+.72,1.15)],fill=sh(ST_R,.8))
            s.d.rectangle([c[0]-2,c[1]-3,c[0]+2,c[1]+3],fill=DARK)
    def bunk(s,x,y):
        s.contact(x,y,1.05,2.3)
        s.prism(x,y,1.05,2.3,.26,ST,ST_L,ST_R)
        s.prism(x+.05,y+.05,.95,.65,.40,WHT,WHT_L,WHT_R)
        s.prism(x+.05,y+.72,.95,1.5,.36,OL,OL_L,OL_R)
    def bench(s,x,y,w,l,items=3):
        s.contact(x,y,w,l)
        s.prism(x,y,w,l,.82,WHT,WHT_L,WHT_R)
        for k in range(items):
            ix=x+.25+k*(w-.5)/max(1,items)
            s.prism(ix,y+l*.3,.34,.34,.34,ST,ST_L,ST_R,z=.82)
            c=s.P(ix+.17,y+l*.3+.34,.98); s.d.rectangle([c[0]-3,c[1]-5,c[0]+3,c[1]-1],fill=GLS)
    def tank(s,x,y,col=GRN):
        s.contact(x,y,.7,.7)
        s.prism(x,y,.7,.7,.2,ST,ST_L,ST_R)
        s.prism(x+.08,y+.08,.54,.54,.78,sh(col,1.15),sh(col,.85),sh(col,.68),z=.2)
        g=Image.new('RGBA',s.im.size,(0,0,0,0))
        cc=s.P(x+.35,y+.35,.62)
        ImageDraw.Draw(g).ellipse([cc[0]-16,cc[1]-20,cc[0]+16,cc[1]+12],fill=col+(52,))
        s.im.alpha_composite(g.filter(ImageFilter.GaussianBlur(7)))
        s.prism(x+.05,y+.05,.6,.6,.12,ST,ST_L,ST_R,z=.98)
    def figure(s,x,y,body=OL,head=(206,170,138)):
        s.contact(x,y,.42,.42,70)
        s.prism(x+.08,y+.08,.26,.26,.56,sh(body,.9),sh(body,.72),sh(body,.6))
        s.prism(x+.06,y+.06,.30,.30,.44,body,sh(body,.8),sh(body,.66),z=.56)
        s.prism(x+.12,y+.12,.18,.18,.22,head,sh(head,.82),sh(head,.7),z=1.0)
    def fence(s,x,y,axis,ln,h=1.6):
        a0=s.P(x,y,h); a1=s.P(x+ln,y,h) if axis=='x' else s.P(x,y+ln,h)
        b0=s.P(x,y,0); b1=s.P(x+ln,y,0) if axis=='x' else s.P(x,y+ln,0)
        lay=Image.new('RGBA',s.im.size,(0,0,0,0)); ld=ImageDraw.Draw(lay)
        steps=int(ln*DX*2/5)
        for k in range(steps+1):
            f=k/steps
            p0=(a0[0]+(a1[0]-a0[0])*f,a0[1]+(a1[1]-a0[1])*f)
            p1=(b0[0]+(b1[0]-b0[0])*f,b0[1]+(b1[1]-b0[1])*f)
            ld.line([p0,(p1[0]+6,p1[1])],fill=(200,204,208,88))
            ld.line([p0,(p1[0]-6,p1[1])],fill=(200,204,208,88))
        s.im.alpha_composite(lay)
        s.d.line([a0,a1],fill=ST,width=2)
        for i in range(int(ln)+1):
            f=i/max(1,int(ln))
            s.d.line([(a0[0]+(a1[0]-a0[0])*f,a0[1]+(a1[1]-a0[1])*f),
                      (b0[0]+(b1[0]-b0[0])*f,b0[1]+(b1[1]-b0[1])*f)],fill=ST_L,width=2)
    def trim(s):
        bb=s.im.getbbox(); return s.im.crop(bb) if bb else s.im

# ============================================================ LABORATORY
def lab():
    r=Room()
    CLEAN=(176,178,174)
    for q in range(N+N-1):
        for x in range(N):
            y=q-x
            if not (0<=y<N): continue
            clean = x<6
            r.tile(x,y, CLEAN if clean else CON, 'y' if x==6 else None)
    for cx,cy in ((2.5,2.5),(2.5,7.0),(8.0,4.5)): r.lightpool(cx,cy,2.9,52)
    r.wall(0,-0.2,'x',N); r.wall(-0.2,0,'y',N)
    r.partition(6.0,0,'y',4.2)                      # clean room / store divide
    r.partition(6.0,6.4,'y',3.6)
    r.pipe(0.2,0.2,'x',9.4,1.80); r.pipe(0.2,0.2,'x',9.4,1.62,(104,110,118))
    r.strip(1.0,1.6,'x',4.0); r.strip(1.0,6.6,'x',4.0); r.strip(7.0,2.0,'y',5.0)
    r.panel(1.2,0,'n',1.6,.55); r.panel(3.6,0,'n',1.6,.55)
    r.panel(2.0,0,'w',1.4,.5,col=(56,62,66),lit=(126,176,150))
    # clean side: benches and tanks
    r.bench(0.6,1.6,3.6,1.1,items=4)
    r.bench(0.6,5.2,3.6,1.1,items=3)
    r.tank(4.6,2.0); r.tank(4.6,3.2,(132,170,196)); r.tank(4.6,6.0)
    r.figure(3.2,3.4); r.figure(1.4,7.0,(196,198,192))
    # store side: caged racking
    r.fence(7.0,1.2,'y',3.2); r.fence(7.0,6.6,'y',2.8)
    for i in range(3):
        r.crate(7.6,1.6+i*1.0); r.crate(7.6,1.6+i*1.0,z=.85)
    r.locker(8.6,6.8,2)
    return r.trim()

# =============================================================== BARRACKS
def barracks():
    r=Room()
    for q in range(N+N-1):
        for x in range(N):
            y=q-x
            if not (0<=y<N): continue
            aisle = 4<=x<=5
            r.tile(x,y,(166,164,158) if aisle else CON, 'y' if x==4 else None)
    for cy in (1.8,5.0,8.2): r.lightpool(4.8,cy,2.8,46)
    r.wall(0,-0.2,'x',N); r.wall(-0.2,0,'y',N)
    r.partition(0,4.9,'x',3.6,1.1)                   # a low divider between squads
    r.pipe(0.2,0.2,'x',9.4,1.84)
    r.strip(4.4,1.0,'y',3.0); r.strip(4.4,6.0,'y',3.0)
    r.panel(6.6,0,'n',1.8,.55,col=(56,60,64),lit=(132,164,186))
    for by in (0.5,3.1,6.6):                          # bunks, left rank
        for i,bx in enumerate((0.5,2.0)):
            r.bunk(bx,by)
    for by in (0.5,3.1,6.6):                          # bunks, right rank
        for i,bx in enumerate((6.4,7.9)):
            r.bunk(bx,by)
    r.locker(3.3,0.6,2); r.locker(3.3,3.2,2); r.locker(3.3,6.7,2)
    r.contact(4.5,4.2,1.6,1.0)
    r.prism(4.5,4.2,1.6,1.0,.72,(150,138,114),(122,112,92),(98,90,74))   # mess table
    r.prism(4.7,5.3,.5,.5,.42,ST,ST_L,ST_R); r.prism(5.5,3.6,.5,.5,.42,ST,ST_L,ST_R)
    r.figure(5.1,5.9); r.figure(6.0,2.0,(188,190,184))
    for bx,by in ((1.3,2.5),(7.2,5.6)): r.crate(bx,by,sz=.6)
    return r.trim()

if __name__=='__main__':
    lab().save('/tmp/room_lab.png')
    barracks().save('/tmp/room_barracks.png')
    print('rendered lab + barracks')
