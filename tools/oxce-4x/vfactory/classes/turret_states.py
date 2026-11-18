"""Turret store states (John 17 Nov 20:21 "they dont disappear"): the turret rendered with the first k missiles gone, k = 1..N, 8 headings,
clean look, into the package as turret/<name>_turret_clean_s<k>_<heading>.png (same frame and pivot as the loaded turret).
Fire order = the cfg's store list order. The engine shows frame 8 + (fired - 1) * 8 + turret heading (VFACTORY hook in UnitSprite).
python3 turret_states.py cfg.json obj1,obj2,...   (objects removed one per shot, in firing order)"""
import json, sys, os, subprocess, shutil
from concurrent.futures import ThreadPoolExecutor
cfg = json.load(open(sys.argv[1])); ORDER = sys.argv[2].split(','); T = cfg['turret']; N = cfg['name']
R = '/home/claude/rt/ttt/tools/render_vehicle.py'; P = f'/home/claude/rt/veh/pkg/{N}'; W = cfg['out'] + '/turret_states'; H = ['N','NE','E','SE','S','SW','W','NW']
def job(a):
    k, h = a; d = f'{W}/s{k}_{h}'; os.makedirs(d, exist_ok=True)
    subprocess.run(['python3', '-I', R, cfg['blends']['clean'], d, 'turret', f'clean_s{k}', str(h), str(cfg['scale'])], capture_output=True,
                   env=dict(os.environ, SHADE='detail', FOOT=str(cfg['foot_frame']), PART='turret', TURRET=','.join(T['objs']),
                            TPIV=','.join(str(v) for v in T['pivot']), HIDE=','.join(['wrk_fly'] + ORDER[:k])))
    shutil.copy(f'{d}/turret_clean_s{k}_{H[h]}.png', f'{P}/turret/{N}_turret_clean_s{k}_{H[h]}.png')
with ThreadPoolExecutor(2) as ex: list(ex.map(job, [(k, h) for k in range(1, len(ORDER) + 1) for h in range(8)]))
m = json.load(open(f'{P}/manifest.json')); m['turret_store_states'] = {'count': len(ORDER), 'order': ORDER, 'file': f'turret/{N}_turret_clean_s<k>_<heading>.png'}
json.dump(m, open(f'{P}/manifest.json', 'w'), indent=1); print('TURRET STATES', len(ORDER) * 8)
