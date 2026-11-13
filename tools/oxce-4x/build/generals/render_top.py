#!/usr/bin/env python3
"""Render an OBJ (from w3d2obj.py) straight down and at a 3/4 check angle.

    python3 render_top.py model.obj out_prefix [size_px] [--keep name,...] [--drop name,...]

Writes <out_prefix>_top.png (orthographic, straight down, transparent background, light from the
upper left as FACILITY_ART_SPEC asks) and <out_prefix>_iso.png (a quick look at the model).
Objects whose name contains 'shadow' are removed (Generals' shadow volumes)."""
import bpy, sys, math, os
from mathutils import Vector

args = sys.argv[1:]
obj, prefix = args[0], args[1]
size = int(args[2]) if len(args) > 2 and args[2].isdigit() else 768
drop = []
if '--drop' in args: drop = args[args.index('--drop') + 1].lower().split(',')

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.wm.obj_import(filepath=obj, forward_axis='Y', up_axis='Z')
for o in list(sc.objects):
    n = o.name.lower()
    if 'shadow' in n or any(d and d in n for d in drop):
        bpy.data.objects.remove(o)
# flat textures: emission-ish shading so the playset paint reads as paint
for m in bpy.data.materials:
    if not m.use_nodes: continue
    p = m.node_tree.nodes.get('Principled BSDF')
    if p:
        p.inputs['Roughness'].default_value = 0.8
        if 'Specular IOR Level' in p.inputs: p.inputs['Specular IOR Level'].default_value = 0.1
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for o in sc.objects:
    if o.type != 'MESH': continue
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
ctr = (mn + mx) / 2; ext = max(mx.x - mn.x, mx.y - mn.y)
print('bounds', tuple(round(v, 1) for v in mn), tuple(round(v, 1) for v in mx))

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 24
sc.render.film_transparent = True; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.75, 0.75, 0.78, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.5; sun.rotation_euler = (math.radians(35), 0, math.radians(135))   # from the upper left of the picture
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ext * 1.02
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (ctr.x, ctr.y, mx.z + 100); cam.rotation_euler = (0, 0, 0)
cd.clip_end = 10000
sc.render.filepath = prefix + '_top.png'; bpy.ops.render.render(write_still=True)
cd.ortho_scale = ext * 1.5
d = ext * 2
cam.location = (ctr.x + d * 0.7, ctr.y - d * 0.7, ctr.z + d * 0.8)
cam.rotation_euler = (math.radians(55), 0, math.radians(45))
sc.render.filepath = prefix + '_iso.png'; bpy.ops.render.render(write_still=True)
