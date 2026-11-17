# Thunder Machine rework: build -> markings -> (damaged) hit stickers on top. Private blends in /home/claude/vb.
set -e
H=$(cd "$(dirname "$0")" && pwd); S=/home/claude/vb/thunder_machine/thunder_machine; D=/home/claude/vb/thunder_machine_v2/thunder_machine_v2; mkdir -p $D
for L in clean damaged; do
  python3 -I $H/build_tm.py $S/thunder_machine_$L.blend $D/thunder_machine_v2_$L.blend | grep -E "BUILT|GUN|NAVY"
  (cd /home/claude/rt/veh && python3 -I damage_generic.py $D/thunder_machine_v2_$L.blend /home/claude/rt/veh/tm_decals $H/decals.json $D/thunder_machine_v2_$L.blend | grep -cE " on ")
done
for L in clean damaged; do python3 -I $H/hits_on_top.py $D/thunder_machine_v2_$L.blend | grep LIFTED; done
