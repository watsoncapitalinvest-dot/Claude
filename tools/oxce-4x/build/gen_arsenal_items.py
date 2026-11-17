"""THE ARSENAL as game items (BRIEF_FOR_BUILD_Arsenal; John 16 Nov 21:24 "I want the ammunitions and guns and cannons
all accurate", 21:29 "B").

Source: John's Sheet, snapshot story_tools/arsenal/vehicle_weapons.csv, ids from story_tools/arsenal/arsenal_index.yml
(STORY's gen_arsenal.py; the names and Intel File texts are STORY's gijoe_story_arsenal_text.rul).

For every row of the Sheet: a weapon item STR_GJA_<id>_W named STR_GJA_<id> and its ammo STR_GJA_<id>_A (same name),
stats DERIVED from the row - nothing typed in by hand:
  group    GUNS / MISSILES / ARTY / DROPS / SP. ROUNDS from the weapon type (HUD v2 weapon lists)
  power    from the calibre, on a curve through the guns already in the game: 5.56 = 30, 7.62 = 34, .50 = 52;
           then 20mm 65, 30mm 75, 40mm 80, 60mm 95, 130mm 140, 200mm 170. No calibre: the type's ordinary figure.
  ammo     guns: one shot = 10 real rounds, at most 100 (the load column; "each" x qty); missiles, bombs, rockets,
           torpedoes: one for one with the load or the quantity on the toy.
Plus an Intel File article per row in the ARSENAL section, and the unlocks:
  Joe:   open once the vehicle is in the game (in-game vehicles now; the rest wait on STR_GJA_HAVE_<vehicle>)
  Cobra: STR_GJA_SEEN_<vehicle>, set by the engine the first time that vehicle fires at the Joes.
And the 10 vehicles in the battle game get their whole Sheet set: the vehicle's own item becomes its first weapon,
the rest are built into its armour.

usage: python3 build/gen_arsenal_items.py   -> mod/Ruleset/zz_gijoe_arsenal.rul + build/arsenal_report.txt
"""
import csv, math, os, re, yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
CSV = os.path.join(ROOT, 'story_tools', 'arsenal', 'vehicle_weapons.csv')
IDX = os.path.join(ROOT, 'story_tools', 'arsenal', 'arsenal_index.yml')
OUT = os.path.join(ROOT, 'mod', 'Ruleset', 'zz_gijoe_arsenal.rul')
REPORT = os.path.join(HERE, 'arsenal_report.txt')

# the vehicles already in the battle game (gijoe_vehicles.rul) -> their Sheet name
IN_GAME = {
    'STR_GJ_VEH_VAMP': 'V.A.M.P.', 'STR_GJ_VEH_VAMP_MK2': 'V.A.M.P. Mk II', 'STR_GJ_VEH_TRIPLE_T': 'Triple "T"',
    'STR_GJ_VEH_MOBAT': 'M.O.B.A.T.', 'STR_GJ_VEH_WOLVERINE': 'Wolverine', 'STR_GJ_VEH_MAULER': 'Mauler M.B.T.',
    'STR_GJ_VEH_STINGER': 'Stinger', 'STR_GJ_VEH_HISS': 'H.I.S.S.', 'STR_GJ_VEH_FERRET': 'Ferret A.T.V.',
    'STR_GJ_VEH_THUNDER': 'Dreadnok Thunder Machine',
}

CURVE = [(5.56, 30), (7.62, 34), (12.7, 52), (20, 65), (30, 75), (40, 80), (60, 95), (130, 140), (200, 170)]


def by_calibre(mm):
    if mm <= CURVE[0][0]: return CURVE[0][1]
    for (a, pa), (b, pb) in zip(CURVE, CURVE[1:]):
        if mm <= b:
            t = (math.log(mm) - math.log(a)) / (math.log(b) - math.log(a))
            return round(pa + t * (pb - pa))
    return CURVE[-1][1]


def calibre(text):
    t = text.lower()
    m = re.search(r'(\d+(?:\.\d+)?)\s*mm', t)
    if m: return float(m.group(1))
    m = re.search(r'\.(\d{2})\s*cal', t) or re.search(r'(?<![\d.])\.(\d{2})\b', t)
    if m: return {'50': 12.7, '30': 7.62, '45': 11.43}.get(m.group(1), int(m.group(1)) * 0.254)
    if '7.62' in t: return 7.62
    return None


def number(s):
    return int(s.replace(',', ''))


def classify(name, wtype, load):
    t = (wtype + ' ' + name).lower().replace('laser-guided', 'guided')
    if any(k in t for k in ('torpedo',)): return 'DROPS', 'torpedo'
    if any(k in t for k in ('depth charge', 'mine')): return 'DROPS', 'mine'
    if 'bomb' in t and 'launcher' not in t and 'rocket' not in t: return 'DROPS', 'bomb'
    if any(k in t for k in ('flame', 'freeze', 'water cannon', 'foam', 'smoke', 'sludge')) or re.search(r'\b(ink|net|nets)\b', t): return 'SP. ROUNDS', 'special'
    if 'laser' in t and 'missile' not in t: return 'GUNS', 'laser'
    if any(k in t for k in ('mortar', 'howitzer', 'artillery', 'grenade launcher', 'automatic launcher')): return 'ARTY', 'lob'
    if any(k in t for k in ('missile', 'rocket', 'sam', 'agm', 'aim-', 'stinger', 'sidewinder', 'sparrow', 'phoenix')):
        if 'laser' in t and 'missile' not in t: return 'GUNS', 'laser'
        return 'MISSILES', 'missile'
    if 'pulse' in t: return 'GUNS', 'pulse'
    if 'laser' in t: return 'GUNS', 'laser'
    if any(k in t for k in ('gatling', 'vulcan', 'chain gun', 'chain guns', 'rotary', 'minigun')): return 'GUNS', 'gatling'
    if 'machine gun' in t or 'mg' in t.split(): return 'GUNS', 'mg'
    if 'cannon' in t: return 'GUNS', 'cannon'
    return 'GUNS', 'gun'


def derive(row):
    name, wtype, load, qty = row['Weapon / ammo name'], row['Weapon type'], row['Ammo / load'], row['Qty']
    group, kind = classify(name, wtype, load)
    mm = calibre(' '.join((wtype, load, name)))
    if mm is None and re.search(r'\b(tank|main) (cannon|gun)\b', (wtype + ' ' + name).lower()):
        mm = 105.0                        # a tank's main gun with no calibre given: the 105mm of its day
    qn = re.findall(r'\d+', qty)
    q = int(qn[-1]) if qn else 1          # "6-12" -> the most it carries
    why = []
    s = dict(group=group, kind=kind, dt=1, power=0, radius=-1, clip=0, auto=0, arcing=False,
             acc=(60, 85, 0), tu=(25, 50, 35))
    if kind in ('gun', 'mg', 'gatling', 'cannon'):
        if mm: s['power'] = by_calibre(mm); why.append('%gmm' % mm)
        else:
            s['power'] = {'mg': 52, 'gatling': 60, 'cannon': 75, 'gun': 52}[kind]; why.append('no calibre: %s default' % kind)
        if mm and mm >= 40: s['dt'], s['radius'] = 3, (1 if mm < 100 else 2)
        s['auto'] = {'mg': 3, 'gatling': 5, 'gun': 3, 'cannon': 3 if (mm or 30) <= 30 else 0}[kind]
        if kind == 'cannon' and (mm or 30) > 30: s['acc'], s['tu'] = (55, 90, 0), (35, 60, 0)
    elif kind == 'laser':
        s.update(dt=4, power=70, auto=3); why.append('laser')
    elif kind == 'pulse':
        s.update(dt=5, power=90, auto=0); why.append('pulse')
    elif kind == 'missile':
        t = (wtype + ' ' + name).lower()
        p = 90 if ('air-to-air' in t or 'surface-to-air' in t or 'aa' in t.split()) else 110
        if 'rocket' in t and 'missile' not in t: p = 80
        s.update(dt=3, power=p, radius=2, acc=(60, 100 if any(k in t for k in ('guided', 'homing', 'seeking')) else 90, 0), tu=(40, 60, 0))
        why.append('missile %d' % p)
    elif kind == 'lob':
        p = by_calibre(mm) if mm else 70
        s.update(dt=3, power=p, radius=2 if p >= 80 else 1, arcing=True, acc=(55, 80, 0), tu=(35, 55, 0))
        why.append('lobbed %s' % ('%gmm' % mm if mm else 'default'))
    elif kind in ('bomb', 'mine', 'torpedo'):
        p = {'bomb': 130, 'mine': 110, 'torpedo': 140}[kind]
        if '250 lb' in load.lower(): p = 120
        s.update(dt=3, power=p, radius=3 if kind == 'bomb' else 2, arcing=kind == 'bomb', acc=(50, 75, 0), tu=(40, 60, 0))
        why.append(kind)
    elif kind == 'special':
        t = (wtype + ' ' + name).lower()
        if 'flame' in t: s.update(dt=2, power=60, radius=1)
        elif 'smoke' in t or 'ink' in t: s.update(dt=9, power=30, radius=3)
        else: s.update(dt=6, power=60, radius=1)            # freeze, water, foam, net, sludge: they stop a man, not kill him
        s.update(arcing=False, auto=0, tu=(30, 50, 0)); why.append('special')
    # ammo
    lt = (load + ' ' + wtype).lower()
    m = re.search(r'([\d,]{2,})\s*(?:hedp\s*)?(?:rounds|rds|round)', lt) or re.search(r'\(?([\d,]{3,})\s*rds', lt)
    if s['group'] == 'GUNS' and m:
        rounds = number(m.group(1)) * (q if 'each' in lt else 1)
        s['clip'] = max(1, min(100, math.ceil(rounds / 10))); why.append('%d rounds -> %d shots' % (rounds, s['clip']))
    elif 'regenerat' in lt:
        s['clip'] = 99; why.append('regenerating')
    elif s['group'] == 'GUNS':
        s['clip'] = {'mg': 50, 'gatling': 100, 'cannon': 20, 'gun': 50, 'laser': 30, 'pulse': 20}[kind]; why.append('no load: default')
    else:
        nums = [int(x) for x in re.findall(r'\b(\d{1,2})\b', lt.replace('mm', ' mm'))] if not re.search(r'\d+\s*mm', lt) else []
        if '+' in lt and nums: n = sum(nums)
        elif re.match(r'^\s*\d{1,2}\b', lt) and nums: n = nums[0]
        else: n = q if qn else 2
        if s['group'] == 'ARTY' and not re.search(r'\d', lt) and not qty.strip(): n = 10   # a launcher with no load given
        if s['group'] == 'ARTY' and qn and not re.search(r'\d', load) and n <= 2: n = 10   # qty = barrels, not rounds
        s['clip'] = max(1, min(24, n)); why.append('%d carried' % s['clip'])
    s['why'] = '; '.join(why)
    return s


def item_pair(wid, s, sprite):
    w = {'type': wid + '_W', 'name': wid, 'battleType': 1, 'fixedWeapon': True, 'invWidth': 1, 'invHeight': 1,
         'weight': 1, 'bigSprite': sprite['big'], 'floorSprite': sprite['floor'], 'handSprite': 0,
         'bulletSprite': sprite['bullet'], 'fireSound': sprite['fire'], 'compatibleAmmo': [wid + '_A'],
         'accuracySnap': s['acc'][0], 'tuSnap': s['tu'][0], 'accuracyAimed': s['acc'][1], 'tuAimed': s['tu'][1],
         'gjaGroup': s['group']}
    if s['auto']:
        w.update(accuracyAuto=max(30, s['acc'][0] - 15), tuAuto=s['tu'][2] or 35, confAuto={'shots': s['auto']})
    if s['arcing']: w['arcingShot'] = True
    a = {'type': wid + '_A', 'name': wid, 'battleType': 2, 'clipSize': s['clip'], 'power': s['power'],
         'damageType': s['dt'], 'weight': 1, 'invWidth': 1, 'invHeight': 1, 'bigSprite': 12, 'floorSprite': 12,
         'hitAnimation': 26 if s['dt'] in (1, 4, 5) else 0}
    if s['radius'] >= 0 and s['dt'] in (2, 3, 6, 9): a['blastRadius'] = s['radius']
    return w, a


def main():
    rows = list(csv.DictReader(open(CSV)))
    idx = yaml.safe_load(open(IDX))
    vg = yaml.safe_load(open(os.path.join(ROOT, 'mod', 'Ruleset', 'gijoe_vehicles.rul')))
    veh_items = {i['type']: i for i in vg['items']}
    veh_units = {u['type']: u for u in vg['units']}
    # sprites: the vehicle's own picture where it has one, else the V.A.M.P. gun's
    gen_sprite = {'big': 340, 'floor': 0, 'bullet': 2, 'fire': [727, 728, 729]}
    by_vehicle = {}
    for r in rows:
        by_vehicle.setdefault(r['Vehicle'], []).append(r)
    items, ufo, research, report = [], [], [], []
    ids_by_vehicle = {}
    for v, rs in by_vehicle.items():
        ws = idx[v]['weapons']
        assert len(ws) == len(rs), v
        fac = idx[v]['faction']
        vslug = re.sub(r'[^A-Z0-9]+', '_', v.upper()).strip('_')
        gate = ('STR_GJA_SEEN_' if fac == 'Cobra' else 'STR_GJA_HAVE_') + vslug
        research.append({'name': gate, 'cost': 1, 'points': 0, 'requiresBaseFunc': ['STR_STORY_NEVER']})
        ids_by_vehicle[v] = []
        for r, w in zip(rs, ws):
            s = derive(r)
            wi, ai = item_pair(w['id'], s, gen_sprite)
            if fac == 'Cobra': wi['gjaUnlock'] = gate
            items += [wi, ai]
            ids_by_vehicle[v].append((w['id'], s))
            ufo.append({'id': w['id'], 'type_id': 8, 'section': 'STR_GJA_SECTION', 'text': w['id'] + '_UFOPEDIA',
                        'requires': [gate], 'listOrder': 60000 + len(ufo)})
            report.append('%-6s %-34s %-44s %-10s pow %3d dt %d clip %3d %s' % (
                fac, v[:34], w['name'][:44], s['group'], s['power'], s['dt'], s['clip'], s['why']))
    # the vehicles in the battle game: the item is the first weapon, the rest are built into the armour
    vehicle_over, armor_over, unit_over = [], [], []
    for vt, sheet in IN_GAME.items():
        lst = ids_by_vehicle[sheet]
        first_id, fs = lst[0]
        w0, a0 = item_pair(first_id, fs, gen_sprite)
        it = veh_items[vt]
        vehicle_over.append({k: v for k, v in dict(type=vt, name=first_id, accuracySnap=w0['accuracySnap'], tuSnap=w0['tuSnap'],
                            accuracyAimed=w0['accuracyAimed'], tuAimed=w0['tuAimed'], arcingShot=fs['arcing'],
                            gjaGroup=fs['group']).items()})
        if idx[sheet]['faction'] == 'Cobra':
            vehicle_over[-1]['gjaUnlock'] = 'STR_GJA_SEEN_' + re.sub(r'[^A-Z0-9]+', '_', sheet.upper()).strip('_')
        if fs['auto']:
            vehicle_over[-1].update(accuracyAuto=w0['accuracyAuto'], tuAuto=w0['tuAuto'], confAuto=w0['confAuto'])
        ammo = it['compatibleAmmo'][0]
        vehicle_over.append({'type': ammo, 'name': first_id, 'clipSize': fs['clip'], 'power': fs['power'], 'damageType': fs['dt'],
                             **({'blastRadius': fs['radius']} if fs['radius'] >= 0 and fs['dt'] in (2, 3, 6, 9) else {})})
        rest = []
        for wid, _ in lst[1:]:
            rest += [wid + '_W', wid + '_A']
        armor = veh_units[vt]['armor']
        if rest:
            armor_over.append({'type': armor, 'builtInWeapons': rest})
        report.append('IN GAME %s = %s: item -> %s; built in: %d more' % (vt, sheet, first_id, len(lst) - 1))
    # Joe vehicles already in the game: their cards open from the start
    have_now = {'STR_GJA_HAVE_' + re.sub(r'[^A-Z0-9]+', '_', s.upper()).strip('_') for vt, s in IN_GAME.items()
                if idx[s]['faction'] == 'Joe'}
    for u in ufo:
        if u['requires'][0] in have_now:
            del u['requires']
    rack = {'id': 'STR_GJA_RACK', 'x': 2000, 'y': 0, 'type': 0, 'slots': [[i, 0] for i in range(16)]}
    rul = {'invs': [rack], 'items': items + vehicle_over, 'armors': armor_over, 'research': research, 'ufopaedia': ufo,
           'extraStrings': [{'type': 'en-US', 'strings': {'STR_GJA_SECTION': 'ARSENAL'}}]}
    hdr = ('# GENERATED by build/gen_arsenal_items.py from John\'s Sheet (story_tools/arsenal): do not edit by hand.\n'
           '# Every vehicle weapon and its ammo, stats derived from calibre and load; Intel File cards in ARSENAL.\n')
    open(OUT, 'w').write(hdr + yaml.safe_dump(rul, sort_keys=False, width=160, allow_unicode=True, default_flow_style=None))
    open(REPORT, 'w').write('\n'.join(report) + '\n')
    print('arsenal: %d weapons, %d vehicles, %d in the battle game' % (len(items) // 2, len(by_vehicle), len(IN_GAME)))


if __name__ == '__main__':
    main()
