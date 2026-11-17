RENDER MACHINE - runs on your PC, offline. Drop a model in, a finished game sheet comes out.

START IT
  Double-click RENDER_MACHINE.bat and leave the window open. It watches two folders:
    Reference\cartel   ARMED men      (gun poses: rifle stand/kneel/aim, pistol stand/kneel)
    Reference\civ      CIVILIANS      (no gun: plain standing pose for every still)
  Any .blend dropped in either folder is rendered, checked and filed. Change a .blend and drop it again
  (overwrite) and it is re-rendered. Already-finished models are not redone. Close the window to stop.

WHAT COMES OUT
  Reference\sheets\cartel  (armed)   and   Reference\sheets\civ  (civilians):
    <name>_body.png, <name>_body_rgb.png, <name>_body_anchors.txt   the walk16 game sheet (2048x8960, 896 frames)
    extras\<name>_<clip>.png   the held spell, seven runs, walk up / down stairs: 8 facings x 16 frames, raw renders
                               (no outline, no game palette). The game has no slot for these yet - BUILD decides.
  render_work\MACHINE_STATUS.txt   what is queued, what is done, OK or FAILED
  render_work\render_log.txt       start/finish/minutes per model and the sheet check
  About 13-15 minutes a model for the sheet, about 1.5 more for each extra clip in extras.txt (all 21: about 30).

A MODEL MUST BE
  A .blend on one Mixamo skeleton (mixamorig: bones), the mesh skinned to it, textures packed in. The file name is
  the character's name. The machine does not change the model: what you build and paint is what comes out.

THE FINISH (same as the current Joes / Cobra troopers / greenshirts)
  Default: the painted textures carry the shading and fold lines; the machine adds the outline. Nothing to set.
  For an older-style finish, put a text file beside the model, <name>.ink.txt, with one line in the render
  script's ink format  HAIR|FOLD|PEN  - for example:
      48,38,32||TERMIDS=3,6,11 TERMMIN=90          hair tone + fold lines on garment parts 3, 6, 11
      ||PENIDS=20 PENPCT=84 PENDARK=0.66            pen shading on garment part 20 (adds the shade pass)
  The log says "ink from <name>.ink.txt" when it is used.

ONE-OFF RUNS (instead of the machine)
  RENDER_CARTEL.bat                      every model in Reference\cartel, then stop
  RENDER_CIVILIANS.bat                   every model in Reference\civ, then stop
  RENDER_CARTEL.bat cartel_boss_a Ch42   just these names (looked for in cartel, then civ)
  add --no-extras or --extras-only to skip or only do the extra clips

NEEDS
  The Python 3.13 + Blender module that SETUP_v3.bat installed on 17 Nov. If missing, the .bat installs it
  (about 1 GB, once). Also uses Downloads\ (the four animation pack zips + Standing Idle.fbx) and the game's
  XCom UFO Defense\XCOM\UNITS palette.

TESTED in the cloud with these exact scripts and your folder layout: cartel_boss_b (armed) 2048x8960, 896 anchors,
0 empty frames, 13.6 min; Ch42 (civilian) pixel-identical to the Ch42 sheet already in the game.
