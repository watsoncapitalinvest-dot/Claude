#!/usr/bin/env python3
"""Put a playset (rendered straight down by compose_room.py --floor none) into a painted room.

    python3 into_room.py shell_hi.png playset.png out.png [--fill F] [--inset PX]

The painted room keeps its walls, doors and floor colour: everything inside the walls (inset from
the edge) is cleared to the room's own floor colour, and the playset is laid in the middle, scaled
to --fill of the inner area. Works for any footprint (the shell may be a whole 2x1 or 2x2 room)."""
import sys
import numpy as np
from PIL import Image, ImageFilter

a = sys.argv[1:]
shell, play, out = a[0], a[1], a[2]
fill = float(a[a.index('--fill') + 1]) if '--fill' in a else 0.92
inset = int(a[a.index('--inset') + 1]) if '--inset' in a else 26
S = Image.open(shell).convert('RGBA'); P = Image.open(play).convert('RGBA')
A = np.asarray(S).astype(np.int32)
W, H = S.size
# the floor colour: the most common colour in a strip just inside the walls
strip = np.concatenate([A[inset:inset + 4, inset:W - inset].reshape(-1, 4), A[H - inset - 4:H - inset, inset:W - inset].reshape(-1, 4)])
q = (strip[:, :3] // 8) * 8
vals, counts = np.unique(q, axis=0, return_counts=True)
floor = vals[counts.argmax()] + 4
# a little texture so the cleared floor is not a flat slab: blur the original interior heavily and pull it to the floor colour
inner = S.crop((inset, inset, W - inset, H - inset)).filter(ImageFilter.GaussianBlur(18))
I = np.asarray(inner).astype(np.float32)
I[..., :3] = I[..., :3] * 0.25 + floor * 0.75
I[..., 3] = 255
out_im = S.copy(); out_im.paste(Image.fromarray(I.astype(np.uint8), 'RGBA'), (inset, inset))
# the playset, trimmed to its pixels and fitted to the inner area
bb = P.getchannel('A').point(lambda v: 255 if v > 16 else 0).getbbox()
if bb: P = P.crop(bb)
iw, ih = W - 2 * inset, H - 2 * inset
k = fill * min(iw / P.width, ih / P.height)
P = P.resize((max(1, round(P.width * k)), max(1, round(P.height * k))), Image.LANCZOS)
# a soft drop shadow toward the lower right (light from the upper left)
sh = Image.new('RGBA', P.size, (0, 0, 0, 0)); sh.putalpha(P.getchannel('A').point(lambda v: int(v * 0.45)))
sh = sh.filter(ImageFilter.GaussianBlur(3))
x, y = (W - P.width) // 2, (H - P.height) // 2
out_im.alpha_composite(sh, (x + 4, y + 4)); out_im.alpha_composite(P, (x, y))
out_im.save(out)
print(out, out_im.size)
