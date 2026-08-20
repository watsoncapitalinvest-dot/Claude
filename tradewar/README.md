# 💥 SCFL Trade War

Turn-based artillery between two club crests, fought on themed home fields.
One HTML file, no build step.

## Playing

Two sliders and a fire button. Drag **ANGLE** and **POWER**, or tap the −/+
nudges for single steps, or tap either number and type an exact value. The
barrel tracks your aim live. **AMMO** opens the inventory. Arrow keys and
Space still work on desktop.

Pick both clubs on the title screen — **←→** club, **↑** side, **↓** two-player
or computer, **Tab** how sharp the computer is. **The first club picked is
home**, and the match is played on their field. First to three rounds.

## Ordnance

| Round | Ammo | What it does |
|---|---|---|
| **Lowball Offer** | ∞ | The workhorse. Dead accurate. |
| **Waiver Claim** | 6 | Flat and fast, and ignores wind entirely. |
| **1st Round Pick** | 3 | Tight — lands within ~50px of where you aimed. |
| **2nd Round Pick** | 6 | Same damage, four times the spread. A gamble. |
| **Blockbuster** | 3 | Huge crater, but drifts twice as hard in wind. |
| **Shit Talk** | 5 | Buries them under a heap. Barely scratches. |
| **Veto** | ∞ | Clears ground. Four damage. It's a tool, not a weapon. |

Every other round digs; **Shit Talk is the only one that adds ground.** Land it
on a crest and that crest is under a pile, and its own next shot detonates in
its own muck. Getting out means lobbing near-vertically over the heap, or
firing **Veto** down into it and digging free at the cost of a turn. Veto is
unlimited precisely because burial is unlimited — otherwise a buried player
with no shovel is entombed and the match dies by attrition.

**Fall damage is light** — 1 per 10px dropped, with a grace so ordinary
settling is free, capped at 15. Enough that undermining someone's hill is a
real tactic, not enough to win on its own.

**Crests take damage too.** Where a blast lands, that part of the badge chips
away — about 3% for a taunt, 25% for a first-rounder, and roughly a quarter of
the crest gone by the time it dies. Cosmetic only: the hitbox stays a circle,
because tying it to the eroded shape would let shots sail through the missing
half of a living crest.

## Home fields

Each club's ground sets the sky, the backdrop, the props, the turf colours
**and the shape of the terrain itself**.

- **The Machines** → the scrap wastes: rust sky, dead gantries, terraced mesas
- **Pork Chop Express** → the night market: lit tenements, strung lanterns, flat rooftops
- **Powers of Pain** → the squared circle: a canvas mat between turnbuckles, and both fighters spawn inside the ropes

Every other club falls back to the stadium for now. The rest of the sixteen
are the next pass — that's also what the single-player tour needs, since you
play each club at their own ground.

## Verified

Headless runs against the game's own physics confirm:

- scatter behaves as designed — the baseline lands in *exactly* the same spot
  across 80 identical shots (0px), 1st rounders spread 51px, 2nd rounders 195px
- Shit Talk raises ground 22px over a target and flags it buried; Veto clears
  it back to grade and frees them
- crest erosion scales with damage taken rather than blast size
- the three computer settings differ properly: 24% / 54% / 84% hit rates
- 40 computer-vs-computer matches split 20–20, none stuck, ~21 turns each
- terrain across every arena profile is smooth enough that no one-pixel spike
  can swallow a shot

Three real faults came out of that testing: one blockbuster erased 84% of a
crest because erosion was scaling a world-space blast radius into badge space;
growing crests to 32px had silently widened every blast's damage reach; and
the wrestling ring spawned its fighters out on the floor rather than inside
the ropes.
