# The interrogation spine — what John already decided, and what is in the way

**The chain is not an open design question.** It is written out in the master
doc as a 29-row table, step by step, each row with its Needs and its Unlocks.
This file is that table set against the shipped rulesets, so the next decision
is about build order rather than about story.

Doc: *G.I. Joe XCOM — Research & Tech Tree Design*, the interrogation table
(a Claude Docs document, id `e84ae02a-e968-4d71-b078-735cf4dd39fc`, read with
the Claude Docs connector — never web-fetch it). The doc wins any
disagreement with this file.

## What is actually in the game right now

Seven research topics, in `gijoe_campaign.rul`, one per Cobra unit:

    STR_COBRA_COMMANDER_UNIT   STR_DESTRO_UNIT      STR_VIPER_ENGINEER
    STR_VIPER_MEDIC            STR_STORM_SHADOW_UNIT
    STR_COBRA_TROOPER          STR_BAT_TERRORIST

**All seven carry `lookup: STR_SECTOID`.** Interrogating Cobra Commander and
interrogating a trooper open the same vanilla Sectoid article. Their `unlocks`
and `getOneFree` are vanilla X-COM plumbing too — `STR_ALIEN_ORIGINS`,
`STR_PSI_LAB`, `STR_LEADER_PLUS`, `STR_HYPER_WAVE_DECODER`, and
`getOneFree` lists of UFO types and alien races. None of those strings is
defined anywhere in this mod; they come from the base game.

So the interrogation chain today is the X-COM tree with Cobra names on seven
nodes, and every one of them reads the same.

## The blocker is units, not topics

The chain's 29 rows need a prisoner of twelve different kinds. **Five of those
twelve exist.** The other seven have never been built as units — they are not
in `units:` in `gijoe_units.rul` and not in any `members:` list in
`gijoe_campaign.rul`'s `alienRaces`.

| Step | Needs a prisoner of | Unit exists |
| --- | --- | --- |
| 1  | Cobra Soldier | yes — `STR_COBRA_TROOPER` |
| 3  | Viper Pilot | **no** |
| 5  | Cobra Officer | **no** |
| 7  | Medi-Viper | yes — `STR_VIPER_MEDIC` |
| 8  | Arashikage | **no** |
| 10 | Storm Shadow | yes — `STR_STORM_SHADOW_UNIT` |
| 11 | Iron Grenadier | **no** |
| 14 | Destro | yes — `STR_DESTRO_UNIT` |
| 16 | Crimson Guard | **no** |
| 18 | The Baroness | **no** |
| 20 | Dr. Mindbender | **no** |
| 26 | Cobra Commander | yes — `STR_COBRA_COMMANDER_UNIT` |

Three more rows need a won mission rather than a prisoner, and both of those
deployments are already built in `gijoe_cobra_sites.rul`:

| Step | Needs | Deployment |
| --- | --- | --- |
| 13 | win a M.A.R.S. factory raid | `STR_COBRA_FACTORY_SITE` |
| 22 | win a Terror Drome mission | `STR_COBRA_TERROR_DROME_SITE` |
| 30 | B.A.T. Control Chip + M.A.R.S. Supply Lines | — chains off step 12 |

The remaining fourteen rows are follow-on topics that need only the topic
before them, so they cost nothing but text.

## The ending is reachable; the texture around it is not

Walking John's own dependencies forward from what exists:

    22 Terror Drome Assault      (mission — built)
     └ 23 Terror Drome Data Core
        └ 24 Cobra's True Agenda ← also needs 15
             └ 25 Cobra Commander's Movements
                └ 26 Cobra Commander Captured   (unit — exists)
                   └ 27 Location: Cobra Island
                      └ 28 Cobra Island or Bust → final mission

    14 Destro Captured           (unit — exists)
     └ 15 Destro's Arms Ledger ──┘

**Every link on the path to Cobra Island is buildable today.** It needs one
Terror Drome win and Destro taken alive, and both of those work now.

What is blocked is everything that gives the climb its texture — the Viper
Pilot's airstrips, the Cobra Officer's flight routes, the Arashikage thread
that leads to Storm Shadow, the Iron Grenadier's supply lines, the Crimson
Guard into the Baroness, Mindbender's brainwave work. Seven missing units,
and with them twelve of the twenty-nine rows.

## What the rows unlock that also does not exist

Several Unlocks name things that are not topics, facilities or missions
anywhere in the mod. They are design, not transcription, and each needs its
own answer before its row can be wired:

| Row | Unlocks | What it would be |
| --- | --- | --- |
| 2  | Detention Block upgrades | a facility, and a capacity rule |
| 2  | Mission-type briefings | a UI surface |
| 6  | Signals Intelligence Center | a facility |
| 7  | Trauma Kit, Brainwave Scanner | items |
| 15 | Cobra funding cut, 2 months | an engine behaviour, not a ruleset topic |
| 19 | reveals hidden Terror Dromes on the globe | an engine behaviour — the intel layer |
| 21 | Mind Shield Helmet discount | a cost modifier |
| 27 | Strategic Command | a facility |

Row 19 is the one worth noticing: *"Reveals hidden Terror Dromes on the
globe"* is exactly the intel half of the situation board built on 11 Nov.
`GlobeMark` already carries `fromIntel` and a confidence tier, and
`Globe::drawMarks` already ages an intel mark down a tier. **Nothing sets
`fromIntel` yet**, and this row is the first thing in the design that would.

## Row 29 is missing

The doc's table runs 1–28 and then 30. There is no row 29. Either it was
removed and the numbering never closed up, or a step was lost. Worth asking
rather than inventing — it sits between "Cobra Island or Bust" and the
B.A.T. factory, which are not obviously adjacent.

## The cheap fix that does not wait on any of this

Seven units exist, seven topics exist, and all seven open the same vanilla
article. Giving each its own Ufopaedia entry is text and a `lookup`, needs no
new unit, no new facility and no engine work, and it is the difference between
an Intel File and a reprint. The doc calls these out as the game's main way of
telling its story: *"Intel Files from interrogations and captured intel"*.

That is the recommended first move, and it is independent of every decision
above.
