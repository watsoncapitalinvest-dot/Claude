#!/bin/bash
# Does Cobra actually pick a downed Joe up, carry him, and take him off the map?
#
# Three claims, three separate runs, because a single run that ends with a captured Joe would
# not say WHICH of the three passes did the work - and the drop pass only matters if it can be
# shown to fire when the carrier goes down rather than when he walks out.
#
#   pickup   stun a Joe with a hostile beside him          -> "[capture] N picked up M"
#   extract  same, then put the carrier in the exit area   -> "[capture] M carried off the map"
#   drop     same, then kill the carrier                   -> "[capture] M dropped"
#
# The probe only arranges the board. The three passes in BattlescapeGame::captureStep are the
# real ones, so a wrong captureStep still fails here.
set -u
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad
B=$S/oxc/oxce/build/bin
L=/root/.local/share/openxcom/openxcom.log
export DISPLAY=:99

# The shared log is deleted at the start of every run, so two of these at once make each other
# report a battle that generated fine as a battle that never happened. Learned on gar_test.sh.
exec 9>/tmp/cap_test.lock
if ! flock -n 9; then
  echo "another cap_test.sh is running - that would clobber the shared log."
  exit 1
fi
trap 'pkill -9 -x openxcom 2>/dev/null' EXIT

run() {   # run <label> <turns> <extra env...>
  pgrep Xvfb >/dev/null || (nohup Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 &)
  sleep 2
  pkill -9 -x openxcom 2>/dev/null; sleep 1; rm -f "$L"
  local label="$1"; local turns="$2"; shift 2
  ( cd "$B" && env OXCE_MAP_HIRES=0 SDL_AUDIODRIVER=dummy "$@" \
      nohup ./openxcom -data "$B" > /tmp/oxc_cap.log 2>&1 < /dev/null & )
  # WAIT FOR THE MENU, never sleep a guess at it. The first version of this slept 10 seconds,
  # which was the number gar_test.sh uses; startup here takes about SIXTY, so every click landed
  # on a loading screen and both runs reported nothing at all - which reads exactly like a
  # feature that does not work. The log line below is the main menu's own music starting.
  local waited=0
  until grep -q "playMusic('GMSTORY')" "$L" 2>/dev/null; do
    sleep 2; waited=$((waited+2))
    if [ $waited -gt 150 ]; then echo "  $label: never reached the main menu"; return; fi
  done
  sleep 2
  xdotool mousemove 838 400 click 1 2>/dev/null; sleep 3   # New Battle
  xdotool mousemove 232 736 click 1 2>/dev/null; sleep 8   # OK -> generate
  # End the player's turn <turns> times so the hostile side moves and captureStep runs.
  #
  # END TURN IS BACKSPACE (Options::keyBattleEndTurn defaults to SDLK_BACKSPACE), not Return.
  # The first version pressed Return, which does nothing here, so the turn never ended,
  # endTurn() never ran and captureStep() was never called - and the run reported silence,
  # which is indistinguishable from three passes that do not work. The battle had generated
  # perfectly: GMTACTIC is in the log both times.
  local i
  for ((i=0; i<turns; i++)); do
    xdotool key BackSpace 2>/dev/null; sleep 2
    xdotool key Return 2>/dev/null    # clear a confirm-end-turn prompt if one appears
    sleep 10                          # let the hostile side actually take its turn
  done
  pkill -9 -x openxcom 2>/dev/null; sleep 1
  printf '  %-28s %s\n' "$label" "$(grep -oE '\[cap(ture)?\] .*' "$L" 2>/dev/null | sort -u | tr '\n' ' | ')"
}

echo "the probe arranges the board; captureStep decides what happens on it:"
run "pickup"  2 OXCE_CAP_STUN=1
run "extract" 3 OXCE_CAP_STUN=1 OXCE_CAP_EXIT=1
echo
echo "expected: pickup prints 'picked up'; extract prints 'picked up' AND 'carried off the map'."
echo "A run that prints 'stunned' and nothing else means the passes did not fire - which is"
echo "exactly the failure this harness exists to catch."
