# 🏈 SCFL Scramble

An 8-bit platformer where you play as your SCFL crest. Sixteen clubs, six
drives, one end zone. One HTML file, no build step.

## Playing

| | |
|---|---|
| **← →** or **A D** | run |
| **Space**, **↑**, **W**, **Z** | jump — hold for height, tap for a hop |
| **M** | music on/off |

On a phone the on-screen pad appears automatically. Land on a rival to stomp
them; touch one any other way and you lose a life.

- **Footballs** +100 · **stomp** +250 · **end zone** +500
- **Time bonus** for beating the drive's par, **+1000** for a clean sweep of a
  drive's footballs
- Three lives, six drives, best score kept on-device

## The drives

1. **Opening Drive** — running and jumping, nothing else
2. **Two-Minute Drill** — gaps and crates
3. **The Blitz** — rivals on the ground and in the air
4. **Turf Monster** — spikes
5. **Special Teams** — every pit crossed on a moving platform
6. **The Championship** — all of it

## How it works

Your crest is loaded from the league's own `scfl-team-logos-resized.json`, then
masked into a round badge so photo logos read as game pieces. Each club's ring
and HUD colour is sampled from its crest at load time — the dominant saturated
tone — so nothing is hand-configured. Rivals wear the other fifteen clubs, never
your own. If the logo bundle can't be fetched the game draws placeholder crests
and still runs.

Everything else is generated: the turf, the stands, the particle dust, and an
original square-wave riff written in Web Audio. No sprite sheets, no images, no
external requests.

## Level design is verified, not eyeballed

Levels are generated onto a fixed vertical grid — turf on row 12, shelves only on
rows 8 and 4 — because a full held jump rises 4.6 tiles and travels about 7, so a
shelf five rows up is unreachable and anything on it is stranded.

Two checks enforce that:

- a **linter** that models the real jump envelope, floods reachability out from
  the kickoff spot, and fails the build on an unbridged pit, a spike run flush
  against a ledge, a stranded platform, an uncollectable football, a rival penned
  into a lane too short to fight in, or an unreachable end zone
- a **bot** that drives the game's own physics headlessly, sixty runs a drive, to
  confirm every drive can actually be finished

Both caught real bugs: spikes sitting nine tiles from the nearest landing, a pit
whose only platform was seven tiles overhead, an end zone short enough to jump
clean over, and rivals trapped in the run-up to a spike pit.

## Running it

Open `index.html` from a server that also serves the repo root, so
`../scfl-team-logos-resized.json` resolves. On GitHub Pages that happens
automatically.
