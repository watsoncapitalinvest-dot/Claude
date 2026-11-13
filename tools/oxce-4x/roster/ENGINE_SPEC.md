# ROSTER -> BUILD: engine spec for named-character mechanics (Day-1 batch)

Owner: ROSTER. 12 Nov 2026. One spec for everything the character records need that a plain soldier
rule cannot hold: signature moves, signature traits, bonds, grudges, Timber, Strafing Run.
Data: `roster_day1.yaml` (this folder). Numbers marked *proposed* are ROSTER's; John can move them.

Checked against OXCE source (current master; the fork's base `f0134ef` already has `RuleSkill`):
- **Soldier skills** (`RuleSoldier.skills`, `RuleSkill`, `SkillMenuState`, `skillUseUnit` script) = a per-soldier
  ability menu in battle with a TU/energy cost and a script hook.
- **`specialWeapon`** on a soldier type (and on an armour) = an item every unit of that type carries without
  using a slot. Ammo is full at mission start and nothing refills it in battle, so **1 round = once per mission**.
- **`spawnUnit` / `spawnUnitFaction`** on an item = a unit created where the item lands, on any side.
- **Unit scripts**: `damageUnit`, `hitUnit` (attacker + victim + weapon), `newTurnUnit`, `createUnit`,
  `reactionUnit`, `healUnit`, `returnFromMissionUnit` (has the geoscape `Soldier`), unit and soldier tags.

## The one fork helper that unlocks most of the rest
Many traits and bonds are "if X is on the map / within N tiles / was downed this mission". Unit scripts see
one unit (plus the attacker on a hit). **Ask: two script helpers**
1. `battle_game.unitsNear(unit, radius, faction)` (or an iterator over the battle's units), and
2. battle-level script variables (`battle_game.tag`) that any unit's script can read and write.
If OXCE already exposes either, use it; otherwise this is a small fork addition. Below, **[H]** = needs it.

## Signature moves (once per mission), Phase 1
Two native routes. Attack-type moves = the Joe's **`specialWeapon` with 1 round** (an item ROSTER specifies,
BUILD wires). Effect-type moves = a **skill** whose `skillUseUnit` script sets unit tag `GJR_MOVE_USED` and refuses
a second use.

| Joe | Move | Route | Proposed effect |
|---|---|---|---|
| Hawk | Fire Mission | specialWeapon `STR_GJR_MOVE_FIRE_MISSION` | indirect strike anywhere in sight of any Joe: power 110 HE, radius 4, 1 round |
| Duke | Yo Joe! | skill [H] | every Joe in Duke's line of sight +20 TU this turn |
| Roadblock | Full Belt | specialWeapon | .50 cal burst x10, power 52; every Cobra hit loses 50% TU next turn (uses the Suppression tag below) |
| Rock 'n Roll | Rock and Roll | specialWeapon | M-60 burst x12 this turn; Phase 2 (fork): repeats on his next turn without his input |
| Grand Slam | Jump Strike | Phase 2 (fork) | jet-pack hop up to 15 tiles then a free aimed laser shot. Phase 1 stand-in: none |
| Short-Fuze | Walking Barrage | specialWeapon | 3 mortar rounds, arcing, auto mode, power 75 HE r3 *(he is WAITING; build it when he has a look)* |
| Zap | Bunker Buster | specialWeapon | rocket power 110, very high damage to terrain (destroys one wall section) |
| Grunt | Covering Fire | skill [H] | Joes in his sight get +30 reactions until his next turn |
| Stalker | Ranger Ambush | skill [H] | turn 1 only: every Joe gets one free snap shot before Cobra moves (Phase 2 fork; Phase 1: +30 reactions turn 1) |
| Breaker | Intercept | skill (script) | every Cobra on the map revealed for one turn (to test: `visibilityUnit`; else fork) |
| Flash | Overcharge | specialWeapon | laser power 90, ignores all armour, 1 round |
| Scarlett | Triple Bolt | specialWeapon | crossbow auto x3, silent, power 40, up to 3 targets |
| Snake Eyes | Shadow Strike | specialWeapon | silent sword strike power 90 that doesn't reveal him; Timber is player-controlled, so the player picks Timber's target with Timber's own turn (John's rule, met natively) |
| Doc | Field Surgery | specialWeapon (medikit type) | fully revives a downed Joe at full health, 1 use |
| Ace | Strafing Run | specialWeapon, research-gated | line of 5 tiles hit for power 60; only if the Skystriker is researched (true "in service" check = fork) |
| Airborne | Drop In | Phase 2 (fork) | paradrop next to any Cobra unit. Phase 1 stand-in: none |

## Signature traits (always on), Phase 1

| Joe | Trait | Route | Proposed effect |
|---|---|---|---|
| Hawk | Command Post | `visibilityUnit` script (test) | turn 1: all Cobra on the map visible to the player |
| Duke | Field Leadership | `newTurnUnit` [H] | Joes within 5 tiles: morale loss halved, +5 firing |
| Roadblock | .50 Cal Suppression | `hitUnit` + `newTurnUnit` | a unit hit by his gun gets tag `GJR_PINNED`; next turn it loses 25% TU |
| Rock 'n Roll | Sustained Fire | stock | his own M-60 item: auto x7 instead of x5 |
| Grand Slam | Forward Observer | specialWeapon? | **clash**: a second once-per-mission strike would need a second special weapon. Proposal: fold into his laser's long range; John to say |
| Short-Fuze | Mortar | stock | the weapon itself |
| Zap | Bazooka | stock | his rocket item: +50% vs vehicles/armour (damage alter) |
| Grunt | Steady | `reactionUnit` | +10% on his reaction checks |
| Stalker | Ranger Lead | `newTurnUnit` [H] | turn 1: every Joe +10 TU if Stalker is on the map |
| Breaker | Radio Net | see question 1 | |
| Flash | Laser Rifle | stock | the weapon itself |
| Scarlett | Crossbow | stock now, fork later | phase 1: nothing extra (stock fire doesn't reveal); phase 2 stealth (fork #8) makes the shot silent |
| Snake Eyes | Silent Killer | armour `camouflage` (stock) + fork #8 | phase 1: Cobra spot him at half range; phase 2: melee kills raise no alert |
| Doc | Battlefield Surgeon | stock | his own medikit: revives a downed Joe in one action, heals +50% |
| Ace | Ace | stock (piloting) | pilot bonuses on craft; interceptions currently resolve at once (BUILD's stand-in) |
| Airborne | Paradrop | fork | deploy away from the landing zone. Phase 1: none |

## Bonds (when both are deployed)
| Pair | Route | Proposed effect |
|---|---|---|
| Snake Eyes + Scarlett (romance, John 21:13) | `damageUnit` sets battle tag on downing [H]; partner's `newTurnUnit` reads it | if one goes down: the other +15 firing, +15 melee, +10 TU for the rest of the mission |
| Duke + Lt. Falcon (later) | [H] | Falcon gets Duke's Field Leadership at double strength |
| Roadblock + Heavy Duty (later) | [H] | within 3 tiles: both apply Suppression at 50% instead of 25% |
| Snake Eyes + Jinx (later), Storm Shadow after defection (later) | fork #8 | stealth effects; wait for stealth phase 2 |

## Grudges
| Grudge | Route | Proposed effect |
|---|---|---|
| Snake Eyes vs Storm Shadow (while Cobra) | `damageUnit`: attacker/victim type pair | +15% damage both ways |
| Scarlett vs Baroness | same | +15% damage both ways |
| Major Bludd's marked list: Duke, Hawk | same | Bludd +15% damage against them |
| **Major Bludd vs any Joe who downs, stuns or captures him** (John 21:13) | `damageUnit` on Bludd: when he goes down, set unit tag `GJR_BLUDD_GRUDGE` on the attacker; `returnFromMissionUnit` copies it to the Soldier; Bludd's `damageUnit` later checks the victim's soldier tag | that Joe joins his marked list for the rest of the game (+15%). "Captures him" = the Joe who stunned him when Bludd is taken prisoner |
| Bludd's Bounty move (villain side) | later, with the Cobra batch | Cobra moves need the AI to use skills: fork |

## Timber (Snake Eyes' wolf)
- **Unit** `STR_TIMBER`: player faction, small and fast, bite melee, no weapons. *Proposed* stats: TU 90, Stamina 100,
  Health 30, Bravery 100, Reactions 80, Melee 80, Strength 40; camouflage like Snake Eyes.
- **Arrives** each mission with Snake Eyes: Snake Eyes' **armour** (`STR_SNAKE_EYES_UC`) gets a second `specialWeapon`,
  `STR_GJR_TIMBER_CALL`, with `spawnUnit: STR_TIMBER`, `spawnUnitFaction: 0`, 1 round, used on turn 1 next to him.
  Phase 2: placed automatically at deployment.
- **Look**: a wolf sprite sheet. No owner yet; DESIGN can build it in the character factory if John says so.
- Never dies (like a named Joe): goes down instead.

## Depends on (already planned by BUILD)
- Named Joes go **down, not dead** (the master doc's damage script). Bonds and Field Surgery read "downed".
- Fixed stats, no promotion, canon rank: the installer contract in `README.md`.

## Questions for John (ROSTER will ask; BUILD needn't wait for the native parts)
1. **Radio Net**: stock X-COM already shares sight across the squad, so "every Joe sees what any Joe sees" changes
   nothing. Proposal: *Cobra a Joe has seen stay marked for one turn after every Joe loses sight of them*
   (no ambush from the fog), plus Joes out of sight of each other don't lose morale for it.
2. **Grand Slam**: Forward Observer (call artillery) and Jump Strike are both once-per-mission actions, and a soldier
   has one special weapon. Proposal: Forward Observer becomes "his laser's long-range shots don't lose accuracy with
   distance", and Jump Strike stays his move.

## Test plan (BUILD loads, ROSTER checks numbers)
1. Clean load with the move items and skills defined (no references to missing rules).
2. Quick battle with Hawk, Duke, Roadblock, Snake Eyes, Scarlett, Doc: each special weapon fires once and is empty
   after; a second mission has it full again.
3. Grudge: Snake Eyes hits a Storm Shadow test unit; log the damage with and without the pair.
4. Bludd: stun a Bludd test unit with Grunt; next mission Bludd's hits on Grunt carry +15%.
5. Timber: spawns next to Snake Eyes on turn 1, takes orders, goes down instead of dying.
