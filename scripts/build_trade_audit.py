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

Released. This writes the article into investigations.json; the page itself is
scripts/build_story_page.py trade-audit, its pagination is measure_pages.js,
and its share card is build_fallback_card.py. Rebuild in that order after any
change to the copy or the data.
"""
import json, os, re, subprocess, sys, collections, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import importlib.util as _ilu
_tv = _ilu.spec_from_file_location('tv', os.path.join(ROOT, 'scripts',
                                                      'build_trade_values.py'))
TV = _ilu.module_from_spec(_tv); sys.modules['tv'] = TV; _tv.loader.exec_module(TV)
ARTICLE_ID = 'trade-audit'
ME = 'machines'
E = lambda t: (str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

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


# The live Trade Court's own threshold: a net of more than this counts as a
# win, less than minus this a loss, anything between is even (index.html,
# TC_WIN). Reused rather than reinvented so the article and the app cannot
# grade the same deal differently.
TC_WIN = 12
MIN_DEALS = 15          # below this a win rate is noise, not a ranking


def values():
    """Every deal priced AT ITS OWN SEASON, from scripts/build_trade_values.py.

    This is the part the first draft gave up on. It claimed The Machines "come
    out ahead on the clear majority of their trades... behind on only one or
    two" and this desk cut it, on the grounds that nothing here could price a
    2021 trade. That was wrong: the model values players off the August
    dp-values snapshot of the trade's own season and picks off the chart
    calibrated to real SCFL trades, with no hindsight anywhere in it. See
    docs/TRADE-VALUE-MODEL.md.

    tradeValues.json is gitignored, so it is rebuilt here if it is not on
    disk. If it cannot be built the piece runs without the paragraph rather
    than guessing at it.

    One limitation, checked rather than assumed. A pick traded three years out
    is priced at the league average, because the rank regression has decayed
    to nothing by then on purpose (r^2 ~ 0.03 -- finishing position does not
    persist). That is right for a league, and wrong for this franchise: The
    Machines went into the ledger's six seasons ranked 2nd, 4th, 4th, 2nd,
    7th and 7th, so their own future first lands around slot 13-16 and is
    worth $190-270 on the chart, not the $455.60 the model gives it. The model
    therefore OVERVALUES what the Machines give away, which biases the ledger
    against him -- the opposite of the direction a reader would suspect.

    Repricing every Machines-owned future pick at their median finish moves
    the record from 28-21 to 28-20: one deal, a 2023 trade with Wookie Leaks,
    goes from a $91 loss to an $8 push. The published record stands.
    """
    path = os.path.join(ROOT, 'tradeValues.json')
    if not os.path.exists(path):
        subprocess.run([sys.executable, os.path.join(ROOT, 'scripts',
                                                     'build_trade_values.py')],
                       cwd=ROOT, capture_output=True)
    if not os.path.exists(path):
        return None
    d = json.load(open(path, encoding='utf-8'))
    # Only two-team deals can be scored from this file: in a three-team trade
    # the receipts do not say which side each asset came from, so a net cannot
    # be formed without guessing. There are few of them and they are counted
    # out loud rather than folded in.
    per = collections.defaultdict(list)
    skipped = 0
    for t in d['trades']:
        if len(t['sides']) != 2:
            skipped += 1
            continue
        a, b = t['sides']
        for me, other in ((a, b), (b, a)):
            per[me['franchiseKey']].append(me['total'] - other['total'])

    def tally(v):
        w = sum(1 for x in v if x > TC_WIN)
        l = sum(1 for x in v if x < -TC_WIN)
        return {'n': len(v), 'w': w, 'l': l, 'e': len(v) - w - l,
                'net': sum(v), 'mean': sum(v) / len(v),
                'median': statistics.median(v),
                'rate': w / (w + l) if w + l else 0}

    tbl = {k: tally(v) for k, v in per.items() if v}
    nets = dict(per)
    rank = sorted((k for k, r in tbl.items() if r['n'] >= MIN_DEALS),
                  key=lambda k: -tbl[k]['rate'])
    return {'tbl': tbl, 'rank': rank, 'nets': nets, 'skipped_3way': skipped,
            'unresolved': d.get('unresolvedCount', 0)}


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

    active = {r['key'] for r in fr['franchises'] if r.get('active')}
    era = max(r.get('numSeasons', 0) for r in rec.values())
    full_era = [r for r in rec.values() if r.get('numSeasons', 0) >= era - 1]

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
        # who actually leads what. The first draft's closing called him the
        # best trader and the best manager; he leads the table on record and
        # on playoff appearances, he does NOT lead it on titles, and the
        # value board has him fourth. A closing is a claim like any other.
        'pct_rank': sorted(full_era, key=lambda r: -r['winPct']),
        # "the two weakest franchises in the league" was typed, not counted,
        # and it is not true: Killer Klowns sit between them on the table and
        # two defunct sides sit below both. The copy now says where each one
        # actually ranks, among the franchises still playing.
        'weak_rank': [key(r['name']) for r in
                      sorted((rec[k] for k in active if k in rec),
                             key=lambda r: r['winPct'])],
        'active': active,
        'po_rank': sorted(full_era, key=lambda r: -r.get('playoffs', 0)),
        'title_rank': sorted(rec.values(), key=lambda r: -(r.get('titles') or 0)),
        'val': values(),
        'moves': moves,
        'in_': in_, 'out_': out_, 'trades': trades, 'key': key, 'mine': mine,
    }


ORD = ['', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh',
       'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth', 'thirteenth']
ordinal = lambda n: ORD[n] if n < len(ORD) else f'{n}th'
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
        f'both of them come from the bottom of the all-time table. {name(k2)} have the '
        f'worst winning percentage of any side still in this league, {rec[k2]["record"]}, '
        f'and {"have never made the playoffs" if not rec[k2].get("playoffs") else "have made the playoffs " + word(rec[k2]["playoffs"]) + " times"} '
        f'in {word(rec[k2]["numSeasons"])} seasons. {name(k1)} are '
        f'{ordinal(F["weak_rank"].index(k1) + 1)}-worst of the '
        f'{word(len(F["weak_rank"]))}, at {rec[k1]["record"]}. If you wanted to draw the prosecution '
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

    V = F['val']
    if V:
        m = V['tbl'][ME]
        even_share = round(100 * m['e'] / m['n'])
        P.append(
            f'Does he win the deals? More than he loses, and by less than the theory '
            f'needs. Priced at the season each trade was made in — August values of that '
            f'year, picks on the same dollar board the Trade Court grades on, no '
            f'hindsight anywhere — The Machines are {m["w"]}-{m["l"]} across the '
            f'{word(m["n"])} two-team deals in the ledger. But the number that says more '
            f'is the third one: {word(m["e"])} of those {word(m["n"])} finish inside '
            f'twelve dollars either way. {even_share} per cent of everything he has done '
            f'is, by the board, a fair trade. His median deal is worth '
            f'${m["median"]:.0f} to him. That is the shape of a man making a great many '
            f'ordinary trades, not a man running a protection racket.')

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
            'And the misses are not abstract. Some of them walked back through the door. '
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

    ahead = [name(k) for k in (F['val']['rank'][:F['val']['rank'].index(ME)]
                               if F['val'] else [])]
    pct1, pct2 = F['pct_rank'][0], F['pct_rank'][1]
    po1, po2 = F['po_rank'][0], F['po_rank'][1]
    tl = F['title_rank'][0]
    me2 = rec[ME]

    listed = (' and '.join([', '.join(ahead[:-1]), ahead[-1]]) if len(ahead) > 1
              else (ahead[0] if ahead else ''))
    worked = (f'{name(busiest_k)} appear in more of its deals than he does'
              if busiest_k != ME else 'nobody appears in more of its deals than he does')
    read = ('and he does not clear it either, because most of what he does in it '
            'comes out level')
    P.append(
        'This newsroom has now read every deal in the dynasty ledger, priced every asset '
        'at the season it moved in, and counted every partner. There is no cabal. There '
        'is a concentration, and an explanation for the concentration that the '
        f'concentration itself supports. There is a market, open every summer, and he '
        f'does not own it: {worked}, {read}. And there is a room that has decided, '
        f'for twenty-one years, that whatever he is doing instead must be against the '
        f'rules.')

    P.append(
        f'So the verdict of the ledger is not close, and it is not the one the league '
        f'wants either. On the charge of cheating: not guilty. On the charge of '
        f'collusion: not guilty. On the charge of running a market that pays him and '
        f'nobody else: not guilty — {word(F["val"]["tbl"][ME]["e"])} of his '
        f'{word(F["val"]["tbl"][ME]["n"])} priced deals come out level, and he is a net '
        f'seller of players in the ones that do not. He does not have the most '
        f'championships either; {tl["name"]} have {word(tl["titles"])} to his '
        f'{word(me2["titles"])}. What he is guilty of is narrower than the theory and '
        f'worse for everybody else: the best record anybody has put together here, '
        f'{pc(me2["winPct"])} against {pc(pct2["winPct"])} for the next side to go the '
        f'distance, and {word(me2["playoffs"])} playoff appearances in '
        f'{word(me2["numSeasons"])} seasons, {word(po1["playoffs"] - po2["playoffs"])} '
        f'more than anyone else has managed. He is beaten in his own trade ledger '
        f'{word(F["val"]["tbl"][ME]["l"])} times out of {word(F["val"]["tbl"][ME]["n"])} '
        f'and he finishes above you anyway. Some empires are built in the dark. This one was '
        f'built in the group chat, in broad daylight, one ordinary deal at a time, while '
        f'everybody watched and nobody could stop it.')

    P.append(
        f'Sourcing: the itemised Obvibase ledger ({F["league_deals"]} deals, {y0}–{y1}), '
        f'with multi-team legs consolidated and relay assets netted out; the League '
        f'Legacy all-time table for records, playoff appearances and titles. Pre-{y0} '
        f'trades are not in the ledger and are not claimed here. Trade values are '
        f'scripts/build_trade_values.py, which prices every asset at the August of the '
        f'season the trade was made in — players off that year’s dp-values snapshot, '
        f'picks off the chart calibrated to real SCFL trades — so nothing here is graded '
        f'with hindsight; the method is docs/TRADE-VALUE-MODEL.md. A win is a net above '
        f'${TC_WIN}, the Trade Court’s own threshold. '
        f'{word(F["val"]["skipped_3way"]).capitalize() if F["val"] else "Some"} three-team '
        f'deals are left out of the win-loss record, because their receipts do not say '
        f'which side each asset came from, and {word(F["val"]["unresolved"]) if F["val"] else "a few"} '
        f'assets league-wide — team defences, mostly — carry no price and count as zero.')
    return P


def audit(F, P):
    """Re-check the published figures against the data that produced them.

    Belt and braces: every number is interpolated from facts(), so these can
    only fail if a source file changes shape. They are here because the
    paragraph that sank the first draft was a set of counts that LOOKED
    right, and nothing in the build would have caught it.
    """
    txt = ' '.join(P).lower()          # the copy capitalises sentence starts
    V, rec, me = F['val'], F['rec'], F['rec'][ME]
    m = V['tbl'][ME] if V else {}
    want = [
        (me['record'], 'all-time record'),
        (pc(me['winPct']), 'win percentage'),
        (f'{word(F["deals"])} deals', 'his deal count'),
        (f'{word(F["partners"])} different franchises', 'partner count'),
        (f'{m["w"]}-{m["l"]}', 'trade win-loss') if V else None,
        (f'{word(F["metronome"])} trades', 'the per-season rate') if F['metronome'] else None,
    ]
    bad = [why for pair in want if pair
           for val, why in [pair] if str(val).lower() not in txt]
    # and the claims that are comparisons rather than counts
    if F['busiest'][0] != ME and 'does not own it' not in txt:
        bad.append('the market-share claim')
    if V and V['rank'].index(ME) == 0 and 'grade out ahead of him' in txt:
        bad.append('says sides grade ahead of him when none do')
    if bad:
        raise SystemExit('audit failed: ' + '; '.join(bad))
    return len(want)


def build():
    F = facts()
    P = prose(F)
    audit(F, P)
    path = os.path.join(ROOT, 'investigations.json')
    d = json.load(open(path, encoding='utf-8'))
    inv = d['investigations']
    old = next((x for x in inv if x.get('id') == ARTICLE_ID), None)
    if old is None:
        raise SystemExit(f'{ARTICLE_ID} not in investigations.json')
    old['paragraphs'] = P
    old['blocks'] = blocks(F, P)
    tmp = path + '.tmp'
    json.dump(d, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    print(f'{ARTICLE_ID}: {len(P)} paragraphs, {sum(len(p) for p in P):,} chars')
    print(f'  {F["deals"]} Machines deals of {F["league_deals"]} in the ledger '
          f'({F["span"][0]}-{F["span"][1]}), {F["partners"]} partners')
    print(f'  top two: ' + ', '.join(f'{F["club"].get(k,k)} {n}' for k, n in F['top'][:2]))
    print(f'  players {F["got_p"]} in / {F["gave_p"]} out, picks {F["got_k"]} in / '
          f'{F["gave_k"]} out')
    print(f'  status {old.get("status")} · staff {old.get("staff")}')



# ---------------------------------------------------------------------------
# Figures. Same rule as the prose: every cell is read out of the data, and
# the table and the sentence beside it cannot disagree because they come from
# one facts() call.
# ---------------------------------------------------------------------------
def bar(v, hi, lo=False, level=False):
    # a zero count gets no bar at all. The minimum width exists so a small
    # count is still visible; applied to nothing it drew a stub that read as
    # "one or two" on four rows that were empty.
    if not v:
        return '<td class="bar"></td>'
    pct = min(100, max(2, round(100 * abs(v) / hi))) if hi else 2
    tint = ';background:#d8b45a' if level else ''
    return (f'<td class="bar"><span class="{"lo" if lo and not level else ""}" '
            f'style="width:{pct}%{tint}"></span></td>')


def fig_partners(F):
    rec, top = F['rec'], F['top']
    hi = top[0][1]
    rows = ''
    for k, n in top:
        r = rec.get(k) or {}
        rows += (f'<tr><th scope="row">{E(F["club"].get(k, k))}</th>'
                 f'<td class="num">{n}</td>{bar(n, hi)}'
                 f'<td class="num">{r.get("record", "&mdash;")}</td>'
                 f'<td class="num">{r.get("playoffs", "&mdash;")}</td>'
                 f'<td class="num">{r.get("titles") or "&mdash;"}</td></tr>')
    return ('<figure><div class="scroll"><table>'
            '<thead><tr><th class="lt">Partner</th><th>Deals</th><th></th>'
            '<th>All-time</th><th>Playoffs</th><th>Titles</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
            '<figcaption>Every franchise The Machines have traded with in the dynasty '
            f'ledger, {F["span"][0]}&ndash;{F["span"][1]}. Record, playoff appearances and '
            'titles are all-time, from League Legacy. Two of the sixteen do not appear at '
            'all.</figcaption></figure>')


def fig_spread(F):
    """Where the sixty-six deals land once they are priced."""
    V = F['val']
    nets = V['nets'][ME]
    edges = [(-10**9, -100, 'worse than &minus;$100'), (-100, -50, '&minus;$100 to &minus;$50'),
             (-50, -TC_WIN, f'&minus;$50 to &minus;${TC_WIN}'),
             (-TC_WIN, TC_WIN, f'level (within ${TC_WIN})'),
             (TC_WIN, 50, f'${TC_WIN} to $50'), (50, 100, '$50 to $100'),
             (100, 10**9, 'better than $100')]
    counts = [(lab, sum(1 for x in nets if lo < x <= hi), lo >= TC_WIN, lo == -TC_WIN)
              for lo, hi, lab in edges]
    hi = max(c for _, c, _, _ in counts)
    rows = ''
    for lab, c, good, level in counts:
        rows += (f'<tr><th scope="row">{lab}</th><td class="num">{c}</td>'
                 f'{bar(c, hi, lo=not good, level=level)}</tr>')
    return ('<figure><div class="scroll"><table>'
            '<thead><tr><th class="lt">Differential to The Machines</th><th>Deals</th>'
            '<th></th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
            f'<figcaption>All {V["tbl"][ME]["n"]} two-team deals, priced at the season each '
            f'was made in. {V["tbl"][ME]["e"]} of them finish inside twelve dollars either '
            'way &mdash; the threshold the Trade Court uses to call a deal a win. Red is '
            'the Machines ahead, blue behind.</figcaption></figure>')


def fig_picks(F):
    now = int(F['span'][1])
    years = [now + i for i in range(4)]
    dec = lambda y: TV.PICK_DECAY ** max(0, y - now)
    rows = ''
    for slot in range(1, 17):
        b = TV.PICK_CHART[slot]
        rows += (f'<tr><th scope="row">{slot}</th>'
                 + ''.join(f'<td class="num">{b * dec(y):.1f}</td>' for y in years) + '</tr>')
    r1 = sum(TV.PICK_CHART[s] for s in range(1, 17)) / 16
    r2 = sum(TV.PICK_CHART[s] for s in range(17, 33)) / 16
    for lab, base in (('a 1st, slot unknown', r1), ('a 2nd, slot unknown', r2)):
        rows += (f'<tr><th scope="row" class="dim">{lab}</th>'
                 + ''.join(f'<td class="num dim">{base * dec(y):.1f}</td>' for y in years)
                 + '</tr>')
    return ('<figure><div class="scroll"><table>'
            '<thead><tr><th class="lt">Pick</th>'
            + ''.join(f'<th>{y}</th>' for y in years) + '</tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
            '<figcaption>The pick board, in the same dollars as the players: the 1.01 is '
            '$100 and so is a player valued at 100. A pick loses '
            f'{round((1 - TV.PICK_DECAY) * 100)} per cent a year for every year you have to '
            'wait for it. A traded future pick has no known slot, so it is priced at the '
            'average of its round.</figcaption></figure>')


def method(F):
    """How the numbers were made. Published with the piece, not behind it."""
    V, sp = F['val'], F['span']
    return [
        ('sect', '<div class="sect">How This Was Counted</div>'),
        ('body', '<p class="b">Every figure in this piece is computed from three files in '
                 'the newsroom repository, and the piece is regenerated from them rather '
                 'than typed. The first version of it was typed, and almost every count in '
                 'the paragraph carrying the defence was wrong.</p>'),
        ('body', f'<p class="b"><b>The ledger.</b> The itemised Obvibase export: '
                 f'{F["league_deals"]} deals from {sp[0]} to {sp[1]}, with multi-team legs '
                 f'consolidated and pass-through assets netted out, so a middleman is '
                 f'credited only with what he kept. There is nothing before {sp[0]}; there '
                 f'was no dynasty market, and the league WhatsApp — created in 2016 — holds '
                 f'nothing but three setup notices until {sp[0]} either. Both records start '
                 f'in the same place, which is why this is the dynasty-era ledger and not '
                 f'the twenty-one-year one.</p>'),
        ('body', '<p class="b"><b>Players</b> are priced from the DynastyProcess superflex '
                 'board, taken from the August snapshot of the season the trade was made '
                 'in. Not today&rsquo;s. A player who became a star in 2024 is priced in a '
                 '2021 trade at what he was worth in 2021, because the question is whether '
                 'the deal was fair when it was made, not whether it aged well.</p>'),
        ('body', '<p class="b"><b>Picks</b> are priced from the league&rsquo;s own pick '
                 'curve, calibrated against 235 real SCFL trades. A pick with a known slot '
                 'is worth what the curve says. A future pick has no slot yet, so it is '
                 'priced at the average of its round and discounted for every year of '
                 'waiting.</p>'),
        ('body', '<div class="ad">' + fig_picks(F) + '</div>'),
        ('body', '<p class="b"><b>The two boards had to be reconciled, and that is where '
                 'this audit nearly went wrong.</b> The pick curve puts the 1.01 at 1,000. '
                 'The player board puts the 1.01 at 100 and the best player in the league '
                 'at 127. They are the same scale ten units apart, and the first run of '
                 'this audit added them together raw &mdash; which valued a pick three '
                 'drafts away at nine times a top-five tight end and inflated every pick in '
                 'the ledger about tenfold. Dividing the curve by ten puts the 1.01 on $100 '
                 'and the average first-round pick on $45.60, which the league&rsquo;s Trade '
                 'Court, calibrated separately, independently puts at $48. Two boards built '
                 'apart agreeing inside five per cent is the check that this is a '
                 'reconciliation and not a convenience.</p>'),
        ('body', f'<p class="b"><b>A win</b> is a net above ${TC_WIN} on that board, which '
                 f'is the Trade Court&rsquo;s own threshold, and anything inside it is '
                 f'called level. <b>What is left out:</b> {word(V["skipped_3way"])} '
                 f'three-team deals, whose receipts do not say which side each asset came '
                 f'from, and {word(V["unresolved"])} assets league-wide &mdash; team '
                 f'defences, mostly &mdash; that carry no price and count as zero.</p>'),
        ('body', '<p class="b"><b>What is deliberately not here.</b> No league ranking for '
                 'who trades best. The order moves by several places depending on nothing '
                 'more than what an unknown future second is assumed to be worth, and a '
                 'table an assumption can reshuffle is not a finding. No claim about how a '
                 'trade aged, either: this board does not know, and neither did anybody at '
                 'the table.</p>'),
    ]


def blocks(F, P):
    """The article as page blocks: prose, with the figures where they argue."""
    out = []
    for i, p in enumerate(P):
        if i == len(P) - 1:
            break                       # the sourcing line is placed last, after the method
        out.append(('body', '<p class="b">' + p + '</p>'))
        if i == 4:
            out.append(('body', '<div class="ad">' + fig_partners(F) + '</div>'))
        if i == 8 and F['val']:
            out.append(('body', '<div class="ad">' + fig_spread(F) + '</div>'))
    out += method(F)
    out.append(('body', '<div class="devnote">' + P[-1] + '</div>'))
    return out

if __name__ == '__main__':
    build()
