# Base view facilities — what is built, and the one thing still missing

Built 11 Nov from John's facility art package. 137 sprite frames for 104 rooms,
in `mod/Resources/Base/facilities/`, wired by `mod/Ruleset/gijoe_base_facilities.rul`
at BASEBITS indices 100–236.

## The art is derived from the package's data, not from its pictures

The package ships 109 isometric room renders and the generator that made them.
The renders are the wrong projection for this: **vanilla base-view facilities are
top-down**, and an isometric block fitted into a square comes out as a diamond that
fights the grid and leaves the plate showing through above and below. Tried, looked
wrong, not used.

What is used is the generator's own placement data. `packer.place(r, name, x, y, w, d)`
is called once per prop with its tile footprint, so wrapping it harvests every room's
contents exactly: **104 rooms, 2,146 placements, 119 prop types, 0 failures**.
`build/harvest_placements.py` does that and writes the table.

**`specials.py` does `from packer import *`**, and `specs.py` does `from specials import *`,
so each module holds its own binding of `place` taken at import time. Patching
`packer.place` alone records the ordinary rooms and **silently misses every room built
by a special** — hangars, motor pools, reactors, ranges. All three are patched.

## A faithful plan does not read, and no amount of polish fixes it

The first version drew the harvested plan straight: floor, props at their real tile
positions, outer wall. Every sprite came out a near-empty square with clutter round
the rim, and they were indistinguishable from one another.

Two reasons, both structural. Ten tiles to a 32px square is **3.2 pixels per tile**, so
a 1×1 prop is a three-pixel block. And real rooms line their furniture along the walls,
so the middle of an honest plan is empty. Vanilla's sprites are not plans — they are
emblems that fill the square: rows of beds, a radar dish, hazard stripes.

So the room's **contents** pick the emblem, which keeps it derived rather than drawn.
A plain count picks the wrong prop, because `crates` appears 202 times across the set
and identifies nothing; each prop is weighted against how many rooms contain it:

| room | signature |
| --- | --- |
| `j_bunks` | cot ×8 |
| `j_archives` | bookshelf ×9, filing ×8, safe ×3 |
| `j_infirmary` | medcab ×7, hbed ×5 |
| `j_detention` | lockers ×6, toilet ×3, cellbunk ×3 |
| `c_reactor` | drums_toxic ×6, panel ×6 |
| `j_training` | bag ×16, weights ×11, mat ×5 |

The primary is tiled to fill the square with its own footprint's aspect, the secondary
runs as a band along the bottom edge.

## Two things that were got wrong first, and cost a pass each

- **`PALETTES.DAT` is five palettes at a 774-byte stride**, 768 plus six bytes of
  padding — not 768 flat. Read flat, no palette matches anything. Read correctly,
  **palette 1 matches the project's existing base art 768/768**, so the frames are
  indexed against it and there is no colour drift. Index 0 is the transparent cut.
- **The reference was rendered with the wrong palette.** An early BASEBITS contact
  sheet used palette 0, which made vanilla look olive, so a lavender floor got
  "corrected" that was already right: **index 72, rgb(120,112,148), is the single
  most-used colour in vanilla's facility frames.** Check the reference before
  trusting a judgement made against it.

Colours snap only to the **139 indices vanilla's own facility frames use**, by the
redmean weighting. Quantising against the whole 256 is what let the globe markers
pick white for a gold line; same restriction, same fix.

## The plate must show through

The engine draws `spriteShape` first and `spriteFacility` on top. Art that is opaque
to the edge hides the plate completely, every facility butts against its neighbour
with no boundary, and the base reads as one grey field. The art is inset 2px with the
corners cut back — but **only on sides facing out of the whole facility**, so the four
squares of a 2×2 still meet flush and a hangar reads as one room.

## What is missing: the facilities themselves

**The mod defines no `facilities:` at all** — it inherits vanilla's wholesale, and the
seven older `facility_*.png` in `mod/Resources/Base/` were never wired to anything.
So these 137 frames are loaded and currently unused.

Writing 104 facility definitions means costs, build times, upkeep, prerequisites and
provided capacities. **Those are design numbers and are John's, not this desk's** —
inventing them is exactly how the weapon ladder ended up three calendar bands too
high. `build/baseview_frames.json` maps each room id to its first frame index, frame
count and size, so the definitions can be generated once the numbers exist.
