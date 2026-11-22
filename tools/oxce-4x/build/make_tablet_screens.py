#!/usr/bin/env python3
"""Each menu screen's background IS its approved round-3 mockup (John 19 Nov: "use the art i sent
you, cut out the buttons and windows that need to be replaced").

    python3 build/make_tablet_screens.py [State ...]

Source: art/tablet_round3/<State>.png (1920x1200, the graphics AI's tablet-mockups-round-3-build1).
Everything the game draws itself - words, numbers, buttons, list rows, scroll bars - is cut out of
the picture and replaced by what was under it, so the engine's own widgets land on clean panels.
The engine side (each State's constructor, `if (HiUI::tablet())`) puts its widgets on the same
spots: coordinates there are these rectangles divided by 6.

Cut operations (rectangles in 1920x1200 px):
  ('row', x0,y0,x1,y1, sx)       each pixel row of the rect takes the colour at column sx of that row
                                 (text on a flat bar, a header strip, a button on a panel)
  ('tile', x0,y0,x1,y1, ty0,ty1) the rect is filled by repeating rows ty0..ty1 of the picture
                                 (a list body: two empty striped rows repeated over the filled ones)
  ('copy', x0,y0,x1,y1, dx,dy)   the rect takes the pixels dx,dy away (patch from a clean spot)

Writes mod/Resources/UI/Tablet/screens/<State>.png (320x200, 8-bit) + <State>_hi.png and
mod/Ruleset/zz_gijoe_tablet_screens.rul (one sprite per screen, its interface categories on it).
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
SRC = os.path.join(ROOT, 'art', 'tablet_round3')
OUT = os.path.join(ROOT, 'mod', 'Resources', 'UI', 'Tablet', 'screens')
RUL = os.path.join(ROOT, 'mod', 'Ruleset', 'zz_gijoe_tablet_screens.rul')
sys.path.insert(0, HERE)
from install_screen_backgrounds import to_8bit   # noqa: E402

def list_screen(strip, body_bottom, empty_row, strip_cuts=None, extra=(), title=(118, 118, 1300, 172, 1360),
                buttons=(1255, 984, 1805, 1042, 1250), body=(120, 1346), scroll=(1346, 1380)):
    """The common round-3 list screen: title, khaki header strip, striped list body with a thin
    scroll bar, buttons bottom right. strip = (y0, y1); empty_row = y of a row with nothing in it
    (two rows from there are repeated over the body)."""
    y0, y1 = strip
    ops = [('row',) + tuple(title)]
    for c in (strip_cuts or [(body[0] + 2, scroll[1] - 6)]):
        ops.append(('row', c[0], y0 + 2, c[1], y1 - 1, c[0] - 2))
    if empty_row is None:
        ops.append(('row', body[0], y1, body[1], body_bottom, body[1] - 30))
    else:
        ops.append(('tile', body[0], y1, body[1], body_bottom, empty_row, empty_row + 96))
    ops.append(('row', scroll[0], y1, scroll[1], body_bottom, scroll[0] - 6))
    ops.append(('row',) + tuple(buttons))
    ops.extend(extra)
    return ops


# State -> (interface categories that take this background, cut operations)
SPECS = {
    'StoresState': (['storesInfo'], list_screen((230, 270), 942, 510)),
    'SoldiersState': (['soldierList'], list_screen((231, 270), 942, 510, extra=[
        ('row', 1418, 108, 1797, 156, 1412),         # SORT BY pick-list
    ])),
    'PurchaseState': (['buyMenu'], list_screen((246, 285), 953, 573,
        strip_cuts=[(495, 660), (1105, 1230)],       # COST PER UNIT, QUANTITY (ITEM, IN STORES stay painted)
        extra=[('row', 120, 188, 1000, 234, 1030),   # funds / cost of purchases
               ('row', 1395, 186, 1797, 236, 1390)])),  # category pick-list
    'SellState': ([], list_screen((246, 285), 956, 429,
        strip_cuts=[(480, 600), (815, 945), (1092, 1180)],    # QUANTITY, SELL/SACK, VALUE (ITEM stays painted)
        extra=[('row', 120, 188, 1000, 234, 1030), ('row', 1395, 186, 1797, 236, 1390)])),
    'FundingState': ([], list_screen((181, 220), 995, None, buttons=(1255, 996, 1805, 1056, 1250),
        extra=[('row', 120, 995, 1262, 1050, 1256)])),   # the TOTAL row
    'CobraIntelState': ([], list_screen((195, 234), 903, 282, buttons=(1530, 996, 1805, 1056, 1520),
        extra=[('row', 120, 915, 1250, 1002, 1262)])),       # the two lines of notes
    'CraftSoldiersState': ([], list_screen((247, 286), 956, 430, extra=[('row', 120, 188, 700, 232, 710)])),
    'CraftEquipmentState': ([], list_screen((246, 285), 956, 429, strip_cuts=[(138, 220), (598, 700)],
        extra=[('row', 120, 188, 760, 232, 770)])),
    'CraftsState': ([], list_screen((243, 282), 953, 378, extra=[('row', 118, 188, 400, 228, 420)])),
    'InterceptState': ([], list_screen((231, 270), 940, 414, body=(120, 1767), scroll=(1767, 1798),
        strip_cuts=[(122, 1790)])),
    'NewManufactureListState': ([], list_screen((245, 284), 956, 428, extra=[('row', 120, 186, 1170, 232, 1180)])),
    'ManufactureState': ([], list_screen((279, 318), 986, 366, body=(120, 1767), scroll=(1767, 1798),
        strip_cuts=[(122, 1790)], buttons=(1255, 996, 1805, 1056, 1250),
        extra=[('row', 120, 182, 760, 262, 770)])),
    'AllocateTrainingState': ([], list_screen((246, 285), 956, 429, extra=[
        ('row', 120, 188, 520, 232, 530), ('row', 1418, 108, 1797, 156, 1412)])),
    'TransferBaseState': ([], [
        ('row', 150, 120, 1320, 200, 1340),          # title
        ('row', 1420, 245, 1760, 305, 1410),         # the funds figure (CURRENT FUNDS stays painted)
        ('copy', 620, 360, 1380, 452, 0, 100),       # first base plate -> a plain one like the others
    ]),
    'PauseState': ([], [
        ('row', 175, 125, 600, 225, 1000),                    # OPTIONS
    ] + [('row', 1262, y0, 1705, y1, 1252) for (y0, y1) in [(280, 355), (406, 482), (533, 610), (660, 736), (800, 885)]]),
    'MonthlyReportState': ([], [
        ('row', 118, 118, 1300, 172, 1360),                   # title
        ('row', 160, 250, 1150, 490, 1170),                   # the figures
        ('row', 150, 545, 1120, 925, 1130),                   # the Joint Chiefs' words
        ('row', 1530, 985, 1805, 1045, 1520),                 # OK
    ]),
    'MainMenuState': ([], [('row', 1368, y0, 1752, y1, 1362) for (y0, y1) in
        [(397, 458), (492, 548), (590, 646), (687, 743), (783, 839), (886, 950)]]),
    'BaseInfoState': ([], [
        ('row', 118, 118, 1300, 172, 1360),                   # title
        ('row', 118, 185, 700, 225, 710),                     # base name
        ('row', 125, 272, 1250, 420, 1248),                   # personnel rows
        ('row', 125, 460, 1250, 694, 1248),                   # space rows
        ('row', 125, 738, 1250, 882, 1248),                   # defence and radar rows
        ('row', 705, 985, 1805, 1045, 700),                   # the four keys
    ]),
    'UfopaediaStartState': ([], [('row', 190, 135, 700, 218, 760)] +
        [('row', 570, round((c - 14) * 4 / 3), 1365, round((c + 14) * 4 / 3), 560)
         for c in (211, 258, 306, 354, 402, 449, 495, 541, 587, 633, 679)] +
        [('row', 768, 925, 1166, 1000, 762)]),
    'ResearchInfoState': ([], [
        ('row', 228, 138, 980, 222, 1000),                    # topic name
        ('row', 1556, 318, 1650, 382, 1548),                  # scientists available
        ('row', 1556, 430, 1650, 498, 1548),                  # laboratory space
        ('row', 1480, 556, 1580, 624, 1462),                  # scientists allocated
        ('row', 790, 845, 1075, 915, 765),                    # CANCEL
        ('row', 1262, 845, 1640, 915, 1240),                  # START PROJECT
    ]),
    'ResearchCompleteState': ([], []),
    'ManufactureInfoState': ([], []),
    'CraftInfoState': ([], []),
    'SoldierInfoState': ([], []),
    'GraphsState': ([], []),
}


def cut(a, ops):
    a = a.copy()
    for op in ops:
        k = op[0]
        if k == 'row':
            x0, y0, x1, y1, sx = op[1:]
            a[y0:y1, x0:x1] = a[y0:y1, sx:sx + 1]
        elif k == 'tile':
            x0, y0, x1, y1, t0, t1 = op[1:]
            pat = a[t0:t1, x0:x1].copy()
            for y in range(y0, y1):
                a[y, x0:x1] = pat[(y - y0) % (t1 - t0)]
        elif k == 'copy':
            x0, y0, x1, y1, dx, dy = op[1:]
            a[y0:y1, x0:x1] = a[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
    return a


def main(only):
    os.makedirs(OUT, exist_ok=True)
    for st, (cats, ops) in SPECS.items():
        if only and st not in only:
            continue
        clean = os.path.join(ROOT, 'art', 'tablet_clean', st + '_clean.png')
        if os.path.exists(clean) and not ops:
            hi = Image.open(clean).convert('RGB')      # the graphics AI cut it already (its _boxes.txt beside it)
        else:
            a = np.asarray(Image.open(os.path.join(SRC, st + '.png')).convert('RGB'))
            hi = Image.fromarray(cut(a, ops))
        hi.save(os.path.join(OUT, st + '_hi.png'))
        to_8bit(hi).save(os.path.join(OUT, st + '.png'))
        print(st, 'done')
    with open(RUL, 'w') as f:
        f.write('# Each menu screen on its round-3 tablet picture (John 19 Nov). Written by build/make_tablet_screens.py.\n')
        f.write('# Loads after zz_gijoe_tablet_backgrounds.rul, so a screen listed here wins over the plain tablet.\n')
        f.write('extraSprites:\n')
        for st in SPECS:
            f.write(f'  - type: JOE_TAB_{st.upper()}.SCR\n    singleImage: true\n    width: 320\n    height: 200\n')
            f.write(f'    files:\n      0: Resources/UI/Tablet/screens/{st}.png\n')
        f.write('interfaces:\n')
        for st, (cats, _) in SPECS.items():
            for c in cats:
                f.write(f'  - type: {c}\n    backgroundImage: JOE_TAB_{st.upper()}.SCR\n')


if __name__ == '__main__':
    main(sys.argv[1:])
