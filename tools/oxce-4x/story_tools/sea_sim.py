# Rough sea-battle number check (STORY, 13 Nov). Numbers = claude/SEA_BATTLES_DESIGN_v1.md section 4 (tuned 17:55). A guide, not the engine.
# Re-run after changing a number there:  python3 sea_sim.py
import random, math, sys
# kind: tu hp armor agility gun(dmg,range,bursts) aa(dmg,range,bursts) torps depth big level role
U = {
 'Skystriker': dict(tu=60,hp=100,ar=2,ag=15,gun=(30,8,12),aa=None,torp=0,dc=0,big=False,lvl='air',role='fighter'),
 'Devilfish':  dict(tu=56,hp=100,ar=3,ag=14,gun=(24,7,12),aa=None,torp=0,dc=4,big=False,lvl='surf',role='fighter'),
 'SHARC':      dict(tu=50,hp=80, ar=2,ag=16,gun=(20,6,10),aa=None,torp=2,dc=0,big=False,lvl='surf',role='fighter'),
 'CobraShip':  dict(tu=30,hp=300,ar=6,ag=0, gun=(22,7,14),aa=(18,8,14),torp=0,dc=0,big=True,lvl='surf',role='cargo'),
 'Moray':      dict(tu=52,hp=100,ar=3,ag=10,gun=(22,7,12),aa=None,torp=2,dc=0,big=False,lvl='surf',role='fighter'),
 'Moccasin':   dict(tu=44,hp=100,ar=3,ag=8, gun=(20,6,12),aa=None,torp=0,dc=0,big=False,lvl='surf',role='fighter'),
 'SeaSled':    dict(tu=50,hp=40, ar=0,ag=18,gun=None,     aa=None,torp=1,dc=0,big=False,lvl='under',role='fighter'),
}
def mk(k,side,x,y,h,fire=55,react=40,**ov):
    d=dict(U[k]); d.update(ov); d.update(t=k,side=side,x=x,y=y,h=h,fire=fire,react=react,max=d['hp'],out=False,esc=False,dis=False,sunk=False,
        bursts=d['gun'][2] if d['gun'] else 0, aab=d['aa'][2] if d['aa'] else 0, eng=0, guns=0)
    return d
def ang(a): return (a+180)%360-180
def aspect(s,t):  # where the shooter sits relative to the target's nose
    rel=abs(ang(math.degrees(math.atan2(s['y']-t['y'],s['x']-t['x']))-t['h']))
    return 'rear' if rel>135 else ('front' if rel<45 else 'side')
def chance(s,t,dist,sh_h):
    b=math.degrees(math.atan2(t['y']-s['y'],t['x']-s['x']))
    if abs(ang(b-sh_h))>45: return 0
    p=60+(s['fire']-50)/2-3*max(0,dist-3)-t['ag']-t['react']/5
    a=aspect(s,t); p+= 20 if a=='rear' else (-10 if a=='front' else 0)
    if s['lvl']!=t['lvl']: p-=15
    return max(5,min(95,p))/100
SYS={'rear':(0.6,0.1),'side':(0.2,0.3),'front':(0.1,0.3)}   # (engines, guns) share of hits; rest hull
def hit(s,t,dmg,sysroll=True):
    t['hp']-=max(1,round(dmg*random.uniform(.75,1.25))-t['ar'])
    if t['hp']<=0: t['out']=True; t['sunk']=True; return
    if sysroll and t['big'] or (sysroll and t['lvl']=='surf'):
        e,g=SYS[aspect(s,t)]; r=random.random()
        need=4 if t['big'] else 3
        if r<e:
            t['eng']+=1
            if t['eng']>=need and not t['dis']: t['dis']=True
        elif r<e+g: t['guns']+=1
def act(s,U_,mode):
    foes=[u for u in U_ if u['side']!=s['side'] and not u['out']]
    if not foes: return
    if s['role']=='cargo':
        if not s['dis']:
            s['x']+=s['tu']/4; s['h']=0
            if s['x']>=39: s['out']=True; s['esc']=True
        # AA / deck gun shots on its own turn
        for f in foes:
            d=math.hypot(f['x']-s['x'],f['y']-s['y'])
            if f['lvl']=='air' and s['aa'] and s['aab']>0 and d<=s['aa'][1] and s['guns']<3:
                s['aab']-=1
                if random.random()<max(.05,(55-f['ag']-f['react']/5)/100): f['hp']-=max(1,s['aa'][0]-f['ar']); f['out']=f['hp']<=0
            if f['lvl']=='surf' and s['gun'] and s['bursts']>0 and d<=s['gun'][1] and s['guns']<3:
                s['bursts']-=1
                if random.random()<max(.05,(55-f['ag']-f['react']/5-3*max(0,d-3))/100): f['hp']-=max(1,s['gun'][0]-f['ar']); f['out']=f['hp']<=0
        return
    t=min(foes,key=lambda f:(f['dis'] and mode=='disable', math.hypot(f['x']-s['x'],f['y']-s['y'])))
    if t['lvl']=='under' and s['lvl']=='surf':
        # depth charges: move over it, drop
        d=math.hypot(t['x']-s['x'],t['y']-s['y'])
        if d<=s['tu']/4-2 and s['dc']>0:
            s['x'],s['y']=t['x'],t['y']; s['dc']-=1; hit(s,t,35,False)
        else:
            b=math.atan2(t['y']-s['y'],t['x']-s['x']); s['x']+=s['tu']/4*math.cos(b); s['y']+=s['tu']/4*math.sin(b)
        return
    best=None
    for keep in (12,24,36):
        R=(s['tu']-keep)/4
        for da in range(0,360,30):
            if mode=='disable' and t['big']:
                # prefer the stern for engine hits
                pass
            for dist in (2,3,4,5,6,8):
                px=t['x']+dist*math.cos(math.radians(da)); py=t['y']+dist*math.sin(math.radians(da))
                h=math.degrees(math.atan2(t['y']-py,t['x']-px))
                if math.hypot(px-s['x'],py-s['y'])*4+abs(ang(h-s['h']))/45*2>s['tu']-keep: continue
                tmp=dict(s,x=px,y=py); p=chance(tmp,t,dist,h); n=min(keep//12,s['bursts'])
                v=1-(1-p)**n
                if mode=='disable' and t['big'] and aspect(tmp,t)=='rear': v*=1.6
                if best is None or v>best[0]: best=(v,px,py,h,n,p)
    if best is None:
        b=math.atan2(t['y']-s['y'],t['x']-s['x']); s['x']+=s['tu']/4*math.cos(b); s['y']+=s['tu']/4*math.sin(b); s['h']=math.degrees(b); return
    _,s['x'],s['y'],s['h'],n,p=best
    if s['torp']>0 and mode=='sink' and math.hypot(t['x']-s['x'],t['y']-s['y'])<=8:
        s['torp']-=1
        if random.random()<(0.85 if t['big'] else 0.85-t['ag']*0.04): hit(s,t,40 if s['t']=='SeaSled' else 60,False)   # torpedo: hull only; agile targets steer out of its path
    for _ in range(n):
        if t['out'] or p<=0.3 or s['bursts']<=0: break
        s['bursts']-=1
        if random.random()<p: hit(s,t,s['gun'][0])
        if mode=='disable' and t['dis']: break
def battle(J,C,mode='disable',rounds=12):
    A=J+C
    for r in range(rounds):
        for s in [u for u in J if not u['out']]: act(s,A,mode)
        for s in [u for u in C if not u['out']]: act(s,A,mode)
        if all(c['out'] or (mode=='disable' and c['dis']) for c in C): break
        if all(j['out'] for j in J): break
    return A
def run(name,fJ,fC,mode='disable',N=2000):
    r=dict(dis=0,sunk=0,esc=0,jlost=0,jdmg=0)
    for _ in range(N):
        J=fJ(); C=fC(); battle(J,C,mode)
        r['dis']+=sum(c['dis'] and not c['sunk'] for c in C)/len(C); r['sunk']+=sum(c['sunk'] for c in C)/len(C)
        r['esc']+=sum(c['esc'] for c in C)/len(C); r['jlost']+=sum(j['hp']<=0 for j in J)/len(J); r['jdmg']+=sum(1-max(0,j['hp'])/j['max'] for j in J)/len(J)
    print('%-46s [%s] disabled %3.0f%% | sunk %3.0f%% | escaped %3.0f%% | Joe lost %3.0f%% | Joe damage %3.0f%%'%(name,mode,*(100*r[k]/N for k in ('dis','sunk','esc','jlost','jdmg'))))
if __name__=='__main__':
    random.seed(11)
    ship=lambda:[mk('CobraShip','C',4,20,0)]
    run('Skystriker v Cobra-flagged ship',lambda:[mk('Skystriker','J',20,2,90)],ship)
    run('2 Skystrikers v Cobra-flagged ship',lambda:[mk('Skystriker','J',18,2,90),mk('Skystriker','J',22,2,90)],ship)
    run('2 Skystrikers v Cobra-flagged ship',lambda:[mk('Skystriker','J',18,2,90),mk('Skystriker','J',22,2,90)],ship,'sink')
    run('Devilfish v Cobra-flagged ship',lambda:[mk('Devilfish','J',20,2,90)],ship)
    run('Devilfish + Skystriker v Cobra-flagged ship',lambda:[mk('Devilfish','J',20,2,90),mk('Skystriker','J',22,2,90)],ship)
    run('S.H.A.R.C. v Cobra-flagged ship',lambda:[mk('SHARC','J',20,2,90)],ship,'sink')
    run('Devilfish v Water Moccasin',lambda:[mk('Devilfish','J',2,20,0)],lambda:[mk('Moccasin','C',27,20,180)],'sink')
    run('Devilfish v Moray',lambda:[mk('Devilfish','J',2,20,0)],lambda:[mk('Moray','C',27,20,180)],'sink')
    run('Devilfish (depth charges) v Sea Sled',lambda:[mk('Devilfish','J',2,20,0)],lambda:[mk('SeaSled','C',27,20,180)],'sink')
