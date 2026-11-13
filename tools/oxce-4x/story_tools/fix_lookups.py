"""OXCE needs every research `lookup:` to name a RESEARCH topic (RuleResearch::afterLoad -> linkRule), not just a
Ufopaedia article. BUILD found 16 lookups that named only an Intel File article, which stopped the game loading
(12 Nov 21:50). This adds a stub research topic for each such lookup: cost 1, no points, behind STR_STORY_LOCK so it
is never researchable on its own; it is discovered only when its parent finishes (that is what lookup does), and it
opens the Intel File article of the same name. `lookupOnly: true` tells the research tree screen not to draw it.
Run after the gen_batch scripts and BEFORE add_lanes.py:  python3 fix_lookups.py <Ruleset dir>"""
import os, re, sys, glob, json, yaml

RD = sys.argv[1]
MINE = ['gijoe_research_spine.rul', 'gijoe_story_act1.rul', 'gijoe_research_captured.rul', 'gijoe_research_joe.rul']
HERE = os.path.dirname(os.path.abspath(__file__))

known = set(json.load(open(os.path.join(HERE, 'stock_research_names.json'))))
for p in glob.glob(os.path.join(RD, '*.rul')):
    try:
        d = yaml.safe_load(open(p)) or {}
    except Exception:
        continue
    for r in d.get('research') or []:
        if isinstance(r, dict) and r.get('name'):
            known.add(r['name'])

added = 0
for f in MINE:
    p = os.path.join(RD, f)
    text = open(p).read()
    d = yaml.safe_load(text)
    need = []
    for r in d.get('research') or []:
        L = r.get('lookup')
        if L and L != r['name'] and L not in known and L not in need:
            need.append(L)
    if not need:
        continue
    block = ''.join(f"- name: {n}\n  cost: 1\n  points: 0\n  dependencies:\n  - STR_STORY_LOCK\n  unlocks: []\n  lookupOnly: true\n" for n in need)
    lines = text.split('\n'); out = []; sec = None; done = False
    for line in lines:
        if re.match(r'^[A-Za-z]\w*:', line):
            if sec == 'research' and not done:
                out.extend(block.rstrip('\n').split('\n')); done = True
            sec = line.split(':')[0]
        out.append(line)
    if not done:
        sys.exit('no section after research in ' + f)
    open(p, 'w').write('\n'.join(out))
    known.update(need); added += len(need)
    print(f, 'stubs:', ', '.join(need))
print('lookup stubs added:', added)
