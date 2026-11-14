"""Year 1 research pacing check (STORY). Day by day: scientists hired and labs built per strategy, topics researched in
a priority order once their prerequisites and items exist, money tracked. Reports when each topic lands vs the map's
estimate. All economy numbers are stated assumptions, not game data unless marked."""
import yaml, json, sys, collections, os
RD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mod', 'Ruleset', '')
T = {}
for f in ['gijoe_research_spine.rul', 'gijoe_story_act1.rul', 'gijoe_research_captured.rul', 'gijoe_research_joe.rul']:
    d = yaml.safe_load(open(RD + f)); S = d['extraStrings'][0]['strings']
    for r in d['research']:
        if r['name'] == 'STR_STORY_LOCK': continue
        T[r['name']] = dict(r, disp=S.get(r.get('lookup') or r['name']) or S.get(r['name']) or 'Cobra Ledgers', file=f)
unlocked_by = collections.defaultdict(list)
for k, r in T.items():
    for u in r.get('unlocks', []): unlocked_by[u].append(k)
DONE0 = {'STR_STANDARD_ISSUE', 'STR_STANDARD_EXPLOSIVES', 'STR_STANDARD_FATIGUES', 'STR_FIELD_MEDICINE', 'STR_BREACHING_SHOTGUN', 'STR_RUMOURED_TERROR_GROUP'}
# month an item / prisoner first reaches the player (estimate from the Act 1 outline + escalation calendar)
# Cartel arc (John 13 Nov 02:38): the factory comes after a month-long lead, so the Cobra beats shift about a month later
ITEM_MONTH = {'STR_CARTEL_LEDGER': .1, 'STR_CRATE_SERIAL_PLATE': .1, 'STR_COBRA_STENCIL': .1, 'STR_CARTEL_BOSS': .1,
 'STR_INFORMANT_TIP': .6, 'STR_ROBBERY_LEADER': .85, 'STR_GETAWAY_PAPERS': 99, 'STR_CARTEL_LOGBOOK': 99,
 'STR_FACTORY_SCHEDULE': 1.5, 'STR_BROADCAST_RECORDING': 1.8, 'STR_COBRA_TROOPER': 2.5, 'STR_COBRA_REVOLVER': 2.5, 'STR_CORPSE_TROOPER': 2.5,
 'STR_COBRA_LEDGERS': 2.3, 'STR_SHIPPING_MANIFEST': 2.5, 'STR_PILOT_LOGBOOK': 3.5, 'STR_BLUDD_CALLING_CARD': 3.8,
 'STR_FANG_WRECKAGE': 2.5, 'STR_COBRA_RIFLE': 4.5, 'STR_ALIEN_GRENADE': 4.8, 'STR_VULTURE_PARTS': 4.5, 'STR_STINGER_WRECKAGE': 5,
 'STR_VIPER_PILOT': 5, 'STR_COBRA_OFFICER': 5.5, 'STR_VIPER_MEDIC': 6, 'STR_COBRA_FIELD_KIT': 6, 'STR_RATTLER_WRECKAGE': 7,
 'STR_DEPOT_RECORDS': 8, 'STR_HISS_WRECKAGE': 10, 'STR_ARASHIKAGE': 10.5, 'STR_TERROR_DROME_PLANS': 10.5, 'STR_MARS_MARKED_WEAPON': 11.8,
 'STR_RADIO_CODEBOOK': 3, 'STR_FUEL_RECEIPTS': 2, 'STR_VEHICLE_REGISTRATION': 2, 'STR_MATCHBOOK': 1, 'STR_PHONE_NUMBER': 1,
 'STR_BURNED_PAPERS': 2, 'STR_CIRCLED_MAP': 4, 'STR_BANDED_CASH': 1, 'STR_BILL_OF_LADING': 5, 'STR_TICKET_STUB': 2,
 'STR_NOTICE_BOARD_ORDERS': 4, 'STR_COBRA_PIN': 1.5, 'STR_PHOTOGRAPHS': 4}
# the map's month estimates (midpoints) for the story / captured topics
EST = {'STR_CARTEL_LEDGER': 0, 'STR_WHO_IS_COBRA': 0.5, 'STR_FACTORY_REACTIVATION_DATE': .5, 'STR_BROADCAST_RECORDING': 1.75,
 'STR_CARTEL_FLIGHT_ROUTE': .3, 'STR_INFORMANT_TIP': .7, 'STR_BORDER_BANK_TRACE': 1.1,
 'STR_COBRA_TROOPER': 2.5, 'STR_COBRA_ORDER_OF_BATTLE': 2, 'STR_EXTENSIVE_ENTERPRISES': 3, 'STR_BLUDD_CALLING_CARD': 4,
 'STR_VIPER_PILOT': 6, 'STR_FANG_OPERATING_BASES': 6, 'STR_COBRA_OFFICER': 6.5, 'STR_COBRA_FLIGHT_ROUTES': 7.5,
 'STR_VIPER_MEDIC': 7.5, 'STR_COBRA_DEPOTS': 8.5, 'STR_TERROR_DROME_RUMOURS': 9.5, 'STR_TERROR_DROME_PLANS': 11,
 'STR_MARS_MARKED_WEAPON': 12, 'STR_ARASHIKAGE': 11, 'STR_COBRA_RIFLE': 6, 'STR_ALIEN_GRENADE': 6, 'STR_RATTLER_WRECKAGE': 9,
 'STR_HISS_WRECKAGE': 10.5, 'STR_SKYSTRIKER_MK2': 10, 'STR_TOMAHAWK': 8, 'STR_C130_HERCULES': 3, 'STR_SKYSTRIKER': 3}
# Hawk's order for Joe research (the player will differ; this is a sensible one)
JOE_ORDER = ['STR_KEVLAR_VEST', 'STR_AP_ROUNDS', 'STR_FIELD_RADIO', 'STR_VAMP', 'STR_C130_HERCULES', 'STR_RADAR_ROOM', 'STR_NIGHT_VISION',
 'STR_SKYSTRIKER', 'STR_DETENTION_BLOCK', 'STR_C4_DEMOLITIONS', 'STR_CONCUSSION_GRENADE', 'STR_MATCH_GRADE_OPTICS', 'STR_TOMAHAWK',
 'STR_MOBAT', 'STR_SQUAD_AUTOMATIC_WEAPON', 'STR_MMS', 'STR_COMBAT_STIMS', 'STR_TRAUMA_KIT', 'STR_SIGNALS_INTELLIGENCE_CENTER',
 'STR_AIR_COMBAT_DOCTRINE', 'STR_SKYSTRIKER_MK2', 'STR_JOE_COBRA_GRENADE', 'STR_INFIRMARY', 'STR_AVALANCHE_MISSILE', 'STR_FLAK',
 'STR_BATTLE_STATIONS', 'STR_WATCH_TOWER', 'STR_INCENDIARY_ROUNDS', 'STR_GHILLIE_SUIT', 'STR_LONG_RANGE_RADAR', 'STR_VAMP_MK2',
 'STR_RAM', 'STR_WOLVERINE', 'STR_DRAGONFLY', 'STR_MANTA', 'STR_SKY_HAWK', 'STR_LASER_GUIDED_ROCKETS', 'STR_THERMITE',
 'STR_CLAYMORE_MINES', 'STR_MUDFIGHTER', 'STR_ARCTIC_GEAR', 'STR_NINJA_GEAR', 'STR_JUMP_JET_PACK', 'STR_PAC_RATS',
 'STR_MOUNTAIN_HOWITZER', 'STR_SLUGGER', 'STR_HAL', 'STR_POLAR_BATTLE_BEAR', 'STR_SNOW_CAT', 'STR_TWIN_BATTLE_GUN',
 'STR_ANTI_AIRCRAFT_GUN', 'STR_SHARC', 'STR_SONAR_SUITE', 'STR_DEVILFISH', 'STR_STOP_AND_SEARCH', 'STR_KILLER_WHALE',
 'STR_FALCON_GLIDER', 'STR_BIVOUAC']
JOE_ORDER += [k for k, r in T.items() if r['file'] == 'gijoe_research_joe.rul' and k not in JOE_ORDER and k not in DONE0]
# ECONOMY (assumptions; BUILD/DESIGN own the real numbers)
import os
W=float(os.environ.get('WAGE','1.0'))
ECON = dict(start=4.0e6, funding=float(os.environ.get('FUND','1.0'))*1e6, other_income=0.4e6,          # raids, sold loot: estimate
            soldiers=24 * 20000 * W, engineers=10 * 25000 * W, sci_salary=30000 * W, sci_hire=60000 * W,
            upkeep=0.2e6, lab=(750000, 26, 30000), quarters=(400000, 16, 10000), base_staff_room=20)
# Facility numbers (John 23:48 OK'd claude/FACILITY_STATS_v1.md): Day 1 Lab Bench seats 10; a Lab seats 25 for $375k,
# 20 days, $15k/month; staff housing on Day 1 = the Command Center's 20 (full with 10 scientists + 10 engineers);
# more housing = a Barracks, 24 people for $150k, 10 days, $4k/month. FAC=0 reruns the old stock-X-COM assumption.
FAC = os.environ.get('FAC', '1') == '1'
if FAC:
    ECON.update(lab=(375000, 20, 15000), quarters=(150000, 10, 4000))
LAB_START, LAB_ADD = (10, 25) if FAC else (50, 50)
HOUSE_START, HOUSE_ADD = (20, 24) if FAC else (30, 50)
# Analysts (John 13 Nov 02:05): staff like scientists who research every INTEL-lane topic; scientists do the rest.
# Day 1: 10 analysts, 10 seats (Computer Station); each Computer Banks / Archives / Situation Analysis adds 6 seats.
# Same pay as scientists. Housing: the Command Center grows to 24 to house them. ANALYSTS=0 = the old model.
ANALYSTS = os.environ.get('ANALYSTS', '1') == '1'
AN_ROOM = (300000, 16, 10000)
AN_TARGET = {'cautious': {0: 4, 6: 6}, 'typical': {0: 4, 2: 8, 6: 12}, 'aggressive': {0: 4, 1: 8, 4: 14}}
AN0 = int(os.environ.get('AN0', '10'))   # John 02:10: 10 analysts on Day 1, regular-size intel topics
INTEL_SCALE = float(os.environ.get('INTEL_SCALE', '1.0'))
if ANALYSTS: HOUSE_START += AN0
FUNDS_SCALE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
ECON['other_income'] = float(sys.argv[2]) * 1e6 if len(sys.argv) > 2 else ECON['other_income']
STRATS = {  # target scientists by month; second lab when targets pass 50
 'cautious':   {0: 10, 3: 15, 6: 20, 9: 25},
 'typical':    {0: 10, 1: 15, 2: 20, 4: 30, 6: 40, 9: 50},
 'aggressive': {0: 10, 1: 20, 2: 30, 4: 50, 6: 70, 9: 90}}
PARALLEL, PER_PROJECT = 4, 20
# Department rooms (13 Nov, John 18:04-18:25; DEPARTMENT_HEADS_DESIGN_v1): a lane's topics can't start until its room exists.
# Day 1 base = the Bare 5, so COMMAND, ARMORY and MOTOR_POOL are open; the rest are built by the player the day a topic in
# that lane is first ready (cost, days). ROOMGATE=0 = the old model, every lane open from Day 1.
ROOMGATE = os.environ.get('ROOMGATE', '1') == '1'
LANE_ROOM = {'INTEL': (80000, 8), 'COMMS': (100000, 8), 'MEDICAL': (60000, 6), 'AIR_WING': (200000, 25)}
# Story-locked topics granted by an event (month): Clutch's VAMP (rescue + junkyard, John 13 Nov 17:10).
GRANT = {'STR_VAMP_RECOVERED': float(os.environ.get('VAMP_MONTH', '2.5'))}     # projects worked at once; scientists usefully on one project

def run(strat):
    target = STRATS[strat]; day = 0; cash = ECON['start']; sci = 10; labs = LAB_START; rooms = HOUSE_START; nlab_built = 0; nq_built = 0
    an = AN0 if ANALYSTS else 0; an_seats = AN0; nan_built = 0
    open_lanes = set(T[k].get('lane') for k in T) if not ROOMGATE else {'COMMAND', 'ARMORY', 'MOTOR_POOL', None}; rooms_wanted = set(); room_day = {}
    done = {k: 0.0 for k in DONE0}; prog = collections.defaultdict(float); paid = set(); building = []; spent = collections.Counter()
    def tgt(m): return max(v for mm, v in target.items() if mm <= m)
    def avail(k):
        r = T[k]
        if k in done: return False
        if r.get('needItem') and ITEM_MONTH.get(k, 99) > day / 30: return False
        deps = [d for d in r.get('dependencies', []) if d != 'STR_STORY_LOCK']
        if 'STR_STORY_LOCK' in r.get('dependencies', []):
            ok = any(u in done for u in unlocked_by[k]) or GRANT.get(k, 99) <= day / 30
        else:
            ok = all(d in done for d in deps) or any(u in done for u in unlocked_by[k])
        if ok and r.get('lane') not in open_lanes:
            rooms_wanted.add(r.get('lane')); return False
        return ok
    order = [k for k, r in T.items() if r['file'] != 'gijoe_research_joe.rul'] + JOE_ORDER   # intel/story first
    order = [k for k in order if k in T]
    low_cash_days = 0
    while day < 365:
        m = day / 30
        # finish construction
        for b in list(building):
            if b[1] <= day:
                building.remove(b)
                if b[0] == 'lab': labs += LAB_ADD; nlab_built += 1
                elif b[0] == 'an': an_seats += 6; nan_built += 1
                else: rooms += HOUSE_ADD; nq_built += 1
        # department rooms: build the room the day its lane is first wanted
        for ln in list(rooms_wanted):
            if ln in LANE_ROOM and ln not in room_day and cash > LANE_ROOM[ln][0]:
                room_day[ln] = day + LANE_ROOM[ln][1]; cash -= LANE_ROOM[ln][0]; spent['department rooms'] += LANE_ROOM[ln][0]
        for ln, d in room_day.items():
            if d <= day: open_lanes.add(ln)
        rooms_wanted.clear()
        # hire / build toward the target
        want = tgt(m)
        if ANALYSTS:
            awant = max(v for mm, v in AN_TARGET[strat].items() if mm <= m)
            while an < awant and sci + 10 + an < rooms and an < an_seats and cash > ECON['sci_hire'] + 1e6:
                an += 1; cash -= ECON['sci_hire']; spent['hiring'] += ECON['sci_hire']
            if awant > an_seats and not any(b[0] == 'an' for b in building) and cash > AN_ROOM[0] + 1e6:
                building.append(('an', day + AN_ROOM[1])); cash -= AN_ROOM[0]; spent['intel rooms'] += AN_ROOM[0]
            if awant + want + 10 > rooms and not any(b[0] == 'q' for b in building) and cash > ECON['quarters'][0] + 1e6:
                building.append(('q', day + ECON['quarters'][1])); cash -= ECON['quarters'][0]; spent['quarters'] += ECON['quarters'][0]
        while sci < want and sci + 10 + an < rooms and sci < labs and cash > ECON['sci_hire'] + 1e6:
            sci += 1; cash -= ECON['sci_hire']; spent['hiring'] += ECON['sci_hire']
        if want + 10 > rooms and not any(b[0] == 'q' for b in building) and cash > ECON['quarters'][0] + 1e6:
            building.append(('q', day + ECON['quarters'][1])); cash -= ECON['quarters'][0]; spent['quarters'] += ECON['quarters'][0]
        if want > labs and not any(b[0] == 'lab' for b in building) and cash > ECON['lab'][0] + 1e6:
            building.append(('lab', day + ECON['lab'][1])); cash -= ECON['lab'][0]; spent['labs'] += ECON['lab'][0]
        # research: up to PARALLEL projects in priority order
        active = []
        for k in order:
            if len(active) >= PARALLEL: break
            if not avail(k): continue
            f = T[k].get('costFunds', 0) * FUNDS_SCALE
            if k not in paid:
                if f > 0 and cash < f: continue
                cash -= f; paid.add(k); spent['research money'] += f
            active.append(k)
        intel = [k for k in active if ANALYSTS and T[k].get('lane') == 'INTEL']
        rest = [k for k in active if k not in intel]
        for k in active:
            n = (an / max(1, len(intel))) if k in intel else (sci / max(1, len(rest)))
            prog[k] += n
            if prog[k] >= T[k]['cost'] * (INTEL_SCALE if k in intel else 1): done[k] = day / 30
        # money, daily slice of the month
        monthly = ECON['funding'] + ECON['other_income'] - ECON['soldiers'] - ECON['engineers'] - (sci + an) * ECON['sci_salary'] - nan_built * AN_ROOM[2] \
                  - ECON['upkeep'] - nlab_built * ECON['lab'][2] - nq_built * ECON['quarters'][2]
        cash += monthly / 30
        if cash < 0: low_cash_days += 1
        day += 1
    done['_rooms'] = {ln: round(d / 30, 2) for ln, d in room_day.items()}
    return done, dict(sci=sci, analysts=an, intel_rooms=nan_built, lab_seats=labs, labs_built=nlab_built, cash=round(cash / 1e6, 2), spent={k: round(v / 1e6, 2) for k, v in spent.items()},
                      broke_days=low_cash_days, monthly_at_end=round(monthly / 1e6, 2))
out = {}
for s in STRATS:
    done, info = run(s); out[s] = (done, info)
    print(s, info, 'rooms open (month):', done.get('_rooms'))
print()
print(f"{'topic':38s} {'est':>5s} " + ' '.join(f'{s:>10s}' for s in STRATS))
keys = [k for k in EST] + [k for k in JOE_ORDER[:20] if k not in EST]
rows = []
for k in keys:
    if k not in T: continue
    vals = [out[s][0].get(k) for s in STRATS]
    rows.append((T[k]['disp'], EST.get(k), vals))
    print(f"{T[k]['disp'][:38]:38s} {('' if EST.get(k) is None else EST[k]):>5} " + ' '.join(f"{('never' if v is None else round(v,1)):>10}" for v in vals))
nd = {s: sum(1 for k in T if k not in out[s][0] and k not in DONE0 and T[k]['file'] == 'gijoe_research_joe.rul') for s in STRATS}
print('Joe topics not reached in Year 1:', nd)
json.dump({'rows': rows, 'info': {s: out[s][1] for s in STRATS}, 'notdone': nd, 'strats': list(STRATS)}, open('pacing.json', 'w'))
