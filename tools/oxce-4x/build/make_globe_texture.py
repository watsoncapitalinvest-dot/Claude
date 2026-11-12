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
DIM = 0.80

def main(src_path, pal_path, out_path, flip=False, roll_deg=0.0):
    raw = open(pal_path, 'rb').read()
    pal = [(min(255, raw[i*3]*4), min(255, raw[i*3+1]*4), min(255, raw[i*3+2]*4))
           for i in range(256)]
    legal = [b*16+k for b in BLOCKS for k in range(16) if b*16+k != 0]

    src = Image.open(src_path).convert('RGB')

    # FORCE 2:1. THE MODEL'S TEXTURE IS NOT.
    #
    # John's globe model ships earth_vegetation_index.png at 2048x2048 - a 2:1
    # equirectangular map squeezed into a square sheet, which is how it wraps onto
    # the model's UVs. Every line below assumes equirectangular, where one row is a
    # constant latitude and the whole sheet spans 180 degrees, so a square sheet
    # puts the equator at row h/2 of a map that only reaches 45 degrees by then.
    #
    # The committed texture and gijoe_globe_earth.rul are both 2048x1024, and the
    # ten-landmark orientation check was run at 2:1 - so the resize was happening
    # outside this script, in a shell line nobody wrote down. Rebuilding from the
    # raw square source without it produced a 2048x2048 file that the rul still
    # declares as 1024 tall. It lives here now.
    if abs(src.width / src.height - 2.0) > 0.01:
        src = src.resize((src.width, src.width // 2), Image.LANCZOS)
        print('source was %s, resized to 2:1 for equirectangular sampling'
              % (Image.open(src_path).size,))
    w, h = src.size
    a = np.asarray(src)
    if flip:
        a = np.asarray(Image.fromarray(a).transpose(Image.FLIP_LEFT_RIGHT))
    a = np.roll(a, int(round(roll_deg/360*w)), axis=1)
    a = np.roll(a, -w//2, axis=1).astype(np.int16)      # Greenwich to the left edge
    ocean = a.sum(axis=2) < 46

    # DIM THE LAND BEFORE QUANTISING, NOT AFTER.
    #
    # John: "darken the globe a little bit". The photo is lit for a daylight render
    # and against drawOcean's deep blue the continents read hot.
    #
    # It has to happen HERE, on the RGB, for two reasons. Quantising first and then
    # subtracting from the index walks off the end of a 16-entry block and lands in
    # whatever block follows - which is how the first globe attempt ended up with
    # red and yellow speckle. And it has to come AFTER `ocean` is computed, because
    # dimming pushes dark land under the sum<46 sea test and would quietly reclassify
    # coastline as sea.
    #
    # Dimming the RGB instead lets the existing quantiser pick a lower entry inside
    # each pixel's own ramp, so getLandShadow still has its whole block to shade
    # into at the terminator. At 0.80 the mean land entry moves about 2 of 16 down
    # its block, which leaves the night side as separable as it was.
    a[~ocean] = (a[~ocean] * DIM).astype(np.int16)

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
    land = out[out != 0]
    print('wrote %s  (%dx%d, sea %.1f%%, dim %.2f, mean land entry %.1f/16 '
          'into its block)' % (out_path, w, h, 100*(out == 0).mean(), DIM,
                               (land % 16).mean()))

if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
