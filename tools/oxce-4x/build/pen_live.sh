#!/bin/bash
# Start a battle, hand the turn to the AI a few times, and report what penetration did.
#
# OXCE_PEN_LOG is a shipped switch now, not a probe, so this needs no instrumented build and
# John can run the same check himself after changing a number.
#
# The battlescape is a much safer thing to drive blind than the geoscape: nothing stops a clock,
# there are no modal popups to misread, and a failure shows up as no log lines rather than as a
# run that looks like it worked. End Turn is bound to a key, so there is no clicking on the map
# and no chance of ordering a soldier somewhere.
#
# usage: pen_live.sh [turns, default 6]
set -u
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad
B=$S/oxc/oxce/build/bin
L=/root/.local/share/openxcom/openxcom.log
TURNS=${1:-6}
export DISPLAY=:99

pgrep Xvfb >/dev/null || (nohup Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 &)
sleep 2
pkill -9 -x openxcom 2>/dev/null; sleep 1; rm -f "$L"

( cd "$B" && OXCE_PEN_LOG=1 OXCE_MAP_HIRES=0 SDL_AUDIODRIVER=dummy \
    nohup ./openxcom -data "$B" > /tmp/oxc_penlive.log 2>&1 & )
sleep 10
# The same click path start_battle.sh uses and has used all week. Return does NOT dismiss the
# inventory screen - its OK is a button in the top right - and the first attempt at this sat
# there for six turns pressing End Turn at a screen that has no turns.
xdotool mousemove 838 400 click 1 2>/dev/null; sleep 3    # New Battle
xdotool mousemove 232 736 click 1 2>/dev/null; sleep 6    # OK
xdotool mousemove 640 690 click 1 2>/dev/null; sleep 4    # briefing OK
xdotool mousemove 1016 48 click 1 2>/dev/null; sleep 5    # inventory OK
xdotool mousemove 640 560 click 1 2>/dev/null; sleep 4    # turn screen

# Backspace is End Turn. Each round the AI moves and shoots, which is where the shots come from.
for i in $(seq 1 "$TURNS"); do
  xdotool key BackSpace 2>/dev/null
  sleep 6
  xdotool key Return 2>/dev/null     # clear any "aliens spotted" style prompt
  sleep 2
done
import -window root /tmp/penlive_end.png 2>/dev/null
pkill -9 -x openxcom 2>/dev/null

python3 -I "$S/rb/build/pen_live_report.py" "$L"
