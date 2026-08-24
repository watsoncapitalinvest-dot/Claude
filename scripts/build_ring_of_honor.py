#!/usr/bin/env python3
"""Build ring-of-honor.json — the seed candidate list for the SCFL Ring of Honor.

The Ring of Honor is fun people and athletes this league likes — full stop.
Not "fantasy-relevant," not "was on someone's roster." A UFC heavyweight
whose post-fight interviews the group chat loves belongs here exactly as
much as a manager everyone's glad is in the league. Induction is a league
call, not something this script can make — chat exports never enter this
repo (see docs/ROADMAP.md), so this seeds candidates only from material
already distilled and reviewed elsewhere in the repo, plus names named
directly by the commissioner. Nothing here is quoted chat text; every blurb
is written fresh from the sourced facts and every candidate is DRAFT until
the league votes it in through the app.

Two categories:
  people    — the sixteen managers, one candidate each, from dossier.json.
  athletes  — real athletes (any sport) the league is genuinely a fan of.
              This list is necessarily incomplete — this script cannot read
              the chat, and "who we like" isn't something a build script can
              discover on its own, so most of this category has to come from
              the league itself. The app takes open nominations for anyone
              missing.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'ring-of-honor.json')

dossier = json.load(open(os.path.join(ROOT, 'dossier.json')))
investigations = json.load(open(os.path.join(ROOT, 'investigations.json')))['investigations']

def slug(s):
    return ''.join(c.lower() if c.isalnum() else '-' for c in s).strip('-')
    
PEOPLE = []
for m in dossier['managers']:
    pref = (m.get('preferences') or [''])[0]
    PEOPLE.append({
        'id': 'p-' + slug(m['manager']),
        'category': 'person',
        'name': m['manager'],
        'team': m['team'],
        'status': m.get('status', ''),
        'blurb': pref,
        'source': 'dossier.json',
    })

# Athletes with a real, fact-checked file behind them (investigations.json).
# Hand-mapped: this is not automatic, because the piece has to actually be
# about the player, not just mention him.
ATHLETE_SOURCES = {
    'the-hill-standoff': ('Tyreek Hill', 'Five years of trade offers the Hairy Gumbas turned down, and the deal that died at midnight. The player at the center of the league’s longest-running "will he, won’t he."'),
    'jcm-trade-review': ('Jacory Croskey-Merritt', 'The board had him as a mid-second. Washington’s starting back cost a real 2027 first anyway — the buy that turned an off-radar name into a league argument.'),
}
ATHLETES = []
for inv in investigations:
    slg = inv.get('slug') or ''
    if slg in ATHLETE_SOURCES:
        name, blurb = ATHLETE_SOURCES[slg]
        ATHLETES.append({
            'id': 'a-' + slug(name),
            'category': 'athlete',
            'name': name,
            'team': None,
            'status': '',
            'blurb': blurb,
            'source': f'investigations.json ({inv.get("headline")})',
        })

# Named directly by the commissioner — not tied to any roster, which is the
# point: the Ring of Honor isn't a fantasy-relevance list.
NAMED = [
    {
        'id': 'a-derrick-lewis',
        'category': 'athlete',
        'name': 'Derrick Lewis',
        'team': None,
        'status': '',
        'blurb': '"The Black Beast" — UFC heavyweight, the division’s all-time knockout record, '
                 'and the most quotable post-fight mic in the sport. A league favorite for being '
                 'exactly as unbothered as he looks.',
        'source': 'named by the commissioner, Aug 2026',
    },
]
ATHLETES.extend(NAMED)

payload = {
    'note': ("Seed candidates only — built from dossier.json and investigations.json, "
             "not from the chat archive directly (it never enters this repo). "
             "Nothing here is inducted. See docs/ROADMAP.md and the Ring of Honor "
             "page for how induction actually works."),
    'builtBy': 'scripts/build_ring_of_honor.py',
    'people': PEOPLE,
    'athletes': ATHLETES,
    'count': len(PEOPLE) + len(ATHLETES),
}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)
    f.write('\n')
print(f"wrote {OUT}: {len(PEOPLE)} people, {len(ATHLETES)} athletes")
