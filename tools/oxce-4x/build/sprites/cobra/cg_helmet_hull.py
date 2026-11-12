"""Crimson Guard helmet carved from the toy photos (visual hull): front outline x side outline -> 3D shape.
Colour by projection: black faceplate + silver crest from the front photo, black mask sides from the side photo,
a straight silver eye slit drawn in the front view. Output: npz (verts in normalised units, faces, per-face material)
  units: z 0 = faceplate bottom (chin), 1 = helmet crown; x/y in the same units, centred.
Materials: 0 red shell, 1 black faceplate, 2 silver slit, 3 silver crest."""
import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure

PH = '/mnt/user-data/uploads/Reference/figure_photos/crimson-guard/angles/1985-crimson-guard-v1-{}-by-phillip-donnelly_orig.jpg'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/fac/cg_hull.npz'

def head_mask(img, box, chin_y):
    """silhouette of helmet+faceplate inside box, cut at the chin row (neck below is excluded)"""
    a = np.asarray(img.crop(box)).astype(int)
    fg = (a.min(-1) < 205) | (np.ptp(a, -1) > 45)
    fg[chin_y - box[1]:] = False
    fg = ndi.binary_fill_holes(ndi.binary_opening(fg, iterations=2))
    lab, n = ndi.label(fg); sz = ndi.sum(fg, lab, range(1, n + 1)); fg = lab == (1 + int(np.argmax(sz)))
    return fg, a

front = Image.open(PH.format('a')).convert('RGB'); side = Image.open(PH.format('c')).convert('RGB')
# head boxes (photo pixels) and chin rows, read off the crops: front x 200-600, side x 100-450 (figure faces +x in the side photo)
Fm, Fa = head_mask(front, (200, 0, 600, 330), 306)
Sm, Sa = head_mask(side, (100, 0, 450, 300), 258)
def zspan(m): ys = np.nonzero(m.any(1))[0]; return ys.min(), ys.max()
fz0, fz1 = zspan(Fm); sz0, sz1 = zspan(Sm)
fH, sH = fz1 - fz0, sz1 - sz0
print('front head px', fH, 'side head px', sH)
# ---- lofted surface: one rounded slice per height; width from the front outline, front/back from the side outline ----
NZ, K, P = 170, 224, 2.6                    # slices, points per slice, superellipse exponent (2 = ellipse, higher = squarer)
def prof(m, z0, H):
    rows = np.arange(m.shape[0]); out = []
    for z in np.linspace(0.0, 1.0, NZ):
        r = int(np.clip(round(z0 + (1 - z) * H), 0, m.shape[0] - 1)); cols = np.nonzero(m[r])[0]
        out.append((cols.min(), cols.max()) if len(cols) else (np.nan, np.nan))
    o = np.array(out, float)
    for k in range(2):                      # fill gaps, then smooth top-to-bottom (no stair-steps)
        msk = np.isnan(o[:, k]); o[msk, k] = np.interp(np.nonzero(msk)[0], np.nonzero(~msk)[0], o[~msk, k])
    o = ndi.median_filter(o, size=(9, 1))                       # kill seam-line / crest spikes in the outline
    return ndi.gaussian_filter1d(o, 7.0, axis=0)
fp = prof(Fm, fz0, fH); sp = prof(Sm, sz0, sH)
fxc = np.median((fp[:, 0] + fp[:, 1]) / 2)
zs = np.linspace(0, 1, NZ)
L, R = (fp[:, 0] - fxc) / fH, (fp[:, 1] - fxc) / fH
# side photo: the figure faces +x(photo) -> our front is -y: front = -(max col), back = -(min col)
sxc = np.median((sp[:, 0] + sp[:, 1]) / 2)
YF, YB = -(sp[:, 1] - sxc) / sH, -(sp[:, 0] - sxc) / sH
th = np.linspace(0, 2 * np.pi, K, endpoint=False)
c, s = np.cos(th), np.sin(th)
rr_ = (np.abs(c) ** P + np.abs(s) ** P) ** (-1 / P); ex = c * rr_; ey = s * rr_          # smooth superellipse (no seam)
verts = []
for i, z in enumerate(zs):
    xc, hw = (L[i] + R[i]) / 2, (R[i] - L[i]) / 2
    yc, hd = (YF[i] + YB[i]) / 2, (YB[i] - YF[i]) / 2
    # the faceplate juts forward only in the middle: pull the front corners back toward the helmet line
    wfront = np.clip(-ey / 0.35, 0, 1) ** 2 * (3 - 2 * np.clip(-ey / 0.35, 0, 1))          # smooth, no kink at the sides
    cap = np.sqrt(max(0.0, 1 - ((z - 0.86) / 0.145) ** 2)) if z > 0.86 else 1.0               # round crown, not a flat top
    hw, hd = hw * (0.25 + 0.75 * cap), hd * (0.25 + 0.75 * cap)
    pull = wfront * (np.abs(ex) ** 2.2) * 0.38 * hd
    verts.append(np.stack([xc + hw * ex, yc + hd * ey + pull, np.full(K, z)], 1))
v = np.concatenate(verts)
faces = []
for i in range(NZ - 1):
    for k in range(K):
        a0 = i * K + k; a1 = i * K + (k + 1) % K; b0 = a0 + K; b1 = a1 + K
        faces += [(a0, a1, b1), (a0, b1, b0)]
top = len(v); v = np.vstack([v, [[np.mean(verts[-1][:, 0]), np.mean(verts[-1][:, 1]), 1.0]]])
faces += [((NZ - 1) * K + k, (NZ - 1) * K + (k + 1) % K, top) for k in range(K)]
f = np.array(faces, np.int32)
# smooth the shell itself: average each ring vertex with its neighbours around and up/down (keeps the outline, removes ripples)
g = v[:NZ * K].reshape(NZ, K, 3)
for _ in range(30):
    g2 = g.copy()
    g2[1:-1] = (g[1:-1] * 2 + np.roll(g[1:-1], 1, 1) + np.roll(g[1:-1], -1, 1) + g[:-2] + g[2:]) / 6
    g = g2
v[:NZ * K] = g.reshape(-1, 3)
def sample(m, z0, H, xc, u, z):   # u, z in normalised units -> mask lookup
    r = np.clip(np.round(z0 + (1 - z) * H).astype(int), 0, m.shape[0] - 1)
    c = np.round(xc + u * H).astype(int)
    ok = (c >= 0) & (c < m.shape[1]); rr, cc = np.broadcast_arrays(r, c)
    out = np.zeros(rr.shape, bool); out[ok] = m[rr[ok], cc[ok]]
    return out
# face normals + centres
tri = v[f]; fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
fc = tri.mean(1)
cen = v.mean(0)
if np.mean(np.sum(fn * (fc - cen), 1)) < 0: f = f[:, ::-1]; fn = -fn   # outward normals
def colour_at(a, z0, H, xc, u, z):
    r = np.clip(np.round(z0 + (1 - z) * H).astype(int), 0, a.shape[0] - 1); c = np.clip(np.round(xc + u * H).astype(int), 0, a.shape[1] - 1)
    return a[r, c]
cF = colour_at(Fa, fz0, fH, fxc, fc[:, 0], fc[:, 2]); cS = colour_at(Sa, sz0, sH, sxc, -fc[:, 1], fc[:, 2])
def is_black(c): return (c.max(-1) < 95) | ((c.max(-1) < 150) & (np.ptp(c, -1) < 30) & (c.mean(-1) < 120))
def is_silver(c): return (c.min(-1) > 150) & (np.ptp(c, -1) < 40)
mat = np.zeros(len(f), np.int32)
plate2d = is_black(Fa.reshape(-1, 3)).reshape(Fa.shape[:2]) & Fm
plate2d = ndi.binary_fill_holes(ndi.binary_closing(ndi.binary_opening(plate2d, iterations=3), iterations=8))
plate2d = ndi.binary_closing(plate2d, structure=np.ones((25, 25)))                  # close the notch under the crest
plate2d = ndi.gaussian_filter(plate2d.astype(float), 9) > 0.5                        # smooth faceplate outline
# angle the faceplate like the toy's: widest across the eyes, sides slanting in to a narrower chin
rows_ = np.nonzero(plate2d.any(1))[0]; pt_, pb_ = rows_.min(), rows_.max()
cols_ = np.nonzero(plate2d[pt_ + int(0.30 * (pb_ - pt_))])[0]; pc_ = (cols_.min() + cols_.max()) / 2; hw_top = (cols_.max() - cols_.min()) / 2
RR, CC = np.mgrid[0:plate2d.shape[0], 0:plate2d.shape[1]]
fr = np.clip((RR - (pt_ + 0.30 * (pb_ - pt_))) / max(0.70 * (pb_ - pt_), 1), 0, 1)        # 0 at eye line .. 1 at chin
plate2d &= np.abs(CC - pc_) < hw_top * (1.0 - 0.42 * fr)
plate2d = ndi.gaussian_filter(plate2d.astype(float), 4) > 0.5
yc_z = np.interp(fc[:, 2], zs, (YF + YB) / 2)
inplate = sample(plate2d, fz0, fH, fxc, fc[:, 0], fc[:, 2])
mat[inplate & (fc[:, 1] < yc_z) & (fn[:, 1] < 0.25)] = 1                             # faceplate (front + muzzle sides), never the back
# eye slit: straight band in the front view, centred on the faceplate, at eye level
prow = np.nonzero(plate2d.any(1))[0]; ptop, pbot = prow.min(), prow.max()
slit_row = ptop + 0.30 * (pbot - ptop); slit_z = 1 - (slit_row - fz0) / fH
pcols = np.nonzero(plate2d[int(slit_row)])[0]; pcx = ((pcols.min() + pcols.max()) / 2 - fxc) / fH; phw = (pcols.max() - pcols.min()) / 2 / fH
slit_curve = slit_z - 0.075 * ((fc[:, 0] - pcx) / max(phw * 0.60, 1e-3)) ** 2 * (phw * 0.60)   # gentle arch: ends dip, following the faceplate
mat[(mat == 1) & (fn[:, 1] < -0.4) & (np.abs(fc[:, 2] - slit_curve) < 0.024) & (np.abs(fc[:, 0] - pcx) < phw * 0.60)] = 2
# crest: clean stepped badge (3 tiers, narrowing upward) where the toy's silver crest sits, centred on the faceplate
crest2d = is_silver(Fa.reshape(-1, 3)).reshape(Fa.shape[:2]) & Fm & ~plate2d
crest2d[ptop - 4:] = False                                                       # only above the faceplate (no faceplate shine)
lab_, n_ = ndi.label(ndi.binary_opening(crest2d, iterations=1)); sz_ = ndi.sum(lab_ > 0, lab_, range(1, n_ + 1))
cr, cc = np.nonzero(lab_ == 1 + int(np.argmax(sz_)))
cz0 = 1 - (cr.max() - fz0) / fH; cz1 = 1 - (cr.min() - fz0) / fH
cw = (np.percentile(cc, 95) - np.percentile(cc, 5)) / 2 / fH
tier = np.clip(((fc[:, 2] - cz0) / max(cz1 - cz0, 1e-3) * 3).astype(int), 0, 2)
cz0 = min(cz0, 1 - (ptop - fz0) / fH + 0.015); cw *= 1.25
tier = np.clip(((fc[:, 2] - cz0) / max(cz1 - cz0, 1e-3) * 3).astype(int), 0, 2)
crest = (fn[:, 1] < -0.15) & (fc[:, 2] > cz0) & (fc[:, 2] < cz1) & (np.abs(fc[:, 0] - pcx) < cw * (1.0 - 0.22 * tier)) & (mat == 0)
mat[crest] = 3
print('crest z', round(cz0, 3), round(cz1, 3), 'half-width', round(cw, 3), 'slit z', round(slit_z, 3))
np.savez(OUT, v=v.astype(np.float32), f=f.astype(np.int32), mat=mat, slit_z=slit_z)
print('hull verts', len(v), 'faces', len(f), 'materials', np.bincount(mat), 'bbox', v.min(0).round(3), v.max(0).round(3))
