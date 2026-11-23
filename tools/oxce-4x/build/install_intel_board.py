"""Install the graphics AI's Intel board kit (intel-board-and-covert-ops-build1.zip, 19 Nov).

art/intel_board/*.png  ->  mod/Resources/UI/Intel/  (board_hi.png + its 8-bit twin board.png,
the operation photos, stamps, cards, pins) and mod/Ruleset/zz_gijoe_intel_board.rul (JOE_INTEL_BOARD.SCR).
"""
import os, shutil, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from make_tablet_screens import to_8bit

SRC = os.path.join(ROOT, 'art', 'intel_board')
OUT = os.path.join(ROOT, 'mod', 'Resources', 'UI', 'Intel')
os.makedirs(OUT, exist_ok=True)
hi = Image.open(os.path.join(SRC, 'intel_board_bg.png')).convert('RGB')
hi.save(os.path.join(OUT, 'board_hi.png'))
to_8bit(hi).save(os.path.join(OUT, 'board.png'))
for f in sorted(os.listdir(SRC)):
    if f != 'intel_board_bg.png' and f.endswith('.png'):
        shutil.copy(os.path.join(SRC, f), os.path.join(OUT, f))
with open(os.path.join(ROOT, 'mod', 'Ruleset', 'zz_gijoe_intel_board.rul'), 'w') as o:
    o.write("# The Intel board's corkboard (graphics AI, 19 Nov). Written by build/install_intel_board.py.\n"
            "extraSprites:\n  - type: JOE_INTEL_BOARD.SCR\n    singleImage: true\n    width: 320\n    height: 200\n"
            "    files:\n      0: Resources/UI/Intel/board.png\n")
print('installed', len(os.listdir(OUT)), 'files')
