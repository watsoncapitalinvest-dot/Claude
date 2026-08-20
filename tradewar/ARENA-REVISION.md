# SCFL TRADE WARS — Terrain Revision

Second pass on the terrain layers. **Backdrops are finished — do not change
them.** Only the sixteen `<key>-terrain.png` files need work.

Everything in the original brief still applies: 960 × 540, real alpha channel,
opaque = solid ground, transparent = open air, bottom 40px solid across the
full width, nothing thinner than 12px, everything connected down to the ground
mass.

---

## FIX 1 — Remove the border frame

Every plate delivered has a frame baked into it:

- a band of opaque pixels **4 to 14 rows deep across the entire top edge**
- **fully solid columns down the extreme left and right edges**

In the game that top band is an invisible ceiling that every high shot
detonates against, and it also breaks crest placement. The engine currently
strips it on load, but it should not be there.

**The terrain layer must have transparent pixels at the top edge and along both
side edges.** No frame, no border, no backing rectangle. The only place solid
pixels touch an edge is the bottom.

---

## FIX 2 — Far more height variation

This is the main change. Right now several plates are close to a flat shelf, so
both players stand at the same height and fire straight at each other. The whole
point of an artillery game is arcing a shot over something.

Three requirements, all measurable:

**a. The ground surface must span at least 200px vertically.** Measure the
highest and lowest points of the walkable surface across the width — the
difference should be 200px or more. Several current plates are under 60px.

**b. There must be a tall mass in the middle third.** At least one solid
structure whose top reaches **y = 260 or higher** (upper half of the field),
sitting somewhere between x = 320 and x = 640. This is what the shot has to
clear. Without it there is no arc.

**c. The left and right thirds must sit at clearly different heights.** Not a
mirror image. One side high, one side low, by at least 120px. The two players
start in those outer thirds, so if they match, the fight is symmetrical and
dull.

Keep the wide supported bases — a tall mass still needs to look like it could
stand, because undermining it makes it fall.

---

## Priority order

Measured over 20 rounds per arena, these have the least ground between the two
starting positions. Work down the list:

| Arena | State |
|---|---|
| `stillthecream` — THE LOVE PAD | **Worst by far.** A low flat platform with nothing to shoot over. Needs a genuine tall element — a tall headboard, a mirrored column, a raised bar unit — reaching the upper half. |
| `heavyhitters` — THE DEMOLITION SITE | Needs a standing concrete frame or crane base much taller than the rubble. |
| `porkchopexpress` — THE NIGHT MARKET | Buildings are all similar height. Make one a five-storey tenement, drop others to single-storey stalls. |
| `machines` — THE SCRAP WASTES | Heaps are too even. One towering heap, one low flat span. |
| `newworldorder` — THE FLOODLIT BOWL | Terraces step too gently. Steepen them and raise one side. |
| `smokedragons` — THE ASH PEAKS | Add one genuinely tall spire. |
| `guidohaters` — THE BOARDWALK | Deck is flat end to end. Add a raised pier structure or a tall shuttered pavilion. |
| `masterjeti` — THE CANYON | Mesas are close in height. Push one much higher. |

**Already good — leave alone or adjust only lightly:** `gumbas` (MUSHROOM
FOREST), `powersofpain` (THE SQUARED CIRCLE), `wookieleaks` (THE CANOPY),
`bigblue` (THE STEEL SKYLINE), `beavereaters` (THE DAM), `lilchops` (THE CHOP
SHOP), `killerklowns` (THE BIG TOP), `horsecollars` (THE STOCKYARD).

---

## Self-check before sending

For each terrain file:

- [ ] Top edge and both side edges are transparent — no frame
- [ ] Bottom 40px solid across the full width
- [ ] Surface high point and low point differ by 200px or more
- [ ] A solid mass in the middle third reaching y = 260 or higher
- [ ] Left and right thirds differ in height by 120px or more
- [ ] Nothing thinner than 12px, everything connected to the ground
- [ ] Still exactly 960 × 540, alpha channel intact
- [ ] No text, letters or numbers anywhere

Send raw PNG files.

---

# SPRITE PACK — what went wrong

Separately, on the 87-file sprite set. Only four files were usable. Two problems,
both in export rather than art:

**1. Every sprite has its own filename painted into the image.** Actual pixels,
sitting under the artwork — `explosion_large_1.png`, `debris_small.png` and so
on. These are not labels in a contact sheet, they are burned into the assets.

**2. The crops are offset by roughly one cell.** Files contain fragments of
neighbouring sprites, or the wrong asset entirely: `hud_power_meter` holds the
angle dial, `hud_angle_meter` holds the wind arrows, `hud_wind` is a slice.
`explosion_small_1/2/3`, `debris_small` and `dust_cloud` crop down to nothing.

**If redone:** one sprite per file, trimmed to its own content, transparent
background, **no filename or caption rendered into the image**.

**Worth redoing:** the remaining explosion frames, the debris and dust frames,
and `logo_main` — that logo would improve the splash screen, but it currently
has "logo_main.png" across the bottom and an empty frame attached beneath it.

**Skip entirely:** the HUD panels, meters, buttons and menus. They were built for
a different design — an END TURN button (turns end on their own here), a turn
timer, a PLAY/ARENAS/OPTIONS/QUIT menu, and six ammo types that are not this
game's eight rounds.
