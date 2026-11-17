# scale that fills an n x m footprint over all 8 headings (STORY rule), hull only (no barrels/antenna), 5% margin
import bpy, sys, math, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[1]); fx, fy = int(sys.argv[2]), int(sys.argv[3])
skip = ('turret', 'thunderclap_trailer.004')
pts = np.array([(o.matrix_world @ v.co)[:2] for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith(skip) and len(o.data.vertices) > 0 and o.dimensions.z < 12 for v in o.data.vertices])
pts -= (pts.min(0) + pts.max(0)) / 2
best = 9
for k in range(8):
    a = math.radians(45 * k); R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]]); q = pts @ R.T
    ex = np.ptp(q[:, 0]); ey = np.ptp(q[:, 1])
    lx, ly = (fx, fy) if k % 4 == 0 else (fy, fx) if k % 4 == 2 else (max(fx, fy),) * 2
    best = min(best, 0.95 * lx / ex, 0.95 * ly / ey)
s = best; print('SCALE', round(s, 5), 'hull', np.round(np.ptp(pts, 0), 2), 'fill straight', np.round(np.ptp(pts, 0) * s / [fx, fy] * 100, 1))
