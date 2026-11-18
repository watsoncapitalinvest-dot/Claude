"""Wolverine toy markings as magenta-keyed decal images (3DJoes photo set): star roundel (pale disc, star cut out in hull green),
WOLVERINE (black italic, rear), UNITED STATES (black condensed) + US flag (front deck), AID KIT/TOOLCASE (left side),
RELAY 23 / RELAY 24 (pod backs), and the pod G.I.JOE logo block.
python3 make_decals.py generals_texture.png outdir"""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
TEX, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True)
K = (255, 0, 255); GREEN = (58, 84, 56); PALE = (226, 228, 218); INK = (24, 26, 24)
FD = '/usr/share/fonts/truetype/dejavu/'
def text(name, s, font, size, w, h, fill=INK, skew=0.0):
    im = Image.new('RGB', (w, h), K); d = ImageDraw.Draw(im); f = ImageFont.truetype(FD + font, size)
    bb = d.textbbox((0, 0), s, font=f); d.text(((w - bb[2] - bb[0]) / 2, (h - bb[3] - bb[1]) / 2), s, font=f, fill=fill)
    im.save(f'{OUT}/{name}.png')
# star roundel
im = Image.new('RGB', (200, 200), K); d = ImageDraw.Draw(im); d.ellipse((6, 6, 194, 194), fill=PALE, outline=(150, 152, 146), width=4)
import math
pts = [(100 + (70 if i % 2 == 0 else 28) * math.sin(i * math.pi / 5), 104 - (70 if i % 2 == 0 else 28) * math.cos(i * math.pi / 5)) for i in range(10)]
d.polygon(pts, fill=GREEN); im.save(f'{OUT}/wv_star.png')
text('wv_name', 'WOLVERINE', 'DejaVuSans-BoldOblique.ttf', 120, 900, 170)
text('wv_us', 'UNITED STATES', 'DejaVuSansCondensed-Bold.ttf', 110, 900, 150)
text('wv_toolcase', 'AID KIT/TOOLCASE', 'DejaVuSansCondensed-Bold.ttf', 60, 600, 90, fill=PALE)
text('wv_relay23', 'RELAY 23', 'DejaVuSansCondensed-Bold.ttf', 70, 360, 100, fill=PALE)
text('wv_relay24', 'RELAY 24', 'DejaVuSansCondensed-Bold.ttf', 70, 360, 100, fill=PALE)
# US flag: 13 stripes, blue canton
im = Image.new('RGB', (190, 100), K); d = ImageDraw.Draw(im)
for i in range(13): d.rectangle((0, i * 100 / 13, 189, (i + 1) * 100 / 13), fill=(190, 30, 40) if i % 2 == 0 else (240, 240, 236))
d.rectangle((0, 0, 76, 54), fill=(36, 60, 150)); im.save(f'{OUT}/wv_flag.png')
# pod logo: white italic G.I.JOE with a black edge and the red / white / blue bars after it (the texture's own logo is
# 20 px tall and turns to mush when keyed, so it is drawn here the same way as the Thunderclap tanks' logo block)
im = Image.new('RGB', (720, 200), K); d = ImageDraw.Draw(im); f = ImageFont.truetype(FD + 'DejaVuSans-BoldOblique.ttf', 130)
d.text((14, 22), 'GI JOE', font=f, fill=(244, 244, 240), stroke_width=9, stroke_fill=INK)
x0 = d.textbbox((14, 22), 'GI JOE', font=f, stroke_width=9)[2] - 6
for i, c in enumerate([(200, 30, 36), (244, 244, 240), (36, 60, 160)]):
    y = 52 + i * 34; d.polygon([(x0 + 14, y), (x0 + 196, y - 10), (x0 + 190, y + 24), (x0 + 8, y + 32)], fill=c, outline=INK)
im.crop(Image.fromarray((np.asarray(im) != np.array(K)).any(-1).astype(np.uint8) * 255).getbbox()).save(f'{OUT}/wv_logo.png')
print('DECALS', sorted(os.listdir(OUT)))
