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

### The Pit floors: what the 15 Nov pass left (PIT_FLOORS_v1)
Built: six 3 x 2 blocks on the 6 x 6 grid (Surface + floors 1-5), a room only on its floor, no corridors
needed, the Day 1 layout, Lab Bench 10 seats, the Surface cap 2/3/4, Research Lab and Manufacturing outpost
kinds, the Lab and Fabrication Shop as outpost add-ons. Owed:
- the HQ Command Center airfield as the Day 1 outpost with Ace's Skystriker (needs a new-game hook; the game
  starts with no Skystriker today, so nothing is lost yet);
- labs and shops 25% faster at the two new outpost kinds; at most one Lab or Fabrication Shop on an ordinary outpost;
- the Command Center as a 2x1 room (it is the 1x1 Access Lift);
- base defence on the stacked canon Pit (MAPS' per-facility pieces; the floors fight side by side on one flat map now);
- the second Pit: its Command Center placement does not check the floor yet (PlaceLiftState);
- old campaign saves keep their 6 x 6 layout; rooms off their floor stay where they are.

### Shipping: what the 15 Nov pass left (SEA design 7, 9, 12)
- the warning network for hijackings (always alerted now); the held ship sailing to a hidden Cobra port to be tailed;
- Washington impounding a Cobra line at 3 Confirmed ships; wrecks and the wreck dive;
- a bluffing crew that reveals itself partway through boarding (aboard from the start now);
- a merchant picture for the sea fight (the Cobra ship greyed is the stand-in);
- trackers from bugged crates confirming a ship at once (only research and analysts feed ship intel now).

### MAPS' 13-14 Nov maps: wired for New Battle, not for the campaign (14 Nov)

Harbour, hijacked ship, container ship, riot, chop shop, junkyard, small city (day and damaged),
the lab outpost (.MAP2 version, desert ring) and the bank robbery are in `gijoe_maps_14nov.rul`;
Emmaville's 27 noded sample pieces are in `gijoe_maps_emmaville.rul` (generated by
`build/gen_emmaville_rul.py`). Each loaded in New Battle with the Joes on their start nodes; the
bank, the lab and the harbour were played three turns. What is NOT built:

- **No campaign mission sends any of them.** Each has a test deployment only.
- **Hooks the briefs ask for:** hostage shooting (bank, hijacked ship); container doors waking the
  hidden minders (container ship, harbour); the riot's weapons locker and lift exit; Clutch as a Joe
  (he is a civilian stand-in); the hijack timer; the lab's department head staying in his office,
  sabotage targets and booby traps. The bank reuses the armored-car robbery's exit/leader/points hooks.
- **Small city:** night and damaged-night terrains are defined but nothing picks them by time of day.
- **Lab:** only the desert ring exists; the eight other biome rings are still to come from MAPS.
- **Emmaville:** EMMA_LM_RADIO_B and EMMA_LM_SUBSTATION_C have no route nodes, so the Joes cannot be
  placed; they are left out of the deployments. Fire escapes, roof hatches, manholes, the subway
  stairs and the highway ramps (MAPS' "test first" list) were not walked.
- Fixed on the way in: small_city.rul had its `mapScripts:` block in the middle of `terrains:`; its
  `addLine` used OXCE's default groups (crossing = 4, the landmark group) and crashed; the engine read
  .MAP/.MAP2 header sizes as signed bytes, so Emmaville's 240-wide weirs and 200-long bridge refused.

### Air fights: what Phase 1 still lacks (14 Nov)

- ~~Transports need a pilot~~ — John 14 Nov 10:56 "It needs a pilot": Tomahawk, Phantom and Defiant
  have `pilots: 1`; the pilot is one of the squad and fights on the ground with them (engine default).
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

### The canon Pit battle: what is left (build/gen_pit_canon.py, BattlescapeGenerator::applyPitModules)
- **pit_canon_v4 in (15 Nov evening):** 27 of the 35 slots follow what is built, fit-outs copied from MAPS'
  showcase map (PITSHOW). Day 1 = STORY's v1.1 (Command Center, Bunks in NCO 1, Lab Bench, one A.P.C.); CAST's
  spec says Lab Bench only, STORY to settle (one line in MAPS' pitfit.py STATES).
- **Rooms with no facility in the game** stay as Day 1 draws them: Pentagon Hook-up, Briefing, Hologram,
  Situation Analysis, Archives, Computer Banks, the two MG nests, Ammo Dump, Backup Data Vault.
- **A fit-out copied from another slot** keeps its own facing (Comms Room in ops_g1 comes from ops_g2, the second
  Lab Bench from CLASSIFIED 1, the Workbench in the SW garage from the SE one); seen and they read fine, but a
  door-side mismatch is possible elsewhere. Only floors and objects travel; walls stay the slot's own.
- **Caps** now apply per group (comms rooms 3, training 4, recruiting 2, quarters 8, infirmary 1, CLASSIFIED 4,
  detention 1, workbench 2). The cap refusal in the base screen has still not been seen.
- **No surface.** Cobra comes in at Staging and the alternate escape tunnel. Stacking PITSURF over it waits.
- **Not seen:** a campaign base defence, a fight to the end. Two Cobra died on Staging in the first 5 turns of
  one test with no Joe in sight: cause not found.

### Villains: what the 15 Nov pass left (build/gen_villains.py, Battlescape/Villains.cpp)
- **Arrival is John's open question** ("save this for later. Deeper discussion"): every villain is missionOnly, so
  in a campaign none appears unless a deployment names him.
- **Moves built (Year 1):** Bludd's mark, Firefly's charge, Storm Shadow's silent shot from hiding (John replaced the Arashikage Strike, 17:31), Scrap-Iron's launcher (stock
  launcher AI, vehicles first), Copperhead's drop, Buzzer's cut-through, Ripper's door, Torch's cut and burn.
  Seen in the test: the mark, the drop, Torch's breach, the charge left. NOT seen: the charge going off on a Joe,
  Storm Shadow's shot from hiding, Buzzer, Ripper, a Scrap-Iron launch. Bludd's marked list is Duke and Hawk only
  ("any Joe who has downed him" needs memory across missions).
- **Not built:** Zartan's disguise (parked fork), Wild Weasel's strafing run (air fights), and every Move and
  scripted trait from months 14 on (Baroness, Tomax/Xamot, Destro, CC, Mindbender, Serpentor, Big Boa, Croc
  Master, Crystal Ball, Raptor's reveal, Zarana, Zandar, Monkeywrench, Thrasher, Zanzibar, Road Pig,
  Gnawgahyde, Overkill). Copperhead's swamp movement and Torch's faster fire are not built either.
- **Look:** 19 villains wear the Cobra trooper's sheet until ROSTER renders them; downed villains drop a trooper
  corpse. Weapons are stand-ins from items the game has (chainsaw, claw and gloves use the sword's sprites).
- **Test:** New Battle "Cobra villains (Year 1 test)" on HUNTAMB; OXCE_VILLAIN_TEST=1 makes Cobra know every
  Joe, the Joes hold reaction fire and Cobra never retreats, so each Move shows in a few turns.

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

### Muzzle flashes - HELD until John says "build now" (15 Nov 19:56)
- Art (John's downloads, licences unknown: private, zip only, never the repo):
  C:\Users\Chairman\Downloads\muzzle_flashs.zip (16 cartoon flashes, 256x256, red/orange/yellow) and
  rc_art_-_muzzle_effects.zip (Reactorcore Art: 232 pixel sprites, yellow fire, blue ion, red/green melee slashes).
- Plan given to John: the game has no muzzle flash today. Engine: on each firearm shot draw a flash for 1-2
  frames at the weapon's hand anchor pushed out along the shooter's facing, turned to the facing (8 directions),
  a new one per round on auto. Cartoon set on rifles, pistols, MGs (random pick; scaled up for heavy guns and
  vehicle cannons); RC blue ion on lasers / pulse; RC slashes on melee hits. About 2-3 hours with screenshots.

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

## Pit attack from the surface - HELD until John says "go" (15 Nov 21:51)
John 21:51: "fight should start with cobra landing on the surface, they don't know about the secret entrances unless through their intel. then they fight their way down." 21:51: "dont build until i say go".
This is PIT_FALLS_DESIGN_v1 section 1 (approved 13 Nov). What is shipped (237004b) starts Cobra in the garage AND the escape tunnel, intel or not - wrong on both counts.
Plan offered: (1) stage 1 on PITGATE, hold the surface = attack beaten; (2) lose it -> stage 2 on the canon Pit, survivors carried, Cobra starts at the lift landing; (3) the water-tower hatch is Cobra's only if leaked (stand-in: Cobra's file on the Joes past a threshold) - leaked = guarded on the surface, maybe a 2nd team through it; (4) Joes use the hatch to flank, 2 turns. About a day for 1-3, half a day for 4.
Unchecked: nextStage on a base-defence mission (fallback: yard stacked on top as one tall map). Not covered: surface guns opening (surface install), Evacuate / Self-Destruct.

## Continue or exfiltrate - HELD until John says "build now" (16 Nov 00:22)
John 00:19: "all targets neutralized - continue or exfiltrate? every map". Written, not built: build/held/ (HOOKS.txt + SecureAreaState.h/.cpp).
Asked once when the last Cobra goes down (also on Cobra's turn); not air/sea fights, MUST_DESTROY or VIP escorts. EXFILTRATE = end now, a win. CONTINUE = turns pass, ABORT ends it as a full win (not a retreat).

## Pit free placement (STORY's BRIEF_FOR_BUILD_PitFreePlacement) - HELD until John says "build now" (16 Nov 00:22)
Replaces the 35 slots and applyPitModules' slot groups. Stamping at any tile: yes, the copy is per tile, no coarse grid. Rotation: only with a drawn rotated version from MAPS (sprites can't turn). The cost is the screen: five blueprint sheets, drag a card, green/red fit, rotate, save tile positions (each module keeps a hidden 6x6 grid spot for capacity/build/dismantle). 2-3 days vs about 1 for the slots. Reachability flood fill is cheap: include it. Throws away the slot groups (mod_update_13) and rewrites the bay plan in BRIEF_FOR_MAPS_PitModuleSpec.
