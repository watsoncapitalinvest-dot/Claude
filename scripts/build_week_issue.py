#!/usr/bin/env python3
"""Lay the week's game reports out as a flip-book magazine issue.

    python3 scripts/build_week_issue.py --week 4

Takes the stories scripts/write_week.py produced and runs them through the same
cover, contents page, page engine and measured pagination as every other issue
this desk has shipped, so a weekly issue looks like the magazine rather than
like a web page that happens to contain football.

Pagination is measured, not guessed: build_issue lays the pages out once, the
headless measurer renders them at phone size and records where each page
actually fills up, and the issue is laid out again against those breaks. A
magazine page that scrolls is a bug.

The cover art comes from John's graphics AI like every other issue. If it is
not there yet the issue still builds, with a typographic stand-in, because an
issue that will not build is worth less than one with a plain cover.
"""
import argparse, importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')
_s = importlib.util.spec_from_file_location('bi', os.path.join(ROOT, 'scripts', 'build_issue.py'))
bi = importlib.util.module_from_spec(_s); sys.modules['bi'] = bi; _s.loader.exec_module(bi)
E = bi.esc

# eight games a week, so the numerals have to reach eight -- stopping at
# four gave a contents page reading I, II, III, IV, 5, 6, 7
ORD = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII', 8: 'VIII'}


def scoreboard_blocks(stories):
    """The scoreboard as a pre-rendered article, so the packer treats it as one."""
    rows = ''
    for s in sorted(stories, key=lambda s: -(s['score'][0] + s['score'][1])):
        rows += (f'<tr><th scope="row">{E(s["winner"])}</th>'
                 f'<td class="num"><b>{s["score"][0]}</b></td>'
                 f'<td class="vs">def.</td>'
                 f'<td>{E(s["loser"])}</td>'
                 f'<td class="num dim">{s["score"][1]}</td>'
                 f'<td class="num dim">+{s["margin"]:.1f}</td></tr>')
    return [('body', '<div class="ad"><figure><div class="scroll"><table>'
             f'<tbody>{rows}</tbody></table></div>'
             '<figcaption>Every game of the week, heaviest first. Margin at the right.'
             '</figcaption></figure></div>')]


def build(season, week, remeasure=True):
    p = os.path.join(WDIR, f'{season}-w{week}-stories.json')
    if not os.path.exists(p):
        sys.exit(f'no {p} -- run scripts/write_week.py --week {week} first')
    d = json.load(open(p, encoding='utf-8'))
    stories, lead = d['stories'], d['lead']

    # lead story first, then the rest by how much there is to say about them
    order = [lead] + sorted((i for i in range(len(stories)) if i != lead),
                            key=lambda i: (stories[i]['arc'] == 'rout', stories[i]['margin']))

    arts = [{'id': 'wk-scoreboard', 'flag': 'The Scoreboard',
             'headline': f'Week {week}, Settled',
             'subhead': 'Eight games, every one of them rebuilt from the tape.',
             'blocks': scoreboard_blocks(stories)}]
    for n, i in enumerate(order):
        s = stories[i]
        arts.append({
            'id': f'wk{week}-g{i}',
            'flag': 'The Game of the Week' if i == lead else f'Game {ORD.get(n, n)}',
            'headline': s['headline'],
            'subhead': s['dek'],
            'paragraphs': s['paragraphs'],
        })

    out = f'scfl-week-{week}-issue.html'
    key = f'week-{week}'
    ls = stories[lead]
    big = max(stories, key=lambda s: s['margin'])
    lines = [f'{s["winner"].upper()} {s["score"][0]}, {s["loser"].upper()} {s["score"][1]}'
             for s in sorted(stories, key=lambda s: s['margin'])[:5]]
    bi.ISSUES[key] = {
        'out': out,
        'title': f'The Week {week} Issue',
        'tagline': f'Week {week} of the 2026 season',
        'dateline': f'Week {week}, {season}',
        'runhead': f'Skirt Chasers &middot; Week {week} &middot; {season}',
        'art': f'scfl-week-{week}-cover.jpg',
        'og': f'scfl-week-{week}-og.jpg',
        'ogtitle': f'Skirt Chasers — The Week {week} Issue',
        'ogdesc': (f'{ls["headline"]}. Eight games rebuilt play by play, from Thursday night '
                   f'to the last snap on Monday.'),
        'sharetext': f'Week {week}, replayed from the tape.',
        'kicker': f'The Magazine · Week {week}',
        'seal': (f'Week', f'{week}'),
        'issueline': f'2026&ndash;27 Season &middot; Week {week}',
        'hook': ls['headline'],
        'hooksub': ls['dek'],
        'coverlines': lines + [f'THE ROUT: {big["winner"].upper()} BY {big["margin"]:.0f}'],
        'articles': [],
        'arts_inline': arts,
        'openart': {},
    }
    bi.build(key, remeasure=remeasure)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, required=True)
    ap.add_argument('--season', default='2026')
    ap.add_argument('--no-measure', action='store_true')
    a = ap.parse_args()
    out = build(a.season, a.week, remeasure=not a.no_measure)
    print(f'  -> {out}')


if __name__ == '__main__':
    main()
