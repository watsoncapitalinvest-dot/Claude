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


def action(play):
    """What is happening, in one paragraph, from the play's own kind."""
    yd = play.get('yards')
    td = play.get('td')
    pos = play['pos']
    if pos == 'QB' and 'pass' in (play.get('text') or ''):
        return ('The quarterback is at the top of his throwing motion, front foot planted, '
                'ball just leaving his hand, eyes downfield and away from the camera. One '
                'pass rusher is on him, an arm across his chest, too late. The receiver is '
                'not in the frame.')
    if pos == 'K':
        return ('The kicker is through the ball with his plant foot off the ground and his '
                'kicking leg at full extension, head still down. The holder is on one knee '
                'in front of him. Nobody else is in the frame.')
    if 'catch' in (play.get('text') or ''):
        return (f'The receiver has just taken the ball in at full stretch, both hands on it, '
                f'body turned back toward where it came from and feet about to come down on '
                f'{"the goal line" if td else "the turf"}. One defender is behind him and '
                f'below him, beaten, one arm still up at empty air. No other players in the '
                f'frame.')
    return (f'The runner is at full stride, left to right, '
            f'{"about to cross a white goal line painted across the turf in front of him" if td else "breaking into open ground"}. '
            f'The ball is in his outside arm, carried high and tight. His head is up and '
            f'turned slightly back toward the man he has beaten. Mud is flying from his '
            f'cleats. One defender is behind him and to his left, down on one knee with one '
            f'arm still outstretched at empty air, having missed the tackle. No other '
            f'players in the frame.')


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

Night. Stadium floodlights high behind and to one side, burning through drifting smoke as hard white flares. The man with the ball carries a hard gold rim light along his back and shoulders, the brightest and warmest thing in the picture. Everything else falls into warm amber and deep near-black. The beaten man is in shadow with only a cold blue-white edge. A full crowd behind, out of focus, in the colours of the side he is scoring against. Churned wet turf and mud underfoot.

PALETTE

Near-black, warm amber, gold, and the two kits' own colours. Gold appears only on the man with the ball.

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

        subject = (f'{play["player"]} of the {scorer["team"].strip()}, '
                   f'{play["text"]}, at night under stadium floodlights.')
        body = TEMPLATE.format(
            subject=subject, action=action(play),
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
