#!/usr/bin/env python3
"""Assemble a multi-article SCFL magazine issue as one flip book.

    python3 scripts/build_issue.py kickoff-2026

Takes a list of articles from investigations.json, wraps them in a cover and a
contents page, and lays the whole thing out with the same house CSS and page
engine as the single-article pages. Pagination is measured, not guessed -- run
scripts/measure_pages.js against the built file and rebuild.

Covers come from John's graphics AI, never from code. If the cover file named in
the issue definition is missing, the build says so and uses a typographic
stand-in so the issue is still readable.
"""
import json, os, re, sys

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE=os.path.join(ROOT,'scfl-politics-wire-freeze-flip.html')
SITE='https://watsoncapitalinvest-dot.github.io/Claude/'

ISSUES={
 'kickoff-2026': {
   'out':'scfl-kickoff-2026.html',
   'title':'The 2026 Kickoff Issue',
   'mast':('Skirt ','Chasers'),
   'tagline':'The 2026&ndash;27 Season Kickoff Issue',
   'dateline':'August 2026',
   'runhead':'Skirt Chasers &middot; The Kickoff Issue &middot; August 2026',
   'art':'scfl-kickoff-cover.jpg',
   'og':'scfl-kickoff-og.jpg',
   'ogtitle':'Skirt Chasers — The 2026 Kickoff Issue',
   'ogdesc':("A 7-7 champion, a name change decided by 207 points, the division that holds the three "
             "best offences in the league, and all sixteen teams previewed."),
   'sharetext':'The 2026-27 SCFL season starts here.',
   'kicker':'The Magazine · Aug 2026',
   'articles':['kick-2026-champion','kick-2026-namechange','kick-2026-blackandblue',
               'kick-2026-preview','the-grudge-report','the-hill-standoff'],
 },
}

EXTRA_CSS="""
.issue-cover{position:absolute;inset:0;background:#0a0806;display:flex;flex-direction:column;padding:0;}
.issue-cover img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;}
/* Scrim so the masthead and the headline read over whatever the art does at the
   top and bottom edges. object-fit:cover re-crops per viewport, so the bands
   cannot be relied on to stay dark on their own. */
.issue-cover.has-art::after{content:'';position:absolute;inset:0;z-index:1;pointer-events:none;
  background:linear-gradient(180deg,rgba(6,5,4,.78) 0%,rgba(6,5,4,.34) 15%,rgba(6,5,4,0) 30%,
  rgba(6,5,4,0) 58%,rgba(6,5,4,.42) 78%,rgba(6,5,4,.88) 100%);}
.ic-top{position:relative;z-index:2;text-align:center;padding:26px 22px 0;}
.ic-mast{font-family:var(--serif);font-weight:900;font-size:46px;line-height:.95;color:#f7f3ec;
  text-shadow:0 2px 16px rgba(0,0,0,.9);}
.ic-mast span{color:#e8393e;}
.ic-tag{font-family:var(--sans);font-size:10.5px;font-weight:900;letter-spacing:.26em;
  text-transform:uppercase;color:#e0d9cd;margin-top:10px;text-shadow:0 1px 8px rgba(0,0,0,.9);}
.ic-bot{position:absolute;z-index:2;left:0;right:0;bottom:74px;padding:0 24px;text-align:center;}
.ic-line{font-family:var(--serif);font-size:15px;line-height:1.5;color:#e8e2d8;
  text-shadow:0 1px 10px rgba(0,0,0,.95);}
.ic-fallback{position:absolute;inset:0;background:#fffdfb;}
.toc{list-style:none;padding:0;margin:6px 0 0;}
.toc li{display:flex;gap:10px;align-items:baseline;padding:10px 0;border-bottom:1px solid var(--line);}
.toc .n{font-family:var(--sans);font-size:11px;font-weight:900;color:var(--red);min-width:22px;}
.toc .t{flex:1;font-weight:800;font-size:14px;line-height:1.3;}
.toc .k{font-family:var(--sans);font-size:10px;font-weight:800;letter-spacing:.1em;
  text-transform:uppercase;color:var(--faint);display:block;margin-top:3px;}
.divider{text-align:center;padding:26px 0 8px;}
.divider .d-flag{font-family:var(--sans);font-size:10.5px;font-weight:900;letter-spacing:.24em;
  text-transform:uppercase;color:var(--red);}
.divider .d-h{font-family:var(--serif);font-weight:900;font-size:27px;line-height:1.15;margin-top:10px;}
.divider .d-s{font-family:var(--serif);font-style:italic;font-size:15px;line-height:1.5;
  color:var(--muted,#6b6b70);margin-top:10px;}
.divider .d-rule{width:64px;height:3px;background:var(--red);margin:14px auto 0;}
"""

SECT=re.compile(r'^([A-Z][A-Z0-9 ’\'&,·-]{3,44}) — (.*)$', re.S)
# House style has no inline bold — emphasis is structural (p.b, .sect, .pullquote).
# Markdown markers in copy would render as literal asterisks, so fail loudly instead.
MD=re.compile(r'\*\*[^*]+\*\*|(?<![\w*])\*[^*\n]+\*(?![\w*])')
def esc(t):
    m=MD.search(t)
    if m:
        raise SystemExit('markdown emphasis in copy (house style has no inline bold): '+m.group(0))
    return (t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace("'",'’'))

def article_blocks(art, first):
    out=[('sect', '<div class="divider"><div class="d-flag">'+esc(art.get('flag',''))+'</div>'
          '<div class="d-h">'+esc(art['headline'])+'</div>'
          '<div class="d-s">'+esc(art.get('subhead',''))+'</div>'
          '<div class="d-rule"></div></div>')]
    paras=art['paragraphs']
    for i,p in enumerate(paras):
        if i==len(paras)-1 and p.startswith('Sourcing'):
            out.append(('body','<div class="devnote">'+esc(p)+'</div>')); continue
        m=SECT.match(p)
        if m:
            out.append(('sect','<div class="sect">'+esc(m.group(1).title())+'</div>'))
            out.append(('body','<p class="b">'+esc(m.group(2))+'</p>'))
        elif p.startswith('“') and p.rstrip().endswith('”'):
            out.append(('body','<div class="pullquote">'+esc(p)+'</div>'))
        else:
            out.append(('body','<p class="b">'+esc(p)+'</p>'))
    return out

def build(key):
    cfg=ISSUES[key]
    src=open(TEMPLATE,encoding='utf-8').read()
    css=re.search(r'<style>(.*?)</style>',src,re.S).group(1)
    engine=re.search(r'<script>(.*?)</script>',src,re.S).group(1)
    inv={a['id']:a for a in json.load(open(os.path.join(ROOT,'investigations.json'),
                                           encoding='utf-8'))['investigations']}
    arts=[inv[i] for i in cfg['articles'] if i in inv]
    missing=[i for i in cfg['articles'] if i not in inv]
    if missing: print('  !! not found in investigations.json:', missing)

    have_art=os.path.exists(os.path.join(ROOT,cfg['art']))
    if not have_art:
        print(f"  note: cover art {cfg['art']} not present — using a typographic stand-in")
    cover=('<section class="page"><div class="issue-cover'+(' has-art' if have_art else '')+'">'
      + (f'<img src="{cfg["art"]}" alt="{esc(cfg["title"])}">' if have_art else '<div class="ic-fallback"></div>')
      + '<div class="ic-top">'
        '<div class="ic-mast" style="'+('' if have_art else 'color:#17181c;text-shadow:none')+'">'
        +cfg['mast'][0]+'<span>'+cfg['mast'][1]+'</span></div>'
        '<div class="ic-tag" style="'+('' if have_art else 'color:#8a8a90;text-shadow:none')+'">'
        +cfg['tagline']+'</div></div>'
        '<div class="ic-bot"><div class="ic-line" style="'+('' if have_art else 'color:#3a3a40;text-shadow:none')+'">'
        +esc(arts[0]['headline'] if arts else '')+'</div></div>'
      '</div></section>')

    toc=''.join(f'<li><span class="n">{i+1}</span><span class="t">{esc(a["headline"])}'
                f'<span class="k">{esc(a.get("flag",""))}</span></span></li>'
                for i,a in enumerate(arts))
    blocks=[('head','<span class="flag">In this issue</span>'
             '<h1 class="hl">'+esc(cfg['title'])+'</h1>'
             '<ul class="toc">'+toc+'</ul>')]
    for i,a in enumerate(arts): blocks += article_blocks(a, i==0)

    here=os.path.dirname(os.path.abspath(__file__))
    json.dump([b for _,b in blocks], open(os.path.join(here,'.pack-blocks.json'),'w',encoding='utf-8'))
    json.dump([k for k,_ in blocks], open(os.path.join(here,'.pack-kinds.json'),'w',encoding='utf-8'))
    brk=os.path.join(here,f'.pack-breaks-{key}.json')
    breaks=json.load(open(brk)) if os.path.exists(brk) else []
    run='<div class="runhead">'+cfg['runhead']+'</div>'
    pages=[]; start=0
    for b in breaks+[len(blocks)]:
        chunk=blocks[start:b]
        if chunk:
            pages.append('<section class="page"><div class="page-inner">'+run+
                         ''.join(x for _,x in chunk)+'</div></section>')
        start=b
    body='\n'.join(pages)

    share=('<button id="shareBtn" aria-label="Share" style="position:fixed;left:12px;bottom:12px;'
      'z-index:70;border:none;border-radius:999px;background:rgba(194,15,22,.45);backdrop-filter:blur(3px);'
      'color:#fff;font-weight:800;font-size:12.5px;padding:8px 14px;cursor:pointer;box-shadow:none;'
      'font-family:-apple-system,sans-serif">\U0001f4e4 Share</button>')
    sharejs=('<script>document.getElementById("shareBtn").addEventListener("click",async function(){'
      'var u=location.href.split("#")[0];var data={title:%s,text:%s,url:u};'
      'if(navigator.share){try{await navigator.share(data);return;}catch(e){if(e&&e.name==="AbortError")return;}}'
      'try{await navigator.clipboard.writeText(u);}catch(e){}'
      'var b=this,t=b.textContent;b.textContent="\\u2713 Link copied";'
      'setTimeout(function(){b.textContent=t;},1800);});</script>'
      % (json.dumps(cfg['ogtitle']), json.dumps(cfg['sharetext'])))

    html=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{cfg['title']} — Skirt Chasers</title>
<meta name="scfl:kicker" content="{cfg['kicker']}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Skirt Chasers — Dynasty League Magazine">
<meta property="og:title" content="{cfg['ogtitle']}">
<meta property="og:description" content="{cfg['ogdesc']}">
<meta property="og:url" content="{SITE}{cfg['out']}">
<meta property="og:image" content="{SITE}{cfg['og']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{cfg['ogtitle']}">
<meta name="twitter:description" content="{cfg['sharetext']}">
<meta name="twitter:image" content="{SITE}{cfg['og']}">
<link rel="icon" href="newsroom-favicon.png">
<style>{css}{EXTRA_CSS}</style>
</head>
<body>
<div class="book"><div class="pages">
{cover}
{body}
</div></div>
{share}
<button class="nav prev" id="prevBtn" aria-label="Previous">&lsaquo;</button>
<button class="nav next" id="nextBtn" aria-label="Next">&rsaquo;</button>
<div class="pagenum"><span id="pn">1</span> / <span id="pt">1</span></div>
<div class="fliphint" id="hint">Tap &rsaquo; or swipe to turn &rsaquo;</div>
<script>{engine}</script>
{sharejs}
</body></html>'''
    open(os.path.join(ROOT,cfg['out']),'w',encoding='utf-8').write(html)
    npages=html.count('<section class="page"')
    print(f"wrote {cfg['out']} | {len(arts)} articles | {len(blocks)} blocks | {npages} pages")
    return cfg

if __name__=='__main__':
    build(sys.argv[1] if len(sys.argv)>1 else 'kickoff-2026')
