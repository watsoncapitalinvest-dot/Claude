# Firing clip for John: the vehicle at three headings (guns fixed, the vehicle turns to aim), both Gatlings flashing in turn, the 30mm round (the game's own head
# sheet) flying out of each barrel along the barrel's screen direction. usage: python3 fire_gif.py pkg_dir head_rgb.png out.gif
import sys, json, math
from PIL import Image, ImageDraw
P, HEAD, OUT = sys.argv[1:4]; CASE = sys.argv[4] if len(sys.argv) > 4 else None
case = Image.open(CASE).convert('RGBA') if CASE else None
if case is not None: case = case.resize((max(4, round(case.width * 0.6)), max(2, round(case.height * 0.6))), Image.LANCZOS)   # John 18:19 'smaller'
m = json.load(open(f'{P}/manifest.json')); AX, AY = m['anchor']
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
    ox, oy = 420, 300; rounds = []; shells = []; spent = []
    for n in range(26):
        c = ground(); c.alpha_composite(body, (ox - AX, oy - AY))
        if n < 16:                                                    # a burst: barrels alternate, a round each frame
            g = 'gatL' if n % 2 == 0 else 'gatR'; mz = f['muzzles'][g]; mx, my = ox - AX + mz['xy'][0], oy - AY + mz['xy'][1]
            dx, dy = mz['dir_screen']; L = math.hypot(dx, dy); dx, dy = dx / L, dy / L
            rounds.append([mx, my, dx, dy])
            if case is not None:                                       # spent case thrown up and out of the receiver side
                o = f['muzzles']['gatL']['xy'], f['muzzles']['gatR']['xy']; sx, sy = o[0][0] - o[1][0], o[0][1] - o[1][1]; sl = math.hypot(sx, sy) or 1
                side = 1 if g == 'gatL' else -1; sx, sy = side * sx / sl, side * sy / sl
                ex, ey = mx - dx * 47 + sx * 8, my - dy * 47 + sy * 8          # the receiver, ~47 px back from the muzzle
                shells.append([ex, ey, sx * 3.0 + (n % 3 - 1) * 0.5, -6.0 - (n % 3) * 0.7, ey + 40 + (n % 5) * 3, n * 37 % 360])   # John 18:19 'not as far'
            fx = next((x for x in m['fx_frames'] if x.get('weapon') == g and x.get('heading') == hd and x.get('frame') == n % 2), None)
            if fx: c.alpha_composite(Image.open(f'{P}/{fx["file"]}').convert('RGBA'), (int(mx - 48), int(my - 48)))
        if case is not None:
            for sh in shells:                                          # arc: up and out, gravity, tumbling
                sh[0] += sh[2]; sh[1] += sh[3]; sh[3] += 2.2; sh[5] += 55
                if sh[1] >= sh[4] and sh[3] > 0: spent.append((sh[0], sh[4], sh[5])); sh[3] = None
            shells[:] = [sh for sh in shells if sh[3] is not None]
            for sh in shells: im_ = case.rotate(sh[5] % 360, expand=True); c.alpha_composite(im_, (int(sh[0] - im_.width / 2), int(sh[1] - im_.height / 2)))
        for r in rounds:
            r[0] += r[2] * 34; r[1] += r[3] * 34
            ang = math.degrees(math.atan2(r[2], -r[3])); k = int(math.floor((ang + 22.5) / 45)) % 8; h = heads[k]
            if -Z < r[0] < W and -Z < r[1] < H: c.alpha_composite(h, (int(r[0] - Z / 2), int(r[1] - Z / 2)))
        frames.append(c.convert('RGB'))
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=70, loop=0, optimize=True); print('frames', len(frames))
