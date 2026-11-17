# STORY's size brief, ORDER item 3: every classed vehicle beside a soldier, old size and new size side by side, all at the
# game's own pixel scale (vehicle frames and soldier cells are both 4x game pixels, same ppu).
# usage: python3 lineup_soldier.py old_packs_dir new_pkg_dir soldier_body_rgb.png out.png
import sys, json, glob, os
from PIL import Image, ImageDraw, ImageFont
OLD, NEW, SOL, OUT = sys.argv[1:5]; HD = 'SE'
V = [('ferret', 'Ferret', '1x2'), ('vamp', 'VAMP', '2x3'), ('vamp_mk2', 'VAMP Mk II', '2x3'), ('stinger', 'Stinger', '2x3'),
     ('thunder_machine', 'Thunder Machine', '2x3'), ('wolverine', 'Wolverine', '2x3'), ('triple_t', 'Triple T', '3x3'),
     ('hiss', 'H.I.S.S.', '3x4'), ('mobat', 'MOBAT', '3x4'), ('mauler', 'Mauler', '4x5')]
sheet = Image.open(SOL).convert('RGBA'); sol = sheet.crop((3 * 128, 0, 4 * 128, 160)); sol = sol.crop(sol.getbbox())
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22); F2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
def frame(root):
    m = json.load(open(glob.glob(f'{root}/**/manifest.json', recursive=True)[0])); base = os.path.dirname(glob.glob(f'{root}/**/manifest.json', recursive=True)[0])
    fr = [f for f in m.get('frames', m.get('hull', [])) if f.get('look') == 'clean' and f.get('heading') == HD]
    f = fr[0]; im = Image.open(f'{base}/{f["file"]}').convert('RGBA'); ax, ay = f.get('anchor', m['anchor'])
    tur = [t for t in m.get('turret', []) if t.get('look') == 'clean' and t.get('heading') == HD]
    if tur and 'hull' in m:                                            # old two-layer packages: put the turret back on
        t = Image.open(f'{base}/{tur[0]["file"]}').convert('RGBA'); to = f.get('turret_paste_offset', [0, 0]); im.alpha_composite(t, (to[0], to[1]))
    elif tur:
        t = Image.open(f'{base}/{tur[0]["file"]}').convert('RGBA'); to = f.get('turret_paste_offset', [0, 0]); c = Image.new('RGBA', im.size); c.alpha_composite(t, (max(0, to[0]), max(0, to[1]))); im.alpha_composite(c)
    bb = im.getbbox(); return im, ax, ay + 16, bb                       # ground = anchor + 16 px
cells = []
for key, name, cls in V:
    pair = []
    for root in (f'{OLD}/{key}', f'{NEW}/{key}'):
        im, gx, gy, bb = frame(root); W = bb[2] - bb[0]; H = max(gy, bb[3]) - bb[1]
        c = Image.new('RGBA', (W + sol.width + 40, max(H, sol.height) + 10), (122, 114, 86, 255))
        base = c.height - 5; c.alpha_composite(im.crop(bb), (0, base - (gy - bb[1])))
        c.alpha_composite(sol, (W + 20, base - sol.height + 2)); pair.append(c)
    cells.append((name, cls, pair))
wmax = max(p[0].width + p[1].width for _, _, p in cells) + 60; hrow = [max(p[0].height, p[1].height) + 40 for _, _, p in cells]
S = Image.new('RGB', (wmax + 260, sum(hrow) + 60), (40, 40, 40)); d = ImageDraw.Draw(S); y = 50
d.text((20, 12), 'Old size (left) and new class size (right), each beside Hawk, at game pixel scale', font=F, fill=(240, 240, 230))
for (name, cls, (a, b)), h in zip(cells, hrow):
    d.text((20, y + 10), name, font=F, fill=(255, 255, 255)); d.text((20, y + 40), 'class ' + cls, font=F2, fill=(210, 210, 200))
    S.paste(a.convert('RGB'), (240, y + h - 40 - a.height)); S.paste(b.convert('RGB'), (240 + a.width + 60, y + h - 40 - b.height)); y += h
S.save(OUT); print(S.size)
