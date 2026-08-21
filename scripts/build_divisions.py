#!/usr/bin/env python3
"""Recover the league's division and conference structure from the schedule.

    python3 scripts/build_divisions.py

history.json carries no division field, so structure is inferred from how the
schedule is built:

  * you play your own division twice  -> divisional pairs are the four-team
    cliques in the "met twice" graph that exactly cover all sixteen teams;
  * you play the other division in your own conference once each -> the division
    a team plays four single games against is its conference partner;
  * the remaining games are scattered across the other conference.

Sixteen of eighteen seasons resolve. 2008 and 2013 used a different schedule
shape and are left unresolved rather than guessed. Current division names come
from the league app and are checked against the inferred membership.
"""
import json, os, collections, itertools

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERGE={'scamp1467':'danscampi','Dgclunie':'MrBlast','espn39740077':'papasuelo','nandon2624579':'Nando42',
 'Wookie leaks 80':'coachnick1980redfox','ESPNfan3428058992':'coachnick1980redfox'}
own=lambda o: MERGE.get((o or '').strip(),(o or '').strip())

# Division names as they appear in the league app, 2026.
CURRENT={
 'The Four Horsemen': {'papasuelo','tommyvertu123','TheKidd420','mcnutze'},
 'Black and Blue':    {'coachnick1980redfox','sheq7777','westchesterwarrior','danscampi'},
 'Spartan':           {'Nando42','Michael Lagares','ESPNFAN3503249627','Balls143'},
 'Spectre Syndicate': {'MrBlast','john420blaze','cuzo77','Maristmidi'},
}

def divisions(s):
    cnt=collections.Counter()
    for m in (s.get('matchups') or []):
        if m.get('playoff'): continue
        cnt[tuple(sorted((m['home'],m['away'])))]+=1
    twice={p for p,n in cnt.items() if n>=2}
    teams=sorted({t['id'] for t in s['teams']})
    adj={t:set() for t in teams}
    for a,b in twice: adj[a].add(b); adj[b].add(a)
    cl=[c for c in itertools.combinations(teams,4)
        if all(y in adj[x] for x,y in itertools.combinations(c,2))]
    def solve(rem,ch):
        if not rem: return ch
        f=min(rem)
        for c in cl:
            if f in c and set(c)<=rem:
                r=solve(rem-set(c),ch+[c])
                if r: return r
        return None
    got=solve(set(teams),[])
    return got if got and sorted(len(c) for c in got)==[4,4,4,4] else None

def conferences(s, ds):
    """The division you play four single games against is your conference partner."""
    dof={t:i for i,c in enumerate(ds) for t in c}
    cross=collections.defaultdict(collections.Counter)
    for m in (s.get('matchups') or []):
        if m.get('playoff'): continue
        a,b=dof[m['home']],dof[m['away']]
        if a!=b: cross[a][b]+=1; cross[b][a]+=1
    partner={}
    for d in range(4):
        best=max((n,o) for o,n in cross[d].items())
        partner[d]=best[1]
    # partner must be mutual for the split to be a real two-conference league
    if all(partner[partner[d]]==d for d in partner):
        seen=set(); out=[]
        for d in range(4):
            if d in seen: continue
            seen|={d,partner[d]}; out.append(sorted((d,partner[d])))
        return out if len(out)==2 else None
    return None

def build():
    h=json.load(open(os.path.join(ROOT,'history.json'),encoding='utf-8'))
    seasons={}
    for s in h['seasons']:
        ds=divisions(s)
        if not ds: continue
        tid={t['id']:own(t.get('owner')) for t in s['teams']}
        conf=conferences(s, ds)
        seasons[s['year']]={
          'divisions':[sorted(tid[t] for t in c) for c in ds],
          'conferences':conf}
    # realignments: pairs whose divisional status changed between resolved seasons
    prev=None; prevyear=None; realign=[]
    for y in sorted(seasons):
        cur={}
        for c in seasons[y]['divisions']:
            for a,b in itertools.combinations(sorted(c),2): cur[(a,b)]=True
        if prev is not None:
            shared={o for c in seasons[y]['divisions'] for o in c} & prevset
            moved=sum(1 for a,b in itertools.combinations(sorted(shared),2)
                      if prev.get((a,b),False)!=cur.get((a,b),False))
            if moved: realign.append({'from':prevyear,'to':y,'pairsMoved':moved})
        prev=cur; prevset={o for c in seasons[y]['divisions'] for o in c}; prevyear=y
    payload={'note':'inferred from the schedule by scripts/build_divisions.py',
             'current':{k:sorted(v) for k,v in CURRENT.items()},
             'realignments':realign,'seasons':seasons}
    json.dump(payload, open(os.path.join(ROOT,'divisions.json'),'w',encoding='utf-8'),
              ensure_ascii=False, indent=1)
    return payload, h

if __name__=='__main__':
    p,h=build()
    print(f"resolved {len(p['seasons'])}/18 seasons")
    last=max(p['seasons'])
    divs=[set(c) for c in p['seasons'][last]['divisions']]
    label={}
    print(f"\n{last} inferred divisions checked against the app's names:")
    for name,members in p['current'].items():
        hit=[i for i,d in enumerate(divs) if d==set(members)]
        if hit: label[hit[0]]=name
        print(f"  {'MATCH' if hit else 'MISS '}  {name}")
    for pair in (p['seasons'][last]['conferences'] or []):
        print(f"  conference: {' + '.join(label.get(i,str(i)) for i in pair)}")
    print("\nrealignments:", p['realignments'])
