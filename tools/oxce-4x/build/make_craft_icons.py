"""G.I. Joe icons for the craft screen (John 18 Nov: X-COM leftovers). CraftInfoState draws one BASEBITS frame per man,
per vehicle and per item, 10 px apart: 38 a crewman, 40 a vehicle, 39 a piece of kit. Vanilla's are X-COM's blue
soldier, its tank and its crate. Drawn here at 6x (the _hi twin, 192x240 like craft_33_hi.png) and reduced to the
32x40 8-bit frame on craft_33.png's palette. Each sits in the top-left 10x18, as vanilla's do.
usage: python3 build/make_craft_icons.py"""
import os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..', 'mod', 'Resources', 'Base')
K = 6
INK = (16, 18, 14, 255); OLIVE = (92, 108, 52, 255); OLIVE_D = (60, 72, 34, 255); OLIVE_L = (132, 150, 76, 255)
SKIN = (214, 166, 122, 255); STEEL = (70, 74, 78, 255); STEEL_L = (130, 134, 138, 255); TAN = (170, 140, 90, 255)
GOLD = (216, 180, 90, 255); BLACK = (24, 24, 24, 255)

def canvas():
    return Image.new('RGBA', (32 * K, 40 * K), (0, 0, 0, 0))

def R(d, x0, y0, x1, y1, fill, out=INK):   # a box in 1x units, outlined
    d.rectangle([x0 * K, y0 * K, x1 * K - 1, y1 * K - 1], fill=out)
    d.rectangle([x0 * K + K // 2, y0 * K + K // 2, x1 * K - 1 - K // 2, y1 * K - 1 - K // 2], fill=fill)

def joe():
    im = canvas(); d = ImageDraw.Draw(im)
    d.ellipse([2 * K, 0, 8 * K, 5 * K], fill=INK); d.ellipse([2 * K + 3, 3, 8 * K - 3, 5 * K - 3], fill=OLIVE)   # helmet
    R(d, 3, 3, 7, 6, SKIN)                                   # face
    d.rectangle([2 * K, int(2.6 * K), 8 * K, int(3.2 * K)], fill=OLIVE_D)  # helmet brim
    R(d, 1, 6, 9, 12, OLIVE)                                 # torso and arms
    d.rectangle([4.5 * K, 6.5 * K, 5.5 * K, 11.5 * K], fill=OLIVE_D)       # webbing
    d.rectangle([1.5 * K, 9 * K, 8.5 * K, 9.6 * K], fill=TAN)             # belt
    R(d, 2, 12, 5, 16, OLIVE_D); R(d, 5, 12, 8, 16, OLIVE_D)               # legs
    R(d, 2, 15, 5, 18, BLACK); R(d, 5, 15, 8, 18, BLACK)                   # boots
    return im

def kit():
    im = canvas(); d = ImageDraw.Draw(im)
    # an M16 across, stock bottom-left, muzzle top-right
    d.line([1 * K, 15 * K, 9.4 * K, 1 * K], fill=INK, width=int(2.6 * K)); d.line([1 * K, 15 * K, 9.4 * K, 1 * K], fill=BLACK, width=int(1.4 * K))
    d.line([5 * K, 8 * K, 6.6 * K, 10.6 * K], fill=INK, width=int(1.8 * K)); d.line([5 * K, 8 * K, 6.4 * K, 10.3 * K], fill=STEEL, width=int(0.8 * K))  # magazine
    d.line([3 * K, 11.6 * K, 7.5 * K, 4.2 * K], fill=STEEL_L, width=max(2, K // 3))
    # a grenade bottom-right
    d.ellipse([5 * K, 12 * K, 10 * K, 18 * K], fill=INK); d.ellipse([5.5 * K, 12.6 * K, 9.5 * K, 17.4 * K], fill=OLIVE)
    d.rectangle([6.8 * K, 11 * K, 8.2 * K, 12.6 * K], fill=STEEL); d.line([8.2 * K, 11.4 * K, 9.6 * K, 13 * K], fill=STEEL_L, width=K // 2)
    d.line([6 * K, 15 * K, 9 * K, 15 * K], fill=OLIVE_D, width=K // 3)
    return im

def vehicle():
    im = canvas(); d = ImageDraw.Draw(im)
    # a V.A.M.P.-like jeep from the front: wheels, body, windscreen, the gun on top
    R(d, 0, 9, 3, 15, BLACK); R(d, 7, 9, 10, 15, BLACK)                    # wheels
    R(d, 1, 6, 9, 12, OLIVE)                                               # body
    d.rectangle([2 * K, 7 * K, 8 * K, 8 * K], fill=OLIVE_L)                # bonnet
    d.rectangle([2.5 * K, 9.5 * K, 3.8 * K, 10.6 * K], fill=GOLD); d.rectangle([6.2 * K, 9.5 * K, 7.5 * K, 10.6 * K], fill=GOLD)  # lights
    R(d, 2, 2, 8, 6, STEEL)                                                # windscreen frame
    d.rectangle([2.7 * K, 2.7 * K, 7.3 * K, 5.3 * K], fill=(110, 140, 150, 255))
    d.rectangle([4.4 * K, 0, 5.6 * K, 3 * K], fill=INK)                    # the twin .50 above
    return im

def save(im, idx):
    hi = os.path.join(BASE, 'craft_icon_%d_hi.png' % idx); im.save(hi)
    pal_src = Image.open(os.path.join(BASE, 'craft_33.png'))
    lo = im.resize((32, 40), Image.LANCZOS)
    a = lo.getchannel('A').point(lambda v: 255 if v > 110 else 0)
    rgb = Image.new('RGB', lo.size, (0, 0, 0)); rgb.paste(lo.convert('RGB'), mask=a)
    q = rgb.quantize(palette=pal_src, dither=Image.NONE)
    px = q.load(); am = a.load()
    for y in range(40):
        for x in range(32):
            if not am[x, y]: px[x, y] = 0
            elif px[x, y] == 0: px[x, y] = 15     # never let a drawn pixel land on transparent
    q.save(os.path.join(BASE, 'craft_icon_%d.png' % idx), transparency=0)

save(joe(), 38); save(vehicle(), 40); save(kit(), 39)
print('wrote craft_icon_38/39/40 (+_hi)')
