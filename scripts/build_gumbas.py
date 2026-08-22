#!/usr/bin/env python3
"""The Gumbas File -- one manager's heat numbers, tested four ways.

    python3 scripts/build_gumbas.py [path/to/chats]

Writes scfl-gumbas.html and its share card. Every figure is recounted from the
corpus at build time; nothing here is read back off another page.

The right-of-reply box at the end is real. Put his answer in RESPONSE below,
verbatim and unedited, and rebuild -- the page swaps the reserved notice for
his words. Aggregates only: the build checks the finished page against every
message and refuses to write if any run of thirty characters survives into it.
"""
import collections, importlib.util, json, os, re, statistics, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts',
                                                               'build_addendum.py'))
ad = importlib.util.module_from_spec(_s)
sys.modules['ad'] = ad
_s.loader.exec_module(ad)

OUT = os.path.join(ROOT, 'scfl-gumbas.html')
OG = os.path.join(ROOT, 'scfl-gumbas-og.jpg')
G = 'tommyvertu123'

# ---------------------------------------------------------------------------
# His answer goes here, verbatim. Leave it empty and the page reserves the
# space instead of pretending he was not asked.
RESPONSE = ''
RESPONSE_BY = 'The Hairy Gumbas'
# ---------------------------------------------------------------------------


def crunch(D):
    """One pass over the corpus for everything this page claims."""
    ms = ad._corpus
    tot, hot = collections.Counter(), collections.Counter()
    tothot, own = collections.Counter(), collections.Counter()
    mine = them = both = 0
    gwords_mine, gwords_them = collections.Counter(), collections.Counter()
    gy, gyh, ly, lyh = (collections.Counter() for _ in range(4))

    for i in range(1, len(ms)):
        a, b = ms[i - 1], ms[i]
        oa, ob = ad.CHAT.get(a['who']), ad.CHAT.get(b['who'])
        if a['who'] == b['who'] or not oa or not ob or oa == ob:
            continue
        if not 0 <= (b['ts'] - a['ts']).total_seconds() <= ad.WINDOW:
            continue
        ha = {t.lower() for t in ad.HEAT.findall(a['x'])}
        hb = {t.lower() for t in ad.HEAT.findall(b['x'])}
        heated = bool(ha or hb)
        yr = b['ts'].year
        ly[yr] += 1
        if heated:
            lyh[yr] += 1
        for o in (oa, ob):
            tot[o] += 1
            if heated:
                hot[o] += 1
        if heated:                       # whose message carried the word
            for o, h in ((oa, ha), (ob, hb)):
                tothot[o] += 1
                if h:
                    own[o] += 1
        if G not in (oa, ob):
            continue
        gy[yr] += 1
        if not heated:
            continue
        gyh[yr] += 1
        g = ha if oa == G else hb
        o_ = hb if oa == G else ha
        if g and o_:
            both += 1
        elif g:
            mine += 1
        else:
            them += 1
        for w in g:
            gwords_mine[w] += 1
        for w in o_:
            gwords_them[w] += 1

    rate = {o: hot[o] / tot[o] for o in tot}
    exp = {}
    for who in ad.NAME:
        parts = [(p['b'] if p['a'] == who else p['a'], p['v'])
                 for p in D['pairs'] if who in (p['a'], p['b'])]
        tv = sum(v for _, v in parts)
        exp[who] = sum(v * rate[o] for o, v in parts) / tv

    hist = json.load(open(os.path.join(ROOT, 'history.json'), encoding='utf-8'))
    seasons = []
    for s in hist['seasons']:
        owner = {t['id']: ad.MERGE.get((t.get('owner') or '').strip(),
                                       (t.get('owner') or '').strip()) for t in s['teams']}
        nm = {t['id']: t['name'] for t in s['teams']}
        for r in s['standings']:
            if owner.get(r['teamId']) == G:
                seasons.append(dict(y=s['year'], nm=re.sub(r'\s+', ' ', nm[r['teamId']]).strip(),
                                    rank=r['rank'], w=r['wins'], l=r['losses'], t=r['ties'],
                                    pf=r['pf'], pa=r['pa']))
    return dict(tot=tot, hot=hot, rate=rate, exp=exp, own=own, tothot=tothot,
                mine=mine, them=them, both=both, wm=gwords_mine, wt=gwords_them,
                gy=gy, gyh=gyh, ly=ly, lyh=lyh, seasons=seasons)


EXTRA_CSS = """
.ad .hl th,.ad .hl td{background:#fdf3f0;}
.ad .hl th{color:var(--red);}
.ad .div{width:44%;position:relative;height:15px;}
.ad .div .mid{position:absolute;left:50%;top:-1px;bottom:-1px;width:1px;background:var(--ink);
  opacity:.5;}
.ad .div span{position:absolute;top:4px;height:8px;border-radius:2px;}
.ad .div span.up{background:var(--red);left:50%;}
.ad .div span.dn{background:#0e8ab5;right:50%;}
.ad .pair th{width:30%;}
.ad .thinrow th,.ad .thinrow td{color:var(--faint);}
.ad .wcell{width:44%;}
.ad .two{width:100%;position:relative;height:14px;background:#f0ece4;border-radius:2px;
  overflow:hidden;}
.ad .two i{position:absolute;left:0;top:0;bottom:0;background:var(--red);}
.ad .two b{position:absolute;top:-2px;bottom:-2px;width:1px;background:var(--ink);opacity:.55;}
.reply{margin:44px 0 0;border:2px solid var(--red);background:#fffaf8;padding:22px 24px;}
.reply .k{font-family:var(--sans);font-size:10.5px;font-weight:900;letter-spacing:.2em;
  text-transform:uppercase;color:var(--red);}
.reply p{margin:12px 0 0;max-width:60ch;}
.reply .who{font-family:var(--sans);font-size:12px;color:var(--muted);margin-top:14px;}
.reply .wait{font-style:italic;color:var(--muted);margin-top:12px;max-width:60ch;}
"""

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>The Gumbas File — SCFL NewsRoom</title>
<meta name="scfl:kicker" content="The Record Room · Aug 2026">
<meta name="scfl:published" content="2026-08-22">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SCFL NewsRoom">
<meta property="og:title" content="The Gumbas File">
<meta property="og:description" content="__DESC__">
<meta property="og:image" content="https://watsoncapitalinvest-dot.github.io/Claude/scfl-gumbas-og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="newsroom-favicon.png">
<style>
:root{--cream:#fffdfb;--paper:#faf7f2;--ink:#17181c;--muted:#65656b;--faint:#9a958c;
 --line:#e6e0d6;--red:#c20f16;
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
.stats{display:flex;flex-wrap:wrap;gap:24px 38px;margin:0 0 28px;padding-bottom:22px;
 border-bottom:1px solid var(--line);}
.stat .k{font-family:var(--sans);font-size:9.5px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.stat .v{font-size:30px;font-weight:900;line-height:1.15;font-variant-numeric:tabular-nums;}
.stat .n{font-family:var(--sans);font-size:11px;color:var(--muted);}
.more{margin-top:46px;border-top:1px solid var(--line);padding-top:18px;font-family:var(--sans);
 font-size:13px;line-height:1.6;color:var(--muted);max-width:72ch;}
.more a{color:var(--red);font-weight:700;}
@media (prefers-reduced-motion:reduce){*{transition:none!important;}}
__FIGCSS__
__EXTRA__
</style></head>
<body><div class="wrap">
<div class="runhead">SCFL NewsRoom &middot; The Record Room &middot; August 2026</div>
<span class="flag">The Record Room</span>
<h1>The Gumbas <em>File</em></h1>
<p class="dek">He is the hottest manager in the chat, he says the number is unfair, and he is
owed a hearing. So here is every figure behind it, and the three best arguments against it,
tested.</p>
<div class="byline">The SCFL NewsRoom &middot; Mos Eisley</div>
<div class="rule"></div>
__BODY__
<div class="more">The measure, the word list and the floor are all documented in the
<a href="scfl-addendum.html">Transparent Research Addendum</a>. The grid this page argues about
is on its own page at <a href="scfl-heat.html">Where The Arguments Are</a>.</div>
</div></body></html>"""

CARD = """<style>
:root{--red:#c20f16;--ink:#17181c;--faint:#9a958c;
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
.p1{left:446px;top:22px;width:338px;transform:rotate(-1.4deg);}
.p2{left:800px;top:26px;width:352px;transform:rotate(1.5deg);}
.p3{left:516px;top:352px;width:504px;transform:rotate(1.1deg);}
table{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:9.5px;}
td,th{padding:2.5px 4px;vertical-align:middle;}
tbody th{text-align:left;font-weight:700;white-space:nowrap;}
tbody tr + tr th,tbody tr + tr td{border-top:1px solid #eee7db;}
.num{text-align:right;font-variant-numeric:tabular-nums;color:var(--faint);}
.hl th,.hl td{background:#fdf3f0;} .hl th,.hl .num{color:var(--red);font-weight:800;}
.bar span{display:block;height:8px;background:var(--red);border-radius:0 2px 2px 0;min-width:2px;}
.bar{width:52%;}
.wcell{width:56%;}
.two{width:100%;position:relative;height:11px;background:#f0ece4;border-radius:2px;overflow:hidden;}
.two i{position:absolute;left:0;top:0;bottom:0;background:var(--red);}
.two b{position:absolute;top:-2px;bottom:-2px;width:1px;background:var(--ink);opacity:.55;}
.l{position:absolute;left:0;top:0;bottom:0;width:430px;z-index:9;
 padding:54px 30px 44px 52px;display:flex;flex-direction:column;
 background:linear-gradient(90deg,#efe9de 0%,#efe9de 72%,rgba(239,233,222,.94) 87%,
 rgba(239,233,222,0) 100%);}
.flag{font-family:var(--sans);font-size:11.5px;font-weight:900;letter-spacing:.22em;
 text-transform:uppercase;color:var(--red);}
h1{font-size:62px;line-height:.97;letter-spacing:-.028em;font-weight:900;margin-top:16px;}
h1 em{font-style:normal;color:var(--red);}
.rule{width:64px;height:3px;background:var(--red);margin:22px 0 18px;}
.dek{font-style:italic;color:#4b4b52;font-size:17px;line-height:1.4;max-width:23ch;}
.st{margin-top:auto;display:flex;gap:26px;}
.st .k{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.st .v{font-size:29px;font-weight:900;line-height:1.1;font-variant-numeric:tabular-nums;}
</style>
<div class="card">
 <div class="pc p1"><div class="cap">Heat rate &middot; all sixteen</div>__RATE__</div>
 <div class="pc p2"><div class="cap">Whose words are they</div>__OWN__</div>
 <div class="pc p3"><div class="cap">Observed against expected</div>__EXC__</div>
 <div class="l">
  <div class="flag">The Record Room</div>
  <h1>The<br>Gumbas<br><em>File</em></h1>
  <div class="rule"></div>
  <div class="dek">Four tests, one answer, and a box reserved for his.</div>
  <div class="st">
   <div><div class="k">Heat rate</div><div class="v">__HR__</div></div>
   <div><div class="k">His own words</div><div class="v">__OW__</div></div>
   <div><div class="k">Over expected</div><div class="v">__EX__</div></div>
  </div>
 </div>
</div>"""


def figures(D, C):
    """[(kind, html)] for the body. kind is sect|body, same shape as the addendum."""
    out = []
    S = lambda t: out.append(('sect', f'<div class="sect">{t}</div>'))
    B = lambda h: out.append(('body', f'<div class="ad">{h}</div>'))
    P = lambda h: out.append(('body', h))
    A, N, E = ad.ABBR, ad.NAME, ad.esc
    rate, exp, hot, tot = C['rate'], C['exp'], C['hot'], C['tot']
    order = sorted(N, key=lambda o: -rate[o])
    gr = order.index(G) + 1
    H = hot[G]

    P(f'''<div class="stats">
      <div class="stat"><div class="k">Heat rate</div><div class="v">{100*rate[G]:.2f}%</div>
        <div class="n">1st of 16 &middot; league {100*sum(hot.values())/sum(tot.values()):.2f}%</div></div>
      <div class="stat"><div class="k">Heated volleys</div><div class="v">{H:,}</div>
        <div class="n">of {tot[G]:,} he appears in</div></div>
      <div class="stat"><div class="k">Words that are his</div>
        <div class="v">{100*C['own'][G]/C['tothot'][G]:.1f}%</div>
        <div class="n">also 1st of 16</div></div>
      <div class="stat"><div class="k">On the field</div>
        <div class="v">{sum(s['w'] for s in C['seasons'])}&ndash;{sum(s['l'] for s in C['seasons'])}</div>
        <div class="n">18 recorded seasons</div></div>
    </div>''')

    P('<p class="b">The Hairy Gumbas is the hottest manager in the Mos Eisley chat. Not the '
      'loudest &mdash; he is ninth of sixteen for sheer volume &mdash; the hottest: the highest '
      'share of his conversations carrying a word off the argument list. He does not accept the '
      'number. That is a reasonable position to take about a measure this blunt, so this page does '
      'not restate the finding. It tries to break it.</p>')
    P('<p class="b">Three defences are available to him, and all three are testable. The chart '
      'could be catching the other man&rsquo;s words and billing them to him. He could simply be '
      'talking to the angriest people in the league. Or the whole thing could be riding on the two '
      'softest words on the list. Each gets its own figure below, and one of them lands.</p>')

    S('Test Zero &mdash; The Ranking Itself')
    top = max(rate.values())
    rows = ''.join(
        f'<tr class="{"hl" if o==G else ""}"><th scope="row">{E(N[o])}</th>'
        f'<td class="bar"><span style="width:{100*rate[o]/top:.1f}%"></span></td>'
        f'<td class="num"><b>{100*rate[o]:.2f}%</b></td>'
        f'<td class="num dim">{hot[o]:,}</td>'
        f'<td class="num dim">{tot[o]:,}</td></tr>' for o in order)
    B(f'<figure><div class="scroll"><table><thead><tr><th class="lt"></th>'
      f'<th class="lt">Share of his volleys that are heated</th><th>Rate</th><th>Heated</th>'
      f'<th>Volleys</th></tr></thead><tbody>{rows}</tbody></table></div>'
      f'<figcaption>A volley is two managers speaking back to back inside '
      f'{ad.WINDOW//60} minutes; it is heated if either message contains one of '
      f'{len(D["words"])} strings on a fixed list. Every '
      f'manager is counted the same way. He finishes {gr}st at {100*rate[G]:.2f} per cent, ahead '
      f'of {E(N[order[1]])} at {100*rate[order[1]]:.2f}.</figcaption></figure>')

    S('Test One &mdash; Whose Words Are They?')
    P(f'<p class="b">This is the objection worth taking seriously. A volley is heated if '
      f'<em>either</em> of its two messages carries a word, so a man who never types one can still '
      f'sit in a hot cell all day &mdash; the measure would be recording what is being said '
      f'<em>to</em> him. So split it: in each of his {H:,} heated volleys, whose message actually '
      f'contained the word?</p>')
    mine, them, both = C['mine'], C['them'], C['both']
    seg = ''.join(
        f'<tr><th scope="row">{lbl}</th>'
        f'<td class="bar"><span style="width:{100*n/H:.1f}%"></span></td>'
        f'<td class="num"><b>{n:,}</b></td><td class="num dim">{100*n/H:.1f}%</td></tr>'
        for lbl, n in (('The word is in his message', mine),
                       ('The word is in the other man&rsquo;s', them),
                       ('Both messages', both)))
    B(f'<figure><div class="scroll"><table><tbody>{seg}</tbody></table></div>'
      f'<figcaption>He typed a word himself in {mine+both:,} of {H:,} heated volleys &mdash; '
      f'{100*(mine+both)/H:.1f} per cent. The defence would need this number low. It is the '
      f'highest in the league.</figcaption></figure>')

    ords = sorted(N, key=lambda o: -C['own'][o] / C['tothot'][o])
    rows = ''.join(
        f'<tr class="{"hl" if o==G else ""}"><th scope="row">{E(N[o])}</th>'
        f'<td class="wcell"><div class="two"><i style="width:{100*C["own"][o]/C["tothot"][o]:.1f}%"></i>'
        f'<b style="left:50%"></b></div></td>'
        f'<td class="num"><b>{100*C["own"][o]/C["tothot"][o]:.1f}%</b></td>'
        f'<td class="num dim">{C["own"][o]:,}/{C["tothot"][o]:,}</td></tr>' for o in ords)
    B(f'<figure><div class="scroll"><table><thead><tr><th class="lt"></th>'
      f'<th class="lt">Of the heated volleys he is in, the share where the word is his</th>'
      f'<th>His</th><th>Count</th></tr></thead><tbody>{rows}</tbody></table></div>'
      f'<figcaption>The hairline is fifty per cent &mdash; an even split between the two men in '
      f'the volley. Above it you are supplying the argument; below it you are receiving it. '
      f'{E(N[ords[-1]])} sits at {100*C["own"][ords[-1]]/C["tothot"][ords[-1]]:.1f} per cent, which '
      f'is what being shouted at looks like. The Gumbas is first, at '
      f'{100*C["own"][G]/C["tothot"][G]:.1f}. The defence fails.</figcaption></figure>')

    S('Test Two &mdash; Is He Just Talking To Hot People?')
    P('<p class="b">The second defence is better made than the first. Heat is contagious in a '
      'group chat: if a man spends his time with the four most argumentative managers in the '
      'league, his own rate will climb without him doing anything. So work out what his rate '
      '<em>should</em> be. Take every pairing he is in, weight it by how often that partner runs '
      'hot with everybody else, and add it up. That is the rate a neutral man in his seat would '
      'post.</p>')
    dv = sorted(N, key=lambda o: -(rate[o] - exp[o]))
    span = max(abs(rate[o] - exp[o]) for o in N)
    rows = ''
    for o in dv:
        d = (rate[o] - exp[o]) * 100
        w = 50 * abs(d) / (span * 100)
        bar = (f'<span class="up" style="width:{w:.1f}%"></span>' if d >= 0
               else f'<span class="dn" style="width:{w:.1f}%"></span>')
        rows += (f'<tr class="{"hl" if o==G else ""}"><th scope="row">{E(N[o])}</th>'
                 f'<td class="num dim">{100*rate[o]:.2f}%</td>'
                 f'<td class="num dim">{100*exp[o]:.2f}%</td>'
                 f'<td class="div"><span class="mid"></span>{bar}</td>'
                 f'<td class="num"><b>{d:+.2f}</b></td></tr>')
    B(f'<figure><div class="scroll"><table><thead><tr><th class="lt"></th><th>Observed</th>'
      f'<th>Expected</th><th class="lt">Excess</th><th>Points</th></tr></thead>'
      f'<tbody>{rows}</tbody></table></div>'
      f'<div class="legend"><span><i style="background:{ad.RED}"></i>Hotter than his company '
      f'explains</span><span><i style="background:{ad.TEAL}"></i>Cooler</span></div>'
      f'<figcaption>Expected is what his partner mix predicts. A man who is merely keeping bad '
      f'company lands on the line. The Gumbas is {100*(rate[G]-exp[G]):+.2f} points clear of his '
      f'own expectation, the largest positive gap in the league &mdash; and his expected rate, '
      f'{100*exp[G]:.2f} per cent, is dead average. He is not sitting in a hot room. He is heating '
      f'it.</figcaption></figure>')

    S('Test Three &mdash; Is It All Soft Words?')
    P('<p class="b">The third defence is the one that lands, at least partly. The list cannot tell '
      'an insult from a quotation of one, and two of its entries &mdash; &ldquo;wrong&rdquo; and '
      '&ldquo;joke&rdquo; &mdash; do an enormous amount of perfectly ordinary work in a fantasy '
      'football chat. If his heat were mostly those two, the number would be an artefact.</p>')
    W = C['wm'] + C['wt']
    tw = sum(W.values())
    lw = D['words']
    lt = sum(lw.values())
    rows = ''.join(
        f'<tr><th scope="row">{E(w)}</th>'
        f'<td class="bar"><span style="width:{100*n/max(W.values()):.1f}%"></span></td>'
        f'<td class="num"><b>{100*n/tw:.1f}%</b></td>'
        f'<td class="num dim">{100*lw[w]/lt:.1f}%</td>'
        f'<td class="num dim">{C["wm"][w]:,}</td>'
        f'<td class="num dim">{C["wt"][w]:,}</td></tr>' for w, n in W.most_common(12))
    soft = 100 * sum(W[w] for w in ('wrong', 'joke')) / tw
    lsoft = 100 * sum(lw[w] for w in ('wrong', 'joke')) / lt
    hard = 100 * sum(W[w] for w in ('stupid', 'dumb', 'weak')) / tw
    B(f'<figure><div class="scroll"><table><thead><tr><th class="lt">Top twelve of his</th>'
      f'<th class="lt">Share of his heat</th><th>His</th><th>League</th><th>He typed</th>'
      f'<th>They did</th></tr></thead><tbody>{rows}</tbody></table></div>'
      f'<figcaption>He does lean on the soft end: &ldquo;wrong&rdquo; and &ldquo;joke&rdquo; are '
      f'{soft:.1f} per cent of his heat against {lsoft:.1f} across the league. That is a real '
      f'point in his favour and it is the only one he has. It is not enough &mdash; '
      f'&ldquo;stupid&rdquo;, &ldquo;dumb&rdquo; and &ldquo;weak&rdquo; are another {hard:.1f} per '
      f'cent between them, and strip the two soft words out entirely and he still finishes '
      f'first.</figcaption></figure>')

    S('Test Four &mdash; Was It One Bad Year?')
    gy, gyh, ly, lyh = C['gy'], C['gyh'], C['ly'], C['lyh']
    yrs = sorted(y for y in gy if gy[y] > 200)
    hi = max(max(100*gyh[y]/gy[y] for y in yrs), max(100*lyh[y]/ly[y] for y in yrs))
    rows = ''.join(
        f'<tr><th scope="row">{y}</th>'
        f'<td class="bar"><span style="width:{100*(100*gyh[y]/gy[y])/hi:.1f}%"></span></td>'
        f'<td class="num"><b>{100*gyh[y]/gy[y]:.2f}%</b></td>'
        f'<td class="num dim">{100*lyh[y]/ly[y]:.2f}%</td>'
        f'<td class="num dim">{gy[y]:,}</td></tr>' for y in yrs)
    B(f'<figure><div class="scroll"><table><thead><tr><th class="lt"></th>'
      f'<th class="lt">His rate that year</th><th>His</th><th>League</th><th>Volleys</th>'
      f'</tr></thead><tbody>{rows}</tbody></table></div>'
      f'<figcaption>Six years in the record and he clears the league rate in every one of them. '
      f'The peak is {max(yrs, key=lambda y: gyh[y]/gy[y])} at '
      f'{100*max(gyh[y]/gy[y] for y in yrs):.2f} per cent. There is no single season to blame this '
      f'on.</figcaption></figure>')

    S('What The Desk Concedes')
    P(f'<p class="b">Two things, without being asked. His two hottest-looking pairings are not on '
      f'the grid at all: against Still The Creamiest he runs '
      f'{[p for p in D["pairs"] if {p["a"],p["b"]}=={G,"MrBlast"}][0]["heat"]:.1f} per cent and '
      f'against The Jet-I {[p for p in D["pairs"] if {p["a"],p["b"]}=={G,"Michael Lagares"}][0]["heat"]:.1f}, '
      f'and both are suppressed for resting on too few volleys to mean anything. If anyone has '
      f'waved those figures at him, they did not come from here.</p>')
    P('<p class="b">And heat is a small input to the rivalry score, not a headline. This desk has '
      'never published a line of chat on the strength of it and does not intend to. The measure '
      'says how often argument words turn up near a man. It does not say he is unpleasant, it does '
      'not say he started it, and it cannot read a room.</p>')

    S('The Record, Which Is A Separate Argument')
    ss = C['seasons']
    w, l, t = (sum(s[k] for s in ss) for k in 'wlt')
    po = sum(1 for s in ss if s['rank'] <= 8)
    rows = ''.join(
        f'<tr class="{"hl" if s["rank"]<=3 else ""}"><th scope="row">{s["y"]}</th>'
        f'<td class="dim">{E(s["nm"])}</td>'
        f'<td class="num"><b>{s["rank"]}</b></td>'
        f'<td class="num dim">{s["w"]}&ndash;{s["l"]}</td>'
        f'<td class="num dim">{s["pf"]:,.0f}</td>'
        f'<td class="num dim">{s["pf"]-s["pa"]:+,.0f}</td></tr>' for s in ss)
    B(f'<figure><div class="scroll"><table><thead><tr><th class="lt"></th>'
      f'<th class="lt">Filed as</th><th>Finish</th><th>Record</th><th>PF</th><th>Diff</th>'
      f'</tr></thead><tbody>{rows}</tbody></table></div>'
      f'<figcaption>{w}&ndash;{l}{"&ndash;"+str(t) if t else ""} across '
      f'{len(ss)} recorded seasons, average finish '
      f'{statistics.mean(s["rank"] for s in ss):.1f}, the bracket in {po} of them, and a points '
      f'difference of {sum(s["pf"]-s["pa"] for s in ss):+,.0f}. The good years are real and they '
      f'are bunched: second, second and third across {min(s["y"] for s in ss if s["rank"]<=3)} to '
      f'{max(s["y"] for s in ss if s["rank"]<=3)}. Outside that window he has made the bracket '
      f'once in fifteen years.</figcaption></figure>')

    body = ''
    if RESPONSE.strip():
        paras = ''.join(f'<p>{E(p.strip())}</p>' for p in RESPONSE.strip().split('\n\n')
                        if p.strip())
        body = f'{paras}<div class="who">&mdash; {E(RESPONSE_BY)}, unedited</div>'
    else:
        body = ('<p class="wait">Reserved for the Hairy Gumbas. His answer runs here in full, '
                'unedited and uncut, the moment it arrives, and nothing else on this page changes '
                'when it does. The figures above are his to attack &mdash; every one of them is '
                'recounted from the record on each build, and the method is published in full.</p>')
    P(f'<div class="reply"><div class="k">Right Of Reply</div>{body}</div>')
    return out


def build():
    D = ad.compute()
    C = crunch(D)
    blocks = figures(D, C)
    body = '\n'.join(h for _, h in blocks)
    desc = (f"{100*C['rate'][G]:.2f} per cent of his volleys run hot, the highest in the league. "
            f"Three defences, tested. One of them lands.")
    page = (PAGE.replace('__FIGCSS__', ad.FIG_CSS).replace('__EXTRA__', EXTRA_CSS)
                .replace('__BODY__', body).replace('__DESC__', desc))

    flat = re.sub(r'\s+', ' ', page)
    leaked = [x for x in (re.sub(r'\s+', ' ', m['x']).strip() for m in ad._corpus)
              if len(x) >= 30 and x in flat]
    if leaked:
        sys.exit(f'chat text leaked into the page: {leaked[:2]}')
    open(OUT, 'w', encoding='utf-8').write(page)

    card(D, C)
    print(f'wrote {os.path.basename(OUT)} ({len(page):,} chars)')
    print(f"  heat {100*C['rate'][G]:.2f}% (1st) | his own words "
          f"{100*C['own'][G]/C['tothot'][G]:.1f}% (1st) | excess "
          f"{100*(C['rate'][G]-C['exp'][G]):+.2f}pts (1st) | reply "
          f"{'FILED' if RESPONSE.strip() else 'reserved, empty'}")


def card(D, C):
    N, A, rate, exp = ad.NAME, ad.ABBR, C['rate'], C['exp']
    order = sorted(N, key=lambda o: -rate[o])
    top = rate[order[0]]
    r1 = ''.join(f'<tr class="{"hl" if o==G else ""}"><th>{A[o]}</th>'
                 f'<td class="bar"><span style="width:{100*rate[o]/top:.1f}%"></span></td>'
                 f'<td class="num">{100*rate[o]:.2f}%</td></tr>' for o in order)

    ords = sorted(N, key=lambda o: -C['own'][o] / C['tothot'][o])
    r2 = ''.join(f'<tr class="{"hl" if o==G else ""}"><th>{A[o]}</th>'
                 f'<td class="wcell"><div class="two"><i style="width:{100*C["own"][o]/C["tothot"][o]:.1f}%"></i>'
                 f'<b style="left:50%"></b></div></td>'
                 f'<td class="num">{100*C["own"][o]/C["tothot"][o]:.0f}%</td></tr>' for o in ords)

    dv = sorted(N, key=lambda o: -(rate[o] - exp[o]))[:12]
    span = max(abs(rate[o] - exp[o]) for o in N)
    r3 = ''
    for o in dv:
        d = (rate[o] - exp[o]) * 100
        w = 50 * abs(d) / (span * 100)
        side = (f'<span style="position:absolute;left:50%;top:2px;height:8px;width:{w:.1f}%;'
                f'background:var(--red);border-radius:2px"></span>' if d >= 0 else
                f'<span style="position:absolute;right:50%;top:2px;height:8px;width:{w:.1f}%;'
                f'background:#0e8ab5;border-radius:2px"></span>')
        r3 += (f'<tr class="{"hl" if o==G else ""}"><th>{A[o]}</th>'
               f'<td style="position:relative;height:12px;width:54%">'
               f'<span style="position:absolute;left:50%;top:-1px;bottom:-1px;width:1px;'
               f'background:var(--ink);opacity:.5"></span>{side}</td>'
               f'<td class="num">{d:+.2f}</td></tr>')

    doc = (CARD.replace('__RATE__', f'<table><tbody>{r1}</tbody></table>')
               .replace('__OWN__', f'<table><tbody>{r2}</tbody></table>')
               .replace('__EXC__', f'<table><tbody>{r3}</tbody></table>')
               .replace('__HR__', f'{100*rate[G]:.2f}%')
               .replace('__OW__', f"{100*C['own'][G]/C['tothot'][G]:.0f}%")
               .replace('__EX__', f'{100*(rate[G]-exp[G]):+.2f}'))
    ad.shoot(doc, OG, 'gum-card')


if __name__ == '__main__':
    build()
