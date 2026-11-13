"""ROSTER: one source for every named Joe's character data (Day-1 batch).
Writes:
  roster_day1.yaml                         the full records (for BUILD's installer now, the engine later)
  ../mod/Ruleset/gijoe_roster_text.rul     extraStrings only: names, ranks, specialties, traits, moves, voice lines
Stats come from statmodel.py (stats_day1.json). Owner: ROSTER (claude/status/ROSTER.md). Run: python3 gen_roster.py"""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
ST = json.load(open(os.path.join(HERE, 'stats_day1.json')))
K = ['tu', 'stamina', 'health', 'bravery', 'reactions', 'firing', 'throwing', 'strength', 'melee']
KS = ['TU', 'Sta', 'HP', 'Brav', 'React', 'Fire', 'Throw', 'Str', 'Melee']
RANKS = {'O-6': 'Colonel', 'O-3': 'Captain', 'O-2': 'First Lieutenant', 'E-9': 'Sergeant Major', 'E-8': 'Master Sergeant',
         'E-7': 'Sergeant First Class', 'E-6': 'Staff Sergeant', 'E-5': 'Sergeant', 'E-4': 'Corporal'}
EV = ['deploy', 'order', 'kill', 'hit', 'down', 'move']
# name, key, rank, primary, secondary, status, weapon text, armory ids, mastery, attachments, trait(name, text, engine), move(name, text, engine), bonds, grudges, voice(6), look
J = [
 ('Hawk', 'HAWK', 'O-6', 'Command', 'Comms & Tech', 'DAY1', 'M-16 rifle and M1911A1 pistol', ['W_RIFLE_J', 'W_PISTOL'], 'aimed shots > quick double shot > reaction-fire bonus', 'scope, under-barrel grenade launcher, bayonet, bipod',
  ('Command Post', 'When he deploys, Cobra positions are revealed for the first turn.', 'script'), ('Fire Mission', 'Calls an M.M.S. missile strike.', 'request'), [], ['Major Bludd (on his marked list)'],
  ['Positions. We go on my mark.', 'Execute.', 'One less.', "I'm fine. Stay on task.", 'Duke has command.', 'Fire mission, grid follows. Make it count.'], 'CAST; sprites rendering'),
 ('Duke', 'DUKE', 'E-8', 'Command', None, 'DAY1', 'M-32 submachine gun and binoculars', ['W_SMG'], 'spray control > fire on the move > close-quarters bonus', 'suppressor, folding stock, weapon light, red dot',
  ('Field Leadership', 'Joes near him hold their nerve and aim better.', 'script'), ('Yo Joe!', 'Every Joe in sight gets extra movement this turn.', 'request'), ['Lt. Falcon (half-brother): Falcon gets his leadership at double strength'], ['Major Bludd (on his marked list)'],
  ["Spread out. Eyes open. Nobody's a hero today.", "Move. I've got your back.", 'Target down. Next.', 'Just a scratch. Keep moving.', "Get the squad out. That's an order.", 'Yo Joe! On me!'], 'in game (STR_DUKE / STR_DUKE_UC)'),
 ('Roadblock', 'ROADBLOCK', 'E-6', 'Heavy Weapons', None, 'DAY1', 'M-2X machine gun (.50 cal on tripod)', ['W_HMG'], 'suppression > walking fire > sustained fire (2 turns)', 'tripod (must deploy), ammo box',
  ('.50 Cal Suppression', 'A burst pins the target, cutting its next turn\'s actions.', 'script'), ('Full Belt', 'Pins every Cobra in an area.', 'request'), ['Heavy Duty (cousin): both suppress better side by side'], [],
  ['Set me down somewhere with a view.', "Rollin'. Slowly.", "Should've stayed home.", "That's gonna leave a mark.", 'Somebody watch my stew.', 'Full belt, coming through!'], 'in game as STR_SOLDIER + STR_ROADBLOCK_UC (to become STR_ROADBLOCK)'),
 ("Rock 'n Roll", 'ROCK_N_ROLL', 'E-7', 'Heavy Weapons', None, 'DAY1', 'M-60 machine gun', ['W_LMG'], 'suppression > walking fire > sustained fire (2 turns)', 'bipod, tripod, ammo belt',
  ('Sustained Fire', 'Longer machine-gun bursts.', 'native'), ('Rock and Roll', 'Sustained fire over two turns.', 'request'), [], [],
  ["Let's make some noise.", 'Moving. Try to keep up.', 'Wipeout.', 'Ow. Rude.', 'Somebody keep that gun warm.', 'Rock and roll!'], 'CAST; sprites rendering'),
 ('Grand Slam', 'GRAND_SLAM', 'E-5', 'Heavy Weapons', 'Comms & Tech', 'DAY1', 'Laser rifle', ['W_LASER_R'], 'faster battery swap > burn-through shot > overcharge shot', 'extended battery, scope',
  ('Forward Observer', 'Calls in artillery on a spotted target.', 'script'), ('Jump Strike', 'J.U.M.P. jet-pack hop across the map, firing his laser on landing.', 'request'), [], [],
  ['Coordinates logged.', 'Plotting a route. A high one.', 'Splash one.', 'Hit. Still airborne.', "Jet pack's done. So am I.", 'Range is just a question of how far you jump.'], 'REGJOE; sheet held for BUILD go'),
 ('Short-Fuze', 'SHORT_FUZE', 'E-6', 'Heavy Weapons', 'Demolitions & Engineering', 'WAITING', 'M-1 81mm mortar', ['W_MORTAR'], 'ranging shot > walking barrage > fire for effect', 'baseplate, smoke rounds',
  ('Mortar', 'Indirect fire over cover.', 'native'), ('Walking Barrage', 'Three mortar rounds along a line of tiles in one turn.', 'request'), [], [],
  ['Baseplate down.', 'Relocating the tube.', 'On target.', "Watch it, I'm holding explosives.", 'Somebody spot for me.', 'Walking it in. Heads down.'], 'NO LOOK (CAST parked); roster WAITING (John 21:31)'),
 ('Zap', 'ZAP', 'E-4', 'Heavy Weapons', 'Demolitions & Engineering', 'DAY1', 'Bazooka', ['W_ROCKET'], 'steady aim > anti-armor shot > double load', 'optical sight, extra rockets',
  ('Bazooka', 'Extra damage against plating and vehicles.', 'native'), ('Bunker Buster', 'A rocket that destroys a wall section, exposing everyone behind it.', 'request'), [], [],
  ['Who ordered the big one?', 'Moving. Mind the backblast.', 'That wall had it coming.', 'Okay, that one stung.', "Bazooka's yours. Use it well.", 'Fire in the hole!'], 'CAST; sprites rendering'),
 ('Grunt', 'GRUNT', 'E-5', 'Infantry', None, 'DAY1', 'M-16', ['W_RIFLE_J'], 'aimed shots > quick double shot > reaction-fire bonus', 'scope, under-barrel grenade launcher, bayonet, bipod',
  ('Steady', 'Strong reaction fire; the dependable rifleman.', 'native'), ('Covering Fire', 'Reaction fire for the whole squad.', 'request'), [], [],
  ['In position.', 'Moving up.', 'Got him.', "I'm hit. Still shooting.", 'Hold the line without me.', "I've got you covered. All of you."], 'CAST; first game sheet shipped 17:48'),
 ('Stalker', 'STALKER', 'E-9', 'Infantry', 'Command', 'DAY1', 'M-32 "Pulverizer" submachine gun', ['W_SMG'], 'spray control > fire on the move > close-quarters bonus', 'suppressor, folding stock, weapon light, red dot',
  ('Ranger Lead', 'His squad gets extra movement on the first turn.', 'script'), ('Ranger Ambush', 'His squad fires first in the first turn.', 'request'), [], [],
  ['Rangers lead the way.', 'Low and quiet. Go.', 'Clear.', 'Took one. Keep moving.', 'Get them home, Grunt.', 'We were here first.'], 'CAST; sprites rendering'),
 ('Breaker', 'BREAKER', 'E-5', 'Comms & Tech', None, 'DAY1', 'Rifle and radio', ['W_RIFLE_J'], 'aimed shots > quick double shot > reaction-fire bonus', 'scope, under-barrel grenade launcher, bayonet, bipod',
  ('Radio Net', 'Every Joe on the map shares what any Joe sees.', 'script'), ('Intercept', 'Reveals every Cobra on the map for one turn.', 'request'), [], [],
  ['Comms are up.', 'On the move, still on channel.', 'Scratch one.', "Hit! Radio's fine.", 'Somebody grab the radio!', "If they're talking, I'm listening."], 'CAST; sprites rendering'),
 ('Flash', 'FLASH', 'E-5', 'Comms & Tech', None, 'DAY1', 'XMLR-1A laser rifle', ['W_LASER_R'], 'faster battery swap > burn-through shot > overcharge shot', 'extended battery, scope',
  ('Laser Rifle', 'One of two Joes, with Grand Slam, carrying an energy weapon from Day 1.', 'native'), ('Overcharge', 'A laser shot that burns through any plating.', 'request'), [], [],
  ["Battery's full.", 'Moving. Mind the cable.', 'Lights out.', "Hey! That's my good side.", "Don't let them take the rifle.", 'Overcharging. Stand back.'], 'CAST; sprites rendering'),
 ('Scarlett', 'SCARLETT', 'E-5', 'Covert Ops & Intel', 'Martial Arts', 'DAY1', 'XK-1 power crossbow', ['W_CROSSBOW'], 'silent shot > multi-bolt > triple bolt', 'explosive bolts, scope',
  ('Crossbow', "Silent shots that don't give away her position.", 'script'), ('Triple Bolt', 'Three silent bolts at up to three targets.', 'request'), ['Snake Eyes (romance): each fights harder if the other goes down'], ['Baroness (canon rivalry)'],
  ["Eyes on. Nobody's seen me.", 'Moving. Quietly.', 'Down. Not a sound.', "Hit. I've had worse.", 'Get the intel out. Not me. The intel.', 'Three bolts. Three problems solved.'], 'CAST v2; sprites rendering'),
 ('Snake Eyes', 'SNAKE_EYES', 'E-8', 'Martial Arts', None, 'DAY1', 'Mini-Uzi and ninja sword', ['W_SMG', 'W_SWORD'], 'Uzi: spray control > fire on the move > close-quarters bonus; sword: silent strike > strike from hiding > whirlwind', 'Uzi: suppressor, folding stock, weapon light, red dot',
  ('Silent Killer', "Moves silently; melee kills don't alert nearby Cobra. With Timber, his wolf, who scouts and fights beside him.", 'script'), ('Shadow Strike', "He and Timber attack unseen in one turn; the player picks Timber's target.", 'request'), ['Scarlett (romance): each fights harder if the other goes down', 'Jinx (mentor): she moves silently near him', 'Storm Shadow after the defection (blood brothers): silent kills by one keep the other hidden'], ['Storm Shadow while he is Cobra (canon rivalry)'],
  ['[signals: two fingers, then forward]', '[a nod]', '[sheathes the sword]', '[says nothing]', '[Timber stands over him]', "[Timber's growl, then nothing]"], 'in game (STR_SNAKE_EYES / STR_SNAKE_EYES_UC); Timber: no look'),
 ('Doc', 'DOC', 'O-3', 'Medic', None, 'DAY1', 'Rescue flare launcher (non-lethal) and stretcher', ['W_FLARE'], 'illuminate > signal for evac > smoke and flare', 'none',
  ('Battlefield Surgeon', 'Revives a downed Joe in one action with more health.', 'script'), ('Field Surgery', 'Fully revives a downed Joe.', 'request'), [], [],
  ['Medic up. Who needs me?', 'Coming through.', '[he does not celebrate]', "I'm fine. Help him first.", 'Keep pressure on it. You know what to do.', "Stay down. I'm coming to you."], 'CAST; sprites rendering'),
 ('Ace', 'ACE', 'O-3', 'Pilot', None, 'DAY1', 'Sidearm (M1911)', ['W_PISTOL'], 'quick draw > fire after moving > double tap', 'suppressor, extended magazine, laser sight',
  ('Ace', 'Craft he flies hit harder and dodge more in interceptions.', 'native'), ('Strafing Run', 'Once per mission, if a Skystriker is in service, one strafing pass along a line of tiles. (Air: Ace Maneuver, dodges every shot in one dogfight round.)', 'request'), [], [],
  ['Deal me in.', 'Taxiing.', 'Splash one.', 'Just a scratch on the paint.', 'Get me back in a cockpit.', 'Watch this.'], 'in game (STR_ACE / STR_ACE_UC)'),
 ('Airborne', 'AIRBORNE', 'E-7', 'Airborne', 'Medic', 'DAY1', 'XM-16 attack rifle with bayonet', ['W_CARBINE'], 'aimed shots > quick double shot > reaction-fire bonus', 'bayonet, scope, under-barrel grenade launcher',
  ('Paradrop', 'Can deploy away from the landing zone.', 'script'), ('Drop In', 'Paradrop next to any Cobra unit.', 'request'), [], [],
  ['Green light.', 'Moving.', 'Target down.', 'Hit. Keep going.', "Go on. I'll catch up.", 'Look up.'], 'CAST; sprites rendering'),
]
SPEC = sorted({j[3] for j in J} | {j[4] for j in J if j[4]} | set(ST['unnamed']))
def skey(s): return re.sub(r'[^A-Z0-9]+', '_', s.upper()).strip('_')
def q(s): return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
recs, strings = [], {}
for (nm, key, rk, pri, sec, status, wtxt, wids, mast, att, tr, mv, bonds, grudges, voice, look) in J:
    s = ST['named'][nm]['stats']; assert ST['named'][nm]['rank'] == rk
    rank_key = 'STR_GJR_RANK_' + skey(RANKS[rk]); strings[rank_key] = RANKS[rk]
    strings['STR_' + key] = nm
    strings[f'STR_GJR_TRAIT_{key}'] = tr[0]; strings[f'STR_GJR_TRAIT_{key}_DESC'] = tr[1]
    strings[f'STR_GJR_MOVE_{key}'] = mv[0]; strings[f'STR_GJR_MOVE_{key}_DESC'] = mv[1]
    for e, line in zip(EV, voice): strings[f'STR_GJR_VOICE_{key}_{e.upper()}'] = line
    recs.append(dict(id='C_' + key, name=nm, soldierType='STR_' + key, rosterStatus=status, rank=rk, rankString=rank_key,
        allowPromotion=False, costBuy=0, primary='STR_GJR_SPEC_' + skey(pri), secondary=('STR_GJR_SPEC_' + skey(sec)) if sec else None,
        stats={k: s[ks] for k, ks in zip(K, KS)} | {'psiStrength': 0, 'psiSkill': 0},
        weapon=dict(name=wtxt, armory=wids, mastery=mast, attachments=att),
        trait=dict(name=f'STR_GJR_TRAIT_{key}', desc=f'STR_GJR_TRAIT_{key}_DESC', engine=tr[2]),
        move=dict(name=f'STR_GJR_MOVE_{key}', desc=f'STR_GJR_MOVE_{key}_DESC', engine=mv[2], perMission=1),
        bonds=bonds, grudges=grudges, voice={e: f'STR_GJR_VOICE_{key}_{e.upper()}' for e in EV},
        dossier=f'STR_ART_{key}_TEXT (generated in the design repo, not yet wired)', look=look))
for sp in SPEC: strings['STR_GJR_SPEC_' + skey(sp)] = sp
unn = {('STR_GJR_SPEC_' + skey(p)): dict(name=p, start={k: d['start'][ks] for k, ks in zip(K, KS)}, cap={k: d['cap'][ks] for k, ks in zip(K, KS)})
       for p, d in ST['unnamed'].items()}
# roster_day1.yaml (plain YAML, written by hand-rolled emitter to keep key order)
def y(v, ind):
    p = '  ' * ind
    if isinstance(v, dict):
        return ''.join(f"\n{p}{k}:" + (' ' + y(x, ind + 1) if not isinstance(x, (dict, list)) or not x else y(x, ind + 1)) for k, x in v.items())
    if isinstance(v, list):
        if not v: return '[]'
        return ''.join(f"\n{p}- " + (y(x, ind + 1).lstrip('\n').lstrip() if isinstance(x, dict) else y(x, ind + 1)) for x in v)
    if v is None: return 'null'
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, (int, float)): return str(v)
    return q(str(v))
with open(os.path.join(HERE, 'roster_day1.yaml'), 'w') as f:
    f.write('# ROSTER data, Day-1 Joes (generated by gen_roster.py - edit the script, not this file).\n'
            '# Named Joes: stats fixed for the game (John 12 Nov 21:13): minStats = maxStats = statCaps = stats; allowPromotion false; costBuy 0 (not hireable).\n'
            '# Unnamed Joes by specialty: roll around start, grow to cap (cap = 78% of the specialty template; John 21:16).\n'
            '# Text keys resolve in mod/Ruleset/gijoe_roster_text.rul.\n')
    f.write('named:' + y(recs, 1) + '\nunnamed:' + y(unn, 1) + '\n')
# text ruleset
with open(os.path.join(HERE, '..', 'mod', 'Ruleset', 'gijoe_roster_text.rul'), 'w') as f:
    f.write('# ROSTER text (generated by tools/oxce-4x/roster/gen_roster.py - edit the script, not this file).\n'
            '# Strings only: soldier names, canon ranks, specialties, signature traits and moves, voice lines.\n'
            '# Owner: ROSTER (claude/status/ROSTER.md). Data: tools/oxce-4x/roster/roster_day1.yaml.\nextraStrings:\n  - type: en-US\n    strings:\n')
    for k in sorted(strings):
        if k in ('STR_' + j[1] for j in J): continue      # soldier-type names are BUILD's (en-US.yml)
        f.write(f'      {k}: {q(strings[k])}\n')
print('records', len(recs), 'strings', len(strings), 'unnamed', len(unn))
