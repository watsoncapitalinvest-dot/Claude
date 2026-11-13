# Rough Phase-1 dogfight check (STORY, 13 Nov). Not the engine: one deck, no pathfinding, no reaction fire.
# Re-run after changing any number in DOGFIGHT_DESIGN_v1.md section 3:  python3 dogfight_sim.py
import random, math, sys
A = {  # tu hp armor agility sight gun(dmg,range,bursts) role  -- the table in claude/DOGFIGHT_DESIGN_v1.md section 3 (13 Nov 15:50)
 'Skystriker': (60,100,2,15,(30,8,12),'fighter'),
 'Rattler':    (48,110,4,8,(26,7,12),'strike'),
 'Firebat':    (56,90,2,16,(26,8,12),'fighter'),
 'NightRaven': (64,70,1,20,None,'cargo'),
 'Vulture':    (35,140,3,0,(10,4,12),'cargo'),
 'Smuggler':   (40,80,1,4,None,'cargo'),
 'Tomahawk':   (36,120,3,5,None,'cargo'),
}
def mk(t,side,x,y,h,fire=55,react=40):
    tu,hp,ar,ag,gun,role=A[t]
    return dict(t=t,side=side,x=x,y=y,h=h,tu=tu,hp=hp,max=hp,ar=ar,ag=ag,gun=gun,role=role,bursts=gun[2] if gun else 0,fire=fire,react=react,out=False,esc=False)
def ang(a): return (a+180)%360-180
def bearing(a,b): return math.degrees(math.atan2(b['y']-a['y'],b['x']-a['x']))
def hitch(s,t,sx,sy,sh):
    d=math.hypot(t['x']-sx,t['y']-sy)
    if d>s['gun'][1] or d<0.5: return 0
    b=math.degrees(math.atan2(t['y']-sy,t['x']-sx))
    if abs(ang(b-sh))>45: return 0
    p=60+(s['fire']-50)/2-3*max(0,d-3)-t['ag']-t['react']/5
    rel=abs(ang(math.degrees(math.atan2(sy-t['y'],sx-t['x']))-t['h']))  # where shooter is, seen from target nose
    if rel>135: p+=20
    elif rel<45: p-=10
    return max(5,min(95,p))/100
def turn(side,U,edge_x):
    for s in [u for u in U if u['side']==side and not u['out']]:
        if s['role']=='cargo' or (s['hp']<0.25*s['max']) or (s['role']=='strike' and s['hp']<0.4*s['max']):
            step=s['tu']/4; s['x']+=step*(1 if edge_x>s['x'] else -1); s['h']=0 if edge_x>s['x'] else 180
            if (edge_x>=40 and s['x']>=39) or (edge_x<=0 and s['x']<=1): s['out']=True; s['esc']=True
            continue
        foes=[u for u in U if u['side']!=side and not u['out']]
        if not foes: return
        # pick target: cargo first for Joe, else nearest
        foes.sort(key=lambda f:(0 if (f['role']=='cargo' and side=='J') else 1, math.hypot(f['x']-s['x'],f['y']-s['y'])))
        t=foes[0]
        best=None
        for keep in (12,24,36):
            R=(s['tu']-keep)/4
            if R<0: continue
            for da in range(0,360,30):
                for dist in (2,3,4,5,6,8):
                    px=t['x']+dist*math.cos(math.radians(da)); py=t['y']+dist*math.sin(math.radians(da))
                    mv=math.hypot(px-s['x'],py-s['y'])
                    h=math.degrees(math.atan2(t['y']-py,t['x']-px))
                    turns=abs(ang(h-s['h']))/45*2
                    if mv*4+turns>s['tu']-keep: continue
                    p=hitch(s,t,px,py,h); n=min(keep//12,s['bursts'])
                    val=1-(1-p)**n
                    if best is None or val>best[0]: best=(val,px,py,h,n,p)
        if best is None:  # close in
            b=bearing(s,t); step=s['tu']/4; s['x']+=step*math.cos(math.radians(b)); s['y']+=step*math.sin(math.radians(b)); s['h']=b; continue
        _,s['x'],s['y'],s['h'],n,p=best
        for _ in range(n):
            if p<=0.30: break
            s['bursts']-=1
            if random.random()<p:
                dmg=max(1,round(s['gun'][0]*random.uniform(.75,1.25))-t['ar']); t['hp']-=dmg
                if t['hp']<=0: t['out']=True; break
def fight(J,C,cargo_edge=40,rounds=12,joe_edge=0):
    U=J+C
    for r in range(rounds):
        turn('J',U,joe_edge); turn('C',U,cargo_edge)
        if all(u['out'] for u in C) or all(u['out'] for u in J): break
    return U
def run(name,mkJ,mkC,N=2000,edge=40,jedge=0):
    res={'cobra_down':0,'cargo_esc':0,'joe_down':0,'joe_dmg':0}
    for _ in range(N):
        J=mkJ(); C=mkC(); fight(J,C,edge,joe_edge=jedge)
        res['cobra_down']+=sum(1 for c in C if c['out'] and not c['esc'] and c['hp']<=0)/len(C)
        res['cargo_esc']+=any(c['esc'] and c['role']=='cargo' for c in C+J)
        res['joe_down']+=sum(1 for j in J if j['hp']<=0)/len(J)
        res['joe_dmg']+=sum(1-max(0,j['hp'])/j['max'] for j in J)/len(J)
    print('%-44s Cobra planes downed %3.0f%% | cargo escaped %3.0f%% | Joe planes lost %3.0f%% | Joe avg damage %3.0f%%'%(name,100*res['cobra_down']/N,100*res['cargo_esc']/N,100*res['joe_down']/N,100*res['joe_dmg']/N))
random.seed(7)
# Crossing starts (design section 2): cargo starts 4 tiles in from the west edge heading east; Joes enter from the south.
run('Skystriker (rookie) v Rattler',lambda:[mk('Skystriker','J',2,20,0)],lambda:[mk('Rattler','C',27,20,180)])
run('Skystriker (Ace) v Rattler',lambda:[mk('Skystriker','J',2,20,0,75,60)],lambda:[mk('Rattler','C',27,20,180)])
run('Skystriker v Firebat',lambda:[mk('Skystriker','J',2,20,0)],lambda:[mk('Firebat','C',27,20,180)])
run('Skystriker v cartel smuggler',lambda:[mk('Skystriker','J',20,2,90)],lambda:[mk('Smuggler','C',4,20,0)])
run('Skystriker v Night Raven',lambda:[mk('Skystriker','J',20,2,90)],lambda:[mk('NightRaven','C',4,20,0)])
run('Skystriker v Vulture alone',lambda:[mk('Skystriker','J',20,2,90)],lambda:[mk('Vulture','C',4,20,0)])
run('2 Skystrikers v Vulture + 1 Rattler',lambda:[mk('Skystriker','J',18,2,90),mk('Skystriker','J',22,2,90)],lambda:[mk('Vulture','C',4,20,0),mk('Rattler','C',6,22,0)])
run('1 Skystriker v Vulture + 2 Rattlers',lambda:[mk('Skystriker','J',20,2,90)],lambda:[mk('Vulture','C',4,20,0),mk('Rattler','C',6,18,0),mk('Rattler','C',6,22,0)])
run('Rattler v Tomahawk, no escort',lambda:[mk('Tomahawk','J',4,20,0)],lambda:[mk('Rattler','C',20,2,90)],jedge=40)
