#!/bin/bash
# Render soldiers into game sheets, one after another.
#   render_cast.sh name [name ...]
# A ready-built character in /tmp/claude-0/ws/chars/<name>.blend is used as it is
# (Regular Joe, Roadblock, Beach Head, Snake Eyes, Doc, Stalker, Scarlett, the Cobra troopers, Ace); otherwise
# the cartoon-cast member is built from its look + textures with cast/build_cast.py.
# Sheets land in /tmp/claude-0/ws/cast/sheets/<name>_body*.png + anchors.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
CC=/mnt/user-data/uploads/GIJoe_XCOM_4x/Reference/models/mixamo/painted/cast_cartoon
P=/tmp/claude-0/ws/mix/packs
Q=/tmp/claude-0/ws/mix/pistol
W=/tmp/claude-0/ws/cast
CLIPS="stand=$P/idle.fbx,walk=$P/walk forward.fbx,kneel=$P/idle crouching.fbx,aim=$P/idle aiming.fbx,death=$P/death from the front.fbx,pstand=$Q/pistol idle.fbx,pwalk=$Q/pistol walk.fbx,pkneel=$Q/pistol kneeling idle.fbx"
# ink per man: "HAIR colour | FOLD_IDS pen fold lines | PEN env" (from the design chat's briefs).
# The third field is env for soldier_ink.py. PENIDS in it turns on pen shading (John, 12 Nov): render_char.py --shade
# renders the geometry pass and soldier_ink.py reads PENIDS / PENPCT / PENDARK / PENFACE. TERMIDS / TERMMIN (the
# Roadblock method's fold lines, John 14:59; compose_factory.py's rule) need no extra pass, so no --shade for them.
ink() { case $1 in
  duke)      echo "246,182,22||TERMIDS=3,6,11 TERMMIN=90" ;;          # Duke v4, Roadblock method: tones in the texture, fold lines at compose (v4 meta hair tones)
  roadblock) echo "40,30,26|20:0.36:2:40|PENIDS=6,21 PENPCT=84 PENDARK=0.66" ;;          # pen folds replace the wavy trouser FOLD 6
  scarlett)  echo "212,66,40|24:0.35:3:80|PENIDS=24 PENPCT=84 PENDARK=0.66 PENFACE=1 PENFACEIDS=20" ;;
  snake_eyes) echo "||PENIDS=20 PENPCT=84 PENDARK=0.66" ;;                               # bodysuit; masked face, no PENFACE
  beach_head) echo "||PENIDS=20,22 PENPCT=84 PENDARK=0.66" ;;                            # shirt + camo trousers; balaclava, no PENFACE
  # cast v3 (Roadblock textures on the v2 +1.6 cm builds): fold lines TERMIDS=3,6,11 TERMMIN=90, HAIR = <name>_cartoon.json
  grunt)       echo "176,101,39||TERMIDS=3,6,11 TERMMIN=90" ;;
  zap)         echo "48,38,32||TERMIDS=3,6,11 TERMMIN=90" ;;
  rock_n_roll) echo "246,182,22||TERMIDS=3,6,11 TERMMIN=90" ;;
  breaker)     echo "132,80,34||TERMIDS=3,6,11 TERMMIN=90" ;;
  airborne)    echo "48,38,32||TERMIDS=3,6,11 TERMMIN=90" ;;
  hawk)        echo "132,80,34||TERMIDS=3,6,11 TERMMIN=90" ;;
  flint)       echo "48,38,32||TERMIDS=3,6,11 TERMMIN=90" ;;
  doc)         echo "48,38,32||TERMIDS=3,6,11 TERMMIN=90" ;;       # Ch18 head: his hair is flat id 37, so HAIR changes nothing
  stalker)     echo "48,38,32||TERMIDS=3,6,11 TERMMIN=90" ;;       # (was 36,30,26; cartoon.json says 48,38,32 - id 37 hair as Doc)
  flash)       echo "|" ;;                                          # Ch15, v2 textures as shipped (his own bake); not re-inked with TERMIDS
  greenshirt_rifleman|greenshirt_medic) echo "||" ;;                # v4: Roadblock method, tones + fold ink in the textures; no pen, no --shade (medic: satchel_* id 37, contour only)
  grand_slam) echo "||" ;;                                           # Ch15 slimmed, Roadblock-method paint; no pen, no --shade
  greenshirt_pilot) echo "||PENIDS=20 PENPCT=84 PENDARK=0.66 INKJOIN=21:20" ;;           # Ch15: suit 20, rest 21 joined for lines
  ace)       echo "||PENIDS=20 PENPCT=84 PENDARK=0.66 PENFACE=1 INKJOIN=21:20" ;;    # Ch15 slimmed: suit 20, rest 21 joined; helmet 26, Duke face 2 (PENFACE)
  regular_joe) echo "|" ;;
  cobra_soldier|cobra_officer|crimson_guard|cobra_recruit|viper_pilot) echo "|" ;;   # Cobra v4: Roadblock shading, fold ink baked into the texture, outline only
  Ch*|Remy) echo "$(awk -v n=$1 '$1==n{print $2}' $HERE/civ/civ_hair.txt)|" ;;   # civilians: hair as rendered
  *) H=$(python3 -c "import json;print(','.join(map(str,json.load(open('$CC/$1/${1}_cartoon.json'))['colors']['hair'])))" 2>/dev/null); echo "$H|" ;;
esac; }
D=/mnt/user-data/uploads/Downloads
CIV_CLIPS="stand=$D/Standing Idle.fbx,walk=$D/Walking.fbx,kneel=$D/Standing Idle.fbx,aim=$D/Standing Idle.fbx,death=$P/death from the front.fbx"
mkdir -p $W/sheets
for n in "$@"; do
  [ -f $W/sheets/${n}_body.png ] && [ -z "${FORCE:-}" ] && { echo "skip $n (sheet exists; FORCE=1 to redo)"; continue; }
  echo "== $n $(date +%T)"
  B=/tmp/claude-0/ws/chars/$n.blend; CL=$CLIPS
  # civilians (build/sprites/civ): own blends, plain idle / walk / death; kneel and aim reuse the idle
  if [ -f /tmp/claude-0/ws/civ/$n.blend ]; then B=/tmp/claude-0/ws/civ/$n.blend; CL="$CIV_CLIPS"; fi
  if [ ! -f $B ]; then
    B=$W/$n.blend
    LOOK=$CC/looks/$n.json CHAR_TEX=$CC/$n python3 $HERE/cast/build_cast.py --clip $P/idle.fbx --save-blend $B > $W/$n.build.log 2>&1 || { echo "build failed $n"; continue; }
  fi
  rm -rf $W/fr_$n
  I=$(ink $n); R=${I#*|}; FOLD=${R%%|*}; PEN=""; [ "$R" != "$FOLD" ] && PEN=${R#*|}
  SH=""; case " $PEN" in *" PENIDS="*) SH="--shade" ;; esac      # only pen shading needs the geometry pass
  python3 $HERE/render_char.py --blend $B --clips "$CL" --frames 8 $SH --out $W/fr_$n > $W/$n.render.log 2>&1 || { echo "render failed $n"; continue; }
  env $PEN HAIR=${I%%|*} FOLD_IDS=$FOLD python3 $HERE/assemble_sheet.py $W/fr_$n $W/sheets $n > $W/$n.asm.log 2>&1 || { echo "assemble failed $n"; continue; }
  echo "done $n $(date +%T)"
done
