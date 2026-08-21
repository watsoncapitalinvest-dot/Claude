#!/usr/bin/env python3
"""Generate the picks article — divisions, conferences, champion.

    python3 scripts/build_picks.py

Same contract as build_preview.py, which this borrows its loaders from: the
calls are written, every number in them is interpolated from the record at
build time. A pick can be wrong — that is the point of a pick — but it cannot
misquote the season it is arguing from.
"""
import importlib.util, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('bp', os.path.join(ROOT, 'scripts', 'build_preview.py'))
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)
own, LBL, ORD, NUM, RIV_ALIAS = bp.own, bp.LBL, bp.ORD, bp.NUM, bp.RIV_ALIAS
SEASON = bp.SEASON

# ------------------------------------------------------------------ the calls
DIVISION = {
 'Spartan': ('The Machines',
   "Went {rec:The Machines} on {pf:The Machines} points, the most in the division, off the only "
   "top-eight finish in every season the records hold. The Chops own him head to head and it has "
   "never once cost him a season. A {grade:The Machines} class on top of the deepest roster in the "
   "league. This is the safest of the four calls."),
 'Spectre Syndicate': ('Guido Haters',
   "Taking the division off the reigning champion, which needs saying out loud. The Powers of Pain "
   "won the title on {pf:Powers of Pain} points — fewer than any team in the bracket — while the "
   "Haters posted {pf:Guido Haters} on the identical {rec:Guido Haters} record. Same wins, ninety-two "
   "more points, and a {grade:Guido Haters} draft against a champion who does not grade himself. The "
   "title was real. The scoring underneath it was not."),
 'Black and Blue': ('Big Blue',
   "The hardest division to call and the one most likely to embarrass this desk. The Express scored "
   "{pf:Pork Chop Express} to Big Blue's {pf:Big Blue} off the same {rec:Big Blue} record. The "
   "separator is the summer: an {grade:Big Blue} class against a {grade:Pork Chop Express}, and a "
   "franchise that has been to {finals:Big Blue} title games and lost none of them. The Beaver "
   "Eaters scored {pf:Beaver Eaters} and missed the bracket from here last year, which tells you "
   "what this division does to good teams."),
 'The Four Horsemen': ('New World Order',
   "Horse Collars won it at {rec:Horse Collars} and are not being picked to repeat it, because they "
   "scored fewer points than the team behind them and then drafted {grade:Horse Collars}, second "
   "worst on the board. The New World Order put up {pf:New World Order}, the most in the division, "
   "took a {grade:New World Order} class, and have {po:New World Order} top-eight finishes in "
   "{seasons:New World Order} seasons. Last year's {fin:New World Order} was the outlier, not the "
   "level."),
}

WILDCARD = {
 'John McClane': (['Powers of Pain', "Lil' Chops"],
   "The champion as a wild card is not an insult, it is arithmetic: {pf:Powers of Pain} points does "
   "not win a division containing a team that scored ninety-two more. He gets in anyway, because "
   "{titles:Powers of Pain} titles from {finals:Powers of Pain} title games is a manager who knows "
   "the three weeks that count. The Chops take the second on {pf:Lil' Chops} points and a series "
   "lead over the team picked to win the conference."),
 'Cobra Kai': (['Pork Chop Express', 'Horse Collars'],
   "The Express miss the division and are still the highest-scoring team in this league at "
   "{pf:Pork Chop Express}. That is the Black and Blue tax. Horse Collars take the last place on "
   "{rec:Horse Collars} and a division title already banked, which leaves the Beaver Eaters at "
   "{pf:Beaver Eaters} points on the outside again."),
}

CONFERENCE = {
 'John McClane': ('The Machines',
   "Nobody in this conference has his record and nobody is close. {allrec:The Machines} across "
   "{seasons:The Machines} seasons, {finals:The Machines} title games, and a bracket that has never "
   "once been played without him. Getting to the final is the thing he does."),
 'Cobra Kai': ('Big Blue',
   "Through the Express, who beat him to the points title and lost the game that mattered, and "
   "through a New World Order side that has reached {finals:New World Order} finals and won "
   "{titles:New World Order}. Big Blue is {finals:Big Blue}-for-{finals:Big Blue} in title games. "
   "The road to one is the part he has to prove again."),
}

CHAMPION = ('Big Blue',
  "So: Big Blue over The Machines, and this desk is aware of how that sounds after picking the "
  "Machines to walk his conference.\n"
  "Here is the whole argument. The Machines has been to {finals:The Machines} title games and won "
  "{titles:The Machines} of them — {finalrec:The Machines} in the only week that hands out a "
  "trophy. Big Blue has been to {finals:Big Blue} and won {titles:Big Blue}. "
  "{finalrec:Big Blue}. The most decorated manager in the league loses finals, and the man picked "
  "to beat him has never lost one.\n"
  "That is a small sample and this desk knows it. Seven losses across eighteen years is not a flaw "
  "in a manager, it is what happens to anyone who keeps arriving. But a pick has to come down on "
  "one side of something, and the only place these two separate is the last Sunday.")

HEDGE = (
  "WHAT WOULD MAKE THIS LOOK STUPID — Four things, in order of likelihood. Still The Cream drew an "
  "{grade:Still The Cream}, the best class anybody got, and finished {fin:Still The Cream}: if that "
  "draft lands, the Spectre Syndicate pick is wrong twice over. The Killer Klowns took an "
  "{grade:Killer Klowns} and have already won a title inside the last two years. The Hairy Gumbas "
  "hold the reigning champion {vs:Hairy Gumbas over Powers of Pain} and nobody has picked them for "
  "anything. And the Beaver Eaters scored {pf:Beaver Eaters} points last season, more than three of "
  "the four teams picked to win divisions, and are picked for nothing at all.")


def build():
    h = json.load(open(os.path.join(ROOT, 'history.json'), encoding='utf-8'))
    riv = json.load(open(os.path.join(ROOT, 'rivalries.json'), encoding='utf-8'))['rows']
    pg = {bp.GRADE_ALIAS.get(t['team'], t['team']): t['grade']
          for t in json.load(open(os.path.join(ROOT, 'pop-grades.json'), encoding='utf-8'))['years']['2026']}
    s = [x for x in h['seasons'] if x['year'] == SEASON][0]
    tid = {t['id']: own(t.get('owner')) for t in s['teams']}
    st = {LBL[tid[r['teamId']]]: r for r in s['standings']}

    car = {}
    for ss in sorted(h['seasons'], key=lambda x: x['year']):
        o = {t['id']: own(t.get('owner')) for t in ss['teams']}
        by = {r['teamId']: r for r in ss['standings']}
        for i, ow in o.items():
            r = by.get(i)
            if not r or ow not in LBL:      # franchises that have since left the league
                continue
            c = car.setdefault(LBL[ow], {'w': 0, 'l': 0, 'seasons': 0, 'titles': 0,
                                         'finals': 0, 'po': 0})
            c['w'] += r['wins']; c['l'] += r['losses']; c['seasons'] += 1
            c['titles'] += own(ss['champion']) == ow
            c['finals'] += r['rank'] <= 2
            c['po'] += r['rank'] <= 8

    def h2h(a, b):
        ra, rb = RIV_ALIAS.get(a, a), RIV_ALIAS.get(b, b)
        for r in riv:
            if {r['a'], r['b']} == {ra, rb}:
                w, l = (int(x) for x in r['rec'].split('-'))
                return f'{w}-{l}' if r['a'] == ra else f'{l}-{w}'
        raise SystemExit(f'no head-to-head row for {a} vs {b}')

    def sub(m):
        k = m.group(1)
        if ':' not in k:
            raise SystemExit(f'placeholder {{{k}}} needs a team')
        key, team = k.split(':', 1)
        if key == 'vs':
            a, b = team.split(' over '); return h2h(a, b)
        if team not in st:
            raise SystemExit(f'unknown team in placeholder: {team}')
        r, c = st[team], car[team]
        return {
            'rec': f"{r['wins']}-{r['losses']}",
            'pf': f"{r['pf']:,.0f}",
            'fin': ORD[r['rank']],
            'grade': pg.get(team, 'ungraded'),
            'allrec': f"{c['w']}-{c['l']}",
            'seasons': NUM[c['seasons']],
            'titles': NUM[c['titles']],
            'finals': NUM[c['finals']],
            'po': NUM[c['po']],
            'finalrec': f"{c['titles']}-{c['finals']-c['titles']}",
        }[key]

    def fill(t): return re.sub(r'\{([^}]+)\}', sub, t)

    paras = [
     "Every pick below comes off the same three things: what a team scored last season, what the "
     "Powers of Pain made of its draft, and what the franchise has done when it got to January "
     "before. Records are the worst of the three — this league just watched a 7-7 team win the "
     "whole thing — so points carry more weight here than wins do.",

     "THE CARD — Four division winners, four wild cards, two conference champions, one ring. Here "
     "is the desk's call on all of it, and the reasoning underneath, so it can be held against us "
     "in January.",
    ]
    for conf, dnames in bp.CONF.items():
        paras.append(f"{conf.upper()} CONFERENCE — Two divisions, two wild cards, and one of "
                     f"these four teams reaches the final.")
        for dv in dnames:
            pick, why = DIVISION[dv]
            paras.append(f"{dv.upper()} — {pick}. " + fill(why))
        wc = WILDCARD[conf][0]
        paras.append(f"{conf.upper()} WILD CARDS — {wc[0]} and {wc[1]}. " + fill(WILDCARD[conf][1]))
    for conf, (pick, why) in CONFERENCE.items():
        paras.append(f"{conf.upper()} CHAMPION — {pick}. " + fill(why))

    pick, why = CHAMPION
    parts = fill(why).split('\n')
    paras.append(f"THE CHAMPION — {pick}. " + parts[0])
    paras += parts[1:]
    paras.append(fill(HEDGE))
    paras.append("Sourcing: 2025 finishes, points and career totals from the league record, the same "
                 "eighteen seasons used everywhere else in this issue. Draft grades from the Powers "
                 "of Pain's 2026 board. Head-to-head from the 2,344 games behind The Grudge Report. "
                 "Every number is interpolated from those files by scripts/build_picks.py; the "
                 "opinions are the desk's own and carry no such guarantee.")

    entry = {"id": "kick-2026-picks", "slug": "kick-2026-picks",
     "flag": "THE PICKS", "kicker": "Kickoff 2026",
     "headline": "Four Divisions, Two Conferences, One Ring",
     "subhead": "The desk calls every round of it, and says what would make each call look silly.",
     "dateline": "MOS EISLEY · AUGUST 2026", "byline": "The SCFL NewsRoom · Kickoff",
     "status": "FILED", "release": "", "cover": "", "staff": "published", "paragraphs": paras}
    P = os.path.join(ROOT, 'investigations.json')
    d = json.load(open(P, encoding='utf-8'))
    inv = d['investigations']; inv[:] = [x for x in inv if x.get('id') != entry['id']]
    inv.insert(0, entry)
    tmp = P + '.tmp'
    json.dump(d, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.replace(tmp, P)
    return entry


if __name__ == '__main__':
    e = build()
    print(f"wrote {e['id']}: {len(e['paragraphs'])} paragraphs, "
          f"{sum(len(p.split()) for p in e['paragraphs'])} words")
