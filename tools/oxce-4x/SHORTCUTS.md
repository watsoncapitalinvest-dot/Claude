# Temporary shortcuts, to review later

John, 12 Nov 2026 20:49: "some shortcuts accepted temporarily", and 21:09: "note the shortcuts
so we can review in the future". Everything here is in the game ON PURPOSE as a stand-in, and
none of it is the design. Each line says what the shortcut is, what the real thing is, and
where the real thing is written down. Remove a line when the real thing ships.

Kept apart from BACK_BURNER.md, which is for things parked by decision, things owed and bugs.

| # | Shortcut in the game now | The real thing | Where it's specified |
|---|---|---|---|
| 1 | Interceptions resolve at once: the craft attacks on Standard, breaks off at half damage, and a one-line report pops up. `OXCE_DOGFIGHT_WINDOW=1` brings the stock window back for testing. | The turn-based tactical air war on a hex grid with altitude bands, pilot moves, cargo forced down, fight-or-auto-resolve with odds. | Master design doc, "Dogfights (approved Nov 9)" |
| 2 | Everything loads at start-up (`-lazyLoadResources false` in Play_4x.bat): about 1.3 GB resident at the Geoscape, roughly 9 s longer to start. | Screens open fast without holding everything: preload in the background, or load per screen ahead of time. | ENGINE_NOTES.md, "Frame cost and screen opening" |
| 3 | Day 1: the Bare-5 Pit is built from stock X-COM room types renamed (Access Lift = Command, Living Quarters = Barracks, General Stores = Stores, Laboratory = Lab, Hangar = Motor Pool). | Real Pit room types with their own rules (department head stations, what each room does). | DAY1_SETUP.md section 4; FACILITY_MANIFEST.txt |
| 4 | Day 1: the A.P.C. is a transport craft that can cross water, and it lands on the Tomahawk helicopter's battle map. Its base-plan picture is now its own (ART's cartoon set, 12 Nov). | A land-only troop truck (no water crossing), with its own battle-map block (MAPS, from ART's 11 views in art_briefs/returned/apc_cartoon). | DAY1_SETUP.md; master doc "Day 1 transport (decided Nov 9)" |
| 5 | Day 1: the 16 named Joes have placeholder stats and the stock rank. | Each Joe's own record: fixed stats, specialties, canon rank, trait, move, bonds, voice. | ROSTER chat, claude/HANDOFF_Characters.md; Roster and Arsenal Bible |
| 6 | Named Joes without their own rendered sprite yet wear Duke's; greenshirt riflemen and medics wear Beach Head's until theirs are rendered. | Every Joe in his own look. | The render split, claude/BRIEF_RENDER_KIT_from_BUILD.txt |
| 7 | Day 1 kit uses the guns that exist as items (M4 Carbine for the M-16, Uzi for the pistol, and so on); signature weapons are not items yet. | The 21 signature weapons as items with their own stats and sprites; the decided Day 1 kit list. | DAY1_SETUP.md section 5; art_briefs/returned/weapons_2d |
| 8 | Department heads exist only as a name in the design; no head slows or speeds anything. | Named heads (Hawk, Scarlett, Doc, Breaker, Roadblock on Day 1) whose injury or capture slows their branch: John 12 Nov 21:50, only very slightly, ideally not at all, so heads are lanes in the research tree first and a speed effect is optional. | DAY1_SETUP.md section 2; master doc, research heads |
| 9 | Held weapons on the new soldier sprites are fitted onto the old X-COM held frames. | Weapons rendered from the 3D set in the soldiers' own camera and facings, placed by each frame's hand anchors. | BUILD status, signature weapons row |
| 10 | Stock X-COM research is still in the lab (STORY's tree replaces it). | Year 1 research and story. | STORY chat, claude/HANDOFF_ResearchStory.md |
| 11 | Battles use reworked X-COM terrain; a FANG on the battle map is the grey saucer. | Our own maps per mission type; Cobra vehicles as units up to 4x4. | MAPS chat; CONVOY_RAID_DESIGN.md; HANDOFF_BattleMaps.md |
| 12 | Shots are the stock small sprites; the projectile work is parked in wip_projectiles/. | Blue Joe / red Cobra fire, bigger shots, rockets pointing where they fly. | wip_projectiles/README.txt |
| 13 | The graphs screen and some other stock screens keep the 1994 look. | Restyled to the UI standard. | UI_STANDARD_v1.md |
| 14 | Mission 1 (Cartel Ranch) appears on the Geoscape about an hour into a new game, on the Rio Grande, for 30 days (BUILD's zz_gijoe_day1_opener.rul, a stand-in until STORY's opener loads). Its garrison is 8-10 Cobra troopers with pistols plus the officer rank as the boss, and BUILD added 12 G.I. Joe start points (route nodes, rank XCOM, priority 5) in the north-west landing zone. The A.P.C. starts loaded with the first mission's gear, taken out of the Day 1 stores. | The Day 1 opening mission wired by STORY's scripts (Hawk's briefing, the lead chain), the real cartel gunmen and boss, and MAPS' own start points. | MAP_DESIGN_M1_CartelBase.md; STORY_Year1_ResearchMap.md; MAPS status |
| 15 | Chuckles is pulled: his soldier type stays in the files but cannot be hired (costBuy 0), so he never appears. | Chuckles back in, rebuilt to the same standard as the other named Joes (look, record, weapon). | ROSTER chat; mod/Ruleset/gijoe_chuckles.rul |
