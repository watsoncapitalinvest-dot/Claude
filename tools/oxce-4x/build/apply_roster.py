#!/usr/bin/env python3
"""ROSTER's character records -> the soldier types in the game (SHORTCUTS #5).

    python3 build/apply_roster.py

Reads tools/oxce-4x/roster/roster_*.yaml (ROSTER's generated data, never hand-edited) and rewrites, in place,
every matching soldier block in the mod's soldier rulesets (gijoe_soldiers.rul, gijoe_body_sheets.rul):

  named Joe:  minStats = maxStats = statCaps = his record's stats (fixed for the whole game, John 12 Nov 21:13)
              allowPromotion: false and rankStrings: [his canon rank] (no promotions; rank 0 shows that string)
  unnamed:    minStats = start - 5 (bravery - 10), maxStats = start, statCaps = cap, for the specialty that
              soldier type stands for (UNNAMED below)

ROSTER's README contract (tools/oxce-4x/roster/README.md, brief 2.1). install_body_sheets.py calls this at the
end, so regenerating the sheets never puts the placeholder stats back. A record whose soldier type is not in
the game yet (Clutch, Slaughter, the navy Joes) is reported and skipped.
"""
import glob
import os
import re
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.normpath(os.path.join(HERE, '..'))
RULES = [os.path.join(TOOLS, 'mod', 'Ruleset', f) for f in ('gijoe_soldiers.rul', 'gijoe_body_sheets.rul')]
# the record's soldier type -> the type the game actually uses for him
ALIAS = {'STR_ROADBLOCK': 'STR_SOLDIER'}
# unnamed soldier types -> the specialty in ROSTER's unnamed table
UNNAMED = {'STR_REGULAR_JOE': 'STR_GJR_SPEC_INFANTRY', 'STR_JOE_PILOT': 'STR_GJR_SPEC_PILOT',
           'STR_JOE_MEDIC': 'STR_GJR_SPEC_MEDIC'}
KEYS = ['tu', 'stamina', 'health', 'bravery', 'reactions', 'firing', 'throwing', 'strength', 'psiStrength', 'psiSkill', 'melee']


def flow(d):
    return '{' + ', '.join(f'{k}: {int(d.get(k, 0))}' for k in KEYS) + '}'


def patch_block(body, mn, mx, cap, rank=None):
    """body = the indented lines of one soldier block (without its '  - type:' line)"""
    lines = body.split('\n')
    out, skip = [], False
    for l in lines:
        if skip:
            if l.startswith('      '):
                continue
            skip = False
        m = re.match(r'    (minStats|maxStats|statCaps|allowPromotion|rankStrings):(.*)$', l)
        if m:
            if m.group(2).strip() == '':
                skip = True          # a block-style map follows: drop its lines too
            continue
        out.append(l)
    add = [f'    minStats: {flow(mn)}', f'    maxStats: {flow(mx)}', f'    statCaps: {flow(cap)}']
    if rank:
        add += ['    allowPromotion: false', f'    rankStrings: [{rank}]']
    # after costSalary if present, else first
    for i, l in enumerate(out):
        if l.startswith('    costSalary:'):
            return '\n'.join(out[:i + 1] + add + out[i + 1:])
    return '\n'.join(add + out)


def main():
    named, unnamed = {}, {}
    for f in sorted(glob.glob(os.path.join(TOOLS, 'roster', 'roster_*.yaml'))):
        d = yaml.safe_load(open(f)) or {}
        for c in d.get('named', []) or []:
            t = c.get('soldierType')   # Joes; villains carry unitType instead and are not soldiers
            if t:
                named[ALIAS.get(t, t)] = c
        unnamed.update(d.get('unnamed', {}) or {})
    done, missing = [], set(named)
    for p in RULES:
        txt = open(p).read()
        def repl(m):
            typ = m.group(1)
            body = m.group(2)
            if typ in named:
                c = named[typ]
                s = c['stats']
                missing.discard(typ)
                done.append(typ)
                return m.group(0)[:m.start(2) - m.start(0)] + patch_block(body, s, s, s, c.get('rankString'))
            if typ in UNNAMED and UNNAMED[typ] in unnamed:
                u = unnamed[UNNAMED[typ]]
                st, cap = u['start'], u['cap']
                mn = {k: max(1, st.get(k, 0) - (10 if k == 'bravery' else 5)) for k in st}
                done.append(typ)
                return m.group(0)[:m.start(2) - m.start(0)] + patch_block(body, mn, st, cap)
            return m.group(0)
        new = re.sub(r'(?m)^  - type: (STR_\w+)\n((?:    .*\n?)+)', repl, txt)
        if new != txt:
            open(p, 'w').write(new)
    print('records applied:', ', '.join(done) or 'none')
    if missing:
        print('no soldier type in the game yet (skipped):', ', '.join(sorted(missing)))


if __name__ == '__main__':
    main()
