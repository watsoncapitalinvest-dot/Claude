#!/usr/bin/env python3
"""The issue number, set on a finished cover.

    python3 scripts/cover_number.py --cover scfl-week-7-cover.jpg --week 7
    python3 scripts/cover_number.py --cover x.jpg --week 1 --league "Ten Man PPR"

A magazine always has an issue number, and a league in its first week has
nothing else to put on a cover: no lead changes, no comeback, no history. So
the number is the one piece of cover furniture that is always available and
always true, which makes it the default the app can set on any plate -- the
one that ships with the product, John's own art, or a league's upload.

The app does not GENERATE art. It sets type on a plate it was given. No model,
no key, no bill, nothing that can fail because somebody's API quota ran out.

WHY IT RUNS LAST

The first version set the number on the art plate and handed that to
compose_cover, whose 270px drop then cropped the numeral clean off the bottom
of the page. The number is furniture, not picture: it goes on the finished
1024x1536 frame, where its position is identical on every cover whatever the
art underneath is doing. That is also what makes it safe on an upload nobody
at this desk has ever seen.

WHAT THE PLATE HAS TO LEAVE CLEAR

  - the top 35 per cent, for the masthead. Every cover brief here says so
  - the bottom right, for the number, if `corner` is used

`band` needs neither: it lays its own strip across the foot and never touches
the picture. It is the safe choice for an arbitrary upload and the duller one.
"""
import argparse, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREAM, GOLD = '#fffdfb', '#d8b45a'

# DejaVu ships with every Linux runner this is ever going to run on. A missing
# font is not a reason to fail a cover, so a fallback walks a few candidates
# and only then gives up on the number rather than on the issue.
FONTS = ('/usr/share/fonts/truetype/dejavu/DejaVu%s.ttf',
         '/usr/share/fonts/truetype/liberation/Liberation%s.ttf')
MAP = {'Sans-Bold': ('Sans-Bold', 'Sans-Bold'), 'Serif-Bold': ('Serif-Bold', 'Serif-Bold')}


def font(kind, size):
    for pat in FONTS:
        p = pat % MAP[kind][0 if 'DejaVu' in pat else 1]
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def pool(img, box, strength=175, blur=95):
    """A soft dark pool under the type.

    Art is not a flat colour and the number has to hold whatever it lands on --
    the same reason compose_cover puts a scrim under the masthead. Soft-edged,
    because a hard box reads as a sticker.
    """
    w, h = img.size
    lay = Image.new('L', (w, h), 0)
    ImageDraw.Draw(lay).ellipse(box, fill=strength)
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    return Image.composite(Image.new('RGB', (w, h), (10, 10, 13)), img, lay)


def corner(img, week, league, season):
    """Number low-right, league along the foot. Sits in the art."""
    w, h = img.size
    img = pool(img, (w * 0.42, h * 0.60, w * 1.18, h * 1.10))
    d = ImageDraw.Draw(img, 'RGBA')
    d.text((w * 0.935, h * 0.805), 'WEEK', font=font('Sans-Bold', int(h * 0.040)),
           fill=GOLD, anchor='rm')
    d.text((w * 0.955, h * 0.893), str(week), font=font('Serif-Bold', int(h * 0.175)),
           fill=CREAM, anchor='rm')
    d.text((w * 0.045, h * 0.955), league.upper(), font=font('Sans-Bold', int(h * 0.030)),
           fill=CREAM, anchor='lm')
    if season:
        d.text((w * 0.045, h * 0.982), str(season), font=font('Sans-Bold', int(h * 0.023)),
               fill=(255, 255, 255, 165), anchor='lm')
    return img


def band(img, week, league, season):
    """Number on a foot band. Never touches the picture at all."""
    w, h = img.size
    bh = int(h * 0.135)
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, h - bh, w, h], fill=(16, 17, 21, 244))
    d.line([(0, h - bh), (w, h - bh)], fill=GOLD, width=4)
    cy = h - bh // 2
    d.text((w * 0.055, cy - int(bh * 0.17)), 'WEEK', font=font('Sans-Bold', int(bh * 0.27)),
           fill=GOLD, anchor='lm')
    d.text((w * 0.055, cy + int(bh * 0.21)), league.upper(),
           font=font('Sans-Bold', int(bh * 0.21)), fill=(255, 255, 255, 190), anchor='lm')
    d.text((w * 0.945, cy), str(week), font=font('Serif-Bold', int(bh * 0.95)),
           fill=CREAM, anchor='rm')
    return img


PLACE = {'corner': corner, 'band': band}


def number(cover, week, league='', season='', place='corner', out=None):
    """Set the issue number on `cover`. Returns the path written."""
    img = Image.open(cover).convert('RGB')
    img = PLACE[place](img, week, league, season)
    out = out or cover
    img.save(out, quality=92)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cover', required=True, help='the finished cover to set the number on')
    ap.add_argument('--week', required=True, type=int)
    ap.add_argument('--league', default='')
    ap.add_argument('--season', default='')
    ap.add_argument('--place', default='corner', choices=sorted(PLACE))
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    src = a.cover if os.path.isabs(a.cover) else os.path.join(ROOT, a.cover)
    if not os.path.exists(src):
        sys.exit(f'no such cover: {src}')
    out = number(src, a.week, a.league, a.season, a.place,
                 a.out and (a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)))
    print(f'  week {a.week} set on {os.path.basename(out)} ({a.place})')


if __name__ == '__main__':
    main()
