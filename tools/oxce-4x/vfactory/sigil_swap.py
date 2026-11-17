"""Put the sigil in place of the diamond decals in a source blend and restore unpacked flat-colour textures.
python3 sigil_swap.py in.blend out.blend mask.png 'img1,img2' 'missing_img=r,g,b;...'
Each named decal image keeps its size; the sigil is drawn in the diamond's own main colour on magenta (= transparent)."""
import bpy, sys, numpy as np
from PIL import Image
src, out, maskp, names, fixes = sys.argv[1:6]
bpy.ops.wm.open_mainfile(filepath=src)
M = Image.open(maskp).convert('L')
for nm in [n for n in names.split(',') if n]:
    im = bpy.data.images[nm]; w, h = im.size[:]
    a = np.array(im.pixels[:]).reshape(h, w, 4)
    mg = (a[..., 0] > .9) & (a[..., 1] < .1) & (a[..., 2] > .9)
    cols = (a[~mg][:, :3] * 255).round().astype(int); u, c = np.unique(cols, axis=0, return_counts=True); col = u[c.argmax()] / 255.0
    k = 0.86 * min(w / M.width, h / M.height); mw, mh = max(1, round(M.width * k)), max(1, round(M.height * k))
    mk = np.asarray(M.resize((mw, mh), Image.LANCZOS)) > 127
    canvas = np.zeros((h, w), bool); y0, x0 = (h - mh) // 2, (w - mw) // 2; canvas[y0:y0 + mh, x0:x0 + mw] = mk
    canvas = canvas[::-1]                                     # Blender pixels are bottom-up
    new = np.zeros((h, w, 4)); new[..., 3] = 1; new[..., 0] = 1; new[..., 2] = 1
    new[canvas, 0], new[canvas, 1], new[canvas, 2] = col
    im.pixels[:] = new.ravel(); im.update(); im.pack()
    print('SIGIL', nm, (w, h), 'colour', [int(x * 255) for x in col], 'cover', round(canvas.mean(), 3))
for f in [f for f in fixes.split(';') if f]:
    nm, rgb = f.split('='); r, g, b = [int(x) / 255 for x in rgb.split(',')]
    import os, tempfile; p = os.path.join(tempfile.mkdtemp(), nm)
    Image.new('RGB', (512, 512), tuple(int(x) for x in rgb.split(','))).save(p)
    im = bpy.data.images[nm]; im.filepath = p; im.source = 'FILE'; im.reload(); im.pack(); print('FIXED', nm, rgb, im.size[:])
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
