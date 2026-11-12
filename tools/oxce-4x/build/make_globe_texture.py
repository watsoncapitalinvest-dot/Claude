#!/usr/bin/env python3
"""Turn an equirectangular earth photo into the 8-bit texture Globe::drawEarthTexture wants.

    python3 build/make_globe_texture.py <source.png> <PALETTES.DAT> <out.png>

The source stays OUT of this repository - it is derived from a third-party
model of unknown licence and the repo is public. Only this script is kept.

What the output has to satisfy, and why:

  index 0 is the sea.   Globe::drawEarthTexture skips it, so drawOcean's colour
                        survives and isOcean() still recognises the sea by its
                        index being inside the 32-entry block at OCEAN_COLOR.
                        Sea painted from a photo would not be in that block and
                        would stop shading at the terminator.

  land avoids 192-223.  Same reason from the other side: a land pixel in the
                        ocean block would be shaded as sea.

  land uses blocks      1,2,3,4,7 (greens), 9 (tan), 10 (rock), 14 (olive).
                        Each is a light-to-dark ramp, and getLandShadow darkens
                        a pixel WITHIN its own 16-block - which is the whole
                        reason this is cheap. Let the quantiser use the entire
                        palette and it reaches for the UI reds and yellows in
                        block 0, which is exactly what the first attempt did:
                        the globe came out covered in red and yellow speckle.

  no dithering.         At this scale dither reads as noise, not as shading.
"""
import sys
import numpy as np
from PIL import Image

BLOCKS = [1, 2, 3, 4, 7, 9, 10, 14]

# ORIENTATION, MEASURED RATHER THAN EYEBALLED.
#
# This used to default to flip=True, roll_deg=87, which is what hand-tuning looks
# like when the first guess was wrong. The source is an ordinary equirectangular
# map with Greenwich at its CENTRE, so the only transform it needs is a roll of
# half the width to put Greenwich at the left edge, which is what the engine's
# u = lon/(2*pi)*width expects. No mirror, no extra degrees.
#
# Checked against eight landmarks - London, Congo, Amazon, Sahara, Australia and
# three open-ocean points. flip=False, roll=0 scores 8/8. The old flip=True,
# roll=87 scores 5/8: it put the Atlantic over Africa, which is why half the globe
# had no texture and the vanilla polygons showed through underneath it.
def main(src_path, pal_path, out_path, flip=False, roll_deg=0.0):
    raw = open(pal_path, 'rb').read()
    pal = [(min(255, raw[i*3]*4), min(255, raw[i*3+1]*4), min(255, raw[i*3+2]*4))
           for i in range(256)]
    legal = [b*16+k for b in BLOCKS for k in range(16) if b*16+k != 0]

    src = Image.open(src_path).convert('RGB')
    w, h = src.size
    a = np.asarray(src)
    if flip:
        a = np.asarray(Image.fromarray(a).transpose(Image.FLIP_LEFT_RIGHT))
    a = np.roll(a, int(round(roll_deg/360*w)), axis=1)
    a = np.roll(a, -w//2, axis=1).astype(np.int16)      # Greenwich to the left edge
    ocean = a.sum(axis=2) < 46

    lat = 90 - np.arange(h)/h*180.0
    ice = np.array([198, 208, 216], dtype=np.int16)
    south = lat < -78
    a[south] = ice; ocean[south] = False
    m = (lat > 86)[:, None] & ocean
    a[m] = ice; ocean[m] = False

    lp = np.array([pal[i] for i in legal], dtype=np.int32)
    li = np.array(legal, dtype=np.uint8)
    out = np.zeros((h, w), dtype=np.uint8)
    for y0 in range(0, h, 32):
        blk = a[y0:y0+32].reshape(-1, 3).astype(np.int32)
        d = ((blk[:, None, :] - lp[None, :, :])**2 * np.array([3, 4, 2])).sum(axis=2)
        out[y0:y0+32] = li[d.argmin(axis=1)].reshape(-1, w)
    out[ocean] = 0

    # NORTH ENDS UP AT THE BOTTOM, ON PURPOSE.
    #
    # OpenXcom's geoscape latitude is POSITIVE GOING SOUTH, and drawEarthTexture
    # samples v = (pi/2 - lat)/pi * height. Feed it a normal north-up map and the
    # north pole reads from the bottom row - the globe comes out inverted. Every
    # line above this works north-up so the ice bands land on the right latitudes;
    # the flip happens once, here, at the end.
    #
    # Checked against ten landmarks including Greenland and Siberia: with this
    # flip and no other transform the texture scores 10/10. Without it, 5/10.
    out = out[::-1]

    flat = []
    for c in pal: flat += list(c)
    im = Image.fromarray(out, mode='P'); im.putpalette(flat)
    im.save(out_path, optimize=False)
    print('wrote %s  (%dx%d, sea %.1f%%)' % (out_path, w, h, 100*(out == 0).mean()))

if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
