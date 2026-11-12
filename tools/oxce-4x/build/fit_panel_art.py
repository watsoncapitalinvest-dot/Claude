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

# THE READOUT IS ONE WINDOW, NOT SIX SLOTS. THE ENGINE SAYS SO.
#
# GeoscapeState builds SEVEN text widgets in the middle of the panel and they
# overlap each other freely, because they are text boxes, not recesses (base
# coords, x = screenWidth-61 => strip-local 18, times 6 for 4x):
#
#   _txtFunds    y 73  h 8    438..486
#   _txtHour/Min y 74  h 16   444..540      funds sits ACROSS the top of these
#   _txtSec      y 80  h 8    480..528
#   _txtWeekday  y 87  h 8    522..570      <- left out of the first list
#   _txtDay/Mon  y 94  h 8    564..612
#   _txtYear     y 101 h 8    606..654      overlaps day/month by one base pixel
#
# Pinned as six separate bands, the monotonic anchor filter dropped every second
# one and the art's metal ribs stayed where text lands: the first build in game
# printed FRIDAY across a rib between the clock recess and the date recess.
#
# So the whole span 438..654 is ONE target band and one deepened recess. That is
# also what the art request asked for and what vanilla does.
READOUT = (438, 654)
TARGET = [(0,66),(72,138),(144,210),(216,282),(288,354),(360,426),
          READOUT,
          (672,750),(756,834),(840,918)]

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

# GROUP THE ART'S BANDS ONTO THE ENGINE'S TEN.
#
# The art draws the readout as several recesses - the delivered file has four
# there, a funds strip, a clock window and two date strips - while the engine has
# ONE band. Pairing art band i to target i therefore runs out of step from the
# clock down and every slot below it is pinned to the wrong rectangle.
#
# The layout is fixed by GeoscapeState, so the grouping is too: the first six art
# bands are the six command buttons, the last three are the three speed rows, and
# whatever lies between them is the readout however many pieces it was drawn in -
# its first top and its last bottom are the only two anchors it needs.
# THE CONTROL CLUSTER IS NOT A SLOT, AND IT MUST NOT BE COUNTED AS ONE.
#
# Below the speed buttons the art draws arrows and dials, which are dark shapes on
# metal and read to the band detector exactly like recesses - the delivered file
# produced 20 bands where the engine has 10. Taking "the last three" then pinned
# three pieces of the dial cluster onto the three speed-button rectangles, and the
# real cluster was stretched over the whole tail: in game it came out as a
# vertical smear where the rotate and zoom controls should be.
#
# Two filters separate them. A slot is taller than a hairline and SHORTER than any
# command button plus a margin; and nothing in the bottom quarter of the panel is a
# slot at all, because the lowest rectangle the engine draws into ends at y=918.
CLUSTER_TOP = 0.75
bands = [b for b in bands
         if 12 <= b[1] - b[0] <= 100 and b[0] < ph * CLUSTER_TOP]
print('bands after dropping the cluster: %d (engine has %d)' % (len(bands), len(TARGET)))
if len(bands) >= 10:
    groups = [[b] for b in bands[:6]] + [bands[6:-3]] + [[b] for b in bands[-3:]]
else:
    groups = [[b] for b in bands]                      # too few to group; pin in order
    print('WARNING only %d bands - pinning in order, check the result' % len(bands))

anchors = [(0.0, 0.0)]
for i, g in enumerate(groups[:len(TARGET)]):
    if not g:
        continue
    anchors.append((float(g[0][0]), float(TARGET[i][0])))
    anchors.append((float(g[-1][1]), float(TARGET[i][1])))
anchors.append((float(ph), 1200.0))
clean = [anchors[0]]
for a in anchors[1:]:
    if a[0] > clean[-1][0] + 0.5 and a[1] > clean[-1][1] + 0.5:
        clean.append(a)
src_y = np.array([c[0] for c in clean]); dst_y = np.array([c[1] for c in clean])
arr = np.asarray(panel).astype(np.float32)
inv = np.interp(np.arange(1200), dst_y, src_y)

# HOW HARD IS THIS FILE BEING BENT?
#
# The warp pins the slots wherever the art put them, so it will always report
# every rectangle on recess - and it buys that by stretching some stretches of
# the picture and squashing others. Past about 1.3 the bevels visibly smear, and
# that is a property of the DELIVERY, not of the fit: art whose slots are nearly
# right needs almost none. Printed so two deliveries can be compared on it
# instead of on how they look after correction.
seg = np.diff(dst_y) / np.maximum(np.diff(src_y), 1e-6)
worst_i = int(np.argmax(np.abs(np.log(seg))))
print('warp: %d segments, scale %.2f to %.2f, worst %.2fx around y=%d'
      % (len(seg), seg.min(), seg.max(), seg[worst_i], int(dst_y[worst_i])))
print('      mean |stretch| %.3f  (0 = the art already fitted)'
      % float(np.abs(np.log(seg)).mean()))
out = np.zeros((1200, 384, 3), np.float32)
for yo in range(1200):
    ys = float(inv[yo]); lo = int(np.floor(ys)); f = ys - lo
    lo = min(max(lo, 0), ph - 1); hi = min(lo + 1, ph - 1)
    out[yo] = arr[lo] * (1 - f) + arr[hi] * f

# DEEPEN THE RECESS UNDER EVERY TEXT RECT.
#
# The warp pins the slot bands, and that is enough for the buttons, which are one
# recess per label. It is NOT enough for the readout block, because the engine's
# own widget rects OVERLAP there and no art can have a separate recess for each:
#
#   _txtFunds  y=73 h=8   -> 438..486        the funds line sits ACROSS the top
#   _txtHours  y=74 h=16  -> 444..540        of the clock's digit box
#   _txtDay    y=94 h=8   -> 564..612        and the year row overlaps the
#   _txtYear   y=101 h=8  -> 606..654        day/month row by one base pixel
#
# So the art draws metal ribs between its recesses and those ribs land inside a
# text rect. Measured on the fitted art, funds/hours/minutes/seconds/year all came
# out 74-90% dark, i.e. pale digits over lit metal for the rest.
#
# Each rect is therefore deepened to its OWN recess colour - the median of the dark
# pixels already inside it, so a rib takes the shade of the recess it interrupts
# rather than a flat black - with the mask feathered 3px so no edge is stamped on.
RECTS = [(6,0,378,66),(6,72,378,66),(6,144,378,66),(6,216,378,66),(6,288,378,66),
         (6,360,378,66),
         (18, READOUT[0], 354, READOUT[1]-READOUT[0]),   # funds, clock, weekday, date
         (6,672,186,78),(198,672,186,78),(6,756,186,78),(198,756,186,78),
         (6,840,186,78),(198,840,186,78)]
LIT = 210.0
for x, y, w, h in RECTS:
    blk = out[y:y+h, x:x+w]
    lum = blk.sum(axis=2)
    dk = blk[lum < LIT]
    if len(dk) < 50:
        continue                       # no recess to take a colour from; leave it
    tone = np.median(dk, axis=0)
    m = np.clip((lum - LIT) / 120.0, 0.0, 1.0)      # 0 where already dark
    pad = np.zeros((h + 6, w + 6), np.float32); pad[3:-3, 3:-3] = m
    for _ in range(3):                              # cheap separable feather
        pad = (pad + np.roll(pad, 1, 0) + np.roll(pad, -1, 0) +
               np.roll(pad, 1, 1) + np.roll(pad, -1, 1)) / 5.0
    m = pad[3:-3, 3:-3][:, :, None]
    out[y:y+h, x:x+w] = blk * (1 - m) + tone * m

canvas = Image.new('RGBA', (1920, 1200), (0, 0, 0, 0))
canvas.paste(Image.fromarray(out.astype(np.uint8)).convert('RGBA'), (1536, 0))
canvas.save(OUT)
print('written %s  1920x1200 RGBA, panel at x=1536' % OUT)
