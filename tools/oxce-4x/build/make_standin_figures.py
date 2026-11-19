#!/usr/bin/env python3
"""Stand-in equipment-screen figures for Joes who have no painted one yet.

    python3 build/make_standin_figures.py [--write]

John 19 Nov 00:31: "In inventory soldiers pictures don't match who they are." Every Joe
without a painted figure (Resources/Inventory/<name>_inv.png) borrowed Duke's. This cuts
each one's OWN standing frame (row 1, frame 0: facing the camera) out of his battle body
sheet and stands it where install_inventory_figures.py stands a painted figure, so the
equipment screen shows the right man. Softer than a painting, because it is a 160 px
frame blown up - a painted figure from the graphics AI replaces it with
install_inventory_figures.py and nothing else changes.

Then the armour's spriteInv in gijoe_body_sheets.rul is pointed at the new figure and
its extraSprite added.
"""
import os
import re
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import install_inventory_figures as iif                    # noqa: E402
import make_weapon_sprites as mws                          # noqa: E402

MOD = os.path.normpath(os.path.join(HERE, '..', 'mod'))
RUL = os.path.join(MOD, 'Ruleset', 'gijoe_body_sheets.rul')
FW, FH, ROW, COL = 128, 160, 1, 0
# body-sheet stem -> armours that should wear it
WHO = {'beach_head': ['STR_BEACH_HEAD_UC', 'STR_DRILL_CADRE_BH_UC'], 'scarlett': ['STR_SCARLETT_UC'],
       'rock_n_roll': ['STR_ROCK_N_ROLL_UC'], 'zap': ['STR_ZAP_UC'], 'grunt': ['STR_GRUNT_UC'],
       'stalker': ['STR_STALKER_UC'], 'breaker': ['STR_BREAKER_UC'], 'flash': ['STR_FLASH_UC']}


def frame(stem):
    im = Image.open(os.path.join(MOD, 'Resources', 'Units', stem + '_body_rgb.png')).convert('RGBA')
    f = im.crop((COL * FW, ROW * FH, COL * FW + FW, ROW * FH + FH))
    return f.crop(f.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox())


def main(write):
    pal, legal, lp = mws.palette_and_legal()
    for stem in WHO:
        if os.path.exists(os.path.join(iif.INV, stem + '_inv.png')):
            print('%-12s has a figure already, left alone' % stem)
            continue
        hi = iif.place(frame(stem))
        small = hi.resize((320, 200), Image.LANCZOS)
        a = np.asarray(small).copy()
        a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
        base = mws.quantise(Image.fromarray(a, 'RGBA'), pal, legal, lp)
        print('%-12s stand-in figure made' % stem)
        if write:
            hi.save(os.path.join(iif.INV, stem + '_inv_hi.png'))
            base.save(os.path.join(iif.INV, stem + '_inv.png'))
    if not write:
        return
    txt = open(RUL).read()
    for stem in WHO:
        inv = 'GIJOE_%s_INV' % stem.upper()
        if '- type: %s.SPK' % inv not in txt:
            txt = txt.replace('\narmors:\n', '\n  - type: %s.SPK\n    singleImage: true\n    width: 320\n    height: 200\n'
                              '    files:\n      0: Resources/Inventory/%s_inv.png\narmors:\n' % (inv, stem), 1)
    open(RUL, 'w').write(txt)
    for path in (RUL, os.path.join(MOD, 'Ruleset', 'gijoe_proving_ground.rul')):
        txt = open(path).read()
        for stem, arms in WHO.items():
            inv = 'GIJOE_%s_INV' % stem.upper()
            for arm in arms:
                txt, n = re.subn(r'(- type: %s\n(?:    .*\n)*?    spriteInv: )\S+' % re.escape(arm), r'\g<1>' + inv, txt)
                if n:
                    print('  %s -> %s in %s' % (arm, inv, os.path.basename(path)))
        open(path, 'w').write(txt)


if __name__ == '__main__':
    main('--write' in sys.argv)
