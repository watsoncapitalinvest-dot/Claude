#!/usr/bin/env python3
"""The Pit's gas bottles (LABSCI part 93) as a rendered 3D model rather than a flat drawing.

John, 15 Nov (screen029): "the gas tanks should be imported models and they should explode when shot".
The explosion is mod/Ruleset/zz_gijoe_gas_bottles.rul. This is the picture.

A small ray tracer in the battlescape's own camera: X-COM's dimetric view, one tile a 128 x 64 floor
diamond whose top corner sits at (64, 96) in a 128 x 160 frame, one storey 96 px tall. Each bottle is a
cylinder with a domed shoulder, a neck and a valve cap. Shaded in three flat bands with a sheen down
the lit side and an ink outline, like the rest of the kit's terrain art; rendered at 3x and reduced.

    python3 build/render_gas_bottles.py            # writes the frame into LABSCI_4X.png/.PCK and LABSCI.PCK
    python3 build/render_gas_bottles.py --preview out.png
"""
import os, sys, struct
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.join(HERE, '..', 'mod')
FRAME = 93
SS = 3                      # supersampling
W, H = 128, 160

# (x, y) on the tile floor (0..1), radius, height in storeys, body colour, band colour
BOTTLES = [
    ((0.18, 0.56), 0.085, 0.86, (46, 82, 178), (236, 236, 236)),   # blue, white band
    ((0.30, 0.18), 0.085, 0.92, (44, 138, 66), (236, 236, 236)),   # green
    ((0.68, 0.38), 0.085, 0.84, (228, 230, 234), (196, 40, 36)),   # white, red band
    ((0.58, 0.74), 0.085, 0.78, (220, 134, 40), (40, 40, 40)),     # orange, black band
]
STEEL = (92, 96, 104)
BRASS = (176, 150, 70)
INK = (24, 26, 30)
LIGHT = np.array([-0.55, 0.15, 0.82]); LIGHT = LIGHT / np.linalg.norm(LIGHT)
VIEW = np.array([1.0, 1.0, 2.0 / 3.0]); VIEW = VIEW / np.linalg.norm(VIEW)


def rays():
    ys, xs = np.mgrid[0:H * SS, 0:W * SS].astype(np.float64)
    sx = (xs + 0.5) / SS; sy = (ys + 0.5) / SS
    a = (sx - 64) / 64.0          # wx - wy
    b = (sy - 96) / 32.0          # wx + wy  (at wz = 0)
    p0 = np.stack([(a + b) / 2, (b - a) / 2, np.zeros_like(a)], -1)
    return p0, np.array([1.0, 1.0, 2.0 / 3.0])   # P = p0 + t d; larger t is nearer the camera


def cyl(p0, d, c, r, z0, z1, tbest, nbest, idbest, oid, colbest, col, capped=True):
    ox = p0[..., 0] - c[0]; oy = p0[..., 1] - c[1]
    A = d[0] ** 2 + d[1] ** 2; B = 2 * (ox * d[0] + oy * d[1]); C = ox ** 2 + oy ** 2 - r * r
    disc = B * B - 4 * A * C
    ok = disc >= 0
    sq = np.sqrt(np.where(ok, disc, 0))
    t = (-B + sq) / (2 * A)                         # the near wall
    z = p0[..., 2] + t * d[2]
    hit = ok & (z >= z0) & (z <= z1) & (t > tbest)
    nx = (ox + t * d[0]) / r; ny = (oy + t * d[1]) / r
    tbest[hit] = t[hit]; nbest[hit] = np.stack([nx, ny, np.zeros_like(nx)], -1)[hit]; idbest[hit] = oid; colbest[hit] = col
    if capped:
        tc = (z1 - p0[..., 2]) / d[2]
        px = ox + tc * d[0]; py = oy + tc * d[1]
        hit = (px ** 2 + py ** 2 <= r * r) & (tc > tbest)
        tbest[hit] = tc[hit]; nbest[hit] = (0, 0, 1); idbest[hit] = oid; colbest[hit] = col


def dome(p0, d, c, r, z0, hz, tbest, nbest, idbest, oid, colbest, col):
    """The shoulder: the upper half of an ellipsoid, radius r, height hz, sitting on z0."""
    s = np.array([1 / r, 1 / r, 1 / hz])
    o = (p0 - np.array([c[0], c[1], z0])) * s; dd = d * s
    A = (dd ** 2).sum(); B = 2 * (o * dd).sum(-1); C = (o ** 2).sum(-1) - 1
    disc = B * B - 4 * A * C
    ok = disc >= 0
    t = (-B + np.sqrt(np.where(ok, disc, 0))) / (2 * A)
    q = o + t[..., None] * dd
    hit = ok & (q[..., 2] >= 0) & (t > tbest)
    n = q * s; n = n / np.linalg.norm(n, axis=-1, keepdims=True)
    tbest[hit] = t[hit]; nbest[hit] = n[hit]; idbest[hit] = oid; colbest[hit] = col


def render():
    p0, d = rays()
    shp = p0.shape[:2]
    t = np.full(shp, -1e9); n = np.zeros(shp + (3,)); oid = np.zeros(shp, np.int32); col = np.zeros(shp + (3,))
    part = 1
    # far bottles first does not matter: the nearest hit wins
    for (c, r, h, body, band) in BOTTLES:
        sh = r * 0.9 / 0.75 * 0.75          # shoulder height in storeys, about the radius on screen
        hb = h - sh - 0.12                  # body top
        cyl(p0, d, c, r, 0.0, hb, t, n, oid, part, col, np.array(body, float), capped=False)
        # the band: a ring a little below the shoulder, drawn as a slightly proud cylinder
        cyl(p0, d, c, r * 1.02, hb - 0.10, hb - 0.05, t, n, oid, part, col, np.array(band, float), capped=False)
        dome(p0, d, c, r, hb, sh, t, n, oid, part, col, np.array(body, float))
        cyl(p0, d, c, r * 0.30, hb + sh * 0.85, hb + sh + 0.05, t, n, oid, part + 1, col, np.array(BRASS, float))
        cyl(p0, d, c, r * 0.48, hb + sh + 0.05, h, t, n, oid, part + 2, col, np.array(STEEL, float))
        # the valve handle: a short bar off the cap, toward the viewer's left
        part += 3
    # a steel restraint bar behind them, across the two back bottles, as racks have
    hit = t > -1e8
    lam = np.clip((n * LIGHT).sum(-1), 0, 1)
    band = np.where(lam > 0.72, 1.12, np.where(lam > 0.38, 0.92, 0.66))
    rgb = col * band[..., None]
    # the sheen: a pale stripe where the reflection of the light points at the camera
    hv = LIGHT + VIEW; hv = hv / np.linalg.norm(hv)
    spec = (n * hv).sum(-1)
    rgb = np.where((spec > 0.93)[..., None] & hit[..., None], rgb * 0.35 + 255 * 0.65, rgb)
    rgb = np.clip(rgb, 0, 255)
    # ink: where the part changes, or the depth jumps (one bottle in front of another)
    ink = np.zeros(shp, bool)
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        o2 = np.roll(np.roll(oid, dy, 0), dx, 1); t2 = np.roll(np.roll(t, dy, 0), dx, 1)
        ink |= hit & ((o2 != oid) | (np.abs(t2 - t) > 0.04))
    k = 2 * SS // 2
    grow = ink.copy()
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            grow |= np.roll(np.roll(ink, dy, 0), dx, 1)
    ink = grow & hit
    rgb[ink] = INK
    a = np.where(hit, 255, 0).astype(np.float64)
    img = np.dstack([rgb, a]).astype(np.uint8)
    big = Image.fromarray(img, 'RGBA')
    # premultiplied reduce, so the edge does not pick up black from empty pixels
    pm = np.array(big).astype(np.float64); pm[..., :3] *= pm[..., 3:4] / 255
    small = Image.fromarray(pm.astype(np.uint8), 'RGBA').resize((W, H), Image.BOX)
    s = np.array(small).astype(np.float64)
    al = s[..., 3:4]
    s[..., :3] = np.where(al > 0, s[..., :3] * 255 / np.maximum(al, 1), 0)
    s[..., 3] = np.where(s[..., 3] < 20, 0, s[..., 3])
    return Image.fromarray(np.clip(s, 0, 255).astype(np.uint8), 'RGBA')


def read_pck(path, tab, w, h, wide):
    data = open(path, 'rb').read(); tb = open(tab, 'rb').read()
    fmt, step = ('<I', 4) if wide else ('<H', 2)
    offs = [struct.unpack_from(fmt, tb, i)[0] for i in range(0, len(tb) - step + 1, step)]
    out = []
    for i, o in enumerate(offs):
        end = offs[i + 1] if i + 1 < len(offs) else len(data)
        out.append(data[o:end])
    return out


def encode(idx):
    """One frame (2-D uint8 palette indices, 0 = clear) in UFO PCK form."""
    h, w = idx.shape
    flat = idx.reshape(-1)
    skip = 0
    while skip < h and not idx[skip].any():
        skip += 1
    out = bytearray([skip])
    pos = skip * w
    last = len(flat)
    while last > pos and flat[last - 1] == 0:
        last -= 1
    run = 0
    for v in flat[pos:last]:
        if v == 0:
            run += 1
            if run == 255:
                out += bytes([0xFE, 255]); run = 0
            continue
        if run:
            out += bytes([0xFE, run]); run = 0
        out.append(int(v) if v not in (0xFE, 0xFF) else 0xFD)
    out.append(0xFF)
    return bytes(out)


def quant(img, pal):
    a = np.array(img.convert('RGBA')).astype(np.int32)
    rgb = a[..., :3].reshape(-1, 1, 3); P = pal[1:].reshape(1, -1, 3)
    best = np.zeros(rgb.shape[0], np.int64)
    for s in range(0, rgb.shape[0], 4096):
        dd = ((rgb[s:s + 4096] - P) ** 2).sum(-1)
        best[s:s + 4096] = dd.argmin(1) + 1
    idx = best.reshape(a.shape[:2]).astype(np.uint8)
    idx[a[..., 3] < 128] = 0
    return idx


def write_pck(frames, path, tab, wide):
    data = b''.join(frames); offs = []; o = 0
    for f in frames:
        offs.append(o); o += len(f)
    open(path, 'wb').write(data)
    open(tab, 'wb').write(b''.join(struct.pack('<I' if wide else '<H', x) for x in offs))


def main():
    img = render()
    if len(sys.argv) > 2 and sys.argv[1] == '--preview':
        bg = Image.new('RGBA', (W, H), (120, 120, 120, 255)); bg.alpha_composite(img)
        bg.resize((W * 3, H * 3), Image.NEAREST).save(sys.argv[2]); return
    sys.path.insert(0, HERE)
    from make_air_terrain import battle_palette
    pal = np.array(battle_palette(), np.int32).reshape(-1, 3)[:256]
    t = os.path.join(MOD, 'TERRAIN')
    sheet = Image.open(os.path.join(t, 'LABSCI_4X.png')).convert('RGBA')
    x0, y0 = (FRAME % 8) * W, (FRAME // 8) * H
    sheet.paste(Image.new('RGBA', (W, H), (0, 0, 0, 0)), (x0, y0)); sheet.alpha_composite(img, (x0, y0))
    sheet.save(os.path.join(t, 'LABSCI_4X.png'))
    # both packs carry 32-bit TAB offsets
    for suffix, w, h, wide, pic in (('_4X', 128, 160, True, img), ('', 32, 40, True, img.resize((32, 40), Image.LANCZOS))):
        p, tb = os.path.join(t, f'LABSCI{suffix}.PCK'), os.path.join(t, f'LABSCI{suffix}.TAB')
        frames = read_pck(p, tb, w, h, wide)
        frames[FRAME] = encode(quant(pic, pal))
        write_pck(frames, p, tb, wide)
    print('LABSCI frame', FRAME, 'rendered and installed')


if __name__ == '__main__':
    main()
