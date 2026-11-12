"""Swap a character's painted textures in a ready-built .blend (same rig, same material mapping).
   python3 swap_textures.py <in.blend> <textures dir> <out.blend>
Every packed image whose name ends in one of the delivery's file names (Ch49_1001.png, Ch49_1002.png,
face.png, hair.png, id_Ch49_100x_Diffuse.png) is reloaded from the delivery and repacked.
Used for the Cobra v4 redo (DESIGN, 12 Nov): only the textures changed."""
import bpy, sys, os
src, tex, out = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=src)
names = os.listdir(tex)
done = []
for im in bpy.data.images:
    hit = [n for n in names if n.endswith('.png') and (im.name == n or im.name.endswith('_' + n))]
    if not hit:
        continue
    p = os.path.join(tex, hit[0])
    if im.packed_file: im.unpack(method='REMOVE')
    im.filepath = p; im.reload(); im.pack()
    done.append(f'{im.name} <- {hit[0]} {tuple(im.size)}')
print('\n'.join(done) or 'NOTHING SWAPPED')
bpy.ops.wm.save_as_mainfile(filepath=out)
