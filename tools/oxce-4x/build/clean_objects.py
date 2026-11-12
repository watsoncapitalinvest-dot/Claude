"""Clean delivered room-object pictures and file them for the game.

    python3 clean_objects.py <delivered dir> <out dir> [spec.txt ...]

The painter blends each object's edge into the magenta, so the outer pixels are part object,
part FF00FF - a pink fringe once keyed. Each such pixel is un-blended: its magenta share is
estimated from how far it sits toward FF00FF, and if it is mostly magenta it becomes background;
otherwise its colour is replaced with the nearest solid object pixel. The result has a hard edge,
every pixel object or pure FF00FF. Sizes are checked against the group specs when given.
"""
import os, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage

src, out = sys.argv[1], sys.argv[2]
want = {}
for spec in sys.argv[3:]:
    for line in open(spec):
        m = re.match(r'\s+(obj_\S+\.png)\s+(\d+) x (\d+)', line)
        if m:
            want[m.group(1)] = (int(m.group(2)), int(m.group(3)))
os.makedirs(out, exist_ok=True)

MAG = np.array([255, 0, 255], float)
done = fixed = 0
for name in sorted(os.listdir(src)):
    if not (name.startswith('obj_') and name.endswith('.png')):
        continue
    im = Image.open(os.path.join(src, name)).convert('RGBA')
    a = np.array(im).astype(float)
    rgb = a[:, :, :3]
    if (a[:, :, 3] < 128).any():                      # transparent background -> magenta
        rgb[a[:, :, 3] < 128] = MAG
    # pinkness: magenta is high R, high B, low G with R ~ B
    pink = np.clip((np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1]) / 255.0, 0, 1)
    pink *= np.clip(1 - np.abs(rgb[:, :, 0] - rgb[:, :, 2]) / 80.0, 0, 1)
    bg = pink > 0.55
    solid = pink < 0.15
    # fill: any pixel that is neither clear background nor solid object takes its nearest solid colour
    edge = ~bg & ~solid
    if edge.any():
        idx = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
        rgb[edge] = rgb[idx[0][edge], idx[1][edge]]
        fixed += 1
    rgb[bg] = MAG
    res = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB')
    if name in want and res.size != want[name]:
        print('  size', name, res.size, 'spec', want[name])
    res.save(os.path.join(out, name))
    done += 1
print('%d cleaned (%d had fringe) -> %s' % (done, fixed, out))
