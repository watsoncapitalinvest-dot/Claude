#!/bin/bash
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad; U=/tmp/claude-0/ws/pfull; pkill -9 openxcom; sleep 1; export DISPLAY=:97
rm -f $U/openxcom.log; (cd $S/w4/bin && OXCE_HIUI=1 OXCE_HICOLOR=1 OXCE_BATTLE_SCALE=4 OXCE_MAP_HIRES=4 SDL_AUDIODRIVER=dummy env ${AUTO:+OXCE_AIRFIGHT_AUTO=1} ${TRACE:+OXCE_AIRFIGHT_TRACE=1} ${UNDER:+OXCE_SEA_TEST_UNDER=1} setsid ./openxcom -data $S/w4/bin -user $U -cfg $U -battlescapeScale 6 > /dev/null 2>&1 &)
for i in $(seq 180); do grep -q "GIJOE_THEME\|FATAL\|failed to load" $U/openxcom.log 2>/dev/null && break; sleep 1; done; sleep 8
xdotool mousemove --sync 960 600; xdotool click 1; sleep 4
