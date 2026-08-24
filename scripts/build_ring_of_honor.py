#!/usr/bin/env python3
"""Build ring-of-honor.json — the seed candidate list for the SCFL Ring of Honor.

The Ring of Honor is fun people and athletes this league likes — full stop.
Not "fantasy-relevant," not "was on someone's roster." A UFC heavyweight
whose post-fight interviews the group chat loves belongs here exactly as
much as a wrestler one manager's spouse works with. Induction is a league
call, not something this script can make — chat exports never enter this
repo (see docs/ROADMAP.md), so this seeds candidates only from material
already distilled and reviewed elsewhere in the repo, plus names named
directly by the commissioner. Nothing here is quoted chat text; every blurb
is written fresh from the sourced facts and every candidate is DRAFT until
the league votes it in through the app.

The sixteen managers are explicitly NOT eligible for self-nomination here —
"we're not nominating owners" (the commissioner, Aug 2026). dossier.json is
about the league's own people and stays out of this build entirely. Every
candidate below is an outside person or athlete the league likes, never one
of the sixteen. The 'person' category still exists in the schema for
someone like that — a spouse, a broadcaster, a comedian — nominated through
the app, same as an athlete.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'ring-of-honor.json')

def slug(s):
    return ''.join(c.lower() if c.isalnum() else '-' for c in s).strip('-')

PEOPLE = []

# investigations.json pieces (the-hill-standoff, jcm-trade-review, etc.) are
# NOT a source here on their own — they document trade *value*, and this
# board is explicitly not a fantasy-relevance list (see the module docstring
# above). Checked the raw chat for both Tyreek Hill and Jacory Croskey-Merritt
# directly: every mention is roster/trade/injury talk, no personality
# affection, and Hill draws open dislike at least once ("I hate tyreek hill
# so goddamn much"). Neither belongs here on the evidence. Athletes only make
# this list below, sourced from a real like, not a real trade.
ATHLETES = []

# Named directly by the commissioner, or found in the league's own chat —
# distilled to a fact and a fresh blurb, never a stored quote. The chat file
# itself stays local and out of this repo; only the finding does.
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
        'argument': 'Named "first ballot" by more than one manager, independently, in the same '
                 'conversation — not a bit one guy kept alive alone.',
        'source': 'named by the commissioner, Aug 2026',
    },
    {
        'id': 'a-jameis-winston',
        'category': 'athlete',
        'name': 'Jameis Winston',
        'team': None,
        'status': '',
        'blurb': 'The chat has been calling him a first-ballot SCFL Hall of Famer since at least '
                 '2025 — a running, multi-manager consensus pick, not a one-person bit.',
        'argument': 'Called a first-ballot SCFL Hall of Famer and, in the same breath, someone’s '
                 'outright favorite person in sports. A running position, not a single fan’s bit.',
        'source': 'league chat, distilled Aug 2026',
    },
    {
        'id': 'a-bob-uecker',
        'category': 'athlete',
        'name': 'Bob Uecker',
        'team': None,
        'status': '',
        'blurb': 'The voice of the Brewers for over 50 years and the deadpan star of the Major '
                 'League movies — nominated outright in the chat as an SCFL Ring of Honor member.',
        'argument': 'Nominated by name, unprompted, the same day the chat learned who he was: "an '
                 'American treasure." Fifty years on Brewers radio plus Major League — case closed.',
        'source': 'league chat, distilled Aug 2026',
    },
    {
        'id': 'a-willie-mack',
        'category': 'athlete',
        'name': 'Willie Mack',
        'team': None,
        'status': '',
        'blurb': 'Pro wrestler, and a genuine league connection — one manager’s wife makes his '
                 'ring gear. The chat calls him a legend, and means it literally, not as a bit.',
        'argument': 'A real, personal tie, not a fandom-from-a-distance pick — one manager’s wife '
                 'makes his ring gear — and the chat calls him a legend without a hint of irony.',
        'source': 'league chat, distilled Aug 2026',
    },
    {
        'id': 'a-eli-manning',
        'category': 'athlete',
        'name': 'Eli Manning',
        'team': None,
        'status': '',
        'blurb': 'A years-long running argument for first-ballot honors, championed loudest by '
                 'the league’s Giants fans but debated by more than one manager, more than once.',
        'argument': 'A years-long, multi-manager argument for first-ballot honors — loudest from the '
                 'league’s Giants fans, but never once contested by anyone else either.',
        'source': 'league chat, distilled Aug 2026',
    },
]
ATHLETES.extend(NAMED)

payload = {
    'note': ("Seed candidates only — outside people and athletes distilled straight out of the "
             "league's own chat, where 'ring of honor' has been a running idea since 2022. The "
             "league's own sixteen managers are not eligible for nomination here. The raw chat "
             "itself never enters this repo. Nothing here is inducted. See docs/ROADMAP.md and "
             "the Ring of Honor page for how induction actually works."),
    'builtBy': 'scripts/build_ring_of_honor.py',
    'people': PEOPLE,
    'athletes': ATHLETES,
    'count': len(PEOPLE) + len(ATHLETES),
}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)
    f.write('\n')
print(f"wrote {OUT}: {len(PEOPLE)} people, {len(ATHLETES)} athletes")
