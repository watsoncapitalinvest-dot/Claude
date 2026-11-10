#!/bin/bash
# Run a campaign headlessly and print one line a month of what Cobra did.
#
# Loads the test save and holds the geoscape at 1-day compression, which is key 6. Nothing is
# clicked on the globe, so this is Cobra left entirely alone: no raids, no interference, which
# is the run that shows the policy most clearly. A run WITH raids is the interesting second
# test and needs a hand on the controls.
#
# usage: campaign_run.sh [seconds of real time to let it run, default 90]
set -u
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad
B=$S/oxc/oxce/build/bin
L=/root/.local/share/openxcom/openxcom.log
RUN=${1:-90}
export DISPLAY=:99

pgrep Xvfb >/dev/null || (nohup Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 &)
sleep 2
pkill -x openxcom 2>/dev/null; sleep 1; rm -f "$L"

( cd "$B" && OXCE_CAMP_PROBE=1 OXCE_MAP_HIRES=0 SDL_AUDIODRIVER=dummy \
    nohup ./openxcom -data "$B" -continue > /tmp/oxc_camp.log 2>&1 & )
sleep 12

# -continue lands on the geoscape with the save loaded. Dismiss anything modal, then hold 1 day.
xdotool key Return 2>/dev/null; sleep 1
xdotool key 6 2>/dev/null
# Everything that stops the clock has to be cleared or the run sits on one date forever. There
# are two kinds and they want different keys. The month-end funding report takes Return. A UFO
# detection popup does NOT: its default button is INTERCEPT, so Return would scramble a craft,
# and its CANCEL button is what to click.
#
# Escape is what NOT to send. On the geoscape it opens the options menu, and a second one walks
# into the mod list - which is where the first long run ended up, three months in, with the
# clock stopped and the log looking exactly like a campaign that had gone quiet.
for i in $(seq 1 $((RUN * 2))); do
  sleep 0.5
  xdotool mousemove 512 625 click 1 2>/dev/null   # CANCEL on a detection popup
  xdotool key Return 2>/dev/null                  # OK on the month-end report
  xdotool key 6 2>/dev/null                       # back to 1-day compression
done
import -window root /tmp/campaign_end.png 2>/dev/null
pkill -x openxcom 2>/dev/null; sleep 1

echo "=== months observed ==="
grep '\[camp\]' "$L" | sed 's/.*INFO\]\t//'
echo "=== count: $(grep -c '\[camp\]' "$L") ==="
grep -E '\[FATAL\]|\[ERROR\]' "$L" | head -3
