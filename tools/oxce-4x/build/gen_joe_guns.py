#!/usr/bin/env python3
"""The 21 locked G.I. Joe guns (claude/ARMORY_GUNS_AND_AMMO_v1.md, approved 12 Nov 22:37) as game items.

usage: gen_joe_guns.py PREVIEWS_DIR MOD_DIR

PREVIEWS_DIR  Weapons_3D_GLB_v3/previews (REGJOE's renders of the locked models, magenta background).
MOD_DIR       tools/oxce-4x/mod

Writes Ruleset/gijoe_joe_guns.rul and the pictures:
  inventory  big_<gun>.png (32x48, game palette) + big_<gun>_hi.png (128x192)
  floor      floor_<gun>.png (128x160, game palette) + floor_<gun>_rgb.png
Pictures of models whose licence is not settled (SMAW = a game rip; the low-poly M16 / AK / M4) go to
Resources/WeaponsPrivate/ (gitignored, delivered in the update zip); the rest to Resources/JoeGuns/.
In-hand pictures are STAND-INS: each gun borrows the hand sprite of the closest existing weapon.
Frag and smoke grenades already exist (STR_GRENADE / STR_SMOKE_GRENADE, Joe art): they are only put in the kit.
"""
import os, sys
from PIL import Image

PREV, MOD = sys.argv[1:3]
PRIVATE = {"bazooka", "m16", "ak47", "xm16_carbine"}
PAL = Image.open(os.path.join(MOD, "Resources/Items/big_m4.png"))

# stats from the armory doc. acc/tu pairs are accuracy% / TU%; auto = (acc, tu, shots)
G = [
 # model, name, power, dmg, snap, aimed, auto, clip, wt, (w,h), range, ammo, hand, bullet, cls
 ("m16", "M-16", 30, 1, (60,25), (110,50), (35,35,3), 20, 8, (2,3), 20, "a556", 0, 2, "rifle"),
 ("xm16_carbine", "XM-16 Attack Rifle", 28, 1, (60,24), (95,45), (35,35,3), 30, 7, (2,3), 20, "a556", 0, 2, "rifle"),
 ("ak47", "AK-47", 32, 1, (55,25), (100,50), (35,35,3), 30, 8, (2,3), 20, "a762ak", 0, 2, "rifle"),
 ("uzi", "Uzi", 22, 1, (55,22), (70,40), (40,30,3), 30, 5, (2,2), 12, "a9mm", 96, 1, "smg"),
 ("m32_pulverizer", "M-32 Pulverizer", 22, 1, (55,22), (70,40), (40,30,3), 30, 5, (2,2), 12, "a9mm", 96, 1, "smg"),
 ("xf7_wasp", "XF-7 Wasp", 22, 1, (55,22), (70,40), (40,30,3), 30, 5, (2,2), 12, "a9mm", 96, 1, "smg"),
 ("m1911_pistol", "M1911A1 Pistol", 26, 1, (60,18), (78,30), None, 7, 3, (1,2), 8, "a45", 104, 1, "pistol"),
 ("revolver", "Revolver", 34, 1, (55,22), (82,35), None, 6, 4, (1,2), 8, "a44", 104, 1, "pistol"),
 ("shotgun", "Shotgun", 48, 1, (70,25), (85,40), None, 8, 7, (2,3), 8, "a12g", 0, 1, "rifle"),
 ("m60", "M-60", 34, 1, (40,32), (70,60), (35,40,5), 100, 14, (2,3), 30, "a762belt", 24, 4, "heavy"),
 ("m2x_50cal", "M-2X .50 Cal", 52, 1, (30,40), (70,70), (30,45,5), 100, 22, (2,3), 40, "a50", 24, 4, "heavy"),
 ("bazooka", "Bazooka", 90, 3, (40,45), (100,75), None, 1, 10, (2,3), 40, "a83", 72, 0, "launcher"),
 ("mortar", "M-1 Mortar", 75, 3, None, (75,80), None, 1, 18, (2,3), 40, "a81", 72, 0, "launcher"),
 ("xk1_crossbow", "XK-1 Power Crossbow", 40, 1, (60,25), (110,45), None, 1, 5, (2,3), 20, "abolt", 0, 1, "rifle"),
 ("xmlr1a_laser_rifle", "XMLR-1A Laser Rifle", 55, 4, (65,25), (115,50), (45,35,3), 20, 9, (2,3), 30, "alaser", 0, 6, "rifle"),
 ("power_javelin", "Power Javelin", 110, 3, None, (115,80), None, 1, 14, (2,3), 40, "ajav", 72, 0, "launcher"),
 ("flare_launcher", "Rescue Flare Launcher", 10, 2, (60,20), None, None, 3, 3, (1,2), 20, "aflare", 104, 1, "pistol"),
]
MELEE = [  # model, name, power, dmg, (acc, tu), wt, (w,h), hand
 ("ninja_sword", "Ninja Sword", 55, 7, (95,25), 3, (1,3), 80),
 ("swagger_stick", "Swagger Stick", 35, 6, (95,18), 2, (1,2), 80),
]
# ammo: key, name, rounds, price, weight, fits, bigSprite (existing Joe ammo art as stand-in), dmg override
AMMO = [
 ("a556", "5.56 mm Magazine (20)", 20, 150, 1, ["m16", "xm16_carbine"], 2),
 ("a556_30", "5.56 mm Magazine (30)", 30, 180, 1, ["m16", "xm16_carbine"], 2),
 ("a762ak", "7.62 mm AK Magazine", 30, 150, 1, ["ak47"], 2),
 ("a9mm", "9 mm SMG Magazine", 30, 120, 1, ["uzi", "m32_pulverizer", "xf7_wasp"], 4),
 ("a45", ".45 Pistol Magazine", 7, 60, 1, ["m1911_pistol"], 4),
 ("a44", ".44 Speedloader", 6, 50, 1, ["revolver"], 4),
 ("a12g", "12-Gauge Shells", 8, 80, 1, ["shotgun"], 4),
 ("a762belt", "7.62 mm Belt", 100, 400, 4, ["m60"], 12),
 ("a50", ".50 Cal Ammo Box", 100, 700, 6, ["m2x_50cal"], 12),
 ("a83", "83 mm Rocket", 1, 2500, 4, ["bazooka"], 16),
 ("a81", "81 mm Mortar Bomb", 1, 800, 4, ["mortar"], 16),
 ("abolt", "XK-1 Bolt", 1, 200, 1, ["xk1_crossbow"], 4),
 ("alaser", "Laser Battery", 20, 1500, 2, ["xmlr1a_laser_rifle"], 2),
 ("ajav", "Javelin Missile", 1, 4000, 4, ["power_javelin"], 16),
 ("aflare", "Flare Cartridges", 3, 100, 1, ["flare_launcher"], 4),
]
# sounds: CAST's kit (zzz_gijoe_sounds_cast.rul, 700-765) and John's board picks (zzz_gijoe_sounds.rul, 300+N)
CAST = {n: i for i, n in enumerate(sorted([
    "ak47", "bazooka_launch", "explosion_large", "flare_launcher", "frag_grenade", "m16", "m1911_pistol", "m2x_50cal",
    "m32_pulverizer", "m60", "mortar_launch", "ninja_sword", "power_javelin_launch", "revolver", "shotgun",
    "smoke_grenade", "swagger_stick", "uzi", "xf7_wasp", "xk1_crossbow", "xm16_carbine", "xmlr1a_laser_rifle"]))}
def cast(n): b = 700 + 3 * CAST[n]; return [b, b + 1, b + 2]
FIRE = {"bazooka": "bazooka_launch", "mortar": "mortar_launch", "power_javelin": "power_javelin_launch"}
BULLET_HIT = [577, 578, 579, 574, 575]      # John's "bullet hit" picks
PULSE_HIT = [590, 591, 592]                 # John's "pulse hit" picks, used for the laser
RELOAD = [538, 540]                         # John's reload picks
RANGE_CLASS = {"rifle": 20, "smg": 12, "pistol": 8, "heavy": 30, "launcher": 40}

def keyed(name):
    im = Image.open(os.path.join(PREV, name + ".png")).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if r > 200 and b > 200 and g < 70:
                px[x, y] = (0, 0, 0, 0)
    return im.crop(im.getbbox())

def palettise(rgba):
    # the game palette's index 0 is transparent
    base = Image.new("RGB", rgba.size, (0, 0, 0))
    base.paste(rgba, (0, 0), rgba)
    q = base.quantize(palette=PAL, dither=Image.Dither.NONE)
    qp = q.load(); ap = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            if ap[x, y][3] < 128:
                qp[x, y] = 0
            elif qp[x, y] == 0:
                qp[x, y] = 1
    return q

def pictures(model, w, h, outdir, top=False):
    src = keyed(model + ("_top" if top else ""))
    # inventory: muzzle up, inside the item's w x h slots (64 px a slot at 4x)
    inv = src.rotate(-90, expand=True) if src.width > src.height else src
    bw, bh = w * 64 - 8, h * 64 - 8
    s = min(bw / inv.width, bh / inv.height)
    inv = inv.resize((max(1, int(inv.width * s)), max(1, int(inv.height * s))), Image.LANCZOS)
    hi = Image.new("RGBA", (128, 192), (0, 0, 0, 0))
    hi.paste(inv, ((w * 64 - inv.width) // 2, (h * 64 - inv.height) // 2), inv)
    lo = palettise(hi.resize((32, 48), Image.LANCZOS))
    # floor: lying on the tile, a quarter turn of the iso view, scaled to its real length
    L = max(18, min(92, int(src.width * 0.065)))
    fl = src.resize((L, max(1, int(src.height * L / src.width))), Image.LANCZOS).rotate(27, expand=True, resample=Image.BICUBIC)
    fl = fl.resize((fl.width, max(1, int(fl.height * 0.75))), Image.LANCZOS)
    fr = Image.new("RGBA", (128, 160), (0, 0, 0, 0))
    fr.paste(fl, (64 - fl.width // 2, 118 - fl.height // 2), fl)
    os.makedirs(outdir, exist_ok=True)
    hi.save(os.path.join(outdir, f"big_{model}_hi.png")); lo.save(os.path.join(outdir, f"big_{model}.png"))
    fr.save(os.path.join(outdir, f"floor_{model}_rgb.png")); palettise(fr).save(os.path.join(outdir, f"floor_{model}.png"))

def rel(model):
    return "Resources/WeaponsPrivate" if model in PRIVATE else "Resources/JoeGuns"

T = lambda m: "STR_GJ_" + m.upper()
A = lambda k: "STR_GJ_AMMO_" + k.upper()
L = ["# The 21 locked G.I. Joe guns and their ammo: generated by tools/oxce-4x/build/gen_joe_guns.py.",
     "# Stats: claude/ARMORY_GUNS_AND_AMMO_v1.md (John 12 Nov 22:37). Sounds: CAST's kit + John's sound-board picks.",
     "# Inventory and floor pictures: rendered from REGJOE's locked models. IN-HAND PICTURES ARE STAND-INS.",
     "# Category STR_JOE_KIT = what New Battle loads onto the craft.", "", "extraSprites:"]
spr = {}
idx = 300
models = [g[0] for g in G] + [m[0] for m in MELEE]
for m in models:
    w, h = next((g[9] for g in G if g[0] == m), None) or next(mm[6] for mm in MELEE if mm[0] == m)
    pictures(m, w, h, os.path.join(MOD, rel(m)), top=(m == "xk1_crossbow"))
    spr[m] = idx
    L += ["  - type: BIGOBS.PCK", "    width: 32", "    height: 48", "    files:", f"      {idx}: {rel(m)}/big_{m}.png",
          "  - type: FLOOROB.PCK", "    width: 128", "    height: 160", "    files:", f"      {idx}: {rel(m)}/floor_{m}.png"]
    idx += 1
L += ["", "items:"]
fits = {}
for a in AMMO:
    for g in a[5]: fits.setdefault(g, []).append(A(a[0]))
for (m, name, pw, dt, snap, aimed, auto, clip, wt, (w, h), rng, ammo, hand, bullet, cls) in G:
    fs = cast(FIRE.get(m, m))
    L += [f"  - type: {T(m)}", "    categories: [STR_JOE_KIT]", "    battleType: 1", f"    weight: {wt}", f"    invWidth: {w}", f"    invHeight: {h}",
          f"    bigSprite: {spr[m]}", f"    floorSprite: {spr[m]}", f"    handSprite: {hand}", f"    bulletSprite: {bullet}",
          f"    fireSound: {fs}", f"    reloadSound: {RELOAD}", f"    compatibleAmmo: {fits[m]}", f"    aimRange: {rng}", f"    snapRange: {max(5, rng // 2)}", f"    autoRange: {max(4, rng // 3)}",
          "    twoHanded: " + ("false" if cls in ("pistol", "smg") else "true"), "    costBuy: 0", "    costSell: 0", "    transferTime: 24"]
    if snap: L += [f"    accuracySnap: {snap[0]}", f"    tuSnap: {snap[1]}"]
    if aimed: L += [f"    accuracyAimed: {aimed[0]}", f"    tuAimed: {aimed[1]}"]
    if auto: L += [f"    accuracyAuto: {auto[0]}", f"    tuAuto: {auto[1]}", f"    confAuto: {{shots: {auto[2]}}}"]
    if m == "mortar": L += ["    arcingShot: true"]
for (m, name, pw, dt, (acc, tu), wt, (w, h), hand) in MELEE:
    L += [f"  - type: {T(m)}", "    categories: [STR_JOE_KIT]", "    battleType: 3", f"    weight: {wt}", f"    invWidth: {w}", f"    invHeight: {h}",
          f"    bigSprite: {spr[m]}", f"    floorSprite: {spr[m]}", f"    handSprite: {hand}", f"    power: {pw}", f"    damageType: {dt}",
          f"    accuracyMelee: {acc}", f"    tuMelee: {tu}", "    clipSize: -1", f"    meleeSound: {cast(m)}", "    costBuy: 0", "    costSell: 0", "    twoHanded: false"]
gun = {g[0]: g for g in G}
for (k, name, rounds, price, wt, fit, big) in AMMO:
    g = gun[fit[0]]
    pw, dt = g[2], g[3]
    hit = cast("explosion_large") if dt == 3 else (PULSE_HIT if dt == 4 else BULLET_HIT)
    L += [f"  - type: {A(k)}", "    categories: [STR_JOE_KIT]", "    battleType: 2", f"    clipSize: {rounds}", f"    power: {pw}", f"    damageType: {dt}",
          f"    weight: {wt}", "    invWidth: 1", "    invHeight: 1", f"    bigSprite: {big}", f"    floorSprite: {big}", f"    hitSound: {hit}",
          f"    hitAnimation: {0 if dt == 3 else (36 if dt == 4 else 26)}", f"    costBuy: {price}", f"    costSell: {price // 2}", "    transferTime: 24"]
    if dt == 3: L += [f"    blastRadius: {3 if fit[0] == 'mortar' else 1}"]
    if fit[0] == "shotgun": L += ["    powerRangeReduction: 3"]
    if fit[0] == "flare_launcher": L += ["    blastRadius: 1"]
# the two grenades and the field kit already exist with Joe art: only put them in the kit
for t in ["STR_GRENADE", "STR_SMOKE_GRENADE", "STR_MEDI_KIT", "STR_MOTION_SCANNER"]:
    L += [f"  - type: {t}", "    categories: [STR_JOE_KIT]"]
L += ["", "extraStrings:", "  - type: en-US", "    strings: &joeguns"]
L += [f'      {T(g[0])}: "{g[1]}"' for g in G] + [f'      {T(m[0])}: "{m[1]}"' for m in MELEE] + [f'      {A(a[0])}: "{a[1]}"' for a in AMMO]
L += ['      STR_JOE_KIT: "Joe kit"', "  - type: en-GB", "    strings: *joeguns"]
open(os.path.join(MOD, "Ruleset", "gijoe_joe_guns.rul"), "w").write("\n".join(L) + "\n")
print(len(G) + len(MELEE), "guns,", len(AMMO), "ammo; private pictures:", sorted(PRIVATE))
