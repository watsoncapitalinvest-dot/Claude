# G.I. Joe 4x — what the fork changes, and why

Save point: 10 Nov 2026. Patch head `24690c4`. 44 files, ~1,775 lines added.

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

**`BULLET_SPRITES` is 35.** The trail already exists; it is 35 copies of one sprite. Per-weapon
projectile art is an authoring job, not an engine one — but the set is created at 3x3, so frames
are clipped to 3x3 before any scaling. Authoring real projectile art needs that size to become
declarable. Not done.

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

## Not done

- Menu conversion stages 1–3: list rows and their text (122 screens), numbers, text entry, bars,
  scrollbars, the battle control panel's 30 icons, the geoscape side panel. The globe is separate.
- Item icons are sharp only on the soldier inventory screen. Craft equipment, buy/sell and the
  UFOpaedia still draw them at 1x.
- Wall penetration. Collapse is done; the matrix is not started.
- Projectile set size is still fixed at 3x3, so painted projectiles are blocked.

## The principle for anything with an AI half

Build the mechanic in the shared layer — the voxel trace, the damage application, the firing
code all run for both sides — and expose it as one query. The AI learns to ask that query later;
the mechanic is never rebuilt. Wall penetration is the worked example: shipping it with no AI
work still gives both sides the physics, and leaves only *deliberate* use unimplemented.
