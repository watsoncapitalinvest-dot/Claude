"""Every bullet gun fires the tracer of its own calibre (John 18 Nov 01:42: "make sure the guns match to what they are and
what ammo they use ... all be caliber similar to canon").

Rows of the Projectiles sheet (make_projectile_sheet.py), real rounds, very small, pointing where they fly (each row is
followed by its eight heads, bulletDirectional):
  22 pistol / SMG (9mm, .45, .38)       24 rifle / LMG (5.56, 7.62)       26 heavy MG (.50, 12.7, 14.5)
  28 autocannon (20 - 40mm)             30 cannon (57mm and up)           32 shotgun (buckshot, not directional)
Each also gets gjMuzzleFlash (engine, ProjectileFlyBState): pistol small, rifle and shotgun normal, heavy MG and
autocannon heavy, cannon the cannon flash (MUZZLE.PCK sets from build/make_muzzle_sizes.py).

Only guns that fire BULLETS change: anything on a laser, pulse, rocket, missile, grenade-ball or other special row keeps
it. The calibre is read off the gun and its ammo (type, name, and gen_arsenal_items' calibre parser); a gun with no
calibre in its name is placed by what it is (the KNOWN table, then words like PISTOL / RIFLE / SHOTGUN), then by power.
The engine reads the AMMO's bulletSprite first, so the gun and every round it takes are set.

usage: python3 build/gen_tracers_by_calibre.py  -> mod/Ruleset/zz_gijoe_tracers_calibre.rul (loads after
zz_gijoe_projectile_assign.rul, so it wins), and a report of every gun and its class.
"""
import glob, os, re, sys, yaml
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
RUL = os.path.join(HERE, '..', 'mod', 'Ruleset')
OUT = os.path.join(RUL, 'zz_gijoe_tracers_calibre.rul')
PISTOL, RIFLE, HMG, AUTOCANNON, CANNON, SHOTGUN = 22, 24, 26, 28, 30, 32   # each but buckshot is followed by its 8 heads
FLASH = {22: 0, 24: 1, 32: 1, 26: 2, 28: 2, 30: 3}   # gjMuzzleFlash: 0 small, 1 normal, 2 heavy, 3 cannon
NAMES = {22: 'pistol/SMG', 24: 'rifle/LMG', 26: 'heavy MG', 28: 'autocannon', 30: 'cannon', 32: 'shotgun'}
BULLET_ROWS = {None, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32}   # stock dots and the two old tracers
SKIP = ('CROSSBOW', 'FLARE', 'FLAMER', 'FLAME', 'TORCH', 'TRANQ', 'DEPTH_CHARGE', 'MINE', 'TORPEDO', 'BAZOOKA', 'JAVELIN',
        'ROCKET', 'MISSILE', 'GRENADE', 'MORTAR', 'BOMB', 'DART', 'NET', 'HARPOON', 'LAUNCHER', 'PULVERIZER_GL')

# the mod's own guns whose names carry no calibre (the real weapon each one is)
KNOWN = {
    'STR_GJ_M16': RIFLE, 'STR_GJ_XM16_CARBINE': RIFLE, 'STR_GJ_AK47': RIFLE, 'STR_GJ_M60': RIFLE,
    'STR_GJ_UZI': PISTOL, 'STR_GJ_M1911_PISTOL': PISTOL, 'STR_GJ_REVOLVER': PISTOL, 'STR_GJ_XF7_WASP': PISTOL,
    'STR_GJ_M32_PULVERIZER': PISTOL,       # Duke's M-32 Pulverizer: a submachine gun
    'STR_GJ_SHOTGUN': SHOTGUN, 'STR_GJ_M2X_50CAL': HMG,
    'STR_GJ_VEH_VAMP': HMG,                # V.A.M.P. twin .50
    'STR_GJ_VEH_TRIPLE_T': AUTOCANNON,     # one 30mm cannon per ball (VFACTORY 54)
    'STR_SEA_DEVILFISH_GUN': HMG, 'STR_SEA_SHARC_GUN': HMG, 'STR_SEA_SLED_GUN': HMG, 'STR_TOM_DOOR_GUN': HMG,
    'STR_PISTOL': PISTOL, 'STR_RIFLE': RIFLE, 'STR_SEA_AA_GUN': AUTOCANNON, 'STR_SEA_DECK_GUN': CANNON,
}
WORDS = [  # (pattern, class), first match wins, read off type + name + ammo
    (r'SHOTGUN|SCATTER|BUCKSHOT', SHOTGUN),
    (r'GATLING|MINIGUN|VULCAN', HMG),
    (r'PISTOL|REVOLVER|UZI|SMG|SUBMACHINE|MAC.?10|MP5|DERRINGER|HANDGUN', PISTOL),
    (r'\bM2\b|\.50|50.?CAL|HEAVY.?MACHINE|HMG', HMG),
    (r'TANK.?GUN|MAIN.?GUN|HOWITZER|ARTILLERY|ANNIHILATOR|DEVASTATION', CANNON),
    (r'AUTOCANNON|AUTO.?CANNON|CHAIN.?GUN', AUTOCANNON),
    (r'CANNON', AUTOCANNON),
    (r'RIFLE|CARBINE|MACHINE.?GUN|\bMG\b|M60|M249|SAW|AK|FAL|GARAND|SNIPER|ASSAULT', RIFLE),
]


def calibre(text):
    t = text.lower()
    m = re.search(r'(\d+(?:\.\d+)?)\s*mm', t)
    if m: return float(m.group(1))
    m = re.search(r'\.(\d{2})\s*cal', t) or re.search(r'(?<![\d.])\.(\d{2})\b', t) or re.search(r'\b(50|30|45)[\s_]*cal', t)
    if m: return {'50': 12.7, '30': 7.62, '45': 11.43, '38': 9.0, '22': 5.6}.get(m.group(1), int(m.group(1)) * 0.254)
    if '7.62' in t: return 7.62
    if '5.56' in t: return 5.56
    return None


def by_mm(mm, words):
    if mm < 5.0: return PISTOL
    if mm < 8.5: return RIFLE
    if mm < 12.0: return PISTOL if not re.search(r'RIFLE|CARBINE|MACHINE', words) else RIFLE   # 9mm/.45 handguns
    if mm < 16: return HMG
    if mm < 50: return AUTOCANNON
    return CANNON


def classify(t, w, ammo):
    words = ' '.join([t, str(w.get('name', ''))] + [a.get('type', '') + ' ' + str(a.get('name', '')) for a in ammo]).upper()
    words = words.replace('_', ' ')
    if t in KNOWN:
        return KNOWN[t], 'known'
    if t.startswith('STR_AF_GUN_'):
        return AUTOCANNON, 'jet cannon'      # a fighter's gun is a 20-30mm cannon (M61 Vulcan and kin)
    if max([(a.get('power') or 0) for a in ammo] + [w.get('power') or 0]) <= 0:
        return None, 'no damage'
    if any(re.search(r'\b' + s.replace('_', ' ') + r'\b', words) for s in SKIP):
        return None, 'skip'
    mm = calibre(words)
    if mm:
        return by_mm(mm, words), '%gmm' % mm
    for pat, c in WORDS:
        if re.search(pat, words):
            return c, 'word'
    p = max([(a.get('power') or 0) for a in ammo] + [w.get('power') or 0])
    return (PISTOL if p < 30 else RIFLE if p < 45 else HMG if p < 62 else AUTOCANNON if p < 85 else CANNON), 'power %d' % p


def main():
    items = {}
    for f in sorted(glob.glob(os.path.join(RUL, '*.rul'))):
        if os.path.abspath(f) == os.path.abspath(OUT):
            continue
        try:
            d = yaml.safe_load(open(f)) or {}
        except Exception:
            continue
        for it in d.get('items', []) or []:
            if isinstance(it, dict) and it.get('type'):
                items.setdefault(it['type'], {}).update(it)
    out, report = [], []
    for t, w in sorted(items.items()):
        if w.get('battleType') != 1:
            continue
        ammo = [items[a] for a in (w.get('compatibleAmmo') or []) if a in items]
        # what the engine draws today: the first ammo's row, else the gun's
        rows = [a.get('bulletSprite') for a in ammo] or [w.get('bulletSprite')]
        if not all(r in BULLET_ROWS for r in rows):
            continue
        if ammo and all((a.get('damageType', w.get('damageType', 1)) not in (1, 3, None)) for a in ammo):
            continue          # not a slug: lasers, plasma, stun, smoke ...
        c, why = classify(t, w, ammo)
        if c is None:
            continue
        for target in [t] + [a['type'] for a in ammo]:
            if not any(e['type'] == target for e in out):
                out.append({'type': target, 'bulletSprite': c, 'bulletDirectional': c != SHOTGUN, 'gjMuzzleFlash': FLASH[c]})
        report.append('%-70s %-11s %s' % (t, NAMES[c], why))
    hdr = ('# GENERATED by build/gen_tracers_by_calibre.py: do not edit by hand.\n'
           '# Every bullet gun fires the tracer of its own calibre (John 18 Nov 01:42); the muzzle flash follows the row.\n')
    open(OUT, 'w').write(hdr + yaml.safe_dump({'items': out}, sort_keys=False, default_flow_style=None, width=160))
    open(os.path.join(HERE, 'tracers_report.txt'), 'w').write('\n'.join(report) + '\n')
    print('guns:', len(report), 'items written:', len(out), dict(Counter(r.split()[1] for r in report)))


if __name__ == '__main__':
    main()
