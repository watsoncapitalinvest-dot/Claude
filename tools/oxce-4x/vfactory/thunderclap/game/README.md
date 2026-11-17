# Thunderclap tractor + trailer as battle units (VFACTORY, 17 Nov 2026)

Code only. The blends, renders and sprites are private (Reference\ and mod/Resources/VehiclesPrivate, gitignored).

1. `detail_paint.py k_<v>.blend d_<v>.blend`: more detail on the guns and missiles in the same colours. Turret: steel barrels, black bores,
   dark undersides and small parts. Stores renamed `missile_*` so the renderer gives them rounded missile shading: dark nose, nozzle, a band, fins a shade down.
2. `run.sh <v> <first missile> <tip>` (env `DMG` = dir of hit stickers, magenta-keyed): the damaged look (`damage_generic.py` + `dmg_<v>.json`),
   then ROSTER's gen chain: render.py, turret.py, full_launch.py, pkg.py, turret_pkg.py, preview.py, turntable.py, with `crisp_out.py` in between.
   That step sharpens the turret and missile pixels and brings the turret's tone down to the hull's.
3. `mkcfg.py` writes the two cfgs: 3x3, scale 0.01266, states m0..m3, turret and muzzles, with canon weapon names.
4. Install: `ONLY=thunderclap_tractor,thunderclap_trailer python3 build/gen_vehicles.py <packs> mod`.
   The gun is the main weapon; the missiles are a second built-in weapon (`wpn2`).
