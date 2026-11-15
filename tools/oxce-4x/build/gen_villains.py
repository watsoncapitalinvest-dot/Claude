#!/usr/bin/env python3
"""ROSTER's villain records -> the villains as Cobra units (BUILD's villain pass, 15 Nov).

    python3 build/gen_villains.py [--sheets DIR]

Reads roster/roster_cobra_b1.yaml and roster_cobra_b2.yaml (ROSTER's data, never hand-edited here) and writes
mod/Ruleset/gijoe_villains.rul:

- a unit for every villain the game does not have yet (26), with the record's stats as they stand, his
  signature weapon built in (the armory class -> an item in the game, WEAPONS below), a body sheet where ROSTER
  has made one (7: Bludd, Baroness, Firefly, Scrap-Iron, Buzzer, Torch, Ripper), else the Cobra trooper's look;
- the native traits that are armour lines (camouflage, sight, flying, stun immunity);
- an availability window from the record, all missionOnly: how villains reach a battle in a campaign is John's
  open question ("save this for later"), so for now a villain only appears where a deployment names him;
- villains: the engine's table of each villain's Move and trait (Battlescape/Villains.cpp). Only the Year 1
  Moves are built; the rest are listed with move: NONE so the table says plainly what is missing;
- STR_VILLAIN_TEST, a New Battle mission on the HUNTAMB farm with the Year 1 villains against the Joes.

Cobra Commander, Destro and Storm Shadow already exist (gijoe_units.rul); their stats are set to the record's
there by this script, in place. The sheets are copied from --sheets (default: John's Reference\\sheets staged).
"""
import os
import re
import shutil
import sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.normpath(os.path.join(HERE, '..'))
MOD = os.path.join(TOOLS, 'mod')
SHEETS = sys.argv[sys.argv.index('--sheets') + 1] if '--sheets' in sys.argv else '/mnt/user-data/uploads/GIJoe_XCOM_4x/Reference/sheets'
EXISTING = {'STR_COBRA_COMMANDER_UNIT', 'STR_DESTRO_UNIT', 'STR_STORM_SHADOW_UNIT'}
KEYS = ['tu', 'stamina', 'health', 'bravery', 'reactions', 'firing', 'throwing', 'strength', 'psiStrength', 'psiSkill', 'melee']

# armory class -> the items he carries (built in: he always has them, whatever the deployment issues)
WEAPONS = {
    'W_LASER_P': ['STR_LASER_PISTOL'],
    'W_LASER_R': ['STR_GJ_XMLR1A_LASER_RIFLE', 'STR_GJ_AMMO_ALASER'],
    'W_MISSILE': ['STR_ROCKET_LAUNCHER', 'STR_SMALL_ROCKET', 'STR_SMALL_ROCKET'],
    'W_SMG': ['STR_PISTOL', 'STR_PISTOL_CLIP', 'STR_PISTOL_CLIP'],
    'W_BOW': ['STR_GJ_XK1_CROSSBOW', 'STR_GJ_NINJA_SWORD', 'STR_GJ_AMMO_ABOLT', 'STR_GJ_AMMO_ABOLT'],
    'W_PISTOL': ['STR_GJ_M1911_PISTOL', 'STR_GJ_AMMO_A45', 'STR_GJ_AMMO_A45'],
    'W_RIFLE_J': ['STR_GJ_M16', 'STR_GJ_AMMO_A556', 'STR_GJ_AMMO_A556'],
    'W_STUN': ['STR_GJ_M1911_PISTOL', 'STR_STUN_ROD', 'STR_GJ_AMMO_A45'],
    'W_KNIFE': ['STR_GJ_M1911_PISTOL', 'STR_GJV_KNIFE', 'STR_GJ_AMMO_A45'],
    'W_SNIPER': ['STR_LASER_RIFLE'],
    'W_HARPOON': ['STR_GJ_XK1_CROSSBOW', 'STR_GJ_AMMO_ABOLT', 'STR_GJ_AMMO_ABOLT'],
    'W_FLAMER': ['STR_GJV_TORCH_FLAMER'],
    'W_HEAVY_MELEE': ['STR_GJV_CHAINSAW'],
}
# per-villain weapon where the class alone is wrong
WEAPON_OVERRIDE = {
    'STR_SCRAP_IRON_UNIT': ['STR_BLASTER_LAUNCHER', 'STR_GJ_M1911_PISTOL', 'STR_BLASTER_BOMB', 'STR_GJ_AMMO_A45'],
    'STR_MAJOR_BLUDD_UNIT': ['STR_ROCKET_LAUNCHER', 'STR_GJ_M1911_PISTOL', 'STR_SMALL_ROCKET', 'STR_SMALL_ROCKET', 'STR_GJ_AMMO_A45'],
    'STR_RIPPER_UNIT': ['STR_GJV_CLAW'],
    'STR_BIG_BOA_UNIT': ['STR_GJV_GLOVES'],
    'STR_ROAD_PIG_UNIT': ['STR_GJV_SLEDGE'],
    'STR_MONKEYWRENCH_UNIT': ['STR_GJ_XK1_CROSSBOW', 'STR_GJ_AMMO_ABOLT', 'STR_GRENADE', 'STR_GRENADE'],
}
SHEET = {'STR_MAJOR_BLUDD_UNIT': 'major_bludd', 'STR_BARONESS_UNIT': 'baroness', 'STR_FIREFLY_UNIT': 'firefly',
         'STR_SCRAP_IRON_UNIT': 'scrap_iron', 'STR_BUZZER_UNIT': 'buzzer', 'STR_TORCH_UNIT': 'torch',
         'STR_RIPPER_UNIT': 'ripper'}
# native traits written as armour (ROSTER's [native] lines)
CAMO = {'STR_BARONESS_UNIT', 'STR_ZARTAN_UNIT', 'STR_ZARANA_UNIT', 'STR_ZANDAR_UNIT'}
# the engine's table. move NONE = not built yet (only the Year 1 Moves are, John 15 Nov: "1")
VILLAINS = {
    'STR_MAJOR_BLUDD_UNIT': {'move': 'MARK', 'trait': 'MARKED_LIST', 'pct': 115, 'marked': ['STR_DUKE', 'STR_HAWK']},
    'STR_FIREFLY_UNIT': {'move': 'BOOBY_TRAP', 'item': 'STR_GJV_FIREFLY_CHARGE'},
    'STR_STORM_SHADOW_UNIT': {'move': 'SILENT_ASSASSIN'},   # John 15 Nov 17:31: replaces the Arashikage Strike
    'STR_SCRAP_IRON_UNIT': {'move': 'REMOTE_MISSILE', 'trait': 'VEHICLE_HUNTER', 'pct': 150},
    'STR_COPPERHEAD_UNIT': {'move': 'MOCCASIN_DROP', 'spawn': 'STR_GJV_DROP_TROOPER', 'count': 3},
    'STR_BUZZER_UNIT': {'move': 'CUT_THROUGH', 'trait': 'STEADY'},
    'STR_RIPPER_UNIT': {'move': 'RIP_DOOR', 'trait': 'CLOSE_QUARTERS', 'pct': 125, 'range': 2},
    'STR_TORCH_UNIT': {'move': 'CUT_BURN'},
}
TEST = ['STR_MAJOR_BLUDD_UNIT', 'STR_FIREFLY_UNIT', 'STR_STORM_SHADOW_UNIT', 'STR_SCRAP_IRON_UNIT',
        'STR_COPPERHEAD_UNIT', 'STR_BUZZER_UNIT', 'STR_RIPPER_UNIT', 'STR_TORCH_UNIT']


def window(w):
    m = re.match(r'\s*(\d+)\s*-\s*(\d+)', str(w))
    return (int(m.group(1)), int(m.group(2))) if m else None


def main():
    recs = []
    for f in ('roster_cobra_b1.yaml', 'roster_cobra_b2.yaml'):
        recs += yaml.safe_load(open(os.path.join(TOOLS, 'roster', f)))['named']
    units, armors, sprites, avail, strings, nb_names = [], [], [], [], {}, []
    for r in recs:
        ut = r['unitType']
        st = {k: int(r['stats'].get(k, 0)) for k in KEYS}
        if ut in EXISTING:
            continue
        key = ut[len('STR_'):-len('_UNIT')]
        arm = 'COBRA_TROOPER_ARMOR'
        sheet = SHEET.get(ut)
        if sheet and os.path.exists(os.path.join(SHEETS, sheet + '_body.png')):
            pck = 'GIJOE_%s_BODY_HD.PCK' % sheet.upper()
            u = os.path.join(MOD, 'Resources', 'Units')
            for suf in ('_body.png', '_body_rgb.png'):
                shutil.copy(os.path.join(SHEETS, sheet + suf), os.path.join(u, sheet + suf))
            shutil.copy(os.path.join(SHEETS, sheet + '_body_anchors.txt'), os.path.join(u, 'anchors', pck + '.txt'))
            sprites.append({'type': pck, 'width': 2048, 'height': 5120, 'subX': 128, 'subY': 160,
                            'files': {0: 'Resources/Units/%s_body.png' % sheet}})
            arm = 'VILLAIN_%s_ARMOR' % key
            a = {'type': arm, 'drawingRoutine': 23, 'deathFrames': 8, 'spriteSheet': pck}
        elif ut in CAMO or ut in ('STR_RAPTOR_UNIT', 'STR_ZANZIBAR_UNIT'):
            arm = 'VILLAIN_%s_ARMOR' % key
            a = {'type': arm, 'spriteSheet': 'GIJOE_TROOPER_HD.PCK'}
        else:
            a = None
        if a:
            a.update({'corpseBattle': ['STR_CORPSE_TROOPER'], 'frontArmor': 14, 'sideArmor': 10, 'rearArmor': 6,
                      'underArmor': 2, 'loftempsSet': [3]})
            if ut in CAMO:
                a.update({'camouflageAtDay': 10, 'camouflageAtDark': 5})
            if ut == 'STR_RAPTOR_UNIT':
                a.update({'visibilityAtDay': 24})
            if ut == 'STR_ZANZIBAR_UNIT':
                a.update({'movementType': 1})
            armors.append(a)
        wcls = (r['weapon'].get('armory') or ['W_PISTOL'])[0]
        weapons = WEAPON_OVERRIDE.get(ut, WEAPONS.get(wcls, WEAPONS['W_PISTOL']))
        melee_only = all(w.startswith('STR_GJV_') and w != 'STR_GJV_TORCH_FLAMER' for w in weapons)
        units.append({'type': ut, 'race': 'STR_COBRA', 'rank': 'STR_LIVE_LEADER', 'stats': st, 'armor': arm,
                      'standHeight': 22, 'kneelHeight': 14, 'value': 50, 'deathSound': 41,
                      'intelligence': 4, 'aggression': 3 if melee_only else 2,
                      'builtInWeaponSets': [weapons]})
        strings[ut] = r['name']
        w = window(r['window'])
        # all missionOnly: how a villain reaches a campaign battle is John's open question (15 Nov "save this for
        # later"), so for now he appears only where a deployment names him
        units[-1]['availability'] = {'earliest': w[0] if w else 30, 'full': w[1] if w else 30, 'missionOnly': True,
                                     'substitute': 'STR_COBRA_TROOPER'}
    # the three that exist: record stats in place (gijoe_units.rul is hand-written, so patch the stats block only)
    ufile = os.path.join(MOD, 'Ruleset', 'gijoe_units.rul')
    t = open(ufile).read()
    for r in recs:
        if r['unitType'] not in EXISTING:
            continue
        st = {k: int(r['stats'].get(k, 0)) for k in KEYS}
        pat = re.compile(r'(  - type: %s\n(?:    .*\n)*?    stats:\n)((?:      \w+: -?\d+\n)+)' % r['unitType'])
        m = pat.search(t)
        assert m, r['unitType']
        t = t[:m.start(2)] + ''.join('      %s: %d\n' % (k, st[k]) for k in KEYS) + t[m.end(2):]
    # Storm Shadow carries his own crossbow and sword whatever the deployment issues (the Arashikage Strike needs
    # the sword in his hand)
    m = re.search(r'(  - type: STR_STORM_SHADOW_UNIT\n(?:    .*\n)*?    armor: COBRA_STORM_ARMOR\n)', t)
    if m and 'builtInWeaponSets' not in t[m.end():m.end() + 200]:
        t = t[:m.end()] + '    builtInWeaponSets: [[%s]]\n' % ', '.join(WEAPONS['W_BOW']) + t[m.end():]
    open(ufile, 'w').write(t)

    items = [
        {'type': 'STR_GJV_CHAINSAW', 'battleType': 3, 'weight': 6, 'invWidth': 1, 'invHeight': 3, 'bigSprite': 317,
         'floorSprite': 317, 'handSprite': 80, 'power': 70, 'damageType': 7, 'accuracyMelee': 90, 'tuMelee': 30,
         'clipSize': -1, 'meleeSound': [733, 734, 735], 'twoHanded': True},
        {'type': 'STR_GJV_CLAW', 'battleType': 3, 'weight': 5, 'invWidth': 1, 'invHeight': 3, 'bigSprite': 317,
         'floorSprite': 317, 'handSprite': 80, 'power': 55, 'damageType': 7, 'accuracyMelee': 90, 'tuMelee': 25,
         'clipSize': -1, 'meleeSound': [733, 734, 735]},
        {'type': 'STR_GJV_SLEDGE', 'battleType': 3, 'weight': 6, 'invWidth': 1, 'invHeight': 3, 'bigSprite': 318,
         'floorSprite': 318, 'handSprite': 80, 'power': 65, 'damageType': 7, 'accuracyMelee': 85, 'tuMelee': 30,
         'clipSize': -1, 'meleeSound': [733, 734, 735], 'twoHanded': True},
        {'type': 'STR_GJV_GLOVES', 'battleType': 3, 'weight': 2, 'invWidth': 1, 'invHeight': 2, 'bigSprite': 318,
         'floorSprite': 318, 'handSprite': 80, 'power': 60, 'damageType': 6, 'accuracyMelee': 95, 'tuMelee': 20,
         'clipSize': -1, 'meleeSound': [733, 734, 735]},
        {'type': 'STR_GJV_KNIFE', 'battleType': 3, 'weight': 1, 'invWidth': 1, 'invHeight': 2, 'bigSprite': 318,
         'floorSprite': 318, 'handSprite': 80, 'power': 35, 'damageType': 7, 'accuracyMelee': 100, 'tuMelee': 15,
         'clipSize': -1, 'meleeSound': [733, 734, 735]},
        {'type': 'STR_GJV_TORCH_FLAMER', 'battleType': 1, 'weight': 6, 'invWidth': 1, 'invHeight': 2, 'bigSprite': 3,
         'floorSprite': 3, 'handSprite': 96, 'bulletSprite': 1, 'fireSound': 4, 'clipSize': 12, 'power': 40,
         'damageType': 2, 'accuracySnap': 90, 'tuSnap': 30, 'flatRate': True, 'maxRange': 5},
        # Firefly's charge: armed where he leaves it, goes off when a Joe comes next to it, never drawn for the Joes
        {'type': 'STR_GJV_FIREFLY_CHARGE', 'battleType': 5, 'weight': 3, 'invWidth': 1, 'invHeight': 1,
         'bigSprite': 21, 'floorSprite': 21, 'power': 110, 'damageType': 3, 'blastRadius': 2},
    ]
    drop = {'type': 'STR_GJV_DROP_TROOPER', 'race': 'STR_COBRA', 'rank': 'STR_LIVE_SOLDIER',
            'stats': {'tu': 50, 'stamina': 55, 'health': 18, 'bravery': 20, 'reactions': 25, 'firing': 28,
                      'throwing': 27, 'strength': 30, 'psiStrength': 40, 'psiSkill': 0, 'melee': 23},
            'armor': 'COBRA_TROOPER_ARMOR', 'standHeight': 22, 'kneelHeight': 14, 'value': 10, 'deathSound': 41,
            'intelligence': 2, 'aggression': 2, 'builtInWeaponSets': [['STR_RIFLE', 'STR_RIFLE_CLIP', 'STR_RIFLE_CLIP']]}
    units.append(drop)
    # a captured (downed) villain comes home as a live prisoner: the game needs an item named after his unit
    for u in units:
        items.append({'type': u['type'], 'size': 0.0, 'recover': True, 'liveAlien': True, 'costSell': 0})
    strings.update({
        'STR_GJV_DROP_TROOPER': 'Cobra Trooper',
        'STR_GJV_CHAINSAW': 'Chainsaw', 'STR_GJV_CLAW': 'Jaws-of-life claw', 'STR_GJV_SLEDGE': 'Sledgehammer',
        'STR_GJV_GLOVES': 'Boxing gloves', 'STR_GJV_KNIFE': 'Knife', 'STR_GJV_TORCH_FLAMER': 'Cutting torch (Torch)',
        'STR_GJV_FIREFLY_CHARGE': "Firefly's charge",
        'STR_VILLAIN_TEST': 'Cobra villains (Year 1 test)',
        'STR_VILLAIN_TEST_BRIEFING': 'Major Bludd, Firefly, Storm Shadow, Scrap-Iron, Copperhead, Buzzer, Ripper and Torch are on the farm. Each uses his special Move once.',
        'STR_GJV_MARK': '{0} marks {1}: every Cobra gun is on him.',
        'STR_GJV_MOCCASIN': 'A boat engine roars somewhere on the map.',
        'STR_GJV_ASSASSIN': 'A bolt from nowhere.',
        'STR_GJV_BREACH': '{0} cuts through the wall.',
        'STR_GJV_DOOR': '{0} rips the door off.',
        'STR_GJV_BURN': '{0} cuts through and sets it burning.',
    })
    villains = [dict(unit=u, **v) for u, v in VILLAINS.items()]
    for r in recs:
        if r['unitType'] not in VILLAINS:
            villains.append({'unit': r['unitType'], 'move': 'NONE'})
    test_ranks = TEST + ['STR_COBRA_TROOPER']
    rul = {
        'items': items,
        'armors': armors,
        'units': units,
        'alienRaces': [{'id': 'STR_GJV_TEST_RACE', 'members': test_ranks}],
        'alienDeployments': [{
            'type': 'STR_VILLAIN_TEST', 'race': 'STR_GJV_TEST_RACE',
            'data': [{'alienRank': i, 'lowQty': 1, 'highQty': 1, 'dQty': 0, 'percentageOutsideUfo': 100, 'itemSets': [[]]}
                     for i in range(len(TEST))] +
                    [{'alienRank': len(TEST), 'lowQty': 4, 'highQty': 4, 'dQty': 0, 'percentageOutsideUfo': 100,
                      'itemSets': [['STR_RIFLE', 'STR_RIFLE_CLIP', 'STR_RIFLE_CLIP']]}],
            'width': 50, 'length': 40, 'height': 2, 'terrains': ['HUNTAMB'], 'script': 'HUNTAMB_SCRIPT', 'shade': 0,
            'briefing': {'palette': 0, 'title': 'STR_VILLAIN_TEST', 'desc': 'STR_VILLAIN_TEST_BRIEFING'}}],
        'villains': villains,
        'extraSprites': sprites,
        'extraStrings': [{'type': 'en-US', 'strings': strings}],
    }
    out = os.path.join(MOD, 'Ruleset', 'gijoe_villains.rul')
    hdr = ('# GENERATED by build/gen_villains.py from roster/roster_cobra_b1.yaml and _b2.yaml: do not edit by hand.\n'
           '# The 29 villains as Cobra units, their Moves and traits (Battlescape/Villains.cpp). Year 1 Moves only.\n')
    with open(out, 'w') as f:
        f.write(hdr + yaml.safe_dump(rul, sort_keys=False, width=140))
    print('%d new units (%d with sheets), %d villains in the table, %d with a Move' % (
        len(units) - 1, len(sprites), len(villains), sum(1 for v in villains if v['move'] != 'NONE')))


if __name__ == '__main__':
    main()
