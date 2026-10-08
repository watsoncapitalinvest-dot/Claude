#!/usr/bin/env python3
"""Draw the weekly cover, instead of waiting on an image model.

    python3 scripts/build_week_cover.py --week 4

Claude cannot make a photograph. It can set type, and a designed typographic
cover is a real magazine cover -- the kind an art director reaches for when the
story is a number rather than a face. This builds one from the week's own
result: the losing and winning scores, the man who decided it, the week itself
set enormous.

Rendered through the same Chromium pipeline as every share card in this repo,
at 1024x1536 so it drops straight into the slot build_issue.py already expects.
If John's graphics AI later supplies a photograph, it overwrites this file and
nothing else changes.
"""
import argparse, importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')
_s = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts', 'build_addendum.py'))
ad = importlib.util.module_from_spec(_s); sys.modules['ad'] = ad; _s.loader.exec_module(ad)
E = ad.esc

COVER = """<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@700&display=swap');
:root{--red:#c20f16;--ink:#0b0b0f;--cream:#f4f1ea;--gold:#d8b45a;}
*{box-sizing:border-box;margin:0;}
html,body{width:1024px;height:1536px;overflow:hidden;background:var(--ink);
 font-family:Georgia,'Times New Roman',serif;color:var(--cream);}
.c{position:relative;width:1024px;height:1536px;overflow:hidden;
 background:
  radial-gradient(130% 80% at 50% 26%, #2b2f3a 0%, #14161d 42%, #0b0b0f 78%),
  var(--ink);}
/* floodlight haze across the upper third, where the masthead will sit */
.haze{position:absolute;left:0;right:0;top:0;height:46%;
 background:radial-gradient(60% 100% at 50% 0%, rgba(216,180,90,.26) 0%,
  rgba(216,180,90,.07) 45%, rgba(0,0,0,0) 72%);}
/* turf band at the foot, with yard lines running to a vanishing point */
.turf{position:absolute;left:-10%;right:-10%;bottom:0;height:38%;
 background:linear-gradient(180deg,#10261a 0%,#0c1c13 55%,#070d09 100%);
 transform:perspective(900px) rotateX(46deg);transform-origin:bottom center;}
.turf i{position:absolute;top:0;bottom:0;width:3px;background:rgba(244,241,234,.16);}
.band{position:absolute;left:0;right:0;top:30%;height:34%;
 background:linear-gradient(180deg,rgba(11,11,15,0) 0%,rgba(11,11,15,.55) 38%,
  rgba(11,11,15,.92) 100%);}
/* the week, set enormous and cropped by its own frame */
.wk{position:absolute;left:0;right:0;top:28%;text-align:center;
 font-family:'Oswald',Impact,sans-serif;font-weight:700;font-size:430px;line-height:.78;
 letter-spacing:-18px;color:transparent;
 -webkit-text-stroke:3px rgba(216,180,90,.46);}
.wknum{position:absolute;left:0;right:0;top:30%;text-align:center;
 font-family:'Oswald',Impact,sans-serif;font-weight:700;font-size:360px;line-height:.8;
 letter-spacing:-14px;color:var(--cream);
 text-shadow:0 10px 50px rgba(0,0,0,.95),0 2px 0 rgba(0,0,0,.6);}
.rule{position:absolute;left:50%;transform:translateX(-50%);top:50.5%;
 width:210px;height:5px;background:var(--red);}
.score{position:absolute;left:0;right:0;top:50%;text-align:center;
 font-family:'Oswald',Impact,sans-serif;font-weight:700;font-size:40px;letter-spacing:2px;
 text-transform:uppercase;color:var(--cream);}
.score b{color:var(--gold);}
.score span{color:rgba(244,241,234,.55);font-size:30px;}
.who{position:absolute;left:0;right:0;top:55.4%;text-align:center;
 font-style:italic;font-size:30px;color:rgba(244,241,234,.80);}
.vig{position:absolute;inset:0;pointer-events:none;
 background:radial-gradient(120% 78% at 50% 44%, rgba(0,0,0,0) 36%, rgba(0,0,0,.72) 100%);}
</style>
<div class="c">
  <div class="haze"></div>
  <div class="turf">__LINES__</div>
  <div class="band"></div>
  <div class="wk">__BIGWK__</div>
  <div class="wknum">__BIGWK__</div>
  <div class="rule"></div>
  <div class="vig"></div>
</div>"""


def build(season, week):
    p = os.path.join(WDIR, f'{season}-w{week}-stories.json')
    if not os.path.exists(p):
        sys.exit(f'no {p} -- run scripts/write_week.py --week {week} first')
    d = json.load(open(p, encoding='utf-8'))
    s = d['stories'][d['lead']]
    rp = json.load(open(os.path.join(WDIR, f'{season}-w{week}-replay.json'), encoding='utf-8'))
    g = rp['games'][d['lead']]
    go = g.get('go_ahead')
    who = ''
    if go and not go['residual']:
        q = go['fc']['qtr']
        who = f'{go["player"]} settled it in the {["first","second","third","fourth"][q-1]}'

    lines = ''.join(f'<i style="left:{x}%"></i>' for x in range(4, 100, 8))
    doc = (COVER.replace('__LINES__', lines)
                .replace('__BIGWK__', str(week))
                )
    # the score, the headline and the lead man are all composited on top by
    # build_issue.py. Drawing them here too put each of them on the cover twice
    # -- the same rule the art brief gives the graphics AI applies to this.
    _ = (s, who)
    out = os.path.join(ROOT, f'scfl-week-{week}-cover.jpg')
    ad.shoot(doc, out, f'wk{week}-cover', 1024, 1536)
    print(f'  wrote {os.path.basename(out)}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, required=True)
    ap.add_argument('--season', default='2026')
    a = ap.parse_args()
    build(a.season, a.week)


if __name__ == '__main__':
    main()
