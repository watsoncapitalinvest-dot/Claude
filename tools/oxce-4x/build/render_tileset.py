"""A tileset's art as one sheet, with the MCD index drawn on every tile.

Written because the vanilla sets have no tile names, so the only way to say what BARN tile 11 is
made of is to look at it - and the first attempt at looking at it put the labels under the tile
to the left, which makes a confident wrong reading almost guaranteed. The index goes ON the tile
here for that reason.

Use it whenever a material tag looks wrong on the field: render the set, find the index, fix the
one line in tag_materials.py.

usage: render_tileset.py <TERRAIN dir> <SET> <out.png>
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'hd'))
from pck import load_pck, palette                       # noqa: E402

TERRAIN, SET, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
COLS, CELL, PAD = 6, 104, 22

frames = load_pck(os.path.join(TERRAIN, SET + '.PCK'),
                  os.path.join(TERRAIN, SET + '.TAB'), 32, 40)
pal = np.array(palette() if callable(palette) else palette, np.uint8).reshape(-1, 3)

rows = (len(frames) + COLS - 1) // COLS
sheet = Image.new('RGB', (COLS * (CELL + PAD), rows * (CELL + PAD)), (18, 18, 22))
draw = ImageDraw.Draw(sheet)
for i, frame in enumerate(frames):
    tile = Image.fromarray(pal[np.array(frame, np.uint8).reshape(40, 32)], 'RGB')
    tile = tile.resize((CELL, CELL), Image.NEAREST)
    r, c = divmod(i, COLS)
    x, y = c * (CELL + PAD), r * (CELL + PAD)
    draw.rectangle([x, y, x + CELL + PAD - 2, y + CELL + PAD - 2], outline=(70, 70, 80))
    sheet.paste(tile, (x + PAD // 2, y + PAD // 2))
    draw.rectangle([x + 1, y + 1, x + 20, y + 14], fill=(0, 0, 0))
    draw.text((x + 4, y + 2), str(i), fill=(255, 220, 120))

sheet.save(OUT)
print('wrote %s - %d tiles, %dx%d' % (OUT, len(frames), sheet.width, sheet.height))
