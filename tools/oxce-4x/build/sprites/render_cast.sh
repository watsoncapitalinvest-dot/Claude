#!/bin/bash
# Render soldiers into game sheets, one after another.
#   render_cast.sh name [name ...]
# A ready-built character in /tmp/claude-0/ws/chars/<name>.blend is used as it is
# (Regular Joe, Roadblock, Beach Head, Snake Eyes, Doc, Stalker, Scarlett); otherwise
# the cartoon-cast member is built from its look + textures with cast/build_cast.py.
# Sheets land in /tmp/claude-0/ws/cast/sheets/<name>_body*.png + anchors.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
CC=/mnt/user-data/uploads/GIJoe_XCOM_4x/Reference/models/mixamo/painted/cast_cartoon
P=/tmp/claude-0/ws/mix/packs
Q=/tmp/claude-0/ws/mix/pistol
W=/tmp/claude-0/ws/cast
CLIPS="stand=$P/idle.fbx,walk=$P/walk forward.fbx,kneel=$P/idle crouching.fbx,aim=$P/idle aiming.fbx,death=$P/death from the front.fbx,pstand=$Q/pistol idle.fbx,pwalk=$Q/pistol walk.fbx,pkneel=$Q/pistol kneeling idle.fbx"
# ink per man: HAIR colour and pen fold lines (from the design chat's briefs)
ink() { case $1 in
  roadblock) echo "40,30,26|6:0.45:3:50,20:0.36:2:40" ;;
  scarlett)  echo "212,66,40|24:0.35:3:80" ;;
  doc)       echo "48,38,32|" ;;
  stalker)   echo "36,30,26|" ;;
  regular_joe|beach_head|snake_eyes) echo "|" ;;
  *) H=$(python3 -c "import json;print(','.join(map(str,json.load(open('$CC/$1/${1}_cartoon.json'))['colors']['hair'])))" 2>/dev/null); echo "$H|" ;;
esac; }
mkdir -p $W/sheets
for n in "$@"; do
  echo "== $n $(date +%T)"
  B=/tmp/claude-0/ws/chars/$n.blend
  if [ ! -f $B ]; then
    B=$W/$n.blend
    LOOK=$CC/looks/$n.json CHAR_TEX=$CC/$n python3 $HERE/cast/build_cast.py --clip $P/idle.fbx --save-blend $B > $W/$n.build.log 2>&1 || { echo "build failed $n"; continue; }
  fi
  rm -rf $W/fr_$n
  python3 $HERE/render_char.py --blend $B --clips "$CLIPS" --frames 8 --out $W/fr_$n > $W/$n.render.log 2>&1 || { echo "render failed $n"; continue; }
  I=$(ink $n)
  HAIR=${I%%|*} FOLD_IDS=${I#*|} python3 $HERE/assemble_sheet.py $W/fr_$n $W/sheets $n > $W/$n.asm.log 2>&1 || { echo "assemble failed $n"; continue; }
  echo "done $n $(date +%T)"
done
