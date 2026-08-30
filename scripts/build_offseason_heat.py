#!/usr/bin/env python3
"""The Offseason Heat Map -- Bosom Bowl 21 to Kickoff, on its own page.

    python3 scripts/build_offseason_heat.py [path/to/chats]

Same volley/heat measure as the all-time Heat Index, sliced to one window:
the day after the 2025 championship (Bosom Bowl 21, won by Powers of Pain,
concluded the night of Dec 29) through the most recent message in the corpus.
That start date is read straight out of the chat record, not guessed --
see OFFSEASON_START below.

Reuses build_addendum's message load and owner mapping so this can't disagree
with the Heat Index or the weekly index about what counts as a volley or a
hit. The 150-volley floor the all-time grid uses to call a cell "measured" is
calibrated for a decade of data; an 8-month window needs its own, smaller
floor -- OFFSEASON_MIN_V below, chosen from this window's own volley-count
spread so a cell still means something when it lights up.

Aggregate only, same guard as every other page built from the chat corpus:
the build checks the rendered page against every message in the full corpus
(not just the window) and refuses to write if any run of thirty characters
survives into it.
"""
import collections, datetime, importlib.util, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts', 'build_addendum.py'))
ad = importlib.util.module_from_spec(_spec)
sys.modules['ad'] = ad
_spec.loader.exec_module(ad)

OUT = os.path.join(ROOT, 'scfl-offseason-heat.html')
OG = os.path.join(ROOT, 'scfl-offseason-heat-og.jpg')
# The night Bosom Bowl 21 wrapped -- Powers Of Pain's 5th title, confirmed in
# the chat record (congratulations posted the night of 12/29/25). The window
# starts the next morning.
OFFSEASON_START = datetime.date(2025, 12, 30)
OFFSEASON_MIN_V = 30   # see module docstring


def week_start(d):
    return d - datetime.timedelta(days=d.weekday())


def compute_window():
    ad.compute()
    ms = [m for m in ad._corpus if m['ts'].date() >= OFFSEASON_START]
    if not ms:
        sys.exit('no messages on or after the offseason start date -- nothing to build')

    volley, heated, words = collections.Counter(), collections.Counter(), collections.Counter()
    person = collections.Counter()
    hotvol = 0
    volley_wk = collections.defaultdict(collections.Counter)
    heated_wk = collections.defaultdict(collections.Counter)
    for i in range(1, len(ms)):
        a, b = ms[i - 1], ms[i]
        oa, ob = ad.CHAT.get(a['who']), ad.CHAT.get(b['who'])
        if a['who'] == b['who'] or not oa or not ob or oa == ob:
            continue
        if a['c'] != b['c']:
            continue  # different rooms: not the same conversation, just adjacent in time
        if not 0 <= (b['ts'] - a['ts']).total_seconds() <= ad.WINDOW:
            continue
        k = tuple(sorted((oa, ob)))
        volley[k] += 1
        w = week_start(b['ts'].date())
        volley_wk[w][k] += 1
        hit = {t.lower() for t in ad.HEAT.findall(a['x']) + ad.HEAT.findall(b['x'])}
        if hit:
            heated[k] += 1; hotvol += 1; person[oa] += 1; person[ob] += 1
            heated_wk[w][k] += 1
            for t in hit:
                words[t] += 1

    pairs = [{'a': a, 'b': b, 'v': v, 'heat': 100 * heated[(a, b)] / v}
             for (a, b), v in volley.items()]
    # teams for the grid: every franchise the site knows about, ordered by
    # offseason volley volume so the busiest talkers sit up top.
    tot = collections.Counter()
    for (a, b), v in volley.items():
        tot[a] += v; tot[b] += v
    teams = sorted(ad.NAME, key=lambda k: -tot[k])

    weeks = sorted(volley_wk)
    week_rows = []
    for w in weeks:
        tv, th = sum(volley_wk[w].values()), sum(heated_wk[w].values())
        top = max(heated_wk[w], key=lambda k: heated_wk[w][k]) if heated_wk[w] else None
        week_rows.append({'w': w, 'v': tv, 'h': th,
                           'pair': (ad.NAME[top[0]], ad.NAME[top[1]]) if top else None})

    return dict(ms=ms, volley=volley, heated=heated, words=words, hotvol=hotvol,
                person=person, pairs=pairs, teams=teams, week_rows=week_rows,
                span=(ms[0]['ts'].date(), ms[-1]['ts'].date()))


# ------------------------------------------------------------------- page --
FIG_CSS_EXTRA = """
.lead{display:flex;justify-content:space-between;gap:10px;padding:8px 0;
 border-bottom:1px solid var(--line);font-family:var(--sans);font-size:13px;}
.lead .who{font-weight:700;} .lead .n{color:var(--faint);font-variant-numeric:tabular-nums;}
.wk{display:flex;align-items:baseline;gap:10px;padding:9px 0;border-bottom:1px solid var(--line);}
.wk .rank{font-family:var(--sans);font-weight:900;font-size:15px;color:var(--faint);min-width:20px;}
.wk .d{font-family:var(--sans);font-weight:800;font-size:12.5px;min-width:98px;}
.wk .p{flex:1;font-size:14px;} .wk .h{font-family:var(--sans);font-weight:900;font-size:16px;color:var(--red);}
"""

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>The Offseason Heat Map — SCFL NewsRoom</title>
<meta name="scfl:kicker" content="The Record Room · Aug 2026">
<meta name="scfl:published" content="2026-08-30">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SCFL NewsRoom">
<meta property="og:title" content="The Offseason Heat Map">
<meta property="og:description" content="__DESC__">
<meta property="og:image" content="https://watsoncapitalinvest-dot.github.io/Claude/scfl-offseason-heat-og.jpg">
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
.wrap{max-width:820px;margin:0 auto;padding:0 20px 80px;}
.runhead{font-family:var(--sans);font-size:10.5px;font-weight:800;letter-spacing:.22em;
 text-transform:uppercase;color:var(--faint);border-bottom:1px solid var(--line);padding:20px 0 12px;}
.flag{font-family:var(--sans);font-size:10.5px;font-weight:900;letter-spacing:.24em;
 text-transform:uppercase;color:var(--red);margin-top:26px;display:block;}
h1{font-weight:900;font-size:clamp(34px,7vw,54px);line-height:1.02;letter-spacing:-.022em;
 margin:12px 0 0;text-wrap:balance;}
h1 em{font-style:normal;color:var(--red);}
.dek{font-style:italic;color:var(--muted);font-size:18px;margin:14px 0 0;max-width:60ch;}
.rule{height:3px;background:var(--red);width:70px;margin:22px 0 26px;}
.sect{font-family:var(--sans);font-size:11px;font-weight:900;letter-spacing:.2em;
 text-transform:uppercase;color:var(--red);margin:44px 0 12px;padding-top:14px;
 border-top:1px solid var(--line);}
p.b{margin:0 0 16px;max-width:62ch;}
.stats{display:flex;flex-wrap:wrap;gap:26px 40px;margin:0 0 30px;padding-bottom:22px;
 border-bottom:1px solid var(--line);}
.stat .k{font-family:var(--sans);font-size:9.5px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.stat .v{font-size:30px;font-weight:900;line-height:1.15;font-variant-numeric:tabular-nums;}
.stat .n{font-family:var(--sans);font-size:11px;color:var(--muted);}
.more{margin-top:46px;border-top:1px solid var(--line);padding-top:18px;font-family:var(--sans);
 font-size:13px;line-height:1.6;color:var(--muted);max-width:70ch;}
.more a{color:var(--red);font-weight:700;}
#tip{position:fixed;z-index:80;pointer-events:none;opacity:0;transition:opacity .12s;
 background:var(--ink);color:var(--cream);font-family:var(--sans);font-size:11.5px;line-height:1.45;
 padding:7px 10px;border-radius:4px;max-width:250px;box-shadow:0 6px 22px rgba(0,0,0,.28);}
#tip b{display:block;color:#fff;}
@media (prefers-reduced-motion:reduce){*{transition:none!important;}}
__FIGCSS__
__EXTRACSS__
</style></head>
<body><div class="wrap">
<div class="runhead">SCFL NewsRoom &middot; The Record Room &middot; August 2026</div>
<span class="flag">The Record Room</span>
<h1>The Offseason <em>Heat Map</em></h1>
<p class="dek">Bosom Bowl 21 to Kickoff. Eight months, no games, and the chat never once cooled off.</p>
<div class="rule"></div>
__BODY__
<div class="more">Built the same way as <a href="scfl-heat.html">Where The Arguments Are</a> and the
<a href="scfl-addendum.html">Transparent Research Addendum</a> &mdash; same volley window, same fixed
word list, aggregate only. This slice just starts the clock at the final whistle of the last
championship instead of at the start of the chat record.</div>
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
:root{--red:#c20f16;--ink:#17181c;--faint:#9a958c;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;margin:0;}
html,body{width:1200px;height:630px;overflow:hidden;background:#efe9de;
 font-family:Georgia,'Times New Roman',serif;color:var(--ink);}
.card{position:relative;width:1200px;height:630px;overflow:hidden;background:#efe9de;
 border-top:9px solid var(--red);border-bottom:9px solid var(--red);}
.pc{position:absolute;background:#fffdfb;border:1px solid #ded7ca;padding:11px 13px;
 overflow:hidden;box-shadow:0 10px 26px rgba(0,0,0,.17),0 2px 5px rgba(0,0,0,.09);}
.pc .cap{font-family:var(--sans);font-size:8px;font-weight:800;letter-spacing:.15em;
 text-transform:uppercase;color:var(--red);margin-bottom:8px;}
.p1{left:432px;top:88px;width:424px;transform:rotate(-1.5deg);}
.mx{border-collapse:separate;border-spacing:1.5px;}
.mx td{width:23px;height:23px;padding:0;border-radius:2px;}
.mx td.c{background:color-mix(in oklab,var(--red) calc(var(--k)*100%),#f4efe6);}
.mx td.self{background:repeating-linear-gradient(135deg,#e9e2d6 0 3px,transparent 3px 6px);}
.mx td.none{background:#f6f2ea;}
.mx td.thin{background:repeating-linear-gradient(45deg,#ded7ca 0 1.5px,#faf7f2 1.5px 4.5px);}
.l{position:absolute;left:0;top:0;bottom:0;width:420px;z-index:9;
 padding:56px 30px 44px 52px;display:flex;flex-direction:column;
 background:linear-gradient(90deg,#efe9de 0%,#efe9de 72%,rgba(239,233,222,.94) 87%,
 rgba(239,233,222,0) 100%);}
.flag{font-family:var(--sans);font-size:11.5px;font-weight:900;letter-spacing:.22em;
 text-transform:uppercase;color:var(--red);}
h1{font-size:54px;line-height:.97;letter-spacing:-.028em;font-weight:900;margin-top:16px;}
h1 em{font-style:normal;color:var(--red);}
.rule{width:64px;height:3px;background:var(--red);margin:22px 0 18px;}
.dek{font-style:italic;color:#4b4b52;font-size:16px;line-height:1.4;max-width:23ch;}
.st{margin-top:auto;display:flex;gap:26px;}
.st .k{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.st .v{font-size:28px;font-weight:900;line-height:1.1;font-variant-numeric:tabular-nums;}
</style>
<div class="card">
 <div class="pc p1"><div class="cap">Every pairing since Bosom Bowl 21 &middot; hotter is redder</div>__HEAT__</div>
 <div class="l">
  <div class="flag">The Record Room</div>
  <h1>The<br>Offseason<br><em>Heat Map</em></h1>
  <div class="rule"></div>
  <div class="dek">Bosom Bowl 21 to Kickoff &mdash; the chat never cooled off.</div>
  <div class="st">
   <div><div class="k">Volleys</div><div class="v">__VOL__</div></div>
   <div><div class="k">Heated</div><div class="v">__HOT__</div></div>
   <div><div class="k">Rate</div><div class="v">__PCT__</div></div>
  </div>
 </div>
</div>"""


def grid_figure(D, label='full'):
    P = D['pairs']
    cell = {}
    for p in P:
        cell[(p['a'], p['b'])] = cell[(p['b'], p['a'])] = p
    solid = [p for p in P if p['v'] >= OFFSEASON_MIN_V]
    hh = max((p['heat'] for p in solid), default=1)

    def heatcell(r, c):
        p = cell.get((r, c))
        if not p:
            return None
        if p['v'] < OFFSEASON_MIN_V:
            return ('thin', f"only {p['v']:,} volleys this offseason &mdash; too few to rate")
        return (ad.heat_k(p['heat']), f"{p['heat']:.1f}% of {p['v']:,} volleys carry an argument word")

    return ('<figure>' + ad.mxfig(D, heatcell, ad.RED, 'Cooler', 'Hotter',
        f'<span style="margin-left:auto"><i class="sw thin"></i>Under {OFFSEASON_MIN_V} volleys</span>',
        label=label) +
      f'<figcaption>Every pairing, Bosom Bowl 21 to now, coloured by the share of its volleys '
      f'carrying an argument word. Eight months is a fraction of the sample the all-time grid runs '
      f'on, so the measured floor drops from 150 volleys to {OFFSEASON_MIN_V}: {len(P)-len(solid)} of '
      f'the {len(P)} recorded pairings still fall under it and stay uncoloured rather than '
      f'flattered. Colour is a straight, fixed proportion of the percentage &mdash; 0 to '
      f'{ad.HEAT_COLOR_CEILING:.0f}%, the same ceiling the all-time grid uses, so a shade means the '
      f'same number on both pages &mdash; and the exact percentage is always on the cell\'s hover or '
      f'tap.</figcaption></figure>')


def card(D):
    # abbreviated labels here, not full names: the share-card panel is a fixed
    # 424px and can't fit sixteen rotated franchise names at readable size.
    ht = grid_figure(D, label='abbr')
    # card wants the raw <table>+key markup only, not the <figure> wrapper/caption
    ht = re.sub(r'^<figure>|<figcaption>.*$', '', ht, flags=re.S)
    vol = sum(D['volley'].values())
    doc = (CARD.replace('__HEAT__', ht).replace('__VOL__', f'{vol:,}')
               .replace('__HOT__', f'{D["hotvol"]:,}').replace('__PCT__', f'{100*D["hotvol"]/vol:.1f}%'))
    ad.shoot(doc, OG, 'offseason-heat-card')


def build():
    D = compute_window()
    vol = sum(D['volley'].values())
    hv = D['hotvol']
    grid = grid_figure(D)

    top_words = D['words'].most_common(8)
    word_line = ', '.join(f'&ldquo;{ad.esc(w)}&rdquo; ({n})' for w, n in top_words[:5])

    leaders = D['person'].most_common(6)
    lead_html = ''.join(f'<div class="lead"><span class="who">{ad.esc(ad.NAME[o])}</span>'
                        f'<span class="n">{n} heated exchange{"s" if n != 1 else ""}</span></div>'
                        for o, n in leaders)

    weeks_by_heat = sorted(D['week_rows'], key=lambda w: -w['h'])[:5]
    week_html = ''
    for i, w in enumerate(weeks_by_heat, 1):
        end = w['w'] + datetime.timedelta(days=6)
        pair = f'{ad.esc(w["pair"][0])} <span style="color:var(--faint)">vs</span> {ad.esc(w["pair"][1])}' if w['pair'] else 'no clear pairing'
        week_html += (f'<div class="wk"><span class="rank">{i}</span>'
                      f'<span class="d">{w["w"]:%b %-d}&ndash;{end:%-d}</span>'
                      f'<span class="p">{pair}</span><span class="h">{w["h"]}</span></div>')

    # the two facts the article leans on: the champ's near-silence, and the
    # single hottest pairing by raw heated count (not just by rate)
    pop = 'Maristmidi'
    pop_heat = sum(n for (a, b), n in D['heated'].items() if pop in (a, b))
    top_pair_by_heat = max(D['pairs'], key=lambda p: D['heated'].get((p['a'], p['b']), 0))
    tph_a, tph_b = ad.NAME[top_pair_by_heat['a']], ad.NAME[top_pair_by_heat['b']]
    tph_n = D['heated'][(top_pair_by_heat['a'], top_pair_by_heat['b'])]

    hottest = weeks_by_heat[0]
    hottest_end = hottest['w'] + datetime.timedelta(days=6)
    second = weeks_by_heat[1] if len(weeks_by_heat) > 1 else None

    article = (
        f'<p class="b">Eight months between championships and the heat rate barely moved: '
        f'{100*hv/vol:.1f} per cent of offseason volleys carried an argument word, against '
        f'3.67 per cent across the entire five-year chat record. The offseason is not the calm '
        f'season. It just argues about different things &mdash; waivers, schedules, whether the '
        f'league is old enough to matter &mdash; instead of a missed start or a bad beat.</p>'
        f'<p class="b">The single hottest week of the whole window was '
        f'{hottest["w"]:%B %-d}&ndash;{hottest_end:%-d}, and it is not a coincidence: that is the week '
        f'this desk published the Heat Index, the Addendum, and the Gumbas file. The league spent a '
        f'night arguing about being measured, which produced more heat than most weeks produce '
        f'arguing about football. Being told who argues the most made everybody argue about it.</p>'
        + (f'<p class="b">The week that says more is the second-hottest one, '
           f'{second["w"]:%B %-d}&ndash;{(second["w"]+datetime.timedelta(days=6)):%-d} &mdash; five '
           f'months before any of that existed. A sustained, multi-hour exchange, openly called '
           f'&ldquo;an altercation&rdquo; by one of the managers watching it happen, pulled in half '
           f'the league. The record was going to have a hot week regardless of whether anyone was '
           f'keeping score.</p>' if second else '')
        + f'<p class="b">By raw heated exchanges, no pairing ran hotter than '
        f'{tph_a} and {tph_b}, with {tph_n} over the window. Meanwhile the reigning, five-time '
        f'champion managed exactly {pop_heat} heated exchanges in eight months &mdash; the quietest '
        f'record of anyone who showed up regularly. Winning, it turns out, is a pretty effective way '
        f'to stay out of an argument.</p>'
    )

    desc = (f'{hv:,} of {vol:,} volleys since Bosom Bowl 21 carried an argument word '
            f'({100*hv/vol:.1f}% &mdash; almost identical to the all-time rate). Who ran hottest, '
            f'and why.')

    body = '\n'.join([
        f'''<div class="stats">
          <div class="stat"><div class="k">Messages read</div><div class="v">{len(D['ms']):,}</div>
            <div class="n">{D['span'][0]:%b %-d} &ndash; {D['span'][1]:%b %-d, %Y}</div></div>
          <div class="stat"><div class="k">Volleys</div><div class="v">{vol:,}</div>
            <div class="n">{len(D['volley'])} pairings</div></div>
          <div class="stat"><div class="k">Heated</div><div class="v">{hv:,}</div>
            <div class="n">{100*hv/vol:.1f}% of volleys</div></div>
          <div class="stat"><div class="k">Weeks tracked</div><div class="v">{len(D['week_rows'])}</div>
            <div class="n">since Bosom Bowl 21</div></div>
        </div>''',
        f'<div class="ad">{grid}</div>',
        '<div class="sect">The Five Hottest Weeks</div>',
        week_html,
        '<div class="sect">Who Ran Hottest</div>',
        f'<p class="b">Ranked by heated exchanges, either side. The most-used words this offseason: '
        f'{word_line}.</p>',
        lead_html,
        '<div class="sect">What It Means</div>',
        article,
    ])

    page = (PAGE.replace('__FIGCSS__', ad.FIG_CSS).replace('__EXTRACSS__', FIG_CSS_EXTRA)
                .replace('__BODY__', body).replace('__DESC__', desc))

    flat = re.sub(r'\s+', ' ', page)
    leaked = [t for t in (re.sub(r'\s+', ' ', m['x']).strip() for m in ad._corpus)
              if len(t) >= 30 and t in flat]
    if leaked:
        sys.exit(f'chat text leaked into the page: {leaked[:2]}')
    open(OUT, 'w', encoding='utf-8').write(page)

    card(D)
    print(f'wrote {os.path.basename(OUT)} ({len(page):,} chars)')
    print(f'  window {D["span"][0]}..{D["span"][1]} | {vol:,} volleys | {hv:,} heated '
          f'({100*hv/vol:.1f}%) | text check clean')


if __name__ == '__main__':
    build()
