#!/usr/bin/env python3
"""Give a page a share card when it hasn't got one of its own.

    python3 scripts/build_fallback_card.py                 # every page missing one
    python3 scripts/build_fallback_card.py ir-watch.html   # just this one

Pages built by a dedicated builder make their own card out of their own
material -- the issue cards are the cover, the record book's card is the top
six. This is for the rest: the ones that declare an og:image nobody ever built,
or declare none at all, and so arrive in any chat or feed as a grey rectangle.

Everything on the card comes off the page itself -- the kicker, the title, the
share blurb -- so a plain card cannot say something the page does not. It is
deliberately typographic. A page that deserves better art should get a real
builder; this exists so that nothing is unsendable while it waits.

A page that already has a card on disk is left alone unless --force is passed,
because overwriting somebody's real artwork with grey type would be worse than
the problem.
"""
import importlib.util, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts', 'build_addendum.py'))
ad = importlib.util.module_from_spec(_s); sys.modules['ad'] = ad; _s.loader.exec_module(ad)
E = ad.esc

TITLE = re.compile(r'<title>([^<]*)</title>')
DESC = re.compile(r'og:description"\s+content="([^"]*)"')
IMG = re.compile(r'og:image"\s+content="([^"]*)"')
KICKER = re.compile(r'scfl:kicker"\s+content="([^"]*)"')

CARD = """<style>
:root{--red:#c20f16;--ink:#17181c;--faint:#9a958c;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;}
*{box-sizing:border-box;margin:0;}
html,body{width:1200px;height:630px;overflow:hidden;background:#efe9de;
 font-family:Georgia,'Times New Roman',serif;color:var(--ink);}
.card{position:relative;width:1200px;height:630px;overflow:hidden;background:#efe9de;
 border-top:9px solid var(--red);border-bottom:9px solid var(--red);
 padding:62px 72px 48px;display:flex;flex-direction:column;}
.flag{font-family:var(--sans);font-size:12px;font-weight:900;letter-spacing:.22em;
 text-transform:uppercase;color:var(--red);}
h1{font-size:__FS__px;line-height:1.02;letter-spacing:-.026em;font-weight:900;margin-top:20px;
 max-width:21ch;}
.rule{width:64px;height:3px;background:var(--red);margin:26px 0 22px;}
.dek{font-style:italic;color:#4b4b52;font-size:22px;line-height:1.4;max-width:46ch;}
.ft{margin-top:auto;font-family:var(--sans);font-size:12px;font-weight:800;
 letter-spacing:.16em;text-transform:uppercase;color:var(--faint);}
</style>
<div class="card">
 <div class="flag">__FLAG__</div>
 <h1>__HEAD__</h1>
 <div class="rule"></div>
 <div class="dek">__DEK__</div>
 <div class="ft">SCFL NewsRoom</div>
</div>"""


def card_for(rel, force=False):
    path = os.path.join(ROOT, rel)
    text = open(path, encoding='utf-8', errors='replace').read(6000)
    tm = TITLE.search(text)
    if not tm or not tm.group(1).strip():
        return None                                  # not an article
    # where the page says its card lives; if it says nothing, name one after it
    im = IMG.search(text)
    folder = os.path.dirname(rel)
    if im:
        fn = im.group(1).rsplit('/', 1)[-1]
        out_rel = os.path.join(folder, fn) if folder else fn
    else:
        out_rel = rel[:-5] + '-og.jpg'
    out = os.path.join(ROOT, out_rel)
    if os.path.exists(out) and not force:
        return None

    title = tm.group(1).strip()
    # the tab title carries the masthead; the card already says SCFL NewsRoom
    head = re.split(r'\s+(?:&mdash;|&ndash;|—|–|\|)\s+', title)[0].strip()
    dek = (DESC.search(text).group(1).strip() if DESC.search(text) else '')
    km = KICKER.search(text)
    flag = km.group(1).split('&middot;')[0].strip() if km else 'The NewsRoom'
    plain = re.sub(r'&[a-z]+;|<[^>]+>', '', head)
    fs = 72 if len(plain) <= 22 else 60 if len(plain) <= 34 else 50
    doc = (CARD.replace('__FS__', str(fs)).replace('__FLAG__', E(flag))
               .replace('__HEAD__', head).replace('__DEK__', dek or E(title)))
    ad.shoot(doc, out, 'fallback-card')
    return out_rel


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    force = '--force' in sys.argv
    if not args:
        args = sorted(f for f in os.listdir(ROOT)
                      if f.endswith('.html') and f not in ('index.html', 'scfl-index.html'))
        for sub in ('jeopardy', 'tradewar'):
            p = f'{sub}/index.html'
            if os.path.exists(os.path.join(ROOT, p)):
                args.append(p)
    made = []
    for rel in args:
        if not os.path.exists(os.path.join(ROOT, rel)):
            print(f'  ! no such page: {rel}')
            continue
        r = card_for(rel, force)
        if r:
            made.append(r)
            print(f'  {rel} -> {r}')
    print(f'{len(made)} card{"" if len(made) == 1 else "s"} built')


if __name__ == '__main__':
    main()
