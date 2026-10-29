#!/usr/bin/env python3
"""The replay, made watchable: scfl-replay.html plus the feeds it runs on.

    python3 scripts/build_watch.py              # every week with a replay
    python3 scripts/build_watch.py --week 7     # just one

Until now the rebuilt games only existed at the desk -- replay.py prints one to
a terminal, and the issue quotes it. This puts them in front of the league: pick
a week, pick a matchup, and watch the sixty minutes run, play by play, with the
score moving and the lead changing in front of you.

WHAT IT WRITES

  team-identity.json              roster_id -> current name + logo slug
  week-data/{season}-w{N}-watch.json   one slim feed a week
  week-data/watch-index.json      which weeks exist, so the page can ask
  scfl-replay.html                the viewer
  scfl-replay-og.jpg              its share card

THE FEED IS SLIM ON PURPOSE

A full replay file is ~800kb, most of it keys repeated sixteen hundred times
and fields the viewer has no use for. The feed interns player names and NFL
game ids into tables and writes each event as a flat array, which is about a
fifth of the size -- it matters, because this is opened on a phone on a
Sunday evening.

TWO THINGS IT WILL NOT DO

Residuals are carried, because dropping them makes the running score jump with
nothing beside it, and they are flagged so the page can show them as the
adjustment they are. Nothing may present one as a play: they are points no play
explains, and the viewer renders them without play text for exactly that reason.

Teams are keyed by roster_id end to end. Names get changed mid-season --
Forty2V became Horsecollars, Heavy Hitters became Phins Phag -- so a logo
looked up by name silently vanishes the week somebody renames. LOGO_BY_RID is
keyed by roster id and any roster that will not resolve is named in the build
output rather than quietly losing its crest.
"""
import argparse, glob, importlib.util, json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')
SEASON = 2026
OUT = 'scfl-replay.html'
OG = 'scfl-replay-og.jpg'

# roster_id -> slug in scfl-team-logos-resized.json, for the two that the
# obvious normalisation cannot reach: n.W.o's crest is filed under the stable's
# full name, and Phins Phag's is still filed under what the franchise was
# called before it was renamed mid-season.
LOGO_BY_RID = {1: 'newworldorder', 13: 'heavyhitters'}

# The three-letter tag, as the broadcast has carried it since the sprite sheet
# arrived. The COLOURS used to live here too, as a guessed pair per crest slug,
# and two of them were identical: Wookie Leaks and BIG BLUE both came out
# #1090f0, so when they met each other every figure on the field was the same
# shade of blue. The kits now come from team-kits.json, which is John's own
# answer for each franchise and is what the play art is already drawn to -- so
# the field and the pictures in the issue dress the same sixteen clubs alike.
ABBR = {
    'wookieleaks': 'WKL', 'bigblue': 'BLU', 'beavereaters': 'BVR',
    'guidohaters': 'GUI', 'powersofpain': 'POP', 'newworldorder': 'NWO',
    'masterjeti': 'JET', 'horsecollars': 'HC', 'porkchopexpress': 'PCE',
    'machines': 'MCH', 'stillthecream': 'CRM', 'gumbas': 'GUM',
    'heavyhitters': 'PHN', 'lilchops': 'CHP', 'smokedragons': 'SMK',
    'killerklowns': 'KLW',
}

# team-kits.json names colours in words, because it is written for a graphics
# AI. The sprite sheet needs numbers: it is painted neutral white and grey, and
# tintSheet() turns the white into the primary and the grey into the secondary.
INK = {
    'black': '#1b1b1f', 'white': '#f2f2ee', 'brown': '#6b4420',
    'khaki': '#c3b183', 'silver': '#c8ccd2', 'deep purple': '#4a2173',
    'smoke grey': '#8a8f99', 'green': '#1f7a3a', 'light green': '#67c27a',
    'red': '#c0272d', 'blue': '#1f5fd0', 'teal': '#16a3a3',
    'orange': '#e2731f', 'yellow': '#efc62c', 'very dark red': '#4a0d12',
    'purple': '#7a3fa8', 'laser green': '#63f06a', 'gold': '#d8b45a',
}


# Guido Haters' trim is a sentence -- "Italian green, white and red stripe,
# gold collar and facemask" -- and four colours are named in it. Taking the
# first match gave white, which is n.W.o's secondary over the same black: the
# two kits came out identical. Gold is the one that tells them apart and is
# what John wrote the kit around.
TRIM_PICK = {16: 'gold'}


def ink(word):
    """A kit colour in words -> a hex the tinter can use.

    Guido Haters' trim is a whole sentence about an Italian tricolour stripe
    and a gold collar, which is a description of a kit rather than a colour.
    The first colour word in it that resolves is the one used.
    """
    w = (word or '').strip().lower()
    if w in INK:
        return INK[w]
    for k in sorted(INK, key=len, reverse=True):      # longest first: "deep purple" before "purple"
        if k in w:
            return INK[k]
    return ''

FLAG_TD, FLAG_GO, FLAG_RES = 1, 2, 4


def slug(name):
    k = re.sub(r'[^a-z0-9]', '', str(name).lower())
    return k[3:] if k.startswith('the') else k


def identity(weeks):
    """roster_id -> {name, logo}, from the newest week file that names them.

    Newest wins so a renamed franchise shows the name it goes by now, and the
    logo comes off LOGO_BY_RID or the slug, never off the name alone.
    """
    logos = set(json.load(open(os.path.join(ROOT, 'scfl-team-logos-resized.json'),
                               encoding='utf-8')).keys())
    out, missing = {}, []
    for w in weeks:                       # ascending, so later weeks overwrite
        wk = json.load(open(os.path.join(WDIR, f'{SEASON}-w{w}.json'), encoding='utf-8'))
        for g in wk['games']:
            for t in g['teams']:
                out[t['roster_id']] = {'rid': t['roster_id'],
                                       'name': t['team'].strip().strip('*').strip()}
    kits = json.load(open(os.path.join(ROOT, 'team-kits.json'),
                          encoding='utf-8'))['teams']
    nokit = []
    for rid, t in sorted(out.items()):
        k = LOGO_BY_RID.get(rid) or slug(t['name'])
        if k not in logos:
            missing.append(f'{rid} {t["name"]!r} -> {k!r}')
            k = ''
        t['logo'] = k
        # The kit, out of John's own answer for this franchise. Where primary
        # and secondary are the same word -- n.W.o is black on black, Wookie
        # Leaks brown on brown -- the trim is the second colour instead, or
        # the figure comes out a silhouette with nothing to read.
        t['abbr'] = ABBR.get(k, '')
        kit = kits.get(str(rid)) or {}
        c1 = ink(kit.get('primary'))
        c2 = ink(kit.get('secondary'))
        if not c2 or c2 == c1:
            c2 = ink(TRIM_PICK.get(rid) or kit.get('trim')) or c2
        if not c1 or not c2 or c1 == c2:
            nokit.append(f'{rid} {t["name"]!r} -> {kit.get("primary")!r}/'
                         f'{kit.get("secondary")!r}/{kit.get("trim")!r}')
            c1, c2 = c1 or '#d8d8d8', c2 or '#9aa0a8'
        t['c1'], t['c2'] = c1, c2
        # the change strip, for the weeks this franchise meets somebody in the
        # same colour. Its trim first, then its own secondary.
        t['alt'] = ink(TRIM_PICK.get(rid) or kit.get('trim')) or c2
    if missing:
        print('  NO CREST for:', '; '.join(missing))
        print('  -> add the roster id to LOGO_BY_RID in scripts/build_watch.py')
    if nokit:
        print('  UNREADABLE KIT for:', '; '.join(nokit))
        print('  -> fix the words in team-kits.json, or add them to INK')
    return out


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def near(a, b, tol=70):
    """Would these two kits read as the same colour on a 170px-tall field?"""
    return sum(abs(x - y) for x, y in zip(rgb(a), rgb(b))) < tol


def _lum(h):
    r, g, b = rgb(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def sep(a, b):
    """How far apart two kits read at sprite size.

    Plain RGB distance calls dark purple and near-black 96 apart and lets them
    on the same field. They are not separable: on a 170px field the eye has hue
    and brightness to work with and those two share the brightness. This is the
    redmean weighting, which tracks the eye far better, and the luminance gap
    comes back separately because two DARK kits are hard whatever their hues.
    """
    (r1, g1, b1), (r2, g2, b2) = rgb(a), rgb(b)
    rb = (r1 + r2) / 2
    dr, dg, db = r1 - r2, g1 - g2, b1 - b2
    d = math.sqrt((2 + rb / 256) * dr * dr + 4 * dg * dg
                  + (2 + (255 - rb) / 256) * db * db)
    return d, abs(_lum(a) - _lum(b))


def tells_apart(a, b):
    d, dl = sep(a, b)
    return d >= 200 or (d >= 150 and dl >= 60)


def kit_ok(h1, h2, c1, c2):
    """Can a man in c1/c2 be told from a man in h1/h2, and from the pitch?

    The sprite is painted body=c1, trim=c2, so the bodies carry the read and
    have to be clearly apart. But a trim collision muddies it too: the Smoke
    Dragons wear purple with a near-black trim and the Guido Haters wear
    near-black, so a Dragon's trim was the exact colour of a Hater, with only
    21 points of brightness between the two bodies. That was the muddiest
    picture of the eight and nothing caught it, because the old test compared
    body against body and nothing else.
    """
    if not tells_apart(h1, c1) or near(c1, c2):
        return False                    # bodies too close, or one colour
    # A trim collision only muddies the picture when the bodies are merely
    # adequate. Once they are miles apart -- a gold man beside a black one --
    # nobody is reading the trim to tell them apart, and insisting on it left
    # the Guido Haters with no legal strip at all against StillTheCream.
    if sep(h1, c1)[0] >= 300:
        return True
    return not near(c1, h2) and not near(h1, c2)


def kit_clash(teams):
    """Put one side in its change strip when the two cannot be told apart.

    Three franchises wear red -- the Powers of Pain, Pork Chop Express and the
    Killer Klowns -- and two wear brown. The weeks any pair of them met, every
    figure on the field was the same shade and the picture said nothing. The
    SECOND side named in the matchup changes, so the first keeps the colours
    the issue's play art already put it in, and it changes into a strip it
    actually owns: body and trim are drawn from its own two colours and its
    alt, in any order, and the first pairing that clears wins.
    """
    h, a = teams
    if kit_ok(h['c1'], h['c2'], a['c1'], a['c2']):
        return None
    pool = [c for c in (a['c1'], a['c2'], a.get('alt')) if c]
    for c1 in pool:
        for c2 in pool:
            if c1.lower() == c2.lower():
                continue
            if kit_ok(h['c1'], h['c2'], c1, c2):
                was = f'{a["c1"]}/{a["c2"]}'
                a['c1'], a['c2'] = c1, c2
                return f'{a["name"]} {was} -> {c1}/{c2} (vs {h["name"]})'
    return f'{a["name"]} has no change strip clear of {h["name"]}'


def lineups_for(week):
    """matchup_id -> {roster_id: [[name, pos], ...]}, that week's own starters.

    The broadcast needs eleven names a side to put on the field, and it used
    to top them up out of scfl-rosters.json -- a Sleeper export from July, so
    it could name a man who had been traded away months earlier. The week file
    knows exactly who each side started that week, which is the only list
    entitled to appear on a field for that week.
    """
    wk = json.load(open(os.path.join(WDIR, f'{SEASON}-w{week}.json'), encoding='utf-8'))
    out = {}
    for g in wk['games']:
        out[g['matchup_id']] = {
            t['roster_id']: [[pl['name'], pl['pos']]
                             for pl in (t.get('starters') or []) if pl.get('name')]
            for t in g['teams']}
    return out


def rosters_for(week):
    """matchup_id -> {team name: roster_id} out of the week file.

    The replay only carries names, so the join runs through the week file it
    was built from. Keyed within the matchup, because two franchises have
    shared a name prefix before now.
    """
    wk = json.load(open(os.path.join(WDIR, f'{SEASON}-w{week}.json'), encoding='utf-8'))
    return {g['matchup_id']: {t['team'].strip().strip('*').strip(): t['roster_id']
                              for t in g['teams']} for g in wk['games']}


def feed(week, ident):
    """One week of rebuilt games, in the shape the page reads."""
    rp = json.load(open(os.path.join(WDIR, f'{SEASON}-w{week}-replay.json'),
                        encoding='utf-8'))
    rid_of = rosters_for(week)
    line_of = lineups_for(week)
    games, orphans, swaps = [], [], []

    for g in rp['games']:
        names = [t['team'].strip().strip('*').strip() for t in g['teams']]
        byname = rid_of.get(g['matchup_id'], {})
        rids = [byname.get(n) for n in names]
        if None in rids:
            orphans.append(f'w{week} m{g["matchup_id"]}: ' +
                           ' / '.join(n for n, r in zip(names, rids) if r is None))
            continue

        teams = [dict(ident[r]) for r in rids]    # copies: the swap is per game
        swap = kit_clash(teams)
        if swap:
            swaps.append(f'w{week} m{g["matchup_id"]}: {swap}')

        players, src, ev = [], [], []
        pidx, sidx = {}, {}
        for e in g['timeline']:
            key = (e['player'], e['pos'], e.get('nfl') or '')
            if key not in pidx:
                pidx[key] = len(players); players.append(list(key))
            gid = e.get('game_id') or ''
            if gid not in sidx:
                sidx[gid] = len(src); src.append(gid)
            fl = ((FLAG_TD if e.get('td') else 0) |
                  (FLAG_GO if e.get('go_ahead') else 0) |
                  (FLAG_RES if e.get('residual') else 0))
            fc = e['fc']
            # kind and yards are last because the field needs them and the feed
            # rows do not: a reader gets the sentence, the field gets the pose
            # to strike and the distance to cover. yards is null wherever the
            # replay has no distance (a sack, a fumble, an extra point), and the
            # field stages those standing still rather than inventing a gain.
            ev.append([fc['sec'], fc['qtr'], fc['clock'], e['side'], pidx[key],
                       round(e['pts'], 2), e['text'] or '', fl,
                       round(e['score'][0], 2), round(e['score'][1], 2),
                       sidx[gid], e.get('nfl_qtr') or '', e.get('nfl_clock') or '',
                       e['kind'], e.get('yards')])

        games.append({
            'm': g['matchup_id'],
            't': [{'rid': t['rid'], 'name': t['name'], 'logo': t['logo'],
                   'c1': t['c1'], 'c2': t['c2'], 'abbr': t['abbr']}
                  for t in teams],
            'f': [round(t['final'], 2) for t in g['teams']],
            # who each side actually started that week, so nothing on the
            # field is a player who is not on one of these two teams
            'r': [line_of.get(g['matchup_id'], {}).get(r, []) for r in rids],
            'lc': g['lead_changes'], 'td': g['touchdowns'],
            'p': players, 'src': src, 'ev': ev,
        })

    for sw in swaps:
        print('  kit clash,', sw)
    if orphans:
        print('  UNRESOLVED SIDE (left out of the feed):')
        for o in orphans:
            print('   ', o)
    return {'season': SEASON, 'week': week, 'windows': rp['windows'], 'games': games}


def crests(ident):
    """Sixteen small files instead of one 1.1mb blob.

    The resized logo json is a single base64 payload that has to arrive whole
    before anything can be drawn, and the lobby shows all sixteen. As webp at
    112px the same crests come to about 70kb for the set and load per card.
    """
    import base64, io
    from PIL import Image
    src = json.load(open(os.path.join(ROOT, 'scfl-team-logos-resized.json'),
                         encoding='utf-8'))
    out = os.path.join(ROOT, 'crests')
    os.makedirs(out, exist_ok=True)
    n = tot = 0
    for t in ident.values():
        k = t['logo']
        if not k or k not in src:
            continue
        im = Image.open(io.BytesIO(base64.b64decode(src[k].split(',', 1)[1])))
        im = im.convert('RGBA').resize((112, 112), Image.LANCZOS)
        p = os.path.join(out, f'{k}.webp')
        im.save(p, 'WEBP', quality=82, method=6)
        n += 1; tot += os.path.getsize(p)
    print(f'  crests/ {n} files, {tot // 1024}kb')


HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>The Replay Room &mdash; SCFL NewsRoom</title>
<meta name="description" content="__BLURB__">
<meta name="scfl:kicker" content="The Replay Room">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Skirt Chasers &mdash; Dynasty League Magazine">
<meta property="og:title" content="The Replay Room">
<meta property="og:description" content="__BLURB__">
<meta property="og:url" content="https://watsoncapitalinvest-dot.github.io/Claude/__OUT__">
<meta property="og:image" content="https://watsoncapitalinvest-dot.github.io/Claude/__OG__">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://watsoncapitalinvest-dot.github.io/Claude/__OG__">
<link rel="icon" href="newsroom-favicon.png">
</head><body>
"""

CARD = """<!doctype html><meta charset="utf-8"><style>
html,body{margin:0;width:1200px;height:630px;background:#17181c;color:#fffdfb;
 font-family:Georgia,serif;}
.w{padding:52px 60px;height:630px;box-sizing:border-box;display:flex;
 flex-direction:column;justify-content:space-between;}
.f{font-family:-apple-system,'Segoe UI',sans-serif;font-size:14px;font-weight:900;
 letter-spacing:.3em;text-transform:uppercase;color:#c20f16;}
h1{font-size:72px;line-height:1.02;margin:14px 0 0;font-weight:900;letter-spacing:-.02em;}
.d{font-style:italic;font-size:21px;color:#9b9ba4;margin-top:16px;max-width:900px;}
.g{display:flex;gap:46px;}
.g div b{display:block;font-size:40px;font-weight:900;font-variant-numeric:tabular-nums;}
.g div span{font-family:-apple-system,'Segoe UI',sans-serif;font-size:11px;
 font-weight:800;letter-spacing:.15em;text-transform:uppercase;color:#9b9ba4;}
.bar{height:8px;background:#c20f16;}
.gold{height:4px;background:#d8b45a;}
</style><div class="bar"></div><div class="gold"></div><div class="w">
<div><div class="f">The Replay Room</div><h1>Watch the<br>week back</h1>
<div class="d">__D__</div></div>
<div class="g">__G__</div></div><div class="gold"></div><div class="bar"></div>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, help='just this one; default is all of them')
    a = ap.parse_args()

    weeks = sorted(int(m.group(1)) for m in
                   (re.search(r'-w(\d+)-replay\.json$', f)
                    for f in glob.glob(os.path.join(WDIR, f'{SEASON}-w*-replay.json')))
                   if m)
    if not weeks:
        sys.exit('no replay files -- run scripts/replay.py first')

    ident = identity(weeks)
    json.dump({'note': 'roster_id -> current name and crest. Keyed by id because '
                       'franchises get renamed mid-season and a lookup by name '
                       'silently loses the crest when they do.',
               'teams': {str(k): v for k, v in sorted(ident.items())}},
              open(os.path.join(ROOT, 'team-identity.json'), 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)
    print(f'  team-identity.json {len(ident)} franchises')
    crests(ident)

    built, plays, flips = [], 0, 0
    for w in (weeks if a.week is None else [a.week]):
        f = feed(w, ident)
        p = os.path.join(WDIR, f'{SEASON}-w{w}-watch.json')
        json.dump(f, open(p, 'w', encoding='utf-8'),
                  separators=(',', ':'), ensure_ascii=False)
        n = sum(len(g['ev']) for g in f['games'])
        print(f'  w{w}: {len(f["games"])} games, {n:,} plays, '
              f'{os.path.getsize(p) // 1024}kb')
        built.append(w)
        plays += n
        flips += sum(g['lc'] for g in f['games'])

    # the index is what the page asks first, so it decides which weeks exist
    allw = sorted(set(built) | set(
        int(m.group(1)) for m in
        (re.search(r'-w(\d+)-watch\.json$', f)
         for f in glob.glob(os.path.join(WDIR, f'{SEASON}-w*-watch.json'))) if m))
    json.dump({'season': SEASON, 'weeks': allw},
              open(os.path.join(WDIR, 'watch-index.json'), 'w', encoding='utf-8'))

    per = round(plays / max(1, len(built)))
    blurb = ('Every matchup rebuilt out of the plays that really made the points, '
             'laid onto one sixty-minute clock. Pick a game and watch it back — '
             'the score moving, the lead changing, play by play.')
    html = (HEAD.replace('__BLURB__', blurb).replace('__OUT__', OUT).replace('__OG__', OG)
            + open(os.path.join(ROOT, 'scripts', 'tpl', 'replay.html'),
                   encoding='utf-8').read()
            + '</body></html>\n')
    open(os.path.join(ROOT, OUT), 'w', encoding='utf-8').write(html)
    print(f'  -> {OUT} ({len(html) / 1024:.0f}kb)')

    _s = importlib.util.spec_from_file_location(
        'ad', os.path.join(ROOT, 'scripts', 'build_addendum.py'))
    ad = importlib.util.module_from_spec(_s); _s.loader.exec_module(ad)
    g = ''.join(f'<div><b>{v}</b><span>{k}</span></div>' for k, v in [
        ('weeks to watch', len(allw)),
        ('games rebuilt', sum(1 for _ in allw) * 8),
        ('plays a week', f'{per:,}'),
        ('lead changes', flips)])
    ad.shoot(CARD.replace('__D__', ad.esc(blurb)).replace('__G__', g), OG, 'replay-card')


if __name__ == '__main__':
    main()
