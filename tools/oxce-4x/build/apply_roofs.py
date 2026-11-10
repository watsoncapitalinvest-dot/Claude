"""The sloped roofs and the gable ends - the last of the buildings still on the old 3D art.

Three different shapes, and only one of them is new work:

  tar_roof            flat, so it is a diamond like every other flat tile.
  gable{W,B,Y,R}_*    a triangle of ordinary wall. It sits in the plane of the wall below it,
                      so the wall projection is already right and the only new thing is the
                      silhouette - which the old sprite already has, exactly. Measured off the
                      old art rather than guessed: a gable's bottom edge runs at the same
                      +-0.5 as the wall beneath it, _x over the north face and _y over the west.
  roof_*, barnroof_*  a sloped plane, which is in no plane we already draw. Its four corners
                      are read off the old sprite and the affine solved from them, so the new
                      shingles land on the pitch the maps were built around rather than on a
                      pitch invented here.

Everything keeps the old sprite's own alpha, so nothing moves by a pixel and the tiles still
line up with the walls they sit on.

usage: apply_roofs.py <materials dir>
"""
import sys, json, glob, numpy as np
from PIL import Image
from scipy.spatial import ConvexHull

MAT = sys.argv[1]
SS = 4
FW, FH = 128 * SS, 160 * SS
LEVEL = 384.0
N = 1024

_m = {}
def mat(name):
    if name not in _m:
        im = Image.open(f'{MAT}/materials/{name}.png').convert('RGB')
        if im.size != (N, N):
            im = im.resize((N, N), Image.LANCZOS)
        _m[name] = im
    return _m[name]


def tile_path(folder, name):
    names = json.load(open(f'{folder}/names.json'))
    i = names.index(name)
    return (glob.glob(f'{folder}/{i:02d}_{name}.png') + glob.glob(f'{folder}/{i:03d}_{name}.png'))[0]


def alpha(folder, name):
    return np.array(Image.open(tile_path(folder, name)).convert('RGBA'))[..., 3]


# ---- the two projections we already have, kept identical to apply_mats.py
def panel(im, axis, shade):
    w, h = im.size
    Hpx = LEVEL
    if axis == 'w':
        coef = (-w / 256.0, 0, w, 0.5 * h / Hpx, h / Hpx, h * (Hpx - 512) / Hpx)
    else:
        coef = (w / 256.0, 0, -w, -0.5 * h / Hpx, h / Hpx, h * (Hpx - 256) / Hpx)
    out = im.transform((FW, FH), Image.AFFINE, coef, Image.BICUBIC)
    a = np.array(out).astype(np.float32)
    a[..., :3] *= shade
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def even(im):
    a = np.array(im.convert('RGB')).astype(np.float32)
    a = a[256:768, 256:768]; n = a.shape[0]
    t = np.abs(np.linspace(-1, 1, n)); w = np.clip((1 - t) * 2.2, 0, 1)
    w2 = np.maximum(np.outer(w, np.ones(n)), 0) * np.outer(np.ones(n), w)
    r = np.roll(a, (n // 2, n // 2), (0, 1))
    return np.clip(a * w2[..., None] + r * (1 - w2[..., None]), 0, 255).astype(np.uint8)


def diamond(tex):
    T = Image.fromarray(tex); n = T.width
    hw, hh = 64 * SS, 32 * SS; cx, cy = 64 * SS, 128 * SS
    a = n / (2 * hw); b = n / (2 * hh)
    coef = (a, b, -a * cx - b * (cy - hh), -a, b, a * cx - b * (cy - hh))
    out = T.convert('RGBA').transform((FW, FH), Image.AFFINE, coef, Image.BICUBIC)
    yy, xx = np.mgrid[0:FH, 0:FW]
    inside = (np.abs(xx + 0.5 - cx) / hw + np.abs(yy + 0.5 - cy) / hh) <= 1.0
    o = np.array(out); o[..., 3] = np.where(inside, 255, 0)
    return Image.fromarray(o)


# ---- the new one: a plane we have no formula for, measured off the sprite that already has it
def corners(mask):
    """The four corners of the sloped slab, as the old art drew it.

    Taken as the largest-area quadrilateral on the convex hull rather than by the extremes of
    x+y and x-y: those find the corners of a diamond, and a roof slab is a sheared parallelogram
    whose edges do not run along either of those directions."""
    pts = np.argwhere(mask > 8)[:, ::-1].astype(np.float64)      # (x, y)
    h = pts[ConvexHull(pts).vertices]
    n = len(h)
    best, area = None, -1.0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                for l in range(k + 1, n):
                    q = h[[i, j, k, l]]
                    a = 0.5 * abs(np.dot(q[:, 0], np.roll(q[:, 1], -1)) - np.dot(q[:, 1], np.roll(q[:, 0], -1)))
                    if a > area:
                        area, best = a, q
    return best


def slab(texture, mask, flip=False):
    """Lay a material square onto the slab the mask describes.

    The corners come back anticlockwise from the hull. The texture's own up-axis is put on the
    slab's up-slope edge so the shingle courses run along the eaves rather than down the pitch."""
    q = corners(mask)
    c = q.mean(0)
    ang = np.arctan2(q[:, 1] - c[1], q[:, 0] - c[0])
    q = q[np.argsort(ang)]                       # consistent winding
    top = int(np.argmin(q[:, 1]))                # start from the highest corner on screen
    q = np.roll(q, -top, axis=0)
    if flip:
        q = q[[0, 3, 2, 1]]
    src = np.array([[0, 0], [N, 0], [N, N], [0, N]], np.float64)
    # PIL maps output -> input, so solve frame coords -> texture coords
    A = np.zeros((8, 6)); b = np.zeros(8)
    for i in range(4):
        A[2 * i] = [q[i, 0], q[i, 1], 1, 0, 0, 0]; b[2 * i] = src[i, 0]
        A[2 * i + 1] = [0, 0, 0, q[i, 0], q[i, 1], 1]; b[2 * i + 1] = src[i, 1]
    coef, *_ = np.linalg.lstsq(A, b, rcond=None)
    out = texture.convert('RGBA').transform((FW, FH), Image.AFFINE, tuple(coef), Image.BICUBIC)
    o = np.array(out); o[..., 3] = mask          # the old silhouette, to the pixel
    return Image.fromarray(o)


def shade(im, k):
    a = np.array(im).astype(np.float32); a[..., :3] *= k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


# ---- what goes where.  _x sits over the north wall, _y over the west; measured, not assumed.
#
# The letters do NOT follow the wall set. na_blocks.py is the authority on which gable goes on
# which building, and it says gableR is the BARN's, so it is barn board and not brick; a brick
# house is given the white gable, which is a real enough thing and not ours to change. Read off
# the map builder rather than off the names, which would have put brick on the barn.
GABLE_MAT = {'W': 'siding_white', 'B': 'siding_blue', 'Y': 'siding_yellow', 'R': 'barn_board'}
SLOPES = {'roof_x': ('shingle', 'x'), 'roof_y': ('shingle', 'y'), 'barnroof_y': ('roof_metal', 'y')}
# The barn's roof is galvanised and not the pack's roof_barn, which is red corrugated at mean 69
# against barn board's 76 - the same tone and the same hue, so the whole barn read as one red
# mass and the ridge disappeared. No shade multiplier fixes a hue collision, and the old art had
# a light roof over red walls for the same reason. roof_barn is left unused on purpose.
# A roof is not a wall. The walls run 0.84 and 1.0, and giving the slopes the same pair let the
# barn's roof land on exactly its walls' tone, so the whole building read as one red mass where
# the old art's lighter roof had separated them. A roof faces the sky and a wall does not, so
# the slopes sit above both wall tones. Capped at 1.18 because the materials already carry their
# own lighting and anything higher clips the highlights off the shingle courses.
SLOPE_SHADE = {'x': 1.18, 'y': 1.02}

ng = ns = nf = 0
missing = []
names = set(json.load(open('natiles/names.json')))

# flat tar roof
if 'tar_roof' in names:
    diamond(even(mat('roof_tar'))).save(tile_path('natiles', 'tar_roof')); nf += 1
else:
    missing.append('tar_roof')

# gables: ordinary wall, clipped to the rake the old art drew
for letter, m in GABLE_MAT.items():
    for ax_tag, axis, sh in (('x', 'n', 1.0), ('y', 'w', 0.84)):
        face = panel(mat(m).convert('RGBA'), axis, sh)
        for i in range(4):
            t = f'gable{letter}_{ax_tag}{i}'
            if t not in names:
                missing.append(t); continue
            a = alpha('natiles', t)
            o = np.array(face); o[..., 3] = a
            Image.fromarray(o).save(tile_path('natiles', t)); ng += 1

# sloped planes
for stem, (m, ax_tag) in SLOPES.items():
    tex = mat(m)
    for i in range(4):
        t = f'{stem}{i}'
        if t not in names:
            missing.append(t); continue
        a = alpha('natiles', t)
        if (a > 8).sum() < 400:
            missing.append(t + '(empty)'); continue
        shade(slab(tex, a), SLOPE_SHADE[ax_tag]).save(tile_path('natiles', t)); ns += 1

print('gables %d   slopes %d   flat %d' % (ng, ns, nf))
if missing:
    print('no such tile:', ' '.join(missing))
