"""Explosion marks fixed to a craft that has no .blend on hand (Tomahawk, Swampfire, Water Moccasin).
A stand-in 3D shape is carved from the craft's 8 damaged headings in its shipped sheet (visual hull, same camera as the
renderer: ortho, 30 deg up, 90.51 px per world unit, heading k = model turned -45k deg). The marks are put on that shape
and projected into all 8 headings, so they turn with the craft like the marks of the craft that do have a .blend.

python3 proxy_hull.py <sheet png> <sheet json> <out json> [E fractions json list | auto]
E fractions = [[fx, fy, size], ...] of the damaged heading-E picture's bbox (blast_points.json style)."""
import sys, json, math
import numpy as np
from PIL import Image

PNG, JS, OUT, MODE = sys.argv[1:5]
info = json.load(open(JS)); W, H = info['cell']; AX, AY = info['anchor_in_cell']; PR = info['per_row']
dmg0 = info['index']['damaged_headings'][0]
sheet = np.array(Image.open(PNG)) != 0                                # palette index 0 = see-through
sil = [sheet[(f // PR) * H:(f // PR + 1) * H, (f % PR) * W:(f % PR + 1) * W] for f in range(dmg0, dmg0 + 8)]

PPU, C30, S30 = 90.50967, math.cos(math.radians(30)), math.sin(math.radians(30))
def rot(k, P):                                     # model -> the heading-k frame (k=0 is N)
    a = math.radians(-45 * k); c, s = math.cos(a), math.sin(a)
    return np.stack([c * P[..., 0] - s * P[..., 1], s * P[..., 0] + c * P[..., 1], P[..., 2]], -1)
def proj(k, P):                                    # -> px offset from the anchor, and depth toward the camera
    Q = rot(k, P); u = (Q[..., 0] - Q[..., 1]) / math.sqrt(2); v = (Q[..., 0] + Q[..., 1]) / math.sqrt(2)
    return PPU * u, -PPU * S30 * v - PPU * C30 * Q[..., 2], -C30 * v + S30 * Q[..., 2]

# carve
R = max(W, H) / PPU * 0.6; G = 230; ax = np.linspace(-R, R, G); vs = ax[1] - ax[0]
X, Y, Z = np.meshgrid(ax, ax, np.linspace(-R / 2, R, G), indexing='ij'); P = np.stack([X, Y, Z], -1)
keep = np.ones(X.shape, bool)
for k in range(8):
    px, py, _ = proj(k, P); ix = np.round(px + AX).astype(int); iy = np.round(py + AY).astype(int)
    inside = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
    on = np.zeros(X.shape, bool); on[inside] = sil[k][iy[inside], ix[inside]]
    S = sil[k]; cut = S[0].any() or S[-1].any() or S[:, 0].any() or S[:, -1].any()
    edge = (~inside) if cut else np.zeros(X.shape, bool)   # picture cut off at the cell edge: beyond it is unknown, keep
    keep &= on | edge
pts = P[keep]
print('proxy voxels', len(pts), 'of', keep.size)
if len(pts) < 50: sys.exit('carving failed')

# how well the stand-in fills the 8 pictures (it can only be bigger than the real craft, never smaller)
fit = []
for k in range(8):
    px, py, _ = proj(k, pts); m = np.zeros((H, W), bool)
    ix = np.clip(np.round(px + AX).astype(int), 0, W - 1); iy = np.clip(np.round(py + AY).astype(int), 0, H - 1); m[iy, ix] = True
    from scipy.ndimage import binary_dilation
    m = binary_dilation(m, iterations=int(math.ceil(PPU * vs))); fit.append(round(float((m & sil[k]).sum() / max(1, (m | sil[k]).sum())), 3))
print('silhouette match per heading', fit)

def front(k, x, y):                                 # first voxel hit by the camera ray through (x, y) px at heading k
    px, py, dep = proj(k, pts); near = (np.abs(px - x) < 1.2 * PPU * vs) & (np.abs(py - y) < 1.2 * PPU * vs)
    if not near.any(): return None
    i = np.argmax(np.where(near, dep, -1e9)); return pts[i]

marks = []
if MODE == 'auto':                                 # boats (+x = bow): 1 small aft starboard, 2 regular forward port, D middle; all on top
    lo, hi = pts.min(0), pts.max(0); L, Wd = hi[0] - lo[0], hi[1] - lo[1]; deck = lo[2] + 0.85 * (hi[2] - lo[2])
    c0 = (lo[:2] + hi[:2]) / 2
    def top(x, y):
        for t in np.linspace(0, 1, 21):
            q = np.array([x, y]) + (c0 - np.array([x, y])) * t
            col = pts[(np.abs(pts[:, 0] - q[0]) < vs) & (np.abs(pts[:, 1] - q[1]) < vs) & (pts[:, 2] <= deck)]
            if len(col): return np.array([q[0], q[1], col[:, 2].max()])
        return np.array([x, y, deck])
    want = [(top(lo[0] + 0.22 * L, lo[1] + 0.22 * Wd), 's'), (top(lo[0] + 0.70 * L, lo[1] + 0.74 * Wd), 'r'), (top(*c0), 'b')]
else:                                              # John's E marks: fractions of the damaged E picture -> px -> onto the shape
    ys, xs = np.nonzero(sil[2]); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    want = []
    for fx, fy, size in json.loads(MODE):
        x, y = x0 + fx * (x1 - x0) - AX, y0 + fy * (y1 - y0) - AY; p = front(2, x, y); r = 0
        while p is None and r < 20: r += 1; p = front(2, x + r, y) if front(2, x + r, y) is not None else front(2, x - r, y)
        want.append((p, size))

out = {'frame': [W, H], 'anchor': [AX, AY], 'proxy': True, 'silhouette_match': fit, 'marks': []}
for loc, size in want:
    per = []
    for k in range(8):
        px, py, dep = proj(k, loc[None])
        apx, apy, adep = proj(k, pts); near = (np.abs(apx - px[0]) < PPU * vs) & (np.abs(apy - py[0]) < PPU * vs)
        seen = bool(dep[0] >= adep[near].max() - 2.5 * vs) if near.any() else True
        per.append([round(float(px[0]), 1), round(float(py[0]), 1), seen])
    out['marks'].append({'size': size, 'model': [round(float(v), 4) for v in loc], 'placed_by': 'VFACTORY on a stand-in shape carved from the 8 pictures (John 14:58)', 'headings': per})
json.dump(out, open(OUT, 'w'), indent=1); print('MARKS8', OUT, [m['size'] for m in out['marks']])
