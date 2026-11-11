#!/bin/bash
# Run a campaign forward N days with no hand on the controls, and print what Cobra did.
#
# The clock is advanced inside the engine by ff_probe, so nothing here clicks anything. The
# earlier xdotool version is kept in campaign_run.sh for the day somebody wants a run WITH
# interference - raids, interceptions - which is the other half of the test and needs a person.
#
# usage: campaign_ff.sh [days, default 240]
# RAID=<month> campaign_ff.sh 330   also takes one Cobra site off the board that month,
#                                    through the same path the debriefing uses, so the
#                                    planner replacing what it lost is watched and not assumed.
set -u
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad
B=$S/oxc/oxce/build/bin
L=/root/.local/share/openxcom/openxcom.log
DAYS=${1:-240}
export DISPLAY=:99

# This run needs BOTH probes and silently does nothing useful with only one: campaign_probe
# writes the monthly line (SavedGame.cpp) and ff_probe drives the clock (GeoscapeState.cpp).
# With ff_probe missing the game loads the save, sits on a paused geoscape and burns CPU, which
# for two minutes looks exactly like a slow fast-forward. Refuse instead of looking busy.
SRC=$S/oxc/oxce/src
# ff_probe is required: without it the game loads the save, sits on a paused geoscape and
# burns CPU, which for two minutes is indistinguishable from a slow fast-forward.
if ! grep -q FFPROBE "$SRC/Geoscape/GeoscapeState.cpp"; then
  echo "the clock is not instrumented, so nothing would advance. Apply it and rebuild:"
  echo "  python3 -I $S/rb/build/ff_probe.py apply $SRC"
  exit 1
fi
# campaign_probe is now OPTIONAL. It writes the per-month [camp] line, which is the only way to
# see the planner's wants and the garrison lookup - but OXCE_ECON_LOG is shipped in the engine
# and covers the economy on its own, so an economy test no longer needs instrumentation it is
# not reading. Say so rather than refusing, or the cheapest test gets a rebuild it never needed.
if ! grep -q CAMPROBE "$SRC/Savegame/SavedGame.cpp"; then
  echo "note: campaign_probe is not applied, so there will be no [camp] lines."
  echo "      [econ] lines still work - they ship in the engine. Apply it if you need"
  echo "      the planner's wants or the garrison lookup:"
  echo "  python3 -I $S/rb/build/campaign_probe.py apply $SRC"
fi

pgrep Xvfb >/dev/null || (nohup Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 &)
sleep 2
pkill -9 -x openxcom 2>/dev/null; sleep 1; rm -f "$L"

# -continue loads the NEWEST save, autosaves and quicksaves included - and every New Battle
# run of gar_test.sh writes _autobattle_.asav. So running a garrison test silently breaks the
# next campaign test: the game loads a TACTICAL autosave, pushes BattlescapeState over the
# geoscape, GeoscapeState::init() never runs and the clock never starts. That cost an evening,
# and the screenshot showing a soldier on a street map was the truth, not a stale framebuffer.
#
# Two harnesses sharing one save folder is the same trap as two gar_test runs sharing one log.
# So: name the save, prove it is a geoscape save, and make it the newest.
SAVE=${SAVE:-fronttest.sav}
SAVEDIR=/root/.local/share/openxcom/xcom1
if [ ! -f "$SAVEDIR/$SAVE" ]; then
  echo "no such save: $SAVEDIR/$SAVE"; ls "$SAVEDIR" | sed 's/^/  /'; exit 1
fi
if grep -q '^battleGame:' "$SAVEDIR/$SAVE"; then
  echo "$SAVE is a BATTLESCAPE save. The geoscape is never reached from one, so the clock"
  echo "cannot start. Point SAVE= at a geoscape save."; exit 1
fi
touch "$SAVEDIR/$SAVE"

( cd "$B" && OXCE_ECON_LOG=1 OXCE_CAMP_PROBE=1 OXCE_CAMP_FF="$DAYS" OXCE_CAMP_RAID="${RAID:-}" OXCE_CAMP_RAID_TYPE="${RAIDTYPE:-}" OXCE_CAMP_RAID_BENCH="${RAIDBENCH:-}" OXCE_CAMP_PLANT="${PLANT:-}" OXCE_CAMP_SHOOTDOWN="${SHOOT:-}" OXCE_MAP_HIRES=0 SDL_AUDIODRIVER=dummy \
    nohup ./openxcom -data "$B" -continue > /tmp/oxc_ff.log 2>&1 & )

# -continue does NOT load a save on its own. It pushes the save list, and ListLoadState::init
# auto-picks the newest entry - but loadSave() first compares every mod named in the save
# against the active mod list and, on any mismatch, pushes ConfirmLoadState: a modal waiting
# for a click. campaign_run.sh has always worked because it presses Return; this script did
# not, so it sat on a dialog burning 70% CPU for the full twenty minutes and then printed
# zeros. Press Return a few times: it dismisses the dialog if there is one and is harmless
# if there is not.
sleep 6
for i in 1 2 3; do xdotool key Return 2>/dev/null; sleep 2; done

# FAIL FAST. The old loop waited 240 x 5s for '[ff] done' and could not tell "the clock is
# grinding" from "the clock never started" - twenty minutes to learn nothing, twice tonight.
# '[ff] advancing' is logged BEFORE the loop, so if it has not appeared in a minute the run
# is not slow, it is stuck, and there is no point waiting out the rest.
for i in $(seq 1 12); do
  grep -q '\[ff\] advancing' "$L" 2>/dev/null && break
  sleep 5
done
if ! grep -q '\[ff\] advancing' "$L" 2>/dev/null; then
  echo "the clock never started: the geoscape was never reached in 60s."
  echo "the game is most likely sitting on a dialog. Last lines of its log:"
  tail -3 "$L" | sed 's/.*\]\t//'
  pkill -9 -x openxcom 2>/dev/null
  exit 1
fi

# Now it is genuinely advancing, so wait for the end.
for i in $(seq 1 240); do
  grep -q '\[ff\] done' "$L" 2>/dev/null && break
  sleep 5
done
sleep 2
pkill -9 -x openxcom 2>/dev/null

echo "=== $DAYS days ==="
grep -E '\[ff\]' "$L" | sed 's/.*INFO\]\t//'
echo
grep '\[camp\]' "$L" | sed 's/.*INFO\]\t//'
echo "=== months observed: $(grep -c '\[camp\]' "$L") ==="
echo
echo "=== economy ==="
grep '\[econ\]' "$L" | sed 's/.*INFO\]\t//' | tail -40
printf '  [econ] lines: %s\n' "$(grep -c '\[econ\]' "$L")"
echo
grep -E '\[FATAL\]|\[ERROR\]' "$L" | head -3
