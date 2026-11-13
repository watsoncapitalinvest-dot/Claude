#!/usr/bin/env python3
"""A Generals playset as a base room (FACILITY_ART_SPEC: straight down, 192 px a square, 12 px margin,
outside corners cut back, light from the upper left).

    python3 compose_room.py model.obj out.png WxH [--rot DEG] [--floor pad|deck|none] [--fill F] [--drop a,b]

Builds what the playset does not have: a floor slab under it and a low wall around the room's edge,
then renders the lot from directly above at the room's size. The model is turned by --rot and scaled
to fill the room (--fill of the inner area). Writes an RGBA picture; the margin is transparent."""
import bpy, sys, math
from mathutils import Vector

a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
obj, out, fp = a[0], a[1], a[2]
W, H = (int(v) for v in fp.lower().split('x'))
def opt(k, d):
    return a[a.index(k) + 1] if k in a else d
rot = float(opt('--rot', 0)); floor = opt('--floor', 'pad'); fill = float(opt('--fill', 0.9))
drop = [d for d in opt('--drop', '').lower().split(',') if d]
PX = 192; M = 12
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.wm.obj_import(filepath=obj, forward_axis='Y', up_axis='Z')
meshes = []
for o in list(sc.objects):
    n = o.name.lower()
    if 'shadow' in n or any(d in n for d in drop): bpy.data.objects.remove(o); continue
    meshes.append(o)
# one pivot so the playset turns and scales as one
root = bpy.data.objects.new('root', None); sc.collection.objects.link(root)
for o in meshes: o.parent = root
root.rotation_euler = (0, 0, math.radians(rot)); bpy.context.view_layer.update()
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for o in meshes:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
# room in world units: 1 px = 1 unit at the end, so scale the model into the inner area
inner_w, inner_h = W * PX - 2 * M - 16, H * PX - 2 * M - 16
s = fill * min(inner_w / max(1e-3, mx.x - mn.x), inner_h / max(1e-3, mx.y - mn.y))
root.scale = (s, s, s)
bpy.context.view_layer.update()
ctr = (mn + mx) / 2 * s
root.location = (-ctr.x, -ctr.y, -mn.z * s + 0.5)
bpy.context.view_layer.update()

def mat(name, rgb, rough=0.9):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']; p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough
    return m
def box(name, x0, y0, x1, y1, z0, z1, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.object; o.name = name; o.scale = (x1 - x0, y1 - y0, z1 - z0); o.data.materials.append(m); return o
RW, RH = W * PX - 2 * M, H * PX - 2 * M
if floor != 'none':
    fl = {'pad': (0.42, 0.42, 0.40), 'deck': (0.36, 0.38, 0.40)}.get(floor, (0.42, 0.42, 0.40))
    box('floor', -RW / 2, -RH / 2, RW / 2, RH / 2, -2, 0, mat('floor', fl))
    wall = mat('wall', (0.22, 0.26, 0.20)); t = 8; h = 14
    box('wN', -RW / 2, RH / 2 - t, RW / 2, RH / 2, 0, h, wall); box('wS', -RW / 2, -RH / 2, RW / 2, -RH / 2 + t, 0, h, wall)
    box('wW', -RW / 2, -RH / 2, -RW / 2 + t, RH / 2, 0, h, wall); box('wE', RW / 2 - t, -RH / 2, RW / 2, RH / 2, 0, h, wall)
    # hazard stripe at the door (south wall, middle)
    haz = mat('haz', (0.85, 0.65, 0.05)); box('door', -18, -RH / 2, 18, -RH / 2 + t, 0, h + 0.5, haz)

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 32
sc.render.film_transparent = True; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = W * PX; sc.render.resolution_y = H * PX
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.8, 0.8, 0.82, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.55
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.2; sun.data.angle = math.radians(8); sun.rotation_euler = (math.radians(40), 0, math.radians(135))
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = max(W, H) * PX; cd.clip_end = 100000
cd.sensor_fit = 'HORIZONTAL' if W >= H else 'VERTICAL'
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0, 0, 5000)
sc.render.filepath = out; bpy.ops.render.render(write_still=True)

# the spec's margin and cut corners: everything outside the room plate becomes transparent
from PIL import Image, ImageDraw
im = Image.open(out).convert('RGBA'); mask = Image.new('L', im.size, 0); d = ImageDraw.Draw(mask)
x0, y0, x1, y1 = M, M, im.width - M - 1, im.height - M - 1
d.polygon([(x0 + M, y0), (x1 - M, y0), (x1, y0 + M), (x1, y1 - M), (x1 - M, y1), (x0 + M, y1), (x0, y1 - M), (x0, y0 + M)], fill=255)
a_ = im.getchannel('A'); from PIL import ImageChops
im.putalpha(ImageChops.multiply(a_, mask)); im.save(out)
print('room', out, im.size)
