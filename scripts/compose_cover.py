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


def compose(art, out, top=240, inset=''):
    """art (any aspect) -> a 1024x1536 cover at `out`. Returns the photo height.

    A picture already taller than 2:3 is run full bleed and cropped to the
    frame, because that is what it was drawn for. A landscape one is laid in at
    full width and feathered into the black instead, so none of it is thrown
    away -- see the note at the top of this file.

    `inset` is a second picture, boxed and keylined in the upper right. An inset
    is how a magazine runs two pictures on one cover without either of them
    winning: the big one is the week, the small one is the other thing worth
    buying it for. It sits high, clear of the hook and the cover lines, which
    are composited over the bottom third by build_issue.py.
    """
    src = Image.open(os.path.join(ROOT, art)).convert('RGB')
    w, h = src.size
    cover = Image.new('RGB', (W, H), INK)

    if h / w >= 1.1:                           # portrait enough to carry the frame
        s = max(W / w, H / h)
        im = src.resize((round(w * s), round(h * s)), Image.LANCZOS)
        cover.paste(im, (-(im.size[0] - W) // 2, 0))
        ph, top = H, 0
    else:
        ph = round(h * W / w)                  # full width, nothing cropped sideways
        photo = src.resize((W, ph), Image.LANCZOS)
        cover.paste(photo, (0, top), feather(photo, 150, 260))

    if ph >= H:
        # A full-bleed figure is a worse bed for type than the black a laid-in
        # photograph leaves behind it, and build_issue.py composites the hook
        # and six cover lines over the bottom third. Its own scrim is tuned for
        # that black. This one is for a picture.
        sc = Image.new('L', (1, H))
        for y in range(H):
            t = max(0.0, (y - H * 0.52) / (H * 0.48))
            sc.putpixel((0, y), int(255 * min(0.62, t * t * 0.62)))
        cover = Image.composite(Image.new('RGB', (W, H), INK), cover,
                                sc.resize((W, H)))

    if inset:
        iw, ih, pad = 330, 220, 34
        strip = band(inset, iw, ih, 0.62)
        x, y = W - iw - pad, 268
        # a hairline key, so the inset reads as a second picture and not as a
        # hole punched in the first one
        cover.paste(Image.new('RGB', (iw + 6, ih + 6), (226, 226, 222)), (x - 3, y - 3))
        cover.paste(Image.new('RGB', (iw + 2, ih + 2), (11, 11, 15)), (x - 1, y - 1))
        cover.paste(strip, (x, y))

    p = os.path.join(ROOT, out)
    cover.save(p, quality=88, optimize=True)
    print(f'  {art} {w}x{h} -> {out} {W}x{H} '
          f'({os.path.getsize(p)//1024}kb, photo at y{top}-{top+ph}'
          + (f', inset {inset}' if inset else '') + ')')
    return ph


def band(art, w, h, at=0.62, focus=None, place=(0.79, 0.42), zoom=1.0):
    """The same photograph cropped to a w x h strip, for the share card.

    `at` is where in the vertical overflow the strip sits, 0 at the top. The
    card is wide and short where the cover is tall, so a landscape picture keeps
    the lit half -- the floodlights and the field -- and loses the empty sky the
    cover has room for.

    A centred crop is wrong for a portrait, though. The card's left 640 pixels
    are a near-solid panel carrying the headline, so a figure in the middle of
    the frame ends up behind the type. `focus` is where the subject is in the
    source, as fractions, and `place` is where to put him in the card -- right
    of the panel by default. `zoom` buys the room to move him there.
    """
    src = Image.open(os.path.join(ROOT, art)).convert('RGB')
    sw, sh = src.size
    s = max(w / sw, h / sh) * zoom
    im = src.resize((round(sw * s), round(sh * s)), Image.LANCZOS)
    if focus:
        clamp = lambda v, hi: max(0, min(round(v), hi))
        x = clamp(focus[0] * im.size[0] - place[0] * w, im.size[0] - w)
        y = clamp(focus[1] * im.size[1] - place[1] * h, im.size[1] - h)
    else:
        x = (im.size[0] - w) // 2
        y = round((im.size[1] - h) * at)
    return im.crop((x, y, x + w, y + h))


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
