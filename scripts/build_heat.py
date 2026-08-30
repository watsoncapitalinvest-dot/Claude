#!/usr/bin/env python3
"""Where The Arguments Are -- the heat grid and its word list, on their own page.

    python3 scripts/build_heat.py [path/to/chats]

The same two figures already sit inside the Transparent Research Addendum, but
that page is long and lives at the back of an issue, so nobody scrolling a chat
will ever find them. This publishes them as one short shareable with its own
preview card.

Both figures come from build_addendum.heat_figures(), so this page and the
addendum cannot disagree about a single number. Aggregates only: the build
checks the finished page against every message in the corpus and refuses to
write if any run of thirty characters survives into it.
"""
import importlib.util, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts',
                                                               'build_addendum.py'))
ad = importlib.util.module_from_spec(_s)
sys.modules['ad'] = ad
_s.loader.exec_module(ad)

OUT = os.path.join(ROOT, 'scfl-heat.html')
OG = os.path.join(ROOT, 'scfl-heat-og.jpg')

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Where The Arguments Are — SCFL NewsRoom</title>
<meta name="scfl:kicker" content="The Record Room · Aug 2026">
<meta name="scfl:published" content="2026-08-22">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SCFL NewsRoom">
<meta property="og:title" content="Where The Arguments Are">
<meta property="og:description" content="__DESC__">
<meta property="og:image" content="https://watsoncapitalinvest-dot.github.io/Claude/scfl-heat-og.jpg">
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
</style></head>
<body><div class="wrap">
<div class="runhead">SCFL NewsRoom &middot; The Record Room &middot; August 2026</div>
<span class="flag">The Record Room</span>
<h1>Where The <em>Arguments</em> Are</h1>
<p class="dek">Sixteen managers, a hundred and twenty pairings, and a very dumb list of
twenty-four words. This is the whole of it.</p>
<div class="rule"></div>
__BODY__
<div class="more">Both figures are lifted straight out of the
<a href="scfl-addendum.html">Transparent Research Addendum</a>, which shows the other seven and
everything none of them can tell you. That runs inside the
<a href="scfl-kickoff-2026.html">2026 Kickoff Issue</a>.</div>
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
.p2{left:848px;top:150px;width:306px;transform:rotate(1.7deg);}

.mx{border-collapse:separate;border-spacing:1.5px;}
.mx td{width:23px;height:23px;padding:0;border-radius:2px;}
.mx td.c{background:color-mix(in oklab,var(--red) calc(var(--k)*100%),#f4efe6);}
.mx td.self{background:repeating-linear-gradient(135deg,#e9e2d6 0 3px,transparent 3px 6px);}
.mx td.none{background:#f6f2ea;}
.mx td.thin{background:repeating-linear-gradient(45deg,#ded7ca 0 1.5px,#faf7f2 1.5px 4.5px);}

table.w{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:9.5px;}
table.w td,table.w th{padding:2.5px 4px;vertical-align:middle;}
table.w tbody th{text-align:left;font-weight:700;white-space:nowrap;}
table.w tbody tr + tr th,table.w tbody tr + tr td{border-top:1px solid #eee7db;}
.bar span{display:block;height:8px;background:var(--red);border-radius:0 2px 2px 0;min-width:2px;}
.bar{width:50%;}
.num{text-align:right;font-variant-numeric:tabular-nums;color:var(--faint);}

.l{position:absolute;left:0;top:0;bottom:0;width:420px;z-index:9;
 padding:56px 30px 44px 52px;display:flex;flex-direction:column;
 background:linear-gradient(90deg,#efe9de 0%,#efe9de 72%,rgba(239,233,222,.94) 87%,
 rgba(239,233,222,0) 100%);}
.flag{font-family:var(--sans);font-size:11.5px;font-weight:900;letter-spacing:.22em;
 text-transform:uppercase;color:var(--red);}
h1{font-size:60px;line-height:.97;letter-spacing:-.028em;font-weight:900;margin-top:16px;}
h1 em{font-style:normal;color:var(--red);}
.rule{width:64px;height:3px;background:var(--red);margin:22px 0 18px;}
.dek{font-style:italic;color:#4b4b52;font-size:17px;line-height:1.4;max-width:22ch;}
.st{margin-top:auto;display:flex;gap:28px;}
.st .k{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:var(--faint);}
.st .v{font-size:30px;font-weight:900;line-height:1.1;font-variant-numeric:tabular-nums;}
</style>
<div class="card">
 <div class="pc p1"><div class="cap">Every pairing &middot; hotter is redder</div>__HEAT__</div>
 <div class="pc p2"><div class="cap">The list, top twelve</div>__WORDS__</div>
 <div class="l">
  <div class="flag">The Record Room</div>
  <h1>Where The<br><em>Arguments</em><br>Are</h1>
  <div class="rule"></div>
  <div class="dek">A hundred and twenty pairings and twenty-four very dumb words.</div>
  <div class="st">
   <div><div class="k">Words</div><div class="v">__NW__</div></div>
   <div><div class="k">Heated</div><div class="v">__HOT__</div></div>
   <div><div class="k">Of all volleys</div><div class="v">__PCT__</div></div>
  </div>
 </div>
</div>"""


def card(D):
    """Card = the grid at full size plus the top of the list. Same floor as the page."""
    T, P = D['teams'], D['pairs']
    cell = {}
    for p in P:
        cell[(p['a'], p['b'])] = cell[(p['b'], p['a'])] = p
    ht = ''
    for r in T:
        tds = ''
        for c in T:
            p = cell.get((r, c))
            if r == c:
                tds += '<td class="self"></td>'
            elif not p:
                tds += '<td class="none"></td>'
            elif p['v'] < ad.MIN_HEAT_V:
                tds += '<td class="thin"></td>'
            else:
                tds += f'<td class="c" style="--k:{ad.heat_k(p["heat"]):.3f}"></td>'
        ht += f'<tr>{tds}</tr>'
    ht = f'<table class="mx"><tbody>{ht}</tbody></table>'

    W, hv = D['words'], D['hotvol']
    top = W.most_common(12)
    wmax = top[0][1]
    rows = ''.join(f'<tr><th>{ad.esc(w)}</th>'
                   f'<td class="bar"><span style="width:{100*n/wmax:.1f}%"></span></td>'
                   f'<td class="num">{n:,}</td></tr>' for w, n in top)
    words = f'<table class="w"><tbody>{rows}</tbody></table>'

    vol = sum(D['volley'].values())
    doc = (CARD.replace('__HEAT__', ht).replace('__WORDS__', words)
               .replace('__NW__', str(len(W))).replace('__HOT__', f'{hv:,}')
               .replace('__PCT__', f'{100*hv/vol:.1f}%'))
    ad.shoot(doc, OG, 'heat-card')


def build():
    D = ad.compute()
    vol = sum(D['volley'].values())
    hv, W = D['hotvol'], D['words']
    grid, words = ad.heat_figures(D)

    intro = (
        f'<p class="b">A volley is two managers speaking back to back: one posts, a different one '
        f'answers inside {ad.WINDOW//60} minutes. There are {vol:,} of them in the league record. '
        f'A volley is <em>heated</em> if either of its two messages contains one of twenty-four '
        f'strings on a fixed list &mdash; no sentiment model, no cleverness, no judgement about '
        f'who started it.</p>',
        f'<p class="b">{hv:,} volleys trip the list, which is {100*hv/vol:.1f} per cent of '
        f'everything ever said. Below is where they sit, and then the list itself, so you can '
        f'argue with the list instead of with the chart.</p>')

    body = '\n'.join(list(intro) + [f'<div class="ad">{grid}</div>',
                                    '<div class="sect">The List</div>',
                                    f'<div class="ad">{words}</div>'])
    desc = (f'{hv:,} of {vol:,} volleys carry an argument word. Here is every pairing, and the '
            f'{len(W)}-word list that decides it.')
    page = (PAGE.replace('__FIGCSS__', ad.FIG_CSS).replace('__BODY__', body)
                .replace('__DESC__', desc))

    flat = re.sub(r'\s+', ' ', page)
    leaked = [t for t in (re.sub(r'\s+', ' ', m['x']).strip() for m in ad._corpus)
              if len(t) >= 30 and t in flat]
    if leaked:
        sys.exit(f'chat text leaked into the page: {leaked[:2]}')
    open(OUT, 'w', encoding='utf-8').write(page)

    card(D)
    print(f'wrote {os.path.basename(OUT)} ({len(page):,} chars)')
    print(f'  {len(W)} words | {hv:,} heated of {vol:,} volleys ({100*hv/vol:.1f}%) | '
          f'text check clean')


if __name__ == '__main__':
    build()
