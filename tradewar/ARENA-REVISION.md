# SCFL TRADE WARS — Art Brief

Self-contained. Everything needed is in this document.

I have a 2D turn-based artillery game. Two players lob shells at each other
across a battlefield. **The ground is fully destructible** — explosions blow
chunks out of it, and unsupported pieces collapse and fall.

Sixteen arenas exist already. The **backdrops are finished and must not be
changed.** This brief is a revision of the sixteen **terrain** layers, plus notes
on a sprite pack.

---

# PART 1 — HOW THE TWO LAYERS WORK

Each arena is two images the game stacks at runtime:

- **BACKDROP** (`<key>-back.png`) — the distant scene. Never collided with,
  never destroyed. **Already done. Do not touch.**
- **TERRAIN** (`<key>-terrain.png`) — the solid mass players stand on and shells
  destroy. **This is what needs revising.**

The backdrop must never contain anything drawn in the terrain layer. If a
building appears in both, blowing a hole in it just reveals an identical intact
copy painted behind, and the destruction becomes invisible.

## Terrain layer — hard requirements

**Exactly 960 × 540 pixels. Must carry a real alpha channel.** The alpha is the
entire mechanic:

- **Opaque pixel = solid ground.** Players stand on it, shells explode against
  it, blasts carve it away.
- **Transparent pixel = open air.** Shells fly through freely.
- **Never paint air as dark or black pixels.** It must be genuinely transparent,
  or shells hit invisible walls.

Plus:

1. **Bottom 40px solid across the entire width** — otherwise players fall out of
   the world.
2. **Everything connects down to the ground mass.** The engine drops anything
   unsupported the moment play starts. If it should hang in the air, it belongs
   in the backdrop.
3. **Nothing thinner than 12px.** Thin spurs shatter into stray specks when a
   blast cuts them.
4. **Paint interiors as detail on solid pixels, not holes.** Windows, doors,
   signage, brickwork — painted on solid mass, not cut through.
5. **A darker interior tone behind façades.** A blast slices a hard edge through
   whatever was painted there; a darker fill makes craters read as depth rather
   than a bite out of a sticker.
6. **Structures must look plausibly supported** — wide bases, visible pillars.
   Undermining them makes them fall, so they should look like they could.

## Style

> Pixel art plate for a 2D artillery game. Chunky visible pixels, limited
> palette, hard edges, no anti-aliasing, no soft gradients. Dark and moody with
> low contrast — bright white text and glowing projectiles are drawn on top and
> must stay readable. Wide horizontal composition reading evenly across the full
> width. No text, no letters, no numbers, no logos, no watermarks, no people or
> creatures. Original generic environment art only — nothing resembling any
> existing film, television, game or brand.

---

# PART 2 — THE TWO FIXES

## FIX 1 — Remove the border frame

Every plate delivered so far has a frame baked into it:

- a band of opaque pixels **4 to 14 rows deep across the entire top edge**
- **fully solid columns down the extreme left and right edges**

In the game that top band is an invisible ceiling every high shot detonates
against, and it also breaks player placement.

**The terrain layer must have transparent pixels at the top edge and along both
side edges.** No frame, no border, no backing rectangle. The only place solid
pixels touch an edge is the bottom.

## FIX 2 — Far more height variation

This is the main change. Several plates are close to a flat shelf, so both
players stand at the same height and fire straight at each other. The point of
an artillery game is arcing a shot over something.

Three requirements, all measurable:

**a. The ground surface must span at least 200px vertically.** Measure the
highest and lowest points of the walkable surface across the width — the
difference should be 200px or more. Several current plates are under 60px.

**b. There must be a tall mass in the middle third.** At least one solid
structure whose top reaches **y = 260 or higher** (upper half of the field),
sitting between x = 320 and x = 640. This is what the shot has to clear.

**c. The left and right thirds must sit at clearly different heights.** Not a
mirror image — one side high, one side low, by at least 120px. The players start
in those outer thirds; if they match, the fight is symmetrical and dull.

Keep the wide supported bases. A tall mass still needs to look like it could
stand, because undermining it makes it fall.

---

# PART 3 — WHICH ARENAS, IN PRIORITY ORDER

Measured over 20 rounds each, these have the least ground between the two
starting positions. Work down the list.

| Arena | What it needs |
|---|---|
| `stillthecream` — THE LOVE PAD | **Worst by far.** A low flat platform with nothing to shoot over. Needs a genuine tall element — a tall headboard, a mirrored column, a raised bar unit — reaching the upper half. |
| `heavyhitters` — THE DEMOLITION SITE | A standing concrete frame or crane base much taller than the rubble. |
| `porkchopexpress` — THE NIGHT MARKET | Buildings are all similar height. Make one a five-storey tenement, drop others to single-storey stalls. |
| `machines` — THE SCRAP WASTES | Heaps too even. One towering heap, one low flat span. |
| `newworldorder` — THE FLOODLIT BOWL | Terraces step too gently. Steepen them and raise one side. |
| `smokedragons` — THE ASH PEAKS | Add one genuinely tall spire. |
| `guidohaters` — THE BOARDWALK | Deck is flat end to end. Add a raised pier or a tall shuttered pavilion. |
| `masterjeti` — THE CANYON | Mesas too close in height. Push one much higher. |

**Already good — leave alone, or adjust only lightly for Fix 1:**
`gumbas` (MUSHROOM FOREST) · `powersofpain` (THE SQUARED CIRCLE) ·
`wookieleaks` (THE CANOPY) · `bigblue` (THE STEEL SKYLINE) ·
`beavereaters` (THE DAM) · `lilchops` (THE CHOP SHOP) ·
`killerklowns` (THE BIG TOP) · `horsecollars` (THE STOCKYARD)

Every one of the sixteen still needs Fix 1 applied.

---

# PART 4 — SELF-CHECK BEFORE SENDING

For each terrain file:

- [ ] Top edge and both side edges transparent — no frame
- [ ] Bottom 40px solid across the full width
- [ ] Surface high point and low point differ by 200px or more
- [ ] A solid mass in the middle third reaching y = 260 or higher
- [ ] Left and right thirds differ in height by 120px or more
- [ ] Nothing thinner than 12px, everything connected to the ground
- [ ] Exactly 960 × 540, alpha channel intact
- [ ] No text, letters or numbers anywhere

**Send raw PNG files, not screenshots.** Alpha, exact size and edge coverage are
all invisible in a screenshot.

Filenames, unchanged:

```
machines-terrain.png          porkchopexpress-terrain.png
powersofpain-terrain.png      wookieleaks-terrain.png
killerklowns-terrain.png      smokedragons-terrain.png
heavyhitters-terrain.png      lilchops-terrain.png
horsecollars-terrain.png      beavereaters-terrain.png
guidohaters-terrain.png       masterjeti-terrain.png
bigblue-terrain.png           stillthecream-terrain.png
gumbas-terrain.png            newworldorder-terrain.png
```

---

# PART 5 — THE SPRITE PACK

Separately, on the 87-file sprite set: only four files were usable. Two problems,
both in export rather than art.

**1. Every sprite has its own filename painted into the image.** Actual pixels
sitting under the artwork — `explosion_large_1.png`, `debris_small.png` and so
on. Burned into the assets, not captions on a contact sheet.

**2. The crops are offset by roughly one cell.** Files contain fragments of
neighbouring sprites, or the wrong asset entirely: `hud_power_meter` holds the
angle dial, `hud_angle_meter` holds the wind arrows, `hud_wind` is a slice.
`explosion_small_1/2/3`, `debris_small` and `dust_cloud` crop down to nothing.

**If redone:** one sprite per file, trimmed to its own content, transparent
background, **no filename or caption rendered into the image**.

**Worth redoing:** the remaining explosion frames, the debris and dust frames,
and `logo_main` — that logo would improve the splash screen, but it currently has
"logo_main.png" across the bottom and an empty frame attached beneath it.

**Skip entirely:** the HUD panels, meters, buttons and menus. They were built for
a different design — an END TURN button (turns end on their own in this game), a
turn timer, a PLAY/ARENAS/OPTIONS/QUIT menu, and six ammo types that are not this
game's eight rounds.
