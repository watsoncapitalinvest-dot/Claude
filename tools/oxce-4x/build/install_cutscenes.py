#!/usr/bin/env python3
"""Act 1 cutscenes (STORY's captions in gijoe_story_act1_text.rul, ART's pictures) -> the game.

    python3 build/install_cutscenes.py

Reads art_briefs/returned/cutscenes_act1/cut_<name>.png (1920x1200, the bottom band left dark for
the caption), writes mod/Resources/Cutscenes/Act1/<name>.png (320x200, 8-bit) + <name>_hi.png,
and mod/Ruleset/gijoe_cutscenes_act1.rul with one slideshow per outcome. STORY triggers them
(a research topic's or a mission's `cutscene:`); the ids are below.
"""
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from install_screen_backgrounds import fit, to_8bit  # same 1920x1200 fit and 8-bit stand-in

ROOT = os.path.normpath(os.path.join(HERE, '..'))
SRC = os.path.join(ROOT, 'art_briefs', 'returned', 'cutscenes_act1')
OUT = os.path.join(ROOT, 'mod', 'Resources', 'Cutscenes', 'Act1')
RUL = os.path.join(ROOT, 'mod', 'Ruleset', 'gijoe_cutscenes_act1.rul')

# cutscene id -> [(picture, caption)]. Factory B opens on the same picture as A: same caption.
CUTS = {
    'act1FactoryReopened': [('factory_a1', 'STR_CUT_FACTORY_A1'), ('factory_a2', 'STR_CUT_FACTORY_A2'),
                            ('factory_a3', 'STR_CUT_FACTORY_A3'), ('factory_a4', 'STR_CUT_FACTORY_A4')],
    'act1FactoryWrecked': [('factory_a1', 'STR_CUT_FACTORY_B1'), ('factory_b2', 'STR_CUT_FACTORY_B2')],
    'act1DromePlans': [('drome_a1', 'STR_CUT_DROME_A1'), ('drome_2', 'STR_CUT_DROME_2'),
                       ('drome_3', 'STR_CUT_DROME_3'), ('drome_4', 'STR_CUT_DROME_4')],
    'act1DromeNoPlans': [('drome_b1', 'STR_CUT_DROME_B1'), ('drome_2', 'STR_CUT_DROME_2'),
                         ('drome_3', 'STR_CUT_DROME_3'), ('drome_4', 'STR_CUT_DROME_4')],
    'act1CloseDromeTaken': [('close_a1', 'STR_CUT_CLOSE_A1'), ('close_2', 'STR_CUT_CLOSE_2'),
                            ('close_3', 'STR_CUT_CLOSE_3'), ('close_4', 'STR_CUT_CLOSE_4')],
    'act1CloseDromeStands': [('close_b1', 'STR_CUT_CLOSE_B1'), ('close_2', 'STR_CUT_CLOSE_2'),
                             ('close_3', 'STR_CUT_CLOSE_3'), ('close_4', 'STR_CUT_CLOSE_4')],
}


def main():
    os.makedirs(OUT, exist_ok=True)
    need = sorted({p for s in CUTS.values() for p, _ in s})
    for p in need:
        src = os.path.join(SRC, f'cut_{p}.png')
        if not os.path.exists(src):
            sys.exit(f'missing {src}')
        hi = fit(Image.open(src))
        hi.save(os.path.join(OUT, f'{p}_hi.png'))
        to_8bit(hi).save(os.path.join(OUT, f'{p}.png'))
    lines = ['# Act 1 cutscenes. Written by build/install_cutscenes.py - edit the script, not this file.',
             '# Captions are STORY\'s (gijoe_story_act1_text.rul); STORY triggers these ids.', 'cutscenes:']
    for cid, slides in CUTS.items():
        lines += [f'  - type: {cid}', '    slideshow:', '      transitionSeconds: 7', '      slides:']
        for p, cap in slides:
            lines += [f'        - imagePath: Resources/Cutscenes/Act1/{p}.png', f'          caption: {cap}',
                      '          captionPos: [16, 152]', '          captionSize: [288, 44]', '          captionColor: 1',
                      '          captionAlign: 1', '          captionVerticalAlign: 1']
    open(RUL, 'w').write('\n'.join(lines) + '\n')
    print('installed', len(need), 'pictures,', len(CUTS), 'cutscenes')


if __name__ == '__main__':
    main()
