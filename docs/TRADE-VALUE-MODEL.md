# SCFL Trade Value Model — design doc (not yet implemented)

Goal: put a real, explainable number on every asset in `trades.json` (256
trades, 2021-2026) — draft pick or player, at the time it was traded — so we
can grade trade value across the league's whole history instead of just
counting deals. This is a proposal to react to before any of it gets built.

## The headline finding: we already have most of the raw material

Two files already in the repo turn out to solve the hard parts:

**`draft-intel.json` → `pickValueChart`** — a 32-slot draft-pick value curve
($1000 at pick 1 down to $45 at pick 32), and it's not a generic chart pulled
off the internet — its own note says it's *calibrated to 6 years / 235 real
SCFL trades*. This is our own league's real market for picks, already built.
Reuse it directly, don't reinvent it.

**`dp-values.json`** — DynastyProcess dynasty superflex player values, and
critically it's not one snapshot, it's **one snapshot per year, Aug
2021-2026, per player**. I checked this is genuinely contemporaneous and not
hindsight-tainted — e.g. CJ Stroud reads `[–, –, 40, 117, 96, 51]`: 40 in his
2023 rookie Aug (real preseason value, before anyone knew he'd be great),
117 the next Aug after a monster rookie year, then decaying. Marvin Harrison
Jr. reads `[–, –, –, 93, 72, 48]` — 93 on rookie hype, then the bust shows up
in real time. That's exactly the property we need: a player's value *as the
market saw him that August*, not as we know him to be now. (This is also why
I'm walking back my earlier call not to use this file for trade grading —
that call assumed it was a single current-day snapshot, which would have
been anachronistic. It isn't.)

**`history.json` → `standings`** — exact final rank (1–16) for every team,
every season, 2008–2025. This is what lets us estimate "how good is the team
that owns this future pick" without guessing.

## What's still missing / needs to be built

### 1. Draft pick value resolver

- **Exact-slot picks** (trade record says `"2021 pick 26"`) → direct
  `pickValueChart[26]` lookup. Done, no modeling needed.
- **Round-only future picks** (`"2022 2nd (DoD)"` — round known, slot
  unknown at trade time because the season hasn't been played yet) → needs
  an expected value:
  1. Take the picture we'd actually have had at trade time: the
     pick-owning team's rank in their most recently *completed* season
     (the one before the trade's season — never the season the pick is
     actually for, that would be hindsight).
  2. Convert that rank into a probability distribution over the round's 16
     slots. Fantasy standings regress toward the mean year to year but
     aren't random — I want to measure that regression empirically from
     `history.json`'s own rank-to-rank autocorrelation (how much does a
     team's rank this year predict next year's, across 18 seasons of real
     data) rather than guess a weighting. **Open question below.**
  3. Expected value = Σ P(slot) × `pickValueChart[slot]` over that round.
- **Class quality/depth adjustment**: a small multiplier per draft class,
  derived from that class's rookies' *first available* dp-values snapshot
  (their rookie-year Aug number — still contemporaneous, reflects preseason
  buzz/depth, not outcome) versus the all-class average. Proposed cap:
  ±15%, so a strong or weak class nudges pick value, it doesn't dominate it.

### 2. Player value resolver

- Look up `dp-values[player][seasonIndex]` for the trade's season.
- **Name matching isn't done yet.** I checked: simple normalization
  (lowercase, strip punctuation/suffixes) matches 228 of 287 unique player
  names in `trades.json` against `dp-values.json` — about 79%. The misses
  are mostly typos in the trade ledger itself (`"Buckey Irving"` for Bucky
  Irving, `"Diontate Johnson"` for Diontae Johnson, `"Jonu Smith"` for Jonnu
  Smith), last-name-only shorthand (`"Kupp"`, `"Mattison"`, `"McBride"` —
  ambiguous without a first name and roster context to disambiguate), and
  team defenses (`"Jets Defense"`, `"KC Defense"` — not in a skill-position
  dynasty value set at all, needs its own flat low value). This needs a real
  cleanup pass — fuzzy matching plus a manual review list — before the
  numbers can be trusted.
- **Missing-value fallback**: unmatched or genuinely valueless assets (late
  DST/K throw-ins) get a small fixed replacement-level value, not null —
  so one unresolved name doesn't silently zero out a whole side of a trade.

### 3. Lifecycle tag (the rookie/established/declining/aged-out language)

This becomes a label *derived from* each player's own dp-values curve
shape, not a separate value system:
- **Rookie** — first non-null year.
- **Ascending** — value grew meaningfully from the prior year.
- **Established** — plateaued near its peak.
- **Declining** — fallen a meaningful % from peak.
- **Aged-out** — near-zero or null.

So the original 5-tier idea survives as a readable label, but the number
underneath it is continuous, not a bucket.

### 4. Trade differential

Sum both sides' resolved values (players + picks), report the gap and %,
and — important — keep the full asset-by-asset breakdown attached to every
trade, not just a single net number. Every value has to be traceable back to
"why," or it's not more trustworthy than a guess.

## Worked example, with real numbers (not hypothetical)

Trade #2 in `trades.json`, 2021, Pork Chop Express ↔ The Powers of Pain:

| Side | Asset | Resolved? | Value |
|---|---|---|---|
| PCE gets | 2022 2nd (DoD) | round-only — **needs the model** | TBD |
| PCE gets | JK Dobbins | ✅ dp-values 2021 | 60 |
| PCE gets | Emmanuel Sanders | ✅ dp-values 2021 | 0 |
| POP gets | 2024 2nd (Chops) | round-only, 3 yrs out — **needs the model** | TBD |
| POP gets | 2023 1st (Chops) | round-only, 2 yrs out — **needs the model** | TBD |
| POP gets | James Conner | ✅ dp-values 2021 | 4 |
| POP gets | Keenan Allen | ✅ dp-values 2021 | 41 |
| POP gets | 2021 pick 28 | ✅ exact slot | 65 |

Already resolvable today: PCE's known side = 60, POP's known side = 110.
The three future round-only picks are exactly the piece that needs the
slot-probability model above — everything else in this system already
works off data we have.

## Known limitations (stated up front, not discovered later)

- No trade dates, only season year — so "value at time of trade" is
  approximate to season granularity. An in-season trade in November still
  gets priced off that year's August snapshot, because that's the freshest
  data point that exists.
- The regression-to-mean weighting for slot probability needs to be fit
  from real `history.json` data, not picked by feel — see open question.
- ~21% of player names need a cleanup pass before the player side is fully
  trustworthy.
- This leans on DynastyProcess's market values — real third-party
  consensus, contemporaneous, not our own performance model. I'm
  recommending it because it demonstrably isn't hindsight-tainted and
  building an equivalent from scratch (our own performance-based curve)
  would be a much bigger project for an uncertain accuracy gain. Flagging
  this as a real choice, not a default.

## Open questions for you

1. **Regression-to-mean weight** — okay for me to derive this empirically
   from `history.json` (measure actual rank persistence across 18 seasons)
   rather than pick a number?
2. **DynastyProcess as the player-value backbone** — fine with leaning on a
   third-party market consensus (transparently sourced, contemporaneous),
   or would you rather I build a from-scratch performance-based value even
   though it's a bigger lift and I can't promise it'd be more accurate?
3. **Name cleanup** — I can do a fuzzy-match pass and hand you the leftover
   ambiguous ones (the last-name-only entries) to disambiguate, rather than
   guessing on those myself.
4. **Where results live** — a new `tradeValues.json` (trade-shaped, mirrors
   `trades.json`) versus adding `value` fields directly into `trades.json`
   in place. I'd lean toward a separate file so `trades.json` stays the
   clean itemized source-of-record and this stays a derived/rebuildable
   layer — open to pushback.
