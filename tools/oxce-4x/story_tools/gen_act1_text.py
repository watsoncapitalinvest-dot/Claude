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
}
S.update(CUT)

hdr = ('# STORY (Act 1 writing). Hawk\'s briefings, Cobra Commander\'s broadcast and the Act 1 cutscene captions.\n'
       '# Text only. BUILD wires the ids (see story_tools/gen_act1_text.py). Generated: edit the script, not this file.\n')
body = yaml.dump({'extraStrings': [{'type': 'en-US', 'strings': S}, {'type': 'en-GB', 'strings': S}]},
                 sort_keys=False, width=200, allow_unicode=True)
open(os.path.join(OUT, 'gijoe_story_act1_text.rul'), 'w').write(hdr + body)
print('act1 text:', len(S), 'strings')
