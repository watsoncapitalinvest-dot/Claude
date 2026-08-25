# Trade Court — every weighted factor, in one place

A single reference for every number that shapes a trade's value in the app
(`index.html`'s Trade Court). Companion to `docs/TRADE-VALUE-MODEL.md` (the
narrative design doc) — this is the quick-scan version: what each weight is,
what it does, and where it lives in code.

## Player values

| Factor | Value | What it does | Where |
|---|---|---|---|
| Base market value | dp-values.json snapshot, direct | The DynastyProcess Superflex $ for that player at the target season — no weighting applied, straight lookup | `dpValueAt()` |
| Elite stretch | `1 + 0.20 × min(1, max(0, (v−70)/60))` | Players above $70 get boosted up to +20% at $130+; ≤$70 untouched. Calibrated to real league behavior — a proven star fetches ~1.5× a 1.01 pick in actual SCFL trades | `scflStretch()` |
| Startable floor | Position tiers: QB [95,72,46,26], RB [63,47,31], WR [82,55,36], TE [41,24,13], cut at positional rank [4,12,24,40] / [5,18,40] / [6,24,48] / [3,10,20] | A player still startable by *today's* positional rank can't be graded down to dp's cratered dynasty number — final value = `max(market, floor)`. **Open question, not yet resolved**: this floor is built from today's live roster rank and applies to "at the time" prices too — a historical 2021 valuation can get bumped up because of who that player is *now*. That's a real, live exception to the "at the time never looks forward" rule below, pre-existing (not touched by this session's fix). Worth a call: is that the intended trade-off (don't let a stale dp glitch misgrade an obviously-good player) or should "at the time" use a floor built from the player's rank *as of the trade*? | `tcPlayerFloor()` |

## Draft pick values

| Factor | Value | What it does | Where |
|---|---|---|---|
| Pick-value curve | 32 slots, $100 (pick 1) → $4.5 (pick 32), calibrated to 235 real SCFL trades | Exact-slot picks ("2021 pick 26") look this up directly, no weighting | `calcDollars()` ← `draft-intel.json.pickValueChart` |
| Rank persistence (a, b) | **a = 6.953, b = 0.178** — `nextRank = a + b × priorRank` | How much a franchise's last known finish should move the guess for its next one. b=0.178 means finish barely carries over (fit from 266 real consecutive-season pairs, 2008–present, r² ≈ 0.03) — so this stays close to the league-average rank (8.46) on purpose, not a strong prediction | `fitRankRegression()` — fit live from `history.json`, never hardcoded |
| Slot-probability spread (σ) | **σ = 4.55** | Width of the bell curve around the predicted rank when spreading probability across all 16 possible draft slots — wide, because the regression above explains so little | `fitRankRegression()` |
| Time discount | **0.9 per year out** | A future pick loses 10% per year of distance — time value / format-drift uncertainty for capital that won't convert for a while | `tcChatAssetVal()`, applied after the expected-value calc |
| Class-quality modifier | **±15% cap** (prototype only) | Nudges a draft class's picks by how its rookies were valued their first Aug on file, vs. the all-class average | `scripts/build_trade_values.py` — **not ported to the live app**; scoped out to keep the shipped change to the two proven bugs (see the design doc's "How this actually shipped") |

## Grading thresholds (net $ → verdict)

| Factor | Value | What it does | Where |
|---|---|---|---|
| Win/loss margin | **±$12** | A trade nets as a win/loss only past this margin; inside it, it's graded "even" | `TC_WIN` |
| Verdict tiers | ≥55 Shark 🦈 · ≥18 Operator 📈 · >−18 Fair Dealer ⚖️ · >−55 Overpayer 📉 · else Mark 🎁 | Turns a franchise's summed net $ into the labels shown on the Standings/Reckoning tables | `tcVerdict()` |

## What's NOT weighted (deliberately)

- **"At the time" player values never look forward** past the trade's own season (the hindsight-leak fix) — the *market-value* number itself is a hard cutoff, no blend of past/future. Corrected after an audit found `tcChatAssetVal`'s own fallback (for an unresolved name or a genuine pre-debut rookie with no snapshot yet) was quietly substituting *today's* market price — the identical leak the fix was supposed to close. Fixed: that fallback now floors instead of ever touching today's number when `atTime` is true. The startable *floor* on top of that market value is a separate, still-open exception — see the Startable floor row above.
- **An exact-slot pick in the trade's own season gets zero adjustment** — the pick chart's own calibration already prices the slot; no persistence or class factor touches it. It still gets the ordinary time discount if the slot is for a *future* season (a rare but real case in the ledger — a slot can apparently be locked in more than a year out) — waiting has a cost independent of whether the slot is already known.
