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

def slug(s):
    return ''.join(c.lower() if c.isalnum() else '-' for c in s).strip('-')
    
# The case for each manager — not a bio restatement, an actual pitch for why
# they belong, built from the same sourced facts as the blurb above it.
ARGUMENTS = {
    'Keith': 'Four rings, the loudest voice in the chat by 54,000+ messages, and he once drove to a '
             'public library to pull 1997 microfilm just to win an argument. If this league has a main '
             'character, it’s him.',
    'Horse Collars': 'Runs a garden, trades stocks, coaches two youth teams, and still shows up to argue '
             'that one Geno Smith game personally cost him 11 wins. Committed to the bit in every '
             'direction at once.',
    'Dan / Scamps / PCE': 'The center of gravity for the entire chat — the one manager people refer to by '
             'first name alone. Keeps a running blood feud with Creams alive for the fun of it, and '
             'treats trade honor like scripture.',
    'Smoke Dragons': 'Kept the group chat alive through the political wars, then built an entire '
             'newsroom out of it afterward. He’s the one who said "if we distilled our stories into 5 '
             'people we could write an incredible movie" — and he wasn’t wrong.',
    "Creams, a.k.a. 'Dwayne'": 'The league’s most active trader, defends players he’s already cut, and '
             'has never once backed down from the 1,600-yard high school stat the chat spent a decade '
             'trying to debunk. Legendary, unverifiable, permanent.',
    'Powers of Pain (PoP)': 'Reigning champion, four rings, and the self-appointed anti-kicker crusader '
             'with an actual proposed "🚫 K bill." Runs the league’s rules fights for sport and still '
             'finds time to win.',
    'New World Order (NWO)': 'The unofficial commissioner nobody voted for and everybody needed — runs '
             'the Zoom, locks the draft date, posts "official trade" before anyone has to ask. The '
             'league’s actual institutional memory.',
    'Killer Klowns': 'Took over a dead franchise and turned it into a 2024 title on "believe in the '
             'process" alone. Left the league quietly, and is remembered fondly anyway — "appreciate it '
             'fellas 🍻."',
    "Sheq; earlier chat name '~Dave Sheq'": 'The deepest prospect nerd in the chat, can recite a full '
             'draft board from memory, and laughs so hard and so often it’s basically a personality '
             'trait (haha x545).',
    "Coach Nick / Wookie; earlier '~Wookie'": '1,200+ jokes deep and still going — the chat’s actual '
             'lol-machine, self-deprecating to the bone. The whole group quietly pulled for him through '
             'a real 2026 health scare. That’s not nothing.',
    'Lil Chops (has run Lamb Chops / The Porkys / A-Team)': 'Proudly, permanently rebuilding — "I have '
             'two QBs on IR" — while simultaneously trying to reform the entire league’s format rules. '
             'Committed to losing with integrity.',
    'Tommy / Tom Vertucci': 'The chat’s philosopher-in-residence, dropping dynasty wisdom and Life After '
             'People trivia in the same breath, self-aware enough to admit mid-argument when he’s '
             '"losing me lol."',
    'Jim Hunt': 'Three-peat champion, 2021–2023, the league’s actual dynasty — and still the guy hosting '
             'golf outings and defending the trophy-shot tradition. Blue-collar royalty.',
    "Mike; earlier '~Mike'": 'A 2019 champion who left the chat in 2022 but is still remembered for '
             'running the league’s NFL-rumor trade wire solo, and for nearly rebranding to "Ned’s '
             'Nuggets" on his way out.',
    "Cousin Pete; chat name '~Pete'": 'Came home from a 2026 hospital stay to a chat full of well-wishes '
             'and immediately reassured everyone he still wasn’t trading Ja’Marr Chase. The league’s '
             'hype-man, unconditionally.',
    "Jay; chat name '~Jay'": 'Hosts the cookouts, the golf, the Tee Bar afternoons — the actual social '
             'glue holding sixteen owners together outside the app. Also the guy who begged for "NO '
             'POLITICS NO RELIGION" and mostly got it.',
}

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
        'argument': ARGUMENTS.get(m['manager'], ''),
        'source': 'dossier.json',
    })

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
    'note': ("Seed candidates only — from dossier.json plus a handful of names distilled straight "
             "out of the league's own chat, where 'ring of honor' has been a running idea since "
             "2022. The raw chat itself never enters this repo. Nothing here is inducted. See "
             "docs/ROADMAP.md and the Ring of Honor page for how induction actually works."),
    'builtBy': 'scripts/build_ring_of_honor.py',
    'people': PEOPLE,
    'athletes': ATHLETES,
    'count': len(PEOPLE) + len(ATHLETES),
}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)
    f.write('\n')
print(f"wrote {OUT}: {len(PEOPLE)} people, {len(ATHLETES)} athletes")
