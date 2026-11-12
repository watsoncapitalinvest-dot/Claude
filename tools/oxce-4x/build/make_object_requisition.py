#!/usr/bin/env python3
"""Split John's room-objects requisition into four self-contained orders.

    python3 build/make_object_requisition.py

Reads art_briefs/objects/ROOM_OBJECTS_LIST_source.txt (the requisition as John
wrote it), adds what the game needs that it did not have, and writes
art_briefs/objects/OBJECTS_GROUP_1..4.txt - each one a complete order the
graphics AI can be handed alone: the spec, then every object with its exact
file name and canvas size.

The canvas is the object's footprint from the list times 4 (times 8 when the
footprint's long side is under 32 px, or it would be a smudge), so the art is
drawn big and brought down by area when it is laid on a room.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.normpath(os.path.join(HERE, '..', 'art_briefs', 'objects'))
SRC = os.path.join(DIR, 'ROOM_OBJECTS_LIST_source.txt')

ADDED_COMMON = [
    ('obj_common_pallet', 'empty wooden shipping pallet', (48, 40)),
    ('obj_common_pallet_rack', 'steel pallet racking bay, boxes on the shelves', (96, 36)),
    ('obj_common_pallet_load', 'pallet stacked with plain boxes under shrink wrap', (48, 40)),
    ('obj_common_hand_truck', 'two-wheel hand truck, upright', (18, 22)),
    ('obj_common_coffee_station', 'small counter with coffee maker and mugs', (48, 22)),
    ('obj_common_junction_box', 'grey electrical junction box on a short post', (20, 14)),
    ('obj_common_cable_cover', 'straight rubber floor cable cover, yellow edges', (64, 10)),
    ('obj_common_stretcher', 'folded canvas stretcher', (22, 70)),
    ('obj_common_whiteboard', 'whiteboard on a wheeled stand, seen from above as a thin bar', (64, 12)),
    ('obj_common_vent_unit', 'floor ventilation unit with a round fan grille', (36, 36)),
]
ADDED_BUILD = [
    ('obj_build_scaffold', 'scaffold section, steel tubes and planks', (64, 32)),
    ('obj_build_cement_mixer', 'small cement mixer, drum tilted', (36, 40)),
    ('obj_build_material_pile', 'pile of steel beams and planks under a tarp', (70, 36)),
    ('obj_build_work_light', 'work light on a tripod', (20, 20)),
    ('obj_build_cones', 'two orange traffic cones', (24, 14)),
]
ADDED_ROOMS = [
    ('Access Lift (start)', '1x1', 'j_access_lift.png', [
        ('lift_platform', 'lift platform: steel plate with yellow-black edges, guide rails at two sides', (140, 140)),
        ('control_post', 'lift control post with a lever', (18, 18)),
        ('guard_stool', 'guard stool and small desk', (40, 24)),
    ], ['fire_extinguisher']),
    ('Supply Depot (start)', '1x1', 'j_supply_depot.png', [
        ('issue_counter', 'quartermaster issue counter with a ledger', (80, 24)),
    ], ['pallet_rack x2', 'pallet_load x2', 'hand_truck', 'crate_large', 'crate_small x2']),
]
COBRA_COMMON = ['desk', 'chair', 'table', 'filing_cabinet', 'locker', 'shelf', 'crate_small', 'crate_large',
                'ammo_cans', 'oil_drum', 'console', 'terminal_desk', 'printer', 'bunk_bed', 'footlocker',
                'tool_chest', 'fire_extinguisher', 'trash_can', 'cable_reel', 'pallet', 'pallet_load']


def canvas(w, h):
    k = 8 if max(w, h) < 32 else 4
    return w * k, h * k, k


def slug(text):
    t = text.split(':')[0] if ':' in text[:30] else text
    words = [w for w in re.sub(r'[^a-z0-9 ]', ' ', t.lower()).split() if w not in ('a', 'an', 'the', 'with', 'on', 'of', 'and', 'in')]
    return '_'.join(words[:3])


def parse():
    lines = open(SRC, encoding='utf-8').read().split('\n')
    common, rooms, heads = [], [], []
    section = None
    room = None
    for ln in lines:
        m = re.match(r'=== (\d)\. ', ln)
        if m:
            section = int(m.group(1))
            room = None
            continue
        if section == 1:
            m = re.match(r'\s+(obj_common_\w+)\s+(.*?)\s+\[(\d+)x(\d+)\]', ln)
            if m:
                common.append((m.group(1), m.group(2), (int(m.group(3)), int(m.group(4)))))
        elif section in (2, 3, 4, 5, 6, 7):
            m = re.match(r'(\S.*?)\s+\((\dx\d)\)\s+room file: (\S+)', ln)
            if m:
                room = [m.group(1), m.group(2), m.group(3), [], [], section]
                rooms.append(room)
                continue
            if room is not None:
                m = re.match(r'\s+- common: (.*)', ln)
                if m:
                    room[4] += [c.strip() for c in m.group(1).split(',')]
                    continue
                m = re.match(r'\s+- (.*?) \| (\d+)x(\d+)(.*)', ln)
                if m:
                    room[3].append((slug(m.group(1)), m.group(1).strip(), (int(m.group(2)), int(m.group(3))), m.group(4).strip()))
                    continue
                m = re.match(r'\s+- (.*)', ln)
                if m:   # an item that names a common piece in passing, e.g. "fire-control console (common console)"
                    room[4].append(m.group(1).strip())
        elif section == 8:
            m = re.match(r'\s+(obj_head_\w+)\s+-> (.*)', ln)
            if m:
                heads.append([m.group(1), m.group(2).strip()])
            elif heads and ln.startswith(' ' * 20) and ln.strip():
                heads[-1][1] += ' ' + ln.strip()
    return common, rooms, heads


SPEC = r'''WHAT THESE ARE
Objects for the rooms of a military base, seen on the base planning map. The
rooms themselves are already drawn as empty shells seen from directly above;
these objects are SEPARATE pictures that the game lays onto those floors. One
object per file.

THE VIEW
- Seen from DIRECTLY ABOVE, the same as the room shells: the top of the object
  only. No side, no angle, no perspective - a desk is its desktop, a bunk is
  its blanket, a gun mount is its turntable and barrels seen from above.

SIZE - EXACT
- guide_object_scale_768.png shows one room square at the same 4x scale as the
  canvases, with a few objects' footprints drawn on it, so you can see how big
  each thing is against the room.
- Each object below has a CANVAS size. Make the image exactly that size.
- The object fills its canvas: its outline touches, or comes within 4 pixels
  of, all four edges. The canvas IS the object's footprint, drawn 4 times (or
  8 times for small things) larger than it appears in the game, so it is
  scaled down cleanly. Do not leave a margin; do not crop the object.
- "(x2)", "(x3)" after an object means the game uses it that many times. Draw
  it ONCE.

WHICH WAY ROUND
- The side a person uses - the seat of a desk, the keyboard of a console, the
  open side of a bunk, the muzzle end of a gun - faces DOWN, toward the bottom
  of the picture. The game turns objects to fit the room.

LIGHT - SO OBJECTS CAN BE TURNED
- Soft, even light from DIRECTLY OVERHEAD. No light from one side, no
  highlight on one edge, no shading that says which way the light comes from.
- NO SHADOW of any kind under or beside the object. The game adds the shadow
  itself, the right way round for wherever the object is placed.

STYLE - REAL SHAPES, CARTOON FINISH (approved 12 Nov)
- Real-world shapes and proportions, drawn the way the 1980s Sunbow G.I. Joe
  cartoon draws things, leaning cartoon: bold clean dark outlines round the
  object and its main parts, flat colour with one flat cel-shadow tone, no
  texture, grain or photographic detail. It must sit beside the approved
  soldiers (Reference\character_art\approved\duke_1984.png) and the room shells.
- Outline weight: about 3 pixels on these large canvases, the same on every
  object, so everything reads alike once scaled down.
- Simple strong shapes that read when the object is only 20 to 100 pixels
  across on screen. Leave out detail smaller than about 1/20 of the object.
- Solid objects - consoles, crates, machines - must look solid with clear edges:
  soldiers take cover behind them.

COLOURS
- G.I. Joe objects: olive drab, grey steel, wood, black rubber; small touches
  of safety yellow and red where the real thing has them.
- Cobra objects: dark steel, deep glossy blue, black, thin red accents.
- Screens and displays: plain glowing colour fields and abstract shapes only.

BACKGROUND
- Flat pure magenta, hex FF00FF, everywhere that is not the object, including
  every gap through it. Hard edges: a pixel is object or magenta.

NEVER
- No text, letters, numbers or labels anywhere, including on screens, papers,
  crates and maps.
- No logos, emblems, insignia, flags or badges - no Cobra symbol, no G.I. Joe
  logo, no red cross.
- No people, no hands, no figures (a shadow shape inside a tank is allowed
  only where the list says so).

FILES
- PNG, named exactly as listed. Deliver this group as one zip.

CHECK BEFORE SENDING
1. Straight down, no side visible?
2. Canvas exactly the size listed, object touching the edges?
3. Front facing the bottom of the picture?
4. No shadow, no directional light?
5. Magenta background with hard edges?
6. No text, no logos, no people?
'''


def obj_line(name, desc, wh, note=''):
    w, h = wh
    cw, ch, k = canvas(w, h)
    return '  %-38s %4d x %-4d  %s%s' % (name + '.png', cw, ch, desc, (' ' + note) if note else '')


def room_block(r, prefix):
    name, fp, file, items, commons, _ = r
    stem = file[:-4]
    roomkey = re.sub(r'^[jco]_', '', stem)
    out = ['', '%s  -  %s room  (room file %s)' % (name, fp, file)]
    for s, desc, wh, note in items:
        out.append(obj_line('obj_%s_%s' % (roomkey, s), desc, wh, note))
    if commons:
        out.append('  uses from the common kit (already ordered, do not redraw): ' + ', '.join(commons))
    return out


def head(title, intro):
    bar = '=' * len(title)
    return [title, bar, '', intro, '', SPEC, 'THE OBJECTS IN THIS GROUP', '-------------------------',
            'Name, CANVAS size in pixels (width x height), what it is.']


def main():
    common, rooms, heads = parse()
    for nm, fp, file, items, commons in ADDED_ROOMS:
        rooms.insert(0, [nm, fp, file, [(s, d, wh, '') for s, d, wh in items], commons, 2])
    start = [r for r in rooms if r[5] == 2]
    pit = [r for r in rooms if r[5] == 3]
    outposts = [r for r in rooms if r[5] in (4, 5, 6)]
    cobra = [r for r in rooms if r[5] == 7]
    joe_heads = [h for h in heads if not h[0].startswith('obj_head_cobra')]
    cobra_heads = [h for h in heads if h[0].startswith('obj_head_cobra')]

    groups = []
    g = head('OBJECTS GROUP 1 OF 4 - THE COMMON KIT AND THE PIT\'S START ROOMS',
             'Do this group first. The common kit is reused in nearly every room, and the\n'
             'start rooms are the ones the player sees on day one.')
    g += ['', 'COMMON KIT - reused in many rooms (G.I. Joe colours)']
    g += [obj_line(n, d, wh) for n, d, wh in common + ADDED_COMMON]
    g += ['', 'CONSTRUCTION KIT - laid in a room while it is being built']
    g += [obj_line(n, d, wh) for n, d, wh in ADDED_BUILD]
    g += ['', 'THE PIT - START ROOMS']
    for r in start:
        g += room_block(r, 'j')
    groups.append(g)

    g = head('OBJECTS GROUP 2 OF 4 - THE REST OF THE PIT AND THE JOE DEPARTMENT HEADS',
             'Group 1 (the common kit) must be done first - rooms here reuse it.')
    for r in pit:
        g += room_block(r, 'j')
    g += ['', 'DEPARTMENT HEAD STATIONS - one each, about 80 x 44 unless the note says otherwise.',
          'The head\'s own desk, bench or console seen from above, with the personal items on it.',
          'Heads marked (head TBD) are not named yet: keep the items about the department, not a person.']
    for n, desc in joe_heads:
        w, h = (100, 44) if '100 x 44' in desc else (80, 44)
        g.append(obj_line(n, desc, (w, h)))
    groups.append(g)

    g = head('OBJECTS GROUP 3 OF 4 - THE JOE OUTPOSTS: NAVAL, OUTDOOR, SPACE',
             'Group 1 (the common kit) must be done first - rooms here reuse it.\n'
             'Naval objects are deck grey and steel, outdoor objects olive and canvas, space\n'
             'objects white composite with blue status lights.')
    for r in outposts:
        g += room_block(r, 'o')
    groups.append(g)

    g = head('OBJECTS GROUP 4 OF 4 - COBRA',
             'Cobra installations: dark steel, deep blue, black, thin red accents. Cold and\n'
             'clinical. NO Cobra symbol anywhere. Where a Cobra room below "uses from the\n'
             'common kit", it means the COBRA common kit at the top of this group.')
    g += ['', 'COBRA COMMON KIT - the common pieces again in Cobra colours (dark steel and deep',
          'blue instead of olive), same shapes and same sizes as the Joe kit.']
    sizes = {n: wh for n, d, wh in common + ADDED_COMMON}
    descs = {n: d for n, d, wh in common + ADDED_COMMON}
    for c in COBRA_COMMON:
        jn = 'obj_common_' + c
        g.append(obj_line('obj_cobra_' + c, descs[jn] + ' - in Cobra colours', sizes[jn]))
    for r in cobra:
        g += room_block(r, 'c')
    g += ['', 'COBRA DEPARTMENT HEAD STATIONS - about 80 x 44 unless noted. Draw each TWICE:',
          'once with the personal items (<name>.png) and once bare with the same desk or',
          'station and no personal items (<name>_empty.png), used before that head appears.']
    for n, desc in cobra_heads:
        w, h = (120, 44) if '120 x 44' in desc else (80, 44)
        g.append(obj_line(n, desc, (w, h)))
        g.append(obj_line(n + '_empty', 'the same station with no personal items', (w, h)))
    groups.append(g)

    # the scale guide: the 1x1 shell at 4x with real footprints laid on it
    try:
        from PIL import Image, ImageDraw, ImageFont
        shell = Image.open(os.path.normpath(os.path.join(HERE, '..', 'mod', 'Resources', 'Base', 'shells', 'shell_joe_1x1.png'))).convert('RGBA')
        im = Image.new('RGBA', (768, 768), (255, 0, 255, 255))
        big = shell.resize((768, 768), Image.LANCZOS)
        im.alpha_composite(big)
        d = ImageDraw.Draw(im)
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf', 18)
        for name, (w, h), (x, y) in (('bunk_bed 36x76', (36, 76), (40, 40)), ('desk 64x36', (64, 36), (100, 40)),
                                     ('chair 22x22', (22, 22), (120, 80)), ('crate_large 44x44', (44, 44), (40, 125)),
                                     ('locker 22x22', (22, 22), (100, 130)), ('footlocker 26x16', (26, 16), (130, 130))):
            d.rectangle([x * 4, y * 4, (x + w) * 4, (y + h) * 4], outline=(255, 210, 0, 255), width=4)
            d.text((x * 4 + 6, y * 4 + 4), name, font=f, fill=(255, 230, 120, 255))
        d.text((60, 728), 'one room square at the canvas scale (4x): 768 x 768', font=f, fill=(30, 30, 30, 255))
        im.convert('RGB').save(os.path.join(DIR, 'guide_object_scale_768.png'))
    except Exception as e:
        print('no scale guide:', e)

    total = 0
    for i, g in enumerate(groups, 1):
        n = sum(1 for l in g if re.match(r'\s+obj_\w+\.png', l))
        total += n
        g.insert(3, '%d objects in this group.' % n)
        open(os.path.join(DIR, 'OBJECTS_GROUP_%d.txt' % i), 'w').write('\n'.join(g) + '\n')
        print('group %d: %d objects' % (i, n))
    print('total', total)


if __name__ == '__main__':
    main()
