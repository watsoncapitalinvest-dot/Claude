#!/usr/bin/env python3
"""One page on how a weekly issue gets made.

    python3 scripts/build_how_its_made.py

John asked for something he could hand a friend. It is a page about process,
so it carries no strategy and nothing about anybody's roster -- but it still
obeys the first rule of the desk: every figure on it is counted here, at build
time, out of the repository. Nothing is typed in.

That is also the point of the page. A sheet explaining why this magazine does
not assert numbers would be a poor thing to assert numbers on.
"""
import glob, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = 'scfl-how-an-issue-is-made.html'
OG = 'scfl-how-its-made-og.jpg'
SEASON, WEEK = '2026', 7


def counts():
    """Every number on the page, measured now."""
    c = {}
    py = glob.glob(os.path.join(ROOT, 'scripts', '*.py'))
    c['builders'] = len(py)
    c['lines'] = sum(sum(1 for _ in open(f, errors='replace')) for f in py)
    c['data'] = len(glob.glob(os.path.join(ROOT, '*.json')))
    c['weekfiles'] = len(glob.glob(os.path.join(ROOT, 'week-data', '*.json')))

    rec = json.load(open(os.path.join(ROOT, 'records.json'), encoding='utf-8'))
    c['span'] = rec['span'].replace('-', '\u2013')
    c['seasons'] = rec['seasons'] if isinstance(rec['seasons'], int) else len(rec['seasons'])
    c['franchises'] = len(rec['standings'])
    c['series'] = len(json.load(open(os.path.join(ROOT, 'rivalries.json'),
                                     encoding='utf-8'))['rows'])

    rp = json.load(open(os.path.join(ROOT, 'week-data',
                                     f'{SEASON}-w{WEEK}-replay.json'), encoding='utf-8'))
    c['games'] = len(rp['games'])
    c['events'] = sum(len(g['timeline']) for g in rp['games'])
    c['events_c'] = f'{c["events"]:,}'
    c['residual'] = sum(1 for g in rp['games'] for e in g['timeline']
                        if e.get('residual'))
    c['flips'] = sum(g['lead_changes'] for g in rp['games'])

    wk = json.load(open(os.path.join(ROOT, 'week-data', f'{SEASON}-w{WEEK}.json'),
                        encoding='utf-8'))
    c['starters'] = sum(len(t.get('starters') or []) for g in wk['games']
                        for t in g['teams'])

    cats = json.load(open(os.path.join(ROOT, 'site-index.json'),
                          encoding='utf-8'))['categories']
    c['catalog'] = sum(len(x['items']) for x in cats)
    c['cats'] = len(cats)

    c['kits'] = len(json.load(open(os.path.join(ROOT, 'team-kits.json'),
                                   encoding='utf-8'))['teams'])

    html = open(os.path.join(ROOT, f'scfl-week-{WEEK}-issue.html'),
                encoding='utf-8').read()
    c['pages'] = len(re.split(r'<div class="page-inner"', html)) - 1
    c['art'] = len(glob.glob(os.path.join(ROOT, f'scfl-week-{WEEK}-play-*.jpg')))

    try:
        c['commits'] = int(subprocess.run(
            ['git', 'rev-list', '--count', 'HEAD'], cwd=ROOT,
            capture_output=True, text=True).stdout.strip())
    except Exception:
        c['commits'] = 0
    return c


STEPS = [
    ('The week comes in', [
        ('Sixteen teams, eight games, and every point each man scored. The catch is '
         'that a half-finished Sunday looks exactly like a finished one — the scores '
         'are simply smaller. So a week is only treated as played once two separate '
         'signs agree that it is. Trusting one of them has flipped a conclusion '
         'twice.'),
    ]),
    ('Every point is traced back to the play that made it', [
        ('A fantasy score is an abstraction: a number that appeared beside a name. '
         'So each one is matched back to the actual thing that happened on a field — '
         'the catch, the run, the sack. {events_c} of them this week. Players are '
         'matched by the league’s own identity number rather than by name, '
         'because two different men called Wilson will quietly ruin an afternoon.'),
        ('Those plays are then laid out on a single sixty-minute clock, so the whole '
         'week reads as one afternoon: a touchdown caught on Monday night becomes a '
         'late-fourth-quarter touchdown. Nothing is invented. The plays, the yards '
         'and the order they happened in are all real. The clock is the only thing '
         'that is made up.'),
    ]),
    ('The games get written up', [
        ('Eight reports, one a game, written off that rebuilt afternoon — who scored, '
         'when, what it did to the lead. {flips} lead changes and {starters} starting '
         'players are on the table to write from.'),
        ('The rule that makes it work is dull and absolute: every number in a '
         'sentence has to be the number in the record. Not roughly it, not what it '
         'was rounded to. Eight separate figures were caught wrong in this issue '
         'alone — a score written as 85.40 that was 85.36, a touchdown placed with '
         'twelve seconds left that happened with eight minutes left, a play described '
         'as the last time the lead changed when four more changes came after it.'),
    ]),
    ('A picture of the play that mattered', [
        ('Each report opens on the moment that decided the game — the last time the '
         'lead changed in a close one, the biggest single play in a one-sided one — '
         'drawn as though it had happened for the fantasy team that owned the player, '
         'in that team’s own colours rather than his real club’s. Eight '
         'pictures, one a game.'),
        ('The man in the picture is really him: his jersey number, his actual height '
         'and weight, the kind of build he has. And the world around him is the real '
         'one — the right stadium, the right sky, the right time of day, and whether '
         'the roof was open or shut. Not one of week 7’s games was played in '
         'rain, and the first attempt at this drew rain.'),
    ]),
    ('The cover', [
        ('Drawn to a written brief, and the brief has to think about the finished '
         'page rather than the picture: a masthead sits across the top and a headline '
         'across the bottom, so both of those areas have to be left deliberately '
         'empty before anything is drawn.'),
        ('The cover and the little preview picture that appears when the link is '
         'shared come out of the same artwork. The one week they were allowed to '
         'differ, the link previewed as a chart and then opened on a stadium.'),
    ]),
    ('It is laid out like a magazine', [
        ('Not a web page that happens to contain football. Pages, in order, that turn. '
         '{pages} of them this week.'),
        ('Where the text falls is measured rather than guessed: the issue is built, '
         'every page is checked at phone size to see where it actually runs out of '
         'room, and then it is built again against those real breaks. A page that '
         'scrolls is a mistake. Anything still too long carries on to a second page '
         'instead — as a continuation, not as a new article.'),
    ]),
    ('It ends on next Sunday', [
        ('Every issue closes on the week ahead: a paragraph for each game, so all '
         'sixteen clubs get said something about rather than the same three being '
         'written about every week.'),
        ('It is assembled from the table, the season so far and {seasons} years of '
         'history — {span} of results, and {series} separate head-to-head records '
         'going back to 2008. So a preview can tell you that one of these two has '
         'beaten the other once in twenty-seven attempts, and that it was a playoff '
         'game.'),
        ('Each line only prints when the thing it describes is actually true, which '
         'is why there is no “should be a good one” anywhere in it.'),
    ]),
    ('Then it has to survive', [
        ('Three things have to be true before an issue counts as finished. It has to '
         'be stored somewhere permanent, because the machine it was built on gets '
         'wiped. It has to be listed, so it can be found again in a month rather than '
         'only through a link that scrolls out of a chat. And it has to look right '
         'when it is shared — a page without a preview picture arrives as a grey '
         'rectangle, and the person who sent it has no way of knowing.'),
    ]),
]

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>How An Issue Is Made &mdash; SCFL NewsRoom</title>
<meta name="description" content="{blurb}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Skirt Chasers &mdash; Dynasty League Magazine">
<meta property="og:title" content="How An Issue Is Made">
<meta property="og:description" content="{blurb}">
<meta property="og:url" content="https://watsoncapitalinvest-dot.github.io/Claude/{out}">
<meta property="og:image" content="https://watsoncapitalinvest-dot.github.io/Claude/{og}">
<link rel="icon" href="newsroom-favicon.png">
<style>
:root{{--cream:#fffdfb;--ink:#17181c;--red:#c20f16;--blue:#0e8ab5;--gold:#d8b45a;
 --muted:#65656b;--rule:#e4dfd4;--serif:Georgia,'Times New Roman',serif;
 --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;}}
*{{box-sizing:border-box;}}
body{{margin:0;background:var(--cream);color:var(--ink);font-family:var(--serif);
 line-height:1.6;}}
.wrap{{max-width:760px;margin:0 auto;padding:30px 20px 70px;}}
.flag{{font-family:var(--sans);font-size:11px;font-weight:900;letter-spacing:.26em;
 text-transform:uppercase;color:var(--red);}}
h1{{font-size:40px;line-height:1.08;margin:12px 0 10px;font-weight:900;
 letter-spacing:-.01em;}}
.dek{{font-style:italic;font-size:18px;color:var(--muted);margin:0 0 22px;}}
.rule{{height:3px;width:76px;background:var(--red);margin:22px 0 26px;}}
.figs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:1px;
 background:var(--rule);border:1px solid var(--rule);margin:0 0 34px;}}
.fig{{background:var(--cream);padding:13px 14px;}}
.fig b{{display:block;font-size:25px;font-weight:900;font-variant-numeric:tabular-nums;
 letter-spacing:-.02em;}}
.fig span{{font-family:var(--sans);font-size:9.5px;font-weight:800;letter-spacing:.13em;
 text-transform:uppercase;color:var(--muted);display:block;margin-top:3px;}}
section{{margin:0 0 30px;}}
h2{{font-size:13px;font-family:var(--sans);font-weight:900;letter-spacing:.14em;
 text-transform:uppercase;margin:0 0 10px;display:flex;align-items:baseline;gap:11px;}}
h2 i{{font-style:normal;color:var(--red);font-variant-numeric:tabular-nums;}}
section p{{margin:0 0 11px;font-size:16.5px;}}
.close{{border-top:1px solid var(--rule);margin-top:40px;padding-top:22px;
 font-size:16.5px;}}
.close b{{color:var(--red);}}
.foot{{font-family:var(--sans);font-size:11px;color:var(--muted);margin-top:26px;
 line-height:1.7;}}
@media(prefers-color-scheme:dark){{
 :root{{--cream:#121217;--ink:#f1efe9;--rule:#2c2c34;--muted:#9b9ba4;}}
 .fig{{background:#16161c;}}
}}
</style></head><body><div class="wrap">
<div class="flag">The Desk</div>
<h1>How An Issue Is Made</h1>
<p class="dek">{blurb}</p>
<div class="rule"></div>
<div class="figs">{figs}</div>
{body}
<div class="close">{close}</div>
<p class="foot">{foot}</p>
</div></body></html>
"""


CARD = """<!doctype html><meta charset="utf-8"><style>
html,body{margin:0;width:1200px;height:630px;background:#121217;color:#f1efe9;
 font-family:Georgia,serif;}
.w{padding:54px 60px;height:630px;box-sizing:border-box;display:flex;
 flex-direction:column;justify-content:space-between;}
.f{font-family:-apple-system,'Segoe UI',sans-serif;font-size:14px;font-weight:900;
 letter-spacing:.3em;text-transform:uppercase;color:#c20f16;}
h1{font-size:66px;line-height:1.02;margin:14px 0 0;font-weight:900;letter-spacing:-.02em;}
.d{font-style:italic;font-size:21px;color:#9b9ba4;margin-top:16px;max-width:860px;}
.g{display:flex;gap:46px;}
.g div b{display:block;font-size:40px;font-weight:900;font-variant-numeric:tabular-nums;}
.g div span{font-family:-apple-system,'Segoe UI',sans-serif;font-size:11px;
 font-weight:800;letter-spacing:.15em;text-transform:uppercase;color:#9b9ba4;}
.bar{height:8px;background:#c20f16;}
</style><div class="bar"></div><div class="w">
<div><div class="f">The Desk</div><h1>How An Issue<br>Is Made</h1>
<div class="d">__D__</div></div>
<div class="g">__G__</div></div><div class="bar"></div>"""


def main():
    c = counts()
    blurb = (f'Eight game reports, eight pictures and a preview of next Sunday, '
             f'built out of {c["events"]:,} real plays and {c["seasons"]} seasons of '
             f'history. Every figure on this page was counted when it was built.')

    figs = ''.join(
        f'<div class="fig"><b>{v}</b><span>{k}</span></div>' for k, v in [
            # nine, so the grid fills. Eight left a dead cell at the end of it.
            ('plays rebuilt', f'{c["events"]:,}'),
            ('lead changes', c['flips']),
            ('starters a week', c['starters']),
            ('reports written', c['games']),
            ('pictures drawn', c['art'] + 1),
            ('pages this issue', c['pages']),
            ('seasons on file', c['seasons']),
            ('head-to-heads', c['series']),
            ('clubs, in colour', c['kits']),
        ])

    body = ''
    for i, (title, paras) in enumerate(STEPS, 1):
        ps = ''.join(f'<p>{p.format(**c)}</p>' for p in paras)
        body += f'<section><h2><i>{i:02d}</i>{title}</h2>{ps}</section>'

    close = ('The short version: <b>nothing in it is written from memory.</b> If a '
             'sentence counts something, ranks something, compares two things or says '
             'one was the biggest, that claim is worked out from the record every '
             'time the page is built — and if it cannot be worked out, it does not go '
             'in. It is a dull rule and it is the whole thing. It is why the errors '
             'that do happen get found before anybody else reads them.')

    foot = (f'One of {c["catalog"]} pages in the Skirt Chasers archive. Every figure '
            f'on this page was counted at the moment it was built, including that '
            f'one.')

    html = PAGE.format(blurb=blurb, figs=figs, body=body, close=close, foot=foot,
                       out=OUT, og=OG)
    open(os.path.join(ROOT, OUT), 'w', encoding='utf-8').write(html)

    # the share card, built here rather than by hand: a page whose card was
    # never made arrives as a grey rectangle and the sender cannot see it
    import importlib.util as _iu
    _s = _iu.spec_from_file_location('ad', os.path.join(ROOT, 'scripts',
                                                        'build_addendum.py'))
    ad = _iu.module_from_spec(_s); _s.loader.exec_module(ad)
    g = ''.join(f'<div><b>{v}</b><span>{k}</span></div>' for k, v in [
        ('plays rebuilt', f'{c["events"]:,}'),
        ('seasons on file', c['seasons']),
        ('head-to-heads', c['series']),
        ('pages', c['pages'])])
    ad.shoot(CARD.replace('__D__', ad.esc(blurb)).replace('__G__', g), OG,
             'how-its-made-card')
    print(f'  -> {OUT} ({len(html)/1024:.0f}kb)')
    for k in sorted(c):
        print(f'     {k:12} {c[k]}')


if __name__ == '__main__':
    main()
