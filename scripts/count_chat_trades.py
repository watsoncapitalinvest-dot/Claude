#!/usr/bin/env python3
"""Count trades out of the official WhatsApp room, as a check on the ledger.

    python3 scripts/count_chat_trades.py <path-to-official/_chat.txt>

The Obvibase reconstruction gives The Machines exactly thirteen deals in each
of 2021, 2022, 2023, 2024 and 2025 -- the only franchise of the sixteen whose
count does not move -- so it needs a second source before anything is
published off it. The league announces its trades in the official room, which
is that source and is independent of the export.

Only aggregates come out of here: counts per franchise per season. No message
text is written anywhere, and the corpus itself is never committed (see
CLAUDE.md). Pass the path at run time.

Two things make the count harder than grepping for the word:

- ONE MESSAGE CAN CARRY SEVERAL TRADES. The commissioner posts a run of them
  in a single block, each with its own banner. Counting messages undercounts;
  the unit is the banner, not the message.
- TEAMS ARE TAGGED WITH EMOJI AND NICKNAMES, not their league names: the
  skull is The Machines, the wrestler is Powers of Pain, the gorilla is
  Wookie Leaks, the van is the A-Team (Lil Chops), the unicorn is SDFT
  (Beaver Eaters). The pig is Pork Chop Express -- careful, because Porky's
  is a different franchise entirely (Lil Chops again).
"""
import collections, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANNER = re.compile(r'(?:official\s*trade|trade\s*alert)', re.I)

# token -> franchise key. Longest/most specific patterns first within a team.
TAGS = {
    'machines':        [r'💀', r'\bmachines?\b', r'\bbelichicks?\b'],
    'powersofpain':    [r'🤼', r'\bpo[pb]\b', r'\bpowers\b'],
    'porkchopexpress': [r'\bpce\b', r'\bpork\s*chop\b', r'🐖'],
    'lilchops':        [r'🚐', r'\ba-?team\b', r"\bporky'?s?\b", r'\blil\s*chops\b',
                        r'\blamb\s*chops\b', r'\bdisciples\b'],
    'newworldorder':   [r'🌎', r'🌍', r'\bnwo\b', r'\bnew\s*world\b'],
    'wookieleaks':     [r'🦍', r'\bwookies?\b', r'\bwade\s*garret'],
    'smokedragons':    [r'🐉', r'\bdragons?\b', r'\bsmoke\b'],
    'masterjeti':      [r'✝', r'\bjet\s*-?\s*i\b', r'\bjeti\b', r'\bmahopac\b'],
    'beavereaters':    [r'🦄', r'🦫', r'\bsdft\b', r'\bbeavers?\b', r'\bbeaver\s*eaters\b'],
    'heavyhitters':    [r'🏋', r'\bhitters?\b', r'\bphins\s*phag\b'],
    'stillthecream':   [r'\bcreams?\b', r'\bcreamiest\b'],
    'killerklowns':    [r'🤡', r'\bklowns?\b'],
    'bigblue':         [r'\bbig\s*blue\b', r'\bbb\b'],
    'guidohaters':     [r'\bguido'],
    'gumbas':          [r'\bgumbas?\b', r'\bclams\b'],
    'horsecollars':    [r'\bhorse\s*collars?\b', r'\bforty\s*2v\b', r'\b42v\b'],
}
RX = {k: re.compile('|'.join(v), re.I) for k, v in TAGS.items()}


def units(path):
    """(year, text) for every trade banner in the room."""
    txt = open(path, encoding='utf-8', errors='replace').read()
    msgs = re.findall(
        r'\[(\d{1,2})/(\d{1,2})/(\d{2}), [^\]]+\] ([^:]{1,45}): (.*?)'
        r'(?=\n\[\d{1,2}/\d{1,2}/\d{2}, |\Z)', txt, re.S)
    out = []
    for _, _, yy, _sender, body in msgs:
        parts = BANNER.split(body)
        # parts[0] is whatever came before the first banner -- not a trade
        for p in parts[1:]:
            out.append((2000 + int(yy), p))
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('SCFL_CHAT', '')
    if not path or not os.path.exists(path):
        raise SystemExit('pass the path to the official room export')
    per = collections.defaultdict(collections.Counter)
    sides = collections.Counter()
    total = collections.Counter()
    for yr, text in units(path):
        named = {k for k, rx in RX.items() if rx.search(text)}
        total[yr] += 1
        sides[len(named)] += 1
        for k in named:
            per[k][yr] += 1

    yrs = sorted(total)
    print(f'trade banners in the official room: {sum(total.values())}')
    print('  per season:', {y: total[y] for y in yrs})
    print('  franchises named per banner:', dict(sorted(sides.items())))
    print()
    print(f"{'franchise':<18}" + ''.join(f'{y:>6}' for y in yrs) + f"{'total':>8}")
    for k in sorted(per, key=lambda k: -sum(per[k].values())):
        print(f'{k:<18}' + ''.join(f'{per[k].get(y, 0):>6}' for y in yrs)
              + f'{sum(per[k].values()):>8}')

    led = json.load(open(os.path.join(ROOT, 'trades.json'), encoding='utf-8'))['trades']
    fr = json.load(open(os.path.join(ROOT, 'scfl-franchises.json'), encoding='utf-8'))
    look = fr['lookup']
    norm = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower())
    lp = collections.defaultdict(collections.Counter)
    for t in led:
        for s in t['sides']:
            lp[look.get(norm(s['team'])) or norm(s['team'])][t['season']] += 1
    print()
    print('THE MACHINES, the two sources side by side')
    print(f"{'':<10}" + ''.join(f'{y:>7}' for y in yrs))
    print(f"{'ledger':<10}" + ''.join(f"{lp['machines'].get(y, 0):>7}" for y in yrs))
    print(f"{'chat':<10}" + ''.join(f"{per['machines'].get(y, 0):>7}" for y in yrs))


if __name__ == '__main__':
    main()
