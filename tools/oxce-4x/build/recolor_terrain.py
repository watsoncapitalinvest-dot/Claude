#!/usr/bin/env python3
"""Rebuild the ten X-COM tilesets this mod recolours, from the player's own game data.

    python3 -I build/recolor_terrain.py <X-COM TERRAIN dir> <mod TERRAIN dir>          # check
    python3 -I build/recolor_terrain.py <X-COM TERRAIN dir> <mod TERRAIN dir> --write  # rebuild

WHY THIS EXISTS

BRAIN, MARS, UFO1, U_BASE, U_BITS, U_DISEC2, U_EXT02, U_OPER2, U_PODS and
U_WALL02 are X-COM's own terrain art. The mod ships them recoloured - alien
purple into Joe grey - and the recoloured files were sitting in the mod folder
with no copy in the repository, because this repository is public and they are
derivative of the original game's art.

They turned out not to be artwork at all. The geometry is untouched: same frame
count, same 32x40 tiles, every pixel in the same place. The ONLY difference is
the palette index each pixel carries, and ONE global table of index -> index
reproduces them. Measured over 180,480 pixels across the four tilesets a
partial data install could be checked against: zero pixels where a single
global remap failed.

So the art never needed storing. The table does, and the table is ours.

WHAT IT DOES

Derives the remap from every tileset present in BOTH directories, refuses if
any pixel contradicts it, and reports how much of the mod it can account for.
With --write it regenerates the tilesets from the vanilla files and the table,
and re-reads each one to confirm it decodes to exactly what the mod had.

The .MCD beside each tileset is a byte copy of the original and is copied, not
generated: it holds tile behaviour, not pixels, and this mod does not change it.

RUN IT ON A FULL X-COM INSTALL. A partial one can only prove the tilesets it
actually contains; the rest are reported as unverified rather than assumed.
"""
import os, struct, sys

W, H = 32, 40

# The ten tilesets this mod recolours. Everything else in mod/TERRAIN has a
# Joe, Cobra or North-America name and is this project's own work.
SETS = ['BRAIN', 'MARS', 'UFO1', 'U_BASE', 'U_BITS',
        'U_DISEC2', 'U_EXT02', 'U_OPER2', 'U_PODS', 'U_WALL02']


def load_pck(pck, tab):
    """Decode a PCK into a list of W*H index arrays, using its TAB offsets."""
    t = open(tab, 'rb').read()
    d = open(pck, 'rb').read()
    # Frame 0 always sits at offset 0, so the first entry is zero either way.
    # In a 2-byte TAB the next two bytes are the START of entry 1, which makes
    # the first uint32 NONZERO; in a 4-byte TAB they are the rest of entry 0,
    # so it reads as zero. Getting this backwards reads a 27-frame UFO1.TAB as
    # 13 wide entries and throws on the short buffer.
    wide = len(t) >= 4 and struct.unpack('<I', t[:4])[0] == 0
    offs = (list(struct.unpack('<%dI' % (len(t) // 4), t)) if wide
            else list(struct.unpack('<%dH' % (len(t) // 2), t)))
    frames = []
    for o in offs:
        px = [0] * (W * H)
        p = o
        pos = d[p] * W                      # leading fully-blank rows
        p += 1
        while p < len(d) and d[p] != 255:
            v = d[p]; p += 1
            if v == 254:                    # run of transparent pixels
                pos += d[p]; p += 1
            else:
                if pos < W * H:
                    px[pos] = v
                pos += 1
        frames.append(px)
    return frames


def save_pck(frames, pck, tab):
    """Encode frames back into a PCK + TAB.

    Byte-identical output is NOT the goal and is not achievable: the original
    encoder's choice of run lengths is not recoverable, so the offsets in the
    TAB differ. What matters is that the pair decodes to the same pixels, and
    --write checks exactly that rather than comparing bytes.
    """
    blob = bytearray()
    offs = []
    for px in frames:
        offs.append(len(blob))
        skip = 0
        while skip < H and not any(px[skip * W:(skip + 1) * W]):
            skip += 1
        blob.append(skip)
        run = 0
        for i in range(skip * W, W * H):
            v = px[i]
            if v == 0:
                run += 1
                if run == 255:              # 254 carries a one-byte count
                    blob += bytes([254, 255]); run = 0
            else:
                if run:
                    blob += bytes([254, run]); run = 0
                blob.append(v)
        blob.append(255)
    wide = len(blob) > 0xFFFF
    packed = (struct.pack('<%dI' % len(offs), *offs) if wide
              else struct.pack('<%dH' % len(offs), *offs))
    open(pck, 'wb').write(bytes(blob))
    open(tab, 'wb').write(packed)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    VAN, MOD = sys.argv[1], sys.argv[2]
    write = '--write' in sys.argv[3:]

    remap, conflicts, pixels = {}, [], 0
    checked, missing = [], []

    for s in SETS:
        vp, vt = os.path.join(VAN, s + '.PCK'), os.path.join(VAN, s + '.TAB')
        mp, mt = os.path.join(MOD, s + '.PCK'), os.path.join(MOD, s + '.TAB')
        if not (os.path.exists(vp) and os.path.exists(mp)):
            missing.append(s)
            continue
        a, b = load_pck(vp, vt), load_pck(mp, mt)
        if len(a) != len(b):
            conflicts.append('%s: %d frames in the game data, %d in the mod'
                             % (s, len(a), len(b)))
            continue
        for x, y in zip(a, b):
            for u, v in zip(x, y):
                pixels += 1
                if u in remap:
                    if remap[u] != v:
                        conflicts.append('%s: index %d maps to both %d and %d'
                                         % (s, u, remap[u], v))
                else:
                    remap[u] = v
        checked.append(s)

    print('checked %d of %d tilesets against the game data: %s'
          % (len(checked), len(SETS), ', '.join(checked) or 'none'))
    if missing:
        print('NOT PRESENT in both directories, so unproven here: %s'
              % ', '.join(missing))
    print('%d pixels compared, %d source indices in the table, %d of them change'
          % (pixels, len(remap), sum(1 for k, v in remap.items() if k != v)))

    if conflicts:
        print('\nREFUSING: the recolour is not a single palette remap.')
        for c in conflicts[:10]:
            print('  ' + c)
        print('  (%d more)' % max(0, len(conflicts) - 10) if len(conflicts) > 10 else '')
        return 1
    if not checked:
        print('\nNothing could be compared. Point the first argument at the '
              'TERRAIN directory of a full X-COM install.')
        return 1
    print('no pixel contradicts a single global remap')

    if not write:
        print('\nnothing written - pass --write to rebuild the tilesets')
        return 0

    for s in SETS:
        vp, vt = os.path.join(VAN, s + '.PCK'), os.path.join(VAN, s + '.TAB')
        if not os.path.exists(vp):
            print('  skip %-10s no %s.PCK in the game data' % (s, s))
            continue
        frames = [[remap.get(v, v) for v in f] for f in load_pck(vp, vt)]
        mp, mt = os.path.join(MOD, s + '.PCK'), os.path.join(MOD, s + '.TAB')
        before = load_pck(mp, mt) if os.path.exists(mp) else None
        save_pck(frames, mp, mt)
        after = load_pck(mp, mt)
        if after != frames:
            print('  FAIL %-10s re-read does not match what was written' % s)
            return 1
        if before is not None and after != before:
            print('  FAIL %-10s differs from the tileset that was already there' % s)
            return 1
        mcd = os.path.join(VAN, s + '.MCD')
        if os.path.exists(mcd):
            open(os.path.join(MOD, s + '.MCD'), 'wb').write(open(mcd, 'rb').read())
        print('  ok   %-10s %3d frames%s' % (s, len(frames),
              ', identical to the one it replaced' if before is not None else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
