#!/usr/bin/env python3
"""John's turn screen art (13 Nov 2026) -> GIJOE_TURN_SCREEN.SCR, the "TURN > n / SIDE >" screen.

    python3 build/install_turn_screen.py [source png]

Writes Resources/Backgrounds/turn_screen_hi.png (1920x1200, what HiUI draws) and
turn_screen.png (320x200, battlescape palette, the 8-bit fallback), and
Ruleset/gijoe_turn_screen.rul. NextTurnState puts the text in the picture's open panel
(x 67-236, y 75-187 of 320x200) whenever GIJOE_TURN_SCREEN.SCR exists.
"""
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
MOD = os.path.join(ROOT, 'mod')
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'art_briefs', 'returned', 'turn_screen', 'turn_screen_src.png')
sys.path.insert(0, HERE)
import make_inventory_bg as mib  # noqa: E402
import make_weapon_sprites as mws  # noqa: E402

art = Image.open(SRC).convert('RGBA')
hi = art.resize((1920, 1200), Image.LANCZOS)
out = os.path.join(MOD, 'Resources', 'Backgrounds')
hi.convert('RGB').save(os.path.join(out, 'turn_screen_hi.png'))
pal, legal, lp = mib.palette_and_legal()
mws.quantise(hi.resize((320, 200), Image.LANCZOS), pal, legal, lp).save(os.path.join(out, 'turn_screen.png'))
open(os.path.join(MOD, 'Ruleset', 'gijoe_turn_screen.rul'), 'w').write(
    '# The turn screen (John 13 Nov 2026): build/install_turn_screen.py.\n'
    'extraSprites:\n'
    '  - type: GIJOE_TURN_SCREEN.SCR\n'
    '    singleImage: true\n'
    '    width: 320\n'
    '    height: 200\n'
    '    files:\n'
    '      0: Resources/Backgrounds/turn_screen.png\n')
print('turn screen written', art.size, '-> 1920x1200 + 320x200')
