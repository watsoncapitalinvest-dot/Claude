# SCFL TRADE WARS — Arena Art Brief

Everything the art side needs. Self-contained: hand this over as-is.

---

## What the game is

A 2D turn-based artillery game. Two players lob shells at each other across a
battlefield. **The ground is fully destructible** — explosions blow chunks out of
it, and unsupported pieces collapse and fall.

Sixteen arenas. **Two PNG files each, thirty-two total.**

---

## THE ONE THING THAT MATTERS MOST

Each arena is **two layers** the game stacks at runtime:

- **BACKDROP** — the distant scene. Never collided with, never destroyed.
- **TERRAIN** — the solid mass players stand on and shells blow apart.

**The backdrop must NOT contain anything drawn in the terrain layer.**

If a building appears in both, blowing a hole in it reveals an identical intact
copy painted behind, and the destruction becomes invisible.

> **Test:** the backdrop alone should look like an establishing shot of an empty
> location — sky, horizon, far scenery, nothing in the foreground. Anything a
> shell can hit lives only in the terrain layer.

---

## TECHNICAL REQUIREMENTS — NON-NEGOTIABLE

### Size
**Every file is exactly 960 × 540 pixels.** Both layers of every arena, identical
dimensions, pixel-aligned. A mixed set cannot be used.

### `<key>-back.png` — backdrop
Fully opaque. No transparency anywhere.

### `<key>-terrain.png` — destructible mass
**Must carry a real alpha channel.** This is the entire mechanic:

- **Opaque pixel = solid ground.** Players stand on it, shells explode against
  it, blasts carve it away.
- **Transparent pixel = open air.** Shells fly through freely.
- **Never paint air as dark pixels.** It must be genuinely transparent, or shells
  hit invisible walls.

Rules:

1. **Bottom 40px solid across the entire width.** Otherwise players fall out of
   the world.
2. **Ground surface roughly between y 280 and y 460**, leaving sky to arc through.
3. **Everything connects down to the ground mass.** The engine drops anything
   unsupported the moment play starts. If it should hang in the air, it belongs
   in the backdrop.
4. **Nothing thinner than about 12px.** Thin spurs shatter into stray specks.
5. **Paint interiors as detail on solid pixels, not holes.** Windows, doors,
   signage, brickwork — painted on solid mass, not cut through, unless shells
   should fly through that gap.
6. **Darker interior tone behind façades.** A blast slices a hard edge through
   whatever was painted there; a darker interior fill makes craters read as
   depth rather than a bite out of a sticker.
7. **Structures must look plausibly supported** — wide bases, visible pillars.
   Undermining them makes them fall, so they should look like they could.

---

## STYLE BLOCK — apply to every image

> Pixel art plate for a 2D artillery game. Chunky visible pixels, limited
> palette, hard edges, no anti-aliasing, no soft gradients except broad sky
> bands. Dark and moody with low contrast — bright white text and glowing
> projectiles are drawn on top and must stay readable. Wide horizontal
> composition reading evenly across the full width, no single central focal
> point. No text, no letters, no numbers, no logos, no watermarks, no people or
> creatures, no foreground vehicles. Original generic environment art only —
> nothing resembling any existing film, television, game or brand.

## Composition zones

| Band | Status | What belongs there |
|---|---|---|
| y 0–36 | Covered by the HUD | Keep dark and plain |
| y 36–180 | **Always visible** | Sky and far scenery — the arena's identity |
| y 180–320 | Usually visible | Horizon, distant mid-ground |
| y 280–540 | Terrain territory | Ground mass, foundations, strata |

Keep the top third dark — a bright sky washes out white damage numbers drawn
over it. Avoid strong diagonal detail in y 180–320; shells leave a thin bright
trail there and busy diagonals make it hard to follow.

---

## THE SIXTEEN ARENAS

**1. `machines` — THE SCRAP WASTES** — *DONE*
*back:* Rust-orange smog sky, distant refinery towers, cooling stacks and crane
silhouettes on the horizon, hazy far ground.
*terrain:* Heaped mesas of crushed metal and slag at varying heights, a
half-buried machine hulk embedded in the piles, compacted scrap strata beneath.
One or two narrow transparent gaps between heaps.

**2. `porkchopexpress` — THE NIGHT MARKET** — *DONE*
*back:* Deep purple night sky, distant tower blocks with lit windows, paper
lanterns strung high across the width, night haze.
*terrain:* A solid row of two- and three-storey market buildings running the full
width at differing heights — tiled awnings, shuttered stall fronts, fire escapes,
stacked crates between them. Painted lit windows and signboards. Solid stone and
drainage mass beneath street level. Narrow transparent alleys between a few.

**3. `powersofpain` — THE SQUARED CIRCLE**
*back:* Blacked-out arena interior, banked crowd as dense dark dots, hard white
spotlight cones from above.
*terrain:* A raised canvas ring platform spanning the middle third with red
turnbuckle posts, apron skirt and scaffold decking beneath, arena floor either
side, solid to the bottom edge.

**4. `wookieleaks` — THE CANOPY**
*back:* Green-black forest mist, colossal trunks receding into haze, pale light
shafts between them.
*terrain:* Massive buttressed tree roots and fallen trunks forming the ground,
mossy earth banks at differing heights, dense root mass and loam beneath.

**5. `killerklowns` — THE BIG TOP**
*back:* Circus tent interior at night, red and cream striped canvas rising to a
dark peak, strings of dim bulbs.
*terrain:* Tiered wooden bleacher blocks and stacked equipment crates forming an
uneven surface, a low ring wall across the centre, sawdust and earth beneath.

**6. `smokedragons` — THE ASH PEAKS**
*back:* Bruised red volcanic sky, distant ridgeline, drifting ash, dull orange
glow along far slopes.
*terrain:* Jagged basalt outcrops and ash dunes at sharply varying heights, faint
magma veins glowing in the rock, dense stone strata beneath.

**7. `heavyhitters` — THE DEMOLITION SITE**
*back:* Dust haze under sodium lights, a wrecking crane silhouette, half-standing
concrete frames far off.
*terrain:* Partly collapsed concrete floor slabs and pillars at stepped heights,
exposed rebar painted flat against the mass, rubble mounds between them, broken
concrete fill beneath.

**8. `lilchops` — THE CHOP SHOP**
*back:* Cold fluorescent strips over a tiled back-of-house wall, hanging rails,
walk-in cooler doors.
*terrain:* Heavy butcher blocks, stacked steel prep counters and a long tiled
bench forming the surface at differing heights, drain channels and grouted tile
mass beneath. Muted red and bone white.

**9. `horsecollars` — THE STOCKYARD**
*back:* Dusk sky, distant timber stables, warm amber lamp glow.
*terrain:* Deep stacked hay bales, timber pen railings and feed troughs forming
stepped ground, packed dirt and buried fence posts beneath.

**10. `beavereaters` — THE DAM**
*back:* River gorge at blue hour, conifer treeline, still black water far below.
*terrain:* A great interlocked log dam spanning the full width, timber piled at
varying heights, silt and stone packed between the logs, solid to the bottom.

**11. `guidohaters` — THE BOARDWALK**
*back:* Seaside night, shuttered arcade fronts far off, a distant ferris wheel
outline, neon glow on the horizon.
*terrain:* A weathered plank promenade on thick pilings running the width,
benches and shuttered kiosk boxes rising at intervals, dark sand beneath.

**12. `masterjeti` — THE CANYON**
*back:* Twin-moon desert dusk, layered mesas receding into haze, wind-blown grit.
*terrain:* Banded sandstone shelves and pillars at strongly varying heights, wide
stable bases, deep red rock strata beneath.

**13. `bigblue` — THE STEEL SKYLINE**
*back:* Cold blue corporate towers in flat silhouette, grid-lit windows, low fog
at their base.
*terrain:* Rooftop level of a row of steel-and-glass buildings at differing
heights — parapets, rooftop plant housings, ventilation blocks. Painted window
grids. Girder and slab mass beneath.

**14. `stillthecream` — THE LOVE PAD**
*back:* 1970s bachelor lounge, wood panelling, mirrored ceiling, lava lamps
glowing warm pink and orange.
*terrain:* Deep shag carpet floor with a sunken conversation pit, a low modular
sofa run and a heart-shaped bed platform rising at differing heights, floorboards
beneath. Deliberately tacky, comic rather than explicit.

**15. `gumbas` — THE MUSHROOM FOREST**
*back:* Damp dusk forest, drifting spores, faint bioluminescence.
*terrain:* Oversized speckled toadstools with thick solid stalks and broad caps at
varying heights, mossy earth banks between them, peat beneath. Generic fantasy
only.

**16. `newworldorder` — THE FLOODLIT BOWL**
*back:* Empty stadium at night, four hard floodlight towers, tiered seating in
dark blocks, faint pitch mist.
*terrain:* Tiered concrete seating banks stepping down from both sides toward a
low central pitch, solid concrete footings and drainage layer beneath.

---

## DELIVERY

All files 960 × 540, named exactly:

```
machines-back.png          machines-terrain.png          DONE
porkchopexpress-back.png   porkchopexpress-terrain.png   DONE
powersofpain-back.png      powersofpain-terrain.png
wookieleaks-back.png       wookieleaks-terrain.png
killerklowns-back.png      killerklowns-terrain.png
smokedragons-back.png      smokedragons-terrain.png
heavyhitters-back.png      heavyhitters-terrain.png
lilchops-back.png          lilchops-terrain.png
horsecollars-back.png      horsecollars-terrain.png
beavereaters-back.png      beavereaters-terrain.png
guidohaters-back.png       guidohaters-terrain.png
masterjeti-back.png        masterjeti-terrain.png
bigblue-back.png           bigblue-terrain.png
stillthecream-back.png     stillthecream-terrain.png
gumbas-back.png            gumbas-terrain.png
newworldorder-back.png     newworldorder-terrain.png
```

Drop them in `tradewar/arenas/`. Any arena whose files are missing falls back to
procedurally generated ground, so partial delivery is fine — the game never
breaks waiting on art.

## CHECK BEFORE SENDING

- [ ] Both files exactly 960 × 540
- [ ] Terrain has a real alpha channel — open air transparent, not dark pixels
- [ ] Backdrop contains none of the terrain
- [ ] Terrain solid across the full width for the bottom 40px
- [ ] Every part of the terrain connects down to the ground mass
- [ ] Nothing in the terrain thinner than 12px
- [ ] No text, letters or numbers anywhere

**Send raw PNG files, not screenshots.** Alpha, exact size and edge-to-edge
coverage are all invisible in a screenshot.
