#!/bin/bash
# FIRST HOUR SHEETS (John 17 Nov 18:19: "all of the playable characters from the first hour rendered with all of the
# animations they need including stairs and hands up before my next test"). 1216-frame sheets: the 896 walk16 frames,
# re-framed so no clip runs off the cell (FirstHour item 5), plus up the stairs, down the stairs and hands up.
#   render_firsthour.sh name [name ...]       sheets land in /tmp/claude-0/ws/cast/sheets16/
# The stairs clips are John's (Reference\cartel\clips_17nov.blend, walk_up_stairs / walk_down_stairs, the down one
# looped by loop_close.py); hands up is posed on each model by render_char.py (no clip exists).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
K=/tmp/claude-0/ws/packs16; P=/tmp/claude-0/ws/mix/packs; Q=/tmp/claude-0/ws/mix/pistol; W=/tmp/claude-0/ws/cast
LIB=${CLIPLIB:-/mnt/user-data/uploads/GIJoe_XCOM_4x/Reference/cartel/clips_17nov.blend}
IDLE="/mnt/user-data/uploads/Downloads/Standing Idle.fbx"
CL="stand=$P/idle.fbx,kneel=$P/idle crouching.fbx,aim=$P/idle aiming.fbx,death=$P/death from the front.fbx,pstand=$Q/pistol idle.fbx,pkneel=$Q/pistol kneeling idle.fbx"
CL="$CL,walk=$K/Basic Shooter Pack/walking.fbx,pwalk=$K/Pistol_Handgun Locomotion Pack/pistol walk.fbx,swalk=$K/Rifle 8-Way Locomotion Pack/walk crouching forward.fbx,ewalk=$K/Action Adventure Pack/walking.fbx"
CL="$CL,upstairs=$LIB#walk_up_stairs,downstairs=$LIB#walk_down_stairs,handsup=$IDLE"
eval "$(sed -n '/^ink() {/,/^esac; }/p' $HERE/render_cast.sh)"
mkdir -p $W/sheets16
for n in "$@"; do
  echo "== $n $(date +%T)"
  B=/tmp/claude-0/ws/chars/$n.blend; [ -f $B ] || B=$W/$n.blend
  [ -f $B ] || { echo "no blend for $n"; continue; }
  I=$(ink $n); R=${I#*|}; FOLD=${R%%|*}; PEN=""; [ "$R" != "$FOLD" ] && PEN=${R#*|}
  SH=""; case " $PEN" in *" PENIDS="*) SH="--shade" ;; esac
  rm -rf $W/fh_$n
  python3 $HERE/render_char.py --blend $B --clips "$CL" --frames 8 --clipframes walk=16,pwalk=16,swalk=16,ewalk=16,upstairs=16,downstairs=16 $SH --out $W/fh_$n > $W/$n.fh.log 2>&1 || { echo "render failed $n"; tail -3 $W/$n.fh.log; continue; }
  W16=1 env $PEN HAIR=${I%%|*} FOLD_IDS=$FOLD python3 $HERE/assemble_sheet.py $W/fh_$n $W/sheets16 $n > $W/$n.fha.log 2>&1 || { echo "assemble failed $n"; tail -3 $W/$n.fha.log; continue; }
  grep "^fit\|handsup:" $W/$n.fha.log $W/$n.fh.log | sed 's/^/   /'
  rm -rf $W/fh_$n
  echo "done $n $(date +%T)"
done
