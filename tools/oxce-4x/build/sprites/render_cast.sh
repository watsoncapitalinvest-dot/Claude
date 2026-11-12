#!/bin/bash
# Render the cartoon cast (design chat, BRIEF_FOR_BUILD_SESSION_CartoonCast.txt) into game sheets.
#   render_cast.sh name [name ...]      e.g. render_cast.sh grunt zap
# Needs the cast folder staged from Reference (CC below) and the Duke workspace in /tmp/claude-0/ws.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
CC=/mnt/user-data/uploads/GIJoe_XCOM_4x/Reference/models/mixamo/painted/cast_cartoon
P=/tmp/claude-0/ws/mix/packs
Q=/tmp/claude-0/ws/mix/pistol
W=/tmp/claude-0/ws/cast
CLIPS="stand=$P/idle.fbx,walk=$P/walk forward.fbx,kneel=$P/idle crouching.fbx,aim=$P/idle aiming.fbx,death=$P/death from the front.fbx,pstand=$Q/pistol idle.fbx,pwalk=$Q/pistol walk.fbx,pkneel=$Q/pistol kneeling idle.fbx"
mkdir -p $W/sheets
for n in "$@"; do
  echo "== $n $(date +%T)"
  LOOK=$CC/looks/$n.json CHAR_TEX=$CC/$n python3 $HERE/cast/build_cast.py --clip $P/idle.fbx --save-blend $W/$n.blend > $W/$n.build.log 2>&1 || { echo "build failed $n"; continue; }
  rm -rf $W/fr_$n
  python3 $HERE/render_char.py --blend $W/$n.blend --clips "$CLIPS" --frames 8 --out $W/fr_$n > $W/$n.render.log 2>&1 || { echo "render failed $n"; continue; }
  H=$(python3 -c "import json;print(','.join(map(str,json.load(open('$CC/$n/${n}_cartoon.json'))['colors']['hair'])))" 2>/dev/null || echo "")
  HAIR=$H python3 $HERE/assemble_sheet.py $W/fr_$n $W/sheets $n > $W/$n.asm.log 2>&1 || { echo "assemble failed $n"; continue; }
  echo "done $n $(date +%T)"
done
