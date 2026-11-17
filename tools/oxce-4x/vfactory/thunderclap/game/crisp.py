# local contrast for small hard-surface parts (guns, missiles) at game size: unsharp on lightness only, alpha kept
import sys, numpy as np
from PIL import Image, ImageFilter
def crisp(im, mask=None, radius=1.6, amount=1.1, thr=2):
    im = im.convert('RGBA'); a = np.asarray(im).astype(np.float32); rgb = Image.fromarray(a[..., :3].astype(np.uint8))
    sh = np.asarray(rgb.filter(ImageFilter.UnsharpMask(radius=radius, percent=int(amount * 100), threshold=thr))).astype(np.float32)
    m = (a[..., 3] > 0) if mask is None else (mask & (a[..., 3] > 0))
    a[..., :3][m] = sh[m]; return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
if __name__ == '__main__':
    for f in sys.argv[1:]: crisp(Image.open(f)).save(f)
