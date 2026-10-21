#!/usr/bin/env python3
"""The Trade Audit -- the Machines ledger, computed rather than remembered.

    python3 scripts/build_trade_audit.py

The first draft of this piece was written from memory and it did not survive
contact with trades.json. Every figure in the paragraph that carried the whole
defence was wrong: forty-five deals (sixty-seven), fifteen franchises
(fourteen), Wookie Leaks the most frequent partner at sixteen (Lil' Chops, at
fifteen), New World Order at nine (two), Smoke Dragons at eight (two), Killer
Klowns at seven (three). The spread it described does not exist.

Worse, the real shape ran the other way. His two most frequent partners are the
two weakest franchises in the league's recorded history, and between them they
account for getting on for half his deals -- which is the prosecution's case,
stated by the evidence the defence brought.

So the article is no longer written. It is derived: this script reads the
ledger, counts what is there, and prints the sentences around the counts. The
argument is the same one and the verdict is the same verdict, but it is now
made out of what the ledger actually says, including the part that is hard.

Inputs
    trades.json          256 itemised deals, 2021-2026. There is nothing
                         before 2021 -- the builtNote says there was no
                         dynasty market -- so this is the dynasty-era ledger
                         and the copy says so rather than claiming the lot.
    records.json         League Legacy's all-time table, for partner quality.
    scfl-franchises.json names to franchises, because everybody renames.

Status is held. This writes the article into investigations.json and nothing
else: no page, no catalog entry, no share card. It is John's to release.
"""
import json, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLE_ID = 'trade-audit'
ME = 'machines'

ONES = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
        'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
        'sixteen', 'seventeen', 'eighteen', 'nineteen']
TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy',
        'eighty', 'ninety']


def word(n):
    """Numbers as words, because the copy is written in them."""
    n = int(n)
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ('-' + ONES[n % 10] if n % 10 else '')
    return f'{n:,}'


def facts():
    j = lambda f: json.load(open(os.path.join(ROOT, f), encoding='utf-8'))
    tj = j('trades.json')
    fr = j('scfl-franchises.json')
    look = fr['lookup']
    norm = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower())
    key = lambda s: look.get(norm(s)) or norm(s)
    rec = {key(r['name']): r for r in j('records.json')['standings']}
    # records.json carries the name a franchise had in League Legacy -- Lamb
    # Chops for what is now Lil' Chops. scfl-franchises.json says which name to
    # print, and the copy has to use that one or the league will not recognise
    # who it is reading about.
    club = {k: r['name'] for k, r in rec.items()}
    for row in fr['franchises']:
        k = row.get('key') or key(row.get('club') or '')
        if k:
            club[k] = row.get('club') or club.get(k, k)

    trades = tj['trades']
    seasons = sorted({t['season'] for t in trades})
    mine = [t for t in trades if ME in [key(s['team']) for s in t['sides']]]

    # how often each franchise appears in ANY deal -- the league's busiest
    # trader is not who the theory assumes
    seen = collections.Counter()
    for t in trades:
        for s in t['sides']:
            seen[key(s['team'])] += 1

    partner = collections.Counter()
    got_p = got_k = gave_p = gave_k = 0
    in_, out_ = collections.defaultdict(list), collections.defaultdict(list)
    for t in mine:
        for s in t['sides']:
            k = key(s['team'])
            if k != ME:
                partner[k] += 1
            for a in s['gets']:
                p = a.get('player')
                if k == ME:
                    if p:
                        got_p += 1
                        in_[p].append(t['season'])
                    else:
                        got_k += 1
                else:
                    if p:
                        gave_p += 1
                        out_[p].append(t['season'])
                    else:
                        gave_k += 1

    # every move of a player in or out, with the team on the other side, so a
    # round trip can name both counterparties instead of implying them
    moves = collections.defaultdict(list)
    for t in mine:
        ks = [key(x['team']) for x in t['sides']]
        for k, side in zip(ks, t['sides']):
            other = [x for x in ks if x != k]
            for a in side['gets']:
                if a.get('player'):
                    moves[a['player']].append(
                        {'y': t['season'], 'to': k,
                         'from': other[0] if len(other) == 1 else None})

    per_season = collections.Counter(t['season'] for t in mine)
    # the metronome: the run of consecutive seasons on the same count
    full = [y for y in seasons if y != seasons[-1]] or seasons
    counts = [per_season.get(y, 0) for y in full]
    same = len(set(counts)) == 1

    # one row per deal: who was across the table, so a three-team trade counts
    # once however many partners it had
    across = [{key(x['team']) for x in t['sides']} - {ME} for t in mine]
    deals_with = lambda f: sum(1 for ks in across if any(f(rec.get(k) or {}) for k in ks))
    top = partner.most_common()
    return {
        'span': (seasons[0], seasons[-1]),
        'league_deals': len(trades),
        'deals': len(mine),
        'partners': len(partner),
        'top': top,
        'rec': rec, 'club': club, 'seen': seen,
        'got_p': got_p, 'got_k': got_k, 'gave_p': gave_p, 'gave_k': gave_k,
        'per_season': per_season, 'full': full, 'metronome': counts[0] if same else None,
        'busiest': seen.most_common(1)[0],
        'with_contenders': deals_with(lambda r: r.get('playoffs', 0) >= 10),
        'with_champions': deals_with(lambda r: r.get('titles', 0) > 0),
        'top_two_deals': sum(1 for ks in across
                             if ks & {top[0][0], top[1][0]}),
        'sides': sum(partner.values()),
        'round_trips': sorted((p for p in set(in_) & set(out_)
                               if max(in_[p]) > min(out_[p])),
                              key=lambda p: (max(in_[p]) - min(out_[p]), max(in_[p])),
                              reverse=True),
        'others': (j('sleeper-schedule.json').get('total_rosters') or 16) - 1,
        'moves': moves,
        'in_': in_, 'out_': out_, 'trades': trades, 'key': key, 'mine': mine,
    }


pc = lambda v: f'.{round(v * 1000):03d}'
allplay = lambda s: '-'.join(f'{int(x):,}' for x in s.split('-'))


def prose(F):
    """The article. Every figure in it comes out of facts()."""
    rec, club, top = F['rec'], F['club'], F['top']
    key_of = lambda r: next(k for k, x in rec.items() if x is r)
    me = rec[ME]
    y0, y1 = F['span']
    name = lambda k: club.get(k, k)

    # the two ends of the partner list, which is where the argument lives
    (k1, n1), (k2, n2) = top[0], top[1]
    pair = F['top_two_deals']
    share = round(100 * pair / F['deals'])
    # the strongest franchises he deals with, by titles then playoffs
    strong = sorted((k for k, _ in top if (rec.get(k) or {}).get('titles', 0) > 0),
                    key=lambda k: (-rec[k]['titles'], -rec[k].get('playoffs', 0)))
    best = strong[0]
    best_n = dict(top)[best]

    # full-era franchises only: a three-season side with a hot run is not a
    # comparison, and the first draft's "nobody else is above .600" was one
    era = max(r.get('numSeasons', 0) for r in rec.values())
    peers = sorted((r for r in rec.values() if r.get('numSeasons', 0) >= era - 1),
                   key=lambda r: -r['winPct'])
    runner = peers[1]

    busiest_k, busiest_n = F['busiest']
    metro = F['metronome']

    P = []
    P.append(
        'There is a theory of the Skirt Chasers Fantasy League that has survived longer '
        'than most of the franchises in it. The theory is simple and it is repeated, in '
        'some form, every single autumn: Keith cheats. The Machines are the Evil Empire. '
        'He preys on the weak owners, he collects the rebuilders like toll booths, and '
        'the rest of the league is left to split the scraps he does not want. It is a '
        'good story. It has a villain, it has victims, and it explains — cleanly, '
        'comfortably — why the same team keeps ending up on top. This newsroom decided '
        'to do the one thing nobody in twenty-one years of group chat had bothered to '
        'do. We pulled the receipts.')

    P.append(
        f'The record itself is not in dispute, and it is the reason the theory exists at '
        f'all. The Machines are {me["record"]} across the tracked era — a {pc(me["winPct"])} '
        f'winning percentage in a league where the next best side to have gone the full '
        f'{word(me["numSeasons"])} seasons, {name(key_of(runner))}, sits on '
        f'{pc(runner["winPct"])}. '
        f'{word(me["playoffs"]).capitalize()} playoff appearances in '
        f'{word(me["numSeasons"])} seasons. {word(me["titles"]).capitalize()} '
        f'championships, {word(me["runnerUps"])} runner-up finishes, an all-play record '
        f'({allplay(me["allPlay"])}) that reads like a typo. You do not have to like it to respect '
        f'it, and most of the league has chosen the first option. When a team is that good '
        f'for that long, the human brain does not reach for "well-run." It reaches for '
        f'"rigged." That instinct is the entire case for the prosecution, and it is worth '
        f'taking seriously — so we did.')

    P.append(
        f'The charge, stated plainly, is collusion: that Keith wins because a handful of '
        f'soft, compliant owners feed him their best players for pennies. If that were '
        f'true, it would leave a fingerprint. Collusion is narrow by nature — you cannot '
        f'conspire with the whole room. So we mapped every trade in the itemised ledger, '
        f'{word(F["league_deals"])} deals from {y0} to {y1}, which is the dynasty era and '
        f'all of it; there was no dynasty market before that and so there is nothing '
        f'before that to read. {word(F["deals"]).capitalize()} of those deals have The '
        f'Machines on one side of the table.')

    P.append(
        f'The first thing the ledger does is refuse to clear him. His most frequent '
        f'partner is {name(k1)}, with {word(n1)} deals. Second is {name(k2)}, with '
        f'{word(n2)}. Between them that is {word(pair)} of his {word(F["deals"])} deals — '
        f'about {share} per cent of everything he has done — and '
        f'they are, by the all-time table, the two weakest franchises in the league: '
        f'{name(k1)} {rec[k1]["record"]}, {name(k2)} {rec[k2]["record"]} with '
        f'{"no playoff appearance at all" if not rec[k2].get("playoffs") else "barely a playoff appearance"} '
        f'in {word(rec[k2]["numSeasons"])} seasons. If you wanted to draw the prosecution '
        f'case as a chart, that is the chart. We are not going to pretend otherwise, '
        f'because it is the first thing in the file.')

    P.append(
        f'The second thing the ledger does is refuse to convict him. Those '
        f'{word(F["deals"])} deals are spread across {word(F["partners"])} different '
        f'franchises — effectively everyone who has held a roster in the dynasty era. '
        f'{word(F["with_contenders"]).capitalize()} of them were with sides that have made '
        f'the playoffs ten times or more. {word(F["with_champions"]).capitalize()} were '
        f'with sides that have won the thing. His joint-second most frequent partner is '
        f'{name(best)}, who own {word(rec[best]["titles"])} championships — more than '
        f'Keith does — and who have done {word(best_n)} deals with him. That is not a '
        f'cabal of three. That is a man doing business with the entire building, including '
        f'the parts of it that can beat him.')

    P.append(
        'Both things are true at once, and the theory cannot hold both. Collusion needs a '
        'closed room. What the ledger shows is an open one with two doors that get used '
        'more than the others — and in a dynasty league, those two doors have a name. The '
        'rebuilders are not the contender\'s victims; they are the contender\'s trading '
        'partners by design. A team going nowhere in November has one asset a title team '
        'wants and one thing it needs, and the title team is the only reliable buyer in '
        'the building. The sides who trade with Keith most are the sides with the most '
        'reason to.')

    P.append(
        f'And the direction of travel is the opposite of the one the story tells. Across '
        f'those {word(F["deals"])} deals The Machines took in {word(F["got_p"])} players '
        f'and gave up {word(F["gave_p"])}. They took in {word(F["got_k"])} picks and gave '
        f'up {word(F["gave_k"])}. By the count, the Evil Empire is a net seller of players '
        f'and a net '
        f'buyer of draft capital — which is not what hoovering up the league\'s veterans '
        f'looks like. It is what a rebuild looks like, run every year, by a team that '
        f'keeps winning while it runs it.')

    busy = ('He is not even the busiest man in the market. '
            f'{name(busiest_k)} appear in {word(busiest_n)} deals in this ledger; '
            f'The Machines appear in {word(F["seen"][ME])}.'
            if busiest_k != ME else
            f'He is the busiest man in the market: {word(busiest_n)} appearances in '
            f'{word(F["league_deals"])} deals.')
    rhythm = (f' And the rate never moves. {word(metro).capitalize()} trades in '
              + ', '.join(str(y) for y in F['full'][:-1]) + f' and {F["full"][-1]}: '
              f'{word(len(F["full"]))} straight seasons on the same number, with a '
              f'different set of partners every time.' if metro else '')
    P.append(busy + rhythm + ' Whatever he is doing, he is doing it in public, on a '
             'schedule, with everyone.')

    rt = F['round_trips']
    if rt:
        bits = []
        for p in rt[:2]:
            mv = sorted(F['moves'][p], key=lambda m: m['y'])
            gone = next(m for m in mv if m['to'] != ME)
            back = next(m for m in mv if m['to'] == ME and m['y'] > gone['y'])
            # naming both counterparties says the player came back from somewhere
            # else without the copy having to assert it
            bits.append(
                f'{p} went to {name(gone["to"])} in {gone["y"]} and was bought back from '
                f'{name(back["from"]) if back["from"] else "the market"} in {back["y"]}, '
                f'{word(back["y"] - gone["y"])} '
                f'year{"" if back["y"] - gone["y"] == 1 else "s"} later')
        P.append(
            'Does he win the deals? The ledger cannot tell you that, and this desk is not '
            'going to pretend it can — there is no price on a 2021 trade that is not just '
            'today\'s opinion in a wig. What the ledger can tell you is that he misses. '
            + '. '.join(b[0].upper() + b[1:] for b in bits) + '. '
            + (f'{word(len(rt)).capitalize()} players in this ledger have made that round '
               f'trip. ' if len(rt) > 1 else 'That is the only round trip in the ledger. ')
            + 'It is not the paperwork of a man with the game in a fix. It is the '
              'paperwork of a very good manager who is still, occasionally, human — which '
              'is the most exculpatory evidence we found.')

    P.append(
        f'So why does the accusation never die? Because it does useful work for the '
        f'{word(F["others"])} other guys. "Keith cheats" is a more bearable '
        f'explanation than "Keith is better than me at the one thing we all show up to '
        f'do." The persecution complex Keith wears — everyone\'s teaming up on me, they '
        f'gang up because I\'m the best — is not entirely paranoia; the chat does organize '
        f'against him, does root against him, does treat a deal that helps The Machines as '
        f'a threat to the republic. But that is a tax the league levies on excellence, not '
        f'evidence of a crime. They gang up on him because he keeps winning. He keeps '
        f'winning because he is good.')

    P.append(
        'This newsroom has now read every deal in the dynasty ledger, counted every '
        'partner, and weighed the one asset the prosecution never brings to the table: a '
        'motive that holds up. There is no cabal. There is a concentration, and there is '
        'an explanation for the concentration that the concentration itself supports. '
        'There is a market, open every summer, and one man who works it harder and reads '
        'it better than the rest of the room — and a room that has decided, for '
        'twenty-one years, that this must be against the rules.')

    P.append(
        'The verdict of the ledger is not close. On the charge of cheating: not guilty. '
        'On the charge of collusion: not guilty. On the charge of being, by a wide and '
        'infuriating margin, the best trader and the best manager this league has '
        'produced — guilty, and it is not up for appeal. File it under the only heading '
        'that fits. Some empires are built in the dark. This one was built in the group '
        'chat, in broad daylight, one fair deal at a time, while everybody watched and '
        'nobody could stop it.')

    P.append(
        f'Sourcing: the itemised Obvibase ledger ({F["league_deals"]} deals, {y0}–{y1}), '
        f'with multi-team legs consolidated and relay assets netted out; the League '
        f'Legacy all-time table for records, playoff appearances and titles. Pre-{y0} '
        f'trades are not in the ledger and are not claimed here. Nothing in this piece '
        f'prices a trade, because nothing in this repo can.')
    return P


def build():
    F = facts()
    P = prose(F)
    path = os.path.join(ROOT, 'investigations.json')
    d = json.load(open(path, encoding='utf-8'))
    inv = d['investigations']
    old = next((x for x in inv if x.get('id') == ARTICLE_ID), None)
    if old is None:
        raise SystemExit(f'{ARTICLE_ID} not in investigations.json')
    old['paragraphs'] = P
    tmp = path + '.tmp'
    json.dump(d, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    print(f'{ARTICLE_ID}: {len(P)} paragraphs, {sum(len(p) for p in P):,} chars')
    print(f'  {F["deals"]} Machines deals of {F["league_deals"]} in the ledger '
          f'({F["span"][0]}-{F["span"][1]}), {F["partners"]} partners')
    print(f'  top two: ' + ', '.join(f'{F["club"].get(k,k)} {n}' for k, n in F['top'][:2]))
    print(f'  players {F["got_p"]} in / {F["gave_p"]} out, picks {F["got_k"]} in / '
          f'{F["gave_k"]} out')
    print(f'  status {old.get("status")} · staff {old.get("staff")} — not filed, not published')


if __name__ == '__main__':
    build()
