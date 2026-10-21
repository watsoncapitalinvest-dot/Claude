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
_h = importlib.util.spec_from_file_location('hist', os.path.join(ROOT, 'scripts', 'history.py'))
history = importlib.util.module_from_spec(_h); sys.modules['hist'] = history
_h.loader.exec_module(history)
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


PER_PAGE = 4          # preview paragraphs to a page; see preview_prose()
ORD_W = ['', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh',
         'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth', 'thirteenth',
         'fourteenth', 'fifteenth', 'sixteenth']
NUM_W = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
         'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
         'sixteen']


# The tables stop at ten and at twelve; seeds run to sixteen and a losing run
# can pass twelve. Every lookup goes through these, because the half of them
# that carried an inline guard and the half that did not is exactly how a week
# 5 rebuild died on an eleventh seed. Numerals past the table are correct with
# a plain 'th' for everything a 16-team league can produce.
def ordw(n):
    return ORD_W[n] if 0 <= n < len(ORD_W) else f'{n}th'


def numw(n):
    return NUM_W[n] if 0 <= n < len(NUM_W) else str(n)


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

    A preview is about what happens next. The first two versions of this were
    about what had already happened -- two sentences of last week's scores a
    paragraph, and a line of forward-looking copy if there was room -- which
    is a results service with a date on it. So the weight is the other way
    round now: what the result does to the records, the division and the table
    comes first and always, last week appears only where it carries a hook,
    and the closing line is about Sunday rather than about last Sunday.

    The voice is Harry Doyle -- dry, flat, short sentences, funniest when it
    is most matter-of-fact.

    Everything is still derived, and the forward half is derived too: a record
    after a win is arithmetic, a division gap after a win is arithmetic, and a
    second meeting is in the schedule file. Nothing here projects a score or a
    winner, because nothing in this repo can. Where a claim would depend on
    points for -- any claim about where a side would SIT in a table tiebroken
    on points -- it is not made.
    """
    nxt = week + 1
    try:
        sc = json.load(open(os.path.join(ROOT, 'sleeper-schedule.json'), encoding='utf-8'))
        fixtures = sc['weeks'].get(str(nxt)) or []
    except Exception:
        return []
    if not fixtures or nxt >= int(st.get('playoff_week') or 99):
        return []
    tbl = st['table']
    by = {r['roster_id']: r for r in tbl}
    by_name = {r['team'].strip(): r for r in tbl}
    pairs = []
    for g in fixtures:
        a, b = by.get(g.get('home_roster')), by.get(g.get('away_roster'))
        if a and b:
            pairs.append((a, b) if a['seed'] <= b['seed'] else (b, a))
    pairs.sort(key=lambda x: x[0]['seed'] + x[1]['seed'])

    clear_best = (len(pairs) > 1
                  and pairs[0][0]['seed'] + pairs[0][1]['seed']
                  < pairs[1][0]['seed'] + pairs[1][1]['seed'])
    left = max(0, int(st['playoff_week']) - 1 - int(st['through']))
    after_left = max(0, left - 1)
    rest = f'{numw(after_left)} week{"" if after_left == 1 else "s"}'
    last_seed = max(r['seed'] for r in tbl)

    def meet_again(a, b):
        """The next week after this one that the schedule has them meeting."""
        for w in sorted(int(k) for k in sc['weeks']):
            if w <= nxt or w >= int(st.get('playoff_week') or 99):
                continue
            for g in sc['weeks'][str(w)]:
                ids = {g.get('home_roster'), g.get('away_roster')}
                if ids == {a['roster_id'], b['roster_id']}:
                    return w
        return None

    def rec(t, won):
        w = t['w'] + (1 if won else 0)
        return f'{w}-{t["l"] + (0 if won else 1)}' + (f'-{t["t"]}' if t['t'] else '')

    def div_top(t):
        return max(r['w'] for r in tbl if r['div'] == t['div'])

    def leg(t):
        return (t.get('trail') or [None])[-1]

    def sc_(me, them):
        return f'{me:.0f}&ndash;{them:.0f}'

    def winless_until(name, wk):
        o = by_name.get((name or '').strip())
        if not o:
            return False
        won = [x for x in o['trail'] if x[1] == 'W' and x[0] <= wk]
        return len(won) == 1 and won[0][0] == wk

    def prospect(a, b, n, first):
        """What the afternoon does. Always present, always first.

        Only claims that the fixture itself settles. A projected DIVISION
        POSITION is not one of them: the other two sides in a division are
        playing on the same Sunday and can gain a win too, so "level at the
        top of Spectre Syndicate" was a guess dressed as arithmetic. What the
        game does settle exactly is each side's record and the gap between
        these two -- so that is what this says, and anything about the rest of
        the division is said in the present tense about the table as it is.
        """
        dv = E(a['div_name'])
        if a['div'] == b['div']:
            gap = a['w'] - b['w']
            if gap == 0:
                out = [f'The winner leaves at {rec(a, True)} and a game clear of the loser '
                       f'in {dv}.',
                       f'One of them leaves at {rec(a, True)} and the other at '
                       f'{rec(a, False)}, and that is the whole of {dv} for a week.',
                       f'{rec(a, True)} for the winner, {rec(a, False)} for the loser, and a '
                       f'game between them in {dv}.'][n % 3]
            else:
                lead = f'{numw(gap + 1)} clear of them'
                chase = ('level with them' if gap == 1 else f'{numw(gap - 1)} behind them')
                out = (f'{E(a["team"])} win and they are {rec(a, True)}, {lead} in {dv}. '
                       f'{E(b["team"])} win and they are {rec(b, True)}, {chase}.')
            if a['div_rank'] == 1 and b['div_rank'] == 2:
                out = f'These are the top two in {dv}. ' + out.replace(f' in {dv}', '', 1)
            return out
        out = (f'{E(a["team"])} win and they are {rec(a, True)}; {E(b["team"])} win and they '
               f'are {rec(b, True)}.')
        # one present-tense line about whichever of them has further to go
        t = max((a, b), key=lambda r: div_top(r) - r['w'])
        back = div_top(t) - t['w']
        if back >= 2:
            out += ' ' + [f'{E(t["team"])} are {numw(back)} off the top of '
                          f'{E(t["div_name"])} as the table stands.',
                          f'{E(t["team"])} have {numw(back)} games to find on '
                          f'{E(t["div_name"])} from where they are.',
                          f'That still leaves {E(t["team"])} {numw(back)} short of the top '
                          f'of {E(t["div_name"])}.'][n % 3]
        return out

    def form(t, k, covered=False):
        """Last week, but only when last week is worth a sentence.

        Returns '' for an ordinary result. Eight paragraphs that each recite
        two scorelines is the thing this article was rewritten to stop doing.
        """
        lg = leg(t)
        if not lg:
            return ''
        wk, res, me, them, opp = lg
        won, m = res == 'W', abs(me - them)
        who = E(t['team'])
        if won and t['w'] == 1:
            return f'{who} won for the first time this season last week, {sc_(me, them)}.'
        if t['streak_n'] >= 3:
            if covered:
                return ''
            run = numw(t['streak_n'])
            return (f'{who} have won {run} in a row and a fourth makes it {rec(t, True)}.'
                    if t['streak_kind'] == 'W' and t['streak_n'] == 3 else
                    f'{who} have won {run} in a row.' if t['streak_kind'] == 'W' else
                    f'{who} have lost {run} in a row.')
        if won and m > 45:
            return [f'{who} put {me:.0f} on {E(opp)} last week, which is less a result than '
                    'a weather report.',
                    f'{who} won by {m:.0f} last week, which is not a margin but a verdict.',
                    f'{who} won {sc_(me, them)} last week, and the second number is not a '
                    'misprint.'][k % 3]
        if not won and m > 45:
            return [f'{who} were beaten by {m:.0f} last week, which takes a certain '
                    'commitment.',
                    f'{who} lost by {m:.0f} last week.',
                    f'{who} were beaten {sc_(me, them)} last week, which is a scoreline you '
                    'check twice.'][k % 3]
        if m < 6:
            return ([f'{who} got past {E(opp)} by {m:.1f} last week, which counts the same '
                     'as fifty.',
                     f'{who} won by {m:.1f} last week, and the table does not ask how.',
                     f'{who} won by {m:.1f} last week, which is a win.'][k % 3] if won else
                    [f'{who} lost by {m:.1f} last week.',
                     f'{who} came up {m:.1f} short last week, which is the worst way to do it.',
                     f'{who} lost by {m:.1f}, and have had a week to think about it.'][k % 3])
        if not won and winless_until(opp, wk):
            return f'{who} lost to a side that had not won a game.'
        return ''

    hist = history.load().bind(tbl)
    if hist.unresolved:
        print('  note: no history for', ', '.join(hist.unresolved))
    most_titles = max((hist.alltime(r['roster_id']) or {}).get('titles', 0) for r in tbl)
    used = []

    def thread(a, b, n):
        """One line of history. Eighteen seasons is a lot of threads to pull.

        Everything here is the stored series or the stored all-time table with
        this season added -- rivalries.json stops at 2025, so quoting it raw
        would publish a head-to-head that is a year stale and looks exactly
        like a current one.
        """
        s_ = hist.series(a, b, st)
        A, B = E(a['team']), E(b['team'])
        if s_ and s_['g'] >= 10:
            hi, lo = ((a, b) if s_['w'] >= s_['l'] else (b, a))
            hw, hl = (s_['w'], s_['l']) if s_['w'] >= s_['l'] else (s_['l'], s_['w'])
            # the stored row stops at 2025, so naming WHICH game the one
            # defeat was is only safe when the one defeat cannot be a 2026 one
            if hw / s_['g'] >= 0.78 and hl == 1 and s_['worst'] and not s_['this_season']:
                g_ = s_['worst'] if s_['w'] >= s_['l'] else s_['biggest']
                when = (f"a {g_['y']} playoff game" if g_ and g_.get('po')
                        else f"week {g_['wk']} of {g_['y']}" if g_ else 'once')
                t = (f'{E(lo["team"])} have beaten {E(hi["team"])} once in '
                     f'{numw(s_["g"])} meetings, and it was {when}.')
                if t and (r := _cap('lopsided', t)):
                    return r
            elif hw / s_['g'] >= 0.75:
                t = (f'{E(hi["team"])} have won {numw(hw)} of the {numw(s_["g"])} they have '
                     f'played, going back to {s_["first"]}.')
                if r := _cap('lopsided', t):
                    return r
        if s_ and s_['w'] == s_['l'] and s_['g'] >= 8:
            if r := _cap('level', f'They have played {numw(s_["g"])} times and won '
                                  f'{numw(s_["w"])} each.'):
                return r
        if s_ and (s_['porec'] or {}).get('w', 0) + (s_['porec'] or {}).get('l', 0) >= 2:
            pw, pl = s_['porec']['w'], s_['porec']['l']
            tot, best = pw + pl, max(pw, pl)
            lead = A if pw >= pl else B
            how = ('and they have split them.' if pw == pl else
                   f'and {lead} won both.' if best == tot == 2 else
                   f'and {lead} won them all.' if best == tot else
                   f'and {lead} won {numw(best)} of them.')
            t = f'{upper1(numw(tot))} of their meetings have been playoff games {how}'
            if r := _cap('playoffs', t):
                return r
        if s_ and s_['closest'] and abs(s_['closest']['for'] - s_['closest']['against']) <= 1:
            c = s_['closest']
            m = abs(c['for'] - c['against'])
            t = (f'One of these finished {c["for"]:.0f}&ndash;{c["against"]:.0f} in {c["y"]}.'
                 if m else f'One of these finished level, {c["for"]:.0f} each, in {c["y"]}.')
            if r := _cap('closest', t):
                return r
        if s_ and s_['streak'] and s_['streak']['n'] >= 3:
            wn = A if s_['streak']['kind'] == 'W' else B
            if r := _cap('streak', f'{wn} have won the last {numw(s_["streak"]["n"])}.'):
                return r
        la, lb = hist.alltime(a['roster_id'], tbl), hist.alltime(b['roster_id'], tbl)
        if la and lb and la['titles'] != lb['titles'] and max(la['titles'], lb['titles']):
            t_, o_ = (a, la) if la['titles'] > lb['titles'] else (b, lb)
            t = (f'{E(t_["team"])} have {numw(o_["titles"])} '
                 + ('title' if o_['titles'] == 1 else 'titles')
                 + (', which is more than anybody.' if o_['titles'] == most_titles
                    else ' to their name.'))
            if r := _cap('titles', t):
                return r
        if la and lb:
            t = (f'{A} are {la["record"]} all time; {B} are {lb["record"]}.')
            if r := _cap('lifetime', t):
                return r
        if s_ and s_['g'] >= 16:
            lead = A if s_['w'] >= s_['l'] else B
            t = (f'This is the {ordw(s_["g"] + 1)} meeting since {s_["first"]}, and '
                 f'{lead} leads it {max(s_["w"], s_["l"])}&ndash;{min(s_["w"], s_["l"])}.')
            if r := _cap('long', t):
                return r
        if s_ and s_['first']:
            if r := _cap('first', f'They have been doing this since {s_["first"]}.'):
                return r
        return ''

    def _cap(tag, text, cap=2):
        if sum(1 for x in used if x == tag) >= cap:
            return ''
        used.append(tag)
        return text

    def kicker(a, b, n):
        """One closing line, and it points at Sunday rather than away from it."""
        if (a['streak_kind'] == 'L' and b['streak_kind'] == 'L'
                and min(a['streak_n'], b['streak_n']) >= 3):
            return ('One of these runs ends on Sunday. The other one gets longer.')
        if (a['streak_kind'] == 'W' and b['streak_kind'] == 'W'
                and min(a['streak_n'], b['streak_n']) >= 3):
            return ('Both of them arrive on a run of three or more. One of them does not '
                    'leave with it.')
        for t, o in ((a, b), (b, a)):
            if t['l'] == 0 and t['t'] == 0 and t['games'] >= 3:
                return (f'{E(t["team"])} have not lost a game, and {E(o["team"])} are the '
                        f'{ordw(t["games"] + 1)} side asked to do something about it.')
        w = meet_again(a, b)
        if w and 'again' not in used:
            used.append('again')
            return f'They do this again in week {w}, so nobody settles anything on Sunday.'
        for lg in a.get('trail') or []:
            if (lg[4] or '').strip() == b['team'].strip():
                win = a if lg[1] == 'W' else b
                hi, lo = (lg[2], lg[3]) if lg[1] == 'W' else (lg[3], lg[2])
                return (f'{E(win["team"])} won the first meeting in week {lg[0]}, '
                        f'{sc_(hi, lo)}, and that is the only evidence anybody has.')
        for t in (a, b):
            if t['seed'] == last_seed:
                return (f'{E(t["team"])} are {ordw(t["seed"])} of {numw(last_seed)}. A loss '
                        f'is {rec(t, False)} with {rest} to play.')
        return ''

    unb = [r for r in tbl if r['l'] == 0 and r['t'] == 0]
    runs_w = [r for r in tbl if r['streak_kind'] == 'W' and r['streak_n'] >= 3]
    runs_l = [r for r in tbl if r['streak_kind'] == 'L' and r['streak_n'] >= 3]
    lead = [f'{upper1(numw(len(pairs)))} games, and {rest} after them before the playoffs.']
    if unb:
        lead.append(f'{upper1(numw(len(unb)))} '
                    + ('side can still finish the week unbeaten' if len(unb) == 1
                       else 'sides can still finish the week unbeaten')
                    + f', {numw(len(runs_w))} arrive on a winning run of three or more and '
                    + f'{numw(len(runs_l))} on a losing one.')
    else:
        lead.append(f'Nobody is unbeaten any more, {numw(len(runs_w))} arrive on a winning '
                    f'run of three or more and {numw(len(runs_l))} on a losing one.')
    lead.append('This is what Sunday is worth.')
    out = [('body', '<p class="b">' + ' '.join(lead) + '</p>')]

    for n, (a, b) in enumerate(pairs):
        first = n == 0
        verb = 'play' if first else ['play', 'meet', 'get'][n % 3]
        bill = (f'<b>{E(a["team"])} ({a["record"]}) {verb} '
                f'{E(b["team"])} ({b["record"]})</b>')
        s = [bill + (', and it is the one worth sitting down for.' if first else '.')]
        if (not first and a['div'] != b['div']
                and abs(a['seed'] - b['seed']) >= 8 and a['w'] - b['w'] >= 2):
            s.append([f'{upper1(ordw(a["seed"]))} against {ordw(b["seed"])}.',
                      f'{upper1(ordw(a["seed"]))} against {ordw(b["seed"])}, which the '
                      'fixture list presumably thought was a treat for somebody.',
                      f'{upper1(ordw(a["seed"]))} against {ordw(b["seed"])}.'][n % 3])
        elif first and a['div'] != b['div']:
            s.append(f'{upper1(ordw(a["seed"]))} against {ordw(b["seed"])}'
                     + (', and nothing else on the card is close.' if clear_best
                        else ', which is the best the card had.'))
        s.append(prospect(a, b, n, first))
        k = kicker(a, b, n)
        th = thread(a, b, n)
        if th:
            s.append(th)
        covered = any(w in k for w in ('in a row', 'run of three', 'not lost a game'))
        back = ' '.join(x for x in (form(a, n, covered), form(b, n + 1, covered)) if x)
        if back:
            s.append(back)
        if k:
            s.append(k)
        # Four games a page, broken here rather than shrunk: fit() had taken
        # the whole article to 0.67, the smallest type in the issue, on the
        # page that closes it.
        out.append(('pagebreak' if n and n % PER_PAGE == 0 else 'body',
                    '<p class="b">' + ' '.join(s) + '</p>'))
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
            return (f'made it {numw(t["streak_n"])} in a row, '
                    f'{me:.0f}&ndash;{them:.0f} over {E(who)}')
        if t['streak_kind'] == 'L' and t['streak_n'] >= 3:
            return (f'lost their {ordw(t["streak_n"])} in a row, '
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
                    f'{numw(o["streak_n"])} straight')
        if o['streak_kind'] == 'L' and o['streak_n'] >= 3:
            return (f'and get {E(o["team"])} next, who have lost {numw(o["streak_n"])} '
                    f'on the spin')
        if t['div'] == o['div'] and abs(t['seed'] - o['seed']) <= 3:
            return (f'and meet {E(o["team"])} next in {a_div(t["div_name"])} that '
                    f'{"could close the gap" if t["seed"] > o["seed"] else "could open it up"}')
        if o['seed'] <= 4:
            return f'and draw {E(o["team"])} next, {ordw(o["seed"])} in the table'
        if o['seed'] >= 13:
            tag = ('but coming off a win' if o['streak_kind'] == 'W'
                   else 'and sinking')
            return (f'and get {E(o["team"])} next, '
                    f'{ordw(o["seed"])} '
                    f'{tag}')
        return f'and play {E(o["team"])} next'

    rows = ''
    for t in st['table']:
        tail = ahead(t)
        rows += (f'<tr><th scope="row" class="lt">{E(t["team"])}<br>'
                 f'<span class="dim">{t["record"]} &middot; {ordw(t["seed"])}</span></th>'
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
                         f'{numw(t["streak_n"])}'
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
    # is the top fixture clearly the top fixture, or just first on a tie
    clear_best = (len(pairs) > 1
                  and pairs[0][0]['seed'] + pairs[0][1]['seed']
                  < pairs[1][0]['seed'] + pairs[1][1]['seed'])
    left = max(0, int(st['playoff_week']) - 1 - int(st['through']))
    tail.append(f'{numw(left).capitalize()} week'
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
        out.append(f'{hi[1].upper()} {hi[0]:.2f}: {ordw(rank).upper()}-BIGGEST '
                   f'WEEK ON RECORD')

    # how the game of the week was actually a game
    try:
        rp = json.load(open(os.path.join(WDIR, f'{season}-w{week}-replay.json'),
                            encoding='utf-8'))
        n = rp['games'][lead]['lead_changes']
    except Exception:
        n = 0
    if n:
        out.append(f'{numw(n).upper()} LEAD CHANGE'
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
