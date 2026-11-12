#!/usr/bin/env python3
"""Stock the empty room shells with the room objects, for the base view.

    python3 build/install_stocked_rooms.py --ufo <dir holding GEODATA/ and GEOGRAPH/> [--write] [--sheet OUT.png]

Without --write it lays every room out and reports, and writes nothing into mod/.

WHAT IT MAKES, per room that has a shell (only the Pit's four sizes exist, so only
theme `joe` rooms) and a harvested plan:
  mod/Resources/Base/facilities/<room>_<i>_hi.png   192x192 RGBA, one per grid square,
      the shell with its objects on it. The engine registers it as the sharp twin of
      BASEBITS frame <room>_<i>.png, and the base view draws it in place of the bare shell.
  mod/Resources/Base/facilities/<room>_<i>.png      the 8-bit frame, rebuilt from the same
      picture (area-reduced to 32 px, snapped to the palette-1 indices vanilla's own
      facility frames use) so the two agree.
  mod/Ruleset/gijoe_stocked_rooms.rul               points the vanilla facilities the mod
      renames (Barracks, Detention Block, ...) at those frames. Art only: no cost, time or
      capacity is touched.

WHERE THINGS GO comes from build/room_placements.json - the generator's own prop placements
(harvest_placements.py), 10 tiles to a grid square. Each harvested prop is mapped to an object
(PROP / ROOM_PROP below); a prop with no object leaves the floor bare and is listed as a gap.
Nothing is a stand-in: a prop only maps to an object that IS that thing.

The objects keep their drawn size - the footprint in the requisition, in shell pixels, 192 to
a grid square - and that is about 2.7 times what the generator gave the same prop against its
floor. So the plan cannot be copied one for one. Each object is put where its prop was (snapped
to the wall its prop stood against, turned so its front faces into the room) and, if that spot
is taken, walled, or in front of a door, slid to the nearest free spot within reach; if there is
none it is left out. Signature pieces (the room's own objects, biggest first) go down before the
common kit, so what gets left out is the small, generic stuff. Small clutter under SMALLEST px
is never placed: at the base view's real size it is noise.

Refuses, and writes nothing, when: an input file is missing, an object's canvas is not its
footprint x4 (x8 when under 32 px), a shell is not 192 px a square, a harvested room's size
disagrees with baseview_frames.json, or a mapped object does not exist.
"""
import argparse
import json
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
BASE = os.path.join(ROOT, 'mod', 'Resources', 'Base')
OBJ = os.path.join(BASE, 'objects')
SHELLS = os.path.join(BASE, 'shells')
FAC = os.path.join(BASE, 'facilities')
RUL = os.path.join(ROOT, 'mod', 'Ruleset', 'gijoe_stocked_rooms.rul')
PLACE = os.path.join(HERE, 'room_placements.json')
FRAMES = os.path.join(HERE, 'baseview_frames.json')
SQ = 192            # shell px per grid square
PX = 32             # 8-bit frame px per grid square
SMALLEST = 15       # objects whose long side is under this (shell px) are not placed
GAP = 3             # px kept clear between objects, and between an object and a wall
SAME_PER_SQUARE = 3  # copies of one object a grid square may hold, so a room reads, not swarms
SEARCH = 48         # px an object may slide from its harvested spot
SHELL_THEME = 'joe'

sys.path.insert(0, HERE)
import make_object_requisition as req   # noqa: E402  (footprints and who-owns-what)

# ---- harvested prop -> object -----------------------------------------------------------
# Same thing, any room. A prop absent here and from ROOM_PROP has no object: a gap.
PROP = {
    'crates': 'obj_common_crate_small', 'ammo': 'obj_common_ammo_cans', 'drums': 'obj_common_oil_drum',
    'filing': 'obj_common_filing_cabinet', 'toolchest': 'obj_common_tool_chest',
    'console': 'obj_common_console', 'lockers': 'obj_common_locker', 'shelf': 'obj_common_shelf',
    'plant': 'obj_common_plant', 'crtdesk': 'obj_common_terminal_desk',
    'sandbags': 'obj_common_sandbags_straight', 'sandbags2': 'obj_common_sandbags_straight',
    'desk': 'obj_common_desk', 'table': 'obj_common_table', 'conf': 'obj_common_table',
    'chairs': 'obj_common_chair', 'cot': 'obj_common_cot', 'dbunk': 'obj_common_bunk_bed',
    'bunk': 'obj_common_bunk_bed', 'footlocker': 'obj_common_footlocker',
}
# The room's own object for a prop, where the requisition gave the room one. None = no object.
ROOM_PROP = {
    'j_motorpool_lift': {'lift': 'vehicle_lift'},
    'j_bunks': {'cot': 'obj_common_bunk_bed'},          # the requisition puts bunk beds in Bunks
    'j_weapons_locker': {'rack': 'rifle_rack_rifles', 'ammo': 'ammo_shelf'},
    'j_lab_bench': {'labbench': 'lab_bench_glassware'},
    'j_workbench': {'pegbench': 'workbench_vise_tools'},
    'j_infirmary_cot': {'medcab': 'medicine_cabinet'},
    'j_holding_block': {'cellbunk': 'small_cell'},
    'j_generator': {'biggen': 'large_diesel_generator', 'panel': 'breaker_panel'},
    'j_cobranium_reactor': {'reactor': 'reactor_core', 'console_green': 'obj_common_console'},
    'j_quarters_suites': {'bed': 'single_bed_blanket', 'bed_red': 'single_bed_blanket',
                          'bookshelf': 'bookcase', 'tv': 'small_tv_stand'},
    'j_ammo_dump': {'ammo': 'stacked_ammo_crates', 'crates': 'obj_common_crate_large'},
    'j_lab': {'labbench': 'lab_bench_glassware', 'hood': 'fume_hood', 'fridge': 'specimen_refrigerator'},
    'j_fabshop': {'lathe': 'metal_lathe', 'welder': 'welding_station_gas', 'shelf': 'parts_rack'},
    'j_hangar': {'tank': 'fuel_bowser_small', 'crates': 'obj_common_crate_large'},
    'j_motorpool': {'pegbench': 'workbench_vise', 'engine': 'engine_hoist_frame'},
    'j_heavy_elevator': {'lift': 'elevator_platform'},
    'j_radar': {'scope': 'radar_scope_console', 'plot': 'small_radar_plotting'},
    'j_lr_radar': {'dish': 'radar_mast_base', 'scope': 'radar_scope_console'},
    'j_sigint': {'radio': 'receiver_rack_dials'},
    'j_infirmary': {'optable': 'operating_table_round', 'hbed': 'hospital_bed', 'medcab': 'medicine_cabinet'},
    'j_detention': {'cellbunk': 'cell', 'crtdesk': 'guard_desk_monitor'},
    'j_sitroom': {'plot': 'round_analysis_table', 'crtdesk': 'analyst_desk_terminal'},
    'j_archives': {'filing': 'row_filing_cabinets', 'bookshelf': 'obj_common_shelf',
                   'microfiche': 'microfilm_reader_desk', 'table': 'reading_table_document'},
    'j_computer_banks': {'mainframe': 'mainframe_cabinet_tape'},
    'j_pentagon': {'teletype': 'secure_teletype_machine'},
    'j_briefing': {'lectern': 'lectern', 'chairs': 'obj_common_folding_chair'},
    'j_hologram': {'holo': 'hologram_projector_pad'},
    'j_training': {'bag': 'punching_bag_round', 'weights': 'weight_bench_barbell', 'mat': 'exercise_mat'},
    'j_rifle_range': {'booth': 'shooting_booth_row', 'target': 'target_stand_paper'},
    'j_brainwave_lab': {'helmet': 'reclining_test_chair', 'console_purple': 'obj_common_console'},
    'j_brainwave_jammer': {'coil': 'jammer_machine', 'console_purple': 'control_console_dials'},
    'j_mg_defense': {'t_mg': 'machine_gun_emplacement'},
    'j_double_mg': {'t_mg': 'twin_machine_gun', 'ammo': 'ammo_belt_box'},
    'j_missile_defense': {'t_missile': 'twin_missile_launcher', 'ammo': 'reload_crate'},
    'j_mortar_defense': {'t_mortar': 'mortar_sandbag_ring', 'ammo': 'mortar_bomb_rack'},
    'j_mortar_launcher': {'t_mortar': 'heavy_mortar_base', 'ammo': 'mortar_bomb_crates'},
    'j_air_defense': {'t_aa': 'sam_launcher_mount', 'ammo': 'missile_reload_crate'},
    'j_aa_gun': {'t_aa': 'twin_barrel_aa', 'ammo': 'ready_ammo_box'},
    'j_mountain_howitzer': {'t_howitzer': 'pack_howitzer_top', 'ammo': 'shell_crates'},
    'j_laser_battery': {'t_laser': 'laser_cannon_turret'},
    'j_law': {'t_laser': 'laser_artillery_piece'},
    'j_pulse_battery': {'t_pulse': 'pulse_cannon_mount'},
    'j_sonic_barrier': {'t_sonic': 'sonic_emitter'},
    'j_emergency_tunnel': {'ladder': 'tunnel_mouth', 'crates': 'emergency_supply_crates'},
    'j_data_vault': {'mainframe': 'reel_to_reel'},
    'j_hq_command_center': {'console_red': 'command_console_bank', 'desk': 'commander_s_desk'},
    'o_field_command': {'plot': 'map_table_paper', 'radio': 'field_radio_crate'},
    'o_comms': {'radio': 'radio_rack'},
}
# Features the generator draws as floor, not through place(), so the harvest has no row for
# them. Tile rectangles copied from specials.py (sp_pool): x, y, w, d in the room's tiles.
FIXTURES = {
    'j_pool': [('swimming_pool', 3, 2.2, 14, 5.6), ('diving_board', 17.2, 4.6, 1.4, 0.8)],
}
# Lie flat on the floor: drawn first and cast no shadow.
FLAT = ('exercise_mat', 'swimming_pool', 'vehicle_lift', 'elevator_platform', 'lift_platform',
        'hologram_projector_pad', 'cable_cover', 'diving_board')
# Vanilla facility -> the room it is (by the name the mod gives it, en-US.yml).
VANILLA = {
    'STR_LIVING_QUARTERS': 'j_barracks',          # "Barracks"
    'STR_LABORATORY': 'j_lab',                    # "Laboratory"
    'STR_WORKSHOP': 'j_fabshop',                  # "Workshop" - the Pit's manufacturing room
    'STR_SMALL_RADAR_SYSTEM': 'j_radar',
    'STR_LARGE_RADAR_SYSTEM': 'j_lr_radar',
    'STR_MISSILE_DEFENSES': 'j_missile_defense',
    'STR_LASER_DEFENSES': 'j_laser_battery',
    'STR_PLASMA_DEFENSES': 'j_pulse_battery',     # "Pulse Defenses"
    'STR_ALIEN_CONTAINMENT': 'j_detention',       # "Detention Block"
    'STR_PSIONIC_LABORATORY': 'j_brainwave_lab',  # "Brainwave Laboratory"
    'STR_HYPER_WAVE_DECODER': 'j_sigint',         # "Signals Intelligence Center"
    'STR_MIND_SHIELD': 'j_brainwave_jammer',      # shields the base's brain waves
    'STR_HANGAR': 'j_hangar',
    'STR_ACCESS_LIFT': 'j_access_lift',           # no harvested plan yet: left as it is
    'STR_GENERAL_STORES': 'j_supply_depot',       # "Supply Depot" - no harvested plan yet
}


def refuse(msg):
    sys.exit('REFUSED: ' + msg)


# ---- inputs ----------------------------------------------------------------------------
def footprints():
    """Every object's footprint in shell px, from the requisition (the canvas alone is
    ambiguous: a 176 px canvas is a 44 px crate at x4 or a 22 px locker at x8)."""
    common, rooms, _ = req.parse()
    foot, owner = {}, {}
    for n, _d, wh in common + req.ADDED_COMMON + req.ADDED_BUILD:
        foot[n] = wh
    for nm, fp, file, items, commons in req.ADDED_ROOMS:
        rooms.insert(0, [nm, fp, file, [(s, d, wh, '') for s, d, wh in items], commons, 2])
    for r in rooms:
        rid = r[2][:-4]
        key = rid.split('_', 1)[1]
        for s, _d, wh, _n in r[3]:
            foot['obj_%s_%s' % (key, s)] = wh
            owner.setdefault(rid, set()).add('obj_%s_%s' % (key, s))
    return foot, owner


def load_object(name, foot):
    p = os.path.join(OBJ, name + '.png')
    if not os.path.exists(p):
        refuse('object %s is mapped but %s does not exist' % (name, p))
    if name not in foot:
        refuse('object %s has no footprint in the requisition' % name)
    w, h = foot[name]
    k = 8 if max(w, h) < 32 else 4
    im = Image.open(p).convert('RGB')
    if im.size != (w * k, h * k):
        refuse('%s is %dx%d, its footprint %dx%d wants a %dx%d canvas' % (name, im.width, im.height, w, h, w * k, h * k))
    a = np.asarray(im).astype(np.int16)
    mag = (a[..., 0] > 200) & (a[..., 1] < 70) & (a[..., 2] > 200)
    rgba = np.dstack([a.astype(np.uint8), np.where(mag, 0, 255).astype(np.uint8)])
    return Image.fromarray(rgba, 'RGBA').resize((w, h), Image.LANCZOS)


def floor_mask(shell):
    """The open floor of a shell: the region joined to the middle with no sharp edge in it
    (light pools and gradients are smooth; a wall's outline is not), eroded so nothing
    touches a wall, a door recess or the wall's cast shadow."""
    a = np.asarray(shell).astype(float)
    h, w = a.shape[:2]
    g = ndimage.gaussian_filter(a[..., :3].mean(axis=2), 1)
    edge = np.hypot(ndimage.sobel(g, 0), ndimage.sobel(g, 1))
    low = (edge < 40) & (a[..., 3] == 255)
    lab, _ = ndimage.label(low)
    m = lab == lab[h // 2, w // 2]
    m = ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=3))
    return ndimage.binary_erosion(m, iterations=GAP)


def door_aprons(sw, sh, mask):
    """Rectangles in front of every door (the middle of each outer square edge) kept clear,
    so no object stands across a corridor's mouth."""
    ys, xs = np.nonzero(mask)
    fx0, fx1, fy0, fy1 = xs.min(), xs.max(), ys.min(), ys.max()
    out, half, deep = [], 30, 12
    for i in range(sw):
        cx = i * SQ + SQ // 2
        out.append((cx - half, 0, cx + half, fy0 + deep))
        out.append((cx - half, fy1 - deep, cx + half, sh * SQ))
    for j in range(sh):
        cy = j * SQ + SQ // 2
        out.append((0, cy - half, fx0 + deep, cy + half))
        out.append((fx1 - deep, cy - half, sw * SQ, cy + half))
    return out, (fx0, fy0, fx1, fy1)


# ---- layout ----------------------------------------------------------------------------
def turn_for(tile_rect, X, Y, ow, oh):
    """Degrees (PIL, counter-clockwise) to turn an object whose front faces DOWN in its art,
    so its long side runs the way the prop's did and its front faces away from its wall."""
    x, y, w, d = tile_rect
    walls = {'top': y <= 0.15, 'bottom': y + d >= Y - 0.15, 'left': x <= 0.15, 'right': x + w >= X - 0.15}
    long_obj = 'v' if oh > ow * 1.15 else 'h' if ow > oh * 1.15 else None
    long_prop = 'v' if d > w * 1.15 else 'h' if w > d * 1.15 else None
    if long_obj and long_prop:
        upright = long_obj == long_prop
    else:   # square-ish: face away from the nearest wall it stands against
        upright = not (walls['left'] or walls['right']) or walls['top'] or walls['bottom']
    if upright:
        return 180 if walls['bottom'] and not walls['top'] else 0
    return 270 if walls['right'] and not walls['left'] else 90


def layout(rid, room, shell, foot, owner, idf):
    sw, sh = room['size']
    X, Y = 10 * sw, 10 * sh            # the generator's grid: 10 tiles to a square
    mask = floor_mask(shell)
    aprons, (fx0, fy0, fx1, fy1) = door_aprons(sw, sh, mask)
    walls = ~mask                     # flat floor pieces only have to stay off the walls
    busy = walls.copy()               # anything standing also stays out of the door mouths
    for (a, b, c, d) in aprons:
        busy[max(0, b):d, max(0, a):c] = True
    key = rid.split('_', 1)[1]
    own = owner.get(rid, set())
    wants, gaps = [], {}
    rows = [(n, x, y, w, d, False) for n, x, y, w, d in room['props']]
    rows += [(n, x, y, w, d, True) for n, x, y, w, d in FIXTURES.get(rid, [])]
    for n, x, y, w, d, fixture in rows:
        o = n if fixture else ROOM_PROP.get(rid, {}).get(n, PROP.get(n))
        if o is None:
            gaps[n] = gaps.get(n, 0) + 1
            continue
        name = o if o.startswith('obj_') else 'obj_%s_%s' % (key, o)
        if not name.startswith('obj_common_') and name not in own:
            refuse('%s maps %s to %s, which the requisition does not give this room' % (rid, n, name))
        wants.append((name, (x, y, w, d), n))
    # signature pieces first: the room's own objects, then the kit by how much its prop
    # identifies this room (count here x rarity across rooms - BASEVIEW.md's weighting),
    # biggest first within that
    tf = {}
    for n, *_ in room['props']:
        tf[n] = tf.get(n, 0) + 1
    def rank(t):
        name, _r, n = t
        fw, fh = foot[name]
        if name in own:
            return (0, 0, -fw * fh)
        return (1, -round(tf.get(n, 1) * idf.get(n, 1.0), 1), -fw * fh)
    wants.sort(key=rank)
    # the prop that most identifies the room (rows of chairs in Briefing, mainframes in
    # Computer Banks) is exempt from the repeat cap: repeating it IS the picture
    # (only the room's own object, or a kit prop found in under a tenth of the rooms:
    # ammo cans, crates and lockers identify nothing)
    mapped = [t for t in wants if t[2] in tf and (t[0] in own or idf.get(t[2], 0) >= 2.5)]
    sig = max(mapped, key=lambda t: tf[t[2]] * idf.get(t[2], 1.0))[0] if mapped else None
    placed, dropped, small = [], {}, {}
    cache = {}
    for name, (x, y, w, d), _n in wants:
        ow, oh = foot[name]
        if name != sig and sum(1 for p in placed if p[0] == name) >= SAME_PER_SQUARE * sw * sh:
            dropped[name] = dropped.get(name, 0) + 1
            continue
        if max(ow, oh) < SMALLEST:
            small[name] = small.get(name, 0) + 1
            continue
        t = turn_for((x, y, w, d), X, Y, ow, oh)
        bw, bh = (ow, oh) if t in (0, 180) else (oh, ow)
        # the prop's spot, on this floor
        cx = fx0 + (x + w / 2) / X * (fx1 - fx0)
        cy = fy0 + (y + d / 2) / Y * (fy1 - fy0)
        if x <= 0.15: cx = fx0 + bw / 2
        if x + w >= X - 0.15: cx = fx1 - bw / 2
        if y <= 0.15: cy = fy0 + bh / 2
        if y + d >= Y - 0.15: cy = fy1 - bh / 2
        flat = any(f in name for f in FLAT)
        if name not in cache:
            cache[name] = load_object(name, foot)
        im = cache[name]
        if t:
            im = im.rotate(t, expand=True, resample=Image.BICUBIC)
        # occupancy is the object's own outline, not its box: a round turret leaves its
        # corners free
        shape = np.asarray(im.getchannel('A')) > 40
        spot = fit(walls if flat else busy, int(round(cx - bw / 2)), int(round(cy - bh / 2)), shape)
        if spot is None:     # blocked at its wall: try again from the prop's own centre
            ux = fx0 + (x + w / 2) / X * (fx1 - fx0)
            uy = fy0 + (y + d / 2) / Y * (fy1 - fy0)
            spot = fit(walls if flat else busy, int(round(ux - bw / 2)), int(round(uy - bh / 2)), shape)
        if spot is None:
            dropped[name] = dropped.get(name, 0) + 1
            continue
        px, py = spot
        pad = np.zeros((shape.shape[0] + 2 * GAP, shape.shape[1] + 2 * GAP), bool)
        pad[GAP:-GAP, GAP:-GAP] = shape
        pad = ndimage.binary_dilation(pad, iterations=GAP)
        H, W = busy.shape
        y0, x0 = py - GAP, px - GAP
        sy0, sx0 = max(0, -y0), max(0, -x0)
        sy1, sx1 = min(pad.shape[0], H - y0), min(pad.shape[1], W - x0)
        for b in (walls, busy):
            b[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1] |= pad[sy0:sy1, sx0:sx1]
        placed.append((name, px, py, im))
    return placed, gaps, dropped, small


def fit(busy, x0, y0, shape):
    """Nearest spot to (x0, y0), within SEARCH px, where the object's outline lies on clear
    floor."""
    H, W = busy.shape
    h, w = shape.shape
    best = None
    for r in range(0, SEARCH + 1, 2):
        for dy in range(-r, r + 1, 2):
            for dx in (-r, r) if abs(dy) != r else range(-r, r + 1, 2):
                x, y = x0 + dx, y0 + dy
                if x < 0 or y < 0 or x + w > W or y + h > H:
                    continue
                if not (busy[y:y + h, x:x + w] & shape).any():
                    dd = dx * dx + dy * dy
                    if best is None or dd < best[0]:
                        best = (dd, x, y)
        if best:
            return best[1], best[2]
    return None


def compose(shell, placed):
    """Shell, then the objects' soft shadows (light from the upper left, as the preview
    mock-ups do it), then the objects, back to front."""
    out = shell.copy()
    shadow = Image.new('RGBA', shell.size, (0, 0, 0, 0))
    objs = Image.new('RGBA', shell.size, (0, 0, 0, 0))
    flat = [p for p in placed if any(f in p[0] for f in FLAT)]
    stand = [p for p in placed if p not in flat]
    stand.sort(key=lambda p: (p[2] + p[3].height, p[1]))       # far (top) to near (bottom)
    for name, x, y, im in flat:
        out.alpha_composite(im, (x, y))
    for name, x, y, im in stand:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        sh.putalpha(im.getchannel('A').point(lambda v: v * 110 // 255))
        shadow.alpha_composite(sh, (x + 3, y + 3))
        objs.alpha_composite(im, (x, y))
    shadow = shadow.filter(ImageFilter.GaussianBlur(2))
    # the shadow falls on floor only, never up a wall
    a = np.asarray(shadow).copy()
    floor = np.asarray(shell)[..., 3] == 255
    a[..., 3] = np.where(floor, a[..., 3], 0)
    out.alpha_composite(Image.fromarray(a, 'RGBA'))
    out.alpha_composite(objs)
    return out


# ---- the 8-bit twin --------------------------------------------------------------------
def palette(ufo):
    pal_dat = os.path.join(ufo, 'GEODATA', 'PALETTES.DAT')
    bb = os.path.join(ufo, 'GEOGRAPH', 'BASEBITS')
    for p in (pal_dat, bb + '.PCK', bb + '.TAB'):
        if not os.path.exists(p):
            refuse('missing %s (pass --ufo, the folder holding GEODATA and GEOGRAPH)' % p)
    raw = open(pal_dat, 'rb').read()
    pal = [min(255, c << 2) for c in raw[774:774 + 768]]          # palette 1, 774-byte stride
    t = open(bb + '.TAB', 'rb').read()
    dpk = open(bb + '.PCK', 'rb').read()
    wide = len(t) >= 4 and struct.unpack('<I', t[:4])[0] == 0
    offs = list(struct.unpack('<%dI' % (len(t) // 4), t)) if wide else list(struct.unpack('<%dH' % (len(t) // 2), t))
    used = set()
    for i in range(1, min(37, len(offs))):
        p = offs[i] + 1
        while p < len(dpk) and dpk[p] != 255:
            v = dpk[p]; p += 1
            if v == 254: p += 1
            elif v: used.add(v)
    return pal, sorted(used)


def to_8bit(img, pal, uses):
    """Area-reduce to 32 px a square and snap every pixel to the allowed indices (redmean);
    what the shell left transparent stays index 0, the plate showing through."""
    W, H = img.width * PX // SQ, img.height * PX // SQ
    small = np.asarray(img.resize((W, H), Image.BOX)).astype(float)
    P = np.array([pal[i * 3:i * 3 + 3] for i in uses], float)
    rgb = small[..., :3].reshape(-1, 1, 3)
    rm = (P[None, :, 0] + rgb[..., 0]) / 2
    dd = ((2 + rm / 256) * (P[None, :, 0] - rgb[..., 0]) ** 2 + 4 * (P[None, :, 1] - rgb[..., 1]) ** 2
          + (2 + (255 - rm) / 256) * (P[None, :, 2] - rgb[..., 2]) ** 2)
    idx = np.array(uses)[dd.argmin(axis=1)].reshape(H, W)
    idx[small[..., 3] < 128] = 0
    out = Image.fromarray(idx.astype(np.uint8), 'P')
    out.putpalette(pal)
    return out


# ---- main ------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--ufo', required=True, help='vanilla data folder holding GEODATA/ and GEOGRAPH/')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--sheet', help='write a contact sheet of every stocked room here')
    a = ap.parse_args()

    for p in (PLACE, FRAMES, OBJ, SHELLS, FAC):
        if not os.path.exists(p):
            refuse('missing ' + p)
    rooms = json.load(open(PLACE))
    frames = json.load(open(FRAMES))
    foot, owner = footprints()
    pal, uses = palette(a.ufo)
    if len(uses) < 100:
        refuse('only %d palette indices found in BASEBITS - wrong file?' % len(uses))

    shells = {}
    for w, h in ((1, 1), (2, 1), (1, 2), (2, 2)):
        p = os.path.join(SHELLS, 'shell_%s_%dx%d.png' % (SHELL_THEME, w, h))
        if os.path.exists(p):
            im = Image.open(p).convert('RGBA')
            if im.size != (w * SQ, h * SQ):
                refuse('%s is %dx%d, want %dx%d' % (p, im.width, im.height, w * SQ, h * SQ))
            shells[(w, h)] = im
    if not shells:
        refuse('no shells in ' + SHELLS)

    import math
    df = {}
    for r in rooms.values():
        for n in set(p[0] for p in r['props']):
            df[n] = df.get(n, 0) + 1
    idf = {n: math.log(len(rooms) / c) for n, c in df.items()}
    done, report, out_imgs = [], [], []
    tot_placed = set()
    for rid in sorted(rooms):
        r = rooms[rid]
        if r['theme'] != SHELL_THEME:
            continue
        size = tuple(r['size'])
        fr = frames.get(rid)
        if fr is None or tuple(fr['size']) != size or fr['frames'] != size[0] * size[1]:
            refuse('%s: harvested size %s disagrees with baseview_frames.json %s' % (rid, size, fr))
        if size not in shells:
            report.append('%-22s no %dx%d shell - left as it is' % (rid, *size))
            continue
        shell = shells[size]
        placed, gaps, dropped, small = layout(rid, r, shell, foot, owner, idf)
        img = compose(shell, placed)
        out_imgs.append((rid, img))
        tot_placed.update(n for n, *_ in placed)
        done.append(rid)
        counts = {}
        for n, *_ in placed:
            counts[n] = counts.get(n, 0) + 1
        report.append('%-22s placed %2d  %s' % (rid, len(placed), ', '.join('%s x%d' % (n.replace('obj_', ''), c) for n, c in sorted(counts.items()))))
        if dropped:
            report.append('%-22s   no room for: %s' % ('', ', '.join('%s x%d' % (n.replace('obj_', ''), c) for n, c in sorted(dropped.items()))))
        if small:
            report.append('%-22s   too small to read: %s' % ('', ', '.join('%s x%d' % (n.replace('obj_', ''), c) for n, c in sorted(small.items()))))
        if gaps:
            report.append('%-22s   GAP, no object: %s' % ('', ', '.join('%s x%d' % (n, c) for n, c in sorted(gaps.items()))))
        unused = sorted(o for o in owner.get(rid, ()) if o not in counts)
        if unused:
            report.append('%-22s   requisitioned, no harvested spot: %s' % ('', ', '.join(o.replace('obj_', '') for o in unused)))
        if a.write:
            sw, sh = size
            for j in range(sh):
                for i in range(sw):
                    sq = img.crop((i * SQ, j * SQ, (i + 1) * SQ, (j + 1) * SQ))
                    k = j * sw + i
                    sq.save(os.path.join(FAC, '%s_%d_hi.png' % (rid, k)))
                    to_8bit(sq, pal, uses).save(os.path.join(FAC, '%s_%d.png' % (rid, k)))

    print('\n'.join(report))
    print('\nrooms stocked: %d   distinct objects used: %d of %d on disk'
          % (len(done), len(tot_placed), len([f for f in os.listdir(OBJ) if f.endswith('.png')])))
    missing = [r for r in ('j_access_lift', 'j_supply_depot') if r not in rooms]
    if missing:
        print('no harvested plan, so not stocked: ' + ', '.join(missing))

    if a.write:
        lines = ['# GENERATED by build/install_stocked_rooms.py - do not hand-edit.',
                 '#',
                 '# Points the vanilla facilities the mod renames at the stocked room frames',
                 '# (gijoe_base_facilities.rul, BASEBITS 100+). spriteFacility only: no cost,',
                 '# build time, upkeep or capacity is changed. The base view draws each frame\'s',
                 '# _hi twin (the shell with its objects) in place of the bare shell.',
                 'facilities:']
        for t, rid in VANILLA.items():
            if rid in done:
                lines += ['  - type: %s' % t, '    spriteFacility: %d    # %s' % (frames[rid]['first'], rid)]
                if rooms[rid]['size'] != [1, 1]:   # vanilla draws a big room's frames only when told to
                    lines.append('    spriteEnabled: true')
        open(RUL, 'w').write('\n'.join(lines) + '\n')
        print('written: %d rooms of frames + twins to %s, and %s' % (len(done), FAC, RUL))
    else:
        print('(dry run - nothing written; add --write)')

    if a.sheet and out_imgs:
        cols = 6
        cell = 2 * SQ + 40
        rows = (len(out_imgs) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * cell, rows * cell), (29, 33, 26, 255))
        from PIL import ImageDraw
        d = ImageDraw.Draw(sheet)
        for n, (rid, img) in enumerate(out_imgs):
            x, y = (n % cols) * cell + 20, (n // cols) * cell + 30
            sheet.alpha_composite(img, (x, y))
            d.text((x, y - 18), rid, fill=(230, 220, 170, 255))
        sheet.convert('RGB').save(a.sheet)
        print('sheet:', a.sheet)


if __name__ == '__main__':
    main()
