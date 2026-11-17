#!/bin/bash
# WALK16 (BRIEF_FOR_BUILD_Walk16; John 16 Nov 21:29 "do the animations now"): re-render a soldier's walks at 16 frames
# a stride and assemble the 896-frame sheet (six still clips + four walks; UnitSprite reads it by its size).
#   render_walk16.sh name [name ...]
# The four walks: two-handed gun = Basic Shooter "walking", pistol = Pistol pack "pistol walk", crouched =
# Rifle 8-Way "walk crouching forward", empty-handed / knife = Action Adventure "walking".
# The still clips are reused from an earlier render (fr_<name>) when there is one, else rendered too.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
K=/tmp/claude-0/ws/packs16
P=/tmp/claude-0/ws/mix/packs
Q=/tmp/claude-0/ws/mix/pistol
W=/tmp/claude-0/ws/cast
WALKS="walk=$K/Basic Shooter Pack/walking.fbx,pwalk=$K/Pistol_Handgun Locomotion Pack/pistol walk.fbx,swalk=$K/Rifle 8-Way Locomotion Pack/walk crouching forward.fbx,ewalk=$K/Action Adventure Pack/walking.fbx"
STILLS="stand=$P/idle.fbx,kneel=$P/idle crouching.fbx,aim=$P/idle aiming.fbx,death=$P/death from the front.fbx,pstand=$Q/pistol idle.fbx,pkneel=$Q/pistol kneeling idle.fbx"
D=/mnt/user-data/uploads/Downloads
CIV_STILLS="stand=$D/Standing Idle.fbx,kneel=$D/Standing Idle.fbx,aim=$D/Standing Idle.fbx,death=$P/death from the front.fbx,pstand=$D/Standing Idle.fbx,pkneel=$D/Standing Idle.fbx"
eval "$(sed -n '/^ink() {/,/^esac; }/p' $HERE/render_cast.sh)"
mkdir -p $W/sheets16
for n in "$@"; do
  echo "== $n $(date +%T)"
  B=/tmp/claude-0/ws/chars/$n.blend; [ -f $B ] || B=/tmp/claude-0/ws/civ/$n.blend; [ -f $B ] || B=$W/$n.blend
  [ -f $B ] || { echo "no blend for $n"; continue; }
  I=$(ink $n); R=${I#*|}; FOLD=${R%%|*}; PEN=""; [ "$R" != "$FOLD" ] && PEN=${R#*|}
  SH=""; case " $PEN" in *" PENIDS="*) SH="--shade" ;; esac
  CL="$WALKS"; SRC=$W/fr16_$n
  # a civilian's stills are the idle he was rendered with (Downloads "Standing Idle"), for every still clip
  ST="$STILLS"; case $B in */civ/*) ST="$CIV_STILLS" ;; esac
  if [ -d $W/fr_$n ] && [ -f $W/fr_$n/meta.json ] && [ -d $W/fr_$n/pkneel ]; then SRC="$W/fr_$n,$W/fr16_$n"; else CL="$ST,$WALKS"; fi
  rm -rf $W/fr16_$n
  python3 $HERE/render_char.py --blend $B --clips "$CL" --frames 8 --clipframes walk=16,pwalk=16,swalk=16,ewalk=16 $SH --out $W/fr16_$n > $W/$n.r16.log 2>&1 || { echo "render failed $n"; continue; }
  W16=1 env $PEN HAIR=${I%%|*} FOLD_IDS=$FOLD python3 $HERE/assemble_sheet.py "$SRC" $W/sheets16 $n > $W/$n.a16.log 2>&1 || { echo "assemble failed $n"; tail -3 $W/$n.a16.log; continue; }
  echo "done $n $(date +%T)"
done
