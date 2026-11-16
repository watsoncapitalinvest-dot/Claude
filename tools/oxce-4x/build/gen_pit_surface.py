"""The Pit attack starts on the SURFACE (John 15 Nov 21:51, "go" 16 Nov 09:32; PIT_FALLS_DESIGN_v1 s.1).

Reads MAPS' pitsurf_v2.zip unpacked (none\\, hidden\\, open\\ with PITSURF_spots.json) and writes:
  MAPS/PITSURF.MAP2   the surface with nothing installed (padded to a multiple of 10)
  MAPS/PITSURFO.MAP2  the same with every defence deployed: the library the engine copies installed spots from
  ROUTES/PITSURF.RMP  MAPS' nodes (12 Joe, 8 Cobra on the road ends and edges, 12 civilians)
  TERRAIN/            CHAPEL and PDEF (private: John's downloads and Generals-mod models), PHATCH
  Ruleset/gijoe_pit_surface_battle.rul
Engine: BattlescapeGenerator plays a Pit base defence as STR_PIT_SURFACE first; falling back down a way down
(an END_POINT tile: every PHATCH part) is the abort that takes the survivors - both sides - to STR_PIT_DEFENSE.

usage: python3 build/gen_pit_surface.py <unpacked pitsurf_v2 folder>
"""
import json, os, shutil, struct, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.join(HERE, '..', 'mod')
PRIVATE_SETS = ('CHAPEL', 'PDEF', 'PHATCH')
ESCAPE = [(44, 8), (44, 7), (43, 8)]     # the Pit's escape tunnel off Utility (gen_pit_canon.py), z 0


def load(p):
    d = open(p, 'rb').read()
    Y, X, Z = d[0], d[1], d[2]
    return X, Y, Z, list(struct.unpack('<%dH' % ((len(d) - 3) // 2), d[3:]))


def pad(src, dst):
    X, Y, Z, v = load(src)
    PX, PY = -(-X // 10) * 10, -(-Y // 10) * 10
    out = []
    for L in range(Z):
        for y in range(PY):
            for x in range(PX):
                out += [v[((L * Y + y) * X + x) * 4 + k] for k in range(4)] if (x < X and y < Y) else [0, 0, 0, 0]
    with open(dst, 'wb') as f:
        f.write(bytes([PY, PX, Z]) + struct.pack('<%dH' % len(out), *out))
    return PX, PY, Z


def main(root):
    none, opn = os.path.join(root, 'none'), os.path.join(root, 'open')
    sets_none = json.load(open(os.path.join(none, 'PITSURF_terrain.json')))['mapDataSets']
    sets_open = json.load(open(os.path.join(opn, 'PITSURF_terrain.json')))['mapDataSets']
    assert sets_open[:len(sets_none)] == sets_none, 'open must extend none'
    PX, PY, Z = pad(os.path.join(none, 'MAPS', 'PITSURF.MAP2'), os.path.join(MOD, 'MAPS', 'PITSURF.MAP2'))
    pad(os.path.join(opn, 'MAPS', 'PITSURF.MAP2'), os.path.join(MOD, 'MAPS', 'PITSURFO.MAP2'))
    shutil.copy(os.path.join(none, 'ROUTES', 'PITSURF.RMP'), os.path.join(MOD, 'ROUTES', 'PITSURF.RMP'))
    for d in (none, opn):
        for f in os.listdir(os.path.join(d, 'TERRAIN')):
            dst = os.path.join(MOD, 'TERRAIN', f)
            same = os.path.exists(dst) and open(dst, 'rb').read() == open(os.path.join(d, 'TERRAIN', f), 'rb').read()
            if same:
                continue
            if f.split('.')[0].split('_')[0] not in PRIVATE_SETS and os.path.exists(dst):
                raise SystemExit('refusing to overwrite a terrain file another map uses: ' + f)
            shutil.copy(os.path.join(d, 'TERRAIN', f), dst)
    sj = json.load(open(os.path.join(opn, 'PITSURF_spots.json')))
    spots = {}
    for k, s in sj['spots'].items():
        cells = set()
        for key in ('floor_tiles', 'roof_hatch', 'tank', 'poles'):
            for c in s.get(key, []):
                cells.add((c[0], c[1]))
        spots[k] = [list(c) for c in sorted(cells)]
    kit = yaml.safe_load(open(os.path.join(MOD, 'Ruleset', 'gijoe_cobra_kit.rul')))
    base = next(d for d in kit['alienDeployments'] if d['type'] == 'STR_BASE_DEFENSE')
    phatch = os.path.getsize(os.path.join(MOD, 'TERRAIN', 'PHATCH.MCD')) // 62
    rul = {
        'terrains': [{'name': 'PITSURF_T', 'mapDataSets': sets_open,
                      'mapBlocks': [{'name': 'PITSURF', 'width': PX, 'length': PY, 'height': Z}]}],
        'mapScripts': [{'type': 'PITSURF_SCRIPT', 'commands': [{'type': 'addBlock', 'size': [PX // 10, PY // 10]}]}],
        'alienDeployments': [{'type': 'STR_PIT_SURFACE', 'data': base['data'],
                              'width': PX, 'length': PY, 'height': Z, 'civilians': 8,
                              'terrains': ['PITSURF_T'], 'script': 'PITSURF_SCRIPT', 'shade': 0,
                              'nextStage': 'STR_PIT_DEFENSE',
                              'briefing': {'palette': 0, 'title': 'STR_PIT_SURFACE_TITLE', 'desc': 'STR_PIT_SURFACE_BRIEFING'}}],
        # every way down (the elevator, both vehicle lifts, the heavy elevator, the stairwell, both escape hatches,
        # the vent) is an exit: a Joe standing on one when you abort falls back below
        'MCDPatches': [{'type': 'PHATCH', 'data': [{'MCDIndex': i, 'specialType': 13} for i in range(phatch)]}],
        'pitSurfaceBattle': {'deployment': 'STR_PIT_SURFACE', 'library': 'PITSURFO', 'spots': spots,
                             'leakNeeds': 'STR_COBRA_PIT_ESCAPE_TUNNEL', 'leakTeam': 3, 'escape': [[x, y, 0] for (x, y) in ESCAPE]},
        'extraStrings': [{'type': 'en-US', 'strings': {
            'STR_PIT_SURFACE': 'The Pit (surface)',
            'STR_PIT_SURFACE_TITLE': 'COBRA IS AT THE GATE',
            'STR_PIT_SURFACE_BRIEFING': "Cobra has landed on the motor pool. They don't know what is under it - yet.{NEWLINE}"
                                        "Hold the surface and the attack is beaten. If it goes badly, get your Joes onto a way down "
                                        "(the elevator, the vehicle lifts, the heavy elevator, the stairwell, the hatches) and ABORT: "
                                        "they fall back below, and whatever Cobra has left comes down after them.",
            'STR_PIT_DEFENSE_FOLLOWED': 'Cobra is in the Pit',
            'STR_PIT_FALL_BACK': 'FALL BACK BELOW?',
            'STR_PIT_UNITS_ON_WAYS_DOWN': 'On a way down (they go): {0}',
            'STR_PIT_UNITS_LEFT_BEHIND': 'Left on the surface (lost): {0}',
        }}],
    }
    hdr = ('# GENERATED by build/gen_pit_surface.py from MAPS\' pitsurf_v2.zip: do not edit by hand.\n'
           '# The Pit attack starts on the surface (PIT_FALLS_DESIGN_v1 s.1; John 15 Nov 21:51, go 16 Nov 09:32).\n'
           '# The maps are private (traced off Broca; John\'s models): gitignored, zip only.\n')
    with open(os.path.join(MOD, 'Ruleset', 'gijoe_pit_surface_battle.rul'), 'w') as f:
        f.write(hdr + yaml.safe_dump(rul, sort_keys=False, width=140))
    print('PITSURF %dx%dx%d; %d spots; PHATCH %d parts are exits' % (PX, PY, Z, len(spots), phatch))


if __name__ == '__main__':
    main(sys.argv[1])
