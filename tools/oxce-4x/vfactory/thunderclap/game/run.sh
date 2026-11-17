set -e
V=$1; C=/home/claude/rt/v5/thunderclap/cfg_$V.json; N=thunderclap_$V; P=/home/claude/rt/veh/pkg/$N; D=/home/claude/rt/veh/${N}_x
FLY=$2; TIP=$3; T=/home/claude/rt/v5/thunderclap
cp /home/claude/tc/w/d_$V.blend $D/base.blend
cd /home/claude/rt/veh && python3 -I damage_generic.py $D/base.blend ${DMG:-/home/claude/tc/dmg} /home/claude/tc/dmg_$V.json $D/damaged.blend | grep -cE " on "
cd /tmp && python3 -I /home/claude/rt/gen/render.py $C | tail -1 && python3 -I /home/claude/rt/gen/turret.py $C | tail -1
python3 -I $T/crisp_out.py out $C
rm -rf $P; mkdir -p $P && echo '{}' > $P/manifest.json
cd /home/claude/rt/veh && SHADE=detail LEVEL=1 python3 /home/claude/rt/vamp2/full_launch.py $N $D/base.blend $FLY 0.01266 3 $P whole 0,0,0 $TIP | tail -1
python3 -I $T/crisp_out.py pkg $P
cd /tmp && python3 -I /home/claude/rt/gen/pkg.py $C && python3 -I /home/claude/rt/gen/turret_pkg.py $C && python3 -I /home/claude/rt/gen/preview.py $C && python3 -I /home/claude/rt/gen/turntable.py $P $N 0 $P/${N}_turntable.gif 1.2
echo DONE_$V
