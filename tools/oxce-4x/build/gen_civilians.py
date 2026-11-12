#!/usr/bin/env python3
"""Civilians: the pool every mission draws from (John, 12 Nov: "all of them should be a pool
the levels choose from").

    python3 build/gen_civilians.py [--sheets DIR]

For every civilian whose rendered sheet exists (build/sprites/render_cast.sh writes
<name>_body.png, _body_rgb.png and _body_anchors.txt), copies it into
mod/Resources/Units/civ_<name>_body*.png + anchors/<SHEET>.txt, and writes
mod/Ruleset/gijoe_civilians.rul:
  - one whole-body sheet, armour and unit per civilian (drawingRoutine 23, like the soldiers);
  - every terrain (the base game's and the mod's) gets civilianTypes = the whole pool, so the
    battle generator's random pick per civilian draws from all of them.
Civilians with no sheet yet are left out, so the ruleset never names a missing file.
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
MOD = os.path.join(ROOT, 'mod')
SPEC = os.path.join(HERE, 'sprites', 'civ', 'civ.json')
SHEETS = sys.argv[sys.argv.index('--sheets') + 1] if '--sheets' in sys.argv else '/tmp/claude-0/ws/cast/sheets'
ENGINE_STD = '/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad/oxc/oxce/build/bin/standard/xcom1/terrains.rul'


def terrain_names():
    names = set()
    files = [ENGINE_STD] + [os.path.join(MOD, 'Ruleset', f) for f in os.listdir(os.path.join(MOD, 'Ruleset')) if f.endswith('.rul')]
    for p in files:
        if not os.path.exists(p) or p.endswith('gijoe_civilians.rul'):
            continue
        txt = open(p, encoding='utf-8').read()
        m = re.search(r'^terrains:\s*\n(.*?)(?=^\S)', txt + '\nEOF:\n', re.S | re.M)
        if m:
            names.update(re.findall(r'^\s*-\s*name:\s*(\S+)', m.group(1), re.M))
    return sorted(names)


def main():
    spec = json.load(open(SPEC))
    have = []
    for c in spec:
        n = c['name']
        src = os.path.join(SHEETS, f'{n}_body.png')
        if not os.path.exists(src):
            continue
        stem = f'civ_{n.lower()}'
        shutil.copy(src, os.path.join(MOD, 'Resources', 'Units', f'{stem}_body.png'))
        shutil.copy(os.path.join(SHEETS, f'{n}_body_rgb.png'), os.path.join(MOD, 'Resources', 'Units', f'{stem}_body_rgb.png'))
        sheet = f'GIJOE_CIV_{n.upper()}_HD.PCK'
        shutil.copy(os.path.join(SHEETS, f'{n}_body_anchors.txt'), os.path.join(MOD, 'Resources', 'Units', 'anchors', f'{sheet}.txt'))
        female = 'woman' in c.get('desc', '') or 'female' in c.get('desc', '')
        have.append((n, stem, sheet, female))
    if not have:
        sys.exit('no civilian sheets yet in ' + SHEETS)
    from PIL import Image
    L = ['# Civilians: one pool, every mission draws from it (John, 12 Nov).',
         '# Written by build/gen_civilians.py - edit the script, not this file.', 'extraSprites:']
    for n, stem, sheet, _ in have:
        w, h = Image.open(os.path.join(MOD, 'Resources', 'Units', f'{stem}_body.png')).size
        L += [f'  - type: {sheet}', f'    width: {w}', f'    height: {h}', '    subX: 128', '    subY: 160',
              '    files:', f'      0: Resources/Units/{stem}_body.png']
    L.append('armors:')
    for n, stem, sheet, female in have:
        L += [f'  - type: CIV_{n.upper()}_ARMOR', f'    spriteSheet: {sheet}', '    drawingRoutine: 23', '    deathFrames: 8',
              f'    corpseBattle: [{"CIVF_CORPSE" if female else "CIVM_CORPSE"}]',
              '    frontArmor: 0', '    sideArmor: 0', '    rearArmor: 0', '    underArmor: 0', '    loftempsSet: [ 3 ]']
    L.append('units:')
    for n, stem, sheet, female in have:
        L += [f'  - type: CIV_{n.upper()}', f'    refNode: &civ_{n.lower()}', '    race: STR_CIVILIAN',
              '    stats: {tu: 35, stamina: 65, health: 30, bravery: 80, reactions: 30, firing: 30, throwing: 50, strength: 20, psiStrength: 5, psiSkill: 0, melee: 50}',
              f'    armor: CIV_{n.upper()}_ARMOR', '    standHeight: 21', '    kneelHeight: 14', '    value: 30',
              '    intelligence: 4', '    energyRecovery: 20', f'    deathSound: {[44, 45, 46] if female else [41, 42, 43]}']
    pool = [f'CIV_{n.upper()}' for n, *_ in have]
    L.append('terrains:')
    for t in terrain_names():
        L += [f'  - name: {t}', '    civilianTypes:'] + [f'      - {u}' for u in pool]
    # the refNode anchors are unused; drop them (kept the generator simple)
    out = '\n'.join(l for l in L if 'refNode' not in l) + '\n'
    open(os.path.join(MOD, 'Ruleset', 'gijoe_civilians.rul'), 'w').write(out)
    print(f'{len(have)} civilians in the pool:', ', '.join(n for n, *_ in have))


if __name__ == '__main__':
    main()
