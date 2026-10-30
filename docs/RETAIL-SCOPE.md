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

- ~~The five hand-made files degrade gracefully instead of hard-crashing~~
  **DONE.** `optional()` in `build_watch.py` and a tolerant `history.load()`.
  A league with no crests, kits, franchises, records or rivalries now builds a
  154KB issue of 6,145 words instead of a stack trace, and says so: *"no stored
  history: the issue runs on this season alone"*
- ~~Team count and slots read from `roster_positions`~~ **DONE.**
  `slots_for()` in `waiver_depth.py`; SCFL's output is byte-identical
- Sweep the remaining league-shape literals the same way

## Run itself

- ~~One workflow: fetch → replay → write → cover → issue → publish~~ **DONE.**
  `.github/workflows/weekly-issue.yml`, chained off the fetch, with the sanity
  gate as the step before publish — nothing commits if the numbers are wrong
- ~~A concurrency group per league~~ **DONE**, keyed on the repository
- The cover's art is **recorded in the week file** now. `--art` was a flag and
  nothing else, so the choice lived in a shell history: rebuilding week 7
  without repeating it took the tug-of-war off the live issue and dropped the
  cover from 434kb to 67kb. A bare rebuild now reproduces it byte for byte
- The workflow **refuses to rebuild a published week** unless explicitly forced,
  because weeks 4-6 keep the layout they went out with
- ~~The app sets the week number on a plate~~ **DONE.**
  `scripts/cover_number.py`, corner or band, run on the finished 1024x1536
  frame so compose_cover's drop cannot crop it. Takes any plate: the default,
  John's art, or a league's upload
- ~~Ship the default plate itself~~ **DONE.** `art/cover-plate-default.jpg`,
  John's. It carries its own masthead and a cream centre, so it needs no
  masthead drop and the number goes on in INK, not cream -- that is the
  `plate` placement, a third one beside `corner` and `band`

## Don't publish nonsense

- ~~A sanity gate before publish~~ **DONE.** `scripts/sanity_gate.py`, 20
  checks, exit 1 to hold. Verified it catches the 27-waiver bug, a half-played
  week, a replay final that drifted, and `undefined` reaching the page
- Wire it into the weekly workflow as the step before publish

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
