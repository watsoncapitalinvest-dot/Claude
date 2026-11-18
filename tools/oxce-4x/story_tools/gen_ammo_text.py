"""STORY: text for ammo, resupply and the M.A.R.S. supply line (claude/AMMO_SUPPLY_v1.md, John 17 Nov 18:44-19:40).
Writes mod/Ruleset/gijoe_story_ammo_text.rul (extraStrings only, en-US + en-GB). Loads after gijoe_story_act1.rul,
so its STR_CRATE_SERIAL_PLATE_UFOPEDIA (the one hint, John 19:31) replaces batch 1's.
The ids are the ones in claude/BRIEF_FOR_BUILD_AmmoSupply.txt. Usage: python3 gen_ammo_text.py <mod/Ruleset dir>
"""
import os, sys, yaml

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'mod', 'Ruleset')
N = '{NEWLINE}'
P = N + N
S = {}
SUPPLIER = 'Larkhall Ordnance Supply'
S['STR_SUPPLIER_NAME'] = SUPPLIER

# ---- The one hint (the ranch crate plate). Batch 1's text, plus the last paragraph.
S['STR_CRATE_SERIAL_PLATE_UFOPEDIA'] = P.join([
    "Roadblock read me the plate off a crate in the barn. The serial belongs to no army and no maker on any register we can reach. It carries a lot number, C-0417, that nobody admits to.",
    "Someone stamps their own lot numbers. That's a factory, somewhere.",
    "- Scarlett",
    "ROADBLOCK: Every round in our own stores has a lot stamp on it too. Never looked at ours twice. Might be worth reading the cards on what we've got."])

# ---- Card markings: one line on every ammo item's card (BUILD item 4). Every Larkhall lot is C-04xx, ours and theirs.
MARK = "Lot {}, stamped on the base."
CARDS = {
    # bought by the Joes (through Larkhall)
    'STR_GJ_AMMO_A556': 'C-0421', 'STR_GJ_AMMO_A556_30': 'C-0422', 'STR_GJ_AMMO_A9MM': 'C-0419', 'STR_GJ_AMMO_A45': 'C-0408',
    'STR_GJ_AMMO_A44': 'C-0405', 'STR_GJ_AMMO_A12G': 'C-0411', 'STR_GJ_AMMO_A762BELT': 'C-0430', 'STR_GJ_AMMO_A50': 'C-0433',
    'STR_GJ_AMMO_A83': 'C-0440', 'STR_GJ_AMMO_A81': 'C-0441', 'STR_GJ_AMMO_ABOLT': 'C-0402', 'STR_GJ_AMMO_AFLARE': 'C-0401',
    'STR_GJ_AMMO_AJAV': 'C-0450', 'STR_GJ_AMMO_ALASER': 'C-0460',
    'STR_HC_AP_AMMO': 'C-0435', 'STR_AC_AP_AMMO': 'C-0434', 'STR_SMALL_ROCKET': 'C-0442',
    # issued by Cobra (also in the Joes' Day 1 stores: the same rounds, the same maker)
    'STR_PISTOL_CLIP': 'C-0419', 'STR_RIFLE_CLIP': 'C-0420', 'STR_ALIEN_GRENADE': 'C-0417', 'STR_GJ_AMMO_A762AK': 'C-0425',
    # later Cobra ammunition: no lot, a part number (the trail goes cold here, on purpose)
    'STR_PLASMA_PISTOL_CLIP': None, 'STR_PLASMA_RIFLE_CLIP': None, 'STR_HEAVY_PLASMA_CLIP': None,
}
for item, lot in CARDS.items():
    S['STR_CARD_MARKINGS_' + item[4:]] = MARK.format(lot) if lot else "No lot stamp. A part number, etched: MRS-11."

# ---- Ammo research, one topic per Cobra round (BUILD item 5). Ordinary research first; the provenance is the last
# paragraph. Voice: Roadblock (Armory head), with Scarlett where it turns into intel.
def ammo(item, name, body, maker):
    S['STR_AMMO_' + item[4:]] = name
    S['STR_AMMO_' + item[4:] + '_UFOPEDIA'] = P.join(body + [maker])

ammo('STR_PISTOL_CLIP', '9 mm Pistol Round (Cobra)', [
    "ROADBLOCK: Standard 9 millimetre, full metal jacket, a 30-round box for the Uzi. Nothing clever about it. Cobra's men carry it because it's cheap, it's everywhere, and it kills you just as dead.",
    "We've checked it in our guns. It feeds clean, so whatever we take off them, we use. Knowing what they shoot also tells us what our vests have to stop: the next armour job in the lab starts ahead."],
    "SCARLETT: The lot stamp is C-0419. The boxes come from Firth Precision, Rotterdam. Firth has an address, a telex number and a registered agent in Glasgow. It does not have a factory.")
ammo('STR_RIFLE_CLIP', '5.56 mm Rifle Round (Cobra)', [
    "ROADBLOCK: 5.56 NATO, 30 to the magazine. The same round we fire. Cobra's riflemen got it the same way we did, by buying it, which tells you how big their wallet is.",
    "It fits our rifles, so captured stock goes straight into our stores. And we know now exactly what our armour has to stop."],
    "SCARLETT: Lot C-0420. Maker of record: Calder Arms Export, Antwerp. Calder's warehouse is a rented room over a bakery. Same registered agent in Glasgow as Firth. Somebody owns a lot of companies that don't make anything.")
ammo('STR_ALIEN_GRENADE', 'Cobra Fragmentation Grenade', [
    "ROADBLOCK: A fragmentation grenade with a short fuse, and the casing scored so it breaks even. Better than ours, if I'm honest. Somebody designs these for a living.",
    "We can throw what we capture. Knowing the pattern helps the lab with what our vests have to stop."],
    "SCARLETT: Lot C-0417. The same number as the plate on the ranch crates. The fuse body says Arbroath Industrial, Lisbon. Arbroath, Calder and Firth all file their accounts through the same Glasgow office.")
ammo('STR_GJ_AMMO_A762AK', '7.62 mm AK Round (Cobra)', [
    "ROADBLOCK: The short 7.62, thirty to a curved magazine. Cobra hands it out with the AKs it buys by the crate. Heavy, hits hard, carries well.",
    "Captured magazines fit the captured rifles, so they're ours to use."],
    "SCARLETT: Lot C-0425. Calder Arms Export again. Their invoices are in sterling, not dollars or guilders. The money ends up in Scotland.")
ammo('STR_PLASMA_PISTOL_CLIP', 'Pulse Pistol Cell', [
    "ROADBLOCK: This isn't a cartridge. It's a sealed cell, and when it's spent it's warm and empty. I don't know who makes these. Nobody sells them.",
    "We can study how it's built, and that tells the lab what our armour has to take."],
    "SCARLETT: No lot stamp. A part number etched in the casing: MRS-11. Whoever made the lot-stamped rounds didn't make this, or doesn't want to be seen to.")
ammo('STR_PLASMA_RIFLE_CLIP', 'Pulse Rifle Cell', [
    "ROADBLOCK: A bigger cell for the pulse rifle. Same build, more of it.",
    "Knowing its output helps the lab with our armour."],
    "SCARLETT: Part number MRS-14. The same etching as the pistol cell.")
ammo('STR_HEAVY_PLASMA_CLIP', 'Heavy Pulse Cell', [
    "ROADBLOCK: The heavy pulse gun's cell. If one of these cracks, stand somewhere else.",
    "Knowing its output helps the lab with our armour."],
    "SCARLETT: Part number MRS-19.")

# ---- The audit of our own stock (opened by a Joe ammo card once a Cobra round is researched).
S['STR_AMMO_QUALITY_AUDIT'] = 'Ammunition Quality Audit'
S['STR_AMMO_QUALITY_AUDIT_UFOPEDIA'] = P.join([
    "ROADBLOCK: We pulled a sample of every lot in our stores and test-fired it. A few bad boxes went back. What's left is checked, and it groups tighter.",
    "SCARLETT: Every box we own came from " + SUPPLIER + ". Their lot numbers start C-04. So do Cobra's.",
    "I'm not saying what that means yet."])

# ---- The end of the trail (INTEL). Needs the M.A.R.S.-marked weapon from the Act 1 close.
S['STR_CLEAN_SUPPLY'] = 'Clean Supply'
S['STR_CLEAN_SUPPLY_UFOPEDIA'] = P.join([
    "SCARLETT: " + SUPPLIER + ", Firth Precision, Calder Arms Export, Arbroath Industrial. Four names, one office in Glasgow, one owner behind it, and the same mark we found on the weapon from the Drome: M.A.R.S.",
    "We have been buying our ammunition from the people who arm Cobra. Every box we paid for, they got paid for.",
    "HAWK: That stops today. General Flagg will take over every purchase this team makes, personally, through the Pentagon. It will cost more and it will be slower. It will be clean."])

# ---- The Pentagon attack and the rescue (BUILD item 7).
S['STR_EVENT_FLAGG_HIT'] = 'GENERAL FLAGG IS DOWN'
S['STR_EVENT_FLAGG_HIT_DESCRIPTION'] = P.join([
    "HAWK: General Flagg was shot leaving the Pentagon twenty minutes ago. His car is pinned on a side street and the shooters are still there.",
    "He was on his way to sign the new supply contract. Somebody didn't want it signed. Get a team to Washington, now."])
S['STR_FLAGG_RESCUE'] = 'Washington: Flagg Ambushed'
S['STR_BRIEFING_FLAGG_RESCUE_TITLE'] = 'OPERATION: SHIELD'
S['STR_BRIEFING_FLAGG_RESCUE'] = P.join([
    "HAWK: Flagg is down behind his car, hit and bleeding. His driver is dead. Cobra has the street.",
    "Reach him, keep him alive, and get him to the extraction point. Don't try to take him through the shooters. He can't run.",
    "If we fail, they'll take him with them. Don't fail."])
S['STR_EVENT_FLAGG_RETIRES'] = 'THE GENERAL STEPS DOWN'
S['STR_EVENT_FLAGG_RETIRES_DESCRIPTION'] = P.join([
    "HAWK: The doctors say General Flagg will walk again. They also say he won't be going back into the field.",
    "He's been asked to serve as Secretary of Defense, and he's said yes. His first order was to put every purchase this team makes through his own office. Our supply is clean.",
    "I've worked for worse men. I don't think I'll work for a better one."])
S['STR_EVENT_LIBERTY_RENAMED'] = 'U.S.S. FLAGG'
S['STR_EVENT_LIBERTY_RENAMED_DESCRIPTION'] = P.join([
    "The Navy has renamed the carrier U.S.S. Liberty in honour of General Flagg. She sails as the U.S.S. Flagg.",
    "KEEL-HAUL: Same ship, same crew, a better name. All hands, battle stations."])
S['STR_CARRIER_NAME_LIBERTY'] = 'U.S.S. Liberty'
S['STR_CARRIER_NAME_FLAGG'] = 'U.S.S. Flagg'
# Keel-Haul's dossier after the rename (BUILD swaps STR_ART_KEEL_HAUL_TEXT for this one).
S['STR_ART_KEEL_HAUL_TEXT_RENAMED'] = (
    'KEEL-HAUL{NEWLINE}G.I. Joe - Rear Admiral (O-8){NEWLINE}Real name: Everett P. Colby{NEWLINE}Specialty: Carrier commander; Pilot'
    '{NEWLINE}Birthplace: Charlottesville, Virginia{NEWLINE}{NEWLINE}DOSSIER{NEWLINE}Keel-Haul commands the U.S.S. Flagg, the aircraft '
    'carrier that serves as the team\'s floating base, renamed for the general who gave the team its supply back. A Virginia naval officer '
    'of the old school, he runs his ship with discipline and his crew with pride. When his guns speak, the battle changes.{NEWLINE}{NEWLINE}'
    'IN THE FIELD{NEWLINE}Signature weapon: Sidearm{NEWLINE}Signature move: Fleet Support: naval gunfire on a target area if the U.S.S. Flagg '
    'or a TTBP is in range; otherwise a coastal battery strike{NEWLINE}{NEWLINE}"All hands, battle stations."')

hdr = ('# STORY: ammo research, card markings and the M.A.R.S. supply line (claude/AMMO_SUPPLY_v1.md).\n'
       '# Text only; BUILD wires the ids (claude/BRIEF_FOR_BUILD_AmmoSupply.txt). Generated by story_tools/gen_ammo_text.py.\n'
       '# Loads after gijoe_story_act1.rul on purpose: its STR_CRATE_SERIAL_PLATE_UFOPEDIA replaces batch 1\'s.\n')
body = yaml.dump({'extraStrings': [{'type': 'en-US', 'strings': S}, {'type': 'en-GB', 'strings': S}]},
                 sort_keys=False, width=200, allow_unicode=True)
open(os.path.join(OUT, 'gijoe_story_ammo_text.rul'), 'w').write(hdr + body)
print('ammo text:', len(S), 'strings')
