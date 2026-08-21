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

def resolve_ties(h):
    """history.json stores scores to half-point precision, so ~24 real games look
    like ties. The stored standings know the true W-L, which lets us recover the
    winner of each by constraint propagation. Verified: every recovered season
    reconciles exactly against its standings."""
    import collections
    stats={'resolved':0,'true_ties':0,'unresolved':0}
    for s in h['seasons']:
        st={r['teamId']:r for r in (s.get('standings') or [])}
        if not st: continue
        reg=[m for m in (s.get('matchups') or []) if not m.get('playoff')]
        base=collections.defaultdict(lambda:{'w':0,'l':0}); tied=[]
        for m in reg:
            a,b,sa,sb=m['home'],m['away'],m['homeScore'],m['awayScore']
            if sa==sb: tied.append(m); continue
            if sa>sb: base[a]['w']+=1; base[b]['l']+=1
            else: base[b]['w']+=1; base[a]['l']+=1
        need={t:{'w':st[t]['wins']-base[t]['w'],'l':st[t]['losses']-base[t]['l'],
                 't':st[t].get('ties',0)} for t in st}
        pend={id(m):m for m in tied}
        changed=True
        while changed:
            changed=False
            for m in list(pend.values()):
                a,b=m['home'],m['away']
                oa=sum(1 for x in pend.values() if a in (x['home'],x['away']))
                ob=sum(1 for x in pend.values() if b in (x['home'],x['away']))
                done=False
                for me,other,om in ((a,b,oa),(b,a,ob)):
                    if need[me]['w']==0 and need[me]['l']>0:
                        m['resolvedWinner']=other; need[other]['w']-=1; need[me]['l']-=1
                        del pend[id(m)]; changed=True; stats['resolved']+=1; done=True; break
                    if need[me]['l']==0 and need[me]['w']>0 and om==need[me]['w']:
                        m['resolvedWinner']=me; need[me]['w']-=1; need[other]['l']-=1
                        del pend[id(m)]; changed=True; stats['resolved']+=1; done=True; break
                if done: break
        for m in pend.values():
            a,b=m['home'],m['away']
            if need[a]['t']>0 and need[b]['t']>0: m['resolvedWinner']=None; stats['true_ties']+=1
            else: stats['unresolved']+=1
    return stats

def verify(h):
    """Independent check: summing matchups must reproduce the stored standings."""
    import collections
    bad=[]; checked=0
    for s in h['seasons']:
        st={r['teamId']:r for r in (s.get('standings') or [])}
        if not st: continue
        agg=collections.defaultdict(lambda:{'w':0,'l':0,'t':0,'pf':0.0,'pa':0.0})
        for m in (s.get('matchups') or []):
            if m.get('playoff'): continue
            rw=m.get('resolvedWinner','__none__')
            for x,y,sx,sy in ((m['home'],m['away'],m['homeScore'],m['awayScore']),
                              (m['away'],m['home'],m['awayScore'],m['homeScore'])):
                a=agg[x]; a['pf']+=sx; a['pa']+=sy
                if sx>sy: a['w']+=1
                elif sx<sy: a['l']+=1
                elif rw=='__none__' or rw is None: a['t']+=1
                else: a['w' if rw==x else 'l']+=1
        for tid,r in st.items():
            checked+=1; a=agg.get(tid)
            if not a or (a['w'],a['l'],a['t'])!=(r['wins'],r['losses'],r.get('ties',0)) \
               or abs(a['pf']-r['pf'])>1.5 or abs(a['pa']-r['pa'])>1.5:
                bad.append((s['year'],tid))
    return checked,bad

h=json.load(open(os.path.join(ROOT,'history.json')))
_r=resolve_ties(h)
_checked,_bad=verify(h)
# 2008 is the one season where the upstream import's standings disagree with its
# own scores (four teams, two games, margins of 3+ so it is not a rounding effect).
# We trust the game record, which is what head-to-head is built from, and refuse to
# let any NEW inconsistency slip through unnoticed.
KNOWN_BAD={2008}
print(f"data check: {_checked} team-seasons reconciled against stored standings | "
      f"mismatches: {len(_bad)} (all {sorted({y for y,_ in _bad}) or 'none'}) | "
      f"tied-looking games resolved from standings: {_r['resolved']}, "
      f"genuine ties: {_r['true_ties']}, unresolved: {_r['unresolved']}")
assert _r['unresolved']==0, 'a tied game could not be resolved'
assert {y for y,_ in _bad} <= KNOWN_BAD, f'new standings inconsistency: {_bad}'

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
            rw=m.get('resolvedWinner','__none__')
            if sx>sz: d['w']+=1
            elif sx<sz: d['l']+=1
            elif rw=='__none__' or rw is None: d['t']+=1
            else: d['w' if rw==(m['home'] if x==tid.get(m['home']) else m['away']) else 'l']+=1
            rw=m.get('resolvedWinner','__none__')
            side=None if rw in ('__none__',None) else ('me' if rw==(m['home'] if x==tid.get(m['home']) else m['away']) else 'them')
            d['games'].append({'y':y,'wk':m.get('week'),'po':po,'me':sx,'them':sz,'rw':side})

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


# ---- per-pairing detail the board renders -----------------------------------
def finals_map(h):
    """(year) -> (winner_owner, loser_owner) for each title game."""
    out={}
    for s in h['seasons']:
        tid={t['id']:own(t.get('owner')) for t in s['teams']}
        champ=own(s.get('champion')); po=[m for m in (s.get('matchups') or []) if m.get('playoff')]
        if not po or not champ: continue
        last=max(m['week'] for m in po)
        for m in po:
            if m['week']!=last: continue
            a,b=tid.get(m['home']),tid.get(m['away'])
            if champ not in (a,b): continue
            w,l=(a,b) if m['homeScore']>m['awayScore'] else (b,a)
            if w==champ: out[s['year']]=(w,l)
    return out
FIN=finals_map(h)

def enrich(a,b):
    d=H[(a,b)]
    gs=sorted(d['games'], key=lambda g:(g['y'],g['wk'] or 0))
    def res(g):
        if g['me']>g['them']: return 'W'
        if g['me']<g['them']: return 'L'
        rw=g.get('rw','__none__')
        return 'T' if rw in ('__none__',None) else ('W' if rw=='me' else 'L')
    seq=[res(g) for g in gs]
    streak=0; kind=seq[-1] if seq else ''
    for r in reversed(seq):
        if r!=kind: break
        streak+=1
    best=0; run=0
    for r in seq:
        run=run+1 if r=='W' else 0; best=max(best,run)
    last=gs[-1] if gs else None
    wins=[g for g,r in zip(gs,seq) if r=='W']; losses=[g for g,r in zip(gs,seq) if r=='L']
    biggest = max(wins, key=lambda g:g['me']-g['them']) if wins else None
    worst   = max(losses, key=lambda g:g['them']-g['me']) if losses else None
    close   = min(gs, key=lambda g:abs(g['me']-g['them'])) if gs else None
    pw=sum(1 for g,r in zip(gs,seq) if g['po'] and r=='W')
    pl=sum(1 for g,r in zip(gs,seq) if g['po'] and r=='L')
    fins=[{'y':y,'result':'W' if w==a else 'L'} for y,(w,l) in FIN.items() if {w,l}=={a,b}]
    def G(g):
        return None if not g else {'y':g['y'],'wk':g['wk'],'po':g['po'],'r':res(g),
                                   'for':round(g['me'],1),'against':round(g['them'],1)}
    return {'streak':{'kind':kind,'n':streak},'bestRun':best,'last':G(last),
            'biggestWin':G(biggest),'worstLoss':G(worst),'closest':G(close),
            'playoff':{'w':pw,'l':pl},'finals':sorted(fins,key=lambda f:f['y']),
            'first':gs[0]['y'] if gs else None}

rows=[]
for (a,b),v in volley.items():
    d=H.get((a,b))
    if not d or d['g']<8: continue
    share=math.sqrt((v/tot[a])*(v/tot[b])); hh=heated[(a,b)]; hp=hh/v
    wp=d['w']/d['g']; bal=1-abs(wp-.5)*2
    rows.append({'a':NAME.get(a,a),'b':NAME.get(b,b),'ka':a,'kb':b,'g':d['g'],
      'rec':f"{d['w']}-{d['l']}"+(f"-{d['t']}" if d['t'] else ''),'diff':round(d['pf']-d['pa']),
      'po':d['po'],'yrs':len(d['seasons']),'v':v,'share':share,'heat':100*hp,'bal':bal,
      'score':share/0.30*0.30+bal*0.26+min(d['g'],36)/36*0.14+min(d['po'],6)/6*0.14+min(hp/0.022,1)*0.16,
      'detail':enrich(a,b)})
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
