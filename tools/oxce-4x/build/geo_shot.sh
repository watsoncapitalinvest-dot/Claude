#!/bin/bash
# Load the test save, land on the geoscape at 4x, and photograph it.
#
# This is the only honest test of the side panel and the globe texture. Both are
# art drawn by the engine through HiUI and Globe::drawEarthTexture, so measuring
# the PNG proves the file is right and proves nothing about what is on screen:
# GEOBORD_hi.png was loaded, logged and never drawn for a whole afternoon because
# the geoscape holds a COPY of GEOBORD and the twin is looked up by pointer.
#
# OXCE_MAP_HIRES=4 is what Play_4x.bat sets, and it is what turns HiColor and HiUI
# on - at 0 the panel twin is never consulted at all and the shot would be of the
# 64-pixel original blown up, which is the thing being replaced.
#
# usage: geo_shot.sh <out.png> [seconds to settle, default 70]
set -u
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad
B=$S/oxc/oxce/build/bin
L=/root/.local/share/openxcom/openxcom.log
OUT=${1:?usage: geo_shot.sh <out.png> [settle]}
SETTLE=${2:-70}
export DISPLAY=:99

pgrep Xvfb >/dev/null || (nohup Xvfb :99 -screen 0 1920x1200x24 >/dev/null 2>&1 &)
sleep 2
pkill -x openxcom 2>/dev/null; sleep 1; rm -f "$L"

# -continue TAKES THE NEWEST SAVE, AND THE NEWEST SAVE IS USUALLY A BATTLE.
#
# The capture work leaves _autobattle_.asav behind every run, so -continue landed
# on the battlescape and the first geoscape shot was a photograph of Snake Eyes
# standing in a boatyard. There is no CLI switch for "load this one", so the
# battle autosave is moved aside for the duration and put back afterwards -
# never deleted, because it is the capture test's state.
SAVEDIR=/root/.local/share/openxcom/xcom1
HID=""
for f in "$SAVEDIR"/_autobattle_.asav; do
  [ -f "$f" ] && { mv "$f" "$f.aside"; HID="$f"; }
done
restore() { [ -n "$HID" ] && [ -f "$HID.aside" ] && mv "$HID.aside" "$HID"; }
trap restore EXIT

( cd "$B" && OXCE_MAP_HIRES=4 SDL_AUDIODRIVER=dummy \
    nohup ./openxcom -data "$B" -continue > /tmp/oxc_geo.log 2>&1 & )

# Startup is about a minute. Poll the log rather than sleeping a guessed amount:
# GMSTORY is the geoscape's own music and is the first line that means "we are
# there". Without this the shot was taken of the loading screen twice.
for i in $(seq 1 "$SETTLE"); do
  sleep 1
  grep -q "GMSTORY" "$L" 2>/dev/null && break
done
sleep 4
xdotool key Return 2>/dev/null; sleep 2   # dismiss anything modal over the globe
sleep 1
import -window root "$OUT" 2>/dev/null

echo "--- display mode ---"
grep -m2 "Display set to\|hiRes\|HiUI\|HiColor" "$L" 2>/dev/null
echo "--- GEOBORD / earth ---"
grep -m6 -i "geobord\|GLOBE_EARTH" "$L" 2>/dev/null
echo "--- fatals ---"
grep -c "FATAL" "$L" 2>/dev/null
pkill -x openxcom 2>/dev/null
echo "wrote $OUT"
