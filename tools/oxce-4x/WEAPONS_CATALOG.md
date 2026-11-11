# The weapons catalog — every firearm, what it is called, and what it looks like

Twenty-one items with `battleType: 1`. The mod defines **no new weapon items**:
every one is a vanilla X-COM id renamed in `en-US.yml`, and twelve of them have
had their art repainted. Nine still wear X-COM's.

Render the sheet that goes with this file with `build/weapon_sheet.py`. Reading
the table is not the same as looking at it, and three of the five findings below
were invisible until the sprites were put side by side.

## What is repainted, and what is not

| id | in-game name | art | for |
| --- | --- | --- | --- |
| `STR_PISTOL` | Uzi | `Items/big_uzi.png` | Joe |
| `STR_RIFLE` | M4 Carbine | `Items/big_m4.png` | Joe |
| `STR_HEAVY_CANNON` | .50 Cal | `Items/big_cal50.png` | Joe |
| `STR_AUTO_CANNON` | M-32 Launcher | `Items/big_m32.png` | Joe |
| `STR_ROCKET_LAUNCHER` | RPG-7 | `Items/big_rpg.png` | Joe |
| `STR_LASER_RIFLE` | Sniper Rifle | `Items/big_sniper.png` | Joe |
| `STR_PLASMA_PISTOL` | Pulse Pistol | `Cobra/big_pistol.png` | Cobra |
| `STR_PLASMA_RIFLE` | Pulse Rifle | `Cobra/big_rifle.png` | Cobra |
| `STR_HEAVY_PLASMA` | Heavy Pulse | `Cobra/big_heavy.png` | Cobra |
| `CELATID_WEAPON` | B.A.T. Sentry Weapon | slot 60 | Cobra, built-in |
| `CYBERDISC_WEAPON` | B.A.T. Drone Weapon | slot 60 | Cobra, built-in |
| `SECTOPOD_WEAPON` | B.A.T. Heavy Weapon | slot 60 | Cobra, built-in |
| `STR_BLASTER_LAUNCHER` | **not renamed** | **vanilla** | — |
| `STR_HEAVY_LASER` | **not renamed** | **vanilla** | — |
| `STR_LASER_PISTOL` | **not renamed** | **vanilla** | — |
| `STR_SMALL_LAUNCHER` | **not renamed** | **vanilla** | — |
| `STR_HOVERTANK_LAUNCHER` | HAVOC/Launcher | **vanilla** | Joe vehicle |
| `STR_HOVERTANK_PLASMA` | HAVOC/Pulse | **vanilla** | Joe vehicle |
| `STR_TANK_CANNON` | MOBAT/Cannon | **vanilla** | Joe vehicle |
| `STR_TANK_LASER_CANNON` | MOBAT/Laser Cannon | **vanilla** | Joe vehicle |
| `STR_TANK_ROCKET_LAUNCHER` | MOBAT/Rocket Launcher | **vanilla** | Joe vehicle |

## 1. Cobra has no weapon art of its own

`Resources/Cobra/` is not Cobra art. It is the Joe art under other filenames,
**byte for byte**:

    Cobra/big_pistol.png    == Items/big_uzi.png      (cmp: identical)
    Cobra/big_rifle.png     == Items/big_m4.png       (cmp: identical)
    Cobra/big_heavy.png     == Items/big_cal50.png    (cmp: identical)
    Cobra/floor_pistol.png  == Items/floor_uzi.png    (cmp: identical)

So on the field and in the inventory, Cobra's sidearm IS the Joes' Uzi, Cobra's
rifle IS the M4, and Cobra's heavy IS the .50 Cal. Two sides, one armoury. This
is the finding that matters most and it is not visible in any ruleset — the
filenames say Cobra and the bytes say Joe.

## 2. Nine weapons still wear X-COM's alien art

Five of the nine are the MOBAT and HAVOC turrets, which read as purple organic
alien hardware in a G.I. Joe game. Four more are plain X-COM weapons that were
never touched at all, and those four **also still carry X-COM's names**, because
`en-US.yml` has no entry for them and the game falls back to the base strings:

    STR_BLASTER_LAUNCHER   "Blaster Launcher"
    STR_HEAVY_LASER        "Heavy Laser"
    STR_LASER_PISTOL       "Laser Pistol"
    STR_SMALL_LAUNCHER     "Small Launcher"

## 3. The Pulse names sit on conventional guns

`STR_PLASMA_PISTOL` is drawn as a semi-automatic pistol, `STR_PLASMA_RIFLE` as
an AR-pattern rifle with a carry handle, `STR_HEAVY_PLASMA` as a long-barrelled
heavy rifle. Their names are Pulse Pistol, Pulse Rifle and Heavy Pulse — which
are the months 15–22, 23–30 and 31–60 names in the escalation calendar.

This is why the calendar looks broken from the ruleset and is not broken in the
engine. `maxKitTierByMonth` clamps a month-1 garrison to tier 0 correctly, and
tier 0 is a conventional pistol drawn as a conventional pistol. Only the label
on it belongs to month 15. See the kit section of `CLAUDE.md`.

## 4. `STR_LASER_RIFLE` is the Sniper Rifle, so the laser band has nowhere to live

The calendar wants "first Cobra lasers" at months 9–14 and "lasers standard" at
15–22. The laser rifle id is spent on a Joe sniper rifle, and the plasma ids are
spent on Cobra's conventional guns. Any real laser or pulse tier needs ids that
are not currently free.

## 5. Two smaller things

- **The three B.A.T. built-in weapons share sprite slot 60 with
  `STR_CORPSE_SNAKE`**, which `gijoe_items.rul` paints as
  `Items/corpse_big_snake.png`. A terror unit's built-in weapon never appears in
  an inventory, so nothing is visibly wrong, but the slot is double-booked and a
  future repaint of either will surprise the other.
- **`big_rpg.png` is the only weapon off the grey palette** — mean RGB
  (99, 111, 59) olive against (55, 55, 55) for every other repainted weapon, and
  it carries four colours. Possibly deliberate; it does not match anything else.
