"""python3 render_smuggler.py <outdir> : singles via kitlib.render, big objects via kitbig.cut_cells.
Writes smuggler_cells.json (cell sprites that are not empty) and smuggler_wing.json (plane cells that are wing only)."""
import sys, os, json, random, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitlib, kitbig, smuggler
from kitlib import S
from PIL import Image
import numpy as np
OUT = sys.argv[-1]; os.makedirs(OUT, exist_ok=True); tmp = os.path.join(OUT, 'cells'); os.makedirs(tmp, exist_ok=True)
for k, (name, ink, fn) in enumerate(smuggler.SINGLES):
    random.seed(k); p = kitlib.Part(name, ink); fn(p); kitlib.render(p, os.path.join(tmp, name)); print('single', name, flush=True)
cells = {}; wing = []
cy = -4.5 * S
for (obj, fn, (nx, ny, nz)) in smuggler.BIGS:
    p = kitlib.Part(obj, True); fn(p)
    occ = kitbig.occupied(p, nx, ny, nz)
    names = [(i, j, l, '%s_%d_%d_%d' % (obj, i, j, l)) for (i, j, l) in occ]
    kitbig.cut_cells(p, names, tmp, 'c')
    keep = []
    for (i, j, l, n) in names:
        f = os.path.join(tmp, 'c_%s.png' % n)
        if np.array(Image.open(f))[..., 3].any() or l == 0: keep.append([i, j, l, n])   # empty ground-level cells stay as invisible blockers (inside the fuselage)
        else: os.remove(f)
    cells[obj] = keep; print(obj, len(occ), 'cells,', len(keep), 'kept', flush=True)
    if obj == 'plane':
        for (i, j, l, n) in keep:
            y0, y1 = -(j + 1) * S, -j * S
            x0, x1 = i * S, (i + 1) * S
            fus = y1 > cy - 0.75 and y0 < cy + 0.75
            eng = any(y1 > yc - 0.42 and y0 < yc + 0.42 and x1 > 5.2 and x0 < 7.6 for yc in (cy - 2.3, cy + 2.3))
            if not (fus or eng): wing.append(n)
json.dump(cells, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'smuggler_cells.json'), 'w'))
json.dump(wing, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'smuggler_wing.json'), 'w'))
# frame-ordered copies for build_set.py
import importlib; importlib.reload(smuggler)
for idx, (name, _, _) in enumerate(smuggler.KIT):
    src = os.path.join(tmp, name + '.png') if os.path.exists(os.path.join(tmp, name + '.png')) else os.path.join(tmp, 'c_%s.png' % name)
    Image.open(src).save(os.path.join(OUT, '%02d_%s.png' % (idx, name)))
print('total parts', len(smuggler.KIT))
