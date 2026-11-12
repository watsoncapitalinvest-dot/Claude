#!/usr/bin/env python3
"""Fit a delivered geoscape panel painting onto the engine's actual geometry.

    python3 build/fit_panel_art.py <delivered.png> <out_hi.png>

Three deliveries in, the graphics AI gets the LOOK right every time and the
geometry wrong every time, in the same three ways. So this does the correcting
rather than asking again:

  crop   the panel is cut away from whatever surrounds it. Twice the
         "transparency" came back as a painted grey chequer in an RGB file with
         no alpha at all, so the cut is by content, not by alpha.
  scale  to exactly 384 x 1200 - the right-hand 20% of a 1920x1200 canvas, which
         is where GEOBORD's panel lives (base x 256..320 of 320).
  warp   the slots drift low and the drift accumulates down the panel - 38 to 60
         px by the bottom row, which is most of a button's height. A monotonic
         piecewise vertical remap pins every measured slot edge onto the
         rectangle the engine actually draws its text into.

The target rectangles are computed from GeoscapeState's own widget constructors,
not measured off a screenshot: buttons at screenWidth-63 and screenHeight/2-100
stepping by 12, the clock block, the date rows, and six speed buttons 31x13.
"""
import sys
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 320, 200
TARGET = [(0,66),(72,138),(144,210),(216,282),(288,354),(360,426),
          (438,486),(444,540),(564,612),(606,654),(672,750),(756,834),(840,918)]

# USE ALPHA WHEN THERE IS ANY, CONTENT WHEN THERE IS NOT.
# Deliveries have arrived both ways: RGB with a grey chequer painted into the
# pixels, and RGBA with real transparency. Converting the second to RGB turns the
# transparent region BLACK, which the chequer test reads as panel - so it kept the
# whole canvas and found no slots at all.
raw = Image.open(SRC)
has_alpha = raw.mode in ('RGBA', 'LA') and raw.convert('RGBA').split()[3].getextrema()[0] < 250
im = raw.convert('RGB')
px = im.load(); w, h = im.size
if has_alpha:
    ap = raw.convert('RGBA').split()[3].load()
    solid = lambda x, y: ap[x, y] > 128
    print('source has real alpha - cropping by it')
else:
    solid = lambda x, y: not (px[x, y][0] > 190 and px[x, y][1] > 190 and px[x, y][2] > 190)
    print('source has no alpha - cropping by content (painted chequer)')

cols = [x for x in range(w) if sum(1 for y in range(0, h, 7) if solid(x, y)) > h // 14]
rows = [y for y in range(h) if sum(1 for x in range(min(cols), max(cols), 7) if solid(x, y)) > (max(cols)-min(cols)) // 14]
panel = im.crop((min(cols), min(rows), max(cols)+1, max(rows)+1)).resize((384, max(rows)-min(rows)+1), Image.LANCZOS)
ph = panel.height; ppx = panel.load()
print('panel cropped from x %d..%d, set to 384 wide, height %d' % (min(cols), max(cols), ph))

dark = [sum(1 for x in range(0, 384, 3) if sum(ppx[x, y]) < 170) for y in range(ph)]
thr = max(dark) * 0.45
bands = []; s = None
for y, v in enumerate(dark):
    if v >= thr and s is None: s = y
    elif v < thr and s is not None:
        if y - s > 4: bands.append((s, y))
        s = None
print('slot bands found: %d (expected about %d)' % (len(bands), len(TARGET)))

anchors = [(0.0, 0.0)]
for i in range(min(len(bands), len(TARGET))):
    anchors.append((float(bands[i][0]), float(TARGET[i][0])))
    anchors.append((float(bands[i][1]), float(TARGET[i][1])))
anchors.append((float(ph), 1200.0))
clean = [anchors[0]]
for a in anchors[1:]:
    if a[0] > clean[-1][0] + 0.5 and a[1] > clean[-1][1] + 0.5:
        clean.append(a)
src_y = np.array([c[0] for c in clean]); dst_y = np.array([c[1] for c in clean])
arr = np.asarray(panel).astype(np.float32)
inv = np.interp(np.arange(1200), dst_y, src_y)
out = np.zeros((1200, 384, 3), np.float32)
for yo in range(1200):
    ys = float(inv[yo]); lo = int(np.floor(ys)); f = ys - lo
    lo = min(max(lo, 0), ph - 1); hi = min(lo + 1, ph - 1)
    out[yo] = arr[lo] * (1 - f) + arr[hi] * f

canvas = Image.new('RGBA', (1920, 1200), (0, 0, 0, 0))
canvas.paste(Image.fromarray(out.astype(np.uint8)).convert('RGBA'), (1536, 0))
canvas.save(OUT)
print('written %s  1920x1200 RGBA, panel at x=1536' % OUT)
