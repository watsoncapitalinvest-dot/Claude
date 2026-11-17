"""Research owed by the villain arrival missions (STORY, 16 Nov 2026; VILLAIN_ARRIVALS_v1, John 16:39 approved, 20:04 "finish").
Three items the missions hand out, and their research topics:
  STR_ARASHIKAGE_ARROW   Silent Night lost: the arrow that killed the witness (a clue)
  STR_MARS_PROTOTYPE     Trade Fair won: Destro's demonstrator weapon
  STR_BRAINWAVE_MACHINE  Second Opinion won: Mindbender's machine
Each topic consumes its item (needItem + destroyItem), carries `lane:` and `costFunds` like the other STORY topics, and
its Intel File text is STR_<id>_UFOPEDIA. Effects that need the engine are listed under `hooks` for BUILD.
Writes gijoe_research_villains.rul. Usage: python3 gen_villain_research.py ../mod/Ruleset"""
import os, sys, yaml
OUT = sys.argv[1]
N = '{NEWLINE}'
P = N + N

TOPICS = [
    dict(id='STR_ARASHIKAGE_ARROW', lane='INTEL', cost=80, funds=0, sell=0,
         name='Arashikage Arrow',
         text=["SCARLETT: Hand-made, bamboo shaft, the fletching cut from a hawk's flight feathers. Nobody has made an arrow like this in Japan for a hundred years, except one family.",
               "The Arashikage. Ninja, for six hundred years. Cobra has bought itself an assassin, and he works for honour, not money. That makes him harder to buy back."],
         hooks='Opens the Arashikage line on the spine (STR_ARASHIKAGE_INTERROGATION, already in the Year 1 map) as a lead; Storm Shadow Intel File.'),
    dict(id='STR_MARS_PROTOTYPE', lane='ARMORY', cost=300, funds=120000, sell=0,
         name='M.A.R.S. Prototype',
         text=["ROADBLOCK: Seized off Destro's own firing range. Beautiful work, every part machined in Scotland, every part stamped M.A.R.S.",
               "Take it apart and we know how M.A.R.S. builds, what it fails at and what it needs to work. Every M.A.R.S. weapon Cobra carries from now on has the same weak points."],
         hooks="Joe armour and cover take -15% damage from M.A.R.S.-tier Cobra weapons; Cobra's first M.A.R.S. kit tier arrives a month later (VILLAIN_ARRIVALS_v1, Trade Fair won)."),
    dict(id='STR_BRAINWAVE_MACHINE', lane='MEDICAL', cost=280, funds=90000, sell=0,
         name='Brainwave Machine',
         text=["DOC: A chair, a helmet and a lot of wiring. It doesn't erase a mind. It quiets it, until it does what it's told.",
               "Now we know the frequency, we can shield against it, and we can bring people back faster. Mindbender will build a better one. This one taught us how he thinks."],
         hooks='Brainwashed civilians (Second Opinion lost, later brainwave attacks) recover on a stun instead of fighting on; opens Joe resistance to brainwave attacks (months 23-30 calendar band).'),
]

items, research, S = [], [], {}
for t in TOPICS:
    items.append({'type': t['id'], 'size': 0.1, 'weight': 1, 'bigSprite': 100, 'floorSprite': 100,
                  'invWidth': 1, 'invHeight': 1, 'recover': True, 'battleType': 0, 'costSell': t['sell']})
    r = {'name': t['id'], 'lane': t['lane'], 'cost': t['cost'], 'points': 40, 'needItem': True, 'destroyItem': True,
         'unlocks': []}
    if t['funds']:
        r['costFunds'] = t['funds']
    research.append(r)
    S[t['id']] = t['name']
    S[t['id'] + '_UFOPEDIA'] = P.join(t['text'])
hdr = ('# STORY: research owed by the villain arrival missions (story_tools/gen_villain_research.py; VILLAIN_ARRIVALS_v1).\n'
       '# BUILD hooks (effects the engine must apply when each topic is researched):\n'
       + ''.join(f"#   {t['id']}: {t['hooks']}\n" for t in TOPICS)
       + '# Generated: edit the script, not this file.\n')
body = yaml.dump({'items': items, 'research': research,
                  'extraStrings': [{'type': 'en-US', 'strings': S}, {'type': 'en-GB', 'strings': S}]},
                 sort_keys=False, width=200, allow_unicode=True)
open(os.path.join(OUT, 'gijoe_research_villains.rul'), 'w', encoding='utf-8').write(hdr + body)
print('villain research:', len(TOPICS), 'topics')
