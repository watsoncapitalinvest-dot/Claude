"""M.O.B.A.T. toy markings as magenta-keyed decal images (John's 3DJoes photos, 17 Nov 21:44): plain white stars (turret sides,
front plate, mantlet), UNITED STATES (white) + US flag on the front plate, U.S.A. and the big 5 on the turret sides.
The Generals G.I.JOE logo on the hull sides is in the texture and stays.
python3 make_decals.py outdir"""
import sys, os, math
from PIL import Image, ImageDraw, ImageFont
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
K = (255, 0, 255); WHITE = (238, 238, 232); FD = '/usr/share/fonts/truetype/dejavu/'
im = Image.new('RGB', (200, 200), K); d = ImageDraw.Draw(im)
d.polygon([(100 + (96 if i % 2 == 0 else 38) * math.sin(i * math.pi / 5), 108 - (96 if i % 2 == 0 else 38) * math.cos(i * math.pi / 5)) for i in range(10)], fill=WHITE)
im.save(f'{OUT}/mb_star.png')
def text(name, s, font, size, w, h, fill=WHITE):
    im = Image.new('RGB', (w, h), K); d = ImageDraw.Draw(im); f = ImageFont.truetype(FD + font, size)
    bb = d.textbbox((0, 0), s, font=f); d.text(((w - bb[2] - bb[0]) / 2, (h - bb[3] - bb[1]) / 2), s, font=f, fill=fill); im.save(f'{OUT}/{name}.png')
text('mb_us', 'UNITED STATES', 'DejaVuSansCondensed-Bold.ttf', 110, 900, 150)
im = Image.new('RGB', (420, 200), K); d = ImageDraw.Draw(im)
d.text((10, 60), 'U.S.A.', font=ImageFont.truetype(FD + 'DejaVuSansCondensed-Bold.ttf', 80), fill=WHITE)
d.text((270, 0), '5', font=ImageFont.truetype(FD + 'DejaVuSerifCondensed-Bold.ttf', 190), fill=WHITE); im.save(f'{OUT}/mb_usa5.png')
im = Image.new('RGB', (190, 100), K); d = ImageDraw.Draw(im)
for i in range(13): d.rectangle((0, i * 100 / 13, 189, (i + 1) * 100 / 13), fill=(190, 30, 40) if i % 2 == 0 else (240, 240, 236))
d.rectangle((0, 0, 76, 54), fill=(36, 60, 150)); im.save(f'{OUT}/mb_flag.png')
print('DECALS', sorted(os.listdir(OUT)))
