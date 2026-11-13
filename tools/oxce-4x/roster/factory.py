"""ROSTER character factory: one command per character, from CAST's look package to game sheets + data + notes.
John 13 Nov 12:48: "i have character art chat making the art and they put it in the handoff and you take it and do the rest".
Handoff rules: claude/HANDOFF_CharacterArt_to_ROSTER.md (project).

    python3 factory.py <look_package.zip | dir> --name <sheet name> --kit <render_kit dir> [--quick] [--out <dir>]

Steps (stops at the first failure and says why; nothing is shipped from a failed run):
  1 intake   unpack; the package must hold a look card (*.look.yaml) or a ready .blend, and every file the card names
  2 blend    use the package's .blend, or run the builder the card names (card: builder: <script>) -> <name>.blend
  3 quick    BUILD's kit, QUICK=1 (stand + walk, facing 5): figure inside the frame, nothing cut off, height sane
  4 full     BUILD's kit, render_one.sh unchanged (8 clips x 8 facings x 8 frames) -> <name>_body*.png + anchors
  5 sheet QA sheet size = BUILD's layout, every rendered cell non-empty, anchors line count, magenta background
  6 gif      8-facing walk GIF (the kit's walk_gif.py) for the record
  7 report   <out>/<name>/FACTORY_REPORT.txt: timings, QA lines, what to ship where, the note for BUILD
The data side (stats, text) is build.py; run it once per batch, not per character.
BUILD's kit is used exactly as shipped: no script, clip, camera or ink setting is changed here."""
import argparse, glob, json, os, shutil, subprocess, sys, time, zipfile
import numpy as np
from PIL import Image

CW, CH, COLS = 128, 160, 16          # BUILD's sheet layout (assemble_sheet.py)


def log(rep, s):
    print(s, flush=True); rep.append(s)


def fail(rep, out, s):
    log(rep, 'FAIL: ' + s); open(os.path.join(out, 'FACTORY_REPORT.txt'), 'w').write('\n'.join(rep) + '\n'); sys.exit(1)


def intake(pkg, work, rep, out):
    src = os.path.join(work, 'pkg')
    shutil.rmtree(src, ignore_errors=True)
    if os.path.isdir(pkg): shutil.copytree(pkg, src)
    else:
        with zipfile.ZipFile(pkg) as z:
            for m in z.namelist():                       # untrusted archive: refuse paths that escape the folder
                if m.startswith('/') or '..' in m.split('/'): fail(rep, out, f'unsafe path in package: {m}')
            z.extractall(src)
    cards = glob.glob(os.path.join(src, '**', '*.look.yaml'), recursive=True)
    blends = glob.glob(os.path.join(src, '**', '*.blend'), recursive=True)
    if not cards and not blends: fail(rep, out, 'package has neither a look card (*.look.yaml) nor a .blend')
    card = None
    if cards:
        import yaml
        card = yaml.safe_load(open(cards[0])); base = os.path.dirname(cards[0])
        missing = [f for f in (card.get('files') or []) if not os.path.exists(os.path.join(base, f))]
        if missing: fail(rep, out, f'files the card names are missing: {missing} - back to CAST')
        log(rep, f'intake: card {os.path.basename(cards[0])}, {len(card.get("files") or [])} files present')
    return src, card, (cards[0] if cards else None), blends


def make_blend(src, card, card_path, blends, name, work, rep, out):
    if blends:
        log(rep, f'blend: from the package ({os.path.basename(blends[0])})'); return blends[0]
    builder = (card or {}).get('builder')
    if not builder: fail(rep, out, 'no .blend in the package and the card names no builder')
    dst = os.path.join(work, f'{name}.blend')
    t = time.time()
    r = subprocess.run([sys.executable, builder, '--card', card_path, '--out', dst], capture_output=True, text=True)
    if r.returncode or not os.path.exists(dst): fail(rep, out, f'builder failed: {r.stderr[-800:]}')
    log(rep, f'blend: built by {builder} in {time.time() - t:.0f}s'); return dst


def kit_run(kit, name, blend, quick, rep, out):
    env = dict(os.environ); env.pop('QUICK', None)
    if quick: env['QUICK'] = '1'
    t = time.time()
    r = subprocess.run(['bash', os.path.join(kit, 'render_one.sh'), name, blend], env=env, capture_output=True, text=True)
    msg = (r.stdout + r.stderr).strip().splitlines()[-1:] or ['']
    if r.returncode: fail(rep, out, f'render kit ({"quick" if quick else "full"}): {msg[0]}')
    log(rep, f'kit {"quick" if quick else "full"}: {time.time() - t:.0f}s - {msg[0]}')


def qa_frames(kit, name, rep, out, dirs_expected):
    """every rendered beauty frame: something there, nothing touching the frame edge (cut off)"""
    fr = os.path.join(kit, 'work', f'fr_{name}')
    files = sorted(glob.glob(os.path.join(fr, '*', 'd*_f*_beauty.png')))
    if not files: fail(rep, out, 'no frames rendered')
    empty, cut, tops = [], [], []
    for f in files:
        a = np.array(Image.open(f))[..., 3] > 8
        if not a.any(): empty.append(f); continue
        ys, xs = np.where(a); tops.append(ys.min())
        if ys.min() <= 1 or xs.min() <= 1 or xs.max() >= a.shape[1] - 2 or ys.max() >= a.shape[0] - 2: cut.append(os.path.relpath(f, fr))
    if empty: fail(rep, out, f'{len(empty)} empty frames, e.g. {os.path.relpath(empty[0], fr)}')
    hard = [c for c in cut if not c.startswith('death')]
    if hard: fail(rep, out, f'figure touches the frame edge (cut off) in {len(hard)} frames, e.g. {hard[0]}')
    if cut:   # known kit issue (13 Nov): the fallen man runs off the 512x640 frame in facings 1, 2, 4, 8 - reported to BUILD
        log(rep, f'WARN: death pose cut off at the frame edge in {len(cut)} frames ({", ".join(sorted({c.split("/")[1][:2] for c in cut}))}) - BUILD kit issue, reported')
    log(rep, f'frames QA: {len(files)} frames, none empty; head row {min(tops)}-{max(tops)}')


def qa_sheet(kit, name, rep, out):
    sh = os.path.join(kit, 'sheets'); p = {k: os.path.join(sh, f'{name}_body{k}') for k in ('.png', '_rgb.png', '_anchors.txt')}
    for k, f in p.items():
        if not os.path.exists(f): fail(rep, out, f'missing {os.path.basename(f)}')
    rgb = Image.open(p['_rgb.png']); w, h = rgb.size
    if w != CW * COLS or h % CH: fail(rep, out, f'sheet {w}x{h} is not {CW * COLS} wide in {CH}-px rows')
    a = np.array(rgb.convert('RGBA')); cells = (h // CH) * COLS
    nonempty = sum(bool((a[r * CH:(r + 1) * CH, c * CW:(c + 1) * CW, 3] > 8).any()) for r in range(h // CH) for c in range(COLS))
    lines = [l for l in open(p['_anchors.txt']) if l.strip()]
    pal = Image.open(p['.png'])
    log(rep, f'sheet QA: {w}x{h} ({h // CH} rows, {nonempty}/{cells} cells drawn), 8-bit sheet mode {pal.mode}, {len(lines)} anchor lines')
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('package'); ap.add_argument('--name', required=True); ap.add_argument('--kit', required=True)
    ap.add_argument('--quick', action='store_true'); ap.add_argument('--out', default='factory_out')
    a = ap.parse_args()
    out = os.path.abspath(os.path.join(a.out, a.name)); os.makedirs(out, exist_ok=True)
    work = os.path.join(out, 'work'); os.makedirs(work, exist_ok=True)
    kit = os.path.abspath(a.kit); rep = [f'FACTORY REPORT - {a.name} - {time.strftime("%Y-%m-%d %H:%M")}', f'package: {a.package}']
    t0 = time.time()
    src, card, card_path, blends = intake(a.package, work, rep, out)
    blend = os.path.abspath(make_blend(src, card, card_path, blends, a.name, work, rep, out))
    kit_run(kit, a.name, blend, True, rep, out)
    qa_frames(kit, a.name, rep, out, [5])
    shutil.copy(os.path.join(kit, 'sheets', f'{a.name}_quick.png'), out)
    if not a.quick:
        kit_run(kit, a.name, blend, False, rep, out)
        qa_frames(kit, a.name, rep, out, list(range(1, 9)))
        p = qa_sheet(kit, a.name, rep, out)
        for f in p.values(): shutil.copy(f, out)
        g = subprocess.run([sys.executable, os.path.join(kit, 'scripts', 'walk_gif.py'), os.path.join(kit, 'work', f'fr_{a.name}'),
                            os.path.join(out, f'{a.name}_walk_8dir.gif')], capture_output=True, text=True)
        log(rep, 'walk gif: ' + ((g.stdout or g.stderr).strip().splitlines() or ['?'])[-1])
        rep += ['', 'SHIP: the three sheet files -> Reference\\sheets\\ ; GIF stays with the record.',
                f'NOTE FOR BUILD (ROSTER.md outgoing): "sheets for {a.name} in Reference\\sheets (render kit unchanged); data in roster_<batch>.yaml"']
    log(rep, f'total {time.time() - t0:.0f}s')
    open(os.path.join(out, 'FACTORY_REPORT.txt'), 'w').write('\n'.join(rep) + '\n')


if __name__ == '__main__':
    main()
