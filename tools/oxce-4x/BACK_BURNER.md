# Back burner, owed, and broken

Three different things, kept apart on purpose. **Parked** is a decision — it
was reviewed and set down. **Owed** is work this desk said it would do, or
something shipped that is now wrong. **Broken** is a bug with evidence.

Nothing here is a wish list. If it is on this page it has been costed at least
roughly, and the cost is written down.

---

## Parked by decision

### Disguise in battle (parked 10 Nov, John)

Zartan's *Disguise*, Zarana's *Disguise*, and Act 4 infiltrators in captured
Joe gear that "look friendly or civilian until revealed".

**Why it is parked rather than queued:** OXCE draws a hostile as a hostile.
There is no mid-battle faction flip and no native concept of a unit the player
reads as friendly until it fires. Faking it means standing a unit up in the
neutral or civilian faction and converting it to hostile on a trigger, and
that conversion is the part with no support — line of sight, reaction fire,
AI ownership and the turn order all assume a unit's side does not change.

This is the largest single battlescape ask in the design doc, and **nothing
else in the Cobra soldier pass depends on it.** The other 37 villains and all
13 elite troop types can ship without it.

If it comes off the burner, it wants scoping on its own rather than being
folded into a villain content pass.

### Zanzibar's stolen signature weapon

He takes a downed Joe's signature weapon; it comes back through a recovery
mission on his hideout, or a black-market sale found through intel.

One villain crossing the battlescape, the geoscape and mission generation.
**The cheap version:** the weapon returns when Zanzibar is next beaten, with
no recovery mission. That keeps the sting and costs almost nothing.

### Subterfuge's strategic half

Moles at The Pit, impersonation off-screen, false flag operations, fake Joe
signals, sleeper cells, Synthoids.

All geoscape, all leaning on detection the player can act on. **Ordering
matters here:** intel has to exist before fakes have anything to corrupt. Park
until the Joe Intelligence department is real, then take it as its own pass.

---

## Owed

### The calendar ceiling is not scoped to the AI

`maxKitTierByMonth` clamps Cobra's weapon tier unconditionally. The design doc
is explicit that calendar windows *"apply only to the side the computer
plays… a pacing rail for the AI, not a rule of the world."*

Right while the player is G.I. Joe. **Wrong the moment Cobra is playable**,
which is the stated plan. One condition, not a rebuild.

### The department head signs off in person

A node accumulates while its head is away but parks at full progress until he
turns up at that bench for a few days (John's window: a few days — tight
enough that catching one is a genuine intercept).

Needs a villain-to-department mapping in the ruleset, which does not exist,
plus per-villain travel state.

**Build it once for both sides.** The doc gives G.I. Joe the same rule —
"if Scarlett goes out on a field operation, the department slows while she's
away, the same rule as an injured or captured head". Two factions, one
mechanism, one code path. Doing it twice is the mistake available here.

### The player's research tree is 8 topics

Against roughly 195 planned, and 7 of the 8 are interrogations still pointing
at a vanilla `lookup`. The ~29-topic interrogation spine is the story's
backbone and almost none of it exists.

### Cobra's tech tree is 2 departments

Benches, exclusivity and raid-clearing are built and verified — but the bench
model's whole tension is scarcity, and with two departments against three
labs nothing competes for anything. **The mechanism is correct and will not
feel like anything until the tree is populated.** Content, not engine.

---

## Broken

### A campaign crashes around month 15

```
[FATAL] FileRecord::at(TERRAIN/XBASE1.MCD): requested file not found.
```

A base-defence map the mod cannot load. Caps unattended campaign runs at about
fourteen months, which is why the planner never reaches some later buildings
in testing. Found 10 Nov in a 900-day run.

### Two parsed ruleset keys nothing consumes

`garrisonRefillPerMonth` and `stockpileCap`. The second is the M.A.R.S. dealer
threshold and M.A.R.S. is not built, so that one is expected. The first is
not.

---

## Designed, agreed, not yet built

Held from earlier sessions. These are not parked — they are queued.

- **The hidden starting network.** Cobra opens with one working network in one
  region and enough capital to improve weapons faster than it appears it can.
  Hook confirmed in `Mod::newSave`; `RuleRegion::getRandomPoint` places sites.
- **The cartel opening.** Scripted first mission against a drug cartel, its
  intel pointing to an abandoned Cobra weapons factory; the factory is empty
  until cartel gunmen stumble in as the Joes extract, and the intel found
  there is the date it comes back online.
- **The provocation gauge.** Accumulates on Joe actions, decays flat per
  month, feeds the planner's decision to attack a base. A shot-down scout
  moves the needle; it does not summon a retaliation.
- **Cobra cells** unconnected to the main economy, as something for the Joes
  to find.
- **Convoys and M.A.R.S.** — same faction, parallel, a stable force not driven
  by Cobra's economy; money that flows to it dies in the loop but stays at the
  site; restocks at a threshold; stock is its armoury.
- **The Drome superseding the crime launchers** — regional suppression on
  `genMission` once a Terror Drome stands.
