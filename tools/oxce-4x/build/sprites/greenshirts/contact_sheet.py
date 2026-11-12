"""Side-by-side contact sheet at game size: walk frame 0, facings 5 and 3, inked per man with his own ink() env,
all from render_char.py's shared reference frame, so relative height, build and line weight compare directly.
Top row 2x (to look at), bottom row 1x = 128x160 game cells.
  python3 contact_sheet.py <out.png> name=<render dir>=<ENV k=v;k=v> ..."""
import sys, os, subprocess
from PIL import Image, ImageDraw
out = sys.argv[1]; items = [a.split('=', 2) for a in sys.argv[2:]]
code = r'''
import sys; sys.path.insert(0, "/home/claude/claude/tools/oxce-4x/build/sprites")
import soldier_ink as ink
from PIL import Image
src, d, o = sys.argv[1:4]; p = f"{src}/walk/d{d}_f00"
ink.ink_frame(Image.open(p + "_beauty.png").convert("RGBA"), Image.open(p + "_id.png")).save(o)
'''
tiles = []
for name, src, env in items:
    e = {k: v for k, v in os.environ.items() if not k.startswith(('PEN', 'HAIR', 'FOLD', 'INKJOIN'))}
    e.update(dict(kv.split('=', 1) for kv in env.split(';') if kv))
    for d in (5, 3):
        o = f'/tmp/_cs_{name}_{d}.png'; subprocess.run([sys.executable, '-c', code, src, str(d), o], env=e, check=True)
        tiles.append((name, d, Image.open(o)))
GREY = (200, 200, 205); W, H = 256, 320
sheet = Image.new('RGB', (len(tiles) * W, H + 24 + H // 2), GREY); dr = ImageDraw.Draw(sheet)
for i, (name, d, im) in enumerate(tiles):
    c = Image.new('RGBA', im.size, GREY + (255,)); c.alpha_composite(im); sheet.paste(c.convert('RGB'), (i * W, 24))
    g = im.resize((128, 160), Image.LANCZOS); c = Image.new('RGBA', g.size, GREY + (255,)); c.alpha_composite(g); sheet.paste(c.convert('RGB'), (i * W + 64, 24 + H))
    dr.text((i * W + 6, 6), f'{name} f{d}', fill=(20, 20, 20))
sheet.save(out); print('wrote', out, sheet.size)
