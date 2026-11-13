# hair_fit: a hair piece cut from a scanned bust, fitted to a look as CAST's mesh_part
Made 13 Nov 2026 for Baroness v2 (John: "do this yourself"). Steps, in order, all one-off scripts:
1. dec.py      import the bust (glb), join, weld, decimate to ~60k tris -> bust.npz
2. seg2.py     hair mask by shape: cut the face oval and everything below the jaw except hair hanging behind the shoulder line; drop islands
3. rview.py    4-view render of the mask (check it by eye)
4. fit.py      move the hair onto the body (1:1, aligned on the nose tip), decimate to ~6k tris, outward faces -> <name>.npz (V, F, zone, wh)
5. clear.py    push the hair 4 mm clear of the body's head (radial)
6. clear2.py   push it 5 mm clear of the upper body along the body's surface normals (the swelled back and shoulders)
7. build_v2.py rebuild the look's hair object exactly as CAST's make_blend.py does (cel tones from the card zone, Head/Spine2 weights)
Landmarks (nose tip, head-only verts, upper-body surface) are measured from the look's own blend. Paths are the 13 Nov working paths.
The bust and the blends are John's private files and never go in this repo.
