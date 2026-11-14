#!/usr/bin/env python3
"""A straight-down top view of a 3D kit (STL), for make_air_units.py's 8 headings.

    python3 build/render_topview.py MODEL.stl OUT.png [--paint R,G,B] [--deck R,G,B] [--flip]

Orthographic, nose up, magenta background, 1024 x 1024 - the same as John's aircraft top views
(Reference\\aircraft_cartoon.zip), so every craft and vessel goes through one pipeline.
A cartoon finish: flat paint lit from above-left, the upper parts in the deck colour, dark outlines.
The model's longest horizontal axis is the length; the narrower end is taken as the bow (--flip turns it).
This is BUILD's quick renderer, not the factory's Blender kit: good enough to tell craft apart at battle size.
"""
import argparse
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model'); ap.add_argument('out')
    ap.add_argument('--paint', default='70,80,95'); ap.add_argument('--deck', default='170,175,180')
    ap.add_argument('--flip', action='store_true')
    ap.add_argument('--up', type=int, default=-1, help='the up axis (0,1,2); default: the flattest')
    a = ap.parse_args()
    m = trimesh.load(a.model, force='mesh')
    v = m.vertices.copy()
    v -= v.mean(0)
    # up = the smallest extent axis (boats are long and flat)
    ext = v.max(0) - v.min(0)
    up = int(np.argmin(ext)) if a.up < 0 else a.up
    hor = [i for i in range(3) if i != up]
    L, W = (hor[0], hor[1]) if ext[hor[0]] >= ext[hor[1]] else (hor[1], hor[0])
    x, y, z = v[:, W], v[:, L], v[:, up]
    # bow = the narrower end along the length
    def width_at(sel):
        return np.ptp(x[sel]) if sel.any() else 0
    top = y > np.percentile(y, 85); bot = y < np.percentile(y, 15)
    if (width_at(top) > width_at(bot)) != a.flip:
        y = -y; x = -x
    # is z up the right way? more area should face up than down
    f = m.faces
    tri = np.stack([np.stack([x[f[:, k]], y[f[:, k]], z[f[:, k]]], 1) for k in range(3)], 1)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    if (n[:, 2] > 0).sum() < (n[:, 2] < 0).sum():
        z = -z; x = -x
        tri = np.stack([np.stack([x[f[:, k]], y[f[:, k]], z[f[:, k]]], 1) for k in range(3)], 1)
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    up_faces = n[:, 2] > 0.05
    tri, n = tri[up_faces], n[up_faces]
    light = np.array([-0.4, 0.5, 0.77]); light /= np.linalg.norm(light)
    shade = np.clip(n @ light, 0.25, 1.0)
    zc = tri[:, :, 2].mean(1)
    zn = (zc - z.min()) / max(np.ptp(z), 1e-6)
    paint = np.array([int(t) for t in a.paint.split(',')]) / 255.0
    deck = np.array([int(t) for t in a.deck.split(',')]) / 255.0
    # decks: flat faces above the waterline take the deck colour; sides and the low hull keep the paint
    k = (np.clip((n[:, 2] - 0.8) * 5, 0, 1) * np.clip((zn - 0.25) * 4, 0, 1))[:, None]
    col = (paint * (1 - k) + deck * k) * (0.35 + 0.75 * shade[:, None])
    # posterise a little: cartoon bands
    col = np.round(np.clip(col, 0, 1) * 6) / 6
    order = np.argsort(zc)
    span = max(np.ptp(x), np.ptp(y)) * 0.54
    fig = plt.figure(figsize=(10.24, 10.24), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(-span, span); ax.set_ylim(-span, span); ax.axis('off')
    fig.patch.set_facecolor((1, 0, 1))
    ax.add_collection(PolyCollection(tri[order][:, :, :2], facecolors=col[order], edgecolors=col[order] * 0.6, linewidths=0.3))
    fig.savefig(a.out, facecolor=(1, 0, 1))
    print(a.out, len(tri), 'faces up')


if __name__ == '__main__':
    main()
