#!/bin/bash
# Drive the game through its main screens, photograph each, and list every
# string that is wider or taller than its box.
#
# John: "all the fonts need to be correct and colors and it looks like its
# clipping". Clipping is silent - the engine cuts a string at its box edge and
# says nothing - so finding it by eye means opening every window and squinting.
# OXCE_CLIP_REPORT makes Text::draw log each overflowing string once, and this
# walks the screens a player actually uses so the log becomes the list.
#
# The window is 320x200 at 5.4x, offset (96,60): x = 96 + bx*5.4, y = 60 + by*5.4.
#
# usage: ui_sweep.sh <out-dir>
set -u
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad
B=$S/oxc/oxce/build/bin
L=/root/.local/share/openxcom/openxcom.log
OUT=${1:?usage: ui_sweep.sh <out-dir>}
mkdir -p "$OUT"
export DISPLAY=:99

pgrep Xvfb >/dev/null || (nohup Xvfb :99 -screen 0 1920x1200x24 >/dev/null 2>&1 &)
sleep 2
pkill -x openxcom 2>/dev/null; sleep 1; rm -f "$L"
SAVEDIR=/root/.local/share/openxcom/xcom1
HID=""
[ -f "$SAVEDIR/_autobattle_.asav" ] && { mv "$SAVEDIR/_autobattle_.asav" "$SAVEDIR/_autobattle_.asav.aside"; HID=1; }
restore() { [ -n "$HID" ] && [ -f "$SAVEDIR/_autobattle_.asav.aside" ] && mv "$SAVEDIR/_autobattle_.asav.aside" "$SAVEDIR/_autobattle_.asav"; }
trap restore EXIT

( cd "$B" && OXCE_MAP_HIRES=4 OXCE_CLIP_REPORT=1 SDL_AUDIODRIVER=dummy \
    nohup ./openxcom -data "$B" -continue > /tmp/oxc_sweep.log 2>&1 & )
for i in $(seq 1 90); do sleep 1; grep -q GMSTORY "$L" 2>/dev/null && break; done
sleep 4; xdotool key Return; sleep 2; xdotool key 1; sleep 1

click() { xdotool mousemove "$(python3 -c "print(int(96+$1*5.4))")" "$(python3 -c "print(int(60+$2*5.4))")" click 1; }
shot()  { import -window root "$OUT/$1.png" 2>/dev/null; echo "  shot $1"; }
back()  { xdotool key Escape; sleep 2; }

shot geoscape
# geoscape panel buttons, panel-local centre x 32 => base 288
for spec in "intercept 5" "graphs 29" "intel_files 41" "funding 65"; do
  set -- $spec; click 288 "$2"; sleep 3; shot "$1"; back
done

# the base screen and its sub-screens (right column x 192..320)
click 288 17; sleep 3; shot basescape
for spec in "base_info 77" "soldiers 90" "crafts 103" "facilities 116" "research 129" \
            "manufacture 142" "transfer 155" "purchase 168" "sell 181"; do
  set -- $spec; click 256 "$2"; sleep 3; shot "$1"; back
done
back

grep "\[clip\]" "$L" | sed 's/^.*\[clip\]/[clip]/' > "$OUT/clips.txt"
pkill -x openxcom
echo "screens: $(ls "$OUT"/*.png | wc -l)   clipped strings: $(wc -l < "$OUT/clips.txt")"
