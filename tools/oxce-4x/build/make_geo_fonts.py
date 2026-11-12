#!/usr/bin/env python3
"""Build the sharp twins for the GEOSCAPE's own fonts.

Why this exists. Every widget on the geoscape - INTERCEPT, BASES, the clock, the
six speed buttons - was falling back to the flat renderer, which is why that one
screen was unreadable at 1920x1080 while the main menu was crisp. The engine said
so itself, 4764 times in one run:

    HiUI: button "5 Mins" would draw 0 of 5 glyphs ... leaving this one to the
    flat renderer

"0 of N" means not one glyph resolved. Instrumenting the three early-outs in
HiUI::glyphs showed every one failing on noAtlas - the atlas lookup - and logging
the sheet identity gave the answer:

    [atlaskey] registered Language/FontBig.png   256x400
    [atlaskey] registered Language/FontSmall.png 128x225
    [atlaskey] MISS sheet= 80x70

80x70 is FontGeoSmall.png. THE GEOSCAPE HAS ITS OWN FONTS - FONT_GEO_BIG and
FONT_GEO_SMALL - and the mod only ever shipped FontBig_hi.png and FontSmall_hi.png.
With no twin, HiUI::registerFontImage returns before registering, no atlas exists,
and every glyph on the screen misses. One missing pair of files, one whole screen.

Rather than upscale the 1994 bitmaps - which would only make blocky letters
smoother - each geo glyph is rebuilt from the SHARP small font the rest of the
interface already uses, so the geoscape ends up in the same typeface as every
other screen. The geo cells are narrow (5 wide against 8), so glyphs are fitted
to the geo cell, which reproduces the condensed look the original had.

usage: make_geo_fonts.py <common/Language dir> <mod Language dir>
"""
import sys, os, yaml
from PIL import Image

COMMON, MODLANG = sys.argv[1], sys.argv[2]
K = 6                                    # the twins are exactly 6x, checked against FontBig_hi

d = yaml.safe_load(open(os.path.join(COMMON, 'Font.dat')))
fonts = d['fonts'] if isinstance(d, dict) and 'fonts' in d else d
spec = {}
for f in fonts:
    im = f['images'][0]
    spec[f['id']] = dict(file=im['file'],
                         w=im.get('width', f['width']), h=im.get('height', f['height']),
                         chars=im['chars'])

def cells(img, cw, ch):
    return img.width // cw, img.height // ch

def find(path):
    for base in (MODLANG, COMMON):
        p = os.path.join(base, path)
        if os.path.exists(p): return p
    raise SystemExit('missing ' + path)

# THE SOURCE IS THE GEO FONT ITSELF, NOT THE REGULAR SHARP FONT.
#
# The first version lifted each geo glyph from FontSmall_hi so the geoscape would
# share the interface typeface. It rendered sharp and it was WRONG: the engine
# crops every glyph to that character's own width in ITS font, and the geo font is
# 5 wide where the small font is 8. An 8-wide letterform pasted across the geo cell
# gets cropped to the narrower box, which chopped every I - INTERCEPT came out
# "IN TERCEPT", FILES came out "F LES", Min came out "M n".
#
# Upscaling the geo font's own sheet keeps every glyph's ink exactly where its crop
# expects it, at every character width, by construction. The letterforms stay the
# condensed 1994 ones; they are simply resolved at 6x instead of being point-sampled.
made = []
for fid in ('FONT_GEO_BIG', 'FONT_GEO_SMALL'):
    g = spec[fid]
    flat = Image.open(find(g['file'])).convert('RGBA')
    big = flat.resize((flat.width * K, flat.height * K), Image.LANCZOS)
    dest = os.path.join(MODLANG, g['file'].replace('.png', '_hi.png'))
    big.save(dest)
    made.append((os.path.basename(dest), big.size, len(g['chars']), 0))

for n, s, hit, miss in made:
    print('%-22s %-12s %d glyphs, upscaled x%d from the geo sheet' % (n, '%dx%d' % s, hit, K))
