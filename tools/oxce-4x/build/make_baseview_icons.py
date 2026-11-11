"""Base-view facility sprites as ICONS, derived from each room's prop census.

The faithful top-down plan did not work and the reason was not fixable by polish:
at ten tiles to a 32px square a prop is three pixels, and real rooms line their
furniture along the walls, so every sprite came out an empty square with clutter
round the rim. Vanilla's base sprites are not plans. They are emblems - rows of
beds, a radar dish, hazard stripes - that fill the square and read instantly.

So the room's CONTENTS pick the emblem, which keeps this derived rather than drawn.
A plain count picks the wrong prop, because crates appear 202 times across the set
and identify nothing; each prop is weighted against how many rooms contain it, so
j_bunks resolves to cot x8 and j_archives to bookshelf x9.

Colours are each prop's own first fill out of props.py, snapped to the palette
indices VANILLA ITSELF USES in its facility frames. Quantising against the whole
256 is what let the globe markers pick white for a gold line; the same restriction
is the same fix.
"""
import sys, os, re, json, math, struct, collections
from PIL import Image, ImageDraw

SRC, PLACE, PALDAT, BASEBITS, OUT = sys.argv[1:6]
os.makedirs(OUT, exist_ok=True)
G, PX = 10, 32

def hx(c):
    c = c.lstrip('#'); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

# ---- palette 1, and the indices vanilla's own facility frames use ---------
raw = open(PALDAT, 'rb').read()
pal = [min(255, c << 2) for c in raw[774:774 + 768]]
RGB = [tuple(pal[i*3:i*3+3]) for i in range(256)]
pck, tab = BASEBITS + '.PCK', BASEBITS + '.TAB'
t = open(tab, 'rb').read(); dpk = open(pck, 'rb').read()
wide = len(t) >= 4 and struct.unpack('<I', t[:4])[0] == 0
offs = (list(struct.unpack('<%dI' % (len(t)//4), t)) if wide
        else list(struct.unpack('<%dH' % (len(t)//2), t)))
used = set()
for i in range(1, min(37, len(offs))):
    o = offs[i]; p = o; pos = dpk[p]*32; p += 1
    while p < len(dpk) and dpk[p] != 255:
        v = dpk[p]; p += 1
        if v == 254: pos += dpk[p]; p += 1
        else:
            if v: used.add(v)
            pos += 1
USES = sorted(used)

def snap(c):
    """nearest allowed index, redmean - the weighting sep() uses in build_watch."""
    best, bd = USES[0], 1e18
    for i in USES:
        p = RGB[i]; rm = (p[0]+c[0])/2
        dd = ((2+rm/256)*(p[0]-c[0])**2 + 4*(p[1]-c[1])**2
              + (2+(255-rm)/256)*(p[2]-c[2])**2)
        if dd < bd: bd, best = dd, i
    return best

def shade(i, f):
    return snap(tuple(max(0, min(255, int(v*f))) for v in RGB[i]))

# ---- colours out of the package ------------------------------------------
iso = open(os.path.join(SRC, 'isolib.py'), encoding='utf-8').read()
THEME = {}
for m in re.finditer(r"'(\w+)'\s*:\s*dict\((.*?)\)\s*,?\s*(?=\n|'|\})", iso, re.S):
    d0 = dict(re.findall(r"(\w+)\s*=\s*'(#[0-9a-fA-F]{6})'", m.group(2)))
    f = re.search(r"floor\s*=\s*\('(#[0-9a-fA-F]{6})'", m.group(2))
    if f: d0['floor'] = f.group(1)
    if 'wall' in d0: THEME[m.group(1)] = d0
props_src = open(os.path.join(SRC, 'props.py'), encoding='utf-8').read()
PROPC = {}
for b in re.split(r'\ndef ', props_src):
    m = re.match(r'(p_\w+)\(', b)
    if not m: continue
    h = re.findall(r"'(#[0-9a-fA-F]{6})'", b)
    if h: PROPC[m.group(1)[2:]] = h[0]

def prop_rgb(n):
    if n in PROPC: return hx(PROPC[n])
    base = n.split('_')[0]
    if base in PROPC: return hx(PROPC[base])
    if n.startswith('v_'): return hx('#4a5534')
    return (150, 150, 148)

rooms = json.load(open(PLACE))
N = len(rooms)
df = collections.Counter()
for r in rooms.values():
    for n in {p['n'] for p in r['props']}: df[n] += 1
FOOT = collections.defaultdict(collections.Counter)
for r in rooms.values():
    for p in r['props']: FOOT[p['n']][(round(p['w']), round(p['d']))] += 1

def signature(r):
    tf = collections.Counter(p['n'] for p in r['props'])
    return sorted(((c * math.log(N / df[n]), n, c) for n, c in tf.items()), reverse=True)

made = 0
for rid, r in sorted(rooms.items()):
    sx, sy = max(1, r['size'][0]), max(1, r['size'][1])
    T = THEME.get(r['theme'], THEME['joe'])
    Wd, Ht = PX*sx, PX*sy
    fl = snap(hx(T.get('floor', '#a9aca6')))
    im = Image.new('P', (Wd, Ht), fl); im.putpalette(pal)
    d = ImageDraw.Draw(im)
    # floor seams, so the ground is not a flat slab
    sm = shade(fl, .92)
    for gx in range(0, Wd, 8): d.line([(gx, 0), (gx, Ht-1)], fill=sm)
    for gy in range(0, Ht, 8): d.line([(0, gy), (Wd-1, gy)], fill=sm)

    sig = signature(r)
    if sig:
        w1, n1, c1 = sig[0]
        fw, fh = (FOOT[n1].most_common(1)[0][0] if FOOT[n1] else (1, 1))
        col = snap(prop_rgb(n1)); lit = shade(col, 1.35); dk = shade(col, .55)
        n = max(4, min(16, c1))
        cols = max(1, int(round(math.sqrt(n * (Wd/Ht) * (max(fh,1)/max(fw,1))))))
        rows = max(1, int(math.ceil(n / cols)))
        mx, my = 4, 4
        cw, ch = (Wd - 2*mx) / cols, (Ht - 2*my) / rows
        bw, bh = cw*0.70, ch*0.70
        if fh > fw: bh = ch*0.88; bw = cw*0.52
        elif fw > fh: bw = cw*0.88; bh = ch*0.52
        k = 0
        for rr in range(rows):
            for cc in range(cols):
                if k >= n: break
                k += 1
                x0 = mx + cc*cw + (cw-bw)/2; y0 = my + rr*ch + (ch-bh)/2
                x1, y1 = x0+bw-1, y0+bh-1
                d.rectangle([x0, y0, x1, y1], fill=col, outline=dk)
                d.line([(x0+1, y0), (x1-1, y0)], fill=lit)
    if len(sig) > 1:                       # the second prop as an edge band
        n2 = sig[1][1]; c2 = snap(prop_rgb(n2)); d2 = shade(c2, .55)
        for i in range(sx*3):
            x0 = 3 + i*(Wd-6)/(sx*3); d.rectangle([x0, Ht-6, x0+(Wd-6)/(sx*3)-2, Ht-4],
                                                  fill=c2, outline=d2)
    # LEAVE THE PLATE VISIBLE. The engine draws spriteShape first and this on top,
    # and art that is opaque to the edge hides the plate completely - every facility
    # then butts against its neighbour with no boundary and the base reads as one
    # grey field. Vanilla's frames sit inside the plate with its bevel showing as a
    # rim, so the art is inset and the corners are cut back, but ONLY on the sides
    # that face out of the whole facility: the squares of a 2x2 still meet flush.
    INSET, CUT = 2, 5
    for j in range(sy):
        for i in range(sx):
            fr = im.crop((i*PX, j*PX, (i+1)*PX, (j+1)*PX))
            px = fr.load()
            left, right = i == 0, i == sx-1
            top, bot = j == 0, j == sy-1
            for yy in range(PX):
                for xx in range(PX):
                    if (left and xx < INSET) or (right and xx >= PX-INSET) \
                       or (top and yy < INSET) or (bot and yy >= PX-INSET):
                        px[xx, yy] = 0
            for (ox, oy) in ((-1,-1), (1,-1), (-1,1), (1,1)):
                if not (((ox < 0 and left) or (ox > 0 and right))
                        and ((oy < 0 and top) or (oy > 0 and bot))):
                    continue
                for yy in range(CUT):
                    for xx in range(CUT - yy):
                        X = xx if ox < 0 else PX-1-xx
                        Y = yy if oy < 0 else PX-1-yy
                        px[X, Y] = 0
            fr.save(os.path.join(OUT, '%s_%d.png' % (rid, j*sx + i)))
            made += 1
print('rooms:', len(rooms), 'frames:', made, 'palette indices allowed:', len(USES))
