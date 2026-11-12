"""Character factory, station 2 (Paint): recipe JSON -> per-character texture set.
Recolours Duke's approved FLAT textures garment-by-garment using the garment-ID maps,
keeping each texel's two-tone cel shading (shade = texel luminance / Duke's base luminance).
Usage: python3 prep_textures.py <roster.json> <outdir>
"""
import json, os, sys
import numpy as np
from PIL import Image

ANIM = '/mnt/user-data/uploads/Reference/models/mixamo/painted/duke/anim/'
TEXD = '/mnt/user-data/uploads/Reference/character_textures/'
ADD = '/tmp/claude-0/x/add/'
REC = '/tmp/claude-0/x/rec/'

GID = {19: 'shirt', 26: 'collar', 32: 'belt', 38: 'trousers', 45: 'boots', 51: 'hair', 57: 'webbing', 70: 'skin'}
DUKE = {'shirt': (242, 176, 55), 'collar': (63, 87, 32), 'belt': (219, 148, 40), 'trousers': (128, 121, 29),
        'boots': (118, 66, 26), 'hair': (246, 182, 22), 'webbing': (88, 105, 51), 'skin': (250, 170, 76)}
DUKE_SKIN_SH = np.array([165, 112, 50], np.float32)
HAIR_B = np.array([246, 182, 22], np.float32)


def lum(c):
    c = np.asarray(c, np.float32)
    return c[..., 0] * .299 + c[..., 1] * .587 + c[..., 2] * .114


def camo_tile(path, tile, size=2048):
    cam = Image.open(path).convert('RGB')
    t = max(1, int(round(size / tile)))
    cam = np.asarray(cam.resize((t, t), Image.LANCZOS)).astype(np.float32)
    reps = size // t + 1
    return np.tile(cam, (reps, reps, 1))[:size, :size]


def body_sheet(sheet, colors, camo):
    flat = np.asarray(Image.open(f'{ANIM}flat_Ch49_{sheet}_Diffuse.png').convert('RGB')).astype(np.float32)
    ids = np.asarray(Image.open(f'{ANIM}id_Ch49_{sheet}_Diffuse.png'))
    if ids.ndim == 3: ids = ids[..., 0]
    out = flat.copy()
    camo_img = camo_tile(TEXD + os.path.basename(camo['texture']), camo.get('tile', 6)) if camo else None
    for g, name in GID.items():
        m = ids == g
        if not m.any() or name not in colors: continue
        shade = np.clip(lum(flat[m]) / max(lum(DUKE[name]), 1), 0.3, 1.3)[:, None]
        base = np.array(colors[name], np.float32)[None, :].repeat(m.sum(), 0)
        if camo and name in camo['areas']:
            base = camo_img[m]
        out[m] = base * shade
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


def face_sheet(face_png, skin):
    a = np.asarray(Image.open(face_png).convert('RGB')).astype(np.float32)
    tgt = np.array(skin, np.float32)
    d1 = np.linalg.norm(a - np.array(DUKE['skin'], np.float32), axis=-1)
    d2 = np.linalg.norm(a - DUKE_SKIN_SH, axis=-1)
    m1, m2 = d1 < 34, (d2 < 34) & ~(d1 < 34)
    a[m1] = tgt; a[m2] = tgt * 0.66
    # drawn features (dark brown) stay readable on dark skin: lift them only if skin is dark
    if lum(tgt) < 110:
        feat = (lum(a) < 70) & (a[..., 0] > a[..., 2]) & ~m1 & ~m2
        a[feat] = np.array([24, 14, 10], np.float32)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def hair_sheet(hair):
    im = Image.open(ANIM + 'Ch33_hair_duke.png').convert('RGBA')
    a = np.asarray(im).astype(np.float32)
    rgb = a[..., :3]
    shade = np.clip(lum(rgb) / lum(HAIR_B), 0.5, 1.2)[..., None]
    a[..., :3] = np.array(hair, np.float32) * shade
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def hair_tones(hair):
    h = np.array(hair, np.float32)
    dark = lum(h) < 80
    base = h
    shadow = h * (0.86 if dark else 0.86)
    line = np.array([14, 12, 12], np.float32) if dark else h * 0.39
    return [base.round().tolist(), shadow.round().tolist(), line.round().tolist()]


def main():
    roster = json.load(open(sys.argv[1])); out = sys.argv[2]
    for c in roster:
        d = os.path.join(out, c['id']); os.makedirs(d, exist_ok=True)
        r = c['recipe'] if isinstance(c['recipe'], dict) else json.load(open(c['recipe'] if c['recipe'].startswith('/') else REC + c['recipe']))
        col = dict(r['colors']); col.update(c.get('override', {}))
        camo = r.get('camo')
        for s in ('1001', '1002'):
            body_sheet(s, col, camo).save(f'{d}/Ch49_{s}.png')
        face_src = ADD + c['face'] if c.get('face') else ANIM + 'Ch33_face_duke.png'
        face_sheet(face_src, col['skin']).save(f'{d}/face.png')
        hair_sheet(col['hair']).save(f'{d}/hair.png')
        meta = {'id': c['id'], 'name': c['name'], 'drop_hair': c.get('drop_hair', False),
                'hair_tones': hair_tones(col['hair']), 'mirror': c.get('mirror', False), 'notes': c.get('notes', [])}
        json.dump(meta, open(f'{d}/meta.json', 'w'), indent=1)
        print('painted', c['id'], flush=True)


if __name__ == '__main__':
    main()
