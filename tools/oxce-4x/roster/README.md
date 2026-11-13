# ROSTER: named characters' data

Owner: ROSTER (status file `claude/status/ROSTER.md` in the Project). One source for every named
character: stats, canon rank, specialty, signature weapon, trait, move, bonds, grudges, voice.

| File | What it is |
|---|---|
| `build.py` | **The builder.** Joins John's sources (Bible, Catalog, character articles; private, read with `--src`) with the hand layers and the stat model, and writes every output below plus the project docs (records, review page, tracker). Run `python3 build.py --src <design folder> --docs <out>`. |
| `characters_<batch>.yaml` | Hand layers: only what the sources lack (stat-model inputs, engine route and numbers, bonds, grudges, voice). `characters_day1.yaml` (16 Joes), `characters_cobra_b1.yaml` (15 villains). |
| `tracker.yaml` | What the other desks have delivered (figure art, 3D look, sprites), for the tracker. |
| `roster_cobra_b1.yaml` | Cobra batch 1 records: unit type, fixed stats, weapon, trait, move, bonds, grudges, voice keys, window. |
| `statmodel.py` | Stat model. Named Joe = specialty template + rank bonus + 25% of the secondary's lead + one canon nudge. Unnamed cap = 78% of the template; unnamed start = the decided greenshirt start, lowered to 70% of the template where that is less. Writes `stats_day1.json`. |
| `roster_day1.yaml` | The 16 Day-1 Joes + 14 unnamed specialties. |

## John's rules this follows (12 Nov 2026)
- Named Joes' stats never change ("named joes cant move stats. thyre high enough. regular joes can gain.").
- Unnamed Joes top out at 75-80% of a named Joe; named Joes "very good also commensurate with their rank and their specialty".
- Short-Fuze: no look yet, so on the roster as WAITING ("back burner him into the roster waiting"). Day 1 fields 15 named Joes.

## Contract with BUILD (proposed; nothing in BUILD's files is changed)
`install_body_sheets.py` already writes every named Joe's soldier type (Day 1, 12 Nov 21:31: all 16, generic stats,
`costBuy: 0`, one-name files). It should take these fields from `roster_day1.yaml` instead of the generic block:
- `minStats`, `maxStats`, `statCaps` = the record's `stats` (all three the same: fixed)
- `allowPromotion: false` (`costBuy: 0` is already there)
- `rankStrings: [<rankString>]` (one entry: a soldier who never promotes stays at rank 0, so OXCE shows entry 0)

Unnamed specialty types (`unnamed:`): `minStats` = start minus 5 (bravery minus 10), `maxStats` = start, `statCaps` = cap.

Why not an override file: this OXCE build loads rule files in reverse alphabetical order
(`Mod::loadMod` sorts `a.fullpath > b.fullpath`), so a "loads last" override would depend on the
exact engine build. The installer reading this data has no load-order risk.

The text file (`gijoe_roster_text.rul`) holds strings only (prefix `STR_GJR_`) and is safe to load as it is.
It does not touch soldier-type names, which are BUILD's.

Short-Fuze: John 21:31 put him on the roster as WAITING (no look). BUILD's Day-1 `startingBase` still lists
`STR_SHORT_FUZE: 1`; that is BUILD's call to change.

## Contract with BUILD for named villains (roster_cobra_b1.yaml)
- `unitType` names the OXCE unit. Three exist already (STR_COBRA_COMMANDER_UNIT, STR_DESTRO_UNIT, STR_STORM_SHADOW_UNIT);
  the rest are new unit types for BUILD to create (armour, sprites, names).
- unit `stats` = the record's `stats` (fixed). OXCE adds its own difficulty bonus to enemy units on top.
- `window` = campaign months for `gijoe_availability.rul` (BUILD's file); entries marked PROPOSED wait for John.
- trait/move `engine`: native (item or armour property), script (unit script hook), ai-fork (needs the AI to use a skill: fork).

## Not in stock OXCE (engine requests, to come as one spec)
Bonds, signature moves (once per mission), grudges (preset + Major Bludd's: anyone who downs, stuns
or captures him), Timber's strike (player picks the target), companion units, Strafing Run.
