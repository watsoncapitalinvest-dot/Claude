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

**The gap is stockpiles.** `stockpileCap` and `garrisonRefillPerMonth` are both
parsed by the engine and consumed by nothing (`BACK_BURNER.md`). The first is
expected — it is the M.A.R.S. dealer threshold and M.A.R.S. is not built. The
second is not expected and is the real remainder here.

## 2. Civil War: two Cobra factions and three-way battles
**Not started.** The battlescape knows one hostile side. Act 5 content, so the
campaign reaches it last, and it is a deep change to targeting, AI and
deployment. Nothing depends on it yet.

## 3. Full capture: Cobra carries downed Joes off the map
**Not started, and the cheapest story-critical one.**

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

1. **#3 full capture** — design written, engine empty, nothing in its way.
2. **The intel wire** — not on the brief's list. `GlobeMark::fromIntel` and
   `CobraProject::known` both exist and nothing connects them, so the
   situation board has no intel half. Small.
3. **#1's last mile** — make `garrisonRefillPerMonth` do something, or delete
   the key.
4. **Cutting the 109 facility rooms into MCD parts** — unblocked, independent
   of #5's Z axis, and it is the art that is already paid for.
5. **#11 prison breakouts**, once a Detention Block exists.

Everything else is either large (#2, #5, #7), blocked on vehicles (#6, #9,
part of #11), or parked (#10).
