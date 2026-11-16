"""Villain arrival missions (STORY, 16 Nov 2026; John 16:36 "Do them all"). Design: claude/VILLAIN_ARRIVALS_v1.md (DRAFT).
The seven villains who arrive through a story mission (VILLAINS_DESIGN_v1, Q1): Storm Shadow, Zartan and the Dreadnoks,
Destro, the Baroness, Tomax and Xamot, Dr. Mindbender, Serpentor. Each: the Geoscape event that opens it, Hawk's briefing,
and one line per outcome. Every outcome has a version; named characters never die.
Writes gijoe_story_villains_text.rul (extraStrings only, en-US + en-GB). Text only: BUILD wires the ids."""
import yaml, sys, os
OUT = sys.argv[1]
N = '{NEWLINE}'
P = N + N
S = {}

# ------------------------------------------------------------------ 1. Storm Shadow (ALLY: the Arashikage pact; needs a training camp)
S['STR_EVENT_SS_WITNESS'] = 'A WITNESS WHO WANTS TO TALK'
S['STR_EVENT_SS_WITNESS_DESCRIPTION'] = P.join([
    "SCARLETT: A Cobra bookkeeper walked into a sheriff's office last night and asked for us by name. He says he moved the money that paid for a training camp, and he can tell us where.",
    "He also says Cobra has made a deal with someone he calls 'the clan'. He was very frightened of the clan."])
S['STR_BRIEFING_SS_ARRIVAL_TITLE'] = 'OPERATION: SILENT NIGHT'
S['STR_BRIEFING_SS_ARRIVAL'] = P.join([
    "HAWK: Our witness is in a motel off the interstate with two deputies and a lot of coffee. We move him at dawn. Until then he's ours to keep breathing.",
    "Cobra knows where he is. Whoever they send won't kick the door in. Expect one man, at night, and expect not to hear him.",
    "Keep the witness away from windows. Keep your people in pairs. If somebody goes quiet on the radio, assume the worst and go look.",
    "Hold until the transport arrives."])
S['STR_EVENT_SS_ARRIVAL_WON'] = P.join([
    "SCARLETT: The witness made it. He gave us the camp, and a name for the man who came for him: Storm Shadow. Ninja, Arashikage clan. Cobra's new friend.",
    "SNAKE EYES: (He reads the name and says nothing at all.)"])
S['STR_EVENT_SS_ARRIVAL_LOST'] = P.join([
    "SCARLETT: We lost the witness. One arrow, through a window nobody was watching. Our people never saw him.",
    "We have the arrow. The fletching is Japanese, and very old style. Somebody in this outfit isn't Cobra at all."])

# ------------------------------------------------------------------ 2. Zartan and the Dreadnoks (HIRE: fee + pay; needs a Dreadnok Garage)
S['STR_EVENT_DREADNOKS_CONVOY'] = 'FUEL CONVOY OVERDUE'
S['STR_EVENT_DREADNOKS_CONVOY_DESCRIPTION'] = P.join([
    "BREAKER: An Army fuel convoy went quiet on a swamp road in Florida two hours ago. Last call from the lead truck was 'bikers', then music, then nothing.",
    "SCARLETT: Florida State Police have it from a gas station clerk: a gang in leather, a swamp boat, and a man in a hood who paid for everything in new hundred-dollar bills."])
S['STR_BRIEFING_DREADNOKS_ARRIVAL_TITLE'] = 'OPERATION: SWAMP RAT'
S['STR_BRIEFING_DREADNOKS_ARRIVAL'] = P.join([
    "HAWK: Somebody hired a motorcycle gang to steal ten thousand gallons of Army fuel. They're draining the trucks into barges at a bait shop on the water.",
    "They're loud, they're mean, and they don't run. Don't let that fool you into thinking they're stupid. The hooded one isn't with the gang. He's the one paying them.",
    "Recover the trucks. Stop the barges. If you get a clean look at the man in the hood, take it, because I don't think anybody ever has."])
S['STR_EVENT_DREADNOKS_ARRIVAL_WON'] = P.join([
    "SCARLETT: Fuel recovered. The gang calls itself the Dreadnoks, from Australia by way of every swamp in the South. They follow one man: Zartan. Master of disguise.",
    "He was standing next to Roadblock at the end, wearing a deputy's uniform. Nobody noticed until he was gone."])
S['STR_EVENT_DREADNOKS_ARRIVAL_LOST'] = P.join([
    "SCARLETT: The barges got away with the fuel and the gang got away with the barges. Cobra just bought a lot of driving.",
    "The bikes have a name painted on the tanks: Dreadnoks. And the hooded man has one too. Zartan. Every report describes a different face."])

# ------------------------------------------------------------------ 3. Destro (ALLY: the M.A.R.S. order; opens Act 2)
S['STR_EVENT_DESTRO_ARMS_FAIR'] = 'AN ARMS FAIR'
S['STR_EVENT_DESTRO_ARMS_FAIR_DESCRIPTION'] = P.join([
    "SCARLETT: Every crate with the M.A.R.S. mark has pointed one way: a castle in Scotland and the family that has sold weapons out of it for four hundred years. Its head is called Destro.",
    "He's holding a private demonstration this week, by invitation. One of the invitations went to Cobra Commander. He accepted."])
S['STR_BRIEFING_DESTRO_ARRIVAL_TITLE'] = 'OPERATION: TRADE FAIR'
S['STR_BRIEFING_DESTRO_ARRIVAL'] = P.join([
    "HAWK: Remember the man in the steel mask on the footage? He's real, his name is Destro, and he's about to shake Cobra Commander's hand on his own firing range.",
    "If that handshake happens, Cobra stops buying M.A.R.S. weapons and starts getting them first. I'd rather it didn't.",
    "His guards are professionals, not Cobra recruits. His guests are dictators with bodyguards of their own. Nobody here is on our side.",
    "Break up the meeting. Grab whatever he's demonstrating. If you can take either man, take him."])
S['STR_EVENT_DESTRO_ARRIVAL_WON'] = P.join([
    "SCARLETT: The fair's broken up and we have the demonstrator's prototype. The handshake still happened, in the car on the way out. Destro is Cobra's partner now.",
    "But we cost him a buyer list and a weapon. He'll remember that. He's a man who keeps accounts."])
S['STR_EVENT_DESTRO_ARRIVAL_LOST'] = P.join([
    "SCARLETT: They shook hands on the range, in front of every dictator on Earth, and then they watched us leave.",
    "M.A.R.S. builds Cobra's weapons from today. Expect better guns, more of them, sooner."])

# ------------------------------------------------------------------ 4. The Baroness (PROMOTE: Cobra Intelligence)
S['STR_EVENT_BARONESS_TRANSPORT'] = 'PRISONER TRANSPORT'
S['STR_EVENT_BARONESS_TRANSPORT_DESCRIPTION'] = P.join([
    "SCARLETT: Washington is moving three of our Cobra prisoners to federal custody tomorrow. The route is supposed to be secret.",
    "Someone requested a copy of it this morning, with clearances that check out. They check out too well."])
S['STR_BRIEFING_BARONESS_ARRIVAL_TITLE'] = 'OPERATION: CHAIN OF CUSTODY'
S['STR_BRIEFING_BARONESS_ARRIVAL'] = P.join([
    "HAWK: Cobra knows the route. We know they know. So we're riding with the transport.",
    "Whoever runs this is good: real paperwork, real clearances, a real leak somewhere in Washington. That isn't a field commander. That's an intelligence officer.",
    "Keep the prisoners in the trucks and the trucks moving. If it turns into a fight, the prisoners are the prize. Theirs and ours."])
S['STR_EVENT_BARONESS_ARRIVAL_WON'] = P.join([
    "SCARLETT: Prisoners delivered. The woman running the ambush got away in a helicopter: black leather, glasses, a European accent. Cobra calls her the Baroness. She runs Cobra Intelligence.",
    "She knew my name. She used it."])
S['STR_EVENT_BARONESS_ARRIVAL_LOST'] = P.join([
    "SCARLETT: They took the prisoners. The leak in Washington is real, and the woman who used it is called the Baroness. She runs Cobra Intelligence now.",
    "Everything those prisoners told us, Cobra will hear about by the end of the week."])

# ------------------------------------------------------------------ 5. Tomax and Xamot (PROMOTE: the Crimson Guard)
S['STR_EVENT_TWINS_BOARD'] = 'EXTENSIVE ENTERPRISES'
S['STR_EVENT_TWINS_BOARD_DESCRIPTION'] = P.join([
    "SCARLETT: Extensive Enterprises has new chairmen: twins, Tomax and Xamot Paoli. Since they took over, the company's security men have started wearing red.",
    "There's a board meeting on the top floor of their tower on Friday. Washington has finally signed a warrant."])
S['STR_BRIEFING_TWINS_ARRIVAL_TITLE'] = 'OPERATION: HOSTILE TAKEOVER'
S['STR_BRIEFING_TWINS_ARRIVAL'] = P.join([
    "HAWK: We have a warrant for the books of Extensive Enterprises, and a feeling the books aren't going to be handed over politely.",
    "The guards are Crimson Guard: Cobra's elite, men with law degrees and rifles. The twins fight together. Hurt one and the other feels it. Don't let them stand side by side.",
    "There are office workers in that building who think they work for a shipping company. Get them out."])
S['STR_EVENT_TWINS_ARRIVAL_WON'] = P.join([
    "SCARLETT: We have the books. Extensive Enterprises was Cobra's bank, and the twins ran it. Tomax and Xamot, commanders of the Crimson Guard.",
    "Their lawyers were in court by noon. The company is ours to take apart."])
S['STR_EVENT_TWINS_ARRIVAL_LOST'] = P.join([
    "SCARLETT: The books went into a shredder on the forty-first floor while the twins went out by helicopter. Tomax and Xamot, commanders of the Crimson Guard.",
    "Their lawyers were in court by noon, suing us. They'll probably win."])

# ------------------------------------------------------------------ 6. Dr. Mindbender (CREATE: the Brainwave lab)
S['STR_EVENT_MINDBENDER_CLINIC'] = 'THE QUIET PATIENTS'
S['STR_EVENT_MINDBENDER_CLINIC_DESCRIPTION'] = P.join([
    "DOC: Six people walked out of a private clinic in Arizona this month and went home. Their families say they came back polite, calm, and somebody else.",
    "Two of them have since driven trucks for a Cobra front company. Neither one remembers applying."])
S['STR_BRIEFING_MINDBENDER_ARRIVAL_TITLE'] = 'OPERATION: SECOND OPINION'
S['STR_BRIEFING_MINDBENDER_ARRIVAL'] = P.join([
    "HAWK: The clinic belongs to a man who lost his medical licence twenty years ago. He's back, and Cobra is paying for his research.",
    "The patients aren't the enemy, even if they're holding rifles. Stun them if you can. Doc wants every one of them alive.",
    "Find the machine they're using, and find the doctor."])
S['STR_EVENT_MINDBENDER_ARRIVAL_WON'] = P.join([
    "DOC: The patients are coming back to themselves, slowly. The machine is in our hangar. The doctor calls himself Mindbender, and he left his notes behind.",
    "He'll build another one. But we understand this one now."])
S['STR_EVENT_MINDBENDER_ARRIVAL_LOST'] = P.join([
    "DOC: The clinic was empty by the time we were inside, patients and all. Dr. Mindbender's machine went with them.",
    "Somewhere tonight there are people who'll do whatever Cobra asks, and they won't know why."])

# ------------------------------------------------------------------ 7. Serpentor (CREATE: the Cloning Vats). Opened by a chain of tomb robberies.
S['STR_EVENT_SERPENTOR_TOMBS'] = 'GRAVE ROBBERS'
S['STR_EVENT_SERPENTOR_TOMBS_DESCRIPTION'] = P.join([
    "SCARLETT: Somebody is robbing tombs. Napoleon's. Genghis Khan's, if anybody could find it. Every one of them a great conqueror.",
    "They don't take the gold. They take samples."])
S['STR_BRIEFING_SERPENTOR_ARRIVAL_TITLE'] = 'OPERATION: LAST RELIC'
S['STR_BRIEFING_SERPENTOR_ARRIVAL'] = P.join([
    "HAWK: Cobra has its list of dead conquerors almost complete. The last name on it is in a museum vault, and Cobra is going in tonight.",
    "Mindbender is building something out of all those samples. Every one we keep from him is a piece he doesn't get.",
    "Stop the theft. Whatever comes out of that laboratory, I want it born missing something."])
S['STR_EVENT_SERPENTOR_ARRIVAL_WON'] = P.join([
    "SCARLETT: The relic stayed in the vault. It didn't stop them. Cobra has crowned a new leader, grown in a vat: Serpentor, emperor of Cobra.",
    "He's missing the conqueror we kept from him. Doc thinks it shows."])
S['STR_EVENT_SERPENTOR_ARRIVAL_LOST'] = P.join([
    "SCARLETT: They got the last relic. Cobra has crowned a new leader, grown in a vat from every great conqueror in history: Serpentor, emperor of Cobra.",
    "Cobra Commander stood at his side at the coronation. He didn't look happy about it."])

hdr = ('# STORY: the seven villain arrival missions (claude/VILLAIN_ARRIVALS_v1.md, DRAFT).\n'
       '# Text only. BUILD wires the ids. Generated: edit story_tools/gen_villain_text.py, not this file.\n')
body = yaml.dump({'extraStrings': [{'type': 'en-US', 'strings': S}, {'type': 'en-GB', 'strings': S}]},
                 sort_keys=False, width=200, allow_unicode=True)
open(os.path.join(OUT, 'gijoe_story_villains_text.rul'), 'w').write(hdr + body)
print('villain text:', len(S), 'strings')
