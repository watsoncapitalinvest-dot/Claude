from PIL import Image, ImageDraw, ImageFilter
import random, math
random.seed(23)

SW,SH = 32,40
DX,DY,DZ = SW//2, SW//4, (SH+SW//4)//2      # 16, 8, 24  - derived, see FACILITIES_NOTES
N = 10                                       # one base square = one 10x10 XBASE block

def sh(c,f): return tuple(max(0,min(255,int(v*f))) for v in c)
CON=(152,152,150); WT=(190,190,187); WL=(146,146,144); WR=(104,104,103)
ST=(162,166,170);  ST_L=(121,125,131); ST_R=(94,98,104)
OL=(130,144,110);  OL_L=(102,115,86);  OL_R=(80,92,66)
WHT=(216,216,210); WHT_L=(182,182,177); WHT_R=(150,150,146)
AMB=(208,172,54);  DARK=(30,30,32); RED=(170,60,54)
GLS=(126,176,188); SCR=(86,142,160)

class Room:
    def __init__(s,w,h,ox,oy):
        s.im=Image.new('RGBA',(w,h),(0,0,0,0)); s.d=ImageDraw.Draw(s.im)
        s.ox,s.oy=ox,oy; s.q=[]
    def P(s,x,y,z=0): return (s.ox+(x-y)*DX, s.oy+(x+y)*DY - z*DZ)
    def add(s,depth,fn): s.q.append((depth,len(s.q),fn))
    def run(s):
        for _,_,fn in sorted(s.q, key=lambda t:(t[0],t[1])): fn()
    # ---- surfaces
    def grain(s,pts,base,g=7,lines=None,lc=None):
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
            for a,b in lines: pd.line([(a[0]-x0,a[1]-y0),(b[0]-x0,b[1]-y0)],fill=lc or sh(base,.84))
        m=Image.new('L',(w,h),0)
        ImageDraw.Draw(m).polygon([(p[0]-x0,p[1]-y0) for p in pts],fill=255)
        s.im.paste(pa,(x0,y0),m)
    def floor(s,x,y,col=CON,lane=None,ao=0.0):
        c = sh(col, 1.0-ao)
        p=[s.P(x,y),s.P(x+1,y),s.P(x+1,y+1),s.P(x,y+1)]
        s.grain(p,c,6)
        s.d.line([p[0],p[1]],fill=sh(c,.91)); s.d.line([p[0],p[3]],fill=sh(c,.91))
        if lane=='x': s.d.line([s.P(x,y+.5),s.P(x+1,y+.5)],fill=AMB,width=2)
        if lane=='y': s.d.line([s.P(x+.5,y),s.P(x+.5,y+1)],fill=AMB,width=2)
    def prism(s,x,y,w,l,hz,top,left,right,z=0,courses=0,lightfall=True):
        t =[s.P(x,y,z+hz),s.P(x+w,y,z+hz),s.P(x+w,y+l,z+hz),s.P(x,y+l,z+hz)]
        lf=[s.P(x,y+l,z+hz),s.P(x+w,y+l,z+hz),s.P(x+w,y+l,z),s.P(x,y+l,z)]
        rf=[s.P(x+w,y,z+hz),s.P(x+w,y+l,z+hz),s.P(x+w,y+l,z),s.P(x+w,y,z)]
        ll=[];rl=[]
        for k in range(1,max(1,courses)):
            f=k/courses*hz*DZ
            ll.append(((lf[0][0],lf[0][1]+f),(lf[1][0],lf[1][1]+f)))
            rl.append(((rf[0][0],rf[0][1]+f),(rf[1][0],rf[1][1]+f)))
        s.grain(rf,right,6,rl); s.grain(lf,left,6,ll); s.grain(t,top,5)
        if lightfall and hz>=1:                    # light falls off toward the floor
            for face,base in ((lf,left),(rf,right)):
                lay=Image.new('RGBA',s.im.size,(0,0,0,0)); ld=ImageDraw.Draw(lay)
                ld.polygon(face,fill=(0,0,0,46))
                m=Image.new('L',s.im.size,0)
                ImageDraw.Draw(m).polygon([(face[2][0],face[2][1]),(face[3][0],face[3][1]),
                                           (face[3][0],face[3][1]-hz*DZ*0.45),(face[2][0],face[2][1]-hz*DZ*0.45)],fill=255)
                s.im.alpha_composite(Image.composite(lay,Image.new('RGBA',s.im.size,(0,0,0,0)),m))
        s.d.line(t+[t[0]],fill=sh(top,1.11))
    def contact(s,x,y,w,l,a=85):
        c=s.P(x+w/2,y+l/2)
        g=Image.new('RGBA',(int(w*DX*2.6)+10,int(l*DY*2.8)+10),(0,0,0,0))
        ImageDraw.Draw(g).ellipse([0,0,g.width-1,g.height-1],fill=(0,0,0,a))
        g=g.filter(ImageFilter.GaussianBlur(2.2))
        s.im.alpha_composite(g,(int(c[0]-g.width/2),int(c[1]-g.height/2+2)))
    # ---- props
    def bunk(s,x,y,rot=0):
        s.contact(x,y,1.1,2.3)
        s.prism(x,y,1.1,2.3,.26,ST,ST_L,ST_R,lightfall=False)
        s.prism(x+.05,y+.05,1.0,.65,.40,WHT,WHT_L,WHT_R,lightfall=False)
        s.prism(x+.05,y+.72,1.0,1.5,.36,OL,OL_L,OL_R,lightfall=False)
        for px_ in (x,x+1.05):
            s.d.line([s.P(px_,y,.26),s.P(px_,y,.95)],fill=ST_L,width=2)
            s.d.line([s.P(px_,y+2.3,.26),s.P(px_,y+2.3,.75)],fill=ST_R,width=2)
    def locker(s,x,y,n=1):
        s.contact(x,y,.55*n,.7)
        s.prism(x,y,.55*n,.7,1.7,ST,ST_L,ST_R,courses=2)
        for k in range(n):
            c=s.P(x+.55*k+.27,y+.7,.95)
            s.d.rectangle([c[0]-2,c[1]-3,c[0]+2,c[1]+1],fill=DARK)
    def foot(s,x,y):
        s.contact(x,y,.8,.5,70); s.prism(x,y,.8,.5,.4,OL,OL_L,OL_R,lightfall=False)
    def bench(s,x,y,w=3.0,l=.9,white=True):
        s.contact(x,y,w,l)
        top,lt,rt = (WHT,WHT_L,WHT_R) if white else (ST,ST_L,ST_R)
        s.prism(x,y,w,l,.9,top,lt,rt,courses=1)
        s.d.line([s.P(x,y,.9),s.P(x+w,y,.9)],fill=sh(top,1.14))
    def monitor(s,x,y,z=.9,w=.8):
        s.prism(x,y,w,.10,.14,(60,64,68),(46,50,54),(38,42,46),z=z,lightfall=False)   # stand
        s.prism(x,y,w,.10,.46,(54,58,62),(42,46,50),(34,38,42),z=z+.14,lightfall=False)
        # the lit screen is the +y face of that box, not a floating rectangle
        f=[s.P(x+.04,y+.10,z+.56),s.P(x+w-.04,y+.10,z+.56),
           s.P(x+w-.04,y+.10,z+.20),s.P(x+.04,y+.10,z+.20)]
        s.d.polygon(f,fill=SCR)
        for k in range(3):
            t=(k+1)/4.0
            a=(f[0][0]+(f[3][0]-f[0][0])*t, f[0][1]+(f[3][1]-f[0][1])*t)
            b=(f[1][0]+(f[2][0]-f[1][0])*t, f[1][1]+(f[2][1]-f[1][1])*t)
            s.d.line([a,(a[0]+(b[0]-a[0])*.6,a[1]+(b[1]-a[1])*.6)],fill=(176,218,226))
    def tank(s,x,y):
        s.contact(x,y,.8,.8)
        s.prism(x,y,.8,.8,.3,ST,ST_L,ST_R,lightfall=False)
        lay=Image.new('RGBA',s.im.size,(0,0,0,0)); ld=ImageDraw.Draw(lay)
        a=[s.P(x,y+.8,.3+1.3),s.P(x+.8,y+.8,.3+1.3),s.P(x+.8,y+.8,.3),s.P(x,y+.8,.3)]
        b=[s.P(x+.8,y,.3+1.3),s.P(x+.8,y+.8,.3+1.3),s.P(x+.8,y+.8,.3),s.P(x+.8,y,.3)]
        ld.polygon(a,fill=GLS+(120,)); ld.polygon(b,fill=sh(GLS,.8)+(120,))
        s.im.alpha_composite(lay)
        s.prism(x,y,.8,.8,.18,ST,ST_L,ST_R,z=1.6,lightfall=False)
    def chair(s,x,y):
        s.contact(x,y,.45,.45,60)
        s.prism(x,y,.45,.45,.45,ST_L,ST_R,ST_R,lightfall=False)
        s.prism(x,y+.35,.45,.1,.95,ST,ST_L,ST_R,lightfall=False)
    def table(s,x,y,w=1.8,l=1.0):
        s.contact(x,y,w,l); s.prism(x,y,w,l,.75,(150,134,104),(120,106,82),(98,86,66),lightfall=False)
    def figure(s,x,y):
        s.contact(x,y,.5,.5,70)
        s.prism(x+.1,y+.1,.3,.3,1.0,OL_L,OL_R,OL_R,lightfall=False)      # legs/torso
        s.prism(x+.08,y+.08,.34,.34,.5,OL,OL_L,OL_R,z=1.0,lightfall=False)
        c=s.P(x+.25,y+.25,1.5)
        s.d.ellipse([c[0]-4,c[1]-10,c[0]+4,c[1]-2],fill=(196,166,132))
    def pipes(s,x0,x1,z=1.5):                      # a run along the north wall face
        for k,dz in enumerate((0,.13,.26)):
            col=(ST_R,ST_L,sh(ST_R,.85))[k]
            s.prism(x0,0.0,x1-x0,0.07,.07,col,sh(col,.84),sh(col,.7),z=z+dz,lightfall=False)
    def shell(s,gapN=None,gapW=None,lightfall=True):
        for i in range(N):
            if gapN and gapN[0]<=i<gapN[1]: continue
            s.prism(i,-0.22,1,0.22,2,WT,WL,WR,courses=4,lightfall=lightfall)
        for j in range(N):
            if gapW and gapW[0]<=j<gapW[1]: continue
            s.prism(-0.22,j,0.22,1,2,WT,WL,WR,courses=4,lightfall=lightfall)
    def strip(s,x,w=2.0,z=1.72):                   # light fixed to the north wall face
        s.prism(x,0.0,w,0.09,.14,(240,240,220),(226,226,204),(198,198,178),z=z,lightfall=False)
    def wstrip(s,y,l=2.0,z=1.72):                  # the same on the west wall face
        s.prism(0.0,y,0.09,l,.14,(240,240,220),(226,226,204),(198,198,178),z=z,lightfall=False)

def build(kind):
    w=(2*N)*DX+150; h=(2*N)*DY+2*DZ+170
    r=Room(int(w),int(h),int(N*DX+70),80)
    light = (4.5,4.5) if kind=='lab' else (5,5)
    for q in range(2*N-1):
        for x in range(N):
            y=q-x
            if not (0<=y<N): continue
            dist=max(abs(x-light[0]),abs(y-light[1]))/float(N)
            ao=min(.12,max(0.0,(dist-0.18)*.34))
            base = (176,176,170) if kind=='lab' else CON
            lane = None if kind=='lab' else ('y' if x==5 else None)
            r.add(x+y-1, (lambda X,Y,B,L,A: (lambda: r.floor(X,Y,B,L,A)))(x,y,base,lane,ao))
    r.add(-100, lambda: r.shell(gapN=(4,6)))
    if kind=='lab':
        r.add(-99, lambda: r.strip(2.2,2.2))
        r.add(-99, lambda: r.strip(6.2,2.2))
        r.add(-98, lambda: r.pipes(0.4,N-0.4))
        for i,(bx,by) in enumerate([(0.6,1.0),(0.6,3.2),(0.6,5.4)]):
            r.add(bx+by, (lambda X,Y: (lambda: r.bench(X,Y,3.2,.9)))(bx,by))
            r.add(bx+by+.1, (lambda X,Y: (lambda: r.monitor(X+.4,Y+.1)))(bx,by))
            r.add(bx+by+.2, (lambda X,Y: (lambda: r.monitor(X+1.6,Y+.1,w=.7)))(bx,by))
        for (tx,ty) in ((6.4,1.2),(6.4,2.6),(6.4,4.0)):
            r.add(tx+ty, (lambda X,Y: (lambda: r.tank(X,Y)))(tx,ty))
        r.add(13, lambda: r.bench(5.6,6.6,3.4,1.0,white=False))
        r.add(13.3, lambda: r.chair(4.6,7.0))
        r.add(13.5, lambda: r.figure(4.2,5.6))
        r.add(15, lambda: r.locker(8.6,7.4,2))
    else:
        r.add(-99, lambda: r.strip(4.0,2.4))
        r.add(-99, lambda: r.wstrip(4.0,2.4))
        r.add(-98, lambda: r.pipes(0.4,N-0.4))
        for row,by in ((0,0.5),(1,7.2)):
            for i in range(3):
                bx=0.8+i*2.9
                r.add(bx+by, (lambda X,Y: (lambda: r.bunk(X,Y)))(bx,by))
                r.add(bx+by+.3, (lambda X,Y: (lambda: r.foot(X+.15,Y+2.4)))(bx,by))
        r.add(9, lambda: r.locker(8.5,1.0,3))
        r.add(12, lambda: r.table(3.9,4.2,2.2,1.2))
        r.add(12.4, lambda: r.chair(3.3,4.6))
        r.add(12.6, lambda: r.chair(6.2,4.6))
        r.add(12.8, lambda: r.figure(6.9,4.0))
    r.run()
    bb=r.im.getbbox()
    return r.im.crop(bb) if bb else r.im

for k in ('lab','barracks'):
    im=build(k); im.save('/tmp/room_%s.png'%k); print(k, im.size)
