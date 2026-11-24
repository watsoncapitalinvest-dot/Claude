#!/usr/bin/env python3
"""Pack mod files as mod_update_<n>.zip for Play_4x.bat.

    python3 build/make_update.py <n> <out dir> <path under mod/> [...]

Play_4x.bat unpacks every update into user\\mods, so each path in the zip MUST start with GIJoe4x/. Updates 101-109
(23 Nov) were zipped from inside mod/ without it, landed in user\\mods\\Ruleset and user\\mods\\Resources, and the game
skipped them ("No metadata.yml in Ruleset, skipping") - a whole day of fixes never reached John's game. This script is
the only way updates are made from now on, and it checks the result before it says done.
"""
import os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, '..', 'mod'))
n, outdir, paths = sys.argv[1], sys.argv[2], sys.argv[3:]
if not paths:
    sys.exit('nothing to pack')
out = os.path.join(outdir, f'mod_update_{n}.zip')
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in paths:
        src = os.path.join(MOD, p)
        if not os.path.isfile(src):
            sys.exit(f'not a file under mod/: {p}')
        z.write(src, 'GIJoe4x/' + p.replace(os.sep, '/'))
names = zipfile.ZipFile(out).namelist()
bad = [x for x in names if not x.startswith('GIJoe4x/')]
assert not bad, bad
print(out, len(names), 'files, all under GIJoe4x/')
