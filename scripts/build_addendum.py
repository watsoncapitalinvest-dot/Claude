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
import collections, datetime, html, json, math, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHATS = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('SCFL_CHATS',
    '/tmp/claude-0/-home-user-Claude/c302abf8-582a-5977-91c7-1dfbd915ffe3/scratchpad/chats')
OUT = os.path.join(ROOT, 'scfl-addendum.html')
OG = os.path.join(ROOT, 'scfl-addendum-og.jpg')
BROWSER = '/opt/pw-browsers/chromium'
ARTICLE_ID = 'kick-2026-addendum'
WINDOW = 420
MIN_GAMES = 8
# Heat is a ratio, so a pairing with twenty volleys can top the scale on two
# messages. Below this many volleys the cell is drawn as unmeasured, not cold.
MIN_HEAT_V = 150
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
                           'x': m.group(4), 'c': sub})
            elif ms:
                ms[-1]['x'] += ' ' + raw.strip()
    if not ms:
        sys.exit(f'no chat exports under {CHATS} -- nothing to count')
    for m in ms:
        m['ts'] = datetime.datetime.strptime(m['d'] + ' ' + re.sub(r'\s', '', m['t']),
                                             '%m/%d/%y %I:%M:%S%p')
    ms.sort(key=lambda m: m['ts'])
    _corpus = ms

    # Presence is not uniform: one manager can be in the league and out of the room.
    # Count each manager per chat so the figures can say who is still standing in it.
    rooms = {o: {c: [0, None] for c in ('mos', 'official')} for o in NAME}
    for m in ms:
        o = CHAT.get(m['who'])
        if not o:
            continue
        r = rooms[o][m['c']]
        r[0] += 1
        if r[1] is None or m['ts'].date() > r[1]:
            r[1] = m['ts'].date()
    end = ms[-1]['ts'].date()
    absent = sorted((o for o in NAME
                     if rooms[o]['mos'][1] and (end - rooms[o]['mos'][1]).days > 540
                     and rooms[o]['official'][0]),
                    key=lambda o: rooms[o]['mos'][1])

    volley, heated = collections.Counter(), collections.Counter()
    words, hotvol = collections.Counter(), 0
    for i in range(1, len(ms)):
        a, b = ms[i - 1], ms[i]
        oa, ob = CHAT.get(a['who']), CHAT.get(b['who'])
        if a['who'] == b['who'] or not oa or not ob or oa == ob:
            continue
        if not 0 <= (b['ts'] - a['ts']).total_seconds() <= WINDOW:
            continue
        k = tuple(sorted((oa, ob)))
        volley[k] += 1
        hit = {t.lower() for t in HEAT.findall(a['x']) + HEAT.findall(b['x'])}
        if hit:
            heated[k] += 1
            hotvol += 1
            for t in hit:            # a volley can trip more than one word
                words[t] += 1
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
                teams=teams, mg=mg, riv=riv, rank=rank, rooms=rooms, absent=absent, end=end,
                words=words, hotvol=hotvol)


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
.ad .dag{color:var(--red,#c20f16);font-weight:700;padding-left:2px;cursor:help;}
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
/* measured but under the floor: a texture, so it cannot be misread as "cold" */
.ad .mx td.thin,.ad .sw.thin{background:repeating-linear-gradient(45deg,#ded7ca 0 1.5px,
  #faf7f2 1.5px 4.5px);}
.ad .key .sw{display:inline-block;width:13px;height:13px;border-radius:2px;
  vertical-align:-2px;margin-right:5px;}
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
            if k == 'thin':      # measured, but on too little to colour honestly
                tds += f'<td class="thin" title="{re.sub("<[^>]+>", "", tip)}"></td>'; continue
            tds += (f'<td class="c" style="--k:{k:.3f}" tabindex="0" '
                    f'data-t="{esc(NAME[r])} &rarr; {esc(NAME[c])}" data-v="{tip}"></td>')
        rows += f'<tr><th scope="row" title="{esc(NAME[r])}">{ABBR[r]}</th>{tds}</tr>'
    return (f'<div class="scroll"><table class="mx" style="--hue:{hue}">'
            f'<thead><tr><td></td>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
            f'<div class="key"><span>{keylo}</span>'
            f'<span class="ramp" style="background:linear-gradient(90deg,#f4efe6,{hue})"></span>'
            f'<span>{keyhi}</span>{extra}</div>')


def shoot(doc, out, tag, w=1200, h=630):
    """Rasterise a share card. Shared with scripts/build_heat.py.

    deviceScaleFactor stays 1: at 2 this engine silently drops painted content,
    and a card that renders blank still writes a plausible-sized file, so the
    guard below counts pixels rather than bytes.
    """
    tmp = os.path.join(ROOT, f'.{tag}.html')
    open(tmp, 'w', encoding='utf-8').write(doc)
    raw = os.path.join(tempfile.gettempdir(), f'{tag}.png')
    js = os.path.join(tempfile.gettempdir(), f'{tag}.js')
    open(js, 'w').write(
        "const {chromium}=require('playwright');(async()=>{"
        f"const b=await chromium.launch({{executablePath:'{BROWSER}'}});"
        f"const p=await b.newPage({{viewport:{{width:{w},height:{h}}},deviceScaleFactor:1}});"
        f"await p.goto('file://{tmp}',{{waitUntil:'load'}});"
        "await p.evaluate(async()=>{await document.fonts.ready;"
        "document.body.getBoundingClientRect();"
        "await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));});"
        "await p.waitForTimeout(1200);"
        f"await p.screenshot({{path:'{raw}'}});await b.close();}})();")
    try:
        subprocess.run(['node', js], check=True, cwd=ROOT,
                       env=dict(os.environ, NODE_PATH='/opt/node22/lib/node_modules'),
                       capture_output=True)
        from PIL import Image
        im = Image.open(raw).convert('RGB')
        g = im.convert('L').resize((80, 42))
        blank = sum(1 for v in g.get_flattened_data() if v > 245) / (80 * 42)
        if blank > 0.55:
            sys.exit(f'  !! preview card is {blank:.0%} blank -- not shipping it')
        im.save(out, 'JPEG', quality=90, optimize=True, progressive=True)
        print(f'  card {os.path.basename(out)} {im.width}x{im.height} '
              f'{os.path.getsize(out)//1024}kb ({blank:.0%} blank)')
    finally:
        keep = os.environ.get('SCFL_KEEP_CARD')   # debugging the collage layout
        for f in (js, raw, tmp):
            if os.path.exists(f) and not keep:
                os.remove(f)


def heat_figures(D):
    """The heat matrix and the word list behind it, as two <figure> strings.

    Lives out here because scripts/build_heat.py publishes the same two figures
    as a standalone shareable, and the two must not be able to disagree.
    """
    P, vol = D['pairs'], sum(D['volley'].values())
    cell = {}
    for p in P:
        cell[(p['a'], p['b'])] = cell[(p['b'], p['a'])] = p
    solid = [p for p in P if p['v'] >= MIN_HEAT_V]
    hh = max(p['heat'] for p in solid)

    def heatcell(r, c):
        p = cell.get((r, c))
        if not p:
            return None
        if p['v'] < MIN_HEAT_V:
            return ('thin', f"only {p['v']:,} volleys &mdash; too few to rate")
        return (p['heat'] / hh,
                f"{p['heat']:.1f}% of {p['v']:,} volleys carry an argument word")

    grid = ('<figure>' + mxfig(D, heatcell, RED, 'Cooler', 'Hotter',
        f'<span style="margin-left:auto"><i class="sw thin"></i>Under {MIN_HEAT_V} volleys</span>') +
      f'<figcaption>Every pairing, coloured by the share of its volleys containing a '
      f'word from a fixed argument list. Heat is a ratio, so a thin pairing can top it on two '
      f'messages: under {MIN_HEAT_V} volleys, {len(P)-len(solid)} of the {len(P)} cells are '
      f'left uncoloured rather than flattered, and the ramp is set by the '
      f'{len(solid)} that survive &mdash; a real range of {min(p["heat"] for p in solid):.1f} to '
      f'{hh:.1f} per cent. Uncoloured is not cold; it is unmeasured. Heat is a ranking input and '
      f'nothing else: the desk has never published a line of chat on the strength of '
      f'it.</figcaption></figure>')

    W, hv = D['words'], D['hotvol']
    wmax = max(W.values())
    wrows = ''.join(
        f'<tr><th scope="row">{esc(w)}</th>'
        f'<td class="bar"><span style="width:{100*n/wmax:.1f}%"></span></td>'
        f'<td class="num">{n:,}</td>'
        f'<td class="num dim">{100*n/hv:.1f}%</td></tr>' for w, n in W.most_common())
    words = (f'<figure><div class="scroll"><table><thead><tr><th class="lt">The whole list, '
      f'{len(W)} words</th><th class="lt">Share of heated volleys</th><th>Volleys</th>'
      f'<th>Share</th></tr></thead><tbody>{wrows}</tbody></table></div>'
      f'<figcaption>There is no cleverness here and no sentiment model: a volley is heated if '
      f'either of its two messages contains one of these {len(W)} strings, whole-word and '
      f'case-insensitive. {hv:,} of {vol:,} volleys trip at least one, which is '
      f'{100*hv/vol:.1f} per cent of the record. The shares sum to {100*sum(W.values())/hv:.1f} '
      f'rather than a hundred because one volley can trip several words. '
      f'The obvious objection is that the list cannot tell an insult from a '
      f'quotation of one, and that &ldquo;joke&rdquo; and &ldquo;wrong&rdquo; carry a great deal of '
      f'ordinary traffic &mdash; which is the honest reason heat is worth a fraction of the rivalry '
      f'score and no headline of its own.</figcaption></figure>')
    return [grid, words]


def sections(D):
    """The addendum, once. Returns [(kind, html)] where kind is sect|body."""
    P, T, tot = D['pairs'], D['teams'], D['tot']
    cell = {}
    for p in P:
        cell[(p['a'], p['b'])] = cell[(p['b'], p['a'])] = p
    out = []
    S = lambda t: out.append(('sect', f'<div class="sect">{t}</div>'))
    B = lambda h: out.append(('body', f'<div class="ad">{h}</div>'))
    # a dagger follows anybody whose count is capped by absence, not by temperament
    DAG = '<span class="dag" title="No longer in the Mos Eisley chat">&dagger;</span>'
    AB = lambda t: ABBR[t] + (DAG if t in D['absent'] else '')
    NM = lambda t: esc(NAME[t]) + (DAG if t in D['absent'] else '')

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
    bars = ''.join(f'<tr><th scope="row">{NM(t)}</th>'
                   f'<td class="bar"><span style="width:{100*tot[t]/top:.1f}%"></span></td>'
                   f'<td class="num">{tot[t]:,}</td>'
                   f'<td class="num dim">{200*tot[t]/sum(tot.values()):.1f}%</td></tr>' for t in T)
    B(f'<figure><div class="scroll"><table><tbody>{bars}</tbody></table></div>'
      f'<figcaption>Volleys each franchise appears in. {esc(NAME[T[0]])} sits in {tot[T[0]]:,}; '
      f'{esc(NAME[T[-1]])} in {tot[T[-1]]:,} &mdash; a factor of {tot[T[0]]/tot[T[-1]]:.0f}. Rank on '
      f'raw volume and you would be ranking who types. A dagger marks a manager who is still in the '
      f'league but no longer in the chat; see the note below.</figcaption></figure>')

    S('A Note On Who Is In The Room')
    for who in D['absent']:
        mo, of = D['rooms'][who]['mos'], D['rooms'][who]['official']
        out.append(('body',
            f'<p class="b">One number on this page does not mean what the other fifteen mean. '
            f'{esc(NAME[who])} left the Mos Eisley chat on {mo[1]:%-d %B %Y} and has not posted in '
            f'it since. He did not leave the league. He is still in it, still drafting, and still in '
            f'the league chat, where his most recent message is dated {of[1]:%-d %B %Y}. The reasons '
            f'he walked out of the room were not fantasy football, and they are not this '
            f'desk&rsquo;s business.</p>'))
        out.append(('body',
            f'<p class="b">What is this desk&rsquo;s business is that every figure here counts the '
            f'room he stopped standing in. His {tot[who]:,} volleys are not a measure of how much he '
            f'talks; they are a measure of when he stopped. Read every {ABBR[who]} row as a floor, '
            f'and read his splits with more suspicion still &mdash; a small denominator makes any '
            f'pairing look like an obsession, which is exactly why he takes two of the top four rows '
            f'in Figure Three.</p>'))
        def ago(d):
            n = (D['end'] - d).days
            return ('current' if n < 60 else f'{n//30} months ago' if n < 730
                    else f'{n//365} years ago')
        rows = ''.join(
            f'<tr><th scope="row">{lbl}</th><td class="num">{n:,}</td>'
            f'<td class="num dim">{d:%-d %b %Y}</td>'
            f'<td class="num dim">{ago(d)}</td></tr>'
            for lbl, (n, d) in (('Mos Eisley &mdash; the banter chat', mo),
                                ('The league chat', of)) if d)
        B(f'<figure><div class="scroll"><table><thead><tr><th class="lt">'
          f'{esc(NAME[who])}</th><th>Messages</th><th>Last posted</th><th></th></tr></thead>'
          f'<tbody>{rows}</tbody></table></div>'
          f'<figcaption>Both chats are in this corpus and both are counted. Almost every volley in '
          f'the league happens in the first row&rsquo;s room &mdash; which is why a manager who is '
          f'fully present in the second row still reads on these charts as a man who went '
          f'quiet.</figcaption></figure>')

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
        rows += (f'<tr><th scope="row">{AB(hiS[0])} <span class="vs">and</span> {AB(loS[0])}</th>'
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
      'a fixture &mdash; precisely what the geometric mean exists to demote. Daggered rows are the '
      'other kind of wide gap: a manager out of the chat, whose few hundred remaining volleys all '
      'land on the same one or two names.</figcaption></figure>')

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
        f'<tr><th scope="row">{NM(t)}</th>'
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
    for h in heat_figures(D):
        B(h)

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
                f'<th scope="row">{AB(p["a"])} <span class="vs">v</span> {AB(p["b"])}</th>'
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
    out.append(('body', '<p class="b">Presence is not temperament. The measure assumes the sixteen '
        'are all standing in the same room, and one of them has not been for years. Where that is '
        'true the page says so with a dagger, but there is no correction that fixes it: you cannot '
        'infer the volleys a man would have thrown had he stayed.</p>'))
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
<meta property="og:image" content="https://watsoncapitalinvest-dot.github.io/Claude/scfl-addendum-og.jpg">
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
number for all sixteen managers, the eight figures behind it, and everything it cannot do.</p>
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


CARD = """<style>
:root{--red:#c20f16;--ink:#17181c;--muted:#65656b;--faint:#9a958c;--line:#e6e0d6;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;margin:0;}
html,body{width:1200px;height:630px;overflow:hidden;background:#efe9de;
 font-family:Georgia,'Times New Roman',serif;color:var(--ink);}
.card{position:relative;width:1200px;height:630px;overflow:hidden;
 border-top:9px solid var(--red);border-bottom:9px solid var(--red);background:#efe9de;}

/* the clippings, pinned to the desk */
.pc{position:absolute;background:#fffdfb;border:1px solid #ded7ca;padding:9px 11px;
 overflow:hidden;box-shadow:0 10px 26px rgba(0,0,0,.17),0 2px 5px rgba(0,0,0,.09);}
.pc .cap{font-family:var(--sans);font-size:7.5px;font-weight:800;letter-spacing:.15em;
 text-transform:uppercase;color:var(--red);margin-bottom:6px;}
.p1{left:446px;top:16px;width:278px;transform:rotate(-1.6deg);}      /* mutual   */
.p6{left:454px;top:316px;width:278px;transform:rotate(1.5deg);}      /* heat     */
.p4{left:742px;top:44px;width:372px;transform:rotate(1.3deg);}       /* board    */
.p5{left:752px;top:238px;width:356px;transform:rotate(-1.2deg);}     /* volleys  */
.p3{left:744px;top:428px;width:372px;transform:rotate(1.9deg);}      /* dumbbell */

table{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:8.5px;}
td,th{padding:2px 4px;}
tbody th{text-align:left;font-weight:700;white-space:nowrap;}
.num{text-align:right;font-variant-numeric:tabular-nums;}
.dim{color:var(--faint);}
tbody tr + tr th,tbody tr + tr td{border-top:1px solid #eee7db;}
.bar span{display:block;height:7px;background:var(--red);border-radius:0 2px 2px 0;min-width:2px;}
.bar{width:52%;}
.dumb{width:56%;position:relative;height:15px;}
.track{position:absolute;left:0;right:0;top:7px;height:2px;background:#e6e0d6;}
.seg{position:absolute;top:7px;height:2px;background:var(--ink);opacity:.3;}
.dot{position:absolute;top:3px;width:9px;height:9px;border-radius:50%;margin-left:-4.5px;
 border:2px solid #fffdfb;}
.dot.hi{background:var(--red);} .dot.lo{background:#0e8ab5;}
.mx{border-collapse:separate;border-spacing:1.5px;}
.mx td{width:14px;height:14px;padding:0;border-radius:2px;}
.mx td.c{background:color-mix(in oklab,var(--red) calc(var(--k)*100%),#f4efe6);}
.mx td.self{background:repeating-linear-gradient(135deg,#e9e2d6 0 3px,transparent 3px 6px);}
.mx td.none{background:#f6f2ea;}
.mx td.thin{background:repeating-linear-gradient(45deg,#ded7ca 0 1.5px,#faf7f2 1.5px 4.5px);}

/* the masthead panel sits over the collage */
.l{position:absolute;left:0;top:0;bottom:0;width:430px;z-index:9;
 padding:52px 34px 40px 52px;display:flex;flex-direction:column;
 background:linear-gradient(90deg,#efe9de 0%,#efe9de 74%,rgba(239,233,222,.94) 88%,
 rgba(239,233,222,0) 100%);}
.flag{font-family:var(--sans);font-size:11.5px;font-weight:900;letter-spacing:.22em;
 text-transform:uppercase;color:var(--red);}
h1{font-size:54px;line-height:.99;letter-spacing:-.025em;font-weight:900;margin-top:15px;}
h1 em{font-style:normal;color:var(--red);}
.rule{width:64px;height:3px;background:var(--red);margin:20px 0 18px;}
.dek{font-style:italic;color:#4b4b52;font-size:17px;line-height:1.4;max-width:23ch;}
.st{margin-top:auto;display:flex;gap:26px;}
.st .k{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.st .v{font-size:29px;font-weight:900;line-height:1.1;font-variant-numeric:tabular-nums;}
</style>
<div class="card">
 <div class="pc p1"><div class="cap">Fig. 2 &middot; Mutual attention</div>__MX__</div>
 <div class="pc p6"><div class="cap">Fig. 5 &middot; Where the arguments are</div>__HEAT__</div>
 <div class="pc p5"><div class="cap">Fig. 1 &middot; Volleys</div>__BARS__</div>
 <div class="pc p3"><div class="cap">Fig. 3 &middot; One-way streets</div>__DUMB__</div>
 <div class="pc p4"><div class="cap">The full board</div>__TBL__</div>
 <div class="l">
  <div class="flag">Transparent Research Addendum</div>
  <h1>How The<br>Rivalries<br>Were <em>Counted</em></h1>
  <div class="rule"></div>
  <div class="dek">Every ranking rests on one number. Here it is for all sixteen.</div>
  <div class="st">
   <div><div class="k">Volleys</div><div class="v">__VOL__</div></div>
   <div><div class="k">Pairings</div><div class="v">__PAIRS__</div></div>
   <div><div class="k">Figures</div><div class="v">8</div></div>
  </div>
 </div>
</div>"""


def card(D):
    """Preview image: a desk collage of the page's own figures, so the card is
    made of the evidence rather than decorated with something else."""
    P, T, tot = D['pairs'], D['teams'], D['tot']
    cell = {}
    for p in P:
        cell[(p['a'], p['b'])] = cell[(p['b'], p['a'])] = p
    hi = max(p['share'] for p in P)

    mx = ''
    for r in T:
        tds = ''
        for c in T:
            if r == c:
                tds += '<td class="self"></td>'
            elif (r, c) in cell:
                tds += f'<td class="c" style="--k:{cell[(r,c)]["share"]/hi:.3f}"></td>'
            else:
                tds += '<td class="none"></td>'
        mx += f'<tr>{tds}</tr>'
    mx = f'<table class="mx"><tbody>{mx}</tbody></table>'

    # Figure Five's grid, on the same floor the page uses: thin pairings are
    # textured, not coloured, so the card cannot flatter a twenty-volley cell.
    hh = max(p['heat'] for p in P if p['v'] >= MIN_HEAT_V)
    ht = ''
    for r in T:
        tds = ''
        for c in T:
            p = cell.get((r, c))
            if r == c:
                tds += '<td class="self"></td>'
            elif not p:
                tds += '<td class="none"></td>'
            elif p['v'] < MIN_HEAT_V:
                tds += '<td class="thin"></td>'
            else:
                tds += f'<td class="c" style="--k:{p["heat"]/hh:.3f}"></td>'
        ht += f'<tr>{tds}</tr>'
    ht = f'<table class="mx"><tbody>{ht}</tbody></table>'

    top = max(tot.values())
    bars = ''.join(f'<tr><th>{ABBR[t]}</th>'
                   f'<td class="bar"><span style="width:{100*tot[t]/top:.1f}%"></span></td>'
                   f'<td class="num dim">{tot[t]//1000}k</td></tr>' for t in T[:7])
    bars = f'<table><tbody>{bars}</tbody></table>'

    lop = sorted((p for p in P if p['v'] >= 300), key=lambda p: -abs(p['sa'] - p['sb']))[:5]
    dumb = ''
    for p in lop:
        h_, l_ = (p['a'], p['sa']), (p['b'], p['sb'])
        if l_[1] > h_[1]:
            h_, l_ = l_, h_
        s_ = .32
        dumb += (f'<tr><th>{ABBR[h_[0]]}<span class="dim"> / </span>{ABBR[l_[0]]}</th>'
                 f'<td class="dumb"><span class="track"></span>'
                 f'<span class="seg" style="left:{100*l_[1]/s_:.1f}%;right:{100-100*h_[1]/s_:.1f}%"></span>'
                 f'<span class="dot lo" style="left:{100*l_[1]/s_:.1f}%"></span>'
                 f'<span class="dot hi" style="left:{100*h_[1]/s_:.1f}%"></span></td>'
                 f'<td class="num">{h_[1]*100:.0f}<span class="dim">/</span>{l_[1]*100:.0f}</td></tr>')
    dumb = f'<table><tbody>{dumb}</tbody></table>'

    tbl = ''.join(
        f'<tr><th>{ABBR[p["a"]]}<span class="dim"> v </span>{ABBR[p["b"]]}</th>'
        f'<td class="num">{p["v"]:,}</td><td class="num"><b>{p["share"]*100:.1f}%</b></td>'
        f'<td class="num dim">{p["heat"]:.1f}%</td>'
        f'<td class="num dim">{p["g"]}</td></tr>' for p in P[:7])
    tbl = f'<table><tbody>{tbl}</tbody></table>'

    doc = (CARD.replace('__MX__', mx).replace('__HEAT__', ht).replace('__BARS__', bars)
               .replace('__DUMB__', dumb).replace('__TBL__', tbl)
               .replace('__VOL__', f"{sum(D['volley'].values()):,}")
               .replace('__PAIRS__', str(len(D['volley']))))
    shoot(doc, OG, 'ad-card')


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
                         'everything it cannot do.'),
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

    card(D)
    print(f'wrote {os.path.basename(OUT)} ({len(page):,} chars) and {ARTICLE_ID} '
          f'({len(blocks)} blocks) from one build')
    print(f'  {D["ms"]:,} messages | {sum(D["volley"].values()):,} volleys | '
          f'{sum(D["ment"].values()):,} mentions | text check clean')


if __name__ == '__main__':
    build()
