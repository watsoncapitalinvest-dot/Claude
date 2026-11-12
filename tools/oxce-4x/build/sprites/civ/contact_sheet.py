"""Ink each civilian's test frames and lay them out on one contact sheet.

    python3 contact_sheet.py civ.json OUT.png [--ws /tmp/claude-0/ws/civ]

civ.json: [{"name": "Ch20", "desc": "man in suit", "hair": "r,g,b"}, ...]
Frames come from <ws>/test_<name>/stand/d{5,3}_f00_{beauty,id}.png (render_char.py).
Each frame is inked with soldier_ink.ink_frame, HAIR set to the model's hair colour.
"""
import importlib, json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
BG = (112, 124, 104)          # mid grey-green
CW, CH = 256, 320


def font(sz):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def hair_from_render(ws, name):
    """the hair colour as rendered: beauty pixels the ID pass marks as hair (id 1), a lit-ish percentile"""
    import numpy as np
    px = []
    for k in (5, 3):
        p = f"{ws}/test_{name}/stand/d{k}_f00"
        b = np.asarray(Image.open(p + '_beauty.png').convert('RGBA')).astype(np.float32)
        i = np.asarray(Image.open(p + '_id.png').convert('RGB'))
        sel = (np.round(i[..., 0] / 255 * 40) == 1) & (b[..., 3] > 200)
        px.append(b[sel][:, :3])
    px = np.concatenate(px)
    if len(px) < 30: return None
    lum = px.mean(1); pick = px[(lum >= np.percentile(lum, 50)) & (lum <= np.percentile(lum, 85))]
    return ','.join(str(int(v)) for v in np.median(pick, 0))


def main(spec, out, ws):
    civs = json.load(open(spec))
    cols = 4                                   # 4 characters a row, 2 views each
    rows = (len(civs) + cols - 1) // cols
    LH = 44
    S = Image.new('RGB', (cols * 2 * CW + (cols + 1) * 16, rows * (CH + LH) + (rows + 1) * 16), BG)
    d = ImageDraw.Draw(S); f = font(17)
    ink = None
    for i, c in enumerate(civs):
        if c.get('hair') == 'auto': c['hair'] = hair_from_render(ws, c['name']); print(c['name'], 'hair', c['hair'])
        if c.get('hair'): os.environ['HAIR'] = c['hair']
        else: os.environ.pop('HAIR', None)
        import soldier_ink
        ink = importlib.reload(soldier_ink)
        x0 = 16 + (i % cols) * (2 * CW + 16); y0 = 16 + (i // cols) * (CH + LH + 16)
        for j, k in enumerate((5, 3)):
            p = f"{ws}/test_{c['name']}/stand/d{k}_f00"
            fr = ink.ink_frame(Image.open(p + '_beauty.png').convert('RGBA'), Image.open(p + '_id.png'))
            fr.save(f"{ws}/test_{c['name']}/inked_d{k}.png")
            S.paste(fr, (x0 + j * CW, y0), fr)
        d.text((x0 + 4, y0 + CH + 6), f"{c['name']} - {c['desc']}", fill=(255, 253, 240), font=f)
    S.save(out)
    print('wrote', out, S.size)


if __name__ == '__main__':
    a = sys.argv
    main(a[1], a[2], a[a.index('--ws') + 1] if '--ws' in a else '/tmp/claude-0/ws/civ')
