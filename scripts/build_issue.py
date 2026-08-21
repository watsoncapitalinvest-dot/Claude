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
import json, os, re, subprocess, sys

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
   'ogdesc':("Sixteen teams enter. One leaves with the ring. A 7-7 champion with a target on his "
             "back, a rename decided by 207 points, the division that will eat two contenders "
             "alive, and all sixteen scouted."),
   'sharetext':'Sixteen enter. One leaves. The 2026-27 SCFL season starts here.',
   'kicker':'The Magazine · Aug 2026',
   'seal':('Kickoff','Issue'),
   'issueline':'2026&ndash;27 Season &middot; The Kickoff Issue',
   'hook':'Sixteen Enter. One Leaves.',
   'hooksub':('A 7-7 champion with a target on his back, a division that will eat two '
              'contenders alive, and one man about to lose his name.'),
   'coverlines':[
     'THE CHAMPION NOBODY FEARS: 7-7, AND HE STILL HAS THE RING',
     'ONE OF THESE MEN LOSES HIS NAME',
     'THE GROUP OF DEATH: THREE MONSTER OFFENCES, ONE DIVISION',
     'ALL 16 SCOUTED: WHO&rsquo;S LOADED, WHO&rsquo;S COOKED',
     'THE PICKS: EVERY DIVISION, AND WHO LIFTS IT',
     'THE GRUDGE REPORT: 2,344 GAMES, EVERY RIVALRY RANKED',
   ],
   'articles':['kick-2026-champion','kick-2026-namechange','kick-2026-blackandblue',
               'kick-2026-preview','kick-2026-picks','the-grudge-report','the-hill-standoff'],
   # Opener art, one per article. Any missing file is skipped and that article
   # opens typographically, so the issue always builds. Cropped to 3:2, so the
   # supplied image can be any shape as long as the subject is centred.
   'openart':{
     'kick-2026-champion':'scfl-art-champion.jpg',
     'kick-2026-namechange':'scfl-art-namechange.jpg',
     'kick-2026-blackandblue':'scfl-art-blackandblue.jpg',
     'kick-2026-preview':'scfl-art-preview.jpg',
     'kick-2026-picks':'scfl-art-picks.jpg',
     'the-grudge-report':'scfl-grudge-art.jpg',
     'the-hill-standoff':'scfl-art-hillstandoff.jpg',
   },
 },
}

EXTRA_CSS="""
/* ---- the house issue cover: red frame, wordmark panel, coverlines ----
   Matches draft-issue.html and scfl-post-draft-issue.html exactly. The art is a
   background on .magcover rather than an <img> so the 2:3 frame is fixed by
   aspect-ratio and never re-crops to the viewport. */
.cover-page{display:flex;align-items:center;justify-content:center;padding:0;background:#d9d6ce;}
.cover-page .magcover{margin:0;min-height:0;width:min(94vw,63vh);height:auto;
  box-shadow:0 20px 60px rgba(0,0,0,.7);}
.magcover{position:relative;overflow:hidden;max-width:600px;margin:0 auto 26px;
  border:11px solid #e11b22;border-radius:3px;box-shadow:0 26px 70px rgba(0,0,0,.6);
  background:var(--teaser) center/cover no-repeat #0b0f14;aspect-ratio:2/3;min-height:600px;
  display:flex;flex-direction:column;color:#fff;}
.magcover::before{content:'';position:absolute;inset:0;z-index:0;pointer-events:none;
  background:linear-gradient(180deg,rgba(6,8,10,.20) 0%,rgba(6,8,10,0) 9%,rgba(6,8,10,0) 55%,
  rgba(6,8,10,.40) 70%,rgba(6,8,10,.90) 100%);}
.cov-top{position:relative;z-index:1;margin:10px 11px 0;padding:6px 14px 5px;text-align:center;
  background:#f4f1ea;border-radius:4px;box-shadow:0 5px 18px rgba(0,0,0,.5);
  border-top:2px solid #e11b22;border-bottom:2px solid #e11b22;}
.mag-logo{display:block;width:100%;max-width:280px;height:auto;margin:0 auto;}
.mag-issue{color:#c20f16;font-weight:900;font-size:9.5px;letter-spacing:2.5px;margin-top:3px;
  text-transform:uppercase;}
.preseal{position:absolute;left:3px;bottom:-22px;width:60px;height:60px;border-radius:50%;
  background:#e11b22;color:#fff;border:2px solid #fff;box-shadow:0 4px 12px rgba(0,0,0,.6);
  display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;
  transform:rotate(-9deg);font-family:var(--serif);font-weight:900;font-size:10px;line-height:1;
  text-transform:uppercase;letter-spacing:.2px;z-index:4;}
.preseal small{font-size:6.5px;font-weight:800;letter-spacing:1px;opacity:.92;display:block;margin-top:2px;}
.cov-bottom{position:relative;z-index:1;margin-top:auto;padding:0 20px 12px;text-align:center;}
.mag-hook{font-family:var(--serif);font-weight:900;font-size:clamp(26px,5.8vw,38px);line-height:.95;
  letter-spacing:-1px;color:#fff;text-wrap:balance;
  text-shadow:0 3px 20px rgba(0,0,0,.95),0 1px 3px rgba(0,0,0,.9);}
.mag-name{font-family:var(--serif);font-weight:800;font-style:italic;font-size:clamp(12px,3.1vw,15px);
  line-height:1.22;color:#f3f5f8;margin:7px auto 0;text-shadow:0 2px 12px rgba(0,0,0,.95);max-width:34ch;}
.mag-lines{margin-top:10px;border-top:2px solid #ff5442;padding-top:8px;display:flex;
  flex-direction:column;gap:4px;text-align:left;max-width:340px;margin-left:auto;margin-right:auto;}
.mag-line{font-size:9.5px;font-weight:800;letter-spacing:.2px;text-transform:uppercase;color:#f3f5f8;
  padding-left:14px;position:relative;line-height:1.25;text-shadow:0 1px 5px rgba(0,0,0,.98);}
.mag-line::before{content:'▸';position:absolute;left:0;color:#ff5442;}
.mag-shield{display:block;margin:9px auto 0;width:44px;height:auto;
  filter:drop-shadow(0 2px 8px rgba(0,0,0,.95));}
@media(max-width:720px){.magcover{margin:0 0 20px;border-width:9px;}}
.toc{list-style:none;padding:0;margin:6px 0 0;}
.toc li{display:flex;gap:10px;align-items:baseline;padding:10px 0;border-bottom:1px solid var(--line);}
.toc .n{font-family:var(--sans);font-size:11px;font-weight:900;color:var(--red);min-width:22px;}
.toc .t{flex:1;font-weight:800;font-size:14px;line-height:1.3;}
.toc .k{font-family:var(--sans);font-size:10px;font-weight:800;letter-spacing:.1em;
  text-transform:uppercase;color:var(--faint);display:block;margin-top:3px;}
.divider{text-align:center;padding:26px 0 8px;}
.divider .d-art{display:block;width:100%;aspect-ratio:3/2;object-fit:cover;border-radius:2px;
  margin:0 0 20px;background:#e8e2d8;}
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

def article_blocks(art, first, openart=None):
    # 'divider' rather than 'sect': the packer forces a page break before one, so
    # every article finishes its own page and the next one opens a fresh one.
    img=(f'<img class="d-art" src="{openart}" alt="">' if openart else '')
    out=[('divider', '<div class="divider">'+img+'<div class="d-flag">'+esc(art.get('flag',''))+'</div>'
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

def build(key, remeasure=True, quiet=False):
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
    art_css = f"url('{cfg['art']}')" if have_art else 'none'
    lines=''.join('<div class="mag-line">'+l+'</div>' for l in cfg['coverlines'])
    cover=('<section class="page cover-page">'
      f'<div class="magcover" style="--teaser:{art_css}">'
        '<div class="cov-top">'
          '<img class="mag-logo" src="wordmark.png" alt="Skirt Chasers — Dynasty League Magazine">'
          '<div class="mag-issue">'+cfg['issueline']+'</div>'
          '<div class="preseal">'+cfg['seal'][0]+'<small>'+cfg['seal'][1]+'</small></div>'
        '</div>'
        '<div class="cov-bottom">'
          '<div class="mag-hook">'+esc(cfg['hook'])+'</div>'
          '<div class="mag-name">'+esc(cfg['hooksub'])+'</div>'
          '<div class="mag-lines">'+lines+'</div>'
          '<img class="mag-shield" src="scfl-shield.png" alt="SCFL">'
        '</div>'
      '</div></section>')

    toc=''.join(f'<li><span class="n">{i+1}</span><span class="t">{esc(a["headline"])}'
                f'<span class="k">{esc(a.get("flag",""))}</span></span></li>'
                for i,a in enumerate(arts))
    blocks=[('head','<span class="flag">In this issue</span>'
             '<h1 class="hl">'+esc(cfg['title'])+'</h1>'
             '<ul class="toc">'+toc+'</ul>')]
    openart=cfg.get('openart',{})
    missing_art=[]
    for i,a in enumerate(arts):
        f=openart.get(a['id'])
        if f and not os.path.exists(os.path.join(ROOT,f)):
            missing_art.append(f); f=None
        blocks += article_blocks(a, i==0, f)
    if missing_art and not quiet:
        print('  note: opener art not present, those articles open typographically:',
              ', '.join(missing_art))

    here=os.path.dirname(os.path.abspath(__file__))
    json.dump([b for _,b in blocks], open(os.path.join(here,'.pack-blocks.json'),'w',encoding='utf-8'))
    json.dump([k for k,_ in blocks], open(os.path.join(here,'.pack-kinds.json'),'w',encoding='utf-8'))
    brk=os.path.join(here,f'.pack-breaks-{key}.json')
    if remeasure:
        # Pass 1 lays the page out with whatever breaks are on disk so the
        # measurer has something to render, then re-measures against the copy
        # that is actually being published and lays it out again. Without this
        # an edit silently keeps the previous issue's page breaks.
        if os.path.exists(brk): os.remove(brk)
        build(key, remeasure=False, quiet=True)
        subprocess.run(['node', os.path.join(here,'measure_pages.js'), key, cfg['out'],
                        'file://'+ROOT], check=True,
                       env=dict(os.environ, NODE_PATH='/opt/node22/lib/node_modules'),
                       cwd=ROOT, capture_output=True)
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
    if not quiet:
        print(f"wrote {cfg['out']} | {len(arts)} articles | {len(blocks)} blocks | {npages} pages")
    return cfg

if __name__=='__main__':
    build(sys.argv[1] if len(sys.argv)>1 else 'kickoff-2026')
