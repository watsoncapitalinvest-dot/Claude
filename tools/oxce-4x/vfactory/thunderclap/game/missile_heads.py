# Directional projectile rows for the Thunderclap missiles (VFACTORY, 17 Nov "finish the missiles"):
# per missile two 35-frame rows of 48x48: the smoke trail (copied from the mod's missile row 20) and 8 heads by screen direction
# (0 = nose up, clockwise; bulletDirectional). Heads come from the package's full-size flight sprite (heading NE flies screen-right).
# usage: missile_heads.py projectiles_rgb.png projectiles.png out_stem pkg1 [pkg2 ...]   -> out_stem.png (paletted) + out_stem_rgb.png
import sys, json, numpy as np
from PIL import Image
RGB, PAL, OUT, PKGS = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
src = Image.open(RGB).convert('RGBA'); trail = src.crop((0, 9 * 48, 1680, 10 * 48))     # row 20 (sheet starts at row 11)
S = Image.new('RGBA', (1680, 96 * len(PKGS)), (0, 0, 0, 0))
for i, p in enumerate(PKGS):
    m = json.load(open(f'{p}/manifest.json')); e = m['missile_full']['by_heading']['NE']
    h = Image.open(f'{p}/{e["file"]}').convert('RGBA'); h = h.crop(h.getbbox())
    k = 44 / h.width; h = h.resize((44, max(3, round(h.height * k))), Image.LANCZOS)      # nose right = direction 2
    S.alpha_composite(trail, (0, i * 96))
    for d in range(8):
        r = h.rotate((2 - d) * 45, resample=Image.BICUBIC, expand=True)
        S.alpha_composite(r, (d * 48 + (48 - r.width) // 2, i * 96 + 48 + (48 - r.height) // 2))
S.save(OUT + '_rgb.png')
pal = Image.open(PAL); P = np.array(pal.getpalette()[:768], np.int32).reshape(-1, 3)
a = np.asarray(S).astype(np.int32); out = np.zeros(a.shape[:2], np.uint8); m = a[..., 3] > 127
f = a[..., :3][m]; out[m] = ((f[:, None, :] - P[None, 1:]) ** 2).sum(-1).argmin(1) + 1
q = Image.fromarray(out, 'P'); q.putpalette(pal.getpalette()); q.save(OUT + '.png'); print('rows', 2 * len(PKGS), S.size)
