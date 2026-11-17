"""Cut the sigil out of John's picture (red on white) into a mask; private, never committed.
python3 make_sigil.py in.png out_mask.png"""
import sys, numpy as np
from PIL import Image
a = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(int)
m = (a[..., 0] > 120) & (a[..., 1] < 110) & (a[..., 2] < 120)
ys, xs = np.nonzero(m); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
Image.fromarray((m * 255).astype(np.uint8)).save(sys.argv[2]); print('mask', m.shape, round(m.mean(), 3))
