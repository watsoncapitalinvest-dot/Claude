import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
fbx, out, R = argv[0], argv[1], int(argv[2]) if len(argv) > 2 else 2048
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16
imgs = {}
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    for slot in o.material_slots:
        m = slot.material; nt = m.node_tree
        nimg = None
        for n in nt.nodes:
            if n.type == 'TEX_IMAGE' and n.image and 'normal' in (n.image.name + str(n.image.filepath)).lower(): nimg = n.image
        nt.nodes.clear()
        outn = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfDiffuse'); bs.inputs[0].default_value = (1, 1, 1, 1)
        nt.links.new(bs.outputs[0], outn.inputs[0])
        if nimg:
            nimg.colorspace_settings.name = 'Non-Color'
            tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = nimg
            nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs[0].default_value = 2.4
            nt.links.new(tn.outputs[0], nm.inputs[1]); nt.links.new(nm.outputs[0], bs.inputs['Normal'])
        im = imgs.setdefault(m.name, bpy.data.images.new('bake_' + m.name, R, R, float_buffer=True))
        tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = im; nt.nodes.active = tb
    print('normal map:', o.name, bool(nimg))
def sun(d, e):
    l = bpy.data.lights.new('s', 'SUN'); l.energy = e; ob = bpy.data.objects.new('s', l); sc.collection.objects.link(ob)
    ob.rotation_euler = Vector(d).to_track_quat('-Z', 'Y').to_euler()
# Mixamo in Blender faces -Y; key from front-left-above
sun((0.45, 0.6, -0.66), 2.5); sun((-0.45, -0.6, -0.66), 1.2)
w = bpy.data.worlds.new('w'); sc.world = w
for o in bpy.data.objects: o.select_set(o.type == 'MESH')
bpy.context.view_layer.objects.active = [o for o in bpy.data.objects if o.type == 'MESH'][0]
sc.render.bake.use_pass_direct = True; sc.render.bake.use_pass_indirect = False; sc.render.bake.use_pass_color = False
sc.render.bake.margin = 8
bpy.ops.object.bake(type='DIFFUSE')
import numpy as np
for k, im in imgs.items():
    a = np.array(im.pixels[:], dtype=np.float32).reshape(R, R, 4)[::-1, :, :3].mean(-1); np.save(out + '_' + k + '.npy', a); print('baked', k, a.max())
