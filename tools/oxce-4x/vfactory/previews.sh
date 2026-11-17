#!/bin/bash
# rebuild preview + turntable for re-issued packages with ROSTER's own scripts
cd /tmp
while IFS='|' read -r n c i f; do
  [ -z "$n" ] && continue; P=/home/claude/pk/new/$n/$n
  ln -sfn $P /home/claude/rt/veh/pkg/$n
  t=$(date +%s)
  if ls $P/*_preview.gif >/dev/null 2>&1; then timeout 900 python3 -I /home/claude/rt/gen/preview.py /home/claude/rt/v5/$c > /home/claude/work/prev_$n.log 2>&1 || echo "PREVIEW_FAIL $n"; fi
  echo "PREV $n $(( $(date +%s) - t ))s"
done < <(sed -n '/<<.LIST./,/^LIST/p' /home/claude/vf/batch_sigil.sh | grep '|')
echo PREV_DONE
