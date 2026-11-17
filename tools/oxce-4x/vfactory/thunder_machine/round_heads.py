# 8-direction head sheet for the 30mm round (gjBulletHeadSheet: frame d = screen direction, 0 = nose up, clockwise).
# usage: python3 round_heads.py side_view_nose_right.png palette_source.png out_stem
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter
SRC, PALSRC, OUT = sys.argv[1:4]
h = Image.open(SRC).convert('RGBA'); h = h.crop(h.getbbox())
tr = Image.new('RGBA', (h.width + 26, max(h.height, 8)), (0, 0, 0, 0)); d = ImageDraw.Draw(tr); cy = tr.height // 2
for i in range(26):                                                # tracer glow fading out behind the case
    a = int(200 * (i / 26)); d.line([(i, cy - 1), (i, cy + 1)], fill=(255, 190, 70, a))
tr = tr.filter(ImageFilter.GaussianBlur(0.8)); tr.alpha_composite(h, (26, (tr.height - h.height) // 2)); h = tr
Z = max(48, -(-(max(h.size) + 6) // 16) * 16)
H = Image.new('RGBA', (8 * Z, Z), (0, 0, 0, 0))
for k in range(8):
    r = h.rotate((2 - k) * 45, resample=Image.BICUBIC, expand=True)
    H.alpha_composite(r, (k * Z + (Z - r.width) // 2, (Z - r.height) // 2))
H.save(OUT + '_rgb.png')
pal = Image.open(PALSRC); P = np.array(pal.getpalette()[:768], np.int32).reshape(-1, 3)
a = np.asarray(H).astype(np.int32); out = np.zeros(a.shape[:2], np.uint8); m = a[..., 3] > 110
f = a[..., :3][m]; out[m] = ((f[:, None, :] - P[None, 1:]) ** 2).sum(-1).argmin(1) + 1
q = Image.fromarray(out, 'P'); q.putpalette(pal.getpalette()); q.save(OUT + '.png'); print('head', H.size, 'frame', Z)
