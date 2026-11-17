#!/bin/bash
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad; U=/tmp/claude-0/ws/pfull; pkill -9 openxcom; sleep 1; export DISPLAY=:97
c(){ xdotool mousemove --sync $1 $2; sleep 0.3; xdotool mousedown 1; sleep 0.15; xdotool mouseup 1; }
rm -f $U/openxcom.log; (cd $S/w4/bin && OXCE_HIUI=1 OXCE_HICOLOR=1 OXCE_BATTLE_SCALE=4 OXCE_MAP_HIRES=4 SDL_AUDIODRIVER=dummy setsid ./openxcom -data $S/w4/bin -user $U -cfg $U -battlescapeScale 6 > /dev/null 2>&1 &)
for i in $(seq 180); do grep -q "GIJOE_THEME\|FATAL\|failed to load" $U/openxcom.log 2>/dev/null && break; sleep 1; done; sleep 8
c 960 600; sleep 4; c 1500 656; sleep 5
import -window root $S/nb1.png
