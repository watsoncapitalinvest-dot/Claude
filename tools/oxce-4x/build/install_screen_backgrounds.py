#!/usr/bin/env python3
"""Screen backgrounds (SCREEN_BACKGROUNDS_BRIEF.txt) -> the game.

    python3 build/install_screen_backgrounds.py

Reads art_briefs/returned/backgrounds/bg_<room>.png (any size near 16:10; the
chat delivers them at 1586x992), fits each to 1920x1200 - scaled to the width,
and a picture wider than 16:10 has its top and bottom rows extended rather than
its edges cropped, because the room lives in the edges - and writes
mod/Resources/Backgrounds/Pit/<room>.png (320x200, 8-bit) + <room>_hi.png.
Then writes mod/Ruleset/gijoe_screen_backgrounds.rul: one extraSprite per room
and an interfaces entry per screen pointing its backgroundImage at it.

Checks the brief's one rule before accepting a picture: the middle (200 px in
from the sides, 160 from top and bottom, at 1920x1200) must be dim.
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
SRC = os.path.join(ROOT, 'art_briefs', 'returned', 'backgrounds')
OUT = os.path.join(ROOT, 'mod', 'Resources', 'Backgrounds', 'Pit')
RUL = os.path.join(ROOT, 'mod', 'Ruleset', 'gijoe_screen_backgrounds.rul')
W, H = 1920, 1200
# The list screens set text from 8 base px in, right over the edge art, so the
# whole picture is dimmed to keep that text readable (checked in game 12 Nov).
DIM = 0.55

# room -> the screens it sits behind (interface categories the engine sets)
SCREENS = {
    'barracks': ['soldierList', 'soldierInfo', 'soldierArmor', 'soldierMemorial', 'soldierDiary',
                 'soldierDiaryMission', 'soldierDiaryPerformance', 'soldierRank', 'soldierTransformation',
                 'soldierTransform', 'transformationList', 'craftSoldiers', 'craftPilots', 'craftPilotsSelect',
                 'promotions', 'commendations', 'commendationsLate', 'psiTraining', 'allocatePsi',
                 'martialTraining', 'allocateMartial', 'sackSoldier', 'trainingFinished'],
    'lab': ['researchMenu', 'selectNewResearch', 'globalResearchMenu', 'globalResearchDiary', 'allocateResearch',
            'techTreeViewer', 'techTreeSelect', 'dependencyTree', 'manageContainment', 'globalContainmentMenu'],
    'workshop': ['manufactureMenu', 'selectNewManufacture', 'manufactureInfo', 'allocateManufacture',
                 'globalManufactureMenu'],
    'hangar': ['craftSelect', 'craftInfo', 'craftWeapons', 'craftEquipment', 'craftEquipmentLoad',
               'craftEquipmentSave', 'craftArmor'],
    'supply_depot': ['buyMenu', 'sellMenu', 'storesInfo', 'itemLocations', 'itemsArriving', 'transferBaseSelect',
                     'transferMenu', 'transferConfirm', 'transferInfo', 'costsInfo', 'monthlyReport'],
    'radar_room': ['intercept', 'ufoTracker'],
    'base_defence': ['baseDestroyed'],
    'situation_room': ['targetInfo', 'debriefing', 'geoscapeEvent', 'multipleTargets', 'confirmDestination'],
}


def fit(im):
    im = im.convert('RGB')
    h = round(im.height * W / im.width)
    im = im.resize((W, h), Image.LANCZOS)
    if h >= H:
        top = (h - H) // 2
        return im.crop((0, top, W, top + H))
    a = np.asarray(im)
    pt = (H - h) // 2; pb = H - h - pt
    return Image.fromarray(np.pad(a, ((pt, pb), (0, 0), (0, 0)), mode='edge'))


def to_8bit(hi):
    small = hi.resize((320, 200), Image.LANCZOS)
    q = small.quantize(colors=254, method=Image.MEDIANCUT, dither=Image.NONE)
    pal = q.getpalette()[:254 * 3]
    a = np.asarray(q).astype(np.uint8) + 2
    out = Image.fromarray(a, 'P')
    out.putpalette([0, 0, 0, 233, 230, 220] + pal)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    have = []
    for room in SCREENS:
        p = os.path.join(SRC, f'bg_{room}.png')
        if not os.path.exists(p):
            print('not delivered yet:', room); continue
        hi = fit(Image.open(p))
        hi = Image.fromarray((np.asarray(hi).astype(np.float32) * DIM).astype(np.uint8))
        mid = np.asarray(hi.convert('L'))[160:H - 160, 200:W - 200]
        if mid.mean() > 64:
            sys.exit(f'REFUSED bg_{room}.png: the middle is not dim (mean {mid.mean():.0f})')
        if np.percentile(mid, 99) > 140:
            print(f'  WARNING bg_{room}.png: bright detail inside the middle (99th pct {np.percentile(mid, 99):.0f})')
        hi.save(os.path.join(OUT, f'{room}_hi.png'))
        to_8bit(hi).save(os.path.join(OUT, f'{room}.png'))
        have.append(room)
        print('installed', room, 'middle mean %.0f' % mid.mean())
    lines = ['# Screen backgrounds: rooms of The Pit behind the list screens (SCREEN_BACKGROUNDS_BRIEF.txt).',
             '# Written by build/install_screen_backgrounds.py - edit the script, not this file.',
             'extraSprites:']
    for r in have:
        lines += [f'  - type: JOE_BG_{r.upper()}.SCR', '    singleImage: true', '    width: 320', '    height: 200',
                  '    files:', f'      0: Resources/Backgrounds/Pit/{r}.png']
    lines.append('interfaces:')
    for r in have:
        for s in SCREENS[r]:
            lines += [f'  - type: {s}', f'    backgroundImage: JOE_BG_{r.upper()}.SCR']
    open(RUL, 'w').write('\n'.join(lines) + '\n')
    print('wrote', RUL, len(have), 'rooms')


if __name__ == '__main__':
    main()
