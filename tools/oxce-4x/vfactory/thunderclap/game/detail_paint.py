# More detail on guns + missiles, same colours (John 17 Nov 14:52 "more detail on the guns, the colors make them look flat. the color is good though").
# Turret: light-grey housing kept; barrels steel, cooling rings, black bores, dark undersides and small parts. Stores -> missile_*: orange body kept,
# dark nose cone, dark nozzle, a dark band, fins a shade down (render_vehicle gives 'missile*' objects their own rounded shading).
import bpy, sys, numpy as np
from mathutils import Vector
from PIL import Image
import tempfile
IN, OUT = sys.argv[-2:]; bpy.ops.wm.open_mainfile(filepath=IN); TMP = tempfile.mkdtemp()
def mat(name, rgb):
    m = bpy.data.materials.get(name)
    if m: return m
    p = f'{TMP}/{name}.png'; Image.new('RGB', (4, 4), rgb).save(p); im = bpy.data.images.load(p); im.pack()
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; t.interpolation = 'Closest'
    nt.links.new(t.outputs[0], nt.nodes['Principled BSDF'].inputs['Base Color']); m.diffuse_color = (*[c / 255 for c in rgb], 1); return m
def repaint(o, slots, pick):
    o.data.materials.clear(); ix = {}
    for n, (mn, rgb) in slots.items(): o.data.materials.append(mat(mn, rgb)); ix[n] = len(o.data.materials) - 1
    W = o.matrix_world; R = W.to_3x3()
    for p in o.data.polygons: p.material_index = ix[pick(W @ p.center, (R @ p.normal).normalized(), p.area)]
# ---- turret
t = bpy.data.objects['turret']; P = np.array([(t.matrix_world @ v.co)[:] for v in t.data.vertices]); x1 = P[:, 0].max()
tips = P[P[:, 0] > x1 - 3]; ys = sorted(set(np.round(tips[:, 1] / 4) * 4))
from scipy.cluster.vq import kmeans2
C, _ = kmeans2(tips[:, 1:], 2, seed=1, minit='++')                      # the two barrel axes (y, z)
# where the barrels leave the housing: walk back from the muzzle while the cross-section stays thin
xs = np.arange(x1, P[:, 0].min(), -1.0); xb = x1
for x in xs:
    s = P[(P[:, 0] > x - 1) & (P[:, 0] <= x)]
    if len(s) and np.min([np.hypot(s[:, 1] - c[0], s[:, 2] - c[1]) for c in C], 0).max() > 9: break
    xb = x
area_med = np.median([p.area for p in t.data.polygons])
def tpick(c, n, a):
    r = min(np.hypot(c.y - cc[0], c.z - cc[1]) for cc in C)
    if c.x > x1 - 1.2 and r < 3.5: return 'bore'
    if c.x > xb and r < 7.5:
        return 'barrel'
    if n.z < -0.35: return 'under'
    if a < area_med * 0.35: return 'small'
    if abs(n.z) < 0.3 and abs(n.y) > 0.7: return 'side'
    return 'housing'
repaint(t, {'housing': ('tk_gun', (150, 156, 166)), 'side': ('tk_gun_side', (128, 134, 144)), 'under': ('tk_gun_dk', (60, 64, 70)),
            'small': ('tk_gun_part', (92, 97, 106)), 'barrel': ('tk_barrel', (104, 110, 120)), 'ring': ('tk_barrel_ring', (52, 55, 60)),
            'bore': ('tk_bore', (18, 18, 20))}, tpick)
print('TURRET barrels from x', round(xb, 1), 'to', round(x1, 1), 'axes', np.round(C, 1))
# ---- missiles
for o in [o for o in bpy.data.objects if o.name.startswith('msl_')]:
    o.name = 'missile_' + o.name[4:]
    Q = np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices]); a0, a1 = Q[:, 0].min(), Q[:, 0].max(); L = a1 - a0
    cy, cz = np.median(Q[:, 1]), np.median(Q[:, 2]); rr = np.hypot(Q[:, 1] - cy, Q[:, 2] - cz); rbody = np.percentile(rr, 50)
    def mpick(c, n, a):
        u = (c.x - a0) / L; r = np.hypot(c.y - cy, c.z - cz)
        if u > 0.90: return 'tip'
        if u < 0.04: return 'nozzle'
        if r > rbody * 1.35: return 'fin'
        if 0.62 < u < 0.66: return 'band'
        return 'body'
    repaint(o, {'body': ('missile_body', (244, 128, 28)), 'tip': ('missile_tip', (40, 40, 44)), 'nozzle': ('missile_tip_nozzle', (70, 72, 78)),
                'fin': ('missile_fin', (214, 104, 18)), 'band': ('missile_band', (40, 40, 44))}, mpick)
    print('MISSILE', o.name, 'len', round(L, 1), 'r', round(rbody, 2))

from mathutils.bvhtree import BVHTree
def ao_shade(objs, levels=(1.0, 0.82, 0.64, 0.48), dist=14.0, nray=24):
    import bmesh
    bm = bmesh.new()
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('decal')]:
        m = o.data.copy(); m.transform(o.matrix_world); bm.from_mesh(m)
    tree = BVHTree.FromBMesh(bm); rng = np.random.default_rng(3)
    D = rng.normal(size=(nray, 3)); D /= np.linalg.norm(D, axis=1)[:, None]
    for o in objs:
        W = o.matrix_world; R = W.to_3x3(); base = list(o.data.materials); cache = {}
        for p in o.data.polygons:
            c = W @ p.center; n = (R @ p.normal).normalized(); hit = 0; k = 0
            for d in D:
                v = Vector(d)
                if v.dot(n) < 0: v = -v
                v = (v + n * 0.3).normalized(); k += 1
                if tree.ray_cast(c + n * 0.05, v, dist)[0] is not None: hit += 1
            occ = hit / k; lv = 0 if occ < 0.25 else 1 if occ < 0.45 else 2 if occ < 0.65 else 3
            if lv == 0: continue
            src = base[p.material_index]; key = (src.name, lv)
            if key not in cache:
                nm = f'{src.name}_ao{lv}'; m = bpy.data.materials.get(nm)
                if not m:
                    rgb = tuple(int(255 * x * levels[lv]) for x in src.diffuse_color[:3])
                    if src.name.startswith('tk_') and src.diffuse_color[0] > 0.79 and src.diffuse_color[1] > 0.79:   # kit materials keep their colour in the texture
                        im = [nd for nd in src.node_tree.nodes if nd.type == 'TEX_IMAGE'][0].image; px = list(im.pixels[:3])
                        rgb = tuple(int(255 * x * levels[lv]) for x in px)
                    m = mat(nm, rgb)
                o.data.materials.append(m); cache[key] = len(o.data.materials) - 1
            p.material_index = cache[key]
        print('AO', o.name, len(cache))
# ao_shade([o for o in bpy.data.objects if o.name in ('turret', 'launcher', 'launcher_cradle', 'antenna')])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
