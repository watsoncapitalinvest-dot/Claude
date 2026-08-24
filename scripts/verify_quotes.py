#!/usr/bin/env python3
"""Check every quotation in an article against the chat corpus, verbatim.

    python3 scripts/verify_quotes.py kick-2026-wire-freeze

House rule: nothing gets published in quotation marks unless it is in the
corpus word for word. This reads the article out of investigations.json, pulls
every "..." span, and looks for it in the chat.

The corpus never enters the repo -- the Pages workflow publishes the whole root
-- so this only runs where the exports happen to be unpacked, and says so
plainly rather than passing silently when it cannot find them.
"""
import datetime, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHATS = os.environ.get('SCFL_CHATS',
    '/tmp/claude-0/-home-user-Claude/c302abf8-582a-5977-91c7-1dfbd915ffe3/scratchpad/chats')
LINE = re.compile(r'^\[(\d{1,2})/(\d{1,2})/(\d{2}), (\d{1,2}:\d{2}:\d{2}\s*[AP]M)\] ([^:]+): (.*)$')


def canon(t):
    """Lowercase, normalise smart punctuation, strip everything else."""
    t = (t.replace('’', "'").replace('‘', "'")
          .replace('“', '"').replace('”', '"')
          .replace('—', ' ').replace('–', ' ').replace('…', ' '))
    return re.sub(r'[^a-z0-9]+', '', t.lower())


def load():
    out = []
    for sub in ('official', 'mos'):
        p = os.path.join(CHATS, sub, '_chat.txt')
        if not os.path.exists(p):
            continue
        msgs = []
        for raw in open(p, encoding='utf-8', errors='replace'):
            raw = raw.rstrip('\n').replace('‎', '')
            m = LINE.match(raw)
            if m:
                mo, da, yr, tm, who, txt = m.groups()
                msgs.append([datetime.date(2000 + int(yr), int(mo), int(da)), who.strip(), txt])
            elif msgs:
                msgs[-1][2] += ' ' + raw.strip()
        out += msgs
    return out


def main(aid):
    d = json.load(open(os.path.join(ROOT, 'investigations.json'), encoding='utf-8'))
    art = next((a for a in d['investigations'] if a['id'] == aid), None)
    if not art:
        sys.exit(f'no article {aid!r} in investigations.json')

    msgs = load()
    if not msgs:
        sys.exit(f'no corpus under {CHATS} -- cannot verify; set SCFL_CHATS')
    blob = canon(' '.join(m[2] for m in msgs))
    who = {canon(m[2]): m[1] for m in msgs}

    quotes = []
    for p in art['paragraphs']:
        quotes += re.findall(r'“([^”]{8,})”', p)

    bad = []
    print(f'{aid}: {len(quotes)} quotations, corpus {len(msgs):,} messages\n')
    for q in quotes:
        c = canon(q)
        ok = c in blob
        speaker = next((v for k, v in who.items() if c in k), '?')
        print(('  OK   ' if ok else '  MISS ') + f'[{speaker}] "{q[:78]}"')
        if not ok:
            bad.append(q)
    print()
    if bad:
        sys.exit(f'{len(bad)} quotation(s) not found verbatim in the corpus')
    print(f'all {len(quotes)} quotations verified verbatim')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'kick-2026-wire-freeze')
