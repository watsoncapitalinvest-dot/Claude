"""Batch 3 (STORY): G.I. Joe research, Year 1. Writes gijoe_research_joe.rul.
Open on Day 1 = John's short list (12 Nov 21:10). Nothing opens by date (John 21:20): the rest follows from research,
and the months in the design are estimates of research time and cost. Gear the Joes already carry on Day 1 is
'done at start' (BUILD's starting research). Items, crafts, facilities and manufacture that these topics open are
BUILD's rules; they point at these names."""
import yaml, sys, os
OUT = sys.argv[1]
SECTION = 'STR_JOE_RESEARCH_FILES'
T = []   # (id, name, cost, points, deps, text)
def t(i, n, c, p, deps, txt): T.append((i, n, c, p, deps, txt))
# --- done at start (BUILD: starting research). Listed so the tree and the articles exist.
t('STR_STANDARD_ISSUE', 'Standard Issue', 10, 0, [], 'The rifles, pistols and submachine guns the Joes carry on Day 1, and the signature weapons each named Joe brings with him.')
t('STR_STANDARD_EXPLOSIVES', 'Standard Explosives', 10, 0, [], 'Fragmentation and smoke grenades: Army issue, bought and delivered.')
t('STR_STANDARD_FATIGUES', 'Standard Fatigues', 10, 0, [], 'Every Joe\'s own uniform, and flak vests for the greenshirts.')
t('STR_FIELD_MEDICINE', 'Field Medicine', 10, 0, [], 'Medkits and the training to use them under fire.')
t('STR_BREACHING_SHOTGUN', 'Breaching Shotgun', 10, 0, [], 'Pump shotguns for close quarters and for doors that will not open.')
# --- open on Day 1 (John's short list)
t('STR_KEVLAR_VEST', 'Kevlar Vest', 80, 10, [], 'Soft body armour that stops pistol rounds and fragments. Heavier than a flak vest and worth it.')
t('STR_AP_ROUNDS', 'Armor-Piercing Rounds', 80, 10, [], 'Hardened-core magazines for the rifles, the sniper rifle and Roadblock\'s .50 cal. For targets behind steel.')
t('STR_FIELD_RADIO', 'Field Radio', 60, 10, [], 'A man-pack radio like Breaker\'s. A Joe carrying one can call in support the base has researched.')
t('STR_NIGHT_VISION', 'Night-Vision Goggles', 80, 10, [], 'Starlight goggles. Joes wearing them see as far at night as Cobra does in the day.')
t('STR_VAMP', 'VAMP', 120, 20, ['STR_VAMP_RECOVERED'], 'The Multi-Purpose Attack Vehicle: a fast four-wheel-drive with a twin machine gun. Two Joes, any road.')
t('STR_SKYSTRIKER', 'Skystriker', 250, 30, [], 'The Skystriker XP-14F: G.I. Joe\'s swing-wing fighter. It needs a hangar. Upgrades keep it Joe\'s dogfighter for the whole war.')
t('STR_RADAR_ROOM', 'Radar Room', 150, 20, [], 'A radar room for The Pit. Until it is built, Cobra is found only through leads, intel and its own mistakes.')
t('STR_C130_HERCULES', 'C-130 Hercules', 200, 30, [], 'Strategic airlift. The A.P.C. cannot cross water; the Hercules can carry a squad and its vehicles to another continent, if there is a landing zone at the other end.')
# --- the rest of the master doc's Day 1 list: no date gate (John 21:20: months are estimates of research time and
#     cost, never a switch). Each one follows from a Day 1 topic, so it takes real research to reach.
for i, n, c, dep, txt in [
 ('STR_MATCH_GRADE_OPTICS', 'Match-Grade Optics', 60, 'STR_AP_ROUNDS', 'Scopes for the M-16: a marksman in every squad.'),
 ('STR_C4_DEMOLITIONS', 'C-4 Demolitions', 60, 'STR_AP_ROUNDS', 'Satchel charges that open walls and doors.'),
 ('STR_CLAYMORE_MINES', 'Claymore Mines', 60, 'STR_AP_ROUNDS', 'Directional mines for ambushes and for guarding a flank.'),
 ('STR_MOBAT', 'MOBAT', 250, None, 'The Motorized Battle Tank: G.I. Joe\'s first tank.'),
 ('STR_RAM', 'R.A.M.', 60, None, 'The Rapid-fire Motorcycle: a scout bike with a machine gun in a sidecar.'),
 ('STR_HAL', 'H.A.L.', 150, 'STR_MOBAT', 'The Heavy Artillery Laser: a towed laser cannon.'),
 ('STR_FLAK', 'F.L.A.K.', 100, 'STR_RADAR_ROOM', 'A towed anti-aircraft gun for The Pit and the outposts.'),
 ('STR_WOLVERINE', 'Wolverine', 200, 'STR_MOBAT', 'An armoured missile carrier: light tank and fire support.'),
 ('STR_SLUGGER', 'Slugger', 250, 'STR_MOBAT', 'A self-propelled cannon: artillery on the battle map.'),
 ('STR_POLAR_BATTLE_BEAR', 'Polar Battle Bear', 150, None, 'A tracked arctic vehicle, at its best in snow and ice.'),
 ('STR_MMS', 'M.M.S.', 100, 'STR_FIELD_RADIO', 'The Mobile Missile System: off-map missile support a Joe with a radio can call in.'),
 ('STR_MOUNTAIN_HOWITZER', 'Mountain Howitzer', 100, 'STR_FIELD_RADIO', 'A light howitzer for off-map fire support.'),
 ('STR_DRAGONFLY', 'Dragonfly', 200, 'STR_C130_HERCULES', 'An attack helicopter that flies over the battle map.'),
 ('STR_FALCON_GLIDER', 'Falcon Glider', 60, 'STR_C130_HERCULES', 'A silent glider for night insertions.'),
 ('STR_SKY_HAWK', 'Sky Hawk', 120, 'STR_SKYSTRIKER', 'A light VTOL that escorts transports.'),
 ('STR_SHARC', 'S.H.A.R.C.', 200, 'STR_SKYSTRIKER', 'A flying submarine: air and underwater.'),
 ('STR_MANTA', 'MANTA', 60, None, 'A small amphibious assault craft.'),
 ('STR_KILLER_WHALE', 'Killer W.H.A.L.E.', 300, 'STR_MANTA', 'A hovercraft assault transport for squads and light vehicles.'),
 ('STR_JUMP_JET_PACK', 'J.U.M.P. Jet Pack', 120, 'STR_KEVLAR_VEST', 'A jet pack launched from a ground platform.'),
 ('STR_PAC_RATS', 'PAC/RATs', 60, 'STR_FIELD_RADIO', 'Remote-controlled tracked weapons: machine gun, flamethrower and missile.'),
 ('STR_BATTLE_STATIONS', 'Battle Stations', 80, 'STR_RADAR_ROOM', 'Machine gun, missile and mortar defense units for The Pit and the outposts.'),
 ('STR_WATCH_TOWER', 'Watch Tower', 40, 'STR_RADAR_ROOM', 'A tower that spots Cobra sooner, and makes the base easier to spot.'),
 ('STR_BIVOUAC', 'Bivouac', 40, 'STR_FIELD_RADIO', 'A field camp: cheap barracks for outposts.')]:
    t(i, n, c, 10, [dep] if dep else [], txt)   # None = no prerequisite (John 13 Nov 20:55: only VAMP Mk II waits for Clutch)
# --- follow-ons that can land in Year 1
for i, n, c, deps, txt in [
 ('STR_SQUAD_AUTOMATIC_WEAPON', 'Squad Automatic Weapon', 150, ['STR_AP_ROUNDS'], 'The M249 SAW: a light machine gun for the squad.'),
 ('STR_INCENDIARY_ROUNDS', 'Incendiary Rounds', 120, ['STR_AP_ROUNDS'], 'Incendiary ammunition for the .50 cal and the grenade launcher.'),
 ('STR_CONCUSSION_GRENADE', 'Concussion Grenade', 80, ['STR_C4_DEMOLITIONS'], 'A stun grenade. Prisoners feed the trail; this takes them alive.'),
 ('STR_THERMITE', 'Thermite', 100, ['STR_INCENDIARY_ROUNDS'], 'Thermite grenades that burn through doors and vehicles.'),
 ('STR_LASER_GUIDED_ROCKETS', 'Laser-Guided Rockets', 150, ['STR_MATCH_GRADE_OPTICS'], 'A guided round for the rocket launcher.'),
 ('STR_JOE_COBRA_GRENADE', 'Joe-Built Cobra Grenade', 80, ['STR_ALIEN_GRENADE'], 'Cobra\'s own grenade design, built in our shop.'),
 ('STR_GHILLIE_SUIT', 'Ghillie Suit', 60, ['STR_KEVLAR_VEST'], 'Sniper camouflage.'),
 ('STR_ARCTIC_GEAR', 'Arctic Gear', 80, ['STR_KEVLAR_VEST'], 'Cold-weather suits for polar missions.'),
 ('STR_NINJA_GEAR', 'Ninja Gear', 150, ['STR_ARASHIKAGE'], 'What the Arashikage prisoner wore and how it is made: a stealth suit in the Snake Eyes style.'),
 ('STR_COMBAT_STIMS', 'Combat Stims', 80, ['STR_FIELD_MEDICINE'], 'A stim pack that restores energy and cuts stun.'),
 ('STR_TRAUMA_KIT', 'Trauma Kit', 120, ['STR_FIELD_MEDICINE', 'STR_VIPER_MEDIC'], 'Built from the Medi-Viper\'s kit: a trauma kit that heals more than a medkit.'),
 ('STR_INFIRMARY', 'Infirmary', 150, ['STR_TRAUMA_KIT'], 'An infirmary for The Pit: wounded Joes recover faster.'),
 ('STR_VAMP_MK2', 'VAMP Mk II', 100, ['STR_VAMP'], 'The VAMP rebuilt for heavier work: an armoured roof over the crew and a rocket pod in place of the machine gun. It hits armour the twin guns only scratch.'),   # John 13 Nov 18:09: missile upgrade of the base VAMP
 ('STR_TWIN_BATTLE_GUN', 'Twin Battle Gun', 80, ['STR_FLAK'], 'A twin anti-aircraft gun.'),
 ('STR_ANTI_AIRCRAFT_GUN', 'Anti-Aircraft Gun', 80, ['STR_FLAK'], 'A heavy anti-aircraft gun emplacement.'),
 ('STR_SNOW_CAT', 'Snow Cat', 150, ['STR_POLAR_BATTLE_BEAR'], 'A big arctic half-track with missiles. Frostbite comes with it.'),
 ('STR_DEVILFISH', 'Devilfish', 100, ['STR_MANTA'], 'A fast attack boat.'),
 ('STR_SONAR_SUITE', 'Sonar Suite', 120, ['STR_SHARC'], 'Sonar that finds submarines and divers.'),
 ('STR_STOP_AND_SEARCH', 'Stop and Search Teams', 60, ['STR_MANTA'], 'Boarding a ship without a fight, and without sinking an innocent merchant.'),
 ('STR_AVALANCHE_MISSILE', 'Avalanche Missile', 120, ['STR_SKYSTRIKER'], 'A heavy air-to-air missile, good against bombers.'),
 ('STR_TOMAHAWK', 'Tomahawk', 250, ['STR_C130_HERCULES'], 'A twin-rotor helicopter transport: hot landing zones, not just airfields.'),
 ('STR_MUDFIGHTER', 'Mudfighter', 150, ['STR_SKYSTRIKER'], 'A strike plane for close air support.'),
 ('STR_SKYSTRIKER_MK2', 'Skystriker Mk II', 200, ['STR_SKYSTRIKER', 'STR_RATTLER_WRECKAGE'], 'Better radar and a tighter turn, from what the Rattler wreck taught us.'),
 ('STR_AIR_COMBAT_DOCTRINE', 'Air Combat Doctrine', 150, ['STR_VIPER_PILOT'], 'How Cobra\'s pilots are taught to fly, and how to beat them. Every Joe aircraft is more accurate.'),
 ('STR_DETENTION_BLOCK', 'Detention Block', 120, ['STR_COBRA_TROOPER'], 'Cells for Cobra prisoners, with room to grow. The trail runs through the men we take alive.'),
 ('STR_SIGNALS_INTELLIGENCE_CENTER', 'Signals Intelligence Center', 250, ['STR_COBRA_FLIGHT_ROUTES'], 'A listening post in The Pit. Cobra\'s radio traffic becomes leads.'),
 ('STR_LONG_RANGE_RADAR', 'Long-Range Radar', 200, ['STR_RADAR_ROOM'], 'A radar with a far longer reach.'),
 # squad tactics (John 23:16-23:19): researched only in a base with a Briefing Room (base function STR_BRIEFING_ROOM)
 ('STR_OVERWATCH_DRILLS', 'Overwatch Drills', 80, None, 'Hawk drills the squads on holding ground. A Joe who ends his turn without moving gets +15% reaction-fire accuracy and reacts a little sooner.'),
 ('STR_BREACHING_DRILLS', 'Breaching Drills', 100, ['STR_OVERWATCH_DRILLS'], 'Door drills. Opening doors and containers costs half the time units, and the first Joe through a door gets +20% accuracy that turn.'),
 ('STR_FIRE_AND_MOVE', 'Fire and Move', 120, ['STR_OVERWATCH_DRILLS'], 'One Joe shoots, another moves. A Cobra a Joe fires at is pinned: no reaction fire until his next turn. Smoke grenades cost half the time units to throw, and Joes moving inside smoke cannot be reaction-fired.'),
 # transport defences (John 13 Nov 14:11): open the first time a Joe transport is attacked in the air.
 # Outpost cap (John 13 Nov 21:13: "1, but some research aspect for more"): 1 outdoor outpost to start, +1 per step, 4 at most.
 ('STR_FORWARD_OPERATIONS_1', 'Forward Operations I', 60, ['STR_FIELD_RADIO'], 'Supplying and commanding a second base far from The Pit. Lets G.I. Joe run two outdoor outposts.'),
 ('STR_FORWARD_OPERATIONS_2', 'Forward Operations II', 100, ['STR_FORWARD_OPERATIONS_1', 'STR_WATCH_TOWER'], 'Regional command: outposts that watch for each other. Lets G.I. Joe run three outdoor outposts.'),
 ('STR_FORWARD_OPERATIONS_3', 'Forward Operations III', 150, ['STR_FORWARD_OPERATIONS_2', 'STR_COBRA_DEPOTS'], 'A standing network of forward bases, placed where Cobra moves its goods. Lets G.I. Joe run four outdoor outposts.'),
 # STR_VAMP_RECOVERED is never researched by hand: BUILD's hook grants it when the junkyard mission is won, or one month after Clutch is rescued if it is lost (STORY_ClutchRescue_v1, John 17:10: no VAMP research before Clutch).
 ('STR_VAMP_RECOVERED', 'Clutch\'s VAMP', 1, ['STR_STORY_LOCK'], 'Clutch knows the VAMP bolt by bolt. With him in the Motor Pool we can build our own.'),
 # STR_TRANSPORT_UNDER_FIRE is never researched by hand: BUILD's hook grants it on the first transport interception.
 ('STR_TRANSPORT_UNDER_FIRE', 'Transport Under Fire', 1, ['STR_STORY_LOCK'], 'Cobra has started hunting our transports in the air. Our helicopters and the Hercules fly unarmed, and every squad aboard is a target. The Air Wing has three answers on the drawing board.'),
 ('STR_TRANSPORT_DOOR_GUNS', 'Transport Door Guns', 60, ['STR_TRANSPORT_UNDER_FIRE'], 'A heavy machine gun on a swing mount in every transport door. It fires in any direction and answers anything that comes close.'),
 ('STR_TRANSPORT_ARMOR_PLATING', 'Transport Armor Plating', 80, ['STR_TRANSPORT_UNDER_FIRE'], 'Bolt-on armour over the cockpit, the engines and the troop bay. Every transport takes more punishment before it goes down.'),
 ('STR_TRANSPORT_COUNTERMEASURE_PODS', 'Countermeasure Pods', 60, ['STR_TRANSPORT_UNDER_FIRE'], 'Flare dispensers under every transport, and drills for the pilots on breaking a missile lock.')]:
    t(i, n, c, 15, deps, txt)

# research money (John 21:28: "some are money and/or resources like cobra parts"). Dollars, charged when the project
# starts. OXCE has no such field: costFunds is the name proposed to BUILD for the fork. Intel, interrogations, clues
# and captured gear cost no money: they use up the item or prisoner instead.
FUNDS = {
 'STR_KEVLAR_VEST': 150000, 'STR_AP_ROUNDS': 100000, 'STR_FIELD_RADIO': 100000, 'STR_NIGHT_VISION': 150000,
 'STR_VAMP': 300000, 'STR_SKYSTRIKER': 1500000, 'STR_RADAR_ROOM': 400000, 'STR_C130_HERCULES': 1200000,
 'STR_MATCH_GRADE_OPTICS': 80000, 'STR_C4_DEMOLITIONS': 100000, 'STR_CLAYMORE_MINES': 100000, 'STR_MOBAT': 800000,
 'STR_RAM': 150000, 'STR_HAL': 500000, 'STR_FLAK': 300000, 'STR_WOLVERINE': 700000, 'STR_SLUGGER': 800000,
 'STR_POLAR_BATTLE_BEAR': 400000, 'STR_MMS': 400000, 'STR_MOUNTAIN_HOWITZER': 300000, 'STR_DRAGONFLY': 900000,
 'STR_FALCON_GLIDER': 150000, 'STR_SKY_HAWK': 600000, 'STR_SHARC': 900000, 'STR_MANTA': 200000, 'STR_KILLER_WHALE': 1200000,
 'STR_JUMP_JET_PACK': 250000, 'STR_PAC_RATS': 150000, 'STR_BATTLE_STATIONS': 300000, 'STR_WATCH_TOWER': 100000,
 'STR_BIVOUAC': 100000, 'STR_SQUAD_AUTOMATIC_WEAPON': 200000, 'STR_INCENDIARY_ROUNDS': 150000, 'STR_CONCUSSION_GRENADE': 100000,
 'STR_THERMITE': 150000, 'STR_LASER_GUIDED_ROCKETS': 250000, 'STR_JOE_COBRA_GRENADE': 100000, 'STR_GHILLIE_SUIT': 80000,
 'STR_ARCTIC_GEAR': 120000, 'STR_NINJA_GEAR': 200000, 'STR_COMBAT_STIMS': 100000, 'STR_TRAUMA_KIT': 150000,
 'STR_INFIRMARY': 400000, 'STR_VAMP_MK2': 250000, 'STR_TWIN_BATTLE_GUN': 200000, 'STR_ANTI_AIRCRAFT_GUN': 250000,
 'STR_SNOW_CAT': 500000, 'STR_DEVILFISH': 400000, 'STR_SONAR_SUITE': 300000, 'STR_STOP_AND_SEARCH': 100000,
 'STR_AVALANCHE_MISSILE': 300000, 'STR_TOMAHAWK': 1000000, 'STR_MUDFIGHTER': 800000, 'STR_SKYSTRIKER_MK2': 500000,
 'STR_AIR_COMBAT_DOCTRINE': 100000, 'STR_DETENTION_BLOCK': 300000, 'STR_SIGNALS_INTELLIGENCE_CENTER': 700000,
 'STR_LONG_RANGE_RADAR': 600000}
FUNDS = {k: int(round(v * 0.75, -4)) for k, v in FUNDS.items()}   # John 21:38: research money cut by 25%
FUNDS.update({'STR_FORWARD_OPERATIONS_1': 100000, 'STR_FORWARD_OPERATIONS_2': 200000, 'STR_FORWARD_OPERATIONS_3': 300000})   # after the cut (John 13 Nov 21:13)
FUNDS.update({'STR_OVERWATCH_DRILLS': 60000, 'STR_BREACHING_DRILLS': 80000, 'STR_FIRE_AND_MOVE': 90000})   # pitched after the cut (John 23:16-23:19)
FUNDS.update({'STR_TRANSPORT_DOOR_GUNS': 60000, 'STR_TRANSPORT_ARMOR_PLATING': 90000, 'STR_TRANSPORT_COUNTERMEASURE_PODS': 70000})   # John 13 Nov 14:11 (dogfight design 3b)
BASEFUNC = {'STR_OVERWATCH_DRILLS': ['STR_BRIEFING_ROOM'], 'STR_BREACHING_DRILLS': ['STR_BRIEFING_ROOM'], 'STR_FIRE_AND_MOVE': ['STR_BRIEFING_ROOM']}
R = [{'name': i, 'cost': c, 'points': p, **({'costFunds': FUNDS[i]} if i in FUNDS else {}), **({'dependencies': d} if d else {}), **({'requiresBaseFunc': BASEFUNC[i]} if i in BASEFUNC else {}), 'unlocks': []} for i, n, c, p, d, _ in T]
missing=[i for i,*_ in T if i not in FUNDS and not i.startswith('STR_STANDARD') and i not in ('STR_FIELD_MEDICINE','STR_BREACHING_SHOTGUN','STR_TRANSPORT_UNDER_FIRE','STR_VAMP_RECOVERED')]
assert not missing, missing
ART = [{'id': i, 'type_id': 8, 'section': SECTION, 'requires': [i], 'text': i + '_UFOPEDIA'} for i, *_ in T]
S = {'STR_JOE_RESEARCH_FILES': 'G.I. JOE RESEARCH'}
for i, n, c, p, d, txt in T: S[i] = n; S[i + '_UFOPEDIA'] = txt
hdr = ('# STORY (Year 1 research + story), batch 3: G.I. Joe research for Year 1.\n'
       '# Day 1 open list = John\'s short list (12 Nov 21:10). Nothing opens by date (John 21:20): every other topic follows\n'
       '# from research; the months in the design are estimates of research time and cost. Done-at-start topics are\n'
       '# for BUILD\'s starting research. The items, crafts, facilities and manufacture these open are BUILD\'s rules.\n'
       '# costFunds = research money in dollars (John 21:28). Not an OXCE field: BUILD to read it in the fork.\n')
data = {'research': R, 'ufopaedia': ART, 'extraStrings': [{'type': 'en-US', 'strings': S}, {'type': 'en-GB', 'strings': S}]}
open(os.path.join(OUT, 'gijoe_research_joe.rul'), 'w').write(hdr + yaml.dump(data, sort_keys=False, width=200, allow_unicode=True))
print('topics', len(R))
