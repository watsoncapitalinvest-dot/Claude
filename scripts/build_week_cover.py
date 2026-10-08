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
import argparse, importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')
_s = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts', 'build_addendum.py'))
ad = importlib.util.module_from_spec(_s); sys.modules['ad'] = ad; _s.loader.exec_module(ad)

W, H = 1024, 1536


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
    """Where the lead actually changed hands, for the markers."""
    out = []
    for a, b in zip(points, points[1:]):
        if (a[1] > 0) != (b[1] > 0) and abs(b[1]) > 0.01:
            out.append(b[0])
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
    <div><div class="k">Final</div><div class="v">__WS__<b>&ndash;</b>__LS__</div></div>
    <div><div class="k">Lead changes</div><div class="v">__NF__</div></div>
  </div>
</div>
</div>"""


def og_card(season, week, g, lead_story, pts, flips_t):
    """The link preview. Unlike the cover, nothing is composited on top of this
    one, so it carries the headline and the score itself -- a share card with no
    words is just a smear of colour in a chat window."""
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
             .replace('__WS__', f"{s['score'][0]:.2f}")
             .replace('__LS__', f"{s['score'][1]:.2f}")
             .replace('__NF__', str(g['lead_changes'])))
    out = os.path.join(ROOT, f'scfl-week-{week}-og.jpg')
    ad.shoot(doc, out, f'wk{week}-og', 1200, 630)
    print(f'  wrote {os.path.basename(out)}')


def build(season, week):
    rp = json.load(open(os.path.join(WDIR, f'{season}-w{week}-replay.json'), encoding='utf-8'))
    lead, stories = 0, []
    for cand in (f'{season}-w{week}-written.json', f'{season}-w{week}-stories.json'):
        p = os.path.join(WDIR, cand)
        if os.path.exists(p):
            d = json.load(open(p, encoding='utf-8'))
            lead, stories = d.get('lead', 0), d.get('stories', [])
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

    doc = (COVER.replace('__QUARTERS__', quarters)
                .replace('__AREA__', area).replace('__LINE__', line)
                .replace('__MID__', f'{mid:.1f}').replace('__FLIPS__', flips)
                .replace('__WK__', str(week)))
    out = os.path.join(ROOT, f'scfl-week-{week}-cover.jpg')
    ad.shoot(doc, out, f'wk{week}-cover', W, H)
    print(f'  wrote {os.path.basename(out)} - {len(crossings(pts))} lead changes drawn')
    if stories:
        og_card(season, week, g, stories[lead], pts, crossings(pts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, required=True)
    ap.add_argument('--season', default='2026')
    a = ap.parse_args()
    build(a.season, a.week)


if __name__ == '__main__':
    main()
