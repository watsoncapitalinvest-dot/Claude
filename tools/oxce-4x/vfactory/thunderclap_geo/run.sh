# Thunderclap world-map pictures (John 17 Nov 19:05): the three hitched, one model, from the battle units' own blends + the kit.
# Inputs are private (blends, kit STLs); outputs go to mod/Resources/VehiclesPrivate/thunderclap_geo/ (gitignored).
set -e; H=$(cd "$(dirname "$0")" && pwd); TC=${TC:-/home/claude/tc}; O=${O:-$TC/geo/out}; B=$TC/geo/combo.blend
python3 $H/build_combo.py $TC/w/d_tractor.blend $TC/w/d_trailer.blend $TC/kit/files $B
cd /tmp
for pair in "0 1" "2 3" "4 5" "6 7"; do for k in $pair; do mkdir -p $O/h$k; SHADE=detail FOOT=5 python3 -I $H/render_geo.py $B $O/h$k m0 clean $k 0.005763 & done; wait; done
mkdir -p $O/t6 $O/s6 $O/side
ELEV=90 SHADE=detail FRAME=1024,1024,512,512 python3 -I $H/render_geo.py $B $O/t6 top clean 6 0.01306
ELEV=90 SHADE=detail FRAME=640,640,320,320 python3 -I $H/render_geo.py $B $O/s6 strip clean 6 0.0076
ELEV=0 SHADE=detail FRAME=1024,384,512,330 python3 -I $H/render_geo.py $B $O/side side clean 1 0.01250
