"""Old vs new crops around the changed decal area, clean and damaged, one row per package (largest-change heading).
python3 check_sheet.py out.png name..."""
import sys, json, numpy as np
from PIL import Image, ImageDraw
ld = lambda p: Image.open(p).convert('RGBA'); rows = []
for n in sys.argv[2:]:
    mo = json.load(open(f'pk/old/{n}/{n}/manifest.json')); s0 = mo['frames'][0]['state']
    best = None
    for h in ['N','NE','E','SE','S','SW','W','NW']:
        a = np.asarray(ld(f'pk/old/{n}/{n}/whole/{n}_clean_{s0}_{h}.png')).astype(int); b = np.asarray(ld(f'pk/new/{n}/{n}/whole/{n}_clean_{s0}_{h}.png')).astype(int)
        c = (np.abs(a - b) > 3).any(-1)
        if best is None or c.sum() > best[1]: best = (h, c.sum(), c)
    h, _, c = best; ys, xs = np.nonzero(c); pad = 14; box = (xs.min() - pad, ys.min() - pad, xs.max() + pad, ys.max() + pad)
    cells = [ld(f'pk/{v}/{n}/{n}/whole/{n}_{l}_{s0}_{h}.png').crop(box) for l in ('clean', 'damaged') for v in ('old', 'new')]
    k = max(1, 120 // max(1, box[3] - box[1])); k = min(k, 6)
    cells = [x.resize((x.width * k, x.height * k), Image.NEAREST) for x in cells]
    row = Image.new('RGBA', (sum(x.width for x in cells) + 230, max(x.height for x in cells) + 6), (70, 74, 70, 255)); d = ImageDraw.Draw(row); d.text((4, 4), f'{n}\n{h} {s0}', fill='white'); x = 226
    for cc in cells: row.alpha_composite(cc, (x, 3)); x += cc.width + 2
    rows.append(row)
W = max(r.width for r in rows); S = Image.new('RGBA', (W, sum(r.height for r in rows) + 20), (40, 40, 40, 255)); ImageDraw.Draw(S).text((230, 4), 'clean old | clean new | damaged old | damaged new', fill='white'); y = 20
for r in rows: S.alpha_composite(r, (0, y)); y += r.height
S.save(sys.argv[1]); print(S.size)
