#!/usr/bin/env python3
"""Put a landscape photograph onto the portrait cover without cropping it away.

    python3 scripts/compose_cover.py --week 5 --art scfl-art-stafford.jpg

The cover slot is a 2:3 frame and build_issue.py paints the art into it with
`center/cover`, which means a 3:2 photograph gets centre-cropped to 2:3 -- for
the week 5 stadium that is the middle 533 of 1200 pixels, upscaled. Everything
that makes the picture work, the sweep of empty stands on one side and the
floodlights on the other, is outside that window.

So the photograph is not cropped to the frame. It is laid full width into a
portrait canvas and feathered top and bottom into the same near-black the house
cover already uses, which leaves the masthead sitting on clean sky above it and
the hook and cover lines on clean black below -- where they are legible, and
where they are not covering the picture. It is the same composition the drawn
covers use: one image floating in a dark field.

The graphics AI returns 3:2 because that is what the briefs in docs/ ask for.
If a cover is wanted at 2:3 natively, ask for it in the brief and drop the
file straight in -- this script is for when it arrives landscape.
"""
import argparse, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1024, 1536
INK = (11, 11, 15)


def feather(img, top, bottom):
    """Fade `top` px at the top and `bottom` px at the bottom into INK.

    A hard edge where a photograph stops reads as a photograph pasted onto a
    page. A fade over a couple of hundred pixels reads as the dark of the
    picture simply continuing, which is what the house cover looks like.
    """
    a = Image.new('L', img.size, 255)
    px = a.load()
    for y in range(img.size[1]):
        v = 255
        if top and y < top:
            v = int(255 * (y / top))
        if bottom and y >= img.size[1] - bottom:
            v = min(v, int(255 * ((img.size[1] - y) / bottom)))
        for x in range(img.size[0]):
            px[x, y] = v
    return a


def compose(art, out, top=240):
    """art (any aspect) -> a 1024x1536 cover at `out`. Returns the photo height."""
    src = Image.open(os.path.join(ROOT, art)).convert('RGB')
    w, h = src.size
    ph = round(h * W / w)                      # full width, nothing cropped sideways
    photo = src.resize((W, ph), Image.LANCZOS)

    cover = Image.new('RGB', (W, H), INK)
    cover.paste(photo, (0, top), feather(photo, 150, 260))
    p = os.path.join(ROOT, out)
    cover.save(p, quality=88, optimize=True)
    print(f'  {art} {w}x{h} -> {out} {W}x{H} '
          f'({os.path.getsize(p)//1024}kb, photo at y{top}-{top+ph})')
    return ph


def band(art, w, h, at=0.62):
    """The same photograph cropped to a w x h strip, for the share card.

    `at` is where in the vertical overflow the strip sits, 0 at the top. The
    card is wide and short where the cover is tall, so it keeps the lit half of
    the picture -- the floodlights and the field -- and loses the empty sky the
    cover has room for.
    """
    src = Image.open(os.path.join(ROOT, art)).convert('RGB')
    sw, sh = src.size
    s = max(w / sw, h / sh)
    im = src.resize((round(sw * s), round(sh * s)), Image.LANCZOS)
    y = round((im.size[1] - h) * at)
    return im.crop(((im.size[0] - w) // 2, y, (im.size[0] - w) // 2 + w, y + h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, required=True)
    ap.add_argument('--art', required=True, help='the photograph, any aspect')
    ap.add_argument('--top', type=int, default=240,
                    help='y of the photograph in the 1536-tall cover')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    compose(a.art, a.out or f'scfl-week-{a.week}-cover.jpg', a.top)


if __name__ == '__main__':
    main()
