#!/usr/bin/env python3
"""Rebuild GEOBORD.png's side panel from the 4x panel art, so both agree.

    python3 build/make_base_panel.py <GEOBORD_hi.png> <PALETTES.DAT> <GEOBORD.png>

GEOBORD.png is the 320x200 panel the engine draws at base resolution, and
GEOBORD_hi.png is the 1920x1200 twin HiUI draws over it at 4x. Until now they
were two different pictures: the twin is John's painted console, the base file
is still vanilla's bezel with the graticule removed.

That did not matter while the only thing on top of them was text, because the
text rectangles are the same either way. It matters now that the ROTATE AND ZOOM
HITBOXES have been moved to match the painted console's layout - a dial at each
end and the arrow cross in the middle, where vanilla has the cross on the left
and both zoom controls stacked on the right. Leave the base file alone and base
resolution would draw vanilla's arrows with the new rectangles over them, which
is the same bug in the other direction.

So the panel strip is downscaled from the twin and quantised onto PAL_GEOSCAPE.
Only x 256..320 is touched: the rest of GEOBORD.png is the globe's backdrop and
is left exactly as it is.

Index 0 is transparent in this palette, so it is excluded - a panel pixel that
quantised to 0 would punch a hole through to the globe.
"""
import sys
import numpy as np
from PIL import Image

HI, PAL, BASE = sys.argv[1], sys.argv[2], sys.argv[3]
PANEL_X, W, H = 256, 320, 200

raw = open(PAL, 'rb').read()
# PALETTES.DAT is five palettes at a 774-byte stride - 768 plus six of padding.
# Read flat and palette 0 is the only one that lands right; every other one is
# shifted by six bytes and comes out as noise.
pal = [(min(255, raw[i*3]*4), min(255, raw[i*3+1]*4), min(255, raw[i*3+2]*4))
       for i in range(256)]

hi = Image.open(HI).convert('RGB').crop((1536, 0, 1920, 1200))
strip = hi.resize((W - PANEL_X, H), Image.LANCZOS)
a = np.asarray(strip).astype(np.int32)

legal = np.array([i for i in range(1, 256)], dtype=np.uint8)
lp = np.array([pal[i] for i in legal], dtype=np.int32)
flat = a.reshape(-1, 3)
d = ((flat[:, None, :] - lp[None, :, :])**2 * np.array([3, 4, 2])).sum(axis=2)
idx = legal[d.argmin(axis=1)].reshape(H, W - PANEL_X)

base = Image.open(BASE)
assert base.size == (W, H) and base.mode == 'P', 'GEOBORD.png must be 320x200 P'
b = np.asarray(base).copy()
before = b[:, PANEL_X:].copy()
b[:, PANEL_X:] = idx
out = Image.fromarray(b, mode='P')
out.putpalette(base.getpalette())
out.save(BASE, optimize=False)
print('panel strip x%d..%d rebuilt from the 4x art, %d of %d pixels changed'
      % (PANEL_X, W, int((before != idx).sum()), before.size))
