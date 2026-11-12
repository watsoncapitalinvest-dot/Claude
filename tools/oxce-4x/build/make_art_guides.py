#!/usr/bin/env python3
"""Guide images that go to the graphics AI with each brief: the canvas, drawn.

    python3 build/make_art_guides.py <out dir>

A brief says "12-pixel margin, door at the middle of every edge, head at 40";
a guide shows it. Each is the exact canvas size the brief asks for, magenta
where the background goes, with the fixed lines drawn in. They are references
to lay the work over, never to paint on.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

MAG = (255, 0, 255)
ROOM = (120, 124, 112)
WALL = (70, 74, 64)
DOOR = (0, 230, 255)
LINE = (255, 210, 0)
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf', 18)
SQ, MARGIN, WALLW, DOORW = 192, 12, 18, 48


def room_guide(wsq, hsq):
    W, H = wsq * SQ, hsq * SQ
    im = Image.new('RGB', (W, H), MAG)
    d = ImageDraw.Draw(im)
    m, c = MARGIN, MARGIN
    outer = [(m + c, m), (W - m - c, m), (W - m, m + c), (W - m, H - m - c),
             (W - m - c, H - m), (m + c, H - m), (m, H - m - c), (m, m + c)]
    d.polygon(outer, fill=WALL)
    w = WALLW
    inner = [(m + c + w * 0.6, m + w), (W - m - c - w * 0.6, m + w), (W - m - w, m + c + w * 0.6),
             (W - m - w, H - m - c - w * 0.6), (W - m - c - w * 0.6, H - m - w), (m + c + w * 0.6, H - m - w),
             (m + w, H - m - c - w * 0.6), (m + w, m + c + w * 0.6)]
    d.polygon(inner, fill=ROOM)
    # a door at the middle of every outside edge of every square
    for i in range(wsq):
        cx = i * SQ + SQ // 2
        d.rectangle([cx - DOORW // 2, m, cx + DOORW // 2, m + w], fill=DOOR)
        d.rectangle([cx - DOORW // 2, H - m - w, cx + DOORW // 2, H - m], fill=DOOR)
    for j in range(hsq):
        cy = j * SQ + SQ // 2
        d.rectangle([m, cy - DOORW // 2, m + w, cy + DOORW // 2], fill=DOOR)
        d.rectangle([W - m - w, cy - DOORW // 2, W - m, cy + DOORW // 2], fill=DOOR)
    # the floor zone that must stay empty and even
    fx, fy = (W - 2 * (m + w)) * 0.1, (H - 2 * (m + w)) * 0.1
    d.rectangle([m + w + fx, m + w + fy, W - m - w - fx, H - m - w - fy], outline=LINE, width=2)
    d.text((m + w + fx + 6, m + w + fy + 4), 'keep empty and even', font=FONT, fill=LINE)
    d.text((m + w + 6, H - m - w - 26), '%dx%d  %dx%d px' % (wsq, hsq, W, H), font=FONT, fill=(30, 30, 30))
    return im


def figure_guide():
    W, H = 640, 1600
    im = Image.new('RGB', (W, H), MAG)
    d = ImageDraw.Draw(im)
    d.line([(0, 40), (W, 40)], fill=LINE, width=3)
    d.line([(0, 1560), (W, 1560)], fill=LINE, width=3)
    d.line([(W // 2, 0), (W // 2, H)], fill=DOOR, width=2)
    d.text((10, 46), 'top of head / helmet: 40 px', font=FONT, fill=LINE)
    d.text((10, 1566), 'soles of the boots: 1560 px', font=FONT, fill=LINE)
    d.text((W // 2 + 8, 800), 'centre', font=FONT, fill=DOOR)
    return im


def topview_guide():
    S = 1024
    im = Image.new('RGB', (S, S), MAG)
    d = ImageDraw.Draw(im)
    f = S * 0.85
    d.rectangle([(S - f) / 2, (S - f) / 2, (S + f) / 2, (S + f) / 2], outline=LINE, width=3)
    d.line([(S // 2, 0), (S // 2, S)], fill=DOOR, width=2)
    d.line([(0, S // 2), (S, S // 2)], fill=DOOR, width=1)
    d.polygon([(S // 2, 8), (S // 2 - 22, 52), (S // 2 + 22, 52)], fill=DOOR)
    d.text((S // 2 + 30, 18), 'NOSE UP', font=FONT, fill=DOOR)
    d.text(((S - f) / 2 + 8, (S - f) / 2 + 6), 'widest span reaches this box (85%)', font=FONT, fill=LINE)
    d.text((S // 2 + 8, S - 40), 'mirror-symmetrical about this line', font=FONT, fill=DOOR)
    return im


def main(out):
    os.makedirs(out, exist_ok=True)
    for w, h in ((1, 1), (2, 1), (1, 2), (2, 2)):
        room_guide(w, h).save(os.path.join(out, 'guide_room_%dx%d.png' % (w, h)))
    figure_guide().save(os.path.join(out, 'guide_inventory_figure_640x1600.png'))
    topview_guide().save(os.path.join(out, 'guide_craft_top_1024.png'))
    print('guides written to', out)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'art_briefs/guides')
