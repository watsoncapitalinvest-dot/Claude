# The retail app — what "simple and complete" needs

SCFL stays the driver. This is the list for the version a stranger can use.

Everything below was measured on 2026-10-30, not guessed. Two tests: the
weekly path run with the hand-made assets withheld, and run against a
synthetic 10-team 1-QB full-PPR league.

## What already travels

- **No LLM calls anywhere in the weekly pipeline.** `write_week.py` derives
  the headlines, deks and paragraphs. Marginal cost per issue is zero and
  nothing breaks when somebody's API key lapses.
- **`replay.py` reads `wd['scoring']`** — the league's own settings. PPR,
  superflex, any scoring, it just computes.
- **The prose asserts nothing about league shape.** 6,298 words generated for
  a 10-team league, zero instances of "16-team", "four divisions", "14-week",
  "superflex" or "non-PPR".
- Six of the eight weekly scripts ran clean on a league shaped nothing like
  this one.

## Onboarding — get a league in

- Connect by Sleeper league ID; `fetch_week.py` already accepts one
- Crests from Sleeper avatars, not hand-drawn files
- Kit colours extracted from the avatar, run through `sep()` / `kit_ok()` so
  no matchup reads alike
- Franchises and handles read from the league, replacing `scfl-franchises.json`
- Records and rivalries walked back through `previous_league_id` — and
  **optional**, because a new league has no past

## Stop assuming SCFL

- The five hand-made files degrade gracefully instead of hard-crashing:
  `scfl-team-logos-resized.json`, `team-kits.json`, `scfl-franchises.json`,
  `records.json`, `rivalries.json`, plus `crests/`
- Team count and slots read from `roster_positions`, not frozen constants
- Sweep the remaining league-shape literals the same way

## Run itself

- One workflow: fetch → replay → write → cover → issue → publish, weekly cron
- A concurrency group **per league**, not one global — that is how week 2 was
  lost
- Ship a default cover plate; the app sets the week number on it. No model in
  the loop

## Don't publish nonsense

- A sanity gate before publish: figures in plausible ranges, scores reconcile,
  every team present
- If the gate trips, hold the issue. Never ship it quietly

## Light enough to read

- Images as files, not base64 — an issue goes from 7.8MB to a few hundred KB.
  Week 7 carries 12 images at 424–744KB each, inlined, with the same cover
  also sitting unused on disk beside it
- A working share card on every issue. That is how it spreads

## Optional uploads — each makes it better, none required

- Cover plate
- Crests
- Group chat, **with commissioner review before publish**

## Decide before building, not after

- Licensing: nflverse and Sleeper commercial terms, NFL names and marks
- What it sends in the nine months with no Sunday

## The two that matter most

**The sanity gate.** At SCFL's scale John is the check. A free product with no
human in the loop will eventually publish a confident wrong number to eleven
strangers. The measured example: `waiver_depth` reported **27 players who would
upgrade a lineup** on the 10-team league, where the house rules say the true
figure runs 2 to 5. It did not crash and it did not warn.

**Commissioner review on chat.** The same valve as *"run past John first"* —
the only thing between banter and somebody's real insult going out under the
masthead.
