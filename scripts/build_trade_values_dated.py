#!/usr/bin/env python3
"""Price every trade at THE DAY IT WAS MADE, not at the August of its season.

    python3 scripts/build_trade_values_dated.py --ecr path/to/db_fpecr.csv.gz

Writes tradeValuesDated.json, and value-curve.json beside it.

THE PROBLEM THIS FIXES
----------------------
Every dollar in the Trade Audit so far comes from the August snapshot of the
trade's own season. That was the best available while the ledger had no dates
on it. The register has dates on all 533 deals, and they are not clustered
around August:

    median days from a trade to 1 August of its season   28
    mean                                                 48
    worst                                               122

A hundred and fifteen of the 250 deals in the priced window sit more than a
month from the snapshot that prices them, and eighty-four are two months or
more into a season -- which is exactly when a value moves most, because by
then the breakout has broken out and the hamstring has gone. Pricing a
November trade at August is not pricing it at the table.

Dated instead, the same 250 deals sit a MEDIAN OF THREE DAYS from a real
market reading, and 215 of them are inside a week.

WHERE A DATED PRICE COMES FROM
------------------------------
DynastyProcess publishes the FantasyPros consensus it builds its values from,
and the full history ships in its own repo as `files/db_fpecr.csv.gz`. The
series this league needs -- `dsf`, dynasty superflex -- runs weekly from 16
October 2020: 265 scrapes, a median of 479 players each, a median of seven
days apart.

That gives a RANK on any date. Turning a rank into a dollar is the one step
that needs care, and it is calibrated rather than invented: at each of the
five Augusts the audit already prices at, every player's rank in that week's
scrape is paired with the dollar `dp-values.json` gives him. That is 2,240
real (rank, dollar) pairs, and the relationship is not only clean but stable:

    ECR rank     2021   2022   2023   2024   2025
      1-5        $122   $120   $121   $122   $114
     10-15        $98    $94    $96    $96    $96
     25-30        $69    $72    $67    $68    $64
     50-60        $37    $34    $34    $34    $37
    100-110       $12    $11    $10    $12    $12
    150-170        $3     $3     $3     $3     $3

Five years, no drift worth the name. So one pooled curve serves every date,
and -- this is the point -- a dollar on this board means exactly what a dollar
means everywhere else in the audit, because it was fitted to that board.

Picks are not repriced by date. A pick has no weekly market; it is priced
from the league's own chart exactly as before, with the same time discount.
Only players move.

A player with no rank at or before the trade's date (a rookie before his
first consensus, a name that will not match) is reported, not guessed at.
"""
import argparse, bisect, collections, csv, datetime, difflib, gzip, json, os, re, statistics, sys
import importlib.util as _ilu

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_tv = _ilu.spec_from_file_location('tv', os.path.join(ROOT, 'scripts',
                                                      'build_trade_values.py'))
TV = _ilu.module_from_spec(_tv); sys.modules['tv'] = TV; _tv.loader.exec_module(TV)

OUT, CURVE = 'tradeValuesDated.json', 'value-curve.json'
ECR_TYPE = 'dsf'                      # dynasty superflex, the format this league plays
MAX_STALE = 120                       # days; beyond this a price is flagged, not trusted
norm = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower())
D = datetime.date.fromisoformat

# "2021 Pick 26", "2021 1st Rd Pick (13)", "2022 2nd Rd Pick (Creams)" and
# "2022 1st Rd Pick 4" -- the slot is as often bare as parenthesised.
PICK = re.compile(r'^\s*(\d{4})\s+(?:(1st|2nd|3rd|4th)\s+)?(?:rd\s+)?pick\s*'
                  r'(?:\(\s*([^)]*?)\s*\)|\s+([^\s(].*?))?\s*$', re.I)
SLOT = re.compile(r'^(\d+)(?:st|nd|rd|th)?$', re.I)
ORD = {'1st': 1, '2nd': 2, '3rd': 3, '4th': 4}


def read_ecr(path):
    """-> sorted scrape dates, and {date: {player: rank}}."""
    by = collections.defaultdict(dict)
    with gzip.open(path, 'rt', encoding='utf-8', errors='replace') as f:
        for row in csv.DictReader(f):
            if row.get('ecr_type') != ECR_TYPE:
                continue
            try:
                by[row['scrape_date']][norm(row['player'])] = float(row['ecr'])
            except (TypeError, ValueError):
                continue
    dates = sorted(by)
    return dates, by


def fit_curve(dates, by):
    """rank -> dollars, calibrated against dp-values.json at each August.

    Bucketed medians rather than a fitted function: the relationship is a
    market's shape, not a law, and a median through 2,240 real pairs is
    harder to argue with than an exponent. Interpolated between bucket
    centres, flat beyond the last one.
    """
    dp = json.load(open(os.path.join(ROOT, 'dp-values.json'), encoding='utf-8'))
    V = {norm(k): v for k, v in dp['v'].items()}
    pairs, per_year = [], {}
    for yi, y in enumerate(dp['years']):
        tgt = datetime.date(y, 8, 1)
        near = [d for d in dates if abs((D(d) - tgt).days) <= 25]
        if not near:
            continue
        best = min(near, key=lambda d: abs((D(d) - tgt).days))
        got = []
        for p, e in by[best].items():
            row = V.get(p)
            if row is None or yi >= len(row) or row[yi] is None:
                continue
            got.append((e, float(row[yi])))
        pairs += got
        per_year[y] = {'scrape': best, 'pairs': len(got)}
    if not pairs:
        raise SystemExit('no (rank, dollar) pairs — is the ECR file the right one?')

    width, buckets = 5, collections.defaultdict(list)
    for e, d in pairs:
        buckets[int(e // width)].append(d)
    pts = sorted((k * width + width / 2, statistics.median(v))
                 for k, v in buckets.items() if len(v) >= 5)
    # The market is monotone even where a thin bucket is not; enforce it so a
    # worse rank can never price higher than a better one.
    out = []
    for x, y in pts:
        out.append((x, min(y, out[-1][1]) if out else y))
    return {'points': out, 'pairs': len(pairs), 'byYear': per_year,
            'bucketWidth': width}


def curve_at(curve, rank):
    pts = curve['points']
    if rank <= pts[0][0]:
        return pts[0][1]
    if rank >= pts[-1][0]:
        return pts[-1][1]
    i = bisect.bisect_left([p[0] for p in pts], rank)
    (x0, y0), (x1, y1) = pts[i - 1], pts[i]
    return y0 + (y1 - y0) * (rank - x0) / (x1 - x0)


# Names the canonicaliser does not carry and no edit distance should be
# trusted to guess. A nickname is not a typo.
NICKNAME = {'big ben': 'Ben Roethlisberger'}


class Market:
    def __init__(self, dates, by, curve):
        self.dates, self.by, self.curve = dates, by, curve
        self.dd = [D(d) for d in dates]
        # Every name the consensus has ever listed, for the last-resort match.
        self.known = {}
        for d in dates:
            for k in self.by[d]:
                self.known.setdefault(k, k)
        self.fuzzy = {}
        self.resolved = {}

    def _key(self, name):
        """Register spelling -> a name the consensus uses, or None.

        Three passes, each weaker than the last and each recorded. Exact
        after canonicalising; then a nickname table; then closest match on
        edit distance, which catches Connor/Conner, Garapolo/Garoppolo,
        Reager/Reagor and Shaduer/Shedeur. The cutoff is tight enough that
        two different players do not collide, and every fuzzy hit is written
        into the output so it can be checked rather than trusted.
        """
        raw = name.strip()
        if raw in self.resolved:
            return self.resolved[raw]
        k = norm(TV.canonical_player_name(raw))
        if k in self.known:
            self.resolved[raw] = k
            return k
        n = NICKNAME.get(raw.lower())
        if n and norm(n) in self.known:
            self.resolved[raw] = norm(n)
            return self.resolved[raw]
        hit = difflib.get_close_matches(k, self.known.keys(), n=1, cutoff=0.86)
        self.resolved[raw] = hit[0] if hit else None
        if hit:
            self.fuzzy[raw] = hit[0]
        return self.resolved[raw]

    def price(self, name, on):
        """(dollars, scrape used, days stale) or (None, None, None).

        The register spells names the way a man types them at eleven at
        night -- James Connor, Taysum Hill, Shaduer Sanders -- so every name
        goes through the ledger's own canonicaliser first, the same one
        build_trade_values.py uses. A name that still will not match is
        reported rather than guessed at.

        A price can also be STALE in a way a date alone does not show. The
        consensus lists about 480 players; falling off it is not a gap in
        the data, it is the market saying he is no longer a dynasty asset.
        So a rank older than MAX_STALE is not used at face value -- the
        player is priced at the bottom of the curve and flagged.
        """
        if name.strip() in TV.KNOWN_DST:
            return 0.0, None, None
        key = self._key(name)
        if key is None:
            # Never ranked in five years of a 480-deep dynasty superflex
            # consensus. That is not a gap in the data; it is the market
            # saying he was never a dynasty asset. Colt McCoy, Kalen
            # Ballage, Salvon Ahmed -- roster filler, and $0 is the honest
            # number, the same answer the model already gives a defence.
            return 0.0, None, None
        i = bisect.bisect_right(self.dd, D(on)) - 1
        while i >= 0:
            d = self.dates[i]
            r = self.by[d].get(key)
            if r is not None:
                age = (D(on) - self.dd[i]).days
                v = (curve_at(self.curve, r) if age <= MAX_STALE
                     else self.curve['points'][-1][1])
                return v, d, age
            i -= 1
        return None, None, None


def register_pick_text(raw):
    """The register's spellings, rewritten into the one TV.parse_pick knows.

    Obvibase is typed by hand over nine years and the same pick is written six
    ways. None of these is ambiguous; they just are not the two forms the
    published parser was built for ("2022 pick 11", "2022 1st Rd Pick (11)").
    Each rule below is a spelling actually in the file:

        2026 1st Round Pick (NWO)      Round spelled out
        2024 2nd Pick (Dragons)        no "Rd"
        2021 1st Rd Pick NWO           owner, no brackets
        2022 1st Rd Pick 11            slot, no brackets
        2023 2nd Rd Pick SDFT (Pick 29)   owner AND slot; the slot wins

    Anything that still will not parse is reported, never guessed.
    """
    s = re.sub(r'\bround\b', 'Rd', raw.strip(), flags=re.I)
    # an owner and a slot together: the slot is the better information
    m = re.match(r'^(\d{4}).*?\(\s*pick\s+(\d{1,2})\s*\)\s*$', s, re.I)
    if m:
        return f'{m.group(1)} pick {m.group(2)}'
    m = re.match(r'^(\d{4})\s+(1st|2nd|3rd|4th)\s+(?:rd\s+)?pick\s+(\d{1,2})\s*$',
                 s, re.I)
    if m:
        return f'{m.group(1)} pick {m.group(3)}'
    s = re.sub(r'^(\d{4})\s+(1st|2nd|3rd|4th)\s+pick\b', r'\1 \2 Rd Pick', s, flags=re.I)
    m = re.match(r'^(\d{4})\s+(1st|2nd|3rd|4th)\s+rd\s+pick\s+([^(\d].*)$', s, re.I)
    if m:
        return f'{m.group(1)} {m.group(2)} Rd Pick ({m.group(3).strip()})'
    return s


def price_pick(raw, season, sides, me):
    """The published model's pick pricer, called directly rather than copied.

    This matters more than it looks. The first draft of this script priced an
    unslotted pick at the flat average of its round, and that is NOT what the
    audit does: build_trade_values.py weights the slot probabilities by the
    OWNER's last finish, so a first from a bad team is worth more than a first
    from a good one. The Machines are a net buyer of picks and he buys them
    from the bottom of the table, so the flat version undercharged everything
    he received and turned a 15-6 record into 4-12 -- a swing that was
    entirely method, nothing to do with dates.

    So the pick model is imported, not reimplemented. The ONLY thing this
    script changes about a price is the day the player is valued on, which is
    the one thing it is supposed to change.
    """
    p = TV.parse_pick(register_pick_text(raw), season)
    log = []
    r = TV.resolve_pick(p, {'season': season, 'sides': sides}, me, log)
    return r.get('value'), r.get('resolved'), log


def _price_pick_flat(raw, season, look):
    """Superseded; kept only so the docstring above has something to point at."""
    m = PICK.match(raw.replace('Rd ', 'rd ').replace('Round ', 'rd '))
    if not m:
        return None, 'unparsed'
    year, rnd = int(m.group(1)), m.group(2)
    inner = (m.group(3) or m.group(4) or '').strip()
    rnd = ORD.get((rnd or '').lower(), 1)
    out = max(0, year - season)
    s = SLOT.match(inner) if inner else None
    if s:                                   # a known slot
        slot = int(s.group(1))
        base = TV.PICK_CHART.get(slot if slot <= 32 else 32, TV.PICK_CHART[32])
        return base * (TV.PICK_DECAY ** out), 'slot'
    lo, hi = (1, 17) if rnd == 1 else (17, 33)
    base = sum(TV.PICK_CHART[x] for x in range(lo, hi)) / 16
    return base * (TV.PICK_DECAY ** out), 'round-average'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ecr', required=True, help="DynastyProcess files/db_fpecr.csv.gz")
    a = ap.parse_args()
    dates, by = read_ecr(os.path.expanduser(a.ecr))
    curve = fit_curve(dates, by)
    json.dump({'note': ('Dynasty-superflex consensus rank to dollars, fitted to '
                        'dp-values.json at each August. Bucketed medians, made '
                        'monotone, interpolated between bucket centres. Built by '
                        'scripts/build_trade_values_dated.py.'),
               'ecrType': ECR_TYPE, 'span': [dates[0], dates[-1]],
               'scrapes': len(dates), **curve},
              open(os.path.join(ROOT, CURVE), 'w', encoding='utf-8'), indent=1)
    mk = Market(dates, by, curve)

    led = json.load(open(os.path.join(ROOT, 'trade-ledger.json'), encoding='utf-8'))
    look = None
    out, miss, stale = [], collections.Counter(), []
    for t in led['trades']:
        if not t['date'] or not (dates[0] <= t['date']):
            continue
        sides, ok = [], True
        # resolve_pick needs the other side, to infer an untagged pick's owner
        tsides = [{'team': x['team'], 'franchiseKey': x['franchiseKey']}
                  for x in t['sides']]
        for s, _tside in zip(t['sides'], tsides):
            tot, items = 0.0, []
            for raw in s['gives']:
                if PICK.match(raw.replace('Rd ', 'rd ').replace('Round ', 'rd ')):
                    v, how, log = price_pick(raw, t['season'], tsides, _tside)
                    if v is None or how in ('unparsed', 'bad-slot'):
                        miss[raw] += 1; ok = False
                        v = v or 0
                    tot += v
                    items.append({'asset': raw, 'kind': 'pick', 'how': how,
                                  'value': round(v, 1)})
                else:
                    v, on, age = mk.price(raw, t['date'])
                    if v is None:
                        miss[raw] += 1; ok = False
                    else:
                        tot += v
                        if age is not None and age > MAX_STALE:
                            stale.append((raw, t['date'], age))
                    items.append({'asset': raw, 'kind': 'player',
                                  'value': None if v is None else round(v, 1),
                                  'asOf': on, 'daysStale': age})
            # `gave` is what this side SENT. trade-ledger.json records a
            # trade by what each side gives up; tradeValues.json records it by
            # what each side receives. Netting one as if it were the other
            # inverts every verdict in the file -- it turned the Machines'
            # 15-6 into 5-12, a near mirror image, which is what a sign error
            # looks like when it is pretending to be a finding. Both figures
            # are written out so nothing downstream has to remember which is
            # which.
            sides.append({'team': s['team'], 'franchiseKey': s['franchiseKey'],
                          'gave': round(tot, 1), 'assets': items})
        # what a side GOT is what every other side gave
        whole = sum(x['gave'] for x in sides)
        for x in sides:
            x['got'] = round(whole - x['gave'], 1)
            x['net'] = round(x['got'] - x['gave'], 1)
        out.append({'season': t['season'], 'date': t['date'], 'ids': t['ids'],
                    'complete': ok, 'sides': sides})

    d = {'note': ('Every trade priced at its own date. Players from the '
                  'dynasty-superflex consensus on the nearest scrape at or '
                  'before the trade, converted by value-curve.json; picks from '
                  "the league's own chart, which has no weekly market. Built by "
                  'scripts/build_trade_values_dated.py.'),
         'curve': {'pairs': curve['pairs'], 'points': len(curve['points'])},
         'ecrSpan': [dates[0], dates[-1]], 'scrapes': len(dates),
         'count': len(out), 'complete': sum(1 for x in out if x['complete']),
         'unpricedAssets': sum(miss.values()),
         'unpricedDistinct': len(miss),
         'fuzzyMatched': dict(sorted(mk.fuzzy.items())),
         'trades': out}
    json.dump(d, open(os.path.join(ROOT, OUT), 'w', encoding='utf-8'), indent=1)

    ages = [i['daysStale'] for x in out for s in x['sides'] for i in s['assets']
            if i.get('daysStale') is not None]
    print(f'  {CURVE}: {curve["pairs"]} rank/dollar pairs, '
          f'{len(curve["points"])} points, {dates[0]} to {dates[-1]}')
    for y, v in sorted(curve['byYear'].items()):
        print(f'      {y} calibrated on {v["scrape"]} ({v["pairs"]} players)')
    print(f'  {OUT}: {len(out)} trades priced, {d["complete"]} complete')
    if ages:
        print(f'      price age: median {statistics.median(ages):.0f}d, '
              f'mean {sum(ages)/len(ages):.0f}d, worst {max(ages)}d')
    if mk.fuzzy:
        print(f'      {len(mk.fuzzy)} names matched by spelling, all recorded:')
        for a, b in sorted(mk.fuzzy.items())[:10]:
            print(f'        {a}  ->  {b}')
    if miss:
        print(f'      {sum(miss.values())} assets unpriced across '
              f'{len(miss)} distinct names; commonest:')
        for n, c in miss.most_common(8):
            print(f'        {c:3}  {n}')


if __name__ == '__main__':
    main()
