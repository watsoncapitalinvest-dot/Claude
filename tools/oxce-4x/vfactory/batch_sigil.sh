#!/bin/bash
# name|cfg|images|fixes
cd /home/claude/vf
while IFS='|' read -r n c i f; do
  [ -z "$n" ] && continue
  echo "START $n $(date +%T)"
  python3 -I reskin.py /home/claude/pk/old/$n/$n /home/claude/rt/v5/$c /home/claude/work/$n /home/claude/pk/new/$n/$n "$i" "$f" private/sigil_mask.png 2>&1 | grep -E "REPORT|Error|assert|Traceback|swap|failed" | tail -3
done <<'LIST'
rattler|rattler/cfg.json|rt_diamond.png|col_rt_glass.png=96,106,122
rattler_airsea|rattler/cfg_airsea.json|rt_diamond.png|col_rt_glass.png=96,106,122
night_raven|nraven/cfg.json|nr_diamond.png,nr_fin.png|col_nr_glass.png=150,32,40
night_raven_airsea|nraven/cfg_airsea.json|nr_diamond.png,nr_fin.png|col_nr_glass.png=150,32,40
condor_z25|condor/cfg.json|cd_diamond.png|col_cd_glass.png=158,176,196
condor_z25_airsea|condor/cfg_airsea.json|cd_diamond.png|col_cd_glass.png=158,176,196
firebat|firebat/cfg.json|fb_diamond.png|
firebat_airsea|firebat/cfg_airsea.json|fb_diamond.png|
stellar_stiletto|stiletto/cfg.json|st_diamond.png|col_st_glass.png=104,114,130
stellar_stiletto_airsea|stiletto/cfg_airsea.json|st_diamond.png|col_st_glass.png=104,114,130
vulture|vulture/cfg.json|vu_diamond.png|
vulture_airsea|vulture/cfg_airsea.json|vu_diamond.png|
sea_rattler|searattler/cfg.json|sr_diamond.png|col_sr_glass.png=40,46,56
float_plane|floatplane/cfg.json|fp_diamond.png|col_fp_glass.png=40,52,64
air_chariot|chariot/cfg.json|ac_diamond.png|
flight_pod|fpod/cfg.json|fp_diamond.png|col_fp_glass.png=178,210,230
moray|moray/cfg.json|mr_diamond.png|col_mr_glass_dark.png=30,60,80
moray_airsea|moray/cfg_airsea.json|mr_diamond.png|col_mr_glass_dark.png=30,60,80
hurricane_vtol|hurricane/cfg.json|hu_diamond.png|col_hu_glass.png=62,54,48
hurricane_vtol_flight_airsea|hurricane/cfg_flight_airsea.json|hu_diamond.png|col_hu_glass.png=62,54,48
LIST
echo ALL_DONE $(date +%T)
