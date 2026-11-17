set -e
V=$1; C=/home/claude/rt/v5/classes/cfg_$V.json; P=/home/claude/rt/veh/pkg/$V
T=$(python3 -c "import json; print(1 if 'turret' in json.load(open('$C')) else 0)")
SC=$(python3 -c "import json; print(json.load(open('$C'))['scale'])"); FT=$(python3 -c "import json; print(json.load(open('$C'))['foot_frame'])")
cd /tmp && python3 -I /home/claude/rt/gen/render.py $C | tail -1
[ $T = 1 ] && python3 -I /home/claude/rt/gen/turret.py $C | tail -1
rm -rf $P; mkdir -p $P && echo '{}' > $P/manifest.json
if [ $V = vamp_mk2 ]; then cd /home/claude/rt/veh && SHADE=detail LEVEL=1 python3 /home/claude/rt/vamp2/full_launch.py $V /home/claude/vb/vamp_mk2/vamp_mk2/vamp_mk2_clean.blend rocket_fly $SC $FT $P whole 0,0,0 -4.46,3.0,11.25 | tail -1; fi
if [ $V = stinger ]; then cd /home/claude/rt/veh && SHADE=detail LEVEL=1 python3 /home/claude/rt/vamp2/full_launch.py $V /home/claude/vb/stinger_v2/stinger_v2/stinger_v2_clean.blend rocket_fly $SC $FT $P whole 0,0,0 -1.658,3.665,13.611 | tail -1; fi
if [ $V = triple_t ]; then cd /home/claude/rt/veh && SHADE=detail LEVEL=1 python3 /home/claude/rt/vamp2/full_launch.py $V /home/claude/vb/triple_t/triple_t/triple_t_clean.blend missile_R $SC $FT $P whole 0,0,0 5.5,-8.9,10.78 | tail -1; fi
cd /tmp && python3 -I /home/claude/rt/gen/pkg.py $C | tail -1
[ $T = 1 ] && python3 -I /home/claude/rt/gen/turret_pkg.py $C | tail -c 120
python3 -I /home/claude/rt/gen/preview.py $C && python3 -I /home/claude/rt/gen/turntable.py $P $V 0 $P/${V}_turntable.gif 1.2
echo DONE_$V
