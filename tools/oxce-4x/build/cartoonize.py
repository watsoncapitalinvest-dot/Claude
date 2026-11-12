"""Push a detailed illustration on magenta toward the approved cartoon finish.

    python3 cartoonize.py IN.png OUT.png [--tones 3] [--ink 3] [--strength 1.0]

Shapes and markings are kept. Defaults are tuned to the base map's room shells
(Resources/Base/shells): flat, slightly muted colour, thin dark outline. What changes:
  - fine texture and soft gradients are smoothed away (edge-preserving filter)
  - shading inside each colour is snapped to a few flat cel tones
  - a bold dark outline round the silhouette, a thinner one on the strong
    internal edges (part boundaries, not panel lines)
Background stays pure FF00FF with a hard edge.
"""
import argparse
import cv2
import numpy as np

INK = np.array([18, 26, 40], np.float32)  # BGR of 40,26,18 - the soldiers' ink


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--tones', type=int, default=3, help='light steps per colour')
    ap.add_argument('--ink', type=float, default=3.0, help='outline width at 1024 px')
    ap.add_argument('--strength', type=float, default=0.7, help='0..1 blend toward the flat version')
    ap.add_argument('--sat', type=float, default=0.85, help='saturation multiplier')
    a = ap.parse_args()

    img = cv2.imread(a.src, cv2.IMREAD_COLOR)
    h, w = img.shape[:2]
    k = max(h, w) / 1024.0
    mag = (img[:, :, 0] > 200) & (img[:, :, 1] < 60) & (img[:, :, 2] > 200)
    mask = (~mag).astype(np.uint8)
    # pull the magenta out of the edge pixels before filtering so it does not bleed in
    fill = cv2.inpaint(img, mag.astype(np.uint8), 3, cv2.INPAINT_TELEA)

    # 1. smooth texture, keep edges
    sm = fill.copy()
    for _ in range(3):
        sm = cv2.bilateralFilter(sm, int(9 * k) | 1, 40, 7 * k)

    # 2. cel tones: keep each pixel's hue and saturation, snap its lightness
    hls = cv2.cvtColor(sm, cv2.COLOR_BGR2HLS).astype(np.float32)
    # lightness smoothed hard first so the tone bands follow the big forms, not the noise
    # and applied as an offset, so the broad shading flattens while small detail (markings,
    # stars, lights) keeps its own contrast and stays sharp
    Lp = hls[:, :, 1] / 255.0
    L = cv2.GaussianBlur(Lp, (0, 0), 6 * k)
    n = a.tones
    Lq = (np.floor(L * n) + 0.5) / n
    # very dark and very light stay where they are (black tails, white wings)
    Lq = np.where(L < 0.12, L, np.where(L > 0.9, np.maximum(L, 0.92), Lq))
    hls[:, :, 1] = np.clip((Lp + (Lq - L)) * 255, 0, 255)
    # a touch muted, like the base map's olive and concrete
    hls[:, :, 2] = hls[:, :, 2] * a.sat
    flat = cv2.cvtColor(hls.astype(np.uint8), cv2.COLOR_HLS2BGR)
    # keep small bright detail (markings, lights) from the smoothed picture
    out = cv2.addWeighted(flat, a.strength, sm, 1 - a.strength, 0).astype(np.float32)

    # 3. ink: strong internal edges thin, silhouette bold
    # the drawing's own strong dark lines (black-hat: darker than their surroundings)
    g = cv2.cvtColor(fill, cv2.COLOR_BGR2GRAY)
    bh = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(7 * k) | 1,) * 2))
    # only lines that are dark in their own right - a red stripe on white is a marking, not ink
    hsv = cv2.cvtColor(fill, cv2.COLOR_BGR2HSV)
    dark = (hsv[:, :, 2] < 120) | ((hsv[:, :, 2] < 170) & (hsv[:, :, 1] < 80))
    ed = ((bh > 55) & dark).astype(np.uint8) * 255
    n_, lab, st, _ = cv2.connectedComponentsWithStats(ed, 8)
    keep = np.zeros(n_, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= int(40 * k * k)
    ed = keep[lab].astype(np.uint8) * 255
    sil = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 1))) - cv2.erode(
        mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(a.ink * k) * 2 + 1,) * 2))
    inner = (ed > 0).astype(np.float32) * 0.85
    outer = sil.astype(np.float32)
    alpha = np.maximum(inner, outer)[:, :, None]
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)[:, :, None] if alpha.ndim == 2 else cv2.GaussianBlur(alpha, (3, 3), 0)[:, :, None]
    out = out * (1 - alpha) + INK * alpha

    out[mag] = (255, 0, 255)
    cv2.imwrite(a.dst, np.clip(out, 0, 255).astype(np.uint8))


if __name__ == '__main__':
    main()
