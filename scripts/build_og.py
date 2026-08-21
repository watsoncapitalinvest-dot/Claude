#!/usr/bin/env python3
"""Render an issue's share card.

    python3 scripts/build_og.py kickoff-2026

House format, matching scfl-postdraft-og.jpg: 1200x630, red bars top and
bottom, the issue's hook in white serif at the bottom left, and a line of
caps beneath it with red middots. Reads the hook straight out of
build_issue.ISSUES so the card and the cover never drift apart.

Rendered in the browser rather than drawn with PIL so the type matches the
site's own font stack.
"""
import importlib.util, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8991
BROWSER = '/opt/pw-browsers/chromium'

spec = importlib.util.spec_from_file_location('bi', os.path.join(ROOT, 'scripts', 'build_issue.py'))
bi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bi)

# The strip of the cover art the card crops to, as a background-position Y.
FOCUS = {'kickoff-2026': '34%'}

CARD = """<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1200px;height:630px;overflow:hidden}}
.card{{position:relative;width:1200px;height:630px;overflow:hidden;background:#0b0f14;
 border-top:10px solid #e11b22;border-bottom:10px solid #e11b22}}
.art{{position:absolute;inset:0;background:url('{art}') center {focus}/cover no-repeat}}
.scrim{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(6,8,10,.30) 0%,
 rgba(6,8,10,0) 22%,rgba(6,8,10,.18) 48%,rgba(6,8,10,.80) 78%,rgba(6,8,10,.96) 100%)}}
.txt{{position:absolute;left:52px;right:52px;bottom:34px}}
.hook{{font-family:Georgia,'Liberation Serif','Times New Roman',serif;font-weight:700;
 font-size:{size}px;line-height:.95;letter-spacing:-1.5px;color:#fff;
 text-shadow:0 3px 22px rgba(0,0,0,.95),0 1px 3px rgba(0,0,0,.9)}}
.line{{margin-top:16px;font-family:Helvetica,'Liberation Sans',Arial,sans-serif;font-weight:700;
 font-size:21px;letter-spacing:.5px;text-transform:uppercase;color:#f3f5f8;
 text-shadow:0 2px 10px rgba(0,0,0,.98)}}
.line i{{font-style:normal;color:#ff5442;padding:0 10px}}
</style>
<div class="card"><div class="art"></div><div class="scrim"></div>
<div class="txt"><div class="hook">{hook}</div><div class="line">{line}</div></div></div>"""

SHOT = """const {{chromium}}=require('playwright');
(async()=>{{
const b=await chromium.launch({{executablePath:'%s'}});
const p=await b.newPage({{viewport:{{width:1200,height:630}},deviceScaleFactor:2}});
await p.goto('http://127.0.0.1:%d/{tmp}',{{waitUntil:'networkidle'}});
await p.waitForTimeout(600);
await p.screenshot({{path:'{out}'}});
await b.close();
}})();""" % (BROWSER, PORT)


def build(key):
    cfg = bi.ISSUES[key]
    art = cfg['art']
    if not os.path.exists(os.path.join(ROOT, art)):
        sys.exit(f'cover art {art} not present — nothing to make a card from')

    line = '<i>&middot;</i>'.join(cfg['ogline'])
    hook = cfg['hook']
    size = 66 if len(hook) <= 28 else 56

    tmp = '.og-tmp.html'
    open(os.path.join(ROOT, tmp), 'w', encoding='utf-8').write(
        CARD.format(art=art, focus=FOCUS.get(key, 'center'), hook=hook, line=line, size=size))
    raw = os.path.join(tempfile.gettempdir(), f'og-{key}.png')
    js = os.path.join(tempfile.gettempdir(), f'og-{key}.js')
    open(js, 'w').write(SHOT.format(tmp=tmp, out=raw))
    try:
        env = dict(os.environ, NODE_PATH='/opt/node22/lib/node_modules')
        subprocess.run(['node', js], check=True, env=env, cwd=ROOT)
        from PIL import Image
        im = Image.open(raw).convert('RGB').resize((1200, 630), Image.LANCZOS)
        out = os.path.join(ROOT, cfg['og'])
        im.save(out, 'JPEG', quality=88, optimize=True)
        print(f"wrote {cfg['og']} 1200x630 | {hook}")
    finally:
        for f in (os.path.join(ROOT, tmp), js, raw):
            if os.path.exists(f):
                os.remove(f)


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'kickoff-2026')
