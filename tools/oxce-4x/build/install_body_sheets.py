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
    # the rest of the Day 1 sixteen (DAY1_SETUP.md); each wears FALLBACK until his sheet lands
    'hawk': ('STR_HAWK_UC', 'STR_HAWK', 'Hawk', ['Hawk']),
    'rock_n_roll': ('STR_ROCK_N_ROLL_UC', 'STR_ROCK_N_ROLL', "Rock 'n Roll", ["Rock 'n Roll"]),
    'grand_slam': ('STR_GRAND_SLAM_UC', 'STR_GRAND_SLAM', 'Grand Slam', ['Grand Slam']),
    'short_fuze': ('STR_SHORT_FUZE_UC', 'STR_SHORT_FUZE', 'Short-Fuze', ['Short-Fuze']),
    'zap': ('STR_ZAP_UC', 'STR_ZAP', 'Zap', ['Zap']),
    'grunt': ('STR_GRUNT_UC', 'STR_GRUNT', 'Grunt', ['Grunt']),
    'stalker': ('STR_STALKER_UC', 'STR_STALKER', 'Stalker', ['Stalker']),
    'breaker': ('STR_BREAKER_UC', 'STR_BREAKER', 'Breaker', ['Breaker']),
    'flash': ('STR_FLASH_UC', 'STR_FLASH', 'Flash', ['Flash']),
    'doc': ('STR_DOC_UC', 'STR_DOC', 'Doc', ['Doc']),
    'airborne': ('STR_AIRBORNE_UC', 'STR_AIRBORNE', 'Airborne', ['Airborne']),
}
# SHORTCUTS.md #6: a soldier type whose sheet has not been rendered yet wears one that has
FALLBACK = {'greenshirt_rifleman': 'STR_BEACH_HEAD_UC', 'greenshirt_medic': 'STR_BEACH_HEAD_UC'}
FALLBACK_DEFAULT = 'STR_DUKE_UC'
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


def soldier(n, typ, arm, names):
    """A soldier type wearing armour arm; a named Joe gets a names file holding only his name."""
    nam = f'Resources/Names/{"RegularJoe" if names is None else typ[4:].title().replace("_", "")}.nam'
    if names is not None:
        # the engine refuses a pool with an empty maleFirst, so a woman's name is in both lists
        lst = ''.join('  - "%s"\n' % x for x in names)
        open(os.path.join(MOD, nam), 'w').write('maleFirst:\n' + lst + ('femaleFirst:\n' + lst if n in FEMALE else '')
                                                + f'femaleFrequency: {100 if n in FEMALE else 0}\n')
    stats = STATS.rstrip('\n').split('\n')
    if names is not None:   # a named Joe is never on the hiring list (costBuy 0 hides him)
        stats = [l.replace('costBuy: 40000', 'costBuy: 0') for l in stats]
    return [f'  - type: {typ}'] + stats + [
        f'    armor: {arm}', '    standHeight: 22', '    kneelHeight: 14',
        f'    femaleFrequency: {100 if n in FEMALE else 0}', '    soldierNames:', '      - delete', f'      - {nam}',
        '    deathMale: [41, 42, 43]', '    deathFemale: [44, 45, 46]']


def clone_armour(src, new, inv, generated):
    """The armour block src (from gijoe_units.rul, or one written earlier in this run) as new, with
    spriteInv set to inv."""
    lines = None
    for text in ('\n'.join(generated), open(UNITS).read()):
        tl = text.split('\n')
        for i, l in enumerate(tl):
            if l.strip() == f'- type: {src}':
                j = i + 1
                while j < len(tl) and tl[j].startswith('    '):
                    j += 1
                lines = tl[i:j]
                break
        if lines:
            break
    if not lines:
        raise SystemExit(f'cannot clone armour {src}: not found')
    out = [f'  - type: {new}']
    for l in lines[1:]:
        if l.strip().startswith('spriteInv:'):
            continue
        out.append(l)
    out.insert(2, f'    spriteInv: {inv}')
    return out


def main():
    sprites, armors, soldiers, lang = [], [], [], []
    done = []
    for n in list(EXISTING) + list(NEW):
        size = install(n)
        if not size and n in NEW:
            arm, typ, disp, names = NEW[n]
            fb = FALLBACK.get(n, FALLBACK_DEFAULT)
            if os.path.exists(os.path.join(MOD, 'Resources', 'Inventory', f'{n}_inv.png')):
                # His own equipment-screen figure exists, but he still wears a borrowed body
                # sheet: the figure belongs to the armour, so he gets his own copy of the borrowed
                # armour carrying his figure (SHORTCUTS #6).
                inv = f'GIJOE_{n.upper()}_INV'
                sprites += [f'  - type: {inv}.SPK', '    singleImage: true', '    width: 320', '    height: 200',
                            '    files:', f'      0: Resources/Inventory/{n}_inv.png']
                armors += clone_armour(fb, arm, inv, armors)
                lang += [(arm, disp.upper())]
                fb = arm
            soldiers += soldier(n, typ, fb, names)
            lang += [(typ, disp)]
            continue
        if not size:
            continue
        w, h = size
        sprites += [f'  - type: {sheet_name(n)}', f'    width: {w}', f'    height: {h}', '    subX: 128', '    subY: 160',
                    '    files:', f'      0: Resources/Units/{n}_body.png']
        if n in EXISTING:
            switch_existing(EXISTING[n], sheet_name(n))
        else:
            arm, typ, disp, names = NEW[n]
            # Inventory figure: his own if one has been painted (Resources/Inventory/<name>_inv.png), else
            # Duke's (SHORTCUTS #6). An armour with no spriteInv crashes the equip screen before a battle.
            inv = 'GIJOE_DUKE_INV'
            if os.path.exists(os.path.join(MOD, 'Resources', 'Inventory', f'{n}_inv.png')):
                inv = f'GIJOE_{n.upper()}_INV'
                sprites += [f'  - type: {inv}.SPK', '    singleImage: true', '    width: 320', '    height: 200',
                            '    files:', f'      0: Resources/Inventory/{n}_inv.png']
            armors += [f'  - type: {arm}', f'    spriteSheet: {sheet_name(n)}', f'    spriteInv: {inv}', '    drawingRoutine: 23', '    deathFrames: 8',
                       '    corpseBattle: [STR_CORPSE_DUKE]', '    frontArmor: 12', '    sideArmor: 8', '    rearArmor: 5',
                       '    underArmor: 2', '    loftempsSet: [ 3 ]']
            soldiers += soldier(n, typ, arm, names)
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
