"""V.A.M.P. toy markings (3DJoes photos) as magenta-keyed decal images: G.I.JOE block (same as the Wolverine's), 4647 (white,
rockers and gun), UNITED STATES (black, hood), star roundel. python3 make_decals.py wolverine_decal_dir outdir"""
import sys, os, shutil
from PIL import Image, ImageDraw, ImageFont
WV, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True); K = (255, 0, 255); FD = '/usr/share/fonts/truetype/dejavu/'
shutil.copy(f'{WV}/wv_logo.png', f'{OUT}/vp_logo.png'); shutil.copy(f'{WV}/wv_star.png', f'{OUT}/vp_star.png')
def text(name, s, font, size, w, h, fill):
    im = Image.new('RGB', (w, h), K); d = ImageDraw.Draw(im); f = ImageFont.truetype(FD + font, size)
    bb = d.textbbox((0, 0), s, font=f); d.text(((w - bb[2] - bb[0]) / 2, (h - bb[3] - bb[1]) / 2), s, font=f, fill=fill); im.save(f'{OUT}/{name}.png')
text('vp_4647', '4647', 'DejaVuSerifCondensed-Bold.ttf', 120, 330, 150, (238, 238, 232))
text('vp_us', 'UNITED STATES', 'DejaVuSansCondensed-Bold.ttf', 110, 900, 150, (26, 28, 26))
print('DECALS', sorted(os.listdir(OUT)))
