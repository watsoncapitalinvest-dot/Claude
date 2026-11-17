# CARTEL RENDER ON JOHN'S PC (17 Nov 2026). Renders the nine cartel men in Reference\cartel onto walk16 sheets
# (2048x8960, 896 frames) with the same render_char.py + assemble_sheet.py the cloud desks use, then the extra clips
# (the runs and the held spell) as plain frame strips. Run from RENDER_CARTEL.bat, or:
#   python render_cartel.py [name ...] [--no-extras] [--extras-only]
import os, sys, glob, json, time, shutil, zipfile, subprocess

KIT = os.path.dirname(os.path.abspath(__file__))
BASE = r'C:\GI-Joe-Silent-Storm\GIJoe_XCOM_4x'
DOWN = os.path.join(os.path.expanduser('~'), 'Downloads')
CARTEL = os.path.join(BASE, 'Reference', 'cartel')            # the nine .blend + clips_17nov.blend
UNITS = os.path.join(BASE, 'XCom UFO Defense', 'XCOM', 'UNITS')
WORK = os.path.join(BASE, 'render_work')                         # frames, logs; safe to delete afterwards
OUT = os.path.join(BASE, 'Reference', 'sheets', 'cartel')      # finished sheets land here
SPRITES = os.path.join(KIT, 'build', 'sprites')

# hair colour of the civilian body each man is built on (civ_hair.txt) - the assembler's outline uses it
HAIR = {'cartel_foot_a': '16,18,22', 'cartel_foot_b': '50,35,32', 'cartel_foot_c': '166,126,93',
        'cartel_heavy_a': '166,126,93', 'cartel_heavy_b': '16,18,22', 'cartel_heavy_c': '48,46,39',
        'cartel_boss_a': '16,15,14', 'cartel_boss_b': '48,46,39', 'cartel_boss_c': '16,15,14'}
PACKS = ['Basic Shooter Pack', 'Pistol_Handgun Locomotion Pack', 'Rifle 8-Way Locomotion Pack', 'Action Adventure Pack']
EXTRAS = ['cast_spell_hold', 'run', 'run_b', 'run_forward', 'fast_run', 'pistol_run', 'injured_run', 'run_up_stairs']


def log(*a):
    line = time.strftime('%H:%M:%S ') + ' '.join(str(x) for x in a)
    print(line, flush=True)
    with open(os.path.join(WORK, 'render_log.txt'), 'a') as f: f.write(line + '\n')


def find_blender():
    if os.environ.get('BLENDER') and os.path.exists(os.environ['BLENDER']): return os.environ['BLENDER']
    c = sorted(glob.glob(r'C:\Program Files\Blender Foundation\Blender*\blender.exe')) + \
        sorted(glob.glob(os.path.join(KIT, 'blender*', 'blender.exe'))) + \
        sorted(glob.glob(os.path.join(DOWN, 'blender-*', 'blender.exe')))
    return c[-1] if c else None


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


def main():
    os.makedirs(WORK, exist_ok=True); os.makedirs(OUT, exist_ok=True); os.makedirs(os.path.join(WORK, 'sheets16'), exist_ok=True)
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    names = args or [n for n in HAIR if os.path.exists(os.path.join(CARTEL, n + '.blend'))]
    blender = find_blender()
    if not blender: sys.exit('Blender not found. Install Blender 5.x from blender.org (or set BLENDER=path\\to\\blender.exe).')
    log('blender:', blender); log('men:', ' '.join(names))
    stills, walks = unpack()
    rc = os.path.join(SPRITES, 'render_char.py'); asm = os.path.join(SPRITES, 'assemble_sheet.py')
    if '--extras-only' not in sys.argv:
        for n in names:
            t0 = time.time(); log('==', n, 'start')
            fr = os.path.join(WORK, 'fr16_' + n); shutil.rmtree(fr, ignore_errors=True)
            clips = ','.join('%s=%s' % kv for kv in list(stills.items()) + list(walks.items()))
            c = run([blender, '-b', '--factory-startup', '--python', rc, '--', '--blend', os.path.join(CARTEL, n + '.blend'),
                     '--clips', clips, '--frames', '8', '--clipframes', 'walk=16,pwalk=16,swalk=16,ewalk=16', '--out', fr],
                    os.path.join(WORK, n + '.render.log'))
            if c: log('RENDER FAILED', n, '- see', n + '.render.log'); continue
            env = dict(os.environ, W16='1', HAIR=HAIR.get(n, ''), FOLD_IDS='', XCOM_UNITS=UNITS)
            c = run([sys.executable, asm, fr, os.path.join(WORK, 'sheets16'), n], os.path.join(WORK, n + '.assemble.log'), env)
            if c: log('ASSEMBLE FAILED', n, '- see', n + '.assemble.log'); continue
            ok, why = check(n)
            for suf in ('_body.png', '_body_rgb.png', '_body_anchors.txt'):
                shutil.copy(os.path.join(WORK, 'sheets16', n + suf), OUT)
            log('done' if ok else 'CHECK FAILED', n, why, '%.1f min' % ((time.time() - t0) / 60))
    if '--no-extras' in sys.argv: return
    lib = os.path.join(CARTEL, 'clips_17nov.blend')
    for n in names:
        t0 = time.time(); fr = os.path.join(WORK, 'extras_' + n); shutil.rmtree(fr, ignore_errors=True)
        clips = ','.join('%s=%s#%s' % (e, lib, e) for e in EXTRAS)
        c = run([blender, '-b', '--factory-startup', '--python', rc, '--', '--blend', os.path.join(CARTEL, n + '.blend'),
                 '--clips', clips, '--frames', '16', '--out', fr], os.path.join(WORK, n + '.extras.log'))
        if c: log('EXTRAS FAILED', n); continue
        strips(n, fr)
        log('extras', n, '%.1f min' % ((time.time() - t0) / 60))


def strips(n, fr):
    # one PNG per clip: 8 facings (rows) x 16 frames, 128x160 cells, raw beauty frames (no outline / palette)
    from PIL import Image
    d = os.path.join(OUT, 'extras'); os.makedirs(d, exist_ok=True)
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
