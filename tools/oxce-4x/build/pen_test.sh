#!/bin/bash
# Does the penetration matrix actually come out of the ruleset?
#
# Shipping the tuning file with the defaults in it makes the obvious test useless: the probe
# prints 30/2/10/30/55/45 whether the file was read or ignored, so a pass proves nothing. Each
# case below therefore changes something to a value the defaults could not produce.
set -u
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad
B=$S/oxc/oxce/build/bin
M=/root/.local/share/openxcom/mods/GIJoe4x
L=/root/.local/share/openxcom/openxcom.log
T=$M/Ruleset/gijoe_tuning.rul
export DISPLAY=:99

run() {   # run() <name>  -> leaves the log in $L
  pkill -x openxcom 2>/dev/null; sleep 1; rm -f "$L"
  (cd "$B" && OXCE_PEN_PROBE=1 OXCE_MAP_HIRES=0 SDL_AUDIODRIVER=dummy \
     nohup ./openxcom -data "$B" > /tmp/oxc_pen.log 2>&1 &)
  sleep 9
  xdotool mousemove 838 400 click 1 2>/dev/null; sleep 2    # New Battle
  xdotool mousemove 232 736 click 1 2>/dev/null; sleep 8    # OK -> builds the TileEngine
  pkill -x openxcom 2>/dev/null; sleep 1
}

val() {   # val <material> <field>
  grep "\[penprobe\] $1 " "$L" | tail -1 | grep -oE "$2=[0-9.]+" | cut -d= -f2
}

check() { # check <label> <got> <want>
  if [ "$2" = "$3" ]; then echo "   ok   $1: $2"; else echo "   FAIL $1: got '$2' want '$3'"; fi
}

cp "$T" /tmp/tuning_backup.rul

echo "1. shipped defaults - confirms the probe and the chain, proves nothing on its own"
run
check "wood cost"      "$(val wood cost)"        "10"
check "masonry energy" "$(val masonry energyCost)" "20"
check "maxWalls"       "$(grep -oE 'maxWalls=[0-9]+' "$L" | tail -1 | cut -d= -f2)" "4"

echo "2. wood cost 999 - a number no default can produce"
sed -i 's/wood:     { cost: 10, pass: 0.65 }/wood:     { cost: 999, pass: 0.65 }/' "$T"
run
check "wood cost"  "$(val wood cost)"  "999"
check "light cost" "$(val light cost)" "2"      # untouched materials must not move

echo "3. masonry cost doubled, energyCost unstated - the ratio must carry"
cp /tmp/tuning_backup.rul "$T"
sed -i 's/masonry:  { cost: 30, pass: 0.35, energyCost: 20 }/masonry:  { cost: 60, pass: 0.35 }/' "$T"
run
check "masonry cost"   "$(val masonry cost)"       "60"
check "masonry energy" "$(val masonry energyCost)" "40"

echo "4. a material name that does not exist must be named, not ignored"
cp /tmp/tuning_backup.rul "$T"
sed -i 's/    metal:    { cost: 45, pass: 0.25 }/    metal:    { cost: 45, pass: 0.25 }\n    granite:  { cost: 77, pass: 0.11 }/' "$T"
run
if grep -q "no material named 'granite'" "$L"; then echo "   ok   warned about granite"
else echo "   FAIL no warning for the unknown material"; fi
check "metal cost unharmed" "$(val metal cost)" "45"

cp /tmp/tuning_backup.rul "$T"
echo "restored the shipped tuning file"
