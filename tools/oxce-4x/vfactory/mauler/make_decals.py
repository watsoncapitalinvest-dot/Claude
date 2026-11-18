"""Mauler M.B.T. toy stickers as magenta-keyed decal images, from the toy's sticker sheet (John 17 Nov 22:32). Only the ones that read
at game size: 1 the G.I.JOE logo with its three long stripes (upper hull sides, rear), 7 the big star in a circle (front deck),
5 the "51" roundel, 6 the turret stars, 30 US ARMY (gun sleeve), 2 UNITED STATES (front plate), 4 S-021683 and 27 12CX84 (rear).
python3 make_decals.py outdir"""
import sys, os, math
from PIL import Image, ImageDraw, ImageFont
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
K = (255, 0, 255); INK = (26, 26, 28); WHITE = (236, 236, 230); FD = '/usr/share/fonts/truetype/dejavu/'
def star(d, cx, cy, r, fill):
    d.polygon([(cx + (r if i % 2 == 0 else r * 0.4) * math.sin(i * math.pi / 5), cy - (r if i % 2 == 0 else r * 0.4) * math.cos(i * math.pi / 5)) for i in range(10)], fill=fill)
for name, ring in (('ml_star7', 10), ('ml_star6', 8)):        # star in a circle: dark ring and star on a white disc
    im = Image.new('RGB', (200, 200), K); d = ImageDraw.Draw(im); d.ellipse((4, 4, 196, 196), fill=WHITE, outline=INK, width=ring)
    star(d, 100, 106, 78, INK); im.save(f'{OUT}/{name}.png')
im = Image.new('RGB', (200, 200), K); d = ImageDraw.Draw(im); d.ellipse((4, 4, 196, 196), fill=WHITE)    # 51 in a dashed ring
for k in range(16): d.arc((14, 14, 186, 186), k * 22.5, k * 22.5 + 13, fill=INK, width=14)
f = ImageFont.truetype(FD + 'DejaVuSansCondensed-Bold.ttf', 84); bb = d.textbbox((0, 0), '51', font=f); d.text((100 - (bb[2] + bb[0]) / 2, 100 - (bb[3] + bb[1]) / 2), '51', font=f, fill=INK)
im.save(f'{OUT}/ml_51.png')
def text(name, s, size, w, h, fg, bg=None, box=False):
    im = Image.new('RGB', (w, h), bg or K); d = ImageDraw.Draw(im); f = ImageFont.truetype(FD + 'DejaVuSansCondensed-Bold.ttf', size)
    if box: d.rectangle((3, 3, w - 4, h - 4), outline=fg, width=5)
    bb = d.textbbox((0, 0), s, font=f); d.text(((w - bb[2] - bb[0]) / 2, (h - bb[3] - bb[1]) / 2), s, font=f, fill=fg); im.save(f'{OUT}/{name}.png')
text('ml_us', 'UNITED STATES', 110, 940, 150, WHITE, INK)    # sheet: white letters on a black strip
text('ml_army', 'US ARMY', 110, 560, 150, INK)               # black letters straight on the tan
text('ml_s021683', 'S-021683', 90, 520, 130, INK, None, True)
text('ml_12cx84', '12CX84', 90, 420, 130, INK, None, True)
# 1: the logo block (white italic G.I.JOE on black) and three long black stripes running on from it
im = Image.new('RGB', (1400, 200), K); d = ImageDraw.Draw(im); d.rectangle((0, 10, 470, 190), fill=INK)
f = ImageFont.truetype(FD + 'DejaVuSans-BoldOblique.ttf', 130); d.text((24, 18), 'GI JOE', font=f, fill=WHITE)
for i in range(3): y = 30 + i * 52; d.rectangle((490, y, 1396, y + 34), fill=INK)
im.save(f'{OUT}/ml_logo.png')
print('DECALS', sorted(os.listdir(OUT)))
