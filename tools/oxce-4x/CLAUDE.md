# G.I. Joe 4x — the constraints that outrank anything in this directory

Read this before changing a deployment, a race, a unit, an itemSet or anything
that decides **who Cobra fields and what they carry**. It is copied from John's
master design doc (*G.I. Joe XCOM — Research & Tech Tree Design*, the
escalation calendar) and from the Storyline Brief. Both are his, both are
approved, and both are **outside this repo** — so the numbers here are a
transcription and the doc wins any disagreement:

- master doc: https://claude.ai/artifact/VghYZ7QoytSiLvs1ayVguy
  (a Claude Docs document — read it with the Claude Docs connector, never
  web-fetch it; its id is `e84ae02a-e968-4d71-b078-735cf4dd39fc`)

## The escalation calendar

Months are campaign months from the start. Six acts over four to five years.

| Months | Cobra fields | Cobra weapons | New missions |
| --- | --- | --- | --- |
| 1–3 | Cobra Recruits, Cobra Soldiers, Viper Pilots | **basic handguns, knives** | small raids, FANG landings |
| 4–8 | + Cobra Officers, Medi-Vipers, Stinger Drivers; **B.A.T.s only where a specific mission calls for them** | Cobra rifles and grenades | crash sites, town raids, first terror attacks |
| 9–14 | + Arashikage and Storm Shadow, H.I.S.S. tanks (by month 12) | first Cobra lasers, M.A.R.S. heavy weapons | airstrip raids, **M.A.R.S. factory raids**, first Terror Dromes |
| 15–22 | + Crimson Guard, **Destro**, the Baroness | lasers standard, first pulse pistols | city terror attacks, the Drome network grows |
| 23–30 | + Dr. Mindbender, **B.A.T. legions**, Toxo-Zombies | pulse rifles standard, brainwave attacks | spore attacks, assaults on The Pit |
| 31–60 | + Serpentor's guard, Cobra Commander's guard, Iron Grenadiers (Act 5) | heavy pulse | the Cobra Island assault |

## The dates are a target, not a gate

John, on the calendar: *"This was a story timeline. Our plumbing is more
important"* and *"I'd like to aim for the dates given by massaging it
organically."*

So the calendar is **what the tuning aims at**, not a switch that fires.
"Lasers at months 9–14" means a typical campaign should see lasers around
then — earlier if Cobra has had a free run, later if the player has been
burning its factories. Three parts:

| | |
| --- | --- |
| **earliest** | a hard floor. Never before this, whatever Cobra's books say |
| **organic** | Cobra's own state decides when inside the window — research done, factories built, materiel flowing |
| **latest** | a ceiling, so the story does not stall against a player who is winning |

`raceWeights` in a missionScript already escalates by month (keyed by month,
resolved on `monthsPassed`), so hard date gating needs **no engine work**. It
is the wrong shape though: a switch, not a slope. Month 8 one race, month 9
another.

**The kit rule shipped 10 Nov already does the organic half for weapons** —
regional materiel decides which itemSet tier Cobra issues. That is the real
mechanism and it is verified. What it lacks is the floor. The smallest honest
fix is therefore one clamp, not a rebuild: cap the tier at what the calendar
allows for the current month. Organic inside the window, impossible outside it.

No per-unit month gate exists anywhere in the engine. That is the one piece of
plumbing the calendar actually needs.

## The New Game head start (12 Nov)

John asked for a slider for how strong Cobra starts, and one for starting cash.
Cobra now has its own clock: `SavedGame::getCobraMonth()` = campaign month +
`cobraHeadStart` (0-24, chosen on New Game). Unit availability, the kit
ceiling, the item-level table, Cobra research gates and the race a mission
sends all read it. **The story does not**: mission scripts still schedule on
the real month, so Act 1 plays from the start whatever the head start.
`cobraApplyHeadStart` finishes every Cobra project the head start has reached
and banks `headStartFundsPerMonth` / `headStartMaterielPerMonth` (cobraEconomy
in gijoe_tuning.rul) per month in `headStartRegion`. It does not plant sites.

## Where the open work is written down

`BACK_BURNER.md` in this directory, and it keeps three things apart on
purpose: **parked** (reviewed and set down by decision), **owed** (work this
desk said it would do, or something shipped that is now wrong), and **broken**
(a bug with evidence). Read it before picking up anything, and put new
deferrals there rather than in a commit message nobody will find again.

Parked as of 10 Nov: disguise in battle, Zanzibar's stolen weapon, and the
strategic half of subterfuge. Owed: scoping the calendar ceiling to the AI
side, and the department head signing off in person.

## What is wrong in this directory right now

Found 10 Nov 2026 by reading the calendar against the shipped rulesets.
**Three of the four are fixed as of 11 Nov**, by the availability window in
`mod/Ruleset/gijoe_availability.rul` and `BattlescapeGenerator::availableUnit`.
The fourth is not, and is called out below.

Verified by fighting the SAME map at three forced months rather than by
reading the code. That deployment uses ranks 5,4,3,2,1,6,7, so it asks for
B.A.T.s, Destro and Storm Shadow every single time:

| month | spawned | roster |
| --- | --- | --- |
| 0 | 15, 10 refused | troopers only |
| 10 | 14, 6 refused | + Viper Medic, Viper Engineer, Storm Shadow |
| 25 | 13, 1 refused | + B.A.T.s, Destro |

### ~~B.A.T.s in every generic garrison~~ — fixed 11 Nov

The Cobra race puts B.A.T.s in ranks 6 and 7, and every generated Cobra site
deployment uses ranks 5,4,3,2,1,6,7. So a raid on a front company in month 2
fielded Battle Android Troopers — a unit the calendar does not allow as a
general force until **month 23**, and before that only where a specific
mission calls for them.

Now `earliest: 22` with `missionOnly: true`, so a scripted mission may still
name one and a garrison may not. Month 0 above fields troopers only.

### ~~Months 1–3 are handguns and knives~~ — fixed 12 Nov

Six-tier ladder in every Cobra deployment (`gen_cobra_sites.py` for the sites,
`gen_cobra_kit.py` for the stock deployments the mod still fights), six-entry
`maxKitTierByMonth`, `gijoe_item_levels.rul` so the base table reaches tier 5,
and pulse rifle / heavy pulse research tiers. There is still **no knife item**,
so months 1-3 are handguns only. The history below is kept for why.

#### (history) STILL BROKEN, but not where this said

The old diagnosis was that nothing checked the month. **That part is fixed and
was already fixed when this note still said otherwise.** `maxKitTierByMonth`
in `gijoe_tuning.rul` (0 → tier 0, month 3 → tier 1, month 8 → tier 2) reaches
`Mod::getCobraKitTierCap`, `SavedGame` puts it on the garrison as `maxKitTier`,
and `BattlescapeGenerator` clamps `itemLevel` to it. `check_loaded.py` confirms
the key is set by a file the game loads, and `gar_test.sh` shows `kitCap=0` on
a month-0 battle with every man landing on tier 0.

**The symptom is real anyway, because tier 0 is the wrong weapon.** Every
generated Cobra site shares one `data: &id001` anchor in
`gijoe_cobra_sites.rul`, and its three itemSets are vanilla X-COM's alien
ladder, never replaced:

| tier | item | what the strings call it | calendar band |
| --- | --- | --- | --- |
| 0 | `STR_PLASMA_PISTOL` | Pulse Pistol | months 15–22 |
| 1 | `STR_PLASMA_RIFLE` | Pulse Rifle | months 23–30 |
| 2 | `STR_HEAVY_PLASMA` | Heavy Pulse | months 31–60 |

So a month-1 raid is correctly clamped to tier 0 and correctly hands out the
**month-15 weapon**. Clamping a ladder that starts three bands too high cannot
produce handguns, and `7xSTR_PLASMA_PISTOL` is what the test prints.

**The mapping needed is already in the item names and is John's own**, so this
is transcription rather than design:

| calendar | item |
| --- | --- |
| 1–3 handguns and knives | `STR_PISTOL` — Uzi |
| 4–8 rifles and grenades | `STR_RIFLE` — M4 Carbine, + `STR_ALIEN_GRENADE` — Cobra Grenade |
| 9–14 first lasers, M.A.R.S. heavy | `STR_LASER_RIFLE` — Sniper Rifle |
| 15–22 lasers standard, first pulse pistols | `STR_PLASMA_PISTOL` — Pulse Pistol |
| 23–30 pulse rifles standard | `STR_PLASMA_RIFLE` — Pulse Rifle |
| 31–60 heavy pulse | `STR_HEAVY_PLASMA` — Heavy Pulse |

Two things follow and neither is one line:

- the shared anchor wants **six** itemSets in calendar order, not three, and
  every rank entry in it carries its own copy;
- `maxKitTierByMonth` wants six entries to match, not three.

Rule 3 below still stands. It was only ever half the job: the cap was built,
and the ladder it caps was left as X-COM's.

### ~~Storm Shadow available from month 1~~ — fixed 11 Nov

`garrisonRankUnlock: 4` holds ranks *below* 4 at home without a training camp
and always permits 4 and above, so Storm Shadow was available from month 1.
Now `earliest: 8`, `full: 13`, which is his 9–14 window.

### ~~Destro twelve months early~~ — fixed 11 Nov

A training camp in the region lifts the rank gate entirely, so a camp built in
month 3 put Destro on the field twelve months early. Now `earliest: 14`,
`full: 21`.

### The rank gate was answering the wrong question — now there are two gates

The original complaint stands as the reason they were separated. One
`garrisonRankUnlock` threshold cannot express "this rank needs a camp, that one
needs a date, that one needs a scripted mission". It gates on *is there a camp*;
the calendar gates on *what month is it*; and specific missions override both.

So there are now three questions and three answers, and none of them is
overloaded onto another:

| question | answered by |
| --- | --- |
| is there a training camp in this region | `garrisonRankUnlock` |
| what month is it | the unit's `availability` window |
| does a scripted mission name this unit | `missionOnly` on that window |

## The rules that follow

1. **A unit has an availability window.** Nothing may field a unit before its
   month, however the deployment is written. **Built 11 Nov.** `earliest` is a
   hard floor, `full` is where it reaches full strength with the chance ramping
   between the two (a well-supplied region gets there sooner), `latest` is a
   ceiling, and `missionOnly` lets a deployment that NAMES the unit ignore all
   of it. `substitute` says what to field instead, because a refusal with no
   substitute quietly thins the garrison.
2. **A generic garrison is not a scripted mission.** B.A.T.s in months 4–22
   belong to named missions only. "Only where a specific mission calls for
   them" is a hard rule, not a preference.
3. **Weapon tier is capped by the calendar, not only by materiel.** The economy
   may make Cobra *poorer* than the calendar allows; it must never make Cobra
   *better armed* than the calendar allows.
4. **Check the calendar before adding a unit to any deployment.** Rank order in
   the race (0 Cobra Commander, 1 Destro, 2 Viper Engineer, 3 Viper Medic,
   4 Storm Shadow, 5 trooper, 6–7 B.A.T.s) has nothing to do with availability.

## Story constraints that bear on mechanics

From the Storyline Brief (also John's, also outside this repo):

- **Act 1 is "Cobra builds its network and its first Terror Drome."** The
  approved opening is: Hawk briefs a rumoured terror group → Cobra Commander's
  broadcast is traced to one Cobra base, never the Drome → first raid on a
  cell, and a Cobra Soldier taken alive opens the interrogation chain.
- **The interrogation chain is the spine**: about 29 topics climbing Cobra's
  chain of command, across all six acts. Anything added to the opening should
  feed it.
- **Act 1 beat 4 is the first front-company raid** (Extensive Enterprises), and
  **beat 8 is officer interrogations leading to flight routes, then depots,
  then rumours of a Terror Drome.** The economy built on 10 Nov — front
  companies, cargo flights, depots — sits on those beats already.
- **M.A.R.S. is a clue in Act 1, not an actor.** Act 1 closes on M.A.R.S.
  markings found on Cobra weapons and a steel-masked man watching the footage.
  Destro allies with Cobra at the **opening of Act 2**. But M.A.R.S. *factory
  raids* are already a mission type at months 9–14, so the organisation exists
  before Destro joins.
- **Named characters never die** on either side: they go down, are captured, or
  escape.
- **Every outcome has a version.** No beat may assume something the player
  could have prevented.
