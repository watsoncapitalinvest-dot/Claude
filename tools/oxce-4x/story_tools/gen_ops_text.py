"""STORY: text for the Act 1 covert operations board (BUILD-1's BRIEF_FOR_STORY_GeoscapeProactive_18Nov, item 1;
John 18 Nov 18:31: the Intel app is the hub of the world map, and the board folds into it).
Writes mod/Ruleset/gijoe_story_ops_text.rul (extraStrings only, en-US + en-GB). Ids: STR_OP_<NAME>, _DESC, and
_SUCCESS / _EMPTY / _BLOWN for each. Usage: python3 gen_ops_text.py <mod/Ruleset dir>
"""
import os, sys, yaml

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'mod', 'Ruleset')
N = '{NEWLINE}'
P = N + N
S = {}

def op(key, name, desc, success, empty, blown):
    S[key] = name
    S[key + '_DESC'] = P.join(desc)
    S[key + '_SUCCESS'] = P.join(success)
    S[key + '_EMPTY'] = P.join(empty)
    S[key + '_BLOWN'] = P.join(blown)

# a. the cartel's banker (opens with the bank trace; cuts it short)
op('STR_OP_PAPER_TRAIL', 'Operation: Twenty Questions',
   ["Somebody at the border bank moves the cartel's money and smiles at the auditors. Scarlett takes a desk across the street and watches who he lunches with, who he calls, and where his deposits go.",
    "Four days. If he makes her, the money goes quiet and so does he."],
   ["SCARLETT: He keeps a second ledger in his car. I photographed every page while he was at lunch. The money goes north before it goes anywhere else."],
   ["SCARLETT: Four days of a man eating soup. Either he's careful or he's clean. I'd bet careful."],
   ["HAWK: The banker made Scarlett on day three. She got out. The cartel will move the money now, and they know we're looking."])
# b. the ranch survivors (opens after the ranch; a captured boss makes it surer)
op('STR_OP_LONG_NIGHT', 'Operation: My Brother\'s Keeper',
   ["The men who ran from the ranch are hiding with family along the river. Scarlett finds them one at a time and buys them a drink. Frightened men talk, if somebody gives them a reason.",
    "Three days. If we're holding their boss, they'll be more frightened and more talkative."],
   ["SCARLETT: One of them drove the trucks. He knows the road they used, and he knows the man who paid for the guns didn't speak Spanish."],
   ["SCARLETT: They've all developed the same bad memory. Somebody got to them first."],
   ["HAWK: The cartel was watching the families. Scarlett walked into a house full of the wrong cousins. Get her out."])
# c. the factory gate (opens with the factory lead; warns before it reopens)
op('STR_OP_NIGHT_SHIFT', 'Operation: Joe\'s Night Out',
   ["A machine works in West Texas went bust two years ago and still pays its electric bill. Scarlett sits on the road above the gate and counts who comes and goes.",
    "Five days. If she sees them getting it ready, we'll know when it starts, and we can be there first."],
   ["SCARLETT: New locks on the gate, a generator on a truck, and a man with a clipboard counting crates. They're opening it, and I can tell you the day."],
   ["SCARLETT: Five nights of tumbleweed. Either it's dead, or they're not ready yet."],
   ["HAWK: A patrol found Scarlett's hide. Whoever owns that factory knows somebody is interested in it."])
# d. an informant in a border town (from Day 1; money)
op('STR_OP_FRIENDLY_BARTENDER', 'Operation: The Spy Who Rooked Me',
   ["Every border town has a bar where the smugglers drink and a bartender who listens. Scarlett finds ours and makes him an offer: a monthly envelope for whatever he hears.",
    "Two days and some of our money. A good one hears about a run before it happens."],
   ["SCARLETT: He's ours. He'll call when a crew starts drinking like they've got a job tomorrow."],
   ["SCARLETT: He took the drink and not the money. He's more scared of them than he likes us."],
   ["HAWK: The bartender sold Scarlett to the people he serves. She got out the back. We're not welcome in that town for a while."])
# e. the broadcast's relay (after the broadcast)
op('STR_OP_DEAD_AIR', 'Operation: Cobra Soundwaves',
   ["Cobra Commander's message to Washington didn't come out of thin air. Somewhere there's a relay that carried it: a mast, a van, a rented room with a dish on the roof. Scarlett goes looking with Breaker's numbers.",
    "Four days. Find the relay and we're halfway to whoever used it."],
   ["SCARLETT: A rented room over a laundromat, a dish on the roof, and a phone bill paid in cash. The man who paid it uses the same name every time."],
   ["SCARLETT: Breaker's numbers put it in a county. A county is a lot of rooftops."],
   ["HAWK: Cobra was watching its relay. Scarlett walked into their camera. They know her face now."])

# Cartel smuggling boats on the Gulf and Caribbean lanes (BUILD-1 item 3; John 18:50, B: contraband and money only, no story link)
S['STR_CARTEL_BOAT'] = 'Fishing boat (unregistered)'
S['STR_CARTEL_BOAT_FOUND_CONTRABAND'] = "The hold is full of fish on top and bales underneath. The crew had a story and nobody believed it. The cargo is ours: sell it on, or keep the guns that came with it."
S['STR_CARTEL_BOAT_FOUND_CASH'] = "No drugs, no guns: a waterproof bag of cash in the engine room, and three men who suddenly can't speak English. The money goes to the war chest."
S['STR_CARTEL_BOAT_FIGHT'] = "The crew went for the guns under the nets when the boarding party came over the rail. Clear the deck."
S['STR_CARTEL_BOAT_CLEAN'] = "Fish, ice and a very angry captain. He'll be telling everyone in port about the Americans who wasted his morning."
hdr = '# STORY: covert operations board text (gen_ops_text.py). Generated: edit the script, not this file.\n'
body = yaml.dump({'extraStrings': [{'type': 'en-US', 'strings': S}, {'type': 'en-GB', 'strings': S}]},
                 allow_unicode=True, width=120, sort_keys=False)
open(os.path.join(OUT, 'gijoe_story_ops_text.rul'), 'w').write(hdr + body)
print('ops text:', len(S), 'strings')
