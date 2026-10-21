#!/usr/bin/env python3
"""Lift the Skirt Chasers wordmark off its paper so it can sit on cover art.

    python3 scripts/cut_wordmark.py --src wordmark-art.png --out wordmark.png

John's graphics AI returns the wordmark painted on a sheet of warm cream
(246, 239, 222). On the flat cream masthead panel that is invisible; straight
onto a cover photograph it is a rectangle of the wrong colour sitting over the
picture. So the paper is cut away and the file is written with an alpha
channel.

Two things make this harder than a colour key.

The figure wears cream. The lit side of her top and the highlight down her sock
read within a few levels of the paper itself, so keying on colour alone punches
holes through her. The paper is therefore cut by CONNECTED REGION rather than
by colour: every patch of cream goes except the patches that sit inside the
figure. That also takes care of the counters of the letters and the gaps
between the letters and the swash, which are the same sheet of paper reaching
in, and of the specks of near-cream scattered through the art.

The letters are painted with a drop shadow. A hard cut leaves either a grey
halo (shadow kept opaque) or a scissored edge (shadow cut away), so the cut is
a ramp: inside the band where the paper used to be, how opaque a pixel ends up
depends on how far it is from the paper colour. Cream goes to nothing, shadow
survives as something partly transparent and dark, and the gold keyline on the
letter edges stays solid.

Needs numpy and scipy, which the image builders otherwise do not: this runs
once when a new wordmark arrives, not on every issue.
"""
import argparse, os
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Where the figure is in the 1536x1024 art, as fractions, so the box survives a
# re-render at another size. Cream inside it is her; cream outside it is paper.
FIGURE = (0.586, 0.039, 0.911, 0.605)


def cut(src, out, tol=16, worn=7, lo=12, hi=46, spread=16, figure=FIGURE, trim=True):
    im = Image.open(src).convert('RGB')
    a = np.asarray(im).astype(np.int16)
    h, w = a.shape[:2]

    # The paper is whatever the border is, not a colour typed in here: the AI
    # renders a slightly different cream every time it is asked.
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    paper = np.median(edge, axis=0)
    diff = np.abs(a - paper).max(axis=2)

    lab, n = ndimage.label(diff <= tol, structure=np.ones((3, 3)))
    x0, y0, x1, y1 = (figure[0] * w, figure[1] * h, figure[2] * w, figure[3] * h)
    # Being inside the figure is not enough on its own: the gaps behind her
    # knee and under her foot are the same sheet of paper reaching in, and
    # keeping them left two cream blobs floating against her leg. The paper is
    # the paper exactly; her cream is a few levels warmer and darker than it.
    # So a patch inside the box survives only if it is off-paper as well.
    keep = np.zeros(n + 1, bool)
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        cx = (sl[1].start + sl[1].stop) / 2
        cy = (sl[0].start + sl[0].stop) / 2
        if not (x0 <= cx <= x1 and y0 <= cy <= y1):
            continue
        px = a[sl][lab[sl] == i]
        keep[i] = np.abs(np.median(px, axis=0) - paper).max() >= worn
    bg = (lab > 0) & ~keep[lab]

    alpha = np.full((h, w), 255, np.int32)
    band = ndimage.binary_dilation(bg, np.ones((3, 3)), iterations=spread) & ~keep[lab]
    ramp = np.clip((diff - lo) / float(hi - lo), 0, 1) * 255
    alpha[band] = ramp[band]
    alpha[bg] = 0

    rgba = np.dstack([np.asarray(im), alpha.astype(np.uint8)])
    img = Image.fromarray(rgba, 'RGBA')
    if trim:
        img = img.crop(img.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox())
    img.save(out)
    cut_share = float(bg.mean())
    print(f'  {os.path.basename(src)} {w}x{h} -> {os.path.basename(out)} {img.size[0]}x{img.size[1]} '
          f'({os.path.getsize(out)//1024}kb, paper {tuple(int(v) for v in paper)}, '
          f'{cut_share:.0%} cut away)')
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--tol', type=int, default=16, help='how close to the paper counts as paper')
    ap.add_argument('--no-trim', action='store_true')
    a = ap.parse_args()
    j = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p)
    cut(j(a.src), j(a.out), tol=a.tol, trim=not a.no_trim)


if __name__ == '__main__':
    main()
