AMMO v2 — 13 Nov 2026
Replaces section 8 of UI REMAINING. No heavy-cannon/autocannon boxes included.

30 game PNGs are together in ammo/. All PNGs have genuine transparent alpha.
Equipment: 128 x 192, centered, straight orthographic overhead, no 3/4 view.
Floor: 128 x 160, small isometric view positioned on the bottom 128 x 64 tile.
No floor diamond is painted into the shipping sprites.

LATEST FOOTPRINT CORRECTION FROM JOHN:
Magazines: 1 x 1. Rockets/missiles, containers and belts: 1 x 2.
Other item footprints retain the brief: speedloader, shells, battery and flares
1 x 1; mortar bomb and crossbow bolt 1 x 2. One slot is 64 x 64 pixels.

Inventory icons are sized for these updated footprints. Relative magazine
lengths are preserved: 20-round M16 is shorter than 30-round M16; the AK has a
deeper curve; Uzi is long and thin; M1911 is short. The .50 can is larger and
chunkier than the M19A1 can. The comparison sheet uses equal pixel scaling
for all 15 exported inventory icons, enlarged uniformly 2x for viewing.
It does not enlarge each item separately. Inventory icon sizes are not a
common physical ruler across all weapon classes; floor sprites use their
separate world-size calibration. Fictional ammo sizes are art design targets.

Permitted stencils only: 7.62, .50 CAL, HEDP. Other ammo has no text or markings.
The loader shows six cartridge bases; the shotgun bundle has eight shells;
the rescue bandolier has three flare cartridges.

ERA NOTE: SMAW was first fielded in 1984, after the 1982 setting. Its original
sealed HEDP tube is included because the approved v2 item list requests it.
Source: United States Marine Corps, SMAW receives new modular ballistic sight
https://www.marines.mil/News/News-Display/Article/509566/smaw-receives-new-modular-ballistic-sight/
Power javelin is the fictional Joe weapon, not a modern FGM-148 Javelin.
Laser battery and crossbow bolt use the specified 1980s science-fiction look.

Built-in image generation was used for each of the 30 individual master
drawings. Export preparation preserves silhouette/aspect ratio, removes
low-opacity background haze and reduces to exact game canvas sizes. Full
prompt set is included in PROMPTS.txt. MANIFEST.csv records the actual visible
dimensions, footprints and hashes. No game rules or older art are modified.

VALIDATION: Exact filenames/count, RGBA modes, canvas sizes, transparency,
centered inventory slot bounds and floor-diamond bounds all passed.
Visual previews reviewed; not tested inside OpenXCOM.
