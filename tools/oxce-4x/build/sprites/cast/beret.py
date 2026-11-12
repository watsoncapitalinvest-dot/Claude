"""A modelled beret: headband hugging the skull + a soft crown that overhangs and droops to one side."""
import numpy as np, math

def make_beret(head_pts, band_z, side=-1.0, crown_r=1.0, puff=1.0, droop=1.0, n=48, m=14):
    """head_pts: Nx3 world points of the head (rest pose). band_z: height of the band's lower edge.
    side=-1 droops toward -X (the character's right). Returns (verts, faces) in world space."""
    P = np.asarray(head_pts)
    top = P[:, 2].max()
    sk = P[P[:, 2] > top - 0.05]; c = np.array([sk[:, 0].mean(), sk[:, 1].mean()])
    # head outline at band height: furthest head point in each direction, slightly outside the skin
    sl = P[np.abs(P[:, 2] - (band_z + 0.006)) < 0.012]
    ang = np.arctan2(sl[:, 1] - c[1], sl[:, 0] - c[0]); rad = np.hypot(sl[:, 0] - c[0], sl[:, 1] - c[1])
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rb = np.array([rad[np.abs(((ang - t + np.pi) % (2 * np.pi)) - np.pi) < 0.25].max() if (np.abs(((ang - t + np.pi) % (2 * np.pi)) - np.pi) < 0.25).any() else rad.max() for t in th]) + 0.004
    from scipy.ndimage import uniform_filter1d
    rb = uniform_filter1d(rb, 5, mode='wrap')
    band_h = 0.014
    dirs = np.stack([np.cos(th), np.sin(th)], -1)
    B0 = np.column_stack([c + dirs * rb[:, None], np.full(n, band_z)])
    B1 = np.column_stack([c + dirs * (rb[:, None] + 0.001), np.full(n, band_z + band_h)])
    # crown: rim overhangs the band, more and lower on the droop side
    lean = np.clip(side * np.cos(th), 0, 1) ** 1.5                     # 1 on the droop side, 0 on the other
    R = rb * (1.04 * crown_r) + 0.045 * lean * droop
    rim_xy = c + np.array([side * 0.012 * droop, 0.0]) + dirs * R[:, None]
    rim_z = band_z + band_h + 0.040 * puff - 0.040 * lean * droop
    T = np.array([c[0] + side * 0.020 * droop, c[1], max(top + 0.012 * puff, rim_z.max() + 0.012)])
    verts = []
    for i in range(n):
        verts.append(B0[i]); verts.append(B1[i])
    # rows from band top -> rim (outward bulge) -> crown centre
    rows = []
    for j in range(1, m + 1):
        t = j / m
        row = []
        for i in range(n):
            b = B1[i]; r = np.array([rim_xy[i, 0], rim_xy[i, 1], rim_z[i]])
            if t <= 0.35:                      # band up and out to the rim, slight underside curl
                u = t / 0.35
                p = b * (1 - u) ** 2 + 2 * u * (1 - u) * (r + np.array([0, 0, -0.012])) + u * u * r
            else:                              # rim over the soft top to the centre
                u = (t - 0.35) / 0.65
                ctl = np.array([r[0] * 0.75 + T[0] * 0.25, r[1] * 0.75 + T[1] * 0.25, T[2] - 0.004 + 0.010 * puff - 0.022 * lean[i] * droop])
                p = r * (1 - u) ** 2 + 2 * u * (1 - u) * ctl + u * u * T
            row.append(p)
        rows.append(row)
    base = len(verts)
    for row in rows:
        verts.extend(row)
    V = np.array(verts)
    F = []
    for i in range(n):                         # band strip
        a, b = 2 * i, 2 * ((i + 1) % n)
        F.append((a, b, b + 1, a + 1))
    prev = [2 * i + 1 for i in range(n)]
    for j in range(m):
        cur = [base + j * n + i for i in range(n)]
        for i in range(n):
            k = (i + 1) % n
            F.append((prev[i], prev[k], cur[k], cur[i]))
        prev = cur
    return V, F, n                             # first 2n verts = band (for a separate material)
