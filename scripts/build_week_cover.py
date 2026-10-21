#!/usr/bin/env python3
"""Draw the weekly cover out of the game itself.

    python3 scripts/build_week_cover.py --week 4

Claude cannot make a photograph, and a stadium drawn from memory looks like
clip art -- an earlier version of this file proved that convincingly. So the
cover is not a picture of football. It is the shape of the week's best match:
the margin plotted across sixty minutes, red where the winner led and blue
where they did not, with a marker everywhere the lead changed hands.

For a game that turned over ten times, that line crosses its own axis ten
times. No other magazine can print it, because no other magazine knows the
running score of a fantasy matchup minute by minute. It is the argument for
the whole replay, in one picture.

Rendered through the same Chromium pipeline as every share card here, at
1024x1536, straight into the slot build_issue.py expects.

Nothing here draws a word, a score or a name. The masthead, the seal, the
headline, the cover lines and the shield are composited on top afterwards --
an earlier version drew the score underneath them, so the cover carried
everything twice. A supplied photograph overwrites this file and nothing else
changes.
"""
import argparse, base64, importlib.util, io, json, os
import re as _re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')
_s = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts', 'build_addendum.py'))
ad = importlib.util.module_from_spec(_s); sys.modules['ad'] = ad; _s.loader.exec_module(ad)

W, H = 1024, 1536


# The portrait card. A figure cannot share a 1200x630 frame with a panel of type
# down one side -- every crop that keeps his face puts it behind the headline,
# and every crop that clears the headline loses the thing he is doing. So the
# picture takes the whole card and the words go across the bottom, which is
# where a cover puts them for the same reason.
OGP = """<style>
:root{--red:#c20f16;--ink:#0b0b0f;--cream:#f4f1ea;--gold:#d8b45a;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;margin:0;}
html,body{width:1200px;height:630px;overflow:hidden;background:#0b0b0f;
 font-family:Georgia,'Times New Roman',serif;color:var(--cream);}
.c{position:relative;width:1200px;height:630px;overflow:hidden;background:#0b0b0f;
 background-size:cover;background-position:center top;__PHOTO__
 border-top:9px solid var(--red);border-bottom:9px solid var(--red);}
.c::after{content:'';position:absolute;inset:0;
 background:linear-gradient(180deg,rgba(11,11,15,.55) 0%,rgba(11,11,15,0) 22%,
 rgba(11,11,15,0) 38%,rgba(11,11,15,.80) 66%,rgba(11,11,15,.97) 100%);}
.b{position:absolute;left:0;right:0;bottom:0;z-index:2;padding:0 54px 40px;
 display:flex;align-items:flex-end;justify-content:space-between;gap:36px;}
.flag{font-family:var(--sans);font-size:11.5px;font-weight:900;letter-spacing:.24em;
 text-transform:uppercase;color:#ff5442;text-shadow:0 1px 6px rgba(0,0,0,.9);}
h1{font-size:50px;line-height:1.02;letter-spacing:-.022em;font-weight:900;margin-top:12px;
 max-width:17ch;text-shadow:0 3px 22px rgba(0,0,0,.95),0 1px 3px rgba(0,0,0,.9);}
.st{display:flex;gap:30px;flex:none;padding-bottom:6px;}
.st .k{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:#b2aca3;}
.st .v{font-size:26px;font-weight:900;line-height:1.1;font-variant-numeric:tabular-nums;
 text-shadow:0 2px 12px rgba(0,0,0,.95);}
.st .v b{color:var(--gold);font-weight:900;}
</style>
<div class="c"><div class="b">
  <div><div class="flag">The Week __WK__ Issue</div><h1>__HL__</h1></div>
  <div class="st">
    __STATS__
  </div>
</div></div>"""

def data_uri(art, tall=False):
    """The share-card strip of `art`, inline, so the card has no dependencies.

    ad.shoot renders the HTML in a throwaway context; a relative src resolves
    against nothing and the card comes out as the empty black rectangle every
    unbuilt card looks like. Inlining is the whole reason the issue builder
    inlines its assets too.
    """
    import importlib.util as _iu
    _s = _iu.spec_from_file_location('cc', os.path.join(ROOT, 'scripts', 'compose_cover.py'))
    cc = _iu.module_from_spec(_s); _s.loader.exec_module(cc)
    buf = io.BytesIO()
    strip = (cc.band(art, 1200, 630, focus=(0.58, 0.13), place=(0.5, 0.33))
             if tall else cc.band(art, 1200, 630))
    strip.save(buf, 'JPEG', quality=86, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def curve(points, w, h, x0, y0):
    """The margin as a path. Returns (line, filled area, the zero axis y)."""
    if not points:
        return '', '', y0 + h / 2
    span = max(max(abs(p[1]) for p in points), 6)
    mid = y0 + h / 2
    xs = lambda t: x0 + w * t
    ys = lambda v: mid - (v / span) * (h / 2) * 0.92
    d = f'M{xs(points[0][0]):.1f} {ys(points[0][1]):.1f}'
    for t, v in points[1:]:
        d += f' L{xs(t):.1f} {ys(v):.1f}'
    area = d + f' L{xs(points[-1][0]):.1f} {mid:.1f} L{xs(points[0][0]):.1f} {mid:.1f} Z'
    return d, area, mid


def crossings(points):
    """Where the lead actually changed hands, for the markers.

    A game starts level, so the first team to score takes the lead -- it does
    not change it. Counting that transition made this cover draw one more gold
    ring than the replay counts lead changes, and the share card beside it
    reads its number straight off the replay, so the two disagreed in print.
    The lead only changes when somebody already held it.
    """
    out, held = [], 0
    for a, b in zip(points, points[1:]):
        if abs(b[1]) <= 0.01:
            continue
        side = 1 if b[1] > 0 else -1
        if held and side != held:
            out.append(b[0])
        held = side
    return out


COVER = """<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@600;700&display=swap');
*{box-sizing:border-box;margin:0;}
html,body{width:1024px;height:1536px;overflow:hidden;background:#0b0b0f;}
.c{position:relative;width:1024px;height:1536px;overflow:hidden;background:#0b0b0f;}
svg{position:absolute;inset:0;}
.wk{position:absolute;left:0;right:0;top:16%;text-align:center;
 font-family:'Oswald',Impact,sans-serif;font-weight:700;font-size:430px;line-height:.78;
 letter-spacing:-16px;color:rgba(244,241,234,.05);
 -webkit-text-stroke:2px rgba(216,180,90,.22);}
.grain{position:absolute;inset:0;opacity:.05;pointer-events:none;
 background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/></filter><rect width='120' height='120' filter='url(%23n)'/></svg>");}
.vig{position:absolute;inset:0;pointer-events:none;
 background:radial-gradient(120% 76% at 50% 40%, rgba(0,0,0,0) 30%, rgba(0,0,0,.82) 100%);}
</style>
<div class="c">
<svg width="1024" height="1536" viewBox="0 0 1024 1536">
 <defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="#131827"/>
    <stop offset="42%"  stop-color="#0d1118"/>
    <stop offset="100%" stop-color="#07080b"/>
  </linearGradient>
  <radialGradient id="bloom" cx="50%" cy="36%" r="58%">
    <stop offset="0%"   stop-color="#d8b45a" stop-opacity=".18"/>
    <stop offset="100%" stop-color="#d8b45a" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="up" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="#c20f16" stop-opacity=".66"/>
    <stop offset="100%" stop-color="#c20f16" stop-opacity=".03"/>
  </linearGradient>
  <linearGradient id="dn" x1="0" y1="1" x2="0" y2="0">
    <stop offset="0%"   stop-color="#0e8ab5" stop-opacity=".55"/>
    <stop offset="100%" stop-color="#0e8ab5" stop-opacity=".03"/>
  </linearGradient>
 </defs>
 <rect width="1024" height="1536" fill="url(#sky)"/>
 <rect width="1024" height="1536" fill="url(#bloom)"/>
 __QUARTERS__
 <clipPath id="above"><rect x="0" y="0" width="1024" height="__MID__"/></clipPath>
 <clipPath id="below"><rect x="0" y="__MID__" width="1024" height="1536"/></clipPath>
 <g clip-path="url(#above)"><path d="__AREA__" fill="url(#up)"/></g>
 <g clip-path="url(#below)"><path d="__AREA__" fill="url(#dn)"/></g>
 <path d="M64 __MID__ L960 __MID__" stroke="#f4f1ea" stroke-opacity=".28" stroke-width="2"/>
 <path d="__LINE__" fill="none" stroke="#f4f1ea" stroke-width="5"
       stroke-linejoin="round" stroke-linecap="round"/>
 __FLIPS__
</svg>
<div class="wk">__WK__</div>
<div class="grain"></div>
<div class="vig"></div>
</div>"""


OG = """<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@600;700&display=swap');
:root{--red:#c20f16;--ink:#0b0b0f;--cream:#f4f1ea;--gold:#d8b45a;--blue:#0e8ab5;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;margin:0;}
html,body{width:1200px;height:630px;overflow:hidden;background:#0b0b0f;
 font-family:Georgia,'Times New Roman',serif;color:var(--cream);}
.c{position:relative;width:1200px;height:630px;overflow:hidden;background:#0b0b0f;
 background-size:cover;background-position:center;__PHOTO__
 border-top:9px solid var(--red);border-bottom:9px solid var(--red);}
svg{position:absolute;inset:0;}
.l{position:absolute;left:0;top:0;bottom:0;width:640px;z-index:9;
 padding:46px 34px 40px 54px;display:flex;flex-direction:column;
 background:linear-gradient(90deg,#0b0b0f 0%,#0b0b0f 62%,rgba(11,11,15,.92) 82%,
 rgba(11,11,15,0) 100%);}
.flag{font-family:var(--sans);font-size:11.5px;font-weight:900;letter-spacing:.24em;
 text-transform:uppercase;color:var(--red);}
h1{font-size:52px;line-height:1.0;letter-spacing:-.022em;font-weight:900;margin-top:14px;
 max-width:16ch;}
.dek{font-style:italic;color:#b9b6ae;font-size:18px;line-height:1.38;margin-top:14px;
 max-width:30ch;}
.st{margin-top:auto;display:flex;gap:30px;}
.st .k{font-family:var(--sans);font-size:9px;font-weight:800;letter-spacing:.14em;
 text-transform:uppercase;color:#8d8880;}
.st .v{font-size:28px;font-weight:900;line-height:1.1;font-variant-numeric:tabular-nums;}
.st .v b{color:var(--gold);font-weight:900;}
</style>
<div class="c">
<svg width="1200" height="630" viewBox="0 0 1200 630">
 <defs>
  <linearGradient id="up" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#c20f16" stop-opacity=".72"/>
    <stop offset="100%" stop-color="#c20f16" stop-opacity=".04"/></linearGradient>
  <linearGradient id="dn" x1="0" y1="1" x2="0" y2="0">
    <stop offset="0%" stop-color="#0e8ab5" stop-opacity=".60"/>
    <stop offset="100%" stop-color="#0e8ab5" stop-opacity=".04"/></linearGradient>
  <radialGradient id="bl" cx="62%" cy="46%" r="52%">
    <stop offset="0%" stop-color="#d8b45a" stop-opacity=".16"/>
    <stop offset="100%" stop-color="#d8b45a" stop-opacity="0"/></radialGradient>
 </defs>
 <rect width="1200" height="630" fill="#0b0b0f"/>
 <rect width="1200" height="630" fill="url(#bl)"/>
 <clipPath id="a"><rect x="0" y="0" width="1200" height="__MID__"/></clipPath>
 <clipPath id="b"><rect x="0" y="__MID__" width="1200" height="630"/></clipPath>
 <g clip-path="url(#a)"><path d="__AREA__" fill="url(#up)"/></g>
 <g clip-path="url(#b)"><path d="__AREA__" fill="url(#dn)"/></g>
 <path d="M40 __MID__ L1160 __MID__" stroke="#f4f1ea" stroke-opacity=".26" stroke-width="2"/>
 <path d="__LINE__" fill="none" stroke="#f4f1ea" stroke-width="4"
       stroke-linejoin="round" stroke-linecap="round"/>
 __FLIPS__
</svg>
<div class="l">
  <div class="flag">The Week __WK__ Issue</div>
  <h1>__HL__</h1>
  <div class="dek">__DEK__</div>
  <div class="st">
    __STATS__
  </div>
</div>
</div>"""


GAME_STATS = ('<div><div class="k">Final</div><div class="v">{ws}<b>&ndash;</b>{ls}</div></div>'
              '<div><div class="k">Lead changes</div><div class="v">{nf}</div></div>')
FEAT_STATS = ('<div><div class="k">{k1}</div><div class="v">{v1}</div></div>'
              '<div><div class="k">{k2}</div><div class="v">{v2}</div></div>')


def week_means(season, upto):
    """League scoring average per week. The injury story's own evidence."""
    import glob as _g
    out = []
    for q in sorted(_g.glob(os.path.join(WDIR, f'{season}-w?.json'))):
        wk = int(_re.search(r'w(\d)\.json', os.path.basename(q)).group(1))
        if wk > upto:
            continue
        d = json.load(open(q, encoding='utf-8'))
        pts = [t['points'] for gm in d['games'] for t in gm['teams']]
        out.append((wk, sum(pts) / len(pts)))
    return out


def feature_card(season, week, feat, art=''):
    """The share card when the cover leads on a feature rather than a game.

    The margin trace belongs to one game. Running it behind a headline about
    the whole week would be a picture of the wrong thing -- so the series is
    swapped for the one the feature actually argues from: the league's scoring
    average, week by week, against its own season mean. Five weeks hovering and
    then a drop is the story, and it draws itself.
    """
    means = week_means(season, week)
    base = sum(v for _, v in means) / len(means)
    n = max(len(means) - 1, 1)
    pts = [(i / n, v - base) for i, (_, v) in enumerate(means)]
    x0, w = 40, 1200 - 80
    y0, h = 150, 330
    line, area, mid = curve(pts, w, h, x0, y0)
    hurt = injured_count(season, week)
    doc = (OG.replace('__AREA__', area).replace('__LINE__', line)
             .replace('__MID__', f'{mid:.1f}').replace('__FLIPS__', '')
             .replace('__WK__', str(week))
             .replace('__HL__', ad.esc(feat.get('headline', '')))
             .replace('__DEK__', ad.esc(feat.get('dek', '')))
             .replace('__STATS__', FEAT_STATS.format(
                 k1='Points a team', v1=f'{means[-1][1]:.1f}',
                 k2='Injured men', v2=str(hurt)))
             .replace('__PHOTO__', ''))
    out = os.path.join(ROOT, f'scfl-week-{week}-og.jpg')
    ad.shoot(doc, out, f'wk{week}-og', 1200, 630)
    print(f'  wrote {os.path.basename(out)} (feature card: '
          f'{means[-1][1]:.1f} a team, {hurt} injured)')


def injured_count(season, week):
    """Men carrying a designation a manager would shelve. Questionable is not
    one, exactly as everywhere else this desk counts injuries."""
    d = json.load(open(os.path.join(WDIR, f'{season}-w{week}.json'), encoding='utf-8'))
    seen = set()
    for gm in d['games']:
        for t in gm['teams']:
            for key in ('starters', 'bench', 'reserve'):
                for pl in t.get(key) or []:
                    if pl.get('injury_status') and pl['injury_status'] != 'Questionable':
                        seen.add(pl['name'])
    return len(seen)


def og_card(season, week, g, lead_story, pts, flips_t, art=''):
    """The link preview. Unlike the cover, nothing is composited on top of this
    one, so it carries the headline and the score itself -- a share card with no
    words is just a smear of colour in a chat window.

    When the week has a photograph, the card is the photograph. The margin curve
    behind it is the drawn cover's argument, not the issue's, and running it on
    the card while the cover was a stadium meant the link previewed as one
    magazine and opened as another.
    """
    x0, w = 40, 1200 - 80
    y0, h = 150, 330
    line, area, mid = curve(pts, w, h, x0, y0)
    flips = ''.join(
        f'<circle cx="{x0 + w*t:.1f}" cy="{mid:.1f}" r="6" fill="#0b0b0f" '
        f'stroke="#d8b45a" stroke-width="3"/>' for t in flips_t)
    s = lead_story
    doc = (OG.replace('__AREA__', area).replace('__LINE__', line)
             .replace('__MID__', f'{mid:.1f}').replace('__FLIPS__', flips)
             .replace('__WK__', str(week))
             .replace('__HL__', ad.esc(s.get('headline', '')))
             .replace('__DEK__', ad.esc(s.get('dek', '')))
             .replace('__STATS__', GAME_STATS.format(
                 ws=f"{s['score'][0]:.2f}", ls=f"{s['score'][1]:.2f}",
                 nf=g['lead_changes'])))
    if art:
        from PIL import Image as _I
        aw, ah = _I.open(os.path.join(ROOT, art)).size
        tall = ah / aw >= 1.1
        if tall:
            doc = (OGP.replace('__WK__', str(week))
                      .replace('__HL__', ad.esc(s.get('headline', '')))
                      .replace('__STATS__', GAME_STATS.format(
                          ws=f"{s['score'][0]:.2f}", ls=f"{s['score'][1]:.2f}",
                          nf=g['lead_changes'])))
        doc = doc.replace('__PHOTO__', f"background-image:url('{data_uri(art, tall)}');")
        if not tall:
            doc = _re.sub(r'<svg width="1200".*?</svg>', '', doc, flags=_re.S)
    else:
        doc = doc.replace('__PHOTO__', '')
    out = os.path.join(ROOT, f'scfl-week-{week}-og.jpg')
    ad.shoot(doc, out, f'wk{week}-og', 1200, 630)
    print(f'  wrote {os.path.basename(out)}' + (f' from {art}' if art else ''))


def build(season, week, art='', inset='', card=''):
    rp = json.load(open(os.path.join(WDIR, f'{season}-w{week}-replay.json'), encoding='utf-8'))
    lead, stories, cover, feats = 0, [], {}, []
    for cand in (f'{season}-w{week}-written.json', f'{season}-w{week}-stories.json'):
        p = os.path.join(WDIR, cand)
        if os.path.exists(p):
            d = json.load(open(p, encoding='utf-8'))
            lead, stories = d.get('lead', 0), d.get('stories', [])
            cover = d.get('cover') or {}
            feats = d.get('features') or []
            break
    g = rp['games'][lead]

    # margin from the winner's point of view, so the red on the cover is theirs
    wi = 0 if g['teams'][0]['final'] >= g['teams'][1]['final'] else 1
    pts = [(0.0, 0.0)]
    for e in g['timeline']:
        t = min(1.0, max(0.0, e['fc']['sec'] / 3600))
        pts.append((t, e['lead'] if wi == 0 else -e['lead']))

    x0, w = 64, W - 128
    y0, h = H * 0.235, H * 0.33
    line, area, mid = curve(pts, w, h, x0, y0)
    flips = ''.join(
        f'<circle cx="{x0 + w*t:.1f}" cy="{mid:.1f}" r="7" fill="#0b0b0f" '
        f'stroke="#d8b45a" stroke-width="3"/>' for t in crossings(pts))
    quarters = ''.join(
        f'<path d="M{x0 + w*k/4:.0f} {y0-26:.0f} L{x0 + w*k/4:.0f} {y0+h+26:.0f}" '
        f'stroke="#f4f1ea" stroke-opacity=".07" stroke-width="2"/>' for k in range(1, 4))

    # A photograph takes both slots or neither. The cover and the share card are
    # the same promise made twice, and the week they disagreed the link
    # previewed as a chart and opened on a stadium.
    out = os.path.join(ROOT, f'scfl-week-{week}-cover.jpg')
    if art:
        import importlib.util as _iu
        _s = _iu.spec_from_file_location('cc', os.path.join(ROOT, 'scripts', 'compose_cover.py'))
        cc = _iu.module_from_spec(_s); _s.loader.exec_module(cc)
        cc.compose(art, os.path.basename(out), inset=inset)
    else:
        doc = (COVER.replace('__QUARTERS__', quarters)
                    .replace('__AREA__', area).replace('__LINE__', line)
                    .replace('__MID__', f'{mid:.1f}').replace('__FLIPS__', flips)
                    .replace('__WK__', str(week)))
        ad.shoot(doc, out, f'wk{week}-cover', W, H)
        print(f'  wrote {os.path.basename(out)} - {len(crossings(pts))} lead changes drawn')
    # The card follows whatever the cover leads on, or the link previews as one
    # magazine and opens as another.
    if cover.get('from') == 'feature' and feats:
        feature_card(season, week, feats[cover.get('index', 0)], card or art)
    elif stories:
        og_card(season, week, g, stories[lead], pts, crossings(pts), card or art)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, required=True)
    ap.add_argument('--season', default='2026')
    ap.add_argument('--art', default='',
                    help="the week's photograph; drives the cover and the card")
    ap.add_argument('--inset', default='',
                    help='a second picture, boxed in the top right of the cover')
    ap.add_argument('--card', default='',
                    help='source for the share card when --art will not crop to '
                         '1200x630 -- a portrait figure loses his face behind the '
                         "card's headline panel. Defaults to --art.")
    a = ap.parse_args()
    build(a.season, a.week, a.art, a.inset, a.card)


if __name__ == '__main__':
    main()
