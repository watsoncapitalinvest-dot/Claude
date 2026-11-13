#!/usr/bin/env python3
"""Rendered whole-body soldier sheets -> the game.

    python3 build/install_body_sheets.py [--sheets DIR]

For every soldier below whose sheet exists in DIR (build/sprites/render_cast.sh writes
<name>_body.png, _body_rgb.png, _body_anchors.txt), copies it into mod/Resources/Units/,
puts its hand anchors in anchors/<SHEET>.txt, and wires it:
  - a soldier who already has an armour (Snake Eyes, Roadblock) has that armour switched
    to the new sheet IN PLACE in the ruleset that defines it (gijoe_units.rul), because the
    mod's rulesets do not load in name order and an override in another file can lose;
  - a new soldier (Beach Head, Scarlett, the greenshirts) gets an armour and a soldier type
    in mod/Ruleset/gijoe_body_sheets.rul, which this script writes.
All sheets' extraSprites go in gijoe_body_sheets.rul. Soldiers with no sheet yet are left
out, so the ruleset never names a missing file. Duke keeps gijoe_duke_body.rul.
"""
import os
import re
import shutil
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, '..', 'mod'))
SHEETS = sys.argv[sys.argv.index('--sheets') + 1] if '--sheets' in sys.argv else '/tmp/claude-0/ws/cast/sheets'
UNITS = os.path.join(MOD, 'Ruleset', 'gijoe_units.rul')

# name: (existing armour to switch, or None) ; new ones: (armour, soldier type, display name, names list)
EXISTING = {'snake_eyes': 'STR_SNAKE_EYES_UC', 'roadblock': 'STR_ROADBLOCK_UC'}
NEW = {
    'beach_head': ('STR_BEACH_HEAD_UC', 'STR_BEACH_HEAD', 'Beach Head', ['Beach Head']),
    'scarlett': ('STR_SCARLETT_UC', 'STR_SCARLETT', 'Scarlett', ['Scarlett']),
    'ace': ('STR_ACE_UC', 'STR_ACE', 'Ace', ['Ace']),
    'greenshirt_rifleman': ('STR_REGULAR_JOE_UC', 'STR_REGULAR_JOE', 'Joe Rifleman', None),
    'greenshirt_medic': ('STR_JOE_MEDIC_UC', 'STR_JOE_MEDIC', 'Joe Medic', None),
    'greenshirt_pilot': ('STR_JOE_PILOT_UC', 'STR_JOE_PILOT', 'Joe Pilot', None),
}
FEMALE = {'scarlett'}
STATS = '''    costBuy: 40000
    costSalary: 20000
    minStats: {tu: 50, stamina: 40, health: 25, bravery: 10, reactions: 30, firing: 40, throwing: 50, strength: 20, psiStrength: 0, psiSkill: 0, melee: 20}
    maxStats: {tu: 60, stamina: 70, health: 40, bravery: 60, reactions: 60, firing: 70, throwing: 80, strength: 40, psiStrength: 100, psiSkill: 16, melee: 40}
    statCaps: {tu: 80, stamina: 100, health: 60, bravery: 100, reactions: 100, firing: 120, throwing: 120, strength: 70, psiStrength: 100, psiSkill: 100, melee: 120}
'''


def sheet_name(n):
    return f'GIJOE_{n.upper()}_BODY_HD.PCK'


def install(n):
    src = os.path.join(SHEETS, f'{n}_body.png')
    if not os.path.exists(src):
        return None
    u = os.path.join(MOD, 'Resources', 'Units')
    shutil.copy(src, os.path.join(u, f'{n}_body.png'))
    shutil.copy(os.path.join(SHEETS, f'{n}_body_rgb.png'), os.path.join(u, f'{n}_body_rgb.png'))
    shutil.copy(os.path.join(SHEETS, f'{n}_body_anchors.txt'), os.path.join(u, 'anchors', sheet_name(n) + '.txt'))
    return Image.open(src).size


def switch_existing(armor, sheet):
    txt = open(UNITS).read()
    m = re.search(rf'(  - type: {armor}\n)((?:    .*\n)+)', txt)
    if not m:
        sys.exit(f'{armor} not found in gijoe_units.rul')
    body = m.group(2)
    body = re.sub(r'    spriteSheet: .*\n', f'    spriteSheet: {sheet}   # whole-body frames, see gijoe_body_sheets.rul\n', body)
    for k, v in (('drawingRoutine', '23'), ('deathFrames', '8')):
        if f'    {k}:' in body:
            body = re.sub(rf'    {k}: .*\n', f'    {k}: {v}\n', body)
        else:
            body = body.replace('    spriteSheet:', f'    {k}: {v}\n    spriteSheet:', 1)
    open(UNITS, 'w').write(txt[:m.start(2)] + body + txt[m.end(2):])


def main():
    sprites, armors, soldiers, lang = [], [], [], []
    done = []
    for n in list(EXISTING) + list(NEW):
        size = install(n)
        if not size:
            continue
        w, h = size
        sprites += [f'  - type: {sheet_name(n)}', f'    width: {w}', f'    height: {h}', '    subX: 128', '    subY: 160',
                    '    files:', f'      0: Resources/Units/{n}_body.png']
        if n in EXISTING:
            switch_existing(EXISTING[n], sheet_name(n))
        else:
            arm, typ, disp, names = NEW[n]
            armors += [f'  - type: {arm}', f'    spriteSheet: {sheet_name(n)}', '    drawingRoutine: 23', '    deathFrames: 8',
                       '    corpseBattle: [STR_CORPSE_DUKE]', '    frontArmor: 12', '    sideArmor: 8', '    rearArmor: 5',
                       '    underArmor: 2', '    loftempsSet: [ 3 ]']
            nam = f'Resources/Names/{"RegularJoe" if names is None else typ[4:].title().replace("_", "")}.nam'
            if names is not None:
                key = 'femaleFirst' if n in FEMALE else 'maleFirst'
                open(os.path.join(MOD, nam), 'w').write(f'{key}:\n' + ''.join(f'  - "{x}"\n' for x in names)
                                                        + f'femaleFrequency: {100 if n in FEMALE else 0}\n')
            soldiers += [f'  - type: {typ}'] + STATS.rstrip('\n').split('\n') + [
                f'    armor: {arm}', '    standHeight: 22', '    kneelHeight: 14',
                f'    femaleFrequency: {100 if n in FEMALE else 0}', '    soldierNames:', '      - delete', f'      - {nam}',
                '    deathMale: [41, 42, 43]', '    deathFemale: [44, 45, 46]']
            lang += [(typ, disp), (arm, disp.upper())]
        done.append(n)
    out = ['# Whole-body soldier sheets rendered by build/sprites/render_cast.sh, drawn by routine 23.',
           '# Written by build/install_body_sheets.py - edit the script, not this file.', 'extraSprites:'] + sprites
    if armors:
        out += ['armors:'] + armors
    if soldiers:
        out += ['soldiers:'] + soldiers
    open(os.path.join(MOD, 'Ruleset', 'gijoe_body_sheets.rul'), 'w').write('\n'.join(out) + '\n')
    for L in ('en-US', 'en-GB'):
        p = os.path.join(MOD, 'Language', f'{L}.yml')
        t = open(p).read()
        add = ''.join(f'  {k}: {v}\n' for k, v in lang if f'\n  {k}:' not in t)
        if add:
            open(p, 'w').write(t.rstrip('\n') + '\n' + add)
    print('installed:', ', '.join(done) or 'nothing yet')


if __name__ == '__main__':
    main()
