# The eleven fork features, in the brief's order, against the engine

From `XCOM_HANDOFF.md` section 7 (11 Nov, 2 PM), checked against the patched
OXCE source rather than against memory. Two are substantially built, one is
partly built, eight have not been started.

---

## 1. Cobra's economy, strategic AI, labs, factories, regional stockpiles
**Mostly built.** The brief calls this "the largest job" and it is the furthest
along of the eleven.

`SavedGame` carries the whole Cobra turn: `cobraPlan` decides what to build and
where, `cobraBuilt` places it, `cobraResearch` advances one project per
department, and `cobraMonthly` is the tick. `CobraEconomy` holds funds and
materiel per region and spends them. Site tiers, garrison strength, garrison
kit tier and the calendar cap on that tier are all wired and tested.

**The gap is stockpiles**, and only that. `stockpileCap` is parsed and consumed
by nothing, which is expected: it is the M.A.R.S. dealer threshold and M.A.R.S.
is not built.

The first draft of this file also named `garrisonRefillPerMonth` as an
unexpected gap, on `BACK_BURNER.md`'s word. That was wrong and the checking
took one grep: the key is not in the engine at all. `ECONOMY.md` had already
established why it never could be — X-COM keeps no garrison on a site, so
nothing depletes.

## 2. Civil War: two Cobra factions and three-way battles
**Not started.** The battlescape knows one hostile side. Act 5 content, so the
campaign reaches it last, and it is a deep change to targeting, AI and
deployment. Nothing depends on it yet.

## 3. Full capture: Cobra carries downed Joes off the map
**Built and verified in-engine, 11 Nov.** Pickup and extraction both observed
twice, in two independent hostile turns, with no crash:

```
[capture] 1000000 picked up 1   ->  [capture] 1 carried off the map by 1000000
[capture] 1000001 picked up 9   ->  [capture] 9 carried off the map by 1000001
```

`captureStep()` runs three passes at the top of `BattlescapeGame::endTurn()`,
in the order **DROP, PICK UP, EXTRACT**. That order matters and was wrong for
three builds: with EXTRACT first, a trooper who grabs a Joe while already
standing on an exit tile had to survive the squad's entire next turn before he
could leave, and the pickup could never be observed in the turn it happened.

Two things cost most of the afternoon and are worth keeping:

- **`BattleUnit::setTile(Tile*, SavedBattleGame*)` declares its second argument
  `= 0` and then dereferences it unconditionally.** The one-argument call
  segfaulted on every single pickup — *after* the carry link was set and
  *before* the log line that would have reported it. For three rounds the
  symptom read as "the pass never fires", which is the opposite of the truth.
  It also clears the tile's unit pointer itself, across all four tiles of a 2x2
  unit, so the hand-rolled clear that used to sit beside it was redundant and
  wrong for big units.
- **A diagnostic that reproduces the predicate it is testing can be wrong in
  its own right.** The first attempt filtered candidates on
  `Position::distance2d(...) > 1`; that returns a float, so a diagonal
  neighbour is 1.41 and the only board the probe ever builds was excluded from
  its own diagnostic, which then printed nothing at all. Logging moved inside
  the real pass, where there is nothing to reproduce.

Verified by `build/cap_probe.py` + `build/cap_test.sh`, which force the three
preconditions and let the real `captureStep` decide what follows — the probe
never sets a carry link itself.

**The DROP pass is still not verified**, and the reason is now exact rather
than a shrug. Drop fires when the carrier is out or has stopped carrying, so
it cannot be seen in the turn the pickup happens — it needs turn N+1. Two
things were in the way and one still is:

- The harness delivered exactly **one** hostile turn per run, because the turn
  loop pressed end-turn *first* and only then clicked to dismiss a splash, so
  every later end-turn landed on a splash and was swallowed. Fixed: dismiss,
  then end the turn. Two turns now arrive, though not every run.
- With two turns, drop still did not fire, and the log says why: the probe
  **knocked the carrier out**, and an unconscious man **recovers during the
  player's turn**, so by the next turn's drop pass `carrier->isOut()` was false
  again and the condition correctly declined. The probe downed the same trooper
  twice. `instaKill` instead of `knockOut` is the fix; the one run made with it
  drew a single hostile turn, so it has not yet had its chance.

Nothing here is evidence against the drop pass. It is evidence that the
scenario has never once been built, which is exactly the failure this harness
exists to catch — and it caught it rather than printing a pass.

The debriefing path — `captureSoldier`, roster removal, no `SoldierDeath` — is
likewise built and not yet exercised end to end.

Vanilla gets part way on its own: a downed Joe is already `STATUS_UNCONSCIOUS`,
a body on the floor. What does not exist is a Cobra trooper picking that body
up, carrying it (slower, firing one-handed), reaching an extraction point, and
the Joe being *gone* when the mission ends.

Everything around it is already written. Tech topic **1-36 Rescue protocol**
says "search-and-rescue missions for captured Joes". Five Joes on the
Recruitment sheet — Mainframe, Scoop, Airtight, Alpine and Bazooka — arrive
through **Rescue** missions that at present have nothing to trigger them. And
"named characters never die, they go down or are captured" is the project's
most-repeated rule, with no mechanism behind it.

Self-contained battlescape work. No art, no new units, no dependency on
anything else in this list.

## 4. 4x HD sprites, better animation, modern menus
**Partly built.** The 4x battlescape is the foundation the whole project stands
on and it works. HiUI renders the interface and was verified again 11 Nov. What
remains is art volume, which is the other track.

## 5. The Pit's stacked levels, up to 10 bases
**Not started, and structurally the deepest.** `BaseView` is a single
`_facilities[6][6]` grid with no Z at all, so digging, sealed levels,
level-by-level defence and Cobra-built bases all hang off giving a base a third
axis first.

Worth knowing: the 109 rooms of facility art are **drawn and waiting**
(`facilities\GIJoe_Facility_Art.zip`), but not cut into 32x40 MCD parts. That
cutting is on the build side and does not need the Z axis — it can happen
first and independently.

## 6. Vehicles larger than 2x2, crew slots, capturing vehicles intact
**Not started, and blocked anyway.** No Joe or Cobra vehicle exists as a unit
yet, so there is nothing for a size rule to apply to.

## 7. The tactical air and sea battle engine
**Not started.** Hex battles with altitude and depth bands, side-by-side turns,
up to 12 a side, guns and missiles and countermeasures. This is a second game
inside the first and is the largest single item on the list.

## 8. Stealth, wall penetration, building collapse
**Mostly built, and partly free.** Penetration is in `TileEngine` with every
tile material-tagged and a live test harness (`pen_test.sh`). Destruction is
tagged across 2,559 lines of `MCDPatches`. For stealth the design says phase 1
is stock camouflage, and OXCE already has `camouflage` and `psiCamouflage` in
the visibility code — so the foundation is there without new engine work.

## 9. Transport terrain travel and mobile bases
**Not started.** Needs the transports first, which are vehicles, which are #6.

## 10. Weapon attachments
**Not started.** Parked on the design side as of 11 Nov along with the rest of
the weapons work.

## 11. Intercepted transfers, prison breakouts, lift-gated vehicle sizes
**Not started.** `Transfer` exists in vanilla; intercepting one is new. Prison
breakouts want the Detention Block, which the interrogation spine's **row 2**
unlocks ("Detention Block upgrades") and which does not exist either. Lift
gating needs vehicle sizes, so it waits on #6.

---

## What this says about order

The brief's numbering is an inventory, not a priority. Taken as a sequence it
would put Act 5's Civil War ahead of Act 1's capture mechanic.

By what is unblocked, self-contained and already designed:

1. ~~**#3 full capture**~~ — built and verified in-engine 11 Nov. What is left
   is an isolated DROP run and the debriefing path end to end.
2. **The intel wire** — not on the brief's list. `GlobeMark::fromIntel` and
   `CobraProject::known` both exist and nothing connects them, so the
   situation board has no intel half. Small.
3. ~~**#1's last mile**~~ — resolved 11 Nov, by reading rather than building:
   there was no key.
4. **Cutting the 109 facility rooms into MCD parts** — unblocked, independent
   of #5's Z axis, and it is the art that is already paid for.
5. **#11 prison breakouts**, once a Detention Block exists.

Everything else is either large (#2, #5, #7), blocked on vehicles (#6, #9,
part of #11), or parked (#10).
