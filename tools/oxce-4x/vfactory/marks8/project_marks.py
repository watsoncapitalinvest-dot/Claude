"""John's explosion marks in all 8 headings (John 18 Nov 14:45 "yes": every craft dies facing the way it flew; the game draws the
death). His marks were clicked on each craft's damaged picture at heading E. This finds each click ON THE 3D MODEL (a ray through
that pixel with the renderer's own camera - gen/render.py -> ttt/tools/render_vehicle.py: ortho, 30 deg, PPU 90.50967, root turned
180 - 45k deg) and projects the hit into all 8 headings with the same camera. Output per craft: for each heading N..NW, each mark's
pixel offset from the frame anchor (+x right, +y down) at the package's 4x frame, and whether the camera sees it.
python3 -I project_marks.py <source.blend> <scale> <foot_frame> <hide,objs> <json in: px of the clicks at E in frame coords> <json out>"""
import bpy, sys, json, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[-6:]
blend, SCALE, FOOT, HIDE, JIN, JOUT = a[0], float(a[1]), int(a[2]), [h for h in a[3].split(',') if h], a[4], a[5]
PPU = 90.50967
FW, FH, AX, AY = {1: (128, 160, 64, 128), 2: (256, 224, 128, 160), 3: (384, 288, 192, 192), 4: (512, 352, 256, 224), 5: (640, 416, 320, 256), 6: (768, 480, 384, 288), 7: (896, 544, 448, 320), 8: (1024, 608, 512, 352), 9: (1152, 672, 576, 384), 10: (1280, 736, 640, 416)}[FOOT]
bpy.ops.wm.open_mainfile(filepath=blend); sc = bpy.context.scene
for o in list(bpy.data.objects):
    if any(o.name == h or (h.endswith('*') and o.name.startswith(h[:-1])) for h in HIDE): bpy.data.objects.remove(o)
objs = [o for o in bpy.data.objects if o.type == 'MESH']
root = bpy.data.objects.new('root', None); sc.collection.objects.link(root)
for o in objs: o.parent = root                                       # exactly as render_vehicle.py does it
root.scale = (SCALE,) * 3
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = FW / PPU; cam.data.clip_start = 0.01; cam.data.clip_end = 200
e = math.radians(30); d = Vector((math.cos(e) / math.sqrt(2), math.cos(e) / math.sqrt(2), math.sin(e)))
cam.location = d * 50; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
cam.data.shift_y = (AY - FH / 2) / FW; cam.data.shift_x = (FW / 2 - AX) / FW
sc.render.resolution_x, sc.render.resolution_y = FW, FH
def turn(k): root.rotation_euler = (0, 0, math.radians(180 - 45 * k)); bpy.context.view_layer.update()
def px(w): q = world_to_camera_view(sc, cam, w); return Vector((q.x * FW, (1 - q.y) * FH))
# the camera is orthographic: pixel -> world point on the plane through the origin is linear
bpy.context.view_layer.update()                                     # the camera's matrix is stale until the scene updates
R = cam.matrix_world.to_3x3(); ux, uy = R @ Vector((1, 0, 0)), R @ Vector((0, 1, 0))
p0, p1, p2 = px(Vector()), px(ux), px(uy)
def world_at(x, y):
    M = [[p1.x - p0.x, p2.x - p0.x], [p1.y - p0.y, p2.y - p0.y]]; det = M[0][0] * M[1][1] - M[0][1] * M[1][0]
    bx, by = x - p0.x, y - p0.y; s = (bx * M[1][1] - by * M[0][1]) / det; t = (M[0][0] * by - M[1][0] * bx) / det
    return ux * s + uy * t
def hit(x, y):
    o = world_at(x, y) + d * 100; r = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), o, -d)
    return r[1] if r[0] else None
clicks = json.load(open(JIN)); turn(2); inv = root.matrix_world.inverted(); out = {'frame': [FW, FH], 'anchor': [AX, AY], 'marks': []}
if isinstance(clicks, dict) and 'auto' in clicks:
    # John 14:58 "just try to match the explosion marks as best as possible, lock them into the model and it will turn with the model":
    # VFACTORY places them on the hull itself (model +x = bow): 1 small on the deck aft, starboard; 2 regular on the deck forward, port;
    # D big in the middle of the hull at deck height (not on a mast or periscope tip)
    import numpy as np
    V = np.array([(inv @ (o.matrix_world @ v.co))[:] for o in objs if not o.name.startswith('decal') for v in o.data.vertices])   # model (root-local) coords
    lo, hi = V.min(0), V.max(0); L, Wd = hi[0] - lo[0], hi[1] - lo[1]; deck = lo[2] + 0.85 * (hi[2] - lo[2])   # only masts/periscopes stick above this
    cx0, cy0 = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    def top(x, y):                                                  # the hull's top surface under (x, y), never above the deck line;
        for t in [i / 20 for i in range(21)]:                       # off the hull (fins, gaps) -> slide in toward the middle until it lands
            xx, yy = x + (cx0 - x) * t, y + (cy0 - y) * t
            o = root.matrix_world @ Vector((xx, yy, hi[2] + 50)); dn = (root.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
            r = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), o, dn)
            if r[0]:
                h = inv @ r[1]
                if h.z <= deck: return h
                # hit something tall (a mast): take the deck under it if the hull is there
                r2 = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), root.matrix_world @ Vector((xx, yy, deck)), dn)
                if r2[0]: return inv @ r2[1]
        return Vector((x, y, deck))
    model = [(top(lo[0] + 0.22 * L, -0.28 * Wd), 's'), (top(lo[0] + 0.70 * L, 0.24 * Wd), 'r'), (top(cx0, cy0), 'b')]
    for loc, size in model:
        per = []
        for k in range(8):
            turn(k); w = root.matrix_world @ loc; p = px(w)
            per.append([round(p.x - AX, 1), round(p.y - AY, 1), not sc.ray_cast(bpy.context.evaluated_depsgraph_get(), w + d * 0.05, d)[0]])
        out['marks'].append({'size': size, 'model': [round(v, 3) for v in loc], 'placed_by': 'VFACTORY on the model (John 14:58)', 'headings': per})
    json.dump(out, open(JOUT, 'w'), indent=1); print('MARKS8', JOUT, 'auto'); sys.exit(0)
for (x, y, size) in clicks:
    turn(2); h = hit(x, y); miss = 0                                # back to heading E for every click
    if h is None:                                                   # clicked a hair off the model: nearest hit in a growing ring
        for r in range(1, 25):
            for t in range(0, 360, 15):
                h = hit(x + r * math.cos(math.radians(t)), y + r * math.sin(math.radians(t)))
                if h is not None: miss = r; break
            if h is not None: break
    if h is None: out['marks'].append({'size': size, 'error': 'no model under the click'}); continue
    loc = inv @ h; per = []; back = None
    for k in range(8):
        turn(k); w = root.matrix_world @ loc; p = px(w)
        seen = not sc.ray_cast(bpy.context.evaluated_depsgraph_get(), w + d * 0.05, d)[0]
        per.append([round(p.x - AX, 1), round(p.y - AY, 1), seen])
        if k == 2: back = (p - Vector((x, y))).length
    out['marks'].append({'size': size, 'model': [round(v, 3) for v in loc], 'snap_px': miss, 'check_E_px': round(back, 2), 'headings': per})
json.dump(out, open(JOUT, 'w'), indent=1); print('MARKS8', JOUT, [(m.get('snap_px'), m.get('check_E_px')) for m in out['marks']])
