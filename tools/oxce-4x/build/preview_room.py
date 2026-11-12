"""Mock up a stocked room: a shell with delivered objects laid on it at their real footprints.

    python3 preview_room.py OUT.png [scale]

A preview for judging the art together, not the game's placement system. Each object is resized
from its 4x/8x canvas to its footprint (ROOM_OBJECTS_LIST_source.txt, shell pixels: 192 a square),
turned, and given the soft shadow the game will add (light from the upper left). Layouts below are
hand-placed in shell pixels: (object, centre x, centre y, turn in degrees).
"""
import os, re, sys
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.join(HERE, '..', 'mod', 'Resources', 'Base')
SRC = os.path.join(HERE, '..', 'art_briefs', 'objects', 'ROOM_OBJECTS_LIST_source.txt')

FOOT = {}
room = None
for line in open(SRC):
    m = re.match(r'\s+(obj_\S+)\s.*\[(\d+)x(\d+)\]', line)
    if m:
        FOOT[m.group(1)] = (int(m.group(2)), int(m.group(3)))

ROOMS = [
    ('HQ Command Center', 'shell_joe_2x1.png', [
        ('obj_hq_command_center_command_console_bank', 192, 52, 0),
        ('obj_hq_command_center_big_plotting_table', 192, 116, 0),
        ('obj_common_chair', 106, 116, 0), ('obj_common_chair', 278, 116, 0),
        ('obj_hq_command_center_commander_s_desk', 318, 140, 180),
        ('obj_common_chair', 318, 112, 180),
        ('obj_common_plant', 44, 44, 0), ('obj_common_plant', 340, 44, 0),
        ('obj_common_trash_can', 44, 148, 0),
    ]),
    ('Bunks', 'shell_joe_1x1.png', [
        ('obj_common_bunk_bed', 56, 78, 0), ('obj_common_bunk_bed', 136, 78, 0),
        ('obj_common_footlocker', 56, 128, 0), ('obj_common_footlocker', 136, 128, 0),
        ('obj_common_locker', 44, 150, 0), ('obj_common_locker', 148, 150, 0),
    ]),
    ('Weapons Locker', 'shell_joe_1x1.png', [
        ('obj_weapons_locker_rifle_rack_rifles', 96, 66, 0),
        ('obj_weapons_locker_rifle_rack_rifles', 96, 88, 180),
        ('obj_weapons_locker_gun_cleaning_table', 96, 132, 0),
        ('obj_weapons_locker_ammo_shelf', 42, 64, 90),
        ('obj_common_ammo_cans', 150, 46, 0), ('obj_common_crate_small', 150, 146, 0),
    ]),
]


def stock(shell_name, items, s):
    shell = Image.open(os.path.join(MOD, 'shells', shell_name)).convert('RGBA')
    shell = shell.resize((shell.width * s, shell.height * s), Image.LANCZOS)
    px = shell.load()
    for y in range(shell.height):                     # magenta margin -> transparent
        for x in range(shell.width):
            r, g, b, a = px[x, y]
            if r > 200 and g < 70 and b > 200:
                px[x, y] = (0, 0, 0, 0)
    shadow = Image.new('RGBA', shell.size, (0, 0, 0, 0))
    objs = Image.new('RGBA', shell.size, (0, 0, 0, 0))
    for name, cx, cy, turn in items:
        im = Image.open(os.path.join(MOD, 'objects', name + '.png')).convert('RGBA')
        d = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = d[x, y]
                if r == 255 and g == 0 and b == 255:
                    d[x, y] = (0, 0, 0, 0)
        if name in FOOT:
            w, h = FOOT[name]
        else:   # room-specific objects: footprint from the canvas rule (x4, or x8 when under 32)
            k = 4 if max(im.size) // 4 >= 32 else 8
            w, h = im.width // k, im.height // k
        im = im.resize((w * s, h * s), Image.LANCZOS).rotate(turn, expand=True, resample=Image.BICUBIC)
        pos = (int(cx * s - im.width / 2), int(cy * s - im.height / 2))
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        sh.putalpha(im.getchannel('A').point(lambda v: v * 110 // 255))
        shadow.alpha_composite(sh, (pos[0] + 3 * s, pos[1] + 3 * s))
        objs.alpha_composite(im, pos)
    shadow = shadow.filter(ImageFilter.GaussianBlur(2 * s))
    out = shell.copy()
    out.alpha_composite(shadow)
    out.alpha_composite(objs)
    return out


def main():
    out, s = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2
    tiles = [stock(sh, items, s) for _, sh, items in ROOMS]
    gap = 24
    W = sum(t.width for t in tiles) + gap * (len(tiles) + 1)
    H = max(t.height for t in tiles) + gap * 2
    sheet = Image.new('RGBA', (W, H), (34, 38, 32, 255))
    x = gap
    for t in tiles:
        sheet.alpha_composite(t, (x, gap))
        x += t.width + gap
    sheet.convert('RGB').save(out)
    print('wrote', out, sheet.size)


if __name__ == '__main__':
    main()
