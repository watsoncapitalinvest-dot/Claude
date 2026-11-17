#!/bin/bash
# nbgo2.sh N: New Battle mission N, straight onto the map (Joe turn 1), no end turn
S=/tmp/claude-0/-home-claude/cba64b7d-e243-5c8b-b8c1-3aaffafa2926/scratchpad; U=/tmp/claude-0/ws/pfull; export DISPLAY=:97
c(){ xdotool mousemove --sync $1 $2; sleep 0.3; xdotool mousedown 1; sleep 0.15; xdotool mouseup 1; }
pkill -9 openxcom; sleep 1; sed -i -e "s/^mission: .*/mission: $1/" -e "s/^terrain: .*/terrain: 0/" $U/xcom1/battle.cfg; $S/nb.sh >/dev/null 2>&1
c 408 1053; for i in $(seq 120); do grep -q "Mod::playMusic('GMTACTIC\|GMDEFEND\|GMNEWMAR\|GMTACT" $U/openxcom.log && break; sleep 1; done; sleep 3
c 960 993; sleep 10; c 1338 247; sleep 8; c 960 600; sleep 5
