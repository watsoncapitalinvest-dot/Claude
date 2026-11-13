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
    "HAWK: The ranch paid off. The cartel's guns came out of a machine works on a rail spur in West Texas. It went bust two years ago and the sign is still up. A dead factory doesn't ship rifles. Somebody's been using it.",
    "Our information says it's empty. Treat that as a guess. Search everything: the offices, the lockers, the boxcar, the furnace. I want to know who owned it, what they made, and whether they're coming back.",
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
