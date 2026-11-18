"""V.A.M.P. Mk II to the 1984 toy (toy pass; refs: 3DJoes mail-away Mk II photo set). Shape and markings were already done
(16 Nov); this corrects the paint: the toy's browner tan (was a pale sand), black hard top and doors (was dark slate),
black fender flares and rockers, tan hubs (were grey), black missiles (were blue-grey), black hood vents (were silver).
python3 build_mk2.py in.blend out.blend"""
import bpy, sys
SRC, OUT = sys.argv[-2:]
bpy.ops.wm.open_mainfile(filepath=SRC)
def lin(c): return tuple(((v / 255) ** 2.2) for v in c) + (1,)
def setc(name, rgb):
    m = bpy.data.materials.get(name)
    if not m: return
    m.diffuse_color = lin(rgb)
    if m.node_tree and m.node_tree.nodes.get('Principled BSDF'): m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = lin(rgb)
setc('mk2_sand', (166, 122, 78)); setc('mk2_pod_sand', (158, 114, 82)); setc('mk2_slate', (30, 30, 30))
setc('mk2_hub', (160, 117, 74)); setc('mk2_hubc', (110, 80, 52))
setc('mk2_metal', (46, 46, 46)); setc('mk2_missile', (34, 34, 36)); setc('mk2_missile_tip', (70, 72, 74))
ch = bpy.data.objects['GJCHASSIS']; names = [m.name for m in ch.data.materials]; blk = names.index('mk2_black'); sand = names.index('mk2_sand')
mw = ch.matrix_world; R = mw.to_3x3(); k = 0
for p in ch.data.polygons:                       # flares are the widest surfaces (|y| 5.92), rockers the low sides; only sand faces change
    if p.material_index != sand: continue
    c = mw @ p.center; ay = abs(c.y)
    if ay > 5.75 or (c.z < 3.2 and ay > 4.2) or (c.x > 12.2 and c.z < 3.6) or (c.x < -11.6 and c.z < 4.0):
        p.material_index = blk; k += 1
print('BLACKED', k); print('BUILT', OUT)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
