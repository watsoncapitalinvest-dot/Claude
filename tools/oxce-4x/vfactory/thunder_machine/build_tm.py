# Dreadnok Thunder Machine rebuild (VFACTORY, John 17 Nov 17:36 "both chain gun turrets rotate when it shoots",
# 17:37 "it also needs better details and decals").
# - GJTURRET (the Generals model's twin gun block) is replaced by two modelled 6-barrel "Penetrator" Gatlings on one
#   cradle (canon: belt-fed synchronized Gatling guns), with ammo boxes and feed chutes; it becomes the turret layer.
# - Toy references (John 17:43: instructions, blueprint, toy photo): navy lower hull under the red armour panels, blue tube
#   roll cage in front of the guns, ammo-belt gear beside them, antenna behind the cab.
# - Dreadnok junk the toy's story asks for ("fabricated from used auto and truck parts"): side exhaust pipes, a vertical
#   stack, jerry cans on the rear deck, a push bar on the front. Sizes chosen to read at sprite size (>= 3 px).
# Decals are placed afterwards by veh/damage_generic.py (decals.json). The rear points ROSTER listed as rocket muzzles
# are the jet exhausts; nothing fires from them now.
# usage: python3 -I build_tm.py in.blend out.blend
import bpy, bmesh, sys, math, tempfile
from mathutils import Matrix, Vector
from PIL import Image
IN, OUT = sys.argv[-2:]; bpy.ops.wm.open_mainfile(filepath=IN); TMP = tempfile.mkdtemp()
_dg = bpy.context.evaluated_depsgraph_get()
def top(x, y):                                                    # hull surface height under (x, y), measured before anything is added
    ok, loc, *_ = bpy.context.scene.ray_cast(_dg, Vector((x, y, 30)), Vector((0, 0, -1)))
    return loc.z if ok else 0.0
ZG = max(top(x, 0) for x in (8.0, 9.0, 10.0, 10.5))                # the front cowl: the guns sit above it (the turret layer draws over the hull)
ZD = top(6.3, 0); ZC = {s: top(-8.6, 2.0 * s) for s in (1, -1)}

def mat(name, rgb):
    m = bpy.data.materials.get(name)
    if m: return m
    p = f'{TMP}/{name}.png'; Image.new('RGB', (4, 4), rgb).save(p); im = bpy.data.images.load(p); im.pack()
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; t.interpolation = 'Closest'
    nt.links.new(t.outputs[0], nt.nodes['Principled BSDF'].inputs['Base Color']); m.diffuse_color = (*[c / 255 for c in rgb], 1); return m

M = {'steel': mat('tm_steel', (92, 96, 102)), 'dark': mat('tm_dark', (30, 31, 34)), 'bore': mat('tm_bore', (8, 8, 8)),
     'brass': mat('tm_brass', (176, 136, 58)), 'olive': mat('tm_olive', (78, 86, 52)), 'chrome': mat('tm_chrome', (168, 170, 174)),
     'rust': mat('tm_rust', (112, 62, 34)), 'red': mat('tm_red', (150, 22, 24)), 'blue': mat('tm_blue', (34, 52, 140))}

class Builder:
    def __init__(self, name):
        self.bm = bmesh.new(); self.name = name; self.keys = list(M); self.uv = None
    def _tag(self, geom, key):
        for f in {f for v in geom for f in v.link_faces}: f.material_index = self.keys.index(key)
    def cyl_x(self, x0, x1, y, z, r, key, seg=12):            # cylinder along X
        L = x1 - x0; m = Matrix.Translation(((x0 + x1) / 2, y, z)) @ Matrix.Rotation(math.pi / 2, 4, 'Y')
        g = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=L, matrix=m); self._tag(g['verts'], key)
    def cyl_z(self, x, y, z0, z1, r, key, seg=12):
        g = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=z1 - z0, matrix=Matrix.Translation((x, y, (z0 + z1) / 2))); self._tag(g['verts'], key)
    def cyl_y(self, x, y0, y1, z, r, key, seg=16):            # disc / cylinder along Y
        m = Matrix.Translation((x, (y0 + y1) / 2, z)) @ Matrix.Rotation(math.pi / 2, 4, 'X')
        g = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=abs(y1 - y0), matrix=m); self._tag(g['verts'], key)
    def tube(self, pts, r, key):                                   # a bent tube through points (roll cage)
        for a, b in zip(pts, pts[1:]):
            a, b = Vector(a), Vector(b); d = b - a; q = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
            g = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=8, radius1=r, radius2=r, depth=d.length, matrix=Matrix.Translation((a + b) / 2) @ q); self._tag(g['verts'], key)
    def box(self, c, s, key):
        g = bmesh.ops.create_cube(self.bm, size=1.0, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*s, 1))); self._tag(g['verts'], key)
    def done(self):
        me = bpy.data.meshes.new(self.name); self.bm.to_mesh(me); self.bm.free()
        for k in self.keys: me.materials.append(M[k])
        me.uv_layers.new(name='UVMap'); o = bpy.data.objects.new(self.name, me); bpy.context.scene.collection.objects.link(o); return o

# ---- the twin Gatlings (replace GJTURRET): raised on a pedestal so they clear the front cowl; muzzles at x 11.45, y +-0.62
old = bpy.data.objects.get('GJTURRET')
if old: bpy.data.objects.remove(old)
g = Builder('GJTURRET')
GZ = ZG + 0.55                                                    # gun axis height
g.cyl_z(6.3, 0, ZD, GZ - 0.3, 0.38, 'dark')                       # pedestal up from the deck (the turret turns on it)
g.cyl_z(6.3, 0, GZ - 0.42, GZ - 0.3, 0.6, 'steel')                # traverse ring
g.box((6.6, 0, GZ), (1.6, 1.0, 0.7), 'dark')                      # cradle between the guns
for s in (1, -1):
    y = 0.62 * s
    g.box((6.9, y, GZ), (1.8, 0.62, 0.72), 'steel')               # receiver
    g.box((6.3, y, GZ + 0.45), (0.7, 0.4, 0.22), 'dark')          # drive motor on top
    for k in range(6):                                            # six barrels round the axis
        a = 2 * math.pi * k / 6; by, bz = y + 0.17 * math.cos(a), GZ + 0.17 * math.sin(a)
        g.cyl_x(7.8, 11.4, by, bz, 0.065, 'steel', seg=8)
        g.cyl_x(11.35, 11.45, by, bz, 0.04, 'bore', seg=6)
    for xr in (8.6, 10.9):                                        # barrel clamps
        g.cyl_x(xr - 0.12, xr + 0.12, y, GZ, 0.3, 'dark')
    g.cyl_x(7.75, 8.05, y, GZ, 0.33, 'dark')                      # front of the receiver
# the "Fast Fire" woven ammo belt: one wide drum of linked rounds wrapped round the middle of the gun armature, across
# nearly the whole width between the front wheels (John 17:45 top view; instructions step 7A "wrap ammo belt around
# middle of gun armature"). Links alternate black link / brass round so it reads as a belt, not a pipe.
for i in range(30):
    yy = -2.55 + i * 0.17
    if i % 2: g.cyl_y(6.85, yy, yy + 0.17, GZ, 0.74, 'dark', seg=14)
    else: g.cyl_y(6.85, yy, yy + 0.17, GZ, 0.66, 'brass', seg=14)
g.cyl_y(6.85, -2.6, 2.6, GZ, 0.22, 'steel')                       # armature axle through it
print('GUN_AXIS_Z %.3f PIVOT 6.3 0 %.3f' % (GZ, ZD))
g.done()

# ---- toy paint: the lower hull is navy under the red armour panels. A navy copy of the same painted texture (red turned
# to navy in HSV, so the Generals panel lines and shading stay; black and grey stay as they are). The renderer reads the
# image itself, not shader nodes, so the copy is a real image. The lower side band (z < 3.6) is navy; the armour above stays red.
import numpy as np, colorsys
ch = bpy.data.objects['GJCHASSIS']; src = ch.data.materials[0]
tex = next(n for n in src.node_tree.nodes if n.type == 'TEX_IMAGE').image
w, hgt = tex.size; px = np.array(tex.pixels[:], dtype=np.float32).reshape(hgt, w, 4)
r, g_, b_ = px[..., 0], px[..., 1], px[..., 2]; mx = np.maximum(np.maximum(r, g_), b_); mn = np.minimum(np.minimum(r, g_), b_)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0); red = (r >= g_) & (r >= b_) & (sat > 0.35)
NAVY = np.array([0.075, 0.095, 0.27])                             # toy navy, scaled by the texel's own brightness
out = px.copy(); k = (mx / max(float(np.percentile(mx[red], 75)) if red.any() else 1.0, 1e-3))[..., None]
out[..., :3] = np.where(red[..., None], np.clip(NAVY * k * 1.25, 0, 1), px[..., :3])
nimg = bpy.data.images.new('gjtm_navy_tex', w, hgt, alpha=True); nimg.pixels = out.ravel().tolist(); nimg.pack()
nv = src.copy(); nv.name = 'gjtm_navy'; next(n for n in nv.node_tree.nodes if n.type == 'TEX_IMAGE').image = nimg
ch.data.materials.append(nv); NV = len(ch.data.materials) - 1; W = ch.matrix_world; nn = 0
for p in ch.data.polygons:
    c = W @ p.center
    if c.z < 3.6 and -11.0 < c.x < 5.5: p.material_index = NV; nn += 1    # whole lower side band: the big hull triangles make any x cut diagonal
print('NAVY_FACES', nn)

# ---- hull junk (all on the hull layer)
h = Builder('GJJUNK')
for s in (1, -1):
    h.cyl_x(-9.0, -1.5, 4.55 * s, 0.9, 0.32, 'chrome')            # side exhaust pipes
    h.cyl_x(-9.4, -9.0, 4.55 * s, 0.9, 0.36, 'rust')              # rusty pipe ends
    h.box((-8.6, 2.0 * s, ZC[s] + 0.6), (1.0, 0.7, 1.2), 'olive')  # jerry cans standing on the rear deck
    h.box((-8.6, 2.0 * s, ZC[s] + 1.26), (0.3, 0.25, 0.12), 'dark') # can handles
h.cyl_z(-3.0, 4.2, 1.0, 7.8, 0.3, 'chrome')                       # exhaust stack up the side (driver's side)
h.cyl_z(-3.0, 4.2, 7.8, 8.1, 0.36, 'rust')
ZF = top(11.6, 2.4)                                               # blue tubular roll cage in front of the guns (blueprint item 4)
for yy in (2.4, -2.4):
    h.tube([(11.6, yy, ZF), (11.9, yy, ZF + 2.2), (11.2, yy * 0.8, ZG + 1.5), (9.8, yy * 0.8, ZG + 1.7)], 0.16, 'blue')
h.tube([(11.2, 1.92, ZG + 1.5), (11.2, -1.92, ZG + 1.5)], 0.16, 'blue')
h.tube([(11.9, 2.4, ZF + 2.2), (11.9, -2.4, ZF + 2.2)], 0.16, 'blue')
ZA = top(-6.5, -2.6); h.cyl_z(-6.5, -2.6, ZA, ZA + 6.0, 0.1, 'blue')  # antenna behind the cab (blueprint item 3)
h.done()

bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print('BUILT', OUT)
