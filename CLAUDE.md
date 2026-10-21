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

Real NFL plays laid onto a 60-minute fantasy clock. Nothing is invented: the
plays, the yardage and the order are real; only the clock is synthesised. A
Monday-night 30-yard touchdown catch becomes a late-fourth-quarter 30-yard
touchdown catch. **Time is told in game time only** — quarters and the clock,
never NFL broadcast windows, in the copy or in the share blurb.

Points no play explains (mostly team defence `pts_allow`) are carried as
flagged residuals so running totals land on the true final. They are never
narratable.

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
- Heat rankings may be used; **do not reproduce the angry quotes**. Lines
  chosen for publication are banter, not shots, and run past John first.
- api.sleeper.app is blocked from this container. The fetch runs in
  `.github/workflows/fetch-week.yml` and comes back through git. GitHub keeps
  only one pending run per concurrency group, so rapid dispatches cancel each
  other — week 2 was lost that way.
