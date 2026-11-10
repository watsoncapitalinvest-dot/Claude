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

pgrep Xvfb >/dev/null || (nohup Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 &)
sleep 2
pkill -9 -x openxcom 2>/dev/null; sleep 1; rm -f "$L"

( cd "$B" && OXCE_CAMP_PROBE=1 OXCE_CAMP_FF="$DAYS" OXCE_CAMP_RAID="${RAID:-}" OXCE_CAMP_PLANT="${PLANT:-}" OXCE_MAP_HIRES=0 SDL_AUDIODRIVER=dummy \
    nohup ./openxcom -data "$B" -continue > /tmp/oxc_ff.log 2>&1 & )

# Wait for the fast-forward to report it is done, rather than guessing how long it takes.
for i in $(seq 1 240); do
  sleep 5
  grep -q '\[ff\] done' "$L" 2>/dev/null && break
done
sleep 2
pkill -9 -x openxcom 2>/dev/null

echo "=== $DAYS days ==="
grep -E '\[ff\]' "$L" | sed 's/.*INFO\]\t//'
echo
grep '\[camp\]' "$L" | sed 's/.*INFO\]\t//'
echo "=== months observed: $(grep -c '\[camp\]' "$L") ==="
grep -E '\[FATAL\]|\[ERROR\]' "$L" | head -3
