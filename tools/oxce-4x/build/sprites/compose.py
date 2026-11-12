"""Ink pass + assemble: beauty/ID frames -> inked frames -> GIFs and contact sheets."""
import os, sys, json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
F = sys.argv[1]; OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
meta = json.load(open(f'{F}/meta.json'))
BG = np.array([200, 200, 205], np.float32)
HAIR_BASE = np.array([246, 182, 22], np.float32); HAIR_SHADOW = np.array([212, 140, 20], np.float32); HAIR_LINE = np.array([96, 58, 14], np.float32); INK = np.array([40, 26, 18], np.float32)
SIZE = (512, 640); FINAL = (256, 320); DZ = 0.10

def ink_frame(beauty, idimg):
    b = beauty.resize(SIZE, Image.LANCZOS); a = np.asarray(b).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3] / 255.0
    idrgb = np.asarray(idimg.convert('RGB').resize(SIZE, Image.NEAREST)).astype(np.float32)
    idb = np.round(idrgb[..., 0] / 255 * 40).astype(np.int16)
    dep = idrgb[..., 1] / 255.0 * 4.0                        # metres, camera depth
    idb[al < 0.5] = 0
    img = rgb * al[..., None] + BG * (1 - al[..., None])
    H, W = idb.shape
    # hair: one clean mass
    hair = idb == 1
    if hair.any():
        r = 4; disk = np.hypot(*np.mgrid[-r:r+1, -r:r+1]) <= r
        clean = ndi.binary_fill_holes(ndi.binary_closing(hair, structure=disk))
        clean = ndi.binary_opening(clean, structure=np.hypot(*np.mgrid[-1:2, -1:2]) <= 1)
        gap = clean & ~hair & ((idb == 0) | (idb == 2)); img[gap] = HAIR_BASE; idb[gap] = 1
        spike = hair & ~clean; img[spike] = BG; idb[spike] = 0
        # flat two-tone fill over the whole cleaned hair shape (hides scalp showing between strands)
        lum = ndi.gaussian_filter(img.mean(-1), 2.5)
        thr = np.percentile(lum[clean], 30)
        tone = ndi.median_filter((lum > thr).astype(np.uint8), size=7)
        img[clean] = np.where(tone[clean][:, None] == 1, HAIR_BASE, HAIR_SHADOW)
        idb[clean] = 1
    fg = idb > 0
    e = np.zeros_like(fg); eh = np.zeros_like(fg); soft = np.zeros_like(fg)
    for dy, dx in ((0, 1), (1, 0)):
        a1 = idb[:H - dy, :W - dx]; a2 = idb[dy:, dx:]
        d1 = dep[:H - dy, :W - dx]; d2 = dep[dy:, dx:]
        diff = ((a1 != a2) & ((a1 > 0) | (a2 > 0))) | ((a1 > 0) & (a2 > 0) & (np.abs(d1 - d2) > DZ) & (a1 != 1) & (a2 != 1))
        hp = (a1 == 1) | (a2 == 1)
        outer = diff & hp & (((a1 == 1) & (a2 == 0)) | ((a1 == 0) & (a2 == 1)))
        sj = diff & hp & ~outer
        ee = diff & ~hp
        e[:H - dy, :W - dx] |= ee; e[dy:, dx:] |= ee
        eh[:H - dy, :W - dx] |= outer & (a1 == 1); eh[dy:, dx:] |= outer & (a2 == 1)
        soft[:H - dy, :W - dx] |= sj & (a1 == 1); soft[dy:, dx:] |= sj & (a2 == 1)
    e &= ndi.binary_dilation(fg, iterations=1) & (fg | ndi.binary_dilation(fg, iterations=1))
    e &= fg                                                     # line sits on the figure
    near_hair = ndi.binary_dilation(idb == 1, iterations=2); touches_bg = ndi.binary_dilation(idb == 0, iterations=1)
    e &= ~(near_hair & ~touches_bg)
    lab, n = ndi.label(e, structure=np.ones((3, 3)))
    if n:
        sz = ndi.sum(e, lab, range(1, n + 1)); e &= np.isin(lab, [i for i, z in enumerate(sz, 1) if z >= 10])
    if soft.any():
        band = ndi.binary_dilation(soft, iterations=1) & fg & ~e
        blur = np.stack([ndi.gaussian_filter(img[..., c], 0.8) for c in range(3)], -1); img[band] = blur[band]
    e = (ndi.binary_dilation(e, iterations=1) & fg)          # ~3 px at 2x, kept on the figure -> ~1.5 px at final size
    eh = ndi.binary_dilation(eh, iterations=1) & (idb == 1) & ~e
    img[e] = INK
    img[eh] = HAIR_LINE
    return Image.fromarray(img.clip(0, 255).astype(np.uint8)).resize(FINAL, Image.LANCZOS)   # downscale = soft anti-aliased lines

dirs = meta['dirs']; n = meta['frames']
inked = {}
for k in dirs:
    for i in range(n):
        p = f'{F}/d{k}_f{i:02d}'
        if not os.path.exists(p + '_id.png'): continue
        inked[(k, i)] = ink_frame(Image.open(p + '_beauty.png').convert('RGBA'), Image.open(p + '_id.png'))
LABEL = {1: 'away', 2: 'away-right', 3: 'right', 4: 'toward-right', 5: 'toward', 6: 'toward-left', 7: 'left', 8: 'away-left'}
done_dirs = [k for k in dirs if all((k, i) in inked for i in range(n))]
# 8-direction grid GIF
cols = 4; rows = (len(done_dirs) + cols - 1) // cols
grid_frames = []
for i in range(n):
    g = Image.new('RGB', (cols * FINAL[0], rows * FINAL[1]), tuple(BG.astype(int)))
    d = ImageDraw.Draw(g)
    for j, k in enumerate(done_dirs):
        x, y = (j % cols) * FINAL[0], (j // cols) * FINAL[1]
        g.paste(inked[(k, i)], (x, y)); d.text((x + 6, y + 6), f'{k} {LABEL[k]}', fill=(40, 40, 40))
    grid_frames.append(g)
if grid_frames:
    grid_frames[0].save(f'{OUT}/duke_walk_8dir.gif', save_all=True, append_images=grid_frames[1:], duration=67, loop=0, optimize=False)
    grid_frames[0].save(f'{OUT}/duke_walk_8dir_frame0.png')
# big single direction + game-size strip
for k in done_dirs:
    big = [inked[(k, i)].resize((512, 640), Image.NEAREST) for i in range(n)]
    big[0].save(f'{OUT}/duke_walk_d{k}_big.gif', save_all=True, append_images=big[1:], duration=67, loop=0)
# contact sheet: every frame of every direction, game size (1x = 128x160)
cs = Image.new('RGB', (n * 128, len(done_dirs) * 160), tuple(BG.astype(int)))
for r, k in enumerate(done_dirs):
    for i in range(n): cs.paste(inked[(k, i)].resize((128, 160), Image.LANCZOS), (i * 128, r * 160))
cs.save(f'{OUT}/duke_walk_contact_gamesize.png')
print('dirs', done_dirs, 'frames', n)
