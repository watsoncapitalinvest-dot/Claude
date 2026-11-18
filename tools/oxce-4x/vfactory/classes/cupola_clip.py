# Clip for John (17 Nov 22:01, "the machine gun rotates faster, less tu than the turret"): a vehicle with a cupola, as the engine
# change draws it - hull, turret at its heading, cupola at ITS heading on top (manifest cupola.offset_in_turret[turret heading]).
# Script: the cannon fires ahead; the cupola swings to another target and bursts while the turret stays put; the turret then
# swings round (the cupola riding on it) and fires again. A TU counter shows the turn costs.
# usage: python3 cupola_clip.py pkg_dir out.gif turret_tu cupola_tu tu_start
import sys, json, math
from PIL import Image, ImageDraw, ImageFont
P, OUT = sys.argv[1:3]; TT, CT, TU = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
m = json.load(open(f'{P}/manifest.json')); AX, AY = m['anchor']; H8 = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']; CU = m['cupola']
W, H = 1100, 640; ox, oy = 330, 420; FNT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
def ground():
    g = Image.new('RGBA', (W, H), (122, 114, 86, 255)); dd = ImageDraw.Draw(g)
    for k in range(-20, 40):
        dd.line([(k * 64 - 600, 0), (k * 64 - 600 + 2 * H, H)], fill=(110, 103, 77, 255)); dd.line([(k * 64, 0), (k * 64 - 2 * H, H)], fill=(110, 103, 77, 255))
    return g
HULL = 'NE'; fr = next(x for x in m['frames'] if x['look'] == 'clean' and x['heading'] == HULL and x.get('state', 'm0') == 'm0')
body = Image.open(f'{P}/{fr["file"]}').convert('RGBA'); off = fr['turret_paste_offset']
TI = {t['heading']: t for t in m['turret'] if t['look'] == 'clean'}; CI = {c['heading']: c for c in CU['frames'] if c['look'] == 'clean'}
frames = []; tu = [TU]
def draw(td, cd, shots=(), note=''):
    c = ground(); c.alpha_composite(body, (ox - AX, oy - AY)); t = TI[td]; pv = t['pivot']; tp = (ox + off[0] - pv[0], oy + off[1] - pv[1])
    c.alpha_composite(Image.open(f'{P}/{t["file"]}').convert('RGBA'), tp)
    co = CU['offset_in_turret'][td]; cp = (tp[0] + co[0], tp[1] + co[1]); ci = CI[cd]
    c.alpha_composite(Image.open(f'{P}/{ci["file"]}').convert('RGBA'), cp)
    dr = ImageDraw.Draw(c)
    for kind, n in shots:
        if kind == 'gun':
            mz = t['muzzles']['main']; x, y = tp[0] + mz['xy'][0], tp[1] + mz['xy'][1]; dx, dy = mz['dir_screen']
        else:
            mz = ci['muzzles']['mg']; x, y = cp[0] + mz['xy'][0], cp[1] + mz['xy'][1]; dx, dy = mz['dir_screen']
        L = math.hypot(dx, dy); dx, dy = dx / L, dy / L
        if kind == 'gun':
            if n == 0: dr.ellipse((x - 14, y - 10, x + 14, y + 10), fill=(255, 220, 140, 255))
            s = 40 * n; dr.line([(x + dx * max(0, s - 36), y + dy * max(0, s - 36)), (x + dx * s, y + dy * s)], fill=(255, 214, 120, 255), width=3)
        else:
            if n % 2 == 0 and n < 8: dr.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 230, 150, 230))
            for j in range(0, min(n, 8), 2):
                s = (n - j) * 34
                if s < 380: dr.line([(x + dx * s, y + dy * s), (x + dx * (s + 18), y + dy * (s + 18))], fill=(255, 200, 90, 255), width=2)
    dr.text((30, 24), f'TU {tu[0]}', font=FNT, fill=(250, 250, 240)); dr.text((30, 60), note, font=FNT, fill=(250, 250, 240))
    frames.append(c.convert('RGB').resize((W * 3 // 4, H * 3 // 4), Image.LANCZOS))
def steps(a, b):
    i0, i1 = H8.index(a), H8.index(b); st = 1 if (i1 - i0) % 8 <= 4 else -1; out = []; i = i0
    while i != i1: i = (i + st) % 8; out.append(H8[i])
    return out
td, cd = 'NE', 'NE'
for _ in range(8): draw(td, cd, note='cannon and M2 forward')
for n in range(10): draw(td, cd, [('gun', n)], 'cannon fires')
for h in steps(cd, 'SE'):                                              # the cupola swings on its own, the turret stays
    tu[0] -= CT; cd = h
    for _ in range(4): draw(td, cd, note=f'M2 turns alone: {CT} TU per 1/8 turn')
for n in range(14): draw(td, cd, [('mg', n)], 'M2 fires, cannon still forward')
for h in steps(td, 'E'):                                               # the turret swings; the cupola rides round with it
    tu[0] -= TT; d = (H8.index(h) - H8.index(td)) % 8; td = h; cd = H8[(H8.index(cd) + d) % 8]
    for _ in range(6): draw(td, cd, note=f'turret turns: {TT} TU per 1/8 turn (M2 rides along)')
for n in range(10): draw(td, cd, [('gun', n)], 'cannon fires')
for _ in range(10): draw(td, cd, note='')
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=80, loop=0); print('CLIP', OUT, len(frames))
