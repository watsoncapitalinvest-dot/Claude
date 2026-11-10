# The Cobra economy — design

Decided 10 Nov with John. Feature 1 of the eleven: *Cobra economy, strategic AI, labs,
factories, regional stockpiles.*

The anchor, in John's words, is that **the target list is the most fundamental reason for this
side of it**. The economy exists so that raiding has a point and so that one target is worth
more than another. Everything below is judged against that.

## The four decisions

| Question | Answer |
| --- | --- |
| Which sites | All eight |
| What Cobra runs on | Two resources: funds and materiel |
| Raided sites | Gone, and Cobra builds new ones when it can afford to |
| Where the player feels it | Mission rate and garrison size, equipment quality, and projects |

All eight sites are supportable precisely because of the last answer. Four of them were
previously held back for want of a system to act on — a research lab needs projects to delay, a
Terror Drome needs a mission rate to raise, a broadcast station needs country goodwill, a hidden
HQ needs a plan to run. Picking all three stakes supplies all four.

Two earlier decisions still stand. **The first version is a schedule, not an AI** — state and
rules need no intelligence, and decisions start as a timetable behind one interface. And
**visibility is built alongside, not afterwards**, because an economy the player cannot see is
wasted work.

## Build it on what is already there

This is the lesson from the broadcast, where a working thing was rebuilt from scratch and came
out worse: *"we have built this whole thing before and it worked."* Four of the five pieces
exist in OXCE already, and they are not approximations of what the economy needs — they are the
thing itself.

**`AlienBase`** is already a persistent site with its own deployment and garrison, a globe
marker, a `_discovered` flag that is fog of war, and its own mission generation. A Cobra site is
an `AlienBase` with an economic role, not a new class.

**`AlienStrategy`** is already the decision layer, and it already asks exactly the two questions
a director asks: *where to act* (`chooseRandomRegion`) and *what to do there*
(`chooseRandomMission`). It persists. It is the interface — there is none to invent.

**`RuleMissionScript`** is already a per-month timetable: `firstMonth`, `lastMonth`, execution
odds, and gates on score and on named counters. "A schedule, not an AI" is the engine's native
model, so version one of the director is largely ruleset authoring.

**`Region`** already keeps a monthly activity series that the graphs screen already plots.

The missing piece is the resources and the sites' economic roles. That is the work.

### The feedback loop is close to free

The mission scripts gate on `strategy.getMissionsRun(varName)`, which reads a persisted
`std::map<std::string,int>` of arbitrary names. The economy mirrors its regional values into
that same map as `COBRA_FUNDS_<REGION>` and `COBRA_MATERIEL_<REGION>`.

Every existing gate can then read economy state with no new scheduling code. A richer region
runs more missions because a ruleset author wrote a counter condition, not because anything in
the scheduler changed. This is the single biggest saving in the design and it is why the
engine-side work is small enough to be worth starting.

## Two resources, held per region

**Funds** are liquid and move between regions. **Materiel** is physical, stockpiled where it is
made, and equips the troops in that region.

Per-region is the whole point. A single global pool makes every site interchangeable, and a
target list of interchangeable targets is just a longer list. Raiding the factory in South
America has to starve South American garrisons specifically, or geography means nothing.

## The eight sites

Each is an `AlienBase` carrying a site type. The column that matters is the last one: a site
earns its place by what raiding it changes.

| Site | Produces | Costs | Raiding it |
| --- | --- | --- | --- |
| Front company | funds | small upkeep | regional income falls |
| Factory | materiel | funds | regional troops degrade |
| Training camp | garrison refill | funds + materiel | garrisons stay thin |
| Depot | stockpile cap, and loot | small upkeep | you take the stockpile |
| Research lab | project progress | funds | a project is delayed and revealed |
| Terror Drome | mission rate in region | funds + materiel | regional activity drops |
| Broadcast station | erodes country goodwill | funds | goodwill recovers |
| Hidden HQ | runs the act's plan | funds | the plan collapses and is revealed |

Cobra rebuilds when it can afford to, so the map becomes the readout: where Cobra expands says
how it is doing, and a region that goes quiet is a region that has been starved.

## The director, and the Cobra playthrough

`AlienStrategy`'s two questions are the interface. Three implementations answer them over time:

1. **Scripted** — a per-act timetable, which is the existing mission scripts gated on economy
   counters. No intelligence, deterministic, tunable, debuggable.
2. **Planner** — scores the options against the state. Swaps in behind the same two questions.
3. **Person** — a Cobra playthrough. John noted this side would need no AI at all.

Keeping the third on the table costs nothing now and a great deal later, so the state model is
built legible to a human from the start: named quantities with units, no opaque scores. That is
a stricter bar than a planner needs, and it is the reason to meet it now.

## Visibility

The intel screen.

It needs a background, and the handoff's claim that a painted one is sitting unassigned does
not survive checking: all eleven painted backgrounds are mapped onto vanilla `BACK` slots and
every one of them is referenced. What is actually free is `BACK06` to `BACK11` — six slots still
carrying X-COM's own art. The screen can take one of those and look like X-COM until a brief
goes to the graphics AI, which is the right order: build it working, paint it after.

It shows only what the player has **learned** — sites found, estimated regional income, known
projects and their timers. Raiding a research lab or a hidden HQ reveals more. That makes intel
itself a reward and gives those two sites a job beyond their production.

## Build order

The state model first, because it is the part that is expensive to change once saves exist.
Visibility third rather than last, per the decision above.

1. `CobraEconomy` — per-region funds and materiel, the project list, save and load, and the
   mirror into the counter map.
2. Site types on `AlienBase`, and their monthly production and upkeep.
3. The intel screen.
4. The consequences: garrison size, equipment quality, projects landing.

## Where the sites can actually go

The mod keeps X-COM's fifteen regions and defines none of its own, but only North America has
G.I. Joe terrain — the rest of the world was deliberately left untouched. Six of the fifteen are
ocean or ice anyway, so there are about nine land regions, and eight of those would put a raid
on an X-COM-looking map.

So version one should seed Cobra sites in North America only. The target list is then dense and
every entry on it is playable, which is the point. The state model stays keyed by region and
costs nothing to leave general, so the day another continent gets terrain the economy already
reaches it.

This is a content decision, not an engine one. Nothing in the state model changes either way.

## Not decided yet

- The numbers. Every rate, cost and threshold is John's to tune, and they belong in the single
  tuning file the design doc asks for, which does not exist yet.
- Whether a region can go bankrupt, and what Cobra does when it does.
- Whether the player can see a region's stockpile exactly, or only an estimate that sharpens
  with intel.
