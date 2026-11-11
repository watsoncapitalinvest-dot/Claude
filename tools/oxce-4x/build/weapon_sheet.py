#!/usr/bin/env python3
"""Every firearm's inventory art with its in-game name under it.

    python3 -I build/weapon_sheet.py <X-COM data dir> <mod dir> <out.png>

WHY A PICTURE

WEAPONS_CATALOG.md has five findings and three of them were invisible in the
rulesets. The sprites had to be put side by side: that is how the Uzi and the
"Pulse Pistol" turned out to be the same file, and how nine weapons still
wearing X-COM's purple alien art turned up in a G.I. Joe game.

Repainted weapons are drawn from the mod's own PNG. The rest are decoded out of
the game's BIGOB_NN.PCK, which is ONE RLE FRAME PER FILE with no TAB beside it -
not the single BIGOBS.PCK+TAB pair the terrain sets use.
"""
import os, sys, glob, json
import numpy as np
import yaml
from PIL import Image, ImageDraw

if len(sys.argv) < 4:
    sys.exit(__doc__)
DATA, MOD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 32, 48


def one_frame(path):
    """BIGOB_NN.PCK: first byte is blank rows to skip, 254 = run of transparent, 255 = end."""
    d = open(path, 'rb').read()
    px = [0] * (W * H)
    p = 0
    pos = d[p] * W
    p += 1
    while p < len(d) and d[p] != 255:
        v = d[p]; p += 1
        if v == 254:
            pos += d[p]; p += 1
        else:
            if pos < W * H:
                px[pos] = v
            pos += 1
    return np.array(px).reshape(H, W)


def rules(d):
    out = {}
    for f in sorted(glob.glob(os.path.join(d, '*.rul'))):
        try:
            y = yaml.safe_load(open(f, encoding='utf-8')) or {}
        except Exception:
            continue
        out[f] = y
    return out


items, repaint = {}, {}
for f, y in rules(os.path.join(DATA, '..', 'standard', 'xcom1')).items():
    for it in (y.get('items') or []):
        if isinstance(it, dict) and it.get('type'):
            items[it['type']] = dict(it)
for f, y in rules(os.path.join(MOD, 'Ruleset')).items():
    for it in (y.get('items') or []):
        if isinstance(it, dict) and it.get('type'):
            items.setdefault(it['type'], {}).update(it)
    for es in (y.get('extraSprites') or []):
        if es.get('type') == 'BIGOBS.PCK':
            for k, v in (es.get('files') or {}).items():
                repaint[int(k)] = v

lang = yaml.safe_load(open(os.path.join(MOD, 'Language', 'en-US.yml'), encoding='utf-8'))
L = list(lang.values())[0]

pal = open(os.path.join(DATA, 'GEODATA', 'PALETTES.DAT'), 'rb').read()[4 * 774:4 * 774 + 768]
PAL = np.array([(pal[i * 3] * 4, pal[i * 3 + 1] * 4, pal[i * 3 + 2] * 4) for i in range(256)], dtype=np.uint8)

guns = sorted((t, v) for t, v in items.items()
              if v.get('battleType') == 1 and v.get('bigSprite') is not None)
SC, COLS = 4, 7
rows = (len(guns) + COLS - 1) // COLS
sheet = Image.new('RGB', (COLS * (W * SC + 16), rows * (H * SC + 36)), (22, 24, 28))
dr = ImageDraw.Draw(sheet)
for i, (t, v) in enumerate(guns):
    x = (i % COLS) * (W * SC + 16) + 8
    y = (i // COLS) * (H * SC + 36) + 4
    art = repaint.get(v['bigSprite'])
    im = None
    if art and os.path.exists(os.path.join(MOD, art)):
        s = Image.open(os.path.join(MOD, art)).convert('RGBA')
        bg = Image.new('RGBA', s.size, (22, 24, 28, 255)); bg.alpha_composite(s)
        im = bg.convert('RGB')
    else:
        fp = os.path.join(DATA, 'UFOGRAPH', 'BIGOB_%02d.PCK' % v['bigSprite'])
        if os.path.exists(fp):
            im = Image.fromarray(PAL[one_frame(fp)])
    if im:
        sheet.paste(im.resize((W * SC, H * SC), Image.NEAREST), (x, y))
    dr.text((x, y + H * SC + 4), (L.get(t) or '(X-COM name)')[:17], fill=(235, 232, 220))
    dr.text((x, y + H * SC + 16), 'repainted' if art else 'VANILLA ART',
            fill=(120, 200, 140) if art else (235, 120, 110))
sheet.save(OUT)
print('%d weapons, %d still on vanilla art -> %s'
      % (len(guns), sum(1 for t, v in guns if v['bigSprite'] not in repaint), OUT))
