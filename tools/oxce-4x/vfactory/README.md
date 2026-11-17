# VFACTORY - the vehicle factory (17 Nov 2026)

One code path per job, data per vehicle. Code only in this repo: no models, textures, renders or decal pictures
(they live in John's Reference\ and reach the game only inside a mod_update zip).

ROSTER's tools (Reference\roster_tools\roster_tools_v2.zip) are unpacked at /home/claude/rt with their
/tmp/claude-0/ paths rewritten; the factory calls them, it does not fork them.

## reskin: change decals on a finished package, render only what changed
    python3 reskin.py PKG_DIR ROSTER_CFG WORK OUT 'img1,img2' 'missing_img=r,g,b' MASK.png   (FULL=1 renders every state)
- sigil_swap.py puts the new picture into the named decal images of the package's own *_source.blend, in the colour of the
  decal it replaces, and restores the flat-colour textures ROSTER never packed (the glass on 9 of 12 vehicles).
- Renders the first state's clean look at 8 headings with ROSTER's render_vehicle.py; every other frame (all states,
  damaged look) is ROSTER's frame with only the changed pixels replaced. Pixels under a damage sticker keep the sticker;
  light soot is carried over as a tint. A state whose removed store touches the decal is rendered in full.
- Checked on the Rattler: 77 fully rendered state frames vs the shortcut, 13,829 changed pixels, worst difference 2/255.
  ROSTER's own re-renders differ by +-1 in places (noise), so equality is tested at 3.
- Tiles and overhang re-cut with pkg.py's cutter; manifest sha256 / pieces / reassembly rewritten; previews.sh rebuilds
  the preview and turntable with ROSTER's preview.py / turntable.py.

## First job: the Cobra sigil (John 17 Nov 09:47; "no cobra on the dreadnoks" = Swampfire keeps its diamond)
batch_sigil.sh: 20 packages (12 vehicles + air/sea) in 16 min of compute; 8 renders each plus 0-24 extra.
