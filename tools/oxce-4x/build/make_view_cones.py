"""John's three view-cone pictures (18 Nov 22:04: unaware / suspicious / alert) laid onto the battle map's ground in the
8 facings. Each picture is the wedge seen from above, apex at the bottom centre, opening upward. The output canvas is
centred on the guard: 2R*32 x 2R*16 base px (R = the cone's reach in tiles), drawn at K x base so it stays sharp.
Writes mod/Resources/UI/Cones/cone_<state>_<dir>.png. Map::drawViewCones places them (STEALTH_SIGHT item 2).
"""
import os, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'art', 'view_cones')
OUT = os.path.join(HERE, '..', 'mod', 'Resources', 'UI', 'Cones')
R, K = 14.0, 2          # reach in tiles (Map::drawViewCones uses the same R); output scale
VX = [0, 1, 1, 1, 0, -1, -1, -1]; VY = [-1, -1, 0, 1, 1, 1, 0, -1]   # OXCE facings 0..7 in tile space
os.makedirs(OUT, exist_ok=True)
for state in ('unaware', 'suspicious', 'alert'):
    src = np.asarray(Image.open(os.path.join(SRC, f'cone_{state}.png')).convert('RGBA')).astype(np.float32)
    al = src[..., 3]; ys, xs = np.nonzero(al > 200)
    apx, apy = (xs.min() + xs.max()) / 2.0, float(ys.max())     # the apex: bottom centre of the wedge
    rimg = apy - ys.min()                                       # picture px from apex to the top of the arc
    W, H = int(2 * R * 32 * K), int(2 * R * 16 * K)
    X, Y = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
    sx, sy = (X - W / 2) / K, (Y - H / 2) / K                  # base px from the guard's floor centre
    dx = (sx / 16 + sy / 8) / 2; dy = (sy / 8 - sx / 16) / 2   # iso back to tiles
    for d in range(8):
        a = np.arctan2(VY[d], VX[d])
        fwd = dx * np.cos(a) + dy * np.sin(a); right = -dx * np.sin(a) + dy * np.cos(a)
        u = apx + right * rimg / R; v = apy - fwd * rimg / R
        ui, vi = np.round(u).astype(int), np.round(v).astype(int)
        ok = (ui >= 0) & (ui < src.shape[1]) & (vi >= 0) & (vi < src.shape[0])
        out = np.zeros((H, W, 4), np.float32)
        out[ok] = src[vi[ok], ui[ok]]
        out[..., 3][out[..., 3] < 40] = 0                      # the stray glow speckle around the edge
        # John 22:06 "make them more transparent": the blue fill is a faint wash, the edge and the sigil stay bright
        r, g, b_ = out[..., 0], out[..., 1], out[..., 2]
        fill = (r < 100) & (g < 100) & (b_ > 90)
        out[..., 0] = np.where(fill, 70, r); out[..., 1] = np.where(fill, 130, g); out[..., 2] = np.where(fill, 255, b_)   # a light blue wash, not a dark one
        out[..., 3] = np.where(fill & (out[..., 3] > 0), 70.0, out[..., 3] * 0.95)
        Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(os.path.join(OUT, f'cone_{state}_{d}.png'), optimize=True)
    print(state, 'apex', apx, apy, 'radius px', rimg)
