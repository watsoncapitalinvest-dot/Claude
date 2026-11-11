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

# Two of these running at once destroy each other: every run deletes the shared log at its
# start, so the other one greps an empty file and reports a battle that generated fine as
# "0 units, the battle did not generate". That happened, and the six FAILs it produced were
# about the harness and not the engine. Second time today two runs have fought over shared
# state, so it gets a lock rather than care.
exec 9>/tmp/gar_test.lock
if ! flock -n 9; then
  echo "another gar_test.sh is already running - that would clobber the shared log."
  echo "wait for it, or: pkill -9 -f gar_test.sh; pkill -9 -x openxcom"
  exit 1
fi
# and never leave a game behind for the next run to trip over
trap 'pkill -9 -x openxcom 2>/dev/null' EXIT

run() {   # run <label> <extra env assignments...>
  pgrep Xvfb >/dev/null || (nohup Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 &)
  sleep 2
  pkill -9 -x openxcom 2>/dev/null; sleep 1; rm -f "$L"
  local label="$1"; shift
  ( cd "$B" && env OXCE_GAR_LOG=1 OXCE_MAP_HIRES=0 SDL_AUDIODRIVER=dummy "$@" \
      nohup ./openxcom -data "$B" > /tmp/oxc_gar.log 2>&1 < /dev/null & )
  sleep 10
  xdotool mousemove 838 400 click 1 2>/dev/null; sleep 3    # New Battle
  xdotool mousemove 232 736 click 1 2>/dev/null; sleep 8    # OK -> generates the map
  pkill -9 -x openxcom 2>/dev/null; sleep 1
  local total ranks kits guns
  # grep -c already prints 0 and exits 1 on no match, so "|| echo 0" printed "0\n0" and
  # printf then rejected it as an invalid number. The noise was hiding the real result.
  total=$(grep -c '\[gar\] spawned' "$L" 2>/dev/null) || total=0
  ranks=$(grep '\[gar\] spawned' "$L" 2>/dev/null | grep -oE 'rank=[0-9]+' | sort | uniq -c \
          | awk '{printf "%s:%s ", $2, $1}')
  # The kit histogram is the whole point of the starvation run: "kit=0" on every man is the
  # pass, and a baseline that is also all zeroes means the test proved nothing rather than
  # that the feature works.
  kits=$(grep '\[gar\] spawned' "$L" 2>/dev/null | grep -oE 'kit=[0-9]+' | sort | uniq -c \
          | awk '{printf "%s:%s ", $2, $1}')
  guns=$(grep '\[gar\] spawned' "$L" 2>/dev/null | grep -oE 'first=[A-Z_]+' | sed 's/first=//' \
          | sort | uniq -c | sort -rn | head -3 | awk '{printf "%sx%s ", $1, $2}')
  printf '  %-22s %3d units   %s\n' "$label" "$total" "${ranks:-none}"
  printf '  %-22s %s\n' "" "${kits:-no kit logged}"
  printf '  %-22s %s\n' "" "${guns:-}"
  # Totals cannot show a one-man-per-entry penalty against New Battle's own dice, so the
  # arithmetic is checked exactly instead. PEN/STV are what this run should produce.
  python3 -I "$S/rb/build/gar_check.py" "$L" "${PEN:-0}" "${STV:-0}" "${CAP:--1}" 2>&1 | sed 's/^/    /'  
  grep -m1 '\[gar\] deployment=' "$L" 2>/dev/null | sed 's/.*INFO\]\t/      /'
}

echo "same map, same deployment, only the forced numbers change:"
run "as the game plays it"
run "bonus forced to 2"  OXCE_GAR_FORCE=2
run "cap forced to 5"    OXCE_GAR_CAP=5
CAP=0 run "calendar month 0"     OXCE_GAR_MONTH=0
CAP=1 run "calendar month 3"     OXCE_GAR_MONTH=3
CAP=2 run "calendar month 8"     OXCE_GAR_MONTH=8
STV=1 CAP=2 run "month 8 but starved"  OXCE_GAR_MONTH=8 OXCE_GAR_STARVED=1
STV=1 run "region out of guns"  OXCE_GAR_STARVED=1
PEN=1 run "region out of money"  OXCE_GAR_BROKE=1
PEN=1 STV=1 run "out of both"    OXCE_GAR_STARVED=1 OXCE_GAR_BROKE=1
echo
echo "expected: the bonus run has more units than the first; the cap run has none"
echo "below rank 5; the out-of-guns run is kit=0 on every man while the first three are not;"
echo "the out-of-money run has FEWER units than the first but keeps its kit spread; and"
echo "out-of-both is fewer units AND all kit=0. Different shortages, different maps."
