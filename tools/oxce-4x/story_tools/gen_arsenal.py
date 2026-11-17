"""The ARSENAL: every vehicle gun, missile and ammo by its canon name (STORY, 16 Nov 2026; John 18:46-19:05).
Source: John's Sheet "G.I. Joe & Cobra Vehicle Weapons and Ammo" (https://claude.ai/artifact/BmBkkCxj4DivWDwnR5xyJU),
exported to arsenal/vehicle_weapons.csv. The Sheet is the master: re-export it and re-run this.
John's rules:
  - each row is the NAME of a weapon or ammo the game needs; the HUD shows that name in the vehicle's weapon slot
    (the item's own name, NOT a "X fires Y" message);
  - each row gets an INTEL CARD (Intel Files, ARSENAL section), written only from the Sheet's own columns;
  - Joe cards open when the player gets the vehicle; Cobra cards open the first time the weapon is fired at the Joes,
    or when its vehicle's wreck is recovered.
A row with no proper name (lower-case words only, e.g. "missiles") is shown as "<vehicle> <name>".
Writes: <out>/gijoe_story_arsenal_text.rul (extraStrings) and arsenal/arsenal_index.yml (for BUILD: vehicle -> ids).
Usage: python3 gen_arsenal.py ../mod/Ruleset"""
import csv, os, re, sys, yaml
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
N = '{NEWLINE}'
NOUNS = ('gun', 'guns', 'cannon', 'cannons', 'missile', 'missiles', 'rocket', 'rockets', 'bomb', 'bombs', 'torpedo',
         'torpedoes', 'launcher', 'launchers', 'laser', 'lasers', 'mine', 'mines', 'charge', 'charges', 'turret', 'turrets',
         'pod', 'blaster', 'blasters', 'rack', 'racks', 'sprayer', 'deployer', 'flamethrower', 'mortar', 'arm', 'platform',
         'stations', 'blades', 'unit', 'system', 'dispenser', 'liquifier', 'interceptor', 'silo', 'sleds', 'subs', 'helicopter', 'box', 'rifle', 'howitzer', 'cal')

def short_vehicle(v):
    return re.sub(r'\s*\(.*?\)', '', v).strip()

def slug(s):
    return re.sub(r'[^A-Z0-9]+', '_', s.upper()).strip('_')

PLAIN = {'machine', 'missiles', 'missile', 'mortar', 'main', 'mini', 'nose', 'deck', 'long-range', 'multiple', 'twin',
         'dual', 'underside', 'side-mounted', 'forward', 'flamethrower', 'giant', 'sludge', 'rear', 'rapid-fire'}

def proper(name):
    # a code, a quoted nickname, an inner capital, or a capitalised first word that isn't a plain English word
    if re.search(r'[0-9"]', name) or any(c.isupper() for c in name[1:]):
        return True
    w = name.split()[0] if name.split() else ''
    return w[:1].isupper() and w.lower() not in PLAIN

def display(row):
    name = re.sub(r'^\((alt)\)\s*|^plus\s+', '', row['Weapon / ammo name'].strip())
    name = re.sub(r'^\d+\s*x\s*$', '', name).strip()
    wtype = row['Weapon type'].strip()
    base = re.split(r'\s*[(/]', wtype)[0].strip()
    if name and proper(name):
        return name
    words = name.lower().split()
    if not words or words[-1] not in NOUNS:
        name = (name + ' ' + base).strip() if base else (name or 'weapon')
    return f"{short_vehicle(row['Vehicle'])} {name[:1].lower() + name[1:]}"

def card(row, shown):
    lines = [shown.upper()]
    what = row['Weapon type'].strip()
    load = row['Ammo / load'].strip()
    if what or load:
        s = (what[:1].upper() + what[1:]) if what else ''
        lines.append((s + (', ' if s and load else '') + load).strip() + '.')
    qty = row['Qty'].strip()
    lines.append(f"Carried by the {row['Vehicle'].strip()}" + (f": {qty} fitted." if qty else '.'))
    lines.append(('G.I. JOE' if row['Faction'] == 'Joe' else 'COBRA') + ' ARSENAL')
    return N.join(lines)

rows = list(csv.DictReader(open(os.path.join(HERE, 'arsenal', 'vehicle_weapons.csv'), encoding='utf-8')))
S, index, seen = {}, {}, set()
for r in rows:
    shown = display(r)
    fac = 'JOE' if r['Faction'] == 'Joe' else 'COBRA'
    sid = f"STR_GJA_{fac}_{slug(short_vehicle(r['Vehicle']))}_{slug(r['Weapon / ammo name'])}"
    n = 2
    while sid in seen:
        sid = f"{sid}_{n}"; n += 1
    seen.add(sid)
    S[sid] = shown
    S[sid + '_UFOPEDIA'] = card(r, shown)
    index.setdefault(r['Vehicle'].strip(), {'faction': r['Faction'], 'modelOnPC': r['Model on PC'] == 'yes',
                                            'unlock': 'vehicle acquired' if fac == 'JOE' else 'first fired at the Joes, or wreck recovered',
                                            'weapons': []})['weapons'].append({'id': sid, 'name': shown})
S['STR_GJA_SECTION'] = 'ARSENAL'
hdr = ('# STORY: the ARSENAL, every vehicle weapon and ammo by its canon name (John\'s Sheet; story_tools/gen_arsenal.py).\n'
       '# STR_GJA_<id> = the name the HUD shows in the weapon slot; STR_GJA_<id>_UFOPEDIA = its Intel File card.\n'
       '# Generated: edit the Sheet / arsenal/vehicle_weapons.csv, not this file.\n')
body = yaml.dump({'extraStrings': [{'type': 'en-US', 'strings': S}, {'type': 'en-GB', 'strings': S}]},
                 sort_keys=False, width=200, allow_unicode=True)
open(os.path.join(OUT, 'gijoe_story_arsenal_text.rul'), 'w', encoding='utf-8').write(hdr + body)
yaml.dump(index, open(os.path.join(HERE, 'arsenal', 'arsenal_index.yml'), 'w', encoding='utf-8'), sort_keys=False,
          width=200, allow_unicode=True)
longest = max((v for k, v in S.items() if not k.endswith('_UFOPEDIA')), key=len)
print(f'arsenal: {len(rows)} weapons, {len(index)} vehicles, {len(S)} strings; longest HUD name {len(longest)}: {longest}')
