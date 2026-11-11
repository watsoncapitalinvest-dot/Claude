"""Harvest every prop placement out of the facility generator.

The generator already knows, for all 109 rooms, exactly which props sit on which
tiles - packer.place(r, name, x, y, w, d) is called once per prop with its tile
footprint. That is a plan view in data form, which is precisely what an X-COM
base-view sprite is a picture of. So nothing is reprojected and nothing is traced:
the placements are recorded and drawn from above.

specials.py does `from packer import *`, and specs.py does `from specials import *`,
so each module holds its OWN binding of place/who taken at import time. Patching
packer.place alone would record the ordinary rooms and silently miss every room
built by a special (hangars, motor pools, reactors, ranges).
"""
import sys, os, json, traceback
SRC, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, SRC); os.chdir(SRC)
import packer, specials, specs

REC = {'props': [], 'people': []}
_place, _who = packer.place, packer.who
def rec_place(r, name, x, y, w, d, front=None, shadow=True):
    REC['props'].append(dict(n=name, x=round(float(x),3), y=round(float(y),3),
                             w=round(float(w),3), d=round(float(d),3)))
    return _place(r, name, x, y, w, d, front, shadow)
def rec_who(r, x, y, kind):
    REC['people'].append(dict(k=kind, x=round(float(x),3), y=round(float(y),3)))
    return _who(r, x, y, kind)
for m in (packer, specials, specs):
    if hasattr(m, 'place'): m.place = rec_place
    if hasattr(m, 'who'):   m.who = rec_who

out, bad = {}, {}
for sp in specs.JOE + specs.COBRA:
    REC['props'], REC['people'] = [], []
    try:
        r = packer.build(sp)
        out[sp['id']] = dict(title=sp['title'], theme=sp['theme'],
                             size=list(sp.get('size', (1,1))),
                             X=getattr(r,'X',10), Y=getattr(r,'Y',10),
                             outdoor=bool(sp.get('outdoor')),
                             lanes=bool(sp.get('lanes', True)),
                             only=sp.get('only'),
                             props=list(REC['props']), people=list(REC['people']))
    except Exception:
        bad[sp['id']] = traceback.format_exc()[-300:]
json.dump(out, open(OUT,'w'), indent=0)
print("rooms harvested:", len(out), " failed:", len(bad))
for k,v in list(bad.items())[:5]: print(" !", k, v.replace('\n',' ')[-160:])
tot = sum(len(v['props']) for v in out.values())
print("placements:", tot, " people:", sum(len(v['people']) for v in out.values()))
