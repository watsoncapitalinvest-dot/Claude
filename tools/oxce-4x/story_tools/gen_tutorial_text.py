"""STORY: tutorial text (claude/TUTORIAL_v1.md, John 18 Nov 19:05-19:12).
Duke's training run at the proving ground (two parts, each skippable) and the one-time campaign tips.
Writes mod/Ruleset/gijoe_story_tutorial_text.rul (extraStrings only, en-US + en-GB). Usage: python3 gen_tutorial_text.py <dir>
"""
import os, sys, yaml

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'mod', 'Ruleset')
N = '{NEWLINE}'
P = N + N
S = {}

# ------------------------------------------------------------------ the offer at New Game
S['STR_TUT_OFFER_TITLE'] = 'BASIC TRAINING'
S['STR_TUT_OFFER'] = P.join([
    "DUKE: Before Hawk sends you anywhere real, I'd like an hour of your time. Two parts: the course, where you learn to move without getting seen, and the office, where you learn what we do with what you bring home.",
    "Take both, take one, or skip it. Your call. I just don't want to meet you for the first time over a stretcher.",
])
S['STR_TUT_BOTH'] = 'Both parts'
S['STR_TUT_COURSE_ONLY'] = 'The course only'
S['STR_TUT_OFFICE_ONLY'] = 'The office only'
S['STR_TUT_SKIP'] = 'Skip training'

# ------------------------------------------------------------------ part 1: the course (battle), one line per step
C = [
    ('LANDING', "DUKE: First choice of the day: where you come in. Green is where the bird fits. Red is what we know is watching. Pick a spot the red can't see."),
    ('MOVE', "DUKE: Move to the wall. Crouch behind it. A crouched man in cover is half as easy to see and twice as hard to hit."),
    ('CONES', "DUKE: That blue wedge is what the guard sees. Blue with the snake cut out, he's got no idea you're here. The darker blue close to him: crouching won't save you in there."),
    ('SUSPICIOUS', "DUKE: Amber. He saw something he didn't like and he's coming to look. He hasn't called anyone. Be somewhere else when he gets there."),
    ('ALERT', "DUKE: Red means he's sure. Now he shouts, and anyone close turns around. Get out of his sight, and he'll walk to where he last saw you."),
    ('RETURN', "DUKE: Nothing there, so he goes back to his post, and once he's there he settles down. Patience is a weapon."),
    ('TAKEDOWN', "DUKE: Behind him, outside the wedge. Knife or dart. Do it right and nobody hears a thing. Get it wrong and the whole course hears him."),
    ('CONCEAL', "DUKE: A body anyone can see is an alarm waiting to happen. Hide it. It costs you time, so do it where nobody's looking."),
    ('DISTRACT', "DUKE: Throw a rock where you want him to look. He'll go and check. You go the other way."),
    ('DOOR', "DUKE: Locked door. Pick it, and nobody's the wiser. Shoot the lock, and everyone in earshot is the wiser. Your call, every door, every time."),
    ('KEYPAD', "DUKE: Keypad. The clues are on the card. Work it out and you walk in quiet. Can't be bothered, blow the door, and see how quiet that is."),
    ('DONE', "DUKE: That's the course. Out there it's the same rules, real bullets. Remember: getting caught isn't the end. It's just the start of a louder day."),
]
for k, v in C:
    S['STR_TUT_COURSE_' + k] = v

# ------------------------------------------------------------------ part 2: the office (base)
O = [
    ('DEBRIEF', "DUKE: Everything you carried home is on this list: the prisoner, his gun, his pack, his papers. Tick what goes to Intel. Each one becomes a case, and each case needs an analyst."),
    ('CHOOSE', "DUKE: Don't send everything. Analysts are few and most things lead nowhere. A talking officer pays off far more often than a rifle. Send too little, though, and you might bin the one thing that mattered."),
    ('CASE', "DUKE: This is a case. Every blank line is something we don't know yet, and next to it, the ways to find out. Field work means somebody goes out. Desk work means an analyst sits on it."),
    ('ANALYST', "DUKE: Put an analyst on it. In a few days he'll have something, or he'll tell you it's a dead end. When it's dead, close it and free his desk."),
    ('STALE', "DUKE: See the date on each line? That's when we last checked. Old isn't wrong, but it might be. Cobra moves things when it's nervous."),
    ('OPERATION', "DUKE: Last thing. The operations board. Pick one, pick who goes, and they're gone for days. It might pay, it might come back empty, and once in a while somebody gets caught. Choose like you mean it."),
    ('DONE', "DUKE: That's the job. Hawk's waiting. Good luck, and bring them all home."),
]
for k, v in O:
    S['STR_TUT_OFFICE_' + k] = v

# ------------------------------------------------------------------ one-time tips in the campaign (first time each appears)
T = {
    # battle
    'ALARM_BOX': "That box on the wall raises the alarm. So does the man with the radio. Put both out of action and this site can't call for help.",
    'GUARD_AMBER': "That guard is suspicious: he saw something and is coming to look. He hasn't told anyone yet.",
    'GUARD_RED': "That guard is alerted. He'll shout to anyone near him and hunt for you. Break his line of sight and he goes to where he last saw you.",
    'ALARM_UP': "The alarm is up. Everyone here is awake and looking. Expect reinforcements, and expect them to carry off whatever they can.",
    'ALARM_SPREAD': "This compound's alarm will reach the next one in a few turns. Wreck its radio mast or drop its radio man to stop it.",
    'SHIFT_CHANGE': "Shift change: sentries head off duty and fresh ones take the posts. Patrol routes have changed. A gap may have opened, or closed.",
    'LOCKED_DOOR': "Locked. Pick it quietly, open it with a key or a code if you have one, or break it down and let everyone hear.",
    'HOSTAGE': "Hostages. Get them out alive. Anything that blows up near them can hurt them too.",
    'CLUE_CONTAINER': "Search it. Papers, keys and codes turn up in desks, lockers and safes. Explosions burn paper.",
    'NEW_FACE': "A face we don't know. Whatever happens here goes into his file.",
    'VILLAIN_DRAGGED': "They're dragging him toward their exit. Stand over him, or stop them reaching it, and he's ours.",
    'RAPPEL': "No room to land, so they're going down the ropes, two a turn. To leave, call the helicopter to somewhere it can land, or climb back up slowly.",
    'APC_SIDE': "Pick the side the A.P.C. comes in from. If anyone sees it on the way, it stops right there and they get the first shots.",
    'SEALED_ROOM': "Walls and closed doors all the way round: nothing in here is heard outside. Open a door and that changes.",
    # world map and base
    'INFORMANT': "An informant sends tips about Cobra nearby. Cobra can find him and burn him.",
    'OLD_INTEL': "This line is old. It may still be true. Check it again, or act on it and take your chances.",
    'LOOSE_THREAD': "This doesn't belong in the case it turned up in. Drag it to the case you think it fits, or give it to an analyst to work out.",
    'DEAD_END': "Nothing. Most leads go nowhere. Close the case and put the analyst on something else.",
    'STAKEOUT_CHOICE': "Something's coming through. Write it down, follow it to see where it goes, or stop it on the road and see what it's carrying.",
    'WHO_KNEW': "Cobra hit something only a few people knew about. Somebody talked, or something was listening. Intel has opened a case: who knew?",
    'CARTEL_BOAT': "Searching a ship that turns out to be honest costs goodwill. A cartel boat may carry contraband, cash or men who'd rather fight.",
    'PROVING_BOOKING': "Joes on the course are away for three days and tired after. They come back better, by how well the exercise went.",
    'READINESS': "Cobra in this region is on guard after the noise we made. Its next site here will have more guards and fewer sleeping.",
    'COBRA_FILE': "We've learned something Cobra knows about us. It's in their file on us, and it can be used: move what they've found, or feed them a lie.",
    'PAPERS_PUZZLE': "Work it yourself and it's done now, and you may find more than the analysts would. Or hand it to them and wait.",
}
for k, v in T.items():
    S['STR_TIP_' + k] = v
S['STR_SKIP_TIPS'] = 'Turn off tips'

hdr = '# STORY: tutorial text (gen_tutorial_text.py). Generated: edit the script, not this file.\n'
body = yaml.dump({'extraStrings': [{'type': 'en-US', 'strings': S}, {'type': 'en-GB', 'strings': S}]},
                 allow_unicode=True, width=120, sort_keys=False)
open(os.path.join(OUT, 'gijoe_story_tutorial_text.rul'), 'w').write(hdr + body)
print('tutorial text:', len(S), 'strings')
