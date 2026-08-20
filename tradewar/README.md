# 💥 SCFL Trade War

Turn-based artillery between two club crests. Set your angle, set your power,
read the wind, and bury the other guy under his own transaction history.
One HTML file, no build step.

## Playing

| | |
|---|---|
| **↑ ↓** | angle |
| **← →** | power |
| **Tab** / **Q** | change ordnance |
| **Space** | fire |

Hold a key to move faster. On a phone the button pad appears automatically.
Pick both clubs on the title screen — **↑** switches which side you're choosing,
**↓** toggles two-player against computer, **Tab** sets how sharp the computer
is. First to three rounds takes the series.

## The ordnance

Every round is something that actually happened in this league.

| Round | Ammo | What it does |
|---|---|---|
| **Lowball Offer** | ∞ | The workhorse. A real trade where one side got a single asset and the other got three or more. |
| **Waiver Claim** | 6 | Flat and fast, small crater. Good for a target on open ground. |
| **Draft Pick** | 4 | Sniper. Barely dents the hill, but a direct hit takes 62. |
| **Blockbuster** | 3 | A real seven-asset-plus trade. Huge crater, slow arc. |
| **Collusion** | 2 | Splits into three at the top of its arc. |
| **Shit Talk** | 5 | A real draft-grade verdict. Barely scratches, but shoves you off your hill. |

The text that flashes on fire is the actual trade, pick, or grade — pulled from
`ammo.json`, which `scripts/build_ammo.py` distils from the league's own
committed record: 35 lowball offers, 12 blockbusters, 57 draft-grade verdicts,
60 first-round picks. Nothing is invented.

The raw group chat is **not** a source and won't become one — the corpora are
excluded from this repo on purpose, so the bundle is built only from artifacts
already committed here.

## How it works

The hill is a heightmap, one entry per screen column, and every explosion
carves it permanently. Shots integrate at four slices a frame so nothing
tunnels through a ridge at speed. Wind pushes the shell sideways the whole
flight and drifts a little between turns.

The computer simulates a couple of hundred candidate shots per turn using the
same physics you play against, scores each by the damage it would actually
land, then misses on purpose by an amount set by the difficulty. It also
rations its limited rounds instead of spending them all at once.

Crests are the league's own logos, masked into round badges and ringed in a
colour sampled from the artwork itself.

## Verified, not eyeballed

Headless runs against the game's own physics check that:

- all six rounds carve distinct craters — the draft pick punches 14 columns,
  the blockbuster tears 70
- a direct hit does the damage it claims
- the computer's three settings actually differ (roughly 48% / 63% / 95% hit
  rates) and it favours damage over noise
- 30 computer-vs-computer matches all terminate, averaging around 12 turns
- terrain over 200 seeds never produces a spike — amplitude scales with
  wavelength, so no tiny peak can swallow a shot

Two real bugs came out of it: more than half the power dial originally
overshot the entire map, and the first terrain generator gave its shortest
wavelength the largest amplitude, which made aiming a lottery.
