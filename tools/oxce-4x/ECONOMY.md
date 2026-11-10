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

**Funds** are liquid and move between regions — held per region but spent from the pool, which
is what "liquid" has to mean once Cobra operates everywhere. **Materiel** is physical, stockpiled
where it is made, and equips the troops in that region.

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

That is built. Each build script requires the region to hold the site's cost before it will run,
reading `COBRA_FUNDS_<REGION>` out of the counter map — no scheduling code, which is what the
mirror was for. The cost is read from this file by the generator, so the gate and the price
cannot drift apart. Cobra is charged on completion, or affording one site would mean affording
every site forever.

**The earner cannot be gated on funds, or nothing is ever built.** Cobra starts with nothing, so
nothing is affordable, so it never earns, and the economy sits dead at zero. The front company
is therefore ungated and capped by `maxRuns` instead — a ruleset number rather than a seed value
hidden in the engine. Cobra's front companies are its bootstrap; everything else it pays for.

**Where Cobra may build is one switch.** `REGION_LOCK` in the generator: a region name locks it
there, `None` goes worldwide, the engine's own region table then chooses and `spawnAlienBase`
finds land by itself. It is set to North America for now because that is the only region with
G.I. Joe terrain, and a raid anywhere else lands on an X-COM map. John's call, and the right
one: widen it when the world has terrain rather than before.

Nothing else depends on that switch, which was the point of doing the worldwide work first.
A build script that may pick any region cannot gate on one region's bank, so that forced the funds model to match what this document already claimed. A build script
that may pick any region cannot gate on one region's bank, so **funds gate and spend as a single
pool** (`COBRA_FUNDS_TOTAL`), with the region a site stands in paying what it can and the rest of
the network covering the remainder. Materiel stays regional, and that is what keeps raiding a
particular factory meaningful.

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

It needs no background of its own, and the question of which free slot to use was one I
invented. The `fundingWindow` interface already declares `backgroundImage: BACK13.SCR`, which
this mod paints, so a state that reuses that interface and sets no background is themed for
free — which is exactly what `FundingState` does.

Setting one explicitly overrode that with `BACK06`, X-COM's graph paper, and the screen rendered
with chart axes and gridlines behind the data. It compiled perfectly. The only reason it was
caught is that the screen was rendered headless to a PNG and looked at.

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

Steps 1 to 3 are done. Of step 4, only the **raid outcome** is built: a site's loot comes out of
its region when it is destroyed, a depot's loot is the whole regional stockpile, a raid cannot
take more than is there, and a lab or headquarters reveals that many unknown projects. The
production stop needed no code at all — the site is deleted, so the next monthly tick simply
stops counting it, which is the summing design paying for itself.

The **broadcast station** is built too, and it needed nothing new. A country's monthly
satisfaction is alien activity weighed against X-COM's, so "eroding goodwill" is already
something the engine does — the station adds alien activity to its region and to the country it
stands in, and funding falls, a pact grows likelier and the graphs screen shows it for free. It
runs before the funding pass so it counts in the month it happens.

Still unread, and both now blocked on a decision rather than on work:

- `projectProgressPerMonth` — nothing yet says what a Cobra project *does* when it lands.
- `garrisonRefillPerMonth` — there is nothing to refill. X-COM stores no garrison on a site; the
  defenders are generated from the deployment each time it is raided, so there is no number to
  deplete and none to top up. A training camp needs a mechanism invented, not a value chosen.
  Raising the garrison size of every site in its region is the cheapest and reads best: starve
  the camp, thin the defenders.

One rough edge in what is built: `cobraRaided` returns funds plus materiel as a single number
for the debriefing line, so "Cobra supplies denied: 640" adds dollars to crates. It is fine as a
score magnitude and wrong as a sentence; reporting the two separately is a small change.

## The planner, which is the part that makes it an economy

Up to here Cobra had a budget and no judgement. The mission scripts rolled their odds every
month and built whatever the dice said, and the economy only ever *refused* — a gate read
`COBRA_FUNDS_TOTAL` and said no. That is a wallet, not a strategy, and the tell was that Cobra
would happily field four headquarters while unable to pay for one.

`SavedGame::cobraPlan` is the decision layer. Once a month, before the scripts run, it works out
what Cobra *wants* and publishes one counter per site type, `COBRA_BUILD_<TYPE>`, set to 1 or 0.
The scripts gate on that and nothing else changed: the odds still decide *whether* it manages a
build this month, the planner decides *what* is on the shopping list.

Three rules, in priority order, each of which is a thing the dice version got wrong:

- **Pay your way first.** While net funds are at or below zero, the only thing wanted is an
  earner. A Cobra that cannot cover its upkeep does not break ground on a research lab.
- **Feed the troops.** While materiel is going backwards, a producer is wanted too.
- **Otherwise, diversify.** A type it owns none of is wanted; a type it already has is not. That
  is also how it rebuilds: raid the factory and `have` drops to zero, so the factory goes back
  on the list and stays there until one stands again.

Affordability is then checked per type against the pooled funds, which is what keeps the list
honest rather than aspirational.

**The bootstrap deadlock is the trap here, and it was walked into twice.** Cobra starts with no
money, so an unconditional affordability test means nothing is ever buildable, so it never earns,
so nothing is ever buildable. The first version dodged it with a hardcoded bootstrap type and a
cap. The planner reintroduced it the moment the test became uniform. The fix is a `freeEarner` —
the *cheapest earning type*, exempt from the funds test while Cobra owns none of it — so the
first front company is always affordable and nothing after it is. Derived from the ruleset, so
repricing the sites moves it on its own.

**Ordering is load-bearing and silently so.** `cobraMonthly` originally ran after
`determineAlienMissions()`, which means the scripts each month acted on *last* month's plan and
on no plan at all in month one. Nothing errors; it just behaves one month late forever. It now
runs before.

Verified headlessly against four scenarios written before the run: empty and broke wants the
front company and nothing else; earning with 2,000 banked wants the factory and the depot and
not another front company; solvent on paper but under water on upkeep goes back to wanting an
earner; solvent with materiel negative wants the factory. All four matched exactly.

## What eleven months found that eleven test cases could not

The planner passed four scenarios and the scenarios were states I wrote, which makes them states
I already believed in. So the economy was run forward eleven months with nobody playing, and the
first run found the thing none of the unit work could have.

`STR_COBRA_FRONT` in `gijoe_frontops.rul` is already a Cobra front company — its own warehouse
terrain, its own briefing about the Crimson Twins moving money under a legitimate name — and it
predates the economy by months. The economy then added a second front company that has never
heard of the first. Over those eleven months Cobra put **eight** of the old fronts on the globe
and earned nothing from any of them, while the economy's own front company sat alone and could
not afford a second site. The intel screen reported three sites while the globe carried
twenty-three.

One line closes it: `cobraSiteType: STR_COBRA_FRONT_COMPANY` on that deployment. Same eleven
months, 3 sites becomes 16 — ten front companies and one of every other type but the Terror
Drome, which it was saving for. It ships as `zz_gijoe_frontops_economy.rul`, a file that merges
into the existing deployment and can be deleted, because a swing that size is a balance question
and not a bug fix.

Twelve of those twenty-three were `STR_ALIEN_BASE_ASSAULT`. The vanilla base campaign is still
running at full tilt next to Cobra's, and none of it is in the economy either. That is the
Terror Drome naming question, which turns out to be much larger than a name.

**The lesson about the harness is worth as much as the finding.** Driving the geoscape with
xdotool does not work, and every failure looked exactly like a quiet campaign. A detection popup
stops the clock and Return will not clear it, because its default button is INTERCEPT. Escape
opens the options menu and a second one lands in the mod list — where a ten-minute run finished,
stopped three months in, with a log that read precisely like Cobra having nothing to build. Only
a screenshot told the difference. `ff_probe.py` advances the clock inside the engine through the
same switch `timeAdvance()` uses and drops the popups, so there is no UI to get wrong.

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

## A ruleset that loads is not a ruleset that loaded

There are **two** places where a broken ruleset and a correct one both start the game in
silence, and both were confirmed here by deliberately breaking them:

- OXCE **silently ignores an unknown top-level key**. A file full of `cobraSites:` in a build
  that has never heard of them logs nothing — and neither does a typo in the key.
- A mission's `siteType` is **not resolved at load**. Pointing one at
  `STR_DOES_NOT_EXIST_AT_ALL` starts just as cleanly; the reference is only looked up when a
  base actually spawns, which may be months into a campaign.

So "it ran without errors" says nothing about whether new content is wired in. Check by
existence instead: a temporary probe that asks the mod for each thing by name and logs what it
got back. That is how the eight site types, their deployments, their garrisons and their
missions were confirmed, and the probe came straight back out afterwards. Anything added to the
ruleset later deserves the same treatment once, because the failure mode is indistinguishable
from success.

## The month is summed before it is applied

Stockpiles are floored at zero, so applying each site's income and upkeep as it is read is not
the same as applying the month's net — and the difference is not small. A region whose consumers
happen to be read before its earners clamps to zero on the way down and then keeps the income
that follows; the identical set of sites built in a different order ends up broke. Read order is
construction order, which has nothing to do with what a region is worth.

It was found by a probe and fixed by summing per region first. Worth knowing that the obvious
test does not catch it: all eight sites net negative whichever way they are applied, so both the
right and the wrong code print zero. The case that discriminates is a set whose net is positive
but which holds one large consumer — a hidden HQ and two front companies gives 140 summed and
220 applied in order. A test that passes under both hypotheses is not a test.

## Open, and John's to settle

**The mod already calls vanilla alien bases "Terror Drome."** `STR_ALIEN_BASE` is renamed that
in the language file, and one of the eight site types is a Terror Drome of its own. Both can
exist and nothing breaks, but two different things on the globe would carry nearly the same
name. Either the vanilla base goes away once Cobra sites replace it, or one of the two is
renamed. Not decided unilaterally because it is a naming call, not a technical one.

## Not decided yet

- The numbers. Every rate, cost and threshold is John's to tune, and they belong in the single
  tuning file the design doc asks for, which does not exist yet.
- Whether a region can go bankrupt, and what Cobra does when it does.
- Whether the player can see a region's stockpile exactly, or only an estimate that sharpens
  with intel.
