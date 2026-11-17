CARTEL RENDER KIT - runs on your PC, not in the cloud.

WHAT YOU NEED
  Nothing new. It uses the Python 3.13 + Blender module that SETUP_v3.bat (walk16_kit) installed on 17 Nov.
  If that is ever missing, RENDER_CARTEL.bat installs it itself the first time (about 1 GB, a few minutes).

TESTED (cloud, same scripts, your folder layout): cartel_boss_b -> 2048x8960, 896 anchors, 0 empty frames in 13.6 min;
  walk_down_stairs extra in 1.4 min. Not yet run on this PC.

WHAT IT USES (already on your PC)
  Reference\cartel\          the nine cartel_*.blend + clips_17nov.blend
  Downloads\                 Basic Shooter Pack.zip, Pistol_Handgun Locomotion Pack.zip, Rifle 8-Way Locomotion Pack.zip,
                             Action Adventure Pack.zip  (unpacked into render_work\packs16 the first time)
  XCom UFO Defense\XCOM\UNITS  the game palette for the sheets

RUN
  Unzip this kit to C:\GI-Joe-Silent-Storm\GIJoe_XCOM_4x\render_kit and double-click RENDER_CARTEL.bat.
  All nine (about 12-15 min a man), then the extra clips (about 1.5 min a clip a man). Or from a command window in the kit folder:
    python render_cartel.py cartel_boss_a            one man
    python render_cartel.py --no-extras              sheets only
    python render_cartel.py --extras-only            only the runs + spell strips

WHAT COMES OUT  (Reference\sheets\cartel)
  <name>_body.png, <name>_body_rgb.png, <name>_body_anchors.txt   the walk16 sheet BUILD-1 installs (2048x8960, 896 frames)
  extras\<name>_<clip>.png   cast_spell_hold, the seven runs, walk_up_stairs and walk_down_stairs (stepping in place): 8 facings x 16 frames, raw renders (no outline,
                             no game palette). The game has no slot for these yet - BUILD decides where they go.
  render_work\render_log.txt   start/finish/minutes for every man, and the check result
                               (2048x8960, 896 anchors, 0 empty frames). Safe to delete render_work afterwards.
