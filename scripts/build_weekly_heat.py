#!/usr/bin/env python3
"""Weekly Heat Index -- "who got hot that week?", straight from the league chat.

    python3 scripts/build_weekly_heat.py [path/to/chats]

The league asked for this the night the Heat Index shipped: a running "who got
hot this week" leaderboard instead of one static all-time number. This buckets
the same volley/heat pass build_addendum.py already runs by calendar week
(Monday-Sunday, keyed to the reply that lands each volley) and keeps only what
a week needs to be readable: total volleys and heated volleys, the single
hottest pairing, and the person who showed up in the most heated exchanges.
The pairing-level heat percentages that power the Heat Index page stay a
season-plus sample; a week is too small a sample for a rate to mean anything,
so this ranks weeks by raw heated-volley count instead.

Reuses build_addendum's message load, owner mapping and heat word list so this
can never disagree with the Heat Index or the Addendum about what counts as a
volley or a hit. Aggregate only, same as everything else built from the chat
corpus -- no message text, ever. The build refuses to write if any string in
the output matches text from the corpus.
"""
import collections, datetime, importlib.util, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location('ad', os.path.join(ROOT, 'scripts', 'build_addendum.py'))
ad = importlib.util.module_from_spec(_spec)
sys.modules['ad'] = ad
_spec.loader.exec_module(ad)

OUT = os.path.join(ROOT, 'weekly-heat.json')
RECENT_N = 16
TOP_ALLTIME_N = 8


def week_start(d):
    return d - datetime.timedelta(days=d.weekday())


def week_entry(w, volley_c, heated_c, person_c):
    total_v = sum(volley_c.values())
    total_h = sum(heated_c.values())
    top_pair = None
    if heated_c:
        k = max(heated_c, key=lambda k: (heated_c[k], volley_c[k]))
        top_pair = {'a': ad.NAME.get(k[0], k[0]), 'b': ad.NAME.get(k[1], k[1]),
                    'heated': heated_c[k], 'volleys': volley_c[k]}
    top_individual = None
    if person_c:
        o = max(person_c, key=lambda o: person_c[o])
        top_individual = {'name': ad.NAME.get(o, o), 'heated': person_c[o]}
    return {'week': w.isoformat(), 'weekEnd': (w + datetime.timedelta(days=6)).isoformat(),
            'volleys': total_v, 'heated': total_h,
            'heatPct': round(100 * total_h / total_v, 1) if total_v else 0.0,
            'topPair': top_pair, 'topIndividual': top_individual}


def assert_no_chat_text(payload, msgs):
    strings = set()
    def walk(o):
        if isinstance(o, str): strings.add(o)
        elif isinstance(o, dict): [walk(v) for v in o.values()]
        elif isinstance(o, list): [walk(v) for v in o]
    walk(payload)
    def norm(x): return re.sub(r'[^a-z0-9]+', '', x.lower())
    corpus = {norm(m['x']) for m in msgs if len(m['x']) > 25}
    for st in strings:
        n = norm(st)
        if len(n) > 25 and (n in corpus or any(n in c for c in corpus)):
            raise SystemExit(f'refusing to write: output contains chat text -> {st[:80]!r}')
    return len(strings)


def build():
    ad.compute()
    ms = ad._corpus

    volley_by_week = collections.defaultdict(collections.Counter)
    heated_by_week = collections.defaultdict(collections.Counter)
    person_by_week = collections.defaultdict(collections.Counter)
    for i in range(1, len(ms)):
        a, b = ms[i - 1], ms[i]
        oa, ob = ad.CHAT.get(a['who']), ad.CHAT.get(b['who'])
        if a['who'] == b['who'] or not oa or not ob or oa == ob:
            continue
        if a['c'] != b['c']:
            continue  # different rooms: not the same conversation, just adjacent in time
        if not 0 <= (b['ts'] - a['ts']).total_seconds() <= ad.WINDOW:
            continue
        w = week_start(b['ts'].date())
        k = tuple(sorted((oa, ob)))
        volley_by_week[w][k] += 1
        if ad.HEAT.search(a['x']) or ad.HEAT.search(b['x']):
            heated_by_week[w][k] += 1
            person_by_week[w][oa] += 1
            person_by_week[w][ob] += 1

    weeks = sorted(volley_by_week)
    entries = [week_entry(w, volley_by_week[w], heated_by_week[w], person_by_week[w]) for w in weeks]

    recent_weeks = list(reversed(entries))[:RECENT_N]
    hottest_alltime = sorted((e for e in entries if e['heated'] > 0),
                              key=lambda e: -e['heated'])[:TOP_ALLTIME_N]

    payload = {
        'note': 'aggregate only; built by scripts/build_weekly_heat.py',
        'asOf': entries[-1]['weekEnd'] if entries else None,
        'totalWeeksTracked': len(entries),
        'recentWeeks': recent_weeks,
        'hottestWeeksAllTime': hottest_alltime,
    }
    n = assert_no_chat_text(payload, ms)
    print(f'text check: {n} strings in output, none from the chat corpus')
    json.dump(payload, open(OUT, 'w'), indent=1)
    print(f'wrote {os.path.basename(OUT)} | {len(entries)} weeks tracked | '
          f'{sum(1 for e in entries if e["heated"] > 0)} ran hot at least once')
    if recent_weeks:
        cur = recent_weeks[0]
        print(f'  most recent week ({cur["week"]}..{cur["weekEnd"]}): '
              f'{cur["heated"]} heated of {cur["volleys"]} volleys')


if __name__ == '__main__':
    build()
