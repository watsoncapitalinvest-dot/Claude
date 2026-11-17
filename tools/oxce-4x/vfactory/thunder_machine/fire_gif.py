# Firing clip for John: the vehicle at three headings (guns fixed, the vehicle turns to aim), both Gatlings flashing in turn, the 30mm round (the game's own head
# sheet) flying out of each barrel along the barrel's screen direction. usage: python3 fire_gif.py pkg_dir head_rgb.png out.gif
import sys, json, math
from PIL import Image, ImageDraw
P, HEAD, OUT = sys.argv[1:4]; m = json.load(open(f'{P}/manifest.json')); AX, AY = m['anchor']
hs = Image.open(HEAD).convert('RGBA'); Z = hs.height; heads = [hs.crop((k * Z, 0, k * Z + Z, Z)) for k in range(8)]
W, H = 1100, 620
def ground():
    g = Image.new('RGBA', (W, H), (122, 114, 86, 255)); d = ImageDraw.Draw(g)
    for k in range(-20, 40):
        d.line([(k * 64 - 600, 0), (k * 64 - 600 + 2 * H, H)], fill=(110, 103, 77, 255)); d.line([(k * 64, 0), (k * 64 - 2 * H, H)], fill=(110, 103, 77, 255))
    return g
frames = []
for hd in ('E', 'SE', 'S'):
    f = next(x for x in m['frames'] if x['look'] == 'clean' and x['heading'] == hd and x.get('state', 'm0') == 'm0')
    body = Image.open(f'{P}/{f["file"]}').convert('RGBA')
    ox, oy = 420, 300; rounds = []
    for n in range(26):
        c = ground(); c.alpha_composite(body, (ox - AX, oy - AY))
        if n < 16:                                                    # a burst: barrels alternate, a round each frame
            g = 'gatL' if n % 2 == 0 else 'gatR'; mz = f['muzzles'][g]; mx, my = ox - AX + mz['xy'][0], oy - AY + mz['xy'][1]
            dx, dy = mz['dir_screen']; L = math.hypot(dx, dy); dx, dy = dx / L, dy / L
            rounds.append([mx, my, dx, dy])
            fx = next((x for x in m['fx_frames'] if x.get('weapon') == g and x.get('heading') == hd and x.get('frame') == n % 2), None)
            if fx: c.alpha_composite(Image.open(f'{P}/{fx["file"]}').convert('RGBA'), (int(mx - 48), int(my - 48)))
        for r in rounds:
            r[0] += r[2] * 34; r[1] += r[3] * 34
            ang = math.degrees(math.atan2(r[2], -r[3])); k = int(math.floor((ang + 22.5) / 45)) % 8; h = heads[k]
            if -Z < r[0] < W and -Z < r[1] < H: c.alpha_composite(h, (int(r[0] - Z / 2), int(r[1] - Z / 2)))
        frames.append(c.convert('RGB'))
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=70, loop=0, optimize=True); print('frames', len(frames))
