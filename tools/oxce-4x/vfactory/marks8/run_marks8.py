"""drive project_marks.py for every craft with John's marks: click px from the package's damaged heading-E picture (+ stopped rotor,
as the sheets and the click pages drew it), the craft's cfg (scale, foot frame, state hide list) -> marks8/<name>.json"""
import json, os, subprocess, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); V5 = '/home/claude/rt/v5'
POINTS = json.load(open(os.path.join(HERE, '..', 'blast_points.json')))
CRAFT = {   # sheet name: (package dir, cfg, state)
 'night_raven': ('/home/claude/rt/veh/pkg/night_raven_airsea', 'nraven/cfg_airsea.json', 'm0'),
 'condor': ('/home/claude/rt/veh/pkg/condor_z25_airsea', 'condor/cfg_airsea.json', 'm0'),
 'stellar_stiletto': ('/home/claude/rt/veh/pkg/stellar_stiletto_airsea', 'stiletto/cfg_airsea.json', 'm0'),
 'rattler': ('/home/claude/rt/veh/pkg/rattler_airsea', 'rattler/cfg_airsea.json', 'm0'),
 'firebat': ('/home/claude/rt/veh/pkg/firebat_airsea', 'firebat/cfg_airsea.json', 'm0'),
 'vulture': ('/home/claude/rt/veh/pkg/vulture_airsea', 'vulture/cfg_airsea.json', 'm0'),
 'hurricane_vtol': ('/home/claude/rt/veh/pkg/hurricane_vtol_flight_airsea', 'hurricane/cfg_flight_airsea.json', 'm0'),
 'mudfighter': ('/tmp/boats/mudfighter_airsea', 'mud/cfg_airsea.json', 'm0'),
 'float_plane': ('/home/claude/rt/veh/pkg/float_plane_airsea', 'floatplane/cfg_airsea.json', 'm0'),
 'sea_rattler': ('/home/claude/rt/veh/pkg/sea_rattler_airsea', 'searattler/cfg_airsea.json', 'm0'),
 'mamba': ('/home/claude/rt/veh/pkg/mamba_airsea', 'mamba/cfg_airsea.json', 'm0'),
 'devilfish': ('/tmp/boats/devilfish_airsea', 'devilfish/cfg_airsea.json', 'm0'),
 'sharc': ('/tmp/boats/s_h_a_r_c_airsea', 'sharc/cfg_airsea.json', 'm0'),
 'moray': ('/tmp/boats/moray_airsea', 'moray/cfg_airsea.json', 'm0'),
 'barracuda': ('/home/claude/rt/veh/pkg/barracuda_airsea', 'barracuda/cfg_airsea.json', 'm0'),
 'piranha': ('/home/claude/rt/veh/pkg/piranha_airsea', 'piranha/cfg_airsea.json', 'm0'),
 'night_landing': ('/home/claude/rt/veh/pkg/night_landing_airsea', 'nightlanding/cfg_cobra_airsea.json', 'm0'),
 'srv9': ('/home/claude/rt/veh/pkg/srv9_airsea', 'srv9/cfg_airsea.json', 'm0'),
 'killer_whale': ('/home/claude/rt/veh/pkg/killer_whale_airsea', 'whale/cfg_airsea.json', 'm0'),
 'night_landing_joe': ('/home/claude/rt/veh/pkg/night_landing_joe_airsea', 'nightlanding/cfg_joe_airsea.json', 'm0'),
 'sea_sled': ('/tmp/boats/sea_sled', 'seasled/cfg.json', 'm0'),
 'swamp_skier': ('/home/claude/rt/veh/pkg/swamp_skier_airsea', 'swampskier/cfg_airsea.json', 'm0'),
}
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
only = sys.argv[1:]
for name, (root, cfgp, st) in CRAFT.items():
    if only and name not in only: continue
    auto = name not in POINTS
    man = json.load(open(os.path.join(root, 'manifest.json'))); cfg = json.load(open(os.path.join(V5, cfgp)))
    e = next(x for x in man['frames'] if x['look'] == 'damaged' and x['heading'] == 'E' and x.get('state', st) == st)
    pic = Image.open(os.path.join(root, e['file'])).convert('RGBA')
    ang = sorted([x for x in (man.get('spin') or []) if x['heading'] == 'E' and x.get('angle_deg') is not None], key=lambda x: x['angle_deg'])
    if ang: pic.alpha_composite(Image.open(os.path.join(root, ang[0]['file'])).convert('RGBA'))
    bb = pic.getbbox()
    clicks = {'auto': True} if auto else [[bb[0] + p[0] * (bb[2] - bb[0]), bb[1] + p[1] * (bb[3] - bb[1]), p[2]] for p in POINTS[name]]
    jin = f'/tmp/marks8_{name}_in.json'; json.dump(clicks, open(jin, 'w'))
    blend = next(os.path.join(root, f) for f in os.listdir(root) if f.endswith('_source.blend'))
    hide = cfg['states'].get(st, [])
    r = subprocess.run(['python3', '-I', os.path.join(HERE, 'project_marks.py'), blend, str(cfg['scale']), str(cfg['foot_frame']), ','.join(hide), jin,
                        os.path.join(HERE, 'out', f'{name}.json')], capture_output=True, text=True)
    line = [l for l in r.stdout.splitlines() if l.startswith('MARKS8')]
    print(name, 'frame', pic.size, 'anchor', man['anchor'], line[0].split(' ', 2)[2] if line else 'FAILED ' + r.stderr[-400:])
