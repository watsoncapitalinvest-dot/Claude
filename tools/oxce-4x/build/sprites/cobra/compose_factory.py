"""Character factory, stations 6/7 (Cut + Proof): ink pass on beauty/ID frames (same rules as Duke's compose.py),
then: inventory PNG (640x1600, FF00FF key), battle frames (128x160 per frame, magenta key), 8-dir GIF, proof sheet.
Usage: python3 compose_factory.py <chars_dir> <out_dir> id1,id2,...
"""
import os, sys, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

INK = np.array([40, 26, 18], np.float32); DZ = 0.10
MAG = (255, 0, 255)

def ink(beauty, idimg, tones, final_size=None, shade=None):
    """Returns RGBA at half the render size (the 2x -> 1x downscale), or resized to final_size."""
    HB, HS, HL = [np.array(t, np.float32) for t in tones]
    a = np.asarray(beauty).astype(np.float32); rgb, al = a[..., :3].copy(), a[..., 3] / 255.0
    idrgb = np.asarray(idimg.convert('RGB').resize(beauty.size, Image.NEAREST)).astype(np.float32)
    idb = np.round(idrgb[..., 0] / 255 * 40).astype(np.int16); dep = idrgb[..., 1] / 255.0 * 4.0
    idb[al < 0.5] = 0
    img = rgb
    H, W = idb.shape
    hair = idb == 1
    if hair.any():
        r = 4; disk = np.hypot(*np.mgrid[-r:r + 1, -r:r + 1]) <= r
        clean = ndi.binary_fill_holes(ndi.binary_closing(hair, structure=disk))
        clean = ndi.binary_opening(clean, structure=np.hypot(*np.mgrid[-1:2, -1:2]) <= 1)
        gap = clean & ~hair & ((idb == 0) | (idb == 2)); img[gap] = HB; idb[gap] = 1
        spike = hair & ~clean; idb[spike] = 0
        lum = ndi.gaussian_filter(img.mean(-1), 2.5)
        thr = np.percentile(lum[clean], 30)
        tone = ndi.median_filter((lum > thr).astype(np.uint8), size=7)
        img[clean] = np.where(tone[clean][:, None] == 1, HB, HS); idb[clean] = 1
    fg = idb > 0
    e = np.zeros_like(fg); eh = np.zeros_like(fg); soft = np.zeros_like(fg)
    # throat V (garment id 16, painted skin by fix_collar.py): joins the neck skin (id 2) with no line, and no depth-jump
    # ink inside it (the shirt mesh folds over itself at the throat)
    ide = np.where(idb == 16, 2, idb); nod = (idb == 16)
    for dy, dx in ((0, 1), (1, 0)):
        a1 = ide[:H - dy, :W - dx]; a2 = ide[dy:, dx:]
        n1 = nod[:H - dy, :W - dx] | nod[dy:, dx:]
        d1 = dep[:H - dy, :W - dx]; d2 = dep[dy:, dx:]
        diff = ((a1 != a2) & ((a1 > 0) | (a2 > 0))) | ((a1 > 0) & (a2 > 0) & (np.abs(d1 - d2) > DZ) & (a1 != 1) & (a2 != 1) & ~n1)
        hp = (a1 == 1) | (a2 == 1)
        outer = diff & hp & (((a1 == 1) & (a2 == 0)) | ((a1 == 0) & (a2 == 1)))
        sj = diff & hp & ~outer; ee = diff & ~hp
        e[:H - dy, :W - dx] |= ee; e[dy:, dx:] |= ee
        eh[:H - dy, :W - dx] |= outer & (a1 == 1); eh[dy:, dx:] |= outer & (a2 == 1)
        soft[:H - dy, :W - dx] |= sj & (a1 == 1); soft[dy:, dx:] |= sj & (a2 == 1)
    e &= fg
    near_hair = ndi.binary_dilation(idb == 1, iterations=2); touches_bg = ndi.binary_dilation(idb == 0, iterations=1)
    e &= ~(near_hair & ~touches_bg)
    lab, n = ndi.label(e, structure=np.ones((3, 3)))
    if n:
        sz = ndi.sum(e, lab, range(1, n + 1)); e &= np.isin(lab, [i for i, z in enumerate(sz, 1) if z >= 10])
    if soft.any():
        band = ndi.binary_dilation(soft, iterations=1) & fg & ~e
        blur = np.stack([ndi.gaussian_filter(img[..., c], 0.8) for c in range(3)], -1); img[band] = blur[band]
    scale = max(1, round(H / 640))                           # ~3 px ink at the 2x size for the sprite renders
    pen = np.zeros_like(fg); facepen = None
    if shade is not None:
        # comic folds from the geometry pass: a shadow tone where the sculpted folds turn from the key light,
        # and pen strokes along the sharp fold edges. Cloth/gear only - never the face, mask edge or helmet.
        S = np.asarray(shade.convert('L').resize(beauty.size, Image.BILINEAR)).astype(np.float32)
        S = ndi.gaussian_filter(S, 1.2 * max(1, round(H / 640)) / 2)
        cloth = fg & ~np.isin(idb, (0, 1, 2, 3, 4, 5, 6, 30))   # never on face, helmet, faceplate, slit or crest
        if os.environ.get('PENIDS'):                               # restrict pen work to these garment IDs (e.g. trousers only)
            cloth = fg & np.isin(idb, [int(x) for x in os.environ['PENIDS'].split(',')])
        ref = np.percentile(S[cloth], 70) if cloth.any() else 1
        dark = cloth & (S < ref * float(os.environ.get('PENDARK', 0.62)))
        dark = ndi.binary_opening(ndi.binary_closing(dark, iterations=1), iterations=max(1, round(H / 640)))
        img[dark] = img[dark] * 0.70
        gm = np.hypot(ndi.sobel(S, 0), ndi.sobel(S, 1))
        sc_ = max(1, round(H / 640))
        ridge = cloth & (gm > np.percentile(gm[cloth], float(os.environ.get('PENPCT', 93)))) & ndi.binary_erosion(fg, iterations=2 * sc_)
        ridge &= dark | ndi.binary_dilation(dark, iterations=1)
        lab, n = ndi.label(ridge, structure=np.ones((3, 3)))
        if n:
            sz = ndi.sum(ridge, lab, range(1, n + 1)); ridge &= np.isin(lab, [i for i, z in enumerate(sz, 1) if z >= 10 * sc_ * sc_])
        pen |= ridge
        if os.environ.get('PENFACE'):
            # light pen on the face/neck (PENFACE=1): a soft shadow tone on the side away from the key light and a
            # few short strokes at the strongest turns (nose side, brow, jaw). Milder than the cloth on purpose.
            face = fg & np.isin(idb, [int(x) for x in os.environ.get('PENFACEIDS', '2,16').split(',')]) & ndi.binary_erosion(fg, iterations=2 * sc_)
            if face.sum() > 200:
                fref = np.percentile(S[face], 70)
                fd = face & (S < fref * float(os.environ.get('PENFACEDARK', 0.72)))
                fd = ndi.binary_opening(ndi.binary_closing(fd, iterations=1), iterations=sc_)
                img[fd] = img[fd] * float(os.environ.get('PENFACETONE', 0.84))
                fr = face & (gm > np.percentile(gm[face], float(os.environ.get('PENFACEPCT', 95)))) & (fd | ndi.binary_dilation(fd, iterations=1))
                lab, n = ndi.label(fr, structure=np.ones((3, 3)))
                if n:
                    sz = ndi.sum(fr, lab, range(1, n + 1)); fr &= np.isin(lab, [i for i, z in enumerate(sz, 1) if z >= 14 * sc_ * sc_])
                facepen = fr
    if os.environ.get('PEN'):
        # pen work: thin ink along the fold-shadow edges inside each garment (comic-style creases), not on the face/hair
        lum = ndi.gaussian_filter(img.mean(-1), 1.0)
        shadow = np.zeros_like(fg)
        for g in np.unique(idb):
            if g in (0, 1, 2, 30): continue
            m = idb == g
            if m.sum() < 50: continue
            shadow |= m & (lum < np.median(lum[m]) * 0.82)
        shadow = ndi.binary_opening(shadow, iterations=1)
        edge = shadow & ~ndi.binary_erosion(shadow, iterations=1)
        edge &= ndi.binary_erosion(fg, iterations=2) & ~e
        same = ndi.maximum_filter(idb, 3) == ndi.minimum_filter(idb, 3)       # stay off garment borders (the outline does those)
        edge &= same
        lab, n = ndi.label(edge, structure=np.ones((3, 3)))
        if n:
            sz = ndi.sum(edge, lab, range(1, n + 1)); edge &= np.isin(lab, [i for i, z in enumerate(sz, 1) if z >= 12 * scale])
        pen = ndi.binary_dilation(edge, iterations=max(0, scale // 2)) & fg if scale > 1 else edge
    e = ndi.binary_dilation(e, iterations=scale) & fg
    eh = ndi.binary_dilation(eh, iterations=scale) & (idb == 1) & ~e
    img[pen & ~e] = img[pen & ~e] * 0.25 + INK * 0.75
    if facepen is not None: fp = facepen & ~e & ~pen; img[fp] = img[fp] * 0.45 + INK * 0.55       # softer brown on skin
    img[e] = INK; img[eh] = HL
    out = np.dstack([img.clip(0, 255), fg.astype(np.float32) * 255]).astype(np.uint8)
    im = Image.fromarray(out, 'RGBA')
    # premultiply-safe downscale
    pm = np.asarray(im).astype(np.float32); pm[..., :3] *= pm[..., 3:4] / 255
    size = final_size or (W // 2, H // 2)
    r = np.dstack([np.asarray(Image.fromarray(pm[..., c].astype(np.float32), 'F').resize(size, Image.LANCZOS)) for c in range(4)])
    r[..., 3] = r[..., 3].clip(0, 255); m = r[..., 3] > 1
    r[m, :3] = r[m, :3] / (r[m, 3:4] / 255)
    return Image.fromarray(r.clip(0, 255).astype(np.uint8), 'RGBA')

def keyed(rgba, bg=MAG, thr=128):
    a = np.asarray(rgba).copy(); m = a[..., 3] < thr
    out = a[..., :3].copy(); out[m] = bg
    return Image.fromarray(out, 'RGB')

def on_bg(rgba, bg):
    b = Image.new('RGBA', rgba.size, bg + (255,)); b.alpha_composite(rgba); return b.convert('RGB')

def inventory(d, tones, mirror):
    b = Image.open(f'{d}/inv/front_beauty.png').convert('RGBA'); i = Image.open(f'{d}/inv/front_id.png')
    sp = f'{d}/inv/front_shade.png'
    full = ink(b, i, tones, final_size=b.size, shade=Image.open(sp) if os.path.exists(sp) else None)                 # ink at render size, scale below
    al = np.asarray(full)[..., 3]; ys, xs = np.where(al > 128)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = full.crop((x0, y0, x1, y1))
    k = 1520 / (y1 - y0); nw = max(1, round((x1 - x0) * k))
    fig = ink_resize(crop, (nw, 1520))
    if nw > 620: fig = ink_resize(crop, (620, round(1520 * 620 / nw)))
    if mirror: fig = fig.transpose(Image.FLIP_LEFT_RIGHT)
    canvas = Image.new('RGBA', (640, 1600), (255, 0, 255, 0))
    canvas.alpha_composite(fig, ((640 - fig.width) // 2, 40))
    return canvas

def ink_resize(im, size):
    pm = np.asarray(im).astype(np.float32); pm[..., :3] *= pm[..., 3:4] / 255
    r = np.dstack([np.asarray(Image.fromarray(pm[..., c], 'F').resize(size, Image.LANCZOS)) for c in range(4)])
    r[..., 3] = r[..., 3].clip(0, 255); m = r[..., 3] > 1; r[m, :3] = r[m, :3] / (r[m, 3:4] / 255)
    return Image.fromarray(r.clip(0, 255).astype(np.uint8), 'RGBA')

LABEL = {1: 'away', 2: 'away-right', 3: 'right', 4: 'toward-right', 5: 'toward', 6: 'toward-left', 7: 'left', 8: 'away-left'}
GREY = (200, 200, 205)

def walk(d, tones):
    meta = json.load(open(f'{d}/walk/meta.json')); n = meta['frames']; dirs = meta['dirs']
    fr = {}
    for k in dirs:
        for i in range(n):
            p = f'{d}/walk/d{k}_f{i:02d}'
            sh = Image.open(p + '_shade.png') if os.path.exists(p + '_shade.png') else None
            fr[(k, i)] = ink(Image.open(p + '_beauty.png').convert('RGBA'), Image.open(p + '_id.png'), tones, shade=sh)  # 256x320
    return fr, n, dirs

def main():
    CH, OUT, ids = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
    os.makedirs(OUT, exist_ok=True)
    for cid in ids:
        d = f'{CH}/{cid}'; meta = json.load(open(f'{d}/meta.json')); tones = meta['hair_tones']
        o = f'{OUT}/{cid}'; os.makedirs(o, exist_ok=True)
        if os.path.exists(f'{d}/inv/front_beauty.png'):
            inv = inventory(d, tones, meta['mirror'])
            keyed(inv).save(f'{o}/{cid}_inventory_640x1600.png')
            on_bg(inv, GREY).resize((160, 400), Image.LANCZOS).save(f'{o}/_inv_thumb.png')
        if os.path.exists(f'{d}/walk/meta.json'):
            fr, n, dirs = walk(d, tones)
            # game sheet: rows = directions 1..8, cols = frames, 128x160 cells, magenta key
            sheet = Image.new('RGB', (n * 128, len(dirs) * 160), MAG)
            for r, k in enumerate(dirs):
                for i in range(n): sheet.paste(keyed(ink_resize(fr[(k, i)], (128, 160))), (i * 128, r * 160))
            sheet.save(f'{o}/{cid}_walk_rifle_128x160_sheet.png')
            cols = 4; rows = (len(dirs) + cols - 1) // cols; g = []
            for i in range(n):
                im = Image.new('RGB', (cols * 256, rows * 320), GREY); dr = ImageDraw.Draw(im)
                for j, k in enumerate(dirs):
                    x, y = (j % cols) * 256, (j // cols) * 320
                    im.paste(on_bg(fr[(k, i)], GREY), (x, y)); dr.text((x + 6, y + 6), f'{k} {LABEL[k]}', fill=(40, 40, 40))
                g.append(im)
            g[0].save(f'{o}/{cid}_walk_8dir.gif', save_all=True, append_images=g[1:], duration=67, loop=0)
            on_bg(fr[(5, 0)], GREY).save(f'{o}/_walk_thumb.png')
        print('composed', cid, flush=True)

if __name__ == '__main__':
    main()
