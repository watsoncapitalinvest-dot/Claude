"""Act 1 writing (STORY, John 12 Nov 22:23 "ok"): Hawk's briefings, Cobra Commander's broadcast, and the captions for
the three Act 1 cutscenes. Writes gijoe_story_act1_text.rul (extraStrings only, en-US + en-GB).
BUILD wires the ids: briefings into the missions' `briefing: desc`, the broadcast into a Geoscape event, the captions
into `cutscenes:` slideshows. The slide pictures are ART's (BRIEF_FOR_GRAPHICS_AI_Act1Cutscenes.txt).
Every beat has a version for each outcome (tools/oxce-4x/CLAUDE.md)."""
import yaml, sys, os
OUT = sys.argv[1]
N = '{NEWLINE}'
P = N + N

S = {}
# ------------------------------------------------------------------ Hawk's briefings
S['STR_BRIEFING_CARTEL_RANCH_TITLE'] = 'OPERATION: BORDER RANCH'
S['STR_BRIEFING_CARTEL_RANCH'] = P.join([
    "HAWK: Listen up. For a year every agency in Washington has traded rumours about a new outfit: well armed, well paid, never there when anyone looks. No name. No photograph. So we start where the guns are.",
    "A cartel runs loads across the Rio Grande onto a ranch on the Texas side. Their gunmen are carrying hardware they have no business owning. I want to know who sold it to them.",
    "The boss keeps his books in a safe in the ranch house. Get that ledger, and don't blow the safe: paper burns. Search the barn. Whatever came in those crates came from somewhere.",
    "There's a tower on the north-east corner covering the airstrip. Nobody crosses open ground under that rifle. Take the boss alive if you can.",
    "Clean operation, people. There are civilians on that ranch.",
])
S['STR_BRIEFING_ABANDONED_FACTORY_TITLE'] = 'OPERATION: DEAD FACTORY'
S['STR_BRIEFING_ABANDONED_FACTORY'] = P.join([
    "HAWK: We pulled one thread for a month and it held all the way. The ranch, the flight, the stash house, the robbery, the bank. Every trail ends at a machine works on a rail spur in West Texas. It went bust two years ago and it's still being paid.",
    "Our information says it's empty. Treat that as a guess. Search everything: the offices, the lockers, the boxcar, the furnace. I want to know who owns it, what they made, and whether they're coming back.",
    "Watch your feet. People who walk away from a place like that sometimes leave a present behind. And put somebody on the water tower.",
    "Get what you find back to the A.P.C. and get out. We go in, we read their mail, we leave.",
])
S['STR_BRIEFING_COBRA_CELL_TITLE'] = 'OPERATION: FIRST CONTACT'
S['STR_BRIEFING_COBRA_CELL'] = P.join([
    "HAWK: Now we know what they call themselves. Breaker pulled Cobra Commander's broadcast apart. It bounced through three relays, and the first one was sloppy. It leads to one building with a Cobra cell in it.",
    "Don't get excited. This is not their headquarters. A cell is a few rooms, a radio, and people who take orders. That's what we want: the people.",
    "Every one of them knows a name we don't. Bring me a Cobra soldier alive and Scarlett will have him talking by the end of the week. Dead men file no reports.",
    "Expect them to be better armed than the cartel. Expect them to fight. Expect civilians close by. Move out.",
])


# ------------------------------------------------------------------ the cartel arc (John 13 Nov 02:31-02:38)
S['STR_LEAD_CARTEL_SUPPLIER_DESC'] = "Somebody is arming the border cartel. Follow the guns, the planes and the money back to whoever it is."
S['STR_EVENT_CARTEL_FLIGHT'] = 'CARTEL FLIGHT DEPARTING'
S['STR_EVENT_CARTEL_FLIGHT_DESCRIPTION'] = P.join([
    "The flight the cartel boss gave us is in the air: a twin-engine cargo plane, running north without lights.",
    "HAWK: Don't shoot it down. Follow it. Wherever it lands is where they keep their stock.",
])
S['STR_OP_SCARLETT_STASH_HOUSE'] = 'Operation: Quiet Courier'
S['STR_OP_SCARLETT_STASH_HOUSE_DESC'] = P.join([
    "Scarlett goes in alone, as a buyer, to the cartel's stash house. She'll bug a shipment or turn one of their couriers into our man. Either way we hear what they plan next.",
    "She'll be gone for days. Intel research slows while she's out, and if she's made, they'll hold her.",
])
S['STR_BRIEFING_ARMORED_CAR_TITLE'] = 'OPERATION: PAYROLL'
S['STR_BRIEFING_ARMORED_CAR'] = P.join([
    "HAWK: The cartel lost a fortune at the ranch and they want it back fast. Scarlett's courier gave us the job: an armored car on a payroll run, hit at a gas station on the highway.",
    "They'll come heavy and they'll come quick. The money goes into a van, and the van goes for the county line. If it gets off the map, the cash is gone.",
    "Local police will already be there, pinned down. Get them out alive. And I want the man running the crew in one piece. He knows where the money goes.",
])
S['STR_BRIEFING_CARTEL_SAFEHOUSE_TITLE'] = 'OPERATION: COLD TRAIL'
S['STR_BRIEFING_CARTEL_SAFEHOUSE'] = P.join([
    "HAWK: They got away with the payroll. They didn't get away clean. The van was dumped two counties over, and the trail ends at a farmhouse they're using as a safehouse.",
    "The money's probably moved on. The paperwork usually doesn't. Bring me anything with a number on it.",
])
S['STR_BRIEFING_STASH_HOUSE_RESCUE_TITLE'] = 'OPERATION: BUYER BEWARE'
S['STR_BRIEFING_STASH_HOUSE_RESCUE'] = P.join([
    "HAWK: Scarlett's cover is blown. The cartel are holding her at the stash house, and every day she's in there she's in more danger and we're more exposed.",
    "We go in now. Get her out first. Everything else is second.",
])

# ------------------------------------------------------------------ Clutch rescue + his VAMP (claude/STORY_ClutchRescue_v1.md, John 13 Nov 17:03-17:15)
# Backstory: an Army driver on a VAMP test run along the border; the cartel hijacked the prototype to strip it and kept him to make it run.
# Pointers to the chop shop: the boss interrogation (fast, appended to STR_CARTEL_BOSS_INTERROGATION_UFOPEDIA in gen_batch1.py)
# or Scarlett's informant (slower, STR_EVENT_CHOP_SHOP_INFORMANT). BUILD fires whichever comes first.
S['STR_EVENT_CHOP_SHOP_INFORMANT'] = 'INFORMANT: A PRISONER AT THE CHOP SHOP'
S['STR_EVENT_CHOP_SHOP_INFORMANT_DESCRIPTION'] = P.join([
    "SCARLETT: My courier delivered more than he meant to. The cartel runs a chop shop outside the border town, and there's a man in the back room who isn't a customer.",
    "Army driver. They took his vehicle on a test run and they've kept him alive to make it work. They're running out of patience with him.",
])
S['STR_BRIEFING_CHOP_SHOP_TITLE'] = 'OPERATION: SPARE PARTS'
S['STR_BRIEFING_CHOP_SHOP'] = P.join([
    "HAWK: Two months ago the Army lost a prototype on a test run near the border: a light attack vehicle, and the man driving it. Corporal Lance Steinberg. Everybody calls him Clutch.",
    "The cartel took both. The vehicle went for parts. Clutch they kept, because nobody else can make it run. He's in a back room at their chop shop.",
    "Get him out alive. Everything else in that yard is stolen, and most of it has a man with a pistol standing next to it. Don't shoot the gas cans.",
    "If he's half the driver his file says, I want him running our Motor Pool by the end of the month.",
])
S['STR_EVENT_CLUTCH_MOVED'] = 'CLUTCH MOVED'
S['STR_EVENT_CLUTCH_MOVED_DESCRIPTION'] = P.join([
    "We didn't get him out. By the time the yard was quiet, the back room was empty and the cartel's truck was gone.",
    "HAWK: They'll put him somewhere else and they'll be more careful. Keep listening. We get one more chance at this.",
])
S['STR_BRIEFING_CHOP_SHOP_2_TITLE'] = 'OPERATION: SECOND GEAR'
S['STR_BRIEFING_CHOP_SHOP_2'] = P.join([
    "HAWK: We found him again. The cartel moved Clutch to another of their garages, and this time they know we're coming.",
    "More guards, fewer chances. Get in, get him, get out. There won't be a third time.",
])
S['STR_EVENT_CLUTCH_ESCAPED'] = 'CLUTCH WALKS IN'
S['STR_EVENT_CLUTCH_ESCAPED_DESCRIPTION'] = P.join([
    "A filthy man in an Army jacket walks up to the gate of The Pit and asks for whoever's in charge.",
    "CLUTCH: \"Your rescue was lousy. Theirs was worse. I hot-wired the truck they were moving me in. Where's the coffee?\"",
])
S['STR_CLUTCH_ARRIVAL'] = 'CLUTCH JOINS G.I. JOE'
S['STR_CLUTCH_ARRIVAL_DESCRIPTION'] = P.join([
    "Corporal Lance \"Clutch\" Steinberg. Armor & Vehicles. He can head the Motor Pool.",
    "CLUTCH: \"Two months I'm fixing their junk with a gun in my ear. Now: they still got my VAMP. It's in a junkyard. I know which one. I want it back.\"",
])
S['STR_BRIEFING_JUNKYARD_TITLE'] = 'OPERATION: REPO'
S['STR_BRIEFING_JUNKYARD'] = P.join([
    "HAWK: Clutch says the cartel never finished stripping his VAMP. It's under a tarp in a shed at their junkyard, waiting for a buyer.",
    "Take it back. It runs, it's ours, and once Clutch has had it apart we can build more of them.",
    "Watch the stacks. There are men up on those wrecks with a clear view of the whole yard, and a crusher in the middle that will flatten anybody who stands next to it when it starts.",
    "CLUTCH: \"And nobody scratches the paint.\"",
])
S['STR_EVENT_VAMP_RECOVERED'] = 'VAMP RECOVERED'
S['STR_EVENT_VAMP_RECOVERED_DESCRIPTION'] = P.join([
    "The VAMP rolls into the Motor Pool on its own wheels, with Clutch at the wheel and one door missing.",
    "It's ours, and Clutch has started on the drawings. Research: VAMP.",
])
S['STR_EVENT_VAMP_LOST'] = 'VAMP GONE'
S['STR_EVENT_VAMP_LOST_DESCRIPTION'] = P.join([
    "The shed was empty by the time we reached it. The cartel sold the VAMP before we could take it back.",
    "CLUTCH: \"Fine. I'll draw you a new one from memory. Give me a month.\" Research: VAMP, in about a month.",
])

# ------------------------------------------------------------------ Beach Head's proving ground (BUILD_DESIGN_ANSWERS_13Nov_Evening A.4)
# Appears once the Training Room is built. Stun weapons only, no deaths. Fail = he comes back every week until you pass. Pass = Beach Head joins.
S['STR_EVENT_PROVING_GROUND'] = 'A VISITOR AT THE TRAINING ROOM'
S['STR_EVENT_PROVING_GROUND_DESCRIPTION'] = P.join([
    "A Ranger sergeant in a balaclava inspects your new Training Room, says nothing for a full minute, then hands Hawk a sealed order.",
    "HAWK: Beach Head. The Army sent him to tell me whether my people are any good. He's offered to show us. On his range.",
])
S['STR_BRIEFING_PROVING_GROUND_TITLE'] = 'OPERATION: PROVING GROUND'
S['STR_BRIEFING_PROVING_GROUND'] = P.join([
    "BEACH HEAD: Listen up, because I'm only saying this once. You think you're soldiers. I think you're tourists. Today we find out.",
    "My range. My men. Stun weapons only: nobody dies on my course, they just wish they had. Put my team on the ground, every last one, and you pass.",
    "Lose, and I'll be back next week. And the week after. Until you get it right.",
    "Move like you mean it.",
])
S['STR_EVENT_PROVING_GROUND_PASSED'] = 'BEACH HEAD JOINS G.I. JOE'
S['STR_EVENT_PROVING_GROUND_PASSED_DESCRIPTION'] = P.join([
    "Sergeant Wayne \"Beach Head\" Sneeden. Infantry, Ranger, drill instructor. He can head Training & Recruiting and train up to six Joes in the Training Room.",
    "BEACH HEAD: \"You're slow, you're sloppy and you talk too much. You'll do. I'm staying.\"",
])
S['STR_EVENT_PROVING_GROUND_FAILED'] = 'PROVING GROUND: FAILED'
S['STR_EVENT_PROVING_GROUND_FAILED_DESCRIPTION'] = P.join([
    "Your squad is carried off Beach Head's range one stunned body at a time.",
    "BEACH HEAD: \"Pathetic. Same time next week.\"",
])

# ------------------------------------------------------------------ Cobra's side of Act 1 (claude/COBRA_ACT1_TIMETABLE_v1.md, John 13 Nov 21:02-21:12)
# {JOE} = the hunted Joe's name, {BASE} = the base; BUILD substitutes them (or drops the sentence if it can't).
S['STR_EVENT_FACTORY_REACTIVATED'] = 'THE FACTORY IS RUNNING'
S['STR_EVENT_FACTORY_REACTIVATED_DESCRIPTION'] = P.join([
    "The date on the production schedule came and went. The machine works in West Texas is lit up, the rail spur is busy, and there are guards on the gate.",
    "HAWK: We knew when. We didn't get there. Cobra has a factory now, and the cartel's next shipment won't be pistols. We'll have to hit it the hard way.",
])
S['STR_EVENT_BLUDD_HIRED'] = 'A PRICE ON A JOE'
S['STR_EVENT_BLUDD_HIRED_DESCRIPTION'] = P.join([
    "SCARLETT: Word from three different informants, all the same week. Cobra has hired a mercenary. Australian, ex-Foreign Legion, writes bad poetry. Major Sebastian Bludd.",
    "His job is one of ours: {JOE}. Cobra has seen enough of {JOE} to want him gone. Bludd will wait for him to travel. Every flight is a risk until this is settled.",
])
S['STR_BRIEFING_BLUDD_AMBUSH_TITLE'] = 'AMBUSH'
S['STR_BRIEFING_BLUDD_AMBUSH'] = P.join([
    "HAWK: Bludd hit the aircraft carrying {JOE}. It's down, and his men are already moving on the wreck.",
    "Get everyone out of that wreck before they do. Bludd doesn't want the aircraft. He wants {JOE}.",
])
S['STR_BRIEFING_BLUDD_RAID_TITLE'] = 'BLUDD AT THE GATE'
S['STR_BRIEFING_BLUDD_RAID'] = P.join([
    "HAWK: {JOE} stayed home, so Bludd came to him. A small team is inside the wire at {BASE}.",
    "They're not here to hold ground. They're here for one man. Keep him alive and run them off.",
])
S['STR_EVENT_BLUDD_CALLING_CARD'] = 'BLUDD WAS HERE'
S['STR_EVENT_BLUDD_CALLING_CARD_DESCRIPTION'] = P.join([
    "Bludd got away. He left a card where we'd find it: a playing card, the ace of spades, with four lines of verse on the back promising to come back for {JOE}.",
    "HAWK: The poetry is terrible. The threat isn't. Research: Bludd's Calling Card.",
])
S['STR_EVENT_DROME_STRIKE'] = 'THE DROME STRIKES'
S['STR_EVENT_DROME_STRIKE_DESCRIPTION'] = P.join([
    "Radar has a wave of Firebats on it, and behind them Cobra transports, heading straight for {BASE}.",
    "HAWK: We didn't go to the Drome, so the Drome is coming to us. Everyone to battle stations. This is the one we've been building to.",
])
# The climax, 16 Nov (Game Logic doc, Act 1 missions tab, cards 30-34)
S['STR_BRIEFING_DROME_PLANS_TITLE'] = 'OPERATION: BLUEPRINT'
S['STR_BRIEFING_DROME_PLANS'] = P.join([
    "HAWK: Every prisoner we take says the same word now: Drome. Scarlett thinks it's a fortress, and that it's close.",
    "This site holds the plans. An officer carries them, and he will try to burn them the moment he knows we're there. Go in quiet. Take him before he gets the chance.",
    "If we get the plans, we know where it is and where its guns point. If we don't, we find it the hard way.",
])
S['STR_BRIEFING_DROME_ASSAULT_TITLE'] = 'OPERATION: DRAWBRIDGE'
S['STR_BRIEFING_DROME_ASSAULT'] = P.join([
    "HAWK: That's it. Cobra's Terror Drome. Firebats in the silo, anti-aircraft on every tower. Fly at it and we lose the aircraft.",
    "But it was built to stop planes, not people. We go in on the ground. Take the command centre and the rest of it is just concrete.",
    "Pick up their weapons when it's over. Somebody has been arming these people, and I want to know who.",
])
S['STR_BRIEFING_DROME_ASSAULT_UNFINISHED'] = P.join([
    "HAWK: Cobra's Terror Drome, half built. The towers have no guns on them yet and the silo is an open hole.",
    "This is the best chance we will ever get. Wreck the construction and it never opens. Leave it a month and we fight it finished.",
    "Watch the crews. They're workmen with rifles, and they know the scaffolding better than you do.",
])
S['STR_EVENT_COBRA_RETREATS'] = 'COBRA PULLS OUT'
S['STR_EVENT_COBRA_RETREATS_DESCRIPTION'] = P.join([
    "SCARLETT: The front companies are shut. The factory is rubble. Their radio traffic has gone quiet across the whole region.",
    "HAWK: They didn't lose a battle. They lost North America. Cobra doesn't quit, so they'll be somewhere else, rebuilding.",
    "Roadblock, that last crate we seized. Tell me what's stamped under the paint.",
])
S['STR_BRIEFING_DROME_STRIKE_TITLE'] = 'OPERATION: HOLD THE LINE'
S['STR_BRIEFING_DROME_STRIKE'] = P.join([
    "HAWK: Cobra's Terror Drome has sent everything it has at {BASE}. Troops, armour, aircraft overhead.",
    "Hold the base. Take prisoners if you can, pick up their weapons when it's over. I want to know who's been arming these people.",
])

# ------------------------------------------------------------------ Sgt. Slaughter saves the day (RECRUITING_BUILD_SPEC_v1 section 4, John 13 Nov 22:57)
# A mission that looks ordinary; 20 Cobra spring an ambush; two turns later Slaughter rolls in behind them in his Triple T.
S['STR_BRIEFING_ROUTINE_SIGHTING_TITLE'] = 'OPERATION: ROUTINE PATROL'
S['STR_BRIEFING_ROUTINE_SIGHTING'] = P.join([
    "HAWK: Local police report armed men in a Cobra-style van moving through the area. Probably a supply run. Probably nothing.",
    "Go and take a look. If it's Cobra, bring me a prisoner. If it isn't, be home for dinner.",
])
S['STR_EVENT_AMBUSH'] = 'AMBUSH!'
S['STR_EVENT_AMBUSH_DESCRIPTION'] = "It was a trap. Cobra troops are coming out of every building on one side of the street. Twenty of them, at least."
S['STR_EVENT_SLAUGHTER_ARRIVES'] = 'SOMETHING BIG IS COMING'
S['STR_EVENT_SLAUGHTER_ARRIVES_DESCRIPTION'] = P.join([
    "An engine roars behind the Cobra line. A small, ugly, very angry tank comes through a fence, and a man in a campaign hat is standing in the hatch.",
    "SGT. SLAUGHTER: \"Cobra! You picked the wrong street, the wrong day and the wrong sergeant! Joes, keep your heads down and watch how it's done!\"",
])
S['STR_EVENT_SLAUGHTER_JOINS'] = 'SGT. SLAUGHTER JOINS G.I. JOE'
S['STR_EVENT_SLAUGHTER_JOINS_DESCRIPTION'] = P.join([
    "Sergeant Slaughter. Drill instructor, Command. He can head Training & Recruiting, and his Triple T tank comes with him.",
    "SGT. SLAUGHTER: \"I've been watching your outfit, Hawk. Good people. Soft. I'm going to fix that. Where do I sign?\"",
])

# ------------------------------------------------------------------ If The Pit falls (claude/PIT_FALLS_DESIGN_v1.md, John 13 Nov 23:02-23:07)
S['STR_EVENT_PIT_ATTACK'] = 'THE PIT IS UNDER ATTACK'
S['STR_EVENT_PIT_ATTACK_DESCRIPTION'] = P.join([
    "Cobra has found us. Trucks and troops are at the fence, and they know exactly where the lift shed is.",
    "HAWK: Everyone who can carry a rifle, topside. We hold the yard and this ends here.",
])
S['STR_EVENT_PIT_BREACHED'] = 'COBRA IS IN THE PIT'
S['STR_EVENT_PIT_BREACHED_DESCRIPTION'] = "They took the yard. Cobra is coming down the lift. Fall back to the rooms and make them pay for every corridor."
S['STR_PIT_EVACUATE'] = 'EVACUATE'
S['STR_PIT_EVACUATE_DESCRIPTION'] = "Get everyone to the lift and the escape hatch. Whatever we leave behind, Cobra gets."
S['STR_PIT_SELF_DESTRUCT'] = 'SELF-DESTRUCT'
S['STR_PIT_SELF_DESTRUCT_DESCRIPTION'] = "Charges set. Five turns. Get out, or stay and hold them while it counts down. Anyone still inside when it blows will be taken."
S['STR_EVENT_PIT_DESTROYED'] = 'THE PIT IS GONE'
S['STR_EVENT_PIT_DESTROYED_DESCRIPTION'] = P.join([
    "The ground jumped and the lift shed folded into the hole. Cobra took nothing out of The Pit but its own dead.",
    "HAWK: We start again. We've done it before.",
])
S['STR_EVENT_PIT_HELD'] = 'COBRA HOLDS THE PIT'
S['STR_EVENT_PIT_HELD_DESCRIPTION'] = P.join([
    "We got out. Cobra has The Pit: our rooms, our labs, our files. Every week they're in there, they learn more about us.",
    "HAWK: We know exactly where it is. When we're ready, we take it back.",
])
S['STR_EVENT_NEW_HQ'] = 'NEW HEADQUARTERS'
S['STR_EVENT_NEW_HQ_DESCRIPTION'] = "Command moves to {BASE}. Washington is asking hard questions."
S['STR_BRIEFING_RETAKE_PIT_TITLE'] = 'OPERATION: HOMECOMING'
S['STR_BRIEFING_RETAKE_PIT'] = P.join([
    "HAWK: We built every room in that hole. We know every corridor, every blind corner and every vent better than the people sitting in it.",
    "Go home. Throw them out. Try not to break anything we'll need.",
])

# ------------------------------------------------------------------ The first air fight (claude/FIRST_AIR_FIGHT_v1.md, John 13 Nov 23:46)
S['STR_EVENT_FIRST_INTERCEPT'] = 'SMUGGLER OVER THE BORDER'
S['STR_EVENT_FIRST_INTERCEPT_DESCRIPTION'] = P.join([
    "Border radar has a twin-engine plane coming north low and without lights. Customs say guns, and nobody else is close enough to stop it.",
    "HAWK: Ace, it's yours. Force it down. I want the plane, the guns and the pilot.",
    "ACE: \"Finally. Somebody around here who needs a pilot.\"",
])
TIPS = {
 'STR_TIP_AIR_TURN': "Your Skystriker's gun only fires forward. Turn to put the target inside the bright arc in front of you before you shoot.",
 'STR_TIP_AIR_DECKS': "The fight has four decks, low to high. Climbing costs time units, diving gains them. A plane on another deck can't be hit by guns.",
 'STR_TIP_AIR_FIRE': "Fire when the target is in your arc and on your deck. The closer you are, the more of the burst hits.",
 'STR_TIP_AIR_MISSILES': "Missiles lock on from further away and hit hard, but you carry only two. Save them for something that shoots back.",
 'STR_TIP_AIR_EDGE': "A plane that reaches its edge of the map gets away. Get between it and its edge, or bring it down before it gets there.",
 'STR_TIP_SKIP': 'SKIP TIPS',
}
S.update(TIPS)

# ------------------------------------------------------------------ Cobra Commander's broadcast (Geoscape event)
S['STR_EVENT_COBRA_BROADCAST'] = 'COBRA SPEAKS'
S['STR_EVENT_COBRA_BROADCAST_DESCRIPTION'] = P.join([
    "Every television and radio station in the free world loses its signal for ninety seconds. When the picture returns, a man in a blue hood stands in front of a banner bearing a coiled snake.",
    "\"People of the world. You have been governed by the weak, defended by the timid, and lied to by both. That ends now. My name does not matter. My organisation does. We are COBRA.",
    "We are already in your cities, your factories and your banks. Governments that cooperate will find us generous. Governments that resist will learn what we are named for. This is your only warning. COBRA!\"",
    "Breaker has the recording. The signal was relayed, and every relay leaves a trace. Research: Trace the Broadcast.",
])

# ------------------------------------------------------------------ cutscene captions (ART paints the slides)
CUT = {
    # 1. Factory reactivation. A plays on the reactivation date if the plant has not been hit; B if the Joes hit it first.
    'STR_CUT_FACTORY_A1': "West Texas. The date on the schedule.",
    'STR_CUT_FACTORY_A2': "The dust sheets come off. The machines still work.",
    'STR_CUT_FACTORY_A3': "Under the floor, something else was never switched off.",
    'STR_CUT_FACTORY_A4': "By morning the first crates are on the rails. Cobra is in the arms business.",
    'STR_CUT_FACTORY_B1': "West Texas. The date on the schedule.",
    'STR_CUT_FACTORY_B2': "Cobra's trucks find the gates chained and the lines wrecked. They turn around. Somewhere, someone takes note of who did it.",
    # 2. Terror Drome reveal. A when the defense plans were stolen; B when the plans raid failed and the Joes find it the hard way.
    'STR_CUT_DROME_A1': "The plans were real.",
    'STR_CUT_DROME_B1': "No plans. Just a reconnaissance photograph, and a lot of anti-aircraft fire.",
    'STR_CUT_DROME_2': "Cobra's first Terror Drome.",
    'STR_CUT_DROME_3': "Its own air wing. Its own garrison. Its own region to command.",
    'STR_CUT_DROME_4': "Every depot, every cell, every crate of rifles was building toward this.",
    # 3. Act 1 close. A when the Drome falls; B when it holds. Both end on the same two slides.
    'STR_CUT_CLOSE_A1': "The first Terror Drome burns. Cobra Commander is not among the prisoners.",
    'STR_CUT_CLOSE_B1': "The first Terror Drome still stands. G.I. Joe will be back.",
    'STR_CUT_CLOSE_2': "Under the Cobra paint, a maker's mark: M.A.R.S.",
    'STR_CUT_CLOSE_3': "Somewhere far from Texas, someone is watching the footage.",
    'STR_CUT_CLOSE_4': "He has seen enough. He is interested.",
    # 16 Nov (John 10:01-11:44, the Game Logic doc): incentivize, never force. The Drome can be found half-built,
    # and Act 1 can end with Cobra's network broken (ending B). Same closing slides 2-4 after each.
    'STR_CUT_DROME_C1': "Not finished. Scaffolding, cranes and half a wall. Cobra is still building it.",
    'STR_CUT_CLOSE_U1': "The first Terror Drome never got its roof. What Cobra built, G.I. Joe tore down.",
    'STR_CUT_CLOSE_C1': "No Drome. No factory. No front companies. Cobra is gone from North America, for now.",
}
S.update(CUT)

# 4. Named Joes at base, injuries, air (John 14 Nov 11:05). NAMED_JOES_AT_BASE_v1, INJURIES_v1, UNDERWATER_MISSIONS_v1.
# {0}, {1}: values the game fills in. No "he/she": Scarlett and Lady Jaye read these too.
STATUS = {
    # battle strain (fatigue), named Joes only
    'STR_STRAIN': 'Battle strain',
    'STR_STRAIN_VALUE': 'Battle strain: {0}',
    'STR_FATIGUE_FRESH': 'Fresh',
    'STR_FATIGUE_TIRED': 'Tired',
    'STR_FATIGUE_WORN': 'Worn out',
    'STR_FATIGUE_FRESH_DESC': 'Rested and ready.',
    'STR_FATIGUE_TIRED_DESC': 'Too many missions too close together. Aim -10, bravery -10. Each full week at base takes off one point of strain.',
    'STR_FATIGUE_WORN_DESC': 'Running on empty. Aim -20, bravery -20, time units -10%. Needs time at base, not another mission.',
    'STR_SQUAD_WARN_TIRED': '{0} is TIRED: aim and bravery are down.',
    'STR_SQUAD_WARN_WORN': '{0} is WORN OUT: aim, bravery and speed are down. Send anyway?',
    # stand-down
    'STR_STAND_DOWN': 'Stand-down',
    'STR_STAND_DOWN_DAYS': 'Stand-down: {0} days',
    'STR_STAND_DOWN_DESC': 'Debrief and rest after a mission. Counts as away from the desk.',
    'STR_STAND_DOWN_NOTICE': '{0} is back from the field: debrief and rest. Back at the desk in {1} days.',
    'STR_STAND_DOWN_OVER': '{0} is back at the desk.',
    # department heads away
    'STR_HEAD_AWAY_WARN': '{0} heads {1}. While away, and for the stand-down after, {1} runs at 60%.',
    'STR_DEPT_SPEED_AWAY': '{0}: head away, running at 60%',
    'STR_HEAD_ONLY_PAUSED': 'Paused: needs {0} at base.',
    'STR_HEAD_ONLY_TAG': 'Head at base only',
    'STR_START_NEEDS_HEAD': "No head at base. {0} can't start new projects.",
    'STR_START_BY_COMMANDER': 'Have {0} start it? {1} loses the {2} bonus for 3 days.',
    'STR_COMMANDER_BONUS_LOST': '{0} is covering for {1}: {2} bonus back in {3} days.',
    # Shaken (named Joes, INJURIES_v1 section 1)
    'STR_SHAKEN': 'Shaken',
    'STR_SHAKEN_MISSIONS': 'Shaken: {0} missions',
    'STR_SHAKEN_DESC': 'That one was too close. Bravery -20 and quicker to panic. Each mission finished clears one.',
    # bleed-out and scars (unnamed Joes, INJURIES_v1 sections 2-3)
    'STR_BLEEDING_OUT': 'Bleeding out: {0} turns',
    'STR_BLEEDING_OUT_WARN': '{0} is down and bleeding out! A medkit next to them stops it.',
    'STR_STABILISED': '{0} is stable.',
    'STR_BLED_OUT': '{0} did not make it.',
    'STR_SCAR_LEGS': 'Bad leg: -{0} TU',
    'STR_SCAR_ARMS': 'Bad arm: -{0} accuracy',
    'STR_SCAR_HEAD': 'Head wound: -{0} reactions',
    'STR_SCAR_BODY': 'Chest wound: -{0} health',
    # air (UNDERWATER_MISSIONS_v1 section 3)
    'STR_AIR': 'Air',
    'STR_AIR_TURNS': 'Air: {0} turns',
    'STR_AIR_LOW': '{0} has 3 turns of air left.',
    'STR_AIR_OUT': '{0} is out of air! Get to the surface or the sub.',
    'STR_AIR_REFILLED': '{0} refilled at the sub.',
    'STR_DIVE_LIGHT_ON': 'Dive light: on',
    'STR_DIVE_LIGHT_OFF': 'Dive light: off',
}
S.update(STATUS)

# 5. Underwater enemies (John 14 Nov 18:08; UNDERWATER_MISSIONS_v1 section 5, BRIEF_FOR_ROSTER_Underwater).
# Names, Intel pages (the Enemy Troop Types format) and short voices. Hydro-Vipers come with their act.
N = '{NEWLINE}'
def troop(name, rank, spec, dossier, ability, quote):
    field = ['', 'IN THE FIELD', 'Squad ability: ' + ability] if ability else []
    return N.join([name.upper(), rank, 'Specialty: ' + spec, '', 'DOSSIER', dossier] + field + ['', '"%s"' % quote])
UW = {
    'STR_CARTEL_DIVER': 'Cartel Diver',
    'STR_ART_CARTEL_DIVER': 'Cartel Diver',
    'STR_ART_CARTEL_DIVER_TEXT': troop('Cartel Diver', 'Hired help - no rank', 'Salvage diving; Smuggling',
        'Commercial salvage men the cartel pays by the crate. They know the reefs and the harbour bottoms, '
        'and they know where the crates go down. They do not know who is really paying, and they are not paid enough to die for it.',
        'Cut and Run: if the fight turns against them, they drop what they carry and swim for the edge', 'Nobody said anything about soldiers.'),   # John 18:13: restored
    'STR_COBRA_EEL': 'Cobra Eel',
    'STR_ART_COBRA_EEL': 'Cobra Eel',
    'STR_ART_COBRA_EEL_TEXT': troop('Cobra Eel', 'Cobra trooper - E-3 or equivalent', 'Frogman; Underwater demolitions',
        "Cobra's frogmen. Trained in the dark and cold, they plant mines on hulls, tap cables on the sea floor and guard "
        "what Cobra hides underwater. They work in silence and in teams, and they never come up where you expect them.",
        'Limpet Run: one Eel in each team carries a limpet mine and goes for the nearest hull, door or charge point', 'Silence below.'),
    'STR_EEL_SQUAD_LEADER': 'Eel Squad Leader',
    'STR_ART_EEL_SQUAD_LEADER': 'Eel Squad Leader',
    'STR_ART_EEL_SQUAD_LEADER_TEXT': troop('Eel Squad Leader', 'Cobra officer - E-6 or equivalent', 'Frogman; Small-unit command',
        'The veteran who leads three to five Eels. He carries Cobra\'s underwater pistol and the team\'s orders, '
        'and while he is alive his Eels hold their ground. Take him and the rest scatter.',
        'Hand Signals: Eels within sight of him keep their nerve; if he goes down, they lose it', 'Hold. Wait. Now.'),
    'STR_LAMPREY': 'Lamprey',
    'STR_ART_LAMPREY': 'Lamprey',
    'STR_ART_LAMPREY_TEXT': troop('Lamprey', 'Cobra trooper - E-4 or equivalent', 'Hydrofoil crew; Underwater assault',
        "The crews of Cobra's Moray hydrofoils, as much at home in the water as on deck. "
        "They go over the side with underwater rifles when a hydrofoil cannot finish the job.",
        'Over the Side: a Lamprey can enter a fight from a Cobra boat at the map edge', 'Over the side. Finish it.'),
    # voices (deploy / hit / down)
    'STR_VOICE_CARTEL_DIVER_DEPLOY': "Keep it quiet. In and out.", 'STR_VOICE_CARTEL_DIVER_HIT': "I'm cut!", 'STR_VOICE_CARTEL_DIVER_DOWN': "Should've stayed on the boat...",
    'STR_VOICE_COBRA_EEL_DEPLOY': "Silence below.", 'STR_VOICE_COBRA_EEL_HIT': "Hit!", 'STR_VOICE_COBRA_EEL_DOWN': "Cobra...!",
    'STR_VOICE_EEL_SQUAD_LEADER_DEPLOY': "Hold. Wait. Now.", 'STR_VOICE_EEL_SQUAD_LEADER_HIT': "Keep moving!", 'STR_VOICE_EEL_SQUAD_LEADER_DOWN': "Eels... fall back...",
    'STR_VOICE_LAMPREY_DEPLOY': "Over the side!", 'STR_VOICE_LAMPREY_HIT': "Taking water!", 'STR_VOICE_LAMPREY_DOWN': "For... Cobra...",
}
S.update(UW)

# 7. General Flagg and the CIA (John 14 Nov 19:25; STORY_FlaggArc_v1). Event text for BUILD's triggers.
S.update({
 'STR_EVENT_FLAGG_ARRIVES_TITLE': 'A NEW COMMANDER',
 'STR_EVENT_FLAGG_ARRIVES': P.join([
   "HAWK: Washington has sent us a general. Brigadier General Lawrence Flagg takes command of G.I. Joe as of today. I still run the Pit. He runs me.",
   "He's a good soldier with a good record. He also brought a staff I've never heard of. Keep your eyes open.",
 ]),
 'STR_EVENT_FLAGG_TURNS_TITLE': 'GENERAL FLAGG',
 'STR_EVENT_FLAGG_TURNS': P.join([
   "FLAGG: I read it twice. Then I put the man from Langley on a plane, and every one of your people he borrowed is home tonight.",
   "I was sent here to hand you over. I'm staying to make sure nobody ever tries again. From today I speak for G.I. Joe in Washington, and the Pentagon hears it from me first. Colonel Hawk commands this team. I'll keep the politicians off his back.",
 ]),
 'STR_EVENT_FLAGG_TURNS_EFFECTS': 'General Flagg is G.I. Joe\'s high commander and Pentagon liaison: funding +10%, Pentagon directives pay 25% more and failed ones cost half the goodwill, public exposure grows more slowly, and the carrier U.S.S. Liberty and Admiral Keel-Haul join the team.',
 'STR_EVENT_CIA_TAKES_JOE_TITLE': 'TEMPORARY ASSIGNMENT',
 'STR_EVENT_CIA_TAKES_JOE': P.join([
   "HAWK: Orders came down this morning. {0} has been reassigned to \"a joint task force\" for an unspecified period. No unit, no location, no number to call.",
   "Nobody in my chain of command signed this, and it isn't the first time. Find out who did.",
 ]),
 'STR_EVENT_CIA_RETURNS_JOE_TITLE': 'BACK WITH US',
 'STR_EVENT_CIA_RETURNS_JOE': "HAWK: {0} is back with us. No report, no explanation, and orders not to discuss it. Give them a few days; wherever they were, it wasn't a holiday.",
 'STR_FLAGG_HIGH_COMMANDER': 'High Commander',
 'STR_CIA_ASSIGNMENT': 'CIA assignment',
})

# 6. Underwater missions: briefings and debriefs (John 14 Nov 18:15; UNDERWATER_MISSIONS_v1 section 8).
# STR_BRIEFING_<M>_TITLE / STR_BRIEFING_<M> as the land missions; STR_DEBRIEF_<M>_WIN / _LOSE for BUILD to show after.
UWM = {
 'REEF_DROP': ('REEF DROP',
   ["HAWK: The cartel's stopped flying everything in. Some of it goes off a boat at night, onto the reef, and their divers bring it up when the coast is clear.",
    "They're down there now. Get the crates, and bring me one of those divers breathing. Watch your air: the reef is a long way from the way up."],
   "The crates are ours, and so is what's in them. Somebody on that boat knew where to drop them. We'll find out who.",
   "The divers got the crates away. The cartel will move the drop. We'll be looking for a new reef."),
 'UNDER_THE_HULL': ('UNDER THE HULL',
   ["HAWK: There's a freighter in harbour carrying something it isn't declaring. Customs went over her twice and found nothing, because it isn't inside the ship. It's welded under the hull.",
    "The cartel has divers guarding it until she sails. Go under, take it off her, and find out where she's headed. It's dark down there. Keep together."],
   "Cut loose and recovered. The ship's papers say one port. What was under her says another. We're going to watch that ship.",
   "She sailed with it still on her. Whatever it was, it's someone else's problem now, and maybe ours again later."),
 'CABLE_TAP': ('CABLE TAP',
   ["HAWK: A telephone cable on the sea floor has been dropping calls. The phone company sent a diver. He didn't come back up.",
    "Cobra has frogmen down there, Eels, and they've clamped something onto the line. Clear them off and bring me that tap in one piece. Whatever they were listening to, I want to know."],
   "The tap is ours, and it was recording. Our people are going through what Cobra heard, and who they were listening for.",
   "The Eels got away with the tap. Assume Cobra heard everything on that line. We'll have to change how we talk."),
 'SEA_CACHE': ('SEA CACHE',
   ["HAWK: Cobra doesn't keep all its supplies on land. There's a cache on the bottom out here, crates under netting, a buoy line to bring them up when a boat comes by.",
    "Eels guard it. Destroy what you can't carry. Every crate down there is a crate their troops won't get."],
   "The cache is gone. Cobra's people in this region will be going short for a while.",
   "The Eels held the cache. Cobra keeps its supplies, and now they know we know where it is."),
 'SALVAGE_RACE': ('SALVAGE RACE',
   ["HAWK: It's on the bottom now, and whatever was aboard went down with it. Cobra knows where it went down too, and their divers are already on the way.",
    "Get in, find it, and get it out before they do. You won't have long down there, and neither will they."],
   "We got there first. What came up with you is on its way to the lab.",
   "Cobra's divers beat us to it. Whatever was down there belongs to them now."),
 'HULL_BREACH': ('HULL BREACH',
   ["HAWK: She's dead in the water, but her crew isn't, and they're waiting for us to come over the rail. So we won't.",
    "Divers under her hull with limpets. Blow a way in below the waterline, and you're inside before they know where you came from."],
   "We came in from below and took her. Her cargo, her logbook and her crew are ours.",
   "The breach didn't hold, and her crew drove us back into the water. She's still Cobra's."),
}
for k, (title, brief, win, lose) in UWM.items():
    S['STR_BRIEFING_%s_TITLE' % k] = title
    S['STR_BRIEFING_%s' % k] = P.join(brief)
    S['STR_DEBRIEF_%s_WIN' % k] = win
    S['STR_DEBRIEF_%s_LOSE' % k] = lose

# ------------------------------------------------------------------ 8. Replacing BUILD's placeholders (BUILD 13 Nov 21:50, 14 Nov 01:15; John 14 Nov 20:50)
# Same ids as gijoe_cartel_arc.rul / gijoe_proving_ground.rul. BUILD: delete your copies so only these load.
S['STR_EVENT_FACTORY_FOUND'] = 'THE MONEY ENDS IN WEST TEXAS'
S['STR_EVENT_FACTORY_FOUND_DESCRIPTION'] = P.join([
    "SCARLETT: The border bank paid out to a \"machine works\" account for eleven months. The account belongs to the Arbco Furniture plant in West Texas. Arbco closed a year ago.",
    "Somebody is still paying its power bill, and the rail spur behind it was cleared last month. Nobody clears a spur to a plant that makes nothing.",
    "HAWK: It's on the map. Let's go and see what furniture looks like these days."])
S['STR_EVENT_ROBBERY_MISSED'] = 'THE PAYROLL IS GONE'
S['STR_EVENT_ROBBERY_MISSED_DESCRIPTION'] = P.join([
    "HAWK: The armored car was hit on schedule and we weren't there. Two guards in the hospital, the payroll gone, and the evening news asking who's supposed to stop this.",
    "If Scarlett's informant is still talking, we'll hear where the crew went to ground. If not, that money has to go through a bank sooner or later, and we'll follow it the slow way."])
# ------------------------------------------------------------------ Act 1 campaign layer, pieces 1-5 (claude/BRIEF_FOR_BUILD_Act1Layer_Part1_Answers.txt, John 17 Nov)
# Placeholders BUILD substitutes: {REGION}, {TOWN}, {COUNTRY}, {TARGET} (one of the STR_CELL_TARGET_* lines), {HOURS}, {DAYS}.
# Alerts come in two forms: _SCANNER (the Police Scanner, short countdown) and _TIPOFF (informants or SIGINT, days ahead).
# 1. Before a site is found: a region-level line in Situation Analysis, never a town.
S['STR_COBRA_ACTIVITY_REPORTED'] = "Cobra activity reported: {REGION}. {BAND}"
S['STR_COBRA_ACTIVITY_FEW'] = "A few reports. Nothing confirmed."
S['STR_COBRA_ACTIVITY_SEVERAL'] = "Several reports, from more than one source."
S['STR_COBRA_ACTIVITY_MANY'] = "Many reports. Cobra is well established here."
# 2. Cell strikes. A small crew hits a small local target.
S['STR_CELL_TARGET_POLICE'] = "the police station"
S['STR_CELL_TARGET_GAS_STATION'] = "a gas station on the highway"
S['STR_CELL_TARGET_SHOPPING_STREET'] = "the shopping street"
S['STR_CELL_TARGET_BANK'] = "the town bank"
S['STR_CELL_TARGET_SUBSTATION'] = "the power substation"
S['STR_ALERT_CELL_STRIKE_SCANNER'] = "POLICE SCANNER: Shots fired at {TARGET}, {TOWN}. Officers pinned down. Armed men in blue. {HOURS} hours before they're gone."
S['STR_ALERT_CELL_STRIKE_TIPOFF'] = "TIP-OFF: A Cobra crew is planning to hit {TARGET} in {TOWN}. We have {DAYS} days to be waiting for them."
S['STR_BRIEFING_CELL_STRIKE_TITLE'] = 'OPERATION: LOCAL CALL'
S['STR_BRIEFING_CELL_STRIKE'] = P.join([
    "HAWK: A Cobra cell is hitting {TARGET} in {TOWN}. It's a small crew, and they want to be seen doing it. The point is to show a town that the police can't protect it.",
    "So we show it something else. The police are already there and outgunned: keep them alive. Every civilian you get out is one more person who saw G.I. Joe turn up.",
    "Take one of them alive. A crew this size works out of a house, not a fortress, and somebody in it knows the address."])
S['STR_EVENT_CELL_STRIKE_STOPPED'] = 'THE CREW IS IN CUSTODY'
S['STR_EVENT_CELL_STRIKE_STOPPED_DESCRIPTION'] = P.join([
    "SCARLETT: {TOWN} has its main street back. One of the crew is talking, mostly to say he doesn't know anything.",
    "He knows a phone number. It's in the file now. Every one of these crews answers to somebody."])
S['STR_EVENT_CELL_STRIKE_MISSED'] = 'COBRA WAS IN {TOWN}'
S['STR_EVENT_CELL_STRIKE_MISSED_DESCRIPTION'] = P.join([
    "HAWK: A Cobra crew hit {TARGET} in {TOWN} and left before anyone could stop it. Nobody in that town is asking the police for help this evening. They're asking who Cobra is.",
    "That's what the strike was for. They'll try it again somewhere nearby, because it worked."])
# 3. Crime that pays Cobra. A getaway pays; a stopped crime gives a lead.
S['STR_ALERT_BANK_ROBBERY_SCANNER'] = "POLICE SCANNER: Armed robbery in progress at a bank in {TOWN}. A van is waiting at the back. {HOURS} hours."
S['STR_ALERT_BANK_ROBBERY_TIPOFF'] = "TIP-OFF: A crew has been watching a bank in {TOWN}. They go in within {DAYS} days."
S['STR_ALERT_ARMORED_CAR_SCANNER'] = "POLICE SCANNER: An armored car has stopped answering its radio outside {TOWN}. {HOURS} hours."
S['STR_ALERT_ARMORED_CAR_TIPOFF'] = "TIP-OFF: Somebody bought the payroll route for an armored car out of {TOWN}. The hit is within {DAYS} days."
S['STR_ALERT_VAN_STOP_SCANNER'] = "POLICE SCANNER: A highway patrolman has pulled over a van at a gas station near {TOWN} and called for backup. Then he stopped answering. {HOURS} hours."
S['STR_ALERT_VAN_STOP_TIPOFF'] = "TIP-OFF: A van carrying Cobra cargo refuels near {TOWN} within {DAYS} days. It will be guarded."
S['STR_ALERT_CONVOY_SCANNER'] = "POLICE SCANNER: Trucks running without lights on the desert highway near {TOWN}, with an escort. {HOURS} hours to the state line."
S['STR_ALERT_CONVOY_TIPOFF'] = "TIP-OFF: A Cobra convoy runs the desert highway past {TOWN} within {DAYS} days."
S['STR_EVENT_CRIME_STOPPED'] = 'THE MONEY STAYED'
S['STR_EVENT_CRIME_STOPPED_DESCRIPTION'] = P.join([
    "HAWK: The van didn't leave. The cash goes back where it came from, and Cobra goes a month short.",
    "Scarlett is going through the crew's pockets. One lead is a start. Two will be an address."])
S['STR_EVENT_CRIME_LEADER_TALKS'] = 'THE LEADER TALKED'
S['STR_EVENT_CRIME_LEADER_TALKS_DESCRIPTION'] = P.join([
    "SCARLETT: The man who ran the job lasted an hour. He wasn't paid enough to last longer.",
    "He gave us the place the money was going. It's on the map."])
S['STR_EVENT_BANK_ROBBERY_MISSED'] = 'THE BANK IS EMPTY'
S['STR_EVENT_BANK_ROBBERY_MISSED_DESCRIPTION'] = P.join([
    "HAWK: The bank in {TOWN} was cleaned out and the van was gone before we got there. {COUNTRY} wants to know what it's paying us for.",
    "The van left a trail. It always does. Somewhere there's a safehouse with a lot of cash in it, and Scarlett is looking for it."])
S['STR_EVENT_VAN_STOP_MISSED'] = 'THE VAN GOT THROUGH'
S['STR_EVENT_VAN_STOP_MISSED_DESCRIPTION'] = P.join([
    "HAWK: The patrolman is alive. The van and whatever was in it are gone.",
    "Somebody saw which way it turned off the highway. It's not much, but it's a trail."])
S['STR_EVENT_CONVOY_MISSED'] = 'THE CONVOY CROSSED'
S['STR_EVENT_CONVOY_MISSED_DESCRIPTION'] = P.join([
    "HAWK: The trucks made it across the state line. Whatever Cobra was moving, it has it now.",
    "Trucks need fuel and drivers need sleep. Somebody along that road was paid to look the other way, and they'll remember the faces."])
# 5. The factory: the 7-day warning, once the Factory Production Schedule is researched.
S['STR_EVENT_FACTORY_WARNING'] = 'SEVEN DAYS'
S['STR_EVENT_FACTORY_WARNING_DESCRIPTION'] = P.join([
    "SCARLETT: The date on the production schedule is a week away. Fuel deliveries to the Arbco plant started on Monday, and the rail spur has a train booked.",
    "HAWK: If we're going to chain those gates, it's this week. After that we'll be raiding a working factory with guards on it."])
S['STR_PROVING_GROUND_BRIEFING'] = P.join([
    "HAWK: A Ranger called Beach Head heard we'd built a Training Room. He doesn't think much of it, or of us. He's set up a course outside the wire and brought his own cadre.",
    "Every round on that course is a stun round. Nobody gets hurt. Everybody gets embarrassed.",
    "Put down every man he's got, Beach Head included, and he'll come and train our people. Pull out, or get put down, and he'll be back next week to try again. He'll enjoy that."])
S['STR_PROVING_GROUND_UP'] = "Beach Head has set up a proving ground near {0}. Beat his cadre and he joins. Every hit only stuns."
S['STR_PROVING_GROUND_PASSED'] = "BEACH HEAD: You'll do. Barely. I start Monday, and your people won't like me. Beach Head has joined G.I. Joe at {0}."
S['STR_PROVING_GROUND_FAILED'] = "BEACH HEAD: That was sad. Same time next week. Bring people who can shoot."

# ------------------------------------------------------------------ 9. Springfield (claude/STORY_Springfield_v1.md, John 15 Nov 09:06-09:20). Act 2.
# Order: STR_CRIMSON_GUARD done -> WALK_IN (opens STR_SPRINGFIELD_STORY) -> range briefing -> RANGE_DEBRIEF (bunker files taken)
# or RANGE_NO_FILES (opens STR_RANGE_LAND_RECORDS) -> STR_ARBCO done -> assault briefing -> INQUIRY -> INQUIRY_OVER.
S['STR_EVENT_SPRINGFIELD_WALK_IN'] = 'SCARLETT HAS A WALK-IN'
S['STR_EVENT_SPRINGFIELD_WALK_IN_DESCRIPTION'] = P.join([
    "SCARLETT: A young man walked into an Army recruiting office yesterday and asked for whoever handles Cobra. The sergeant called me. His name is Danny Marsh.",
    "He says he grew up in a town called Springfield, where every adult works for Cobra and the Crimson Guard train in the open. He says he got out. He's frightened, and he's very sure.",
    "HAWK: We've been asking Cobra's people about the Crimson Guard for weeks, and now one of their neighbours walks in. Take a few days with him. Check every word."])
S['STR_BRIEFING_SPRINGFIELD_RANGE_TITLE'] = 'OPERATION: MAIN STREET'
S['STR_BRIEFING_SPRINGFIELD_RANGE'] = P.join([
    "HAWK: Danny Marsh says this is Springfield: a town in the hills where Cobra trains the Crimson Guard. Scarlett has checked his story and it holds.",
    "He says the training is run from a bunker at the end of Main Street. That's the target. Get inside and bring back whatever they keep in it.",
    "He also says there are families here. Check every target before you fire.",
    "If this is what he says it is, it's the biggest thing we've found since the Drome. If it isn't, I want to know that too. Move out."])
S['STR_EVENT_SPRINGFIELD_RANGE_DEBRIEF'] = 'NOBODY LIVES IN SPRINGFIELD'
S['STR_EVENT_SPRINGFIELD_RANGE_DEBRIEF_DESCRIPTION'] = P.join([
    "SCARLETT: There were no families. There were no people at all. That town is a firing range dressed as a town, and those were B.A.T.s, and they were waiting for us.",
    "Danny Marsh walked out of his safe house the morning we left. He was the Baroness's from the start, and I vouched for him. That's mine.",
    "HAWK: Then you'll want the bunker files. Read them."])
S['STR_EVENT_SPRINGFIELD_RANGE_NO_FILES'] = 'NOBODY LIVES IN SPRINGFIELD'
S['STR_EVENT_SPRINGFIELD_RANGE_NO_FILES_DESCRIPTION'] = P.join([
    "SCARLETT: There were no families. There were no people at all. That town is a firing range dressed as a town, and those were B.A.T.s, and they were waiting for us.",
    "Danny Marsh walked out of his safe house the morning we left. He was the Baroness's from the start, and I vouched for him. That's mine.",
    "We didn't get into the bunker. Somebody built that range and somebody pays for it, so I'll find them on paper. It'll take longer.",
    "HAWK: Then start."])
S['STR_BRIEFING_SPRINGFIELD_TITLE'] = 'OPERATION: HOMETOWN'
S['STR_BRIEFING_SPRINGFIELD'] = P.join([
    "HAWK: This is the real Springfield. Cobra built it, Cobra runs it, and Cobra trains the Crimson Guard under it. The mayor is Cobra. The police are Cobra. Nearly everyone in it is Cobra or married to it.",
    "Three objectives first: the airport, the police station, and the roads out of town. Then the museum on the square. That's their headquarters.",
    "They will run. Destro is running the evacuation, from the helicopter pad at the high school and a tunnel under the airport. We won't stop all of it. Every turn we hold them is another prisoner and another box of files, and I want both. Take Crimson Guard alive.",
    "Armed townsfolk are combatants. Unarmed ones are civilians, whoever they vote for. Check your fire."])
S['STR_EVENT_SPRINGFIELD_INQUIRY'] = 'THE PENTAGON INQUIRY'
S['STR_EVENT_SPRINGFIELD_INQUIRY_DESCRIPTION'] = P.join([
    "HAWK: We took a town, and the town got away. Cobra blew the tunnel, burned what it couldn't carry and flew out from the high school.",
    "Washington wants to know how an American town belonged to Cobra for twenty years, and how we let it leave. Until the inquiry is done, G.I. Joe launches nothing for {DAYS} days. The labs, the shops and the base keep working. The money will be short next month.",
    "What we brought out is thin. They'll use that against us."])
S['STR_EVENT_SPRINGFIELD_INQUIRY_STRONG'] = P.join([
    "HAWK: We took a town, and the town got away. Cobra blew the tunnel, burned what it couldn't carry and flew out from the high school.",
    "Washington wants to know how an American town belonged to Cobra for twenty years, and how we let it leave. Until the inquiry is done, G.I. Joe launches nothing for {DAYS} days. The labs, the shops and the base keep working.",
    "What we brought out is on the committee's table, and it's doing our talking for us."])
S['STR_EVENT_SPRINGFIELD_DANNY_TAKEN'] = "SCARLETT: Danny Marsh is in our cells. He was wearing a Crimson Guard uniform this time."
S['STR_EVENT_SPRINGFIELD_INQUIRY_OVER'] = 'CLEARED TO OPERATE'
S['STR_EVENT_SPRINGFIELD_INQUIRY_OVER_DESCRIPTION'] = P.join([
    "HAWK: The committee is done with us. We're cleared to operate. Nobody said thank you, and nobody's going to.",
    "Springfield is empty. Its people are somewhere else now, and they know our faces. Back to work."])

# ------------------------------------------------------------------ The HQ airfield arrives (claude/HQ_AIRFIELD_DESIGN_v1.md s.0, John 16 Nov 01:53-02:04)
# Fires when the abandoned factory mission is won (either version: before or after reactivation). Ceiling: day 120 if it never is.
S['STR_EVENT_HQ_ARRIVES'] = 'A HEADQUARTERS OF OUR OWN'
S['STR_EVENT_HQ_ARRIVES_DESCRIPTION'] = P.join([
    "HAWK: Washington saw the factory footage. Somebody over there finally believes in Cobra, and they've decided we're worth more than a hole under a motor pool.",
    "We've been given a Headquarters Command Center: a hardened compound with a runway, already garrisoned. It comes with a squad, two vehicles, an anti-aircraft gun, and Ace with his Skystriker. We have air cover.",
    "Cobra will find out we have it. Keep the guns manned."])
S['STR_EVENT_HQ_ARRIVES_LATE'] = 'A HEADQUARTERS OF OUR OWN'
S['STR_EVENT_HQ_ARRIVES_LATE_DESCRIPTION'] = P.join([
    "HAWK: We still haven't taken that factory, and Washington has stopped waiting for us to. Cobra flights are crossing our airspace and nobody's stopping them.",
    "We've been given a Headquarters Command Center: a hardened compound with a runway, already garrisoned. It comes with a squad, two vehicles, an anti-aircraft gun, and Ace with his Skystriker.",
    "It's a vote of confidence we haven't earned yet. Let's earn it."])

hdr = ('# STORY (Act 1 writing). Hawk\'s briefings, Cobra Commander\'s broadcast and the Act 1 cutscene captions.\n'
       '# Text only. BUILD wires the ids (see story_tools/gen_act1_text.py). Generated: edit the script, not this file.\n')
body = yaml.dump({'extraStrings': [{'type': 'en-US', 'strings': S}, {'type': 'en-GB', 'strings': S}]},
                 sort_keys=False, width=200, allow_unicode=True)
open(os.path.join(OUT, 'gijoe_story_act1_text.rul'), 'w').write(hdr + body)
print('act1 text:', len(S), 'strings')
