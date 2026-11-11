# The test harnesses, and the ways they lie

Four features this repo shipped were built, compiled, running and doing
nothing. Three test scripts had to be fixed before they measured anything,
and two of those produced confident wrong answers first. So the scripts are
written to fail loudly rather than to pass quietly, and the notes below are
the failures that earned each guard.

## The harnesses

| script | what it drives | what it proves |
| --- | --- | --- |
| `gar_test.sh` | New Battle, nine runs | garrison headcount and kit-tier arithmetic, per rank entry |
| `campaign_ff.sh` | a loaded save, clock driven from inside the engine | the monthly economy: materiel, funds, production, research, payouts |
| `campaign_run.sh` | a loaded save, driven by `xdotool` | the same, but with a hand on the controls (raids, interceptions) |
| `pen_live.sh` | a real battle | wall penetration, measured off the engine's own log |
| `check_loaded.py` | nothing — it reads files | that a ruleset key the engine parses is set by a file the game **loads** |

## The save folder is shared, and `-continue` takes the newest

**This cost an entire evening on 10 Nov.** `-continue` does not load a
named save. It opens the save list, and `ListLoadState::init` auto-picks
the **newest save including autosaves and quicksaves**.

Every New Battle run of `gar_test.sh` writes `_autobattle_.asav`. So running
a garrison test silently breaks the next campaign test: the campaign loads a
**tactical** autosave, `LoadGameState` pushes `BattlescapeState` on top of the
geoscape, `GeoscapeState::init()` never runs, the fast-forward probe never
fires, and the script reports zeros that read exactly like a feature that did
not work.

Diagnosing it went wrong in three separate ways worth remembering:

- A screenshot of the X display showed a soldier standing on a street map.
  That was **the truth** — the game really had loaded into tactical — and it
  was dismissed as a stale framebuffer because the save named on disk was a
  geoscape save. It was the right evidence, discarded for a plausible reason.
- The zeros were blamed on a mission script that had been deleted earlier that
  evening, and a fix was written and shipped for a bug that did not exist.
  (The fix — neutering with `firstMonth: 9999` instead of deleting — is still
  the correct form, because deleting a mission script **does** break a save
  that holds one. It just was not what was wrong here.)
- Four more hypotheses were tested before the load path was instrumented:
  a modal confirm dialog, a buffered log, software-GL rendering too slow to
  advance states, and an unresponsive window. All four were wrong, and one
  `Log` line in `ListLoadState::init` answered it in a single run.

`campaign_ff.sh` now names its save (`SAVE=`, default `fronttest.sav`),
refuses outright if that save contains `battleGame:`, and `touch`es it so it
is the newest. **Point a new campaign script at a named save, never at
"the newest".**

## A test that cannot fail is not a test

- `campaign_ff.sh` used to wait `240 x 5s` for the clock to report in, and
  could not tell "grinding through 6.9M ticks" from "never started". Twenty
  minutes to learn nothing, twice in one evening. It now fails in **60
  seconds** if `[ff] advancing` has not appeared, and prints the game's last
  log lines when it does.
- `gar_check.py` treats a flat kit spread as a **failure** in a baseline run,
  because a baseline with every man already on tier 0 cannot show the clamp
  doing anything. Its own first bug was the mirror image: it failed the
  control run for reporting `minus0`.
- A shortfall-mode test run at a bill of 2000 proved nothing, because both
  modes stopped the line and quoted their percentage — which a flat comparison
  would also do. The modes only diverge at a bill the region can partly cover.
- `cobraResearch` returns immediately when no `cobraProjects:` are authored,
  so a research test against an empty tech tree reports success by doing
  nothing. Author the tree first.

## Two runs of the same script destroy each other

`gar_test.sh` deletes the shared log at startup. Two concurrent runs produced
six clean "0 units, the battle did not generate" failures about battles that
had worked. It now takes an `flock` and kills its own game on `EXIT`. The
save-folder collision above is the same trap one level up: **the harnesses
share the log, the save folder and the mod tree, and none of that is
namespaced.**

## Probes must never ship

`make_patch.py` refuses to build a patch if any of `GARPROBE`, `CAMPROBE`,
`FFPROBE`, `PENPROBE`, `MATPROBE` or `LOADPROBE` is still in `src/`, and
applies the candidate patch to a throwaway clone at the base commit before
accepting it.

## The two ruleset trees are not mirrors

The game loads `~/.local/share/openxcom/mods/GIJoe4x/`. The scratchpad copy is
a partial working copy, and the installed copy holds files the scratchpad has
never had. **Check direction per file; never blanket-sync.** `check_loaded.py`
asks the only question that matters — is this key set in the tree the game
actually loads — and it is the guard that caught `cobraEconomy:` shipping
inert. Add every new engine key to its lists, or the key passes the audit by
being invisible, which is the guard failing in the exact way it exists to
prevent.
