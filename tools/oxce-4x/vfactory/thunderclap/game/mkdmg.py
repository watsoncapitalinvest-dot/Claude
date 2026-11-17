# procedural hit stickers (scorch, dents, bullet holes, gouges) - RGBA, transparent outside the marks
import numpy as np, sys
from PIL import Image, ImageDraw, ImageFilter
rng = np.random.default_rng(7); out = sys.argv[1]
def blob(W, H, n, rmin, rmax, col, blur):
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y = rng.uniform(.2, .8) * W, rng.uniform(.2, .8) * H; r = rng.uniform(rmin, rmax)
        d.ellipse([x - r, y - r * rng.uniform(.6, 1), x + r, y + r * rng.uniform(.6, 1)], fill=col)
    return im.filter(ImageFilter.GaussianBlur(blur))
def holes(im, n, r):
    d = ImageDraw.Draw(im); W, H = im.size
    for _ in range(n):
        x, y = rng.uniform(.15, .85) * W, rng.uniform(.15, .85) * H; rr = r * rng.uniform(.7, 1.3)
        d.ellipse([x - rr * 1.8, y - rr * 1.8, x + rr * 1.8, y + rr * 1.8], fill=(70, 66, 60, 255))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(12, 10, 9, 255))
    return im
W, H = 160, 120
sc = blob(W, H, 18, 10, 30, (20, 18, 16, 210), 9); sc.alpha_composite(blob(W, H, 8, 6, 14, (8, 7, 6, 255), 4)); sc.save(f'{out}/scorch.png')
c = blob(W, H, 10, 8, 20, (30, 28, 25, 150), 7); holes(c, 9, 4); c.save(f'{out}/cluster.png')
dn = blob(W, H, 6, 14, 26, (60, 58, 54, 170), 6); dn.alpha_composite(blob(W, H, 6, 6, 12, (25, 24, 22, 220), 3)); holes(dn, 3, 5); dn.save(f'{out}/dents.png')
g = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(g)
for _ in range(5):
    x, y = rng.uniform(.1, .5) * W, rng.uniform(.2, .8) * H; L = rng.uniform(.3, .5) * W; a = rng.uniform(-.4, .4)
    d.line([x, y, x + L * np.cos(a), y + L * np.sin(a)], fill=(15, 13, 12, 255), width=int(rng.integers(3, 7)))
g = g.filter(ImageFilter.GaussianBlur(1.2)); g2 = blob(W, H, 6, 10, 22, (35, 32, 28, 130), 8); g2.alpha_composite(g); g2.save(f'{out}/gouges.png')
print('ok')
