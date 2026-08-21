#!/usr/bin/env python3
"""Build the head-to-head and rivalry data behind the Rivalry Board.

    python3 scripts/build_rivalries.py <path-to-mos-eisley-_chat.txt>

Two inputs. history.json supplies 18 seasons of matchups (2,344 games), and the
WhatsApp export supplies engagement -- who actually argues with whom. The export
is NEVER committed (see .gitignore); pass its path at build time. Output is
aggregate only: counts, records, percentages. No message text is written.

Franchise identity is resolved by owner id, because managers rename teams
constantly (THE DICKS -> Wade Garrets -> Wookie Leaks). Chat handles were mapped
to franchises from the transaction log and direct address in chat; the three
that took real work are recorded in ATTRIBUTION below.
"""
ATTRIBUTION = {
 # handle: (franchise, the evidence that settled it)
 '~ Mike': ('The Jet-I', 'posts the draft Zoom link as Michael Lagares; posts his own trades '
                         'as Belichicks / Return of the JET-I / MASTER JET-I in the official log'),
 '~ Pete': ('Guido Haters', 'announces "Guido\'s pick Ja Marr chase" in the draft thread; '
                            '"Guido Haters won\'t disappoint!"'),
 '~ Jay':  ('Heavy Hitters', 'New World Order: "Jay, we know you want desperately to be called '
                             'the Heavy Shitters"; The Machines: "Jay feels so fucking great right '
                             'now knowing he keeps the hitters alive!"'),
}

import json, math, collections, re, datetime, sys, os

MERGE={'scamp1467':'danscampi','Dgclunie':'MrBlast','espn39740077':'papasuelo',
 'nandon2624579':'Nando42','Wookie leaks 80':'coachnick1980redfox','ESPNfan3428058992':'coachnick1980redfox'}
# chat handle -> owner id -> franchise name.  All 16 active franchises now resolved.
CHAT={'The Machines':'Balls143','Pork Chop Express':'danscampi','Smoke Dragons':'john420blaze',
 'Horse Collars':'mcnutze','Beavers':'sheq7777','Still The Creamiest':'MrBlast',
 'The Dry Dicks':'coachnick1980redfox','~ Wookie':'coachnick1980redfox',
 'Lil Chops':'ESPNFAN3503249627','Tom Vertucci':'tommyvertu123','Powers Of Pain':'Maristmidi',
 'New World Order':'TheKidd420','Jim Hunt':'westchesterwarrior','Killer Klowns':'Nando42',
 '~ Jay':'papasuelo','~ Pete':'cuzo77','~ Mike':'Michael Lagares'}
NAME={'Balls143':'The Machines','danscampi':'Pork Chop Express','john420blaze':'Smoke Dragons',
 'mcnutze':'Horse Collars','sheq7777':'The Beaver Eaters','MrBlast':'Still The Creamiest',
 'coachnick1980redfox':'Wookie Leaks','ESPNFAN3503249627':'Lamb Chops','tommyvertu123':'Hairy Gumbas',
 'Maristmidi':'Powers of Pain','TheKidd420':'New World Order','westchesterwarrior':'Big Blue',
 'Nando42':'Killer Klowns','papasuelo':'Heavy Hitters','cuzo77':'Guido Haters',
 'Michael Lagares':'The Jet-I','SDYO':'The Dicks (05-12)','scotthselt':'Quahog Clams',
 'EricRosen80':'Never 1 A Game','cfoxv1980':'The Ox 45s','MothaL2210':'Heading Westbrook'}
def own(o):
    o=(o or '').strip(); return MERGE.get(o,o)

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHATPATH=sys.argv[1] if len(sys.argv)>1 else None
LINE=re.compile(r'^\[(\d{1,2}/\d{1,2}/\d{2}), (\d{1,2}:\d{2}:\d{2}\s*[AP]M)\] ([^:]+): (.*)$')
def load(path):
    out=[]
    for raw in open(path,encoding='utf-8',errors='replace'):
        raw=raw.replace('\u200e','').replace('\u202f',' ').rstrip('\n')
        m=LINE.match(raw)
        if m: out.append({'d':m.group(1),'t':m.group(2),'who':m.group(3).strip(),'x':m.group(4)})
        elif out: out[-1]['x']+=' '+raw.strip()
    return out
h=json.load(open(os.path.join(ROOT,'history.json')))
H=collections.defaultdict(lambda:{'g':0,'w':0,'l':0,'t':0,'pf':0.0,'pa':0.0,'po':0,'seasons':set(),'games':[]})
for s in h['seasons']:
    y=s['year']; tid={t['id']:own(t.get('owner')) for t in s['teams']}
    for m in s.get('matchups') or []:
        a,b=tid.get(m['home']),tid.get(m['away'])
        if not a or not b or a==b: continue
        sa,sb=m.get('homeScore') or 0,m.get('awayScore') or 0
        po=bool(m.get('playoff'))
        for x,z,sx,sz in ((a,b,sa,sb),(b,a,sb,sa)):
            d=H[(x,z)]; d['g']+=1; d['pf']+=sx; d['pa']+=sz; d['seasons'].add(y)
            if po: d['po']+=1
            d['w' if sx>sz else 'l' if sx<sz else 't']+=1
            d['games'].append({'y':y,'wk':m.get('week'),'po':po,'me':sx,'them':sz})

# chat engagement
ms=load(CHATPATH) if CHATPATH else []
for m in ms: m['ts']=datetime.datetime.strptime(m['d']+' '+re.sub(r'\s','',m['t']),'%m/%d/%y %I:%M:%S%p')
HEAT=re.compile(r"\b(wrong|dumb|stupid|idiot|clown|joke|lying|lie|clueless|garbage|trash|pathetic|"
                r"weak|soft|fraud|delusional|hypocrite|shut up|moron|dickhead|excuses|admit|cry|crying)\b",re.I)
volley=collections.Counter(); heated=collections.Counter()
for i in range(1,len(ms)):
    a,b=ms[i-1],ms[i]
    if a['who']==b['who']: continue
    oa,ob=CHAT.get(a['who']),CHAT.get(b['who'])
    if not oa or not ob or oa==ob: continue
    if not 0<=(b['ts']-a['ts']).total_seconds()<=420: continue
    k=tuple(sorted((oa,ob))); volley[k]+=1
    if HEAT.search(b['x']) or HEAT.search(a['x']): heated[k]+=1
tot=collections.Counter()
for (a,b),n in volley.items(): tot[a]+=n; tot[b]+=n

rows=[]
for (a,b),v in volley.items():
    d=H.get((a,b))
    if not d or d['g']<8: continue
    share=math.sqrt((v/tot[a])*(v/tot[b])); hh=heated[(a,b)]; hp=hh/v
    wp=d['w']/d['g']; bal=1-abs(wp-.5)*2
    rows.append({'a':NAME.get(a,a),'b':NAME.get(b,b),'ka':a,'kb':b,'g':d['g'],
      'rec':f"{d['w']}-{d['l']}"+(f"-{d['t']}" if d['t'] else ''),'diff':round(d['pf']-d['pa']),
      'po':d['po'],'yrs':len(d['seasons']),'v':v,'share':share,'heat':100*hp,'bal':bal,
      'score':share/0.30*0.30+bal*0.26+min(d['g'],36)/36*0.14+min(d['po'],6)/6*0.14+min(hp/0.022,1)*0.16})
rows.sort(key=lambda r:-r['score'])
json.dump({'note':'aggregate only; built by scripts/build_rivalries.py','rows':rows},open(os.path.join(ROOT,'rivalries.json'),'w'),indent=1)
json.dump({f'{a}|{b}':{'g':d['g'],'w':d['w'],'l':d['l'],'t':d['t'],'po':d['po'],
                       'pf':d['pf'],'pa':d['pa'],'games':d['games'],'seasons':sorted(d['seasons'])}
           for (a,b),d in H.items()},open(os.path.join(ROOT,'h2h.json'),'w'))
print('=== RIVALRY RANKING (all 16 franchises mapped) ===')
print(f"{'#':>2} {'pairing':48s} {'record':>8s} {'pts':>6s} {'g':>3s} {'PO':>3s} {'attn':>5s} {'heat':>5s}")
for i,r in enumerate(rows[:16],1):
    print(f"{i:2d} {r['a']+'  vs  '+r['b']:48s} {r['rec']:>8s} {r['diff']:+6d} {r['g']:3d} {r['po']:3d} "
          f"{r['share']*100:4.1f}% {r['heat']:4.1f}%")
