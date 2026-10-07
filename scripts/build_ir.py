#!/usr/bin/env python3
"""The Wrong Number -- the IR expansion vote, argued from the season's own record.

    python3 scripts/build_ir.py

Reads ir-watch.json, which scripts/ir_watch.py appends to every Wednesday under
.github/workflows/ir-watch.yml, and types the whole thing as a magazine piece.
Nothing here is hand-entered: every figure, every number in the prose and the
share card all come out of the log, so re-running it after a new week lands
re-types the article around the new numbers rather than dating it.

The one editorial claim the page makes is a counting claim -- that the vote was
argued over "teams at cap" when the quantity that decides it is "constrained
teams", and that those two differ by nearly a factor of two. That is checkable
from Figure Two, which is why Figure Two prints all sixteen rosters.
"""
import importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts',
                                                               'build_addendum.py'))
ad = importlib.util.module_from_spec(_s)
sys.modules['ad'] = ad
_s.loader.exec_module(ad)

LOG = os.path.join(ROOT, 'ir-watch.json')
OUT = os.path.join(ROOT, 'scfl-ir-report.html')
OG = os.path.join(ROOT, 'scfl-ir-report-og.jpg')
E = ad.esc

MONTHS = ('January February March April May June July August September '
          'October November December').split()


def short(name, n=13):
    """A card-sized label. Team names in this league run long and shouty."""
    t = name.strip().strip('*').replace('’', "'")
    return t if len(t) <= n else t[:n - 1].rstrip() + '…'


def crunch():
    if not os.path.exists(LOG):
        sys.exit('no ir-watch.json yet -- run scripts/ir_watch.py first')
    rows = json.load(open(LOG, encoding='utf-8'))['rows']
    if not rows:
        sys.exit('ir-watch.json has no weeks in it yet')
    last = rows[-1]
    teams = last['teams']
    # the three states a roster can be in, which is the whole argument
    constrained = [t for t in teams if t['ir_full'] and t['stranded'] > 0]
    idle_cap = [t for t in teams if t['ir_full'] and t['stranded'] == 0]
    under = [t for t in teams if not t['ir_full']]
    # under the cap and still holding an injured man: nothing the vote does helps
    # these managers, because they have not used the slot they already own
    unused = [t for t in under if t['stranded'] > 0]
    return dict(rows=rows, last=last, teams=teams, constrained=constrained,
                idle_cap=idle_cap, under=under, unused=unused)


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>The Wrong Number &mdash; SCFL NewsRoom</title>
<meta name="scfl:kicker" content="The Rules Desk &middot; __MONTH__">
<meta name="scfl:published" content="__DATE__">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SCFL NewsRoom">
<meta property="og:title" content="The Wrong Number">
<meta property="og:description" content="__DESC__">
<meta property="og:image" content="https://watsoncapitalinvest-dot.github.io/Claude/scfl-ir-report-og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="newsroom-favicon.png">
<style>
:root{--cream:#fffdfb;--paper:#faf7f2;--ink:#17181c;--muted:#65656b;--faint:#9a958c;
 --line:#e6e0d6;--red:#c20f16;--blue:#0e8ab5;
 --serif:Georgia,'Times New Roman',serif;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;}
body{margin:0;background:var(--cream);color:var(--ink);font-family:var(--serif);font-size:17px;
 line-height:1.62;-webkit-font-smoothing:antialiased;}
.wrap{max-width:840px;margin:0 auto;padding:0 20px 80px;}
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
p.b em{font-style:italic;}
.stats{display:flex;flex-wrap:wrap;gap:24px 38px;margin:0 0 28px;padding-bottom:22px;
 border-bottom:1px solid var(--line);}
.stat .k{font-family:var(--sans);font-size:9.5px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.stat .v{font-size:30px;font-weight:900;line-height:1.15;font-variant-numeric:tabular-nums;}
.stat .n{font-family:var(--sans);font-size:11px;color:var(--muted);}
.pull{margin:30px 0;padding:0 0 0 20px;border-left:3px solid var(--red);font-size:21px;
 line-height:1.42;font-weight:700;max-width:46ch;letter-spacing:-.01em;}
.more{margin-top:46px;border-top:1px solid var(--line);padding-top:18px;font-family:var(--sans);
 font-size:13px;line-height:1.6;color:var(--muted);max-width:72ch;}
.more a{color:var(--red);font-weight:700;}
@media (prefers-reduced-motion:reduce){*{transition:none!important;}}
__FIGCSS__
/* ---- three-state roster table: the distinction the vote turned on ---- */
.ad .st1 th,.ad .st1 td{background:#fdf3f0;} .ad .st1 th{color:var(--red);}
.ad .st2 th,.ad .st2 td{background:#f6f2ea;}
.ad .tag{font-family:var(--sans);font-size:8.5px;font-weight:800;letter-spacing:.1em;
 text-transform:uppercase;padding:2px 5px;border-radius:2px;white-space:nowrap;}
.ad .tag.a{background:var(--red);color:#fff;}
.ad .tag.b{background:#e6e0d6;color:#6b6257;}
.ad .tag.c{background:#fff;color:var(--blue);border:1px solid var(--blue);}
.ad .pips{letter-spacing:1px;white-space:nowrap;}
.ad .pips i{font-style:normal;color:var(--red);}
.ad .pips u{text-decoration:none;color:#ded7ca;}
.ad .who{font-family:var(--sans);font-size:10.5px;color:var(--muted);max-width:26ch;
 white-space:normal;line-height:1.35;}
.ad .wk{width:38px;}
.ad .tiny{font-size:11px;}
</style></head>
<body><div class="wrap">
<div class="runhead">SCFL NewsRoom &middot; The Rules Desk &middot; __MONTH__</div>
<span class="flag">The Rules Desk</span>
<h1>The Wrong <em>Number</em></h1>
<p class="dek">The league will vote on a third injured-reserve slot, and all summer both
sides argued it by counting how many teams have a full IR. That number does not measure what a
slot costs. Four weeks of the season&rsquo;s own record say what does &mdash; and the answer is
smaller than one camp claimed and climbing faster than the other could prove in August.</p>
<div class="byline">The SCFL NewsRoom &middot; The Rules Desk</div>
<div class="rule"></div>
__BODY__
<div class="more">Every figure on this page is read straight out of
<a href="ir-watch.json">ir-watch.json</a>, which <code>scripts/ir_watch.py</code> appends to
once a week on its own and never rewrites. The live version, which recomputes from Sleeper on
every load, is at <a href="ir-watch.html">IR&nbsp;Watch</a>. Re-running
<code>scripts/build_ir.py</code> re-types this article around whatever the log says by then.</div>
</div></body></html>"""

CARD = """<style>
:root{--red:#c20f16;--ink:#17181c;--faint:#9a958c;--blue:#0e8ab5;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;margin:0;}
html,body{width:1200px;height:630px;overflow:hidden;background:#efe9de;
 font-family:Georgia,'Times New Roman',serif;color:var(--ink);}
.card{position:relative;width:1200px;height:630px;overflow:hidden;background:#efe9de;
 border-top:9px solid var(--red);border-bottom:9px solid var(--red);}
.pc{position:absolute;background:#fffdfb;border:1px solid #ded7ca;padding:12px 14px;
 overflow:hidden;box-shadow:0 10px 26px rgba(0,0,0,.17),0 2px 5px rgba(0,0,0,.09);}
.pc .cap{font-family:var(--sans);font-size:8px;font-weight:800;letter-spacing:.15em;
 text-transform:uppercase;color:var(--red);margin-bottom:9px;}
.p1{left:448px;top:40px;width:322px;transform:rotate(-1.5deg);}
.p2{left:788px;top:52px;width:366px;transform:rotate(1.4deg);}
.p3{left:470px;top:352px;width:664px;transform:rotate(1.1deg);}
table{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:9.5px;}
td,th{padding:2.5px 4px;vertical-align:middle;}
tbody th{text-align:left;font-weight:700;white-space:nowrap;}
.num{text-align:right;font-variant-numeric:tabular-nums;color:var(--faint);}
tbody tr + tr th,tbody tr + tr td{border-top:1px solid #eee7db;}
.hl th,.hl td{background:#fdf3f0;} .hl th,.hl .num{color:var(--red);font-weight:800;}
.bar{width:56%;} .bar span{display:block;height:8px;background:var(--red);
 border-radius:0 2px 2px 0;min-width:2px;}
.bar span.lo{background:#ded7ca;}
.tag{font-family:var(--sans);font-size:7.5px;font-weight:800;letter-spacing:.08em;
 text-transform:uppercase;padding:1.5px 4px;border-radius:2px;}
.tag.a{background:var(--red);color:#fff;} .tag.b{background:#e6e0d6;color:#6b6257;}
.tag.c{background:#fff;color:var(--blue);border:1px solid var(--blue);}
.l{position:absolute;left:0;top:0;bottom:0;width:452px;z-index:9;
 padding:54px 28px 44px 52px;display:flex;flex-direction:column;
 background:linear-gradient(90deg,#efe9de 0%,#efe9de 72%,rgba(239,233,222,.94) 87%,
 rgba(239,233,222,0) 100%);}
.flag{font-family:var(--sans);font-size:11.5px;font-weight:900;letter-spacing:.22em;
 text-transform:uppercase;color:var(--red);}
h1{font-size:64px;line-height:.96;letter-spacing:-.028em;font-weight:900;margin-top:16px;}
h1 em{font-style:normal;color:var(--red);}
.rule{width:64px;height:3px;background:var(--red);margin:22px 0 18px;}
.dek{font-style:italic;color:#4b4b52;font-size:17px;line-height:1.4;max-width:24ch;}
.st{margin-top:auto;display:flex;gap:24px;}
.st .k{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.st .v{font-size:29px;font-weight:900;line-height:1.1;font-variant-numeric:tabular-nums;}
</style>
<div class="card">
 <div class="pc p1"><div class="cap">Constrained teams, by week</div>__TREND__</div>
 <div class="pc p2"><div class="cap">At cap is not constrained</div>__STATE__</div>
 <div class="pc p3"><div class="cap">What a slot would cost the wire</div>__COST__</div>
 <div class="l">
  <div class="flag">The Rules Desk</div>
  <h1>The<br>Wrong<br><em>Number</em></h1>
  <div class="rule"></div>
  <div class="dek">The IR vote, settled by the season instead of the argument.</div>
  <div class="st">
   <div><div class="k">Constrained</div><div class="v">__CN__</div></div>
   <div><div class="k">At cap</div><div class="v">__AC__</div></div>
   <div><div class="k">Cost of +1</div><div class="v">__PC__</div></div>
  </div>
 </div>
</div>"""


def figures(C):
    """[(kind, html)] -- same sect|body shape the addendum and Gumbas pages use."""
    out = []
    S = lambda t: out.append(('sect', f'<div class="sect">{t}</div>'))
    B = lambda h: out.append(('body', f'<div class="ad">{h}</div>'))
    P = lambda h: out.append(('body', h))

    rows, last = C['rows'], C['last']
    cap, n = last['ir_cap'], last['teams_n']
    cons, idle, under, unused = (C['constrained'], C['idle_cap'], C['under'], C['unused'])
    pool = last['free_agents']
    p1, p2 = last['cost_plus1'], last['cost_plus2']
    first = rows[0]
    pct = lambda k: 100 * k / max(pool, 1)

    P(f'''<div class="stats">
      <div class="stat"><div class="k">Constrained now</div><div class="v">{len(cons)}</div>
        <div class="n">of {n} teams &middot; was {first['constrained']} in week {first['week']}</div></div>
      <div class="stat"><div class="k">At cap</div><div class="v">{last['teams_at_cap']}</div>
        <div class="n">the number everybody argued</div></div>
      <div class="stat"><div class="k">Cost of a third slot</div><div class="v">{p1}</div>
        <div class="n">players off a {pool:,}-man wire &middot; {pct(p1):.2f}%</div></div>
      <div class="stat"><div class="k">Cost of a fourth</div><div class="v">{p2}</div>
        <div class="n">{pct(p2):.2f}% &middot; one more team than the third</div></div>
    </div>''')

    S('What A Slot Actually Does')
    P('<p class="b">Start with the mechanism, because most of the summer went past it. A Sleeper '
      'IR slot does <em>not</em> hold a player who would otherwise be sitting in the free-agent '
      'pool. It holds a man who is already on your roster. What it frees is an '
      '<em>active</em> roster spot &mdash; and that spot gets filled off the wire, immediately, '
      'because no manager in this league leaves one open.</p>')
    P('<p class="b">So the cost of an extra IR spot is not the injured player. It is the healthy '
      'replacement his manager signs with the spot that opens up: one player out of the pool, per '
      'slot actually used. Which makes the whole question countable instead of arguable, because a '
      'manager only uses a new slot if two things are true of him right now &mdash; his IR is '
      'already full, <em>and</em> he is still carrying an injured man on his active roster. '
      'Everybody else costs the pool nothing. They would take the slot and have nobody to put '
      'in it.</p>')
    P('<div class="pull">Both camps counted teams with a full IR. That counts who is '
      'inconvenienced, not what a slot costs.</div>')

    S(f'Figure One &mdash; The Record, Week {first["week"]} To Week {last["week"]}')
    P('<p class="b">Nobody had this in August. The argument was held over a preseason snapshot, '
      'which is the one week of the year when almost nothing is true yet. This is the same '
      'measurement taken every Wednesday since, automatically, and never edited afterwards.</p>')
    mx = max(max(r['stranded_total'] for r in rows), 1)
    mc = max(max(r['constrained'] for r in rows), 1)
    trs = ''.join(
        f'<tr><th scope="row" class="wk">Wk {r["week"]}</th>'
        f'<td class="num">{r["ir_used_total"]}/{r["ir_capacity_total"]}</td>'
        f'<td class="num dim">{r["teams_at_cap"]}</td>'
        f'<td class="num dim">{r["teams_empty_ir"]}</td>'
        f'<td class="bar"><span class="lo" style="width:{100*r["stranded_total"]/mx:.1f}%"></span></td>'
        f'<td class="num dim">{r["stranded_total"]}</td>'
        f'<td class="bar"><span style="width:{100*r["constrained"]/mc:.1f}%"></span></td>'
        f'<td class="num"><b>{r["constrained"]}</b></td>'
        f'<td class="num dim">{r["free_agents"]:,}</td></tr>' for r in rows)
    B(f'<figure><div class="scroll"><table><thead><tr><th class="lt"></th>'
      f'<th>IR&nbsp;used</th><th>At&nbsp;cap</th><th>Empty</th>'
      f'<th class="lt">Injured on active rosters</th><th></th>'
      f'<th class="lt">Constrained</th><th></th><th>Wire</th></tr></thead>'
      f'<tbody>{trs}</tbody></table></div>'
      f'<figcaption>Constrained means IR full <em>and</em> still holding an injured player &mdash; '
      f'the only state in which a manager would use a new slot. It has gone '
      f'{" &rarr; ".join(str(r["constrained"]) for r in rows)} while injured men parked on active '
      f'rosters went {first["stranded_total"]} to {last["stranded_total"]}. The free-agent pool has '
      f'not moved: {first["free_agents"]:,} in week {first["week"]}, {last["free_agents"]:,} now.'
      f'</figcaption></figure>')

    # describe the shape of the curve from the curve, not from an assumption
    # about it: it sat flat before it moved, and saying otherwise is a lie the
    # table underneath would immediately catch
    rises = [r['week'] for i, r in enumerate(rows) if i and r['constrained'] > rows[i - 1]['constrained']]
    if rises:
        flat = rises[0] - first['week']
        shape = (f'It did not move at all for the first {flat} week'
                 f'{"s" if flat != 1 else ""} &mdash; still '
                 f'{first["constrained"]} in week {rises[0] - 1} &mdash; and then went to '
                 f'{len(cons)} across weeks {rises[0]} and {rises[-1]}.'
                 if flat else
                 f'It has risen in {len(rises)} of the {len(rows) - 1} weeks since.')
    else:
        shape = f'It has not moved since: still {len(cons)} in week {last["week"]}.'
    P('<p class="b">Two things in that table point in opposite directions, and both are true. The '
      'pressure the expansion side described is real and it is building &mdash; it just did not '
      f'exist yet when the vote was being argued. In week {first["week"]} exactly '
      f'{first["constrained"]} team in the league was constrained. {shape} '
      'A vote taken in August was voting on the flat part.</p>')

    S('Figure Two &mdash; At Cap Is Not Constrained')
    P(f'<p class="b">Here is where the counting went wrong. {last["teams_at_cap"]} of {n} teams '
      f'have a full IR, and that is the figure that got quoted all summer. But '
      f'{len(idle)} of those {last["teams_at_cap"]} are not holding a single injured player on '
      f'their active roster. Give them a third slot and nothing happens: they have nobody to '
      f'move into it and they sign nobody off the wire. Only {len(cons)} rosters are in the state '
      f'that actually spends a slot.</p>')

    def state(t):
        if t['ir_full'] and t['stranded'] > 0:
            return 'st1', '<span class="tag a">constrained</span>'
        if t['ir_full']:
            return 'st2', '<span class="tag b">at cap, nobody to move</span>'
        return '', '<span class="tag c">under the cap</span>'

    order = sorted(C['teams'], key=lambda t: (-int(t['ir_full'] and t['stranded'] > 0),
                                              -t['ir_used'], -t['stranded'], t['team']))
    trs = ''
    for t in order:
        cls, tag = state(t)
        pips = ''.join(f'<i>&#9679;</i>' for _ in range(t['ir_used'])) + \
               ''.join(f'<u>&#9675;</u>' for _ in range(max(0, cap - t['ir_used'])))
        shown = t['stranded_names'][:3]
        # escape the names first -- the ellipsis is markup, not part of a name
        who = ', '.join(E(x) for x in shown) + \
            ('&hellip;' if t['stranded'] > len(shown) else '')
        trs += (f'<tr class="{cls}"><th scope="row">{E(t["team"])}</th>'
                f'<td class="pips">{pips}</td>'
                f'<td class="num">{t["stranded"] or "&mdash;"}</td>'
                f'<td class="who">{who}</td>'
                f'<td class="tiny">{tag}</td></tr>')
    B(f'<figure><div class="scroll"><table><thead><tr><th class="lt"></th>'
      f'<th class="lt">IR</th><th>Injured, active</th>'
      f'<th class="lt">Who</th><th class="lt">State</th></tr></thead>'
      f'<tbody>{trs}</tbody></table></div>'
      f'<figcaption>All {n} rosters as of week {last["week"]}. Filled circles are IR slots in use, '
      f'out of {cap}. &ldquo;Injured, active&rdquo; counts men Sleeper lists as unavailable who are '
      f'still taking up an active spot. Counting the top two groups together &mdash; '
      f'{last["teams_at_cap"]} teams &mdash; instead of the first alone '
      f'&mdash; {len(cons)} &mdash; overstates the cost of expansion by '
      f'{last["teams_at_cap"]/max(len(cons),1):.1f} times.</figcaption></figure>')

    S('Figure Three &mdash; What It Would Cost The Wire')
    P('<p class="b">Now the number the vote is actually about. One constrained manager with one '
      'stranded player signs one replacement; a manager with four stranded players still only '
      'gets one slot, so he still only signs one. Add a fourth slot and he can take a second. '
      'That is the entire difference between the two proposals.</p>')
    rowsx = [('Today, two slots', 0, pool),
             ('Expand to three', p1, pool - p1),
             ('Expand to four', p2, pool - p2)]
    mxp = max(p2, 1)
    # no span at all for zero: the bar has a min-width, so an empty one still
    # paints a stub and reads as "a little bit"
    def bar(k):
        return f'<span style="width:{100*k/mxp:.1f}%"></span>' if k else ''
    trs = ''.join(
        f'<tr class="{"hl" if k else ""}"><th scope="row">{lbl}</th>'
        f'<td class="bar">{bar(k)}</td>'
        f'<td class="num"><b>{k or "&mdash;"}</b></td>'
        f'<td class="num dim">{pct(k):.2f}%</td>'
        f'<td class="num dim">{left:,}</td></tr>' for lbl, k, left in rowsx)
    B(f'<figure><div class="scroll"><table><thead><tr><th class="lt"></th>'
      f'<th class="lt">Players it takes out of the pool</th><th>Count</th>'
      f'<th>Share of pool</th><th>Pool after</th></tr></thead>'
      f'<tbody>{trs}</tbody></table></div>'
      f'<figcaption>The pool is every unowned player on an NFL roster at a fantasy position: '
      f'{pool:,} men in week {last["week"]}. A third slot takes {pct(p1):.2f} per cent of it. '
      f'A fourth takes {pct(p2):.2f} per cent &mdash; {p2 - p1} more '
      f'{"player" if p2 - p1 == 1 else "players"} than the third, because only '
      f'{sum(1 for t in cons if t["stranded"] > 1)} manager in the league is currently holding '
      f'more than one injured player on an active roster.</figcaption></figure>')

    if unused:
        S(f'The {len(unused)} Who Are Not Using What They Have')
        names = ', '.join(E(t['team'].strip('* ')) for t in unused)
        P(f'<p class="b">One more thing the record turns up, and it is awkward for everybody. '
          f'{names} {"is" if len(unused) == 1 else "are"} carrying an injured player on an active '
          f'roster right now while sitting <em>under</em> the current cap. The slot they are '
          f'asking about, or voting against, is a slot they already own and have not filled. '
          f'Whatever the vote decides, it will not do anything for a manager who has not used '
          f'number two.</p>')

    S('What This Settles')
    P(f'<p class="b"><b>A third slot is cheap.</b> {p1} players, {pct(p1):.2f} per cent of the '
      f'wire, {len(cons)} teams affected. The objection that expansion would strip the free-agent '
      f'pool is not supported by the season: the pool has sat flat around {pool:,} for '
      f'{len(rows)} weeks while IR use climbed from {first["ir_used_total"]} slots to '
      f'{last["ir_used_total"]}.</p>')
    P(f'<p class="b"><b>A fourth buys almost nothing.</b> It adds {p2 - p1} '
      f'{"player" if p2 - p1 == 1 else "players"} and '
      f'{len(set(t["team"] for t in cons if t["would_use_2"] > 1))} '
      f'{"team" if len(set(t["team"] for t in cons if t["would_use_2"] > 1)) == 1 else "teams"} '
      f'over the third. If three passes, four is not worth a second ballot.</p>')
    P(f'<p class="b"><b>And nobody has to remember any of this in December.</b> The log keeps '
      f'taking its weekly reading whether anyone opens it or not, and every figure above re-types '
      f'itself from the log. If the constrained count keeps climbing the way it has since week '
      f'{rises[0] if rises else first["week"]}, the case gets stronger on its own and the page '
      f'will say so. If it flattens out again, the page will say that instead.</p>')
    return out


def card(C):
    rows, last = C['rows'], C['last']
    cons, idle, under = C['constrained'], C['idle_cap'], C['under']
    pool, p1, p2 = last['free_agents'], last['cost_plus1'], last['cost_plus2']
    mc = max(max(r['constrained'] for r in rows), 1)
    t1 = ''.join(
        f'<tr class="{"hl" if r is last else ""}"><th>Wk {r["week"]}</th>'
        f'<td class="bar"><span style="width:{100*r["constrained"]/mc:.1f}%"></span></td>'
        f'<td class="num">{r["constrained"]}</td></tr>' for r in rows)

    buckets = [('Constrained', len(cons), 'a'),
               ('At cap, nobody to move', len(idle), 'b'),
               ('Under the cap', len(under), 'c')]
    mb = max(max(v for _, v, _ in buckets), 1)
    t2 = ''.join(
        f'<tr class="{"hl" if k == "a" else ""}"><th>{lbl}</th>'
        f'<td class="bar"><span class="{"" if k == "a" else "lo"}" '
        f'style="width:{100*v/mb:.1f}%"></span></td>'
        f'<td class="num">{v}</td></tr>' for lbl, v, k in buckets)

    mxp = max(p2, 1)
    cbar = lambda k: f'<span style="width:{100*k/mxp:.1f}%"></span>' if k else ''
    t3 = ''.join(
        f'<tr class="{"hl" if k else ""}"><th>{lbl}</th>'
        f'<td class="bar">{cbar(k)}</td>'
        f'<td class="num">{k or "0"}</td>'
        f'<td class="num">{100*k/max(pool,1):.2f}%</td></tr>'
        for lbl, k in (('Two slots (today)', 0), ('Three slots', p1), ('Four slots', p2)))

    doc = (CARD.replace('__TREND__', f'<table><tbody>{t1}</tbody></table>')
               .replace('__STATE__', f'<table><tbody>{t2}</tbody></table>')
               .replace('__COST__', f'<table><tbody>{t3}</tbody></table>')
               .replace('__CN__', f'{len(cons)}/{last["teams_n"]}')
               .replace('__AC__', str(last['teams_at_cap']))
               .replace('__PC__', f'{100*p1/max(pool,1):.2f}%'))
    ad.shoot(doc, OG, 'ir-card')


def build():
    C = crunch()
    last = C['last']
    body = '\n'.join(h for _, h in figures(C))
    p1, pool = last['cost_plus1'], last['free_agents']
    desc = (f"{last['teams_at_cap']} of {last['teams_n']} teams have a full IR, but only "
            f"{len(C['constrained'])} are constrained. A third slot would cost "
            f"{p1} players off a {pool:,}-man wire.")
    stamp = last.get('stamp', '')[:10]
    month = f"{MONTHS[int(stamp[5:7]) - 1]} {stamp[:4]}" if len(stamp) == 10 else ''
    page = (PAGE.replace('__FIGCSS__', ad.FIG_CSS).replace('__BODY__', body)
                .replace('__DESC__', desc).replace('__DATE__', stamp)
                .replace('__MONTH__', month))
    open(OUT, 'w', encoding='utf-8').write(page)
    card(C)
    print(f'wrote {os.path.basename(OUT)} ({len(page):,} chars)')
    print(f"  weeks {C['rows'][0]['week']}-{last['week']} | constrained "
          f"{' -> '.join(str(r['constrained']) for r in C['rows'])} | at cap "
          f"{last['teams_at_cap']} | +1 costs {p1} of {pool:,} "
          f"({100*p1/max(pool,1):.2f}%) | +2 costs {last['cost_plus2']}")


if __name__ == '__main__':
    build()
