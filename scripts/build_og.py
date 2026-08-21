#!/usr/bin/env python3
"""Render an issue's preview card from its own magazine cover.

    python3 scripts/build_og.py kickoff-2026

The card IS the cover -- red frame, wordmark panel, issue seal, hook,
coverlines and shield -- flattened to a 1200x1800 JPG, the same as
draft-issue-og.jpg.

Lifts the cover markup and the stylesheet straight out of the built issue and
renders that alone, so the card cannot drift from the cover: change a
coverline, rebuild, and the preview changes with it. Rendering the cover in
isolation rather than screenshotting it inside the issue matters -- see the
capture notes below.

Run scripts/build_issue.py first.
"""
import importlib.util, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BROWSER = '/opt/pw-browsers/chromium'
W, H = 1200, 1800
ZOOM = 2                      # .magcover is capped at 600px; 600x900 x2 = 1200x1800

spec = importlib.util.spec_from_file_location('bi', os.path.join(ROOT, 'scripts', 'build_issue.py'))
bi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bi)

# Capture notes, both learned the hard way:
#
# 1. deviceScaleFactor must stay 1. At 2 the cover's background art never paints
#    and the capture comes out as bare grey ground -- silently, no error.
#    Full size comes from CSS zoom instead, which scales art and type together.
# 2. Do not screenshot the cover inside the issue page. Chromium stops
#    rasterizing partway down a 37-page document carrying an opener image per
#    article, and the bottom third of the cover comes back blank. Rendering the
#    cover on its own page sidesteps it entirely and is much faster.
PAGE = """<style>%s</style>
<style>
html,body{margin:0;padding:0;width:%dpx;height:%dpx;overflow:hidden;background:#d9d6ce;}
.wrap{zoom:%d;}
.magcover{margin:0 !important;box-shadow:none !important;}
</style>
<div class="wrap">%s</div>"""

SHOT = """const {chromium}=require('playwright');
(async()=>{
const b=await chromium.launch({executablePath:'%s'});
const p=await b.newPage({viewport:{width:%d,height:%d},deviceScaleFactor:1});
await p.goto('file://%s',{waitUntil:'load'});
await p.evaluate(async ()=>{
  await document.fonts.ready;
  const bg=getComputedStyle(document.querySelector('.magcover')).backgroundImage;
  const m=bg.match(/url\\(["']?(.+?)["']?\\)/);
  const urls=Array.from(document.images).map(i=>i.src).concat(m?[m[1]]:[]);
  await Promise.all(urls.map(u=>{const i=new Image();i.src=u;return i.decode().catch(()=>null);}));
});
await p.waitForTimeout(700);
await p.screenshot({path:'%s'});
await b.close();
})();"""


def build(key):
    cfg = bi.ISSUES[key]
    src = os.path.join(ROOT, cfg['out'])
    if not os.path.exists(src):
        sys.exit(f"{cfg['out']} not built yet -- run scripts/build_issue.py first")
    html = open(src, encoding='utf-8').read()

    css = re.search(r'<style>(.*?)</style>', html, re.S)
    cover = re.search(r'<section class="page cover-page">(.*?)</section>', html, re.S)
    if not css or not cover:
        sys.exit(f"could not find the cover or the stylesheet in {cfg['out']}")

    # Same directory as the issue, so the cover art's relative URL still resolves.
    tmp = os.path.join(ROOT, '.og-cover.html')
    open(tmp, 'w', encoding='utf-8').write(
        PAGE % (css.group(1), W, H, ZOOM, cover.group(1)))
    raw = os.path.join(tempfile.gettempdir(), f'og-{key}.png')
    js = os.path.join(tempfile.gettempdir(), f'og-{key}.js')
    open(js, 'w').write(SHOT % (BROWSER, W, H, tmp, raw))
    try:
        env = dict(os.environ, NODE_PATH='/opt/node22/lib/node_modules')
        subprocess.run(['node', js], check=True, env=env, cwd=ROOT, capture_output=True)
        from PIL import Image
        im = Image.open(raw).convert('RGB')
        if im.size != (W, H):
            print(f'  note: captured {im.width}x{im.height}, resizing to {W}x{H}')
            im = im.resize((W, H), Image.LANCZOS)

        # A half-painted capture is still a valid JPG, so check pixels rather than
        # file size. Below the wordmark panel the cover is dark edge to edge, so
        # any real amount of blank there means the render did not finish.
        g = im.convert('L').crop((0, int(H * 0.18), W, H)).resize((100, 150))
        blank = sum(1 for v in g.get_flattened_data() if v > 235) / (100 * 150)
        if blank > 0.03:
            sys.exit(f'  !! {cfg["og"]} is {blank:.0%} blank below the masthead -- '
                     f'the cover rendered only partly; not shipping it')

        dst = os.path.join(ROOT, cfg['og'])
        im.save(dst, 'JPEG', quality=88, optimize=True, progressive=True)
        print(f"wrote {cfg['og']} {W}x{H} {os.path.getsize(dst)//1024}kb "
              f"| {blank:.1%} blank | {cfg['hook']}")
    finally:
        for f in (js, raw, tmp):
            if os.path.exists(f):
                os.remove(f)


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'kickoff-2026')
