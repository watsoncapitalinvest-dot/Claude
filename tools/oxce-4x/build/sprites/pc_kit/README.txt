CARTEL RENDER KIT - runs on your PC, not in the cloud.

WHAT YOU NEED (once)
  1. Blender 5.x - blender.org/download. The normal installer is fine (it goes to C:\Program Files\Blender Foundation).
  2. Python 3 - you downloaded the Python install manager today; run it, then open a new window and type:  python --version
  The .bat installs numpy, pillow and scipy itself.

WHAT IT USES (already on your PC)
  Reference\cartel\          the nine cartel_*.blend + clips_17nov.blend
  Downloads\                 Basic Shooter Pack.zip, Pistol_Handgun Locomotion Pack.zip, Rifle 8-Way Locomotion Pack.zip,
                             Action Adventure Pack.zip  (unpacked into render_work\packs16 the first time)
  XCom UFO Defense\XCOM\UNITS  the game palette for the sheets

RUN
  Unzip this kit to C:\GI-Joe-Silent-Storm\GIJoe_XCOM_4x\render_kit and double-click RENDER_CARTEL.bat.
  All nine, then the extra clips. Or from a command window in the kit folder:
    python render_cartel.py cartel_boss_a            one man
    python render_cartel.py --no-extras              sheets only
    python render_cartel.py --extras-only            only the runs + spell strips

WHAT COMES OUT  (Reference\sheets\cartel)
  <name>_body.png, <name>_body_rgb.png, <name>_body_anchors.txt   the walk16 sheet BUILD-1 installs (2048x8960, 896 frames)
  extras\<name>_<clip>.png   cast_spell_hold, the seven runs, walk_up_stairs and walk_down_stairs (stepping in place): 8 facings x 16 frames, raw renders (no outline,
                             no game palette). The game has no slot for these yet - BUILD decides where they go.
  render_work\render_log.txt   start/finish/minutes for every man, and the check result
                               (2048x8960, 896 anchors, 0 empty frames). Safe to delete render_work afterwards.
