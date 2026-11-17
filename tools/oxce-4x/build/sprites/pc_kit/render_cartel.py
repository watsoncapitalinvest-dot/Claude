# CARTEL RENDER ON JOHN'S PC (17 Nov 2026). Renders the nine cartel men in Reference\cartel onto walk16 sheets
# (2048x8960, 896 frames) with the same render_char.py + assemble_sheet.py the cloud desks use, then the extra clips
# (the runs and the held spell) as plain frame strips. Run from RENDER_CARTEL.bat, or:
#   python render_cartel.py --watch    THE MACHINE: drop models in, sheets come out (RENDER_MACHINE.bat)
#   python render_cartel.py [name ...] [--civ] [--no-extras] [--extras-only]
#   no names = every .blend in Reference\cartel (armed); --civ = every .blend in Reference\civ (unarmed)
import os, sys, glob, json, time, shutil, zipfile, subprocess

KIT = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('KIT_BASE', r'C:\GI-Joe-Silent-Storm\GIJoe_XCOM_4x')
DOWN = os.environ.get('KIT_DOWNLOADS', os.path.join(os.path.expanduser('~'), 'Downloads'))
CARTEL = os.path.join(BASE, 'Reference', 'cartel')            # the nine .blend + clips_17nov.blend
CIV = os.path.join(BASE, 'Reference', 'civ')                   # civilian .blend files (unarmed: plain standing idle)
UNITS = os.path.join(BASE, 'XCom UFO Defense', 'XCOM', 'UNITS')
WORK = os.path.join(BASE, 'render_work')                         # frames, logs; safe to delete afterwards
OUT = os.path.join(BASE, 'Reference', 'sheets', 'cartel')      # finished sheets land here (armed)
OUT_CIV = os.path.join(BASE, 'Reference', 'sheets', 'civ')     # and here (civilians)
SPRITES = os.path.join(KIT, 'build', 'sprites')

# hair colour of the civilian body each man is built on (civ_hair.txt) - the assembler's outline uses it
HAIR = {'cartel_foot_a': '16,18,22', 'cartel_foot_b': '50,35,32', 'cartel_foot_c': '166,126,93',
        'cartel_heavy_a': '166,126,93', 'cartel_heavy_b': '16,18,22', 'cartel_heavy_c': '48,46,39',
        'cartel_boss_a': '16,15,14', 'cartel_boss_b': '48,46,39', 'cartel_boss_c': '16,15,14',
        # civilians (build/sprites/civ/civ_hair.txt); a name not listed gets no hair tone, which only softens one outline
        'Ch02': '163,141,100', 'Ch06': '', 'Ch07': '24,17,9', 'Ch08': '35,26,21', 'Ch12': '48,46,39', 'Ch13': '106,81,55',
        'Ch20': '', 'Ch21': '154,130,104', 'Ch23': '16,15,14', 'Ch28': '16,18,22', 'Ch42': '50,35,32', 'Remy': '166,126,93'}
PACKS = ['Basic Shooter Pack', 'Pistol_Handgun Locomotion Pack', 'Rifle 8-Way Locomotion Pack', 'Action Adventure Pack']
EXTRAS = os.environ['KIT_EXTRAS'].split(',') if os.environ.get('KIT_EXTRAS') else ['cast_spell_hold', 'run', 'run_b', 'run_forward', 'fast_run', 'pistol_run', 'injured_run', 'run_up_stairs',
          'walk_up_stairs', 'walk_down_stairs']


def log(*a):
    line = time.strftime('%H:%M:%S ') + ' '.join(str(x) for x in a)
    print(line, flush=True)
    with open(os.path.join(WORK, 'render_log.txt'), 'a') as f: f.write(line + '\n')


def find_renderer():
    """The command that runs render_char.py: this Python when it has the bpy module (the PC was set up with
    py -3.13 + bpy 5.3.0 on 17 Nov), else a Blender install."""
    try:
        import bpy  # noqa: F401
        return [sys.executable]
    except ImportError:
        pass
    if os.environ.get('BLENDER') and os.path.exists(os.environ['BLENDER']): return [os.environ['BLENDER'], '-b', '--factory-startup', '--python']
    c = sorted(glob.glob(r'C:\Program Files\Blender Foundation\Blender*\blender.exe'))
    return [c[-1], '-b', '--factory-startup', '--python'] if c else None


def rc_cmd(R, rc, args):
    return R + [rc] + (['--'] if len(R) > 1 else []) + args


def unpack():
    root = os.path.join(WORK, 'packs16')
    for p in PACKS:
        d = os.path.join(root, p)
        if os.path.isdir(d) and os.listdir(d): continue
        z = os.path.join(DOWN, p + '.zip')
        if not os.path.exists(z): sys.exit('MISSING: %s (needed for the walks/stills)' % z)
        os.makedirs(d, exist_ok=True); zipfile.ZipFile(z).extractall(d); log('unpacked', p)
    idx = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f.lower().endswith('.fbx'): idx.setdefault((os.path.basename(dp) if dp != root else '', f.lower()), os.path.join(dp, f))
    def clip(pack, name):
        for dp, _, fs in os.walk(os.path.join(root, pack)):
            for f in fs:
                if f.lower() == name.lower(): return os.path.join(dp, f)
        sys.exit('MISSING clip %s in %s' % (name, pack))
    walks = {'walk': clip('Basic Shooter Pack', 'walking.fbx'), 'pwalk': clip('Pistol_Handgun Locomotion Pack', 'pistol walk.fbx'),
             'swalk': clip('Rifle 8-Way Locomotion Pack', 'walk crouching forward.fbx'), 'ewalk': clip('Action Adventure Pack', 'walking.fbx')}
    stills = {'stand': clip('Rifle 8-Way Locomotion Pack', 'idle.fbx'), 'kneel': clip('Rifle 8-Way Locomotion Pack', 'idle crouching.fbx'),
              'aim': clip('Rifle 8-Way Locomotion Pack', 'idle aiming.fbx'), 'death': clip('Rifle 8-Way Locomotion Pack', 'death from the front.fbx'),
              'pstand': clip('Pistol_Handgun Locomotion Pack', 'pistol idle.fbx'), 'pkneel': clip('Pistol_Handgun Locomotion Pack', 'pistol kneeling idle.fbx')}
    return stills, walks


def where(n):
    for d, civ in ((CARTEL, False), (CIV, True)):
        p = os.path.join(d, n + '.blend')
        if os.path.exists(p): return p, civ
    return None, False


def civ_stills(stills):
    # a civilian holds nothing: every still is the plain Standing Idle (as the civilian sheets were made); death stays
    idle = os.path.join(DOWN, 'Standing Idle.fbx')
    if not os.path.exists(idle): sys.exit('MISSING: %s (the civilians\' standing pose)' % idle)
    return {k: (v if k == 'death' else idle) for k, v in stills.items()}


def run(cmd, logfile, env=None):
    with open(logfile, 'w') as f:
        return subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)


def check(name):
    import numpy as np
    from PIL import Image
    im = Image.open(os.path.join(WORK, 'sheets16', name + '_body.png')); a = np.array(im.convert('RGBA'))
    anc = [l for l in open(os.path.join(WORK, 'sheets16', name + '_body_anchors.txt')) if l.strip()]
    empty = 0
    for i in range(896):
        r, c = divmod(i, 16)
        if a[r * 160:(r + 1) * 160, c * 128:(c + 1) * 128, 3].max() == 0: empty += 1
    ok = im.size == (2048, 8960) and len(anc) == 896 and empty == 0
    return ok, '%dx%d, %d anchors, %d empty frames' % (im.size[0], im.size[1], len(anc), empty)


def sheet(R, n, blend, civ, stills, walks, outdir):
    rc = os.path.join(SPRITES, 'render_char.py'); asm = os.path.join(SPRITES, 'assemble_sheet.py')
    t0 = time.time(); log('==', n, 'start', '(unarmed)' if civ else '(armed)')
    fr = os.path.join(WORK, 'fr16_' + n); shutil.rmtree(fr, ignore_errors=True)
    st = civ_stills(stills) if civ else stills
    clips = ','.join('%s=%s' % kv for kv in list(st.items()) + list(walks.items()))
    c = run(rc_cmd(R, rc, ['--blend', blend, '--clips', clips, '--frames', '8',
                           '--clipframes', 'walk=16,pwalk=16,swalk=16,ewalk=16', '--out', fr]),
            os.path.join(WORK, n + '.render.log'))
    if c: log('RENDER FAILED', n, '- see', n + '.render.log'); return False
    env = dict(os.environ, W16='1', HAIR=HAIR.get(n, ''), FOLD_IDS='', XCOM_UNITS=UNITS)
    c = run([sys.executable, asm, fr, os.path.join(WORK, 'sheets16'), n], os.path.join(WORK, n + '.assemble.log'), env)
    if c: log('ASSEMBLE FAILED', n, '- see', n + '.assemble.log'); return False
    ok, why = check(n)
    os.makedirs(outdir, exist_ok=True)
    for suf in ('_body.png', '_body_rgb.png', '_body_anchors.txt'):
        shutil.copy(os.path.join(WORK, 'sheets16', n + suf), outdir)
    shutil.rmtree(fr, ignore_errors=True)
    log('done' if ok else 'CHECK FAILED', n, why, '%.1f min' % ((time.time() - t0) / 60))
    return ok


def extras(R, n, blend, outdir):
    rc = os.path.join(SPRITES, 'render_char.py')
    lib = os.path.join(CARTEL, 'clips_17nov.blend')   # the extra clips are read from here for every man, civilians too
    if not os.path.exists(lib): log('no clips_17nov.blend in', CARTEL, '- extras skipped'); return False
    t0 = time.time(); fr = os.path.join(WORK, 'extras_' + n); shutil.rmtree(fr, ignore_errors=True)
    clips = ','.join('%s=%s#%s' % (e, lib, e) for e in EXTRAS)
    c = run(rc_cmd(R, rc, ['--blend', blend, '--clips', clips, '--frames', '16', '--out', fr]),
            os.path.join(WORK, n + '.extras.log'))
    if c: log('EXTRAS FAILED', n, '- see', n + '.extras.log'); return False
    strips(n, fr, outdir); shutil.rmtree(fr, ignore_errors=True)
    log('extras', n, '%.1f min' % ((time.time() - t0) / 60))
    return True


def models(folder):
    if not os.path.isdir(folder): return []
    return sorted(os.path.splitext(f)[0] for f in os.listdir(folder)
                  if f.lower().endswith('.blend') and not f.lower().startswith('clips_'))


def setup():
    os.makedirs(WORK, exist_ok=True); os.makedirs(os.path.join(WORK, 'sheets16'), exist_ok=True)
    os.makedirs(CIV, exist_ok=True); os.makedirs(CARTEL, exist_ok=True)
    R = find_renderer()
    if not R: sys.exit('No renderer: run this with py -3.13 (bpy installed by SETUP_v3.bat), or install Blender 5.x.')
    log('renderer:', ' '.join(R))
    stills, walks = unpack()
    return R, stills, walks


def main():
    if '--watch' in sys.argv: return machine()
    R, stills, walks = setup()
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    # no names: every model in the folder - Reference/cartel (armed) by default, Reference/civ (unarmed) with --civ
    names = args or models(CIV if '--civ' in sys.argv else CARTEL)
    log('men:', ' '.join(names))
    for n in names:
        blend, civ = where(n)
        if not blend: log('NO BLEND for', n, '- put', n + '.blend in', CARTEL, 'or', CIV); continue
        outdir = OUT_CIV if civ else OUT
        if '--extras-only' not in sys.argv: sheet(R, n, blend, civ, stills, walks, outdir)
        if '--no-extras' not in sys.argv: extras(R, n, blend, outdir)


def machine():
    r"""THE MACHINE: watch Reference\cartel (armed) and Reference\civ (unarmed). Any model with no finished sheet,
    or changed since its sheet was made, is rendered, checked, filed and given its extra clips. Runs until closed."""
    R, stills, walks = setup()
    state_p = os.path.join(WORK, 'machine_state.json')
    state = json.load(open(state_p)) if os.path.exists(state_p) else {}
    log('MACHINE ON - drop .blend files in', CARTEL, '(armed) or', CIV, '(unarmed). Close this window to stop.')
    idle = False
    while True:
        todo = []
        for folder, civ in ((CARTEL, False), (CIV, True)):
            for n in models(folder):
                blend = os.path.join(folder, n + '.blend'); key = blend.lower()
                m = os.path.getmtime(blend)
                if state.get(key, {}).get('mtime') == m: continue
                if time.time() - m < 10: continue          # still being copied in
                todo.append((n, blend, civ, key, m))
        status(todo, state)
        if not todo:
            if not idle: log('machine: nothing to do - waiting for new models'); idle = True
            time.sleep(20); continue
        idle = False
        n, blend, civ, key, m = todo[0]
        outdir = OUT_CIV if civ else OUT
        ok = sheet(R, n, blend, civ, stills, walks, outdir)
        ex = extras(R, n, blend, outdir) if ok else False
        state[key] = {'mtime': m, 'name': n, 'ok': ok, 'extras': ex, 'when': time.strftime('%Y-%m-%d %H:%M')}
        json.dump(state, open(state_p, 'w'), indent=1)


def status(todo, state):
    lines = ['RENDER MACHINE  ' + time.strftime('%Y-%m-%d %H:%M:%S'), '',
             'Drop armed men (gun poses) in:     ' + CARTEL, 'Drop civilians (no gun) in:        ' + CIV,
             'Finished sheets:  ' + OUT + '  and  ' + OUT_CIV, '', 'QUEUE (%d):' % len(todo)]
    lines += ['  ' + t[0] + ('  (unarmed)' if t[2] else '  (armed)') for t in todo] or ['  empty']
    lines += ['', 'DONE:']
    for k, v in sorted(state.items(), key=lambda kv: kv[1].get('when', '')):
        lines.append('  %-22s %s  sheet %s  extras %s' % (v['name'], v['when'], 'OK' if v['ok'] else 'FAILED',
                                                          'OK' if v['extras'] else '-'))
    open(os.path.join(WORK, 'MACHINE_STATUS.txt'), 'w').write('\n'.join(lines) + '\n')


def strips(n, fr, outdir):
    # one PNG per clip: 8 facings (rows) x 16 frames, 128x160 cells, raw beauty frames (no outline / palette)
    from PIL import Image
    d = os.path.join(outdir, 'extras'); os.makedirs(d, exist_ok=True)
    for e in EXTRAS:
        sheet = Image.new('RGBA', (16 * 128, 8 * 160))
        for k in range(8):
            for i in range(16):
                p = os.path.join(fr, e, 'd%d_f%02d_beauty.png' % (k + 1, i))
                if os.path.exists(p):
                    sheet.paste(Image.open(p).convert('RGBA').resize((128, 160), Image.LANCZOS), (i * 128, k * 160))
        sheet.save(os.path.join(d, '%s_%s.png' % (n, e)))


if __name__ == '__main__':
    main()
