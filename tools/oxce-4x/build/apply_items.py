"""Painted equipment -> inventory icons and ground sprites.
Each item is one top-down painting. The inventory icon keeps the slot footprint the old sprite
had, so no item rule changes; the sharp twin beside it is what the inventory actually draws.
usage: apply_items.py <pack dir> <mod Resources/Items dir>
"""
import sys, os, numpy as np
from PIL import Image
SRC, OUT = sys.argv[1], sys.argv[2]

def cut(path):
    a = np.array(Image.open(path).convert('RGB')).astype(np.float32)
    m = np.minimum(a[...,0], a[...,2]) - a[...,1]
    al = np.clip((150 - m) / 90, 0, 1)
    M = np.array([255,0,255], np.float32)
    rgb = np.clip((a - (1-al[...,None])*M) / np.maximum(al[...,None], 0.05), 0, 255)
    pink = (np.minimum(rgb[...,0], rgb[...,2]) - rgb[...,1]) > 15
    rgb[...,0] = np.where(pink, np.minimum(rgb[...,0], rgb[...,1]+12), rgb[...,0])
    rgb[...,2] = np.where(pink, np.minimum(rgb[...,2], rgb[...,1]+22), rgb[...,2])
    im = Image.fromarray(np.dstack([rgb, al*255]).astype(np.uint8), 'RGBA')
    bb = im.getbbox()
    return im.crop(bb) if bb else im

def box(path, slot=16):
    """The inventory cells the existing sprite occupies. Snapped out to whole cells: the old art
    sat inked inside its slot, and fitting the new painting to that ink shrinks it for nothing."""
    a = np.array(Image.open(path).convert('RGBA'))
    nz = np.argwhere(a[...,3] > 0)
    x0, y0 = int(nz[:,1].min()), int(nz[:,0].min())
    x1, y1 = int(nz[:,1].max())+1, int(nz[:,0].max())+1
    if slot:
        W, H = Image.open(path).size
        x0 = (x0//slot)*slot; y0 = (y0//slot)*slot
        x1 = min(W, -(-x1//slot)*slot); y1 = min(H, -(-y1//slot)*slot)
    return x0, y0, x1, y1

def fit(im, bw, bh):
    k = min(bw/im.width, bh/im.height)
    return im.resize((max(1, round(im.width*k)), max(1, round(im.height*k))), Image.LANCZOS)

def quant(rgba, ref):
    """8-bit in the reference sprite's own palette; index 0 stays transparent"""
    pal = Image.open(ref).convert('P').getpalette()[:768]
    p = np.array(pal, np.int16).reshape(-1,3)[:256].astype(np.float32)
    a = np.array(rgba)
    rgb = a[...,:3].astype(np.float32)
    d = ((rgb[:,:,None,:] - p[None,None,1:,:])**2).sum(-1)      # never pick index 0
    idx = (d.argmin(-1) + 1).astype(np.uint8)
    idx[a[...,3] < 128] = 0
    out = Image.fromarray(idx, 'P'); out.putpalette(pal)
    return out

def iso(im):
    """a top-down item laid flat on the ground: turn it 45 degrees and foreshorten"""
    big = im.rotate(-45, Image.BICUBIC, expand=True)
    big = big.resize((big.width, max(1, big.height//2)), Image.LANCZOS)
    bb = big.getbbox()
    return big.crop(bb) if bb else big

# existing sprite -> the painting that replaces it
PAIRS = {'big_m4':'w_carbine', 'big_sniper':'w_sniper', 'big_uzi':'w_smg', 'big_rpg':'w_rocket',
         'big_cal50':'w_hmg', 'big_ledgers':'k_documents'}
n = 0
for stem, art in PAIRS.items():
    ref = f'{OUT}/{stem}.png'
    src = cut(f'{SRC}/{art}.png')
    x0, y0, x1, y1 = box(ref)
    W, H = Image.open(ref).size
    # --- inventory icon, in the footprint the old one had
    f = fit(src, x1-x0, y1-y0)
    can = Image.new('RGBA', (W, H), (0,0,0,0))
    can.alpha_composite(f, (x0 + (x1-x0-f.width)//2, y0 + (y1-y0-f.height)//2))
    quant(can, ref).save(ref)
    # --- its sharp twin, the same picture at 4x, which is what the inventory draws
    K = 4
    fh = fit(src, (x1-x0)*K, (y1-y0)*K)
    canh = Image.new('RGBA', (W*K, H*K), (0,0,0,0))
    canh.alpha_composite(fh, (x0*K + ((x1-x0)*K-fh.width)//2, y0*K + ((y1-y0)*K-fh.height)//2))
    canh.save(f'{OUT}/{stem}_hi.png')
    # --- the ground sprite, same frame and footprint as before
    fstem = stem.replace('big_', 'floor_')
    fref = f'{OUT}/{fstem}.png'
    if os.path.exists(fref):
        gx0, gy0, gx1, gy1 = box(fref, 0)   # the ground frame has no slot grid
        GW, GH = Image.open(fref).size
        g = fit(iso(src), gx1-gx0, gy1-gy0)
        gcan = Image.new('RGBA', (GW, GH), (0,0,0,0))
        gcan.alpha_composite(g, (gx0 + (gx1-gx0-g.width)//2, gy0 + (gy1-gy0-g.height)//2))
        quant(gcan, fref).save(fref)
        # the battlefield draws 8-bit and composites colour from this twin, so the item on the
        # ground is not palette-limited against full-colour terrain
        gcan.save(f'{OUT}/{fstem}_rgb.png')
    n += 1
print('items', n)
