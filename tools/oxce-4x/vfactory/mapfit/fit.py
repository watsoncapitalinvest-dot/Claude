# Which battle maps still take the bigger vehicles (size 3 = VAMP 2x3, size 4 = H.I.S.S./MOBAT 3x4, square stand-ins).
# For every terrain block: ground-layer positions where an n x n vehicle can stand (every tile: a walkable floor, no wall
# between its tiles, no blocking object), and the biggest square that fits anywhere. Static check from MAP/MCD files only.
import yaml, glob, os, struct, sys, json, collections
MOD = '/home/claude/repo/tools/oxce-4x/mod'; STD = '/home/claude/oxce/bin/standard'; UFO = '/mnt/user-data/uploads/GIJoe_XCOM_4x/UFO'; PRIV = '/mnt/user-data/uploads/GIJoe_XCOM_4x/user/mods/GIJoe4x'
class L(yaml.SafeLoader): pass
L.add_multi_constructor('', lambda l, s, n: None)
def ld(f):
    try: return yaml.load(open(f, encoding='utf-8', errors='replace'), Loader=L) or {}
    except Exception as e: return {}
terr = {}
for f in sorted(glob.glob(f'{STD}/xcom1/*.rul')) + sorted(glob.glob(f'{MOD}/Ruleset/*.rul')):
    d = ld(f)
    for t in (d.get('terrains') or []):
        if isinstance(t, dict) and t.get('name'):
            terr.setdefault(t['name'], {}).update({k: v for k, v in t.items() if v is not None}); terr[t['name']]['_file'] = os.path.basename(f)
mcdcache = {}
def mcd(name):
    if name in mcdcache: return mcdcache[name]
    for p in (f'{MOD}/TERRAIN/{name}.MCD', f'{PRIV}/TERRAIN/{name}.MCD', f'{UFO}/TERRAIN/{name}.MCD'):
        if os.path.exists(p):
            d = open(p, 'rb').read(); recs = []
            for i in range(len(d) // 62):
                r = d[i * 62:(i + 1) * 62]
                recs.append(dict(nofloor=r[32], bigwall=r[33], walk=r[39], door=r[35] or r[30], ttype=r[54]))
            mcdcache[name] = recs; return recs
    mcdcache[name] = None; return None
def mapfile(name):
    for ext, w in (('MAP2', 2), ('MAP', 1)):
        for base in (MOD, PRIV, UFO):
            p = f'{base}/MAPS/{name}.{ext}'
            if os.path.exists(p): return p, w
    return None, 0
def analyse(tname, t, block):
    sets = t.get('mapDataSets') or []
    table = []; missing = []
    for s in sets:
        r = mcd(s)
        if r is None: missing.append(s); r = [None] * 0
        table += r
    p, w = mapfile(block)
    if not p: return None
    d = open(p, 'rb').read(); Y, X, Z = d[0], d[1], d[2]
    if w == 2: v = struct.unpack('<%dH' % ((len(d) - 3) // 2), d[3:3 + 2 * X * Y * Z * 4])
    else: v = d[3:3 + X * Y * Z * 4]
    if len(v) < X * Y * Z * 4: return None
    best = None
    for g in range(Z):                                  # file order is top level first; every level is tried (decks, bays, floors)
        r = level(g, X, Y, Z, v, table)
        r['level_from_ground'] = Z - 1 - g
        if best is None or (r['fit4'], r['fit3'], r['fit2']) > (best['fit4'], best['fit3'], best['fit2']): best = r
        if g == Z - 1: ground = r
    res = {'size': [X, Y, Z], 'missing_sets': missing, 'ground': ground, 'best': best}
    return res
def level(g, X, Y, Z, v, table):
    def part(x, y, k):
        i = v[((g * Y + y) * X + x) * 4 + k]
        if i == 0: return None
        return table[i] if i < len(table) else 'unknown'
    stand = [[False] * X for _ in range(Y)]; wW = [[False] * X for _ in range(Y)]; wN = [[False] * X for _ in range(Y)]
    for y in range(Y):
        for x in range(X):
            fl, west, north, ob = (part(x, y, k) for k in range(4))
            okf = isinstance(fl, dict) and fl['walk'] < 255 and not fl['nofloor']
            okob = ob is None or (isinstance(ob, dict) and ob['walk'] < 255 and ob['bigwall'] == 0)
            stand[y][x] = okf and okob
            wW[y][x] = west is not None and not (isinstance(west, dict) and (west['walk'] < 255 or west['door']))
            wN[y][x] = north is not None and not (isinstance(north, dict) and (north['walk'] < 255 or north['door']))
    def fits(n, x0, y0):
        for y in range(y0, y0 + n):
            for x in range(x0, x0 + n):
                if not stand[y][x]: return False
                if x > x0 and wW[y][x]: return False
                if y > y0 and wN[y][x]: return False
        return True
    res = {}
    for n in (1, 2, 3, 4, 5):
        res[f'fit{n}'] = sum(fits(n, x, y) for y in range(Y - n + 1) for x in range(X - n + 1))
    res['biggest'] = max([n for n in (1, 2, 3, 4, 5) if res[f'fit{n}']] or [0])
    return res
out = {}
for tn, t in sorted(terr.items()):
    for b in (t.get('mapBlocks') or []):
        if not isinstance(b, dict) or not b.get('name'): continue
        r = analyse(tn, t, b['name'])
        if r: out.setdefault(tn, {})[b['name']] = dict(r, block_wl=[b.get('width', 10), b.get('length', 10)], file=t['_file'])
json.dump(out, open('fit.json', 'w'), indent=0)
print('terrains', len(out), 'blocks', sum(len(v) for v in out.values()), 'no-map terrains', len([t for t in terr if t not in out]))
