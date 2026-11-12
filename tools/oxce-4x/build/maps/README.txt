Craft and vehicle tilesets: the earlier pipeline that made the Joe craft battle maps
(JOEHELO, JOEPHANT, JOEDEFI) from 3D models. Kept here as the starting point for the MAPS
chat (claude/HANDOFF_BattleMaps.md, claude/CONVOY_RAID_DESIGN.md).

build_craftmap.py  3D model (OBJ) -> per-cell iso pictures -> <SET>.PCK/TAB (32x40) and
                   <SET>_4X.PCK/TAB (128x160, the 4x twin, same frame order), an MCD cloned
                   from PLANE.MCD records, a 10x10x3 MAP and an RMP. Settings per craft in
                   craftmaps.json; the cells come from craftmap.html/craftmap.js.
build_terrain.py, build_map.py, build_heli.py  helpers it reads from.
Paths inside point at the session that wrote them; repoint before use. Models are not kept
in the repo (licences vary).
