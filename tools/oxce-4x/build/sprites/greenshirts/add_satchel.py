"""Add the medic satchel to a built greenshirt .blend (REGJOE, 12 Nov 2026).
Bag = the lower part (no strap loop) of "Snake Eyes Satchel - Classified Series" (Thingiverse 5022823, bawvu97,
CC-BY), on the LEFT hip, weighted 100% to mixamorig:Hips. Strap = a taut band from the bag over the RIGHT shoulder:
convex hull of the body section in a diagonal plane (so it bridges pouches / hollows like a real strap), offset 1 cm,
weights copied from the nearest body vertex. Olive bag, white flap with red cross on the outer face, webbing strap.
Usage: python3 add_satchel.py -- <in.blend> <out.blend> <Murse.stl tris.npy> [cfg.json]

BUILD SESSION COPY (prop_satchel_medic.zip add_satchel.py), patched only for the render_char.py contract:
  - body meshes are found by 'Ch49' anywhere in the name (factory_ch49.py names them B|Ch49_body1 / B|Ch49_body2;
    the original's startswith('Ch49') finds none of them);
  - every satchel material gets an IDSWITCH (input 2 = garment id SATCHEL_ID/40, default 37, + camera depth 8..12 m),
    the SAME id on bag, core and strap, so the ink draws only the satchel's outer contour (the zip's rule: satchel_*
    objects get contour-only ink, like the helmet's single id 36);
  - textures packed. tris.npy (Murse.stl, bawvu97, CC-BY) stays outside the repo."""
import os
import bpy, sys, json, numpy as np
from mathutils import Vector
from scipy.spatial import ConvexHull, cKDTree
argv = sys.argv[sys.argv.index('--') + 1:]
inb, outb, trisp = argv[:3]
C = dict(bag_w=0.22, thick_mul=0.75, bag_bot=0.80, bag_y=0.01, gap=0.005, strap_w=0.036, strap_off=0.010,
         shoulder_x=-0.10, olive=[104, 124, 62], white=[238, 238, 232], red=[196, 32, 32], strap=[150, 86, 38],
         shadow=0.62, flap_from=0.55)
if len(argv) > 3: C.update(json.load(open(argv[3])))
bpy.ops.wm.open_mainfile(filepath=inb)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
body = [o for o in bpy.data.objects if o.type == 'MESH' and 'Ch49' in o.name]
assert body, 'no Ch49 body meshes found'
V, G = [], []
for o in body:
    names = {g.index: g.name for g in o.vertex_groups}
    for v in o.data.vertices:
        V.append(tuple(o.matrix_world @ v.co)); G.append({names[g.group]: g.weight for g in v.groups if g.weight > 0.01})
V = np.array(V); kd = cKDTree(V)
KEY = -np.array([0.45, 0.6, -0.66]); KEY /= np.linalg.norm(KEY)          # direction TO the key light

SATCHEL_ID = int(os.environ.get('SATCHEL_ID', 37))
def _idswitch(nt, beauty_out, out_in):
    comb = nt.nodes.new('ShaderNodeCombineColor'); comb.inputs[0].default_value = SATCHEL_ID / 40.0
    camd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
    nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
    ei = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], ei.inputs['Color'])
    sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'; sw.inputs[0].default_value = 0.0
    nt.links.new(beauty_out, sw.inputs[1]); nt.links.new(ei.outputs[0], sw.inputs[2]); nt.links.new(sw.outputs[0], out_in)
def emis(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission')
    e.inputs[0].default_value = (*[(c / 255) ** 2.2 for c in col], 1); _idswitch(nt, e.outputs[0], o.inputs[0]); return m

def make(name, verts, faces, mats, mat_idx, groups):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(p) for p in verts], [], [tuple(f) for f in faces])
    for m in mats: me.materials.append(m)
    for p, i in zip(me.polygons, mat_idx): p.material_index = int(i)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    for vi, gw in enumerate(groups):
        for gn, w in gw.items():
            g = ob.vertex_groups.get(gn) or ob.vertex_groups.new(name=gn); g.add([vi], w, 'REPLACE')
    ob.parent = arm; ob.matrix_parent_inverse = arm.matrix_world.inverted()
    md = ob.modifiers.new('arm', 'ARMATURE'); md.object = arm
    return ob

# ---------------- bag
T = np.load(trisp).astype(np.float64)
T = T[(T[..., 2] < 0.66).all(1)]
lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
S = C['bag_w'] / (hi[0] - lo[0]); th = (hi[1] - lo[1]) * S * C['thick_mul']
zs = V[(np.abs(V[:, 2] - (C['bag_bot'] + 0.09)) < 0.03) & (np.abs(V[:, 0]) < 0.35)]
xin = zs[:, 0].max() + C['gap']                                         # outside of the left hip
P = T.reshape(-1, 3)
W = np.stack([xin + (P[:, 1] - lo[1]) / (hi[1] - lo[1]) * th,
              (P[:, 0] - (lo[0] + hi[0]) / 2) * S + C['bag_y'],
              (P[:, 2] - lo[2]) * S + C['bag_bot']], -1)
Wt = W.reshape(-1, 3, 3)
n = np.cross(Wt[:, 1] - Wt[:, 0], Wt[:, 2] - Wt[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
cen = Wt.mean(1); bc = W.mean(0); out = np.sign(((cen - bc) * n).sum(1)); n *= np.where(out == 0, 1, out)[:, None]
bag_top = W[:, 2].max(); bag_h = bag_top - C['bag_bot']
# paint by position only (the STL has coincident layers; per-normal paint z-fights)
outer = cen[:, 0] > xin + th * 0.5
flap = outer & (cen[:, 2] > C['bag_bot'] + C['flap_from'] * bag_h)
fz = (C['bag_bot'] + C['flap_from'] * bag_h + bag_top) / 2; dy = cen[:, 1] - C['bag_y']; dz = cen[:, 2] - fz
arm_ = 0.03; bar = 0.011
cross = flap & (((np.abs(dy) < bar) & (np.abs(dz) < arm_)) | ((np.abs(dy) < arm_) & (np.abs(dz) < bar)))
shade = (cen[:, 2] < C['bag_bot'] + 0.008) | (cen[:, 0] < xin + th * 0.3)      # underside + the side against the hip
base = np.where(cross, 4, np.where(flap, 2, 0)) + shade
# texture painted by (y, z), planar UVs -> clean flap edge whatever the triangulation
ylo, yhi = W[:, 1].min(), W[:, 1].max(); R_ = 256
def bag_img(name, mul):
    yy, zz = np.meshgrid((np.arange(R_) + 0.5) / R_ * (yhi - ylo) + ylo, (np.arange(R_) + 0.5) / R_ * bag_h + C['bag_bot'])
    im = np.zeros((R_, R_, 3)) + C['olive']
    fl = zz > C['bag_bot'] + C['flap_from'] * bag_h; im[fl] = C['white']
    dy_ = yy - C['bag_y']; dz_ = zz - fz
    cr = fl & (((np.abs(dy_) < bar) & (np.abs(dz_) < arm_)) | ((np.abs(dy_) < arm_) & (np.abs(dz_) < bar))); im[cr] = C['red']
    im = (im * mul / 255.0) ** 2.2
    img = bpy.data.images.new(name, R_, R_, alpha=True)
    img.pixels = np.concatenate([im, np.ones((R_, R_, 1))], -1).astype(np.float32).ravel()
    img.pack(); return img
def tex_mat(name, img):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission'); t = nt.nodes.new('ShaderNodeTexImage')
    t.image = img; t.interpolation = 'Closest'; t.image.colorspace_settings.name = 'Non-Color'
    nt.links.new(t.outputs[0], e.inputs[0]); _idswitch(nt, e.outputs[0], o.inputs[0]); return m
mats = [tex_mat('SAT_lit', bag_img('sat_lit', 1.0)), tex_mat('SAT_sh', bag_img('sat_sh', C['shadow'])), emis('SAT_olive', C['olive']), emis('SAT_olive_sh', [c * C['shadow'] for c in C['olive']])]
base = np.where(outer, 0, 3) - np.where(outer, 0, 0)
base = np.where(outer, 0, 3)
bag = make('satchel_bag', W, np.arange(len(W)).reshape(-1, 3), mats, base, [{'mixamorig:Hips': 1.0}] * len(W))
uvl = bag.data.uv_layers.new(name='UV')
for li, lp in enumerate(bag.data.loops):
    p = W[lp.vertex_index]; uvl.data[li].uv = ((p[1] - ylo) / (yhi - ylo), (p[2] - C['bag_bot']) / bag_h)
bpy.ops.object.select_all(action='DESELECT'); bag.select_set(True); bpy.context.view_layer.objects.active = bag
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.remove_doubles(threshold=1e-5); bpy.ops.object.mode_set(mode='OBJECT')
# solid core so the gaps between the STL's compartments don't show the background
x0, x1 = xin + 0.012, xin + th - 0.012; y0, y1 = W[:, 1].min() + 0.010, W[:, 1].max() - 0.010; z0, z1 = C['bag_bot'] + 0.004, bag_top - 0.006
cv = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
cf = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
cn = np.array([[0, 0, -1], [0, 0, 1], [0, -1, 0], [1, 0, 0], [0, 1, 0], [-1, 0, 0]], float)
make('satchel_core', np.array(cv), cf, [mats[2], mats[3]], [1, 0, 0, 0, 0, 1], [{'mixamorig:Hips': 1.0}] * 8)
print('bag', len(T), 'tris; x', round(xin, 3), '..', round(xin + th, 3), 'z', C['bag_bot'], '..', round(bag_top, 3))

# ---------------- strap (taut band over the right shoulder)
P1 = np.array([xin + th / 2, 0.0, bag_top - 0.01])
sh = V[(np.abs(V[:, 0] - C['shoulder_x']) < 0.015) & (np.abs(V[:, 1]) < 0.06)]
P2 = np.array([C['shoulder_x'], 0.0, sh[:, 2].max()])
d = (P2 - P1); d[1] = 0; d /= np.linalg.norm(d); nn = np.array([d[2], 0, -d[0]])
yv = np.array([0, 1.0, 0])
tor = V[np.abs(V[:, 0]) < 0.32]
slab = tor[np.abs((tor - P1) @ nn) < 0.012]
q = np.stack([(slab - P1) @ d, slab[:, 1]], -1); q = q[q[:, 0] > -0.03]
hl = ConvexHull(q); poly = q[hl.vertices]                                # counter-clockwise loop
# chain from the lowest front point over the top to the lowest back point (drop the bottom edge)
ym = np.median(poly[:, 1]); fr = np.where(poly[:, 1] < ym)[0]; bk = np.where(poly[:, 1] >= ym)[0]
i_f = fr[np.argmin(poly[fr, 0])]; i_b = bk[np.argmin(poly[bk, 0])]; i_t = np.argmax(poly[:, 0])
L = len(poly)
def walk(a, b, step):
    out = [a]; i = a
    while i != b: i = (i + step) % L; out.append(i)
    return out
c1 = walk(i_f, i_b, 1)
chain = poly[c1] if i_t in c1 else poly[walk(i_f, i_b, -1)]
hw = C['bag_w'] / 2 - 0.02
chain = np.concatenate([[[0.0, C['bag_y'] - hw]], chain, [[0.0, C['bag_y'] + hw]]])
# resample every 1 cm, offset outward
seg = np.linalg.norm(np.diff(chain, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
ss = np.arange(0, s[-1], 0.01); pts = np.stack([np.interp(ss, s, chain[:, 0]), np.interp(ss, s, chain[:, 1])], -1)
tg = np.gradient(pts, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
nrm2 = np.stack([tg[:, 1], -tg[:, 0]], -1)
cc = q.mean(0)
if ((pts - cc) * nrm2).sum(1).mean() < 0: nrm2 = -nrm2
pts = pts + nrm2 * C['strap_off']
P3 = P1[None] + pts[:, :1] * d[None] + pts[:, 1:2] * yv[None]
w2 = C['strap_w'] / 2
SV = np.concatenate([P3 - nn * w2, P3 + nn * w2]); m_ = len(P3)
SF = [(i, i + 1, m_ + i + 1, m_ + i) for i in range(m_ - 1)]
# shade by the band normal (outward 3D)
on = nrm2[:, :1] * d[None] + nrm2[:, 1:2] * yv[None]
slit = (on @ KEY) > -0.05
smats = [emis('STRAP', C['strap']), emis('STRAP_sh', [c * C['shadow'] for c in C['strap']])]
_, nb = kd.query(SV)
strap = make('satchel_strap', SV, SF, smats, [0 if slit[i] else 1 for i in range(m_ - 1)], [G[j] for j in nb])
print('strap', m_, 'pts; u range', round(pts[:, 0].min(), 3), round(pts[:, 0].max(), 3), 'y', round(pts[:, 1].min(), 3), round(pts[:, 1].max(), 3))
bpy.ops.file.pack_all(); bpy.ops.wm.save_as_mainfile(filepath=outb); print('SAVED', outb)
