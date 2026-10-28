#!/usr/bin/env python3
"""One image brief per game report: the play that mattered, in the two kits.

    python3 scripts/build_play_art.py --week 7

John's idea. Every matchup's article opens on a picture of a play from that
matchup, drawn as though it happened for the fantasy side that owned the man
rather than for his NFL club. This writes the prompt for each one.

NOTHING HERE IS INVENTED. The play comes out of the replay timeline with its
player, action, yardage, fantasy clock, points and the score either side of it.
The jersey number and the build come out of nflverse players.csv. What the
picture adds -- the goal line, the beaten defender, the stadium -- is the
conceit, and the caption only ever claims the derived half.

WHICH PLAY. The obvious rule is "the play that put them in front", and it is
wrong on its own: go_ahead flags EVERY lead change, so the last one in a rout
is a five-yard run at 0:25 of the first quarter worth 0.50, and in one game it
was a team defence with no player, no number and no body to draw. So:

  the last lead change, when the game was close (margin under 25), the play was
  worth 5 or more, and a named man made it -- otherwise the biggest single play
  of the game by a named man.

That gives the decider in a tight game and the highlight in a blowout, and it
is happy to pick a loser: week 7's best picture by a street is Bo Nix's
sixty-two-yard run, which was the biggest play on the field in a game the
Killer Klowns lost by 5.68.

WHAT IT CANNOT DO. Two slots are left as marked blanks rather than guessed:

  - playing colours, which come from team-kits.json. They are not sampled from
    the crests. Four crests are photographs -- a horror still, a Star Wars
    still, a coffee mug -- and sampling those returns skin tones and sky.
  - what the player looks like. Every headshot host is refused by this
    container's egress proxy, the same way api.sleeper.app is, so there is no
    source in here to check a likeness against. A guess from memory is how this
    desk once published Marvin Harrison at 54 years old.

A prompt with a blank in it still gets written, with the blank marked, because
seven-eighths of a brief is worth having and the gap is obvious on the page.
"""
import argparse, csv, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, 'week-data')
OUT = os.path.join(ROOT, 'docs', 'play-art')


def players_index():
    """display_name + position -> row. Never an abbreviated name.

    Sleeper leaves gsis_id null for fringe players -- Emanuel Wilson has none --
    so the join is the full display name plus the position, and a name that
    lands on more than one row is reported rather than resolved. Thirteen
    running backs in here are called Wilson.
    """
    idx = {}
    with open(os.path.join(ROOT, '.nflverse', 'players.csv'), errors='replace') as f:
        for r in csv.DictReader(f):
            idx.setdefault((r['display_name'].strip(), r['position']), []).append(r)
    return idx


def pick_play(game):
    """The play the picture is of, and why it was picked."""
    live = [e for e in game['timeline'] if not e.get('residual')]
    named = [e for e in live if e['pos'] != 'DEF']
    if not named:
        return None, ''
    flips = [e for e in live if e.get('go_ahead')]
    last = flips[-1] if flips else None
    if (game['margin'] < 25 and last and last['pos'] != 'DEF' and last['pts'] >= 5):
        return last, 'the last lead change, in a game decided by %.2f' % game['margin']
    return max(named, key=lambda e: e['pts']), 'the biggest single play of the game'


# --- variety, and where it comes from -----------------------------------------
# The first three of these came back looking like the same picture three times:
# one man crossing a goal line left to right, low sideline camera, night, mud,
# a pylon. That is what a fixed template produces, and a magazine running eight
# of them a week cannot have eight of the same photograph.
#
# So the camera and the light vary -- but off the play rather than at random,
# because an arbitrary variation is a decision nobody can check. The camera
# comes from what kind of play it was and how far it went; the light comes from
# the quarter it happened in, which gives four looks across eight games and is
# a real fact about the afternoon.

# The camera is chosen from the same band as the pose, and from the same
# variant. They used to be picked independently, which produced a brief saying
# "coming almost straight at the camera with the ball above his head" four
# lines above "he has gone low for a ball at his ankles". A shot list that
# contradicts the thing it is shooting is worse than no shot list.
CAMERA = {
    'kick': ('Shot from low and behind, in line with the kick, the ball already away and '
             'climbing out of frame. The kicker and the holder are dark against the '
             'lights.',),
    'pass-short': ('Shot from the side at chest height and close in. The rusher coming '
                   'off the edge is enormous in the foreground and out of focus; the '
                   'quarterback is beyond him, sharp, hemmed in by his own linemen.',),
    'pass-deep': ('Shot from low and behind his throwing shoulder, looking down the line '
                  'of the throw. He is large in frame, the field opening away past him, '
                  'the ball small and already gone.',),
    'catch-crowd': ('Shot from inside the end zone, low, looking up. All of them are '
                    'above the camera and against the sky, arms up, and you are looking '
                    'into the underside of the leap.',),
    'catch-stretch': (
        'Shot from the side, the lens almost on the ground, so his whole body is laid '
        'out flat across the frame at the height of the grass and nothing is under him.',
        'Shot low and close from the front, tight on him, the ball and his hands nearest '
        'the camera and his face right behind them.'),
    'catch-deep': (
        'Shot from behind and above him, travelling with him, so you see what he sees: '
        'the ball dropping in, the empty grass beyond, the defender below the frame.',
        'Shot from the side and low, both men silhouetted together against the lights at '
        'the top of the leap, the ball the only clearly lit thing.'),
    'run-pile': ('Shot from the goal line itself, at the height of a man\'s knees, '
                 'looking straight into the pile as it comes at the camera.',),
    'run-break': ('Shot tight from the side on a long lens, level with him, the tangle of '
                  'linemen compressed into a wall of out-of-focus colour behind.',),
    'run-open': (
        'Shot from the sideline, low and wide, tracking with him. He is in full profile '
        'crossing the frame, both feet off the ground.',
        'Shot from the front and low, slightly below him, so the stiff-arm comes out of '
        'the picture toward the camera.'),
    'run-alone': ('Shot from a long way behind on a long lens, him small and sharp in the '
                  'middle of an empty field, everything else soft. The scale of the gap '
                  'is the subject.',),
}

LIGHT = {
    1: ('Late afternoon, the sun low and raking in from one side, long hard shadows '
        'thrown right across the turf, the floodlights only just coming on and still '
        'pale against the sky. Warm gold and long brown shadow.'),
    2: ('Dusk. The sky overhead still a deep blue, the floodlights now the stronger '
        'light and burning white. Cold blue sky against warm white light, the two '
        'meeting on the players.'),
    3: ('Full night. A black sky, no horizon, the floodlights hard and smoky, every '
        'figure rim-lit and the ground lit in pools. Near-black and gold.'),
    4: ('Night, and raining. The rain visible in the floodlight beams as drifting '
        'silver, standing water on the turf throwing the lights back, everything wet '
        'and running. Near-black, silver and cold white with amber underneath.'),
}


def band(play):
    """Which moment-template a play falls into. Used to spot collisions."""
    txt = play.get('text') or ''
    yd = play.get('yards') or 0
    if play['pos'] == 'K':
        return 'kick'
    if play['pos'] == 'QB' and 'pass' in txt:
        return 'pass-short' if yd <= 10 else 'pass-deep'
    if 'catch' in txt:
        if yd <= 10 and play.get('td'):
            return 'catch-crowd'
        return 'catch-deep' if yd >= 35 else 'catch-stretch'
    if yd <= 5:
        return 'run-pile'
    if yd <= 20:
        return 'run-break'
    return 'run-open' if yd < 40 else 'run-alone'


def camera(play, nth=0):
    opts = CAMERA[band(play)]
    return opts[nth % len(opts)]


def action(play, nth=0):
    """The moment inside the play, chosen by how far it went.

    Bands that can collide inside one week carry two variants, and the choice is
    made on how many games have already used that band -- not on the game index,
    which looked right and was not: week 7's two forty-eight-yard touchdown
    catches are games 5 and 7, both odd, so a parity test handed them the same
    variant and they came back as the same photograph with different shirts.

    The first version of this put everybody at a goal line with a defender
    diving behind them and a pylon in shot, which is one photograph taken eight
    times -- and worse, it told the reader nothing. A sixty-two-yard run and a
    three-yard touchdown are not the same event and must not be the same
    picture. So the moment comes off the distance: a short touchdown is a pile,
    a medium run is the break through the line, a long one is open field, a very
    long one is a man entirely on his own. Only the short plays get the goal
    line, because only on a short play is the goal line what you would see.
    """
    txt = play.get('text') or ''
    yd = play.get('yards') or 0
    td = bool(play.get('td'))
    pos = play['pos']

    if pos == 'K':
        return ('The kicker is through the ball, plant foot off the ground, kicking leg '
                'at full extension, head still down. The holder is on one knee in front '
                'of him and the line is braced across the frame behind. Nobody is '
                'celebrating yet.')

    if pos == 'QB' and 'pass' in txt:
        if yd <= 10:
            return ('A goal-line throw, and it is crowded. The quarterback has stepped up '
                    'into a pocket that is collapsing around him, ball just gone from his '
                    'hand, two linemen locked up either side of him and a rusher coming '
                    'off the edge with an arm outstretched. Bodies everywhere, no open '
                    'space anywhere in the frame.')
        return ('The quarterback has set his feet and let it go deep, ball just leaving '
                'his hand and already climbing out of the top of the frame, his arm still '
                'following through and his eyes a long way downfield. One rusher is '
                'arriving late and low at his legs. He has not been hit yet.')

    if 'catch' in txt:
        if yd <= 10 and td:
            return ('A touchdown caught in a crowd. He has gone up between two defenders '
                    'in the back of the end zone and taken it at the high point with both '
                    'hands, arms fully extended above three sets of other hands, body '
                    'twisted, feet off the ground and about to come down. It is a '
                    'scramble, not a clean catch.')
        if yd >= 35:
            return (
                ('Deep, and over the shoulder. He is at full sprint with his head turned '
                 'back and up, both hands reaching away from his body for a ball that is '
                 'still a foot from his fingers and falling into frame. The defender is a '
                 'stride behind and already beaten, reaching at his back. Open grass in '
                 'front of him and nobody in it.'),
                ('High, and contested. Both men have left the ground at the same instant '
                 'and are turned to face each other in the air, bodies twisted together, '
                 'four hands on or near the ball at the very top of the leap. He has it '
                 'and the defender has his forearm. Neither of them has landed.'),
            )[nth % 2]
        return (
            ('Full stretch and horizontal. He has left his feet entirely and is stretched '
             'flat out parallel to the ground, both hands on the ball, completely '
             'committed, with nothing underneath him yet. The defender has turned the '
             'wrong way and is behind his shoulder.'),
            ('Caught sitting down. He has gone low for a ball at his ankles, both hands '
             'under it, knees buckling and his backside about to hit the turf, head bent '
             'right over it to watch it in. The defender has come through him a fraction '
             'late and high, over the top of his shoulder.'),
        )[nth % 2]

    # runs
    if yd <= 5:
        return ('A short one, and it is a pile. He is driving low into a wall of bodies '
                'at the goal line, shoulders down, legs still churning, the ball wrapped '
                'in both arms, two defenders already on him and a third coming over the '
                'top. Mud and bodies, no daylight anywhere.')
    if yd <= 20:
        return ('The break. He is coming through the line at the moment it opens, one '
                'hand down on the turf for balance, a defender\'s arm sliding off his '
                'hip and another grabbing at empty air behind him. Linemen on both sides, '
                'still tangled. He is about to be clear and is not clear yet.')
    if yd < 40:
        return (
            ('Open field. He is at full stride with nobody within touching distance, one '
             'pursuer running an angle at him from deep on the far side and still a long '
             'way off. No line of scrimmage, no end zone, no pylon -- just turf and the '
             'two of them.'),
            ('The stiff-arm. He has planted a straight arm into the facemask of the one '
             'man who got to him and is pushing off it, his whole weight going through '
             'it, the defender\'s head snapped back and his feet leaving the ground. The '
             'ball is in the other arm. Nobody else is close.'),
        )[nth % 2]
    return ('Completely alone. He is at full sprint, upright now, head turned back over '
            'his shoulder to see where everybody went, the ball loose in one hand at his '
            'side. The nearest man is thirty yards behind him and out of focus. Nothing '
            'else is in the frame but grass.')


def look_line(play, looks):
    """What the man with the ball looks like, or a marked blank.

    Never inferred. There is no source for a likeness in this container, and a
    guess from memory is how this desk once published Marvin Harrison at 54.
    """
    v = looks.get(f'{play["player"]}|{play["pos"]}')
    if not v:
        return (f'<<APPEARANCE of {play["player"]}: skin tone, hair, facial hair, '
                f'tattoos. One line. No headshot is reachable from this container, '
                f'so John fills this. Leave it out rather than guess.>>')
    return (f'He is {v}. Do not attempt a portrait likeness of any real person: the '
            f'face is shadowed under the helmet with the facemask across it, and he '
            f'is identified by the kit, the number and the build rather than by his '
            f'features.')


def kit_line(k, who):
    if not k.get('primary'):
        return (f'<<KIT for {k["team"]}: jersey, trousers and helmet, trim. '
                f'Fill from team-kits.json before running.>>')
    bits = (f'{who} wears {k["primary"]}: {k["primary"]} jersey, {k["secondary"]} '
            f'helmet and {k["secondary"]} trousers, {k["trim"]} at the collar, on the '
            f'facemask and down the sleeve and the leg.')
    # 'wear' is prompt-facing. 'notes' is this desk talking to itself -- which
    # team a colour clashes with, why a trim is only a trim -- and it never
    # reaches the graphics AI, because anything in a brief that is not an
    # instruction is something for it to get wrong.
    if k.get('wear'):
        bits += ' ' + k['wear']
    return bits


TEMPLATE = """SUBJECT

{subject}

CANVAS

Landscape, 1200 x 800 pixels, 3:2. The man with the ball is centred, because this image is cropped and printed small inside a magazine page. It must read at the size of a postage stamp: one figure, one clear silhouette, one direction of travel.

THE CAMERA

{camera}

THE ACTION

{action}

THE TWO KITS

These are not NFL teams. The colours below are the whole point of the picture and must be exact.

{kit_scorer}

The number {number} is on his chest and on both sleeves, in a colour that reads against the jersey. No name, no other numbers anywhere in the picture.

{kit_other}

The two kits must never be confused for one another at a glance.

THE MAN WITH THE BALL IS REAL AND HIS BUILD IS NOT GENERIC. He is {height} and {weight} pounds. Draw that build and not a default athlete.

{appearance}

The beaten man is nobody. His face is not visible, he is turned away or in shadow, and his helmet stays on.

LIGHT

{light}

The man with the ball carries a hard gold rim light along his back and shoulders, the brightest and warmest thing in the picture. The beaten man is darker, with only a cold edge. A full crowd behind, out of focus, in the colours of the side he is scoring against. Churned turf and mud underfoot.

He is moving {direction} across the frame.

PALETTE

The light described above, and the two kits' own colours. Gold appears only on the man with the ball.

STYLE

Painted, not photographic and not a 3D render. Opaque acrylic and airbrush, the way action-adventure paperback covers and arcade cabinet panels were painted in the mid-1980s: visible brush and airbrush modelling, deep saturated colour, firm dark linework holding the figures, hard cel-like shadow edges, a faint print halftone texture across the whole surface. Heroic exaggerated proportions. It should look hand-painted in 1985 and printed slightly out of register.

HARD CONSTRAINTS

Two players only. No referees, no linemen, no sideline, no bench, no coaches, no faces in the crowd.

The only words allowed anywhere in the image are a club name on a helmet. No other words, no other numbers, no wordmarks, no watermarks, no signature, no scoreboard text, no banner text, no signage, no sponsor boards, no advertising hoardings.

No real sports team crests, no league marks, no club badges, no real-world logos of any kind.

Keep the whole of the man with the ball inside the middle 60 per cent of the frame width, clear of all four edges, because the image is cropped.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, required=True)
    ap.add_argument('--season', default='2026')
    a = ap.parse_args()

    rp = json.load(open(os.path.join(WDIR, f'{a.season}-w{a.week}-replay.json'),
                        encoding='utf-8'))
    kits = json.load(open(os.path.join(ROOT, 'team-kits.json'), encoding='utf-8'))['teams']
    looks = json.load(open(os.path.join(ROOT, 'player-looks.json'),
                           encoding='utf-8'))['players']
    # The replay carries team names and no roster_id, and team-kits.json is keyed
    # by roster_id on purpose, because a renamed franchise drops out of a
    # name-keyed file. So resolve through the week file, which has both, on a
    # normalised name -- the week files carry trailing spaces and asterisks.
    wk = json.load(open(os.path.join(WDIR, f'{a.season}-w{a.week}.json'), encoding='utf-8'))
    norm = lambda t: re.sub(r'[^a-z0-9]', '', (t or '').lower())
    rid = {norm(t['team']): t['roster_id'] for gg in wk['games'] for t in gg['teams']}
    idx = players_index()
    os.makedirs(OUT, exist_ok=True)
    gaps = []
    seen = {}          # band -> how many games have used it already this week

    for gi, g in enumerate(rp['games']):
        play, why = pick_play(g)
        if not play:
            print(f'  game {gi}: no play with a named man in it -- skipped')
            continue
        sides = [t for t in g['teams']]
        scorer, other = sides[play['side']], sides[1 - play['side']]
        ks = kits.get(str(rid.get(norm(scorer['team']))), {'team': scorer['team'].strip()})
        ko = kits.get(str(rid.get(norm(other['team']))), {'team': other['team'].strip()})

        rows = idx.get((play['player'], play['pos']), [])
        if len(rows) != 1:
            gaps.append(f'game {gi}: {play["player"]} ({play["pos"]}) matched '
                        f'{len(rows)} rows in players.csv -- number and build unresolved')
            num, ht, wt = '??', '??', '??'
        else:
            r = rows[0]
            num = r['jersey_number'] or '??'
            h = r['height']
            ht = f'{int(h)//12} foot {int(h)%12}' if h.isdigit() else '??'
            wt = r['weight'] or '??'
        if '??' in (num, ht, wt):
            gaps.append(f'game {gi}: {play["player"]} is missing a number or a build')
        for k, side in ((ks, 'scorer'), (ko, 'opponent')):
            if not k.get('primary'):
                gaps.append(f'game {gi}: no kit for {k["team"]} (the {side})')
        if f'{play["player"]}|{play["pos"]}' not in looks:
            gaps.append(f'game {gi}: no appearance on file for {play["player"]}')

        # the subject line used to end "at night under stadium floodlights" on
        # every brief, which flatly contradicted the LIGHT section as soon as
        # that started varying by quarter. Both come off the same fact now.
        when = {1: 'in the low late-afternoon sun',
                2: 'at dusk under the floodlights',
                3: 'at night under stadium floodlights',
                4: 'at night, in the rain, under stadium floodlights'}
        # "of the StillTheCream" -- some club names carry their own article
        club = scorer['team'].strip()
        club = club if club.lower().startswith('the ') else f'the {club}'
        club = club if ' ' in club[4:] or not club[4:].lower().startswith('still') else club[4:]
        b = band(play)
        nth = seen.get(b, 0)
        seen[b] = nth + 1
        subject = (f'{play["player"]} of {club}, '
                   f'{play["text"]}, {when[int(play["fc"]["qtr"])]}.')
        body = TEMPLATE.format(
            subject=subject, action=action(play, nth), camera=camera(play, nth),
            light=LIGHT[int(play['fc']['qtr'])],
            # adjacent pages should not mirror each other
            direction='left to right' if gi % 2 == 0 else 'right to left',
            kit_scorer=kit_line(ks, 'THE MAN WITH THE BALL'),
            kit_other=kit_line(ko, 'THE BEATEN MAN'),
            number=num, height=ht, weight=wt,
            appearance=look_line(play, looks))
        slug = re.sub(r'[^a-z0-9]+', '-',
                      f'{scorer["team"]}-{other["team"]}'.lower()).strip('-')
        path = os.path.join(OUT, f'week-{a.week}-g{gi}-{slug}.txt')
        open(path, 'w').write(body)
        print(f'  g{gi} {why:52} -> {os.path.basename(path)}')
        print(f'      {play["player"]:22} #{num:4} {play["pts"]:5.2f}  '
              f'Q{play["fc"]["qtr"]} {play["fc"]["clock"]}  {play["text"]}')

    if gaps:
        print(f'\n  {len(gaps)} gaps, every one of them left as a marked blank:')
        for g in gaps:
            print('   -', g)


if __name__ == '__main__':
    main()
