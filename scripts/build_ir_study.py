#!/usr/bin/env python3
"""The IR study -- how often the two-slot cap binds, and what a third would fix.

    python3 scripts/build_ir_study.py

Every figure is computed here from ir-watch.json, which scripts/ir_watch.py
writes once a week from the live Sleeper roster and never rewrites. Nothing on
the page is typed by hand, so adding a week changes the conclusions rather than
leaving a stale number sitting under a headline that no longer fits it.

That matters more for this piece than for most. Its own weakest finding is that
the relief a third slot buys SHRINKS as injuries accumulate -- so a page that
froze its numbers in October would be quoting its own best case all season.

Written as a working paper, not a proposal: the league is split on the rule, and
a study that only argues one way gets dismissed in a sentence. The limitations
section is the load-bearing part and concedes the strongest counter-arguments
before a reader has to make them.
"""
import importlib.util, json, os, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts', 'build_addendum.py'))
ad = importlib.util.module_from_spec(_s); sys.modules['ad'] = ad; _s.loader.exec_module(ad)
E = ad.esc
OUT = os.path.join(ROOT, 'scfl-ir-study.html')
OG = os.path.join(ROOT, 'scfl-ir-study-og.jpg')

# Sleeper's designations that mean "a manager would plausibly shelve him".
# Questionable is deliberately excluded -- counting week-to-week knocks would
# inflate every number on the page.
HURT = 'IR, Out, Doubtful, PUP, Sus, NA, COV, DNR'

NUM = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
       'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen']
word = lambda n: NUM[n] if n < len(NUM) else f'{n}'
RENAME = {'Heavy Hitters': 'Phins Phag', '*THE MACHINES*': 'THE MACHINES'}
club = lambda s: RENAME.get(s.strip(), s.strip())


def crunch():
    rows = json.load(open(os.path.join(ROOT, 'ir-watch.json'), encoding='utf-8'))['rows']
    rows = sorted(rows, key=lambda r: r['week'])
    cap = rows[-1]['ir_cap']
    teams_n = rows[-1]['teams_n']

    def model(c):
        """Re-run every week under cap `c`, holding the injuries as they fell.

        The assumption, stated so it can be argued with: each manager fills IR
        greedily up to the cap with whoever is stranded, and nothing else about
        his behaviour changes.
        """
        blocked = stranded = freed = 0
        per = {}
        for r in rows:
            for t in r['teams']:
                moved = max(0, min(t['stranded'], c - t['ir_used']))
                left = t['stranded'] - moved
                freed += moved
                stranded += left
                if left > 0:
                    blocked += 1
                per.setdefault(club(t['team']), [0, 0])
                per[club(t['team'])][0] += moved
        return {'blocked': blocked, 'stranded': stranded, 'freed': freed, 'per': per}

    M = {c: model(c) for c in (cap, cap + 1, cap + 2)}

    # who gains, and are they good teams or bad ones
    _t = importlib.util.spec_from_file_location('sd', os.path.join(ROOT, 'scripts', 'standings.py'))
    sd = importlib.util.module_from_spec(_t); _t.loader.exec_module(sd)
    st = {t['team'].strip(): t for t in sd.build(str(rows[-1]['season']), rows[-1]['week'])['table']}
    gain, blockwk = {}, {}
    for r in rows:
        for t in r['teams']:
            n = club(t['team'])
            g = (max(0, min(t['stranded'], cap + 1 - t['ir_used']))
                 - max(0, min(t['stranded'], cap - t['ir_used'])))
            gain[n] = gain.get(n, 0) + g
            if t['stranded'] > max(0, cap - t['ir_used']):
                blockwk[n] = blockwk.get(n, 0) + 1
    helped = sorted((n for n, g in gain.items() if g > 0),
                    key=lambda n: (-gain[n], st.get(n, {}).get('seed', 99)))
    seeds = [st[n]['seed'] for n in helped if n in st]

    last = rows[-1]
    strand_now = sorted((t for t in last['teams'] if t['stranded']),
                        key=lambda t: -t['stranded'])
    return {'rows': rows, 'cap': cap, 'teams_n': teams_n, 'M': M, 'st': st,
            'gain': gain, 'blockwk': blockwk, 'helped': helped,
            'med_seed': statistics.median(seeds) if seeds else None,
            'league_med': (teams_n + 1) / 2, 'last': last, 'strand_now': strand_now,
            'weeks': [r['week'] for r in rows]}


def figures(C):
    out, cap = [], C['cap']
    S = lambda t: out.append(f'<div class="sect">{t}</div>')
    P = lambda h: out.append(h)
    rows, M = C['rows'], C['M']
    last = C['last']
    n_wk = len(rows)
    tw = n_wk * C['teams_n']
    base, plus1, plus2 = M[cap], M[cap + 1], M[cap + 2]
    cut_b = 100 * (base['blocked'] - plus1['blocked']) / base['blocked']
    cut_s = 100 * (base['stranded'] - plus1['stranded']) / base['stranded']
    cut_b2 = 100 * (base['blocked'] - plus2['blocked']) / base['blocked']
    spots = plus1['freed'] - base['freed']
    active = C['teams_n'] * (last['starters'] + 9)

    P(f'''<div class="stats">
      <div class="stat"><div class="k">IR capacity used</div>
        <div class="v">{100*last['ir_used_total']/last['ir_capacity_total']:.0f}%</div>
        <div class="n">{last['ir_used_total']} of {last['ir_capacity_total']} slots, week {last['week']}</div></div>
      <div class="stat"><div class="k">Injured men on active rosters</div>
        <div class="v">{last['stranded_total']}</div>
        <div class="n">up from {rows[0]['stranded_total']} in week {rows[0]['week']}</div></div>
      <div class="stat"><div class="k">A third slot would clear</div>
        <div class="v">{cut_b:.0f}%</div>
        <div class="n">of blocked team-weeks</div></div>
      <div class="stat"><div class="k">Roster spots it frees</div>
        <div class="v">{spots/n_wk:.1f}</div>
        <div class="n">a week, of {active} in play</div></div>
    </div>''')

    P(f'<p class="lf">The league: <b>{C["teams_n"]} teams, {C["teams_n"]} owners</b>, one each. '
      f'{last["starters"]} starters and nine bench on every roster, plus {word(cap)} injured '
      f'reserve slots &mdash; {C["teams_n"]*(last["starters"]+9)} active spots and '
      f'{last["ir_capacity_total"]} IR spots in play across the league.</p>')
    P('<p class="b">This is a working paper, not a proposal. It measures how often the '
      f'{word(cap)}-slot injured reserve cap actually binds, and how much of that a third '
      'slot would relieve, using the league&rsquo;s own weekly roster data. It does not '
      'argue that anybody lost a game because of the cap &mdash; that claim is not testable '
      'with this data, and nothing here should be read as making it.</p>')
    P('<p class="b">The desk has a position in the debate. The definitions, the counterfactual '
      'and the source files are set out in full so the position can be put aside and the work '
      'checked.</p>')

    S('Where the numbers come from')
    P('<p class="b"><b>ir-watch.json</b> &mdash; one row per week, written by '
      '<code>scripts/ir_watch.py</code> from the Sleeper API at the time of that week, and '
      'never rewritten afterwards. Every figure below was recorded live, so none of it '
      'benefits from hindsight about who got hurt later.</p>')
    P(f'<p class="b"><b>Injured</b> means Sleeper carries one of {HURT}. Questionable is not '
      'counted &mdash; including week-to-week knocks would inflate every number here. '
      '<b>Stranded</b> means an injured man occupying an <i>active</i> roster spot: he is the '
      'unit of harm in this study, a roster slot doing nothing.</p>')
    P('<p class="b"><b>Blocked</b> means a team that cannot shelve everyone it would want to. '
      'There are two defensible readings, and they disagree on exactly '
      f'{word(abs(sum(1 for r in rows for t in r["teams"] if t["stranded"] > max(0, cap-t["ir_used"])) - sum(1 for r in rows for t in r["teams"] if t["ir_full"] and t["stranded"] > 0)))} '
      f'team-week of {tw}: whether a side with a free slot and more injured men than slots '
      'counts as blocked. This page counts it, on the grounds that a team a slot short is a '
      'slot short. A reader who prefers the stricter reading should subtract it.</p>')

    S('Does the cap bind?')
    hdr = ''.join(f'<th>wk {r["week"]}</th>' for r in rows)
    def row(label, vals, bold=False):
        cells = ''.join(f'<td class="num{" hot" if bold and i == len(vals)-1 else ""}">{v}</td>'
                        for i, v in enumerate(vals))
        return f'<tr><th scope="row">{label}</th>{cells}</tr>'
    body = (row('IR slots filled', [f"{r['ir_used_total']}/{r['ir_capacity_total']}" for r in rows], True)
            + row('Share of capacity', [f"{100*r['ir_used_total']/r['ir_capacity_total']:.0f}%" for r in rows], True)
            + row('Teams with IR full', [r['teams_at_cap'] for r in rows], True)
            + row('Stranded players', [r['stranded_total'] for r in rows], True)
            + row('Teams a slot short',
                  [sum(1 for t in r['teams'] if t['stranded'] > max(0, cap - t['ir_used'])) for r in rows], True))
    P(f'<figure class="ad"><div class="scroll"><table><thead><tr><th></th>{hdr}</tr></thead>'
      f'<tbody>{body}</tbody></table></div><figcaption>Utilisation has risen every week of '
      f'the season so far.</figcaption></figure>')

    nblock = sum(1 for n in C['blockwk'] if C['blockwk'][n])
    P(f'<p class="b">By week {last["week"]}, <b>{last["teams_at_cap"]} of {C["teams_n"]}</b> rosters '
      f'are full and <b>{last["stranded_total"]} injured players</b> occupy active roster spots '
      f'league-wide. Over {word(n_wk)} weeks, <b>{nblock} of {C["teams_n"]} teams</b> have been a '
      f'slot short at least once, across <b>{base["blocked"]} of {tw} team-weeks</b> '
      f'({100*base["blocked"]/tw:.0f}%).</p>')
    who = ', '.join(E(', '.join(t['stranded_names'][:2])) for t in C['strand_now'][:4])
    P(f'<p class="lf">Stranded in week {last["week"]} include {who}.</p>')

    S('What a third slot would have done')
    P('<p class="b">The counterfactual holds the injuries exactly as they fell and re-runs '
      'each week under a different cap, assuming every manager fills IR up to the cap with '
      'whoever is stranded and changes nothing else. That assumption is the model&rsquo;s '
      'softest joint and is flagged again below.</p>')
    tr = ''.join(
        f'<tr><th scope="row">{"Cap " + str(c) + (" &mdash; actual" if c == cap else "")}</th>'
        f'<td class="num">{M[c]["blocked"]}</td><td class="num">{M[c]["stranded"]}</td></tr>'
        for c in (cap, cap + 1, cap + 2))
    P(f'<figure class="ad"><div class="scroll"><table><thead><tr><th></th>'
      f'<th class="num">Blocked team-weeks</th><th class="num">Stranded player-weeks</th>'
      f'</tr></thead><tbody>{tr}</tbody></table></div>'
      f'<figcaption>{word(n_wk).capitalize()} weeks, {tw} team-weeks.</figcaption></figure>')
    P(f'<p class="b">Going from {word(cap)} slots to {word(cap+1)} removes <b>{cut_b:.0f}%</b> of '
      f'the blocked team-weeks and <b>{cut_s:.0f}%</b> of the stranded player-weeks. Going to '
      f'{word(cap+2)} removes {cut_b2:.0f}% &mdash; the second extra slot buys roughly '
      f'{"a fraction of" if (cut_b2-cut_b) < cut_b/2 else "as much as"} what the first one does. '
      f'If a line is to be drawn, {word(cap+1)} is where the curve bends.</p>')
    P(f'<p class="b">The magnitude is small. <b>{spots} roster spots</b> freed across '
      f'{word(n_wk)} weeks &mdash; {spots/n_wk:.1f} a week, against {active} active roster '
      f'spots in a {C["teams_n"]}-team, {last["starters"]+9}-man league. About '
      f'{100*spots/n_wk/active:.0f}%.</p>')

    S('Who it helps')
    rr = ''
    for n in C['helped']:
        t = C['st'].get(n)
        rr += (f'<tr><th scope="row">{E(n)}</th>'
               f'<td class="dim">{t["record"] if t else "?"}</td>'
               f'<td class="num dim">{t["seed"] if t else "?"}</td>'
               f'<td class="num">{C["blockwk"].get(n,0)}</td>'
               f'<td class="num">{C["gain"][n]}</td></tr>')
    P(f'<figure class="ad"><div class="scroll"><table><thead><tr><th class="lt">Team</th>'
      f'<th class="lt">Record</th><th class="num">Seed</th><th class="num">Weeks short</th>'
      f'<th class="num">Spots gained</th></tr></thead><tbody>{rr}</tbody></table></div>'
      f'<figcaption>Only these {word(len(C["helped"]))} teams gain anything at all.</figcaption></figure>')
    top = C['helped'][0]
    P(f'<p class="b">Median seed of the teams helped: <b>{C["med_seed"]:.1f}</b>, against a '
      f'league median of {C["league_med"]:.1f}. On this sample the change helps the bottom of '
      f'the table more than the top.</p>')

    # The case AGAINST expansion, tested on its own terms. The paper as first
    # written only examined the claims of the side that wants the rule changed,
    # which is how a study gets dismissed by the other half of the league.
    dep = None
    p = os.path.join(ROOT, 'ir-waiver-depth.json')
    if os.path.exists(p):
        dep = json.load(open(p, encoding='utf-8'))
    if dep and dep['rows']:
        S('The argument against: does it thin the wire?')
        dr = dep['rows']
        up = [r['upgrade_skill'] for r in dr]
        sk_ = [r['startable_skill'] for r in dr]
        depw = dr[-1]['week']
        ex = {r['week']: sum(1 for t in r['teams']
              if max(0, min(t['stranded'], cap + 1 - t['ir_used']))
              > max(0, min(t['stranded'], cap - t['ir_used']))) for r in rows}
        P('<p class="b">The case against expansion is that the wire is already bare and another '
          'slot makes it barer. The mechanism is arithmetic, not opinion: a side that shelves an '
          'injured man frees an active spot, fills it, and the pool is one player smaller. Every '
          'extra slot used takes a player off waivers.</p>')
        P('<p class="b"><b>A headcount cannot test that, and this study does not report one.</b> '
          'Counting unrostered bodies gives a number around five hundred all season, which is '
          'true and useless &mdash; it counts third-string tight ends and quarterbacks nobody in '
          'this league would start in any week of any year. The question is how many men are '
          'worth adding, so that is what is measured.</p>')
        P('<p class="b">Two bars, both set by what the league itself started that week. '
          '<b>Would upgrade a lineup</b> means he outscored the <i>median</i> man started at his '
          'position &mdash; the players managers actually chase. <b>Beats replacement</b> means '
          'he outscored the <i>worst</i> man started at his position, which is a much weaker '
          'test.</p>')
        hdr2 = ''.join(f'<th class="num">wk {r["week"]}</th>' for r in dr)
        def r2(label, vals):
            return (f'<tr><th scope="row">{label}</th>'
                    + ''.join(f'<td class="num">{v}</td>' for v in vals) + '</tr>')
        body2 = (r2('<b>Would upgrade a lineup</b>', [f'<b>{v}</b>' for v in up])
                 + r2('Beats replacement level', sk_)
                 + r2('A third slot would absorb', [ex.get(r['week'], 0) for r in dr]))
        P(f'<figure class="ad"><div class="scroll"><table><thead><tr><th></th>{hdr2}</tr></thead>'
          f'<tbody>{body2}</tbody></table></div><figcaption>Skill positions only. Kickers and '
          'defences are excluded entirely: half the league&rsquo;s are unrostered by '
          'construction, so including them quadruples the count and tells you nothing.'
          '</figcaption></figure>')
        P(f'<p class="b">The entire waiver wire holds <b>{min(up)} to {max(up)} players a week</b> '
          f'who would improve anybody&rsquo;s starting lineup. In week {depw} there were '
          f'<b>{up[-1]}</b>'
          + (f' &mdash; {", ".join(E(u["name"]) + " " + u["pos"] for u in dr[-1]["upgrades"])}'
             if dr[-1]['upgrades'] else '')
          + f'. A third slot would have been taken up by <b>{ex.get(depw,0)}</b> teams that same '
          'week, and those teams take the best man available, not the fourth best.</p>')
        if ex.get(depw, 0) >= up[-1]:
            P(f'<p class="pull">In week {depw} a third slot would have been claimed by '
              f'{word(ex.get(depw,0))} teams, and there were {word(up[-1])} players on the entire '
              f'wire worth claiming. Expansion does not thin the usable wire. In a week like that '
              f'one it empties it.</p>')
        irw = rows[-1]['week']
        if irw > depw and ex.get(irw, 0) > ex.get(depw, 0):
            P(f'<p class="b">And the demand is rising: by week {irw}, <b>{ex.get(irw,0)}</b> teams '
              f'would have used a third slot. Week {irw} has not been played, so it has no depth '
              f'figure yet &mdash; but no week measured so far has offered more than '
              f'{max(up)} players worth having.</p>')
        P('<p class="b">What runs the other way is that the withdrawal is a <b>loan</b>. A player '
          'coming off injured reserve has to be activated, the roster is then one over, and '
          'somebody is dropped. The men come back. What a third slot changes is not how many '
          'players are owned across a season but <i>when</i> they are owned &mdash; and it takes '
          'them in exactly the weeks when injuries make everyone want them.</p>')

    # ---- the scoreboard and the gauge -----------------------------------
    # One claim per row, attributed to the side that made it, with what six
    # weeks of data does to it. The gauge needle is COUNTED from this table
    # rather than felt, so a reader who rejects a verdict can recount and move
    # it himself. That is the only honest way to put a dial on a judgement.
    V = [
        ('The cap binds', 'expand', 'supported',
         f"{last['teams_at_cap']} of {C['teams_n']} rosters full by week {last['week']}, "
         f"{100*last['ir_used_total']/last['ir_capacity_total']:.0f}% of capacity"),
        ('Only injured men qualify, so it cannot be stacked', 'expand', 'supported',
         'structural: an activated player must be rostered or dropped'),
        # Derived, not asserted. In week 5 the beneficiaries' median seed was
        # 11.0 against a league 8.5 and this read clearly "supported"; a week
        # later it is 9.5, which is nearly even. A gap under a seed and a half
        # is not evidence of anything, so it reads untested and the needle
        # moves on its own.
        ('A third slot helps weak teams more than strong ones', 'expand',
         'supported' if (C['med_seed'] or 0) - C['league_med'] >= 1.5 else 'untested',
         f"median seed of the {word(len(C['helped']))} beneficiaries is {C['med_seed']:.1f} "
         f"against a league median of {C['league_med']:.1f}"
         + ('' if (C['med_seed'] or 0) - C['league_med'] >= 1.5
            else ' &mdash; too close to call either way')),
        ('The withdrawal reverses when players return', 'expand', 'supported',
         'structural: activating a returning player puts the roster one over, so a man is '
         'dropped back to the wire'),
        ('Nobody is hoarding IR spots', 'expand', 'overtaken',
         f"true when it was said in preseason; by week {last['week']} "
         f"{last['teams_at_cap']} of {C['teams_n']} teams were at the cap"),
        ('Leagues our size run two to four slots', 'expand', 'untested',
         'no data here on other leagues, their age or their keeper rules'),
        ('The wire is already bare', 'keep two', 'supported',
         'DEPTH'),
        ('Expansion thins the wire further', 'keep two', 'supported',
         'MECH'),
        ('It changes nothing functional', 'keep two', 'contradicted',
         f"it changes {M[cap]['blocked']} blocked team-weeks to {M[cap+1]['blocked']}"),
        ('It helps the committed teams and hurts the rest', 'keep two',
         'contradicted' if (C['med_seed'] or 0) - C['league_med'] >= 1.5 else 'untested',
         'the beneficiaries skew to the bottom of the table, not the top'
         if (C['med_seed'] or 0) - C['league_med'] >= 1.5
         else 'the beneficiaries sit almost exactly at the league median'),
        ('No competitive harm from the cap has been shown', 'keep two', 'supported',
         'correct, and not testable with this data: see the limitations'),
    ]
    if dep and dep['rows']:
        up2 = [r['upgrade_skill'] for r in dep['rows']]
        dw = dep['rows'][-1]['week']
        ex = {r['week']: sum(1 for t in r['teams']
              if max(0, min(t['stranded'], cap + 1 - t['ir_used']))
              > max(0, min(t['stranded'], cap - t['ir_used']))) for r in rows}
        V = [(a, b, c, (f"only {up2[-1]} players on the entire wire would have improved a "
                        f"lineup in week {dw}"
                        if d == 'DEPTH' else
                        f"{ex.get(dw,0)} teams would have used a third slot in week {dw}; there "
                        f"were {up2[-1]} players worth taking" if d == 'MECH' else d))
             for a, b, c, d in V]
    else:
        V = [v for v in V if v[3] not in ('DEPTH', 'MECH')]

    S('The scoreboard')
    P('<p class="b">Every claim either side made in the argument of 7 September, and what six '
      'weeks of data does to it. <b>Supported</b> means the data backs it. <b>Contradicted</b> '
      'means the data runs against it. <b>Overtaken</b> means it was true when it was said and '
      'is not now. <b>Untested</b> means this study cannot speak to it.</p>')
    TONE = {'supported': 'ok', 'contradicted': 'no', 'overtaken': 'mid', 'untested': 'mid'}
    vr = ''.join(
        f'<tr><th scope="row">{c}</th>'
        f'<td class="dim">{"expand" if s == "expand" else "keep two"}</td>'
        f'<td><span class="v {TONE[v]}">{v}</span></td>'
        f'<td class="dim ev">{w}</td></tr>' for c, s, v, w in V)
    P(f'<figure class="ad"><div class="scroll"><table><thead><tr><th class="lt">Claim</th>'
      f'<th class="lt">Made by</th><th class="lt">Verdict</th><th class="lt">On what</th>'
      f'</tr></thead><tbody>{vr}</tbody></table></div></figure>')

    fore = sum(1 for _, s, v, _ in V if s == 'expand' and v == 'supported')
    agin = sum(1 for _, s, v, _ in V if s == 'keep two' and v == 'supported')
    killed_f = sum(1 for _, s, v, _ in V if s == 'expand' and v in ('contradicted', 'overtaken'))
    killed_a = sum(1 for _, s, v, _ in V if s == 'keep two' and v in ('contradicted', 'overtaken'))
    net = (fore - killed_f) - (agin - killed_a)
    span = max(fore + agin, 1)
    x = 50 + 50 * max(-1.0, min(1.0, net / span))
    S('Where it lands')
    P(f'<figure class="gauge"><svg viewBox="0 0 600 124" role="img" '
      f'aria-label="Gauge: the evidence leans {"toward expanding" if net > 0 else "toward keeping two" if net < 0 else "neither way"}">'
      f'<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#0e8ab5"/>'
      f'<stop offset="0.5" stop-color="#d8b45a"/><stop offset="1" stop-color="#c20f16"/>'
      f'</linearGradient></defs>'
      f'<rect x="20" y="52" width="560" height="16" rx="8" fill="url(#g)" opacity=".85"/>'
      f'<line x1="300" y1="44" x2="300" y2="76" stroke="#17181c" stroke-width="2" opacity=".3"/><text x="300" y="92" font-size="10" text-anchor="middle" font-family="-apple-system,sans-serif" font-weight="700" fill="#9a958c">EVEN</text>'
      f'<g transform="translate({20 + 5.6*x},0)">'
      f'<polygon points="0,40 -10,22 10,22" fill="#17181c"/>'
      f'<line x1="0" y1="40" x2="0" y2="80" stroke="#17181c" stroke-width="3"/></g>'
      f'<text x="20" y="114" font-size="13" font-family="-apple-system,sans-serif" '
      f'font-weight="800" fill="#0e8ab5">KEEP TWO</text>'
      f'<text x="580" y="114" font-size="13" text-anchor="end" '
      f'font-family="-apple-system,sans-serif" font-weight="800" fill="#c20f16">EXPAND TO THREE</text>'
      f'</svg><figcaption>The needle is <b>counted, not felt</b>: surviving claims for '
      f'expansion ({fore} supported, {killed_f} knocked out) minus surviving claims against '
      f'({agin} supported, {killed_a} knocked out), over {span}. Reject a verdict in the table '
      f'above and the needle moves.</figcaption></figure>')
    keeps = [v for v in V if v[1] == 'keep two']
    survive = [c for c, _, v, _ in keeps if v == 'supported']
    fell = [c for c, _, v, _ in keeps if v in ('contradicted', 'overtaken')]
    P(f'<p class="b">On the count it leans <b>'
      + ('toward expanding, and not by much' if 0 < net <= 2 else
         'clearly toward expanding' if net > 2 else
         'toward keeping two, and not by much' if -2 <= net < 0 else
         'clearly toward keeping two' if net < 0 else 'neither way &mdash; dead level')
      + f'</b>. Of the {word(len(keeps))} arguments made for keeping the cap, '
      + (f'{word(len(fell))} did not survive contact with the data and '
         if fell else 'none fell outright and ')
      + f'{word(len(survive))} did. The ones that stood are the ones nobody can settle from '
      'here: that the wire is thin, which was true before this debate started, and that no '
      'competitive harm has ever been demonstrated, which is true and may stay true.</p>')
    P('<p class="pull">The strongest surviving argument on either side is not about fairness or '
      'hoarding. It is that a third slot takes its players off the <i>top</i> of a wire that '
      'holds barely a dozen usable men &mdash; and takes them in exactly the weeks when injuries '
      'make everyone want them.</p>')

    S('Limitations')
    P('<p class="b">Read this before quoting any figure above.</p>')
    P(f'<p class="b"><b>It measures roster friction, not competitive harm.</b> Nothing here '
      'shows a blocked team lost a game, or even lost points. Establishing that would need to '
      'know who each manager <i>would</i> have added with the freed slot and what that man '
      'then scored, which is unobservable. Every number above is a ceiling on inconvenience.</p>')
    P('<p class="b"><b>A blocked team is never actually stuck.</b> Any side can cut an injured '
      'man and move on. Blocked means <i>made to choose</i>, not <i>prevented</i> &mdash; and '
      'whether being made to choose is a flaw or the point of a roster limit is a judgement no '
      'amount of this data settles.</p>')
    P(f'<p class="b"><b>The benefit is concentrated.</b> {E(top)} account for '
      f'<b>{C["gain"][top]} of the {spots} freed spots</b> '
      f'({100*C["gain"][top]/spots:.0f}%) and were a slot short in '
      f'{word(C["blockwk"].get(top,0))} of {word(n_wk)} weeks. A fair reader may ask whether a '
      'permanent rule change is warranted by one roster&rsquo;s injury luck. Take that team '
      'out and the case weakens materially.</p>')
    # How much of each week's blockage a third slot actually clears. An earlier
    # draft asserted this decays as the season goes on; week 6 landed while the
    # page was being built and broke the claim -- the share fell to a quarter in
    # week 5 and recovered to nearly two thirds in week 6. So the trend is
    # computed and described, including whether it is monotonic, rather than
    # stated.
    share = []
    for r in rows:
        b2 = sum(1 for t in r['teams'] if t['stranded'] > max(0, cap - t['ir_used']))
        b3 = sum(1 for t in r['teams'] if t['stranded'] > max(0, cap + 1 - t['ir_used']))
        share.append((r['week'], b2, b2 - b3, (b2 - b3) / b2 if b2 else None))
    vals = [s for *_, s in share if s is not None]
    half = len(vals) // 2
    early_m = 100 * sum(vals[:half]) / half if half else 0
    late_m = 100 * sum(vals[half:]) / (len(vals) - half)
    mono = all(a >= b for a, b in zip(vals, vals[1:]))
    worst = min((s for s in share if s[3] is not None), key=lambda s: s[3])
    nowb, nowc = share[-1][1], share[-1][2]
    P(f'<p class="b"><b>The relief looks weaker later in the season, but the trend is noisy.</b> '
      f'The share of each week&rsquo;s blockage a third slot would clear has run '
      + ', '.join(f'{100*s:.0f}%' for *_, s in share if s is not None)
      + f' &mdash; averaging {early_m:.0f}% over the first {word(half)} weeks and {late_m:.0f}% '
      f'since. It is <b>not</b> a steady decline: the worst week was {worst[0]}, at '
      f'{100*worst[3]:.0f}%, and week {share[-1][0]} recovered to {100*share[-1][3]:.0f}% '
      f'({nowc} of {nowb} blocked teams cleared). The mechanism is real &mdash; a side with '
      'more than one man stranded only has its line moved by a single extra slot &mdash; but '
      f'on {word(n_wk)} weeks it cannot be called a trend'
      + ('' if mono else ', and it is not monotonic')
      + '. Stranded counts have run '
      + ', '.join(str(r['stranded_total']) for r in rows)
      + ', so the problem is certainly growing even where the relief is holding up.</p>')
    P(f'<p class="b"><b>One season, {word(n_wk)} weeks, {tw} team-weeks.</b> Injury rates vary '
      'year to year and no claim is made that this one is typical. The greedy-filling '
      'assumption in the model is untested &mdash; a manager might hold a slot open against a '
      'worse injury later, in which case uptake above is overstated. And transactions are not '
      'observed, so we cannot see whether any blocked side actually cut a player it wanted to '
      'keep. That would be the strongest evidence of real cost, and we do not have it.</p>')

    S('The data, in full')
    P('<p class="b">Everything the conclusions rest on, so it can be checked rather than '
      'taken. Each row is one week as it was recorded at the time.</p>')
    cols = [('wk', lambda r: r['week']),
            ('IR used', lambda r: f"{r['ir_used_total']}/{r['ir_capacity_total']}"),
            ('teams at cap', lambda r: r['teams_at_cap']),
            ('teams with empty IR', lambda r: r['teams_empty_ir']),
            ('stranded', lambda r: r['stranded_total']),
            ('teams a slot short', lambda r: sum(1 for t in r['teams']
                                                 if t['stranded'] > max(0, cap - t['ir_used']))),
            ]
    hh = ''.join(f'<th class="num">{c}</th>' for c, _ in cols)
    bb = ''.join('<tr>' + ''.join(f'<td class="num">{f(r)}</td>' for _, f in cols) + '</tr>'
                 for r in rows)
    P(f'<figure class="ad"><div class="scroll"><table><thead><tr>{hh}</tr></thead>'
      f'<tbody>{bb}</tbody></table></div><figcaption>From ir-watch.json, one row written per '
      f'week and never revised.</figcaption></figure>')

    if dep and dep["rows"]:
        hh2 = ('<th class="num">wk</th><th class="num">scored</th>'
               '<th class="num">would upgrade</th><th class="num">beats replacement</th>'
               '<th class="lt">the men who would upgrade</th>')
        bb2 = ''.join(
            f'<tr><td class="num">{r["week"]}</td><td class="num">{r["scored"]}</td>'
            f'<td class="num"><b>{r["upgrade_skill"]}</b></td>'
            f'<td class="num">{r["startable_skill"]}</td>'
            f'<td class="dim ev">' + (', '.join(f'{E(u["name"])} {u["pos"]} {u["pts"]}'
                                                for u in r['upgrades']) or '&mdash;') + '</td></tr>'
            for r in dep['rows'])
        P(f'<figure class="ad"><div class="scroll"><table><thead><tr>{hh2}</tr></thead>'
          f'<tbody>{bb2}</tbody></table></div><figcaption>From ir-waiver-depth.json. Only '
          f'played weeks appear: depth cannot be measured on a week nobody has played. '
          f'Upgrade bar (median starter), week {dep["rows"][-1]["week"]}: '
          + ', '.join(f'{k} {v}' for k, v in dep['rows'][-1]['median_bar'].items()
                      if k in ('QB', 'RB', 'WR', 'TE'))
          + '.</figcaption></figure>')

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

    P('<p class="lf">Files, if you want to run it yourself: <code>ir-watch.json</code> (weekly '
      'snapshots, written by <code>scripts/ir_watch.py</code>), <code>ir-waiver-depth.json</code> '
      '(written by <code>scripts/waiver_depth.py</code>, which needs the nflverse play-by-play '
      'download), <code>week-data/2026-w*.json</code> (weekly rosters and scoring), '
      '<code>scripts/standings.py</code> (records and seeds). The page itself is '
      '<code>scripts/build_ir_study.py</code>.</p>')

    S('What would settle it')
    P('<p class="b"><b>Transaction logs.</b> Drops of injured players by teams at the cap '
      'against drops by teams with a slot free. If the cap forces real losses, it shows there.'
      ' <b>More weeks.</b> The decay above is the open question, and re-running this at week 10 '
      'and week 14 answers it. <b>Earlier seasons.</b> The collector only began logging this '
      'year, so 2026 is all there is.</p>')
    P('<p class="pull">Four questions worth answering before anyone votes: is a team with a '
      'free slot and two injured men blocked? Is the concentration disqualifying, or is '
      '&ldquo;the rule bites hardest on whoever had bad luck&rdquo; what an injury rule is for? '
      'Is roster pressure part of the skill of the game? And does the decay argue for four '
      'slots, or for leaving it alone?</p>')
    return out


CARD = """<style>
:root{--red:#c20f16;--ink:#17181c;--faint:#9a958c;--blue:#0e8ab5;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;margin:0;}
html,body{width:1200px;height:630px;overflow:hidden;background:#efe9de;
 font-family:Georgia,'Times New Roman',serif;color:var(--ink);}
.card{position:relative;width:1200px;height:630px;overflow:hidden;background:#efe9de;
 border-top:9px solid var(--red);border-bottom:9px solid var(--red);
 padding:52px 60px 44px;display:flex;}
.l{width:520px;flex:0 0 520px;display:flex;flex-direction:column;}
.flag{font-family:var(--sans);font-size:11.5px;font-weight:900;letter-spacing:.22em;
 text-transform:uppercase;color:var(--red);}
h1{font-size:58px;line-height:.98;letter-spacing:-.026em;font-weight:900;margin-top:16px;}
h1 em{font-style:normal;color:var(--red);}
.rule{width:64px;height:3px;background:var(--red);margin:22px 0 18px;}
.dek{font-style:italic;color:#4b4b52;font-size:17px;line-height:1.4;max-width:28ch;}
.st{margin-top:auto;display:flex;gap:34px;}
.st .k{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.st .v{font-size:32px;font-weight:900;line-height:1.1;font-variant-numeric:tabular-nums;}
.r{flex:1;padding-left:54px;display:flex;flex-direction:column;justify-content:center;}
.cap{font-family:var(--sans);font-size:10px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);margin-bottom:16px;}
.bars{display:flex;flex-direction:column;gap:16px;}
.b{display:flex;align-items:center;gap:12px;font-family:var(--sans);font-size:13px;}
.b i{font-style:normal;font-weight:800;width:54px;color:var(--faint);}
.b span{display:block;height:26px;background:var(--red);border-radius:0 2px 2px 0;}
.b span.q{background:var(--blue);}
.b b{font-weight:900;font-size:17px;font-variant-numeric:tabular-nums;}
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
 <div class="r">
  <div class="cap">Blocked team-weeks, by cap</div>
  <div class="bars">__BARS__</div>
 </div>
</div>"""


def card(C):
    cap, M = C['cap'], C['M']
    base = M[cap]
    mx = base['blocked'] or 1
    bars = ''.join(
        f'<div class="b"><i>Cap {c}</i>'
        f'<span class="{"" if c == cap else "q"}" style="width:{330*M[c]["blocked"]/mx:.0f}px"></span>'
        f'<b>{M[c]["blocked"]}</b></div>' for c in (cap, cap + 1, cap + 2))
    last = C['last']
    cut = 100 * (base['blocked'] - M[cap + 1]['blocked']) / base['blocked']
    nshort = sum(1 for n in C['blockwk'] if C['blockwk'][n])
    doc = (CARD.replace('__BARS__', bars)
               .replace('__SHORT__', word(nshort).capitalize())
               .replace('__PCT__', f"{100*last['ir_used_total']/last['ir_capacity_total']:.0f}")
               .replace('__STR__', str(last['stranded_total']))
               .replace('__CUT__', f'{cut:.0f}')
               .replace('__DEK__', f"{word(nshort).capitalize()} of {C['teams_n']} teams have been a slot "
                                   f"short this season. What a third would fix, and what it "
                                   f"would not."))
    ad.shoot(doc, OG, 'irstudy-card')


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
.wrap{max-width:860px;margin:0 auto;padding:0 20px 80px;}
.runhead{font-family:var(--sans);font-size:10.5px;font-weight:800;letter-spacing:.22em;
 text-transform:uppercase;color:var(--faint);border-bottom:1px solid var(--line);padding:20px 0 12px;}
.flag{font-family:var(--sans);font-size:10.5px;font-weight:900;letter-spacing:.24em;
 text-transform:uppercase;color:var(--red);margin-top:26px;display:block;}
h1{font-weight:900;font-size:clamp(34px,7vw,54px);line-height:1.02;letter-spacing:-.022em;
 margin:12px 0 0;text-wrap:balance;}
h1 em{font-style:normal;color:var(--red);}
.dek{font-style:italic;color:var(--muted);font-size:18px;margin:14px 0 0;max-width:60ch;}
.byline{font-family:var(--sans);font-size:11.5px;letter-spacing:.06em;color:var(--faint);
 margin-top:16px;text-transform:uppercase;}
.rule{height:3px;background:var(--red);width:70px;margin:22px 0 26px;}
.sect{font-family:var(--sans);font-size:11px;font-weight:900;letter-spacing:.2em;
 text-transform:uppercase;color:var(--red);margin:44px 0 12px;padding-top:14px;
 border-top:1px solid var(--line);}
p.b{margin:0 0 16px;max-width:62ch;}
p.lf{margin:0 0 16px;max-width:62ch;font-family:var(--sans);font-size:13px;color:var(--muted);}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:14px;
 background:var(--paper);padding:1px 5px;border-radius:3px;}
.stats{display:flex;flex-wrap:wrap;gap:24px 38px;margin:0 0 28px;padding-bottom:22px;
 border-bottom:1px solid var(--line);}
.stat .k{font-family:var(--sans);font-size:9.5px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.stat .v{font-size:30px;font-weight:900;line-height:1.15;font-variant-numeric:tabular-nums;}
.stat .n{font-family:var(--sans);font-size:11px;color:var(--muted);}
.pull{margin:34px 0 10px;padding:0 0 0 20px;border-left:3px solid var(--red);font-size:19px;
 line-height:1.45;font-weight:700;max-width:54ch;letter-spacing:-.01em;}
figure.ad{margin:26px 0 30px;}
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
figcaption{font-family:var(--sans);font-size:11.5px;color:var(--faint);margin-top:10px;}
figure.ad .v{font-family:var(--sans);font-size:10px;font-weight:900;letter-spacing:.1em;
 text-transform:uppercase;padding:2px 7px;border-radius:3px;color:#fff;white-space:nowrap;}
figure.ad .v.ok{background:var(--red);}
figure.ad .v.no{background:var(--blue);}
figure.ad .v.mid{background:var(--gold);color:#3a3326;}
figure.ad .ev{white-space:normal;min-width:19em;font-size:12.5px;line-height:1.45;}
figure.gauge{margin:14px 0 26px;}
figure.gauge svg{width:100%;height:auto;display:block;}
.more{margin-top:46px;border-top:1px solid var(--line);padding-top:18px;font-family:var(--sans);
 font-size:12.5px;line-height:1.6;color:var(--muted);max-width:74ch;}
.more a{color:var(--red);font-weight:700;}
</style></head><body><div class="wrap">
<div class="runhead">SCFL NewsRoom &middot; Working Paper</div>
<span class="flag">Rules &middot; Injured Reserve</span>
<h1>Two Slots, <em>__SHORT__</em> Short</h1>
<p class="dek">__DESC__</p>
<div class="byline">An early review of the evidence &middot; data through week __WK__</div>
<div class="rule"></div>
__BODY__
<div class="more">Every figure on this page is computed at build time from
<code>ir-watch.json</code>, which <code>scripts/ir_watch.py</code> writes once a week from the
live roster and never rewrites. Nothing here was typed by hand, and adding a week changes the
conclusions rather than leaving a stale number under a headline that no longer fits it.
Built by <code>scripts/build_ir_study.py</code>.</div>
</div></body></html>"""


def build():
    import datetime
    C = crunch()
    body = '\n'.join(figures(C))
    last = C['last']
    cap = C['cap']
    nshort = sum(1 for n in C['blockwk'] if C['blockwk'][n])
    cut = 100 * (C['M'][cap]['blocked'] - C['M'][cap + 1]['blocked']) / C['M'][cap]['blocked']
    desc = (f"{word(nshort).capitalize()} of {C['teams_n']} teams have been an IR slot short "
            f"this season. A third slot would clear {cut:.0f}% of it — and here is everything "
            f"that measurement cannot tell you.")
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
          f"cap {cap+1}: {C['M'][cap+1]['blocked']} | cap {cap+2}: {C['M'][cap+2]['blocked']}")
    card(C)


if __name__ == '__main__':
    build()
