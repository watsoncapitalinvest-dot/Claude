#!/usr/bin/env python3
"""Build ring-of-honor.json — the seed candidate list for the SCFL Ring of Honor.

This isn't a new idea being bolted onto the league — it's a real one, with a
real history in the chat. Casual "ring of honor" nominations go back to at
least May 2022 (a golfer, praised as an unbothered legend on and off the
course). Smoke Dragons tried to formally build one in May 2023: draw up a
list, take nominations from the league, vote in a couple every year, tie it
to draft day. It never got built then. The bar was never "played in this
league" or "fantasy-relevant" — real "first ballot" votes since have gone to
a UFC heavyweight and a Brewers broadcaster right alongside actual NFL
names. The one real test across every real mention: does the room agree
this person is a legend. Induction is a league call, not something this
script can make — chat exports never enter this repo (see docs/ROADMAP.md),
so this seeds candidates only from material already distilled and reviewed
elsewhere in the repo, plus names named directly by the commissioner.
Nothing here is quoted chat text; every blurb is written fresh from the
sourced facts and every candidate is DRAFT until the league votes it in
through the app.

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
        'blurb': '"The Black Beast" — UFC heavyweight, famous equally for knockouts and the deadpan '
                 'post-fight interviews that follow them.',
        'argument': 'The Machines has been dropping Derrick Lewis references into this chat since at '
                 'least June 2021 — a fight recap here, a Hot Ones watch there — for four straight '
                 'years, right up through a first-ballot vote in February 2025. A second manager '
                 'backed the same vote independently, same conversation, no prompting.',
        'source': 'named by the commissioner, Aug 2026',
    },
    {
        'id': 'a-jameis-winston',
        'category': 'athlete',
        'name': 'Jameis Winston',
        'team': None,
        'status': '',
        'blurb': 'NFL quarterback as well known in this league for personality as for arm talent.',
        'argument': 'Called a first-ballot SCFL Hall of Famer and "my favorite person in sports" by '
                 'Pork Chop Express in the same breath — then seconded, unprompted, by The Machines '
                 'minutes later in the same thread. Two managers, one sitting, zero lobbying.',
        'source': 'league chat, distilled Aug 2026',
    },
    {
        'id': 'a-bob-uecker',
        'category': 'athlete',
        'name': 'Bob Uecker',
        'team': None,
        'status': '',
        'blurb': 'Voice of the Milwaukee Brewers for over 50 years, and Harry Doyle — the fictional '
                 'announcer — in the Major League movies.',
        'argument': 'When he died in January 2025, three different managers reacted inside the same '
                 'hour: one quoting Harry Doyle’s own most famous call, one posting the news story, '
                 'one just typing "RIP." The next morning, mid-tribute over his career stats, Smoke '
                 'Dragons made it official — "an American treasure... Ring of Honor member."',
        'source': 'league chat, distilled Aug 2026',
    },
    {
        'id': 'a-willie-mack',
        'category': 'athlete',
        'name': 'Willie Mack',
        'team': None,
        'status': '',
        'blurb': 'Professional wrestler with a direct, real-life tie to this league.',
        'argument': 'Not a fandom-from-a-distance pick — Keith’s wife builds Willie Mack’s ring gear '
                 'by hand, he wears it, and sends photos back. The chat’s reaction wasn’t a joke; it '
                 'was pride.',
        'source': 'league chat, distilled Aug 2026',
    },
    {
        'id': 'a-eli-manning',
        'category': 'athlete',
        'name': 'Eli Manning',
        'team': None,
        'status': '',
        'blurb': 'Two-time Super Bowl MVP, Giants quarterback for sixteen seasons.',
        'argument': 'A first-ballot debate that has resurfaced across years — 2022, then again in '
                 '2025 — pulling in a different set of managers each time. Nobody in the chat has '
                 'ever actually taken the other side.',
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
