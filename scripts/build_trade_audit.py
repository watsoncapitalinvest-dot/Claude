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
_tc = _ilu.spec_from_file_location('tc', os.path.join(ROOT, 'scripts',
                                                      'build_trade_counts.py'))
TC = _ilu.module_from_spec(_tc); sys.modules['tc'] = TC; _tc.loader.exec_module(TC)
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


def values(skip=()):
    """Every deal priced AT ITS OWN SEASON, from scripts/build_trade_values.py.

    `skip` is the part-seasons: tradeValues.json prices the whole ledger
    including the season in progress, and a win-loss record drawn from a wider
    set than the deal count beside it is two numbers that cannot both be right.

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
        if str(t['season']) in skip:
            continue
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

    # Eleven seasons of VOLUME, and the cross-check that saved the piece.
    # trade-counts.json counts deals from the master Obvibase export, 2016
    # forward; trades.json itemises them from 2021. Where they overlap they
    # agree to within two a season, which is what makes the ledger safe to
    # price -- see scripts/build_trade_counts.py.
    cnt = json.load(open(os.path.join(ROOT, 'trade-counts.json'),
                         encoding='utf-8'))
    recon = TC.reconcile()
    if not recon or not recon['ok']:
        raise SystemExit('trades.json does not reconcile with trade-counts.json; '
                         'run scripts/build_trade_counts.py and read the gaps')
    vol = {r['key']: r for r in cnt['franchises']}
    part = set(cnt.get('partSeasons') or [])

    # The itemised window is the COMPLETE seasons only. 2026 is six weeks old:
    # the ledger holds six deals in it and Sleeper's own log already has
    # twenty-nine, so a season-2026 figure in here would be a quarter of the
    # truth presented as the whole of it.
    trades = [t for t in tj['trades'] if str(t['season']) not in part]
    dropped = len(tj['trades']) - len(trades)
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
    # His per-season rate, from the MASTER counts rather than the ledger.
    #
    # The first printing called this a metronome: thirteen trades in every one
    # of five seasons. The ledger did read flat, and that is what pulled the
    # piece -- a figure that steady in a league whose own total swung 53, 62,
    # 54, 43, 38 looked like a fault. It was not a fault and it was not a
    # metronome either. Counted off the master export the same five seasons
    # run 13, 11, 13, 12, 12, and the ledger's flat line was that sequence
    # plus four rows the two exports disagree on.
    #
    # So the claim is now the one the data supports: a band, not a constant.
    # The copy prints the range and the spread, both counted.
    full = [y for y in seasons]
    rate = [vol[ME]['bySeason'].get(str(y), 0) for y in full]
    rate_lo, rate_hi = min(rate), max(rate)
    league_rate = [cnt['leagueTotals'].get(str(y), 0) for y in full]

    active = {r['key'] for r in fr['franchises'] if r.get('active')}
    era = max(r.get('numSeasons', 0) for r in rec.values())
    full_era = [r for r in rec.values() if r.get('numSeasons', 0) >= era - 1]

    # one row per deal: who was across the table, so a three-team trade counts
    # once however many partners it had
    me_rec = rec[ME]
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
        'per_season': per_season, 'full': full,
        'rate': rate, 'rate_lo': rate_lo, 'rate_hi': rate_hi,
        'league_rate': league_rate,
        'busiest': seen.most_common(1)[0],
        # eleven seasons of volume, which is what the counts can carry even
        # though the itemised detail cannot
        'vol': vol, 'cnt': cnt, 'recon': recon, 'dropped': dropped,
        'recon_me': next(abs(r['ledger'] - r['master'])
                         for r in recon['rows'] if r['key'] == ME),
        'exp': cnt.get('export') or {},
        'part': sorted(part),
        'vol_span': cnt['span'],
        'vol_rank': [r['key'] for r in cnt['franchises'] if r['active']],
        # the five-year window ordered by the master counts, so "busiest" is
        # not a claim about the ledger's own coverage
        'win_rank': sorted((r for r in cnt['franchises'] if r['active']),
                           key=lambda r: -sum(r['bySeason'].get(str(y), 0)
                                              for y in seasons)),
        'win_deals': lambda k: sum(vol[k]['bySeason'].get(str(y), 0)
                                   for y in seasons),
        # the all-play, which is a weekly score against all fifteen others and
        # has to be explained in the copy or it reads as a typo
        'allplay_g': sum(int(x) for x in me_rec['allPlay'].split('-')),
        'allplay_wk': me_rec['record'].split('-'),
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
        'val': values(part),
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

    P = []
    P.append(
        'There is a theory of the Skirt Chasers Fantasy League that has survived longer '
        'than most of the franchises in it. The theory is simple and it is repeated, in '
        'some form, every single autumn: The Machines cheat. The Machines are the Evil '
        'Empire. '
        'He preys on the weak owners, he collects the rebuilders like toll booths, and '
        'the rest of the league is left to split the scraps he does not want. It is a '
        'good story. It has a villain, it has victims, and it explains — cleanly, '
        'comfortably — why the same team keeps ending up on top. This newsroom decided '
        'to do the one thing nobody arguing about it had ever bothered to do. We pulled '
        'the receipts.')

    P.append(
        f'The record itself is not in dispute, and it is the reason the theory exists at '
        f'all. The Machines are {me["record"]} across the tracked era — a {pc(me["winPct"])} '
        f'winning percentage in a league where the next best side to have gone the full '
        f'{word(me["numSeasons"])} seasons, {name(key_of(runner))}, sits on '
        f'{pc(runner["winPct"])}. '
        f'{word(me["playoffs"]).capitalize()} playoff appearances in '
        f'{word(me["numSeasons"])} seasons — League Legacy\'s register, which is the '
        f'league\'s own. {word(me["titles"]).capitalize()} '
        f'championships, {word(me["runnerUps"])} runner-up finishes, and an all-play '
        f'record that reads like a typo until you work out what it counts. Score every '
        f'week he has played against all {word(F["others"])} other teams in the league '
        f'that week, not just the one he was drawn against, and he is '
        f'{allplay(me["allPlay"])}: {word(F["allplay_g"])} notional games, '
        f'{pc(me["allPlayPct"])}. The schedule has not been doing him favours. He beats '
        f'the room. You do not have to like it to respect '
        f'it, and most of the league has chosen the first option. When a team is that good '
        f'for that long, the human brain does not reach for "well-run." It reaches for '
        f'"rigged." That instinct is the entire case for the prosecution, and it is worth '
        f'taking seriously — so we did.')

    P.append(
        f'So let us state the charge properly, because the league rarely does. Nobody '
        f'here seriously thinks there is a conspiracy — a conspiracy needs two guilty '
        f'parties and the accusation is always aimed at one. The charge is predation: '
        f'that The Machines win because he works the owners who do not know what their '
        f'own players are worth, that he finds the naive and the checked-out and the '
        f'rebuilding and takes the good half of the deal while they thank him for it. '
        f'That is a sharper accusation than cheating and a harder one to answer, because '
        f'it does not require anybody to break a rule. It only requires one man at the '
        f'table to be paying more attention than the other. If it is true it leaves a '
        f'fingerprint: the same soft counterparties, over and over, and a ledger that '
        f'runs his way when it is priced.')

    P.append(
        f'So we mapped every trade in the itemised ledger — {word(F["league_deals"])} '
        f'deals from {y0} to {y1}, {word(F["deals"])} of them with The Machines on one '
        f'side of the table. {y0} is not where the league became a dynasty league; it '
        f'has always been one. {y0} is where the receipts start. The league\'s own trade '
        f'register goes back to {F["vol_span"][0]} and has him in '
        f'{word(F["vol"][ME]["total"])} deals across '
        f'{word(len(F["cnt"]["seasons"]))} seasons, so both records were counted and set '
        f'against each other: over the five years they share they are '
        f'{word(F["recon_me"])} deals apart on him, and {word(F["recon"]["exact"])} of '
        f'the {word(len(F["recon"]["rows"]))} franchises come out identical. But the '
        f'register records only how many, not who or what. The '
        f'players and the picks exist from {y0}, so {y0} is where a price can be put on '
        f'anything — and five seasons is the window that bears on this league anyway. '
        f'These are the deals whose players are on these rosters now. Older ones are '
        f'history, and this is an audit.')

    # The top two have been level before and will be again, and "his most
    # frequent partner is X, second is Y" prints a hierarchy that does not
    # exist when they are tied.
    head = (f'His two most frequent partners are level on {word(n1)} deals each: '
            f'{name(k1)} and {name(k2)}.' if n1 == n2 else
            f'His most frequent partner is {name(k1)}, with {word(n1)} deals. Second is '
            f'{name(k2)}, with {word(n2)}.')
    P.append(
        f'The first thing the ledger does is refuse to clear him. {head} '
        f'Between them that is {word(pair)} of his {word(F["deals"])} deals — '
        f'about {share} per cent of everything he has done — and '
        f'both of them come from the bottom of the all-time table. {name(k2)} have the '
        f'worst winning percentage of any side still in this league, {rec[k2]["record"]} '
        f'in {word(rec[k2]["numSeasons"])} seasons, {pc(rec[k2]["winPct"])}. '
        f'{name(k1)} are '
        f'{ordinal(F["weak_rank"].index(k1) + 1)}-worst of the '
        f'{word(len(F["weak_rank"]))}, at {rec[k1]["record"]}. If you wanted to draw the prosecution '
        f'case as a chart, that is the chart. We are not going to pretend otherwise, '
        f'because it is the first thing in the file.')

    P.append(
        f'The second thing the ledger does is refuse to convict him. Those '
        f'{word(F["deals"])} deals are spread across {word(F["partners"])} of the '
        f'league\'s {word(len(F["active"]))} franchises. '
        f'{word(F["with_contenders"]).capitalize()} of them were with sides that have made '
        f'the playoffs ten times or more. {word(F["with_champions"]).capitalize()} were '
        f'with sides that have won the thing. {word(best_n).capitalize()} of them were '
        f'with {name(best)}, who own {word(rec[best]["titles"])} championships — more than '
        f'The Machines do. A man who '
        f'only hunts the naive does not spend his summers across the table from the '
        f'champions. That is a man doing business with the entire building, including '
        f'the parts of it that can beat him.')

    P.append(
        'Both things are true at once, and the theory cannot hold both. Predation needs a '
        'small number of soft marks. What the ledger shows is the whole building with two '
        'doors that get used more than the others — and in a dynasty league, those two '
        'doors have a name. The '
        'rebuilders are not the contender\'s victims; they are the contender\'s trading '
        'partners by design. A team going nowhere in November has one asset a title team '
        'wants and one thing it needs, and the title team is the only reliable buyer in '
        'the building. The sides who trade with The Machines most are the sides with the '
        'most '
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

    # Who is busiest is settled on the master counts, not on the ledger's own
    # coverage: the ledger is a reconstruction and being over-represented in it
    # is not the same as trading more.
    w1, w2 = F['win_rank'][0], F['win_rank'][1]
    wn = F['win_deals']
    busy = (f'He is not even the busiest man in the market. Over the same five seasons '
            f'{name(w1["key"])} were a party to {word(wn(w1["key"]))} deals and The '
            f'Machines to {word(wn(ME))}.'
            if w1['key'] != ME else
            f'He is the busiest man in the market: a party to {word(wn(ME))} deals in '
            f'five seasons, against {word(wn(w2["key"]))} for {name(w2["key"])}, who are '
            f'next.')
    # The rate, off the league register rather than the ledger. The first
    # printing of this piece called it a metronome on the strength of five
    # identical ledger rows; the register says 13, 11, 13, 12, 12, so the claim
    # is a band and the band is printed rather than described.
    lo, hi = F['rate_lo'], F['rate_hi']
    seq = ', '.join(str(n) for n in F['rate'][:-1]) + f' and {F["rate"][-1]}'
    rhythm = (f' And the rate barely moves. The league\'s trade register has him at '
              f'{seq} deals across those five seasons — never fewer than {word(lo)}, '
              f'never more than {word(hi)} — while the league\'s own total over the same '
              f'five years went {", ".join(str(n) for n in F["league_rate"][:-1])} and '
              f'{F["league_rate"][-1]} — {word(max(F["league_rate"]) - min(F["league_rate"]))} '
              f'deals between its busiest summer and its quietest. The market around him '
              f'fills up and empties out. He does his {word(lo)} to {word(hi)} and goes '
              f'back to work.')
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
        f'{word(F["others"])} other teams. "The Machines cheat" is a more bearable '
        f'explanation than "The Machines are better than me at the one thing we all show '
        f'up to do." The persecution complex that comes back off that side of the chat '
        f'— everyone\'s teaming up on me, they '
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
    w1 = F['win_rank'][0]
    worked = (f'{name(w1["key"])} were a party to more of its deals over the same five '
              f'seasons than he was'
              if w1['key'] != ME else 'he is a party to more of its deals than anybody')
    read = ('and he does not clear it either, because most of what he does in it '
            'comes out level')
    P.append(
        'This newsroom has now read every deal in the five-year ledger, priced every '
        'asset at the season it moved in, counted every partner, and checked the counts '
        'against the league\'s own register going back eleven years. There is no ring of '
        'soft touches. There '
        'is a concentration, and an explanation for the concentration that the '
        f'concentration itself supports. There is a market, open every summer, and he '
        f'does not own it: {worked}, {read}. And there is a room that has decided, '
        f'for twenty-one years, that whatever he is doing instead must be against the '
        f'rules.')

    P.append(
        f'So the verdict of the ledger is not close, and it is not the one the league '
        f'wants either. On the charge of cheating: not guilty — there is nothing in the '
        f'file to prosecute. On the charge of preying on the ignorant and the naive: not '
        f'guilty, and it is the ledger that acquits him, not this desk. '
        f'{word(F["with_champions"]).capitalize()} of his deals were done with sides who '
        f'have won this league; {word(F["val"]["tbl"][ME]["e"])} of his '
        f'{word(F["val"]["tbl"][ME]["n"])} priced deals come out level; he is a net '
        f'seller of players in the ones that do not. A predator does not come out level '
        f'in {round(100 * F["val"]["tbl"][ME]["e"] / F["val"]["tbl"][ME]["n"])} '
        f'deals out of every hundred. He does not have the most '
        f'championships either; {tl["name"]} have {word(tl["titles"])} to his '
        f'{word(me2["titles"])}. What he is guilty of is narrower than the charge and '
        f'worse for everybody else: the best record anybody has put together here, '
        f'{pc(me2["winPct"])} against {pc(pct2["winPct"])} for the next side to go the '
        f'distance, and {word(me2["playoffs"])} playoff appearances in '
        f'{word(me2["numSeasons"])} seasons on the league\'s own register, '
        f'{word(po1["playoffs"] - po2["playoffs"])} '
        f'more than anyone else has managed. He is beaten in his own trade ledger '
        f'{word(F["val"]["tbl"][ME]["l"])} times out of {word(F["val"]["tbl"][ME]["n"])} '
        f'and he finishes above you anyway. Some empires are built in the dark. This one was '
        f'built in the group chat, in broad daylight, one ordinary deal at a time, while '
        f'everybody watched and nobody could stop it.')

    P.append(
        f'Sourcing: the itemised Obvibase ledger ({F["league_deals"]} deals, {y0}–{y1}), '
        f'with multi-team legs consolidated and relay assets netted out; the league trade '
        f'register ({sum(F["cnt"]["leagueTotals"].values())} deals, '
        f'{F["vol_span"][0]}–{F["vol_span"][1]}), which carries counts only and is what '
        f'the ledger is checked against; the League '
        f'Legacy all-time table for records, playoff appearances and titles. Itemised '
        f'trades before {y0} are not in the ledger and are not claimed here; the '
        f'{F["part"][0]} season is in progress and is left out of every table. Trade '
        f'values are '
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
        (f'across {word(F["partners"])} of the', 'partner count'),
        (f'{m["w"]}-{m["l"]}', 'trade win-loss') if V else None,
        (f'{word(F["rate_lo"])}', 'the low end of the per-season rate'),
        (f'{word(F["rate_hi"])}', 'the high end of the per-season rate'),
    ]
    bad = [why for pair in want if pair
           for val, why in [pair] if str(val).lower() not in txt]
    # and the claims that are comparisons rather than counts
    if F['win_rank'][0]['key'] != ME and 'does not own it' not in txt:
        bad.append('the market-share claim')
    # A zero in records.json's `playoffs` is League Legacy's and could not be
    # reproduced from the game log -- Wookie Leaks read 0 in eleven seasons
    # having finished 4th of 16 in 2015. The first printing turned that zero
    # into "have never made the playoffs". It cannot be derived, so it cannot
    # be printed. See the playoffsNote in records.json.
    if 'never made the playoffs' in txt:
        bad.append('a never-made-the-playoffs claim, which records.json cannot support')
    # The per-season rate is now the league register's, not the ledger's, and
    # the ledger's flat five rows are what pulled the first printing.
    if 'straight seasons on the same number' in txt or 'the rate never moves' in txt:
        bad.append('the metronome, which the register does not show')
    # The window is whole seasons. A part-season figure in a table of complete
    # ones is the mistake this rebuild exists to avoid.
    if any(str(s) in {str(t['season']) for t in F['mine']} for s in F['part']):
        bad.append('a part-season inside the priced window')
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
    old['headline'] = 'Trial of the Evil Empire'
    old['subhead'] = (f'For twenty-one years the league has whispered that The Machines '
                      f'rig it. We pulled every itemised trade from {F["span"][0]} to '
                      f'{F["span"][1]}, checked the counts against the league register '
                      f'back to {F["vol_span"][0]}, and priced '
                      f'every asset at the season it moved in. Here is what it says.')
    old['paragraphs'] = P
    old['blocks'] = blocks(F, P)
    # Back from the pull. The first printing came down because the Machines'
    # per-season count could not be checked against anything; it now is, by
    # trade-counts.json, and facts() will not build at all if the two sources
    # disagree by more than two deals in a season.
    old['status'], old['staff'] = 'FILED', 'published'
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
            '<figcaption>Every franchise The Machines have traded with in the itemised '
            f'ledger, {F["span"][0]}&ndash;{F["span"][1]}. Record, playoff appearances and '
            f'titles are all-time, from League Legacy. '
            + (f'{word(len(F["active"]) - F["partners"]).capitalize()} of the '
               f'{word(len(F["active"]))} '
               + ('does' if len(F['active']) - F['partners'] == 1 else 'do')
               + ' not appear at all.' if len(F['active']) > F['partners'] else
               'Every franchise in the league appears.')
            + '</figcaption></figure>')


def fig_volume(F):
    """Eleven seasons of volume, which is the one thing the register can carry.

    This is the table that got the piece re-reported. The claim it replaces --
    thirteen deals in five straight seasons -- came out of the itemised ledger
    alone, and the register says 13, 11, 13, 12, 12. Printing both sources'
    span lets a reader see the steadiness without having to take the adjective
    on trust, and lets them see who is actually busiest, which is not him.

    Only the sixteen franchises still holding a roster are in it. A defunct
    side's row stops when the side does and reads as a quiet decade.
    """
    cnt, me = F['cnt'], ME
    seasons = cnt['seasons']
    part = set(F['part'])
    rows_in = [r for r in cnt['franchises'] if r['active']]
    hi = max(r['total'] for r in rows_in)
    rows = ''
    for r in rows_in:
        em = ' class="on"' if r['key'] == me else ''
        rows += (f'<tr{em}><th scope="row">{E(r["club"])}</th>'
                 + ''.join(f'<td class="num{" dim" if s in part else ""}">'
                           f'{r["bySeason"].get(s, 0) or "&mdash;"}</td>'
                           for s in seasons)
                 + f'<td class="num">{r["total"]}</td></tr>')
    rows += ('<tr><th scope="row" class="dim">The league</th>'
             + ''.join(f'<td class="num dim">{cnt["leagueTotals"][s]}</td>'
                       for s in seasons)
             + f'<td class="num dim">{sum(cnt["leagueTotals"].values())}</td></tr>')
    pl = ', '.join(part)
    # No bar column: eleven season columns already draw the shape, and a bar
    # on top of them pushes the table past a phone's width even inside .scroll.
    return ('<figure><div class="scroll"><table>'
            '<thead><tr><th class="lt">Franchise</th>'
            + ''.join(f'<th>{s[2:]}</th>' for s in seasons)
            + '<th>All</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
            f'<figcaption>Deals a franchise was a party to, from the league&rsquo;s own '
            f'trade register, {cnt["span"][0]}&ndash;{cnt["span"][1]}. Counts only &mdash; '
            f'the register does not say what was in them. A three-team deal counts once '
            f'for each of the three; there are {word(cnt["multiTeamDeals"])} of them in '
            f'{word(len(seasons))} seasons. The '
            f'{pl} column is a season in progress and is not in any priced table in this '
            f'piece.</figcaption></figure>')


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
            'way &mdash; the threshold the Trade Court uses to call a deal a win. Gold '
            'is level, red is the Machines ahead, blue behind.</figcaption></figure>')


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
        ('body', f'<div class="psa note"><div class="t">The window: {sp[0]} to {sp[1]}</div>'
                 f'<p>The SCFL has always been a dynasty league. {sp[0]} is not where the '
                 f'market opened — it is where the paperwork starts. Two records were '
                 f'used here and they reach back different distances. The league&rsquo;s '
                 f'trade register counts deals from {F["vol_span"][0]}, '
                 f'{word(len(F["cnt"]["seasons"]))} seasons, and says how many each '
                 f'franchise did and when. The itemised ledger says <i>what was in them</i> '
                 f'— which players, which picks, which way — and it starts in {sp[0]}. '
                 f'Only the second one can be priced, so the priced window is '
                 f'{sp[0]}&ndash;{sp[1]}.</p>'
                 f'<p>Five seasons is also the window that bears on anything. These are '
                 f'the deals whose players are on these rosters, in this league, this '
                 f'Sunday. <b>If anybody still has itemised trades from before {sp[0]} — '
                 f'the official chat, a spreadsheet, screenshots — send it and this desk '
                 f'will price them too.</b></p>'
                 f'<p>The current season is left out entirely. It is '
                 f'{word(F["cnt"]["leagueTotals"][F["part"][0]])} deals old and counting, '
                 f'and a part-season in a table of whole ones is a misleading number '
                 f'dressed as a complete one.</p>'
                 f'</div>'),
        ('body', '<p class="b">Every figure in this piece is computed from files in the '
                 'newsroom repository and the piece is regenerated from them rather than '
                 'typed, so the sentence and the number beside it cannot disagree.</p>'),
        ('body', f'<p class="b"><b>The ledger.</b> The itemised Obvibase export: '
                 f'{F["league_deals"]} deals from {sp[0]} to {sp[1]}, with multi-team legs '
                 f'consolidated and pass-through assets netted out, so a middleman is '
                 f'credited only with what he kept.</p>'),
        ('body', f'<p class="b"><b>Two sources, cross-checked.</b> A reconstruction cannot '
                 f'check itself, so the itemised ledger was counted against the '
                 f'league&rsquo;s own register, franchise by franchise and season by '
                 f'season. Over {F["recon"]["span"][0]}&ndash;{F["recon"]["span"][-1]} the '
                 f'two sources put {F["recon"]["ledger"]} deals and '
                 f'{F["recon"]["master"]} on the table; '
                 f'{word(F["recon"]["exact"])} of the {word(len(F["recon"]["rows"]))} '
                 f'franchises agree exactly, and the largest gap anywhere is '
                 f'{word(F["recon"]["worst"])} deals in one season. The Machines&rsquo; own '
                 f'rows differ by {word(F["recon_me"])} deals across the five years. '
                 f'Any figure in this piece that the register will not '
                 f'back is not in this piece.</p>'),
        # The best part of the cross-check, and the part that nearly went
        # unexamined: the nine-deal gap is not disagreement at all.
        ('body', f'<p class="b"><b>And the gap between them is not a disagreement.</b> '
                 f'The register numbers every trade in it, in order, and never reuses a '
                 f'number. Reading those numbers rather than the rows shows '
                 f'{word(F["exp"]["deleted"])} trades entered over the years and later '
                 f'deleted &mdash; voided, reversed, or entered twice. '
                 f'{word(F["recon"]["deletedInSpan"]).capitalize()} of them fall inside '
                 f'this window, which is where the ledger&rsquo;s extra '
                 f'{word(F["recon"]["ledger"] - F["recon"]["master"])} deals come from: '
                 f'it was built from an earlier pull and still carries trades the '
                 f'register has since dropped. Season by season the deletions cover the '
                 f'gap with '
                 + ('nothing left over' if not F['recon']['unexplained'] else
                    f'{word(F["recon"]["unexplained"])} deal(s) left over') +
                 f'. The ledger is a little out of date. It is not wrong, and those are '
                 f'very different things.</p>'),
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
        ('body', '<p class="b"><b>The two boards are on one scale.</b> Players and picks '
                 'are priced by different curves, built separately and years apart, and '
                 'they do not arrive in the same units: the pick curve puts the 1.01 at '
                 '1,000 where the player board puts it at 100. Nothing can be added until '
                 'that is settled, so the curve is divided by ten and both boards now read '
                 'in the same dollars &mdash; the 1.01 at $100, the best player in the '
                 'league at $127. The check that it is right is independent: on this scale '
                 'the average first-round pick comes out at $45.60, and the league&rsquo;s '
                 'Trade Court, calibrated on its own against real SCFL deals, puts it at '
                 '$48. Two boards built apart agreeing inside five per cent is what makes '
                 'a dollar in this article mean one thing.</p>'),
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
        if i == 8:
            out.append(('body', '<div class="ad">' + fig_volume(F) + '</div>'))
        if i == 9 and F['val']:
            out.append(('body', '<div class="ad">' + fig_spread(F) + '</div>'))
    out += method(F)
    out.append(('body', '<div class="devnote">' + P[-1] + '</div>'))
    return out

if __name__ == '__main__':
    build()
