#!/usr/bin/env python3
"""The A.P.C.'s pictures (art_briefs/returned/apc_cartoon, ART 12 Nov) -> the game.

    python3 build/install_apc_art.py

Top view -> BASEBITS frame 200 (craft sprite 167 + 33): the truck parked in the Motor Pool on the
base plan and on its equipment screen, 32x40 + the 192x240 twin. Sprite 167 is clear of the
vanilla craft frames (33-37) and of the facility frames (100+). The craft's dogfight frames
(INTICON 167 and 178) are never drawn: interceptions auto-resolve (SHORTCUTS #1).
"""
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from install_craft_art import hangar, RES  # same fit and basescape palette as the Tomahawk

SRC = os.path.join(HERE, '..', 'art_briefs', 'returned', 'apc_cartoon')
FRAME = 200


def main():
    top = Image.open(os.path.join(SRC, 'apc_top.png')).convert('RGBA')
    top = top.crop(top.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox())
    top = top.rotate(-90, expand=True)          # delivered nose-left; the hangar wants nose-up
    small, hi = hangar(top)
    stem = os.path.join(RES, 'Base', 'craft_%d' % FRAME)
    small.save(stem + '.png')
    hi.save(stem + '_hi.png')
    print('hangar -> craft_%d' % FRAME)


if __name__ == '__main__':
    main()
