#!/usr/bin/env python3
"""The Transparent Research Addendum -- one product, two deliveries.

    python3 scripts/build_addendum.py [path/to/chats]

Computes the chat-engagement evidence behind the rivalry board once, then emits
it twice: a standalone page at scfl-addendum.html, and an article in
investigations.json that the Kickoff Issue renders as flip pages. Both come from
the same sections() call, so the two deliveries cannot say different things.

Only aggregates ship. The build checks the rendered page against every message
in the corpus and refuses to write if any run of thirty characters survives into
it. The corpus itself is not in this repo and never will be -- the Pages
workflow publishes the whole root.
"""
import collections, datetime, html, json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHATS = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('SCFL_CHATS',
    '/tmp/claude-0/-home-user-Claude/c302abf8-582a-5977-91c7-1dfbd915ffe3/scratchpad/chats')
OUT = os.path.join(ROOT, 'scfl-addendum.html')
ARTICLE_ID = 'kick-2026-addendum'
WINDOW = 420
MIN_GAMES = 8
RED, TEAL = '#c20f16', '#0e8ab5'      # both passed scripts/validate_palette.js

MERGE = {'scamp1467': 'danscampi', 'Dgclunie': 'MrBlast', 'espn39740077': 'papasuelo'}
LINE = re.compile(r'^\[(\d{1,2}/\d{1,2}/\d{2}), (\d{1,2}:\d{2}:\d{2}\s*[AP]M)\] ([^:]+): (.*)$')
CHAT = {'The Machines':'Balls143','Pork Chop Express':'danscampi','Smoke Dragons':'john420blaze',
 'Horse Collars':'mcnutze','Beavers':'sheq7777','Still The Creamiest':'MrBlast',
 'The Dry Dicks':'coachnick1980redfox','~ Wookie':'coachnick1980redfox',
 'Lil Chops':'ESPNFAN3503249627','Tom Vertucci':'tommyvertu123','Powers Of Pain':'Maristmidi',
 'New World Order':'TheKidd420','Jim Hunt':'westchesterwarrior','Killer Klowns':'Nando42',
 '~ Jay':'papasuelo','~ Pete':'cuzo77','~ Mike':'Michael Lagares'}
NAME = {'Balls143':'The Machines','danscampi':'Pork Chop Express','john420blaze':'Smoke Dragons',
 'mcnutze':'Horse Collars','sheq7777':'The Beaver Eaters','MrBlast':'Still The Creamiest',
 'coachnick1980redfox':'Wookie Leaks','ESPNFAN3503249627':'Lamb Chops','tommyvertu123':'Hairy Gumbas',
 'Maristmidi':'Powers of Pain','TheKidd420':'New World Order','westchesterwarrior':'Big Blue',
 'Nando42':'Killer Klowns','papasuelo':'Heavy Hitters','cuzo77':'Guido Haters',
 'Michael Lagares':'The Jet-I'}
ABBR = {'Balls143':'MAC','danscampi':'PCE','john420blaze':'DRA','mcnutze':'COL','sheq7777':'BVR',
 'MrBlast':'CRM','coachnick1980redfox':'WOO','ESPNFAN3503249627':'CHP','tommyvertu123':'GUM',
 'Maristmidi':'POP','TheKidd420':'NWO','westchesterwarrior':'BLU','Nando42':'KLW',
 'papasuelo':'HIT','cuzo77':'GUI','Michael Lagares':'JET'}
# The mention form drops the space after the tilde; both spellings are the same man.
MENT = re.compile(r'@[⁨]?\s*([^⁩@\n]{2,32}?)[⁩]|@([A-Za-z][A-Za-z .\']{2,24})')
MENTNAME = {'~Wookie':'coachnick1980redfox','~Jay':'papasuelo','~Pete':'cuzo77',
            '~Mike':'Michael Lagares','~Dave Sheq':'sheq7777','~ Dave Sheq':'sheq7777'}
HEAT = re.compile(r"\b(wrong|dumb|stupid|idiot|clown|joke|lying|lie|clueless|garbage|trash|pathetic|"
                  r"weak|soft|fraud|delusional|hypocrite|shut up|moron|dickhead|excuses|admit|cry|"
                  r"crying)\b", re.I)

_corpus = []
esc = lambda t: html.escape(str(t))


# ------------------------------------------------------------------ the data --
def compute():
    global _corpus
    ms = []
    for sub in ('official', 'mos'):
        p = os.path.join(CHATS, sub, '_chat.txt')
        if not os.path.exists(p):
            continue
        for raw in open(p, encoding='utf-8', errors='replace'):
            raw = raw.replace('‎', '').replace(' ', ' ').rstrip('\n')
            m = LINE.match(raw)
            if m:
                ms.append({'d': m.group(1), 't': m.group(2), 'who': m.group(3).strip(),
                           'x': m.group(4)})
            elif ms:
                ms[-1]['x'] += ' ' + raw.strip()
    if not ms:
        sys.exit(f'no chat exports under {CHATS} -- nothing to count')
    for m in ms:
        m['ts'] = datetime.datetime.strptime(m['d'] + ' ' + re.sub(r'\s', '', m['t']),
                                             '%m/%d/%y %I:%M:%S%p')
    ms.sort(key=lambda m: m['ts'])
    _corpus = ms

    volley, heated = collections.Counter(), collections.Counter()
    for i in range(1, len(ms)):
        a, b = ms[i - 1], ms[i]
        oa, ob = CHAT.get(a['who']), CHAT.get(b['who'])
        if a['who'] == b['who'] or not oa or not ob or oa == ob:
            continue
        if not 0 <= (b['ts'] - a['ts']).total_seconds() <= WINDOW:
            continue
        k = tuple(sorted((oa, ob)))
        volley[k] += 1
        if HEAT.search(b['x']) or HEAT.search(a['x']):
            heated[k] += 1
    tot = collections.Counter()
    for (a, b), n in volley.items():
        tot[a] += n; tot[b] += n

    ment, sent, recd = collections.Counter(), collections.Counter(), collections.Counter()
    for m in ms:
        src = CHAT.get(m['who'])
        if not src:
            continue
        for a, b in MENT.findall(m['x']):
            dst = CHAT.get((a or b).strip()) or MENTNAME.get((a or b).strip())
            if dst and dst != src:
                ment[(src, dst)] += 1; sent[src] += 1; recd[dst] += 1

    hist = json.load(open(os.path.join(ROOT, 'history.json'), encoding='utf-8'))
    mg = collections.Counter()
    for s in hist['seasons']:
        o = {t['id']: MERGE.get((t.get('owner') or '').strip(), (t.get('owner') or '').strip())
             for t in s['teams']}
        for m in s.get('matchups', []):
            a, b = o.get(m['home']), o.get(m['away'])
            if a and b and a != b:
                mg[tuple(sorted((a, b)))] += 1

    rivrows = json.load(open(os.path.join(ROOT, 'rivalries.json'), encoding='utf-8'))['rows']
    riv = {tuple(sorted((r['ka'], r['kb']))): r for r in rivrows}
    rank = {k: i + 1 for i, k in enumerate(sorted(riv, key=lambda k: -riv[k]['score']))}

    pairs = []
    for (a, b), v in volley.items():
        sa, sb = v / tot[a], v / tot[b]
        r = riv.get((a, b))
        pairs.append({'a': a, 'b': b, 'v': v, 'sa': sa, 'sb': sb, 'share': math.sqrt(sa * sb),
                      'heat': 100 * heated[(a, b)] / v, 'rank': rank.get((a, b)),
                      'rec': r['rec'] if r else None, 'div': r['div'] if r else 0,
                      'g': mg.get((a, b), 0)})
    pairs.sort(key=lambda p: -p['share'])
    teams = sorted(NAME, key=lambda k: -tot[k])
    return dict(ms=len(ms), span=(ms[0]['ts'].date(), ms[-1]['ts'].date()), volley=volley,
                heated=heated, tot=tot, ment=ment, sent=sent, recd=recd, pairs=pairs,
                teams=teams, mg=mg, riv=riv, rank=rank)


# ------------------------------------------------------------- shared styles --
FIG_CSS = """
/* ---- research addendum figures; shared by the standalone and the issue ---- */
.ad figure{margin:18px 0 0;}
.ad figcaption{font-family:var(--sans);font-size:11.5px;line-height:1.5;color:var(--muted,#65656b);
  margin-top:10px;padding-top:9px;border-top:1px solid var(--line,#e6e0d6);}
.ad .scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;}
.ad table{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:12.5px;}
.ad th,.ad td{padding:5px 7px;}
.ad tbody th{text-align:left;font-weight:700;white-space:nowrap;}
.ad .num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}
.ad .dim{color:var(--faint,#9a958c);} .ad .sep{color:var(--faint,#9a958c);}
.ad .vs{color:var(--faint,#9a958c);font-weight:400;font-style:italic;}
.ad thead th{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.11em;
  text-transform:uppercase;color:var(--faint,#9a958c);border-bottom:2px solid var(--ink,#17181c);
  text-align:right;white-space:nowrap;}
.ad thead th:first-child,.ad thead th.lt{text-align:left;}
.ad tbody tr + tr th,.ad tbody tr + tr td{border-top:1px solid var(--line,#e6e0d6);}
.ad .bar span{display:block;height:12px;background:var(--red,#c20f16);border-radius:0 3px 3px 0;
  min-width:2px;}
.ad .bar{width:46%;position:relative;}
.ad .bar span.lo{background:#0e8ab5;}
.ad .bar i.even{position:absolute;top:-2px;bottom:-2px;width:1px;background:var(--ink,#17181c);
  opacity:.45;}
.ad .mx{border-collapse:separate;border-spacing:2px;}
.ad .mx th{font-family:var(--sans);font-size:9px;font-weight:800;color:var(--muted,#65656b);
  padding:1px 3px;border:0;}
.ad .mx thead th{border-bottom:0;letter-spacing:0;}
.ad .mx tbody th{text-align:right;}
.ad .mx tbody tr + tr th,.ad .mx tbody tr + tr td{border-top:0;}
.ad .mx td{width:23px;height:23px;padding:0;border-radius:2px;}
.ad .mx td.c{background:color-mix(in oklab,var(--hue) calc(var(--k)*100%),#f4efe6);}
.ad .mx td.self{background:repeating-linear-gradient(135deg,#efe9de 0 3px,transparent 3px 6px);}
.ad .mx td.none{background:#f6f2ea;}
.ad .key{display:flex;align-items:center;gap:7px;margin-top:11px;font-family:var(--sans);
  font-size:10.5px;color:var(--muted,#65656b);flex-wrap:wrap;}
.ad .key .ramp{height:10px;width:120px;border-radius:2px;}
.ad .legend{display:flex;gap:16px;margin-top:11px;font-family:var(--sans);font-size:11px;
  color:var(--muted,#65656b);flex-wrap:wrap;}
.ad .legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;
  vertical-align:-1px;}
.ad .dumb{width:52%;position:relative;height:26px;}
.ad .track{position:absolute;left:0;right:0;top:12px;height:2px;background:var(--line,#e6e0d6);}
.ad .seg{position:absolute;top:12px;height:2px;background:var(--ink,#17181c);opacity:.28;}
.ad .dot{position:absolute;top:7px;width:11px;height:11px;border-radius:50%;margin-left:-5.5px;
  border:2px solid #fffdfb;}
.ad .dot.hi{background:var(--red,#c20f16);} .ad .dot.lo{background:#0e8ab5;}
.ad .tor{width:19%;} .ad .tor span{display:block;height:11px;}
.ad .tor.l{text-align:right;}
.ad .tor.l span{margin-left:auto;background:#0e8ab5;border-radius:3px 0 0 3px;}
.ad .tor.r span{background:var(--red,#c20f16);border-radius:0 3px 3px 0;}
.ad .who{color:var(--muted,#65656b);white-space:nowrap;}
.ad .pairs{list-style:none;margin:0;padding:0;display:grid;
  grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:1px;
  background:var(--line,#e6e0d6);border:1px solid var(--line,#e6e0d6);font-family:var(--sans);}
.ad .pairs li{background:#faf7f2;padding:9px 11px;display:flex;align-items:baseline;
  justify-content:space-between;gap:8px;}
.ad .pairs .p{font-size:11.5px;font-weight:800;} .ad .pairs .ar{color:var(--red,#c20f16);padding:0 4px;}
.ad .pairs .n{font-size:14px;font-weight:900;font-variant-numeric:tabular-nums;}
.ad .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(126px,1fr));gap:1px;
  background:var(--line,#e6e0d6);border:1px solid var(--line,#e6e0d6);margin:18px 0 0;}
.ad .stat{background:#faf7f2;padding:13px 14px;}
.ad .stat .k{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.14em;
  text-transform:uppercase;color:var(--faint,#9a958c);}
.ad .stat .v{font-weight:900;font-size:25px;line-height:1.1;margin-top:4px;
  font-variant-numeric:tabular-nums;}
.ad .stat .n{font-family:var(--sans);font-size:10.5px;color:var(--muted,#65656b);margin-top:2px;}
"""


# ------------------------------------------------------------- figure makers --
def mxfig(D, get, hue, keylo, keyhi, extra=''):
    """A 16x16 matrix. get(row,col) -> (k, tip) or None."""
    teams = D['teams']
    head = ''.join(f'<th scope="col" title="{esc(NAME[c])}">{ABBR[c]}</th>' for c in teams)
    rows = ''
    for r in teams:
        tds = ''
        for c in teams:
            if r == c:
                tds += '<td class="self" aria-hidden="true"></td>'; continue
            got = get(r, c)
            if not got:
                tds += '<td class="none" title="none recorded"></td>'; continue
            k, tip = got
            tds += (f'<td class="c" style="--k:{k:.3f}" tabindex="0" '
                    f'data-t="{esc(NAME[r])} &rarr; {esc(NAME[c])}" data-v="{tip}"></td>')
        rows += f'<tr><th scope="row" title="{esc(NAME[r])}">{ABBR[r]}</th>{tds}</tr>'
    return (f'<div class="scroll"><table class="mx" style="--hue:{hue}">'
            f'<thead><tr><td></td>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
            f'<div class="key"><span>{keylo}</span>'
            f'<span class="ramp" style="background:linear-gradient(90deg,#f4efe6,{hue})"></span>'
            f'<span>{keyhi}</span>{extra}</div>')


def sections(D):
    """The addendum, once. Returns [(kind, html)] where kind is sect|body."""
    P, T, tot = D['pairs'], D['teams'], D['tot']
    cell = {}
    for p in P:
        cell[(p['a'], p['b'])] = cell[(p['b'], p['a'])] = p
    out = []
    S = lambda t: out.append(('sect', f'<div class="sect">{t}</div>'))
    B = lambda h: out.append(('body', f'<div class="ad">{h}</div>'))

    vol = sum(D['volley'].values())
    B(f'''<div class="stats">
      <div class="stat"><div class="k">Messages read</div><div class="v">{D['ms']:,}</div>
        <div class="n">{D['span'][0]:%b %Y} &ndash; {D['span'][1]:%b %Y}</div></div>
      <div class="stat"><div class="k">Volleys</div><div class="v">{vol:,}</div>
        <div class="n">{len(D['volley'])} pairings</div></div>
      <div class="stat"><div class="k">Mentions</div><div class="v">{sum(D['ment'].values()):,}</div>
        <div class="n">direct @ address</div></div>
      <div class="stat"><div class="k">Tightest</div><div class="v">{P[0]['share']*100:.1f}%</div>
        <div class="n">{esc(NAME[P[0]['a']])} &amp; {esc(NAME[P[0]['b']])}</div></div>
    </div>''')

    S('The Measure')
    out.append(('body', '<p class="b">A volley is two managers speaking back to back: one posts, '
        f'a different one answers within {WINDOW//60} minutes, and that is one volley on their '
        'shared account. It is a deliberately dumb measure. It cannot read a room, it does not know '
        'who was addressing whom in a crowd, and it counts a joke exactly as heavily as a '
        'grievance.</p>'))
    out.append(('body', '<p class="b">What it is good at is the part that matters: it is '
        'symmetrical, it needs no interpretation, and nobody can lobby it. Two managers cannot '
        'volley without both of them showing up.</p>'))
    out.append(('body', '<p class="b">The figure the rankings use is not the raw count. It is the '
        'mutual share &mdash; the geometric mean of the two sides&rsquo; attention. If a pairing is '
        '20 per cent of your talk and 4 per cent of his, the mutual figure is 9, not 12. A geometric '
        'mean punishes lopsidedness on purpose, because one man shouting at another man is not a '
        'rivalry.</p>'))

    S('Figure One &mdash; Not Everybody Talks')
    top = max(tot.values())
    bars = ''.join(f'<tr><th scope="row">{esc(NAME[t])}</th>'
                   f'<td class="bar"><span style="width:{100*tot[t]/top:.1f}%"></span></td>'
                   f'<td class="num">{tot[t]:,}</td>'
                   f'<td class="num dim">{200*tot[t]/sum(tot.values()):.1f}%</td></tr>' for t in T)
    B(f'<figure><div class="scroll"><table><tbody>{bars}</tbody></table></div>'
      f'<figcaption>Volleys each franchise appears in. {esc(NAME[T[0]])} sits in {tot[T[0]]:,}; '
      f'{esc(NAME[T[-1]])} in {tot[T[-1]]:,} &mdash; a factor of {tot[T[0]]/tot[T[-1]]:.0f}. Rank on '
      f'raw volume and you would be ranking who types.</figcaption></figure>')

    S('Figure Two &mdash; Mutual Attention')
    hi = max(p['share'] for p in P)
    B('<figure>' + mxfig(D,
        lambda r, c: (cell[(r, c)]['share'] / hi,
                      f"{cell[(r,c)]['v']:,} volleys &middot; mutual "
                      f"{cell[(r,c)]['share']*100:.1f}%") if (r, c) in cell else None,
        RED, 'Less mutual', 'More',
        '<span style="margin-left:auto">Hatched = same manager</span>') +
      '<figcaption>Symmetrical by construction: a volley belongs to both managers. What differs '
      'across the diagonal is the share each side gives up, which is Figure Three.</figcaption></figure>')

    S('Figure Three &mdash; The One-Way Streets')
    lop = sorted((p for p in P if p['v'] >= 300), key=lambda p: -abs(p['sa'] - p['sb']))[:10]
    rows = ''
    for p in lop:
        hiS, loS = (p['a'], p['sa']), (p['b'], p['sb'])
        if loS[1] > hiS[1]:
            hiS, loS = loS, hiS
        mx = .32
        rows += (f'<tr><th scope="row">{ABBR[hiS[0]]} <span class="vs">and</span> {ABBR[loS[0]]}</th>'
                 f'<td class="dumb"><span class="track"></span>'
                 f'<span class="seg" style="left:{100*loS[1]/mx:.1f}%;right:{100-100*hiS[1]/mx:.1f}%"></span>'
                 f'<span class="dot lo" style="left:{100*loS[1]/mx:.1f}%"></span>'
                 f'<span class="dot hi" style="left:{100*hiS[1]/mx:.1f}%"></span></td>'
                 f'<td class="num"><b>{hiS[1]*100:.0f}%</b> <span class="sep">/</span> '
                 f'{loS[1]*100:.0f}%</td></tr>')
    B(f'<figure><div class="scroll"><table><tbody>{rows}</tbody></table></div>'
      f'<div class="legend"><span><i style="background:{RED}"></i>Gives the pairing more of his '
      f'talk</span><span><i style="background:{TEAL}"></i>Gives it less</span></div>'
      '<figcaption>Read the gap, not the dots. A wide gap is one man with a rival and one man with '
      'a fixture &mdash; precisely what the geometric mean exists to demote.</figcaption></figure>')

    S('Figure Four &mdash; Who Has One At All')
    best, bestwith, toppart = {}, {}, {}
    for p in P:
        for me, you, mine in ((p['a'], p['b'], p['sa']), (p['b'], p['a'], p['sb'])):
            if p['share'] > best.get(me, 0):
                best[me], bestwith[me] = p['share'], you
            if mine > toppart.get(me, 0):
                toppart[me] = mine
    EVEN, SC = 1 / 15, .26
    order = sorted(NAME, key=lambda t: best.get(t, 0))
    alone = [t for t in order if best.get(t, 0) < .07]
    rows = ''.join(
        f'<tr><th scope="row">{esc(NAME[t])}</th>'
        f'<td class="bar"><span class="{"lo" if best.get(t,0)<.07 else ""}" '
        f'style="width:{100*best.get(t,0)/SC:.1f}%"></span>'
        f'<i class="even" style="left:{100*EVEN/SC:.1f}%"></i></td>'
        f'<td class="num"><b>{best.get(t,0)*100:.1f}%</b></td>'
        f'<td class="who">{ABBR[bestwith[t]] if t in bestwith else "&mdash;"}</td>'
        f'<td class="num dim">{toppart.get(t,0)*100:.0f}%</td></tr>' for t in order)
    B(f'<figure><div class="scroll"><table><thead><tr><th class="lt"></th>'
      f'<th class="lt">Best mutual pairing he is in</th><th>Mutual</th><th class="lt">With</th>'
      f'<th>Top partner</th></tr></thead><tbody>{rows}</tbody></table></div>'
      f'<figcaption>The hairline is an even spread, {100/15:.1f}%. '
      f'{len(alone)} managers have no pairing clearing seven per cent against '
      f'{P[0]["share"]*100:.1f}% at the top &mdash; and their own top-partner share, last column, is '
      f'as concentrated as anybody&rsquo;s. The men they talk at do not talk back in the same '
      f'proportion.</figcaption></figure>')

    S('Figure Five &mdash; Where The Arguments Are')
    hh = max(p['heat'] for p in P)
    B('<figure>' + mxfig(D,
        lambda r, c: (cell[(r, c)]['heat'] / hh,
                      f"{cell[(r,c)]['heat']:.1f}% of {cell[(r,c)]['v']:,} volleys carry an "
                      f"argument word") if (r, c) in cell else None,
        RED, 'Cooler', 'Hotter') +
      '<figcaption>The same grid, coloured by the share of a pairing&rsquo;s volleys containing a '
      'word from a fixed argument list. Heat is a ranking input and nothing else: the desk has '
      'never published a line of chat on the strength of it.</figcaption></figure>')

    S('Figure Six &mdash; Direct Address')
    mxv = max(list(D['sent'].values()) + list(D['recd'].values()))
    rows = ''.join(
        f'<tr><th scope="row">{esc(NAME[t])}</th>'
        f'<td class="tor l"><span style="width:{100*D["sent"].get(t,0)/mxv:.1f}%"></span></td>'
        f'<td class="num dim">{D["sent"].get(t,0)}</td>'
        f'<td class="num dim">{D["recd"].get(t,0)}</td>'
        f'<td class="tor r"><span style="width:{100*D["recd"].get(t,0)/mxv:.1f}%"></span></td></tr>'
        for t in sorted(NAME, key=lambda k: -(D['sent'].get(k, 0) + D['recd'].get(k, 0))))
    two = 100 * (D['sent'].get('john420blaze', 0) + D['sent'].get('danscampi', 0)) / sum(D['sent'].values())
    B(f'<figure><div class="scroll"><table><thead><tr><th class="lt"></th><th>Sent</th>'
      f'<th>&nbsp;</th><th>&nbsp;</th><th class="lt">Received</th></tr></thead>'
      f'<tbody>{rows}</tbody></table></div>'
      f'<div class="legend"><span><i style="background:{TEAL}"></i>Names he typed</span>'
      f'<span><i style="background:{RED}"></i>Times he was named</span></div>'
      f'<figcaption>Sent and received are nearly unrelated. The Smoke Dragons and the Express '
      f'between them sent {two:.0f}% of every mention in the record; the Guido Haters have never '
      f'typed one and were still named {D["recd"].get("cuzo77",0)} times. An @ measures who reaches '
      f'for the feature.</figcaption></figure>')

    S('Figure Seven &mdash; The Asymmetric Grid')
    mm = max(D['ment'].values())
    B('<figure>' + mxfig(D,
        lambda r, c: (D['ment'][(r, c)] / mm,
                      f"{D['ment'][(r,c)]} mentions &middot; "
                      f"{100*D['ment'][(r,c)]/max(D['sent'].get(r,1),1):.0f}% of "
                      f"{esc(NAME[r])}&rsquo;s") if D['ment'].get((r, c)) else None,
        TEAL, 'Fewer', 'More @s sent',
        '<span style="margin-left:auto">Row @s column</span>') +
      '<figcaption>The only grid on this page that is not symmetrical, because naming somebody is '
      'something one man does to another. Read a row as outgoing. The bottom rows are nearly empty '
      'and the columns above them are not, which is the whole argument against ranking on '
      'this.</figcaption></figure>')

    S('Figure Eight &mdash; Does The Schedule Make The Talk?')
    buckets = [('Never shared a division', lambda d: d == 0),
               ('1&ndash;5 seasons together', lambda d: 1 <= d <= 5),
               ('6&ndash;10 seasons', lambda d: 6 <= d <= 10),
               ('11 or more', lambda d: d >= 11)]
    rows = ''
    for lab, f in buckets:
        sel = [p for p in P if f(p['div'])]
        if not sel:
            continue
        med = sorted(p['share'] for p in sel)[len(sel) // 2]
        rows += (f'<tr><th scope="row">{lab}</th><td class="num">{len(sel)}</td>'
                 f'<td class="bar"><span style="width:{100*med/0.13:.1f}%"></span></td>'
                 f'<td class="num"><b>{med*100:.1f}%</b></td>'
                 f'<td class="num dim">{sum(p["g"] for p in sel)/len(sel):.0f}</td></tr>')
    B(f'<figure><div class="scroll"><table><thead><tr><th class="lt">Divisional seasons together</th>'
      f'<th>Pairs</th><th class="lt">Median mutual share</th><th>Median</th><th>Avg games</th>'
      f'</tr></thead><tbody>{rows}</tbody></table></div>'
      '<figcaption>Shared divisions raise the talk, but not nearly in proportion to the games. '
      'This is why the rivalry score counts divisional seasons rather than raw meetings: a schedule '
      'can manufacture thirty games without either man choosing one of them.</figcaption></figure>')

    S('The Full Board')
    trs = ''
    for i, p in enumerate(P[:26]):
        rk = f'<b style="color:var(--red)">#{p["rank"]}</b>' if p['rank'] else '<span class="dim">&mdash;</span>'
        trs += (f'<tr><td class="num dim">{i+1}</td>'
                f'<th scope="row">{ABBR[p["a"]]} <span class="vs">v</span> {ABBR[p["b"]]}</th>'
                f'<td class="num">{p["v"]:,}</td><td class="num"><b>{p["share"]*100:.1f}%</b></td>'
                f'<td class="num dim">{p["sa"]*100:.0f}<span class="sep">/</span>{p["sb"]*100:.0f}</td>'
                f'<td class="num">{p["heat"]:.1f}%</td>'
                f'<td class="num{" dim" if p["g"]<MIN_GAMES else ""}">{p["g"]}</td>'
                f'<td class="num">{rk}</td></tr>')
    B(f'<figure><div class="scroll"><table><thead><tr><th></th><th class="lt">Pairing</th>'
      f'<th>Volleys</th><th>Mutual</th><th>Split</th><th>Heat</th><th>Played</th><th>Rank</th>'
      f'</tr></thead><tbody>{trs}</tbody></table></div>'
      f'<figcaption>Top 26 by mutual share. A dash under Rank means the pairing has played fewer '
      f'than {MIN_GAMES} games and never entered the rivalry board.</figcaption></figure>')

    S('What This Cannot Tell You')
    out.append(('body', '<p class="b">A volley is proximity, not address. In a fast group chat two '
        'managers can volley for an hour without once speaking to each other. It cannot see a reply '
        'posted eleven minutes late, and it weighs a joke exactly as heavily as a grievance.</p>'))
    out.append(('body', '<p class="b">Replies are not in the file at all. WhatsApp&rsquo;s text '
        'export carries the sender, the timestamp and the text and nothing else &mdash; a '
        'swipe-to-reply arrives as an ordinary message with no link back to the one it answered. '
        'That thread structure would be the best evidence here and it does not survive the export, '
        'which is why a seven-minute window is doing the work instead.</p>'))
    out.append(('body', '<p class="b">Sourcing: the league chats, '
        f'{D["span"][0]:%B %Y} to {D["span"][1]:%B %Y}. The volley definition is the same code path '
        'as scripts/build_rivalries.py, so this documents the ranking rather than describing a '
        'different measure. Only aggregate counts are published: the build checks the rendered page '
        f'against all {D["ms"]:,} messages and refuses to write if any run of thirty characters '
        'survives into it. The corpus is not in this repository and never will be.</p>'))
    return out


# ------------------------------------------------------------- the two builds --
STANDALONE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Transparent Research Addendum — SCFL NewsRoom</title>
<meta name="scfl:kicker" content="The Record Room · Aug 2026">
<meta name="scfl:published" content="2026-08-21">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SCFL NewsRoom">
<meta property="og:title" content="Transparent Research Addendum — how the rivalries were counted">
<meta property="og:description" content="__DESC__">
<meta property="og:image" content="https://watsoncapitalinvest-dot.github.io/Claude/scfl-grudge-og.jpg">
<link rel="icon" href="newsroom-favicon.png">
<style>
:root{--cream:#fffdfb;--paper:#faf7f2;--ink:#17181c;--muted:#65656b;--faint:#9a958c;
 --line:#e6e0d6;--red:#c20f16;
 --serif:Georgia,'Times New Roman',serif;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;}
body{margin:0;background:var(--cream);color:var(--ink);font-family:var(--serif);font-size:17px;
 line-height:1.62;-webkit-font-smoothing:antialiased;}
.wrap{max-width:900px;margin:0 auto;padding:0 20px 90px;}
.runhead{font-family:var(--sans);font-size:10.5px;font-weight:800;letter-spacing:.22em;
 text-transform:uppercase;color:var(--faint);border-bottom:1px solid var(--line);padding:20px 0 12px;}
.flag{font-family:var(--sans);font-size:10.5px;font-weight:900;letter-spacing:.24em;
 text-transform:uppercase;color:var(--red);margin-top:26px;display:block;}
h1{font-weight:900;font-size:clamp(32px,6.4vw,50px);line-height:1.03;letter-spacing:-.02em;
 margin:12px 0 0;text-wrap:balance;}
h1 em{font-style:normal;color:var(--red);}
.dek{font-style:italic;color:var(--muted);font-size:18px;margin:14px 0 0;max-width:62ch;}
.rule{height:3px;background:var(--red);width:70px;margin:22px 0 26px;}
.sect{font-family:var(--sans);font-size:11px;font-weight:900;letter-spacing:.2em;
 text-transform:uppercase;color:var(--red);margin:44px 0 12px;padding-top:14px;
 border-top:1px solid var(--line);}
p.b{margin:0 0 16px;max-width:62ch;}
footer{margin-top:56px;border-top:1px solid var(--line);padding-top:18px;font-family:var(--sans);
 font-size:12px;color:var(--muted);max-width:70ch;}
#tip{position:fixed;z-index:80;pointer-events:none;opacity:0;transition:opacity .12s;
 background:var(--ink);color:var(--cream);font-family:var(--sans);font-size:11.5px;line-height:1.45;
 padding:7px 10px;border-radius:4px;max-width:250px;box-shadow:0 6px 22px rgba(0,0,0,.28);}
#tip b{display:block;color:#fff;}
@media (prefers-reduced-motion:reduce){*{transition:none!important;}}
__FIGCSS__
</style></head>
<body><div class="wrap">
<div class="runhead">SCFL NewsRoom &middot; The Record Room &middot; August 2026</div>
<span class="flag">Transparent Research Addendum</span>
<h1>How The Rivalries Were <em>Counted</em></h1>
<p class="dek">Every rivalry ranking this desk has published rests on one number. Here is that
number for all sixteen managers, the eight figures behind it, and the four things it cannot do.</p>
<div class="rule"></div>
__BODY__
<footer>Built by <b>scripts/build_addendum.py</b>. This page and the version inside the 2026 Kickoff
Issue are generated from the same call, so the two cannot drift apart.</footer>
</div>
<div id="tip" role="status" aria-live="polite"></div>
<script>
(function(){var tip=document.getElementById('tip');
function show(el,e){tip.innerHTML='<b>'+el.dataset.t+'</b>'+el.dataset.v;tip.style.opacity='1';
 var r=el.getBoundingClientRect(),w=tip.offsetWidth,h=tip.offsetHeight;
 var x=(e&&e.clientX!=null?e.clientX:r.left+r.width/2)-w/2,y=r.top-h-10;
 if(y<6)y=r.bottom+10;
 tip.style.left=Math.max(8,Math.min(x,innerWidth-w-8))+'px';tip.style.top=y+'px';}
function hide(){tip.style.opacity='0';}
document.querySelectorAll('.mx td.c').forEach(function(c){
 c.addEventListener('mouseenter',function(e){show(c,e);});
 c.addEventListener('mousemove',function(e){show(c,e);});
 c.addEventListener('mouseleave',hide);
 c.addEventListener('focus',function(){show(c,null);});
 c.addEventListener('blur',hide);
 c.addEventListener('click',function(e){show(c,e);});});
document.addEventListener('scroll',hide,{passive:true});})();
</script></body></html>"""


def build():
    D = compute()
    blocks = sections(D)
    desc = (f"{sum(D['volley'].values()):,} volleys and {sum(D['ment'].values()):,} mentions across "
            f"ten years. The chat evidence behind every rivalry ranking, shown in full.")

    body = '\n'.join(h for _, h in blocks)
    page = (STANDALONE.replace('__FIGCSS__', FIG_CSS).replace('__BODY__', body)
                      .replace('__DESC__', desc))

    flat = re.sub(r'\s+', ' ', page)
    leaked = [t for t in (re.sub(r'\s+', ' ', m['x']).strip() for m in _corpus)
              if len(t) >= 30 and t in flat]
    if leaked:
        sys.exit(f'chat text leaked into the page: {leaked[:2]}')
    open(OUT, 'w', encoding='utf-8').write(page)

    # delivery two: the same blocks as an article the issue renders
    prose = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h)).strip()
             for k, h in blocks if k == 'body' and h.startswith('<p')]
    entry = {'id': ARTICLE_ID, 'slug': ARTICLE_ID,
             'flag': 'TRANSPARENT RESEARCH ADDENDUM', 'kicker': 'The Record Room',
             'headline': 'How The Rivalries Were Counted',
             'subhead': ('Every rivalry ranking this desk has published rests on one number. Here '
                         'is that number for all sixteen managers, the eight figures behind it, and '
                         'the four things it cannot do.'),
             'dateline': 'MOS EISLEY · AUGUST 2026', 'byline': 'The SCFL NewsRoom · The Record Room',
             'status': 'FILED', 'release': '', 'cover': '', 'staff': 'published',
             'paragraphs': prose, 'blocks': blocks}
    P = os.path.join(ROOT, 'investigations.json')
    d = json.load(open(P, encoding='utf-8'))
    inv = d['investigations']; inv[:] = [x for x in inv if x.get('id') != ARTICLE_ID]
    inv.insert(0, entry)
    tmp = P + '.tmp'
    json.dump(d, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.replace(tmp, P)

    print(f'wrote {os.path.basename(OUT)} ({len(page):,} chars) and {ARTICLE_ID} '
          f'({len(blocks)} blocks) from one build')
    print(f'  {D["ms"]:,} messages | {sum(D["volley"].values()):,} volleys | '
          f'{sum(D["ment"].values()):,} mentions | text check clean')


if __name__ == '__main__':
    build()
