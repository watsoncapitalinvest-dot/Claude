#!/usr/bin/env python3
"""Build a standalone SCFL flip page from an entry in investigations.json.

Lives in the repo on purpose: the previous one-off builders were kept in a temp
directory and were lost when the container reset, leaving published pages that
could not be regenerated.

    python3 scripts/build_story_page.py the-wookie-curse

Pagination is measurement-driven: scripts/measure_pages.js renders the page and
records where each page fills up, so no page ever scrolls. Run the measure pass
(or `--measure`) after changing copy.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, 'scfl-politics-wire-freeze-flip.html')
SITE = 'https://watsoncapitalinvest-dot.github.io/Claude/'

# Per-story presentation. Copy lives in investigations.json; this is only chrome.
STORIES = {
 'the-wookie-curse': {
   'out': 'scfl-wookie-curse.html',
   'tab': 'The Wookie Curse — SCFL Investigations',
   'kicker': 'Investigations · Aug 2026',
   'runhead': 'SCFL NewsRoom · Investigations · August 2026',
   'mast': ('The Wookie ', 'Curse'),
   'art': 'scfl-wookie-curse-art.jpg',
   'og': 'scfl-wookie-curse-og.jpg',
   'ogtitle': 'The Wookie Curse: The Roll Call',
   'ogdesc': ("Romo. Fournette. Hunt. Murray. Kupp. Metcalf. And now Jordyn Tyson. "
              "A field guide to the SCFL's only working curse."),
   'sharetext': "SCFL Investigations: a field guide to the SCFL's only working curse.",
   'covernote': 'Every quotation verified against the league chat.',
   'freeze_after': 'It has a symbol',
   'dropcap_on': 'Every league',
   'sign': '— SCFL Investigations',
 },
}

EXTRA_CSS = """
.freeze{text-align:center;font-size:54px;line-height:1;margin:10px 0 14px;}
/* photo cover — the artwork whole, never cropped */
.photocover{position:absolute;inset:0;background:#0a0806;display:flex;flex-direction:column;
  padding:18px 0 74px;}
.pc-kick{flex:0 0 auto;text-align:center;font-family:var(--sans);font-size:10px;font-weight:900;
  letter-spacing:.32em;text-transform:uppercase;color:#e8393e;padding:0 18px 12px;}
.pc-art{flex:1 1 auto;min-height:0;width:100%;object-fit:contain;display:block;}
.pc-bot{flex:0 0 auto;position:relative;text-align:center;padding:14px 22px 0;
  background:linear-gradient(180deg,rgba(10,8,6,0) 0%,#0a0806 22%);margin-top:-26px;}
.pc-mast{font-family:var(--serif);font-weight:900;font-size:44px;line-height:.98;color:#f7f3ec;
  text-shadow:0 2px 14px rgba(0,0,0,.9);}
.pc-mast span{color:#e8393e;}
.pc-rule{width:70px;height:3px;background:#c20f16;margin:13px auto;}
.pc-h{font-family:var(--serif);font-weight:900;font-size:27px;line-height:1.12;color:#fff;margin-bottom:8px;}
.pc-dek{font-family:var(--serif);font-style:italic;font-size:15px;line-height:1.45;color:#cfc9bf;
  max-width:30em;margin:0 auto 12px;}
.pc-by{font-family:var(--sans);font-size:10.5px;font-weight:800;letter-spacing:.2em;
  text-transform:uppercase;color:#a89f93;}
/* victim support notice */
.psa{border:2px solid var(--red);border-radius:14px;padding:16px 18px;margin:16px 0 6px;
  background:#fdf3f3;text-align:center;}
.psa .t{font-family:var(--sans);font-size:12px;font-weight:900;letter-spacing:.13em;
  text-transform:uppercase;color:var(--red);line-height:1.35;margin-bottom:9px;}
.psa p{font-size:15.5px;line-height:1.5;margin:0;color:var(--ink);}
.psa .wa{display:inline-block;margin-top:11px;font-family:var(--sans);font-size:12.5px;
  font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:#1a7f37;}
"""

SECT = re.compile(r'^([A-Z][A-Z0-9 ’\'&,·-]{3,44}) — (.*)$', re.S)

def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace("'", '’'))

def blocks_for(art, cfg):
    out = [('head', '<span class="flag">Special Feature</span>'
                    '<div class="dateline">' + esc(art['dateline']) + '</div>'
                    '<h1 class="hl">' + esc(art['headline']) + '</h1>')]
    paras = art['paragraphs']
    for i, p in enumerate(paras):
        last = (i == len(paras) - 1)
        if last:
            out.append(('body', '<div class="devnote">' + esc(p) + '</div>'))
            out.append(('body', '<div class="sign">&mdash; ' + esc(cfg['sign'].lstrip('— ')) + '</div>'))
            continue
        if p.startswith('ARE YOU A VICTIM'):
            t, body = p.split(' — ', 1)
            out.append(('body', '<div class="psa"><div class="t">' + esc(t) + '</div><p>' + esc(body) +
                        '</p><div class="wa">\U0001f4f2 WhatsApp · Counselors standing by</div></div>'))
            continue
        m = SECT.match(p)
        if m:
            out.append(('sect', '<div class="sect">' + esc(m.group(1).title()) + '</div>'))
            out.append(('body', '<p class="b">' + esc(m.group(2)) + '</p>'))
        elif p.startswith('“') and p.rstrip().endswith('”'):
            out.append(('body', '<div class="pullquote">' + esc(p) + '</div>'))
        else:
            out.append(('body', '<p class="b">' + esc(p) + '</p>'))
        if cfg.get('freeze_after') and p.startswith(cfg['freeze_after']):
            out.insert(len(out) - 1, ('body', '<div class="freeze">\U0001f976</div>'))
    for i, (k, b) in enumerate(out):
        if k == 'body' and b.startswith('<p class="b">' + cfg['dropcap_on'][0]) and cfg['dropcap_on'] in b:
            c = cfg['dropcap_on'][0]
            out[i] = (k, b.replace('<p class="b">' + c,
                                   '<p class="b"><span class="drop">%s</span>' % c, 1))
            break
    return out

def build(slug):
    cfg = STORIES[slug]
    src = open(TEMPLATE, encoding='utf-8').read()
    css = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
    engine = re.search(r'<script>(.*?)</script>', src, re.S).group(1)
    art = [x for x in json.load(open(os.path.join(ROOT, 'investigations.json'), encoding='utf-8'))
           ['investigations'] if x['id'] == slug][0]

    blocks = blocks_for(art, cfg)
    here = os.path.dirname(os.path.abspath(__file__))
    json.dump([b for _, b in blocks], open(os.path.join(here, '.pack-blocks.json'), 'w', encoding='utf-8'))
    json.dump([k for k, _ in blocks], open(os.path.join(here, '.pack-kinds.json'), 'w', encoding='utf-8'))
    brk = os.path.join(here, '.pack-breaks-%s.json' % slug)
    breaks = json.load(open(brk)) if os.path.exists(brk) else []

    run = '<div class="runhead">' + cfg['runhead'] + '</div>'
    pages, start = [], 0
    for b in breaks + [len(blocks)]:
        chunk = blocks[start:b]
        if chunk:
            pages.append('<section class="page"><div class="page-inner">' + run +
                         ''.join(x for _, x in chunk) + '</div></section>')
        start = b
    body = '\n'.join(pages)

    cover = ('<section class="page"><div class="photocover">'
             '<div class="pc-kick">' + cfg['kicker'].split('·')[0].strip() + ' &middot; SCFL NewsRoom</div>'
             '<img class="pc-art" src="' + cfg['art'] + '" alt="' + esc(art['headline']) + '">'
             '<div class="pc-bot">'
             '<div class="pc-mast">' + cfg['mast'][0] + '<span>' + cfg['mast'][1] + '</span></div>'
             '<div class="pc-rule"></div>'
             '<div class="pc-h">' + esc(art['headline']) + '</div>'
             '<div class="pc-dek">' + esc(art['subhead']) + '</div>'
             '<div class="pc-by">The SCFL NewsRoom</div>'
             '</div></div></section>')

    share = ('<button id="shareBtn" aria-label="Share" style="position:fixed;left:12px;bottom:12px;'
             'z-index:70;border:none;border-radius:999px;background:rgba(194,15,22,.45);'
             'backdrop-filter:blur(3px);color:#fff;font-weight:800;font-size:12.5px;padding:8px 14px;'
             'cursor:pointer;box-shadow:none;font-family:-apple-system,sans-serif">\U0001f4e4 Share</button>')
    sharejs = ('<script>document.getElementById("shareBtn").addEventListener("click",async function(){'
               'var u=location.href.split("#")[0];var data={title:%s,text:%s,url:u};'
               'if(navigator.share){try{await navigator.share(data);return;}catch(e){'
               'if(e&&e.name==="AbortError")return;}}'
               'try{await navigator.clipboard.writeText(u);}catch(e){}'
               'var b=this,t=b.textContent;b.textContent="\\u2713 Link copied";'
               'setTimeout(function(){b.textContent=t;},1800);});</script>'
               % (json.dumps(cfg['ogtitle']), json.dumps(cfg['sharetext'])))

    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{cfg['tab']}</title>
<meta name="scfl:kicker" content="{cfg['kicker']}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Skirt Chasers — Dynasty League Magazine">
<meta property="og:title" content="{cfg['ogtitle']}">
<meta property="og:description" content="{cfg['ogdesc']}">
<meta property="og:url" content="{SITE}{cfg['out']}">
<meta property="og:image" content="{SITE}{cfg['og']}">
<meta property="og:image:alt" content="{cfg['ogtitle']}">
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
    open(os.path.join(ROOT, cfg['out']), 'w', encoding='utf-8').write(html)
    print('wrote', cfg['out'], len(html), 'chars |', len(blocks), 'blocks |',
          html.count('<section class="page"'), 'pages')
    return cfg

if __name__ == '__main__':
    slug = sys.argv[1] if len(sys.argv) > 1 else 'the-wookie-curse'
    build(slug)
