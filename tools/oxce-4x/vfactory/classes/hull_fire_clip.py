# Firing clip for John: a vehicle whose launcher is fixed to the hull (no turret), e.g. the V.A.M.P. Mk II.
# The hull turns to aim (the game turns the whole vehicle), each rocket fires in turn from its muzzle in the package manifest,
# the hull picture switches to the next store state as it leaves (m4 -> m3 -> ... as the game's gjStoreStates does), the
# package's full-size missile flies (the rack's frame stays in front of it until it is clear: clip_mask.py) at the manifest's missile_flight speed with the launch smoke at its tail.
# usage: python3 hull_fire_clip.py pkg_dir out.gif [headings, e.g. NE,E]   (rockets split between the headings)
import sys, json, math
from PIL import Image, ImageDraw
sys.path.insert(0, __import__('os').path.dirname(__file__)); from clip_mask import occluder, draw
P, OUT = sys.argv[1:3]; HDS = (sys.argv[3] if len(sys.argv) > 3 else 'NE,E').split(',')
m = json.load(open(f'{P}/manifest.json')); AX, AY = m['anchor']; H8 = m['heading_order']
STATES = [s.strip() for s in m['states_note'].split(',')]            # loaded first: m4, m3, ..., m0
FL = m['weapons']['missile_flight']; W, H = 1100, 640; ox, oy = 330, 420
def ground():
    g = Image.new('RGBA', (W, H), (122, 114, 86, 255)); dd = ImageDraw.Draw(g)
    for k in range(-20, 40):
        dd.line([(k * 64 - 600, 0), (k * 64 - 600 + 2 * H, H)], fill=(110, 103, 77, 255)); dd.line([(k * 64, 0), (k * 64 - 2 * H, H)], fill=(110, 103, 77, 255))
    return g
def frame(hd, st): return next(x for x in m['frames'] if x['look'] == 'clean' and x['heading'] == hd and x['state'] == st)
def veh(hd, st):                                                     # the vehicle alone on a clip-sized canvas
    v = Image.new('RGBA', (W, H), (0, 0, 0, 0)); v.alpha_composite(img(frame(hd, st)), (ox - AX, oy - AY)); return v
def img(fr): return Image.open(f'{P}/{fr["file"]}').convert('RGBA')
fx = {}
for x in m['fx_frames']:
    if x['weapon'] != 'impact': fx.setdefault(x['heading'], []).append(x)
for k in fx: fx[k].sort(key=lambda x: x['frame'])
names = sorted(frame(HDS[0], STATES[0])['muzzles'])                 # rocket1..rocketN, the game's firing order
per = -(-len(names) // len(HDS)); fired = 0; frames = []
def shot(c): frames.append(c.convert('RGB').resize((W * 3 // 4, H * 3 // 4), Image.LANCZOS))
for si, hd in enumerate(HDS):
    if si:                                                           # turn the hull an eighth at a time to the next heading
        a = H8.index(HDS[si - 1]); b = H8.index(hd)
        for j in range(1, (b - a) % 8 + 1):
            fr = frame(H8[(a + j) % 8], STATES[fired])
            for _ in range(4): c = ground(); c.alpha_composite(img(fr), (ox - AX, oy - AY)); shot(c)
    else:
        for _ in range(6): c = ground(); c.alpha_composite(img(frame(hd, STATES[0])), (ox - AX, oy - AY)); shot(c)
    mf = m['missile_full']['by_heading'][hd]; ms = Image.open(f'{P}/{mf["file"]}').convert('RGBA')
    nx, ny = mf['nose_px']; tx, ty = mf['tail_px']; dx, dy = mf['flight_dir_screen']; L = math.hypot(dx, dy); dx, dy = dx / L, dy / L
    fxs = fx.get(hd, []); live = []; burst = names[fired:fired + per]
    for n in range(len(burst) * 5 + 22):
        if n % 5 == 0 and n // 5 < len(burst):                       # launch: the missile's nose on the muzzle, covering the mounted one
            mz = frame(hd, STATES[fired])['muzzles'][burst[n // 5]]['xy']; x0, y0 = ox - AX + mz[0], oy - AY + mz[1]
            vb, va = veh(hd, STATES[fired]), veh(hd, STATES[fired + 1])
            live.append([x0, y0, 0, FL['start_px_per_frame'], occluder(vb, va, ms, (int(x0 - nx), int(y0 - ny)))]); fired += 1
        cur = veh(hd, STATES[fired]); c = ground(); c.alpha_composite(cur)
        for s in live:
            x, y, age, v, mask = s
            if age < len(fxs):
                g = Image.open(f'{P}/{fxs[age]["file"]}').convert('RGBA'); ga = fxs[age]['anchor']
                c.alpha_composite(g, (int(x - (nx - tx) - ga[0]), int(y - (ny - ty) - ga[1])))
            px, py = int(x - nx), int(y - ny)
            if -120 < px < W and -120 < py < H: draw(c, ms, (px, py), mask, cur)
        for s in live: s[0] += dx * s[3]; s[1] += dy * s[3]; s[2] += 1; s[3] = min(FL['max_px_per_frame'], s[3] + FL['accel_px_per_frame2'])
        shot(c)
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=70, loop=0)
print('CLIP', OUT, len(frames))
