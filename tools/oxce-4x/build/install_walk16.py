#!/usr/bin/env python3
"""Walk16 sheets -> the game (BRIEF_FOR_BUILD_Walk16; John 16 Nov 21:29 "do the animations now").

    python3 build/install_walk16.py [--sheets DIR] [name ...]

build/sprites/render_walk16.sh writes <name>_body.png, _body_rgb.png, _body_anchors.txt (896 frames, 2048 x 8960)
into DIR (default /tmp/claude-0/ws/cast/sheets16). Each replaces the file of the same name the game already loads
(mod/Resources/Units/, or civ_<name> for the civilians), its anchors replace anchors/<SHEET>.txt, and the
extraSprites entry that loads it gets the new height. The engine tells the layout by the frame count, so a sheet not
yet re-rendered keeps drawing exactly as before.
"""
import glob, os, re, shutil, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, '..', 'mod'))
args = sys.argv[1:]
SHEETS = '/tmp/claude-0/ws/cast/sheets16'
if '--sheets' in args:
    i = args.index('--sheets'); SHEETS = args[i + 1]; del args[i:i + 2]
names = args or sorted({os.path.basename(p)[:-len('_body.png')] for p in glob.glob(os.path.join(SHEETS, '*_body.png'))})
ruls = glob.glob(os.path.join(MOD, 'Ruleset', '*.rul'))
for n in names:
    src = os.path.join(SHEETS, n + '_body.png')
    if not os.path.exists(src):
        print('no sheet for', n); continue
    w, h = Image.open(src).size
    stem = n if os.path.exists(os.path.join(MOD, 'Resources', 'Units', n + '_body.png')) else 'civ_' + n.lower()
    rel = 'Resources/Units/%s_body.png' % stem
    if not os.path.exists(os.path.join(MOD, rel)):
        print('%s: the game has no %s - not installed' % (n, rel)); continue
    for suf in ('_body.png', '_body_rgb.png'):
        shutil.copy(os.path.join(SHEETS, n + suf), os.path.join(MOD, 'Resources', 'Units', stem + suf))
    # the extraSprites block that loads it: its height, and the sheet name for the anchors
    sheet = None
    for r in ruls:
        t = open(r).read()
        if rel not in t: continue
        blocks = re.split(r'(?=\n\s*- type: )', t)
        for bi, b in enumerate(blocks):
            if rel in b and 'height:' in b:
                blocks[bi] = re.sub(r'height: \d+', 'height: %d' % h, b, count=1)
                sheet = re.search(r'- type: (\S+)', b).group(1)
        open(r, 'w').write(''.join(blocks))
    if sheet:
        shutil.copy(os.path.join(SHEETS, n + '_body_anchors.txt'), os.path.join(MOD, 'Resources', 'Units', 'anchors', sheet + '.txt'))
    print('%s -> %s (%dx%d), anchors %s' % (n, rel, w, h, sheet))
