"""Batch 1 (STORY): the interrogation spine + Act 1 beats as OXCE rulesets.
Writes gijoe_research_spine.rul and gijoe_story_act1.rul. Text goes in extraStrings (en-US + en-GB)."""
import yaml, sys, os
OUT = sys.argv[1]

class Q(str): pass
def q_rep(d, s): return d.represent_scalar('tag:yaml.org,2002:str', s, style="'")
yaml.add_representer(Q, q_rep)

LOCK = 'STR_STORY_LOCK'          # never researchable; topics behind it only open through another topic's unlocks
SECTION = 'STR_INTEL_FILES'

def topic(name, cost, points, deps=None, unlocks=None, needItem=False, destroyItem=None, lookup=None):
    t = {'name': name, 'cost': cost, 'points': points}
    if needItem: t['needItem'] = True
    if destroyItem is not None: t['destroyItem'] = destroyItem
    if deps: t['dependencies'] = deps
    t['unlocks'] = unlocks or []
    if lookup: t['lookup'] = lookup
    return t

def article(aid, req):
    return {'id': aid, 'type_id': 8, 'section': SECTION, 'requires': [req], 'text': aid + '_UFOPEDIA'}

def live_item(t, sell=40000):  return {'type': t, 'size': 0.0, 'recover': True, 'liveAlien': True, 'costSell': sell}
def clue_item(t, sell=0):      return {'type': t, 'size': 0.1, 'weight': 1, 'bigSprite': 100, 'floorSprite': 100,
                                       'invWidth': 1, 'invHeight': 1, 'recover': True, 'battleType': 0, 'costSell': sell}

def write(fname, header, data):
    body = yaml.dump(data, sort_keys=False, width=200, allow_unicode=True)
    open(os.path.join(OUT, fname), 'w').write(header + body)

# ---------------------------------------------------------------- SPINE
S = {}   # strings
spine_items = [live_item(t) for t in ['STR_VIPER_PILOT', 'STR_COBRA_OFFICER', 'STR_ARASHIKAGE', 'STR_IRON_GRENADIER',
                                      'STR_CRIMSON_GUARD']] + \
              [live_item(t, 60000) for t in ['STR_BARONESS', 'STR_DR_MINDBENDER']] + \
              [clue_item('STR_MARS_FACTORY_RECORDS', 20000), clue_item('STR_TERROR_DROME_DATA_CORE', 40000)]
R = [
 {'name': LOCK, 'cost': 999999, 'points': 0, 'requiresBaseFunc': ['STR_STORY_NEVER']},
 # existing prisoner topics (gijoe_campaign.rul) re-pointed at the spine; fields not listed here stay as they are
 topic('STR_COBRA_TROOPER', 150, 40, unlocks=['STR_COBRA_ORDER_OF_BATTLE'], needItem=True, destroyItem=True, lookup='STR_VIPER_INTERROGATION'),
 topic('STR_COBRA_ORDER_OF_BATTLE', 120, 30, deps=[LOCK]),
 topic('STR_VIPER_PILOT', 180, 50, unlocks=['STR_FANG_OPERATING_BASES'], needItem=True, destroyItem=True, lookup='STR_VIPER_PILOT_INTERROGATION'),
 topic('STR_FANG_OPERATING_BASES', 150, 40, deps=[LOCK]),
 topic('STR_COBRA_OFFICER', 220, 60, unlocks=['STR_COBRA_FLIGHT_ROUTES'], needItem=True, destroyItem=True, lookup='STR_COBRA_OFFICER_INTERROGATION'),
 topic('STR_COBRA_FLIGHT_ROUTES', 200, 50, deps=[LOCK]),
 # Medi-Viper: John 21:08, a prisoner only knows what Cobra has built - so Trauma Kit (batch 3) only, no Brainwave Scanner in Act 1
 topic('STR_VIPER_MEDIC', 180, 50, unlocks=[], needItem=True, destroyItem=True, lookup='STR_MEDI_VIPER_INTERROGATION'),
 topic('STR_ARASHIKAGE', 220, 60, unlocks=['STR_ARASHIKAGE_CLAN_SECRETS'], needItem=True, destroyItem=True, lookup='STR_ARASHIKAGE_INTERROGATION'),
 topic('STR_ARASHIKAGE_CLAN_SECRETS', 200, 50, deps=[LOCK]),
 topic('STR_STORM_SHADOW_UNIT', 300, 80, unlocks=['STR_HARD_MASTERS_MURDER'], needItem=True, destroyItem=True, lookup='STR_STORM_SHADOW_CAPTURED'),
 topic('STR_HARD_MASTERS_MURDER', 250, 60, deps=[LOCK]),
 topic('STR_IRON_GRENADIER', 220, 60, unlocks=['STR_MARS_SUPPLY_LINES'], needItem=True, destroyItem=True, lookup='STR_IRON_GRENADIER_INTERROGATION'),
 topic('STR_MARS_SUPPLY_LINES', 200, 50, deps=[LOCK]),
 topic('STR_MARS_FACTORY_RECORDS', 250, 60, needItem=True, destroyItem=True),
 topic('STR_DESTRO_UNIT', 300, 100, unlocks=['STR_DESTROS_ARMS_LEDGER'], needItem=True, destroyItem=True, lookup='STR_DESTRO_CAPTURED'),
 topic('STR_DESTROS_ARMS_LEDGER', 300, 80, deps=[LOCK]),
 topic('STR_CRIMSON_GUARD', 250, 60, unlocks=['STR_COBRAS_POLITICAL_FRONT'], needItem=True, destroyItem=True, lookup='STR_CRIMSON_GUARD_INTERROGATION'),
 topic('STR_COBRAS_POLITICAL_FRONT', 250, 60, deps=[LOCK]),
 topic('STR_BARONESS', 350, 100, unlocks=['STR_COBRA_INTELLIGENCE_NETWORK'], needItem=True, destroyItem=True, lookup='STR_BARONESS_CAPTURED'),
 topic('STR_COBRA_INTELLIGENCE_NETWORK', 300, 80, deps=[LOCK]),
 topic('STR_DR_MINDBENDER', 350, 100, unlocks=['STR_BRAINWAVE_BREAKTHROUGH'], needItem=True, destroyItem=True, lookup='STR_MINDBENDER_CAPTURED'),
 topic('STR_BRAINWAVE_BREAKTHROUGH', 350, 80, deps=[LOCK]),
 topic('STR_TERROR_DROME_DATA_CORE', 350, 100, needItem=True, destroyItem=True),
 topic('STR_COBRAS_TRUE_AGENDA', 350, 100, deps=['STR_TERROR_DROME_DATA_CORE', 'STR_DESTROS_ARMS_LEDGER']),
 topic('STR_COBRA_COMMANDERS_MOVEMENTS', 300, 80, deps=['STR_COBRAS_TRUE_AGENDA']),
 topic('STR_COBRA_COMMANDER_UNIT', 400, 200, unlocks=['STR_LOCATION_COBRA_ISLAND'], needItem=True, destroyItem=True, lookup='STR_COBRA_COMMANDER_CAPTURED'),
 topic('STR_LOCATION_COBRA_ISLAND', 300, 100, deps=[LOCK]),
 topic('STR_COBRA_ISLAND_OR_BUST', 200, 100, deps=['STR_LOCATION_COBRA_ISLAND']),
 # step 29 (the master doc numbers it 30); STR_BAT_CONTROL_CHIP is in gijoe_research_captured.rul
 topic('STR_BAT_FACTORY', 250, 60, deps=['STR_MARS_SUPPLY_LINES', 'STR_BAT_CONTROL_CHIP']),
]
# articles: the re-pointed prisoner topics read their lookup; everything else reads its own id
looked = {t['name']: t.get('lookup') for t in R}
ART = [article(looked[t['name']] or t['name'], t['name']) for t in R if t['name'] != LOCK]

S.update({
 'STR_INTEL_FILES': 'INTEL FILES',
 'STR_STORY_LOCK': 'Restricted',
 'STR_VIPER_INTERROGATION': 'Viper Interrogation',
 'STR_VIPER_INTERROGATION_UFOPEDIA': 'Step 1 of the trail. The prisoner is a Cobra trooper, a "Viper" in their own word for it: a former soldier with no papers, no unit patch and a rehearsed story. Scarlett broke the story in four days.{NEWLINE}{NEWLINE}He knows his cell, his sergeant and the colour of the trucks that bring the guns. He does not know who Cobra Commander is, and he is more afraid of Cobra than of us. That fear is the first useful thing we have learned about them.',
 'STR_COBRA_ORDER_OF_BATTLE': 'Cobra Order of Battle',
 'STR_COBRA_ORDER_OF_BATTLE_UFOPEDIA': 'Step 2. From prisoners and recovered paperwork we can now draw Cobra the way it draws itself: troopers in cells of ten to fifteen, officers above the cells, pilots and drivers on the side, and a command nobody below the officers has seen.{NEWLINE}{NEWLINE}Briefings from here on name what we are likely to face before we land. The Detention Block can be improved to hold more of them.',
 'STR_VIPER_PILOT_INTERROGATION': 'Viper Pilot Interrogation',
 'STR_VIPER_PILOT_INTERROGATION_UFOPEDIA': 'Step 3. Cobra\'s pilots are better trained than its troopers and proud of it, which makes them talk. This one flew F.A.N.G. gyrocopters from a dirt strip he can describe down to the windsock.{NEWLINE}{NEWLINE}His flight school was military. Ours, he thinks. Our Skystriker crews will want to read what he says about how Cobra flies.',
 'STR_FANG_OPERATING_BASES': 'F.A.N.G. Operating Bases',
 'STR_FANG_OPERATING_BASES_UFOPEDIA': 'Step 4. The F.A.N.G. cannot fly far, so it never lives far from where it fights. Cobra keeps its gyrocopters at small airstrips: a hangar, a fuel bowser, a few men. Each one is a target we can find from the air and hit on the ground.{NEWLINE}{NEWLINE}Airstrip raids are now possible wherever a strip is found.',
 'STR_COBRA_OFFICER_INTERROGATION': 'Cobra Officer Interrogation',
 'STR_COBRA_OFFICER_INTERROGATION_UFOPEDIA': 'Step 5. The first Cobra officer to reach our cells. He wears the same blue as his men and a different look in his eye: he believes. He will not give us his commander.{NEWLINE}{NEWLINE}He gave us something better without meaning to. Officers move between cells by air, on a schedule, and he complained about the schedule.',
 'STR_COBRA_FLIGHT_ROUTES': 'Cobra Flight Routes',
 'STR_COBRA_FLIGHT_ROUTES_UFOPEDIA': 'Step 6. Breaker has put the officer\'s complaints against a year of civil air traffic, and Cobra\'s cargo flights fall out of it: regular, unregistered, and always going somewhere quiet.{NEWLINE}{NEWLINE}A flight we know about is a flight we can follow home. A Signals Intelligence Center would let us listen to the rest.',
 'STR_MEDI_VIPER_INTERROGATION': 'Medi-Viper Interrogation',
 'STR_MEDI_VIPER_INTERROGATION_UFOPEDIA': 'Step 7. Cobra\'s field medic carries a kit that keeps wounded men fighting long after ours would be evacuated. Doc has been through all of it.{NEWLINE}{NEWLINE}The kit is good and we can build our own. Ask him about anything beyond the kit and he has nothing to say: whatever Cobra is planning for medicine, it has not reached the men in the field.',
 'STR_ARASHIKAGE_INTERROGATION': 'Arashikage Interrogation',
 'STR_ARASHIKAGE_INTERROGATION_UFOPEDIA': 'Step 8. A ninja in Cobra\'s service, taken alive, which nobody here thought could be done. He gives his clan\'s name and nothing else for weeks.{NEWLINE}{NEWLINE}Snake Eyes has been asked to read the transcripts. He has not said what he thinks of them.',
 'STR_ARASHIKAGE_CLAN_SECRETS': 'Arashikage Clan Secrets',
 'STR_ARASHIKAGE_CLAN_SECRETS_UFOPEDIA': 'Step 9. The Arashikage are a family of assassins older than Cobra and with no love for it. One of them works for Cobra Commander anyway, and the others call him by name: Storm Shadow.{NEWLINE}{NEWLINE}We know now where he trains and where he goes when the work is done.',
 'STR_STORM_SHADOW_CAPTURED': 'Storm Shadow Captured',
 'STR_STORM_SHADOW_CAPTURED_UFOPEDIA': 'Step 10. Storm Shadow is in our cells. He does not resist and he does not explain himself. He asks for one thing: to speak with Snake Eyes.{NEWLINE}{NEWLINE}What he wants to say concerns the death of the Hard Master, the old head of his clan, and who really killed him.',
 'STR_HARD_MASTERS_MURDER': 'The Hard Master\'s Murder',
 'STR_HARD_MASTERS_MURDER_UFOPEDIA': 'Storm Shadow joined Cobra to find the man who murdered his uncle, the Hard Master, and he believes that man is inside Cobra still. If we help him find the truth, he may stop being Cobra\'s weapon.',
 'STR_IRON_GRENADIER_INTERROGATION': 'Iron Grenadier Interrogation',
 'STR_IRON_GRENADIER_INTERROGATION_UFOPEDIA': 'Step 11. Destro\'s own troops, in Destro\'s own colours, fighting beside Cobra but answering to M.A.R.S. The prisoner is a professional and talks like one: about pay, contracts and shipping.',
 'STR_MARS_SUPPLY_LINES': 'M.A.R.S. Supply Lines',
 'STR_MARS_SUPPLY_LINES_UFOPEDIA': 'Step 12. M.A.R.S. builds the weapons and Cobra fires them. The guns travel from M.A.R.S. factories by routes we can now name. Factory raids are possible wherever a factory is found.',
 'STR_MARS_FACTORY_RECORDS': 'M.A.R.S. Factory Records',
 'STR_MARS_FACTORY_RECORDS_UFOPEDIA': 'Step 13. Production records from a raided M.A.R.S. factory. Every order is signed off by the same man, and the signatures move: we can follow Destro from plant to plant.',
 'STR_DESTRO_CAPTURED': 'Destro Captured',
 'STR_DESTRO_CAPTURED_UFOPEDIA': 'Step 14. James McCullen Destro XXIV, head of M.A.R.S., is our prisoner. He is courteous, untroubled and certain he will not be here long. He offers to talk business.',
 'STR_DESTROS_ARMS_LEDGER': 'Destro\'s Arms Ledger',
 'STR_DESTROS_ARMS_LEDGER_UFOPEDIA': 'Step 15. Destro\'s private accounts: what M.A.R.S. has sold to Cobra, for how much, and what Cobra still owes. Cut those lines and Cobra\'s money and guns both run short for a time.',
 'STR_CRIMSON_GUARD_INTERROGATION': 'Crimson Guard Interrogation',
 'STR_CRIMSON_GUARD_INTERROGATION_UFOPEDIA': 'Step 16. The Crimson Guard are Cobra\'s elite, and they live double lives: lawyers, accountants, a city councilman. This one had a law practice and a family in the suburbs.',
 'STR_COBRAS_POLITICAL_FRONT': 'Cobra\'s Political Front',
 'STR_COBRAS_POLITICAL_FRONT_UFOPEDIA': 'Step 17. The Crimson Guard are only the visible part. Behind them is a network that buys elections, places people and gathers secrets, and it reports to the Baroness.',
 'STR_BARONESS_CAPTURED': 'The Baroness Captured',
 'STR_BARONESS_CAPTURED_UFOPEDIA': 'Step 18. Cobra\'s head of intelligence is in our cells. She has spent years looking for The Pit. Now she is in it, and she is still taking notes.',
 'STR_COBRA_INTELLIGENCE_NETWORK': 'Cobra Intelligence Network',
 'STR_COBRA_INTELLIGENCE_NETWORK_UFOPEDIA': 'Step 19. The Baroness\'s network, mapped. Her people report to regional hubs, and the hubs are Terror Dromes, including Dromes we did not know existed.',
 'STR_MINDBENDER_CAPTURED': 'Dr. Mindbender Captured',
 'STR_MINDBENDER_CAPTURED_UFOPEDIA': 'Step 20. Dr. Mindbender, Cobra\'s chief scientist. He is happy to talk about his work, at length, to anyone. Doc listens in shifts.',
 'STR_BRAINWAVE_BREAKTHROUGH': 'Brainwave Breakthrough',
 'STR_BRAINWAVE_BREAKTHROUGH_UFOPEDIA': 'Step 21. Mindbender\'s notes take our own brainwave work years forward, and they show us how to shield a mind from his.',
 'STR_TERROR_DROME_DATA_CORE': 'Terror Drome Data Core',
 'STR_TERROR_DROME_DATA_CORE_UFOPEDIA': 'Steps 22-23. The data core of a fallen Terror Drome: every order the Drome sent or received. Most of it is routine. Some of it comes from the top, and it is not about a war.',
 'STR_COBRAS_TRUE_AGENDA': 'Cobra\'s True Agenda',
 'STR_COBRAS_TRUE_AGENDA_UFOPEDIA': 'Step 24. Put the Drome\'s orders beside Destro\'s ledger and the shape of it is plain. Cobra does not want to win a war. It wants to become a country.',
 'STR_COBRA_COMMANDERS_MOVEMENTS': 'Cobra Commander\'s Movements',
 'STR_COBRA_COMMANDERS_MOVEMENTS_UFOPEDIA': 'Step 25. Cobra Commander travels, and now we know how: which aircraft, which escorts, which sites he visits and how long he stays. He can be caught.',
 'STR_COBRA_COMMANDER_CAPTURED': 'Cobra Commander Captured',
 'STR_COBRA_COMMANDER_CAPTURED_UFOPEDIA': 'Step 26. Cobra Commander is our prisoner. Under the hood is an ordinary man who once sold used cars, and who lost a brother and blamed the world for it. He will not tell us where Cobra will make its stand. His papers will.',
 'STR_LOCATION_COBRA_ISLAND': 'Location: Cobra Island',
 'STR_LOCATION_COBRA_ISLAND_UFOPEDIA': 'Step 27. Cobra Island, in the Gulf of Mexico: built, armed and about to declare itself a nation.',
 'STR_COBRA_ISLAND_OR_BUST': 'Cobra Island or Bust',
 'STR_COBRA_ISLAND_OR_BUST_UFOPEDIA': 'Step 28. Every Joe, every vehicle, every aircraft. Hawk has the plan. We go to Cobra Island.',
 'STR_BAT_FACTORY': 'B.A.T. Factory',
 'STR_BAT_FACTORY_UFOPEDIA': 'Step 29. The control chips in Cobra\'s Battle Android Troopers and the M.A.R.S. supply lines lead to the same place: a plant where B.A.T.s are built by the hundred.',
 'STR_VIPER_PILOT': 'Viper Pilot', 'STR_COBRA_OFFICER': 'Cobra Officer', 'STR_ARASHIKAGE': 'Arashikage', 'STR_IRON_GRENADIER': 'Iron Grenadier',
 'STR_CRIMSON_GUARD': 'Crimson Guard', 'STR_BARONESS': 'The Baroness', 'STR_DR_MINDBENDER': 'Dr. Mindbender',
})

# ---------------------------------------------------------------- ACT 1 BEATS
act1_items = [live_item('STR_CARTEL_BOSS', 20000)] + [clue_item(t, s) for t, s in [
 ('STR_CARTEL_LEDGER', 5000), ('STR_CRATE_SERIAL_PLATE', 0), ('STR_COBRA_STENCIL', 0), ('STR_FACTORY_SCHEDULE', 0),
 ('STR_BROADCAST_RECORDING', 0), ('STR_BLUDD_CALLING_CARD', 0), ('STR_SHIPPING_MANIFEST', 0), ('STR_PILOT_LOGBOOK', 0),
 ('STR_DEPOT_RECORDS', 0), ('STR_TERROR_DROME_PLANS', 0), ('STR_MARS_MARKED_WEAPON', 0)]]
A = [
 topic('STR_RUMOURED_TERROR_GROUP', 10, 0, deps=[LOCK]),                      # BUILD: put in the starting research
 topic('STR_CARTEL_LEDGER', 60, 20, needItem=True, destroyItem=True, unlocks=['STR_WHO_IS_COBRA']),
 topic('STR_CRATE_SERIAL_PLATE', 40, 10, needItem=True, destroyItem=True),
 topic('STR_COBRA_STENCIL', 30, 10, needItem=True, destroyItem=True, unlocks=['STR_WHO_IS_COBRA']),
 topic('STR_WHO_IS_COBRA', 80, 20, deps=[LOCK]),
 topic('STR_CARTEL_BOSS', 80, 20, needItem=True, destroyItem=True, unlocks=['STR_FACTORY_REACTIVATION_DATE'], lookup='STR_CARTEL_BOSS_INTERROGATION'),
 topic('STR_FACTORY_SCHEDULE', 60, 20, needItem=True, destroyItem=True, unlocks=['STR_FACTORY_REACTIVATION_DATE']),
 topic('STR_FACTORY_REACTIVATION_DATE', 20, 10, deps=[LOCK]),
 topic('STR_BROADCAST_RECORDING', 100, 30, needItem=True, destroyItem=True, lookup='STR_TRACE_THE_BROADCAST'),
 # existing (gijoe_frontops.rul): the front-company books now lead to Extensive Enterprises
 topic('STR_COBRA_LEDGERS', 150, 30, needItem=True, unlocks=['STR_EXTENSIVE_ENTERPRISES']),
 topic('STR_EXTENSIVE_ENTERPRISES', 150, 40, deps=[LOCK]),
 # John 13 Nov 02:00: laundering is fought by tracing the money (needs the front company found AND banded cash decoded)
 topic('STR_FOLLOW_THE_MONEY', 200, 40, deps=['STR_EXTENSIVE_ENTERPRISES', 'STR_BANDED_CASH']),
 topic('STR_BLUDD_CALLING_CARD', 40, 20, needItem=True, destroyItem=True, lookup='STR_MAJOR_BLUDD'),
 topic('STR_SHIPPING_MANIFEST', 50, 15, needItem=True, destroyItem=True),
 topic('STR_PILOT_LOGBOOK', 50, 15, needItem=True, destroyItem=True),
 topic('STR_DEPOT_ROUTE_ANALYSIS', 300, 30, deps=['STR_SHIPPING_MANIFEST', 'STR_PILOT_LOGBOOK', 'STR_FUEL_RECEIPTS', 'STR_BILL_OF_LADING'], unlocks=['STR_COBRA_DEPOTS']),
 topic('STR_COBRA_DEPOTS', 150, 40, deps=['STR_COBRA_FLIGHT_ROUTES', 'STR_SHIPPING_MANIFEST']),
 topic('STR_DEPOT_RECORDS', 80, 20, needItem=True, destroyItem=True),
 topic('STR_TERROR_DROME_RUMOURS', 200, 50, deps=['STR_COBRA_DEPOTS', 'STR_DEPOT_RECORDS']),
 topic('STR_TERROR_DROME_PLANS', 150, 60, needItem=True, destroyItem=True),
 topic('STR_MARS_MARKED_WEAPON', 100, 50, needItem=True, destroyItem=True, lookup='STR_MARS_MARKINGS'),
]
looked = {t['name']: t.get('lookup') for t in A}
ART_A = [article(looked[t['name']] or t['name'], t['name']) for t in A if t['name'] != 'STR_COBRA_LEDGERS']
S.update({
 'STR_RUMOURED_TERROR_GROUP': 'A Rumoured Terror Group',
 'STR_RUMOURED_TERROR_GROUP_UFOPEDIA': 'For a year the agencies have traded stories about a new terrorist outfit: well armed, well paid, and gone by the time anyone arrives. No name, no photograph, no defectors.{NEWLINE}{NEWLINE}Hawk says money and guns always leave a trail. I say anyone this careful has made one mistake somewhere. Either way we start with a border cartel carrying hardware it cannot afford.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_CARTEL_LEDGER': 'Cartel Ledger',
 'STR_CARTEL_LEDGER_UFOPEDIA': 'The boss kept honest books, which is more than his customers did. Drugs, bribes, the usual. And one supplier with no name: cash in advance, collection at a West Texas machine works that went bankrupt two years ago.{NEWLINE}{NEWLINE}Bankrupt factories don\'t sell rifles. Somebody is using that one.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_CRATE_SERIAL_PLATE': 'Crate Serial Plate',
 'STR_CRATE_SERIAL_PLATE_UFOPEDIA': 'Roadblock read me the plate off a crate in the barn. The serial belongs to no army and no maker on any register we can reach. It does match a lot number, C-0417, stamped at a machine works in West Texas that went bust two years ago.{NEWLINE}{NEWLINE}One address. I like it already.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_COBRA_STENCIL': 'Cobra Stencil',
 'STR_COBRA_STENCIL_UFOPEDIA': 'Painted inside a crate lid, where the buyer was never meant to look: a coiled snake, hood spread. Not a cartel mark. Not anybody\'s mark, as far as any file in The Pit knows.{NEWLINE}{NEWLINE}Whoever packs these guns signs their work. That\'s pride, or it\'s a message.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_WHO_IS_COBRA': 'Who Is Cobra?',
 'STR_WHO_IS_COBRA_UFOPEDIA': 'The snake on those crates has a name: Cobra. No country, no cause I can find, and more money than any terrorist group has a right to.{NEWLINE}{NEWLINE}From today, anything we take from them goes to the lab, and anyone we take from them comes to me.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_CARTEL_BOSS_INTERROGATION': 'Cartel Boss Interrogation',
 'STR_CARTEL_BOSS_INTERROGATION_UFOPEDIA': 'The boss is a businessman and he bargained like one. His supplier warned him off the West Texas plant for a while: new owners were coming, and they wanted it back on a fixed date.{NEWLINE}{NEWLINE}He sold me the date for a better cell. Cheap at the price.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_FACTORY_SCHEDULE': 'Factory Production Schedule',
 'STR_FACTORY_SCHEDULE_UFOPEDIA': 'From the plant manager\'s safe: a production schedule on letterhead with the snake on it. The lines restart, a guard detail arrives and the first shipment leaves, all on one date.{NEWLINE}{NEWLINE}Hawk has circled it. So have I.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_FACTORY_REACTIVATION_DATE': 'Factory Reactivation Date',
 'STR_FACTORY_REACTIVATION_DATE_UFOPEDIA': 'We know when Cobra takes the West Texas plant back. Hit it before then and the lines never start. Hit it on the day and it will be guarded. Leave it, and its rifles will be in Cobra hands within months.{NEWLINE}{NEWLINE}Hawk\'s call. My advice is before.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_TRACE_THE_BROADCAST': 'Trace the Broadcast',
 'STR_TRACE_THE_BROADCAST_UFOPEDIA': 'Cobra Commander has introduced himself to the world: a hooded man, a snake banner and ninety seconds of threats. Breaker took the signal apart. Three relays, and whoever set up the first one got lazy.{NEWLINE}{NEWLINE}It leads to one building and one Cobra cell. A cell, not a headquarters. But cells are full of people, and people talk.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_EXTENSIVE_ENTERPRISES': 'Extensive Enterprises',
 'STR_EXTENSIVE_ENTERPRISES_UFOPEDIA': 'Cobra\'s money runs through one company: Extensive Enterprises. Warehouses, shipping lines, offices in three countries, and every one of them clean on paper. The owners of record are twin brothers, Tomax and Xamot Paoli. Their signatures on the board minutes match to the pen stroke.{NEWLINE}{NEWLINE}Their offices and warehouses can now be raided.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_FOLLOW_THE_MONEY': 'Follow the Money',
 'STR_FOLLOW_THE_MONEY_UFOPEDIA': 'Cobra washes its cash before it spends it: through the Twins\' companies, a few friendly banks, and anywhere that takes a lot of money and asks no questions. Washed money leaves cold trails.{NEWLINE}{NEWLINE}The bank wrappers and Extensive Enterprises\' books give us the method. My analysts can now trace laundered cash back to where it was washed, and with enough paper Washington can freeze the accounts.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_MAJOR_BLUDD': 'Major Bludd',
 'STR_MAJOR_BLUDD_UFOPEDIA': 'Sebastian Bludd. Mercenary, Australian, poet by his own account, and Cobra\'s now. He left a card behind with the names of the Joes who got in his way and a promise, in verse, to see each of them again.{NEWLINE}{NEWLINE}The verse is bad. The promise I\'m taking seriously.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_SHIPPING_MANIFEST': 'Shipping Manifest',
 'STR_SHIPPING_MANIFEST_UFOPEDIA': 'A manifest for cargo that doesn\'t exist, from a company that doesn\'t trade, to a warehouse that keeps turning up in other papers.{NEWLINE}{NEWLINE}One piece of paper is a curiosity. I\'m collecting them.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_PILOT_LOGBOOK': 'Pilot\'s Logbook',
 'STR_PILOT_LOGBOOK_UFOPEDIA': 'A Cobra pilot\'s logbook: times, fuel and landing strips in a private shorthand. Private to him, anyway. Once you have the key it reads like a bus timetable.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_DEPOT_ROUTE_ANALYSIS': 'Depot Route Analysis',
 'STR_DEPOT_ROUTE_ANALYSIS_UFOPEDIA': 'I put the manifests, the logbook, the fuel receipts and the bills of lading on one map. The same handful of places keeps coming up. Without an officer to confirm it this took longer, but I\'d stake my stripes on it: depots.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_COBRA_DEPOTS': 'Cobra Depots',
 'STR_COBRA_DEPOTS_UFOPEDIA': 'Cobra\'s flights and trucks don\'t run cell to cell. They run to depots: warehouses where guns, money and men are gathered and sent on.{NEWLINE}{NEWLINE}We can find them now. A depot found is a depot raided.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_DEPOT_RECORDS': 'Depot Records',
 'STR_DEPOT_RECORDS_UFOPEDIA': 'Records from the depot we hit. Most of the stock went out to the cells, as expected. A fixed share of everything went somewhere else, and no address is given.{NEWLINE}{NEWLINE}Nobody skims that neatly unless they\'re told to.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_TERROR_DROME_RUMOURS': 'Rumours of a Terror Drome',
 'STR_TERROR_DROME_RUMOURS_UFOPEDIA': 'Every depot sends its share to the same place, and none of our sources has seen it. Prisoners call it the Drome: a fortress with its own air wing, they say, and nearly finished.{NEWLINE}{NEWLINE}From now on every captured document gets read for one thing: how close.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_TERROR_DROME_PLANS': 'Terror Drome Defense Plans',
 'STR_TERROR_DROME_PLANS_UFOPEDIA': 'Cobra\'s first Terror Drome, on paper: gun positions, the Firebat launch bay, the garrison rota, and where it is. Hawk is drawing up the assault.{NEWLINE}{NEWLINE}I\'ve told him what the plans can\'t. They will know these are missing.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_MARS_MARKINGS': 'M.A.R.S. Markings',
 'STR_MARS_MARKINGS_UFOPEDIA': 'Roadblock found it on a rifle from the Drome, under Cobra\'s paint: a maker\'s mark. M.A.R.S., Military Armaments Research Syndicate.{NEWLINE}{NEWLINE}Cobra doesn\'t build its own guns. Somebody sells them, and a seller that size never has just one customer. I want to know who signs his invoices.{NEWLINE}{NEWLINE}- Scarlett',
 'STR_CARTEL_BOSS': 'Cartel Boss', 'STR_BROADCAST_RECORDING': 'Broadcast Recording', 'STR_BLUDD_CALLING_CARD': 'Bludd\'s Calling Card',
 'STR_MARS_MARKED_WEAPON': 'M.A.R.S.-Marked Weapon',
})

hdr = ('# STORY (Year 1 research + story). The interrogation spine: the 29-step chain from the master doc, as research.\n'
       '# Overrides the prisoner topics in gijoe_campaign.rul (loads after it). Steps past Act 1 are stubs: correct names\n'
       '# and needs, reachable only once their prisoner or item exists. STR_STORY_LOCK is never researchable; a topic that\n'
       '# depends on it only opens through another topic\'s unlocks. Text is in extraStrings below.\n'
       '# Rule (John 12 Nov): a prisoner only knows what Cobra has already built or researched.\n')
strings_spine = {k: v for k, v in S.items() if k.startswith(tuple(['STR_INTEL', 'STR_STORY'] + [t['name'] for t in R] + [a['id'] for a in ART]))}
write('gijoe_research_spine.rul', hdr, {'items': spine_items, 'research': R, 'ufopaedia': ART,
      'extraStrings': [{'type': 'en-US', 'strings': strings_spine}, {'type': 'en-GB', 'strings': strings_spine}]})
strings_a1 = {k: v for k, v in S.items() if k not in strings_spine}
hdr2 = ('# STORY (Year 1 research + story). Act 1 "Rise of Cobra" as research: the cartel raid, the abandoned factory,\n'
        '# Cobra Commander\'s broadcast, Extensive Enterprises, Major Bludd, the depot trail and the Terror Drome climax.\n'
        '# Each beat is a recovered item and the topic that reads it; the item comes from the mission (BUILD wires those).\n'
        '# Every beat has a version for each outcome: the depots open from a captured officer OR from two clues.\n')
write('gijoe_story_act1.rul', hdr2, {'items': act1_items, 'research': A, 'ufopaedia': ART_A,
      'extraStrings': [{'type': 'en-US', 'strings': strings_a1}, {'type': 'en-GB', 'strings': strings_a1}]})
print('spine', len(R), 'topics', len(ART), 'articles', len(strings_spine), 'strings; act1', len(A), len(ART_A), len(strings_a1))
