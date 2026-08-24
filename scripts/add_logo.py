#!/usr/bin/env python3
"""Install a team logo into the app.

The app reads scfl-team-logos-resized.json — a flat {slug: dataURI} map of
160x160 PNGs — so a new logo has to be resized and embedded there, not just
dropped in the repo root. scfl-team-logos.json keeps the full-size original.

    python3 scripts/add_logo.py wookieleaks path/to/wookie.png

Slugs are the keys already in scfl-team-logos-resized.json; run with no
arguments to list them and show which teams are still on a default avatar.
"""
import base64, hashlib, io, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESIZED = os.path.join(ROOT, 'scfl-team-logos-resized.json')
FULL = os.path.join(ROOT, 'scfl-team-logos.json')
SIZE = 160

# The stock ESPN avatar, by content hash. Teams still carrying it have no logo.
DEFAULTS = {}


def load(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def report():
    small = load(RESIZED)
    seen = {}
    for slug, uri in small.items():
        seen.setdefault(hashlib.md5(uri.encode()).hexdigest(), []).append(slug)
    print(f'{len(small)} teams in {os.path.basename(RESIZED)}:\n')
    for slug in small:
        dupes = [g for g in seen[hashlib.md5(small[slug].encode()).hexdigest()]]
        flag = '  <- shares art with ' + ', '.join(s for s in dupes if s != slug) if len(dupes) > 1 else ''
        print(f'  {slug}{flag}')
    print('\nusage: python3 scripts/add_logo.py <slug> <image-file>')


def main():
    if len(sys.argv) < 3:
        report()
        return 0
    slug, src = sys.argv[1], sys.argv[2]
    small = load(RESIZED)
    if slug not in small:
        sys.exit(f'unknown slug {slug!r} — run with no arguments to list them')
    if not os.path.exists(src):
        sys.exit(f'no such file: {src}')

    from PIL import Image
    im = Image.open(src).convert('RGBA')
    im.thumbnail((SIZE, SIZE), Image.LANCZOS)
    canvas = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(im, ((SIZE - im.width) // 2, (SIZE - im.height) // 2), im)
    buf = io.BytesIO()
    canvas.save(buf, 'PNG', optimize=True)
    small[slug] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
    with open(RESIZED, 'w', encoding='utf-8') as fh:
        json.dump(small, fh)
    print(f'{os.path.basename(RESIZED)}: {slug} <- {src} ({canvas.size[0]}x{canvas.size[1]}, {len(buf.getvalue())}b)')

    # Keep the full-size original alongside it when that file carries this team.
    if os.path.exists(FULL):
        full = load(FULL)
        logos = full.get('logos', {})
        key = next((k for k in logos if ''.join(c for c in k.lower() if c.isalnum()).replace('the', '') ==
                    slug.replace('the', '')), None)
        if key:
            raw = open(src, 'rb').read()
            ext = 'png' if raw[:8] == b'\x89PNG\r\n\x1a\n' else ('webp' if raw[:4] == b'RIFF' else 'jpeg')
            logos[key] = {'data': f'data:image/{ext};base64,' + base64.b64encode(raw).decode()}
            with open(FULL, 'w', encoding='utf-8') as fh:
                json.dump(full, fh)
            print(f'{os.path.basename(FULL)}: {key} <- full-size original')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
