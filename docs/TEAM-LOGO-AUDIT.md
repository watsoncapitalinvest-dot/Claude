# Team Logo Audit

What's actually on file for all 16 team logos, checked byte-by-byte against
`scfl-team-logos.json` (full-size originals) and `scfl-team-logos-resized.json`
(the 160×160 versions the app actually uses). Done because the Asset Vault
now surfaces every logo directly (see below), and a fake logo presented as
real art is worse than an obvious gap.

## The finding: 2 teams are running the exact same placeholder image

**Big Blue** and **Wookie Leaks** have byte-identical art in both the
full-size and resized files — a generic blue robot-head icon (a default
avatar style, not a custom crest). Nobody ever uploaded real art for one or
both of these, and whatever produced the roster art fell back to the same
stock icon for both. The app now flags this automatically wherever these
logos appear (Asset Vault, the desk-scene compositing) — the fix is real art
for at least one of them, ideally both.

## 3 more that read as the same generic style, just not identical

Not caught by the automatic check above (it only flags byte-for-byte
duplicates, on purpose — a "looks similar" heuristic would throw false
positives on legitimately-simple crests). But laid out side by side, these
three are the same flat-color-circle default-avatar style as the Big
Blue/Wookie Leaks pair, just recolored, and don't read as a real team crest:

- **The Beaver Eaters** (pink)
- **Hairy Gumbas** (orange)
- **Heavy Hitters** (cyan)

## Teams with real, custom art on file

The other 11 are legitimate chosen images — hand-made crests or a deliberate
photo/movie-still pick that matches the team's running joke:

| Team | What it is |
|---|---|
| The Machines | A horror-movie masked-killer still (Michael Myers-style) |
| Guido Haters | Custom crest, Italian-flag shield, raised middle finger |
| Killer Klowns | Custom crest, a group of horror clowns |
| Lil Chops | Custom crest, "Lil Chops" mascot lineup |
| New World Order | The real nWo wrestling logo |
| Pork Chop Express | Custom crest, cartoon pig + "The Pork Chop Express" |
| Powers of Pain | Custom crest, wrestling-poster style |
| Smoke Dragons | Custom crest, dragon + football (shown above) |
| Still The Cream | Custom crest, gothic top-hat figure |
| Master Jet-I | A *Star Wars* still (Anakin/Obi-Wan) |
| Horse Collars | A "POT HEAD" coffee-mug photo (the team's own joke, not a crest — intentional, not a gap) |

## Two small data-hygiene notes (not urgent, logging them anyway)

- **Smoke Dragons' full-size file is mislabeled**: the data URI says
  `image/png` but the bytes are actually a JPEG. Harmless today (browsers
  sniff the real format and display it fine), but worth fixing next time
  that file gets touched so it doesn't confuse anything that trusts the
  declared mime type.
- `scripts/add_logo.py` already has a `DEFAULTS` dict built for exactly this
  situation — "the stock ESPN avatar, by content hash" — but it's empty
  (`DEFAULTS = {}`). Nobody ever populated it. The Asset Vault's own
  duplicate check (above) now does this job live in the app, so `DEFAULTS`
  staying empty isn't blocking anything, but it's there if a script-side
  check is ever wanted too.

## What to do about it

Five teams could use real crest art: **Big Blue** (Jim Hunt), **Wookie
Leaks** (Coach Nick), **The Beaver Eaters** (Sheq), **Hairy Gumbas** (Tommy
Vertucci), **Heavy Hitters** (Jay). Whenever art shows up for any of them,
`python3 scripts/add_logo.py <slug> <path>` installs it — it resizes,
embeds the base64, and updates both logo files in one step.

## Where all 16 live now

Every team logo — placeholder or real — is in the app: **Executive Office →
Board Desk → Asset Vault → Team Logos**. That section is new; logos used to
only exist inside **Export Team Logos** (a bulk JSON download, still there,
different purpose) with no way to just look at one. The whole Asset Vault
is collapsible now too — see the app changelog / commit for that half of
this change.
