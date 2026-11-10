"""Regenerate oxce_4x.patch, and refuse if it carries probe code or will not apply.

The patch is the only thing in the repo that reproduces the engine, so two failures matter and
neither is visible by reading it:

1. A probe left applied. The probes are temporary instrumentation held in the working tree, and
   `git diff` cannot tell them from the feature - it would ship OXCE_GAR_FORCE, a knob that lets
   an environment variable rewrite a battle's garrison, into John's exe. This refuses on any
   marker, by name, rather than trusting that a revert was remembered.

2. A patch that does not apply. The Windows build clones OXCE at the base commit and applies
   this file; a patch generated from a tree that has drifted fails there, eight minutes later,
   as a red workflow and no exe. So it is applied to a throwaway clone here first. "It built
   locally" says nothing about that - the local tree is already patched.

usage: make_patch.py <oxce src repo> <base commit> <output patch>
"""
import os, subprocess, sys, tempfile, shutil

if len(sys.argv) < 4:
    print(__doc__)
    sys.exit(2)

REPO, BASE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

MARKERS = ['GARPROBE', 'CAMPROBE', 'FFPROBE', 'PENPROBE', 'MATPROBE']


def git(*a, **kw):
    return subprocess.run(['git', '-C', kw.pop('repo', REPO)] + list(a),
                          capture_output=True, text=True, **kw)


# 1. No probe may survive into the patch.
dirty = []
for m in MARKERS:
    r = subprocess.run(['grep', '-rl', m, os.path.join(REPO, 'src')],
                       capture_output=True, text=True)
    for line in r.stdout.strip().split('\n'):
        if line:
            dirty.append((m, os.path.relpath(line, REPO)))
if dirty:
    print('REFUSING: probe instrumentation is still applied to the source.')
    for m, f in dirty:
        print('  %-10s %s' % (m, f))
    print('')
    print('Revert each one and rebuild before shipping, e.g.')
    print('  python3 -I build/gar_probe.py revert <src>')
    sys.exit(1)
print('  ok   no probe markers in src')

# 2. Generate.
r = git('diff', BASE, '--', 'src')
if r.returncode != 0:
    print('REFUSING: git diff failed\n' + r.stderr)
    sys.exit(1)
patch = r.stdout
if not patch.strip():
    print('REFUSING: the patch is empty - wrong base commit?')
    sys.exit(1)
files = patch.count('\ndiff --git') + (1 if patch.startswith('diff --git') else 0)
print('  ok   %d files, %d lines' % (files, len(patch.split('\n'))))

# 3. It has to apply to a clean tree, which is what the workflow does.
tmp = tempfile.mkdtemp(prefix='patchcheck-')
try:
    c = subprocess.run(['git', 'clone', '--quiet', '--no-checkout', '--shared', REPO, tmp],
                       capture_output=True, text=True)
    if c.returncode != 0:
        print('could not clone for the apply check:\n' + c.stderr)
        sys.exit(1)
    subprocess.run(['git', '-C', tmp, 'checkout', '--quiet', BASE], capture_output=True)
    pf = os.path.join(tmp, '..', 'candidate.patch')
    with open(pf, 'w', encoding='utf-8') as fh:
        fh.write(patch)
    a = subprocess.run(['git', '-C', tmp, 'apply', '--check', '-v', pf],
                       capture_output=True, text=True)
    if a.returncode != 0:
        print('REFUSING: the patch does not apply to a clean %s' % BASE[:8])
        print(a.stderr.strip()[:1500])
        sys.exit(1)
    print('  ok   applies cleanly to %s' % BASE[:8])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write(patch)
print('')
print('written: %s' % OUT)
