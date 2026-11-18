"""Render a dressed vehicle to the vessels' battle-map look (vessels_part1 manifest):
orthographic, 30 deg elevation, 90.50967 px per world unit, frame 256x224 for a 2x2 footprint, anchor (128,160),
supersample 3, flat toy palette, 3-tone cel light, thin dark outline, transparent, no shadow, no ground.
python3 render_vehicle.py dressed.blend outdir name look heading_index [scale]"""
import bpy, sys, os, math, numpy as np
from mathutils import Vector, Matrix
from PIL import Image
from scipy import ndimage as ndi
blend, outdir, name, look, hk = sys.argv[1:6]; hk = int(hk); SCALE = float(sys.argv[6]) if len(sys.argv) > 6 else 0.05
HEAD = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
PPU, SS = 90.50966799187809, 3
FOOT = int(os.environ.get('FOOT', '2'))     # footprint n x n: frame sizes and anchors as the vessels' manifest uses them
FW, FH, AX, AY = [int(x) for x in os.environ['FRAME'].split(',')] if os.environ.get('FRAME') else {1: (128, 160, 64, 128), 2: (256, 224, 128, 160), 3: (384, 288, 192, 192), 4: (512, 352, 256, 224), 5: (640, 416, 320, 256), 6: (768, 480, 384, 288), 7: (896, 544, 448, 320), 8: (1024, 608, 512, 352), 9: (1152, 672, 576, 384), 10: (1280, 736, 640, 416)}[FOOT]   # FRAME=w,h,ax,ay overrides (VFACTORY geo copy)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
for o in list(bpy.data.objects):     # HIDE=missile_L,missile_R : fired missiles leave the pods
    if o.name in [h for h in os.environ.get('HIDE', '').split(',') if h]: bpy.data.objects.remove(o)
KEEP = [k for k in os.environ.get('KEEP', '').split(',') if k]     # KEEP=missile_R : render only these, centred on the origin
if KEEP:
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and o.name not in KEEP: bpy.data.objects.remove(o)
# RECOILX=obj:xthresh:dist  : vertices of obj with world x > xthresh slide back dist along -x (a barrel kicking)
for spec in [r for r in os.environ.get('RECOILX', '').split(';') if r]:
    sp_ = spec.split(':'); on, th, dist = sp_[0], float(sp_[1]), float(sp_[2]); ylo, yhi = (float(sp_[3]), float(sp_[4])) if len(sp_) > 4 else (-1e9, 1e9); ob = bpy.data.objects.get(on)   # optional y band: one barrel of a pair
    if ob:
        mw = ob.matrix_world; inv = mw.inverted()
        for v in ob.data.vertices:
            w = mw @ v.co
            if w.x > th and ylo <= w.y <= yhi: v.co = inv @ (w - Vector((dist, 0, 0)))
        ob.data.update()
# PART=hull|turret with TURRET=obj1,obj2 and TPIV=x,y,z : the turret is its own layer, rendered about its own pivot
PART = os.environ.get('PART', ''); TUR = [t for t in os.environ.get('TURRET', '').split(',') if t]
TPIV = Vector([float(x) for x in os.environ['TPIV'].split(',')]) if os.environ.get('TPIV') else None
if PART == 'hull':
    for o in list(bpy.data.objects):
        if o.name in TUR or o.get('on_turret'): bpy.data.objects.remove(o)
elif PART == 'turret':
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and o.name not in TUR and not (o.name.startswith('decal') and o.get('on_turret')): bpy.data.objects.remove(o)
    for o in bpy.data.objects:
        if o.type == 'MESH': o.matrix_world = Matrix.Translation(-TPIV) @ o.matrix_world
objs = [o for o in bpy.data.objects if o.type == 'MESH']
if KEEP:
    pts = np.array([o.matrix_world @ v.co for o in objs for v in o.data.vertices]); c = (pts.min(0) + pts.max(0)) / 2
    for o in objs: o.location = o.location - Vector(c)
# RECOIL=top,bot : barrels slide back along -X by that many model units (top barrel z>13.7, bottom z<13.7), both ball turrets
RC = [float(x) for x in os.environ.get('RECOIL', '').split(',') if x]
if RC:
    for ln in ('laser_L', 'laser_R'):
        if ln not in bpy.data.objects: continue
        las = bpy.data.objects[ln]
        for v in las.data.vertices:
            if v.co.x > -1.4 and abs(v.co.y) > 3: v.co.x -= RC[0] if v.co.z > 13.7 else RC[1]
        las.data.update()
root = bpy.data.objects.new('root', None); sc.collection.objects.link(root)
for o in objs: o.parent = root
root.scale = (SCALE,) * 3; root.rotation_euler = (0, 0, math.radians(180 - 45 * hk))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = FW / PPU; cam.data.clip_start = 0.01; cam.data.clip_end = 200
e = math.radians(float(os.environ.get('ELEV', '30'))); d = Vector((math.cos(e) / math.sqrt(2), math.cos(e) / math.sqrt(2), math.sin(e)))
if e > math.radians(89.9): d = Vector((1e-4, 1e-4, 1)).normalized()
cam.location = d * 50; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
cam.data.shift_y = (AY - FH / 2) / FW; cam.data.shift_x = (FW / 2 - AX) / FW
sc.render.resolution_x, sc.render.resolution_y = FW * SS, FH * SS
sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.film_transparent = True; sc.display.render_aa = 'OFF'
sc.display.shading.show_cavity = False; sc.display.shading.show_object_outline = False; sc.display.shading.show_specular_highlight = False
sc.view_settings.view_transform = 'Standard'
def shot(tag):
    p = os.path.join(outdir, f'_{tag}.png'); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
    return np.asarray(Image.open(p).convert('RGBA')).astype(np.float32) / 255
os.makedirs(outdir, exist_ok=True)
sh = sc.display.shading
sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; A = shot('albedo')
sh.color_type = 'OBJECT'
for o in objs: o.color = (1, 0, 0, 1) if o.name.startswith('decal') else ((0, 1, 0, 1) if o.name.startswith('missile') else (0, 0, 1, 1))
B = shot('mask')
_mc = {}
for mt in bpy.data.materials: _mc[mt.name] = tuple(mt.diffuse_color); mt.diffuse_color = (0, 1, 0, 1) if mt.name.startswith('missile_fin') else ((0, 0, 1, 1) if mt.name.startswith('missile_tip') else (0, 0, 0, 1))
sh.light = 'FLAT'; sh.color_type = 'MATERIAL'; Mi = shot('matid')
for mt in bpy.data.materials: mt.diffuse_color = _mc[mt.name]
if os.environ.get('SHADE') == 'detail':                  # John 15 Nov 19:49 'more detail ... it's just flat': cavity (edges light, crevices dark) in the light pass
    sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.cavity_ridge_factor = 1.4; sh.cavity_valley_factor = 1.6; sh.curvature_ridge_factor = 1.2; sh.curvature_valley_factor = 1.2
    sh.show_specular_highlight = True
sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.8, 0.8, 0.8); L = shot('light')
sh.show_cavity = False; sh.show_specular_highlight = False
alpha = A[..., 3] > 0.5
key = (np.abs(A[..., 0] - 1) < 0.02) & (A[..., 1] < 0.02) & (np.abs(A[..., 2] - 1) < 0.02)
dec = (B[..., 0] > 0.5) & (B[..., 2] < 0.5) & alpha
# a decal pixel that is key colour shows the hull underneath: take it from a render without decals
if (dec & key).any():
    for o in objs:
        if o.name.startswith('decal'): o.hide_render = True
    sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; A0 = shot('albedo0')
    for o in objs: o.hide_render = False
    A = np.where((dec & key)[..., None], A0, A); alpha = A[..., 3] > 0.5
lum = L[..., :3].mean(-1)
lv = lum[alpha]; q1, q2 = np.percentile(lv, 30), np.percentile(lv, 70) if lv.size else (0, 0)
tone = np.where(lum < q1, 0.72, np.where(lum < q2, 0.88, 1.0))
if os.environ.get('SHADE') == 'soft':                     # more tone steps so planes and rounded edges read (John 15 Nov 16:44)
    lo_, hi_ = (np.percentile(lv, 5), np.percentile(lv, 97)) if lv.size else (0, 1); t_ = np.clip((lum - lo_) / max(hi_ - lo_, 1e-6), 0, 1)
    tone = 0.60 + 0.42 * np.round(t_ * 6) / 6
if os.environ.get('SHADE') == 'detail':                  # continuous tone, no banding, so small parts keep their modelling
    lo_, hi_ = (np.percentile(lv, 3), np.percentile(lv, 99)) if lv.size else (0, 1); tone = 0.42 + 0.78 * np.clip((lum - lo_) / max(hi_ - lo_, 1e-6), 0, 1)
col = A[..., :3] * tone[..., None]
# missiles (John 23:52 'shade it so we can see it's a missile'): their own smooth shading, dark underside to a lit top
# with a highlight streak along the body, instead of the hull's three flat tones
mis = (B[..., 1] > 0.5) & (B[..., 0] < 0.5) & (B[..., 2] < 0.5) & alpha
if mis.any():
    fin = mis & ((Mi[..., 1] > 0.5) | (Mi[..., 2] > 0.5)); body = mis & ~fin
    lm = lum[mis]; lo_, hi_ = np.percentile(lm, 5), np.percentile(lm, 97); tn = np.clip((lum - lo_) / max(hi_ - lo_, 1e-3), 0, 1)
    # body: stays near black, a thin grey glint along the top
    shb = 0.80 + 0.50 * tn + 1.8 * (tn > 0.95)
    # fins: flat plates, so each faces the light differently: lit fins come up dark grey, shadowed fins go to black
    shf = 0.35 + 1.4 * tn + 3.5 * (tn > 0.80)
    col[body] = np.clip(A[..., :3][body] * shb[body][:, None], 0, 1)
    col[fin] = np.clip(A[..., :3][fin] * shf[fin][:, None], 0, 1)
# outline: silhouette + creases (jumps in the raw light) + decal edges
gx = ndi.sobel(ndi.gaussian_filter(lum, 0.6), 1); gy = ndi.sobel(ndi.gaussian_filter(lum, 0.6), 0)
crease = (np.hypot(gx, gy) > 0.55) & alpha
sil = alpha & ~ndi.binary_erosion(alpha, iterations=2)
ink = ndi.binary_dilation(crease, iterations=1) | sil
col[ink] = col[ink] * 0.25 + np.array([0.12, 0.12, 0.13]) * 0.75
col = np.clip(col, 0, 1)                                  # tone runs to 1.2: pale paint overflowed uint8 and wrapped (mint -> magenta, pale blue -> lime specks)
out = np.dstack([col * alpha[..., None], alpha.astype(np.float32)])
# downsample x3 with premultiplied alpha
im = Image.fromarray((out * 255).astype(np.uint8), 'RGBA').resize((FW, FH), Image.LANCZOS)
a = np.asarray(im).astype(np.float32); rgb = a[..., :3] / np.maximum(a[..., 3:4] / 255, 1e-3)
fin = np.dstack([np.clip(rgb, 0, 255), a[..., 3]]).astype(np.uint8)
fp = os.path.join(outdir, f'{name}_{look}_{HEAD[hk]}.png' if look else f'{name}_{HEAD[hk]}.png'); Image.fromarray(fin, 'RGBA').save(fp)
from bpy_extras.object_utils import world_to_camera_view
bpy.context.view_layer.update()
MZ = os.environ.get('MUZZLES', 'muzzle_L_top:2.9,5.4,14.12;muzzle_L_bot:2.9,5.4,13.28;muzzle_R_top:2.9,-5.4,14.12;muzzle_R_bot:2.9,-5.4,13.28')
PTS = [(a.split(':')[0], tuple(float(x) for x in a.split(':')[1].split('@')[0].split(','))) for a in MZ.split(';') if a]
MDIR = {a.split(':')[0]: tuple(float(x) for x in a.split('@')[1].split(',')) for a in MZ.split(';') if '@' in a}   # name:x,y,z@dx,dy,dz = barrel not along +x
if TPIV is not None and PART == 'turret': PTS = [(n_, tuple(Vector(p_) - TPIV)) for n_, p_ in PTS]
if TPIV is not None and PART == 'hull': PTS = [('turret_pivot', tuple(TPIV))]
for nm_, p_ in PTS:
    wp = root.matrix_world @ Vector(p_); q = world_to_camera_view(sc, cam, wp)
    hit_ = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), wp + d * 0.02, d)[0]       # anything between the muzzle and the camera hides its flash
    dd_ = MDIR.get(nm_, (1, 0, 0)); q2 = world_to_camera_view(sc, cam, root.matrix_world @ Vector((p_[0] + dd_[0], p_[1] + dd_[1], p_[2] + dd_[2])))      # screen direction the barrel points
    print('MUZZLE', nm_, round(q.x * FW, 1), round((1 - q.y) * FH, 1), 'hidden' if hit_ else 'visible', round((q2.x - q.x) * FW, 2), round((q.y - q2.y) * FH, 2))
ys, xs = np.where(fin[..., 3] > 8); print(fp, 'bbox x', xs.min(), xs.max(), 'y', ys.min(), ys.max())
for t in ('albedo', 'mask', 'light', 'albedo0', 'matid'):
    p = os.path.join(outdir, f'_{t}.png')
    if os.path.exists(p): os.remove(p)
