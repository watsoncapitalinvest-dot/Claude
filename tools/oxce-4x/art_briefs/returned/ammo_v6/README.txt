AMMO v6 — replaces every earlier ammo request.
16 transparent RGBA game PNGs in ammo/; one comparison sheet at ZIP root.
Big: exact 128x192 canvas; 1x1 artwork fills 56x56 at (36,68), 1x2 fills
56x120 at (36,36). These positions leave 4px inside each slot footprint.
Floor: exact 128x160 canvas; all silhouettes are 52px wide, centered on
the bottom tile diamond around (64,128). No tile is baked into sprites.
These are intentionally readable game icons, not a common physical ruler.
Permitted text only: LINKED on large can, HE on rocket tube.
All dimensions, filled bounds, filenames, transparency and tile placement
passed validation. Preview enlarges every inventory canvas uniformly 3x;
green outlines are preview-only export-bound guides. Not tested in OpenXCOM.
Built-in image generation produced each individual master; export preparation
sets the exact pixel sizes. PROMPTS.txt preserves the full generation prompts.
