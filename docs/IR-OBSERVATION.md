# IR Watch — what four weeks of real data say

> **Superseded — this is a frozen week-4 snapshot, kept for the record.**
> The living version is **`scfl-ir-report.html`** ("The Wrong Number"), which
> `scripts/build_ir.py` re-types from the log every time it runs.
> Week 5 has since moved two of the conclusions below: constrained came back
> down from 5 to 4, and the cost of a *fourth* slot rose from 6 to 7 — so
> "expanding to 4 buys almost nothing" is no longer true. A fourth now costs
> 1.8× a third. Read the generated article, not this.

*Record kept automatically by `scripts/ir_watch.py`, run every Wednesday by
`.github/workflows/ir-watch.yml`. One row per week, never rewritten.
Live view: `ir-watch.html`. Frozen at **week 4, 2026**.*

---

## The mechanism, first

Most of the preseason argument was about the wrong thing. A Sleeper IR slot does
**not** hold a player who would otherwise be a free agent. It holds a man who is
*already on your roster*, and it frees an **active** roster spot — which the
manager then fills off the wire.

So the cost of an extra IR spot is not the injured player. It is **the healthy
replacement his manager signs with the spot that opens up** — one player off
waivers, per slot actually used.

That makes the question countable instead of arguable. A manager only uses a new
slot if **both** things are true right now:

1. their IR is already full, and
2. they are still carrying an injured player on their active roster.

Everybody else costs the pool nothing. They don't have anyone to put in it.

---

## The record

| Wk | IR used | Teams at cap | Empty IR | Injured on active rosters | **Constrained** | +1 costs | +2 costs | Free agents |
|---:|:--------|---:|---:|---:|---:|---:|---:|---:|
| 1 | 12/32 | 3 | 7 | 3 | **1** | 1 | 1 | 503 |
| 2 | 18/32 | 7 | 5 | 5 | **1** | 1 | 1 | 500 |
| 3 | 20/32 | 8 | 4 | 10 | **4** | 4 | 5 | 502 |
| 4 | 21/32 | 9 | 4 | 13 | **5** | 5 | 6 | 506 |

**Constrained** = IR full *and* still holding an injured man. That column is the
whole argument.

---

## What it shows

**1. The pressure is real and it is climbing.** Constrained teams went
**1 → 1 → 4 → 5** in four weeks. Injured men parked on active rosters went
**3 → 13**. IR usage went from 12 of 32 available slots to 21. Nine of sixteen
teams now have a full IR. This is the trend the expansion side predicted, and it
did not exist in week 1 — which is exactly why a preseason snapshot settled
nothing either way.

**2. The cost is smaller than anyone claimed.** A third IR spot would pull **5
players** off the wire today. The pool is **506** men. That's **0.99%** — one
player in a hundred. A fourth spot takes **6** (1.19%), and the extra one is a
single team: Gumbas is the only manager in the league with more than one injured
player stranded on an active roster.

**3. Four teams still aren't using the IR they already have.** Lil' Chops,
Smoke Dragons, Powers of Pain and Killer Klowns sit at 0–1 of 2. Three of those
four are carrying an injured man they could put on IR right now and haven't.
Whatever the vote does, it won't help a manager who isn't using slot two.

---

## Who is actually constrained (week 4)

| Team | IR | Injured on active | Would use +1 | Would use +2 |
|---|---:|---:|---:|---:|
| Gumbas | 2/2 | 4 | ✔ | ✔✔ |
| n.W.o | 2/2 | 1 | ✔ | ✔ |
| Horsecollars | 2/2 | 1 | ✔ | ✔ |
| Pork Chop Express | 2/2 | 1 | ✔ | ✔ |
| Heavy Hitters | 2/2 | 1 | ✔ | ✔ |
| *THE MACHINES*, Wookie Leaks, StillTheCream, Master-Jeti | 2/2 | 0 | — | — |
| Beaver Eaters, Guido Haters | 1/2 | 1 | — | — |
| BIG BLUE | 1/2 | 0 | — | — |
| Smoke Dragons, Powers of Pain, Killer Klowns | 0/2 | 1 | — | — |
| Lil' Chops | 0/2 | 0 | — | — |

Note the four teams at **2/2 with nobody stranded**. They are "at cap" but they
are not constrained — they'd get a slot and have nothing to put in it. Counting
*teams at cap* instead of *constrained teams* overstates the cost by nearly
double, and that conflation is where the preseason numbers went wrong.

---

## Bottom line for the vote

Both sides were arguing from the wrong quantity. Measured correctly:

- **Expanding to 3 is cheap.** Roughly 1% of the free-agent pool, five teams
  affected, and the figure is rising with injuries rather than with roster
  hoarding.
- **Expanding to 4 buys almost nothing** over 3 — one extra player, one extra
  team. If a third slot passes, a fourth is not worth the ballot.
- **Nobody has to remember any of this in December.** The log keeps running on
  its own and the table above regenerates from it.

Check it yourself any week: `python3 scripts/ir_watch.py --report`.
