#!/bin/bash
# Click each drawn control on the panel and check the globe does what it shows.
#
# The rotate and zoom surfaces are INVISIBLE rectangles, so no screenshot can tell
# you whether they line up with the arrows in the picture. The only honest test is
# to click where the art draws an arrow and see whether the globe moves that way -
# the fault this catches is an arrow that zooms, which is what vanilla's rectangles
# did under the replacement panel.
#
# The window is 320x200 scaled to fit 1920x1080, so the scale is 1080/200 = 5.4 and
# the picture is centred horizontally: x = 96 + base_x*5.4, y = 60 + base_y*5.4.
# Those two constants are the whole reason a click lands on the right control.
set -u
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad
B=$S/oxc/oxce/build/bin
L=/root/.local/share/openxcom/openxcom.log
OUT=${1:-$S/controls}
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
    nohup ./openxcom -data "$B" -continue > /tmp/oxc_ctl.log 2>&1 & )
for i in $(seq 1 90); do sleep 1; grep -q "GMSTORY" "$L" 2>/dev/null && break; done
sleep 4
xdotool key Return 2>/dev/null; sleep 2
xdotool key 1 2>/dev/null          # 5 secs: slowest clock, so the globe is still

shot() { import -window root "$OUT.$1.png" 2>/dev/null; }

# base coords of each DRAWN control, measured off the panel art
#            name          base_x  base_y
for spec in "rest 200 100" "right 296 177" "left 280 177" "up 288 162" \
            "down 288 192" "zoomin 309 174" "zoomout 267 174"; do
  set -- $spec
  name=$1; bx=$2; by=$3
  if [ "$name" = "rest" ]; then shot before; continue; fi
  sx=$(python3 -c "print(int(96+$bx*5.4))")
  sy=$(python3 -c "print(int(60+$by*5.4))")
  # ROTATION IS PRESS-AND-HOLD, NOT A CLICK. Globe::rotateLeft starts a timer on
  # mouse press and stopRotating() ends it on release, so `click` starts and stops
  # the rotation in the same instant and the globe moves by nothing measurable -
  # which read exactly like a hitbox in the wrong place. Zoom is a real click.
  case $name in
    zoomin|zoomout) xdotool mousemove "$sx" "$sy" click 1 2>/dev/null;;
    *) xdotool mousemove "$sx" "$sy" mousedown 1 2>/dev/null
       sleep 1.2
       xdotool mouseup 1 2>/dev/null;;
  esac
  sleep 1.5
  shot "$name"
  # put it back so each control is measured from the same starting view
  case $name in
    right)  rx=280; ry=177;;
    left)   rx=296; ry=177;;
    up)     rx=288; ry=192;;
    down)   rx=288; ry=162;;
    zoomin) rx=267; ry=174;;
    zoomout) rx=309; ry=174;;
  esac
  rsx=$(python3 -c "print(int(96+$rx*5.4))")
  rsy=$(python3 -c "print(int(60+$ry*5.4))")
  case $name in
    zoomin|zoomout) xdotool mousemove "$rsx" "$rsy" click 1 2>/dev/null;;
    *) xdotool mousemove "$rsx" "$rsy" mousedown 1 2>/dev/null
       sleep 1.2
       xdotool mouseup 1 2>/dev/null;;
  esac
  sleep 1.5
done

echo "fatals: $(grep -c FATAL "$L" 2>/dev/null)"
pkill -x openxcom 2>/dev/null
echo "shots written to $OUT.*.png"
