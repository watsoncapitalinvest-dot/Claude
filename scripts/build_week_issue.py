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
_t = importlib.util.spec_from_file_location('sd', os.path.join(ROOT, 'scripts', 'standings.py'))
sd = importlib.util.module_from_spec(_t); sys.modules['sd'] = sd; _t.loader.exec_module(sd)
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


def standings_blocks(st):
    """The table, by division, because that is the shape the playoffs use."""
    if not st:
        return []
    out = []
    by = {}
    for r in st['table']:
        by.setdefault(r.get('div_name') or 'League', []).append(r)
    for di, dv in enumerate(sorted(by)):
        rows = ''
        for r in by[dv]:
            rows += (f'<tr><th scope="row">{E(r["team"])}</th>'
                     f'<td class="num"><b>{r["record"]}</b></td>'
                     f'<td class="num dim">{r["pf"]:.0f}</td>'
                     f'<td class="num dim">{r["pa"]:.0f}</td>'
                     f'<td class="num dim">{r["streak"]}</td></tr>')
        # the table is reference, not a game report: it is allowed to run over
        # two pages rather than be shrunk to 72 per cent to avoid it
        out.append(('pagebreak' if di == 2 else 'body',
                    f'<div class="ad"><figure>'
                            f'<div class="sect" style="margin-top:14px">{E(dv)}</div>'
                            f'<div class="scroll"><table><thead><tr><th class="lt"></th>'
                            f'<th>W-L</th><th>PF</th><th>PA</th><th>Run</th></tr></thead>'
                            f'<tbody>{rows}</tbody></table></div></figure></div>'))
    lead = st['table'][0]
    out.append(('body', f'<p class="b">{E(lead["team"])} top the league at {lead["record"]} '
                        f'with {lead["pf"]:.0f} points. Playoffs begin in week '
                        f'{st["playoff_week"]}, which leaves '
                        f'{max(0, st["playoff_week"] - 1 - st["through"])} weeks of the regular '
                        f'season still to play.</p>'))
    return out


def build(season, week, remeasure=True):
    p = os.path.join(WDIR, f'{season}-w{week}-stories.json')
    if not os.path.exists(p):
        sys.exit(f'no {p} -- run scripts/write_week.py --week {week} first')
    d = json.load(open(p, encoding='utf-8'))
    stories, lead = d['stories'], d['lead']

    # lead story first, then the rest by how much there is to say about them
    order = [lead] + sorted((i for i in range(len(stories)) if i != lead),
                            key=lambda i: (stories[i]['arc'] == 'rout', stories[i]['margin']))

    st = sd.build(str(season), int(week))
    arts = [{'id': 'wk-scoreboard', 'flag': 'The Scoreboard',
             'headline': f'Week {week}, Settled',
             'subhead': 'Eight games, every one of them rebuilt from the tape.',
             'blocks': scoreboard_blocks(stories)}]
    if st:
        arts.append({'id': 'wk-standings', 'flag': 'The Table',
                     'headline': f'Where Everyone Stands',
                     'subhead': f'Through week {st["through"]} of the {season} season.',
                     'blocks': standings_blocks(st)})
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
    # ---- one article, one page -------------------------------------------
    # The greedy packer fills pages to the brim, so a long game report spills
    # onto a continuation page and the issue stops reading as a magazine. Here
    # the page breaks are not measured at all: they are exactly the article
    # boundaries. Anything that then does not fit is shrunk to fit, which is
    # what a page layout does when the copy runs long.
    here = os.path.join(ROOT, 'scripts')
    bi.build(key, remeasure=False, quiet=True)          # emits .pack-kinds.json
    kinds = json.load(open(os.path.join(here, '.pack-kinds.json'), encoding='utf-8'))
    breaks = [i for i, k in enumerate(kinds) if k in ('divider', 'pagebreak')]
    json.dump(breaks, open(os.path.join(here, f'.pack-breaks-{key}.json'), 'w'))
    bi.build(key, remeasure=False, quiet=True)
    if remeasure:
        fit(out)
    return out


def fit(out):
    """Scale down any page whose article runs past the bottom."""
    import re as _re, subprocess
    try:
        r = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'fit_pages.js'), out,
                            'http://localhost:8991'],
                           capture_output=True, text=True, cwd=ROOT, timeout=180,
                           env=dict(os.environ, NODE_PATH='/opt/node22/lib/node_modules'))
        zooms = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:
        print(f'  note: could not measure the fit ({e}); pages left at full size')
        return
    path = os.path.join(ROOT, out)
    html = open(path, encoding='utf-8').read()
    n = [0]

    def sub(m):
        i = n[0]; n[0] += 1
        z = zooms[i] if i < len(zooms) else 1
        return m.group(0) if z >= 0.999 else f'<div class="page-inner" style="zoom:{z}">'

    html = _re.sub(r'<div class="page-inner">', sub, html)
    open(path, 'w', encoding='utf-8').write(html)
    tight = [(i, z) for i, z in enumerate(zooms) if z < 0.999]
    print(f'  fitted {len(tight)} of {len(zooms)} pages' +
          (f' (smallest {min(z for _, z in tight):.3f})' if tight else ''))


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
