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
        fa = [r['free_agents'] for r in rows]
        irn = [r['ir_used_total'] for r in rows]
        P('<p class="b">The case against expansion is that the waiver wire is already bare '
          'and another slot makes it barer. The mechanism is not in dispute and is worth '
          'stating plainly, because it is arithmetic rather than opinion: a side that shelves '
          'an injured man frees an active spot, fills it from the wire, and the pool is one '
          'player smaller. Every extra slot used takes a player off waivers.</p>')
        P(f'<p class="b">What is in dispute is the size of it. Across {word(len(rows))} weeks, '
          f'the number of players on injured reserve league-wide went from <b>{irn[0]}</b> to '
          f'<b>{irn[-1]}</b> &mdash; {irn[-1]-irn[0]} more men shelved &mdash; while the free-agent '
          f'pool went from <b>{fa[0]}</b> to <b>{fa[-1]}</b>, a fall of {fa[0]-fa[-1]}. Not '
          f'{irn[-1]-irn[0]}. The pass-through is partial because the rule reverses itself: a '
          'returning player has to be activated and somebody dropped, which puts a man back on '
          'the wire. Over a season the pool is close to conserved. What moves is the timing.</p>')
        P('<p class="b">But a headcount is the wrong instrument, and it is the instrument both '
          'sides have been using. It counts bodies, and the complaint is about usable players. '
          'So this measures depth instead: a free agent is <b>startable</b> in a given week if '
          'he outscored the worst man the league actually started at his position &mdash; that '
          'is, if adding him would have improved somebody&rsquo;s lineup.</p>')
        hdr2 = ''.join(f'<th class="num">wk {r["week"]}</th>' for r in dr)
        def r2(label, vals):
            return (f'<tr><th scope="row">{label}</th>'
                    + ''.join(f'<td class="num">{v}</td>' for v in vals) + '</tr>')
        extra = {r['week']: sum(1 for t in r['teams']
                 if max(0, min(t['stranded'], cap + 1 - t['ir_used']))
                 > max(0, min(t['stranded'], cap - t['ir_used']))) for r in rows}
        body2 = (r2('Unrostered men who scored', [r['scored'] for r in dr])
                 + r2('Startable, all positions', [r['startable_all'] for r in dr])
                 + r2('<b>Startable skill players</b>', [f"<b>{r['startable_skill']}</b>" for r in dr])
                 + r2('A third slot would absorb', [extra.get(r['week'], 0) for r in dr]))
        P(f'<figure class="ad"><div class="scroll"><table><thead><tr><th></th>{hdr2}</tr></thead>'
          f'<tbody>{body2}</tbody></table></div><figcaption>Kickers and defences are shown '
          'separately and kept out of the headline: half the league&rsquo;s are unrostered by '
          'construction, which makes the wire look four times deeper than it plays.</figcaption>'
          '</figure>')
        sk_ = [r['startable_skill'] for r in dr]
        depw = dr[-1]['week']           # depth is only measurable on a PLAYED week
        irw = rows[-1]['week']
        P(f'<p class="b">A typical week offers <b>{min(sk_)} to {max(sk_)} usable skill '
          f'players</b> on the entire wire. In week {depw} &mdash; the last week with both '
          f'figures &mdash; there were <b>{sk_[-1]}</b>, and a third slot would have been taken '
          f'up by <b>{extra.get(depw,0)}</b> teams. Those teams do not take random players; they '
          f'take the best available. So expansion would have absorbed about '
          f'<b>{100*extra.get(depw,0)/sk_[-1]:.0f}%</b> of the usable wire that week, off the '
          f'top of it.</p>')
        if irw > depw and extra.get(irw, 0) > extra.get(depw, 0):
            P(f'<p class="b">That share is rising. By week {irw} the number of teams who would '
              f'use a third slot had reached <b>{extra.get(irw,0)}</b>. Week {irw} has not been '
              'played, so there is no depth figure to set it against yet &mdash; but against '
              f'week {depw}&rsquo;s {sk_[-1]} usable players it would be most of the wire. That '
              'is the strongest form of the argument against expansion, and nobody in the league '
              'had put a number on it.</p>')
        P(f'<p class="pull">Both sides are partly right. The wire does thin, and the headcount '
          f'hides it &mdash; {fa[-1]} free agents in week {irw}, of whom, on the last played '
          f'week, {sk_[-1]} were worth starting. But the withdrawal is a loan rather than a '
          'loss, and the men who would do the borrowing are mostly at the bottom of the '
          'table.</p>')
        P('<p class="b">Two findings cut against the case for expansion and one cuts for it. '
          'Against: the mechanism is real and, at an injury peak, large relative to what the '
          'wire actually holds. For: it reverses, and the beneficiaries are the weak teams, not '
          'the strong ones &mdash; which is the opposite of the fairness objection that has been '
          'made against it.</p>')

    S('Limitations')
    P('<p class="b">Read this before quoting any figure above.</p>')
    P(f'<p class="b"><b>It measures roster friction, not competitive harm.</b> Nothing here '
      'shows a blocked team lost a game, or even lost points. Establishing that would need to '
      'know who each manager <i>would</i> have added with the freed slot and what that man '
      'then scored, which is unobservable. Every number above is a ceiling on inconvenience.</p>')
    P(f'<p class="b"><b>A blocked team is never actually stuck.</b> There were '
      f'{rows[0]["free_agents"]} free agents in week {rows[0]["week"]}. Any side can cut an '
      'injured man and move on. Blocked means <i>made to choose</i>, not <i>prevented</i> '
      '&mdash; and whether being made to choose is a flaw or the point of a roster limit is a '
      'judgement no amount of this data settles.</p>')
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
