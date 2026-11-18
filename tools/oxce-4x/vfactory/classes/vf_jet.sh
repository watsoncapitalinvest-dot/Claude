#!/bin/bash
# VFACTORY re-render of a ROSTER jet from /home/claude/rt (ROSTER's scripts lived in /tmp/claude-0; same tools, local paths).
# usage: vf_jet.sh <v5 dir> <cfg file> <package name> <launch script>   (launch script: bash run in /home/claude/rt/veh after the frames)
set -e
D=$1; CF=$2; P=$3; LS=$4
C=/home/claude/rt/v5/$D/$CF; O=$(python3 -c "import json;print(json.load(open('$C'))['out'])")
rm -rf $O /home/claude/rt/veh/pkg/$P
cd /tmp && python3 -I /home/claude/rt/gen/render.py $C | tail -1; FILL=1 python3 -I /home/claude/rt/gen/render.py $C | tail -1
mkdir -p /home/claude/rt/veh/pkg/$P && echo '{}' > /home/claude/rt/veh/pkg/$P/manifest.json
cd /home/claude/rt/veh && bash $LS
cd /tmp && python3 -I /home/claude/rt/gen/pkg.py $C | tail -1 && python3 -I /home/claude/rt/gen/preview.py $C | tail -1 && python3 -I /home/claude/rt/gen/turntable.py /home/claude/rt/veh/pkg/$P $P 64 /home/claude/rt/veh/pkg/$P/${P}_turntable.gif 1.2 | tail -1
echo JET_DONE $P
