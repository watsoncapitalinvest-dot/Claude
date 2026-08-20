#!/usr/bin/env python3
"""Build tradewar/ammo.json — the league's own history, sorted into ordnance.

Nothing here is invented. Offers come from the itemized trade ledger, taunts
from the committed Powers of Pain draft-grade write-ups, picks from the draft
history. The raw group chat is deliberately not in this repo (see .gitignore),
so it is not a source and never will be.
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

def load(name):
    return json.loads((ROOT / name).read_text())

# ---- offers ---------------------------------------------------------
def asset_str(a):
    return a.get('player') or a.get('pick') or '?'

def side(s):
    return {'t': s['team'].strip(), 'g': [asset_str(a) for a in s.get('gets', [])]}

trades = load('trades.json')['trades']
two = [t for t in trades if len(t['sides']) == 2]

def count(t): return [len(s.get('gets', [])) for s in t['sides']]

lowball, blockbuster, regular = [], [], []
for t in two:
    n = count(t)
    rec = {'y': t['season'], 's': [side(s) for s in t['sides']]}
    total = sum(n)
    if min(n) == 1 and max(n) >= 3: lowball.append(rec)
    elif total >= 7:                blockbuster.append(rec)
    elif total <= 4:                regular.append(rec)

# ---- taunts: one trimmed sentence from a real draft grade -----------
taunts = []
for year, rows in load('pop-grades.json')['years'].items():
    for r in rows:
        note = re.sub(r'\s+', ' ', r.get('note', '')).strip()
        # drop the leading roster dump ("TE Kyle Pitts WR Devonta Smith ...").
        # NAME must allow curly apostrophes or it bisects Ja'Marr and friends.
        NAME = r"[A-Z][\w.\u2019'-]*"
        note = re.sub(r'^(?:(?:QB|RB|WR|TE|K|DEF|DL|LB|DB)\s+' + NAME + r'(?:\s+' + NAME + r')*\s*)+',
                      '', note).lstrip()
        # later years list picks as "12 James Cook RB 15 Christian Watson WR ..."
        note = re.sub(r'^(?:\d{1,2}\s+' + NAME + r'(?:\s+' + NAME + r')*\s+(?:QB|RB|WR|TE|K|DEF|DL|LB|DB)\s*)+',
                      '', note).lstrip()
        m = re.search(r'^([A-Z].{30,145}?[.!?])(?:\s|$)', note)
        if not m: continue
        line = m.group(1).strip()
        if len(line) < 32 or line.count(' ') < 6: continue
        taunts.append({'y': int(year), 't': r['team'].strip(), 'g': r.get('grade', '').strip(), 'l': line})

# ---- picks ----------------------------------------------------------
picks = []
for year, rows in load('drafts.json')['years'].items():
    for p in rows:
        if p.get('round') == 1 and p.get('player'):
            picks.append({'y': int(year), 't': p['team'].strip(), 'n': p['pick'], 'p': p['player'].strip()})

# ---- the curse ------------------------------------------------------
curse = ['Romo', 'Fournette', 'Hunt', 'Murray', 'Kupp', 'Metcalf', 'Jordyn Tyson']

out = {
    'built': 'scripts/build_ammo.py',
    'source': 'SCFL trade ledger, Powers of Pain draft grades, draft history',
    'offers': {'lowball': lowball, 'blockbuster': blockbuster, 'regular': regular},
    'taunts': taunts,
    'picks': picks,
    'curse': curse,
}
path = ROOT / 'tradewar' / 'ammo.json'
path.write_text(json.dumps(out, separators=(',', ':')))
print(f"lowball {len(lowball)}  blockbuster {len(blockbuster)}  regular {len(regular)}")
print(f"taunts {len(taunts)}  picks {len(picks)}")
print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size/1024:.1f} KB)")
