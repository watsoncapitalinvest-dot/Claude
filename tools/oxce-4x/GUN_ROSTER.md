# The gun roster — every small arm the game needs, against what is built

Assembled from John's own documents, not invented here:

- the **Tech Tree**'s Year 1 branch *1 Arms* (`claude.ai/artifact/2Kn5Ecvf4UEkMrWC9GsdR8`),
  which names each weapon as a research topic;
- the **Field Manual**'s File 07, branch 1 *Small arms*: 17 topics, *"standard
  issue and AP rounds, then lasers (from a captured Cobra emitter), pulse (from
  a captured pulse rifle and Cobranium) and sonics"*;
- the master design doc's art line B1: *"About 20 new weapon models (M249,
  shotgun, Cobra rifle, 5 lasers, 4 pulse, 2 sonic, launchers, mines,
  grenades)"*.

The count below lands on the same ~20 John's own estimate did, from the other
direction. That is the one encouraging thing in this file.

`WEAPONS_CATALOG.md` covers what the 21 existing firearm items ARE. This covers
what the game still needs.

## Year 1, the Joe side

| # | Weapon | Tech topic | Item today | Art today |
| --- | --- | --- | --- | --- |
| 1 | Uzi — standard sidearm | day 1 | `STR_PISTOL` | own |
| 2 | M4 Carbine — standard rifle | day 1 | `STR_RIFLE` | own |
| 3 | .50 Cal — Roadblock's | day 1 | `STR_HEAVY_CANNON` | own |
| 4 | M-32 Launcher | day 1 | `STR_AUTO_CANNON` | own |
| 5 | RPG-7 | day 1 | `STR_ROCKET_LAUNCHER` | own |
| 6 | **Squad automatic weapon (M249)** | 1-01 | **none** | **none** |
| 7 | **Under-barrel grenade launcher** | 1-02 | **none** | **none** |
| 8 | **Marksman rifle** | 1-04 | see note | — |
| 9 | **Combat shotgun** | 1-05 | **none** | **none** |
| 10 | **Laser pistol prototype** | 1-10 | `STR_LASER_PISTOL` | **vanilla X-COM** |

**Note on 8.** There is a "Sniper Rifle" in the game, but it is sitting on
`STR_LASER_RIFLE` — a conventional marksman rifle occupying the laser rifle's
id. That id is wanted later by the laser line, so the sniper rifle needs its
own item and the laser id needs giving back.

## Year 1, the Cobra side

All three exist, all three are misnamed, and **none has art of its own** — each
is a byte copy of the Joe weapon it sits beside (see `WEAPONS_CATALOG.md`).

| # | Weapon | Item today | Called today | Should be called |
| --- | --- | --- | --- | --- |
| 11 | Cobra pistol | `STR_PLASMA_PISTOL` | Pulse Pistol | a Cobra sidearm |
| 12 | Cobra rifle | `STR_PLASMA_RIFLE` | Pulse Rifle | a Cobra rifle |
| 13 | Cobra heavy | `STR_HEAVY_PLASMA` | Heavy Pulse | a Cobra support gun |

Tech topic **1-24 Cobra small arms** turns these into *"Cobra pistols and rifles
usable by Joes, sellable"*, so they are a real line the player interacts with,
not set dressing.

## Beyond Year 1

The design doc's B1 line asks for **5 lasers, 4 pulse and 2 sonic** — eleven
energy weapons. Four vanilla ids are currently idle and could host some of
them, but all four still wear X-COM's art and three have no name at all:

    STR_LASER_PISTOL     spoken for by topic 1-10
    STR_HEAVY_LASER      free
    STR_BLASTER_LAUNCHER free
    STR_SMALL_LAUNCHER   Cobra already fields it; it is the stun launcher

So of eleven energy weapons, at most three can reuse an existing id. **Eight
need new items.**

## The count

| | new items | new art | rename only |
| --- | --- | --- | --- |
| Year 1 Joe | 4 | 4, plus a repaint of the laser pistol | — |
| Year 1 Cobra | 0 | **3** (they currently wear the Joe art) | 3 |
| Lasers, pulse, sonics | 8 | 11 | — |
| Launchers, mines, grenades | not counted here | | |

**Twelve new weapon items and about eighteen pieces of art**, before launchers,
mines and grenades. John's B1 line said "about 20 new weapon models". The two
numbers agree, which is the best evidence either is right.

## The order this suggests

1. **Rename the three Cobra guns.** No art, no new items, and it stops the game
   calling a conventional pistol a Pulse Pistol in month 1. Fixes the
   escalation calendar's appearance without touching the engine.
2. **Draw Cobra's three.** The single largest honesty problem in the catalog:
   right now both armies carry the same guns.
3. **The four missing Year 1 Joe guns** — SAW, shotgun, marksman rifle,
   under-barrel launcher. These have tech topics already written, so the
   research side is specified and only the items and art are missing.
4. **Give `STR_LASER_RIFLE` back** by moving the sniper rifle to its own item.
5. **The energy lines**, which are a bigger piece of work and want their own
   pass.

## The Joe side: 161 Joes, about 30 gun models

Found 11 Nov in `GI_Joe_XCOM_Catalog.xlsx` on John's PC (the Signature Weapons
sheet), not in any artifact — which is why an earlier search for it failed.

161 Joes have a signature weapon row. They do **not** need 161 guns: 98 of the
rows are generic placeholders by specialty, so they collapse onto a handful of
shared models.

| source marking | rows |
| --- | --- |
| Canon | 20 |
| Likely canon | 30 |
| Placeholder by specialty | 98 |
| Other (incl. 3 undecided) | 13 |

**Note the contradiction.** The build brief's section 8 says filecard signature
weapons are *parked* and *"only Hawk is confirmed (M-16 and M-1911A1)"*, while
the sheet marks twenty rows Canon. Both are true and they mean different
things: nineteen of the twenty read *"Canon (well known); filecard not yet
checked"*, and only Hawk's says *"filecard, checked Nov 9"*. Well known is not
the same as verified, and the brief is using the stricter sense.

### The generic models, which carry most of the roster

| model | Joes | exists today |
| --- | --- | --- |
| Submachine gun | 24 | no |
| Rifle | 23 | no |
| Sidearm | 17 | `STR_PISTOL` is the Uzi, not a generic sidearm |
| Assault rifle | 11 | `STR_RIFLE` — M4 Carbine |
| Scoped rifle | 8 | no |
| Spear gun | 7 | no |
| Airborne rifle | 7 | no |
| Cold-weather rifle | 6 | no |
| Suppressed submachine gun | 6 | no — an SMG plus the suppressor attachment |
| Machine gun | 3 | no |
| Flamethrower | 3 | no |

### The named guns

Laser rifle (Flash, Grand Slam, Snow Job, Robo-Joe) · M-16 rifle (Hawk, Grunt)
and XM-16 with bayonet (Airborne) · M-1911A1 pistol (Hawk) · M-60 machine gun
(Rock 'n Roll) · **.50 cal machine gun (Roadblock) — EXISTS** · **Uzi (Snake
Eyes, Steeler) — EXISTS** · M-32 submachine gun (Duke) and M-32 Pulverizer
(Stalker) · MAC-11 (Mutt) · pump shotgun (Flint) · XK-1 power crossbow
(Scarlett) · bow (Spirit, Storm Shadow) · bazooka (Zap, Bazooka) · mortar
(Short-Fuze, Downtown) · XM-76 grenade launcher (Gung-Ho), multi-shot grenade
launcher (Hardball) · javelin launcher (Lady Jaye) · missile launcher (Salvo),
anti-aircraft launcher (Backblast), missile pack (Fast Draw) · night-scope
sniper rifle (Low-Light) · flare gun (Doc) · heavy machine gun (Heavy Duty).

Three Joes are marked *"Toy came with no weapon: check filecard
qualifications"* — Clutch, Ace, Lift-Ticket.

### What that totals

About **30 distinct gun models for the Joe side**, of which **three exist**:
the Uzi, the .50 Cal, and the M4 Carbine standing in for "Assault rifle". So
roughly **27 new Joe models**, plus Cobra's three and the eleven energy
weapons.

That is larger than B1's "about 20 new weapon models", and the two are not in
conflict: B1 counted the new tiers and specials, while most of these thirty are
the ordinary small arms the roster has always assumed and nobody has drawn.

## The order this suggests

1. **Rename Cobra's three.** No art, no new items, stops a conventional pistol
   being called a Pulse Pistol in month 1.
2. **Draw Cobra's three**, so the two armies stop carrying the same guns.
3. **The eleven generic Joe models**, which cover 98 of the 161 Joes between
   them and are the best art-per-Joe in the project.
4. **The four missing Year 1 Joe guns** — SAW, shotgun, marksman rifle,
   under-barrel launcher — whose tech topics are already written.
5. **Give `STR_LASER_RIFLE` back** by moving the sniper rifle to its own item.
6. **The named canon guns**, then the energy lines.

Steps 1 and 3 are where the leverage is: one is free, and the other covers
sixty per cent of the roster with eleven sprites.
