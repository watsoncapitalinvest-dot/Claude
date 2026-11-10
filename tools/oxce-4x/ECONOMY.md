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
- ~~`garrisonRefillPerMonth`~~ — **built.** See below.

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

**The fix for that had a consequence of its own, and the same harness caught it.** The toggle
went out on its own first. John's front-op scripts name no region, so they place fronts anywhere
on the globe — harmless while those fronts were scenery, not harmless the moment they are
earners, because only North America has G.I. Joe terrain. Printing the region of every Cobra
site each month showed fourteen sites with **nine outside North America**, every one of which
would raid onto an X-COM-looking map. `zz_gijoe_frontops_region.rul` holds them the way the
generated scripts are held. The three states, over the same eleven months:

| | sites | where |
| --- | --- | --- |
| neither file | 3 | all North America |
| economy only | 14 | nine outside North America |
| both | 12 | all North America, five of eight types, still wanting more |

Without the region column in the probe output this would have shipped looking like a success.
The run that found it was the run that had been *asked for* a different reason.

**Two claims that had been written down for John were then checked rather than asserted.** Every
Cobra site lands in North America across eleven months — true, with both files. And a site that
is destroyed goes back on the list: raiding Cobra's only depot took 400, which is the whole
regional stockpile and the depot's own loot rule working, the depot was wanted again the next
month, and it stood again two months later. Raiding one front company out of seven proves
nothing, so the probe takes a type Cobra has exactly one of.

**The lesson about the harness is worth as much as the finding.** Driving the geoscape with
xdotool does not work, and every failure looked exactly like a quiet campaign. A detection popup
stops the clock and Return will not clear it, because its default button is INTERCEPT. Escape
opens the options menu and a second one lands in the mod list — where a ten-minute run finished,
stopped three months in, with a log that read precisely like Cobra having nothing to build. Only
a screenshot told the difference. `ff_probe.py` advances the clock inside the engine through the
same switch `timeAdvance()` uses and drops the popups, so there is no UI to get wrong.

## The training camp, which could not refill anything

X-COM keeps no garrison on a site: the defenders are built from the deployment every time it is
raided, so nothing depletes and `garrisonRefillPerMonth` was a field pointing at a number that
does not exist. A camp therefore changes what the deployment *produces* in its own region, and
it does it two ways, both read off the camp's own rule:

- `garrisonBonus` — added to every rank entry's quantity. A Cobra site deployment has seven rank
  entries, so 1 is about seven more men on the map per camp.
- `garrisonRankUnlock` — with no camp in the region, ranks *below* this stay home.
- `garrisonAllMissions` — false, so it touches raids on Cobra's own sites and not crash sites.

**Low rank number is elite here**: 0 Cobra Commander, 1 Destro, 2 Viper Engineer, 3 Viper Medic,
4 Storm Shadow, 5 trooper, 6–7 B.A.T.s. The comparison was written the natural way round first —
"ranks above the threshold need a camp" — which would have kept the troopers home and sent Cobra
Commander to every raid. Checking the deployment data is what caught it; reading the code would
not have.

A cap that would skip *every* entry is a battle with no enemies, so one that empties a deployment
is ignored with a warning instead. Cobra's own sites keep ranks 4–7 at the shipped threshold so
it cannot happen today, but the cap is a ruleset number meeting a ruleset file.

Verified in four parts rather than by reading it:

| what | how |
| --- | --- |
| the lookup, against real campaign state | a camp planted at month 7 flips the region from `+0/cap4` to `+1/cap-1`, and nothing else moves |
| the bonus puts men on the map | same New Battle map, bonus forced to 2: 9 units become 14, every rank entry up |
| the cap removes the right men | cap forced to 5: ranks 2 and 3 gone, rank 5 untouched |
| the guard | cap forced to 9: warning fires, battle still has 7 men in it |

Exact per-entry arithmetic is not claimed — New Battle randomises its own counts, so the runs
show direction and magnitude rather than a reproducible sum.

All three numbers are guesses. The rank gate in particular changes the baseline everywhere the
moment it is on: set `garrisonRankUnlock: -1` to keep the bonus and drop that half.

## The Drome is the HQ

John: *"The drome is the hq. It's where the planning happens."* That maps onto `cobraPlan()`
directly, so the Hidden HQ's job went to the Terror Drome and the buff is not a number but
whether Cobra is competent at all.

`runsThePlanning` on a site rule. While Cobra holds one, the planner decides: pay upkeep first,
one of everything before two of anything, replace what was destroyed. With none standing it
reverts to buying whatever it can afford in no order — which is what it did before the planner
existed. It keeps the affordability test while leaderless, because without it a decapitated
Cobra could never rebuild the thing that does the thinking, and killing the Drome once would end
the game.

The contrast over one campaign, Drome planted at month 8:

| | before | after |
| --- | --- | --- |
| what it held by month 12 | 4 front companies, 2 depots, nothing else | front companies, factory, camp, depot, drome |
| what it asked for | types it already owned, repeatedly | only types it lacked |

So killing the Drome does not slow Cobra down, it makes it *stupid*: still building, all of it
the same two cheap things.

The Drome also fights back — `genMission: STR_ALIEN_TERROR` at `genMissionFreq: 4`. **None of the
eight sites generated anything before this**, because `genMissionFrequency` defaults to 0 and a
deployment that names no frequency is silently inert forever. The roll is *daily*, in `time1Day`,
so 4 is about one a month and the front op's 6 is one a fortnight — an easy thing to be thirty
times wrong about.

**Two measurement failures on the way, both of which read as "the feature does not work".** The
first counter totalled every generated mission, and John's front ops run supply missions at 6% a
day, so it read 63 before the Drome existed; a number that moves whether or not the thing under
test is present measures nothing. The second was worse: the test planted a Drome with
`setSiteType` alone, which is what the economy reads, while `genMission` hangs off the
*deployment*, a different pointer. That made a base which was a Terror Drome to the planner and a
front company to everything else, and four months of "the Drome launches nothing" was the test,
not the mod. Setting both halves: zero terror missions in seven months without, 1–2 in flight in
every month after.

Terror sites themselves still read zero, because a site is the end of a terror mission and
short-lived, and the probe samples monthly. Not claimed as working; not claimed as broken.

The Hidden HQ is now redundant and still in the list doing nothing. Retiring a site type breaks
saves that hold one, so it is a deliberate separate tidy rather than something done on the
evening of a test.

## The money leaves by air

John, on whether the economy sends cargo ships to earn its money: it did not. Income was
arithmetic at the monthly tick, and the economy was touched in exactly four places — a site
spawning, the month ticking, the planner deciding, a site being raided. Nothing on the globe
earned anything.

Meanwhile his front ops had been flying supply missions at 6% a day the whole time — 63 of them
by month eight in a test campaign — carrying nothing, because the income landed regardless. Two
systems that looked like one system and never touched.

Now an earner's income rides on a flight. `incomeNeedsShipment` on the site rule, `genMission:
STR_ALIEN_SUPPLY` on its deployment. Shoot one down and that site earns nothing that month and
still pays its upkeep, because the staff do not go home because the shipment did not arrive. The
loss lands on the **site that sent it**, not on Cobra in general, because `AlienMission` records
the base that launched it.

**`Ufo::DESTROYED` does not mean shot down.** It means "remove this UFO", and one of its uses is
a UFO that finished its route normally — `AlienMission.cpp`, where `nextWaypoint` runs off the
end of the trajectory. Hooked on that, the denial fired on every *successful* delivery and Cobra
earned nothing ever again. The first campaign after writing it had a front company standing in
month three and an income of zero, and it read exactly like a balance problem. Only three paths,
all in `DogfightState`, set `shotDownByCraftId`, and that is the predicate; it survives the
shot-down-then-crashed-then-decays route, so a cargo run downed over land still counts.

**Two test failures worth keeping.** A single interception attempt on one month boundary reported
"no cargo in the air" — a supply run is airborne only part of the time, so one look proves
nothing either way; retry every month. And the control run showed denials too, because
`campaign_ff.sh` passes `"${SHOOT:-}"`, which *sets* the variable to an empty string rather than
leaving it unset: `getenv` came back truthy with nothing behind it and `atoi("")` gave 0. Both
halves of the comparison did the same thing and it looked like the feature misfiring. All three
knobs now check `*env` as well as `env`.

Verified: control run, zero denials. Test run, a denial in each month following an interception,
naming the site.

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

## Running dry hurts

John, asked what happens when Cobra cannot pay for guns: *"It needs to make or buy more but if
it can't equip personnel it doesn't."*

So materiel stops being a number that goes up and down while nobody is worse off for it. A
region Cobra cannot supply fields the **poorest kit its deployment defines**, however late in
the campaign it is.

The mechanism was already there and unused. Every rank entry in a deployment carries three
`itemSets` — in the Joe mod a pistol tier, a rifle tier and a heavy tier — and the engine picks
between them with `getAlienItemLevels().at(_save->getAlienItemLevel())`, a table indexed by how
far the campaign has run. One line clamps that index to zero:

```cpp
if (!garrison.wellSupplied) { itemLevel = 0; }
```

Two numbers in `gijoe_tuning.rul` decide when:

- `wellSuppliedMateriel: 50` — what a region needs banked. A factory makes 80 a month and a camp
  eats 20, so one factory keeps roughly one region armed and losing it disarms that region
  within a month or two.
- `appliesToAllMissions: false` — raids on Cobra's own sites, not crash sites and terror sites.
  `0` switches the whole rule off.

**Reinforcements obey both rules too.** John: *"I don't know why it wouldn't be set for the same
region. If a region doesn't have enough guns to field a primary team they def can't field a
secondary team."* He is right, and the earlier note here calling that a design question was this
desk describing work it had not done. Two corrections went with it: the "identical line in the
reinforcement path" was `deployCivilians`, read wrong at a function boundary, and reinforcements
are not generated in `BattlescapeGenerator` at all — they land turns later, in `NextTurnState`.

So the state is worked out in `deployAliens`, where the region is in scope, and stashed on the
`SavedBattleGame` for the wave to read. It is **persisted**, or a mid-battle save and reload
would hand the player a full-kit wave right after he had fought a thin and badly armed garrison,
with nothing on screen to explain it.

One trap, because the obvious fix looks like a one-liner: the engine already stashes
`reinforcementsItemLevel`, so clamping *that* seems like the whole job. It is an index into
`alienItemLevels`, and row 0 is `[0,0,0,0,0,0,0,1,1,2]` — it still issues rifles to one man in
five. Clamping the row would have looked like a fix and leaked the better kit anyway, so the
starvation *state* travels and the tier is clamped at the far end.

The only path still exempt is `deployCivilians`, which is civilians.

### Guns and bodies are two different shortages

John, on the back of the above: *"if the troops portion of that fails then cobra should have
less troops available. Even if they have the best guns."*

So the two resources now fail in two distinguishable ways, which is the argument for having two
of them rather than one number called "strength":

| what Cobra is short of | what the player meets |
| --- | --- |
| materiel | a **full** garrison carrying **sidearms** |
| funds | a **thin** garrison carrying **whatever the month gives it** |
| both | a thin garrison carrying sidearms |

Materiel arms the men who are there. Funds are what put them there — payroll, food, training —
so `starvedHeadcount: 1` takes a man off every rank entry in a region that cannot pay. Seven rank
entries, so one is about seven fewer men.

**A flat funds threshold cannot work, and a campaign proved it rather than an argument.** The
first version shipped `wellPaidFunds: 40` and fired **zero times in 400 days**; the lowest
regional balance all run was 110. Raising the number does not fix it. Regional funds are a bank
balance that *accumulates* — Cobra drops under any fixed threshold in month one and never returns
to it, so 200 would have died by month four instead, out past where the test was looking.

So the bar is what the region **owes**: `wellPaidUpkeepMonths: 3` is how many months of its own
sites' upkeep Cobra must have banked there. A region holding eight sites at 20 each owes 160 a
month and needs 480. That bar rises as Cobra grows there, which a fixed number cannot do, and it
states something legible: a region that cannot cover its garrison's keep cannot field it at full
strength. `wellPaidFunds` survives as a flat floor for anyone who wants one — either test failing
is enough.

**No rank entry is ever emptied.** One that had men keeps one, for the same reason the rank cap
refuses to empty a deployment: an empty compound is a bug, not a consequence.

Either number at `0` switches the headcount half off and leaves the kit half running, and the
reverse. A front company nets 110 a month against a threshold of 40, so a region only goes thin
after it has lost whatever was earning there.

### The clamp and the lookup are two different things, and needed two tests

The New Battle test forces `wellSupplied` false by hand, because a New Battle has no Cobra
economy to be short of anything — so left alone it reports the region supplied and the battle
cannot show the effect. That proves the **clamp** and nothing else. Same map, same deployment,
nothing else forced:

| run | units | kit tiers | weapons drawn |
| --- | --- | --- | --- |
| as the game plays it | 10 | 0:7 **1:1 2:2** | 7 pistol, **3 rifle** |
| region out of guns | 7 | **0:7** | **7 pistol, 0 rifle** |

Three of ten men above the pistol tier becomes none of seven. The baseline mattering is the
point: alien tech row 0 is 70/20/10 across the three tiers, so the unstarved run has a spread to
lose. A baseline that happened to be all zeroes would have shown the same "pass" while proving
nothing, which is the shape of two tests that already had to be thrown away here. The checker
now **fails a baseline with no spread** rather than passing it.

The headcount half could not be tested the same way at all. New Battle rolls `dQty` and
`extraQty` per rank entry, so four runs of the *same map with nothing forced* came out at 10,
15, 7 and 7 units. A penalty of one man per entry is invisible against that, and "the starved
run had fewer units" would have been luck reported as a result. So the probe logs each entry's
quantity **before** the subtraction and `gar_check.py` checks the arithmetic exactly — given no
UFO damage the engine spawns exactly `quantity` men, so the pass is

    spawned(rank) == max(1, quantity_before - penalty)

per rank entry, which the dice cannot flatter.

It also landed on **John's own `STR_COBRA_FRONT` deployment** rather than a generated one, which
is the better result — the clamp works on any Cobra deployment with more than one item set, not
just the eight this desk wrote.

The **lookup** — the region's real stock against the real threshold — is campaign-side, so the
campaign probe prints it per month per region next to the number it was compared with
(`+0/cap4/DRY(m0)/paid(f110)`), and the shipped `OXCE_ECON_LOG` prints the same thing without a
probe build. A rule that never fires and a rule that always fires have to look different from
each other in the log, or the next dead number survives as long as this one did.

Verified over 400 days, against state Cobra produced itself rather than state this desk forced:

| months | what the log said | why |
| --- | --- | --- |
| 1–6 | `DRY(m0)` · `materiel=0/50 CANNOT ARM` | Cobra had no factory yet |
| 7 on | `sup(m80)` · `materiel=80/50` | the month its first factory came online |

The transition is caused by Cobra's own build decision, which is what makes it evidence. Region
lookup errors across the whole run: **0**.

A side finding from the same runs: John's `STR_COBRA_FRONT` has no language entry, so the game
logs `STR_COBRA_FRONT_ not found in en-US`. Cosmetic, pre-existing, and in his file rather than
a generated one, so it is left for him to name.

## M.A.R.S., as John has scoped it

Not a second faction. *"Mars doesn't have to be a seperate faction. It can be the same one just
operating parallel. And smaller with less requirements. It doesn't need to order weapons or be
offensive. Mars sells weapons and defends their property."* And: *"their garrison and materiel are
not determined by cobra economy. They are a stable force."*

That removes the structural risk entirely. M.A.R.S. sites are more rows in the same `cobraSites`
list, so there is no faction code to write. Three of the four properties cost nothing:

- **Not offensive** — a deployment naming no `genMissionFrequency` launches nothing, because the
  default is 0. That default was the bug that left eight Cobra deployments silently inert; for a
  purely defensive M.A.R.S. it is exactly right.
- **Defends its property** — garrisons, loot and raid outcomes already key off site type.
- **Smaller, fewer requirements** — numbers in the ruleset.

### A stable force needs one flag, in five places

"Not determined by Cobra economy" is one concept, not five exemptions, and it wants a single flag
on `RuleCobraSite` — every Cobra-economy function then skips the site:

| function | what it would wrongly do to a M.A.R.S. site |
| --- | --- |
| `cobraGarrison` | thin its garrison and drop its kit when **Cobra** is short |
| `cobraGarrison` | count its upkeep into the bar **Cobra** is judged against |
| `cobraMonthly` | pour its materiel into Cobra's regional pool for free |
| `cobraPlan` | offer M.A.R.S. sites on Cobra's shopping list |
| `cobraRaided` | loot **Cobra's** regional stockpile when M.A.R.S. is raided |
| `cobraBuilt` | charge Cobra for a site it did not build |

The second row is the one worth remembering, because it is invisible until it happens and it
reads as a bug rather than a leak: the pay bar sums the upkeep of **every** site in a region, so
M.A.R.S. opening a plant in North America would raise the bar Cobra has to clear and **thin
Cobra's garrisons** — a rival arriving would weaken Cobra by arithmetic nobody designed.

The third row is the trade: M.A.R.S. **sells**, so its `materielPerMonth` is its own stock and
must not reach Cobra's pool except by purchase. That is the convoy, which means **items 3 and 4
of the build order are one feature** — the convoy's "somewhere" *is* M.A.R.S. Cobra's funds leave,
materiel returns, and both legs are interceptable.

### The money dies, and it piles up where it died

John: *"Money that flows from cobra to mars effectively dies in the economy loop. But stays in
the site so if it's been doing a lot of business it will have a lot of money stashed at that
site."*

So the payment is a **sink, not a transfer**. It leaves Cobra's regional funds and enters no pool
that circulates — M.A.R.S. does not order weapons, build, or launch anything, so there is nothing
for it to spend on. Two consequences, both good:

- **Buying guns genuinely costs Cobra.** A transfer that came back would make the arms trade a
  wash and the decision meaningless. A sink makes Cobra's total wealth bounded by what it
  produces, so every purchase is a real trade-off against building.
- **A M.A.R.S. site's loot is its trading history.** The stash is what it has taken off Cobra, so
  a player who lets the trade run unmolested is growing his own target. That is a feedback loop
  with texture rather than a number on a rule.

Mechanically this is **per-site state, not per-region**, and the pattern already exists:
`AlienBase::_shipmentsLost` was added today with its own save and load, so a `_stashedFunds`
alongside it is the same shape. `lootFunds` in the ruleset becomes a floor and the stash rides on
top, rather than loot being a fixed number that ignores what the place has actually done.

It also makes the payment leg of the convoy worth intercepting on its own account: shoot down
Cobra's money on the way out and Cobra loses the funds *and* gets no guns, and the stash does not
grow. Both legs are losses, and they are different losses, which is what the two-leg convoy was
for.

**One second-order effect worth a decision at some point:** nothing drains a stash except a raid,
so a site left alone for a long campaign accumulates without bound. That is probably the intent —
an untouched dealer should become a fat target — but a five-year game could leave a silly number
sitting there. Default assumption is no cap until it looks wrong in play; John's call if he wants
one.

**Not built yet, deliberately.** With no M.A.R.S. sites in the ruleset the flag would be dead
code, and dead code that reads as a finished feature is the single most expensive thing on this
project. It goes in with the sites.

**Still unverified:** "kidnap Destro". Flattening every M.A.R.S. site is easy; detecting that one
*named unit was recovered alive* needs a debriefing hook nobody has looked for. It probably
exists, and it is not promised until somebody has looked.

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
