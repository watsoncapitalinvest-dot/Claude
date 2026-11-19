#!/usr/bin/env python3
"""The mouse pointer (John 19 Nov 17:29 "change the cursor to something more G.I. Joe"): a cartoon arrow in the
tablet's colours - gold with a thick ink outline, a shaded half, and a white star with a red and blue stripe on its
tail like the G.I. Joe flag. The tip is the top-left pixel (the engine draws the picture from the mouse position).

    python3 build/make_cursor.py    ->  mod/Resources/UI/cursor.png (88 x 134, drawn at 4x and reduced)
"""
import os, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'mod', 'Resources', 'UI', 'cursor.png')
K = 4                                  # supersample
W, H = 88, 134
def P(pts): return [(x * K, y * K) for x, y in pts]
im = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
arrow = [(3, 3), (3, 104), (27, 81), (42, 122), (58, 115), (43, 76), (76, 76)]
ink, gold, shade = (23, 24, 28, 255), (232, 185, 35, 255), (190, 140, 20, 255)
d.polygon(P(arrow), fill=ink)                                   # the outline: the shape, then a smaller fill
inner = [(9, 17), (9, 90), (29, 70), (45, 112), (52, 109), (36, 70), (63, 70)]
d.polygon(P(inner), fill=gold)
d.polygon(P([(9, 17), (9, 90), (29, 70), (36, 70)]), fill=shade)  # the shaded left half
d.line(P([(12, 22), (40, 52)]), fill=(255, 236, 160, 255), width=3 * K)   # a highlight along the edge
# the flag on the tail: white star on blue, red stripe
cx, cy, r = 20, 48, 7
star = [(cx + (r if i % 2 == 0 else r * 0.42) * math.sin(i * math.pi / 5), cy - (r if i % 2 == 0 else r * 0.42) * math.cos(i * math.pi / 5)) for i in range(10)]
d.ellipse(P([(cx - 9, cy - 9), (cx + 9, cy + 9)]), fill=(14, 60, 140, 255), outline=ink, width=2 * K)
d.polygon(P(star), fill=(255, 255, 255, 255))
im = im.resize((W, H), Image.LANCZOS)
im.save(OUT)
print('cursor written', OUT)
