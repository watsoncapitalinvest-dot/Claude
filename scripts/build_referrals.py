#!/usr/bin/env python3
"""Build The Referral Room -- the chat-engagement evidence behind the rivalry board.

    python3 scripts/build_referrals.py [path/to/chats]

Reads the chat exports, counts volleys, and writes scfl-referrals.html. Only
aggregate counts reach the page: totals, shares, and heat rates. No message text
is written, and the corpus itself never enters the repo -- the Pages workflow
publishes the whole root.

The volley definition is lifted from scripts/build_rivalries.py deliberately, so
this page documents the ranking rather than describing a different measure.
"""
import collections, datetime, html, json, math, os, re, sys

MERGE = {'scamp1467':'danscampi','Dgclunie':'MrBlast','espn39740077':'papasuelo'}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHATS = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('SCFL_CHATS',
    '/tmp/claude-0/-home-user-Claude/c302abf8-582a-5977-91c7-1dfbd915ffe3/scratchpad/chats')
OUT = os.path.join(ROOT, 'scfl-referrals.html')
WINDOW = 420          # seconds; the reply window that defines a volley
MIN_GAMES = 8         # the rivalry board's own cutoff

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
HEAT = re.compile(r"\b(wrong|dumb|stupid|idiot|clown|joke|lying|lie|clueless|garbage|trash|pathetic|"
                  r"weak|soft|fraud|delusional|hypocrite|shut up|moron|dickhead|excuses|admit|cry|"
                  r"crying)\b", re.I)

# ---- house palette; the two categorical hues passed scripts/validate_palette.js
RED, TEAL = '#c20f16', '#0e8ab5'
_corpus = []


def load(path):
    ms = []
    for raw in open(path, encoding='utf-8', errors='replace'):
        # WhatsApp writes U+202F after the tilde in some display names, and
        # U+200E around attachments. Normalise both or five senders never match.
        raw = raw.replace('‎', '').replace(' ', ' ').rstrip('\n')
        m = LINE.match(raw)
        if m:
            ms.append({'d': m.group(1), 't': m.group(2), 'who': m.group(3).strip(), 'x': m.group(4)})
        elif ms:
            ms[-1]['x'] += ' ' + raw.strip()
    return ms


def gather():
    ms = []
    for sub in ('official', 'mos'):
        p = os.path.join(CHATS, sub, '_chat.txt')
        if os.path.exists(p):
            ms += load(p)
    if not ms:
        sys.exit(f'no chat exports under {CHATS} -- nothing to count')
    for m in ms:
        m['ts'] = datetime.datetime.strptime(m['d'] + ' ' + re.sub(r'\s', '', m['t']),
                                             '%m/%d/%y %I:%M:%S%p')
    ms.sort(key=lambda m: m['ts'])

    msgs = collections.Counter(CHAT[m['who']] for m in ms if m['who'] in CHAT)
    volley, heated, direc = collections.Counter(), collections.Counter(), collections.Counter()
    for i in range(1, len(ms)):
        a, b = ms[i - 1], ms[i]
        if a['who'] == b['who']:
            continue
        oa, ob = CHAT.get(a['who']), CHAT.get(b['who'])
        if not oa or not ob or oa == ob:
            continue
        if not 0 <= (b['ts'] - a['ts']).total_seconds() <= WINDOW:
            continue
        direc[(ob, oa)] += 1                     # b answered a
        k = tuple(sorted((oa, ob)))
        volley[k] += 1
        if HEAT.search(b['x']) or HEAT.search(a['x']):
            heated[k] += 1
    tot = collections.Counter()
    for (a, b), n in volley.items():
        tot[a] += n; tot[b] += n
    span = (ms[0]['ts'].date(), ms[-1]['ts'].date())
    global _corpus
    _corpus = ms
    return msgs, volley, heated, direc, tot, len(ms), span


def esc(t):
    return html.escape(str(t))


def meetings():
    """Head-to-head meeting counts per owner pair, from the league record."""
    h = json.load(open(os.path.join(ROOT, 'history.json'), encoding='utf-8'))
    mg = collections.Counter()
    for s in h['seasons']:
        o = {t['id']: MERGE.get((t.get('owner') or '').strip(), (t.get('owner') or '').strip())
             for t in s['teams']}
        for m in s.get('matchups', []):
            a, b = o.get(m['home']), o.get(m['away'])
            if a and b and a != b:
                mg[tuple(sorted((a, b)))] += 1
    return mg


def build():
    msgs, volley, heated, direc, tot, nmsg, span = gather()
    mg = meetings()
    riv = {tuple(sorted((r['ka'], r['kb']))): r
           for r in json.load(open(os.path.join(ROOT, 'rivalries.json'), encoding='utf-8'))['rows']}
    rank = {k: i + 1 for i, k in enumerate(
        sorted(riv, key=lambda k: -riv[k]['score']))}

    teams = sorted(NAME, key=lambda k: -tot[k])
    pairs = []
    for (a, b), v in volley.items():
        sa, sb = v / tot[a], v / tot[b]
        r = riv.get(tuple(sorted((a, b))))
        pairs.append({'a': a, 'b': b, 'v': v, 'sa': sa, 'sb': sb,
                      'share': math.sqrt(sa * sb),
                      'heat': 100 * heated[(a, b)] / v if v else 0,
                      'rank': rank.get(tuple(sorted((a, b)))),
                      'rec': r['rec'] if r else None,
                      'g': mg.get(tuple(sorted((a, b))), 0)})
    pairs.sort(key=lambda p: -p['share'])

    # ---------- figure 1: volleys per franchise -------------------------------
    top = max(tot.values())
    bars = ''.join(
        f'<tr><th scope="row">{esc(NAME[t])}</th>'
        f'<td class="bar"><span style="width:{100*tot[t]/top:.1f}%"></span></td>'
        f'<td class="num">{tot[t]:,}</td>'
        f'<td class="num pct">{100*tot[t]/sum(tot.values())*2:.1f}%</td></tr>'
        for t in teams)

    # ---------- figure 2: the matrix ------------------------------------------
    hi = max(p['share'] for p in pairs)
    cell = {}
    for p in pairs:
        cell[(p['a'], p['b'])] = cell[(p['b'], p['a'])] = p
    head = ''.join(f'<th scope="col" title="{esc(NAME[c])}">{ABBR[c]}</th>' for c in teams)
    rows = ''
    for r in teams:
        tds = ''
        for c in teams:
            if r == c:
                tds += '<td class="self" aria-hidden="true"></td>'; continue
            p = cell.get((r, c))
            if not p:
                tds += '<td class="none" title="no volleys recorded"></td>'; continue
            k = p['share'] / hi
            mine = (p['sa'] if p['a'] == r else p['sb']) * 100
            tds += (f'<td class="c" style="--k:{k:.3f}" tabindex="0" '
                    f'data-t="{esc(NAME[r])} &rarr; {esc(NAME[c])}" '
                    f'data-v="{p["v"]:,} volleys &middot; {mine:.1f}% of {esc(NAME[r])}&rsquo;s talk '
                    f'&middot; mutual {p["share"]*100:.1f}%"></td>')
        rows += f'<tr><th scope="row" title="{esc(NAME[r])}">{ABBR[r]}</th>{tds}</tr>'

    # ---------- figure 3: the lopsided ones -----------------------------------
    lop = sorted((p for p in pairs if p['v'] >= 300),
                 key=lambda p: -abs(p['sa'] - p['sb']))[:10]
    dumb = ''
    for p in lop:
        hiS, loS = (p['a'], p['sa']), (p['b'], p['sb'])
        if loS[1] > hiS[1]:
            hiS, loS = loS, hiS
        mx = 0.32
        dumb += (
          f'<tr><th scope="row">{esc(NAME[hiS[0]])} <span class="vs">and</span> '
          f'{esc(NAME[loS[0]])}</th>'
          f'<td class="dumb"><span class="track"></span>'
          f'<span class="seg" style="left:{100*loS[1]/mx:.1f}%;'
          f'right:{100-100*hiS[1]/mx:.1f}%"></span>'
          f'<span class="dot lo" style="left:{100*loS[1]/mx:.1f}%" '
          f'title="{esc(NAME[loS[0]])} {loS[1]*100:.1f}%"></span>'
          f'<span class="dot hi" style="left:{100*hiS[1]/mx:.1f}%" '
          f'title="{esc(NAME[hiS[0]])} {hiS[1]*100:.1f}%"></span></td>'
          f'<td class="num"><b>{hiS[1]*100:.0f}%</b> <span class="sep">/</span> '
          f'{loS[1]*100:.0f}%</td></tr>')

    # ---------- the table -----------------------------------------------------
    trs = ''
    for i, p in enumerate(pairs[:28]):
        rk = f'<span class="rk">#{p["rank"]}</span>' if p['rank'] else '<span class="rk off">—</span>'
        trs += (f'<tr><td class="num dim">{i+1}</td>'
                f'<th scope="row">{esc(NAME[p["a"]])} <span class="vs">v</span> '
                f'{esc(NAME[p["b"]])}</th>'
                f'<td class="num">{p["v"]:,}</td>'
                f'<td class="num"><b>{p["share"]*100:.1f}%</b></td>'
                f'<td class="num">{p["sa"]*100:.0f}<span class="sep">/</span>{p["sb"]*100:.0f}</td>'
                f'<td class="num">{p["heat"]:.1f}%</td>'
                f'<td class="num{" dim" if p["g"] < MIN_GAMES else ""}">{p["g"]}</td>'
                f'<td class="num">{esc(p["rec"] or "—")}</td>'
                f'<td class="num">{rk}</td></tr>')

    counted = sum(msgs.values())
    doc = PAGE.format(
        RED=RED, TEAL=TEAL,
        nmsg=f'{nmsg:,}', counted=f'{counted:,}', vol=f'{sum(volley.values()):,}',
        npairs=len(volley), span0=span[0].strftime('%B %Y'), span1=span[1].strftime('%B %Y'),
        window=WINDOW // 60, bars=bars, head=head, rows=rows, dumb=dumb, trs=trs,
        loud=esc(NAME[teams[0]]), loudn=f'{tot[teams[0]]:,}',
        quiet=esc(NAME[teams[-1]]), quietn=f'{tot[teams[-1]]:,}',
        ratio=f'{tot[teams[0]]/max(tot[teams[-1]],1):.0f}',
        tophair=esc(NAME[pairs[0]['a']]) + ' and ' + esc(NAME[pairs[0]['b']]),
        topshare=f"{pairs[0]['share']*100:.1f}", topg=pairs[0]['g'],
        mingames=MIN_GAMES)
    # House rule, enforced rather than trusted: only aggregates may ship. Check the
    # rendered page against the corpus itself -- no substantial run of any message
    # may appear in it.
    flat = re.sub(r'\s+', ' ', doc)
    leaked = [t for t in (re.sub(r'\s+', ' ', m['x']).strip() for m in _corpus)
              if len(t) >= 30 and t in flat]
    if leaked:
        sys.exit(f'chat text leaked into the page: {leaked[:3]}')

    open(OUT, 'w', encoding='utf-8').write(doc)
    print(f'wrote {os.path.basename(OUT)} | {nmsg:,} messages | {sum(volley.values()):,} volleys '
          f'| {len(volley)} pairs | {len(doc):,} chars')
    print(f'  text check: no run of 30+ characters from any of {len(_corpus):,} messages '
          f'appears in the output')


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>The Referral Room — SCFL NewsRoom</title>
<meta name="scfl:kicker" content="The Record Room · Aug 2026">
<meta name="scfl:published" content="2026-08-21">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SCFL NewsRoom">
<meta property="og:title" content="The Referral Room — who actually talks to whom">
<meta property="og:description" content="{vol} volleys across {npairs} pairings. The chat evidence the rivalry rankings were built on, shown in full.">
<meta property="og:image" content="https://watsoncapitalinvest-dot.github.io/Claude/scfl-grudge-og.jpg">
<link rel="icon" href="newsroom-favicon.png">
<style>
:root{{
  --cream:#fffdfb; --paper:#faf7f2; --ink:#17181c; --muted:#65656b; --faint:#9a958c;
  --line:#e6e0d6; --red:{RED}; --teal:{TEAL};
  --serif:Georgia,'Times New Roman',serif;
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
}}
*{{box-sizing:border-box;}}
.sr-only{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;
  clip:rect(0 0 0 0);white-space:nowrap;border:0;}}
body{{margin:0;background:var(--cream);color:var(--ink);font-family:var(--serif);
  font-size:17px;line-height:1.6;-webkit-font-smoothing:antialiased;}}
.wrap{{max-width:940px;margin:0 auto;padding:0 20px 90px;}}
.runhead{{font-family:var(--sans);font-size:10.5px;font-weight:800;letter-spacing:.22em;
  text-transform:uppercase;color:var(--faint);border-bottom:1px solid var(--line);
  padding:20px 0 12px;}}
h1{{font-family:var(--serif);font-weight:900;font-size:clamp(34px,7vw,54px);line-height:1.02;
  letter-spacing:-.02em;margin:26px 0 0;text-wrap:balance;}}
h1 em{{font-style:normal;color:var(--red);}}
.dek{{font-style:italic;color:var(--muted);font-size:18px;margin:14px 0 0;max-width:62ch;}}
.rule{{height:3px;background:var(--red);width:70px;margin:22px 0 0;}}
h2{{font-family:var(--sans);font-size:11px;font-weight:900;letter-spacing:.22em;
  text-transform:uppercase;color:var(--red);margin:0 0 4px;}}
.sec{{margin-top:52px;}}
.sec > p{{margin:0 0 18px;max-width:62ch;}}
.lede{{font-size:19px;}}
.lede .drop{{float:left;font-size:58px;line-height:.82;font-weight:900;padding:4px 9px 0 0;color:var(--red);}}
figure{{margin:22px 0 0;}}
figcaption{{font-family:var(--sans);font-size:12px;color:var(--muted);margin-top:12px;
  padding-top:10px;border-top:1px solid var(--line);max-width:70ch;}}
.scroll{{overflow-x:auto;-webkit-overflow-scrolling:touch;}}

/* --- stat strip --- */
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);margin-top:26px;}}
.stat{{background:var(--paper);padding:16px 18px;}}
.stat .k{{font-family:var(--sans);font-size:10px;font-weight:800;letter-spacing:.16em;
  text-transform:uppercase;color:var(--faint);}}
.stat .v{{font-family:var(--serif);font-weight:900;font-size:30px;line-height:1.1;margin-top:6px;
  font-variant-numeric:tabular-nums;}}
.stat .n{{font-family:var(--sans);font-size:11.5px;color:var(--muted);margin-top:3px;}}

/* --- shared table furniture --- */
table{{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:13px;}}
th,td{{padding:6px 8px;}}
tbody th{{text-align:left;font-weight:700;white-space:nowrap;}}
.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}}
.dim{{color:var(--faint);}}
.sep{{color:var(--faint);}}
.vs{{color:var(--faint);font-weight:400;font-style:italic;}}
.pct{{color:var(--muted);}}

/* --- fig 1: volley bars --- */
.bars tbody tr + tr th,.bars tbody tr + tr td{{border-top:1px solid var(--line);}}
.bars .bar{{width:56%;}}
.bars .bar span{{display:block;height:13px;background:var(--red);border-radius:0 3px 3px 0;
  min-width:2px;}}

/* --- fig 2: matrix --- */
.mx{{border-collapse:separate;border-spacing:2px;font-size:11px;}}
.mx th{{font-family:var(--sans);font-size:9.5px;font-weight:800;letter-spacing:.06em;
  color:var(--muted);padding:2px 4px;}}
.mx tbody th{{text-align:right;}}
.mx td{{width:26px;height:26px;padding:0;border-radius:2px;}}
.mx td.c{{background:color-mix(in oklab,var(--red) calc(var(--k)*100%),#f4efe6);cursor:default;}}
.mx td.c:focus{{outline:2px solid var(--ink);outline-offset:1px;}}
.mx td.self{{background:repeating-linear-gradient(135deg,#efe9de 0 3px,transparent 3px 6px);}}
.mx td.none{{background:#f6f2ea;}}
.key{{display:flex;align-items:center;gap:8px;margin-top:14px;font-family:var(--sans);
  font-size:11.5px;color:var(--muted);}}
.key .ramp{{height:11px;width:150px;border-radius:2px;
  background:linear-gradient(90deg,#f4efe6,var(--red));}}

/* --- fig 3: dumbbells --- */
.dumbs tbody tr + tr th,.dumbs tbody tr + tr td{{border-top:1px solid var(--line);}}
.dumbs .dumb{{width:58%;position:relative;height:30px;}}
.dumbs .track{{position:absolute;left:0;right:0;top:14px;height:2px;background:var(--line);}}
.dumbs .seg{{position:absolute;top:14px;height:2px;background:var(--ink);opacity:.28;}}
.dumbs .dot{{position:absolute;top:9px;width:12px;height:12px;border-radius:50%;
  margin-left:-6px;border:2px solid var(--cream);}}
.dumbs .dot.hi{{background:var(--red);}}
.dumbs .dot.lo{{background:var(--teal);}}
.legend{{display:flex;gap:18px;margin-top:14px;font-family:var(--sans);font-size:11.5px;
  color:var(--muted);flex-wrap:wrap;}}
.legend i{{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:6px;
  vertical-align:-1px;}}

/* --- the big table --- */
.full thead th{{font-family:var(--sans);font-size:9.5px;font-weight:800;letter-spacing:.12em;
  text-transform:uppercase;color:var(--faint);border-bottom:2px solid var(--ink);
  text-align:right;white-space:nowrap;}}
.full thead th:nth-child(2){{text-align:left;}}
.full tbody tr + tr th,.full tbody tr + tr td{{border-top:1px solid var(--line);}}
.full tbody tr:hover th,.full tbody tr:hover td{{background:var(--paper);}}
.rk{{font-weight:800;color:var(--red);}}
.rk.off{{color:var(--faint);font-weight:400;}}

.note{{border-left:3px solid var(--red);padding:2px 0 2px 18px;margin-top:26px;
  font-size:15.5px;color:var(--muted);max-width:64ch;}}
.note b{{color:var(--ink);}}
footer{{margin-top:56px;border-top:1px solid var(--line);padding-top:18px;
  font-family:var(--sans);font-size:12px;color:var(--muted);max-width:70ch;}}

#tip{{position:fixed;z-index:80;pointer-events:none;opacity:0;transition:opacity .12s;
  background:var(--ink);color:var(--cream);font-family:var(--sans);font-size:11.5px;
  line-height:1.45;padding:7px 10px;border-radius:4px;max-width:240px;
  box-shadow:0 6px 22px rgba(0,0,0,.28);}}
#tip b{{display:block;color:#fff;}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important;}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="runhead">SCFL NewsRoom &middot; The Record Room &middot; August 2026</div>

  <h1>The Referral <em>Room</em></h1>
  <p class="dek">Every rivalry ranking this newsroom has published rests on one number:
  how much of a manager&rsquo;s talk is aimed at one other manager. Here is that number,
  for all sixteen, with nothing held back.</p>
  <div class="rule"></div>

  <div class="stats">
    <div class="stat"><div class="k">Messages read</div><div class="v">{nmsg}</div>
      <div class="n">{counted} from a mapped franchise</div></div>
    <div class="stat"><div class="k">Volleys counted</div><div class="v">{vol}</div>
      <div class="n">across {npairs} pairings</div></div>
    <div class="stat"><div class="k">Span</div><div class="v">10 yrs</div>
      <div class="n">{span0} &ndash; {span1}</div></div>
    <div class="stat"><div class="k">Tightest pair</div><div class="v">{topshare}%</div>
      <div class="n">{tophair}</div></div>
  </div>

  <div class="sec">
    <h2>What is being counted</h2>
    <p class="lede"><span class="drop">A</span> volley is two managers speaking back to back.
    One posts, a different one answers within {window} minutes, and that is one volley on
    their shared account. It is a deliberately dumb measure. It cannot read a room, it does
    not know who was talking to whom in a crowd, and it treats a joke and an argument the
    same way.</p>
    <p>What it is good at is the thing that matters here: it is symmetrical, it needs no
    interpretation, and nobody can lobby it. Two managers cannot volley without both of
    them showing up.</p>
    <p>The number the rankings actually use is not the raw count. It is the
    <b>mutual share</b> &mdash; the geometric mean of the two sides&rsquo; attention. If a
    pairing is 20% of your talk and 4% of his, the mutual figure is 9%, not 12%. A
    geometric mean punishes lopsidedness on purpose, because one man shouting at another
    man is not a rivalry.</p>
  </div>

  <div class="sec">
    <h2>Figure 1 &middot; Not everybody talks</h2>
    <p>Before any of it means anything: the raw volumes are wildly unequal. This is the
    reason nothing here is ranked on raw counts.</p>
    <figure>
      <div class="scroll"><table class="bars">
        <caption class="sr-only">Volleys per franchise</caption>
        <tbody>{bars}</tbody>
      </table></div>
      <figcaption>Volleys each franchise appears in, and that as a share of all volleys.
      {loud} sits in {loudn}; {quiet} sits in {quietn}. That is a factor of about
      {ratio}. Rank on raw volume and you would simply be ranking who types.</figcaption>
    </figure>
  </div>

  <div class="sec">
    <h2>Figure 2 &middot; The board</h2>
    <p>Every pairing at once. Read a row: that is one manager&rsquo;s attention, spread
    across the other fifteen. Darker is a larger share of the mutual figure. Hover or
    tap any cell for the exact split.</p>
    <figure>
      <div class="scroll"><table class="mx">
        <thead><tr><td></td>{head}</tr></thead>
        <tbody>{rows}</tbody>
      </table></div>
      <div class="key"><span>Less mutual</span><span class="ramp"></span><span>More</span>
        <span style="margin-left:auto">Hatched = same manager &middot; blank = no volleys recorded</span></div>
      <figcaption>The matrix is symmetrical by construction &mdash; a volley belongs to both
      managers &mdash; so the two halves mirror. What differs across the diagonal is the
      share each side gives up, which is Figure 3.</figcaption>
    </figure>
  </div>

  <div class="sec">
    <h2>The loudest pair in the league have barely played</h2>
    <p>The single highest mutual figure in these ten years belongs to <b>{tophair}</b>, at
    <b>{topshare}%</b>. Nearly a quarter of everything either man says in this chat is said
    next to the other one. They have met <b>{topg} times</b> in eighteen seasons.</p>
    <p>That is under the rivalry board&rsquo;s {mingames}-game cutoff, so the pairing has never
    appeared on it and never will until the schedule puts them together. Both things are
    true at once: they talk more than any two men in the league, and they have no series
    worth the name. It is the clearest evidence on this page that chat volume alone is not
    a rivalry &mdash; and the clearest limit of a board that needs games before it will
    listen.</p>
  </div>

  <div class="sec">
    <h2>Figure 3 &middot; The one-way streets</h2>
    <p>The ten most lopsided pairings with enough traffic to mean anything. Each line runs
    from the manager who cares less to the manager who cares more.</p>
    <figure>
      <div class="scroll"><table class="dumbs"><tbody>{dumb}</tbody></table></div>
      <div class="legend">
        <span><i style="background:{RED}"></i>Gives the pairing a larger share of his talk</span>
        <span><i style="background:{TEAL}"></i>Gives it a smaller share</span>
      </div>
      <figcaption>Read the gap, not the dots. A wide gap is a manager who has a rival and a
      manager who has a fixture. This is precisely what the geometric mean is built to
      demote, and why several of these pairings rank lower than their volume suggests.</figcaption>
    </figure>
  </div>

  <div class="sec">
    <h2>The full board</h2>
    <p>Every pairing ranked by mutual share. <b>Split</b> is the two directional shares,
    his and his. <b>Heat</b> is the share of their volleys carrying a word from the
    argument list. <b>Rank</b> is where the pairing finished on the published rivalry
    board, which weighs this alongside the record, the postseason and shared divisional
    seasons.</p>
    <figure>
      <div class="scroll"><table class="full">
        <thead><tr><th></th><th>Pairing</th><th>Volleys</th><th>Mutual</th><th>Split</th>
          <th>Heat</th><th>Played</th><th>Record</th><th>Rivalry</th></tr></thead>
        <tbody>{trs}</tbody>
      </table></div>
      <figcaption>Top 28 by mutual share. A dash under Rivalry means the pairing has played
      fewer than {mingames} games and never entered the rivalry board at all.</figcaption>
    </figure>
  </div>

  <div class="note">
    <b>What this cannot tell you.</b> A volley is proximity, not address. In a fast group
    chat two managers can volley for an hour without once speaking to each other. The
    measure also cannot see a reply posted eleven minutes late, and it counts a joke
    exactly as heavily as a grievance. It is used here for ranking and for nothing else:
    no line of chat has ever been published on the strength of it.
  </div>

  <footer>
    Built by <b>scripts/build_referrals.py</b> from the league chat exports,
    {span0} to {span1}. The volley definition is the same code path as
    scripts/build_rivalries.py, so this page documents the ranking rather than
    describing a different measure. Only aggregate counts are written here &mdash;
    no message text &mdash; and the corpus itself is not in this repository and never
    will be.
  </footer>
</div>
<div id="tip" role="status" aria-live="polite"></div>
<script>
(function(){{
  var tip=document.getElementById('tip');
  function show(el,e){{
    tip.innerHTML='<b>'+el.dataset.t+'</b>'+el.dataset.v;
    tip.style.opacity='1';
    var r=el.getBoundingClientRect(),w=tip.offsetWidth,h=tip.offsetHeight;
    var x=(e&&e.clientX!=null?e.clientX:r.left+r.width/2)-w/2;
    var y=r.top-h-10;
    if(y<6){{y=r.bottom+10;}}
    tip.style.left=Math.max(8,Math.min(x,innerWidth-w-8))+'px';
    tip.style.top=y+'px';
  }}
  function hide(){{tip.style.opacity='0';}}
  document.querySelectorAll('.mx td.c').forEach(function(c){{
    c.addEventListener('mouseenter',function(e){{show(c,e);}});
    c.addEventListener('mousemove',function(e){{show(c,e);}});
    c.addEventListener('mouseleave',hide);
    c.addEventListener('focus',function(){{show(c,null);}});
    c.addEventListener('blur',hide);
    c.addEventListener('click',function(e){{show(c,e);}});
  }});
  document.addEventListener('scroll',hide,{{passive:true}});
}})();
</script>
</body></html>"""


if __name__ == '__main__':
    build()
