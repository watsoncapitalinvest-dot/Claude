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
 'trade-audit': {
   'out': 'scfl-trade-audit.html',
   'tab': 'Trial of the Evil Empire — SCFL Investigations',
   'kicker': 'Investigations · The Trade Audit',
   'runhead': 'SCFL NewsRoom · Investigations · The Trade Audit',
   'mast': ('Trial of the ', 'Evil Empire'),   # fallback if the wordmark is missing
   'wordmark': 'wordmark-alt-words.png',
   'strapline': 'Fantasy League Magazine',
   'flag': 'The Ledger · A Trade Audit',
   'dek': True,
   'art': 'scfl-trade-audit-art.jpg',
   'bleed': True,
   'og': 'scfl-trade-audit-og.jpg',
   'ogtitle': 'Trial of the Evil Empire',
   # The window is the five COMPLETE seasons. This read "2021 to 2026" while
   # the piece inside priced 2021 to 2025, which is the sort of thing a share
   # card carries into every chat it is pasted into.
   'ogdesc': ('Twenty-one years of whispers that The Machines rig it. Every deal in the '
              'ledger from 2021 to 2025, priced at the season it was made and counted '
              'against the league register back to 2016. The verdict, and the numbers '
              'behind it.'),
   'sharetext': 'Trial of the Evil Empire: every Machines trade pulled, priced and counted.',
   'covernote': 'Every asset priced at the season it moved in.',
   'freeze_after': None,
   'art_topset': False,
   'dropcap_on': 'There is a theory',
   'sign': '— SCFL Investigations',
 },
 'the-grudge-report': {
   'out': 'scfl-grudge-report.html',
   'tab': 'The Grudge Report — SCFL Record Room',
   'kicker': 'The Record Room · Aug 2026',
   'runhead': 'SCFL NewsRoom · The Record Room · August 2026',
   'mast': ('The Grudge ', 'Report'),
   'art': 'scfl-grudge-art.jpg',
   'og': 'scfl-grudge-og.jpg',
   'ogtitle': 'The Grudge Report',
   'ogdesc': ("2,344 games across eighteen seasons. Who actually has a rivalry in the SCFL, "
              "and who just has a tormentor."),
   'sharetext': 'SCFL: 2,344 games audited. Who has a rivalry, and who has a tormentor.',
   'covernote': 'Every figure reconciled against the league record.',
   'freeze_after': None,
   'art_topset': True,  # the artwork leaves a quiet band at the top for the masthead
   'dropcap_on': 'This league has always',
   'sign': '— The Record Room',
 },
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

try:
    import importlib.util as _ilu
    _ad = _ilu.spec_from_file_location('ad', os.path.join(ROOT, 'scripts',
                                                          'build_addendum.py'))
    _adm = _ilu.module_from_spec(_ad); _ad.loader.exec_module(_adm)
    FIG_CSS = _adm.FIG_CSS
except Exception as _e:
    FIG_CSS = ''
    print('  note: figure styles unavailable —', _e)

EXTRA_CSS = """
.freeze{text-align:center;font-size:54px;line-height:1;margin:10px 0 14px;}
/* The verdict, as a page of its own. An investigation should be findable at
   the point where it answers the question it asked -- in prose it reads like
   every other paragraph and a reader flipping past never sees it. */
.verdict{display:flex;flex-direction:column;gap:2px;padding-top:0;}
.verdict .v-flag{font-family:var(--sans);font-size:11px;font-weight:900;
  letter-spacing:.26em;text-transform:uppercase;color:var(--red);}
.verdict .v-sub{font-family:var(--serif);font-style:italic;font-size:14.5px;
  color:var(--muted,#65656b);margin:3px 0 10px;padding-bottom:8px;
  border-bottom:2px solid var(--ink);}
.verdict .v-list{list-style:none;margin:0;padding:0;display:flex;
  flex-direction:column;gap:8px;}
.verdict .v-list li{padding:0 0 8px;border-bottom:1px solid var(--line,#e6e0d6);}
.verdict .v-list li:last-child{border-bottom:0;padding-bottom:0;}
.verdict .v-ch{display:flex;align-items:baseline;gap:10px;}
.verdict .v-n{font-family:var(--sans);font-size:10px;font-weight:900;
  letter-spacing:.1em;color:var(--faint,#9a958c);min-width:20px;}
.verdict .v-t{font-family:var(--serif);font-size:17.5px;line-height:1.18;
  font-weight:700;}
.verdict .v-vd{font-family:var(--sans);font-size:21px;font-weight:900;
  letter-spacing:-.01em;margin:3px 0 0 30px;line-height:1;}
.verdict li.clear .v-vd{color:var(--blue,#0e8ab5);}
.verdict li.guilty .v-vd{color:var(--red,#c20f16);}
.verdict li.guilty .v-t{color:var(--red,#c20f16);}
.verdict .v-ev{font-family:var(--serif);font-size:13.5px;line-height:1.4;
  color:var(--muted,#65656b);margin:4px 0 0 30px;}
/* The row the table is about. A wide table of counts needs one row marked or
   the reader has to find the subject by name on every scroll; gold is the
   house colour for "this is the one that matters". */
.ad tbody tr.on th,.ad tbody tr.on td{background:rgba(216,180,90,.18);font-weight:700;}
/* photo cover — the artwork whole, never cropped */
.photocover{position:absolute;inset:0;background:#0a0806;display:flex;flex-direction:column;
  padding:18px 0 74px;}
.photocover.plain{background:#fffdfb;padding:0 0 62px;}
.photocover.plain .pc-art{object-fit:contain;}
/* A magazine cover: art edge to edge, masthead over the top of it, headline
   over the bottom. Both bands get their own scrim, because art drawn to be
   looked at is a bad bed for type everywhere except where you darken it. The
   older .photocover letterboxes the art between two solid bars instead, which
   is right for a picture that has to be seen whole and wrong for a cover. */
.photocover.bleed{padding:0;display:block;background:#0a0806;}
.photocover.bleed .pc-art{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;}
.photocover.bleed .pc-top{position:absolute;left:0;right:0;top:0;padding:12px 20px 22px;
  text-align:center;background:linear-gradient(180deg,rgba(6,5,4,.94) 0%,
  rgba(6,5,4,.74) 52%,rgba(6,5,4,0) 100%);}
.photocover.bleed .pc-bot{position:absolute;left:0;right:0;bottom:0;margin:0;
  padding:30px 22px 76px;background:linear-gradient(180deg,rgba(10,8,6,0) 0%,
  rgba(10,8,6,.88) 30%,#0a0806 68%);}
.photocover.bleed .pc-kick{padding:0 0 8px;}
/* The masthead is sized to the ART, not to the page. At 84 per cent it sat
   squarely on the one thing this cover is of. A cover subject in the upper
   third is the usual case, not the exception, so the wordmark takes the
   smaller of the two widths here and the scrim follows it up. */
.photocover.bleed .pc-wm{width:66%;max-width:252px;}
.photocover.bleed .pc-wmtag{max-width:252px;}
.photocover.bleed .pc-wmtag span{font-size:8.5px;letter-spacing:.22em;}
/* artwork that leaves its own space for the masthead */
.photocover.topset{background:#f3ece0;padding:0;display:block;}
.photocover.topset .pc-art{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;}
.pc-set{position:absolute;left:0;right:0;top:0;padding:30px 26px 0;text-align:center;}
.pc-set .pc-kick{color:#b23a2c;padding:0 0 10px;}
.pc-set .pc-mast{font-size:40px;color:#1c1814;text-shadow:none;}
.pc-set .pc-mast span{color:#b23a2c;}
.pc-set .pc-h{font-size:21px;color:#3a332a;text-shadow:none;margin:10px 0 0;}
.pc-set .pc-rule{background:#b23a2c;margin:12px auto 0;}
.pc-kick{flex:0 0 auto;text-align:center;font-family:var(--sans);font-size:10px;font-weight:900;
  letter-spacing:.32em;text-transform:uppercase;color:#e8393e;padding:0 18px 12px;}
.pc-art{flex:1 1 auto;min-height:0;width:100%;object-fit:contain;display:block;}
.pc-bot{flex:0 0 auto;position:relative;text-align:center;padding:14px 22px 0;
  background:linear-gradient(180deg,rgba(10,8,6,0) 0%,#0a0806 22%);margin-top:-26px;}
/* The magazine wordmark, when a story runs under the masthead rather than
   under a title set in type. It arrives with its paper already cut away
   (scripts/cut_wordmark.py), so it sits on the art with nothing behind it. */
.pc-wm{display:block;width:84%;max-width:330px;height:auto;margin:0 auto;
  filter:drop-shadow(0 3px 16px rgba(0,0,0,.95));}
.pc-wmtag{display:flex;align-items:center;gap:9px;max-width:330px;margin:7px auto 0;}
.pc-wmtag::before,.pc-wmtag::after{content:'';flex:1;height:1px;}
.pc-wmtag::before{background:linear-gradient(90deg,transparent,#d8b45a);}
.pc-wmtag::after{background:linear-gradient(90deg,#d8b45a,transparent);}
.pc-wmtag span{font-family:var(--serif);font-weight:700;font-size:9.5px;letter-spacing:.26em;
  text-transform:uppercase;color:#efe7d2;white-space:nowrap;
  text-shadow:0 2px 10px rgba(0,0,0,.95);}
.pc-mast{font-family:var(--serif);font-weight:900;font-size:44px;line-height:.98;color:#f7f3ec;
  text-shadow:0 2px 14px rgba(0,0,0,.9);}
.pc-mast span{color:#e8393e;}
.pc-rule{width:70px;height:3px;background:#c20f16;margin:13px auto;}
.pc-h{font-family:var(--serif);font-weight:900;font-size:27px;line-height:1.12;color:#fff;margin-bottom:8px;}
.pc-dek{font-family:var(--serif);font-style:italic;font-size:15px;line-height:1.45;color:#cfc9bf;
  max-width:30em;margin:0 auto 12px;}
.pc-by{font-family:var(--sans);font-size:10.5px;font-weight:800;letter-spacing:.2em;
  text-transform:uppercase;color:#a89f93;}
/* a bordered notice. Centred was right for the one-line victim-support gag it
   was built for; a scope note runs to a paragraph and a half, and centred
   prose at that length is a ragged diamond nobody reads. The title stays
   centred, the body does not. */
.psa{border:2px solid var(--red);border-radius:14px;padding:16px 18px;margin:16px 0 6px;
  background:#fdf3f3;text-align:center;}
.psa .t{font-family:var(--sans);font-size:12px;font-weight:900;letter-spacing:.13em;
  text-transform:uppercase;color:var(--red);line-height:1.35;margin-bottom:9px;}
.psa p{font-size:15.5px;line-height:1.5;margin:0;color:var(--ink);}
.psa p + p{margin-top:10px;}
.psa.note{text-align:left;} .psa.note .t{text-align:center;}
.psa .wa{display:inline-block;margin-top:11px;font-family:var(--sans);font-size:12.5px;
  font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:#1a7f37;}
"""

SECT = re.compile(r'^([A-Z][A-Z0-9 ’\'&,·-]{3,44}) — (.*)$', re.S)

def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace("'", '’'))

def blocks_for(art, cfg):
    out = [('head', '<span class="flag">' + esc(cfg.get('flag', 'Special Feature')) + '</span>'
                    '<div class="dateline">' + esc(art['dateline']) + '</div>'
                    '<h1 class="hl">' + esc(art['headline']) + '</h1>'
                    + ('<p class="dek">' + esc(art['subhead']) + '</p>'
                       if cfg.get('dek') and art.get('subhead') else ''))]
    # An article that carries its own rendered markup -- tables, charts, a
    # methodology section -- owns its body. The paragraph walker below only
    # knows how to wrap plain text, and would escape a <figure> into
    # characters on the page.
    if art.get('blocks'):
        out += [tuple(b) for b in art['blocks']]
        if cfg.get('sign'):
            out.append(('body', '<div class="sign">&mdash; '
                        + esc(cfg['sign'].lstrip('— ')) + '</div>'))
        return dropcap(out, cfg)
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
    return dropcap(out, cfg)


def dropcap(out, cfg):
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

    def masthead():
        if cfg.get('wordmark'):
            return ('<img class="pc-wm" src="' + cfg['wordmark'] + '" alt="Skirt Chasers">'
                    + ('<div class="pc-wmtag"><span>' + esc(cfg['strapline']) + '</span></div>'
                       if cfg.get('strapline') else ''))
        return ('<div class="pc-mast">' + cfg['mast'][0] + '<span>' + cfg['mast'][1]
                + '</span></div>')

    # An art file that is named but not on disk renders as a broken-image icon
    # over the headline. Until the artwork arrives the cover runs typographic,
    # which is the house fallback everywhere else too.
    have_art = bool(cfg.get('art')) and os.path.exists(os.path.join(ROOT, cfg['art']))
    if cfg.get('art') and not have_art:
        print('  note: cover art', cfg['art'], 'not present — cover runs without it')
    art_img = ('<img class="pc-art" src="' + cfg['art'] + '" alt="' + esc(art['headline'])
               + '">') if have_art else ''

    if cfg.get('bleed') and have_art:
        cover = ('<section class="page"><div class="photocover bleed">'
                 + art_img +
                 '<div class="pc-top">'
                 '<div class="pc-kick">' + cfg['kicker'] + '</div>'
                 + masthead() +
                 '</div>'
                 '<div class="pc-bot">'
                 '<div class="pc-rule"></div>'
                 '<div class="pc-h">' + esc(art['headline']) + '</div>'
                 '<div class="pc-dek">' + esc(art['subhead']) + '</div>'
                 '<div class="pc-by">The SCFL NewsRoom</div>'
                 '</div></div></section>')
    elif cfg.get('art_topset'):
        cover = ('<section class="page"><div class="photocover topset">'
                 + art_img +
                 '<div class="pc-set">'
                 '<div class="pc-kick">' + cfg['kicker'] + '</div>'
                 + masthead() +
                 '<div class="pc-rule"></div>'
                 '<div class="pc-h">' + esc(art['subhead'].split('.')[0]) + '.</div>'
                 '</div></div></section>')
    elif cfg.get('plain_art'):
        cover = ('<section class="page"><div class="photocover plain">'
                 + art_img +
                 '</div></section>')
    else:
        cover = ('<section class="page"><div class="photocover">'
             '<div class="pc-kick">' + cfg['kicker'] + '</div>'
             + art_img +
             '<div class="pc-bot">'
             + masthead() +
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
<style>{css}{EXTRA_CSS}{FIG_CSS}</style>
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
