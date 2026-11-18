# In-game head sheet for the CMF-1's round (engine gjBulletHeadSheet): 8 frames by screen direction (0 = up, clockwise), each a
# 128 x 128 cell with the rendered round (cmf_round.py, nose right = direction 2) PX long at 4x, plus a paletted copy.
# usage: python3 cmf_head.py round.png projectiles.png out_stem [px_long]
import sys, numpy as np
from PIL import Image, ImageEnhance
SRC, PAL, OUT = sys.argv[1:4]; PX = int(sys.argv[4]) if len(sys.argv) > 4 else 26
r = Image.open(SRC).convert('RGBA'); r = r.crop(r.getbbox()); k = PX / r.width
r = r.resize((PX, max(3, round(r.height * k))), Image.LANCZOS); a = r.getchannel('A')
r = ImageEnhance.Brightness(r.convert('RGB')).enhance(1.6).convert('RGBA'); r.putalpha(a)
Z = 128; H = Image.new('RGBA', (8 * Z, Z), (0, 0, 0, 0))
for d in range(8):
    q = r.rotate((2 - d) * 45, resample=Image.BICUBIC, expand=True)
    H.alpha_composite(q, (d * Z + (Z - q.width) // 2, (Z - q.height) // 2))
H.save(OUT + '_rgb.png')
pal = Image.open(PAL); P = np.array(pal.getpalette()[:768], np.int32).reshape(-1, 3)
A = np.asarray(H).astype(np.int32); out = np.zeros(A.shape[:2], np.uint8); m = A[..., 3] > 127
f = A[..., :3][m]; out[m] = ((f[:, None, :] - P[None, 1:]) ** 2).sum(-1).argmin(1) + 1
q = Image.fromarray(out, 'P'); q.putpalette(pal.getpalette()); q.save(OUT + '.png'); print('head', OUT, r.size)
