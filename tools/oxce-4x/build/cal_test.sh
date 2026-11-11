#!/bin/bash
# Does the escalation calendar actually keep units off the map?
#
# Same map, same deployment, only the forced month changes. The deployment is
# Cobra's own, which uses ranks 5,4,3,2,1,6,7 - so it ASKS for B.A.T.s, Destro
# and Storm Shadow every single time. If the calendar works, month 0 fields
# none of them and month 25 fields B.A.T.s.
set -u
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad
B=$S/oxc/oxce/build/bin
L=/root/.local/share/openxcom/openxcom.log
export DISPLAY=:99
exec 9>/tmp/cal_test.lock
flock -n 9 || { echo "another cal_test.sh is running"; exit 1; }
trap 'pkill -9 -x openxcom 2>/dev/null' EXIT

run() {
  pgrep Xvfb >/dev/null || (nohup Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 &)
  sleep 2
  pkill -9 -x openxcom 2>/dev/null; sleep 1; rm -f "$L"
  local label="$1"; shift
  ( cd "$B" && env OXCE_MAP_HIRES=0 SDL_AUDIODRIVER=dummy "$@" \
      nohup ./openxcom -data "$B" > /tmp/oxc_cal.log 2>&1 < /dev/null & )
  sleep 10
  xdotool mousemove 838 400 click 1 2>/dev/null; sleep 3
  xdotool mousemove 232 736 click 1 2>/dev/null; sleep 9
  pkill -9 -x openxcom 2>/dev/null; sleep 1
  local total roster refused
  total=$(grep -c '\[cal\] spawned' "$L" 2>/dev/null) || total=0
  roster=$(grep '\[cal\] spawned' "$L" 2>/dev/null | sed 's/.*spawned //' \
           | sort | uniq -c | sort -rn | awk '{printf "%sx%s  ", $1, $2}')
  refused=$(grep -c 'is not available yet' "$L" 2>/dev/null) || refused=0
  printf '  %-18s %3d spawned, %3d refused\n' "$label" "$total" "$refused"
  printf '  %-18s %s\n' "" "${roster:-nothing}"
}

echo "same map, same deployment - only the month changes:"
run "month 0"  OXCE_CAL_MONTH=0
run "month 10" OXCE_CAL_MONTH=10
run "month 25" OXCE_CAL_MONTH=25
