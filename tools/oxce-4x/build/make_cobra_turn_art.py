#!/usr/bin/env python3
"""The Cobra turn screen's HIDDEN MOVEMENT readout (BRIEF_FOR_BUILD_CobraTurnScreen item 3, approved 13 Nov 13:26).

    python3 build/make_cobra_turn_art.py [DSEG14Classic-Bold.ttf]

Writes mod/Resources/UI/cobra_turn_led_on.png and _off.png: the recessed display window (near-black, rounded, 6 px
olive edge #4A5640), every digit's unlit segments at 13% ('~' in DSEG), and - on - the words in LED red #FF281E with a
12 px glow. Sized in the pictures' own 1920x1200 canvas pixels; the engine scales it with the picture and puts it
in the dark band, y 520-680. The font is SIL OFL (fonts/OFL_DSEG.txt), so the font file itself can sit in the repo.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.normpath(os.path.join(HERE, '..', 'mod', 'Resources', 'UI'))
TTF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'fonts', 'DSEG14Classic-Bold.ttf')
TEXT = 'HIDDEN!MOVEMENT'            # '!' is DSEG's blank digit: the gap between the words is one digit wide
RED, OLIVE = (255, 40, 30), (74, 86, 64)
font = ImageFont.truetype(TTF, 96)   # the brief: about 96 px canvas height
l, t, r, b = font.getbbox('~' * len(TEXT))
tw, th = r - l, b - t
PADX, PADY, EDGE = 44, 30, 6
W, H = tw + 2 * PADX, th + 2 * PADY
for lit in (True, False):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=18, fill=OLIVE + (255,))
    d.rounded_rectangle((EDGE, EDGE, W - 1 - EDGE, H - 1 - EDGE), radius=13, fill=(10, 10, 9, 255))
    # recessed: a darker lip along the top and left inside the edge
    d.rounded_rectangle((EDGE, EDGE, W - 1 - EDGE, EDGE + 5), radius=4, fill=(2, 2, 2, 255))
    ghost = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ghost).text((PADX - l, PADY - t), '~' * len(TEXT), font=font, fill=RED + (33,))   # 13%
    im.alpha_composite(ghost)
    if lit:
        txt = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(txt).text((PADX - l, PADY - t), TEXT, font=font, fill=RED + (255,))
        glow = txt.filter(ImageFilter.GaussianBlur(12))
        a = glow.getchannel('A').point(lambda v: min(255, v * 2))
        glow.putalpha(a)
        im.alpha_composite(glow); im.alpha_composite(txt)
    im.save(os.path.join(UI, 'cobra_turn_led_%s.png' % ('on' if lit else 'off')))
print('readout %dx%d canvas px' % (W, H))
