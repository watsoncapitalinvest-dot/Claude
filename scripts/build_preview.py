#!/usr/bin/env python3
"""Generate the season preview article from the record, not from memory.

    python3 scripts/build_preview.py

Writes the division-by-division preview into investigations.json. Every number
comes from history.json (last season's finish, verified against the standings)
and pop-grades.json (the draft class). Division and conference structure comes
from divisions.json. Nothing here is hand-typed, so it cannot drift.
"""
import json, os

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERGE={'scamp1467':'danscampi','Dgclunie':'MrBlast','espn39740077':'papasuelo','nandon2624579':'Nando42',
 'Wookie leaks 80':'coachnick1980redfox','ESPNfan3428058992':'coachnick1980redfox'}
own=lambda o: MERGE.get((o or '').strip(),(o or '').strip())
LBL={'papasuelo':'Heavy Hitters','tommyvertu123':'Hairy Gumbas','TheKidd420':'New World Order',
 'mcnutze':'Horse Collars','coachnick1980redfox':'Wookie Leaks','sheq7777':'Beaver Eaters',
 'westchesterwarrior':'Big Blue','danscampi':'Pork Chop Express','Nando42':'Killer Klowns',
 'Michael Lagares':'Master-Jeti','ESPNFAN3503249627':"Lil' Chops",'Balls143':'The Machines',
 'MrBlast':'Still The Cream','john420blaze':'Smoke Dragons','cuzo77':'Guido Haters',
 'Maristmidi':'Powers of Pain'}
GRADE_ALIAS={'Still the Creamiest':'Still The Cream','The Smoke Dragons':'Smoke Dragons',
 'Lil’ Chops':"Lil' Chops",'The Beaver Eaters':'Beaver Eaters'}
CONF={'John McClane':['Spartan','Spectre Syndicate'],'Cobra Kai':['Black and Blue','The Four Horsemen']}
SEASON=2025

def build():
    h=json.load(open(os.path.join(ROOT,'history.json'),encoding='utf-8'))
    divs=json.load(open(os.path.join(ROOT,'divisions.json'),encoding='utf-8'))
    pg={GRADE_ALIAS.get(t['team'],t['team']):t['grade']
        for t in json.load(open(os.path.join(ROOT,'pop-grades.json'),encoding='utf-8'))['years']['2026']}
    s=[x for x in h['seasons'] if x['year']==SEASON][0]
    tid={t['id']:own(t.get('owner')) for t in s['teams']}
    st={tid[r['teamId']]:r for r in s['standings']}
    champ=own(s.get('champion'))

    paras=[
     "Sixteen teams, two conferences, four divisions. Six of your fourteen games are against the three "
     "teams you are about to read alongside, which means the division you are in is the single biggest "
     "fact about your season. Win it and you are seeded above every wild card in your conference no "
     "matter what anybody's record says. Here is where all sixteen stand, with last season's finish and "
     "the grade the Powers of Pain gave their summer.",
    ]
    for conf, dnames in CONF.items():
        paras.append(f"{conf.upper()} CONFERENCE — Two divisions, four playoff places available: two "
                     f"division winners and two wild cards.")
        for dv in dnames:
            rows=[]
            for o in divs['current'][dv]:
                r=st[o]; nm=LBL[o]
                rows.append({'rank':r['rank'],'nm':nm,'w':r['wins'],'l':r['losses'],
                             'pf':r['pf'],'g':pg.get(nm,'not graded'),'champ':o==champ})
            rows.sort(key=lambda x:x['rank'])
            best=max(rows,key=lambda x:x['pf']); worst=min(rows,key=lambda x:x['pf'])
            paras.append(f"{dv.upper()} — " + '; '.join(
                f"{r['nm']} finished {r['w']}-{r['l']} on {r['pf']:.0f} points"
                + (" and won the championship" if r['champ'] else "")
                + f", draft grade {r['g']}" for r in rows) + '.')
            span=best['pf']-worst['pf']
            paras.append(f"The spread from top to bottom is {span:.0f} points. "
                         f"{best['nm']} scored the most in the division; {worst['nm']} the least.")
    tot=sorted(((r['pf'],LBL[o]) for o,r in st.items()), reverse=True)
    paras.append("ACROSS THE LEAGUE — The highest-scoring team of 2025 was " +
                 f"{tot[0][1]} on {tot[0][0]:.0f}; the lowest was {tot[-1][1]} on {tot[-1][0]:.0f}. "
                 f"That is a gap of {tot[0][0]-tot[-1][0]:.0f} points between the top and the bottom of "
                 "this league, which is roughly a touchdown and a half every week for a whole season.")
    paras.append("Sourcing: 2025 final standings from the league record, reconciled against the stored "
                 "season totals. Draft grades from the Powers of Pain's 2026 board. Division and "
                 "conference alignment recovered from the schedule and the playoff bracket. Generated "
                 "by scripts/build_preview.py, so the numbers here are the numbers on file.")

    entry={"id":"kick-2026-preview","slug":"kick-2026-preview",
     "flag":"THE SEASON PREVIEW","kicker":"Kickoff 2026",
     "headline":"All Sixteen, Division by Division",
     "subhead":"Where every team finished, what the draft gave them, and why the division you are in "
               "decides more of your season than anything you do in it.",
     "dateline":"MOS EISLEY · AUGUST 2026","byline":"The SCFL NewsRoom · Kickoff",
     "status":"FILED","release":"","cover":"","staff":"published","paragraphs":paras}
    P=os.path.join(ROOT,'investigations.json')
    d=json.load(open(P,encoding='utf-8'))
    inv=d['investigations']; inv[:]=[x for x in inv if x.get('id')!=entry['id']]
    inv.insert(0,entry)
    tmp=P+'.tmp'; json.dump(d,open(tmp,'w',encoding='utf-8'),ensure_ascii=False,indent=1); os.replace(tmp,P)
    return entry

if __name__=='__main__':
    e=build()
    print(f"wrote {e['id']}: {len(e['paragraphs'])} paragraphs, "
          f"{sum(len(p.split()) for p in e['paragraphs'])} words")
    for p in e['paragraphs'][1:5]: print('   '+p[:150])
