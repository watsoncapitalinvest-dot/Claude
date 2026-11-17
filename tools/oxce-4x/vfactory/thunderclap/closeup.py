# side + 3/4 close-ups of the roof / turret seat
import bpy, sys, mathutils, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[1]); sc = bpy.context.scene
t = bpy.data.objects['turret']; P = np.array([t.matrix_world @ v.co for v in t.data.vertices]); c = (P.min(0) + P.max(0)) / 2; c[2] -= 8; s = np.ptp(P, 0).max() * 1.5
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 500
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); cam.data.type = 'ORTHO'; cam.data.ortho_scale = s; cam.data.clip_end = 1e5; sc.collection.objects.link(cam); sc.camera = cam
from PIL import Image
ims = []
for d in ((0, -1, 0.08), (0, 1, 0.08), (1, -1, 0.35)):
    d = mathutils.Vector(d).normalized(); cam.location = mathutils.Vector(c) + d * s * 4; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = '/tmp/cu.png'; bpy.ops.render.render(write_still=True); ims.append(Image.open('/tmp/cu.png').convert('RGB'))
S = Image.new('RGB', (1500, 500)); [S.paste(im, (k * 500, 0)) for k, im in enumerate(ims)]; S.save(sys.argv[2])
