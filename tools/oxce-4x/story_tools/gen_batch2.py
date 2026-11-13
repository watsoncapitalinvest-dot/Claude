"""Batch 2 (STORY): captured Cobra tech + the clue library decodes, Year 1 (plus the B.A.T. teardown the spine needs).
Writes gijoe_research_captured.rul. Weapon items are BUILD's: topics on Cobra guns name the item id BUILD will create
(OXCE accepts a needItem topic whose item does not exist yet; it simply never becomes available)."""
import yaml, sys, os
OUT = sys.argv[1]
SECTION = 'STR_INTEL_FILES'
def topic(name, cost, points, deps=None, unlocks=None, lookup=None, destroy=True):
    t = {'name': name, 'cost': cost, 'points': points, 'needItem': True, 'destroyItem': destroy}
    if deps: t['dependencies'] = deps
    t['unlocks'] = unlocks or []
    if lookup: t['lookup'] = lookup
    return t
def article(aid, req): return {'id': aid, 'type_id': 8, 'section': SECTION, 'requires': [req], 'text': aid + '_UFOPEDIA'}
def loot(t, sell=0, w=1, size=0.1): return {'type': t, 'size': size, 'weight': w, 'bigSprite': 100, 'floorSprite': 100,
                                            'invWidth': 1, 'invHeight': 1, 'recover': True, 'battleType': 0, 'costSell': sell}
WHO = 'STR_WHO_IS_COBRA'
S = {}
# ---- Cobra gear (needs "Who Is Cobra?" so the lab knows what it is looking at)
R = [
 # weapons: BUILD's item ids (proposed). STR_ALIEN_GRENADE is the mod's existing Cobra Grenade slot.
 topic('STR_COBRA_REVOLVER', 40, 10, deps=[WHO], lookup='STR_COBRA_SIDEARM'),
 topic('STR_COBRA_RIFLE', 80, 20, deps=[WHO], lookup='STR_COBRA_FIELD_RIFLE'),
 topic('STR_ALIEN_GRENADE', 80, 20, deps=[WHO], lookup='STR_COBRA_GRENADE'),
 topic('STR_COBRA_FIELD_KIT', 100, 20, deps=[WHO]),
 topic('STR_CORPSE_TROOPER', 40, 10, deps=[WHO], lookup='STR_COBRA_UNIFORM'),
 # vehicles and aircraft: recovered wreckage (defined here)
 topic('STR_FANG_WRECKAGE', 150, 40, deps=[WHO]),
 topic('STR_STINGER_WRECKAGE', 150, 40, deps=[WHO]),
 topic('STR_VULTURE_PARTS', 180, 50, deps=[WHO]),
 topic('STR_RATTLER_WRECKAGE', 200, 50, deps=[WHO]),
 topic('STR_HISS_WRECKAGE', 250, 60, deps=[WHO]),
 # Act 3: B.A.T.s (the corpse item exists); the chip feeds spine step 29
 topic('STR_CORPSE_BAT', 250, 60, deps=[WHO], unlocks=['STR_BAT_CONTROL_CHIP'], lookup='STR_BAT_TEARDOWN'),
 {'name': 'STR_BAT_CONTROL_CHIP', 'cost': 250, 'points': 60, 'dependencies': ['STR_STORY_LOCK'], 'unlocks': []},
]
# ---- clue library decodes (CLUE_SYSTEM_DESIGN.md); no Cobra knowledge needed to read them
CLUES = [('STR_RADIO_CODEBOOK', 120, 30), ('STR_FUEL_RECEIPTS', 30, 5), ('STR_VEHICLE_REGISTRATION', 30, 5),
         ('STR_MATCHBOOK', 20, 5), ('STR_PHONE_NUMBER', 20, 5), ('STR_BURNED_PAPERS', 90, 10), ('STR_CIRCLED_MAP', 60, 25),
         ('STR_BANDED_CASH', 40, 10), ('STR_BILL_OF_LADING', 50, 15), ('STR_TICKET_STUB', 20, 5),
         ('STR_NOTICE_BOARD_ORDERS', 60, 20), ('STR_COBRA_PIN', 20, 5), ('STR_PHOTOGRAPHS', 50, 15)]
R += [topic(n, c, p) for n, c, p in CLUES]
items = [loot('STR_FANG_WRECKAGE', 30000, 10, 1.0), loot('STR_STINGER_WRECKAGE', 30000, 10, 1.0), loot('STR_VULTURE_PARTS', 40000, 10, 1.0),
         loot('STR_RATTLER_WRECKAGE', 40000, 10, 1.0), loot('STR_HISS_WRECKAGE', 60000, 15, 1.5)] + \
        [loot(n, 2000 if n == 'STR_BANDED_CASH' else 0) for n, _, _ in CLUES]
looked = {t['name']: t.get('lookup') for t in R}
ART = [article(looked[t['name']] or t['name'], t['name']) for t in R]
S.update({
 'STR_COBRA_SIDEARM': 'Cobra Sidearm',
 'STR_COBRA_SIDEARM_UFOPEDIA': 'A heavy revolver, serial numbers ground off, bought by the crate on the civilian market. Cobra\'s first troops carry whatever handgun is cheapest. There is nothing to learn from the gun except that Cobra does not make its own yet.',
 'STR_COBRA_FIELD_RIFLE': 'Cobra Field Rifle',
 'STR_COBRA_FIELD_RIFLE_UFOPEDIA': 'An AK-pattern rifle, new and unissued, in a wooden stock with no country\'s markings. These are not scavenged. Someone is making rifles for Cobra in quantity, and the men who carried these were issued them, not given them.',
 'STR_COBRA_GRENADE': 'Cobra Grenade',
 'STR_COBRA_GRENADE_UFOPEDIA': 'Cobra\'s fragmentation grenade: a simple, well-made design with a shorter fuse than ours. Roadblock thinks we can build it.',
 'STR_COBRA_FIELD_KIT': 'Cobra Field Kit',
 'STR_COBRA_FIELD_KIT_UFOPEDIA': 'A Medi-Viper\'s kit: pressure dressings, stimulants and a few drugs Doc had to send out to identify. Taken together they keep a wounded man fighting for longer than he should.',
 'STR_COBRA_UNIFORM': 'Cobra Uniform',
 'STR_COBRA_UNIFORM_UFOPEDIA': 'The blue uniform, the snake on the helmet and the hood. The early cells wore whatever they owned with an armband; more and more of them now wear the full uniform. Each new uniform we see is a sign that Cobra\'s supply has reached that region.',
 'STR_FANG_WRECKAGE': 'F.A.N.G. Wreckage',
 'STR_FANG_WRECKAGE_UFOPEDIA': 'What is left of a Cobra F.A.N.G. gyrocopter: a small, cheap machine with a short range, a machine gun and rocket pods. It flies close to where it is based, which tells us a strip is nearby.',
 'STR_STINGER_WRECKAGE': 'Stinger Wreckage',
 'STR_STINGER_WRECKAGE_UFOPEDIA': 'A Cobra Stinger: a four-wheel-drive jeep carrying a three-tube missile launcher. Built on a civilian chassis and fitted out somewhere with a good machine shop.',
 'STR_VULTURE_PARTS': 'Vulture Parts',
 'STR_VULTURE_PARTS_UFOPEDIA': 'Wreckage from a Cobra Vulture, the cargo aircraft that carries Cobra\'s money, guns and men between sites. The cargo hold tells us what it carried; the navigation equipment tells us where it was going.',
 'STR_RATTLER_WRECKAGE': 'Rattler Wreckage',
 'STR_RATTLER_WRECKAGE_UFOPEDIA': 'A Cobra Rattler: a swing-wing ground-attack jet with a rear gun turret. It is built to hunt transports, not fighters. Our pilots will fly better against it now that they know how it turns, and our Skystriker can be improved from what we learned.',
 'STR_HISS_WRECKAGE': 'H.I.S.S. Wreckage',
 'STR_HISS_WRECKAGE_UFOPEDIA': 'The first Cobra tank we have taken apart: the H.I.S.S., High Speed Sentry. Fast, lightly armoured, with twin cannons in an open turret. The hull plate carries a maker\'s mark nobody here recognises.',
 'STR_BAT_TEARDOWN': 'B.A.T. Teardown',
 'STR_BAT_TEARDOWN_UFOPEDIA': 'A Battle Android Trooper, taken apart on the bench. It is a machine, not a man in armour. Under the chest plate is a control chip that gives it its orders.',
 'STR_BAT_CONTROL_CHIP': 'B.A.T. Control Chip',
 'STR_BAT_CONTROL_CHIP_UFOPEDIA': 'The B.A.T.\'s control chip, decoded. It takes orders by radio, which means a strong enough signal can confuse it, and it carries a factory code that points to where it was built.',
 'STR_RADIO_CODEBOOK': 'Radio Codebook',
 'STR_RADIO_CODEBOOK_UFOPEDIA': 'A Cobra radio codebook. Every intercept and coded paper we take from now on is quicker to read.',
 'STR_FUEL_RECEIPTS': 'Fuel Receipts', 'STR_FUEL_RECEIPTS_UFOPEDIA': 'Fuel bought with cash at the same truck stops, again and again. A route.',
 'STR_VEHICLE_REGISTRATION': 'Vehicle Registration', 'STR_VEHICLE_REGISTRATION_UFOPEDIA': 'The registration of a Cobra vehicle, to a company at an address. Small vans do not travel far from home.',
 'STR_MATCHBOOK': 'Matchbook', 'STR_MATCHBOOK_UFOPEDIA': 'A matchbook from a business that does not seem to have any customers.',
 'STR_PHONE_NUMBER': 'Phone Number', 'STR_PHONE_NUMBER_UFOPEDIA': 'A phone number written on a napkin. It rings at a house that is never answered and is never empty.',
 'STR_BURNED_PAPERS': 'Burned Papers', 'STR_BURNED_PAPERS_UFOPEDIA': 'Papers somebody tried to burn and did not finish. What survived took a long time to read and was worth it.',
 'STR_CIRCLED_MAP': 'Map With a Place Circled', 'STR_CIRCLED_MAP_UFOPEDIA': 'A road map with one place circled in pencil and a date beside it.',
 'STR_BANDED_CASH': 'Banded Cash', 'STR_BANDED_CASH_UFOPEDIA': 'Cash in bank wrappers. The wrappers tell us which bank, and the bank tells us whose money it handles.',
 'STR_BILL_OF_LADING': 'Bill of Lading', 'STR_BILL_OF_LADING_UFOPEDIA': 'A bill of lading for a cargo shipped by sea: a ship, a port and a date.',
 'STR_TICKET_STUB': 'Ticket Stub', 'STR_TICKET_STUB_UFOPEDIA': 'A bus ticket stub. The man who carried it came from a town on the route.',
 'STR_NOTICE_BOARD_ORDERS': 'Notice Board Orders', 'STR_NOTICE_BOARD_ORDERS_UFOPEDIA': 'Orders pinned to a Cobra notice board: duty rosters and the next operation in the region.',
 'STR_COBRA_PIN': 'Cobra Pin', 'STR_COBRA_PIN_UFOPEDIA': 'A lapel pin with the Cobra emblem. Small, but it confirms who these men answer to.',
 'STR_PHOTOGRAPHS': 'Photographs', 'STR_PHOTOGRAPHS_UFOPEDIA': 'Photographs of a meeting: faces, a car and a building we can find.',
 'STR_COBRA_REVOLVER': 'Cobra Revolver', 'STR_COBRA_RIFLE': 'Cobra Rifle'
})
hdr = ('# STORY (Year 1 research + story), batch 2: captured Cobra tech and the clue library decodes.\n'
       '# Cobra gear needs "Who Is Cobra?" (gijoe_story_act1.rul) and the recovered item. Wreckage and clue items are\n'
       '# defined here (sprite = the ledger\'s 100 for now); Cobra WEAPON items are BUILD\'s: STR_COBRA_REVOLVER and\n'
       '# STR_COBRA_RIFLE are the ids proposed to BUILD; STR_ALIEN_GRENADE is the mod\'s existing Cobra Grenade.\n'
       '# What a prisoner or wreck teaches follows what Cobra has actually built (John, 12 Nov).\n')
strings = S
data = {'items': items, 'research': R, 'ufopaedia': ART,
        'extraStrings': [{'type': 'en-US', 'strings': strings}, {'type': 'en-GB', 'strings': strings}]}
open(os.path.join(OUT, 'gijoe_research_captured.rul'), 'w').write(hdr + yaml.dump(data, sort_keys=False, width=200, allow_unicode=True))
print('topics', len(R), 'articles', len(ART), 'items', len(items), 'strings', len(strings))
