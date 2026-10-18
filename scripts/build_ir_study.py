#!/usr/bin/env python3
"""The IR study -- how often the two-slot cap binds, and what a third would fix.

    python3 scripts/build_ir_study.py

Every figure is computed here, at build time, from files in this repo. Nothing
on the page is typed by hand, so adding a week changes the conclusions rather
than leaving a stale number sitting under a headline that no longer fits it.

    ir-watch.json        weekly roster snapshots, written live, never rewritten
    transactions.json    the Sleeper transaction log
    ir-waiver-depth.json how many unrostered men are actually worth adding
    week-data/           weekly scoring, for the played/unplayed test
    scripts/standings.py records and seeds

WRITTEN TO BE READ, NOT WADED THROUGH

The first draft was a working paper and read like one: findings buried in
paragraphs, the verdict on page four. This version puts the state of the
argument at the top in a board a reader can scan in ten seconds, gives every
section a one-line finding before its evidence, and ends with what to watch
in the coming weeks -- each watch item carrying the number as it stands, the
threshold that would change the argument, and which side it would help.

Still a working paper and not a proposal. The league is split on the rule and
a study that only argues one way gets dismissed in a sentence, so the claims
of BOTH sides are scored, the limitations section is load-bearing, and the
gauge is counted from the scoreboard rather than felt.
"""
import importlib.util, json, os, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod(name, path):
    s = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


ad = _mod('ad', 'scripts/build_addendum.py')
E = ad.esc
OUT = os.path.join(ROOT, 'scfl-ir-study.html')
OG = os.path.join(ROOT, 'scfl-ir-study-og.jpg')

# Sleeper's designations that mean "a manager would plausibly shelve him".
# Questionable is deliberately excluded -- counting week-to-week knocks would
# inflate every number on the page.
HURT = 'IR, Out, Doubtful, PUP, Sus, NA, COV, DNR'
PLAYOFFS = 15        # league format: 14-week season, playoffs from week 15

NUM = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
       'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen']
word = lambda n: NUM[n] if n < len(NUM) else f'{n}'
RENAME = {'Heavy Hitters': 'Phins Phag', '*THE MACHINES*': 'THE MACHINES'}
club = lambda s: RENAME.get(s.strip(), s.strip())


def andlist(xs):
    """'1 and 2', '1, 2 and 3' -- a comma list reads as a truncation."""
    xs = [str(x) for x in xs]
    return xs[0] if len(xs) == 1 else ' and '.join([', '.join(xs[:-1]), xs[-1]])

# BLOCKED, settled the strict way: injured reserve actually full, and a man
# still stranded on the active roster. A side holding a free slot is not
# blocked by the cap, whatever else it is. One definition, used everywhere on
# the page, so no two figures on it are counted on different rules.
short = lambda t: bool(t['ir_full']) and t['stranded'] > 0


# ---------------------------------------------------------------- the numbers

def crunch():
    rows = json.load(open(os.path.join(ROOT, 'ir-watch.json'), encoding='utf-8'))['rows']
    rows = sorted(rows, key=lambda r: r['week'])
    cap = rows[-1]['ir_cap']
    teams_n = rows[-1]['teams_n']

    def model(c):
        """Re-run every week under cap `c`, holding the injuries as they fell.

        The assumption, stated so it can be argued with: each manager fills IR
        up to the cap with whoever is stranded, and nothing else about his
        behaviour changes.
        """
        blocked = stranded = freed = 0
        for r in rows:
            for t in r['teams']:
                moved = max(0, min(t['stranded'], c - t['ir_used']))
                freed += moved
                left = t['stranded'] - moved
                stranded += left
                if t['ir_used'] + moved >= c and left > 0:
                    blocked += 1
        return {'blocked': blocked, 'stranded': stranded, 'freed': freed}

    # Four slots are not on the table, so they are not modelled.
    M = {c: model(c) for c in (cap, cap + 1)}
    # At the CURRENT cap the state is observed rather than modelled: ir_full is
    # what the collector recorded that week, not a greedy refill of it.
    M[cap]['blocked'] = sum(1 for r in rows for t in r['teams'] if short(t))
    M[cap]['stranded'] = sum(t['stranded'] for r in rows for t in r['teams'] if short(t))

    sd = _mod('sd', 'scripts/standings.py')
    st = {t['team'].strip(): t for t in sd.build(str(rows[-1]['season']),
                                                 rows[-1]['week'])['table']}

    gain, blockwk = {}, {}
    for r in rows:
        for t in r['teams']:
            n = club(t['team'])
            gain[n] = gain.get(n, 0) + (max(0, min(t['stranded'], cap + 1 - t['ir_used']))
                                        - max(0, min(t['stranded'], cap - t['ir_used'])))
            blockwk.setdefault(n, 0)       # every club, so the never-blocked are countable
            if short(t):
                blockwk[n] += 1
    helped = sorted((n for n, g in gain.items() if g > 0),
                    key=lambda n: (-gain[n], st.get(n, {}).get('seed', 99)))
    seeds = [st[n]['seed'] for n in helped if n in st]

    # how much of each week's blockage a third slot clears
    share = []
    for r in rows:
        b2 = sum(1 for t in r['teams'] if short(t))
        b3 = sum(1 for t in r['teams'] if t['stranded'] > max(0, cap + 1 - t['ir_used']))
        share.append({'week': r['week'], 'blocked': b2, 'cleared': b2 - b3,
                      'pct': (b2 - b3) / b2 if b2 else None})
    # how many teams would take up a third slot in each week
    uptake = {r['week']: sum(1 for t in r['teams']
                             if max(0, min(t['stranded'], cap + 1 - t['ir_used']))
                             > max(0, min(t['stranded'], cap - t['ir_used'])))
              for r in rows}

    C = {'rows': rows, 'cap': cap, 'teams_n': teams_n, 'M': M, 'st': st,
         'gain': gain, 'blockwk': blockwk, 'helped': helped, 'share': share,
         'uptake': uptake, 'last': rows[-1],
         'med_seed': statistics.median(seeds) if seeds else None,
         'league_med': (teams_n + 1) / 2,
         'strand_now': sorted((t for t in rows[-1]['teams'] if t['stranded']),
                              key=lambda t: -t['stranded'])}
    C['depth'] = depth()
    C['drops'] = drops()
    C['peers'] = peers()
    return C


def spearman(xs, ys):
    """Rank correlation, so a handful of ten-slot leagues cannot drag the line.

    Pearson on raw slot counts would be pulled around by the leagues running
    ten, which are a different kind of league rather than an extreme version
    of this one.
    """
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r, i = [0.0] * len(v), 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    a, b = rank(xs), rank(ys)
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else 0.0


def peers():
    """What every other 16-team league actually runs.

    The study carried one claim nobody could test -- "leagues our size run two
    to four slots" -- because it had no data on any league but this one.
    scripts/league_survey.py walks outward from here and gets some; this
    reduces it to the comparisons the argument turns on.

    Three things have to be held together or the headline number misleads:

      1. A raw slot count is not comparable. A league with five slots that
         admits only true IR is stricter than one with three that admits Out,
         Doubtful and PUP. So the like-for-like figure is against leagues
         allowing the same NUMBER of designations we do.
      2. Injured reserve is not the only place a dynasty league stashes men.
         A taxi squad does the same job for different reasons, and most of
         these leagues have one where we have none.
      3. Tenure is measurable only in Sleeper seasons, and Sleeper is younger
         than this league. See the note on the tenure block below.
    """
    p = os.path.join(ROOT, 'league-survey.json')
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding='utf-8'))
    h = d.get('home')
    if not h or h.get('ir') is None:
        return None
    med = lambda xs: sorted(xs)[len(xs) // 2] if xs else None
    allow_n = lambda l: sum(1 for v in (l.get('allow') or {}).values() if v)
    ours_allow = allow_n(h)

    def klass(sel):
        g = [l for l in d['leagues'] if l['teams'] == 16 and l['ir'] is not None and sel(l)]
        if not g:
            return None
        ir = sorted(l['ir'] for l in g)
        dist = {}
        for v in ir:
            dist[v] = dist.get(v, 0) + 1
        return {'n': len(g), 'dist': dist, 'median': med(ir),
                'mean': sum(ir) / len(ir), 'lo': min(ir), 'hi': max(ir),
                'at_or_under': sum(1 for v in ir if v <= h['ir']),
                'three_plus': sum(1 for v in ir if v >= 3),
                'exactly_ours': dist.get(h['ir'], 0),
                'rows': g}

    cls = {'all': klass(lambda l: True),
           'dyn': klass(lambda l: l['type'] == 2),
           'sf': klass(lambda l: l['type'] == 2 and l['superflex'])}
    dyn = cls['dyn']['rows'] if cls['dyn'] else []

    # 1 -- like for like on who may be shelved at all
    same = [l for l in dyn if allow_n(l) == ours_allow]
    elig = {'n': len(same), 'median': med([l['ir'] for l in same]),
            'at_or_under': sum(1 for l in same if l['ir'] <= h['ir']),
            'ours_allow': ours_allow, 'of': len(h.get('allow') or {})} if same else None

    # 2 -- every place a roster can park a man, not just injured reserve
    stash = sorted(l['ir'] + l['taxi'] for l in dyn)
    ours_stash = h['ir'] + h['taxi']
    total = sorted(l['starters'] + l['bench'] + l['ir'] + l['taxi'] for l in dyn)
    ours_total = h['starters'] + h['bench'] + h['ir'] + h['taxi']
    room = {'stash_med': med(stash), 'ours_stash': ours_stash,
            'stash_under': sum(1 for v in stash if v <= ours_stash),
            'total_med': med(total), 'ours_total': ours_total,
            'total_under': sum(1 for v in total if v <= ours_total),
            'bench_med': med([l['bench'] for l in dyn]), 'ours_bench': h['bench'],
            'taxi_med': med([l['taxi'] for l in dyn]), 'ours_taxi': h['taxi'],
            'no_taxi': sum(1 for l in dyn if not l['taxi']),
            # what going to three would actually do to our standing
            'stash_under_3': sum(1 for v in stash if v <= ours_stash + 1)} if dyn else None

    # 3 -- tenure. Sleeper only, and it says so wherever it is quoted.
    ten = [l for l in dyn if l.get('seasons')]
    tn = None
    if ten and h.get('seasons'):
        buckets = []
        for lo, hi in ((1, 1), (2, 3), (4, 5), (6, 99)):
            b = [l for l in ten if lo <= l['seasons'] <= hi]
            if b:
                buckets.append({'lab': f'{lo}' if lo == hi
                                else (f'{lo}&ndash;{hi}' if hi < 99 else f'{lo}+'),
                                'n': len(b), 'median': med([l['ir'] for l in b]),
                                'mean': sum(l['ir'] for l in b) / len(b)})
        old = [l for l in ten if l['seasons'] >= 6]
        tn = {'n': len(ten), 'ours': h['seasons'],
              'max': max(l['seasons'] for l in ten),
              'median': med([l['seasons'] for l in ten]),
              'buckets': buckets,
              'rho': spearman([l['seasons'] for l in ten], [l['ir'] for l in ten]),
              'old_n': len(old),
              'old_under': sum(1 for l in old if l['ir'] <= h['ir']),
              'old_med': med([l['ir'] for l in old]),
              'old_taxi': med([l['taxi'] for l in old]),
              'old_bench': med([l['bench'] for l in old])}
    return {'home': h, 'cls': cls, 'elig': elig, 'room': room, 'ten': tn,
            'seen': d['leagues_seen'], 'asked': d['managers_asked'],
            'hops': d['hops'], 'season': d['season'], 'stamp': d['stamp']}


def depth():
    p = os.path.join(ROOT, 'ir-waiver-depth.json')
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding='utf-8'))
    return d if d.get('rows') else None


def drops():
    """The transaction join: did the cap ever actually cost anybody a player?

    scripts/ir_drops.py owns the join, so the page cannot drift from it. The
    extra work here is the question the join does not ask -- whether anybody
    else wanted the man who was let go.
    """
    p = os.path.join(ROOT, 'transactions.json')
    if not os.path.exists(p):
        return None
    ird = _mod('ird', 'scripts/ir_drops.py')
    tx, boxes, n_drops = ird.crunch()
    rows = tx['rows']

    def claimed_since(name, after_week):
        """Did any OTHER roster add him afterwards? If nobody did, the league
        agreed by inaction that the man was expendable, which is the whole
        measure of what the drop cost."""
        return [tx['rosters'].get(str(a['roster_id']))
                for r in rows if r['status'] == 'complete' and r['week'] >= after_week
                for a in r['adds'] if a['name'] == name]

    forced = []
    for d in boxes['cap_cost']:
        back = claimed_since(d['player'], d['week'])
        # a man signed and cut inside a fortnight was never an asset anybody
        # was holding on to, and counting him as a loss overstates the case.
        # It has to be the LAST time this roster signed him, not the first:
        # one of these men was taken in the preseason, dropped, and taken
        # again in week 5, and measuring from the first add turns a one-week
        # flyer into a man held all season.
        held = [r['week'] for r in rows if r['status'] == 'complete'
                and r['week'] <= d['week']
                for a in r['adds'] if a['name'] == d['player']
                and a['roster_id'] == d['roster_id']]
        last_add = max(held) if held else None
        forced.append(dict(d, claimed_since=back, held_from=last_add,
                           weeks_held=(d['week'] - last_add) if held else None))

    # in-season volume, with the two things that inflate it stripped out
    vol = []
    for w in sorted({r['week'] for r in rows}):
        g = [r for r in rows if r['week'] == w]
        m = [r for r in g if r['status'] == 'complete'
             and r['type'] in ('free_agent', 'waiver')]
        movers = {p['roster_id'] for r in m for p in r['adds'] + r['drops']}
        vol.append({'week': w, 'moves': len(m), 'movers': len(movers),
                    'failed': sum(1 for r in g if r['status'] == 'failed'),
                    'adds': sum(len(r['adds']) for r in m),
                    'drops': sum(len(r['drops']) for r in m)})
    return {'forced': forced, 'counts': {k: len(v) for k, v in boxes.items()},
            'n_drops': n_drops, 'judged': n_drops - len(boxes['unobserved']),
            'rows_total': len(rows), 'vol': vol,
            # Completed only. The raw row count is nearly double, because every
            # LOSING waiver claim is a row too -- quoting it reads as activity
            # and is nothing of the kind.
            'rows_done': sum(1 for r in rows if r['status'] == 'complete')}


# ------------------------------------------------------------------ the page

def figures(C):
    out = []
    S = lambda n, t: out.append(f'<h2 class="sect" id="s{n}">'
                                f'<span class="sn">{n}</span>{t}</h2>')
    F = lambda h: out.append(f'<p class="find">{h}</p>')
    P = lambda h: out.append(h)
    cap, rows, M = C['cap'], C['rows'], C['M']
    last, dep, dr, pr = C['last'], C['depth'], C['drops'], C['peers']
    n_wk, tw = len(rows), len(rows) * C['teams_n']
    base, plus1 = M[cap], M[cap + 1]
    cut_b = 100 * (base['blocked'] - plus1['blocked']) / base['blocked']
    cut_s = 100 * (base['stranded'] - plus1['stranded']) / base['stranded']
    spots = plus1['freed'] - base['freed']
    active = C['teams_n'] * (last['starters'] + 9)
    bw = C['blockwk']
    ever = sorted((n for n in bw if bw[n]), key=lambda n: (-bw[n], n))
    never = sorted(n for n in bw if not bw[n])
    tot_b = sum(bw.values())
    heaviest = ever[0]
    up = [r['upgrade_skill'] for r in dep['rows']] if dep else []
    dw = dep['rows'][-1]['week'] if dep else None
    # Demand has to be read off the SAME weeks as supply. Slot demand runs a
    # week ahead of the depth measurement -- a week nobody has played has no
    # depth figure -- and quoting the two ranges against each other silently
    # compares week 6 demand with week 5 supply.
    upt = [C['uptake'][r['week']] for r in dep['rows']] if dep else []
    # the forced drops that were real assets rather than week-old flyers
    forced = dr['forced'] if dr else []
    real = [d for d in forced if (d['weeks_held'] is None or d['weeks_held'] >= 2)]
    flyer = [d for d in forced if d not in real]
    unwanted = [d for d in forced if not d['claimed_since']]
    him = lambda n: 'him' if n == 1 else 'them'
    # The peer section only exists when the survey has been run, so every
    # section after it has to shift rather than be numbered by hand -- a
    # hard-coded 6 would label two sections 6 the day the survey is missing.
    N = lambda i: i + (1 if pr else 0)

    # ---- the board ------------------------------------------------------
    # Everything a reader needs to argue from, above the fold, in words
    # rather than figures. The figures are underneath it.
    def vb(q, a, tone, ev):
        return (f'<div class="vb {tone}"><div class="q">{q}</div>'
                f'<div class="a">{a}</div><div class="e">{ev}</div></div>')

    board = [
        vb('Does the cap bind?', 'Yes', 'yes',
           f'{last["teams_at_cap"]} of {C["teams_n"]} rosters full by week {last["week"]}, '
           f'{100*last["ir_used_total"]/last["ir_capacity_total"]:.0f}% of capacity'),
        vb('Has it cost anyone a player?',
           'Once' if len(real) == 1 else word(len(real)).capitalize(), 'part',
           (f'{word(len(forced))} drop{"s" if len(forced) != 1 else ""} forced by a full IR '
            f'in {word(n_wk)} weeks'
            + (f', {word(len(flyer))} of them a week-old flyer' if flyer else '')
            + (f'. Nobody has claimed {him(len(unwanted))} since' if unwanted else ''))
           if dr else 'no transaction log yet'),
        vb('Would a third slot fix it?', f'{cut_b:.0f}%', 'part',
           f'of blocked team-weeks cleared &mdash; {base["blocked"]} would become '
           f'{plus1["blocked"]}'),
        vb('Does it fall on everyone?', 'No', 'no',
           f'{word(len(ever))} of {C["teams_n"]} sides ever blocked, {word(len(never))} '
           f'never, {100*bw[heaviest]/tot_b:.0f}% of it on one roster'),
    ]
    if pr:
        dyb = pr['cls']['dyn']
        board.append(vb('How common is two?',
                        f'{100*dyb["exactly_ours"]/dyb["n"]:.0f}%', 'yes',
                        f'of {dyb["n"]} sixteen-team dynasty leagues; the median is '
                        f'{dyb["median"]} and {100*dyb["three_plus"]/dyb["n"]:.0f}% run '
                        f'three or more'))
    if dep:
        board.append(vb('Can the wire absorb it?', 'No', 'no',
                        f'{min(up)} to {max(up)} men a week worth starting, against '
                        f'{min(upt)} to {max(upt)} sides who would use a third slot '
                        f'in the same weeks'))
    P('<div class="board">' + ''.join(board) + '</div>')

    # ---- the gauge, built from the scoreboard in section 6 --------------
    V = scoreboard(C, cut_b, real, unwanted)
    fore = sum(1 for _, s, v, _ in V if s == 'expand' and v == 'supported')
    agin = sum(1 for _, s, v, _ in V if s == 'keep two' and v == 'supported')
    kf = sum(1 for _, s, v, _ in V if s == 'expand' and v in ('contradicted', 'overtaken'))
    ka = sum(1 for _, s, v, _ in V if s == 'keep two' and v in ('contradicted', 'overtaken'))
    net = (fore - kf) - (agin - ka)
    span = max(fore + agin, 1)
    x = 50 + 50 * max(-1.0, min(1.0, net / span))
    lean = ('toward expanding, and not by much' if 0 < net <= 2 else
            'clearly toward expanding' if net > 2 else
            'toward keeping two, and not by much' if -2 <= net < 0 else
            'clearly toward keeping two' if net < 0 else 'neither way')
    P(f'''<figure class="gauge"><svg viewBox="0 0 600 128" role="img"
 aria-label="Gauge: the evidence leans {lean}">
<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#0e8ab5"/>
<stop offset="0.5" stop-color="#d8b45a"/><stop offset="1" stop-color="#c20f16"/>
</linearGradient></defs>
<rect x="20" y="56" width="560" height="16" rx="8" fill="url(#g)" opacity=".85"/>
<line x1="300" y1="48" x2="300" y2="80" stroke="#17181c" stroke-width="2" opacity=".3"/>
<text x="300" y="96" font-size="10" text-anchor="middle" font-weight="700"
 font-family="-apple-system,sans-serif" fill="#9a958c">EVEN</text>
<g transform="translate({20 + 5.6*x},0)">
<polygon points="0,44 -10,26 10,26" fill="#17181c"/>
<line x1="0" y1="44" x2="0" y2="84" stroke="#17181c" stroke-width="3"/></g>
<text x="20" y="118" font-size="13" font-weight="800"
 font-family="-apple-system,sans-serif" fill="#0e8ab5">KEEP TWO</text>
<text x="580" y="118" font-size="13" text-anchor="end" font-weight="800"
 font-family="-apple-system,sans-serif" fill="#c20f16">EXPAND TO THREE</text>
</svg><figcaption>On the count of surviving arguments it leans <b>{lean}</b>. The needle is
counted, not felt: {fore} claims for expanding hold up and {kf} did not, against {agin} for
keeping two that hold up and {ka} that did not &mdash; a net of {net:+d} over {span}. Reject a
verdict in <a href="#s6">the scoreboard</a> and the needle moves.</figcaption></figure>''')

    # ---- the short version ----------------------------------------------
    if not dr:
        cost = 'The transaction log has not been pulled, so the real cost is unmeasured.'
    else:
        cost = (f'<b>The measurable cost so far is '
                f'{"one player" if len(real) == 1 else word(len(real)) + " players"}.</b> '
                f'{word(len(forced)).capitalize()} drop'
                f'{"s were" if len(forced) != 1 else " was"} forced by a full injured '
                f'reserve in {word(n_wk)} weeks'
                + (f', and {word(len(flyer))} of those was a man signed and cut inside a '
                   f'fortnight' if flyer else '')
                + (f'. No other side has claimed {him(len(unwanted))} since'
                   if unwanted else '') + '.')
    P(f'''<div class="short"><div class="h">The short version</div><ol>
<li><b>The cap binds, and harder every week.</b> {last['teams_at_cap']} of
{C['teams_n']} rosters are full and {last['stranded_total']} injured men are sitting on
active roster spots. Both numbers have risen every week of the season.</li>
<li><b>A third slot clears {cut_b:.0f}% of it</b> &mdash; {base['blocked']} blocked
team-weeks become {plus1['blocked']} &mdash; and frees {spots/n_wk:.1f} roster spots a
week out of {active}.</li>
<li>{cost}</li>
<li><b>It does not fall on everyone.</b> {word(len(ever)).capitalize()} of
{C['teams_n']} sides have ever been blocked; {word(len(never))} never have.
{E(heaviest)} alone carry {100*bw[heaviest]/tot_b:.0f}% of it.</li>
{f'<li><b>Two slots is not normal for a league this shape.</b> The median sixteen-team dynasty league runs {pr["cls"]["dyn"]["median"]} and {100*pr["cls"]["dyn"]["three_plus"]/pr["cls"]["dyn"]["n"]:.0f}% run three or more, which puts this league in the bottom {100*pr["cls"]["dyn"]["at_or_under"]/pr["cls"]["dyn"]["n"]:.0f}% of {pr["cls"]["dyn"]["n"]}. Going to three would still leave it in the bottom {100*pr["room"]["stash_under_3"]/pr["cls"]["dyn"]["n"]:.0f}% on total stash room.</li>' if pr else ''}
{f'<li><b>The wire cannot absorb it.</b> Across the {word(len(up))} weeks measured, only {min(up)} to {max(up)} unrostered men a week would have improved anybody&rsquo;s lineup, against {min(upt)} to {max(upt)} sides who would have taken up a third slot in those same weeks.</li>' if dep else ''}
</ol></div>''')

    nav = [(1, 'Does it bind?'), (2, 'What three would do'),
           (3, 'Has it cost anyone?'), (4, 'Level playing field?')]
    if pr:
        nav.append((5, 'Other leagues'))
    nav += [(N(5), 'The wire'), (N(6), 'The scoreboard'), (N(7), 'What to watch'),
            (N(8), 'What this cannot tell you'), (N(9), 'The data')]
    P('<nav class="jump"><b>On this page</b> '
      + ' &middot; '.join(f'<a href="#s{i}">{t}</a>' for i, t in nav) + '</nav>')

    P(f'<p class="lf">The league: <b>{C["teams_n"]} teams, {C["teams_n"]} owners</b>, one '
      f'each. {last["starters"]} starters and nine bench on every roster, plus '
      f'{word(cap)} injured reserve slots &mdash; {active} active spots and '
      f'{last["ir_capacity_total"]} IR spots in play. Data through week '
      f'{last["week"]}; {tw} team-weeks.</p>')

    # ---- 1 --------------------------------------------------------------
    S(1, 'Does the cap bind?')
    F(f'It does, and it has tightened every week of the season. By week {last["week"]} '
      f'<b>{last["teams_at_cap"]} of {C["teams_n"]}</b> rosters were full with '
      f'<b>{last["stranded_total"]}</b> injured men stuck on active spots.')
    hdr = ''.join(f'<th class="num">wk {r["week"]}</th>' for r in rows)

    def row(label, vals):
        cells = ''.join(f'<td class="num{" hot" if i == len(vals)-1 else ""}">{v}</td>'
                        for i, v in enumerate(vals))
        return f'<tr><th scope="row">{label}</th>{cells}</tr>'
    body = (row('IR slots filled', [f"{r['ir_used_total']}/{r['ir_capacity_total']}" for r in rows])
            + row('Share of capacity', [f"{100*r['ir_used_total']/r['ir_capacity_total']:.0f}%" for r in rows])
            + row('Teams with IR full', [r['teams_at_cap'] for r in rows])
            + row('Injured men on active rosters', [r['stranded_total'] for r in rows])
            + row('<b>Teams blocked</b>', [f'<b>{s["blocked"]}</b>' for s in C['share']]))
    P(f'<figure class="ad"><div class="scroll"><table><thead><tr><th></th>{hdr}</tr></thead>'
      f'<tbody>{body}</tbody></table></div><figcaption>Every row has risen or held. '
      f'None has fallen.</figcaption></figure>')
    P(f'<p class="b">Over {word(n_wk)} weeks, <b>{len(ever)} of {C["teams_n"]} teams</b> '
      f'have been blocked at least once, across <b>{base["blocked"]} of {tw} team-weeks</b> '
      f'({100*base["blocked"]/tw:.0f}%).</p>')
    who = ', '.join(E(', '.join(t['stranded_names'][:2])) for t in C['strand_now'][:4])
    P(f'<p class="lf">Stranded in week {last["week"]} include {who}.</p>')
    P(f'<p class="b"><b>Blocked</b> means a side whose injured reserve is <b>full</b> and '
      f'who still has an injured man on the active roster &mdash; the strict reading, used '
      f'everywhere on this page. A team holding a free slot is not blocked by the cap, '
      f'whatever else is wrong with its week. '
      + defn_note(C) + '</p>')

    # ---- 2 --------------------------------------------------------------
    S(2, 'What a third slot would do')
    F(f'Clear <b>{cut_b:.0f}%</b> of the blockage and free <b>{spots/n_wk:.1f} roster '
      f'spots a week</b> &mdash; about {100*spots/n_wk/active:.0f}% of the '
      f'{active} in play.')
    P('<p class="b">The counterfactual holds the injuries exactly as they fell and re-runs '
      'each week under a different cap, assuming every manager fills IR to the cap with '
      'whoever is stranded and changes nothing else. That assumption is the model&rsquo;s '
      'softest joint; it is flagged again in section 8.</p>')
    tr = ''.join(
        f'<tr><th scope="row">{"Cap " + str(c) + (" &mdash; actual" if c == cap else "")}</th>'
        f'<td class="num">{M[c]["blocked"]}</td><td class="num">{M[c]["stranded"]}</td></tr>'
        for c in (cap, cap + 1))
    P(f'<figure class="ad"><div class="scroll"><table><thead><tr><th></th>'
      f'<th class="num">Blocked team-weeks</th><th class="num">Stranded player-weeks</th>'
      f'</tr></thead><tbody>{tr}</tbody></table></div>'
      f'<figcaption>{word(n_wk).capitalize()} weeks, {tw} team-weeks. '
      f'{cut_b:.0f}% and {cut_s:.0f}% cleared.</figcaption></figure>')
    P(f'<p class="b">A fourth slot is not modelled anywhere on this page and is not on the '
      f'table. The question in front of the league is {word(cap)} or {word(cap+1)}, and a '
      f'counterfactual nobody will vote on only gives the argument somewhere else to go.</p>')
    P(f'<p class="b"><b>Who gains.</b> Only {word(len(C["helped"]))} sides gain anything at '
      f'all, and their median seed is {C["med_seed"]:.1f} against a league median of '
      f'{C["league_med"]:.1f} &mdash; '
      + ('a real tilt toward the bottom of the table.'
         if (C['med_seed'] or 0) - C['league_med'] >= 1.5
         else 'too close to call it a tilt either way.') + '</p>')
    rr = ''
    for n in C['helped']:
        t = C['st'].get(n)
        rr += (f'<tr><th scope="row">{E(n)}</th>'
               f'<td class="dim">{t["record"] if t else "?"}</td>'
               f'<td class="num dim">{t["seed"] if t else "?"}</td>'
               f'<td class="num">{bw.get(n,0)}</td>'
               f'<td class="num">{C["gain"][n]}</td></tr>')
    P(f'<figure class="ad"><div class="scroll"><table><thead><tr><th class="lt">Team</th>'
      f'<th class="lt">Record</th><th class="num">Seed</th><th class="num">Weeks blocked</th>'
      f'<th class="num">Spots gained</th></tr></thead><tbody>{rr}</tbody></table></div>'
      f'<figcaption>Weeks blocked is the strict count. Spots gained is simply where a third '
      f'slot would have been filled, which also catches a side holding one slot free and '
      f'{word(cap)} men hurt &mdash; so uptake runs wider than blockage.</figcaption></figure>')

    # ---- 3 --------------------------------------------------------------
    S(3, 'Has the cap actually cost anyone a player?')
    if not dr:
        F('Not answerable yet &mdash; the transaction log has not been pulled.')
    else:
        F(('Once. ' if len(real) == 1 else f'{word(len(real)).capitalize()} times. ')
          + f'In {dr["rows_done"]} completed transactions and {dr["n_drops"]} drops, '
          + ('one side' if len(forced) == 1 else f'{word(len(forced))} sides')
          + ' cut a man they were already carrying injured with no slot left to shelve him.')
        P('<p class="b">This is the test the first draft of this paper named as the strongest '
          'evidence nobody had. Everything else measured here is friction &mdash; a roster '
          'slot doing nothing &mdash; and friction is a ceiling on inconvenience, not a '
          'measure of loss. A drop is the first thing in the argument that is a real cost.</p>')
        P(f'<p class="b"><b>How it is judged.</b> Not by looking up the dropped man&rsquo;s '
          f'injury status: Sleeper carries <i>today&rsquo;s</i>, so a man dropped hurt in '
          f'September who has since healed reads healthy now. Instead every drop is matched '
          f'to the IR snapshot taken <i>before it, by timestamp</i> &mdash; waivers clear '
          f'within hours of the Wednesday reading and a week label cannot order the two. '
          f'Of {dr["n_drops"]} drops, <b>{dr["judged"]}</b> fall after a snapshot and can be '
          f'judged; {dr["counts"]["unobserved"]} cannot, almost all of them the preseason '
          f'flood that predates the first reading.</p>')
        fr = ''.join(
            f'<tr><th scope="row">wk {d["week"]}</th><td>{E(club(d["team"]))}</td>'
            f'<td><b>{E(d["player"])}</b> <span class="dim">{d["pos"]}</span></td>'
            f'<td class="dim ev">held '
            + (f'{word(d["weeks_held"])} week{"s" if d["weeks_held"] != 1 else ""}'
               if d['weeks_held'] is not None else 'from the preseason')
            + f', {d["ir_used"]}/{cap} on IR, {len(d["stranded_then"])} stranded; '
            + ('took ' + E(', '.join(d['added_back'])) + ' into the spot'
               if d['added_back'] else 'signed nobody in his place')
            + '. ' + ('<b>Claimed since by ' + E(', '.join(dict.fromkeys(d['claimed_since']))) + '.</b>'
                      if d['claimed_since'] else 'Unclaimed since.')
            + '</td></tr>' for d in dr['forced'])
        P(f'<figure class="ad"><div class="scroll"><table><thead><tr><th class="lt">When</th>'
          f'<th class="lt">Who</th><th class="lt">Dropped</th><th class="lt">The circumstances</th>'
          f'</tr></thead><tbody>{fr}</tbody></table></div><figcaption>Every drop in '
          f'{word(n_wk)} weeks of a stranded man by a side whose IR was full.</figcaption></figure>')
        P('<p class="b"><b>And the size of it.</b> '
          + (f'{word(len(flyer)).capitalize()} of '
             f'{word(len(dr["forced"]))} does not survive inspection: '
             + ', '.join(E(d['player']) for d in flyer)
             + (' was' if len(flyer) == 1 else ' were')
             + ' signed and cut inside a fortnight, which is a flyer rather than an asset a '
               'manager was holding on to. ' if flyer else '')
          + (f'That leaves <b>{word(len(real))} genuine '
             f'{"instance" if len(real) == 1 else "instances"}</b> in {word(n_wk)} weeks: '
             + ', '.join(f'{E(club(d["team"]))} letting {E(d["player"])} go'
                         for d in real) + '. ' if real else '')
          + (f'Not one of {him(len(unwanted))} has been claimed by any of the other '
             f'{C["teams_n"]-1} teams since, which is the league agreeing by inaction about '
             f'what the loss was worth.' if unwanted else '') + '</p>')
        ratio = ('<p class="b">The comparison this paper asked for, both ways round: '
                 f'<b>{exposure(C)[0]}</b> stranded man-weeks at a full injured reserve, of '
                 f'which {len(dr["forced"])} ended in a drop; <b>{exposure(C)[1]}</b> with a '
                 f'slot free, of which {dr["counts"]["own_choice"]} did. The direction is what '
                 'the expansion case predicts. The sample is nowhere near large enough to '
                 'carry it, and this paper does not claim otherwise.</p>')
        P(ratio)

    # ---- 4 --------------------------------------------------------------
    S(4, 'Is it a level playing field?')
    F(f'Equal in form, unequal in effect. <b>{word(len(never)).capitalize()} of '
      f'{C["teams_n"]}</b> rosters have never once been blocked, and '
      f'<b>{100*bw[heaviest]/tot_b:.0f}%</b> of all the blockage there has been sits on '
      f'{E(heaviest)}.')
    mxb = max(bw.values()) or 1
    bars = ''.join(
        f'<div class="bar"><i>{E(n)}</i>'
        f'<span class="{"" if bw[n] else "z"}" '
        f'style="width:{max(2, round(100*bw[n]/mxb))}%"></span><b>{bw[n]}</b></div>'
        for n in sorted(bw, key=lambda n: (-bw[n], n)))
    P(f'<figure class="ad"><div class="bars">{bars}</div><figcaption>Weeks blocked, out of '
      f'{word(n_wk)} possible for every team.</figcaption></figure>')
    P(f'<p class="b"><b>That cuts against expanding, and it should be said plainly.</b> The '
      f'cap is not pressure applied to {word(C["teams_n"])} teams. It is pressure applied to '
      f'{word(len(ever))}, and {100*bw[heaviest]/tot_b:.0f}% of it to one. A third slot does '
      f'not spread the burden evenly; it lifts it where it already falls and leaves the other '
      f'{word(len(never))} rosters exactly as they were. A change that moves nothing for '
      f'{100*len(never)/C["teams_n"]:.0f}% of the league is a hard thing to call a '
      f'levelling.</p>')
    P(f'<p class="b"><b>What runs the other way is why the bite is uneven.</b> It tracks '
      f'nothing a manager chooses. Every roster is built to the same {last["starters"]+9} men '
      f'and the same {word(cap)} slots; what separates {E(heaviest)} from the '
      f'{word(len(never))} untouched sides is which of their players got hurt, and when. '
      f'Roster pressure that follows from a decision is skill. Roster pressure that follows '
      f'from one treatment room is not a decision anybody made.</p>')
    short3 = lambda t: t['stranded'] > max(0, cap + 1 - t['ir_used'])
    bw3 = {}
    for r in rows:
        for t in r['teams']:
            n = club(t['team'])
            bw3[n] = bw3.get(n, 0) + (1 if short3(t) else 0)
    cleared = [n for n in ever if not bw3.get(n)]
    still = [n for n in ever if bw3.get(n)]
    P(f'<p class="b">The data settles the shape and not the principle. A third slot would '
      f'have cleared <b>{word(len(cleared))} of the {word(len(ever))}</b> affected teams '
      f'completely'
      + (f' and left {word(len(still))} still blocked in at least one week' if still else '')
      + '. Whether that is levelling a field or subsidising bad luck is a judgement, and '
        'this page does not have the standing to make it.</p>')

    # ---- 5 --------------------------------------------------------------
    # Evidence of a different KIND from everything above it: what other
    # leagues do is convention, not consequence. It belongs in the paper
    # because the argument of 7 September appealed to it, and it is marked for
    # what it is rather than promoted to a finding about harm.
    if pr:
        S(5, 'What every other 16-team league runs')
        dy, sf, al = pr['cls']['dyn'], pr['cls']['sf'], pr['cls']['all']
        h = pr['home']
        F(f'The median 16-team dynasty league runs <b>{dy["median"]} slots</b>. '
          f'<b>{100*dy["three_plus"]/dy["n"]:.0f}%</b> run three or more. '
          f'{word(dy["exactly_ours"]).capitalize()} of {dy["n"]} run {word(h["ir"])}, '
          f'as we do.')
        P(f'<p class="b">This was the one claim in the argument nobody could test. Sleeper '
          f'has no search &mdash; you can ask it for a league by its id, or for the leagues a '
          f'given manager is in, and nothing else &mdash; so the sample is walked outward '
          f'from here: every manager in this league, every other {pr["season"]} league they '
          f'play in, and onward through theirs. <b>{pr["seen"]:,} leagues from '
          f'{pr["asked"]} managers</b>, {word(pr["hops"])} hops. Of those, '
          f'<b>{al["n"]}</b> have sixteen teams and <b>{dy["n"]}</b> are sixteen-team '
          f'dynasty leagues.</p>')
        mx = max(dy['dist'].values())
        dr_ = ''.join(
            f'<tr><th scope="row">{k} slot{"s" if k != 1 else ""}'
            + (' &mdash; ours' if k == h['ir'] else '') + '</th>'
            f'<td class="num">{dy["dist"][k]}</td>'
            f'<td class="num dim">{100*dy["dist"][k]/dy["n"]:.0f}%</td>'
            f'<td><span class="pip{" me" if k == h["ir"] else ""}" '
            f'style="width:{max(2, round(100*dy["dist"][k]/mx))}%"></span></td></tr>'
            for k in sorted(dy['dist']))
        P(f'<figure class="ad"><div class="scroll"><table><thead><tr>'
          f'<th class="lt">Injured reserve</th><th class="num">Leagues</th>'
          f'<th class="num">Share</th><th class="lt"></th></tr></thead>'
          f'<tbody>{dr_}</tbody></table></div><figcaption>The {dy["n"]} sixteen-team dynasty '
          f'leagues in the sample. Median {dy["median"]}, mean {dy["mean"]:.1f}, range '
          f'{dy["lo"]} to {dy["hi"]}. Ours is {h["ir"]}: {dy["at_or_under"]} of {dy["n"]} run '
          f'that many or fewer, which puts this league in the bottom '
          f'{100*dy["at_or_under"]/dy["n"]:.0f}%.</figcaption></figure>')
        if sf:
            P(f'<p class="b">Narrowing to the closest match &mdash; sixteen-team '
              f'<i>superflex</i> dynasty, {sf["n"]} leagues &mdash; moves it very little: '
              f'median {sf["median"]}, {100*sf["three_plus"]/sf["n"]:.0f}% at three or more, '
              f'and this league in the bottom {100*sf["at_or_under"]/sf["n"]:.0f}%.</p>')
        if pr['elig']:
            el = pr['elig']
            P(f'<p class="b"><b>Eligibility does not explain it, which was the first place to '
              f'look.</b> A raw slot count is not comparable: a league with five slots that '
              f'admits only true injured reserve is stricter than one with three that admits '
              f'Out, Doubtful and PUP. This league admits <b>{word(el["ours_allow"])} of '
              f'{word(el["of"])}</b> designations. Among the {el["n"]} sixteen-team dynasty '
              f'leagues that are exactly as restrictive, the median is still '
              f'<b>{el["median"]} slots</b>, and only {word(el["at_or_under"])} of '
              f'{el["n"]} sit at {word(h["ir"])} or fewer. Across the sample the permissive '
              f'leagues carry <i>more</i> slots rather than fewer, so eligibility compounds '
              f'the gap instead of accounting for it.</p>')
        if pr['room']:
            rm = pr['room']
            P(f'<p class="b"><b>And injured reserve is not the only place a dynasty roster '
              f'parks a man.</b> A taxi squad does much the same job for different reasons, '
              f'and {dy["n"] - rm["no_taxi"]} of these {dy["n"]} leagues have one where this '
              f'league has none.</p>')
            cmp_ = [('Bench', rm['ours_bench'], rm['bench_med']),
                    ('Taxi squad', rm['ours_taxi'], rm['taxi_med']),
                    ('IR + taxi', rm['ours_stash'], rm['stash_med']),
                    ('Whole roster, stash included', rm['ours_total'], rm['total_med'])]
            P(f'<figure class="ad"><div class="scroll"><table><thead><tr>'
              f'<th class="lt"></th><th class="num">Ours</th>'
              f'<th class="num">Median of the {dy["n"]}</th></tr></thead><tbody>'
              + ''.join(f'<tr><th scope="row">{a}</th><td class="num hot">{b}</td>'
                        f'<td class="num">{c}</td></tr>' for a, b, c in cmp_)
              + f'</tbody></table></div><figcaption>On total stash room this league is in the '
                f'bottom {100*rm["stash_under"]/dy["n"]:.0f}%; on roster size including stash, '
                f'the bottom {100*rm["total_under"]/dy["n"]:.0f}%.</figcaption></figure>')
            P(f'<p class="pull">Which cuts both ways, and the second way is the one worth '
              f'noticing. Going to {word(cap+1)} slots would move this league&rsquo;s total '
              f'stash from {rm["ours_stash"]} to {rm["ours_stash"]+1} against a median of '
              f'{rm["stash_med"]} &mdash; still the bottom '
              f'{100*rm["stash_under_3"]/dy["n"]:.0f}%. The distance between this league and '
              f'its peers is not one injured reserve slot. It is '
              f'{rm["total_med"] - rm["ours_total"]} roster spots.</p>')
        if pr['ten']:
            tn = pr['ten']
            P(f'<p class="b"><b>Are they just younger?</b> It was the first objection raised '
              f'to this section and it is half right. The oldest league in the whole '
              f'sixteen-team set has run <b>{tn["max"]} seasons</b> on Sleeper, and it cannot '
              f'show more, because Sleeper is younger than this league &mdash; whose own '
              f'record came off ESPN before the move. So nobody here has existed as long as '
              f'the SCFL, and this measurement is a floor for every league in it, '
              f'<i>including ours at {word(tn["ours"])} '
              f'season{"s" if tn["ours"] != 1 else ""} on the platform</i>.</p>')
            P(f'<p class="b">What the measurement can do is test the <i>reasoning</i>: a '
              f'league being new is only grounds to discount it if new leagues choose '
              f'differently. They do, and in the opposite direction.</p>')
            P(f'<figure class="ad"><div class="scroll"><table><thead><tr>'
              f'<th class="lt">Seasons on Sleeper</th><th class="num">Leagues</th>'
              f'<th class="num">Median IR</th><th class="num">Mean IR</th></tr></thead><tbody>'
              + ''.join(f'<tr><th scope="row">{b["lab"]}</th><td class="num">{b["n"]}</td>'
                        f'<td class="num">{b["median"]}</td>'
                        f'<td class="num">{b["mean"]:.1f}</td></tr>'
                        for b in tn['buckets'])
              + f'</tbody></table></div><figcaption>Rank correlation between tenure and slot '
                f'count: <b>{tn["rho"]:+.2f}</b>. The longer a league has run, the more slots '
                f'it carries.</figcaption></figure>')
            P(f'<p class="b">The longest-running cohort is the least friendly to the case for '
              f'holding at {word(cap)}: of the <b>{tn["old_n"]}</b> sixteen-team dynasty '
              f'leagues with six or more seasons on Sleeper, only '
              f'<b>{word(tn["old_under"])}</b> run {word(h["ir"])} slots or fewer. Their '
              f'median is {tn["old_med"]} slots, {tn["old_taxi"]} taxi and a bench of '
              f'{tn["old_bench"]}.</p>')
            P(f'<p class="b"><b>Read it as convention, not consequence.</b> Every other '
              f'section of this paper measures what the cap <i>does</i>. This one measures '
              f'what other people chose, which is a weaker kind of evidence and a fair thing '
              f'to set aside on principle. It does settle one thing: {word(cap)} slots is not '
              f'normal for a league of this shape, and it is not normal among the oldest '
              f'leagues either. Whether normal is the same as right is not a question any '
              f'survey answers. The correlation above is also likely confounded &mdash; '
              f'long-tenured leagues on Sleeper are simply deeper leagues, bench '
              f'{tn["old_bench"]} against our {pr["room"]["ours_bench"]}, so this may be '
              f'"big-roster leagues migrated early" rather than "experience teaches you to '
              f'add slots".</p>')

    if dep:
        S(6 if pr else 5, 'The argument against: can the wire absorb it?')
        F(f'No. In the {word(len(up))} weeks measured the entire waiver pool held '
          f'<b>{min(up)} to {max(up)} men a week</b> worth starting, against <b>{min(upt)} to '
          f'{max(upt)}</b> sides who would have taken up a third slot in those same weeks.')
        P('<p class="b">The mechanism is arithmetic, not opinion. A side that shelves an '
          'injured man frees an active spot, fills it, and the pool is one player smaller. '
          'Every extra slot used takes a player off waivers.</p>')
        P('<p class="b"><b>A headcount cannot test that, and this study does not report one.</b> '
          'Counting unrostered bodies gives a number near five hundred all season, which is '
          'true and useless &mdash; it counts third-string tight ends and quarterbacks nobody '
          'in this league would start in any week of any year. The question is how many men '
          'are worth <i>adding</i>, so that is what is measured, against a bar the league set '
          'itself: did he outscore the <b>median</b> man actually started at his position '
          'that week?</p>')
        hdr2 = ''.join(f'<th class="num">wk {r["week"]}</th>' for r in dep['rows'])
        r2 = lambda lab, vals: (f'<tr><th scope="row">{lab}</th>'
                                + ''.join(f'<td class="num">{v}</td>' for v in vals) + '</tr>')
        P(f'<figure class="ad"><div class="scroll"><table><thead><tr><th></th>{hdr2}</tr>'
          f'</thead><tbody>'
          + r2('<b>Men worth adding</b>', [f'<b>{v}</b>' for v in up])
          + r2('Beats replacement level', [r['startable_skill'] for r in dep['rows']])
          + r2('Sides wanting a third slot',
               [C['uptake'].get(r['week'], 0) for r in dep['rows']])
          + '</tbody></table></div><figcaption>Skill positions only. Kickers and defences are '
            'excluded: half the league&rsquo;s are unrostered by construction, so including '
            'them quadruples the count and tells you nothing.</figcaption></figure>')
        tight = [r['week'] for r in dep['rows']
                 if C['uptake'].get(r['week'], 0) >= r['upgrade_skill']]
        if tight:
            more = [r['week'] for r in dep['rows']
                    if C['uptake'].get(r['week'], 0) > r['upgrade_skill']]
            P(f'<p class="pull">In week{"s" if len(tight) > 1 else ""} {andlist(tight)}, a '
              f'third slot would have been claimed by as many sides as there were players on '
              f'the entire wire worth claiming'
              + (f' &mdash; and in {andlist(more)}, by more. ' if more else '. ')
              + f'Expansion would not thin the usable wire in a week like '
              + ('those' if len(tight) > 1 else 'that')
              + '. It would empty it.</p>')
        if dr:
            v = [x for x in dr['vol'] if x['week'] > 1]
            if v:
                mv = sum(x['moves'] for x in v) / len(v)
                P(f'<p class="b"><b>And the league is quiet, which is the same finding from '
                  f'the other end.</b> Stripping out failed waiver bids, trades and '
                  f'commissioner moves, in-season activity runs <b>{mv:.0f} completed '
                  f'add-or-drop moves a week</b> across {C["teams_n"]} teams &mdash; '
                  f'{mv/C["teams_n"]:.1f} per side &mdash; with only '
                  f'{min(x["movers"] for x in v)} to {max(x["movers"] for x in v)} of '
                  f'{C["teams_n"]} rosters touched in a given week. Managers are not passing '
                  f'up a deep wire. There is not much on it to pass up.</p>')
        P('<p class="b"><b>What runs the other way is that the withdrawal is a loan.</b> A '
          'player coming off injured reserve has to be activated, the roster is then one '
          'over, and somebody is dropped. The men come back. What a third slot changes is not '
          'how many players are owned across a season but <i>when</i> &mdash; and it takes '
          'them in exactly the weeks when injuries make everyone want them.</p>')

    # ---- 6 --------------------------------------------------------------
    S(N(6), 'The scoreboard')
    F('Every claim either side made, and what the data does to it.')
    P('<p class="b"><b>Supported</b> means the data backs it. <b>Contradicted</b> means the '
      'data runs against it. <b>Overtaken</b> means it was true when it was said and is not '
      'now. <b>Untested</b> means this study cannot speak to it.</p>')
    TONE = {'supported': 'ok', 'contradicted': 'no', 'overtaken': 'mid', 'untested': 'mid'}
    vr = ''.join(
        f'<tr><th scope="row">{c}</th><td class="dim">{s}</td>'
        f'<td><span class="v {TONE[v]}">{v}</span></td>'
        f'<td class="dim ev">{w}</td></tr>' for c, s, v, w in V)
    P(f'<figure class="ad"><div class="scroll"><table><thead><tr><th class="lt">Claim</th>'
      f'<th class="lt">Made by</th><th class="lt">Verdict</th><th class="lt">On what</th>'
      f'</tr></thead><tbody>{vr}</tbody></table></div></figure>')
    keeps = [v for v in V if v[1] == 'keep two']
    survive = [c for c, _, v, _ in keeps if v == 'supported']
    fell = [c for c, _, v, _ in keeps if v in ('contradicted', 'overtaken')]
    rest = len(keeps) - len(survive) - len(fell)
    P(f'<p class="b">Of the {word(len(keeps))} arguments for keeping the cap, '
      + (f'{word(len(fell))} did not survive contact with the data and ' if fell
         else 'none fell outright and ')
      + f'{word(len(survive))} did'
      + (f', with {word(rest)} the data cannot speak to' if rest else '')
      + '. The two that matter most are the two nobody can settle from here: that the wire '
        'is thin, which was true before this debate started, and that no competitive harm '
        'has been demonstrated &mdash; which survived even after the transaction log was '
        'pulled looking for exactly that.</p>')

    # ---- 7 --------------------------------------------------------------
    watch = watch_items(C, cut_b, real)
    S(N(7), 'What to watch in the coming weeks')
    F(f'{word(len(watch)).capitalize()} numbers that would move the argument, each with the '
      f'reading as it stands and the threshold that would matter.')
    P('<p class="b">Every one of these is in the weekly collection already, so they update '
      'themselves. Nobody has to remember to run anything.</p>')
    P('<div class="watch">' + ''.join(watch) + '</div>')
    P(f'<p class="b"><b>And one date rather than a number.</b> {word(last["week"]).capitalize()} '
      f'of fourteen regular-season weeks are played; the playoffs start in week {PLAYOFFS}. Injuries peak late '
      f'and a side carrying men into a playoff run cannot churn its way out of trouble the '
      f'way it can in October. If the cap is going to bite hardest anywhere, it is in weeks '
      f'{PLAYOFFS-2} to {PLAYOFFS}, and that is also when this page will be at its least '
      f'flattering to the side that wants nothing changed.</p>')

    # ---- 8 --------------------------------------------------------------
    S(N(8), 'What this cannot tell you')
    F('Read this before quoting any figure above.')
    lims = [
        ('It measures roster friction, not competitive harm.',
         'Nothing here shows a blocked team lost a game, or even lost points. Establishing '
         'that would need to know who each manager <i>would</i> have added with the freed '
         'slot and what that man then scored, which is unobservable. Every number in '
         'sections 1 and 2 is a ceiling on inconvenience.'),
        ('A blocked team is never actually stuck.',
         'Any side can cut an injured man and move on &mdash; which is exactly what section 3 '
         'counts. Blocked means <i>made to choose</i>, not <i>prevented</i>, and whether '
         'being made to choose is a flaw or the point of a roster limit is a judgement no '
         'amount of this data settles.'),
        ('The benefit is concentrated, and that is not by itself an objection.',
         f'{E(heaviest)} account for <b>{C["gain"][heaviest]} of the {spots} freed spots</b> '
         f'({100*C["gain"][heaviest]/spots:.0f}%). An injury rule biting hardest on whoever '
         f'got hurt most is the rule doing its job, not a distortion in the sample. What it '
         f'does mean is narrower: the headline percentages rest heavily on one roster, so '
         f'take that team out and the measured size of the effect falls sharply.'),
        ('The drop test can only undercount.',
         'A snapshot is weekly. A man signed on Thursday, hurt on Sunday and dropped on '
         'Tuesday was never in one, so he cannot be counted either way. Those drops are '
         'reported as unobserved rather than quietly scored as healthy &mdash; but it means '
         'section 3 is a floor, not a total.') if dr else None,
        ('The peer survey is a snowball sample, not a random one.',
         f'Sleeper has no search, so section 5 is walked outward from this league. That '
         f'draws on people who already play in a sixteen-team superflex dynasty league, so '
         f'it skews toward deeper and more committed leagues than the true population of '
         f'sixteen-team dynasty leagues. The gap it measures is therefore probably '
         f'overstated. It also measures tenure in Sleeper seasons only, which is a floor for '
         f'any league that migrated &mdash; this one included.') if pr else None,
        (f'One season, {word(n_wk)} weeks, {tw} team-weeks.',
         'Injury rates vary year to year and no claim is made that this one is typical. The '
         'greedy-filling assumption in the model is untested &mdash; a manager might hold a '
         'slot open against a worse injury later, in which case uptake above is overstated.'),
    ]
    P('<dl class="lim">' + ''.join(f'<dt>{a}</dt><dd>{b}</dd>' for a, b in lims if a) + '</dl>')
    P(f'<p class="b">{relief_note(C)}</p>')

    # ---- 9 --------------------------------------------------------------
    S(N(9), 'The data, in full')
    F('Everything the conclusions rest on, so it can be checked rather than taken.')
    cols = [('wk', lambda r: r['week']),
            ('IR used', lambda r: f"{r['ir_used_total']}/{r['ir_capacity_total']}"),
            ('teams at cap', lambda r: r['teams_at_cap']),
            ('teams with empty IR', lambda r: r['teams_empty_ir']),
            ('stranded', lambda r: r['stranded_total']),
            ('teams blocked', lambda r: sum(1 for t in r['teams'] if short(t)))]
    P(f'<figure class="ad"><div class="scroll"><table><thead><tr>'
      + ''.join(f'<th class="num">{c}</th>' for c, _ in cols) + '</tr></thead><tbody>'
      + ''.join('<tr>' + ''.join(f'<td class="num">{f(r)}</td>' for _, f in cols) + '</tr>'
                for r in rows)
      + '</tbody></table></div><figcaption>From ir-watch.json, one row written per week and '
        'never revised.</figcaption></figure>')
    if dep:
        P(f'<figure class="ad"><div class="scroll"><table><thead><tr>'
          f'<th class="num">wk</th><th class="num">scored</th>'
          f'<th class="num">worth adding</th><th class="num">beats replacement</th>'
          f'<th class="lt">the men worth adding</th></tr></thead><tbody>'
          + ''.join(
              f'<tr><td class="num">{r["week"]}</td><td class="num">{r["scored"]}</td>'
              f'<td class="num"><b>{r["upgrade_skill"]}</b></td>'
              f'<td class="num">{r["startable_skill"]}</td><td class="dim ev">'
              + (', '.join(f'{E(u["name"])} {u["pos"]} {u["pts"]}' for u in r['upgrades'])
                 or '&mdash;') + '</td></tr>' for r in dep['rows'])
          + f'</tbody></table></div><figcaption>From ir-waiver-depth.json. Only played weeks '
            f'appear: depth cannot be measured on a week nobody has played. Upgrade bar '
            f'(median starter), week {dep["rows"][-1]["week"]}: '
          + ', '.join(f'{k} {v}' for k, v in dep['rows'][-1]['median_bar'].items()
                      if k in ('QB', 'RB', 'WR', 'TE'))
          + '.</figcaption></figure>')
    if dr:
        v = dr['vol']
        P(f'<figure class="ad"><div class="scroll"><table><thead><tr>'
          f'<th class="num">wk</th><th class="num">completed moves</th>'
          f'<th class="num">adds</th><th class="num">drops</th>'
          f'<th class="num">teams active</th><th class="num">failed bids</th>'
          f'</tr></thead><tbody>'
          + ''.join(f'<tr><td class="num">{x["week"]}</td><td class="num">{x["moves"]}</td>'
                    f'<td class="num">{x["adds"]}</td><td class="num">{x["drops"]}</td>'
                    f'<td class="num">{x["movers"]}</td>'
                    f'<td class="num dim">{x["failed"]}</td></tr>' for x in v)
          + '</tbody></table></div><figcaption>From transactions.json. Free-agent and waiver '
            'moves that completed; trades and commissioner moves are excluded. Failed bids '
            'are losing waiver claims &mdash; shown because they inflate any raw transaction '
            'count, not because they are moves. <b>Sleeper files the entire preseason under '
            'week 1</b>, so that row is July to September and not a week at all.'
            '</figcaption></figure>')
    if pr:
        ks = sorted({k for c in pr['cls'].values() if c for k in c['dist']})
        P(f'<figure class="ad"><div class="scroll"><table><thead><tr>'
          f'<th class="num">IR slots</th><th class="num">16-team</th>'
          f'<th class="num">of those, dynasty</th>'
          f'<th class="num">of those, superflex</th></tr></thead><tbody>'
          + ''.join(f'<tr><td class="num">{k}</td>'
                    + ''.join(f'<td class="num{" hot" if k == pr["home"]["ir"] else ""}">'
                              f'{(pr["cls"][c]["dist"].get(k, 0) if pr["cls"][c] else 0)}</td>'
                              for c in ('all', 'dyn', 'sf'))
                    + '</tr>' for k in ks)
          + '<tr><th scope="row">total</th>'
          + ''.join(f'<td class="num">{pr["cls"][c]["n"] if pr["cls"][c] else 0}</td>'
                    for c in ('all', 'dyn', 'sf'))
          + '</tr><tr><th scope="row">median</th>'
          + ''.join(f'<td class="num">{pr["cls"][c]["median"] if pr["cls"][c] else "&mdash;"}</td>'
                    for c in ('all', 'dyn', 'sf'))
          + '</tr></tbody></table></div><figcaption>From league-survey.json, written by '
            f'<code>scripts/league_survey.py</code>: {pr["seen"]:,} leagues reached from '
            f'{pr["asked"]} managers in {word(pr["hops"])} hops, of which these have sixteen '
            f'teams. The row at {pr["home"]["ir"]} is ours. The file records slot counts, '
            f'roster shapes and settings only &mdash; no league names, no ids, no user '
            f'names.</figcaption></figure>')
    tt = ''.join(
        f'<tr><th scope="row">{E(club(t["team"]))}</th>'
        f'<td class="num">{t["ir_used"]}</td><td class="num">{t["ir_free"]}</td>'
        f'<td class="num">{t["stranded"]}</td>'
        f'<td class="dim ev">{E(", ".join(t.get("stranded_names", [])) or "—")}</td></tr>'
        for t in sorted(last['teams'], key=lambda t: (-t['stranded'], club(t['team']))))
    P(f'<figure class="ad"><div class="scroll"><table><thead><tr><th class="lt">Team</th>'
      f'<th class="num">on IR</th><th class="num">free</th><th class="num">stranded</th>'
      f'<th class="lt">who</th></tr></thead><tbody>{tt}</tbody></table></div>'
      f'<figcaption>Every roster as at week {last["week"]}.</figcaption></figure>')
    P(f'<p class="b"><b>Injured</b> means Sleeper carries one of {HURT}. Questionable is not '
      f'counted &mdash; including week-to-week knocks would inflate every number here. '
      f'<b>Stranded</b> means an injured man occupying an <i>active</i> roster spot.</p>')
    P('<p class="lf">To run it yourself: <code>ir-watch.json</code> (weekly snapshots, '
      '<code>scripts/ir_watch.py</code>), <code>transactions.json</code> '
      '(<code>scripts/fetch_transactions.py</code>, joined by '
      '<code>scripts/ir_drops.py</code>), <code>ir-waiver-depth.json</code> '
      '(<code>scripts/waiver_depth.py</code>, needs the nflverse play-by-play download), '
      '<code>week-data/2026-w*.json</code>, <code>scripts/standings.py</code>. The page '
      'itself is <code>scripts/build_ir_study.py</code>.</p>')
    return out


def defn_note(C):
    cap, rows = C['cap'], C['rows']
    loose = sum(1 for r in rows for t in r['teams']
                if t['stranded'] > max(0, cap - t['ir_used']))
    d = loose - C['M'][cap]['blocked']
    return (f'The looser reading &mdash; which also counts a side with one slot free and '
            f'{word(cap)} men hurt &mdash; would add {word(d)} team-week'
            f'{"s" if d != 1 else ""} to every blocked figure on this page '
            f'({loose} of {len(rows)*C["teams_n"]} rather than {C["M"][cap]["blocked"]}). '
            f'The strict reading was settled on, and it is the one that counts fewer.')


def exposure(C):
    """Stranded man-weeks at a full injured reserve, and with a slot free.

    The denominator for section 3: a drop can only be forced by the cap where
    there was a stranded man AND no room to shelve him, so the two populations
    have to be sized before the two drops mean anything.
    """
    full = sum(t['stranded'] for r in C['rows'] for t in r['teams'] if t['ir_full'])
    free = sum(t['stranded'] for r in C['rows'] for t in r['teams'] if not t['ir_full'])
    return full, free


def relief_note(C):
    """Whether the relief a third slot buys is decaying. Computed, not asserted.

    An earlier draft stated flatly that it decays. The next week's data broke
    the claim -- the share fell to a quarter and then recovered. So the shape
    is described from the series rather than from the last time anybody looked.
    """
    s = [x for x in C['share'] if x['pct'] is not None]
    vals = [x['pct'] for x in s]
    half = len(vals) // 2
    early = 100 * sum(vals[:half]) / half if half else 0
    late = 100 * sum(vals[half:]) / (len(vals) - half)
    mono = all(a >= b for a, b in zip(vals, vals[1:]))
    worst = min(s, key=lambda x: x['pct'])
    return (f'<b>The relief looks weaker later in the season, but the trend is noisy.</b> '
            f'The share of each week&rsquo;s blockage a third slot would clear has run '
            + ', '.join(f'{100*x["pct"]:.0f}%' for x in s)
            + f' &mdash; averaging {early:.0f}% over the first {word(half)} weeks and '
              f'{late:.0f}% since. It is <b>not</b> a steady decline: the worst week was '
              f'{worst["week"]}, at {100*worst["pct"]:.0f}%, and week {s[-1]["week"]} reads '
              f'{100*s[-1]["pct"]:.0f}% ({s[-1]["cleared"]} of {s[-1]["blocked"]} blocked '
              f'sides cleared). The mechanism is real &mdash; a side with more than one man '
              f'stranded only has its line moved by a single extra slot &mdash; but on '
              f'{word(len(C["rows"]))} weeks it cannot be called a trend'
            + ('' if mono else ', and it is not monotonic')
            + '. Stranded counts have run '
            + ', '.join(str(r['stranded_total']) for r in C['rows'])
            + ', so the problem is growing even where the relief is holding up.')


def watch_items(C, cut_b, real):
    """What to watch, each with the reading now, the trigger, and whose case it

    helps. Derived rather than listed: the thresholds are set off the series as
    it stands, so they move with it instead of being a judgement made in
    October and left there."""
    cap, rows, last, dep = C['cap'], C['rows'], C['last'], C['depth']
    bw = C['blockwk']
    never = [n for n in bw if not bw[n]]
    st = [r['stranded_total'] for r in rows]
    s = [x for x in C['share'] if x['pct'] is not None]
    up = [r['upgrade_skill'] for r in dep['rows']] if dep else []
    items = [
        ('Injured men on active rosters',
         ' &rarr; '.join(str(x) for x in st),
         f'The first week it <b>falls</b>. It has risen or held in every week of the season, '
         f'which is what makes the problem look structural rather than seasonal. One real '
         f'decline and that reading weakens.',
         'keep two'),
        ('Rosters with IR full',
         f'{last["teams_at_cap"]} of {C["teams_n"]}',
         f'<b>{min(C["teams_n"], last["teams_at_cap"] + 2)} or more.</b> At that point a '
         f'clear majority of the league is at the cap in the same week and &ldquo;it only '
         f'affects a few teams&rdquo; stops being available to either side.',
         'expand'),
        ('Teams never blocked',
         f'{word(len(never))} of {C["teams_n"]}',
         f'<b>{word(C["teams_n"]//4).capitalize()} or fewer.</b> The strongest argument '
         f'against expanding is that it changes nothing for most of the league. If the '
         f'untouched group shrinks to a quarter of the teams, that argument is gone.',
         'expand'),
        ('Forced drops',
         f'{word(len(real))} genuine in {word(len(rows))} weeks'
         if real else f'none in {word(len(rows))} weeks',
         '<b>A dropped man who is then claimed by somebody else.</b> Every forced drop so far '
         'has been a player no other side wanted, which is why the cost reads as trivial. One '
         'claim off the wire turns a forced drop into a real transfer of value and changes '
         'the scoreboard line that has survived everything else.',
         'expand'),
        ('Relief a third slot buys',
         ', '.join(f'{100*x["pct"]:.0f}%' for x in s),
         f'<b>Two straight weeks under half.</b> '
         + (f'{word(sum(1 for x in s if x["pct"] < 0.5)).capitalize()} week has dipped below '
            f'it so far and never twice running. ' if sum(1 for x in s if x['pct'] < 0.5) == 1
            else f'{word(sum(1 for x in s if x["pct"] < 0.5)).capitalize()} weeks have dipped '
                 f'below it so far. ')
         + 'A pair in a row would say the fix is losing potency as injuries stack, which is '
           'the one finding that argues against expanding on the expansion case&rsquo;s own '
           'terms.',
         'keep two'),
    ]
    if dep:
        # Which weeks the wire actually outran demand -- derived, because an
        # earlier draft asserted it had never happened and the opening two
        # weeks of the season say otherwise.
        upt = [C['uptake'][r['week']] for r in dep['rows']]
        loose_wk = [r['week'] for r, u in zip(dep['rows'], upt) if r['upgrade_skill'] > u]
        items.append((
            'Men on the wire worth adding',
            f'{min(up)} to {max(up)} a week',
            f'<b>More of them than there are sides wanting a third slot, two weeks running.</b> '
            + (f'That last held in week{"s" if len(loose_wk) > 1 else ""} '
               f'{andlist(loose_wk)}, before the injuries arrived. '
               if loose_wk else 'It has not held in any week measured. ')
            + 'While the wire holds fewer usable men than there are teams who would claim '
              'one, expansion empties the top of it rather than thinning it.',
            'keep two'))
    side = {'expand': ('EXPAND', 'ok'), 'keep two': ('KEEP TWO', 'no')}
    return [f'<div class="wi"><div class="wh">{t}'
            f'<span class="wt {side[w][1]}">helps {side[w][0]}</span></div>'
            f'<div class="wn">{now}</div><div class="ww">{trig}</div></div>'
            for t, now, trig, w in items]


def scoreboard(C, cut_b, real, unwanted):
    """One claim per row, attributed to the side that made it, with what the

    data does to it. The gauge needle is COUNTED from this table rather than
    felt, so a reader who rejects a verdict can recount and move it himself.
    That is the only honest way to put a dial on a judgement."""
    cap, last, dep, dr = C['cap'], C['last'], C['depth'], C['drops']
    pe, M, bw = C['peers'], C['M'], C['blockwk']
    tilt = (C['med_seed'] or 0) - C['league_med'] >= 1.5
    V = [
        ('The cap binds', 'expand', 'supported',
         f"{last['teams_at_cap']} of {C['teams_n']} rosters full by week {last['week']}, "
         f"{100*last['ir_used_total']/last['ir_capacity_total']:.0f}% of capacity"),
        ('Only injured men qualify, so it cannot be stacked', 'expand', 'supported',
         'structural: an activated player must be rostered or dropped'),
        ('The withdrawal reverses when players return', 'expand', 'supported',
         'structural: activating a returning player puts the roster one over, so a man goes '
         'back to the wire'),
        ('A third slot helps weak teams more than strong ones', 'expand',
         'supported' if tilt else 'untested',
         f"median seed of the {word(len(C['helped']))} beneficiaries is {C['med_seed']:.1f} "
         f"against a league median of {C['league_med']:.1f}"
         + ('' if tilt else ' &mdash; too close to call either way')),
        ('Nobody is hoarding IR spots', 'expand', 'overtaken',
         f"true when it was said in preseason; by week {last['week']}, "
         f"{last['teams_at_cap']} of {C['teams_n']} teams were at the cap"),
        ('Leagues our size run two to four slots', 'expand',
         'supported' if pe else 'untested',
         (f"understated, if anything: {pe['cls']['dyn']['n']} sixteen-team dynasty leagues "
          f"run a median of {pe['cls']['dyn']['median']}, "
          f"{100*pe['cls']['dyn']['three_plus']/pe['cls']['dyn']['n']:.0f}% at three or "
          f"more, and only "
          f"{100*pe['cls']['dyn']['exactly_ours']/pe['cls']['dyn']['n']:.0f}% at two")
         if pe else 'no data here on other leagues, their age or their keeper rules'),
    ]
    if dr:
        V.append(('The cap forces real roster losses', 'expand',
                  'supported' if real else 'untested',
                  (f"{word(len(real))} side{'s' if len(real) != 1 else ''} cut a man already "
                   f"being carried injured with no slot left to shelve him, in "
                   f"{C['drops']['n_drops']} drops"
                   ) if real else 'no instance found in the transaction log'))
    V += [
        ('The wire is already bare', 'keep two', 'supported', 'DEPTH'),
        ('Expansion thins the wire further', 'keep two', 'supported', 'MECH'),
        ('It changes nothing functional', 'keep two', 'contradicted',
         f"it changes {M[cap]['blocked']} blocked team-weeks to {M[cap+1]['blocked']}"),
        ('It helps the committed teams and hurts the rest', 'keep two',
         'contradicted' if tilt else 'untested',
         'the beneficiaries skew to the bottom of the table, not the top' if tilt
         else 'the beneficiaries sit almost exactly at the league median'),
        ('It would change nothing for most of the league', 'keep two', 'supported',
         f"{word(sum(1 for n in bw if not bw[n]))} of {C['teams_n']} rosters have never once "
         f"been blocked"),
    ]
    if dr:
        V.append(('The men the cap forces out are men nobody wants', 'keep two',
                  'supported' if unwanted and len(unwanted) == len(dr['forced'])
                  else 'contradicted' if dr['forced'] and not unwanted else 'untested',
                  (("neither of the two men dropped has" if len(dr['forced']) == 2 else
                    "the man dropped has not" if len(dr['forced']) == 1 else
                    f"none of the {word(len(dr['forced']))} men dropped has")
                   + f" been claimed by any of the other {C['teams_n']-1} teams since")
                  if unwanted and len(unwanted) == len(dr['forced'])
                  else 'at least one dropped man was claimed by another side'))
    V.append(('No competitive harm from the cap has been shown', 'keep two', 'supported',
              ('the transaction log was pulled looking for exactly that; what it found was '
               f'friction and {word(len(dr["forced"]))} '
               f'{"man" if len(dr["forced"]) == 1 else "men"} nobody else wanted')
              if dr else 'correct, and not testable without the transaction log'))
    if dep:
        up = [r['upgrade_skill'] for r in dep['rows']]
        dw = dep['rows'][-1]['week']
        V = [(a, b, c, (f"only {up[-1]} players on the entire wire would have improved a "
                        f"lineup in week {dw}" if d == 'DEPTH' else
                        f"{C['uptake'].get(dw, 0)} sides would have used a third slot in week "
                        f"{dw}; there were {up[-1]} players worth taking" if d == 'MECH' else d))
             for a, b, c, d in V]
    else:
        V = [v for v in V if v[3] not in ('DEPTH', 'MECH')]
    return V


# ------------------------------------------------------------- the share card

CARD = """<style>
:root{--red:#c20f16;--ink:#17181c;--faint:#9a958c;--blue:#0e8ab5;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;margin:0;}
html,body{width:1200px;height:630px;overflow:hidden;background:#efe9de;
 font-family:Georgia,'Times New Roman',serif;color:var(--ink);}
.card{position:relative;width:1200px;height:630px;overflow:hidden;background:#efe9de;
 border-top:9px solid var(--red);border-bottom:9px solid var(--red);
 padding:50px 58px 42px;display:flex;}
.l{width:530px;flex:0 0 530px;display:flex;flex-direction:column;}
.flag{font-family:var(--sans);font-size:11.5px;font-weight:900;letter-spacing:.22em;
 text-transform:uppercase;color:var(--red);}
h1{font-size:56px;line-height:.98;letter-spacing:-.026em;font-weight:900;margin-top:15px;}
h1 em{font-style:normal;color:var(--red);}
.rule{width:64px;height:3px;background:var(--red);margin:20px 0 16px;}
.dek{font-style:italic;color:#4b4b52;font-size:17px;line-height:1.4;max-width:29ch;}
.st{margin-top:auto;display:flex;gap:30px;}
.st .k{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.st .v{font-size:31px;font-weight:900;line-height:1.1;font-variant-numeric:tabular-nums;}
.r{flex:1;padding-left:46px;display:flex;flex-direction:column;justify-content:center;gap:17px;}
.vb{border-left:4px solid var(--red);padding-left:15px;}
.vb.no{border-color:var(--blue);}
.vb .q{font-family:var(--sans);font-size:11px;font-weight:800;letter-spacing:.1em;
 text-transform:uppercase;color:var(--faint);}
.vb .a{font-size:27px;font-weight:900;line-height:1.14;margin-top:2px;}
.vb.no .a{color:var(--blue);}
.vb.yes .a{color:var(--red);}
</style>
<div class="card">
 <div class="l">
  <div class="flag">SCFL NewsRoom &middot; Working Paper</div>
  <h1>Two Slots, <em>__SHORT__</em> Short</h1>
  <div class="rule"></div>
  <div class="dek">__DEK__</div>
  <div class="st">
   <div><div class="k">Capacity used</div><div class="v">__PCT__%</div></div>
   <div><div class="k">Stranded</div><div class="v">__STR__</div></div>
   <div><div class="k">A third clears</div><div class="v">__CUT__%</div></div>
  </div>
 </div>
 <div class="r">__CARDS__</div>
</div>"""


def card(C, nshort, cut, real):
    last, bw = C['last'], C['blockwk']
    never = sum(1 for n in bw if not bw[n])
    cards = [('Does the cap bind?', 'Yes', 'yes'),
             ('Has it cost anyone a player?',
              'Once' if len(real) == 1 else word(len(real)).capitalize(), 'no'),
             ('Does it fall on everyone?', f'No &mdash; {word(never)} untouched', 'no')]
    doc = (CARD.replace('__CARDS__',
                        ''.join(f'<div class="vb {t}"><div class="q">{q}</div>'
                                f'<div class="a">{a}</div></div>' for q, a, t in cards))
           .replace('__SHORT__', word(nshort).capitalize())
           .replace('__PCT__', f"{100*last['ir_used_total']/last['ir_capacity_total']:.0f}")
           .replace('__STR__', str(last['stranded_total']))
           .replace('__CUT__', f'{cut:.0f}')
           .replace('__DEK__', f"{word(len(C['rows'])).capitalize()} weeks of roster data on "
                               f"a rule the league cannot agree on. What a third slot would "
                               f"fix, what it would cost, and what to watch next."))
    ad.shoot(doc, OG, 'irstudy-card')


# ------------------------------------------------------------------- the page

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Two Slots, __SHORT__ Short &mdash; SCFL NewsRoom</title>
<meta name="scfl:kicker" content="Working Paper &middot; __MONTH__">
<meta name="scfl:published" content="__DATE__">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SCFL NewsRoom">
<meta property="og:title" content="Two Slots, __SHORT__ Short">
<meta property="og:description" content="__DESC__">
<meta property="og:image" content="https://watsoncapitalinvest-dot.github.io/Claude/scfl-ir-study-og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="newsroom-favicon.png">
<style>
:root{--cream:#fffdfb;--paper:#faf7f2;--ink:#17181c;--muted:#65656b;--faint:#9a958c;
 --line:#e6e0d6;--red:#c20f16;--blue:#0e8ab5;--gold:#d8b45a;
 --serif:Georgia,'Times New Roman',serif;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;}
body{margin:0;background:var(--cream);color:var(--ink);font-family:var(--serif);font-size:17px;
 line-height:1.62;-webkit-font-smoothing:antialiased;}
.wrap{max-width:880px;margin:0 auto;padding:0 20px 80px;}
.runhead{font-family:var(--sans);font-size:10.5px;font-weight:800;letter-spacing:.22em;
 text-transform:uppercase;color:var(--faint);border-bottom:1px solid var(--line);
 padding:20px 0 12px;}
.flag{font-family:var(--sans);font-size:10.5px;font-weight:900;letter-spacing:.24em;
 text-transform:uppercase;color:var(--red);margin-top:26px;display:block;}
h1{font-weight:900;font-size:clamp(34px,7vw,56px);line-height:1.02;letter-spacing:-.022em;
 margin:12px 0 0;text-wrap:balance;}
h1 em{font-style:normal;color:var(--red);}
.dek{font-style:italic;color:var(--muted);font-size:18.5px;margin:14px 0 0;max-width:58ch;}
.byline{font-family:var(--sans);font-size:11.5px;letter-spacing:.06em;color:var(--faint);
 margin-top:16px;text-transform:uppercase;}
.rule{height:3px;background:var(--red);width:70px;margin:22px 0 28px;}

/* the board: the whole argument, scannable, above everything else */
.board{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
 grid-template-columns:repeat(auto-fit,minmax(215px,1fr));margin:0 0 26px;}
.vb{background:var(--cream);padding:16px 17px 17px;border-top:3px solid var(--gold);}
.vb.yes{border-top-color:var(--red);}
.vb.no{border-top-color:var(--blue);}
.vb .q{font-family:var(--sans);font-size:10px;font-weight:800;letter-spacing:.12em;
 text-transform:uppercase;color:var(--faint);line-height:1.4;}
.vb .a{font-size:29px;font-weight:900;line-height:1.1;margin:5px 0 6px;
 font-variant-numeric:tabular-nums;letter-spacing:-.02em;}
.vb.yes .a{color:var(--red);}
.vb.no .a{color:var(--blue);}
.vb .e{font-family:var(--sans);font-size:12px;line-height:1.45;color:var(--muted);}

.short{background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--red);
 padding:20px 24px 20px;margin:0 0 24px;}
.short .h{font-family:var(--sans);font-size:11px;font-weight:900;letter-spacing:.2em;
 text-transform:uppercase;color:var(--red);margin-bottom:10px;}
.short ol{margin:0;padding-left:22px;}
.short li{margin-bottom:9px;line-height:1.5;}
.short li:last-child{margin-bottom:0;}

.jump{font-family:var(--sans);font-size:12px;color:var(--muted);margin:0 0 30px;
 padding:12px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);
 line-height:1.9;}
.jump b{color:var(--faint);text-transform:uppercase;letter-spacing:.12em;font-size:10px;
 margin-right:6px;}
.jump a{color:var(--ink);font-weight:700;text-decoration:none;
 border-bottom:1px solid var(--line);}
.jump a:hover{border-bottom-color:var(--red);color:var(--red);}

h2.sect{font-family:var(--sans);font-size:13px;font-weight:900;letter-spacing:.18em;
 text-transform:uppercase;color:var(--red);margin:50px 0 14px;padding-top:16px;
 border-top:2px solid var(--ink);display:flex;align-items:baseline;gap:11px;scroll-margin-top:12px;}
h2.sect .sn{font-size:11px;background:var(--red);color:#fff;width:21px;height:21px;
 display:inline-flex;align-items:center;justify-content:center;border-radius:50%;
 letter-spacing:0;flex:0 0 21px;}
p.find{font-size:21px;line-height:1.38;font-weight:700;letter-spacing:-.012em;
 margin:0 0 18px;max-width:52ch;}
p.b{margin:0 0 16px;max-width:64ch;}
p.lf{margin:0 0 16px;max-width:64ch;font-family:var(--sans);font-size:13px;color:var(--muted);}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:14px;
 background:var(--paper);padding:1px 5px;border-radius:3px;}
.pull{margin:30px 0 20px;padding:0 0 0 20px;border-left:3px solid var(--red);font-size:19px;
 line-height:1.45;font-weight:700;max-width:54ch;letter-spacing:-.01em;}

figure.ad{margin:24px 0 30px;}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;}
figure.ad table{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:13.5px;}
figure.ad td,figure.ad th{padding:8px 10px;border-bottom:1px solid var(--line);
 white-space:nowrap;}
figure.ad thead th{font-size:10px;font-weight:900;letter-spacing:.14em;text-transform:uppercase;
 color:var(--faint);border-bottom:2px solid var(--ink);}
figure.ad th[scope=row]{text-align:left;font-weight:700;}
figure.ad .num{text-align:right;font-variant-numeric:tabular-nums;font-weight:800;}
figure.ad .lt{text-align:left;}
figure.ad .dim{color:var(--muted);font-weight:600;}
figure.ad .hot{color:var(--red);}
figcaption{font-family:var(--sans);font-size:11.5px;color:var(--faint);margin-top:10px;
 line-height:1.55;}
figure.ad .v{font-family:var(--sans);font-size:10px;font-weight:900;letter-spacing:.1em;
 text-transform:uppercase;padding:2px 7px;border-radius:3px;color:#fff;white-space:nowrap;}
figure.ad .v.ok{background:var(--red);}
figure.ad .v.no{background:var(--blue);}
figure.ad .v.mid{background:var(--gold);color:#3a3326;}
figure.ad .ev{white-space:normal;min-width:19em;font-size:12.5px;line-height:1.45;}
figure.ad .pip{display:block;height:11px;background:var(--line);border-radius:0 2px 2px 0;
 min-width:3px;}
figure.ad .pip.me{background:var(--red);}
figure.ad td:has(.pip){width:38%;}
figure.gauge{margin:6px 0 28px;}
figure.gauge svg{width:100%;height:auto;display:block;}
figure.gauge a{color:var(--red);font-weight:700;}

.bars{display:flex;flex-direction:column;gap:5px;border-top:2px solid var(--ink);
 padding-top:12px;}
.bar{display:flex;align-items:center;gap:10px;font-family:var(--sans);font-size:12.5px;}
.bar i{font-style:normal;font-weight:700;flex:0 0 11em;color:var(--muted);
 overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.bar span{display:block;height:13px;background:var(--red);border-radius:0 2px 2px 0;
 flex:0 0 auto;max-width:calc(100% - 14em);}
.bar span.z{background:var(--line);}
.bar b{font-weight:900;font-variant-numeric:tabular-nums;}

.watch{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);margin:0 0 20px;}
.wi{background:var(--cream);padding:15px 18px 17px;}
.wh{font-family:var(--sans);font-size:11px;font-weight:900;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);display:flex;flex-wrap:wrap;gap:9px;
 align-items:center;}
.wt{font-size:9.5px;letter-spacing:.1em;padding:2px 7px;border-radius:3px;color:#fff;}
.wt.ok{background:var(--red);} .wt.no{background:var(--blue);}
.wn{font-size:23px;font-weight:900;letter-spacing:-.015em;margin:4px 0 6px;
 font-variant-numeric:tabular-nums;}
.ww{font-family:var(--sans);font-size:13px;line-height:1.5;color:var(--muted);max-width:68ch;}

dl.lim{margin:0 0 20px;}
dl.lim dt{font-weight:700;margin-top:16px;}
dl.lim dd{margin:3px 0 0;color:var(--muted);max-width:64ch;}

.more{margin-top:46px;border-top:1px solid var(--line);padding-top:18px;font-family:var(--sans);
 font-size:12.5px;line-height:1.6;color:var(--muted);max-width:74ch;}
@media(max-width:560px){
 .bar i{flex:0 0 7.5em;font-size:11.5px;}
 p.find{font-size:19px;}
 .vb .a{font-size:26px;}
}
</style></head><body><div class="wrap">
<div class="runhead">SCFL NewsRoom &middot; Working Paper</div>
<span class="flag">Rules &middot; Injured Reserve</span>
<h1>Two Slots, <em>__SHORT__</em> Short</h1>
<p class="dek">__DESC__</p>
<div class="byline">An early review of the evidence &middot; data through week __WK__</div>
<div class="rule"></div>
__BODY__
<div class="more">Every figure on this page is computed at build time from files in the
repository &mdash; the weekly roster snapshots, the transaction log, the waiver-depth
measurement and the scoring files. Nothing here was typed by hand, so adding a week changes
the conclusions rather than leaving a stale number under a headline that no longer fits it.
Built by <code>scripts/build_ir_study.py</code>.</div>
</div></body></html>"""


def build():
    import datetime
    C = crunch()
    cap, last, bw = C['cap'], C['last'], C['blockwk']
    cut = 100 * (C['M'][cap]['blocked'] - C['M'][cap + 1]['blocked']) / C['M'][cap]['blocked']
    nshort = sum(1 for n in bw if bw[n])
    never = sum(1 for n in bw if not bw[n])
    dr = C['drops']
    real = [d for d in (dr['forced'] if dr else [])
            if (d['weeks_held'] is None or d['weeks_held'] >= 2)]
    body = '\n'.join(figures(C))
    pr = C['peers']
    desc = (f"{word(nshort).capitalize()} of {C['teams_n']} teams have hit the IR cap with a "
            f"man still stranded; {word(never)} never have. A third slot would clear "
            f"{cut:.0f}% of it, the wire holds a handful of men worth adding, and in "
            f"{word(len(C['rows']))} weeks the cap has cost "
            f"{'one side one player' if len(real) == 1 else word(len(real)) + ' players'}"
            + (f" — and {100*pr['cls']['dyn']['exactly_ours']/pr['cls']['dyn']['n']:.0f}% of "
               f"{pr['cls']['dyn']['n']} comparable leagues run two slots." if pr else "."))
    today = datetime.date.today()
    doc = (PAGE.replace('__BODY__', body)
               .replace('__SHORT__', word(nshort).capitalize())
               .replace('__DESC__', E(desc))
               .replace('__WK__', str(last['week']))
               .replace('__MONTH__', today.strftime('%B %Y'))
               .replace('__DATE__', today.isoformat()))
    open(OUT, 'w', encoding='utf-8').write(doc)
    print(f'wrote {os.path.basename(OUT)} ({len(doc):,} chars)')
    print(f"  cap {cap}: {C['M'][cap]['blocked']} blocked team-weeks | "
          f"cap {cap+1}: {C['M'][cap+1]['blocked']} ({cut:.0f}% cleared)")
    print(f"  blocked at least once {nshort}/{C['teams_n']} | never {never}")
    if dr:
        print(f"  forced drops {len(dr['forced'])} ({len(real)} genuine) "
              f"of {dr['judged']} judged, {dr['n_drops']} total")
    card(C, nshort, cut, real)


if __name__ == '__main__':
    build()
