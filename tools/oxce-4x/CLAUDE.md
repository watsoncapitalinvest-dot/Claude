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

## What is wrong in this directory right now

Found 10 Nov 2026 by reading the calendar against the shipped rulesets. None
of it is fixed. **Do not treat the current deployments as correct.**

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
