# The Recovery Study — raw findings (draft, not yet written up)

Real numbers pulled from `history.json` (18 seasons, 2008–2025) resolved
through `scfl-franchises.json`, computed while you slept so there's
something concrete to react to. This is **not** the Study itself — no
narrative voice, no owner quotes yet (those come from Owner Interviews as
they arrive) — just the findings worth building the Study around, plus
what's still open. Full per-team numbers: `scripts/study_recovery.py`
(regenerate anytime) → the source data is in this doc's tables below.

## Headline finding: The Machines aren't just stable, they're a statistical outlier

Volatility (standard deviation of season-end rank, 1–16 scale) across all
16 active franchises, 18 years of history:

- **League average: 4.19** (min 1.83, max 4.88)
- **The Machines: 1.83** — dead last in volatility, and not close. That's
  **3.18 standard deviations below the league mean.** Keith's team has
  never finished worse than 7th in 18 seasons, has 4 titles, and — unlike
  every other multi-time champion in the league — never once had a
  bottom-half season the year after winning it all (see below). If the
  Study has a thesis team, it's this one: the anti-ebb-and-flow case study.

## The "title hangover" — 5 of 16 champions crashed the very next year

| Champion | Won it | Finish the next year |
|---|---|---|
| Horse Collars | 2010 | 15th |
| Master Jet-I | 2019 | 15th |
| Heavy Hitters | 2009 | 13th |
| Killer Klowns | 2024 | 14th |
| The Ox 45s (inactive) | 2015 | 11th |

**31% of all championships in league history were immediately followed by
a bottom-half finish.** Worth asking owners directly (a good Owner
Interview question, maybe worth adding): did winning change how you drafted
or managed the next year — complacency, selling the pieces, bad luck, or
something structural about picking last in the next draft?

## Recovery time: how long does a real rebuild actually take?

Every stretch from a bottom-3 finish (rank ≥14) to the next top-3 finish
(rank ≤3), across all active franchises, 28 instances on record:

- **Mean: 4.1 years. Median: 4.0 years. Range: 1–10 years.**

That's a real number to anchor the whole Study around — "the average SCFL
rebuild" is about four years, not one savvy trade deadline.

## The single biggest swing in league history

**Master Jet-I, 2018 → 2019: 16th place to 1st place and a championship.**
A 15-spot swing, the largest one-season move by any franchise, any
direction, in 18 years of record. (Runner-up: Horse Collars' identical
16th→1st in 2009→2010, and Killer Klowns' 2023→2024 15th→1st — both also
ended in a title, then both also hangover-crashed the year after. Jet-I is
the only one of the three who *stayed* strong after — 2020 was a real
follow-up top-half season.)

## Per-team volatility ranking (most chaotic to most stable)

| Team | Manager | Volatility | Worst | Best | Titles |
|---|---|---|---|---|---|
| Pork Chop Express | Dan Scampi | 4.88 | 16th (2017) | 2nd (2025) | — |
| Master Jet-I | Mike | 4.86 | 16th (2012) | 1st (2019) | 2019 |
| Heavy Hitters | Jay | 4.83 | 16th (2013) | 1st (2009) | 2009 |
| Guido Haters | Cousin Pete | 4.82 | 16th (2019) | 1st (2014) | 2014 |
| Lil Chops | Lil Chops | 4.78 | 16th (2021) | 3rd (2020) | — |
| Horse Collars | Horse Collars | 4.57 | 16th (2009) | 1st (2010) | 2010 |
| Hairy Gumbas | Tommy Vertucci | 4.50 | 15th (2010) | 2nd (2018) | — |
| The Beaver Eaters | Sheq | 4.32 | 16th (2023) | 2nd (2021) | — |
| Powers of Pain | PoP | 4.29 | 15th (2021) | 1st (2008) | 2008, 2013, 2025 |
| Big Blue | Jim Hunt | 4.24 | 13th (2011) | 1st (2021) | 2021, 2022, 2023 |
| New World Order | NWO | 4.17 | 16th (2010) | 1st (2020) | 2020 |
| Smoke Dragons | Smoke Dragons | 3.93 | 16th (2020) | 3rd (2008) | — |
| Wookie Leaks | Coach Nick | 3.91 | 16th (2016) | 4th (2015) | — |
| Still The Cream | Creams | 3.60 | 16th (2025) | 3rd (2017) | — |
| Killer Klowns | Nando | 3.56 | 15th (2023) | 1st (2024) | 2024 |
| **The Machines** | **Keith** | **1.83** | **7th (2024)** | **1st (2011)** | **2011, 2012, 2016, 2018** |

## Who's mid-cycle right now (last 3 seasons, 2023–2025)

Worth knowing before the Study goes to print — some of these are live
stories, not closed ones:

- **On the way up**: Powers of Pain (10th→10th→**1st**, 2025 champs),
  Horse Collars (12th→11th→3rd), Guido Haters (13th→13th→4th)
- **On the way down**: The Beaver Eaters were 16th in 2023 and climbed back
  to 5th/9th — actually mid-recovery. **Still The Cream** is the one going
  the wrong way: 11th→12th→**16th**, their worst finish on record, fresh.
  **Heavy Hitters** likewise: 9th→15th→15th, two straight bottom-2 finishes.
- **Currently on top, watch for the hangover pattern**: Powers of Pain just
  won it in 2025 — per the table above, 5 of 16 champions crashed the very
  next year. If POP is bottom-half in the 2026 standings, that's the Study
  writing its own next chapter in real time.

## A weak but real signal: heavy traders run more stable teams

Fixed the name-matching gap below (dossier.json keys managers by team name,
not the person — matched on club instead of on "manager", 15 of 16
resolved). Correlating each manager's trade count (from the earlier
trading-profile work) against their franchise's volatility:

**r = −0.30** (n=15) — a weak-to-moderate negative correlation: managers who
trade more tend to run *more* stable teams, not more chaotic ones. Weak
enough that it's a lead, not a conclusion — but it fits the one data point
that actually jumps out: **The Machines are both the league's 2nd-most
active trader (67 deals) and by far its most stable team.** Worth asking
directly in an interview: is constant, incremental trading actually a
*stability* tool for you, not a rebuilding one?

## What's NOT in here yet (needs your call, or needs data that doesn't exist yet)

- **Owner voice.** Nothing above has a single owner's own explanation for
  *why* — that's exactly what Owner Interviews is for. The title-hangover
  finding especially begs the question directly to the 5 owners it
  happened to.
- **Net buyer/seller vs. volatility** — the trade-count correlation above
  is done; a natural follow-up is whether being a net *buyer* (Coach Nick)
  vs. net *seller* (Keith) of players predicts volatility specifically,
  not just raw trade count. Didn't compute that one — a real next step if
  this angle is worth pursuing further.
- **Format.** This is raw findings, not a draft article. Didn't want to
  commit to a voice/length/publish-as-an-Investigation-piece decision
  without you — that's a real call, not one I should make solo overnight.
