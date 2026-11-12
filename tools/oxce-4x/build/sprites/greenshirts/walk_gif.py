"""8-facing inked walk GIF from a render_char.py output dir (layout as the design chat's compose_factory.py:
4 x 2 grid of 256x320 cells, facing labels, grey ground).  Pen env (PENIDS ...) and HAIR are read by soldier_ink.
  python3 walk_gif.py <render dir> <out.gif> [clip=walk]"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import soldier_ink as ink
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]; clip = sys.argv[3] if len(sys.argv) > 3 else 'walk'
meta = json.load(open(f'{src}/meta.json')); n = meta['frames']; dirs = meta['dirs']
LABEL = {1: 'away', 2: 'away-right', 3: 'right', 4: 'toward-right', 5: 'toward', 6: 'toward-left', 7: 'left', 8: 'away-left'}
GREY = (200, 200, 205); frames = []
for i in range(n):
    im = Image.new('RGB', (4 * 256, 2 * 320), GREY); dr = ImageDraw.Draw(im)
    for j, k in enumerate(dirs):
        p = f'{src}/{clip}/d{k}_f{i:02d}'
        fr = ink.ink_frame(Image.open(p + '_beauty.png').convert('RGBA'), Image.open(p + '_id.png'))
        x, y = (j % 4) * 256, (j // 4) * 320
        cell = Image.new('RGBA', fr.size, GREY + (255,)); cell.alpha_composite(fr); im.paste(cell.convert('RGB'), (x, y))
        dr.text((x + 6, y + 6), f'{k} {LABEL[k]}', fill=(40, 40, 40))
    frames.append(im)
frames[0].save(out, save_all=True, append_images=frames[1:], duration=110, loop=0); print('wrote', out, len(frames), 'frames')
