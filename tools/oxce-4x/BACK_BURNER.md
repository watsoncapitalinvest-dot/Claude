# Back burner, owed, and broken

Three different things, kept apart on purpose. **Parked** is a decision — it
was reviewed and set down. **Owed** is work this desk said it would do, or
something shipped that is now wrong. **Broken** is a bug with evidence.

Nothing here is a wish list. If it is on this page it has been costed at least
roughly, and the cost is written down.

---

## Parked by decision

### Short-Fuze (parked 12 Nov 21:31, John)

"back burner him into the roster waiting". He has textures and a look file, no finished look, and
ROSTER holds his record as WAITING. gijoe_day1.rul startingBase still lists STR_SHORT_FUZE: 1 (so
Day 1 fields him as the 16th Joe in his placeholder look) until John brings him back or says drop him.

### Visual inventory: a holstered pistol that shows on the figure (parked 12 Nov 23:58, John)

"back burner visual inventory for the future". A sidearm equipped as the secondary would show in its
holster on the battle sprite and the equipment figure. Nothing built; Hawk's figure keeps its pistol
painted in the holster.

### ~~A textured globe from the vegetation map~~ — drawn at display resolution 12 Nov

`HiUI::globeFloor` now redraws the earth per DISPLAY pixel: the projection is
inverted (the same maths as `Globe::cartToPolar`), `earth.png` sampled
bilinearly at its own 2048x1024, shaded by the same sun the 8-bit pass uses
(its dithered terminator becomes a smooth one). Pins, names and the player's
marks go on top at display resolution; the 8-bit globe underneath is unchanged
and is still what the game reads. Costs: 130-250 ms to re-project when the
globe turns or zooms (measured here, two loaded cores), one copy a frame when
it is still.

**Where it stops.** The texture is 2048 wide, so at the two closest zooms a
texel is bigger than a screen pixel and the land goes soft and blocky again
(zoom 3 shows it). A bigger texture fixes that with no code: the engine uses a
full-colour `earth_hi.png` beside `earth.png` if one exists. Not shipped,
because the only full-colour source here is the third-party model below, and
the repo is public. The light ellipses at both poles are the texture's own
first and last rows (no Antarctica), not the renderer.

#### (history) the parked note

John downloaded `earths-vegetation-index-low-poly` and asked for the
vegetation one on the geoscape.

**The `.obj` is unusable** — a 3840-face unit sphere, and OpenXcom has no 3D
pipeline at all: the geoscape is `WORLD.DAT` polygons rasterised in software
into an 8-bit palette. There is nowhere to put a mesh.

**The texture was recoverable.** `earth_vegetation_index.png` ships 2048×2048
square — a UV atlas baked for that mesh, not a world map. But the mesh is a
perfect unit sphere (radius 1.000 at every vertex) with 2078 UV coords, so it
unwraps: vertex position gives lat/lon, UV gives the texture pixel, rasterise
the 3840 triangles back out. **94.5% of pixels recovered.**

The result is saved on John's machine, NOT in this repo — it is derived from a
third-party model of unknown licence and the repo is public:

```
C:\GI-Joe-Silent-Storm\GIJoe_XCOM_4x\art_briefs\earth_vegetation_equirect.png
```

Two defects in it, and the first was written down wrong here on 10 Nov.

**The texture is MIRRORED in longitude**, not merely rotated. This page said
"rotated about 70° off Greenwich", which was eyeballed off a render, and a
mirrored Earth still reads as Earth at a glance — Africa keeps its shape, so
nothing looks obviously wrong until a marker lands in the wrong ocean. Measured
against 44 land/sea truth points it scores 43/44 mirrored at an offset of 87°
and 31/44 unmirrored at −75°. The sampling is:

```python
L = -lon                                   # the unwrap came out left-handed
u = ((L + 87.0 + 180.0) % 360.0) / 360.0
v = (90.0 - lat) / 180.0
```

Antarctica is still missing. The lesson is the usual one: the offset was read
off a picture instead of measured, and a picture of a mirrored world is not
obviously a picture of a mirrored world.

**What using it would take.** Render the globe in the HD layer instead of the
palette one: for each screen pixel inside the globe disc, invert the
orthographic projection to lat/lon — `Globe.cpp` already does this for mouse
picking, so the maths exists — sample the map, composite in 32-bit through
HiUI, which already does that kind of overlay for backgrounds. A few hours.

Worth noting for whoever picks it up: this is the **largest cheap visual win
available**. A photographic Earth instead of flat green polygons is a bigger
jump than anything else on this page, and it is plumbing rather than art.

### Disguise in battle (parked 10 Nov, John)

Zartan's *Disguise*, Zarana's *Disguise*, and Act 4 infiltrators in captured
Joe gear that "look friendly or civilian until revealed".

**Why it is parked rather than queued:** OXCE draws a hostile as a hostile.
There is no mid-battle faction flip and no native concept of a unit the player
reads as friendly until it fires. Faking it means standing a unit up in the
neutral or civilian faction and converting it to hostile on a trigger, and
that conversion is the part with no support — line of sight, reaction fire,
AI ownership and the turn order all assume a unit's side does not change.

This is the largest single battlescape ask in the design doc, and **nothing
else in the Cobra soldier pass depends on it.** The other 37 villains and all
13 elite troop types can ship without it.

If it comes off the burner, it wants scoping on its own rather than being
folded into a villain content pass.

### ~~Zanzibar's stolen signature weapon~~ — resolved 10 Nov

Cut, and he was given a new special instead (John). The old one had him
stealing a Joe's signature weapon, recoverable through a mission on his
hideout or a black-market sale: one villain crossing the battlescape, the
geoscape and mission generation.

Replaced with **Skiff-Borne** (he flies — native `MT_FLY`, and the only Cobra
on the board who does, so his Air Skiff does something instead of being
flavour) and **Weighted Net** (a one-shot built-in weapon doing `ToTime`
damage, which OXCE supports natively: it pins a Joe where he stands without
wounding him — a pirate wants them robbed, not dead). Both are pure ruleset.
His world-map half, raids on civilian shipping earning Cobra double, is kept.

### Subterfuge's strategic half, and fake intel (parked 10 Nov, John)

Moles at The Pit, impersonation off-screen, false flag operations, fake Joe
signals, sleeper cells, Synthoids — and **Cobra planting fake intel** through
its Infiltration department (an empty site, or an ambush; rare early, more
common later).

All geoscape, all leaning on detection the player can act on.

**The ordering is the reason, and it is worth stating plainly.** Fake intel
needs the Infiltration department to exist, Infiltration is part of subterfuge,
and subterfuge needs intel — a forgery is worthless until there is something
genuine to forge. Built in the wrong order, the fakes have nothing to corrupt
and the player has no way to tell a planted lead from a real one, which is the
entire point of the mechanic.

**What is NOT parked by this:** the Joe Intelligence department itself. Leads,
intel quality (rumor / likely / confirmed), staleness, the Cobra Research
intel screen and per-region counter-intelligence strength all stay live —
several are cheap extensions of data the economy work already stores. Parking
the fakes is what buys the ordering.

---

## Owed

### Air fights: what Phase 1 still lacks (14 Nov)

- **Transports need a pilot too (design 1b.4), but are not given the rule.** With `pilots: 1` the
  Tomahawk's pilot would be one of the squad it carries. Whether he still fights on the ground, or the
  transport carries a separate crew seat, is John's call. Until then only the Skystriker and the
  Conquest need a pilot (gijoe_air_fight.rul).
- **The C-130 and the Vulture** have no craft or Cobra-aircraft type to hang a 2x2 unit on. The
  Tomahawk and the Condor are in (gijoe_air_big.rul); the Condor's picture is a stand-in.
- **The odds are an estimate** (AirFight::odds, a fast abstract run of 400 fights). Tuned against
  STORY's dogfight_sim table and two engine fights; an unnamed Skystriker against a Rattler reads about
  45% where STORY's sim said 73%, because the engine's Rattler breaks off at 40% and this counts that as
  not a win. Ace against a Condor read 62% and won.
- **Not seen in the engine:** a Tomahawk (2x2 Joe transport) in a fight. It needs Cobra hunting a Joe
  transport, which nothing in Year 1 does yet.


### ~~The geoscape font fix~~ — cause found and shipped 11 Nov, still unseen here

Blank button labels on the geoscape, oversized text clipping in windows
(10 Nov, John's screenshots). On 10 Nov this page said neither defect found by
reading explained the blank buttons. **Reading further, together they do.**

The `TextButton` branch drew its art, called `claim(r)` — which suppresses the
flat 8-bit button underneath — and only *then* called `glyphs()`. And
`glyphs()` dropped a glyph **whole** when its box crossed the base surface:

```cpp
if (... || bx0 < 0 || by0 < 0 || bx1 > bw || by1 > bh) continue;
```

The geoscape's side-panel buttons sit hard against the right edge of a 320-wide
base surface, so their labels tripped `bx1 > bw`, every glyph was dropped, and
the claim had already thrown away the readable original. A blank slab with no
way back. The same guard is the truncated `LAUNCH INTERCEPTIO…`.

Three changes, 11 Nov:

- `glyphs()` **clips** a glyph that crosses the base edge rather than dropping
  it. Only the `xs`/`ys` lookups needed the box in range; those are clamped and
  the inner loops already clip per pixel. The source rect and the inverse map
  follow the clamped box, or a clipped glyph samples the wrong column.
- `glyphs()` **returns how many it drew**, and a `TextButton` asks on a dry run
  BEFORE drawing anything. If the label would come out empty, HiUI stands down
  for that button and the flat one shows. A bare `Text` does the same, leaving
  its rect untagged.
- Both log the rect, the glyph count and the surface bounds at `LOG_VERBOSE`,
  which is the instrumentation offered on 10 Nov — now self-healing rather than
  diagnostic.

**It is still not reproduced here**, and that has not changed: HiUI only
switches on when `_hi.png` twins exist, and the install John uploaded is a
skeleton — one file per folder, no font sheets. So the first clause is reasoned
from the code, not seen. What *is* certain is the failure mode: the fallback
means the worst case is the plain renderer, which is legible. It cannot blank a
button any more, whatever the cause turns out to be.

### Three villains whose only special is environment-locked

Found while replacing Zanzibar's. His one move was *Boarding Raid (water
battles)*, so in a land mission — most missions — he had no signature move at
all. **Wild Weasel** has the same shape (*Strafing Run*, air battles) and
**Copperhead**'s *Water Moccasin Rush* is boat-bound.

Each wants a land move, with the environment one kept as a bonus. Zanzibar is
done; the other two are not.


### The calendar ceiling is not scoped to the AI

`maxKitTierByMonth` clamps Cobra's weapon tier unconditionally. The design doc
is explicit that calendar windows *"apply only to the side the computer
plays… a pacing rail for the AI, not a rule of the world."*

Right while the player is G.I. Joe. **Wrong the moment Cobra is playable**,
which is the stated plan. One condition, not a rebuild.

### The department head signs off in person

A node accumulates while its head is away but parks at full progress until he
turns up at that bench for a few days (John's window: a few days — tight
enough that catching one is a genuine intercept).

Needs a villain-to-department mapping in the ruleset, which does not exist,
plus per-villain travel state.

**Build it once for both sides.** The doc gives G.I. Joe the same rule —
"if Scarlett goes out on a field operation, the department slows while she's
away, the same rule as an injured or captured head". Two factions, one
mechanism, one code path. Doing it twice is the mistake available here.

### The player's research tree is 8 topics

Against roughly 195 planned, and 7 of the 8 are interrogations still pointing
at a vanilla `lookup`. The ~29-topic interrogation spine is the story's
backbone and almost none of it exists.

### Cobra's tech tree is 2 departments

Benches, exclusivity and raid-clearing are built and verified — but the bench
model's whole tension is scarcity, and with two departments against three
labs nothing competes for anything. **The mechanism is correct and will not
feel like anything until the tree is populated.** Content, not engine.

---

### ~~Craft art shows sharp only after the equipment screen has been opened~~ — fixed 12 Nov

All three below are done as described: `resolvePending()` first in
`nativeBaseView`, and `aliasImage` on the article's `_bg` and the equipment
screen's `_sprite` (`aliasImage` now resolves pending frames itself, and drops
a stale alias when the new frame has no twin). The rest of this entry is the
diagnosis, kept.

`build/install_craft_art.py` installs the Tomahawk and Skystriker top views as
BASEBITS 33 / 36 with `_hi` twins, and the dossiers as UP004 / UP002 with `_hi`
twins. The twins are right — but three screens never reach them:

- **Hangar on the base plan.** `HiUI::nativeBaseView` looks the docked craft's
  frame up in `bgImages`, but a BASEBITS twin is only *pending* until
  `resolvePending()` runs, and only `HiUI::sprite` / `spriteFit` (the equipment
  screen) call it. So the hangar shows the blocky 8-bit craft until the player
  has opened an equipment screen once in that session; after that it is sharp.
  Seen both ways on screen. **Fix: `resolvePending();` as the first line of
  `nativeBaseView` (Engine/HiUI.cpp ~1917).**
- **Craft equipment screen** (`CraftInfoState`, 32×40 at 144,56) blits the frame
  into its own `_sprite`, so no twin can be found. Fix: after each blit
  (CraftInfoState.cpp:229 and :675) call `HiUI::sprite(frame, _sprite->getX(),
  _sprite->getY(), 32, 40)` from the state's blit, or alias `_sprite` to the
  frame — `aliasImage` would also need `resolvePending()` first.
- **Intel craft article** blits the picture into the article's `_bg`
  (ArticleStateCraft.cpp:59). Fix: `HiUI::aliasImage(_bg,
  _game->getMod()->getSurface(defs->image_id))` after that line — the same thing
  `InventoryState.cpp:195` does for TAC01.SCR. Every other article type has the
  same copy and the same fix.

Not done either: the craft's outline in an air battle (INTICON frames 11 / 14,
22×25, geoscape palette, recoloured by the damage indicator). Cheap to make;
not installed because it could not be checked without staging a dogfight.

### The geoscape readouts that have no source yet (12 Nov)

The panel's four wells read FUNDS, PUBLIC, THREAT, LEADS (fix list item 2).
Two of them stand on something that is not what the label promises:

- **PUBLIC** says SECRET always. Nothing in the save or the engine records
  G.I. Joe going public. When that state exists, the well wants a percentage.
- **THREAT** is a proxy. There is no provocation gauge (queued, below). It reads
  this month's council score - Joe activity plus research score against Cobra
  activity - banded at MonthlyReportState's own rating lines: TERRIBLE ->
  IMMINENT, POOR -> HIGH, OK -> ELEVATED, GOOD -> LOW. True, and on the player's
  own graphs, but it is "how the month is going", not "what Cobra intends".
- **LEADS** counts dossier entries research has opened and nobody has read
  (articles with a research requirement, status NEW). That is a reasonable
  reading of "unread intel" and not a leads system.

### Cobra site types share one pin when the HD layer is up (12 Nov)

Fix list item 7 asked for one shape and colour per kind, drawn by the engine:
Joe base olive square, Cobra site red diamond, mission orange triangle, contact
white ring, Joe craft cyan arrowhead. That replaces the eight per-type Cobra
marker frames (9-16) on the HD globe; they still draw at base resolution. A
glyph per site type inside the diamond would bring the distinction back. The
mission triangle has not been seen on screen - no save here has a mission site.

### Stocked rooms: what the 12 Nov pass left (12 Nov)

`build/install_stocked_rooms.py` stocks the 52 Pit rooms that have a shell and a
harvested plan; 13 vanilla facilities show them. Left over, each with its cost:

- **Access Lift and Supply Depot are still bare shells.** Their objects exist
  (`obj_access_lift_*`, `obj_supply_depot_*`) but the generator has no plan for
  either, and positions come only from the plan. Needs a plan (a `place()` list)
  for each, then a re-run. Small.
- **Gaps: props with no object.** Every room's run prints them. The big ones:
  `mainframe` (130 placements across the set), `panel`, `fridge`, `radio`,
  `transformer`, `tank`, `drums_toxic`, `crates_blue`/`drums_red`, the `v_*`
  vehicles in the motor pools. A drawn object per prop closes each gap; the
  installer picks it up once it is mapped in `PROP`/`ROOM_PROP`.
- **Requisitioned objects with no harvested spot** go unplaced (e.g. the HQ's
  big plotting table, the weapons locker's cleaning table, the pool's lounge
  chairs). Same fix as above from the other side: a plan entry for each.
- **Only the Joe theme.** Naval, outdoor, space and Cobra rooms wait for their
  shells; `SHELL_THEME` and the engine's `roomShell("joe", ...)` both assume joe.
- **The 8-bit frames are brown-walled.** Palette 1's 139 facility indices have
  no olive, so the shell's olive walls snap to brown. Only seen with HiUI off.
- **A room under construction**: HiUI shows the empty shell (by design); the
  8-bit view still draws the stocked frame under the build count, as vanilla
  draws any facility frame during construction.
- **`sizedTwins` caches by frame address**, like `flatTwin` below. Harmless
  unless BASEBITS is rebuilt in-process (mod change without restart).

### The FANG on the battle map (12 Nov)

The FANG's dossier page and its interception picture are in the game
(`build/install_fang_art.py`). **The landed and crashed FANG on the battle map
are not**: STR_SMALL_SCOUT still drops the vanilla small-scout hull
(`battlescapeTerrainData: UFO1A`, sets BLANKS + UFO1, a 10x10 block), so the
first FANG landing a player raids is a grey saucer.

The art for it is kept, keyed and cleaned, NOT shipped:
`art_briefs/returned/fang/clean/` holds `fang_top.png` (straight down, nose
up) and the four angles the art AI drew unasked (front, rear, opposite side,
rear three-quarter), every pixel subject or pure FF00FF. The untouched
originals are one folder up.

What the map version needs, none of which exists yet:

- **A way from pictures to tiles.** The battlescape is isometric 32x40 tiles
  stacked in levels, each tile a floor, two walls and an object, each with a
  LOFT voxel shape for line of fire. A top-down picture cannot be sliced into
  that; it is a footprint and a reference, not a source. Realistically a 3D
  model of the FANG (the five angles are the modelling references) rendered to
  iso tiles in Blender, the same road the room objects took.
- **A tileset**: MCD/PCK/TAB with the FANG's pieces (body, rotor mast, blades,
  skids, missile rack), and a damaged set for the crash site.
- **A map block** for the landing and one for the crash, sized to a FANG - a
  one-man gyrocopter is two or three tiles long, so the 10x10 saucer block is
  mostly empty ground once it is gone - and route nodes (RMP) for the Viper
  Pilot.
- **The rule**: `battlescapeTerrainData` on STR_SMALL_SCOUT pointed at it.

Cost: the pipeline is the big piece, and it is shared with the Stinger and the
H.I.S.S., which need the same thing in months 4-12. Not started.

## Broken

### WATCH: big maps (.MAP2), the first place to look if a battle will not load or runs out of memory

Not broken yet; John 15:34 asked for the note instead of a guard. From 0193a43 a map can be a
`.MAP2` with up to 65,535 part ids (BattlescapeGenerator::loadMAP). Two ways it can go wrong:
- **A part id the terrain sets do not have.** loadMAP looks it up with no range check, so that
  battle fails to load (or the game falls over loading it). MAPS checks ids with testblock.
- **Too many parts.** Each part's 4x full-colour frame is held in memory (~80 KB), and John's
  game is a 32-bit build. MAPS' budget is 1,000 parts a map (claude/BRIEF_FOR_MAPS_MAP2.txt).
If a new map crashes on load or the game dies of memory in a big battle, check this first: the
map's part count, and its highest id against the terrain's sets. A refuse-with-a-message guard
in loadMAP is the fix if it ever bites.

### `flatTwin` caches by surface address

The same stale-pointer bug that drew a black square on the rotate-up key
(fixed by `HiUI::surfaceGone`) can still hit `flatTwin`, whose cache is a
function-local static keyed by frame pointer and palette. Rare - a frame would
have to be freed and another allocated at its address under the same palette -
and not seen, but it is the same shape.

### A campaign crashes around month 15 — in THIS CONTAINER, not necessarily on a real install

```
[FATAL] FileRecord::at(TERRAIN/XBASE1.MCD): requested file not found.
```

The base-defence tileset. Found 10 Nov in a 900-day run, and first written
down here as a mod bug the player would hit. **That was wrong, and the
correction is the useful part.**

`XBASE1.MCD` is an original X-COM file. OXCE ships `XBASE2.MCD` in
`standard/xcom1/TERRAIN` but **not** XBASE1 — that one is expected to come
from the player's own game data. This container's `UFO/TERRAIN` holds 24
files (BARN, BLANKS, CULTIVAT, PLANE, UFO1, U_BITS, U_EXT02, U_WALL02 —
exactly what the mod's own test maps need) where real X-COM has around a
hundred. So the file is missing *here* because the vanilla data is a stub.

**What it means in practice:**

- On a complete X-COM install, base defence should load and there is nothing
  to fix.
- Unattended campaign runs in this container still die at about month 15 once
  a retaliation fires, so **a fast-forward campaign cannot be run past roughly
  fourteen months here.** That is a real limit on testing and it is why the
  planner never reaches the later buildings in a 400-day run.
- If a player's own data folder is incomplete, they *will* crash on base
  defence. One check settles it: look for `TERRAIN/XBASE1.MCD` beside the exe.

**The lesson worth keeping:** a missing-file crash says where the engine
looked, not whose job it was to put the file there. Check which side of the
line a file comes from — shipped by OXCE, shipped by the mod, or supplied by
the player — before calling it a bug.

### ~~Two parsed ruleset keys nothing consumes~~ — one real, one never existed

`stockpileCap` is the M.A.R.S. dealer threshold and M.A.R.S. is not built, so
that one is expected and stands.

**`garrisonRefillPerMonth` was never a key.** Checked 11 Nov: it is not parsed
by the engine, not read by it, and not set in any shipped ruleset. It survives
only in a stale comment in `gijoe_cobra_economy.rul` claiming it is "read and
used", and in this file. `ECONOMY.md` had already worked out why it cannot
exist: X-COM keeps NO garrison on a site - the defenders are built from the
deployment every time it is raided - so nothing depletes and there is nothing
for a monthly refill to refill. A camp changes what the deployment PRODUCES
instead, through `garrisonBonus` and `garrisonRankUnlock`, both of which are
built and verified.

---

## Designed, agreed, not yet built

### ~~Player pins, notes and routes on the globe~~ — built 11 Nov

John: *"in game i'd like to be able to make notes on the globe. pins with
notes"* and *"i can put legend markers of suspected places and routes"*.

**This is the situation board from the design doc, approached from the other
side.** The doc describes it as Cobra-facing — *"one screen with every known
Cobra site and route, each villain's last known location, and each act
project's clock as an estimate with a confidence bar that sharpens with
intel"*. John is describing the player marking what he SUSPECTS before he
knows. They are one system: confirmed intel and the player's own guesses on
the same globe, drawn at different weights. Built separately they become two
map overlays that contradict each other — so they share one struct, one
drawing path and one confidence ladder.

`SavedGame::_userNotes` was the foothold: save/load wired, but text only, no
coordinates. The replacement is `GlobeMark` — id, lon, lat, label, note, kind,
trust, `fromIntel`, `placedMonth`, and a flattened lon/lat list for a route —
in `SavedGame.h`, saved and loaded alongside it.

Drawn by `Globe::drawMarks()`, placed from `GlobeMarkState`, iconned from
`gijoe_globe_marks.rul`'s `markIcons` in a fixed order the engine indexes by.
A mark with `fromIntel` set and older than `markStaleMonths` is DRAWN one tier
less certain without the stored mark being rewritten; a pin the player placed
himself never decays, because he is not guessing about his own guess.

**The gesture is CTRL + right-click, and that cost two attempts.** Plain
right-click looked free — `globeClick` had only ever registered for the left
button, so a right-click never reached it at all, which is why the first build
did nothing. Registering for the right button made the menu appear and
revealed the real problem: `Globe::mouseClick` centres the globe on every
right-click regardless of what is registered, so the first run with marks
enabled threw the view across the Pacific seven times in seven placements.
Right-click is how the geoscape has been navigated since 1994 and the board
does not get to take it. `Globe::mouseClick` now skips the centring for
exactly the CTRL chord.

`keyGeoToggleMarks` (default `m`, an OXCE option so it shows in the controls
list) hides and shows the layer. A region pinned six times is a region that
cannot be read, so the notes have to be put away.

Still open, and both wanted before this earns the name "intel layer": nothing
yet SETS `fromIntel`, because nothing in the game hands the player a lead as a
mark; and the route is append-only — a route point joins the most recent
player-owned route, with no way to start a second one deliberately.

### ~~Eight Cobra site types, one globe marker~~ — done 11 Nov

27 markers at 72px, in `mod/Resources/Globe`, wired by
`mod/Ruleset/gijoe_globe_markers.rul` and regenerated by
`build/build_globe_markers.py`. The eight Cobra deployments that shared
`markerIcon: 7` now carry 9–16; frames 17–35 are Cobra activity, the Joe side,
and the player's own pins and routes, which have art but nothing consuming them
yet (see below).

Four engine facts it rests on, each read out of the source rather than assumed,
and all four recorded in the ruleset's own header:

- **An oversized frame is legal.** `GlobeMarkers` is created as
  `new SurfaceSet(3, 3)`, but `Surface::loadImage` nulls the surface and
  rebuilds it at the PNG's size, and `Globe::drawTarget` centres on the
  marker's own width and height. The 3x3 is vanilla's art, not a ceiling.
- **The indices agree on both sides.** `maxSharedFrames` is 9, and both
  `ExtraSprites::getFrame` and `AlienDeployment::load`'s
  `mod->getOffset(markerIcon, 8)` shift anything above that by the same mod
  offset. Writing a literal 9 in both places is correct; pre-adding an offset
  by hand is not. Verified in a verbose run: frame 9 resolved to index 1009.
- **Five colours, all exact palette entries**, so nothing is quantised at load.
  Antialiasing is snapped to those five rather than quantised, because stray
  blend pixels land on whatever world-map green is nearest.
- **Every colour was chosen for its NEIGHBOUR.** `drawTarget` blinks a marker
  by drawing `srcStuff + 1`. Index 14 is the obvious Cobra red and index 15 is
  pure black, so a marker on 14 half-vanishes on every blink. 13 blinks to 14,
  a darker red. That one is invisible to every check except reading the draw.

Lazy loading is why a plain boot proves nothing here: `GlobeMarkers` is not
touched until the geoscape opens, so a main-menu run leaves no trace of it in
the log at all. The first control run compared sprite counts with and without
the ruleset, got the same number twice, and meant nothing — `s:` is not a
sprite count.



Held from earlier sessions. These are not parked — they are queued.

- **The hidden starting network.** Cobra opens with one working network in one
  region and enough capital to improve weapons faster than it appears it can.
  Hook confirmed in `Mod::newSave`; `RuleRegion::getRandomPoint` places sites.
- **The cartel opening.** Scripted first mission against a drug cartel, its
  intel pointing to an abandoned Cobra weapons factory; the factory is empty
  until cartel gunmen stumble in as the Joes extract, and the intel found
  there is the date it comes back online.
- **The provocation gauge.** Accumulates on Joe actions, decays flat per
  month, feeds the planner's decision to attack a base. A shot-down scout
  moves the needle; it does not summon a retaliation.
- **Cobra cells** unconnected to the main economy, as something for the Joes
  to find.
- **Convoys and M.A.R.S.** — same faction, parallel, a stable force not driven
  by Cobra's economy; money that flows to it dies in the loop but stays at the
  site; restocks at a threshold; stock is its armoury.
- **The Drome superseding the crime launchers** — regional suppression on
  `genMission` once a Terror Drome stands.
