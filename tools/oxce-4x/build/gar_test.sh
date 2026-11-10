#!/bin/bash
# Does the camp's bonus actually put men on the map, and does the rank cap keep them off it?
#
# A New Battle has no alien bases, so the real lookup returns zero and the battle cannot show the
# effect - which is why the probe forces the numbers. Same map, same deployment, three runs:
# nothing forced, a bonus forced, a cap forced. If the counts do not move, the two lines that use
# the lookup do not work, whatever the campaign log says about the lookup itself.
set -u
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad
B=$S/oxc/oxce/build/bin
L=/root/.local/share/openxcom/openxcom.log
export DISPLAY=:99

run() {   # run <label> <extra env assignments...>
  pgrep Xvfb >/dev/null || (nohup Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 &)
  sleep 2
  pkill -9 -x openxcom 2>/dev/null; sleep 1; rm -f "$L"
  local label="$1"; shift
  ( cd "$B" && env OXCE_GAR_LOG=1 OXCE_MAP_HIRES=0 SDL_AUDIODRIVER=dummy "$@" \
      nohup ./openxcom -data "$B" > /tmp/oxc_gar.log 2>&1 & )
  sleep 10
  xdotool mousemove 838 400 click 1 2>/dev/null; sleep 3    # New Battle
  xdotool mousemove 232 736 click 1 2>/dev/null; sleep 8    # OK -> generates the map
  pkill -9 -x openxcom 2>/dev/null; sleep 1
  local total ranks
  total=$(grep -c '\[gar\] spawned' "$L" 2>/dev/null || echo 0)
  ranks=$(grep '\[gar\] spawned' "$L" 2>/dev/null | grep -oE 'rank=[0-9]+' | sort | uniq -c \
          | awk '{printf "%s:%s ", $2, $1}')
  printf '  %-22s %3d units   %s\n' "$label" "$total" "${ranks:-none}"
  grep -m1 '\[gar\] deployment=' "$L" 2>/dev/null | sed 's/.*INFO\]\t/      /'
}

echo "same map, same deployment, only the forced numbers change:"
run "as the game plays it"
run "bonus forced to 2"  OXCE_GAR_FORCE=2
run "cap forced to 5"    OXCE_GAR_CAP=5
echo
echo "expected: the bonus run has more units than the first; the cap run has none"
echo "below rank 5, and the warning fires instead if that would empty the map."
