#!/bin/bash
# Launch the game fresh, operate ONE panel control, and keep the before/after pair.
#
# The six-in-a-row version could prove every rectangle was live - 41 to 79 per cent
# of the map changed under each - and could prove nothing about DIRECTION, because
# the globe never came back to the same place between controls and the land
# centroid on a sphere moves whichever way it likes as coastline rolls over the
# limb. Direction is the whole question: the rectangles were reassigned to the new
# art by hand, so a drawn left arrow wired to rotateRight would look perfect and
# behave backwards, and the two dials were a guess at which is zoom in.
#
# One control per launch, from the same save, is the only clean comparison.
#
# usage: geo_one_control.sh <name> <base_x> <base_y> <out-prefix> [hold|click]
set -u
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad
B=$S/oxc/oxce/build/bin
L=/root/.local/share/openxcom/openxcom.log
NAME=$1; BX=$2; BY=$3; OUT=$4; MODE=${5:-hold}
export DISPLAY=:99

pgrep Xvfb >/dev/null || (nohup Xvfb :99 -screen 0 1920x1200x24 >/dev/null 2>&1 &)
sleep 2
pkill -x openxcom 2>/dev/null; sleep 1; rm -f "$L"

SAVEDIR=/root/.local/share/openxcom/xcom1
HID=""
for f in "$SAVEDIR"/_autobattle_.asav; do
  [ -f "$f" ] && { mv "$f" "$f.aside"; HID="$f"; }
done
restore() { [ -n "$HID" ] && [ -f "$HID.aside" ] && mv "$HID.aside" "$HID"; }
trap restore EXIT

( cd "$B" && OXCE_MAP_HIRES=4 SDL_AUDIODRIVER=dummy \
    nohup ./openxcom -data "$B" -continue > /tmp/oxc_one.log 2>&1 & )
for i in $(seq 1 90); do sleep 1; grep -q "GMSTORY" "$L" 2>/dev/null && break; done
sleep 4
xdotool key Return 2>/dev/null; sleep 2
xdotool key 1 2>/dev/null            # slowest compression, so the globe sits still
sleep 2
import -window root "$OUT.$NAME.before.png" 2>/dev/null

SX=$(python3 -c "print(int(96+$BX*5.4))")
SY=$(python3 -c "print(int(60+$BY*5.4))")
if [ "$MODE" = click ]; then
  xdotool mousemove "$SX" "$SY" click 1 2>/dev/null
else
  xdotool mousemove "$SX" "$SY" mousedown 1 2>/dev/null
  sleep 1.0
  xdotool mouseup 1 2>/dev/null
fi
sleep 2
import -window root "$OUT.$NAME.after.png" 2>/dev/null
pkill -x openxcom 2>/dev/null
echo "$NAME done"
