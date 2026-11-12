"""Build a civilian .blend from a Mixamo FBX, in the flat cartoon finish, for render_char.py.

    python3 build_civ.py --fbx Ch20_nonPBR.fbx --name Ch20 --height 1.78 --out /tmp/claude-0/ws/civ/Ch20.blend
        [--tex /tmp/claude-0/ws/civ/flat] [--k 8]

What it does:
  - one armature, bones and vertex groups renamed mixamorigN: -> mixamorig:
  - eyelashes dropped (their meshes, or their material's faces on a single-mesh body)
  - scaled (armature scale) so the rest pose stands --height metres
  - each material's base texture flattened by flatten.py (the FBX textures are
    unpacked to --tex/raw/, outside the repo), then a flat emission over it
  - hair materials (name contains 'hair'): cut out by the card alpha, and carry their
    own IDSWITCH with id 1 (hair, for the ink). Every other material has no IDSWITCH,
    so render_char.py adds its own per limb x material.
  - multi-mesh models: UV islands used by clothing meshes are passed to flatten.py as
    never-skin (khaki trousers otherwise fall in the skin colour range)
No clip, no camera, no gun. Textures are packed into the .blend.
Hair colour for the ink (HAIR=) is taken from the test render by contact_sheet.py
("hair": "auto"), not from the texture: Mixamo hair sheets hold several hair variants.
"""
import bpy, bmesh, sys, os, re, subprocess
import numpy as np


def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


FBX = arg('--fbx'); NAME = arg('--name'); OUT = arg('--out')
HEIGHT = float(arg('--height', '1.75')); K = arg('--k', '8')
TEX = arg('--tex', '/tmp/claude-0/ws/civ/flat')
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(TEX, 'raw', NAME); os.makedirs(RAW, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX)
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
assert len(arms) == 1, 'expected one armature, got %d' % len(arms)
arm = arms[0]; arm.name = 'Armature'
PFX = re.compile(r'mixamorig\d*:')
for b in arm.data.bones: b.name = PFX.sub('mixamorig:', b.name)
for o in [o for o in bpy.data.objects if o.type not in ('MESH', 'ARMATURE')]: bpy.data.objects.remove(o)


def is_lash(s): return 'eyel' in s.lower() or 'lash' in s.lower()


meshes = []
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    if is_lash(o.name) or not any(m.type == 'ARMATURE' for m in o.modifiers):
        print('dropped mesh', o.name); bpy.data.objects.remove(o); continue
    for vg in o.vertex_groups: vg.name = PFX.sub('mixamorig:', vg.name)
    for m in o.modifiers:
        if m.type == 'ARMATURE': m.object = arm
    lash = [i for i, m in enumerate(o.data.materials) if m and is_lash(m.name)]
    if lash:
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in lash], context='FACES')
        bm.to_mesh(o.data); bm.free()
        for i in sorted(lash, reverse=True): o.data.materials.pop(index=i)
        print('dropped lash faces on', o.name)
    meshes.append(o)


def world_z(o):
    M = np.array(o.matrix_world); co = np.empty(len(o.data.vertices) * 3, np.float32)
    o.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    return co @ M[:3, :3].T + M[:3, 3]


arm.data.pose_position = 'REST'; bpy.context.view_layer.update()
h0 = max(world_z(o)[:, 2].max() for o in meshes)
z0 = min(world_z(o)[:, 2].min() for o in meshes)
arm.scale = arm.scale * (HEIGHT / h0); bpy.context.view_layer.update()
h1 = max(world_z(o)[:, 2].max() for o in meshes)
print('height %.3f -> %.3f (feet at %.3f)' % (h0, h1, z0 * HEIGHT / h0))


def save_px(im, path, alpha_from=None):
    """write a Blender image's pixels (as stored, sRGB) to png; alpha_from: an opacity image (grey)"""
    w, h = im.size; px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
    a = px.reshape(h, w, 4)[::-1].copy()
    if alpha_from is not None and alpha_from != im:
        w2, h2 = alpha_from.size; p2 = np.empty(w2 * h2 * 4, np.float32); alpha_from.pixels.foreach_get(p2)
        p2 = p2.reshape(h2, w2, 4)[::-1]
        op = p2[..., 3] if (p2[..., 3] < 0.5).mean() > 0.001 else p2[..., :3].mean(-1)
        if op.shape != a.shape[:2]:
            from PIL import Image
            op = np.asarray(Image.fromarray((op * 255).astype(np.uint8)).resize((w, h))) / 255.0
        a[..., 3] = op
    from PIL import Image
    Image.fromarray((a * 255 + 0.5).clip(0, 255).astype(np.uint8), 'RGBA').save(path)


def links_of(m):
    base = alpha = None
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            for inp in ('Base Color', 'Alpha'):
                if n.inputs[inp].links:
                    fn = n.inputs[inp].links[0].from_node
                    if getattr(fn, 'image', None) is not None:
                        if inp == 'Base Color': base = fn.image
                        else: alpha = fn.image
    return base, alpha


def id_emission(nt, idv):
    comb = nt.nodes.new('ShaderNodeCombineColor'); comb.inputs[0].default_value = idv
    camd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 8.0; mr.inputs['From Max'].default_value = 12.0
    nt.links.new(camd.outputs['View Z Depth'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], comb.inputs[1])
    ei = nt.nodes.new('ShaderNodeEmission'); nt.links.new(comb.outputs[0], ei.inputs['Color']); return ei


def uv_mask(m, objs, size=1024):
    """PIL 'L' image, white over the UV faces of material m on the given meshes (None if none)"""
    from PIL import Image, ImageDraw
    img = Image.new('L', (size, size), 0); dr = ImageDraw.Draw(img); n = 0
    for o in objs:
        idx = [i for i, mm in enumerate(o.data.materials) if mm == m]
        if not idx or not o.data.uv_layers: continue
        uv = np.empty(len(o.data.loops) * 2, np.float32); o.data.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
        for poly in o.data.polygons:
            if poly.material_index not in idx: continue
            dr.polygon([(float(uv[li, 0]) * size, (1 - float(uv[li, 1])) * size) for li in poly.loop_indices], fill=255); n += 1
    return img if n else None


def notskin_mask(m, path):
    """UV islands of this material on CLOTHING meshes (anything but the Body/Eyes/hair of a multi-mesh model)"""
    if len(meshes) < 2: return None
    cloth = [o for o in meshes if not any(k in o.name.lower() for k in ('body', 'hair', 'beard')) and not o.name.lower().endswith('eyes')]
    img = uv_mask(m, cloth)
    if img is None: return None
    img.save(path); return path


done = {}
for o in meshes:
    uvname = o.data.uv_layers.active.name if o.data.uv_layers else None
    for si, m in enumerate(o.data.materials):
        if m is None: continue
        if m.name in done: continue
        base, alpha = links_of(m)
        hair = 'hair' in m.name.lower()
        tag = '%s_%s' % (NAME, re.sub(r'[^A-Za-z0-9]+', '_', m.name))
        flat_path = os.path.join(TEX, tag + '.png')
        if base is not None:
            raw = os.path.join(RAW, tag + '.png')
            save_px(base, raw, alpha if hair else None)
            cmd = [sys.executable, '-I', os.path.join(HERE, 'flatten.py'), raw, flat_path, '--k', K] + (['--hair'] if hair else [])
            ns = notskin_mask(m, os.path.join(RAW, tag + '_notskin.png'))
            if ns and not hair: cmd += ['--notskin', ns]
            subprocess.run(['nice', '-n', '10'] + cmd, check=True)
        nm = bpy.data.materials.new('civ_' + tag); nm.use_nodes = True; nt = nm.node_tree
        for n in list(nt.nodes): nt.nodes.remove(n)
        out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
        if base is not None:
            img = bpy.data.images.load(flat_path); img.alpha_mode = 'STRAIGHT'
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Linear'
            if uvname:
                uv = nt.nodes.new('ShaderNodeUVMap'); uv.uv_map = uvname; nt.links.new(uv.outputs[0], t.inputs[0])
            nt.links.new(t.outputs['Color'], em.inputs['Color'])
        else:
            c = m.diffuse_color; em.inputs['Color'].default_value = (c[0], c[1], c[2], 1)
        if hair:
            sw = nt.nodes.new('ShaderNodeMixShader'); sw.name = 'IDSWITCH'; sw.inputs[0].default_value = 0.0
            nt.links.new(em.outputs[0], sw.inputs[1]); nt.links.new(id_emission(nt, 1 / 40.0).outputs[0], sw.inputs[2])
            gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5
            nt.links.new(t.outputs['Alpha'], gt.inputs[0])
            tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
            nt.links.new(gt.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(sw.outputs[0], mx.inputs[2])
            nt.links.new(mx.outputs[0], out.inputs['Surface'])
        else:
            nt.links.new(em.outputs[0], out.inputs['Surface'])
        done[m.name] = nm
    for si, m in enumerate(o.data.materials):
        if m is not None and m.name in done: o.data.materials[si] = done[m.name]

for m in list(bpy.data.materials):
    if not m.name.startswith('civ_'): bpy.data.materials.remove(m)
arm.animation_data_clear()
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.file.pack_all()
n_mat = len({m.name for o in meshes for m in o.data.materials if m})
print('materials', n_mat, [m.name for m in bpy.data.materials])
assert n_mat <= 6, 'render_char.py allows at most 6 materials'
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print('saved', OUT)
