"""GIJOE_SAMPLE 30x30 block: Cobra bunker (west), Joe outpost (east, by the landing zone), trees and cover."""
import struct, sys, json
OUT=sys.argv[1]
names=json.load(open('tiles/names.json')); I={n:68+i for i,n in enumerate(names)}   # BLANKS 2 + CULTIVAT 37 + BARN 29
W=L=30; Z=2
F,WW,NW,OB=0,1,2,3
g=[[[[0,0,0,0] for x in range(W)] for y in range(L)] for z in range(Z)]
def put(z,x,y,part,name): g[z][y][x][part]=I[name]
for y in range(L):
    for x in range(W): put(0,x,y,F,'grass')
# dirt road from the landing zone (east edge) west to the bunker door, and a spur north to the outpost door
for x in range(8,30):
    for y in (14,15): put(0,x,y,F,'dirt')
for y in range(12,14): put(0,7,y,F,'dirt'); put(0,8,y,F,'dirt')
for y in range(16,22): put(0,27,y,F,'dirt'); put(0,28,y,F,'dirt')
def building(x0,y0,x1,y1,floor,roof,wall,door_w=(),door_n=(),emb_w=(),emb_n=(),emb_name=None,door_names=None):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1): put(0,x,y,F,floor); put(1,x,y,F,roof)
    for x in range(x0,x1+1):
        put(0,x,y0,NW,wall+'_n')                                  # back (north) wall
        put(0,x,y1+1,NW,(door_names[1] if x in door_n else (emb_name+'_n' if x in emb_n else wall+'_n')))   # front (south) wall
    for y in range(y0,y1+1):
        put(0,x0,y,WW,wall+'_w')                                  # back (west) wall
        put(0,x1+1,y,WW,(door_names[0] if y in door_w else (emb_name+'_w' if y in emb_w else wall+'_w')))  # front (east) wall
# Cobra bunker, west side
building(3,4,11,11,'metalfloor','roof_cobra','cobra',door_w=(7,),door_n=(7,),emb_w=(5,9),emb_n=(4,10),emb_name='cobra_emb',door_names=('cobra_door_w','cobra_door_n'))
# G.I. Joe outpost, east side next to the landing zone
building(19,18,25,25,'concrete','roof_joe','joe',door_w=(21,),door_n=(22,),emb_w=(23,),emb_n=(20,24),emb_name='joe_star',door_names=('joe_door_w','joe_door_n'))
for x in range(26,30):
    for y in range(16,26):
        if g[0][y][x][F]==I['grass']: put(0,x,y,F,'concrete')
# props
objs={'console':[(5,6),(9,9),(21,19),(24,24)],'crate':[(14,5),(14,10),(13,13),(10,6),(22,23),(17,20)],
      'barrels':[(15,8),(10,16),(16,12),(4,10)],'flagpole':[(27,17)],
      'tree':[(1,1),(15,1),(22,3),(28,5),(1,17),(9,20),(14,24),(4,27),(12,28),(17,16)],
      'pine':[(25,1),(18,9),(2,22),(8,25),(27,28),(20,28)],
      'bush':[(13,2),(19,5),(26,10),(6,18),(12,19),(16,27),(24,12),(1,8),(10,24)],
      'rock':[(20,1),(29,9),(5,23),(15,18)]}
for name,pts in objs.items():
    for x,y in pts: put(0,x,y,OB,name)
for x in range(20,25): put(0,x,16,NW,'sandbag_n')       # sandbag line north of the outpost
for y in range(18,22): put(0,29,y,WW,'sandbag_w')       # and covering the door approach
for x in range(5,10): put(0,x,14,NW,'sandbag_n')        # Cobra sandbags in front of the bunker
data=bytes([L,W,Z])
for z in range(Z-1,-1,-1):
    for y in range(L):
        for x in range(W): data+=bytes(g[z][y][x])
open(f'{OUT}/MAPS/GIJOE_SAMPLE.MAP','wb').write(data)
# routes: Cobra spawn/patrol points in and around the bunker
pts=[(5,6),(8,5),(10,8),(6,10),(9,11),(4,8),(13,7),(14,12),(8,13),(16,9),(12,16),(5,16),(16,3),(19,12)]
nodes=b''
for i,(x,y) in enumerate(pts):
    links=[]
    for j,(a,b) in enumerate(pts):
        if j!=i: links.append((max(abs(a-x),abs(b-y)),j))
    links=sorted(links)[:3]
    lb=b''.join(bytes([j,d,0]) for d,j in links)+bytes([255,0,0])*(5-len(links))
    rank=4 if i<3 else 2
    nodes+=bytes([y,x,Z-1,0])+lb+bytes([0,rank,3,0,5])
open(f'{OUT}/ROUTES/GIJOE_SAMPLE.RMP','wb').write(nodes)
print('map',len(data),'nodes',len(pts))
