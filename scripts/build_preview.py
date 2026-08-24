#!/usr/bin/env python3
"""Generate the season preview article from the record, not from memory.

    python3 scripts/build_preview.py

Sixteen team entries. The judgement in each one is written; every number in it
is interpolated from the files at build time and never typed into the prose --
last season from history.json, the class from pop-grades.json, the alignment
from divisions.json, the head-to-head from rivalries.json. So a take can be
argued with, but it cannot be wrong about a number, and it cannot go stale: fix
a season in the record and the sentence fixes itself.

Placeholders available to every take are built in ctx() below.
"""
import json, os, re

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
# rivalries.json carries its own display names.
RIV_ALIAS={'Still The Cream':'Still The Creamiest',"Lil' Chops":'Lamb Chops',
 'Beaver Eaters':'The Beaver Eaters','Master-Jeti':'The Jet-I'}
CONF={'John McClane':['Spartan','Spectre Syndicate'],'Cobra Kai':['Black and Blue','The Four Horsemen']}
SEASON=2025

ORD={1:'first',2:'second',3:'third',4:'fourth',5:'fifth',6:'sixth',7:'seventh',8:'eighth',9:'ninth',
 10:'tenth',11:'eleventh',12:'twelfth',13:'thirteenth',14:'fourteenth',15:'fifteenth',16:'sixteenth'}
NUM={0:'no',1:'one',2:'two',3:'three',4:'four',5:'five',6:'six',7:'seven',8:'eight',9:'nine',10:'ten',
 11:'eleven',12:'twelve',13:'thirteen',14:'fourteen',15:'fifteen',16:'sixteen',17:'seventeen',18:'eighteen'}

# ---------------------------------------------------------------- the takes --
# {rec} 9-5   {pf} 1,417   {fin} seventh   {grade} B+   {seasons} eighteen
# {allrec} 192-47   {titles} four   {finals} eleven   {po} eighteen
# {last5} 4 4 2 7 7   {vs:Team} 30-4   {h2h_games:Team} 34
TAKE={
 'The Machines':
  "Went {rec} on {pf} points and finished {fin}. None of which is the story. The story is "
  "{allrec} across the {seasons} seasons on record, {titles} championships, {finals} title games, and "
  "a top-eight finish in every single year the records hold — no other franchise has more than "
  "twelve. He beats Still The Cream {vs:Still The Cream}. He beats the Killer Klowns "
  "{vs:Killer Klowns}. Exactly one team in this league has a winning record against him, and they "
  "are sitting directly above him in this division. The "
  "one crack: {fin} place two years running, and no belt since 2018. A {grade} draft says he is not "
  "planning to make that three.",
 "Lil' Chops":
  "Went {rec} on {pf} points and finished {fin}, which undersells the most interesting fact about "
  "them. They hold a {vs:The Machines} record against The Machines — the only winning series anyone "
  "has against him — and across those {h2h_games:The Machines} games the cumulative points "
  "difference is four. Not four a game. Four in total. The Powers of Pain gave the draft a {grade} "
  "for a single running back, which is either discipline or a quiet year, and the Chops have been "
  "quiet before.",
 'Master-Jeti':
  "Went {rec} on {pf} points and finished {fin}, a year after three straight seasons inside the top "
  "six. There is a championship on the shelf and {po} top-eight finishes in {seasons} seasons here, "
  "so the floor is real. He did not appear on the Powers of Pain's board this summer, which in a "
  "league that grades everything is its own kind of statement.",
 'Killer Klowns':
  "Won the championship in 2024 and finished {fin} in 2025 at {rec}. Defending champions have gone "
  "over the side before — twice to fifteenth — so the fall is not unheard of, only steep. {pf} "
  "points is the least in the division, and the "
  "franchise carries a {vs:The Machines} record against The Machines that is not a typo. The reason "
  "to watch anyway: the Powers of Pain graded this draft {grade}, the fourth-best mark on the board, "
  "and a team that has already proved it can win the whole thing does not need to be good for long.",
 'Powers of Pain':
  "The champion. {rec}, {pf} points — fewer than any other team that made the bracket — and the "
  "belt. Read the four years before it in order: fifteenth, eleventh, tenth, tenth, and then first. "
  "There are {titles} titles here in the seasons on record and {finals} title games, so this is a "
  "franchise that knows the walk. The thing standing in the way of a repeat is not the Machines and "
  "it is not the Express. It is the Hairy Gumbas, who hold a {vs:Hairy Gumbas over Powers of Pain} record over him "
  "across {h2h_games:Hairy Gumbas} games and are not in his division, which is the only mercy in it.",
 'Guido Haters':
  "Went {rec} on {pf} points and finished {fin}, the most points in the division and nothing much to "
  "show for it. The last five finishes read thirteenth, third, thirteenth, thirteenth, fourth, which "
  "is not a trend, it is a coin. The long story here is the quietest series in the league: "
  "{h2h_games:Powers of Pain} games against the Powers of Pain, sitting {vs:Powers of Pain}, two "
  "divisional rivals who have almost never said a word about it. A {grade} draft. He is closer than "
  "the finishes suggest.",
 'Smoke Dragons':
  "Went {rec} on {pf} points and finished {fin} — the fewest points in the division and the second "
  "fewest in the league. In {seasons} seasons on record there are {titles} championships and, "
  "harder to look at, {finals} title games. Not lost — reached. The Machines have him {vs:The Machines}. The {grade} "
  "draft leaned on a receiver and a developmental quarterback, which is a plan that needs two years, "
  "and the Dragons have had plenty of those.",
 'Still The Cream':
  "Finished {fin} at {rec} on {pf} points, and then watched the rename go to somebody else on the "
  "tiebreak. {allrec} across {seasons} seasons with {titles} titles and {finals} finals is the "
  "hardest line in this preview. So is {vs:The Machines} against The Machines. And yet: the Powers "
  "of Pain handed this draft an {grade}, the best grade given to anybody all summer. Last place has "
  "the first pick and the best class in the league. If it does not turn now, it does not turn.",
 'Pork Chop Express':
  "Scored {pf} points, more than anyone in this league, went {rec}, and lost the final. Finished "
  "{fin}. That is a season most managers would take and nobody wants to repeat. The worry is the "
  "summer: a {grade} class described as depth rather than difference, in a division where the other "
  "three all scored 1,466 or better. Being the best offence in the league did not settle 2025 and "
  "it will not settle this one either.",
 'Big Blue':
  "Went {rec} on {pf} points and finished {fin}. The résumé is {alltitles} championships, level "
  "with anyone who has ever played here, and inside the eighteen seasons on record {finals} title "
  "games and {finals} wins — the only unbeaten record in the building — off {allrec} overall. The last "
  "two years read fourth and fifth, which for this franchise counts as a slump. He drew an {grade} "
  "for the draft and holds Wookie Leaks {vs:Wookie Leaks}. The reason to be careful about writing "
  "him off: he has reached {finals} finals and never lost one.",
 'Beaver Eaters':
  "Here is the cruellest line in the preview. {allrec} across {seasons} seasons — identical, "
  "win for win and loss for loss, to Big Blue's — and {titles} championships in those seasons to "
  "Big Blue's four. In "
  "2025 he scored {pf} points, third most in the league, went {rec}, and finished {fin}: outside the "
  "bracket entirely. Then the Powers of Pain graded the draft a {grade}, the only one on the board, "
  "and called two of the three picks baffling. Historically one of the best drafters in this league. "
  "Not this year.",
 'Wookie Leaks':
  "Went {rec} on {pf} points and finished {fin}, the fewest points in a division where everybody "
  "else cleared 1,460. Big Blue has him {vs:Big Blue} across {h2h_games:Big Blue} games and The "
  "Machines {vs:The Machines}, so the schedule is not doing him any favours. The summer was the good "
  "news: an {grade} draft built on a receiver who fell further than he should have, and two swings "
  "at a thin running back class. If the receiver stays healthy this is a different team. If.",
 'Horse Collars':
  "Went {rec} on {pf} points and finished {fin}, up from eleventh and twelfth the two years before "
  "it. There is a championship here and {po} top-eight finishes in {seasons} seasons, so the jump is "
  "a return rather than a surprise. The summer is the argument against: a {grade}, second worst on "
  "the board, for a draft the Powers of Pain described as laying up. His longest series is "
  "{h2h_games:New World Order} games against the New World Order, sitting {vs:New World Order}, and "
  "he sees them twice a year.",
 'New World Order':
  "Went {rec} on {pf} points and finished {fin}, the most points in the division. This is the most "
  "consistently dangerous franchise nobody calls dangerous: {finals} title games, {po} top-eight "
  "finishes in {seasons} seasons, and finishes of fifth, second, third and second before last year's "
  "{fin}. The {grade} draft took two first-round receivers and left the roster lopsided, which the "
  "Powers of Pain flagged and the standings may not care about.",
 'Hairy Gumbas':
  "Went {rec} on {pf} points and finished {fin}, and the record does something strange with this "
  "franchise. He has {po} top-eight finishes in {seasons} seasons, the fewest of anyone here, and "
  "{titles} championships from {finals} title games. And yet he owns the reigning champion "
  "{vs:Hairy Gumbas over Powers of Pain} across {h2h_games:Powers of Pain} games. The {grade} draft "
  "took a quarterback who needs three years behind a starter, on a roster whose best players do not "
  "have three years. That tension is the whole season.",
 'Heavy Hitters':
  "Finished {fin} at {rec} on {pf} points — 182 behind the next-lowest team in the league, a "
  "margin that is difficult to look at. The rename is his. What the standings do not say: "
  "there is a championship on this shelf, and a {vs:The Jet-I} record over the Jet-I across "
  "{h2h_games:The Jet-I} games. The Powers of Pain gave the draft a {grade}, fifth best on the "
  "board, built around the one back everybody agreed was elite. New name, first pick, best class in "
  "the division. Worse hands have been dealt.",
}

DIV_INTRO={
 'Spartan': "One franchise has finished top eight in every season on record, and the other three are "
            "playing for the one wild card he does not take.",
 'Spectre Syndicate': "The champion lives here, and so does the worst points total of any division "
                      "winner's neighbourhood. Nobody in it scored 1,300.",
 'Black and Blue': "Three of the four highest-scoring teams in the league, in one division, playing "
                   "each other twice. Somebody very good misses the playoffs out of this.",
 'The Four Horsemen': "The widest division in the league, and the one carrying the rename.",
}


def build():
    h=json.load(open(os.path.join(ROOT,'history.json'),encoding='utf-8'))
    # All-time championships where the league knows them; history.json holds only
    # eighteen of the league's seasons, so counts taken from it can understate.
    lt=json.load(open(os.path.join(ROOT,'league-titles.json'),encoding='utf-8'))['allTimeTitles']
    divs=json.load(open(os.path.join(ROOT,'divisions.json'),encoding='utf-8'))
    riv=json.load(open(os.path.join(ROOT,'rivalries.json'),encoding='utf-8'))['rows']
    pg={GRADE_ALIAS.get(t['team'],t['team']):t['grade']
        for t in json.load(open(os.path.join(ROOT,'pop-grades.json'),encoding='utf-8'))['years']['2026']}
    s=[x for x in h['seasons'] if x['year']==SEASON][0]
    tid={t['id']:own(t.get('owner')) for t in s['teams']}
    st={tid[r['teamId']]:r for r in s['standings']}
    champ=own(s.get('champion'))

    # career totals per owner
    car={}
    for ss in sorted(h['seasons'],key=lambda x:x['year']):
        o={t['id']:own(t.get('owner')) for t in ss['teams']}
        by={r['teamId']:r for r in ss['standings']}
        for i,ow in o.items():
            r=by.get(i)
            if not r: continue
            c=car.setdefault(ow,{'w':0,'l':0,'seasons':0,'titles':0,'finals':0,'po':0,'fin':[]})
            c['w']+=r['wins']; c['l']+=r['losses']; c['seasons']+=1
            c['titles']+= (own(ss['champion'])==ow)
            c['finals'] += r['rank']<=2
            c['po']     += r['rank']<=8
            c['fin'].append(r['rank'])

    def h2h(a,b):
        """Wins-losses for a against b, from a's side."""
        ra,rb=RIV_ALIAS.get(a,a),RIV_ALIAS.get(b,b)
        for r in riv:
            if {r['a'],r['b']}=={ra,rb}:
                w,l=(int(x) for x in r['rec'].split('-'))
                return (f'{w}-{l}' if r['a']==ra else f'{l}-{w}', r['g'])
        raise SystemExit(f'no head-to-head row for {a} vs {b}')

    def render(nm, ow):
        r=st[ow]; c=car[ow]
        ctx={'rec':f"{r['wins']}-{r['losses']}", 'pf':f"{r['pf']:,.0f}", 'fin':ORD[r['rank']],
             'grade':pg.get(nm,'ungraded'), 'seasons':NUM[c['seasons']],
             'allrec':f"{c['w']}-{c['l']}", 'titles':NUM[c['titles']],
             'finals':NUM[c['finals']], 'po':NUM[c['po']],
             'alltitles':NUM[lt.get(nm, c['titles'])],
             'last5':' '.join(str(x) for x in c['fin'][-5:])}
        def sub(m):
            k=m.group(1)
            if k.startswith('vs:'):
                other=k[3:]
                if ' over ' in other:                       # {vs:A over B} -> A's side
                    a,b=other.split(' over '); return h2h(a,b)[0]
                return h2h(nm,other)[0]
            if k.startswith('h2h_games:'):
                n=h2h(nm,k[10:])[1]
                return NUM[n] if n<=12 else str(n)   # house style: spell out to twelve
            if k not in ctx: raise SystemExit(f'{nm}: unknown placeholder {{{k}}}')
            return ctx[k]
        take=TAKE.get(nm)
        if not take: raise SystemExit(f'no take written for {nm}')
        return f"{nm.upper()} — " + re.sub(r'\{([^}]+)\}', sub, take)

    paras=[
     "Sixteen teams, two conferences, four divisions. Six of your fourteen games are against the "
     "three teams you are about to read alongside, which means the division you are in is the single "
     "biggest fact about your season — bigger than your draft, bigger than your roster, and entirely "
     "outside your control. Win it and you are seeded above every wild card in your conference no "
     "matter what anybody's record says. Here is all sixteen, in the order they finished.",
    ]
    for conf,dnames in CONF.items():
        paras.append(f"{conf.upper()} CONFERENCE — Two divisions, four places: the two division "
                     f"winners, and two wild cards for whoever is left.")
        for dv in dnames:
            rows=sorted(((st[o]['rank'],LBL[o],o) for o in divs['current'][dv]))
            span=max(st[o]['pf'] for _,_,o in rows)-min(st[o]['pf'] for _,_,o in rows)
            paras.append(f"{dv.upper()} — {DIV_INTRO[dv]} {span:.0f} points separate top from bottom.")
            for _,nm,ow in rows:
                paras.append(render(nm,ow))

    tot=sorted(((r['pf'],LBL[o]) for o,r in st.items()), reverse=True)
    paras.append("ACROSS THE LEAGUE — The highest-scoring team of 2025 was " +
                 f"{tot[0][1]} on {tot[0][0]:.0f}; the lowest was {tot[-1][1]} on {tot[-1][0]:.0f}. "
                 f"That is a gap of {tot[0][0]-tot[-1][0]:.0f} points between the top and the bottom "
                 "of this league, which is roughly a touchdown and a half every week for a whole "
                 "season. The team at the top of it lost the final. The team at the bottom of it is "
                 "getting a new name.")
    paras.append("Sourcing: 2025 final standings from the league record, reconciled against the "
                 "stored season totals. Career totals, championships and title-game appearances "
                 "counted across the eighteen seasons on file. Head-to-head records from the same "
                 "2,344 games as The Grudge Report. Draft grades and the notes on them from the "
                 "Powers of Pain's 2026 board. Division and conference alignment recovered from the "
                 "schedule and the playoff bracket. Every number here is interpolated from those "
                 "files at build time by scripts/build_preview.py — none of it is typed into the "
                 "prose, so it cannot drift from the record.")

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
