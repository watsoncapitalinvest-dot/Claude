import bpy,sys
from PIL import Image
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2])
def mat(name,rgb):
    f=f'/home/claude/rt/v5/whale/col_{name}.png'; Image.new('RGB',(4,4),rgb).save(f)
    m=bpy.data.materials.new(name); m.use_nodes=True; tn=m.node_tree.nodes.new('ShaderNodeTexImage'); tn.image=bpy.data.images.load(f); tn.interpolation='Closest'
    m.node_tree.links.new(tn.outputs['Color'],m.node_tree.nodes['Principled BSDF'].inputs['Base Color']); return m
# toy photos 19:32: olive turret tubs, dark gunmetal twin guns, olive Pounder barrels, white SAMs, black depth-charge drums
OL=mat('wh_olive',(88,96,64)); GM=mat('wh_gunmetal',(48,50,48)); WH=mat('wh_missile2',(232,232,226)); BK=mat('wh_dc',(34,34,36))
import numpy as np
for o in bpy.data.objects:
    n=o.name
    if n.startswith(('TURRET','CANNON','MSL','DC_')):
        mw=o.matrix_world; me=o.data; me.materials.clear()
        if n.startswith('TURRET'):
            me.materials.append(OL); me.materials.append(GM)
            for p in me.polygons: p.material_index = 1 if (mw@p.center).x>1.1 or (mw@p.center).z>16.6 else 0
        elif n.startswith('CANNON'):
            me.materials.append(OL); me.materials.append(GM)
            for p in me.polygons: p.material_index = 1 if (mw@p.center).x>12.0 else 0
        elif n.startswith('MSL'): me.materials.append(WH)
        else: me.materials.append(BK)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1],compress=True)
