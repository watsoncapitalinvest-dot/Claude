# SCFL NewsRoom — house rules

## This repository is PUBLIC. The league can read it.

`watsoncapitalinvest-dot/Claude` is a public repo with GitHub Pages serving
from the default branch. Every file committed here is readable by the fifteen
other managers, and anything with a `<title>` gets listed in the catalog with a
share card attached.

So **none of this goes in the repo**: which players John is selling or buying,
what he thinks a trade partner will accept, who he is claiming off waivers,
where his roster is weak, what another team's weakness is. That is his hand.

This has already gone wrong once. Eight pages of planning — sell Kyler to
Wookie Leaks because they have the least room to say no; claim Chase McLaughlin
and Kimani Vidal; cut Cleveland — were published to the live site in the same
week John sat fifth in the waiver order behind four teams who would want the
same kicker. Nobody asked for any of it.

Strategy stays in the chat. If something genuinely needs writing down, it goes
somewhere outside this repo and John is told where.

## John decides what is an article. Then save it.

John's rule, in his words: *"save it every time I produce something in article
format. That means I like it enough to share"* — and the correction that
followed, because this desk read it too widely: *"This can stay in the chat. I
only want things that I give the article treatment to to be saved
automatically."*

So the trigger is **John giving something the article treatment**, not this
desk deciding a piece of analysis deserves one. An answer to a question is an
answer to a question. Research, a board, a recommendation, a trade read — those
belong in the chat, however much work went into them and however good the
numbers are. Publishing one unasked puts a page on a live site under the
league's masthead that nobody asked for.

Ask, or wait to be told. "Want this as a note?" costs one line.

Once John has given something the article treatment, producing it is not
finished until all three of these are true, in the same pass, without being
asked again:

1. **Saved** — committed and pushed. This container gets reclaimed. Pages have
   been lost to that before, which is why one-off builders live in `scripts/`
   and not in a temp directory.
2. **Filed** — in `site-index.json`, so it is reachable from The Full Record and
   from the app rather than only from a chat link that scrolls away.
3. **Sendable** — a title, an `og:description`, and an `og:image` that actually
   exists on disk. A page whose card was never built arrives as a grey
   rectangle in every app it is pasted into, and the sender cannot see that
   from their end.

Run `python3 scripts/check_filed.py` before saying a piece is done. It checks
all three and exits non-zero with what to run.

An article means something written for the league to read: a game report, a
record piece, an investigation. It does not mean a worked-out answer to one of
John's questions, however much research went into it — *"These aren't articles.
They are us talking and planning."*

Every issue ends on next week. A weekly issue closes with **What Sunday Is
Worth**: a written preview, then the fixture card.

The preview is **an article, not a list** — a paragraph a game, eight of them,
so all sixteen teams get covered and every one of them gets said something
about. Each paragraph bills the fixture, says what it is worth, and carries
what both sides did last week. Ordered so the biggest game leads and is not
buried fourth in a list of eight. The card underneath says who plays whom; the
prose says why anyone should care.

The voice is **Harry Doyle** — dry, flat, faintly amazed at what it is being
asked to describe, and funniest when it is most matter-of-fact. Short
sentences. The joke is never on a figure, it is on the situation the figure
describes: *"Smoke Dragons have lost three in a row and Guido Haters have lost
four. One of these runs ends on Sunday. The other one gets longer."* What it is
not is a results service — *"A beat B 96-73; C lost to D 76-83"* eight times in
a row is the thing that got this rewritten.

Every aside still hangs off a derived condition, so a line about a rout only
prints over a rout, and the quips characterise the **number**, never the shape
of an afternoon only the replay knows. "It was over early" is not derivable
from a margin. Neither is calling two 2-4 sides ".500".

A preview is about **what happens next**. Each paragraph leads on what the
result does — the record each side leaves at, the gap between these two, what
the division looks like after — and last week appears only where it carries a
hook. But a projected **division position** is not arithmetic: the other two
sides in a division play on the same Sunday and can win too, so the fixture
settles each side's record and the gap between the pair, and nothing else is
stated forward. Anything about the rest of the table is present tense.

The preview also pulls on **eighteen seasons**. `scripts/history.py` joins the
sixteen current `roster_id`s to `records.json` (lifetime records and titles,
2005–2025) and `rivalries.json` (107 pairwise series since 2008 — record,
playoff meetings, biggest win, worst loss, closest game, first year). *"Killer
Klowns have beaten THE MACHINES once in 27 meetings, and it was a 2024 playoff
game."*

**Both stored files stop at 2025**, so anything quoted as all-time is the
stored row plus this season out of the week files — a year-stale head-to-head
reads exactly like a correct one. `history.series()` normalises orientation
once, so `biggest` is always a's biggest win over b; leaving that flip to the
caller nearly printed the wrong game as the one defeat in a 26-1 series. A
thread runs at most twice an issue, and a side that will not resolve to a
franchise is **named in the build output** rather than quietly losing its past.

That page is **derived, not written**: `preview_prose()` and
`preview_blocks()` in `scripts/build_week_issue.py` read the fixtures out of
`sleeper-schedule.json` and the records, streaks, divisions and prior meetings
out of the table, and print only the true things they find. A fixture with
nothing to say about it gets the billing and stops. Eight paragraphs of
"should be a good one" is worse than no preview at all.

`scripts/build_notes.py` and `desk-notes.json` exist for short pieces John
asks for. `desk-notes.json` is **gitignored**, because what ended up in it was
our conversation. A longer piece gets its own builder in `scripts/`.

## Prose is derived, never asserted

Every figure in a published page comes out of a file in this repo, and the
sentence around it is computed from the same data rather than written beside
it. This has gone wrong often enough to be the first rule of the desk:

- "lost three of its next four" about a team that went 15-1-1 and won the title
- "one of them was not enough to win the game" when all ten won
- "the only week in the top ten that did not win" — true once, false forever
  after a second one joins it

If a claim counts, rank, compare or characterise, derive it. If it cannot be
derived, leave it out. Count-aware phrasing (`"That is" if n == 1 else
"Those are"`) is cheaper than a correction after publication.

## Figures are checked, not recalled

- Ages come from nflverse `players.csv` birth dates. A name search returned
  fathers instead of sons here (Marvin Harrison, 54; Pittman, 51).
- Player identity joins on the NFL's `gsis_id`, never on an abbreviated name.
  Sleeper stores `gsis_id` with a **leading space** — strip before use, and
  verify the id resolves against the play data before trusting it.
- Partial week files look like real ones. A week counts only once played, and
  that needs two tells: `min(points) >= 30` catches a week nobody has played,
  and the share of starters on exactly 0 catches a week half played (finished
  weeks run 1–6%, a Sunday evening reads 10%). One tell alone has flipped an
  article's conclusion twice.
- **`posteam` on a kickoff is the RECEIVING team.** Reading a kicker's own side
  off every play he appears on labelled Mevis as Philadelphia and Fairbairn as
  Tennessee. Only field goals and extra points identify a kicker's team.
- Sleeper will not report a player nobody owns, so anything about the waiver
  pool has to be computed from play-by-play — and then checked back against
  what Sleeper paid the owned ones. Kickers came out 63/63 exact; defences
  60/64, each miss one 2-point event.
- The two value scales both anchor the 1.01 at $100 and agree nowhere else.
  `dp-values.json` prices players; `draft-intel.json`'s `pickValueChart`
  prices picks and is deliberately steeper. Quoting one against the other
  reads fine and overvalues picks every time.

## The league, so the copy gets it right

16-team Superflex Dynasty · **NON-PPR** · no taxi · 2-round (32-pick) draft ·
19 roster spots (10 starters + 9 bench) + 2 IR · 14-week regular season,
playoffs from week 15 · 4 divisions of 4.

**16 teams, 16 owners** — one man each, no co-owners and nobody holding two.

The free-agent **count** is not a measure of anything. It sits near 500 all
season because it counts third-string tight ends and quarterbacks nobody here
would ever start. When the waiver pool matters, measure what is *worth adding*:
players who outscore the median man actually started at that position. That
runs **2 to 5 a week**, which is what everyone means when they say the wire is
bare. `scripts/waiver_depth.py` computes it.

Franchises get renamed mid-season (Forty2V → Horsecollars, Heavy Hitters →
Phins Phag). **Key standings and division tables by `roster_id`, never by
name**, or a renamed team drops out of the table entirely.

Bench comparisons must respect slot eligibility. Saying a manager started a WR
"over" an RB is tactically wrong — they were never competing for the seat.

## The replay model

The rebuilt games are watchable, and they are watched on the **broadcast**:
`broadcast-demo.html?w=7&g=0`. That page already had a field, a camera, sprites
and a scoreboard that worked, and the lesson of a long afternoon is that it
should have been pointed at real data rather than rebuilt from scratch — John:
*"we have built this whole thing before and it worked. Now we're worse than
when we first did it."*

`buildGame()` hands `step()` a `plays[]` array; `replayGame()` hands it the same
array built from a rebuilt week, and nothing downstream changes. With no `?w=`
the simulation still runs, for the demo.

`scfl-replay.html` is the **picker** — week tabs and eight matchup cards — and
every way into a game, including each issue's *Watch this one back*, lands on
the broadcast.

**Real**: for every play that scored — the player, the kind of play, the
yardage, the points, the quarter, and the order each side's plays run in.
**Not real**: where the ball sits, and the plays in between. These plays come
out of eight different NFL games at once, so there is no such thing as where
the ball was, and two rosters drawing on the same Sunday trade possession every
other snap — 66 per cent of week 7's possessions ran one or two plays, which
reads as the camera changing its mind rather than as football.

So the tape is **gathered into drives** and given what a drive needs and a box
score never records: the runs and throws between the scoring plays, and the
punt at the end of one that did not score.

**As few of those as the drive can be made to need** — John: *"I'd like as
minimal generated unnamed plays as possible."* Three things keep the count
down, and together they took the week from 54 per cent generated to 35:

- A drive is **started where its own real yardage can carry it**, not on the
  25. A field goal from the 11 used to need 64 yards of invented football to
  reach; the distance goes into the kickoff return or the punt, which are one
  play either way, instead of into six more. The spot a turnover leaves the
  ball on is the exception — that one is real and is not ours to move.
- A drive with **three plays of its own gets no cushion at all**. Only a drive
  too short to read as one is given a play or two.
- **A beat that moves the ball gets a play; one that does not gets a line on
  the play before it.** The fourth-down stop is a note, not a snap: 251 of them
  a week, all reading the same, became none. Those are **marked
CONNECTIVE PLAY in the ticker every time they appear**, they name nobody and
they score nothing, and the page's own footer says all of this. The clock,
already synthesised, may pull a play earlier to join its side's drive — **never
across a quarter**, so the quarter a play is credited to is still the quarter
the tape gives it and every published issue's "fourth-quarter" still holds.

The arithmetic that must survive any change here, and is checked in the
browser across all eight games: every scoring play present, each side's in tape
order, and the running score landing on the true final. **Down and distance are
not shown at all**, because the replay does not know them and this desk does
not invent them.

**Only men who played for these two sides that week are ever named on the
field.** The eleven come from the week file's own starters, carried in the feed
as each game's `r`. Topping them up from `scfl-rosters.json` put a July export
on a week-7 field, which can name somebody traded away months earlier.

**The plays come out of a playbook.** `ROUTES`, `PASS_CONCEPTS` and
`RUN_CONCEPTS` in `broadcast-demo.html` hold the route tree and twenty real
concepts, and the five eligible men run the combination rather than drifting
downfield together — on a screen the two outside receivers barely move, because
they are blocking. A route is read as cumulative offsets from where the man
lines up, lateral **positive toward his own sideline**, so one table serves
both sides of the formation.

Every concept carries the band of gains it can honestly account for: a
five-yard concept is never the caption on a 48-yard touchdown, and a run
concept never appears on a pass. A connective play picks its concept when the
sentence naming it is written and carries it on the play, so the field and the
ticker cannot disagree about what was called. That fit is checked over all
1,325 concepts a week.

You score in **the other team's end zone**. H attacks toward 0, which is `ezL`,
so `ezL` is painted and lettered for the AWAY side. The other way round, the
MACHINES scored in the MACHINES end.

A `gen` play is a quarterback's **passing yardage**, and the man who caught it
is almost always on another fantasy roster — so the quarterback is named and
**the catch is made by a figure with no name over his head**. It used to be
thrown to empty grass with a defender jogging after it, which reads as
incomplete while the ticker says it was completed for 48. 1,085 plays a week
looked that way.

And — John's rule — **every play by a named player is real**, which cuts
exactly one way: *"All starters should be on the field if possible unless
unnamed players need to be involved to make a play or fill non player roles
like linemen."*

So the starters are out there and named on every play, and the men without a
name are only the ones who have to be nameless — **whoever the ball passes
through on a play the tape does not have**. On a connective run that is the
quarterback and the back; on a connective pass the quarterback and the catcher;
on a kickoff or a punt the kicker. Everybody else is the starter he is,
blocking or running his route. That averages **4.8 of the 6 skill men named**,
and it is checked slot by slot across all eight games, every play — named where
he must be, blank where he must be, not eyeballed.

Two men can also shorten to the same label: A.J. Brown and Amon-Ra St. Brown
both came out as `A·Brown`, side by side in the same huddle. `shortName` keeps
the particle (`St. Brown`, `Van Ginkel`), and `lineUp` lengthens both labels if
any two of the eleven still read alike.

Kits come from `team-identity.json`, built off `team-kits.json` — the colours
John set per franchise for the magazine's play art — and the broadcast's own
guessed table is overwritten by them at load, so the field and the pictures in
the issue dress the same sixteen clubs alike. That table had Wookie Leaks and
BIG BLUE on the same blue.

Real NFL plays laid onto a 60-minute fantasy clock. A Monday-night 30-yard
touchdown catch becomes a late-fourth-quarter 30-yard touchdown catch. **Time
is told in game time only** — quarters and the clock, never NFL broadcast
windows, in the copy or in the share blurb.

That quarter comes from the broadcast window the play fell in (`WINDOWS` in
`scripts/replay.py`), and each window owns a fixed slice of the hour whatever
it holds. So a week whose scoring landed in the late Sunday games piles into
one quarter: week 7 game 0 is 44/68/93/4 across the four. It is not a replay
bug — it is the mapping — but it means a quarter can hold most of a game, and
rebuilding the mapping would move quarters that published issues have already
named.

Points no play explains (mostly team defence `pts_allow`) are carried as
flagged residuals so running totals land on the true final. They are never
narratable.

**The fantasy clock says nothing about the real world.** It is synthesised, so
a fantasy fourth quarter is not an evening and a fantasy first quarter is not
an afternoon. Deriving weather, light or a time of day from it is invention
dressed as arithmetic — week 7's play art was lit off the fantasy quarter and
came out with rain in a week nobody played in rain, and with open floodlit
bowls around two games played under a closed roof.

What is real about a play is on the tape and should be read off it. The
play-by-play carries `roof`, `weather`, `temp`, `wind`, `surface`, `stadium`
and `time_of_day` — a true timestamp on every play. `conditions()` in
`scripts/build_play_art.py` reads that row, and `TEAM_TZ` turns the home club
in the `game_id` into the stadium's own zone so the local clock is the local
clock. LA and LAR are both in that map, because Sleeper writes one and
nflverse the other.

So: the narrative runs on the fantasy clock, and anything depicting the world
the play happened in — light, sky, ground, indoors or out — runs on the real
one. Mud is the example worth remembering. It was hardcoded into every play
brief, dome floors included, until somebody asked whether it had been raining.

## Colour means something

Red `#c20f16` = won, or ahead. Blue `#0e8ab5` = lost, or behind. Gold
`#d8b45a` = the moment it changed, and playoff markers. Cream `#fffdfb`,
ink `#17181c`. Georgia serif for copy, system sans for furniture.

## Standing instructions

- **Chat corpora never enter the repo.** "Whatever we had before that's safe.
  It can't get out."
- Covers are generated by John's graphics AI. Briefs go in `docs/` as **plain
  text, instructions only** — "you have things in there that will only confuse
  the AI."
- Anything for another AI goes in a simple text file.
- **The masthead is the plaid one.** Adopted from week 7. The covers run
  `wordmark-alt-words.png` — the two words and the swash, cut off their cream
  paper by `scripts/cut_wordmark.py` — with **no panel behind it**: it carries
  its own gold keyline and sits straight on the art. The strapline under it is
  live type, not bitmap, so it is one string in the issue definition and stays
  crisp at any size.

  It is 1.9:1 where the old `wordmark.png` was 3.5:1, so it takes **38 per cent
  of the cover** rather than 21. `MAST` in `compose_cover.py` is 584 and every
  new **cover brief must ask for the top 35 per cent to be left clear**. Art
  drawn to the old brief needs a `cover.artDrop` in the week's written file or
  the strapline and the issue line land on the picture and cannot be read —
  week 7 needed 270. `compose_cover.py` fills the strip the drop opens with the
  picture's own sky mirrored rather than with black, so the taller masthead
  costs no band; only the rows above the subject may be mirrored (`artClear`),
  because reflecting the whole strip put a quarterback's helmet back in upside
  down. The drop also pushes the subject into the type bed, so `scrim()` comes
  on earlier and harder in proportion to it.

  **Back issues were deliberately not re-dropped.** Weeks 4 to 6 keep the old
  masthead and the layout they were published with. Rebuilding them to change a
  logo would reflow three live issues through every convention that has landed
  since.
- Heat rankings may be used; **do not reproduce the angry quotes**. Lines
  chosen for publication are banter, not shots, and run past John first.
- api.sleeper.app is blocked from this container. The fetch runs in
  `.github/workflows/fetch-week.yml` and comes back through git. GitHub keeps
  only one pending run per concurrency group, so rapid dispatches cancel each
  other — week 2 was lost that way.
