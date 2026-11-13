"""Batch 4 (STORY): retire the stock X-COM research tree without deleting anything (deleting breaks every stock rule
that still names a topic). A retired topic depends on STR_STORY_LOCK, so it never becomes available, and its own
unlocks/getOneFree are cleared. The 26 stock topics behind items and craft the mod reskins (pulse = plasma, lasers,
launchers, the Joe craft, defenses, psi lab, hyper-wave decoder) are KEPT for BUILD to re-link to the G.I. Joe topics."""
import yaml, json, sys, os
OUT = sys.argv[1]
HIDE = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'retire_list.json')))
R = [{'name': n, 'dependencies': ['STR_STORY_LOCK'], 'unlocks': [], 'getOneFree': []} for n in HIDE]
# prisoner topics: their stock getOneFree lists would hand out retired topics for free (getOneFree ignores dependencies)
for n in ['STR_COBRA_COMMANDER_UNIT', 'STR_DESTRO_UNIT', 'STR_VIPER_MEDIC', 'STR_STORM_SHADOW_UNIT', 'STR_COBRA_TROOPER']:
    R.append({'name': n, 'getOneFree': []})
for n in ['STR_VIPER_ENGINEER', 'STR_BAT_TERRORIST']:   # not in the spine; stop them unlocking retired topics
    R.append({'name': n, 'unlocks': [], 'getOneFree': []})
hdr = ('# STORY (Year 1 research + story), batch 4: the stock X-COM research tree, retired.\n'
       '# Nothing is deleted. Each retired topic depends on STR_STORY_LOCK (never researchable) and opens nothing, so it\n'
       '# never shows. Kept (BUILD to re-link to G.I. Joe topics): plasma = pulse weapons and clips, blaster, small\n'
       '# launcher, stun bomb, alien grenade (= Cobra Grenade, gijoe_research_captured.rul), mind probe, the three craft\n'
       '# topics, laser pistol/rifle/heavy/cannon, plasma cannon, fusion missile, laser and plasma defense, mind shield,\n'
       '# psi lab, hyper-wave decoder. Loads after gijoe_research_spine.rul: only the fields listed here change.\n')
open(os.path.join(OUT, 'gijoe_research_retire.rul'), 'w').write(hdr + yaml.dump({'research': R}, sort_keys=False, width=200))
print(len(R))
