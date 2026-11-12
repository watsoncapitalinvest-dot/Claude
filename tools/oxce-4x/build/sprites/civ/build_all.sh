#!/bin/bash
# Build + test-render every civilian. Heights: civ_heights.txt ("name height" per line).
# Usage: build_all.sh [names...]   (default: every line of civ_heights.txt)
HERE=$(cd "$(dirname "$0")" && pwd); D=/mnt/user-data/uploads/Downloads; WS=/tmp/claude-0/ws/civ; P=/tmp/claude-0/ws/mix/packs
cd /tmp
NAMES="$*"; [ -z "$NAMES" ] && NAMES=$(awk '{print $1}' "$HERE/civ_heights.txt")
for n in $NAMES; do
  h=$(awk -v n=$n '$1==n{print $2}' "$HERE/civ_heights.txt")
  f=$D/${n}_nonPBR.fbx; [ -f "$f" ] || f=$D/$n.fbx
  echo "== $n height $h"
  nice -n 10 python3 "$HERE/build_civ.py" --fbx "$f" --name $n --height $h --out $WS/$n.blend 2>&1 | grep -E "^(dropped|height|materials|HAIR|saved)|Error|assert" | tee $WS/$n.build.log
  rm -rf $WS/test_$n
  nice -n 10 python3 /home/claude/claude/tools/oxce-4x/build/sprites/render_char.py --blend $WS/$n.blend --clips "stand=$P/idle.fbx" --frames 1 --dirs 5,3 --out $WS/test_$n 2>&1 | grep -E "done|Error" 
done
echo ALLDONE
