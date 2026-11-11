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

Found 10 Nov 2026 by reading the calendar against the shipped rulesets. None
of it is fixed. Three of these four are **content** — which units sit in which
deployment, and what a gate value is — and one is the missing mechanism above.
**Do not treat the current deployments as correct.**

**The Cobra race puts B.A.T.s in ranks 6 and 7**, and every generated Cobra
site deployment uses ranks 5,4,3,2,1,6,7. So a raid on a front company in
month 2 fields Battle Android Troopers — a unit the calendar does not allow as
a general force until **month 23**, and before that only where a specific
mission calls for them. Never in a generic garrison.

**Months 1–3 are handguns and knives.** The kit rule shipped on 10 Nov issues
the deployment's tier 1 and 2 itemSets as soon as a region holds 50 materiel.
Nothing checks the month. If Cobra is seeded with a working network and capital
(which John asked for the same evening), Cobra fields rifles in month 1.

**Storm Shadow is rank 4 and arrives months 9–14.** `garrisonRankUnlock: 4`
holds ranks *below* 4 at home without a training camp and always permits 4 and
above, so Storm Shadow is available from month 1.

**Destro is rank 1 and arrives months 15–22.** A training camp in the region
lifts the rank gate entirely, so a camp built in month 3 puts Destro on the
field twelve months early.

**The rank gate is answering the wrong question.** It gates on *is there a
camp*. The calendar gates on *what month is it*, and specific missions override
both. One `garrisonRankUnlock` threshold cannot express "this rank needs a
camp, that one needs a date, that one needs a scripted mission". The gate and
the calendar are different mechanisms and only one of them exists.

## The rules that follow

1. **A unit has an availability window.** Nothing may field a unit before its
   month, however the deployment is written. This mechanism does not exist yet
   and is the fix for everything above.
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
