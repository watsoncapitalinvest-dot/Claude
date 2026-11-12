SOLDIER SPRITE RENDERER - from the design chat (12 Nov 2026)

build_duke.py and compose.py are the design chat's working code for the
approved Duke look (BRIEF_FOR_BUILD_SESSION_Duke.txt in Reference), copied
here with one change: the M-16 path points at this container's staging of
Reference\models\guns\grunt_M-16.glb.

Inputs live outside the repo (Mixamo bodies are 117 MB / 55 MB): staged from
John's machine into /mnt/user-data/uploads/, working folders under
/tmp/claude-0/ws/ laid out as the scripts expect:
  ws/duke_out/Ch49_100x_Diffuse.png   = anim\flat_Ch49_100x_Diffuse.png
  ws/anim/tex/                         = Ch33 face/hair, id maps
  ws/mix/packs/walk forward.fbx       = from Rifle 8-Way Locomotion Pack.zip

  python3 build_duke.py --clip "/tmp/claude-0/ws/mix/packs/walk forward.fbx" --out /tmp/claude-0/ws/anim/frames
  python3 compose.py /tmp/claude-0/ws/anim/frames /tmp/claude-0/ws/anim/out

ACCEPTANCE (step 1 of the brief), Blender 5.3 here vs 5.2 there:
reproduces duke_walk_8dir_rifle.gif - 15 frames x 8 facings, 1.5 per cent of
pixels visibly different in every frame, almost all of it the rifle sitting a
little differently in the away facings. Body, colours and ink match.
