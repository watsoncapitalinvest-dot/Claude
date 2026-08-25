# The League Value Board — player values, ours instead of borrowed

Until now, every player dollar figure in the Trade Court (including the
Najee Harris table from this session) traced back to `dp-values.json` —
DynastyProcess's third-party dynasty market consensus. Real and
contemporaneous, but still someone else's read on a player, not this
league's. This is the replacement: **real weekly stats, scored on this
league's own scoring settings, ranked positionally, season by season.**

## How a player gets a number

1. **Real stats, real scoring.** For every season 2021–present, walk all 18
   NFL weeks via Sleeper's stats API (`getWeeklyStats`) and score each
   player's raw stat line through *this league's actual* `scoring_settings`
   (`scoreStats()` — already existed in the app, built for the draft
   calculator; reused here, not reinvented). A generic "PPR vs. half-PPR"
   bucket never enters into it — it's this league's real point values.
2. **Rank within position, that season.** Players need 4+ games on file to
   qualify (fewer than that and a per-game rate isn't trustworthy). Ranked
   by points-per-game within their position, for that season only.
3. **Positional rank → dollar value**, through the *same* tier/cut grid
   `tcPlayerFloor()` already uses (QB/RB/WR/TE tiers, already calibrated to
   real SCFL trades). Only the ranking **input** changes — from Sleeper's
   live consensus rank to our own real production that season.
4. **Blend two seasons**, 65% this year / 35% last, so one fluky week or a
   short DNP stretch doesn't swing a whole grade. A player who played last
   year but not at all this season (injury, inactive) gets last year's
   value at a 30% discount rather than falling off a cliff to zero.
5. **Age-decline multiplier**, position-specific, applied on top — dynasty
   value is an expectation of *future* production, not a report card, so a
   pure trailing-stats ranking isn't enough on its own. Age is computed
   *as of the season being valued*, not today, so grading a 2021 trade
   never uses information about how old the player is now.
6. **No stats on file at all** (a rookie traded before his first season) →
   falls back to his real SCFL draft slot, priced on the same real-trade-
   calibrated pick chart used everywhere else in the app — our own number
   again, not a guess.

## Why this can't leak hindsight (a structural guarantee, not a rule to remember)

Every step above only ever reads stats from the season being valued and
earlier — there's no "walk to the nearest available year in either
direction" the way the DynastyProcess snapshot lookup needed careful
`noFuture` flagging to avoid. The real-stats board simply never has
access to data past the season it's computing, by construction.

## The age curve, spelled out (a first pass, not a precision claim)

| Position | Decline starts | %/year after |
|---|---|---|
| RB | 26 | 13% |
| WR | 28 | 9% |
| TE | 30 | 8% |
| QB | 33 | 6% |

Well-known shapes (RB earliest and steepest, QB latest and gentlest) — a
reasonable, transparent starting point. Floored at 15% of peak value so
nobody goes to literal zero purely from age.

## What's NOT done yet (real scope calls, not oversights)

- **Only wired into Trade Court grading.** The War Room draft calculator
  and the "today's market value" lookups (`playerDollarValue`/
  `scflDpDollar`) still run on DynastyProcess. Swapping those too is a
  separate, smaller follow-up — didn't want to touch a different feature
  (drafting, not trade grading) in the same pass.
- **DynastyProcess is a silent fallback, not a visible comparison.** It
  still shows up automatically when the Value Board has no read on a name,
  but there's no UI yet showing "ours says X, market says Y" side by side.
- **Never tested against live data by me.** This session's sandbox can't
  reach Sleeper's API at all (same network block as everything else
  external) — every function above is verified with hand-checked synthetic
  data, not a real season walk. The math is right; the real walk needs a
  live run to fully prove out. Open Trade Court once for real and it'll
  build itself (one-time, cached, same "Refresh" button that already
  existed rebuilds it too) — if anything's off, that's where it'll show.
