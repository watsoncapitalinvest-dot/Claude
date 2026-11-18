#!/usr/bin/env python3
"""Battle-map vehicles from ROSTER's renders (Reference\\<name>.zip: hull + turret or whole frames, 8 headings).

usage: gen_vehicles.py PACKS_DIR MOD_DIR

PACKS_DIR holds each pack unzipped as PACKS_DIR/<pack>/<asset>/ (manifest.json, hull/, turret/, whole/).
Writes, per vehicle, a unit sheet for drawing routine 23 (UnitSprite::drawRoutineWhole):
  1x1: 2048x5120, 128x160 cells, frame = clip*64 + heading*8 + f (clips 0-3 standing, 4 death)
  2x2: 2048x2880, 256x320 cells, 8 a row: 0-7 headings, then 8 + heading*8 + f death
  NxN (3-5): N*128 x N*160 cells, 4 a row: 0-7 headings, 8-15 one death sequence
  The render's anchor (the footprint's middle, 16 px above the floor, the vessels' convention) goes to
  (cell width / 2, 112 * N), where the engine centres a big unit over its footprint.
Plus an inventory picture (big_<v>.png + _hi) and gijoe_vehicles.rul (units, armours, HWP items, ammo).
ROSTER marks every pack PRIVATE: the pictures go to Resources/VehiclesPrivate (gitignored, update zip only).
The turret is drawn turned with the hull (one picture per heading); a turret aiming on its own is phase 2.
"""
import glob, json, os, sys
import numpy as np
from PIL import Image, ImageEnhance

PACKS, MOD = sys.argv[1:3]
OUT = os.path.join(MOD, "Resources", "VehiclesPrivate")
PAL = Image.open(os.path.join(MOD, "Resources", "Units", "hawk_body.png")).getpalette()
HEAD = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# name: (pack, asset, state for whole frames, side, numbers...)
# side: joe = buyable HWP; cobra = New Battle only (needs STR_NEW_BATTLE_ONLY)
# stats: tu, hp, (front, side, rear, under); weapon: (name, power, damage type, clip, snap(acc,tu), aimed, auto(acc,tu,shots), blast, bullet sprite, sound key)
V = {
 "vamp":      dict(pack="vamp", asset="vamp", state="m0", side="joe", name="VAMP (guns)", tu=80, hp=45, arm=(30, 25, 20, 15),
                  wpn=("Twin machine gun", 30, 1, 100, (50, 25), (75, 45), (40, 35, 4), 0, 2, "m60"), price=100000),
 "vamp_mk2":  dict(pack="vamp_mk2", asset="vamp_mk2", state="m4", side="joe", name="VAMP Mk II (rockets)", tu=70, hp=55, arm=(45, 35, 30, 20),
                  stores=["m3", "m2", "m1", "m0"], store_weapon="self", head="proj_vamp_mk2_head0",
                  wpn=("Rocket pod", 90, 3, 4, None, (85, 50), None, 1, 0, "bazooka_launch"), price=160000),
 "triple_t":  dict(pack="triple_t", asset="triple_t", state="m2", side="joe", stores=["m1", "m0"], store_weapon="self", head="proj_triple_t_head0", name="Triple T", tu=64, hp=80, arm=(70, 55, 45, 40),
                  wpn=("Side-pod missiles", 100, 3, 2, None, (85, 50), None, 2, 0, "power_javelin_launch"), price=250000),
 "mobat":     dict(pack="mobat", asset="mobat", state="m0", side="joe", name="MOBAT", tu=56, hp=120, arm=(90, 75, 60, 60),
                  wpn=("Main gun", 90, 1, 20, (55, 33), (85, 70), None, 0, 4, "m2x_50cal"), price=420000,
                  turret_tu=3, cupola_weapon="STR_GJA_JOE_M_O_B_A_T_MACHINE_GUN_W", cupola_tu=1),   # John 22:01: the M2 cupola turns on its own, faster (180 = 4 TU; the turret 12)
 "wolverine": dict(pack="wolverine", asset="wolverine", state="m0", side="joe", name="Wolverine", tu=60, hp=100, arm=(80, 65, 50, 50),
                  wpn=("Missile rack", 80, 3, 6, None, (85, 55), None, 1, 0, "power_javelin_launch"), price=380000, head="proj_wolverine_head0", turret_stores=12, turret_tu=3),  # its own missile flies full size (John 20:10 "can i see it shoot")
 "mauler":    dict(pack="mauler", asset="mauler", state="m0", side="joe", name="Mauler M.B.T.", tu=50, hp=200, arm=(120, 100, 80, 80),
                  wpn=("Main gun", 110, 1, 20, (50, 35), (80, 70), None, 0, 4, "m2x_50cal"), price=600000, turret_tu=3),
 "stinger":   dict(pack="stinger", asset="stinger", state="m0", side="cobra", name="Cobra Stinger", tu=72, hp=50, arm=(35, 25, 20, 15),
                  wpn=("Ground-to-air rockets", 80, 3, 3, None, (80, 55), None, 1, 0, "bazooka_launch"), price=0, head="proj_stinger_head0", turret_tu=3),  # file card (John 18:37 rework); was "Quad cannon". 3 rockets on the rack; stand-in numbers
 "hiss":      dict(pack="hiss", asset="hiss", state="m0", side="cobra", name="Cobra H.I.S.S.", tu=60, hp=110, arm=(85, 70, 55, 55),
                  wpn=("Twin 30mm automatic cannons", 60, 1, 40, (50, 30), (80, 55), (40, 40, 2), 0, 4, "m2x_50cal"), price=0, head="proj_thunder_round_head0", turret_tu=3),  # blueprint name (John 18:29 rework); same 30mm round as the Thunder Machine
 "hiss_rack": dict(pack="hiss_rack", asset="hiss_rack", state="m0", side="cobra", name="Cobra H.I.S.S. (rocket rack)", tu=60, hp=110, arm=(85, 70, 55, 55),
                  wpn=("H.I.S.S. rocket rack", 90, 3, 4, None, (80, 55), None, 1, 0, "bazooka_launch"), price=0, head="proj_hiss_rack_head0", turret_tu=3),  # Cobra research upgrade (John 18:41); research gate + deployment are STORY/BUILD's; stand-in numbers
 "ferret":    dict(pack="ferret", asset="ferret", state="m2", side="cobra", stores=["m1", "m0"], store_weapon="self", head="proj_ferret_head0",   # Com-Bats leave the pegs (John 23:17)
                  deploy=["dL1", "dL2", "dR1", "dR2"],   # John 23:28: rams push each Com-Bat out from between the wheels, then it fires
                  # where each shot leaves (voxels: forward, left, up from the footprint middle; model units x 1.564 / 1.915, checked against
                  # the rendered muzzles at all 8 headings): the Com-Bats off their rams (left first), the CMF-1 tube, the .50s
                  launch={"self": [[4, 9, 4], [4, -9, 4]], "STR_GJA_COBRA_FERRET_A_T_V_CMF_1_W": [[9, -6, 14]],
                          "STR_GJA_COBRA_FERRET_A_T_V_50_CAL_MACHINE_GUNS_W": [[13, -1, 11], [13, 1, 11]]},   # John 18 Nov 00:02: the twin .50s are the front gun (x 8.0, y +-0.35, z 5.64), barrels alternating
                  name="Cobra Ferret", tu=80, hp=30, arm=(20, 15, 10, 10),
                  wpn=("Machine gun", 30, 1, 60, (50, 25), None, (35, 35, 3), 0, 2, "m60"), price=0),
 "thunder":   dict(pack="thunder_machine", asset="thunder_machine", state="m0", head="proj_thunder_round_head0", side="cobra", name="Dreadnok Thunder Machine", tu=54, hp=110, arm=(70, 60, 50, 40),
                  wpn=("Penetrator Gatling cannons (30mm)", 45, 1, 120, (45, 30), None, (35, 40, 5), 0, 4, "m60"), price=0),  # John 17:36: the twin Gatlings (VFACTORY stand-in numbers for STORY); was a "Rocket rack" firing from the jet exhausts # Thunderclap tractor + trailer (VFACTORY, 17 Nov 2026; John's TechnoViper3D kit, 3x3 each). Canon weapon names from the kit blueprint.
 # Numbers are VFACTORY stand-ins scaled off the Mauler/MOBAT until STORY sets them; the ZPJ-79 copies STORY's arsenal item (power 110, 3, blast 2).
 "thunderclap_tractor": dict(pack="thunderclap_tractor", asset="thunderclap_tractor", state="m0", side="joe", name="Thunderclap Tractor", tu=50, hp=170, arm=(100, 80, 60, 60),
                  wpn=("MG-999 dual-barrelled pulsating assault weapon", 60, 1, 60, (50, 30), (80, 55), (40, 40, 3), 0, 12, "m2x_50cal"),
                  wpn2=("Low attack missile", 100, 3, 3, None, (85, 55), None, 2, 22, "power_javelin_launch"), price=520000,
                  stores=["m1", "m2", "m3"], proj="proj_thunderclap", head="proj_thunderclap_head0", turret_tu=3),
 "thunderclap_trailer": dict(pack="thunderclap_trailer", asset="thunderclap_trailer", state="m0", side="joe", name="Thunderclap Trailer", tu=46, hp=150, arm=(90, 75, 60, 55),
                  wpn=("Rapid-fire blaster cannon", 75, 1, 40, (55, 30), (85, 55), (40, 40, 2), 0, 12, "m2x_50cal"),
                  wpn2=("ZPJ-79 cruise missile", 110, 3, 3, None, (90, 60), None, 2, 24, "power_javelin_launch"), price=480000,
                  stores=["m1", "m2", "m3"], proj="proj_thunderclap", head="proj_thunderclap_head1", turret_tu=3),
}

CAST = sorted(["ak47", "bazooka_launch", "explosion_large", "flare_launcher", "frag_grenade", "m16", "m1911_pistol", "m2x_50cal",
    "m32_pulverizer", "m60", "mortar_launch", "ninja_sword", "power_javelin_launch", "revolver", "shotgun",
    "smoke_grenade", "swagger_stick", "uzi", "xf7_wasp", "xk1_crossbow", "xm16_carbine", "xmlr1a_laser_rifle"])
def cast(n): b = 700 + 3 * CAST.index(n); return [b, b + 1, b + 2]

def quantize(rgba):
    a = np.array(rgba).astype(np.int32)
    out = np.zeros(a.shape[:2], np.uint8)
    m = a[..., 3] > 127
    P = np.array(PAL, np.int32).reshape(-1, 3)[1:255]
    f = a[..., :3][m]
    idx = np.empty(len(f), np.int64)
    for i in range(0, len(f), 20000):
        ch = f[i:i + 20000]
        idx[i:i + 20000] = ((ch[:, None, :] - P[None]) ** 2).sum(-1).argmin(1) + 1
    out[m] = idx
    im = Image.fromarray(out, "P"); im.putpalette(PAL)
    return im

def frame(base, man, look, h, state, turret=True):
    """the full picture of the vehicle at heading h (turret=False: the hull alone)"""
    if os.path.isdir(os.path.join(base, "hull")):
        hull = Image.open(os.path.join(base, "hull", f"{man['asset']}_hull_{look}_{h}.png")).convert("RGBA")
        entry = next(e for e in man["hull"] if e["look"] == look and e["heading"] == h)
        tp = os.path.join(base, "turret", f"{man['asset']}_turret_{look}_f0_{h}.png")
        if turret and os.path.exists(tp):
            tur = Image.open(tp).convert("RGBA")
            ox, oy = entry.get("turret_paste_offset", [0, 0])
            hull.alpha_composite(tur, (int(ox), int(oy)))
        return hull
    pat = f"{man['asset']}_{look}_{state}_{h}.png" if state else f"{man['asset']}_{look}_{h}.png"
    pic = Image.open(os.path.join(base, "whole", pat)).convert("RGBA")
    if turret and man.get("turret"):               # gen/ packages (VFACTORY, ROSTER's gen chain): body frames + a turret layer at the frame's paste offset
        e = next(x for x in man["frames"] if x["look"] == look and x["heading"] == h and x.get("state") == state)
        tur = Image.open(os.path.join(base, "turret", f"{man['asset']}_turret_{look}_{h}.png")).convert("RGBA")
        ox, oy = e.get("turret_paste_offset", [0, 0]); pic.alpha_composite(tur, (int(ox), int(oy)))
        if man.get("cupola"):                      # the cupola on the turret, both at this heading (VFACTORY cupola.py)
            cu = Image.open(os.path.join(base, "cupola", f"{man['asset']}_cupola_{look}_{h}.png")).convert("RGBA")
            cx, cy = man["cupola"]["offset_in_turret"][h]; pic.alpha_composite(cu, (int(ox + cx), int(oy + cy)))
    return pic

def cellOf(pic, anchor, n, dy=0, dark=1.0, alpha=1.0):
    W, H = 128 * n, 160 * n
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if dark != 1.0: pic = ImageEnhance.Brightness(pic).enhance(dark)
    if alpha != 1.0:
        a = np.array(pic); a[..., 3] = (a[..., 3] * alpha).astype(np.uint8); pic = Image.fromarray(a, "RGBA")
    x, y = W // 2 - anchor[0], 112 * n - anchor[1] + dy               # a render frame bigger than the cell (a tall model rendered in a
    l, t = max(0, -x), max(0, -y)                                       # bigger FOOT frame) is cropped to the cell
    pic = pic.crop((l, t, min(pic.width, W - x), min(pic.height, H - y)))
    c.alpha_composite(pic, (x + l, y + t))
    return c

def sheet(v, d):
    base = glob.glob(os.path.join(PACKS, d["pack"], "*", "manifest.json"))[0]
    root = os.path.dirname(base); man = json.load(open(base))
    n = max(man["footprint"]); anchor = man["anchor"]          # non-square classes go in as their enclosing square (BUILD-1 16:35)
    clean = [frame(root, man, "clean", h, d["state"]) for h in HEAD]
    # a turret that turns on its own (2x2 and up): the standing frames are the hull alone, and the turret is its
    # own sheet, frames 0-7 its headings, placed like the hull; the engine moves it by the hull's paste offset
    turret = None
    gen_pkg = bool(man.get("turret")) and not os.path.isdir(os.path.join(root, "hull"))
    if n >= 2 and os.path.isdir(os.path.join(root, "turret")) and (os.path.isdir(os.path.join(root, "hull")) or gen_pkg):
        hull_only = [frame(root, man, "clean", h, d["state"], turret=False) for h in HEAD]
        tname = "{a}_turret_clean_{h}.png" if gen_pkg else "{a}_turret_clean_f0_{h}.png"
        tur = [Image.open(os.path.join(root, "turret", tname.format(a=man["asset"], h=h))).convert("RGBA") for h in HEAD]
        offs = []
        for h in HEAD:
            e = next(x for x in (man["frames"] if gen_pkg else man["hull"]) if x["look"] == "clean" and x["heading"] == h and (not gen_pkg or x.get("state") == d["state"]))
            ox, oy = e.get("turret_paste_offset", [0, 0])
            offs.append([int(round(ox / 4)), int(round(oy / 4))])
        W, H = 128 * n, 160 * n
        per = 8 if n == 2 else 4
        ts_n = d.get("turret_stores", 0)            # missiles on the turret leave it one by one (engine: frame 8 + (fired - 1) * 8 + turret heading)
        cupola = bool(man.get("cupola"))
        assert not (cupola and ts_n), "a cupola vehicle's turret frames 8-15 are the turret without it: no turret stores as well"
        TS = Image.new("RGBA", (per * W, ((8 + 8 * (ts_n or cupola)) // per) * H), (0, 0, 0, 0))
        for hd, h in enumerate(HEAD):
            if cupola:                              # 0-7 the cupola fixed on the turret (an exe without the cupola code), 8-15 the turret alone
                fixed = tur[hd].copy(); cu = Image.open(os.path.join(root, "cupola", f"{man['asset']}_cupola_clean_{h}.png")).convert("RGBA")
                cx, cy = man["cupola"]["offset_in_turret"][h]; fixed.alpha_composite(cu, (int(cx), int(cy)))
                TS.alpha_composite(cellOf(fixed, anchor, n), ((hd % per) * W, (hd // per) * H))
                TS.alpha_composite(cellOf(tur[hd], anchor, n), (((8 + hd) % per) * W, ((8 + hd) // per) * H))
            else:
                TS.alpha_composite(cellOf(tur[hd], anchor, n), ((hd % per) * W, (hd // per) * H))
        for k in range(1, ts_n + 1):
            for hd, h in enumerate(HEAD):
                fr = 8 + (k - 1) * 8 + hd
                im = Image.open(os.path.join(root, "turret", f"{man['asset']}_turret_clean_s{k}_{h}.png")).convert("RGBA")
                TS.alpha_composite(cellOf(im, anchor, n), ((fr % per) * W, (fr // per) * H))
        os.makedirs(OUT, exist_ok=True)
        TS.save(os.path.join(OUT, f"veh_{v}_turret_rgb.png")); quantize(TS).save(os.path.join(OUT, f"veh_{v}_turret.png"))
        cup = None
        if man.get("cupola"):                       # a second turret riding on the turret, its own heading (VFACTORY cupola.py; John 17 Nov 22:01)
            CS = Image.new("RGBA", (per * W, (8 // per) * H), (0, 0, 0, 0))
            for hd, h in enumerate(HEAD):
                im = Image.open(os.path.join(root, "cupola", f"{man['asset']}_cupola_clean_{h}.png")).convert("RGBA")
                CS.alpha_composite(cellOf(im, anchor, n), ((hd % per) * W, (hd // per) * H))
            CS.save(os.path.join(OUT, f"veh_{v}_cupola_rgb.png")); quantize(CS).save(os.path.join(OUT, f"veh_{v}_cupola.png"))
            co = man["cupola"]["offset_in_turret"]; cup = (CS.size, [[int(round(co[h][0] / 4)), int(round(co[h][1] / 4))] for h in HEAD])
        turret = (TS.size, offs, cup)
        standing = hull_only
    else:
        standing = clean
    try: dmg = [frame(root, man, "damaged", h, d["state"]) for h in HEAD]
    except Exception: dmg = clean
    if n == 1:
        S = Image.new("RGBA", (2048, 5120), (0, 0, 0, 0))
        for hd in range(8):
            for clip in range(5):
                for f in range(8):
                    c = cellOf(dmg[hd], anchor, 1, dy=f * 2, dark=1 - f * 0.08, alpha=1 - f * 0.1) if clip == 4 else cellOf(clean[hd], anchor, 1)
                    fr = clip * 64 + hd * 8 + f
                    S.alpha_composite(c, ((fr % 16) * 128, (fr // 16) * 160))
    elif n == 2:
        ns = len(d.get("stores", []) + d.get("deploy", []))
        S = Image.new("RGBA", (2048, (9 + ns) * 320), (0, 0, 0, 0))
        for hd in range(8):
            S.alpha_composite(cellOf(standing[hd], anchor, 2), ((hd % 8) * 256, (hd // 8) * 320))
            for f in range(8):
                fr = 8 + hd * 8 + f
                S.alpha_composite(cellOf(dmg[hd], anchor, 2, dy=f * 3, dark=1 - f * 0.08, alpha=1 - f * 0.1), ((fr % 8) * 256, (fr // 8) * 320))
        # stores on the hull, 2x2 sheets (engine gjStoreStates, N == 2): frame 72 + (fired - 1) * 8 + heading, after the 64 death frames
        # (Cobra Ferret's Com-Bats, John 17 Nov 23:17 "they should shoot off the vehicle"); then the deploy frames (gjStoreDeploy,
        # John 23:28 "actuators push them out ... and then they fire"): 72 + stores * 8 + (fired * steps + step) * 8 + heading
        for k, st in enumerate(d.get("stores", []) + d.get("deploy", [])):
            for hd, h in enumerate(HEAD):
                fr = 72 + k * 8 + hd
                S.alpha_composite(cellOf(frame(root, man, "clean", h, st, turret=turret is None), anchor, 2), ((fr % 8) * 256, (fr // 8) * 320))
    else:
        W, H = 128 * n, 160 * n
        ns = len(d.get("stores", []) + d.get("deploy", []))
        S = Image.new("RGBA", (4 * W, (4 + 2 * ns) * H), (0, 0, 0, 0))
        for hd in range(8):
            S.alpha_composite(cellOf(standing[hd], anchor, n), ((hd % 4) * W, (hd // 4) * H))
        for f in range(8):
            fr = 8 + f
            S.alpha_composite(cellOf(dmg[2], anchor, n, dy=f * 2 * n, dark=1 - f * 0.08, alpha=1 - f * 0.1), ((fr % 4) * W, (fr // 4) * H))
        # stores on the hull (engine gjStoreStates): frame 16 + (fired - 1) * 8 + heading = the picture with that many gone
        for k, st in enumerate(d.get("stores", []) + d.get("deploy", [])):
            for hd, h in enumerate(HEAD):
                fr = 16 + k * 8 + hd
                S.alpha_composite(cellOf(frame(root, man, "clean", h, st, turret=turret is None), anchor, n), ((fr % 4) * W, (fr // 4) * H))
    os.makedirs(OUT, exist_ok=True)
    S.save(os.path.join(OUT, f"veh_{v}_body_rgb.png"))
    quantize(S).save(os.path.join(OUT, f"veh_{v}_body.png"))
    # inventory picture: the SW heading fitted to the 2x3 box
    pic = clean[5].crop(clean[5].getbbox())
    k = min(120 / pic.width, 184 / pic.height)
    pic = pic.resize((max(1, int(pic.width * k)), max(1, int(pic.height * k))), Image.LANCZOS)
    hi = Image.new("RGBA", (128, 192), (0, 0, 0, 0)); hi.alpha_composite(pic, ((128 - pic.width) // 2, (192 - pic.height) // 2))
    hi.save(os.path.join(OUT, f"big_{v}_hi.png")); quantize(hi.resize((32, 48), Image.LANCZOS)).save(os.path.join(OUT, f"big_{v}.png"))
    return n, S.size, turret

L = ["# Battle-map vehicles: generated by tools/oxce-4x/build/gen_vehicles.py from ROSTER's renders.",
     "# Numbers: VAMP (VAMP_STATS_v1), Triple T (TRIPLE_T_STATS_v1); the rest are BUILD's stand-ins scaled off the stock tank",
     "# (TU 70, HP 90, armour 90/75/60/60) until STORY sets them. One weapon each (the Triple T's MGs are not in yet), except a wpn2 entry:",
     "# a second built-in weapon (Thunderclap missiles). Thunderclap numbers are VFACTORY stand-ins.",
     "# Cobra's are New Battle only (STR_NEW_BATTLE_ONLY). Pictures: Resources/VehiclesPrivate (private, update zip only).",
     "", "extraSprites:"]
U, A, I, S2 = ["units:"], ["armors:"], ["items:"], {}
# ONLY=a,b: redraw only those vehicles' pictures; the rest keep the sheets already in VehiclesPrivate (on John's PC) and their
# sizes / turret offsets are read back from the current gijoe_vehicles.rul (the Reference zips have moved on since some were installed)
ONLY = [x for x in os.environ.get("ONLY", "").split(",") if x]
def previous(v):
    import yaml
    r = yaml.safe_load(open(os.path.join(MOD, "Ruleset", "gijoe_vehicles.rul")))
    sp = {e["type"]: e for e in r["extraSprites"]}; ar = {e["type"]: e for e in r["armors"]}[f"GJ_VEH_{v.upper()}_ARMOR"]
    b = sp[f"VEH_{v.upper()}.PCK"]; t = sp.get(f"VEH_{v.upper()}_TURRET.PCK"); c = sp.get(f"VEH_{v.upper()}_CUPOLA.PCK")
    cup = ((c["width"], c["height"]), ar["gjCupolaOffsets"]) if c else None
    return ar["size"], (b["width"], b["height"]), ((t["width"], t["height"]), ar["gjTurretOffsets"], cup) if t else None
for i, (v, d) in enumerate(V.items()):
    n, size, turret = sheet(v, d) if not ONLY or v in ONLY else previous(v)
    W, H = 128 * n, 160 * n
    L += [f"  - type: VEH_{v.upper()}.PCK", f"    width: {size[0]}", f"    height: {size[1]}", f"    subX: {W}", f"    subY: {H}",
          "    files:", f"      0: Resources/VehiclesPrivate/veh_{v}_body.png",
          "  - type: BIGOBS.PCK", "    width: 32", "    height: 48", "    files:", f"      {340 + i}: Resources/VehiclesPrivate/big_{v}.png"]
    if turret:
        L += [f"  - type: VEH_{v.upper()}_TURRET.PCK", f"    width: {turret[0][0]}", f"    height: {turret[0][1]}", f"    subX: {W}", f"    subY: {H}",
              "    files:", f"      0: Resources/VehiclesPrivate/veh_{v}_turret.png"]
        if turret[2]:
            L += [f"  - type: VEH_{v.upper()}_CUPOLA.PCK", f"    width: {turret[2][0][0]}", f"    height: {turret[2][0][1]}", f"    subX: {W}", f"    subY: {H}",
                  "    files:", f"      0: Resources/VehiclesPrivate/veh_{v}_cupola.png"]
    T = f"STR_GJ_VEH_{v.upper()}"
    a = d["arm"]
    A += [f"  - type: GJ_VEH_{v.upper()}_ARMOR", f"    spriteSheet: VEH_{v.upper()}.PCK", "    drawingRoutine: 23", "    deathFrames: 8",
          f"    size: {n}", f"    frontArmor: {a[0]}", f"    sideArmor: {a[1]}", f"    rearArmor: {a[2]}", f"    underArmor: {a[3]}",
          "    allowInv: false", "    allowsKneeling: false", "    allowsRunning: false",
          f"    corpseBattle: [{', '.join(['STR_AF_WRECK'] * (n * n))}]", f"    loftempsSet: [{', '.join(['3'] * (n * n))}]",
          "    damageModifier: [1.0, 1.0, 0.4, 0.75, 1.0, 1.0, 1.0, 1.0]"]
    if d.get("wpn2"):                                # a second built-in weapon (missiles beside the gun), its own item + ammo
        A += [f"    builtInWeapons: [{T}_W2, {T}_A2]"]
    if d.get("stores"):                              # the missiles leave the hull picture one by one as the _W2 weapon fires (engine, VFACTORY)
        A += [f"    gjStoreWeapon: {T if d.get('store_weapon') == 'self' else T + '_W2'}", f"    gjStoreStates: {len(d['stores'])}"]
        if d.get("deploy"):                          # pushed out on its arm before it fires (engine, VFACTORY; John 17 Nov 23:28)
            A += [f"    gjStoreDeploy: {len(d['deploy']) // len(d['stores'])}"]
    if d.get("launch"):                              # where each weapon's shot leaves the vehicle (engine gjLaunchPoints; John 17 Nov 23:24)
        A += ["    gjLaunchPoints:"] + [f"      {w if w.startswith('STR_') else T}: [" + ", ".join(f"[{p[0]}, {p[1]}, {p[2]}]" for p in pts) + "]" for w, pts in d["launch"].items()]
    elif d.get("turret_stores"):                     # the same, for missiles carried on the turret (Wolverine; John 17 Nov 20:21)
        A += [f"    gjStoreWeapon: {T}", f"    gjStoreStates: {d['turret_stores']}"]
    if turret:
        A += [f"    gjTurretSheet: VEH_{v.upper()}_TURRET.PCK", "    gjTurretOffsets: [" + ", ".join(f"[{o[0]}, {o[1]}]" for o in turret[1]) + "]"]
        # turn costs (John 15 Nov 15:08, 17 Nov 22:01: a machine gun turns faster, for fewer TU, than a cannon or missile turret):
        # TU per 45 degree step; stock OpenXcom charges 1 for any turret
        if d.get("turret_tu"): A += [f"    gjTurretTurnTU: {d['turret_tu']}"]
        if turret[2]:
            A += [f"    gjCupolaSheet: VEH_{v.upper()}_CUPOLA.PCK", "    gjCupolaOffsets: [" + ", ".join(f"[{o[0]}, {o[1]}]" for o in turret[2][1]) + "]",
                  f"    gjCupolaWeapon: {d['cupola_weapon']}", f"    gjCupolaTurnTU: {d.get('cupola_tu', 1)}"]
    U += [f"  - type: {T}", f"    race: {T}", f"    armor: GJ_VEH_{v.upper()}_ARMOR",
          f"    stats: {{tu: {d['tu']}, stamina: 100, health: {d['hp']}, bravery: 110, reactions: 30, firing: 65, throwing: 0, strength: 100, psiStrength: 100, psiSkill: 0, melee: 0}}",
          "    standHeight: 16", "    kneelHeight: 16", "    value: 20", "    deathSound: 23", "    moveSound: 14", "    energyRecovery: 50"]
    wn, pw, dt, clip, snap, aimed, auto, blast, bullet, snd = d["wpn"]
    ammo = f"{T}_AMMO"
    I += [f"  - type: {T}", "    categories: [STR_JOE_KIT]" if d["side"] == "joe" else "    categories: [STR_JOE_KIT]",
          "    battleType: 1", "    fixedWeapon: true", f"    invWidth: 2", "    invHeight: 3", "    weight: 1", f"    size: {2 * n}",
          f"    bigSprite: {340 + i}", "    floorSprite: 0", "    handSprite: 0", f"    bulletSprite: {bullet}", f"    fireSound: {cast(snd)}",
          f"    compatibleAmmo: [{ammo}]", "    turretType: 0", f"    costBuy: {d['price']}", f"    costSell: {d['price'] // 2}", "    transferTime: 96"]
    if d["side"] == "cobra": I += ["    requires: [STR_NEW_BATTLE_ONLY]", "    requiresBuy: [STR_NEW_BATTLE_ONLY]"]
    if d.get("head") and not d.get("wpn2"): I += [f"    gjBulletHeadSheet: GJ_HEAD_{v.upper()}.PCK", "    bulletDirectional: true"]   # the hook only draws directional shots   # the main weapon's own full-size shot
    if snap: I += [f"    accuracySnap: {snap[0]}", f"    tuSnap: {snap[1]}"]
    if aimed: I += [f"    accuracyAimed: {aimed[0]}", f"    tuAimed: {aimed[1]}"]
    if auto: I += [f"    accuracyAuto: {auto[0]}", f"    tuAuto: {auto[1]}", f"    confAuto: {{shots: {auto[2]}}}"]
    hit = cast("explosion_large") if dt == 3 else [577, 578, 579, 574, 575]
    I += [f"  - type: {ammo}", "    battleType: 2", f"    clipSize: {clip}", f"    power: {pw}", f"    damageType: {dt}", "    weight: 1",
          "    invWidth: 1", "    invHeight: 1", "    bigSprite: 16" if dt == 3 else "    bigSprite: 12", "    floorSprite: 16" if dt == 3 else "    floorSprite: 12",
          f"    hitSound: {hit}", f"    hitAnimation: {0 if dt == 3 else 26}", f"    costBuy: {2000 if dt == 3 else 400}", "    transferTime: 24"]
    if blast: I += [f"    blastRadius: {blast}"]
    if d.get("head") and not d.get("wpn2"): I += [f"    gjBulletHeadSheet: GJ_HEAD_{v.upper()}.PCK", "    bulletDirectional: true"]   # the hook only draws directional shots
    if d["side"] == "cobra": I += ["    requires: [STR_NEW_BATTLE_ONLY]", "    requiresBuy: [STR_NEW_BATTLE_ONLY]"]
    S2[T] = d["name"]; S2[ammo] = f"{d['name']}: {' '.join(w if any(c.isdigit() for c in w) or w[1:] != w[1:].lower() else w.lower() for w in wn.split())} ammo"
    if d.get("wpn2"):
        wn2, pw2, dt2, clip2, snap2, aimed2, auto2, blast2, bullet2, snd2 = d["wpn2"]
        I += [f"  - type: {T}_W2", "    battleType: 1", "    fixedWeapon: true", "    invWidth: 1", "    invHeight: 1", "    weight: 1",
              "    bigSprite: 16", "    floorSprite: 0", "    handSprite: 0", f"    bulletSprite: {bullet2}", f"    fireSound: {cast(snd2)}", f"    compatibleAmmo: [{T}_A2]",
              "    arcingShot: false"] + (["    bulletDirectional: true"] if bullet2 >= 18 else []) + ([f"    gjBulletHeadSheet: GJ_HEAD_{v.upper()}.PCK"] if d.get("head") else [])
        if snap2: I += [f"    accuracySnap: {snap2[0]}", f"    tuSnap: {snap2[1]}"]
        if aimed2: I += [f"    accuracyAimed: {aimed2[0]}", f"    tuAimed: {aimed2[1]}"]
        if auto2: I += [f"    accuracyAuto: {auto2[0]}", f"    tuAuto: {auto2[1]}", f"    confAuto: {{shots: {auto2[2]}}}"]
        hit2 = cast("explosion_large") if dt2 == 3 else [577, 578, 579, 574, 575]
        I += [f"  - type: {T}_A2", "    battleType: 2", f"    clipSize: {clip2}", f"    power: {pw2}", f"    damageType: {dt2}", "    weight: 1", "    invWidth: 1", "    invHeight: 1",
              "    bigSprite: 16", "    floorSprite: 16", f"    bulletSprite: {bullet2}", f"    hitSound: {hit2}", f"    hitAnimation: {0 if dt2 == 3 else 26}", "    transferTime: 24"] + (["    bulletDirectional: true"] if bullet2 >= 18 else []) + ([f"    gjBulletHeadSheet: GJ_HEAD_{v.upper()}.PCK"] if d.get("head") else [])
        if blast2: I += [f"    blastRadius: {blast2}"]
        S2[f"{T}_W2"] = wn2; S2[f"{T}_A2"] = wn2
    print(v, f"{n}x{n}", size)
PROJ = sorted({d["proj"] for d in V.values() if d.get("proj")})
for pj in PROJ:                                      # VFACTORY's own projectile rows from 22 (missile_heads.py): trail + 8 directional heads per missile
    L += ["  - type: Projectiles", "    width: 1680", f"    height: {Image.open(os.path.join(OUT, pj + '.png')).height}", "    subX: 48", "    subY: 48",
          "    files:", f"      {22 * 35}: Resources/VehiclesPrivate/{pj}.png"]
for v, d in V.items():                               # full-size missile heads (engine gjBulletHeadSheet): frames 0-7 by screen direction
    if d.get("head"):
        hs = Image.open(os.path.join(OUT, d["head"] + ".png")).height       # square frames, 128 or bigger for a long missile
        L += [f"  - type: GJ_HEAD_{v.upper()}.PCK", f"    width: {8 * hs}", f"    height: {hs}", f"    subX: {hs}", f"    subY: {hs}",
              "    files:", f"      0: Resources/VehiclesPrivate/{d['head']}.png"]
L += [""] + U + [""] + A + [""] + I + ["", "extraStrings:", "  - type: en-US", "    strings: &veh"] + [f'      {k}: "{s}"' for k, s in S2.items()] + ["  - type: en-GB", "    strings: *veh"]
open(os.path.join(MOD, "Ruleset", "gijoe_vehicles.rul"), "w").write("\n".join(L) + "\n")
