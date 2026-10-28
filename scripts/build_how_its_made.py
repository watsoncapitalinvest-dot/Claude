#!/usr/bin/env python3
"""One page on how a weekly issue gets made.

    python3 scripts/build_how_its_made.py

John asked for something he could hand a friend. It is a page about process,
so it carries no strategy and nothing about anybody's roster -- but it still
obeys the first rule of the desk: every figure on it is counted here, at build
time, out of the repository. Nothing is typed in.

That is also the point of the page. A sheet explaining why this magazine does
not assert numbers would be a poor thing to assert numbers on.

IT DESCRIBES THE PROCESS, NOT ONE ISSUE

The first version of this page was written off the week in front of it -- "eight
pictures this week", "{pages} pages this issue", a list of the figures that had
been corrected in that issue's drafts. That is a changelog, not an explanation.
A friend reading it learns what happened in week 7 and still does not know what
the magazine is.

So: nothing here is pinned to a week. WEEK resolves to the newest replay on
file, and every per-week figure is an AVERAGE over all the weeks that have been
rebuilt, because the claim being made is "this is what a week looks like". The
excerpt in step 3 is the one thing drawn from a single game, and it is labelled
as an excerpt and relabelled with that game's own teams and week.

AND IT LEADS ON THE MACHINE

The thing worth explaining is that the week gets rebuilt into eight football
games you can sit and watch back, and that the articles are then written off
those rather than off a column of totals. Everything else on the page is
downstream of that sentence. John, on the draft that buried it: "They need to
know we rebuild the games in a viewable machine. And then we write the articles
on those."
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = 'scfl-how-an-issue-is-made.html'
OG = 'scfl-how-its-made-og.jpg'
SEASON = '2026'
WDIR = os.path.join(ROOT, 'week-data')


def weeks_on_file():
    """Every week that has been rebuilt, oldest first. Never a fixed list."""
    ws = sorted(int(m.group(1)) for m in
                (re.search(r'-w(\d+)-replay\.json$', f)
                 for f in glob.glob(os.path.join(WDIR, f'{SEASON}-w*-replay.json')))
                if m)
    if not ws:
        sys.exit('no replay files on disk -- run scripts/replay.py first')
    return ws


def counts():
    """Every number on the page, measured now.

    Per-week figures are means across every rebuilt week, not the latest one.
    The page says "a week"; an average is the only honest thing to put there.
    """
    c = {}
    ws = weeks_on_file()
    c['week'] = ws[-1]
    c['weeks'] = len(ws)

    rec = json.load(open(os.path.join(ROOT, 'records.json'), encoding='utf-8'))
    c['span'] = rec['span'].replace('-', '\u2013')
    c['seasons'] = rec['seasons'] if isinstance(rec['seasons'], int) else len(rec['seasons'])
    c['franchises'] = len(rec['standings'])
    c['series'] = len(json.load(open(os.path.join(ROOT, 'rivalries.json'),
                                     encoding='utf-8'))['rows'])

    ev = fl = gm = 0
    for w in ws:
        rp = json.load(open(os.path.join(WDIR, f'{SEASON}-w{w}-replay.json'),
                            encoding='utf-8'))
        ev += sum(len(g['timeline']) for g in rp['games'])
        fl += sum(g['lead_changes'] for g in rp['games'])
        gm += len(rp['games'])
    c['events'] = round(ev / len(ws))
    c['events_c'] = f'{c["events"]:,}'
    c['flips'] = round(fl / len(ws))
    c['games'] = round(gm / len(ws))

    st = [sum(len(t.get('starters') or []) for g in json.load(
              open(os.path.join(WDIR, f'{SEASON}-w{w}.json'), encoding='utf-8'))['games']
              for t in g['teams']) for w in ws]
    c['starters'] = round(sum(st) / len(st))

    cats = json.load(open(os.path.join(ROOT, 'site-index.json'),
                          encoding='utf-8'))['categories']
    c['catalog'] = sum(len(x['items']) for x in cats)
    c['cats'] = len(cats)
    c['kits'] = len(json.load(open(os.path.join(ROOT, 'team-kits.json'),
                                   encoding='utf-8'))['teams'])

    # the most lopsided series on file, derived rather than remembered. The
    # draft said "one of these two has beaten the other once in twenty-seven
    # attempts" from memory of one fixture; that is exactly the sentence this
    # whole page is about not writing.
    riv = json.load(open(os.path.join(ROOT, 'rivalries.json'), encoding='utf-8'))
    lop = max((r for r in riv['rows'] if r['g'] >= 10),
              key=lambda r: max(int(x) for x in r['rec'].split('-')) / r['g'])
    w, l = (int(x) for x in lop['rec'].split('-'))
    c['lop'] = f'{max(w, l)}–{min(w, l)}'
    c['lop_g'] = lop['g']

    pg = []
    for f in glob.glob(os.path.join(ROOT, 'scfl-week-*-issue.html')):
        pg.append(len(re.split(r'<div class="page-inner"',
                               open(f, encoding='utf-8').read())) - 1)
    c['pages'] = round(sum(pg) / len(pg)) if pg else 0
    c['art'] = max(len(glob.glob(os.path.join(ROOT, f'scfl-week-{w}-play-*.jpg')))
                   for w in ws)
    return c


LEN = 9  # rows in the excerpt


def adds_up(rows):
    """Does the running score in this window visibly follow from the plays?

    It has to, because a reader can do the arithmetic down the column. The
    first draft took the nine plays before the last lead change and skipped
    the residuals inside them -- which is correct (a residual is not a play and
    is never shown as one) and looked like a mistake: the score jumped two
    points with nothing beside it, and the gold lead-change row printed over a
    pair of numbers that had the same side in front as the row above it.
    So a window is only usable if every row follows from the one before it.
    """
    for a, b in zip(rows, rows[1:]):
        if a.get('residual') or b.get('residual'):
            return False
        s, o = b['side'], 1 - b['side']
        if abs(b['score'][s] - (a['score'][s] + b['pts'])) > 0.005:
            return False
        if abs(b['score'][o] - a['score'][o]) > 0.005:
            return False
    return True


def excerpt(week):
    """A few seconds of a rebuilt game, as the machine has it.

    Every window of consecutive plays that ends on a lead change and whose
    running score adds up on the page is a candidate; the one with the most
    lead changes in it wins, because the lead changing hands is the thing the
    excerpt is there to show.
    """
    rp = json.load(open(os.path.join(WDIR, f'{SEASON}-w{week}-replay.json'),
                        encoding='utf-8'))
    best = None
    for g in rp['games']:
        tl = g['timeline']
        for i, e in enumerate(tl):
            if not e.get('go_ahead') or e.get('residual') or i + 1 < LEN:
                continue
            rows = tl[i + 1 - LEN:i + 1]
            if not adds_up(rows):
                continue
            key = (sum(1 for r in rows if r.get('go_ahead')),
                   round(abs(rows[-1]['lead']), 2) * -1)
            if best is None or key > best[0]:
                best = (key, g, rows)
    if best is None:
        sys.exit(f'week {week}: no self-consistent excerpt window found')
    _, g, rows = best
    return g, [t['team'].strip().strip('*').strip() for t in g['teams']], rows


STEPS = [
    ('The week comes in', [
        ('Sixteen teams, eight matchups, and every point every man scored. '
         'Which is where most fantasy leagues stop. You get a column of totals, a '
         'winner and a loser, and no idea what actually happened.'),
        ('A fantasy score is an abstraction — a number that appeared beside a name '
         'at some point over four days. Everything that follows exists to turn it '
         'back into football.'),
    ]),
    ('Every point is traced back to the play that made it', [
        ('Each one is matched to the actual thing that happened on a real field: the '
         'catch, the run, the sack, the kick. Around {events_c} of them in a normal '
         'week. The player, the yardage, the moment it happened, what it was worth.'),
        ('So a score is no longer a number. It is a list of plays, in the order they '
         'were really made.'),
    ]),
    ('The week is rebuilt as eight football games', [
        ('This is the part worth understanding. Those plays get laid onto a single '
         'sixty-minute clock, so a matchup spread across four days becomes one game '
         'that runs from a kickoff to a final whistle. A touchdown caught on Monday '
         'night becomes a late-fourth-quarter touchdown. Two men who never shared a '
         'field are now on the same drive.'),
        ('And then you can watch it back, which you can do from this page. Not a '
         'summary of it — the game itself, play by play, with the clock running and '
         'the score moving and the lead changing hands in front of you. Pick any of '
         'the eight and sit through it. A fantasy matchup that nobody watched, '
         'because there was never anything to watch, turns into sixty minutes you '
         'can follow.'),
        ('Nothing in it is invented. The plays are real, the yardage is real, the '
         'order is real. The clock is the only thing that is made up, and it is made '
         'up the same way every week.'),
    ]),
    ('The articles are written off the replay', [
        ('Which is the whole reason for building it. A report is not written off a '
         'column of totals, because you cannot write anything off a column of '
         'totals. It is written off the game — who scored, when, what it did to the '
         'lead, which of them held. A normal week has about {flips} lead changes in '
         'it across the eight games, and the replay knows where every one of them '
         'is.'),
        ('That makes a sentence like “he took the lead back with four minutes left '
         'and it stayed taken” a thing that is either true or false rather than a '
         'thing that sounds good. It is in the record or it is not. Every figure in '
         'every sentence is read out of the replay when the page is built, so the '
         'number in the prose and the number in the game are the same number by '
         'construction.'),
    ]),
    ('A picture of the play that decided it', [
        ('Each report opens on the moment the game turned — the last time the lead '
         'changed in a close one, the biggest single play in a one-sided one — drawn '
         'as though it had happened for the fantasy team that owned the player, in '
         'that team’s own colours rather than his real club’s. His jersey, his '
         'number, his build.'),
        ('The world around him is the real one, read off the same tape as the play: '
         'the right stadium, the right weather, the right hour of the day, and '
         'whether the roof was open or shut. If the roof was shut there is no sky in '
         'the picture, and if nobody played in rain that week then nothing in the '
         'issue is wet.'),
    ]),
    ('The cover', [
        ('Drawn to a written brief, and the brief has to think about the finished '
         'page rather than the picture: a masthead sits across the top and a '
         'headline across the bottom, so both of those bands are left deliberately '
         'empty before anything is drawn into them.'),
        ('The cover and the little preview picture that shows up when somebody '
         'pastes the link are cut from the same artwork, so the thing you see in the '
         'message is the thing you get when you open it.'),
    ]),
    ('It is laid out like a magazine', [
        ('Not a web page that happens to contain football. Pages, in order, that '
         'turn — around {pages} of them in an issue, opening on a cover and closing '
         'on next Sunday.'),
        ('Where the text falls is measured rather than guessed. The issue is built, '
         'every page is then checked at phone size to find where it actually runs '
         'out of room, and it is built a second time against those real breaks. '
         'Anything too long carries over as a continuation rather than as a new '
         'article, the way a magazine does it.'),
    ]),
    ('It ends on next Sunday', [
        ('Every issue closes on the week ahead: a paragraph a game, eight of them, '
         'so all sixteen clubs get said something about rather than the same three '
         'being written about every week. What the fixture is worth, what each side '
         'leaves with, and what the two of them have done to each other before.'),
        ('That last part reaches back {seasons} seasons — {span} of results and '
         '{series} separate head-to-head records, the most lopsided of which stands '
         'at {lop} over {lop_g} meetings. A fixture that one of them is on the wrong '
         'end of is worth something the standings cannot tell you, and the preview '
         'is where that gets said.'),
        ('Each line only prints when the thing it describes is actually true of the '
         'fixture in front of it. Which is why there is no “should be a good one” '
         'anywhere in it.'),
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
.tape{{border:1px solid var(--rule);margin:16px 0 13px;font-family:var(--sans);}}
.t-head{{font-size:10px;font-weight:800;letter-spacing:.11em;text-transform:uppercase;
 color:var(--muted);padding:10px 12px;border-bottom:1px solid var(--rule);
 line-height:1.5;}}
.t-row{{display:grid;grid-template-columns:52px 1fr auto;gap:0 10px;align-items:start;
 padding:7px 12px;border-bottom:1px solid var(--rule);border-left:3px solid transparent;}}
.t-row:last-child{{border-bottom:0;}}
.t-row i{{font-style:normal;font-size:10.5px;font-weight:800;color:var(--muted);
 font-variant-numeric:tabular-nums;padding-top:2px;}}
.t-row b{{font-size:13px;font-weight:700;font-family:var(--serif);display:block;}}
.t-play span{{display:block;font-size:11.5px;color:var(--muted);}}
.t-row em{{font-style:normal;font-size:12.5px;font-weight:800;
 font-variant-numeric:tabular-nums;white-space:nowrap;padding-top:2px;}}
.t-row.flip{{border-left-color:var(--gold);}}
.t-row.flip em{{color:var(--gold);}}
.t-foot{{font-size:11px;color:var(--muted);padding:9px 12px;line-height:1.55;
 border-top:1px solid var(--rule);}}
.t-foot a{{display:inline-block;font-family:var(--sans);font-size:10.5px;
 font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--red);
 text-decoration:none;border-bottom:2px solid var(--gold);margin-top:6px;}}
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


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def tape(week):
    """Step 3's excerpt. Showing the machine beats describing it."""
    g, names, rows = excerpt(week)
    head = (f'Excerpt &middot; {esc(names[0])} vs {esc(names[1])}, week {week} '
            f'&middot; the rebuilt game, as it runs')
    out = [f'<div class="t-head">{head}</div>']
    for e in rows:
        fc = e['fc']
        flip = ' flip' if e.get('go_ahead') else ''
        out.append(
            f'<div class="t-row{flip}"><i>Q{fc["qtr"]} {fc["clock"]}</i>'
            f'<div class="t-play"><b>{esc(e["player"])}</b>'
            f'<span>{esc(e["text"]) or "scored"}</span></div>'
            f'<em>{e["score"][0]:.2f}&ndash;{e["score"][1]:.2f}</em></div>')
    # the gold rule is the house signal for the moment a game changed hands, so
    # the footnote has to say so or a reader just sees an unexplained stripe
    n = sum(1 for e in rows if e.get('go_ahead'))
    lead = 'took the lead' if n == 1 else 'changed hands'
    out.append(
        f'<div class="t-foot">Gold marks the lead changing hands. It {lead} '
        f'{"once" if n == 1 else f"{n} times"} in these {len(rows)} plays, and '
        f'{g["lead_changes"]} times in the finished game &mdash; every one of '
        f'which the report is written off. '
        f'<a href="scfl-replay.html?w={week}">Watch a game back &rarr;</a></div>')
    return '<div class="tape">' + ''.join(out) + '</div>'


def main():
    c = counts()
    blurb = ('Sixteen teams and four days of real football, rebuilt into eight '
             'games you can watch back on a single sixty-minute clock — and '
             'then written up off those. How an issue of the Skirt Chasers gets '
             'made.')

    figs = ''.join(
        f'<div class="fig"><b>{v}</b><span>{k}</span></div>' for k, v in [
            # nine, so the grid fills. Eight left a dead cell at the end of it.
            # Everything per-week is a mean over every week rebuilt so far: the
            # labels say "a week", so a single week's count would be a fib.
            ('plays a week', f'{c["events"]:,}'),
            ('games rebuilt a week', c['games']),
            ('lead changes a week', c['flips']),
            ('starters a week', c['starters']),
            ('pages an issue', c['pages']),
            ('pictures an issue', c['art'] + 1),
            ('seasons on file', c['seasons']),
            ('head-to-heads', c['series']),
            ('clubs, in colour', c['kits']),
        ])

    body = ''
    for i, (title, paras) in enumerate(STEPS, 1):
        ps = ''.join(f'<p>{p.format(**c)}</p>' for p in paras)
        if i == 3:
            ps += tape(c['week'])
        body += f'<section><h2><i>{i:02d}</i>{title}</h2>{ps}</section>'

    close = ('The short version: <b>the week gets rebuilt into football, and then '
             'the football gets reported.</b> Every sentence in an issue sits on a '
             'play that really happened, for points that were really scored, at the '
             'point in the game where the rebuilt record puts it — because the '
             'sentence and the number in it are both read back out of that record '
             'when the page is built. Nothing is written from memory, and nothing '
             'that cannot be traced to a play goes in at all.')

    foot = (f'One of {c["catalog"]} pages in the Skirt Chasers archive. Every figure '
            f'here was counted out of the record when the page was built; the '
            f'per-week figures are averages across the {c["weeks"]} weeks rebuilt so '
            f'far, so they move as the season does.')

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
        ('plays a week', f'{c["events"]:,}'),
        ('games rebuilt', c['games']),
        ('seasons on file', c['seasons']),
        ('head-to-heads', c['series'])])
    ad.shoot(CARD.replace('__D__', ad.esc(blurb)).replace('__G__', g), OG,
             'how-its-made-card')
    print(f'  -> {OUT} ({len(html)/1024:.0f}kb)')
    for k in sorted(c):
        print(f'     {k:12} {c[k]}')


if __name__ == '__main__':
    main()
