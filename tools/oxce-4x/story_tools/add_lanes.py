"""Add `lane:` to every research topic in STORY's rulesets (John 12 Nov 22:13).
The research tree screen (claude/RESEARCH_TREE_SCREEN_SPEC.md) puts each topic in the
band of the department that runs it (the screen shows its head, whether the head is in the office, and its efficiency). OXCE ignores unknown keys, so this is inert until
BUILD's tree screen reads it. Run after the gen_batch scripts and fix_lookups.py: python3 add_lanes.py <Ruleset dir>
"""
import os, re, sys

RD = sys.argv[1]
# Departments, not heads: a head can change, the department stays (John 22:18).
H, S, D, B, R, V, A = 'COMMAND', 'INTEL', 'MEDICAL', 'COMMS', 'ARMORY', 'MOTOR_POOL', 'AIR_WING'
LANE = {
    # interrogation spine
    'STR_COBRA_TROOPER': S, 'STR_COBRA_ORDER_OF_BATTLE': S, 'STR_VIPER_PILOT': S, 'STR_FANG_OPERATING_BASES': S,
    'STR_COBRA_OFFICER': S, 'STR_COBRA_FLIGHT_ROUTES': B, 'STR_VIPER_MEDIC': D, 'STR_ARASHIKAGE': S,
    'STR_ARASHIKAGE_CLAN_SECRETS': S, 'STR_STORM_SHADOW_UNIT': S, 'STR_HARD_MASTERS_MURDER': S, 'STR_IRON_GRENADIER': S,
    'STR_MARS_SUPPLY_LINES': S, 'STR_MARS_FACTORY_RECORDS': R, 'STR_DESTRO_UNIT': S, 'STR_DESTROS_ARMS_LEDGER': R,
    'STR_CRIMSON_GUARD': S, 'STR_COBRAS_POLITICAL_FRONT': S, 'STR_BARONESS': S, 'STR_COBRA_INTELLIGENCE_NETWORK': S,
    'STR_DR_MINDBENDER': S, 'STR_BRAINWAVE_BREAKTHROUGH': D, 'STR_TERROR_DROME_DATA_CORE': B, 'STR_COBRAS_TRUE_AGENDA': H,
    'STR_COBRA_COMMANDERS_MOVEMENTS': S, 'STR_COBRA_COMMANDER_UNIT': S, 'STR_LOCATION_COBRA_ISLAND': H,
    'STR_COBRA_ISLAND_OR_BUST': H, 'STR_BAT_FACTORY': R,
    # Act 1 beats
    'STR_RUMOURED_TERROR_GROUP': H, 'STR_CARTEL_LEDGER': S, 'STR_CRATE_SERIAL_PLATE': R, 'STR_COBRA_STENCIL': S,
    'STR_WHO_IS_COBRA': S, 'STR_CARTEL_BOSS': S, 'STR_FACTORY_SCHEDULE': S, 'STR_FACTORY_REACTIVATION_DATE': S,
    'STR_BROADCAST_RECORDING': B, 'STR_COBRA_LEDGERS': S, 'STR_EXTENSIVE_ENTERPRISES': S, 'STR_BLUDD_CALLING_CARD': H,
    'STR_SHIPPING_MANIFEST': S, 'STR_PILOT_LOGBOOK': S, 'STR_DEPOT_ROUTE_ANALYSIS': S, 'STR_COBRA_DEPOTS': S,
    'STR_DEPOT_RECORDS': S, 'STR_TERROR_DROME_RUMOURS': S, 'STR_TERROR_DROME_PLANS': H, 'STR_MARS_MARKED_WEAPON': R,
    # captured Cobra gear and clues
    'STR_COBRA_REVOLVER': R, 'STR_COBRA_RIFLE': R, 'STR_ALIEN_GRENADE': R, 'STR_COBRA_FIELD_KIT': D,
    'STR_CORPSE_TROOPER': R, 'STR_FANG_WRECKAGE': A, 'STR_STINGER_WRECKAGE': V, 'STR_VULTURE_PARTS': A,
    'STR_RATTLER_WRECKAGE': A, 'STR_HISS_WRECKAGE': V, 'STR_CORPSE_BAT': R, 'STR_BAT_CONTROL_CHIP': R,
    'STR_RADIO_CODEBOOK': B, 'STR_FUEL_RECEIPTS': S, 'STR_VEHICLE_REGISTRATION': S, 'STR_MATCHBOOK': S,
    'STR_PHONE_NUMBER': S, 'STR_BURNED_PAPERS': S, 'STR_CIRCLED_MAP': S, 'STR_BANDED_CASH': S,
    'STR_BILL_OF_LADING': S, 'STR_TICKET_STUB': S, 'STR_NOTICE_BOARD_ORDERS': S, 'STR_COBRA_PIN': S,
    'STR_PHOTOGRAPHS': S,
}
for t in ('STANDARD_ISSUE STANDARD_EXPLOSIVES STANDARD_FATIGUES BREACHING_SHOTGUN KEVLAR_VEST AP_ROUNDS NIGHT_VISION '
          'MATCH_GRADE_OPTICS C4_DEMOLITIONS CLAYMORE_MINES MOUNTAIN_HOWITZER JUMP_JET_PACK PAC_RATS BATTLE_STATIONS '
          'WATCH_TOWER BIVOUAC SQUAD_AUTOMATIC_WEAPON INCENDIARY_ROUNDS CONCUSSION_GRENADE THERMITE LASER_GUIDED_ROCKETS '
          'JOE_COBRA_GRENADE GHILLIE_SUIT ARCTIC_GEAR NINJA_GEAR ANTI_AIRCRAFT_GUN').split():
    LANE['STR_' + t] = R
for t in 'FIELD_MEDICINE COMBAT_STIMS TRAUMA_KIT INFIRMARY'.split():
    LANE['STR_' + t] = D
for t in 'FIELD_RADIO RADAR_ROOM SONAR_SUITE SIGNALS_INTELLIGENCE_CENTER LONG_RANGE_RADAR'.split():
    LANE['STR_' + t] = B
for t in 'OVERWATCH_DRILLS BREACHING_DRILLS FIRE_AND_MOVE'.split():
    LANE['STR_' + t] = H
for t in 'STOP_AND_SEARCH DETENTION_BLOCK'.split():
    LANE['STR_' + t] = S
for t in ('VAMP VAMP_MK2 MOBAT RAM HAL FLAK WOLVERINE SLUGGER POLAR_BATTLE_BEAR MMS SNOW_CAT TWIN_BATTLE_GUN '
          'SHARC MANTA KILLER_WHALE DEVILFISH').split():
    LANE['STR_' + t] = V
for t in ('SKYSTRIKER SKYSTRIKER_MK2 C130_HERCULES DRAGONFLY FALCON_GLIDER SKY_HAWK TOMAHAWK MUDFIGHTER '
          'AIR_COMBAT_DOCTRINE AVALANCHE_MISSILE').split():
    LANE['STR_' + t] = A
SKIP = {'STR_STORY_LOCK'}

# lookup stubs (fix_lookups.py) take the lane of the topic whose lookup they are
import yaml as _y
for f in ['gijoe_research_spine.rul', 'gijoe_story_act1.rul', 'gijoe_research_captured.rul', 'gijoe_research_joe.rul']:
    for r in (_y.safe_load(open(os.path.join(RD, f))) or {}).get('research') or []:
        if r.get('lookup') and r['name'] in LANE and r['lookup'] not in LANE:
            LANE[r['lookup']] = LANE[r['name']]

missing, done = [], 0
for f in ['gijoe_research_spine.rul', 'gijoe_story_act1.rul', 'gijoe_research_captured.rul', 'gijoe_research_joe.rul']:
    p = os.path.join(RD, f)
    out, sec = [], None
    for line in open(p).read().split('\n'):
        if re.match(r'^[A-Za-z]\w*:', line):
            sec = line.split(':')[0]
        if sec == 'research' and re.match(r'^  lane: ', line):
            continue  # re-runs replace old lanes
        out.append(line)
        m = re.match(r'^- name: (STR_\w+)\s*$', line)
        if sec == 'research' and m and m.group(1) not in SKIP:
            n = m.group(1)
            if n in LANE:
                out.append('  lane: ' + LANE[n]); done += 1
            else:
                missing.append(n)
    open(p, 'w').write('\n'.join(out))
print('lanes written:', done)
if missing:
    sys.exit('NO LANE FOR: ' + ', '.join(missing))
