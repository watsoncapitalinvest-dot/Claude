"""Battle bar icons (ART, 12 Nov; BATTLE_ICONS_BRIEF.txt) -> mod/Resources/UI/battle_icons/.

The delivery is 128x128 on pure magenta. The magenta (and any pink fringe) becomes alpha;
HiUI draws each icon above its button's word (HiUI::nativeKeyIcon).
    python3 install_battle_icons.py
"""
import glob
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'art_briefs', 'returned', 'battle_icons')
OUT = os.path.join(HERE, '..', 'mod', 'Resources', 'UI', 'battle_icons')
os.makedirs(OUT, exist_ok=True)
for p in sorted(glob.glob(os.path.join(SRC, 'icon_*.png'))):
    a = np.asarray(Image.open(p).convert('RGB')).astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # magenta-ness: red and blue high together, green low
    m = np.clip((np.minimum(r, b) - g) / 255.0, 0, 1)
    alpha = np.clip(1.0 - (m - 0.25) / 0.5, 0, 1)            # pure key -> 0, art -> 1, fringe between
    rgb = a.astype(np.float32)
    # despill the fringe: pull red and blue down toward green where it was pink
    spill = (m > 0.05) & (alpha > 0)
    rgb[..., 0][spill] = np.minimum(rgb[..., 0][spill], rgb[..., 1][spill] + 40)
    rgb[..., 2][spill] = np.minimum(rgb[..., 2][spill], rgb[..., 1][spill] + 40)
    out = np.dstack([rgb.clip(0, 255), alpha * 255]).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(os.path.join(OUT, os.path.basename(p)))
    print(os.path.basename(p), 'opaque px', int((alpha > 0.5).sum()))
