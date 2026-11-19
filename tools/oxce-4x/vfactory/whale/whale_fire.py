"""Killer W.H.A.L.E. firing preview from posed renders (/tmp/whpose/out): turrets turn, Thrashers + Pounders fire, the 8 SAMs leave
the launchers one by one (each render has one fewer), the 6 SD-30 drums roll off the stern. Screen points from the renderer's camera."""
import math, sys
from PIL import Image, ImageDraw
PPU, S, AX, AY = 90.50967, 0.124833, 448, 320
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))
def proj(k, p):
    a = math.radians(-45 * k); c, s = math.cos(a), math.sin(a); x, y, z = (v * S for v in p)
    X, Y = c * x - s * y, s * x + c * y; u = (X - Y) / math.sqrt(2); v = (X + Y) / math.sqrt(2)
    return AX + PPU * u, AY - PPU * S30 * v - PPU * C30 * z
def turret_tip(cy, yaw, x=5.0, z=17.0):
    a = math.radians(yaw); px, py = -0.3, cy; dx, dy = x - px, 0
    return (px + dx * math.cos(a) - dy * math.sin(a), py + dx * math.sin(a) + dy * math.cos(a), z)
H = {'E': 2, 'NE': 1}; out = []
for hn, k in H.items():
    L = lambda n: Image.open(f'/tmp/whpose/out/{n}_clean_{hn}.png').convert('RGBA')
    def frame(n, draw=None):
        bg = Image.new('RGBA', (896 + 300, 544 + 160), (52, 92, 126, 255)); im = L(n); bg.alpha_composite(im, (60, 80))
        if draw: draw(ImageDraw.Draw(bg), 60, 80)
        bb = L('t0').getbbox(); out.append(bg.crop((60 + bb[0] - 40, 80 + bb[1] - 90, 60 + bb[2] + 260, 80 + bb[3] + 60)).convert('RGB'))
    def line(d, ox, oy, a, b, col, w): d.line((a[0] + ox, a[1] + oy, b[0] + ox, b[1] + oy), fill=col, width=w)
    def flash(d, ox, oy, p, r):
        d.ellipse((p[0] + ox - r, p[1] + oy - r, p[0] + ox + r, p[1] + oy + r), fill=(255, 200, 60)); d.ellipse((p[0] + ox - r / 2, p[1] + oy - r / 2, p[0] + ox + r / 2, p[1] + oy + r / 2), fill=(255, 250, 210))
    for n in ('t0', 't0', 't1', 't2', 't2'): frame(n)                                     # crow's-nest turrets swing to the target
    for i in range(6):                                                                   # Thrasher bursts
        def dr(d, ox, oy, i=i):
            for cy in (2.15, -2.1):
                a = proj(k, turret_tip(cy, -50)); b = proj(k, turret_tip(cy, -50, x=5.0 + 14 * (i + 1)))
                c_ = proj(k, turret_tip(cy, -50, x=5.0 + 14 * (i + 1) - 7)); flash(d, ox, oy, a, 6 if i % 2 == 0 else 4); line(d, ox, oy, c_, b, (255, 240, 150), 3)
        frame('t2', dr)
    for i in range(7):                                                                   # Pounders
        def dr(d, ox, oy, i=i):
            for y in (7.3, -7.3):
                a = proj(k, (13.0, y, 11.45))
                if i < 2: flash(d, ox, oy, a, 14 - 5 * i)
                b = proj(k, (13.0 + 25 * (i + 1), y, 11.45 + 2 * (i + 1))); c_ = proj(k, (13.0 + 25 * (i + 1) - 6, y, 11.45 + 2 * (i + 1)))
                line(d, ox, oy, c_, b, (255, 220, 120), 5)
        frame('t2', dr)
    tubes = [(-1.4, 7.3, 16.9), (-1.4, -6.0, 16.9), (-1.4, 6.0, 16.9), (-1.4, -7.3, 16.9), (-1.0, 7.3, 15.9), (-1.0, -6.0, 15.9), (-1.0, 6.0, 15.9), (-1.0, -7.3, 15.9)]
    for m in range(1, 9):                                                                # one SAM leaves each frame, the tube is empty after
        for j in range(3):
            def dr(d, ox, oy, m=m, j=j):
                tx, ty, tz = tubes[m - 1]; s = 4 + 9 * j * j + 3 * j; dx, dz = math.cos(math.radians(30)), math.sin(math.radians(30))
                a = proj(k, (tx + dx * s, ty, tz + dz * s)); b = proj(k, (tx + dx * (s + 6), ty, tz + dz * (s + 6)))
                for q in range(1, 6):
                    sm = proj(k, (tx + dx * (s - 3 * q), ty, tz + dz * (s - 3 * q))); r = 3 + 2 * q
                    d.ellipse((sm[0] + ox - r, sm[1] + oy - r, sm[0] + ox + r, sm[1] + oy + r), fill=(215, 215, 210))
                line(d, ox, oy, a, b, (238, 238, 232), 5); flash(d, ox, oy, a, 4)
            frame(f'm{m}', dr)
    for n in range(1, 7):                                                                # SD-30 drums roll off the stern into the sea
        for j in range(4):
            def dr(d, ox, oy, n=n, j=j):
                y0 = -7.6 + (n - 1) * 0.75; p = proj(k, (-17.5 - 3.0 * j, y0, 12.0 - 1.6 * j * j))
                if j < 3:
                    r = 15; d.rounded_rectangle((p[0] + ox - r, p[1] + oy - r * 0.75, p[0] + ox + r, p[1] + oy + r * 0.75), 8, fill=(30, 30, 32), outline=(80, 82, 80), width=2)
                else:
                    q = proj(k, (-27, y0, 0)); [d.ellipse((q[0] + ox - rr, q[1] + oy - rr / 2, q[0] + ox + rr, q[1] + oy + rr / 2), outline=(235, 245, 255), width=3) for rr in (18, 34)]
                    d.line((q[0] + ox, q[1] + oy, q[0] + ox, q[1] + oy - 55), fill=(235, 245, 255), width=10)
            frame(f'd{n}', dr)
out[0].save(sys.argv[1], save_all=True, append_images=out[1:], duration=110, loop=0); print(len(out))
