# G.I. Joe 4x — what the fork changes, and why

Save point: 10 Nov 2026, the Cobra planner and wall penetration. `oxce_4x.patch` touches 68 files
and adds ~2,900 lines. The head is whatever `claude/oxce-gijoe-4x` points at — a hash recorded
here goes stale the moment the next commit lands, and `git log -- tools/oxce-4x/oxce_4x.patch`
answers the question properly.

The fork is a patch against OXCE commit `f0134ef`, not a copy of the engine, so it tracks
upstream instead of drifting. `.github/workflows/build-oxce-4x.yml` applies it and builds
`OpenXcom.exe` on Windows in 8–11 minutes; the exe lands on branch `claude/oxce-gijoe-4x-bin`.

Tag pushes are rejected by this remote (HTTP 403). Roll back by commit hash.

## Switches, all read from the environment

| Variable | Default | What it does |
| --- | --- | --- |
| `OXCE_MAP_HIRES` | 1 | 4 turns on the 4x battlefield |
| `OXCE_BATTLE_SCALE` | 1 | upscale factor for battlescape sprite sets |
| `OXCE_HICOLOR` | follows the above | 0 falls back to the 256-colour palette |
| `OXCE_HIUI` | follows HiColor | 0 leaves the menus 8-bit |
| `OXCE_BULLET_SCALE` | battle scale | total upscale for projectiles (local only, not pushed) |

## The two new files

**`src/Engine/HiColor.cpp`** — full colour on the battlefield. The engine still draws 8-bit.
A sprite that has a registered 32-bit twin also writes true colour into an overlay plus a *tag*,
the 8-bit index it left behind. At composite time a pixel shows the overlay only while its 8-bit
value still equals its tag, so anything drawn on top — units, smoke, the cursor — falls back
automatically with no z-ordering work. Non-opaque source pixels blend over whatever full-colour
pixel is underneath, which is what makes soft edges and ground shadows work.

**`src/Engine/HiUI.cpp`** — menus at display resolution. Same tag trick, applied per widget in
`State::blit`. Knows Window, TextButton, ComboBox, Slider, Frame, ArrowButton and Text.

## Things that cost time to find, recorded so they are not re-learned

**A set's frames are rebuilt after the mod loads.** Registering a sharp twin against a
`Surface*` captured during `ExtraSprites` silently fails: by the time anything is drawn the
pointer is stale. Both `HiUI::registerSetFrame` and `HiColor::registerSetFrame` therefore
remember *(set, frame index, file)* and resolve on first use — HiUI at the first `sprite()`
call, HiColor at the first `beginLayer`.

**PNG colour is sRGB, the vertex/overlay buffers are linear.** Passing 0–255 values straight
through washes everything out. `THREE.SRGBColorSpace` on the three.js side, and the same care
in the compositors.

**Frame is a rim, not a fill.** Filling a Frame widget's interior hides every list drawn inside
it. It claims only its rim rows and columns.

**ComboBox children already hold absolute coordinates.** Adding the parent's offset makes the
text vanish.

**Projectiles are the one battlescape set nobody scales.** `HIT.PCK` and `X1.PCK` are upscaled
in `loadVanillaResources`, but the Projectiles set is created empty there and filled later by
the mods, so the upscale pass misses it. On a 4x battlefield a bullet stayed three pixels
against a 128-pixel tile, and a laser — drawn as 35 sprites strung along the flight path — was
a thread of dots. Now scaled in `Mod::loadAll` once the frames are in.

**`BULLET_SPRITES` is 35, and they are 35 *different* frames, not 35 copies.** This note
previously said copies and that was wrong. `loadSpriteOffset(..., "Projectiles", 35)` makes 35 a
multiplier, so `bulletSprite: 1` means frames 35..69. Vanilla's sheet is 105x33 at subX/subY 3,
which is 35 columns by 11 rows: one row per weapon, frame 0 the head and frames 1..34 a thinning
tail of single pixels.

**A projectile sprite is never rotated.** `Map.cpp` blits it centred, axis-aligned, whatever
direction the shot travels, so the art has to be direction-agnostic — a round head or a glow,
never a streak, which would point the wrong way in seven directions out of eight.

**Visual length is the trail, not the sprite.** The engine draws the particles along the flight
path, so how long a bolt looks is how many of a weapon's 35 frames are non-empty and how dense
they are. That is authored in the sheet and is tunable without new art.

**Enlarging the set is smaller than it looks.** `ExtraSprites::getSurfaceSet` already resizes a
set to whatever `subX`/`subY` declares — but only `if (set->getTotalFrames() == 0)`. The
`new SurfaceSet(3, 3)` in `Mod.cpp` is just a placeholder; vanilla's 105x33 sheet is what pins
it at 3x3, because by the time a later mod declares a bigger sheet the set is no longer empty.

So the engine change needed is narrow: let the projectile size be declared before extra sprites
load, and stop the auto-resize overriding it. Not done, and not worth doing until the painted
heads exist.

`build/build_projectiles.py` is the other half and is done: it takes one head per weapon and
generates the 35-frame trail, since length is frames and not sprite shape. It refuses art with
a long axis, because that art only looks wrong in seven directions out of eight.

**The build fires on any push to this branch, with no path filter.** A commit of art or
build scripts starts an 11-minute Windows build that nobody wanted, and one has already had to
be cancelled by hand. `[skip ci]` in the commit message stops it, and the workflow can still be
started on demand from `workflow_dispatch`. Use it for anything that does not touch engine
source.

**GitHub matches `[skip ci]` anywhere in the message, including inside a sentence saying not to
skip.** An engine commit ended with "No `[skip ci]` on this one — the engine changed and the exe
is the point", and no build ran. The phrase is a marker, not a word, so it is never written in
prose: say "skip marker" and keep the literal string for when it is meant. The recovery is
`gh workflow run build-oxce-4x.yml --ref <branch>`, which builds the branch head regardless.

The reverse is the expensive one. A data-only commit pushed *without* the marker starts a build,
and because the runs share a concurrency group it **cancels whichever build is already running**
— the way week 2's fetch was lost. So the marker goes on before the push, not after.

**`State::blit` is the only reliable per-frame hook.** Anything that must land after a surface
reaches the base buffer — item icons, the equipment-screen figure — is done by overriding that
surface's `blit`, not by hooking where it was drawn.

## What each area does

**Resolution and colour.** 4x battlefield at 128x160. Full colour for terrain and units past the
256-colour palette. Scale2x (EPX) replaces pixel doubling for leftover X-COM sprites. Menus,
item icons and the equipment-screen figure all drawn at display resolution.

**Destruction.** Fire burns structure and climbs through wooden floors. Unsupported structures
collapse: a wall run carries six tiles of floor above it, a lone stub carries one, only tall
walls and objects count as supports, debris does 15–40 damage. Explosions start fires 10–20% of
the time (measured 12.5%); incendiaries always.

**Camera.** `cam(focus, scale, focusY)` gained a vertical axis. Without it the visible band sat
on y60 and WR1 on y5 was off the top of frame at every zoom.

**Wall penetration.** A shot that fails to stop on terrain carries on through it. `penetrate()`
charges the material its absorption cost and passes on a share of what is left — plasterboard
costs 2 and passes 85%, concrete costs 55 and passes 20% — and `penetrateOnward()` re-traces the
same line from a tile beyond the obstruction and hits whatever is behind it at the reduced power.
Laser and plasma pay two thirds against masonry and concrete only, which is the one place energy
earns its reputation.

The material comes from `MapData::_material`, five materials plus unknown, tagged onto 282 tiles
by `build/tag_materials.py` and overridable per tile from a ruleset through `MCDPatch`'s
`material` key. Untagged terrain reads as `MAT_UNKNOWN`, which is deliberately priced like
masonry rather than like air: a tile nobody has classified should behave like a wall, not like a
hole.

Three things keep it from misbehaving. It only runs on a standing ranged attack — not melee, not
explosions, which have their own propagation. The trace restarts a whole tile past the hit, or it
finds the very wall it just came through. And `_penetrationDepth` caps the chain at four, which
is further than any honest shot travels and is what stops a shot that re-hits its own tile from
recursing until the stack runs out.

Written and compiling; not yet watched in a real firefight.

## Not done

- Menu conversion stages 1–3: list rows and their text (122 screens), numbers, text entry, bars,
  scrollbars, the battle control panel's 30 icons, the geoscape side panel. The globe is separate.
- Item icons are sharp only on the soldier inventory screen. Craft equipment, buy/sell and the
  UFOpaedia still draw them at 1x.
- Projectile set size is still fixed at 3x3, so painted projectiles are blocked.
- Neither side's AI *chooses* to shoot through cover yet. Both sides get the physics; only
  deliberate use is missing, which is the split the principle below describes.

## The principle for anything with an AI half

Build the mechanic in the shared layer — the voxel trace, the damage application, the firing
code all run for both sides — and expose it as one query. The AI learns to ask that query later;
the mechanic is never rebuilt. Wall penetration is the worked example: shipping it with no AI
work still gives both sides the physics, and leaves only *deliberate* use unimplemented.
