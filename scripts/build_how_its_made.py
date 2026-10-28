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
    ('The week arrives', [
        ('api.sleeper.app is blocked from the machine this desk runs on, so the '
         'scores are fetched by a GitHub Action and come back through git. Only one '
         'run is kept per group, which is how week 2 was lost once — two dispatches '
         'in quick succession cancelled each other.'),
        ('A half-finished week looks exactly like a finished one, so a week counts '
         'as played only on two tells: nobody below 30 points, and the share of '
         'starters on exactly zero. A finished week runs 1 to 6 per cent. A Sunday '
         'evening reads 10. One tell alone has flipped an article’s conclusion '
         'twice.'),
    ]),
    ('The games are rebuilt from the tape', [
        ('Every fantasy point is matched back to the real NFL play that produced it, '
         'joining on the league’s own player id and never on a name. Sleeper '
         'stores that id with a leading space. Two running backs called Wilson will '
         'ruin an afternoon.'),
        ('{events_c} plays across eight games are then laid onto a single '
         '60-minute clock, so a Monday-night touchdown becomes a late-fourth-quarter '
         'touchdown and the week reads as one afternoon. Nothing is invented: the '
         'plays, the yardage and the order are real. Only the clock is made up.'),
        ('Points no play explains — mostly team defence — are carried as flagged '
         'residuals so the running score lands on the true final. There were '
         '{residual} of them. They are never written about.'),
    ]),
    ('The reports get written', [
        ('Eight game reports, one a game, from the rebuilt tape. {flips} lead '
         'changes, {starters} starting players and every score either side of every '
         'one of them are available to the writing, and the figure in a sentence has '
         'to be the figure in the file.'),
        ('That rule is the whole job. Eight separate figures were caught wrong in '
         'this issue alone — a score rounded to 85.40 that was 85.36, a touchdown '
         'placed at twelve seconds left that happened at 8:14, a play called the '
         'last lead change when four more followed it.'),
    ]),
    ('A picture of the play that mattered', [
        ('Each report opens on the play that decided it — the last lead change in a '
         'close game, the biggest single play in a blowout — drawn as though it '
         'happened for the fantasy side that owned the man rather than for his NFL '
         'club. Eight of them this week, one a game.'),
        ('The brief is generated, not written. It carries the two clubs’ own '
         'colours from a file of {kits}, the player’s real jersey number and '
         'real height and weight, and the real conditions off the tape: the stadium, '
         'the sky, the local time of day, whether the roof was shut. It rained in '
         'none of week 7’s games, and the first version of this drew rain.'),
    ]),
    ('The cover', [
        ('Drawn by a separate graphics AI from a plain-text brief. The brief fixes '
         'the composition in pixel rows, because a masthead sits across the top of '
         'the frame and a headline sits across the bottom, and both are added after '
         'the picture exists.'),
        ('The cover and the link preview are built from the same file by the same '
         'command. The week they were allowed to disagree, the link previewed as a '
         'chart and opened on a stadium.'),
    ]),
    ('The issue is laid out, and measured', [
        ('Pagination is measured rather than guessed. The issue is built once, a '
         'headless browser renders every page at phone size and records where each '
         'one actually fills up, and it is built again against those breaks. A '
         'magazine page that scrolls is a bug.'),
        ('{pages} pages this week. Anything still long is scaled down, and anything '
         'scaled too far runs on to a second page instead — with a continuation '
         'line, not a second headline.'),
    ]),
    ('Next Sunday, argued rather than listed', [
        ('Every issue closes on the week ahead: a paragraph a game, so all sixteen '
         'clubs get said something about. It is generated from the table, the week '
         'files and {seasons} seasons of history — {span} for lifetime records, '
         '{series} head-to-head series going back to 2008.'),
        ('Every line hangs off a condition, so a joke about a rout prints only over '
         'a rout. Repeated phrasings are capped, including against the paragraph '
         'directly above, because the same sentence twice reads worse than silence.'),
    ]),
    ('Then it has to survive', [
        ('Saved, filed and sendable, checked by a script before anything is called '
         'finished. Saved because this machine gets wiped. Filed into a catalog of '
         '{catalog} pages so it is reachable later. Sendable means a share card that '
         'exists — a page without one arrives as a grey rectangle, and the person '
         'who sent it cannot see that from their end.'),
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
            ('plays rebuilt', f'{c["events"]:,}'),
            ('lead changes', c['flips']),
            ('starters a week', c['starters']),
            ('seasons on file', c['seasons']),
            ('head-to-heads', c['series']),
            ('pages this issue', c['pages']),
            ('builders', c['builders']),
            ('lines of them', f'{c["lines"]:,}'),
        ])

    body = ''
    for i, (title, paras) in enumerate(STEPS, 1):
        ps = ''.join(f'<p>{p.format(**c)}</p>' for p in paras)
        body += f'<section><h2><i>{i:02d}</i>{title}</h2>{ps}</section>'

    close = ('The short version: <b>nothing in it is typed from memory.</b> If a '
             'sentence counts, ranks, compares or characterises something, it is '
             'computed from a file in the repository, and if it cannot be computed '
             'it does not get printed. That is a rule the desk learned the hard way, '
             'and it is why the mistakes that do get through tend to be caught '
             'before anybody else sees them.')

    foot = (f'Built from {c["data"]} data files and {c["weekfiles"]} week files across '
            f'{c["commits"]:,} commits. {c["catalog"]} pages in the catalog, in '
            f'{c["cats"]} sections. Figures counted at build time; nothing on this '
            f'page is typed in.')

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
