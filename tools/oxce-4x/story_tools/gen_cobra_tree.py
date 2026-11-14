"""Cobra's research tree (STORY, 13 Nov 2026). John 21:58: "Cobra works as if a player is there. So he needs to
research stuff. We need to do the Cobra research tree." 22:00: the escalation calendar wins every gear date
(first lasers months 9-14), over the master doc's act labels where they disagree.

Source: John's master doc (Research & Tech Tree Design), "Cobra's tech tree (approved Nov 9)", "Departments and
research heads (approved Nov 10)", the Crime and Infiltration tables (approved Nov 10); the escalation calendar in
tools/oxce-4x/CLAUDE.md; later decisions where they changed something (named in the notes column).

How Cobra's research works (master doc + ECONOMY.md, all approved):
- 11 departments. A department is researched at ONE bench anywhere in the world; a bench researches 10 points a month
  (projectProgressPerMonth). So each department works its topics one at a time, in the order written here.
- A topic only starts when its prerequisites are done and its earliest month has come; it is forced done at its latest
  month (the ceiling; the calendar is a rail for the AI side only).
- A finished topic UNLOCKS something, exactly as a player's research does (John 21:58). Gear and vehicles then have to
  be BUILT by a Cobra factory and SHIPPED to a region before its troops carry them (master doc, "Factories").
- Act projects (the Terror Drome, the Weather Dominator...) don't use a department bench: they run in their own chamber.

Act -> months, from the calendar: Act 1 = 1-12, Act 2 = 13-22, Act 3 = 23-30, Act 4 = 31-40, Act 5 = 41-50, Act 6 = 51-60.
Writes cobra_tree.yml next to this script and prints the schedule check. Usage: python3 gen_cobra_tree.py
"""
import os, sys, yaml

S = 'start'   # done at the start (Cobra's working start, master doc Nov 10)
# (id, name, department, cost, materielPerProgress, earliest, latest, requires, unlocks, note)
# unlocks keys (BUILD maps each to its engine id): kitTier:N, unit:<Cobra unit>, craft:<vehicle/aircraft/boat>,
# factory:<what a factory can now build>, site:<site type>, mission:<mission type>, ability:<rule switched on>,
# income:<source>.
T = [
 # ---------------- ARMORY (Destro; M.A.R.S. shipments before he appears in Act 2) ----------------
 ('STR_COBRA_SIDEARMS', 'Cobra Sidearms', 'ARMORY', 0, 0, S, None, [], ['kitTier:0'], 'handguns; no knife item exists yet'),
 ('STR_COBRA_RIFLES', 'Cobra Assault Rifle', 'ARMORY', 40, 2, 3, 8, [], ['kitTier:1'], 'calendar 4-8'),
 ('STR_COBRA_GRENADES', 'Cobra Grenades', 'ARMORY', 20, 2, 3, 8, ['STR_COBRA_RIFLES'], ['factory:Cobra grenade'], 'calendar 4-8'),
 ('STR_COBRA_LASERS', 'Cobra Laser Pistol and Rifle', 'ARMORY', 50, 3, 8, 14, ['STR_COBRA_GRENADES'], ['kitTier:2'], 'calendar 9-14 (John 22:00)'),
 ('STR_COBRA_BODY_ARMOR', 'Cobra Body Armor', 'ARMORY', 40, 2, 12, 20, ['STR_COBRA_LASERS'], ['factory:Cobra body armor'], 'Act 2'),
 ('STR_COBRA_PULSE_WEAPONS', 'Cobra Pulse Pistol', 'ARMORY', 50, 4, 14, 22, ['STR_COBRA_BODY_ARMOR'], ['kitTier:3'], 'calendar 15-22'),
 ('STR_COBRA_PULSE_RIFLES', 'Cobra Pulse Rifle', 'ARMORY', 60, 4, 22, 30, ['STR_COBRA_PULSE_WEAPONS'], ['kitTier:4'], 'calendar 23-30'),
 ('STR_COBRA_HEAVY_PULSE', 'Heavy Pulse Weapons', 'ARMORY', 60, 5, 30, 36, ['STR_COBRA_PULSE_RIFLES'], ['kitTier:5'], 'calendar 31+'),
 ('STR_COBRA_SHIELD_ARMOR', 'Cobra Shield Armor', 'ARMORY', 60, 4, 31, 40, ['STR_COBRA_HEAVY_PULSE'], ['factory:shield armor'], 'Act 4; bullets pass shields, lasers do not'),
 ('STR_COBRA_COBRANIUM', 'Cobranium Alloys', 'ARMORY', 70, 5, 33, 40, ['STR_COBRA_SHIELD_ARMOR'], ['ability:Cobra vehicles and armour +armour'], 'Act 4'),
 ('STR_COBRA_IRON_GRENADIER_ARSENAL', 'Iron Grenadier Arsenal', 'ARMORY', 70, 5, 41, 50, ['STR_COBRA_COBRANIUM'], ['factory:Iron Grenadier weapons', 'income:arms sales to both sides'], 'Act 5, Civil War'),
 ('STR_COBRA_ISLAND_DEFENSES', 'Island Defenses', 'ARMORY', 80, 5, 51, 60, ['STR_COBRA_IRON_GRENADIER_ARSENAL'], ['site:Cobra Island coastal guns, anti-air, sea mines'], 'Act 6'),
 # ---------------- MOTOR POOL AND ARMOR (Destro, with Scrap-Iron) ----------------
 ('STR_COBRA_CONVOY_TRUCKS', 'Convoy Trucks', 'MOTOR_POOL', 0, 0, S, None, [], ['craft:cargo truck'], 'truck logistics from the start'),
 ('STR_COBRA_STINGER', 'Stinger', 'MOTOR_POOL', 30, 2, 3, 8, [], ['craft:Stinger', 'unit:Stinger Driver'], 'calendar 4-8'),
 ('STR_COBRA_HISS_TANK', 'H.I.S.S.', 'MOTOR_POOL', 50, 3, 6, 12, ['STR_COBRA_STINGER'], ['craft:H.I.S.S.', 'unit:H.I.S.S. Driver'], 'calendar: by month 12'),
 ('STR_COBRA_HEAVY_WEAPONS', 'M.A.R.S. Heavy Weapons', 'MOTOR_POOL', 40, 3, 9, 14, ['STR_COBRA_HISS_TANK'], ['factory:rocket launchers, heavy machine guns'], 'calendar 9-14'),
 ('STR_COBRA_VEHICLE_LASERS', 'Vehicle Lasers', 'MOTOR_POOL', 60, 4, 23, 30, ['STR_COBRA_HEAVY_WEAPONS'], ['ability:Cobra vehicles carry lasers'], 'Act 3'),
 ('STR_COBRA_HISS_II', 'H.I.S.S. II', 'MOTOR_POOL', 70, 4, 31, 40, ['STR_COBRA_VEHICLE_LASERS'], ['craft:H.I.S.S. II'], 'Act 4'),
 # ---------------- AIR WING (Wild Weasel from Act 2; Viper Pilot officers before) ----------------
 ('STR_COBRA_EARLY_AIRCRAFT', 'Vulture, F.A.N.G. and Viper Glider', 'AIR_WING', 0, 0, S, None, [], ['craft:Vulture', 'craft:F.A.N.G.', 'craft:Viper Glider', 'unit:Viper Pilot'], 'from the start'),
 ('STR_COBRA_RATTLER', 'Rattler', 'AIR_WING', 40, 3, 3, 8, [], ['craft:Rattler'], 'Year 1 strike jet (DOGFIGHT_DESIGN_v1)'),
 ('STR_COBRA_NIGHT_RAVEN', 'Night Raven', 'AIR_WING', 40, 3, 6, 12, ['STR_COBRA_RATTLER'], ['craft:Night Raven'], 'Year 1 spy plane (DOGFIGHT_DESIGN_v1, 13 Nov), not Act 2'),
 ('STR_COBRA_AIR_SUPERIORITY', 'Terror Drome Firebat', 'AIR_WING', 40, 3, 8, 12, ['STR_COBRA_NIGHT_RAVEN'], ['craft:Firebat'], 'with the Act 1 project; flies from Dromes only'),
 ('STR_COBRA_MAMBA', 'Mamba', 'AIR_WING', 50, 3, 23, 30, ['STR_COBRA_AIR_SUPERIORITY'], ['craft:Mamba'], 'Act 3 helicopter (battlefield only)'),
 ('STR_COBRA_CONDOR', 'Condor Z25', 'AIR_WING', 70, 4, 31, 40, ['STR_COBRA_MAMBA'], ['craft:Condor'], 'Act 4 bomber'),
 ('STR_COBRA_HURRICANE', 'Hurricane VTOL', 'AIR_WING', 70, 4, 41, 50, ['STR_COBRA_CONDOR'], ['craft:Hurricane', 'ability:fighters from any Cobra base'], 'Act 5'),
 # ---------------- NAVY (Copperhead for rivers; Lamprey officers at sea) ----------------
 ('STR_COBRA_MERCHANT_FLEET', 'Cobra Merchant Fleet', 'NAVY', 0, 0, S, None, [], ['craft:Cobra-owned freighter'], "front companies' own lines (SEA_BATTLES_DESIGN_v1 12a)"),
 ('STR_COBRA_PATROL_BOATS', 'Water Moccasin', 'NAVY', 40, 2, 4, 12, [], ['craft:Water Moccasin', 'unit:Water Moccasin crew'], 'Act 1 rivers and swamps'),
 ('STR_COBRA_FLAGGED_SHIPS', 'Cobra-Flagged Ships', 'NAVY', 40, 3, 8, 16, ['STR_COBRA_PATROL_BOATS'], ['craft:Cobra-flagged ship'], 'armed ships that run or fight (SEA 12f)'),
 ('STR_COBRA_MORAY', 'Moray Hydrofoil', 'NAVY', 50, 3, 13, 22, ['STR_COBRA_FLAGGED_SHIPS'], ['craft:Moray', 'unit:Lamprey'], 'Act 2'),
 ('STR_COBRA_PIRANHA', 'Piranha and Sea Sled', 'NAVY', 30, 2, 13, 22, ['STR_COBRA_MORAY'], ['craft:Piranha', 'craft:Sea Sled'], 'Act 2 (rendered 13 Nov)'),
 ('STR_COBRA_SUBMARINES', 'Sea Ray', 'NAVY', 60, 4, 23, 30, ['STR_COBRA_PIRANHA'], ['craft:Sea Ray', 'unit:Sea Slug'], 'Act 3'),
 ('STR_COBRA_TORPEDO', 'Cobra Torpedo', 'NAVY', 40, 3, 23, 30, ['STR_COBRA_SUBMARINES'], ['factory:Cobra torpedoes'], 'Act 3'),
 # ---------------- TROOPS AND TRAINING (Big Boa from Act 4; the Officer Corps before) ----------------
 ('STR_COBRA_RECRUITMENT', 'Cobra Recruitment', 'TROOPS', 0, 0, S, None, [], ['unit:Cobra Recruit', 'unit:Cobra Soldier'], 'from the start'),
 ('STR_COBRA_OFFICER_CORPS', 'Officer Corps', 'TROOPS', 30, 1, 3, 8, [], ['unit:Cobra Officer'], 'calendar 4-8'),
 ('STR_COBRA_VIPER_PROGRAM', 'Viper Program', 'TROOPS', 60, 2, 12, 20, ['STR_COBRA_OFFICER_CORPS'], ['unit:Viper'], 'the 1986 standard trooper; "the Viper comes sooner than Act 3" (Nov 10)'),
 ('STR_COBRA_TELE_VIPER', 'Tele-Viper Comms', 'TROOPS', 30, 1, 13, 22, ['STR_COBRA_VIPER_PROGRAM'], ['unit:Tele-Viper', 'unit:Techno-Viper'], 'Act 2 technicians'),
 ('STR_COBRA_COLD_WATER', 'Snow Serpents and Eels', 'TROOPS', 40, 2, 13, 22, ['STR_COBRA_TELE_VIPER'], ['unit:Snow Serpent', 'unit:Eel'], 'Act 2 arctic and divers'),
 ('STR_COBRA_TROOP_PROGRAMS', 'Viper Specialists', 'TROOPS', 50, 2, 23, 30, ['STR_COBRA_COLD_WATER'], ['unit:Frag-Viper', 'unit:H.E.A.T. Viper', 'unit:S.A.W.-Viper', 'unit:Laser-Viper', 'unit:Flak-Viper', 'unit:Incinerator'], 'Act 3'),
 ('STR_COBRA_NIGHT_VIPER', 'Night-Viper and Terrain Troops', 'TROOPS', 50, 2, 23, 30, ['STR_COBRA_TROOP_PROGRAMS'], ['unit:Night-Viper', 'unit:Rock-Viper', 'unit:Desert Scorpion', 'unit:Ice-Viper', 'unit:W.O.R.M.S.'], 'Act 3'),
 ('STR_COBRA_ALLEY_VIPER', 'Alley Viper and Range-Viper', 'TROOPS', 60, 3, 31, 40, ['STR_COBRA_NIGHT_VIPER'], ['unit:Alley Viper', 'unit:Range-Viper'], 'Act 4 (urban assault, shields; wilderness)'),
 # ---------------- ELITE GUARD (Tomax and Xamot) ----------------
 ('STR_COBRA_CRIMSON_GUARD', 'Crimson Guard Program', 'ELITE_GUARD', 50, 3, 14, 22, [], ['unit:Crimson Guard'], 'calendar 15-22'),
 ('STR_COBRA_SLEEPER_CELLS', 'Sleeper Cells', 'ELITE_GUARD', 40, 2, 15, 22, ['STR_COBRA_CRIMSON_GUARD'], ['ability:Crimson Guard sleeper cells raise a country\'s infiltration'], 'Act 2'),
 ('STR_COBRA_CRIMSON_IMMORTALS', 'Crimson Guard Immortals', 'ELITE_GUARD', 60, 3, 23, 30, ['STR_COBRA_SLEEPER_CELLS'], ['unit:Crimson Guard Immortal', 'unit:Crimson Guard Commander'], 'Act 3'),
 # ---------------- BIOLOGY (Dr. Mindbender from Act 3; Medi-Viper officers before) ----------------
 ('STR_COBRA_MEDI_VIPER', 'Medi-Viper Program', 'BIOLOGY', 30, 1, 3, 8, [], ['unit:Medi-Viper'], 'calendar 4-8'),
 ('STR_COBRA_MEDICINE', 'Field Medicine', 'BIOLOGY', 40, 2, 6, 14, ['STR_COBRA_MEDI_VIPER'], ['ability:wounded Cobra heal faster'], 'Act 1-2'),
 ('STR_COBRA_BAT_PROGRAM', 'B.A.T.', 'BIOLOGY', 60, 4, 18, 24, ['STR_COBRA_MEDICINE'], ['unit:B.A.T. (general garrisons)'], 'before this, B.A.T.s only in named missions (calendar 4-22)'),
 ('STR_COBRA_BAT_LEGIONS', 'B.A.T. Legions', 'BIOLOGY', 60, 4, 22, 30, ['STR_COBRA_BAT_PROGRAM'], ['factory:B.A.T. line', 'unit:Overkill\'s B.A.T. squads'], 'calendar 23-30'),
 ('STR_COBRA_BRAINWAVE', 'Brainwave Attack', 'BIOLOGY', 50, 3, 23, 30, ['STR_COBRA_BAT_LEGIONS'], ['ability:Mindbender\'s mind control in battle'], 'calendar 23-30'),
 ('STR_COBRA_TOXO', 'Toxo-Zombies and Toxo-Viper', 'BIOLOGY', 50, 4, 24, 30, ['STR_COBRA_BRAINWAVE'], ['unit:Toxo-Zombie', 'unit:Toxo-Viper', 'mission:spore attack'], 'calendar 23-30'),
 ('STR_COBRA_MIND_PROBE', 'Cobra Mind Probe', 'BIOLOGY', 40, 3, 25, 34, ['STR_COBRA_TOXO'], ['ability:faster interrogation of captured Joes'], 'Act 3'),
 ('STR_COBRA_CLONING_VATS', 'Cloning Vats', 'BIOLOGY', 70, 5, 31, 40, ['STR_COBRA_MIND_PROBE'], ['factory:cloning vats (Serpentor\'s guard, Synthoids)'], 'Act 4'),
 ('STR_COBRA_SYNTHOIDS', 'Synthoids', 'BIOLOGY', 80, 5, 41, 50, ['STR_COBRA_CLONING_VATS'], ['unit:Synthoid'], 'Act 5; placed by Infiltration'),
 # ---------------- INTELLIGENCE (the Baroness from Act 2; front-company officers before) ----------------
 ('STR_COBRA_INFORMANTS', 'Informant Networks', 'INTELLIGENCE', 0, 0, S, None, [], ['ability:informants report Joe activity'], 'from the start'),
 ('STR_COBRA_SPY_NETWORK', 'Signals Intercept', 'INTELLIGENCE', 40, 2, 4, 12, [], ['ability:Cobra reads Joe radio traffic: more ambushes on Joe flights'], 'Act 1'),
 ('STR_COBRA_JOE_GEAR_TEARDOWN', 'Joe Gear Teardown', 'INTELLIGENCE', 40, 2, 6, 16, ['STR_COBRA_SPY_NETWORK'], ['ability:captured Joe weapons used for subterfuge'], 'needs a captured Joe weapon'),
 ('STR_COBRA_PIT_SEARCH', 'Pit Search Doctrine', 'INTELLIGENCE', 60, 3, 13, 22, ['STR_COBRA_JOE_GEAR_TEARDOWN', 'STR_COBRA_NIGHT_RAVEN'], ['ability:Night Raven sweeps hunt for The Pit'], 'Act 2'),
 ('STR_COBRA_FIND_THE_PIT', 'Joe Vehicle Teardown', 'INTELLIGENCE', 50, 3, 23, 30, ['STR_COBRA_PIT_SEARCH'], ['ability:captured Joe vehicles studied and copied'], 'Act 3; needs a salvaged Joe wreck'),
 ('STR_COBRA_COUNTRY_INFILTRATION', 'Country Infiltration II', 'INTELLIGENCE', 60, 3, 31, 40, ['STR_COBRA_FIND_THE_PIT'], ['ability:countries flip faster'], 'Act 4'),
 ('STR_COBRA_ANTI_SATELLITE', 'Anti-Satellite', 'INTELLIGENCE', 60, 4, 31, 40, ['STR_COBRA_COUNTRY_INFILTRATION'], ['ability:counters the Defiant'], 'Act 4'),
 ('STR_COBRA_PROPAGANDA', 'Propaganda Broadcasts', 'INTELLIGENCE', 50, 2, 41, 55, ['STR_COBRA_ANTI_SATELLITE'], ['ability:Fear earned faster'], 'Act 5-6'),
 # ---------------- CRIME (Tomax and Xamot, then Headman) — master doc table, Nov 10 ----------------
 ('STR_COBRA_FRONT_COVER', 'Front-Company Cover', 'CRIME', 0, 0, S, None, [], ['site:front company', 'income:front companies'], 'start'),
 ('STR_COBRA_SMUGGLING', 'Smuggling', 'CRIME', 0, 0, S, None, [], ['income:gun-running routes'], 'start'),
 ('STR_COBRA_EXTORTION', 'Extortion Rackets', 'CRIME', 0, 0, S, None, [], ['income:protection money where Cobra has Fear'], 'start'),
 ('STR_COBRA_BANK_JOBS', 'Bank Jobs', 'CRIME', 20, 1, 1, 6, [], ['mission:bank and armored-car robbery'], 'Act 1 (loud)'),
 ('STR_COBRA_HACKING', 'Hacking', 'CRIME', 40, 1, 6, 14, ['STR_COBRA_BANK_JOBS'], ['income:bank and corporate theft', 'ability:exposes Joe operations'], 'Act 1'),
 ('STR_COBRA_KIDNAPPING', 'Kidnapping for Ransom', 'CRIME', 30, 1, 6, 12, ['STR_COBRA_BANK_JOBS'], ['mission:kidnapping (hostage rescue)', 'income:ransom'], 'Act 1 (loud)'),
 ('STR_COBRA_LAUNDERING', 'Money Laundering', 'CRIME', 30, 1, 13, 22, ['STR_COBRA_HACKING'], ['ability:Cobra cash harder to trace (Follow the Money slower)'], 'Act 2 (quiet)'),
 ('STR_COBRA_COUNTERFEITING', 'Counterfeiting', 'CRIME', 40, 2, 13, 22, ['STR_COBRA_LAUNDERING'], ['site:Counterfeiting Press', 'ability:weakens a target country\'s funding'], 'Act 2'),
 ('STR_COBRA_BLACK_MARKET', 'Black Market Arms', 'CRIME', 30, 2, 15, 22, ['STR_COBRA_COUNTERFEITING'], ['income:M.A.R.S. surplus sold to outside buyers', 'mission:arms sale'], 'Act 2'),
 ('STR_COBRA_TAKEOVERS', 'Corporate Takeovers', 'CRIME', 40, 1, 23, 30, ['STR_COBRA_BLACK_MARKET'], ['income:steady clean income and influence'], 'Act 3 (quiet; superficial intel-room operations, John 13 Nov)'),
 ('STR_COBRA_STOCKS', 'Stock Manipulation', 'CRIME', 40, 1, 23, 30, ['STR_COBRA_TAKEOVERS'], ['income:big, risky payouts'], 'Act 3 (quiet)'),
 ('STR_COBRA_BRIBERY', 'Bribery Networks', 'CRIME', 50, 1, 31, 40, ['STR_COBRA_STOCKS'], ['ability:countries resist Cobra less and flip faster'], 'Act 4'),
 ('STR_COBRA_NARCOTICS', 'Narcotics', 'CRIME', 50, 2, 41, 50, ['STR_COBRA_BRIBERY'], ['unit:Headman', 'unit:Headhunters', 'income:big, every operation raises exposure'], 'Act 5 (loud)'),
 ('STR_COBRA_CITY_GANGS', 'City Gangs', 'CRIME', 40, 1, 41, 50, ['STR_COBRA_NARCOTICS'], ['unit:Gristle', 'mission:more crime missions in cities'], 'Act 5'),
 # ---------------- INFILTRATION (Zartan, from Act 2) — master doc table, Nov 10 ----------------
 ('STR_COBRA_DISGUISE', 'Disguise', 'INFILTRATION', 30, 1, 13, 22, [], ['ability:agents pass as civilians and officials'], 'Act 2'),
 ('STR_COBRA_DREADNOK_GANG', 'Dreadnok Gang', 'INFILTRATION', 20, 1, 13, 22, ['STR_COBRA_DISGUISE'], ['unit:Dreadnoks (hired, unreliable)'], 'Act 2'),
 ('STR_COBRA_DREADNOK_WEAPONS', 'Dreadnok Weapons', 'INFILTRATION', 20, 2, 13, 22, ['STR_COBRA_DREADNOK_GANG'], ['factory:chainsaws, cutting torches, Ripper\'s claw'], 'Act 2'),
 ('STR_COBRA_CHAMELEON', 'Chameleon', 'INFILTRATION', 20, 2, 13, 22, ['STR_COBRA_DREADNOK_WEAPONS'], ['craft:Chameleon'], 'Act 2'),
 ('STR_COBRA_JOE_UNIFORMS', 'Joe Uniforms', 'INFILTRATION', 30, 1, 15, 24, ['STR_COBRA_CHAMELEON', 'STR_COBRA_JOE_GEAR_TEARDOWN'], ['ability:disguises from captured Joe gear'], 'Act 2'),
 ('STR_COBRA_DREADNOK_VEHICLES', 'Dreadnok Bikes and Buggies', 'INFILTRATION', 30, 2, 23, 30, ['STR_COBRA_JOE_UNIFORMS'], ['craft:Ground Assault', 'craft:Dreadnok Cycle', 'craft:Thunder Machine'], 'Act 3'),
 ('STR_COBRA_DREADNOK_SWAMP', 'Dreadnok Swamp Craft', 'INFILTRATION', 30, 2, 23, 30, ['STR_COBRA_DREADNOK_VEHICLES'], ['craft:Swampfire', 'craft:Air Skiff', 'craft:Air Assault'], 'Act 3'),
 ('STR_COBRA_FALSE_FLAG', 'False Flag Operations', 'INFILTRATION', 40, 2, 23, 30, ['STR_COBRA_DREADNOK_SWAMP'], ['mission:false flag attack (goodwill loss until exposed)'], 'Act 3'),
 ('STR_COBRA_FAKE_SIGNALS', 'Fake Joe Signals', 'INFILTRATION', 40, 1, 23, 30, ['STR_COBRA_FALSE_FLAG'], ['mission:decoy mission requests and false recalls'], 'Act 3'),
 ('STR_COBRA_MOLES', 'Mole Insertion', 'INFILTRATION', 50, 1, 25, 32, ['STR_COBRA_FAKE_SIGNALS'], ['ability:unnamed moles inside Joe ranks (leaks, sabotage)'], 'Act 3'),
 ('STR_COBRA_INFILTRATOR_SQUADS', 'Infiltrator Squads', 'INFILTRATION', 50, 2, 31, 40, ['STR_COBRA_MOLES'], ['unit:Cobra squads disguised as Joes in battle'], 'Act 4'),
 ('STR_COBRA_IMPERSONATION', 'Impersonation', 'INFILTRATION', 50, 1, 31, 40, ['STR_COBRA_INFILTRATOR_SQUADS'], ['ability:Zartan replaces officials; countries flip faster'], 'Act 4'),
 ('STR_COBRA_SYNTHOID_DEPLOYMENT', 'Synthoid Deployment', 'INFILTRATION', 60, 2, 41, 50, ['STR_COBRA_IMPERSONATION', 'STR_COBRA_SYNTHOIDS'], ['ability:Synthoids placed in governments (can flip a country)'], 'Act 5'),
 ('STR_COBRA_DREADNOK_BATTLE_AXE', 'Dreadnok Battle Axe', 'INFILTRATION', 30, 3, 41, 50, ['STR_COBRA_SYNTHOID_DEPLOYMENT'], ['factory:late Dreadnok heavy weapons'], 'Act 5'),
 # ---------------- INTERROGATION (Cobra Officers from the start, Crystal Ball in Act 4) ----------------
 ('STR_COBRA_INTERROGATION', 'Interrogation', 'INTERROGATION', 0, 0, S, None, [], ['ability:captured Joes leak (CAPTURE_DESIGN_v1)'], 'runs from the start (Nov 10)'),
 ('STR_COBRA_CRYSTAL_BALL', 'Hypnosis', 'INTERROGATION', 50, 1, 31, 40, [], ['unit:Crystal Ball', 'ability:captured Joes leak faster'], 'Act 4'),
 ('STR_COBRA_CONDITIONING', 'Conditioning', 'INTERROGATION', 60, 2, 41, 50, ['STR_COBRA_CRYSTAL_BALL'], ['ability:captured unnamed Joes returned as moles'], 'Act 5'),
 ('STR_COBRA_MASS_HYPNOSIS', 'Mass Hypnosis', 'INTERROGATION', 70, 3, 45, 58, ['STR_COBRA_CONDITIONING', 'STR_COBRA_SYNTHOIDS'], ['ability:mass hypnosis (with Mindbender)'], 'Act 5-6'),
]

# Act projects: each runs in its own chamber (Cobra rooms), not on a department bench (master doc "Act projects").
PROJECTS = [
 ('STR_COBRA_PROJECT_TERROR_DROME', 'The First Terror Drome', 1, 'site:Terror Drome', 'built by the planner on Cobra\'s clock, months 8-12 (COBRA_ACT1_TIMETABLE_v1)'),
 ('STR_COBRA_PROJECT_WEATHER_DOMINATOR', 'Weather Dominator', 2, 'storms: funding drops, flights grounded, countries near flipping', 'Weather Dominator Chamber'),
 ('STR_COBRA_PROJECT_MASS_DEVICE', 'MASS Device', 3, 'strikes anywhere without a route; The Pit\'s concealment drops', 'MASS Device Chamber'),
 ('STR_COBRA_PROJECT_SERPENTOR', 'Serpentor', 4, 'Serpentor and his guard at full strength', 'Serpentor Genetics Chamber; needs Cloning Vats'),
 ('STR_COBRA_PROJECT_REBUILDING', 'Rebuilding Cobra', 5, 'Cobra reunites around the Civil War winner', 'the winner\'s HQ'),
 ('STR_COBRA_PROJECT_ISLAND_NATION', 'Cobra Island Nation', 6, 'Cobra Island recognised as a country', 'Intelligence (Recognition Campaign)'),
]

RATE = 10   # points a month per bench (projectProgressPerMonth)


def fit_costs():
    """Cap costs so a FREE-RUNNING Cobra (a bench per department from month 0) finishes every topic at least one month
    before its ceiling. A starved Cobra still hits the ceilings: that is what they are for. Works department by department
    in list order, shrinking a topic (never below 10) until it fits; prints every change."""
    global T
    changed = []
    for _ in range(1000):
        done = schedule()
        bad = [t for t in T if done.get(t[0], (0, False))[1] or (t[6] is not None and done[t[0]][0] > t[6] - 1)]
        if not bad: break
        t = bad[0]; i = T.index(t)
        # shrink this topic, or if it is already at the floor, the dearest earlier topic in its department
        cands = [x for x in T[:i + 1] if x[2] == t[2] and x[5] != S and x[3] > 10]
        if not cands: break
        v = max(cands, key=lambda x: x[3]); j = T.index(v)
        T[j] = v[:3] + (v[3] - 10,) + v[4:]
        changed.append((v[0], v[3], v[3] - 10))
    merged = {}
    for k, a, b in changed: merged[k] = (merged.get(k, (a,))[0], b)
    return merged


def schedule():
    """One bench per department from month 0, a free-running Cobra (the fastest case): each month the department works
    the first topic in its list whose prerequisites are done and whose earliest month has come; a topic still unfinished
    at its latest month is forced done (the ceiling). Returns {id: (month done, forced?)}."""
    done = {t[0]: (0, False) for t in T if t[5] == S}
    depts = sorted(set(t[2] for t in T))
    prog = {}
    for m in range(0, 61):
        for d in depts:
            for t in T:
                tid, _, dep, cost, _, e, l, req, *_ = t
                if dep != d or tid in done: continue
                if m < e or not all(r in done for r in req): continue
                prog[tid] = prog.get(tid, 0) + RATE
                if prog[tid] >= cost: done[tid] = (m + 1, False)
                break
        for t in T:   # ceilings
            if t[0] not in done and t[6] is not None and m + 1 >= t[6]: done[t[0]] = (t[6], True)
    return done


if __name__ == '__main__':
    ids = [t[0] for t in T]
    assert len(ids) == len(set(ids)), 'duplicate id'
    bad = [(t[0], r) for t in T for r in t[7] if r not in ids]
    assert not bad, bad
    fitted = fit_costs()
    if fitted: print('costs fitted to the windows:', ', '.join(f'{k[10:]} {a}->{b}' for k, (a, b) in fitted.items()))
    done = schedule()
    late = [(t[0], done[t[0]][0], t[6]) for t in T if done.get(t[0], (99,))[1]]
    early = [(t[0], done[t[0]][0], t[5]) for t in T if t[5] != S and t[0] in done and done[t[0]][0] < t[5]]
    print(f'{len(T)} topics in {len(set(t[2] for t in T))} departments, {len(PROJECTS)} act projects')
    for d in sorted(set(t[2] for t in T)):
        row = [f"{t[1]} {done[t[0]][0]}{'!' if done[t[0]][1] else ''}" for t in T if t[2] == d and t[5] != S]
        print(f'  {d:13s}', ' | '.join(row))
    print('forced by a ceiling (a department too slow even with a bench from month 0):', late or 'none')
    print('done before its floor:', early or 'none')
    out = {'cobraResearchTopics': [dict(type=t[0], name=t[1], department=t[2], cost=t[3], materielPerProgress=t[4],
                                        **({'doneAtStart': True} if t[5] == S else {'earliestMonth': t[5], 'latestMonth': t[6]}),
                                        requires=t[7], unlocks=t[8], note=t[9]) for t in T],
           'cobraActProjects': [dict(type=p[0], name=p[1], act=p[2], ifCobraFinishes=p[3], where=p[4]) for p in PROJECTS]}
    hdr = ('# Cobra research tree (STORY). Generated by gen_cobra_tree.py: edit the script, not this file.\n'
           '# Design: claude/COBRA_RESEARCH_TREE_v1.md. BUILD maps each unlocks: entry to its engine id.\n')
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cobra_tree.yml'), 'w').write(hdr + yaml.dump(out, sort_keys=False, width=200, allow_unicode=True))
    print('wrote cobra_tree.yml')
