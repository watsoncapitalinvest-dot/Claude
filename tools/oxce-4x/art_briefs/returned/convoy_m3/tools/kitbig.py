"""Big objects (plane, trucks, boxcars, boats) that span several cells and levels.
Model the whole object once in world metres (cell (i, j) spans x i*S..(i+1)*S, y -(j+1)*S..-j*S; i east, j south),
then cut_cells() renders one sprite per (i, j, level): the camera moves to that cell, a position pass says which
cell every pixel's surface belongs to, and only that cell's pixels (plus the ink lines next to them) are kept.
Each pixel ends up in exactly one sprite, so the pieces fit back together with no seams."""
import os, math
import bpy
import numpy as np
from mathutils import Vector, Matrix
from PIL import Image
from scipy import ndimage
import kitlib
from kitlib import S, H, K, reset

def _posmat():
    m = bpy.data.materials.new('pos'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    g = nt.nodes.new('ShaderNodeNewGeometry'); add = nt.nodes.new('ShaderNodeVectorMath'); add.operation = 'ADD'
    add.inputs[1].default_value = (100, 100, 100)
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(g.outputs['Position'], add.inputs[0]); nt.links.new(add.outputs[0], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs[0])
    return m

def _load(path):
    im = bpy.data.images.load(path); w, h = im.size
    a = np.array(im.pixels[:], np.float32).reshape(h, w, 4)[::-1]
    bpy.data.images.remove(im); return a

def cut_cells(part, cells, outdir, prefix):
    """cells: list of (i, j, lvl, name). Writes <outdir>/<prefix>_<name>.png (128x160, hard alpha)."""
    os.makedirs(outdir, exist_ok=True)
    sc, inkc, noinkc, mat = reset(); part.build(sc, inkc, noinkc, mat)
    co = sc.camera; M0 = co.matrix_world.copy(); pm = _posmat(); vl = bpy.context.view_layer
    tmp_c, tmp_p = os.path.join(outdir, '_c.png'), os.path.join(outdir, '_p.exr')
    for (i, j, lvl, name) in cells:
        co.matrix_world = Matrix.Translation(Vector((i * S, -j * S, lvl * H * K))) @ M0
        # colour + ink
        vl.material_override = None; sc.render.use_freestyle = part.ink; sc.cycles.samples = 16
        sc.render.filter_size = 1.5
        sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
        sc.render.filepath = tmp_c; bpy.ops.render.render(write_still=True)
        # position pass
        vl.material_override = pm; sc.render.use_freestyle = False; sc.cycles.samples = 1; sc.render.filter_size = 0.01
        sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
        sc.render.filepath = tmp_p; bpy.ops.render.render(write_still=True)
        col = np.array(Image.open(tmp_c).convert('RGBA'))
        pos = _load(tmp_p); hit = pos[..., 3] > 0.5
        wp = pos[..., :3] - 100.0
        x, y, z = wp[..., 0], wp[..., 1], wp[..., 2] / K
        e = 1e-3
        inside = hit & (x >= i * S - e) & (x < (i + 1) * S - e) & (y <= -j * S + e) & (y > -(j + 1) * S + e) \
                 & (z >= lvl * H - 0.02) & (z < (lvl + 1) * H - 0.02)
        # every drawn pixel takes the cell of the nearest surface pixel (ink over background, AA fringes)
        dist, (iy, ix) = ndimage.distance_transform_edt(~hit, return_indices=True)
        own = inside[iy, ix] & (dist < 10)
        # grow 3 sub-pixels into the neighbours: every cell render is the same image, so the overlap repaints
        # identical colour and closes the 1 px gaps the downscale + hard alpha would leave on the cut lines
        own = ndimage.binary_dilation(own, iterations=3) & (col[..., 3] > 0)
        col[~own] = 0
        im = Image.fromarray(col, 'RGBA').resize((128, 160), Image.LANCZOS)
        a = np.array(im); keep = a[..., 3] >= 128
        a[..., 3] = np.where(keep, 255, 0); a[~keep, :3] = 0
        Image.fromarray(a, 'RGBA').save(os.path.join(outdir, '%s_%s.png' % (prefix, name)))
    vl.material_override = None
    for f in (tmp_c, tmp_p):
        if os.path.exists(f): os.remove(f)

def occupied(part, nx, ny, nz):
    """cells whose column may hold geometry (from each face's bounding box). Empty sprites are dropped after render."""
    used = set()
    for bm in (part.bm, part.noink):
        for f in bm.faces:
            xs = [v.co.x for v in f.verts]; ys = [-v.co.y for v in f.verts]; zs = [v.co.z for v in f.verts]
            for i in range(max(0, int(min(xs) // S)), min(nx, int(max(xs) // S) + 1)):
                for j in range(max(0, int(min(ys) // S)), min(ny, int(max(ys) // S) + 1)):
                    for l in range(max(0, int(min(zs) // H)), min(nz, int(max(zs) // H) + 1)):
                        used.add((i, j, l))
    return sorted(used, key=lambda t: (t[2], t[1], t[0]))
