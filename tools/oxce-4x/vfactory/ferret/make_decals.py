"""Cobra Ferret toy stickers (the toy's instruction sheet and photos, John 17 Nov 22:52) as magenta-keyed decal images. Only the
ones that read at the Ferret's size: 1 the Cobra sigil over ATV (both right-side fenders), 8 MISSILE LAUNCH INFO (both left-side
fenders), 6 BEWARE OF BLAST! (the cannon). The sigil comes from John's own sigil mask (private, never committed), not redrawn.
python3 make_decals.py sigil_mask.png outdir"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
MASK, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True)
K = (255, 0, 255); RED = (206, 30, 36); WHITE = (238, 238, 232); INK = (24, 24, 26); FD = '/usr/share/fonts/truetype/dejavu/'
# 1: sigil over ATV (the sticker is a square; the toy's: red sigil, white ATV, straight on the blue)
im = Image.new('RGB', (240, 300), K); m = Image.open(MASK).convert('L'); m = m.resize((190, int(190 * m.height / m.width)), Image.LANCZOS)
sig = Image.new('RGB', m.size, RED); im.paste(sig, ((240 - m.width) // 2, 10), m.point(lambda v: 255 if v > 110 else 0))
d = ImageDraw.Draw(im); f = ImageFont.truetype(FD + 'DejaVuSerif-Bold.ttf', 74); bb = d.textbbox((0, 0), 'ATV', font=f)
d.text(((240 - bb[2] - bb[0]) / 2, 300 - 90), 'ATV', font=f, fill=WHITE); im.save(f'{OUT}/fr_atv.png')
def text(name, s, size, w, h, fg, bg):
    im = Image.new('RGB', (w, h), bg); d = ImageDraw.Draw(im); f = ImageFont.truetype(FD + 'DejaVuSansCondensed-Bold.ttf', size)
    bb = d.textbbox((0, 0), s, font=f); d.text(((w - bb[2] - bb[0]) / 2, (h - bb[3] - bb[1]) / 2), s, font=f, fill=fg); im.save(f'{OUT}/{name}.png')
text('fr_missile', 'MISSILE LAUNCH INFO', 70, 860, 120, WHITE, K)       # white letters straight on the blue
text('fr_beware', 'BEWARE OF BLAST!', 70, 760, 110, INK, WHITE)          # black on a white strip, on the red cannon
print('DECALS', sorted(os.listdir(OUT)))
