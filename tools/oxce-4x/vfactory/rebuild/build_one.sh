#!/bin/bash
# VFACTORY 18 Nov: rebuild one ROSTER craft from John's Thingiverse download (ROSTER's finished blends were not kept here),
# then render its ONE-NOTCH-UP air/sea package. usage: build_one.sh <v5 dir> <src dir> <zip> <cfg file> [PAINT]
set -e
V=$1; SRC=$2; Z=$3; CF=${4:-cfg.json}; export PAINT=${5:-cobra}
R=/home/claude/rt; D=$R/v5/$V; C=$D/$CF
X=$(python3 -c "import json;print(json.load(open('$C'))['blends']['clean'].rsplit('/',1)[0])")
if [ -n "$BASE" ]; then mkdir -p $X; cp "$BASE" $X/base.blend; echo "$V base from the shipped package (decals included)"; else
mkdir -p $SRC/x && rm -rf $SRC/x/files && (cd $SRC/x && unzip -qo "$Z" 'files/*')
cd $D
python3 -I imp.py > /tmp/rb_$V.imp.log 2>&1
python3 -I asm.py $D/raw.blend $D/asm_$PAINT.blend > /tmp/rb_$V.asm.log 2>&1
B=$D/asm_$PAINT.blend
mkdir -p $X
if [ -f mkdecals.py ]; then mkdir -p decals; python3 -I mkdecals.py > /dev/null 2>&1 || true; fi
if [ -f marks.json ] && [ -d decals ] && python3 -c "
import json,os,sys; n={h[0] for h in json.load(open('marks.json'))['hits']}; sys.exit(0 if all(os.path.exists(f'decals/{k}.png') for k in n) else 1)"; then
  python3 -I $R/veh/damage_generic.py $B $D/decals $D/marks.json $X/base.blend > /tmp/rb_$V.marks.log 2>&1; echo "$V marks applied"
else cp $B $X/base.blend; echo "$V NO DECAL PICTURES - markings left off"; fi
fi
python3 -I $R/veh/damage_generic.py $X/base.blend $R/rebuild/dmgimg $D/dmg.json $X/damaged.blend > /tmp/rb_$V.dmg.log 2>&1
echo "$V model rebuilt -> $X ($(grep -c MISS /tmp/rb_$V.dmg.log || true) damage misses)"
# air/sea config + render
cd $R/gen
S=$(ls ${V}.sh 2>/dev/null || true)
python3 -I make_airsea.py $V /dev/null $CF > /tmp/rb_$V.mk.log
C2=$D/${CF%.json}_airsea.json
cd /tmp && python3 -I $R/gen/render.py $C2 | tail -1; FILL=1 python3 -I $R/gen/render.py $C2 | tail -1
N=$(python3 -c "import json;print(json.load(open('$C2'))['name'])")
rm -rf $R/veh/pkg/$N; mkdir -p $R/veh/pkg/$N && echo '{}' > $R/veh/pkg/$N/manifest.json
python3 -I $R/gen/pkg.py $C2 | tail -1; python3 -I $R/gen/preview.py $C2 | tail -1
cp $X/base.blend $R/veh/pkg/$N/${N}_source.blend
echo "BUILT $N"
