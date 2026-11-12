"""Flatten a photo-ish Mixamo texture sheet to the Sunbow cartoon finish.

    python3 -I flatten.py IN.png OUT.png [--k 8] [--size 1024] [--hair]

Borrowed from ../../cartoonize.py (edge-preserving smooth, tones from a hard-smoothed
lightness) but snapped harder, to flat garment colours:
  1. strong edge-preserving smooth: bilateral x3, then mean-shift
  2. skin found by a YCrCb range and clustered on its own (1 colour), so a face never
     merges with an orange shirt; everything else k-means to K flat colours (Lab, L
     down-weighted so a garment's baked folds join its own colour, not a new cluster)
  3. one cel shadow per colour: where the heavily smoothed lightness falls well below
     that colour's own median, the pixel takes the lit colour x 0.66
  4. small specks (< ~0.03 % of the sheet) are absorbed by their neighbours, so a logo
     survives but grain does not
--hair: hair sheets keep their alpha and get only the smooth + a 3-colour snap
(the ink pass repaints hair as one two-tone mass anyway).
Alpha is passed through untouched.
"""
import argparse
import cv2
import numpy as np
from scipy import ndimage as ndi

SHADOW = 0.66


def kmeans(X, k, seed=1):
    X = X.astype(np.float32)
    samp = X[np.random.default_rng(seed).choice(len(X), min(len(X), 60000), replace=False)]
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, _, C = cv2.kmeans(samp, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    lab = np.empty(len(X), np.int32)
    for i in range(0, len(X), 200000):
        d = ((X[i:i + 200000, None, :] - C[None]) ** 2).sum(-1); lab[i:i + 200000] = d.argmin(1)
    return lab, C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--k', type=int, default=8); ap.add_argument('--size', type=int, default=1024)
    ap.add_argument('--hair', action='store_true')
    ap.add_argument('--notskin', help='mask png: white where the sheet belongs to a clothing mesh (never skin)')
    a = ap.parse_args()
    im = cv2.imread(a.src, cv2.IMREAD_UNCHANGED)
    if im.ndim == 2: im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGRA)
    if im.shape[2] == 3: im = cv2.cvtColor(im, cv2.COLOR_BGR2BGRA)
    im = cv2.resize(im, (a.size, a.size), interpolation=cv2.INTER_AREA)
    bgr, alpha = im[..., :3].copy(), im[..., 3]
    s = a.size / 1024.0
    sm = bgr
    for _ in range(3):
        sm = cv2.bilateralFilter(sm, int(9 * s) | 1, 40, 7 * s)
    sm = cv2.pyrMeanShiftFiltering(sm, int(8 * s), 24)
    H, W = sm.shape[:2]
    lab = cv2.cvtColor(sm, cv2.COLOR_BGR2LAB).astype(np.float32)
    if a.hair:
        X = lab.reshape(-1, 3) * np.array([0.6, 1, 1], np.float32)
        L, C = kmeans(X, 3)
        cen = np.array([np.median(sm.reshape(-1, 3)[L == i], 0) if (L == i).any() else (0, 0, 0) for i in range(3)])
        out = cen[L].reshape(H, W, 3)
        cv2.imwrite(a.dst, np.dstack([out.clip(0, 255).astype(np.uint8), alpha])); return
    ycc = cv2.cvtColor(sm, cv2.COLOR_BGR2YCrCb)
    skin = (ycc[..., 1] > 136) & (ycc[..., 1] < 182) & (ycc[..., 2] > 98) & (ycc[..., 2] < 132) & (ycc[..., 0] > 45)
    skin = ndi.binary_opening(skin, iterations=2)
    skin = ndi.binary_closing(skin, iterations=int(3 * s)) & (ycc[..., 0] > 45)
    if a.notskin:
        ns = cv2.resize(cv2.imread(a.notskin, cv2.IMREAD_GRAYSCALE), (W, H), interpolation=cv2.INTER_NEAREST) > 127
        skin &= ~ns
    labels = np.zeros((H, W), np.int32); cents = []
    X = lab.reshape(-1, 3) * np.array([0.55, 1, 1], np.float32)
    flat_skin = skin.reshape(-1)
    nxt = 0
    for mask, k in ((~flat_skin, a.k), (flat_skin, 1)):
        if mask.sum() < 500: continue
        L = kmeans(X[mask], k)[0] if k > 1 else np.zeros(int(mask.sum()), np.int32)
        labels.reshape(-1)[mask] = L + nxt
        nxt += k
    # absorb specks into the surrounding colour (majority filter on labels)
    lab_m = ndi.median_filter(labels, size=max(3, int(5 * s)) | 1)
    labels = lab_m
    flat = sm.reshape(-1, 3).astype(np.float32)
    lit = np.zeros((nxt, 3), np.float32)
    for i in range(nxt):
        sel = labels.reshape(-1) == i
        if sel.any():
            v = flat[sel]; lum = v.mean(1)
            # the lit colour: the brighter half of the cluster, so baked shading doesn't darken it
            lit[i] = np.median(v[lum >= np.median(lum)], 0)
    # cel shadow from the hard-smoothed lightness, relative to the colour's own median
    Lp = lab[..., 0]
    Lb = cv2.GaussianBlur(Lp, (0, 0), 5 * s)
    out = lit[labels]
    shade = np.zeros((H, W), bool)
    for i in range(nxt):
        sel = labels == i
        if sel.sum() < 50: continue
        med = np.median(Lb[sel])
        shade |= sel & (Lb < med - (36 if (skin[sel].mean() > 0.5) else 22))
    shade = ndi.binary_opening(shade, iterations=max(1, int(2 * s)))
    shade = ndi.median_filter(shade.astype(np.uint8), size=max(3, int(5 * s)) | 1).astype(bool)
    out[shade] *= SHADOW
    cv2.imwrite(a.dst, np.dstack([out.clip(0, 255).astype(np.uint8), alpha]))


if __name__ == '__main__':
    main()
