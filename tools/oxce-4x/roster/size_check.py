"""Game-size check for a finished sheet (added 13 Nov after Storm Shadow v1 read near-white at sprite size).
Measures the figure the way the battlescape shows it, against in-game reference sheets:
  bright  share of figure pixels brighter than 200 (CAST's gate: 25%)
  median  median brightness
  colours 8-bit palette entries the figure uses (speckle shows up as a high count)
and writes a comparison strip: the references and the new sheet, first row, at sheet size and half size.

    python3 size_check.py <name> <sheets dir> <out.png> --ref <units dir> [--refs duke,snake_eyes]
"""
import argparse, os
import numpy as np
from PIL import Image

CW, CH = 128, 160


def stats(base):
    R = np.array(Image.open(base + '_rgb.png').convert('RGBA')); a = R[..., 3] > 8
    rgb = R[..., :3][a].astype(float); lum = 0.299 * rgb[:, 0] + 0.587 * rgb[:, 1] + 0.114 * rgb[:, 2]
    P = Image.open(base + '.png'); used = -1
    if P.mode == 'P':
        q = np.array(P); pa = np.array(P.convert('RGBA'))[..., 3] > 8; used = len(np.unique(q[pa]))
    return dict(bright=float((lum > 200).mean()), median=float(np.median(lum)), colours=used)


def strip(bases, out):
    rows = []
    for b in bases:
        im = Image.open(b + '_rgb.png').convert('RGBA'); row = Image.new('RGBA', (CW * 8, CH), (255, 0, 255, 255))
        for i, c in enumerate(range(0, 16, 2)): row.alpha_composite(im.crop((c * CW, 0, (c + 1) * CW, CH)), (i * CW, 0))
        rows.append(row.convert('RGB'))
    big = Image.new('RGB', (CW * 8, CH * len(rows)))
    for i, r in enumerate(rows): big.paste(r, (0, i * CH))
    half = big.resize((big.width // 2, big.height // 2), Image.LANCZOS)
    c = Image.new('RGB', (big.width, big.height + half.height + 8), (40, 40, 40)); c.paste(big); c.paste(half, (0, big.height + 8)); c.save(out)


def check(name, sheets, out, ref, refs=('duke', 'snake_eyes')):
    lines = []; bases = []
    for r in refs:
        b = os.path.join(ref, f'{r}_body')
        if os.path.exists(b + '_rgb.png'):
            s = stats(b); bases.append(b)
            lines.append(f'  ref {r:16} bright {s["bright"]:.0%}  median {s["median"]:.0f}  colours {s["colours"]}')
    b = os.path.join(sheets, f'{name}_body'); s = stats(b); bases.append(b)
    flag = ' <- over 25%: reads near-white at game size' if s['bright'] > 0.25 else ''
    lines.append(f'  NEW {name:16} bright {s["bright"]:.0%}  median {s["median"]:.0f}  colours {s["colours"]}{flag}')
    strip(bases, out)
    return lines, s


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('name'); ap.add_argument('sheets'); ap.add_argument('out')
    ap.add_argument('--ref', required=True); ap.add_argument('--refs', default='duke,snake_eyes')
    a = ap.parse_args()
    print('\n'.join(check(a.name, a.sheets, a.out, a.ref, a.refs.split(','))[0]))
