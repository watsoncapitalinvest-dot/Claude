"""Killer W.H.A.L.E.: cut the moving parts out of the one Generals mesh (John 19:51): TURRET_L/R (tub + twin guns), CANNON_L/R
(Pounders), MSL_L/R (the quad SAM loads), DC (the depth-charge rack). Selection = every vertex of a face inside the part's box."""
import bpy,sys,bmesh,json
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2]); o=bpy.data.objects['GJCHASSIS']; me=o.data; mw=o.matrix_world
V=np.array([(mw@v.co)[:] for v in me.vertices])
def turret(P,cy): r=np.hypot(P[:,0]+0.3,P[:,1]-cy); return ((r<2.25)&(P[:,2]>14.2)).all() or ((P[:,0]>-1.2)&(P[:,0]<5.4)&(np.abs(P[:,1]-cy)<1.5)&(P[:,2]>15.55)).all()
def cannon(P,cy): return ((P[:,0]>float(sys.argv[-4]))&(P[:,0]<13.6)&(np.abs(P[:,1]-cy)<1.15)&(P[:,2]>10.2)&(P[:,2]<12.7)).all()
MSI=[m.name for m in me.materials].index('wh_missile')
def missiles(P,s): y=P[:,1]*s; return ((y>5.0)&(y<8.6)).all()
B=json.loads(sys.argv[-3]); 
def dc(P): return ((P[:,0]>B[0])&(P[:,0]<B[1])&(P[:,1]>B[2])&(P[:,1]<B[3])&(P[:,2]>B[4])&(P[:,2]<B[5])).all()
TESTS=[('TURRET_L',lambda P:turret(P,2.15)),('TURRET_R',lambda P:turret(P,-2.1)),('CANNON_L',lambda P:cannon(P,7.4)),('CANNON_R',lambda P:cannon(P,-7.4)),
       ('MSL_L',lambda P:missiles(P,1)),('MSL_R',lambda P:missiles(P,-1)),('DC',dc)]
sel={n:[] for n,_ in TESTS}
for p in me.polygons:
    P=V[list(p.vertices)]
    for n,t in TESTS:
        if n.startswith('MSL') and p.material_index!=MSI: continue
        if t(P): sel[n].append(p.index); break
for n in sel:
    if sel[n]:
        Q=np.array([V[list(me.polygons[i].vertices)].mean(0) for i in sel[n]]); print('PART',n,len(sel[n]),Q.min(0).round(2),Q.max(0).round(2))
SUB={}
for n in list(sel):
    if not sel[n]: continue
    Q=np.array([V[list(me.polygons[i].vertices)].mean(0) for i in sel[n]])
    if n.startswith('MSL'):
        ym,zm=np.median(Q[:,1]),np.median(Q[:,2])
        for i,q in zip(sel[n],Q): SUB.setdefault(f'{n}_{int(q[1]>ym)}{int(q[2]>zm)}',[]).append(i)
    elif n=='DC':
        lo,hi=Q[:,1].min(),Q[:,1].max(); w=(hi-lo)/6
        for i,q in zip(sel[n],Q): SUB.setdefault(f'DC_{min(5,int((q[1]-lo)/w))}',[]).append(i)
    else: SUB[n]=sel[n]
for n in SUB: print('SUB',n,len(SUB[n]))
sel=SUB
for n in sel:
    if not sel[n]: continue
    nm=me.copy(); ob=bpy.data.objects.new(n,nm); bpy.context.scene.collection.objects.link(ob); ob.matrix_world=o.matrix_world.copy()
    b2=bmesh.new(); b2.from_mesh(nm); b2.faces.ensure_lookup_table(); keep=set(sel[n])
    bmesh.ops.delete(b2,geom=[f for f in b2.faces if f.index not in keep],context='FACES'); b2.to_mesh(nm); b2.free()
bm=bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); allsel=[i for v in sel.values() for i in v]
bmesh.ops.delete(bm,geom=[bm.faces[i] for i in allsel],context='FACES'); bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1],compress=True)
