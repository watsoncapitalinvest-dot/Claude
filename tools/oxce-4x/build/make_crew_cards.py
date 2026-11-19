#!/usr/bin/env python3
"""Crew cards for the craft screen: one small standing figure per armour.

    python3 build/make_crew_cards.py

John 19 Nov 10:23: "in the vehicle equip screen why can't the little men look like the actual men in the craft".
Each armour's equipment-screen figure (Resources/Inventory/<x>_inv_hi.png, the sharp twin of its spriteInv) is
cropped to the man and saved as Resources/UI/Crew/<ARMOUR>.png, 72 x 144. The craft screen draws one per man aboard
(CraftInfoState, HiUI); an armour with no card keeps the old icon.
"""
import glob
import os
import re
import yaml
from PIL import Image

MOD = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mod'))
OUT = os.path.join(MOD, 'Resources', 'UI', 'Crew')
W, H = 72, 144


class L(yaml.SafeLoader):
    pass


L.add_constructor(None, lambda l, n: None)


def main():
    sprite_file, armour_inv = {}, {}
    for f in sorted(glob.glob(os.path.join(MOD, 'Ruleset', '*.rul'))):
        try:
            d = yaml.load(open(f), Loader=L) or {}
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for e in d.get('extraSprites') or []:
            if isinstance(e, dict) and str(e.get('type', '')).endswith('_INV.SPK') and isinstance(e.get('files'), dict):
                sprite_file[e['type'][:-4]] = list(e['files'].values())[0]
        for a in d.get('armors') or []:
            if isinstance(a, dict) and a.get('type') and a.get('spriteInv'):
                armour_inv[a['type']] = a['spriteInv']
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for arm, inv in sorted(armour_inv.items()):
        f = sprite_file.get(inv)
        if not f:
            continue
        hi = os.path.join(MOD, f.replace('.png', '_hi.png'))
        if not os.path.exists(hi):
            continue
        im = Image.open(hi).convert('RGBA')
        box = im.getchannel('A').point(lambda v: 255 if v > 40 else 0).getbbox()
        if not box:
            continue
        fig = im.crop(box)
        k = min(W / fig.width, H / fig.height)
        fig = fig.resize((max(1, round(fig.width * k)), max(1, round(fig.height * k))), Image.LANCZOS)
        card = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        card.paste(fig, ((W - fig.width) // 2, H - fig.height), fig)
        card.save(os.path.join(OUT, re.sub(r'[^A-Za-z0-9_]', '_', arm) + '.png'))
        n += 1
    print(n, 'crew cards')


if __name__ == '__main__':
    main()
