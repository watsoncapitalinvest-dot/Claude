"""Fit the downloaded beret (Thingiverse 4362514, MarKuSPluS, CC-BY: the beret piece cut from that figure)
onto any head, using the figure's own head as the reference so the beret sits the way it did on him."""
import numpy as np
import os
NPZ = os.path.join(os.environ.get('CAST_V2', '/tmp/claude-0/ws/cast_v2/cast_v2_1p6cm'), 'scripts', 'props', 'beret_brimstone.npz')   # build session: from the zip
def fit_beret(Wn, scale=1.04, lift=0.0, back=0.0, band=0.06, piece='beret', fwd=0.0):
    d = np.load(NPZ); B, H = d[piece].astype(np.float64), d['head'].astype(np.float64)
    topH, top = H[:, 2].max(), Wn[:, 2].max()
    bo = Wn[Wn[:, 2] > top - band]; wO = bo[:, 0].max() - bo[:, 0].min()
    s = 1 / 30.0
    for _ in range(4):
        bh = H[H[:, 2] > topH - band / s]; s = wO / (bh[:, 0].max() - bh[:, 0].min())
    cH = np.array([bh[:, 0].mean(), bh[:, 1].mean(), topH]); cO = np.array([bo[:, 0].mean(), bo[:, 1].mean() + back, top + lift])
    V = (B.reshape(-1, 3) - cH) * s * scale + cO + np.array([0, -fwd, 0])
    F = [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(B))]
    return V, F

def fit_beard(Wn, scale=1.0, lift=0.0, fwd=0.0):
    """The figure's full beard + moustache (same download), placed by the same head match."""
    return fit_beret(Wn, scale=scale, lift=lift, fwd=fwd, piece='beard')
