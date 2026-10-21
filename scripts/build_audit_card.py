#!/usr/bin/env python3
"""The Trade Audit's share card, made from its own cover.

    python3 scripts/build_audit_card.py

A page with artwork should not arrive in a chat as a grey typographic
rectangle. build_fallback_card.py exists for pages with nothing to show; this
one crops the cover, darkens a band for the type, and sets the masthead, the
headline and the one number the piece turns on.

1200x630 because that is what every chat app crops to.
"""
import importlib.util, json, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = 'scfl-trade-audit-art.jpg'
WM = 'wordmark-alt-words.png'
OUT = 'scfl-trade-audit-og.jpg'
W, H = 1200, 630
SERIF = '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'
SANS = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'

_c = importlib.util.spec_from_file_location('cc', os.path.join(ROOT, 'scripts',
                                                               'compose_cover.py'))
cc = importlib.util.module_from_spec(_c); _c.loader.exec_module(cc)


def wrap(draw, text, font, width):
    out, line = [], ''
    for w in text.split():
        t = (line + ' ' + w).strip()
        if draw.textlength(t, font=font) <= width or not line:
            line = t
        else:
            out.append(line); line = w
    if line:
        out.append(line)
    return out


def build():
    # the courtroom reads best slightly above centre: the bench and the dragon
    # sit high in the frame and the gallery at the bottom is just heads
    im = cc.band(ART, W, H, at=0.30)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([0, 0, W, H], fill=(8, 7, 6, 70))
    # A bed for the type: opaque at the very bottom, fading out going up. The
    # first version had the ramp the other way round, which drew a hard black
    # line across the middle of the picture and left the headline sitting on
    # the gallery's faces.
    bed = 330
    for i in range(bed):
        a = int(236 * (1 - i / bed) ** 1.4)
        d.rectangle([0, H - i - 1, W, H - i], fill=(8, 7, 6, a))

    wm = Image.open(os.path.join(ROOT, WM)).convert('RGBA')
    ww = 330
    wm = wm.resize((ww, round(wm.size[1] * ww / wm.size[0])), Image.LANCZOS)
    im.paste(wm, (48, 40), wm)

    art = {x['id']: x for x in json.load(open(os.path.join(ROOT, 'investigations.json'),
                                              encoding='utf-8'))['investigations']}['trade-audit']
    hf = ImageFont.truetype(SERIF, 70)
    sf = ImageFont.truetype(SANS, 24)
    lines = wrap(d, art['headline'], hf, W - 96)
    y = H - 52 - len(lines) * 78 - 46
    for ln in lines:
        d.text((48, y), ln, font=hf, fill=(255, 253, 251)); y += 78
    d.text((48, y + 8), 'EVERY DEAL IN THE DYNASTY LEDGER, 2021-2026, PRICED AT THE '
                        'SEASON IT MOVED IN', font=sf, fill=(216, 180, 90))

    p = os.path.join(ROOT, OUT)
    im.convert('RGB').save(p, quality=88, optimize=True)
    print(f'  card {OUT} {W}x{H} ({os.path.getsize(p)//1024}kb)')


if __name__ == '__main__':
    build()
