"""Render a rocket or missile body in 8 screen directions, cartoon finish, for the projectile sheet.

The model is used for its SHAPE only: every material it ships with is thrown away and the body is
painted in flat bands along its length (nose / body / tail), one cel shadow tone from a key light
at the camera's upper left, and a dark ink outline - the same finish as the soldiers
(render_char.py + soldier_ink.py), done simply because a projectile is a few dozen pixels.

The camera is the battlescape's: orthographic, 30 degrees down (2:1 on the ground). The engine
picks a head by the direction the shot travels ON SCREEN, in eight equal 45-degree sectors,
0 = nose up and clockwise (Map.cpp, bulletDirectional). So each frame is the body lying level and
turned until its projected axis points exactly at that screen angle - a body flying "up the
screen" is flying away from the camera and is drawn foreshortened, as it would be.

Model files never enter the repo (licences vary); pass the path.

usage: python3 render_projectile.py <model.fbx|.glb> <out_dir> --object NAME --nose +
         --bands "0.18:200,40,30;0.80:120,130,80;1:60,60,58" [--len 40] [--cell 48]
  bands run nose -> tail: "fraction:r,g,b;..." each colour up to that fraction of the length.
writes <out_dir>/dir0.png .. dir7.png (RGBA, cell x cell, body centred) and a contact sheet.
"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix
from PIL import Image
from scipy import ndimage as ndi
from bpy_extras.object_utils import world_to_camera_view

MODEL, OUT = sys.argv[1], sys.argv[2]


def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


OBJ = arg('--object')
NOSE = arg('--nose', '+')             # which end of the long axis is the nose: + or -
BANDS = [(float(f), tuple(int(c) for c in rgb.split(','))) for f, rgb in
         (b.split(':') for b in arg('--bands', '0.2:200,40,30;0.85:220,220,210;1:70,70,70').split(';'))]
LEN = int(arg('--len', 40))           # body length in px when it lies across the screen
CELL = int(arg('--cell', 48))
SS = 8                                # supersample
INK = np.array([28, 22, 20], np.float32)
EL = math.radians(30)
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
if MODEL.lower().endswith(('.glb', '.gltf')):
    bpy.ops.import_scene.gltf(filepath=MODEL)
else:
    bpy.ops.import_scene.fbx(filepath=MODEL)
sc = bpy.context.scene
meshes = [o for o in sc.objects if o.type == 'MESH']
keep = [o for o in meshes if (OBJ is None or o.name == OBJ)]
assert keep, 'no mesh %r in %s (have %s)' % (OBJ, MODEL, [o.name for o in meshes])
for o in list(sc.objects):
    if o not in keep:
        bpy.data.objects.remove(o, do_unlink=True)

# one mesh, world transforms baked in, centred, nose on +X, length 1
bpy.ops.object.select_all(action='DESELECT')
for o in keep:
    o.select_set(True)
bpy.context.view_layer.objects.active = keep[0]
if len(keep) > 1:
    bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
V = np.array([v.co[:] for v in body.data.vertices])
# The long axis is the vertices' principal axis, measured AFTER the import's own transforms are
# baked in - an FBX comes in Y-up and its parts can sit at any angle (the RPG-7's round lies
# diagonally in that file), so neither the stated dimensions nor the bounding box can be trusted.
# --nose says which end is the front: + is the end the axis points to once its largest component is
# made positive.
c0 = V.mean(0)
w, vec = np.linalg.eigh(np.cov((V - c0).T))
ax = vec[:, np.argmax(w)]
if ax[np.argmax(np.abs(ax))] < 0:
    ax = -ax
if NOSE[0] == '-':
    ax = -ax
t = (V - c0) @ ax
length = t.max() - t.min()
centre = c0 + ax * (t.max() + t.min()) / 2
FAT = float(arg('--fat', 1.0))       # cartoon licence: thicken the body across its length so it reads at sprite size
to_x = Vector(ax).rotation_difference(Vector((1, 0, 0))).to_matrix()
M = (Matrix.Diagonal((1, FAT, FAT, 1)) @ to_x.to_4x4() @ Matrix.Scale(1.0 / length, 4)
     @ Matrix.Translation(Vector(-centre)))
body.data.transform(M)
body.data.update()

# flat bands along the length: x = +0.5 is the nose, -0.5 the tail
mat = bpy.data.materials.new('flat')
mat.use_nodes = True
nt = mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
tc = nt.nodes.new('ShaderNodeTexCoord')
sep = nt.nodes.new('ShaderNodeSeparateXYZ')
mp = nt.nodes.new('ShaderNodeMapRange')          # x: +0.5 (nose) -> 0, -0.5 (tail) -> 1
mp.inputs['From Min'].default_value = 0.5
mp.inputs['From Max'].default_value = -0.5
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.interpolation = 'CONSTANT'
els = ramp.color_ramp.elements
start = 0.0
for i, (f, rgb) in enumerate(BANDS):
    e = els[i] if i < len(els) else els.new(start)
    e.position = start
    e.color = tuple((c / 255.0) ** 2.2 for c in rgb) + (1,)
    start = f
em = nt.nodes.new('ShaderNodeEmission')
out = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(tc.outputs['Object'], sep.inputs[0])
nt.links.new(sep.outputs['X'], mp.inputs['Value'])
nt.links.new(mp.outputs['Result'], ramp.inputs['Fac'])
nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
body.data.materials.clear()
body.data.materials.append(mat)

shade_mat = bpy.data.materials.new('shade')
shade_mat.use_nodes = True
bsdf = shade_mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1)
bsdf.inputs['Roughness'].default_value = 1.0

sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 8
sc.cycles.use_denoising = False
sc.cycles.max_bounces = 1
res = CELL * SS
sc.render.resolution_x = sc.render.resolution_y = res
sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'
sc.world = bpy.data.worlds.new('w')
sc.world.color = (0, 0, 0)

cam_d = bpy.data.cameras.new('cam')
cam_d.type = 'ORTHO'
cam_d.ortho_scale = CELL / LEN          # the body (length 1) spans LEN of CELL pixels when side-on
cam = bpy.data.objects.new('cam', cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
# camera looks along +Y (north) and down 30 degrees; screen right = +X
fwd = Vector((0, math.cos(EL), -math.sin(EL)))
cam.location = -fwd * 10
cam.rotation_euler = fwd.to_track_quat('-Z', 'Y').to_euler()
right = Vector((1, 0, 0))
up = right.cross(fwd).normalized() * -1
if up.z < 0:
    up = -up
sun = bpy.data.objects.new('key', bpy.data.lights.new('key', 'SUN'))
sun.data.energy = 3.0
sun.data.angle = 0.05
sc.collection.objects.link(sun)
ldir = (fwd * 0.55 - right * 0.55 + up * 0.62).normalized()   # from the camera's upper left
sun.rotation_euler = ldir.to_track_quat('-Z', 'Y').to_euler()
bpy.context.view_layer.update()     # camera matrices are stale until this, and the headings are measured through them


def render(path, override):
    bpy.context.view_layer.material_override = override
    sun.hide_render = override is None
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.context.view_layer.material_override = None
    return np.asarray(Image.open(path).convert('RGBA')).astype(np.float32)


tmp = os.path.join(OUT, '_tmp')
os.makedirs(tmp, exist_ok=True)
frames = []
for d in range(8):
    # Turn the level body until its nose, PROJECTED BY THIS CAMERA, points at 45*d degrees on
    # screen (0 = up, clockwise). Measured, not derived, so no axis convention can sneak in.
    want = 45 * d
    best = None
    for k in range(720):
        hd = math.radians(k / 2)
        nose = world_to_camera_view(sc, cam, Vector((0.5 * math.cos(hd), 0.5 * math.sin(hd), 0)))
        tail = world_to_camera_view(sc, cam, Vector((-0.5 * math.cos(hd), -0.5 * math.sin(hd), 0)))
        ang = math.degrees(math.atan2(nose.x - tail.x, nose.y - tail.y)) % 360   # camera view y is up
        err = abs((ang - want + 180) % 360 - 180)
        if best is None or err < best[0]:
            best = (err, hd)
    body.rotation_mode = 'XYZ'
    body.rotation_euler = (0, 0, best[1])
    if os.environ.get('PROJ_DEBUG'):
        bpy.context.view_layer.update()
        V2 = np.array([v.co[:] for v in body.data.vertices])
        nose_l = Vector(V2[V2[:, 0].argmax()]); tail_l = Vector(V2[V2[:, 0].argmin()])
        pn = world_to_camera_view(sc, cam, body.matrix_world @ nose_l); pt = world_to_camera_view(sc, cam, body.matrix_world @ tail_l)
        print('dir', d, 'heading', round(math.degrees(best[1]), 1), 'local x range', V2[:, 0].min().round(3), V2[:, 0].max().round(3),
              'yz', np.ptp(V2[:, 1]).round(3), np.ptp(V2[:, 2]).round(3), 'nose px', round(pn.x * CELL, 1), round((1 - pn.y) * CELL, 1), 'tail px', round(pt.x * CELL, 1), round((1 - pt.y) * CELL, 1), 'mods', [m.type for m in body.modifiers], body.data.shape_keys)
    bpy.context.view_layer.update()
    col = render(os.path.join(tmp, 'c%d.png' % d), None)
    sh = render(os.path.join(tmp, 's%d.png' % d), shade_mat)

    a = col[..., 3] / 255.0
    rgb = col[..., :3].copy()
    lum = sh[..., :3].mean(-1)
    inside = a > 0.5
    if inside.any():
        ref = np.percentile(lum[inside], 85)
        shadow = inside & (lum < ref * 0.55)
        shadow = ndi.binary_opening(shadow, iterations=2)
        rgb[shadow] *= 0.68                      # the one cel shadow tone
    img = np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8)
    small = np.asarray(Image.fromarray(img, 'RGBA').resize((CELL, CELL), Image.LANCZOS)).astype(np.float32)
    sa = small[..., 3] / 255.0
    solid = sa > 0.35
    ring = ndi.binary_dilation(solid, iterations=1) & ~solid
    outv = small.copy()
    # un-premultiply the soft edge into a hard cartoon edge, then ink round it
    outv[..., 3] = np.where(solid, 255, 0)
    outv[ring, :3] = INK
    outv[ring, 3] = 255
    frames.append(Image.fromarray(outv.clip(0, 255).astype(np.uint8), 'RGBA'))
    frames[-1].save(os.path.join(OUT, 'dir%d.png' % d))

sheet = Image.new('RGBA', (CELL * 8, CELL), (255, 0, 255, 255))
for d, f in enumerate(frames):
    sheet.alpha_composite(f, (d * CELL, 0))
sheet.resize((CELL * 8 * 4, CELL * 4), Image.NEAREST).save(os.path.join(OUT, 'contact.png'))
print('wrote 8 directions to', OUT)
