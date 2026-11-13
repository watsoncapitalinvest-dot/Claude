#!/usr/bin/env python3
"""The game's title on the menu key art: G.I. JOE / USA DEFENSE with the eagle badge.

    python3 build/make_title.py

Reads mod/Resources/FrontEnd/title_base_hi.png (the key art with no title; made from
title_hi.png the first time this runs), the eagle from art_briefs/returned/ui_remaining,
and the two fonts in fonts/. Writes title_hi.png (the full-colour art the menu draws)
and title.png (its 8-bit twin), and title_word.png (the wordmark alone, for other screens).
John, 13 Nov 2026: the game is "G.I. Joe: USA Defense"; a cleaner, more awesome title,
with the G.I. Joe badging.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
FE = os.path.join(ROOT, 'mod', 'Resources', 'FrontEnd')
STENCIL = os.path.join(ROOT, 'fonts', 'SairaStencilOne-Regular.ttf')
OSWALD = os.path.join(ROOT, 'fonts', 'Oswald[wght].ttf')
EAGLE = os.path.join(ROOT, 'art_briefs', 'returned', 'ui_remaining', '07_battle_buttons', 'icon_special.png')

RED, BLUE, WHITE, GOLD, INK = (200, 24, 32), (22, 52, 120), (250, 248, 240), (232, 185, 35), (12, 14, 18)


def text_layer(size, text, font, fill, stroke, stroke_fill, spacing=0):
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 0
    for ch in text:
        d.text((x + stroke, stroke), ch, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        x += font.getlength(ch) + spacing
    return img.crop(img.getbbox())


def eagle_badge(h):
    """The eagle cut off its olive button face, set on a navy roundel with a red and white rim."""
    e = Image.open(EAGLE).convert('RGB')
    a = np.asarray(e).astype(int)
    bg = np.array([74, 86, 64])
    dist = np.abs(a - bg).sum(axis=2)
    alpha = np.clip((dist - 30) * 6, 0, 255).astype(np.uint8)
    eagle = Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), 'RGBA')
    eagle = eagle.crop(eagle.getbbox())
    s = h * 4  # draw large, then shrink, for clean edges
    b = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    d.ellipse((0, 0, s - 1, s - 1), fill=INK)
    r = s * 0.035
    d.ellipse((r, r, s - r, s - r), fill=RED)
    r2 = s * 0.085
    d.ellipse((r2, r2, s - r2, s - r2), fill=WHITE)
    r3 = s * 0.115
    d.ellipse((r3, r3, s - r3, s - r3), fill=BLUE)
    # stars round the rim of the blue
    import math
    for i in range(13):
        ang = math.pi * (0.85 + 1.3 * i / 12)
        cx = s / 2 + math.cos(ang) * s * 0.33
        cy = s / 2 - math.sin(ang) * s * 0.33
        star(d, cx, cy, s * 0.035, WHITE)
    ew = int(s * 0.66)
    eh = int(eagle.height * ew / eagle.width)
    eg = eagle.resize((ew, eh), Image.LANCZOS)
    b.alpha_composite(eg, ((s - ew) // 2, int(s * 0.56 - eh / 2)))
    return b.resize((h, h), Image.LANCZOS)


def star(d, cx, cy, r, fill):
    import math
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.42
        ang = math.pi / 2 + i * math.pi / 5
        pts.append((cx + math.cos(ang) * rr, cy - math.sin(ang) * rr))
    d.polygon(pts, fill=fill)


def wordmark():
    big = ImageFont.truetype(STENCIL, 190)
    sub = ImageFont.truetype(OSWALD, 74)
    try:
        sub.set_variation_by_axes([700])
    except Exception:
        pass
    # G.I. JOE: white, red keyline, black outer line, and a navy drop
    core = text_layer((1400, 300), 'G.I. JOE', big, WHITE, 7, RED, spacing=6)
    outer = text_layer((1400, 320), 'G.I. JOE', big, INK, 16, INK, spacing=6)
    jw, jh = outer.size
    joe = Image.new('RGBA', (jw + 16, jh + 16), (0, 0, 0, 0))
    shadow = Image.new('RGBA', outer.size, BLUE + (255,))
    shadow.putalpha(outer.getchannel('A'))
    joe.alpha_composite(shadow, (14, 14))
    joe.alpha_composite(outer, (0, 0))
    joe.alpha_composite(core, ((jw - core.width) // 2, (jh - core.height) // 2))

    # USA DEFENSE: gold, letter-spaced, on a red-white-blue stripe bar with stars
    words = text_layer((1400, 160), 'USA  DEFENSE', sub, GOLD, 4, INK, spacing=14)
    bar_w = joe.width
    bar_h = words.height + 28
    bar = Image.new('RGBA', (bar_w, bar_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(bar)
    d.rectangle((0, 0, bar_w - 1, bar_h - 1), fill=INK)
    d.rectangle((4, 4, bar_w - 5, bar_h - 5), fill=BLUE)
    d.rectangle((4, bar_h - 14, bar_w - 5, bar_h - 10), fill=RED)
    d.rectangle((4, bar_h - 10, bar_w - 5, bar_h - 7), fill=WHITE)
    d.rectangle((4, 7, bar_w - 5, 10), fill=WHITE)
    d.rectangle((4, 10, bar_w - 5, 14), fill=RED)
    for x in (34, bar_w - 34):
        star(d, x, bar_h / 2, 17, WHITE)
    bar.alpha_composite(words, ((bar_w - words.width) // 2, (bar_h - words.height) // 2 + 2))

    gap = 10
    text = Image.new('RGBA', (joe.width, joe.height + gap + bar.height), (0, 0, 0, 0))
    text.alpha_composite(joe, (0, 0))
    text.alpha_composite(bar, (0, joe.height + gap))

    badge = eagle_badge(text.height + 10)
    out = Image.new('RGBA', (badge.width + 26 + text.width, max(badge.height, text.height)), (0, 0, 0, 0))
    out.alpha_composite(badge, (0, (out.height - badge.height) // 2))
    out.alpha_composite(text, (badge.width + 26, (out.height - text.height) // 2))
    return out


def main():
    base = os.path.join(FE, 'title_base_hi.png')
    if not os.path.exists(base):
        Image.open(os.path.join(FE, 'title_hi.png')).convert('RGB').save(base)
    art = Image.open(base).convert('RGBA')
    # John's logo (13 Nov 2026, gi-joe-usa-defense-enhanced.png) wins when it is there;
    # the drawn wordmark is the fallback.
    logo = os.path.join(FE, 'logo_usa_defense.png')
    wm = Image.open(logo).convert('RGBA') if os.path.exists(logo) else wordmark()
    if not os.path.exists(logo):
        wm.save(os.path.join(FE, 'title_word.png'))
    # the open sky at the top right of the key art
    w = 860
    h = int(wm.height * w / wm.width)
    wm_s = wm.resize((w, h), Image.LANCZOS)
    # a soft dark glow behind it; padded so the blur is not clipped into a visible box
    pad = 60
    mask = Image.new('L', (w + 2 * pad, h + 2 * pad), 0)
    mask.paste(wm_s.getchannel('A'), (pad, pad))
    glow = mask.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.55))
    halo = Image.new('RGBA', mask.size, (0, 0, 0, 0))
    halo.putalpha(glow)
    x, y = 1920 - w - 70, 40
    art.alpha_composite(halo, (x - pad, y - pad + 6))
    art.alpha_composite(wm_s, (x, y))
    art = art.convert('RGB')
    art.save(os.path.join(FE, 'title_hi.png'))
    sys.path.insert(0, HERE)
    import install_screen_backgrounds as isb
    isb.to_8bit(art).save(os.path.join(FE, 'title.png'))
    print('title written', wm.size, '->', (w, h), 'at', (x, y))


if __name__ == '__main__':
    main()
