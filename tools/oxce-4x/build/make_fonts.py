#!/usr/bin/env python3
"""Rebuild the UI font sheets from a real typeface instead of upscaling a bitmap.

    python3 build/make_fonts.py <Font.dat> <out dir> [--font <ttf>]

John: "the font is bad too". It is. Until now the sharp sheets were the 1994
bitmap font enlarged six times with LANCZOS, which cannot add detail it never
had - every label came out soft, and a soft 4x label looks worse than a crisp
small one.

There are two sheets per font and they do different jobs:

  FontX.png      8-bit, palette values 1-5. Drawn at base resolution, and - this
                 is the part that matters at 4x too - Font::init scans each
                 cell's ink columns to get that character's ADVANCE. Every
                 layout in the game is spaced off this sheet.
  FontX_hi.png   RGBA at exactly 6x. HiUI reads only the ALPHA channel as
                 coverage (HiUI.cpp: `a.cov[...] = p[x] >> 24`) and tints it.
                 A sheet that is not an exact integer multiple is refused.

Both are generated here from the same outlines, so the advance the engine
measures and the glyph HiUI draws cannot disagree.

Why that also fixes the overflowing labels: "30 Mins" measured 28.9 base px
against a painted recess 26.7 wide, so it could not fit at any position. The
advance comes from this sheet, and a condensed face narrows it at the source
rather than by shortening the words.

The base sheet is rendered at 6x and downsampled, NOT rendered at 7 pixels.
Hinting a 7px face produces glyphs whose ink columns land a pixel either way,
and those columns are the advances - the UI would be spaced by rounding noise.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import yaml

K = 6                      # the hi sheet multiple HiUI expects
TTF = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
# Which sheets to rebuild, and how tall the caps should sit in each cell. The
# cell sizes come from Font.dat and are not ours to change: FONT_BIG is 16x16
# and FONT_SMALL 8x9, and every existing layout is built on them.
# THE GEOSCAPE HAS ITS OWN PAIR, AND THEY ARE THE ONES ON THE PANEL.
#
# Rebuilding only FontBig and FontSmall made the clock and the date crisp and
# left INTERCEPT, BASES, GRAPHS and the rest exactly as blurry as before, which
# is how it became obvious that the side buttons and the country labels are
# drawn with FONT_GEO_*, not with the general UI fonts.
#
# Their cells are 5x9 and 5x7 - a third the width of FONT_BIG - so they take a
# larger cap ratio to fill the cell, and the whole sheet is 80 wide: 16 columns
# of 5. Nothing here may change a cell size; every layout in the game is spaced
# on them.
# EVERY base sheet stays as shipped. The globe draws its country and city labels
# with FONT_BIG/FONT_SMALL straight into its own surface, never through HiUI, so
# they read the 8-bit sheet - and a 9-pixel downsample of an outline font turned
# NIGERIA into a green slab. The sharp twins are all the panel ever needed.
KEEP_BASE = {'FontBig.png', 'FontSmall.png', 'FontGeoBig.png', 'FontGeoSmall.png'}
# FontSmall is 0.62, not 0.72, because of descenders. Its cell is 9 tall and the
# widgets that use it are 8, so a glyph that drops below the baseline always
# overhangs the row by a pixel - and on a panel with a recess under every row,
# that pixel lands on the lip. "Jan" sat its J on the bottom of the date well.
# Smaller type keeps the descender inside the cell; the caps lose a pixel, which
# at 4x costs nothing a reader notices.
WANT = {'FontBig.png': 0.68, 'FontSmall.png': 0.68,
        'FontGeoBig.png': 0.80, 'FontGeoSmall.png': 0.86}


def cells(sheet_w, cell_w):
    return sheet_w // cell_w


def _glyph(c, f):
    """Render one character on its own and return (image, ink bbox)."""
    probe = Image.new('L', (f.size * 3, f.size * 3), 0)
    ImageDraw.Draw(probe).text((f.size // 2, f.size // 2), c, font=f, fill=255)
    return probe, probe.getbbox()


def base_widths(base_img, chars, cw, ch):
    """Per-character ink width in an existing base sheet - the engine's advance."""
    a = np.asarray(base_img.convert('L'))
    H, Wd = a.shape
    cols = Wd // cw
    out = []
    for i in range(len(chars)):
        x0, y0 = (i % cols) * cw, (i // cols) * ch
        if y0 + ch > H:
            out.append(0)
            continue
        cell = a[y0:y0 + ch, x0:x0 + cw]
        nz = np.nonzero(cell.any(axis=0))[0]
        out.append(int(nz.max()) + 1 if len(nz) else 0)
    return out


def render(chars, cw, ch, cap, sheet_size, ttf, widths=None):
    """Draw every character into its own cell at 6x, returning the coverage sheet.

    A GLYPH MAY NEVER LEAVE ITS CELL.

    The engine crops character i to cell i and nothing else, so anything that
    spills into cell i+1 is served up as part of the NEXT character. Drawing the
    geo fonts at their natural proportions did exactly that: their cells are 5
    wide, a condensed bold cap is wider, and INTERCEPT came out "IINTERCEPT" -
    the phantom I being the left edge of the following glyph.

    So the type is measured before it is set. Every glyph is rendered alone, the
    widest is found, and the whole sheet is scaled by whatever factor makes THAT
    one fit. One factor for the sheet, not one per glyph, or the letters would
    change size mid-word. Each paste is then clipped to its own cell as well, so
    a glyph this script failed to anticipate cannot corrupt its neighbour.
    """
    W, H = sheet_size
    big = Image.new('L', (W * K, H * K), 0)
    cols = cells(W, cw)
    inner_w, inner_h = cw * K - 2, ch * K - 2

    px = max(6, int(round(ch * K * cap)))
    f = ImageFont.truetype(ttf, px)
    widest = 1
    for c in chars:
        if c.isspace():
            continue
        bb = _glyph(c, f)[1]
        if bb:
            widest = max(widest, bb[2] - bb[0])
    # NOT scaled down to the widest glyph. That was the first attempt and it is
    # the wrong lever: one wide symbol somewhere in a 385-glyph sheet - a dash,
    # an OE ligature - dragged every letter down with it, and the geo advances
    # fell from 5 to 3, which is a different kind of unreadable. The per-glyph
    # horizontal squeeze below handles the few that are genuinely too wide, and
    # the per-cell clip guarantees the rest cannot bleed whatever happens.
    if widest > inner_w:
        print('   widest glyph %dpx in a %dpx cell - squeezed individually' % (widest, inner_w))

    # One baseline for the whole sheet. Per-character vertical placement would
    # make a word wobble; this is measured off the font's own metrics once.
    asc, desc = f.getmetrics()
    top = max(0, (ch * K - (asc + desc)) // 2)
    hb = _glyph('H', f)[1]
    cap_bottom = hb[3] if hb else None
    placed = 0
    for i, c in enumerate(chars):
        if c == '\n':
            continue
        cx, cy = (i % cols) * cw * K, (i // cols) * ch * K
        if cy + ch * K > H * K:
            break
        try:
            g, bb = _glyph(c, f)
            if not bb:
                continue
            ink = g.crop(bb)
            # FIT TO THE ADVANCE THE ENGINE WILL CROP THIS GLYPH TO.
            #
            # When a sharp sheet is built against a base sheet that stays as it
            # is - which is what the geoscape fonts do, so the globe's country
            # labels keep their crisp 8-bit letterforms - the engine still takes
            # each character's width from the BASE cell. A wider glyph in the hi
            # sheet is not scaled to fit, it is CUT at that width, and a letter
            # cut on its right side turns into another letter: OPTIONS came out
            # "CPTICNS" on screen because every O lost its closing stroke.
            limit = min(inner_w, widths[i] * K if widths and i < len(widths) and widths[i] else inner_w)
            if ink.width > limit:
                ink = ink.resize((max(1, limit), ink.height), Image.LANCZOS)
            # Not widened to the advance. Tried: round letters fattened while I
            # and T stayed thin and the spacing went uneven, which is worse than
            # a little air. Fitted, never stretched.
            # left-align on the cell with a hair of bearing, baseline shared
            ox = cx + 1
            oy = cy + top + (bb[1] - f.size // 2)
            # CAPITALS AND DIGITS SIT ON THE CAP LINE. DejaVu's capital J is
            # drawn dropping below the baseline, which in a 9-pixel cell lands
            # on the lip of the recess under every row - "Jan" sat its J on the
            # bottom of the date well, and shrinking the font did not cure it
            # because the descent is part of the letter. A UI face does not do
            # that, so any capital or digit whose ink runs below the bottom of
            # an H is lifted until it stands on the same line as the H.
            if (c.isupper() or c.isdigit()) and cap_bottom is not None:
                if bb[3] > cap_bottom:
                    oy -= (bb[3] - cap_bottom)
            cell = Image.new('L', (cw * K, ch * K), 0)
            cell.paste(ink, (1, max(0, min(ch * K - ink.height, oy - cy))))
            big.paste(cell, (cx, cy))
            placed += 1
        except Exception:
            pass
    return big, placed


def main(font_dat, out_dir, ttf=TTF):
    spec = yaml.safe_load(open(font_dat, encoding='utf-8'))
    made = []
    for ent in spec['fonts']:
        cw, chh = ent['width'], ent['height']
        for img in ent['images']:
            name = img['file']
            if name not in WANT:
                continue
            src = os.path.join(os.path.dirname(font_dat), name)
            base = Image.open(src)
            W, H = base.size
            chars = img['chars'].replace('\n', '')
            # KEEP_BASE fonts are rebuilt in the hi sheet ONLY, against the
            # original 8-bit sheet. The globe draws its country labels straight
            # into its own surface, never through HiUI's glyph path, so those
            # labels render from the BASE sheet - replacing it with a 5-pixel
            # downsample of an outline font turned them to mush. The base stays,
            # and every hi glyph is fitted to the advance that base sheet gives.
            widths = base_widths(base, chars, cw, chh) if name in KEEP_BASE else None
            big, placed = render(chars, cw, chh, WANT[name], (W, H), ttf, widths)

            # HI SHEET: coverage lives in ALPHA, and nowhere else. The colour
            # channels are never read, so they are left white - a sheet whose
            # colour carried the glyph and whose alpha was opaque would draw as
            # a solid block the width of every cell.
            hi = Image.merge('RGBA', (Image.new('L', big.size, 255),) * 3 + (big,))
            hi_path = os.path.join(out_dir, name.replace('.png', '_hi.png'))
            hi.save(hi_path)

            # BASE SHEET: downsample the same coverage and threshold it to the
            # font palette's own values. 4 is the body - measured off the stock
            # sheets, whose most common non-zero value is 4 - and 2 takes the
            # partial pixels so the shape survives at 1x. The engine adds these
            # to the text colour index, so they must stay inside 1..5.
            small = big.resize((W, H), Image.LANCZOS)
            a = np.asarray(small).astype(int)
            out = np.zeros((H, W), np.uint8)
            out[a >= 96] = 4
            out[(a >= 40) & (a < 96)] = 2
            pal = base.getpalette() or ([0, 0, 0] * 256)
            im = Image.fromarray(out, mode='P')
            im.putpalette(pal)
            base_path = os.path.join(out_dir, name)
            if name not in KEEP_BASE:
                im.save(base_path, optimize=False)

            # Report the advances this will give, because they are what spaces
            # every label in the game. Width is the last ink column in the cell.
            cols = cells(W, cw)
            def adv(ch_):
                i = chars.find(ch_)
                if i < 0:
                    return None
                x0, y0 = (i % cols) * cw, (i // cols) * chh
                cell = out[y0:y0+chh, x0:x0+cw]
                nz = np.nonzero(cell.any(axis=0))[0]
                return int(nz.max()) + 1 if len(nz) else 0
            sample = ''.join(c for c in '30Mins' if c)
            widths = {c: adv(c) for c in 'ABM0139ins '}
            made.append((name, placed, widths))
            print('%-14s %d glyphs  base %s  hi %s' % (name, placed, base.size, hi.size))
            print('   advances: %s' % ', '.join('%s=%s' % (k, v) for k, v in widths.items()))
    return made


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    ttf = sys.argv[sys.argv.index('--font') + 1] if '--font' in sys.argv else TTF
    main(sys.argv[1], sys.argv[2], ttf)
