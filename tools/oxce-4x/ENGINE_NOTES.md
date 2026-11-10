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
| `OXCE_PEN_LOG` | off | logs every terrain hit, every `penetrate()` and every re-trace |
| `OXCE_ECON_LOG` | off | logs each Cobra site that earns nothing because its cargo was shot down, and once a month every region Cobra holds stock in: materiel and funds against the thresholds they are compared with, flagged `CANNOT ARM` / `CANNOT PAY` |

The economy line prints the threshold beside the stock, which is deliberate: a rule comparing
against a threshold of **0** is how the kit rule shipped switched off, and `materiel=12/0` makes
that visible where `materiel=12` would not. Regions Cobra has never been to are skipped, or it
would be sixteen lines a month saying nothing.

`OXCE_PEN_LOG` is read once at `TileEngine` construction, not per hit, and it ships on purpose:
the penetration numbers are John's to tune and he should be able to see what they are doing
without waiting on a build. `build/pen_live_report.py` turns the log into the destroyed-versus-
survived table that found the `throughBroken` problem.

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

**A threshold against an accumulating balance is a dead rule, not a tunable one.** `wellPaidFunds:
40` compared a region's banked Cobra funds against a fixed number and fired **zero times in 400
days** — the lowest regional balance all run was 110. The instinct is to raise the number; that
is wrong. Regional funds accumulate, so Cobra passes under *any* fixed threshold in month one and
never returns, and a bigger number just moves the death out past wherever the test was looking.
The bar has to be derived from something that grows with the thing it is gating — here, the
upkeep the region's own sites owe. Before tuning a threshold that never fires, check whether the
quantity it tests is monotonic.


**`locateRegion` logs `LOG_ERROR` when it finds nothing, and a New Battle parks its craft at
[0, 0].** Adding a thirteenth caller to it put `Failed to find a region at location [0, 0]` into
the log on **every New Battle** — the one path the mod is actually tested from. The craft was a
fallback for the garrison lookup's position, described as "close enough, since it is parked on
the target"; in a New Battle it is parked on nothing. A craft-only battle is a New Battle or a
craft fight and neither is a raid on a Cobra site, so the fallback bought nothing and cost a
false error. Removed. Before adding a `locateRegion` call, ask what it does on a position that
is in no region.

**`reinforcementsItemLevel` is a table row, not a tier.** Reinforcements are generated in
`NextTurnState::deployReinforcements`, not in `BattlescapeGenerator`, and they read a stashed
`int month` that indexes `alienItemLevels`. Clamping that row to 0 looks like the way to
down-kit a wave and is not: row 0 is `[0,0,0,0,0,0,0,1,1,2]` and still issues the middle tier to
one man in five. The tier has to be clamped where it is drawn.

**Two copies of a UI-driving test destroy each other silently.** Every `gar_test.sh` run deletes
the shared `openxcom.log` at its start, so two runs at once leave one of them grepping an empty
file — it reported six clean failures, *"0 units, the battle did not generate"*, about battles
that had generated perfectly. Second occurrence of this today (the first was an xdotool loop from
a stopped task still firing into a new window). The runner now takes an `flock` and refuses, and
traps EXIT to kill its own game. A harness that can produce fiction is worse than no harness.

**`grep -c` already prints `0` and exits 1.** `total=$(grep -c ... || echo 0)` therefore printed
`0\n0`, and `printf '%3d'` rejected it as an invalid number — noise that sat directly on top of
the real result and helped hide it. Use `total=$(grep -c ...) || total=0`.


**The game reads its mod from `~/.local/share/openxcom/mods/GIJoe4x`, not from the scratchpad.**
`cobraEconomy:` was written into the scratchpad's `gijoe_tuning.rul`, built, tested, shipped and
documented — and the directory the game loads never got the block. `tryRead` left the threshold
at its default of 0, the guard `if (wellSupplied > 0)` skipped the whole lookup, and every region
on earth reported itself well supplied. The feature compiled, ran and did nothing.

The two trees are deliberately **not** mirrors, so a blanket sync is the wrong fix: the installed
copy holds John's own files (`gijoe_frontops`, `gijoe_chuckles`, `gijoe_intro`,
`zz_gijoe_destruction`) that the scratchpad has never had, and it is sometimes *ahead* on shared
ones — `gijoe_terrain_na.rul` had NACOBRA maps there and not here, and copying the scratchpad
over it would have deleted them. Check direction per file.

`scripts/check_loaded.py` (shipped as `build/check_loaded.py`) asks one question per key: is this
key set by a file in the tree the game loads? A key the engine reads that nothing loaded sets is
reported as a failure, and it exits non-zero. It ignores commented lines, because the doc block
above `cobraEconomy:` mentions the name repeatedly and a raw substring count would have passed on
the very file that was missing the setting. Run it before believing any ruleset-tuned feature.

**A ruleset default of 0 plus a `> 0` guard is an off switch nobody chose.** It is the right
shape — it is how `wellSuppliedMateriel: 0` turns the rule off on purpose — but it means a key
that fails to load is indistinguishable, from inside the game, from a key deliberately set to
zero. That is why the check above exists rather than a log line.

**`campaign_ff.sh` needs two probes and looked busy with one.** `campaign_probe` writes the
monthly line (`Savegame/SavedGame.cpp`); `ff_probe` drives the clock
(`Geoscape/GeoscapeState.cpp`). With only the first applied the game loads the save, sits on a
paused geoscape and burns 77 per cent of a core, which for two minutes is indistinguishable from
a slow fast-forward. The runner now greps both files and refuses with the commands to run.

**Totals cannot measure a per-entry change in a New Battle.** Four runs of the same map with
nothing forced gave 10, 15, 7 and 7 units, because `dQty` and `extraQty` are rolled per rank
entry. A headcount penalty of one man per entry is invisible against that spread, so the probe
logs each entry's quantity before the subtraction and `gar_check.py` checks
`spawned == max(1, before - penalty)` exactly. The same checker **fails a baseline with no kit
spread**, because a baseline already all on tier 0 would show the clamp "working" while proving
nothing.


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

**A ruleset naming a file the mod does not have is FATAL, not a warning.** `FileRecord::at` logs
FATAL and the game never reaches the main menu, so one missing PNG costs the whole session. It
happened with `gijoe_items_new.rul`, which had sat in the repo for a day naming 22 painted items
that had never been copied anywhere, and went out inside a zip labelled as a mod update. Both
halves had been verified; what had not was that they were in the same place. `build/check_shipment.py`
runs over the shipment as assembled — not the working tree, because a file present in the
scratchpad and absent from the zip is the exact failure being looked for.

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

The matrix itself is a ruleset key, not a constant, because the one thing certain about these
numbers is that they are wrong and the person who has to fix them should not need a Windows
build to try a value. `penetration:` in `Mod::loadFile` fills `_penCost`, `_penEnergyCost`,
`_penPass` and `_penMaxWalls`; `TileEngine` copies them at construction the way it copies every
other tuned number, so a shot does not chase a `Mod*` per tile. A material left out keeps its
default. An unknown material name is logged rather than ignored, since a typo reads exactly like
a value that did not help. `energyCost` carries its ratio when `cost` changes and `energyCost`
does not: leaving it alone would quietly make lasers better against a material that got tougher,
and setting it equal to cost would quietly throw away the masonry and concrete discount, which
is the one place energy weapons are meant to differ.

Shipping the tuning file with the defaults in it makes the obvious test useless — the probe
prints the same numbers whether the file was read or ignored — so `build/pen_test.sh` changes
each thing to a value no default can produce.

**Coverage is 627 tagged against at least 324 untagged, and the first count of that was wrong.**
The hole report reads the rulesets it is given, and it was given the mod's own and nothing else,
so it reported five small gaps while a Terror Drome assault was quietly loading X-COM's
alien-base tilesets through `UBASE`, a terrain declared in the master ruleset. Widened to scan
both. What is still untagged is the UFO and alien-base interiors — `U_BASE` 67, `U_WALL02` 47,
`PLANE` 65, `MARS` 36, `U_EXT02` 34, `UFO1` 20, `U_DISEC2` 17, `U_OPER2` 15, `U_PODS` 11,
`U_BITS` 8, `BRAIN` 4 — plus thirteen outdoor sets (DESERT, FOREST, JUNGLE, MOUNT, POLAR, URBAN,
ROADS and friends) whose MCDs are not in this container at all, so they cannot be counted here
let alone tagged.

**Materials cannot be derived from the MCD record, and this was measured rather than assumed.**
The record carries `Armor`, `Flammable`, `Fuel` and `Footstep`, which all sound like they should
separate wood from concrete. Cross-tabulated against the 66 genuinely vanilla tiles tagged by
hand, `Footstep` is flat at 2 for everything, `Armor` runs 4–50 for light against 5–35 for wood
and 5–35 for masonry, and `Flammable` is noisier still. Any rule built on them would be guessing
dressed as arithmetic. Reading the art with `build/render_tileset.py` is the method; there is no
shortcut.

**A PCK holds frames, an MCD holds tiles, and they are not the same list.** `U_BASE` has 71
frames against 67 tiles and `U_WALL02` has 66 against 47, so rendering a PCK in order and calling
position N "tile N" mislabels most of a sheet — and the sheet still looks like a tileset, so
nothing gives it away. `build/render_tileset.py` draws every tile through its MCD record's first
frame, which makes the number on the tile the `MCDIndex` a tag will use. BARN and CULTIVAT happen
to be 1:1, which is why the hand tags made from the earlier version survive; that was luck.

**Tagging the saucer tilesets was started and deliberately stopped.** The mod renames the UFOs to
FANG, Firebat, Rattler, Mamba, Night Raven and Condor, but never overrides `ufos:`, so the
battlescape is untouched: a FANG crash site is `UFO1A` and a Condor is `UFO_160` with `U_EXT02`,
`U_WALL02`, `U_PODS`, `U_BITS`. Named right on the globe, flying saucer on the ground, on the
commonest mission in the game. Polishing how a bullet passes through a map that should not be
there is the wrong order, and `build_craftmap.py` already turns a 3D model into a craft tileset —
that is where JOEHELO, JOEPHANT and JOEDEFI came from.

**Watched at last, and as designed it almost never happens.** Everything had been verified except
the thing it does. Across six battles with the shipped rule: 28 ranged hits on terrain, **one**
reached `penetrate()`, and that one was a rifle round against concrete that stopped. The cause is
the gate rather than the numbers — a shot may only cross a wall that *survives* it, because a
wall that breaks gives an opening rather than a penetration, which was deliberate and is in the
comment. At the armour values X-COM gives tiles a wall nearly always just breaks, so the rule
quietly means "almost never".

`penetration.throughBroken` (default false) lets a shot that destroyed the wall carry on through
it too, paying the same cost. Same build, same maps, one line:

| `throughBroken` | terrain hits | reached `penetrate()` | carried power through | hit something behind |
| --- | --- | --- | --- | --- |
| false | 28 | 1 | 0 | 0 |
| true | 56 | 56 | 29 | 15 |

It ships off: off is the rule the design asked for, and which of the two is the better game is
not a call to make on a measurement alone. The energy discount was confirmed in the same runs —
concrete charged 37 instead of 55, masonry 20 instead of 30.

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
