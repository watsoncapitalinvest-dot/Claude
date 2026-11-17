# Append one item to John's vehicle weapons catalog (Reference\ammo_catalog, private) on top of whatever is there now
# (ROSTER edits it too): next free R number, a catalog.csv row, a README line, a card on VEHICLE_WEAPONS_CATALOG.png.
# John 18:42: "put anything you cut or create in the catalog".
# usage: python3 catalog_add.py staged_dir out_dir item "what it is" kind "from vehicle" "source and licence" L W H tris \
#        model.glb preview.png "source blend object" "card line 1" "readme line"
import sys, csv, io, os, shutil
from PIL import Image, ImageDraw, ImageFont
(SRC, OUT, item, what, kind, veh, srcl, L, W, H, tris, glb, prev, obj, card1, readme) = sys.argv[1:17]
os.makedirs(OUT, exist_ok=True)
raw = open(f'{SRC}/catalog.csv', 'rb').read(); nl = '\r\n' if b'\r\n' in raw else '\n'; t = raw.decode(); t = t if t.endswith(nl) else t + nl
ids = [l.split(',')[0] for l in t.split(nl) if l]; n = max(int(i[1:]) for i in ids if i[:1] == 'R' and i[1:].isdigit()) + 1; rid = f'R{n}'
b = io.StringIO(); csv.writer(b, lineterminator=nl).writerow([rid, item, what, kind, veh, srcl, L, W, H, tris, os.path.basename(glb), os.path.basename(prev), obj])
open(f'{OUT}/catalog.csv', 'w', newline='').write(t + b.getvalue())
r = open(f'{SRC}/README.txt').read().rstrip('\n') + f'\n{rid} (VFACTORY): {item} - {readme}\n'; open(f'{OUT}/README.txt', 'w').write(r)
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14); F2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
S = Image.open(f'{SRC}/VEHICLE_WEAPONS_CATALOG.png').convert('RGB'); i = n - 1; need = 40 + 250 * (i // 4 + 1)
if S.height < need: S2 = Image.new('RGB', (S.width, need), (60, 66, 58)); S2.paste(S, (0, 0)); S = S2
c = Image.new('RGB', (320, 250), (236, 232, 220)); d = ImageDraw.Draw(c)
im = Image.open(prev).convert('RGBA'); im = im.crop(im.getbbox()); s = min(300 / im.width, 150 / im.height)
im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS); c.paste(im, ((320 - im.width) // 2, 10 + (150 - im.height) // 2), im)
fit = lambda txt, f, w: txt if d.textlength(txt, font=f) <= w else fit(txt[:-2] + '…', f, w)
d.text((8, 168), fit(f'{rid}  {item}', F, 304), font=F, fill=(20, 20, 20)); d.text((8, 188), fit(card1, F2, 304), font=F2, fill=(40, 40, 40))
d.text((8, 204), fit(f'{veh} - {kind} - {L} x {W} x {H} m', F2, 304), font=F2, fill=(40, 40, 40))
d.text((8, 220), fit(srcl, F2, 304), font=F2, fill=(120, 30, 30) if 'NC' in srcl else (30, 90, 30))
S.paste(c, ((i % 4) * 320, 40 + (i // 4) * 250)); S.save(f'{OUT}/VEHICLE_WEAPONS_CATALOG.png')
shutil.copy(glb, OUT); shutil.copy(prev, OUT); print(rid)
