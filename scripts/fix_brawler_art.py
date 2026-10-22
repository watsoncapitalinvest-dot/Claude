#!/usr/bin/env python3
"""Make the three SCFL brawler characters render as characters.

    python3 scripts/fix_brawler_art.py [--dry-run]

Repacks brawler-test/content/game-test.zip. Two bugs, both in the frames
built from the delivered team art, neither in anything that came with the
sample game.

1. THE BLOCK. OpenBOR treats palette index 0 as transparent. It does not
   read the GIF transparency chunk. Every sprite the sample ships puts its
   chroma colour at index 0 -- kabo is 106 frames for 106. The SCFL frames
   were chroma-keyed with the key left wherever the quantiser happened to put
   it (index 224 for Pork Chop Express, 1 for The Machines, 226 for Smoke
   Dragons) and an explicit transparency chunk written instead. So OpenBOR
   drew the key: a solid magenta or green rectangle, up to 196x192 of it on a
   320x240 screen. 155 of the 156 referenced frames did this. That is the
   "team art blocks the screen".

   Fixed by swapping palette entry 0 with the background entry and swapping
   those two indices through the pixel data, which is lossless, then saving
   without a transparency chunk so the file matches kabo's shape exactly.

2. THE SIZE AND THE ANCHOR. The art is 1.2x to 1.9x the height of everyone
   else in the game, and all three characters carry kabo's offsets verbatim
   -- the README says so, it was deliberate, and it does not survive the
   change of frame size. An offset is the pixel in the sprite that stands on
   the ground. Kabo's convention, measured off its own file, is 0.48 across
   the frame and 0.95 down it. Kabo's (27, 95) on a 153x192 Pork Chop Express
   frame is 0.14 across and 0.49 down, so the sprite drew two thirds of its
   width to the right of the man and half its height below the floor.

   Fixed by scaling each character so its idle height matches kabo's, and
   giving every frame its own offset at kabo's proportions. Bounding and
   attack boxes are kabo's numbers against kabo's 56x101 frame, so they are
   re-expressed against each new frame rather than left pointing at nothing.

Scaling uses NEAREST on purpose. These are palette sprites with one-bit
transparency; a smooth filter invents edge colours that a GIF cannot hold and
that OpenBOR would draw as fringe.

The 106 unreferenced kabo frames sitting in the Smoke Dragons folder are
dropped. Nothing loads them, and this file is a 33MB download that has
already been reported as hanging on a phone.
"""
import collections, io, os, re, shutil, subprocess, sys, zipfile
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAK = os.path.join(ROOT, 'brawler-test', 'content', 'game-test.zip')
CHARS = ('smokedragons', 'machines', 'porkchopexpress')
REF = 'kabo'                      # the cast's own yardstick, not a guess

# Kabo's anchor, read out of kabo.txt rather than chosen: offset 27,95 on a
# 56x101 stand frame, 25,104 on a 56x108 walk frame.
ANCHOR_X, ANCHOR_Y = 0.48, 0.95
# The frame kabo's boxes were authored against.
BOX_W, BOX_H = 56, 101

BOXY = re.compile(r'^(\s*)(bbox|attack\d?|hitbox|shock|burn|steal|freeze)\s+'
                  r'(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)(.*)$')
FRAME = re.compile(r'^(\s*)frame\s+(\S+)\s*$')
OFFSET = re.compile(r'^\s*offset\s+-?\d+\s+-?\d+\s*$')


def _keyish(rgb):
    """Is this a chroma key rather than a colour somebody meant to draw?

    Saturated magenta or green, which is what every sheet in this delivery
    was keyed with. Asking the colour is more reliable than asking the
    corners: The Machines' frames carry a dark border around the green field,
    so all four corners are border and a corner vote picks the wrong slot --
    which is how the first pass left that character still in a green box.
    """
    r, g, b = rgb
    if (r > 180 and g < 80 and b > 180) or (r < 80 and g > 180 and b > 180):
        return True                                  # magenta, cyan
    # Green, including the dull end of it. The guide dashes down The Machines'
    # cells survived every earlier pass because they are not (0,255,0) but
    # (8,77,35) and twenty neighbours of it -- the key, darkened by whatever
    # drew the guides. Counted across all 156 frames, every green-dominant
    # pixel in this delivery belongs to those dashes and none to a character:
    # the three are drawn in blue denim, red and bone. So green that is twice
    # its own red and twice its own blue is the key, light or dark.
    return g > 60 and g > 2 * r and g > 2 * b


def background_index(im):
    """The palette slot the art is keyed out to.

    The key is the colour that dominates a cropped sprite, and it has to look
    like a key: a frame whose commonest colour is a skin tone is a frame with
    no key in it, and swapping that to index 0 would delete the character
    instead of its background.
    """
    hist = im.histogram()
    pal = im.getpalette() or []
    rgb = lambda i: tuple(pal[i * 3:i * 3 + 3])
    ranked = sorted(range(min(256, len(pal) // 3)), key=lambda i: -hist[i])
    for i in ranked[:4]:
        if hist[i] and _keyish(rgb(i)):
            return i
    px, (w, h) = im.load(), im.size
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    guess = collections.Counter(corners).most_common(1)[0][0]
    return guess if _keyish(rgb(guess)) else 0


def key_to_index_0(im):
    """Put the key at palette index 0, and every other shade of it with it.

    Swapping the one dominant index is not enough. A quantiser given a keyed
    sheet spreads the key across several near-identical slots, and the ones it
    leaves behind are exactly the thin dashed guides down The Machines' cells:
    chroma green, at a green index that was never index 0, surviving every
    pass that looked for shapes instead of colours. Every key-coloured slot is
    folded into 0 here, which is lossless for these characters -- none of the
    three is drawn in saturated magenta, green or cyan.

    Returns None when the frame already had it right, so a correct frame is
    left byte-identical.
    """
    bg = background_index(im)
    pal0 = im.getpalette() or []
    extra = [i for i in range(len(pal0) // 3)
             if i not in (0, bg) and _keyish(tuple(pal0[i * 3:i * 3 + 3]))]
    if bg == 0 and not extra:
        return None
    if bg == 0:
        out = im.copy()
        table = list(range(256))
        for i in extra:
            table[i] = 0
        raw = im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata()
        out.putdata(bytes(table[p] for p in raw))
        return out
    pal = list(im.getpalette())
    for c in range(3):
        pal[c], pal[bg * 3 + c] = pal[bg * 3 + c], pal[c]
    out = im.copy()
    out.putpalette(pal)
    # swap the two indices through the pixel data
    table = list(range(256))
    table[0], table[bg] = bg, 0
    for i in extra:
        table[i] = 0
    raw = im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata()
    out.putdata(bytes(table[p] for p in raw))
    return out


def strip_furniture(im):
    """Delete the ruled lines the crop caught from the art sheet.

    The delivered sheets had the characters in panels, and the crop window
    took a slice of panel edge with several of them: a bar down both sides of
    The Machines, a bar over the top of Smoke Dragons, a rule under Pork Chop
    Express. They are opaque, so in game they float beside the character.

    Removed by connected component rather than by colour, because the colours
    involved -- near-black, dark purple -- are colours the characters are also
    drawn in, and a colour rule would punch holes in a pair of jeans. A
    component only goes if it is separate from the character, touches the
    frame edge, and lies outside the character's own bounding box.

    That last test is the one that works, and it took three tries to find.
    The furniture is not one shape: a 12px slab down The Machines, a 4px rule
    under Pork Chop Express, a ring over two sides of Smoke Dragons, and --
    the part that made a thickness rule hopeless -- whole vertical slices of
    the NEXT sprite along, because the crop windows were wider than the cells
    on the sheet. A slice of another pose is not thin and does not span an
    edge; what it is, always, is somewhere the character is not.

    So the character is whatever is connected to the largest mass of pixels,
    anything inside its box stays (Smoke Dragons breathes smoke that does not
    touch him), and anything outside it that runs to the frame edge goes.

    Returns the image, the pixels removed, and the character's bounding box,
    which is where the anchor comes from once the rest is gone.
    """
    w, h = im.size
    raw = im.get_flattened_data() if hasattr(im, 'get_flattened_data') else list(im.getdata())
    px = list(raw)
    killed_edge = 0

    # First the ruled frame, which components alone cannot touch. The Machines'
    # panel is a closed rectangle of bars, and wherever his elbow reaches it
    # the bars become part of his own component -- one connected blob of man
    # and furniture that no later test can separate. So the edges are peeled
    # first, inward, while a row or column is nearly solid AND nearly one
    # colour. A drawn figure does not fill an entire frame edge in a single
    # flat tone; a ruled line is nothing else.
    pal = im.getpalette() or []
    # near-identical colours counted as one. The Machines' bars are a band of
    # near-black noise -- (0,1,2), (0,0,1), (1,1,2) and a dozen more -- so
    # counting palette entries called a flat bar eleven different colours and
    # left every one of them on screen.
    bucket = [tuple(v // 24 for v in pal[i * 3:i * 3 + 3]) if pal[i * 3:i * 3 + 3]
              else (0, 0, 0) for i in range(256)]

    def peel(get, put, n, across):
        nonlocal killed_edge
        for k in range(n):
            vals = [get(k, j) for j in range(across)]
            solid = sum(1 for v in vals if v) / across
            tones = len({bucket[v] for v in vals if v})
            if solid < 0.8 or tones > 2:
                return
            for j in range(across):
                put(k, j)
            killed_edge += sum(1 for v in vals if v)

    peel(lambda y, x: px[y * w + x], lambda y, x: px.__setitem__(y * w + x, 0), h // 4, w)
    peel(lambda y, x: px[(h - 1 - y) * w + x],
         lambda y, x: px.__setitem__((h - 1 - y) * w + x, 0), h // 4, w)
    peel(lambda x, y: px[y * w + x], lambda x, y: px.__setitem__(y * w + x, 0), w // 4, h)
    peel(lambda x, y: px[y * w + (w - 1 - x)],
         lambda x, y: px.__setitem__(y * w + (w - 1 - x), 0), w // 4, h)

    # Then the rules that do not run along an edge. The Machines' panel has
    # lines through the middle of the cell as well as round it, and in several
    # frames they touch him -- jump_04 is one single connected blob of man and
    # green rule, so no component test can ever separate the two. A rule is
    # recognised instead by what it is: a row or column that is almost solid
    # and almost one colour, anywhere in the frame. A column drawn through a
    # character is neither; across all 156 frames this fires on Machines and
    # on nothing else, which is the right answer, because his are the only
    # cells with rules inside them.
    def rules(n, across, at):
        out = []
        for k in range(n):
            vals = [px[at(k, j)] for j in range(across)]
            opaque = [v for v in vals if v]
            if len(opaque) >= 0.85 * across and len({bucket[v] for v in opaque}) <= 2:
                out.append(k)
        return out

    for x in rules(w, h, lambda x, y: y * w + x):
        for y in range(h):
            if px[y * w + x]:
                px[y * w + x] = 0
                killed_edge += 1
    for y in rules(h, w, lambda y, x: y * w + x):
        for x in range(w):
            if px[y * w + x]:
                px[y * w + x] = 0
                killed_edge += 1

    lab = [-1] * (w * h)
    comps = []
    for start in range(w * h):
        if px[start] == 0 or lab[start] != -1:
            continue
        cid = len(comps)
        stack, cells = [start], []
        lab[start] = cid
        while stack:
            i = stack.pop()
            cells.append(i)
            x, y = i % w, i // w
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    j = ny * w + nx
                    if px[j] != 0 and lab[j] == -1:
                        lab[j] = cid
                        stack.append(j)
        xs = [i % w for i in cells]
        ys = [i // w for i in cells]
        comps.append((cells, min(xs), min(ys), max(xs), max(ys)))
    if not comps:
        return im, killed_edge
    body = max(range(len(comps)), key=lambda c: len(comps[c][0]))
    bx0, by0, bx1, by1 = comps[body][1:]
    killed = killed_edge
    for cid, (cells, x0, y0, x1, y1) in enumerate(comps):
        if cid == body:
            continue
        inside = bx0 <= x0 and by0 <= y0 and x1 <= bx1 and y1 <= by1
        touches = x0 == 0 or y0 == 0 or x1 == w - 1 or y1 == h - 1
        slight = len(cells) < 0.2 * len(comps[body][0])
        # outside his box, or inside it and far too small to be any part of
        # him: a lunge stretches the box over the whole frame, so the bars and
        # the neighbour's elbow end up "inside" it without being him
        if touches and (not inside or slight):
            for i in cells:
                px[i] = 0
            killed += len(cells)
    if not killed:
        return im, 0, (bx0, by0, bx1, by1)
    out = im.copy()
    out.putdata(bytes(px))
    return out, killed, (bx0, by0, bx1, by1)


def measure(d, names, stem):
    """A character's standing height, from the frames its model calls idle."""
    hs = [Image.open(os.path.join(d, n)).size[1]
          for n in names if os.path.basename(n).startswith(stem)]
    if not hs:
        hs = [Image.open(os.path.join(d, n)).size[1] for n in names]
    hs.sort()
    return hs[len(hs) // 2]


def rewrite(text, sizes, anchors):
    """Per-frame offsets at kabo's proportions, and boxes re-expressed against
    the frame they now belong to.

    The boxes are kabo's. Dropping them would lose the sample's tuning; leaving
    them would point them at coordinates that no longer exist on these frames.
    Mapping them proportionally keeps the intent and lands them on the body.
    """
    lines = text.split('\n')
    # what size is the next frame after each line
    nxt, cur = [None] * len(lines), None
    for i in range(len(lines) - 1, -1, -1):
        m = FRAME.match(lines[i])
        if m:
            cur = sizes.get(m.group(2))
        nxt[i] = cur
    out = []
    for i, line in enumerate(lines):
        if OFFSET.match(line):
            continue                       # replaced per frame, below
        m = BOXY.match(line)
        if m and nxt[i]:
            w, h = nxt[i]
            sx, sy = w / BOX_W, h / BOX_H
            x, y, bw, bh = (int(m.group(k)) for k in (3, 4, 5, 6))
            out.append(f'{m.group(1)}{m.group(2)}\t{round(x * sx)} {round(y * sy)} '
                       f'{round(bw * sx)} {round(bh * sy)}{m.group(7)}')
            continue
        m = FRAME.match(line)
        if m and sizes.get(m.group(2)):
            ax, ay = anchors[m.group(2)]
            out.append(f'{m.group(1)}offset\t{ax} {ay}')
        out.append(line)
    return '\n'.join(out)


def build(dry=False):
    work = os.path.join(ROOT, '.brawler-work')
    shutil.rmtree(work, ignore_errors=True)
    with zipfile.ZipFile(PAK) as z:
        z.extractall(work)
        order = z.namelist()

    ref_dir = os.path.join(work, 'data', 'chars', REF)
    ref_h = measure(ref_dir, sorted(os.listdir(ref_dir)), 'stand')
    print(f'{REF} stands {ref_h}px tall -- the cast\'s yardstick')

    report = []
    for c in CHARS:
        d = os.path.join(work, 'data', 'chars', c)
        tpath = os.path.join(d, f'{c}.txt')
        text = open(tpath, encoding='latin-1').read()
        used = [f for f in re.findall(r'^\s*frame\s+(\S+)', text, re.M)]
        used = [u for u in used if os.path.exists(os.path.join(work, u))]
        basenames = {os.path.basename(u) for u in used}

        before = measure(d, sorted(basenames), 'idle')
        scale = ref_h / before
        keyed = resized = trimmed = 0
        sizes, anchors = {}, {}
        for u in used:
            p = os.path.join(work, u)
            im = Image.open(p)
            fixed = key_to_index_0(im)
            if fixed is not None:
                im, keyed = fixed, keyed + 1
            im, cut, body = strip_furniture(im)
            trimmed += 1 if cut else 0
            if abs(scale - 1) > 0.02:
                w, h = im.size
                im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))),
                               Image.NEAREST)
                resized += 1
            # the anchor comes off the character, not off the canvas: kabo
            # stands at 0.48 across its body and 5 per cent up from the sole,
            # and that is reproduced here against the body this frame actually
            # draws rather than against whatever the crop window left round it
            k = scale if abs(scale - 1) > 0.02 else 1
            bx0, by0, bx1, by1 = (round(v * k) for v in body)
            bh = max(1, by1 - by0 + 1)
            sizes[u] = im.size
            anchors[u] = (round((bx0 + bx1) / 2), round(by1 - 0.05 * bh))
            if not dry:
                im.save(p, 'GIF')            # no transparency chunk, like kabo
        if not dry:
            open(tpath, 'w', encoding='latin-1').write(rewrite(text, sizes, anchors))

        # the sample's own frames, left in this folder and called by nothing
        dead = [f for f in os.listdir(d)
                if f.endswith('.gif') and f not in basenames
                and not f.endswith('_portrait.gif')]
        if not dry:
            for f in dead:
                os.remove(os.path.join(d, f))
        after = measure(d, sorted(basenames), 'idle') if dry else round(before * scale)
        report.append((c, len(used), keyed, before, round(before * scale), len(dead)))
        print(f'  {c:17} {len(used):3} frames  keyed {keyed:3}  '
              f'furniture off {trimmed:3}  {before}px -> {round(before * scale)}px '
              f'(x{scale:.2f})  dropped {len(dead)} unused')

    if dry:
        print('\n--dry-run: nothing written')
        shutil.rmtree(work, ignore_errors=True)
        return report

    tmp = PAK + '.tmp'
    old = os.path.getsize(PAK)
    # The directory entries matter. The loader walks the archive and writes
    # each entry into an in-memory filesystem, and it makes a folder when it
    # meets one rather than inferring it from a path -- so a repack that keeps
    # only the files produces 850 "Error writing file" lines and a game that
    # never starts. The first version of this script did exactly that.
    with zipfile.ZipFile(PAK) as src:
        info = {i.filename: i for i in src.infolist()}
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in order:
            if name.endswith('/'):
                z.writestr(info[name], b'')
                continue
            p = os.path.join(work, name)
            if os.path.exists(p) and os.path.isfile(p):
                z.write(p, name)
    os.replace(tmp, PAK)
    shutil.rmtree(work, ignore_errors=True)
    new = os.path.getsize(PAK)
    print(f'\nrepacked {os.path.relpath(PAK, ROOT)}  '
          f'{old / 1e6:.1f}MB -> {new / 1e6:.1f}MB')
    return report


if __name__ == '__main__':
    build(dry='--dry-run' in sys.argv)
