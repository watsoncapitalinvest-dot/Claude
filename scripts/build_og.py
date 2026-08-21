#!/usr/bin/env python3
"""Render an issue's preview card from its own magazine cover.

    python3 scripts/build_og.py kickoff-2026

The card IS the cover -- red frame, wordmark panel, issue seal, hook,
coverlines and shield -- flattened to a 1200x1800 JPG, the same as
draft-issue-og.jpg. Screenshots the built issue page's .magcover element,
so the card can never drift from the cover: change a coverline, rebuild,
and the preview changes with it.

Run scripts/build_issue.py first.
"""
import importlib.util, json, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BROWSER = '/opt/pw-browsers/chromium'
W, H = 1200, 1800

spec = importlib.util.spec_from_file_location('bi', os.path.join(ROOT, 'scripts', 'build_issue.py'))
bi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bi)

# Two things here are load-bearing, both learned the hard way.
#
# 1. deviceScaleFactor must stay 1. At 2 the cover's background art never paints
#    and the capture comes out as the page's bare grey ground -- silently, with no
#    error. elementHandle.screenshot(), screenshot({clip}) and a full-viewport
#    capture all reproduce it, and forcing an Image().decode() first does not help.
#    Full size is reached with CSS zoom instead, which scales the whole cover --
#    art, type and all -- so proportions match the cover exactly.
# 2. Capture the viewport and crop in PIL rather than screenshotting the element.
SHOT = """const {chromium}=require('playwright');
(async()=>{
const b=await chromium.launch({executablePath:'%s'});
const p=await b.newPage({viewport:{width:1400,height:2000},deviceScaleFactor:1});
await p.goto('file://%s',{waitUntil:'load'});
await p.waitForTimeout(800);
const el=await p.$('.magcover');
if(!el){console.error('no .magcover on the page');process.exit(2);}
await p.addStyleTag({content:'.cover-page{zoom:%d !important}'});
await p.waitForTimeout(700);
const box=await el.boundingBox();
console.log(JSON.stringify(box));
await p.screenshot({path:'%s'});
await b.close();
})();"""
ZOOM = 2


def build(key):
    cfg = bi.ISSUES[key]
    page = os.path.join(ROOT, cfg['out'])
    if not os.path.exists(page):
        sys.exit(f"{cfg['out']} not built yet -- run scripts/build_issue.py first")

    raw = os.path.join(tempfile.gettempdir(), f'og-{key}.png')
    js = os.path.join(tempfile.gettempdir(), f'og-{key}.js')
    open(js, 'w').write(SHOT % (BROWSER, page, ZOOM, raw))
    try:
        env = dict(os.environ, NODE_PATH='/opt/node22/lib/node_modules')
        out = subprocess.run(['node', js], check=True, env=env, cwd=ROOT,
                             capture_output=True, text=True)
        box = json.loads(out.stdout.strip().splitlines()[-1])
        from PIL import Image
        im = Image.open(raw).convert('RGB').crop((
            round(box['x']), round(box['y']),
            round(box['x'] + box['width']), round(box['y'] + box['height'])))
        print(f"  cover captured at {im.width}x{im.height}")
        if im.size != (W, H):
            im = im.resize((W, H), Image.LANCZOS)
        dst = os.path.join(ROOT, cfg['og'])
        im.save(dst, 'JPEG', quality=88, optimize=True, progressive=True)
        kb = os.path.getsize(dst) // 1024
        if kb < 120:
            sys.exit(f'  !! {cfg["og"]} came out {kb}kb -- the art almost certainly '
                     f'did not render; not shipping a blank cover')
        print(f"wrote {cfg['og']} {W}x{H} {kb}kb | {cfg['hook']}")
    finally:
        for f in (js, raw):
            if os.path.exists(f):
                os.remove(f)


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'kickoff-2026')
