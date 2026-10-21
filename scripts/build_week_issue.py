#!/usr/bin/env python3
"""Lay the week's game reports out as a flip-book magazine issue.

    python3 scripts/build_week_issue.py --week 4

Takes the stories scripts/write_week.py produced and runs them through the same
cover, contents page, page engine and measured pagination as every other issue
this desk has shipped, so a weekly issue looks like the magazine rather than
like a web page that happens to contain football.

Pagination is measured, not guessed: build_issue lays the pages out once, the
headless measurer renders them at phone size and records where each page
actually fills up, and the issue is laid out again against those breaks. A
magazine page that scrolls is a bug.

The cover art comes from John's graphics AI like every other issue. If it is
not there yet the issue still builds, with a typographic stand-in, because an
issue that will not build is worth less than one with a plain cover.
"""
import argparse, importlib.util, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')
_s = importlib.util.spec_from_file_location('bi', os.path.join(ROOT, 'scripts', 'build_issue.py'))
bi = importlib.util.module_from_spec(_s); sys.modules['bi'] = bi; _s.loader.exec_module(bi)
_t = importlib.util.spec_from_file_location('sd', os.path.join(ROOT, 'scripts', 'standings.py'))
sd = importlib.util.module_from_spec(_t); sys.modules['sd'] = sd; _t.loader.exec_module(sd)
E = bi.esc

# eight games a week, so the numerals have to reach eight -- stopping at
# four gave a contents page reading I, II, III, IV, 5, 6, 7
ORD = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII', 8: 'VIII'}


def matchups(season, week, stories):
    """story index -> "Team v Team", for the flag over each game report.

    The flag used to read Game I, Game II, Game III, which is the order this
    desk chose to print them in and tells a reader nothing. In the contents it
    is worse than nothing: eight lines of Roman numerals where the one thing
    anybody wants is to find their own team.

    Ordered as the week file has them rather than winner-first, so the contents
    does not give away eight results before the reader reaches page three.
    """
    out = {}
    try:
        wk = json.load(open(os.path.join(WDIR, f'{season}-w{week}.json'), encoding='utf-8'))
    except Exception:
        return out
    key = lambda t: re.sub(r'[^a-z0-9]', '', (t or '').lower())
    for i, st in enumerate(stories):
        pair = {key(st['winner']), key(st['loser'])}
        for g in wk['games']:
            names = [t['team'].strip() for t in g['teams']]
            if {key(n) for n in names} == pair:
                # print the names the copy uses, in the file's own order
                look = {key(st['winner']): st['winner'], key(st['loser']): st['loser']}
                out[i] = ' v '.join(look[key(n)] for n in names)
                break
    return out


def scoreboard_blocks(stories):
    """The scoreboard as a pre-rendered article, so the packer treats it as one."""
    rows = ''
    for s in sorted(stories, key=lambda s: -(s['score'][0] + s['score'][1])):
        rows += (f'<tr><th scope="row">{E(s["winner"])}</th>'
                 f'<td class="num"><b>{s["score"][0]}</b></td>'
                 f'<td class="vs">def.</td>'
                 f'<td>{E(s["loser"])}</td>'
                 f'<td class="num dim">{s["score"][1]}</td>'
                 f'<td class="num dim">+{s["margin"]:.1f}</td></tr>')
    return [('body', '<div class="ad"><figure><div class="scroll"><table>'
             f'<tbody>{rows}</tbody></table></div>'
             '<figcaption>Every game of the week, heaviest first. Margin at the right.'
             '</figcaption></figure></div>')]


def standings_blocks(st):
    """The table, by division, because that is the shape the playoffs use."""
    if not st:
        return []
    out = []
    by = {}
    for r in st['table']:
        by.setdefault(r.get('div_name') or 'League', []).append(r)
    for di, dv in enumerate(sorted(by)):
        rows = ''
        for r in by[dv]:
            rows += (f'<tr><th scope="row">{E(r["team"])}</th>'
                     f'<td class="num"><b>{r["record"]}</b></td>'
                     f'<td class="num dim">{r["pf"]:.0f}</td>'
                     f'<td class="num dim">{r["pa"]:.0f}</td>'
                     f'<td class="num dim">{r["streak"]}</td></tr>')
        # the table is reference, not a game report: it is allowed to run over
        # two pages rather than be shrunk to 72 per cent to avoid it
        out.append(('pagebreak' if di == 2 else 'body',
                    f'<div class="ad"><figure>'
                            f'<div class="sect" style="margin-top:14px">{E(dv)}</div>'
                            f'<div class="scroll"><table><thead><tr><th class="lt"></th>'
                            f'<th>W-L</th><th>PF</th><th>PA</th><th>Run</th></tr></thead>'
                            f'<tbody>{rows}</tbody></table></div></figure></div>'))
    lead = st['table'][0]
    out.append(('body', f'<p class="b">{E(lead["team"])} top the league at {lead["record"]} '
                        f'with {lead["pf"]:.0f} points. Playoffs begin in week '
                        f'{st["playoff_week"]}, which leaves '
                        f'{max(0, st["playoff_week"] - 1 - st["through"])} weeks of the regular '
                        f'season still to play.</p>'))
    return out


ORD_W = ['', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh',
         'eighth', 'ninth', 'tenth']
NUM_W = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
         'nine', 'ten', 'eleven', 'twelve']


def alltime_rank(pts):
    """Where `pts` would sit on the all-time list of single team-weeks.

    history.json stops at last season, so this season's finished weeks are
    counted in too -- otherwise a 2026 score is ranked against every season
    except the one it was scored in.
    """
    rows = []
    h = json.load(open(os.path.join(ROOT, 'history.json'), encoding='utf-8'))
    for s in h['seasons']:
        for m in s.get('matchups') or []:
            for v in (m.get('homeScore'), m.get('awayScore')):
                if v is not None:
                    rows.append(float(v))
    for p in sorted(os.listdir(WDIR)):
        if not (p.endswith('.json') and '-w' in p) or '-' in p.rsplit('w', 1)[-1]:
            continue
        try:
            wk = json.load(open(os.path.join(WDIR, p), encoding='utf-8'))
            sc = [t['points'] for g in wk['games'] for t in g['teams']]
            star = [x for g in wk['games'] for t in g['teams'] for x in t['starters']]
        except Exception:
            continue
        # the same two tells the Record Book uses: a week nobody has played is
        # all zeroes, and a half-played Sunday shows as starters stuck on 0
        zero = sum(1 for x in star if x['points'] == 0) / max(len(star), 1)
        if sc and min(sc) >= 30 and zero < 0.07:
            rows += sc
    return sum(1 for p in rows if p > pts) + 1


def cover_source(d, stories, lead):
    """What the cover leads on: the lead game, or a feature if the issue says so.

    Some weeks the biggest thing that happened is not a game. The written file
    can point the cover at a feature with {"cover": {"from": "feature"}}, and
    everything that reads as the cover's billing -- the hook, the subhead and
    the share blurb -- follows it. Everything else about the issue is unchanged:
    the game of the week is still the game of the week inside.
    """
    cv = d.get('cover') or {}
    if cv.get('from') == 'feature' and (d.get('features') or []):
        return d['features'][cv.get('index', 0)], True
    return stories[lead], False


def upper1(x):
    """Capitalise the first letter and leave the rest alone.

    str.capitalize() lowercases everything after it, which turned every
    opponent in these lines into "over horsecollars" and "to the machines".
    """
    return x[:1].upper() + x[1:] if x else x


def a_div(name):
    """'a Spartan game', but 'a Four Horsemen game' -- not 'a The Four Horsemen'."""
    n = name[4:] if name.lower().startswith('the ') else name
    return f'a {E(n)} game'


def preview_prose(season, week, st):
    """Next week previewed as an article: a paragraph a game, sixteen teams.

    The table underneath says who plays whom. This says what it is worth, in
    sentences, because a page of bullet points is a listing and not a read.

    Every clause is derived. What a side did last week comes out of its trail,
    the stake comes out of the division and the seeds, and the hooks -- an
    unbeaten opponent, a run of three or more, a first win -- are only printed
    when they are true. A fixture with nothing to say about it gets the
    billing and stops, which is shorter than the invented alternative.
    """
    nxt = week + 1
    try:
        sc = json.load(open(os.path.join(ROOT, 'sleeper-schedule.json'), encoding='utf-8'))
        fixtures = sc['weeks'].get(str(nxt)) or []
    except Exception:
        return []
    if not fixtures or nxt >= int(st.get('playoff_week') or 99):
        return []
    by = {r['roster_id']: r for r in st['table']}
    pairs = []
    for g in fixtures:
        a, b = by.get(g.get('home_roster')), by.get(g.get('away_roster'))
        if a and b:
            pairs.append((a, b) if a['seed'] <= b['seed'] else (b, a))
    pairs.sort(key=lambda x: x[0]['seed'] + x[1]['seed'])

    def form(t, brief=False):
        """Last week, in a clause."""
        leg = (t.get('trail') or [])[-1] if t.get('trail') else None
        if not leg:
            return f'{E(t["team"])} did not play'
        _, res, me, them, who = leg
        won, m = res == 'W', abs(me - them)
        if won and t['w'] == 1:
            return f'{E(t["team"])} won for the first time, {me:.0f}&ndash;{them:.0f} over {E(who)}'
        if t['streak_kind'] == 'W' and t['streak_n'] >= 3:
            return (f'{E(t["team"])} have won {NUM_W[t["streak_n"]]} straight, the latest '
                    f'{me:.0f}&ndash;{them:.0f} over {E(who)}')
        if t['streak_kind'] == 'L' and t['streak_n'] >= 3:
            return (f'{E(t["team"])} have lost {NUM_W[t["streak_n"]]} in a row, the latest '
                    f'{me:.0f}&ndash;{them:.0f} to {E(who)}')
        if m > 45:
            return (f'{E(t["team"])} {"beat" if won else "lost to"} {E(who)} by '
                    f'{m:.0f}')
        if m < 6:
            return (f'{E(t["team"])} {"survived" if won else "fell to"} {E(who)} by {m:.1f}')
        return f'{E(t["team"])} {"beat" if won else "lost to"} {E(who)} {me:.0f}&ndash;{them:.0f}'

    def stake(a, b, first):
        left = max(0, int(st['playoff_week']) - 1 - int(st['through']))
        wks = f'{NUM_W[left] if left < len(NUM_W) else left} week{"" if left == 1 else "s"}'
        if a['div'] == b['div']:
            gap = a['w'] - b['w']
            dv = E(a['div_name'])
            if first:
                return ('It is a division game as well, and the one that decides ' + dv +
                        (f': {E(a["team"])} lead by '
                         f'{NUM_W[gap] if gap < len(NUM_W) else gap} with {wks} to play'
                         if gap else ', with the two of them level at the top of it'))
            return (f'{E(a["team"])} are {NUM_W[gap] if gap < len(NUM_W) else gap} clear of '
                    f'them in {dv}' if gap else f'They are level in {dv}')
        return (f'{ORD_W[a["seed"]].capitalize()} plays '
                f'{ORD_W[b["seed"]] if b["seed"] < len(ORD_W) else str(b["seed"]) + "th"}')

    out = []
    for n, (a, b) in enumerate(pairs):
        first = n == 0
        head = (f'<b>{E(a["team"])} ({a["record"]}) play {E(b["team"])} ({b["record"]})</b>'
                + (' in the game of the week' if first else ''))
        bits = [f'{head}. {stake(a, b, first)}.']
        bits.append(form(a) + '; ' + form(b) + '.')
        if b['l'] == 0 and b['t'] == 0:
            bits.append(f'{E(b["team"])} have not lost yet.')
        elif a['l'] == 0 and a['t'] == 0 and not first:
            bits.append(f'{E(a["team"])} have not lost yet.')
        out.append(('body', '<p class="b">' + ' '.join(bits) + '</p>'))
    return out


def team_lines(season, week, st, stories):
    """One short line per team: what they just did, and what is next.

    Not an essay each. The shape John asked for is conversational and two
    clauses long -- "got their first win, and will struggle to add to it next
    week against a side that has not lost" -- so each line is the strongest
    true thing about their week followed by the strongest true thing about
    their next opponent. Both halves are picked from what the data actually
    supports, and a team with nothing remarkable either side gets the plain
    version rather than an invented angle.
    """
    nxt = week + 1
    try:
        sc = json.load(open(os.path.join(ROOT, 'sleeper-schedule.json'), encoding='utf-8'))
        fixtures = sc['weeks'].get(str(nxt)) or []
    except Exception:
        fixtures = []
    by = {r['roster_id']: r for r in st['table']}
    opp = {}
    for g in fixtures:
        h, a = g.get('home_roster'), g.get('away_roster')
        if h in by and a in by:
            opp[h], opp[a] = by[a], by[h]

    def did(t):
        """What they just did."""
        leg = (t.get('trail') or [])[-1] if t.get('trail') else None
        if not leg:
            return 'sat out'
        _, res, me, them, who = leg
        m = abs(me - them)
        won = res == 'W'
        pts = [x[2] for x in t['trail']]
        if won and t['w'] == 1:
            return f'got their first win of the season, {me:.0f}&ndash;{them:.0f} over {E(who)}'
        if t['streak_kind'] == 'W' and t['streak_n'] >= 3:
            return (f'made it {NUM_W[t["streak_n"]]} in a row, '
                    f'{me:.0f}&ndash;{them:.0f} over {E(who)}')
        if t['streak_kind'] == 'L' and t['streak_n'] >= 3:
            return (f'lost their {ORD_W[t["streak_n"]]} in a row, '
                    f'{me:.0f}&ndash;{them:.0f} to {E(who)}')
        if me == max(pts) and len(pts) > 2:
            return (f'posted a season-best {me:.0f} '
                    + ('and won' if won else 'and lost anyway'))
        if me == min(pts) and len(pts) > 2:
            return (f'scraped a season-low {me:.0f} '
                    + ('and won anyway' if won else 'in defeat'))
        if m < 6:
            return (f'{"edged" if won else "lost to"} {E(who)} by {m:.1f}')
        if m > 45:
            return (f'{"ran over" if won else "were run over by"} {E(who)} by {m:.0f}')
        return f'{"beat" if won else "lost to"} {E(who)} {me:.0f}&ndash;{them:.0f}'

    def ahead(t):
        """What is next, and why it is hard or not."""
        o = opp.get(t['roster_id'])
        if not o:
            return ''
        if o['l'] == 0 and o['t'] == 0:
            return (f'and will struggle to add to it against {E(o["team"])}, who have not lost'
                    if t['w'] == 1 and t['streak_kind'] == 'W'
                    else f'and get {E(o["team"])} next, still unbeaten at {o["record"]}')
        if o['streak_kind'] == 'W' and o['streak_n'] >= 3:
            return (f'and face {E(o["team"])} next, winners of '
                    f'{NUM_W[o["streak_n"]]} straight')
        if o['streak_kind'] == 'L' and o['streak_n'] >= 3:
            return (f'and get {E(o["team"])} next, who have lost {NUM_W[o["streak_n"]]} '
                    f'on the spin')
        if t['div'] == o['div'] and abs(t['seed'] - o['seed']) <= 3:
            return (f'and meet {E(o["team"])} next in {a_div(t["div_name"])} that '
                    f'{"could close the gap" if t["seed"] > o["seed"] else "could open it up"}')
        if o['seed'] <= 4:
            return f'and draw {E(o["team"])} next, {ORD_W[o["seed"]]} in the table'
        if o['seed'] >= 13:
            tag = ('but coming off a win' if o['streak_kind'] == 'W'
                   else 'and sinking')
            return (f'and get {E(o["team"])} next, '
                    f'{ORD_W[o["seed"]] if o["seed"] < len(ORD_W) else str(o["seed"]) + "th"} '
                    f'{tag}')
        return f'and play {E(o["team"])} next'

    rows = ''
    for t in st['table']:
        tail = ahead(t)
        rows += (f'<tr><th scope="row" class="lt">{E(t["team"])}<br>'
                 f'<span class="dim">{t["record"]} &middot; {ORD_W[t["seed"]] if t["seed"] < len(ORD_W) else str(t["seed"]) + "th"}</span></th>'
                 f'<td class="dim ev">{upper1(did(t))}'
                 + (', ' + tail if tail else '') + '.</td></tr>')
    return rows


def preview_blocks(season, week, st):
    """Next week's card, and what is actually at stake in each game.

    Every issue ends here. The notes are derived rather than written: the
    fixtures come out of sleeper-schedule.json, the records and streaks out of
    the table, and each line is the strongest TRUE thing available about that
    pairing. A preview that says "should be a good one" eight times is worse
    than no preview, so a game with nothing to say about it gets the bare
    records and no invented tension.

    Teams are matched on roster_id. Franchises get renamed mid-season here and
    the schedule file still carries the name a side had in August.
    """
    nxt = week + 1
    try:
        sc = json.load(open(os.path.join(ROOT, 'sleeper-schedule.json'), encoding='utf-8'))
        games = sc['weeks'][str(nxt)]
    except Exception:
        return []
    if not games or nxt >= int(st.get('playoff_week') or 99):
        return []
    by = {r['roster_id']: r for r in st['table']}

    def note(a, b):
        """The strongest true thing about this pairing, or nothing."""
        n = []
        if a['l'] == 0 and b['l'] == 0:
            n.append('both unbeaten')
        if a['div'] == b['div']:
            lead_, chase = (a, b) if a['seed'] < b['seed'] else (b, a)
            gap = (lead_['w'] - chase['w'])
            n.append(f'{E(lead_["div_name"])}: {E(lead_["team"])} '
                     + (f'{gap} clear of {E(chase["team"])}' if gap
                        else f'and {E(chase["team"])} level'))
        for t, o in ((a, b), (b, a)):
            if t['streak_n'] >= 3:
                n.append(f'{E(t["team"])} has {"won" if t["streak_kind"] == "W" else "lost"} '
                         f'{NUM_W[t["streak_n"]] if t["streak_n"] < len(NUM_W) else t["streak_n"]}'
                         f' in a row')
        # have they already met this season, and how did it go
        for leg in a.get('trail') or []:
            if leg[4].strip() == b['team'].strip():
                n.append(f'{E(b["team"])} won the first meeting {leg[3]:.0f}&ndash;{leg[2]:.0f}'
                         if leg[1] == 'L' else
                         f'{E(a["team"])} won the first meeting {leg[2]:.0f}&ndash;{leg[3]:.0f}')
                break
        return n[:2]

    pairs = []
    for g in games:
        a, b = by.get(g.get('home_roster')), by.get(g.get('away_roster'))
        if a and b:
            pairs.append((a, b) if a['seed'] <= b['seed'] else (b, a))
    # The fixture worth billing: the two best-placed sides meeting. Without it
    # the one game anybody is waiting for sits fourth in a list of eight,
    # indistinguishable from a game between the twelfth and the fifteenth.
    pick = min(pairs, key=lambda x: x[0]['seed'] + x[1]['seed']) if pairs else None
    pairs.sort(key=lambda x: x[0]['seed'] + x[1]['seed'])

    rows = ''
    for hi, lo in pairs:
        ns = note(hi, lo)
        top = pick is not None and (hi, lo) == pick
        rows += (f'<tr{" class=hot" if top else ""}>'
                 f'<th scope="row" class="lt">{"&#9654; " if top else ""}{E(hi["team"])} '
                 f'<span class="dim">{hi["record"]}</span><br>'
                 f'{E(lo["team"])} <span class="dim">{lo["record"]}</span></th>'
                 f'<td class="num dim">{hi["seed"]}<br>{lo["seed"]}</td>'
                 f'<td class="dim ev">'
                 + (('<b>The one to watch.</b> ' if top else '')
                    + ('. '.join(ns) + '.' if ns else ('' if top else '&mdash;')))
                 + '</td></tr>')
    bill = (f'<p class="b">The one to watch is <b>{E(pick[0]["team"])} against '
            f'{E(pick[1]["team"])}</b>, the best-placed pair on the card'
            + (f' and a {E(pick[0]["div_name"])} game with it'
               if pick[0]['div'] == pick[1]['div'] else '')
            + f'. The rest, in order of what the table says they are worth, follow it. Seeds '
              f'are as they stand after week {week}.</p>') if pick else ''
    out = preview_prose(season, week, st) + [('pagebreak', bill),
           ('body', f'<div class="ad"><figure><div class="scroll"><table><thead><tr>'
                    f'<th class="lt">Week {nxt}</th><th class="num">Seed</th>'
                    f'<th class="lt">What is at stake</th></tr></thead>'
                    f'<tbody>{rows}</tbody></table></div></figure></div>')]
    ub = [t for t in st['table'] if t['l'] == 0 and t['t'] == 0]
    tail = []
    if ub:
        tail.append(f'{" and ".join(E(t["team"]) for t in ub)} '
                    f'{"are" if len(ub) > 1 else "is"} still unbeaten.')
    left = max(0, int(st['playoff_week']) - 1 - int(st['through']))
    tail.append(f'{NUM_W[left].capitalize() if left < len(NUM_W) else left} week'
                f'{"" if left == 1 else "s"} of the regular season remain, and the playoffs '
                f'begin in week {st["playoff_week"]}.')
    out.append(('body', '<p class="b">' + ' '.join(tail) + '</p>'))
    return out


def coverlines(season, week, d, stories, lead, st):
    """What the cover promises, computed from what is actually inside it.

    These used to be the five closest finals plus the biggest rout, which is a
    rule but does not look like one from the outside: six scores in a column,
    no reason given for any of them, and not one of them telling you what is in
    the magazine. A cover line is a billing. Every one of these names a piece
    that is in the issue and carries the figure that makes it worth reading,
    and every figure is derived here rather than typed.
    """
    out = []
    # the feature, in its own words -- the continuation parts are not separate
    # billings, so only the first is taken. Skipped when the feature IS the
    # hook: billing it twice on the same cover reads as a mistake.
    _, from_feature = cover_source(d, stories, lead)
    if from_feature:
        # the game of the week has lost the hook to the feature, so it takes a
        # billing instead -- otherwise the biggest game in the issue is the one
        # thing the cover does not mention
        out.append(stories[lead]['headline'].upper())
    else:
        for f in (d.get('features') or [])[:1]:
            out.append(f['headline'].upper())

    # the week's biggest score, but only worth a line if it is historically big
    hi = max(((s['score'][i], s['winner'] if i == 0 else s['loser'])
              for s in stories for i in (0, 1)))
    rank = alltime_rank(hi[0])
    if rank <= 10:
        # "on record" and not "ever": the book starts in 2008
        out.append(f'{hi[1].upper()} {hi[0]:.2f}: {ORD_W[rank].upper()}-BIGGEST '
                   f'WEEK ON RECORD')

    # how the game of the week was actually a game
    try:
        rp = json.load(open(os.path.join(WDIR, f'{season}-w{week}-replay.json'),
                            encoding='utf-8'))
        n = rp['games'][lead]['lead_changes']
    except Exception:
        n = 0
    if n:
        out.append(f'{NUM_W[n].upper() if n < len(NUM_W) else n} LEAD CHANGE'
                   f'{"" if n == 1 else "S"} IN THE GAME OF THE WEEK')

    big = max(stories, key=lambda s: s['margin'])
    out.append(f'THE ROUT: {big["winner"].upper()} BY {big["margin"]:.0f}')

    # who is still unbeaten, which is the table's one line worth the cover
    ub = [t for t in (st or {}).get('table', []) if t['l'] == 0 and t['t'] == 0]
    if ub and len(ub) <= 3:
        # one record for all of them only if they really do share one: two
        # unbeaten teams a game apart would otherwise both be billed at the
        # first one's record
        same = len({t['record'] for t in ub}) == 1
        who = (' AND '.join(t['team'].upper() for t in ub) if same else
               ' AND '.join(f'{t["team"].upper()} {t["record"]}' for t in ub))
        out.append(f'{who} STILL UNBEATEN' + (f' AT {ub[0]["record"]}' if same else ''))
    elif st and st.get('table'):
        t = st['table'][0]
        out.append(f'{t["team"].upper()} TOP OF THE TABLE AT {t["record"]}')
    return out


def build(season, week, remeasure=True):
    # A written file, when there is one, beats the generated stories. The
    # template can report a game; it cannot have a view about one, and a beat
    # report is mostly view. Generation stays as the floor for a week nobody
    # had time to write.
    pw = os.path.join(WDIR, f'{season}-w{week}-written.json')
    p = os.path.join(WDIR, f'{season}-w{week}-stories.json')
    if os.path.exists(pw):
        d = json.load(open(pw, encoding='utf-8'))
        print(f'  using the written stories ({os.path.basename(pw)})')
    elif os.path.exists(p):
        d = json.load(open(p, encoding='utf-8'))
    else:
        sys.exit(f'no stories for week {week} -- run scripts/write_week.py --week {week}')
    stories, lead = d['stories'], d['lead']

    # lead story first, then the rest by how much there is to say about them
    order = [lead] + sorted((i for i in range(len(stories)) if i != lead),
                            key=lambda i: (stories[i]['arc'] == 'rout', stories[i]['margin']))

    st = sd.build(str(season), int(week))
    arts = [{'id': 'wk-scoreboard', 'flag': 'The Scoreboard',
             'headline': f'Week {week}, Settled',
             'subhead': 'Eight games, every one of them rebuilt from the tape.',
             'blocks': scoreboard_blocks(stories)}]
    if st:
        arts.append({'id': 'wk-standings', 'flag': 'The Table',
                     'headline': f'Where Everyone Stands',
                     'subhead': f'Through week {st["through"]} of the {season} season.',
                     'blocks': standings_blocks(st)})
    # Features sit after the scoreboard and the table and before the game
    # reports: a piece about the week is not a report on one game in it, and
    # burying it at the back of eight match reports is where features go to die.
    for n, f in enumerate(d.get('features') or []):
        arts.append({
            'id': f'wk{week}-f{n}',
            'flag': f.get('flag', 'The Feature'),
            'headline': f['headline'],
            'subhead': f['dek'],
            'paragraphs': f['paragraphs'],
        })

    mu = matchups(season, week, stories)
    for n, i in enumerate(order):
        s = stories[i]
        arts.append({
            'id': f'wk{week}-g{i}',
            'flag': (f'The Game of the Week \u00b7 {mu[i]}' if i == lead and i in mu
                     else 'The Game of the Week' if i == lead
                     else mu.get(i) or f'Game {ORD.get(n, n)}'),
            'headline': s['headline'],
            'subhead': s['dek'],
            'paragraphs': s['paragraphs'],
        })
        # A report with more in it than a page holds runs on, rather than being
        # shrunk to fit. The fitter will take a single page down as far as it
        # has to -- the record week went to 0.663 zoom, two thirds the type size
        # of the reports either side of it, which is not a page anybody reads.
        # Carrying it is what a magazine does; the jump keeps its own headline
        # so it is still a page and not an orphan.
        if s.get('part2'):
            p2 = s['part2']
            arts.append({
                'id': f'wk{week}-g{i}b',
                'flag': p2.get('flag', 'Continued'),
                'headline': p2['headline'],
                'subhead': p2['dek'],
                'paragraphs': p2['paragraphs'],
            })

    # Every issue closes on what is next. A magazine that stops on the last
    # result is a record; one that says what Sunday is worth is a magazine.
    pv = preview_blocks(season, week, st)
    if pv:
        arts.append({'id': f'wk{week}-next',
                     'flag': f'The Preview \u00b7 Week {week + 1}',
                     'headline': 'What Sunday Is Worth',
                     'subhead': f'Eight games, sixteen teams, and what week '
                                f'{week + 1} does to the table.',
                     'blocks': pv})

    out = f'scfl-week-{week}-issue.html'
    key = f'week-{week}'
    ls = stories[lead]
    cs, _cf = cover_source(d, stories, lead)
    big = max(stories, key=lambda s: s['margin'])
    lines = coverlines(season, week, d, stories, lead, st)
    bi.ISSUES[key] = {
        'out': out,
        'title': f'The Week {week} Issue',
        'tagline': f'Week {week} of the 2026 season',
        'dateline': f'Week {week}, {season}',
        'runhead': f'Skirt Chasers &middot; Week {week} &middot; {season}',
        'art': f'scfl-week-{week}-cover.jpg',
        'og': f'scfl-week-{week}-og.jpg',
        'ogtitle': f'Skirt Chasers — The Week {week} Issue',
        # game time here too: the share blurb is the first thing anybody reads,
        # and naming broadcast windows gives away the trick the replay exists for
        'ogdesc': (f'{cs["headline"]}. Eight games rebuilt play by play, from the opening '
                   f'drive to the last snap of the fourth.'),
        'sharetext': f'Week {week}, replayed from the tape. Sixty minutes, eight games.',
        'kicker': f'The Magazine · Week {week}',
        'seal': (f'Week', f'{week}'),
        'issueline': f'2026&ndash;27 Season &middot; Week {week}',
        'hook': cs['headline'],
        'hooksub': cs['dek'],
        'coverlines': lines,
        'articles': [],
        'arts_inline': arts,
        # opener art, keyed by the article id the builder assigns. Features are
        # wk{week}-f{n}; a file that is not there simply opens typographically.
        'openart': {f'wk{week}-f{n}': f
                    for n, f in enumerate(d.get('art') or [])
                    if f},
    }
    # ---- one article, one page -------------------------------------------
    # The greedy packer fills pages to the brim, so a long game report spills
    # onto a continuation page and the issue stops reading as a magazine. Here
    # the page breaks are not measured at all: they are exactly the article
    # boundaries. Anything that then does not fit is shrunk to fit, which is
    # what a page layout does when the copy runs long.
    here = os.path.join(ROOT, 'scripts')
    bi.build(key, remeasure=False, quiet=True)          # emits .pack-kinds.json
    kinds = json.load(open(os.path.join(here, '.pack-kinds.json'), encoding='utf-8'))
    breaks = [i for i, k in enumerate(kinds) if k in ('divider', 'pagebreak')]
    json.dump(breaks, open(os.path.join(here, f'.pack-breaks-{key}.json'), 'w'))
    bi.build(key, remeasure=False, quiet=True)
    if remeasure:
        fit(out)
    inline_assets(out)
    return out


def inline_assets(out):
    """Embed the cover, masthead and shield so the file works on its own.

    The issue referenced them relatively, which is correct on the site and
    useless anywhere else: opened from a download, or sent to somebody, the
    cover came up black and the masthead did not come up at all. A magazine
    you cannot send is not much of a magazine, so the weekly issue carries its
    own pictures.
    """
    import base64, re as _re
    path = os.path.join(ROOT, out)
    html = open(path, encoding='utf-8').read()
    done, total = [], 0
    for fn in sorted(set(_re.findall(r'["\'(]([A-Za-z0-9._-]+\.(?:png|jpg|jpeg|svg))["\')]',
                                     html))):
        src = os.path.join(ROOT, fn)
        if not os.path.exists(src):
            continue
        mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                'svg': 'image/svg+xml'}[fn.rsplit('.', 1)[1].lower()]
        b = open(src, 'rb').read()
        uri = f'data:{mime};base64,' + base64.b64encode(b).decode('ascii')
        before = html
        html = html.replace(f"'{fn}'", f"'{uri}'").replace(f'"{fn}"', f'"{uri}"')
        if html != before:
            done.append(fn)
            total += len(b)
    open(path, 'w', encoding='utf-8').write(html)
    print(f'  inlined {len(done)} assets ({total/1024:.0f}kb): ' + ', '.join(done))


def fit(out):
    """Scale down any page whose article runs past the bottom."""
    import re as _re, subprocess
    try:
        r = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'fit_pages.js'), out,
                            'http://localhost:8991'],
                           capture_output=True, text=True, cwd=ROOT, timeout=180,
                           env=dict(os.environ, NODE_PATH='/opt/node22/lib/node_modules'))
        zooms = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:
        print(f'  note: could not measure the fit ({e}); pages left at full size')
        return
    path = os.path.join(ROOT, out)
    html = open(path, encoding='utf-8').read()
    n = [0]

    def sub(m):
        i = n[0]; n[0] += 1
        z = zooms[i] if i < len(zooms) else 1
        return m.group(0) if z >= 0.999 else f'<div class="page-inner" style="zoom:{z}">'

    html = _re.sub(r'<div class="page-inner">', sub, html)
    open(path, 'w', encoding='utf-8').write(html)
    tight = [(i, z) for i, z in enumerate(zooms) if z < 0.999]
    print(f'  fitted {len(tight)} of {len(zooms)} pages' +
          (f' (smallest {min(z for _, z in tight):.3f})' if tight else ''))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, required=True)
    ap.add_argument('--season', default='2026')
    ap.add_argument('--no-measure', action='store_true')
    a = ap.parse_args()
    out = build(a.season, a.week, remeasure=not a.no_measure)
    print(f'  -> {out}')


if __name__ == '__main__':
    main()
